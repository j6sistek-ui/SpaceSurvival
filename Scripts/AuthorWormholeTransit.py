"""Author only the original wormhole tunnel mesh/material; no map/roster edits.

Run inside the target Unreal Editor Python environment. The lead owns engine
execution. main(replace_owned=True) permits a deliberate recipe update of only
these two metadata-owned packages. Identical reruns preserve package bytes.

Runtime: +X, scale 1; mesh X=-15000..125000 cm, radius 10000 tapering to 6500 cm
before organic corrugation. Open near mouth; luminous far disk is in the mesh.
Set TransitTime to passage seconds. Defaults: TransitBlend=1, Speed=1, Glow=0.8,
ExitFlash=0. TransitBlend changes brightness, not opacity; control visibility
and actor lifetime at runtime. ExitFlash=0..1 adds a soft warm final wash.
"""
import hashlib
import json
import runpy
from datetime import datetime, timezone
from pathlib import Path

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ContentSource/WormholeTransit"
OUTPUT = ROOT / "Artifacts/WormholeTransit"
MESH = "/Game/SpaceSurvival/Meshes/SM_WormholeTunnel"
MATERIAL = "/Game/SpaceSurvival/Materials/M_WormholeTransit"
OWNER = "SpaceSurvival.OriginalWormholeTransit.v1"
LIB, EDIT = u.EditorAssetLibrary, u.MaterialEditingLibrary
SCALARS = {"TransitTime": 0.0, "TransitBlend": 1.0, "Speed": 1.0,
           "Glow": 0.8, "ExitFlash": 0.0}
COLORS = {"FoldColor": (0.055, 0.038, 0.14), "Lavender": (0.34, 0.25, 0.54),
          "Pink": (0.88, 0.40, 0.53), "Peach": (1.0, 0.70, 0.48)}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inspect_existing(path, cls, key, replace_owned):
    asset = LIB.load_asset(path) if LIB.does_asset_exist(path) else None
    if asset:
        if not isinstance(asset, cls) or LIB.get_metadata_tag(asset, "SSWormholeOwner") != OWNER:
            raise RuntimeError("Refusing to modify an unowned package: " + path)
        if LIB.get_metadata_tag(asset, "SSWormholeSourceKey") != key and not replace_owned:
            raise RuntimeError("Recipe changed; review then call main(replace_owned=True): " + path)
    return asset


def save(asset, key):
    path = asset.get_path_name().split(".")[0]
    if path not in (MESH, MATERIAL):
        raise RuntimeError("Refusing save outside the two wormhole assets: " + path)
    LIB.set_metadata_tag(asset, "SSWormholeOwner", OWNER)
    LIB.set_metadata_tag(asset, "SSWormholeSourceKey", key)
    LIB.set_metadata_tag(asset, "SSWormholeVisualAcceptance", "Unreviewed")
    if not LIB.save_loaded_asset(asset, only_if_is_dirty=False):
        raise RuntimeError("Could not save: " + path)


def author_material(asset, key):
    if asset and LIB.get_metadata_tag(asset, "SSWormholeSourceKey") == key:
        return asset
    if asset:
        EDIT.delete_all_material_expressions(asset)
    else:
        asset = u.AssetToolsHelpers.get_asset_tools().create_asset(
            "M_WormholeTransit", "/Game/SpaceSurvival/Materials", u.Material, u.MaterialFactoryNew())
    if not asset:
        raise RuntimeError("Wormhole material creation failed")
    asset.set_editor_property("shading_model", u.MaterialShadingModel.MSM_UNLIT)
    asset.set_editor_property("blend_mode", u.BlendMode.BLEND_OPAQUE)
    asset.set_editor_property("two_sided", True)
    inputs = {"UV": EDIT.create_material_expression(asset, u.MaterialExpressionTextureCoordinate, -750, 0)}
    inputs["UV"].set_editor_property("coordinate_index", 0)
    for index, (name, value) in enumerate(SCALARS.items(), 1):
        expression = EDIT.create_material_expression(asset, u.MaterialExpressionScalarParameter, -750, index * 100)
        expression.set_editor_property("parameter_name", name)
        expression.set_editor_property("default_value", value)
        inputs[name] = expression
    for index, (name, value) in enumerate(COLORS.items(), len(SCALARS) + 1):
        expression = EDIT.create_material_expression(asset, u.MaterialExpressionVectorParameter, -750, index * 100)
        expression.set_editor_property("parameter_name", name)
        expression.set_editor_property("default_value", u.LinearColor(*value, 1.0))
        inputs[name] = expression
    custom = EDIT.create_material_expression(asset, u.MaterialExpressionCustom, -200, 0)
    custom.set_editor_property("code", (SOURCE / "Transit.hlsl").read_text(encoding="utf-8"))
    custom.set_editor_property("description", "Original cylindrical vapor, axial filaments and warm far glow")
    custom.set_editor_property("output_type", u.CustomMaterialOutputType.CMOT_FLOAT3)
    pins = []
    for name in inputs:
        pin = u.CustomInput()
        pin.set_editor_property("input_name", name)
        pins.append(pin)
    custom.set_editor_property("inputs", pins)
    for name, expression in inputs.items():
        if not EDIT.connect_material_expressions(expression, "", custom, name):
            raise RuntimeError("Cannot connect material input: " + name)
    if not EDIT.connect_material_property(custom, "", u.MaterialProperty.MP_EMISSIVE_COLOR):
        raise RuntimeError("Cannot connect tunnel emissive")
    EDIT.recompile_material(asset)
    save(asset, key)
    return asset


def author_mesh(asset, material, key, obj_path):
    if asset and LIB.get_metadata_tag(asset, "SSWormholeSourceKey") == key:
        return asset
    options = u.FbxImportUI()
    for name, value in {"import_mesh": True, "import_as_skeletal": False,
                        "import_materials": False, "import_textures": False,
                        "mesh_type_to_import": u.FBXImportType.FBXIT_STATIC_MESH}.items():
        options.set_editor_property(name, value)
    data = options.get_editor_property("static_mesh_import_data")
    for name, value in {"combine_meshes": True, "auto_generate_collision": False,
                        "generate_lightmap_u_vs": False, "import_uniform_scale": 1.0,
                        "convert_scene": False, "force_front_x_axis": False,
                        "normal_import_method": u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS}.items():
        data.set_editor_property(name, value)
    task = u.AssetImportTask()
    for name, value in {"filename": str(obj_path), "destination_path": "/Game/SpaceSurvival/Meshes",
                        "destination_name": "SM_WormholeTunnel", "automated": True,
                        "replace_existing": asset is not None, "replace_existing_settings": True,
                        "save": False, "options": options, "factory": u.FbxFactory()}.items():
        task.set_editor_property(name, value)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = [LIB.load_asset(path) for path in task.get_editor_property("imported_object_paths")]
    if len(imported) != 1 or not isinstance(imported[0], u.StaticMesh):
        raise RuntimeError("Tunnel import did not produce exactly one static mesh")
    mesh = imported[0]
    if mesh.get_path_name().split(".")[0] != MESH:
        raise RuntimeError("Unexpected import destination: " + mesh.get_path_name())
    if len(mesh.get_editor_property("static_materials")) != 1 or mesh.get_num_sections(0) != 1:
        raise RuntimeError("Tunnel lost the single material section contract")
    mesh.set_material(0, material)
    editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    editor.remove_collisions(mesh)
    for lod in range(editor.get_lod_count(mesh)):
        for section in range(mesh.get_num_sections(lod)):
            editor.enable_section_collision(mesh, False, lod, section)
    body = mesh.get_editor_property("body_setup")
    instance = body.get_editor_property("default_instance")
    instance.set_editor_property("collision_profile_name", "NoCollision")
    instance.set_editor_property("collision_enabled", u.CollisionEnabled.NO_COLLISION)
    body.set_editor_property("default_instance", instance)
    save(mesh, key)
    return mesh


def main(replace_owned=False):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report = {"status": "FAILED", "utc": datetime.now(timezone.utc).isoformat(),
              "engine": u.SystemLibrary.get_engine_version(), "scalar_defaults": SCALARS,
              "color_defaults": COLORS, "replace_owned": replace_owned,
              "limits": ["No map, Data Asset, runtime selection or vendor package is edited.",
                         "Material compiler logs, rendered quality, runtime timing and GPU cost require lead validation.",
                         "Opaque TransitBlend dims emission; runtime must hide the mesh on exit."]}
    try:
        geometry = runpy.run_path(str(SOURCE / "Generate.py"))["generate"](OUTPUT / "Source")
        source_hashes = {path.relative_to(ROOT).as_posix(): sha(path) for path in
                         (Path(__file__), SOURCE / "Generate.py", SOURCE / "Transit.hlsl")}
        material_key = hashlib.sha256(json.dumps({"shader": source_hashes["ContentSource/WormholeTransit/Transit.hlsl"],
            "author": source_hashes["Scripts/AuthorWormholeTransit.py"],
            "scalars": SCALARS, "colors": COLORS, "owner": OWNER}, sort_keys=True).encode()).hexdigest()
        mesh_key = hashlib.sha256((geometry["obj_sha256"] + OWNER).encode()).hexdigest()
        # Check both targets before modifying either. Reruns never adopt foreign assets.
        old_material = inspect_existing(MATERIAL, u.Material, material_key, replace_owned)
        old_mesh = inspect_existing(MESH, u.StaticMesh, mesh_key, replace_owned)
        material = author_material(old_material, material_key)
        mesh = author_mesh(old_mesh, material, mesh_key, OUTPUT / "Source/SM_WormholeTunnel.obj")
        if mesh.get_material(0) != material:
            raise RuntimeError("Tunnel is not bound to the authored material")
        bounds = mesh.get_bounds()
        size = bounds.box_extent * 2.0
        if abs(size.x - geometry["length_cm"]) > 2.0 or abs(bounds.origin.x - 55000.0) > 2.0:
            raise RuntimeError("Imported tunnel axis/scale differs from centimetre +X contract")
        report.update(status="AUTHORED_REQUIRES_RENDERED_REVIEW", geometry=geometry,
                      source_sha256=source_hashes, mesh=mesh.get_path_name(), material=material.get_path_name(),
                      material_source_key=material_key, mesh_source_key=mesh_key,
                      imported_size_cm=[size.x, size.y, size.z],
                      imported_origin_cm=[bounds.origin.x, bounds.origin.y, bounds.origin.z])
        return report
    except Exception as error:
        report["error"] = str(error)
        raise
    finally:
        (OUTPUT / "Author.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        u.log("WormholeTransit: " + json.dumps(report))


if __name__ == "__main__":
    main()
