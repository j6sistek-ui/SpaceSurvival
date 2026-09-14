"""Author exactly two isolated NASA sky assets; preserve the existing sky graph."""
import hashlib
import json
from pathlib import Path
import re
import runpy
import traceback
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ContentSource/ThirdParty/NASA/MilkyWay2020"
OUT = ROOT / "Saved/Validation/MilkyWay2020"
TEXTURE = "/Game/SpaceSurvival/Textures/T_MilkyWay2020"
INSTANCE = "/Game/SpaceSurvival/Materials/MI_SpaceMilkyWay"
PARENT = "/Game/SpaceSurvival/Materials/M_Space"
VERSION = "NASAMilkyWay2020Display1"
LIB = u.EditorAssetLibrary
EDIT = u.MaterialEditingLibrary
OWNED = {"Content/SpaceSurvival/Textures/T_MilkyWay2020.uasset",
         "Content/SpaceSurvival/Materials/MI_SpaceMilkyWay.uasset"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_manifest():
    return runpy.run_path(str(SOURCE / "CheckSource.py"))["check"]()


def write(name, record):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")


def snapshot():
    return {p.relative_to(ROOT).as_posix(): sha(p) for folder in ("Source", "Config", "Content")
            for p in (ROOT / folder).rglob("*") if p.is_file()}


def check_unchanged(before):
    after = snapshot()
    changed = [p for p, digest in before.items() if after.get(p) != digest]
    unexpected = sorted(set(after) - set(before) - OWNED)
    assert not changed and not unexpected, f"Protected assets changed: {changed}; unexpected assets: {unexpected}"


def finish_textures():
    # Installed TextureCompiler.cpp and AsyncCompilationHelpers.cpp register this command.
    # Finish pending editor work without changing streaming or scalability settings.
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    u.SystemLibrary.execute_console_command(world, "Editor.AsyncTextureCompilationFinishAll")


def parent_material():
    parent = LIB.load_asset(PARENT)
    assert isinstance(parent, u.Material), "Existing sky material missing"
    assert LIB.get_metadata_tag(parent, "SSPanoramaVersion") == "EquirectangularStarless3"
    assert parent.get_editor_property("shading_model") == u.MaterialShadingModel.MSM_UNLIT
    assert parent.get_editor_property("two_sided")
    assert {str(n) for n in EDIT.get_texture_parameter_names(parent)} == {"SpacePanorama"}
    assert not EDIT.get_static_switch_parameter_names(parent)
    old = EDIT.get_material_default_texture_parameter_value(parent, "SpacePanorama")
    assert old and old.get_path_name() == "/Game/SpaceSurvival/Textures/T_SpacePanorama_starless_v2.T_SpacePanorama_starless_v2"
    return parent


def texture_settings():
    return {
        "srgb": True, "compression_settings": u.TextureCompressionSettings.TC_BC7,
        "lod_group": u.TextureGroup.TEXTUREGROUP_SKYBOX,
        "power_of_two_mode": u.TexturePowerOfTwoSetting.NONE,
        "mip_gen_settings": u.TextureMipGenSettings.TMGS_SIMPLE_AVERAGE,
        "address_x": u.TextureAddress.TA_WRAP, "address_y": u.TextureAddress.TA_CLAMP,
        "lod_bias": 0, "max_texture_size": 8192, "never_stream": False,
        "virtual_texture_streaming": False,
    }


def metadata(asset, manifest, create=False):
    values = {"SSMilkyWayVersion": VERSION, "SSMilkyWayPNG_SHA256": manifest["sha256"],
              "SSMilkyWayOriginal_SHA256": manifest["source"]["sha256"]}
    for key, value in values.items():
        if create:
            LIB.set_metadata_tag(asset, key, value)
        assert LIB.get_metadata_tag(asset, key) == value, "Existing candidate differs; explicit review required"


def validate_loaded(texture, instance, manifest):
    parent = parent_material()
    assert isinstance(texture, u.Texture2D) and isinstance(instance, u.MaterialInstanceConstant)
    assert texture.get_path_name() == TEXTURE + ".T_MilkyWay2020"
    assert instance.get_path_name() == INSTANCE + ".MI_SpaceMilkyWay"
    metadata(texture, manifest)
    metadata(instance, manifest)
    for key, value in texture_settings().items():
        assert texture.get_editor_property(key) == value, "Texture setting differs: " + key
    assert instance.get_editor_property("parent") == parent
    values = instance.get_editor_property("texture_parameter_values")
    assert len(values) == 1, "Expected exactly one texture override"
    info = values[0].get_editor_property("parameter_info")
    assert str(info.get_editor_property("name")) == "SpacePanorama"
    assert info.get_editor_property("association") == u.MaterialParameterAssociation.GLOBAL_PARAMETER
    assert values[0].get_editor_property("parameter_value") == texture
    for key in ("scalar_parameter_values", "vector_parameter_values", "double_vector_parameter_values",
                "texture_collection_parameter_values", "parameter_collection_parameter_values",
                "runtime_virtual_texture_parameter_values", "sparse_volume_texture_parameter_values",
                "font_parameter_values", "user_scene_texture_overrides"):
        assert not instance.get_editor_property(key), "Unexpected material override: " + key
    overrides = instance.get_editor_property("base_property_overrides").export_text()
    flags = re.findall(r"bOverride\w*\s*=\s*([^,)]+)", overrides)
    assert flags and all(value.strip() in ("False", "0") for value in flags), "Base material override enabled"
    assert EDIT.get_material_instance_texture_parameter_value(instance, "SpacePanorama") == texture
    assert EDIT.get_material_instance_scalar_parameter_value(instance, "SkyIntensity") == EDIT.get_material_default_scalar_parameter_value(parent, "SkyIntensity")
    assert EDIT.get_material_instance_vector_parameter_value(instance, "Tint") == EDIT.get_material_default_vector_parameter_value(parent, "Tint")
    finish_textures()
    dimensions = [texture.blueprint_get_size_x(), texture.blueprint_get_size_y()]
    assert dimensions == [8192, 4096], f"Compiled texture dimensions differ: {dimensions}"
    return {"texture": texture.get_path_name(), "dimensions": dimensions, "parent": parent.get_path_name(),
            "instance": instance.get_path_name(), "texture_overrides": ["SpacePanorama"],
            "inherited": ["Tint", "SkyIntensity", "direction mapping", "seam/pole handling"],
            "never_stream": False, "source_sha256": manifest["sha256"]}


def main():
    before = snapshot()
    record = {"status": "FAILED", "errors": []}
    try:
        manifest = source_manifest()
        parent = parent_material()
        texture = LIB.load_asset(TEXTURE) if LIB.does_asset_exist(TEXTURE) else None
        if texture is None:
            task = u.AssetImportTask()
            for key, value in {"filename": str(SOURCE / manifest["file"]),
                               "destination_path": "/Game/SpaceSurvival/Textures",
                               "destination_name": "T_MilkyWay2020", "automated": True,
                               "replace_existing": False, "save": False}.items():
                task.set_editor_property(key, value)
            u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            products = [LIB.load_asset(p) for p in task.get_editor_property("imported_object_paths")]
            assert len(products) == 1 and isinstance(products[0], u.Texture2D)
            texture = products[0]
            assert texture.get_path_name() == TEXTURE + ".T_MilkyWay2020"
            for key, value in texture_settings().items():
                texture.set_editor_property(key, value)
            metadata(texture, manifest, create=True)
            assert LIB.save_loaded_asset(texture, only_if_is_dirty=False)
        else:
            metadata(texture, manifest)
        instance = LIB.load_asset(INSTANCE) if LIB.does_asset_exist(INSTANCE) else None
        if instance is None:
            factory = u.MaterialInstanceConstantFactoryNew()
            instance = u.AssetToolsHelpers.get_asset_tools().create_asset(
                "MI_SpaceMilkyWay", "/Game/SpaceSurvival/Materials", u.MaterialInstanceConstant, factory)
            assert isinstance(instance, u.MaterialInstanceConstant)
            EDIT.set_material_instance_parent(instance, parent)
            # UE 5.8 MaterialEditingLibrary.cpp returns false even after setting this value.
            # Verify the actual override, which the fresh validator also checks.
            EDIT.set_material_instance_texture_parameter_value(instance, "SpacePanorama", texture)
            assert EDIT.get_material_instance_texture_parameter_value(instance, "SpacePanorama") == texture
            EDIT.update_material_instance(instance)
            metadata(instance, manifest, create=True)
            assert LIB.save_loaded_asset(instance, only_if_is_dirty=False)
        record.update(validate_loaded(texture, instance, manifest))
        check_unchanged(before)
        source_manifest()
        record.update(status="NASA_SKY_TWO_ASSETS_AUTHORED_NOT_VISUAL_ACCEPTANCE",
                      engine=u.SystemLibrary.get_engine_version(), errors=[],
                      preserved_files=len(before), created=sorted(set(snapshot()) - set(before)))
        write("Import.json", record)
        return record
    except Exception as exc:
        record["errors"].append(str(exc))
        try:
            check_unchanged(before)
        except Exception as guard:
            record["errors"].append(str(guard))
        write("Import.json", record)
        u.log_error(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
