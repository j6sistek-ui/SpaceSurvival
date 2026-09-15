"""Author optional private station dressing without touching the paid originals.

Run PrepareStationVisualSources.py using existing Blender first. This script can
run under normal Python with --prepare-only for the generated screen and source
checks. The integration lead schedules the Unreal execution serially.
"""
from pathlib import Path
import hashlib
import json
import math
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".agent/local/StationVisualPass"
BASE = "/Game/SpaceSurvival/Licensed/StationVisualPass"
# The integrated review keeps Station4 as the service destination. Station3 is a
# distant ambient structure only; the fragmented Figur candidate stays unadopted.
EXTERIOR_SOURCE = "Station3Exterior"
VERSION = "1"
FREE_PRESENTATION_ASSETS = (
    "/Game/Robot_scout_R_21/Mesh/SK_Robot_scout_R21",
    "/Game/Robot_scout_R_21/Demo/Animations/ThirdPersonIdle",
    "/Game/Defect/StaticMeshes/Props/WallDecoration/SM_P161_ElectricMeter_01",
    "/Game/Defect/StaticMeshes/Props/WallDecoration/SM_P161_ElectricMeter_02",
    "/Game/Defect/StaticMeshes/Props/WallDecoration/SM_P160_switch",
    "/Game/Defect/StaticMeshes/Props/WallDecoration/SM_P158_annunciator_01",
    "/Game/Defect/StaticMeshes/Props/WallDecoration/SM_P158_annunciator_02",
    "/Game/Defect/StaticMeshes/Props/Photo/SM_P163_lamp",
)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def make_screen():
    """Original non-interactive service schematic, not simulated gameplay data."""
    width, height = 512, 256
    pixels = bytearray((5, 13, 21) * (width * height))

    def point(x, y, color):
        if 0 <= x < width and 0 <= y < height:
            offset = (int(y) * width + int(x)) * 3
            pixels[offset:offset+3] = bytes(color)

    def line(a, b, color, thickness=1):
        steps = max(abs(b[0]-a[0]), abs(b[1]-a[1]), 1)
        for i in range(steps+1):
            x, y = round(a[0]+(b[0]-a[0])*i/steps), round(a[1]+(b[1]-a[1])*i/steps)
            for ox in range(thickness):
                for oy in range(thickness):
                    point(x+ox, y+oy, color)

    def rectangle(x, y, w, h, color):
        for yy in range(y, y+h):
            for xx in range(x, x+w):
                point(xx, yy, color)

    # Low-contrast grid, pale cyan schematic, and restrained maintenance ochre.
    for x in range(16, width-10, 24):
        line((x, 43), (x, 224), (10, 27, 38))
    for y in range(48, 230, 24):
        line((16, y), (496, y), (10, 27, 38))
    rectangle(16, 15, 480, 2, (82, 159, 171))
    rectangle(16, 28, 96, 5, (102, 177, 190))
    rectangle(118, 28, 43, 5, (38, 78, 94))
    rectangle(464, 26, 11, 8, (192, 132, 49))
    rectangle(481, 26, 11, 8, (49, 121, 135))
    for i, length in enumerate((126, 99, 137, 85, 119)):
        y = 67 + i*29
        rectangle(24, y, 7, 7, (93, 150, 164))
        rectangle(42, y, length, 3, (66, 116, 131))
        rectangle(42, y+8, 148, 2, (20, 49, 63))
        rectangle(42, y+8, length-22, 2, (139, 103, 46) if i == 3 else (45, 88, 106))
    cyan = (70, 147, 159)
    hull = [(347, 62), (319, 109), (303, 169), (320, 183), (347, 169),
            (374, 183), (391, 169), (375, 109), (347, 62)]
    for a, b in zip(hull, hull[1:]):
        line(a, b, cyan, 2)
    for a, b in [((347, 62), (347, 169)), ((319, 109), (375, 109)),
                 ((320, 143), (374, 143)), ((320, 183), (314, 201)),
                 ((374, 183), (380, 201))]:
        line(a, b, (46, 94, 111))
    for center in [(347, 123), (331, 158), (363, 158)]:
        for angle in range(360):
            point(round(center[0]+8*math.cos(math.radians(angle))),
                  round(center[1]+8*math.sin(math.radians(angle))), (157, 118, 54))
    line((223, 55), (223, 218), (28, 59, 74))
    line((24, 236), (486, 236), (37, 82, 96))

    def chunk(kind, data):
        return struct.pack(">I", len(data))+kind+data+struct.pack(">I", zlib.crc32(kind+data)&0xffffffff)
    scanlines = b"".join(b"\0"+pixels[y*width*3:(y+1)*width*3] for y in range(height))
    png = b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(scanlines, 9))+chunk(b"IEND", b"")
    SOURCE.mkdir(parents=True, exist_ok=True)
    target = SOURCE / "ServiceScreen.png"
    target.write_bytes(png)
    return target


def source_record(key):
    report = json.loads((SOURCE/f"{key}.json").read_text(encoding="utf-8"))
    source = SOURCE/f"{key}.glb"
    assert sha(source) == report["output_sha256"], "Unreviewed derivative hash: "+key
    assert report["triangles"] <= 250000
    assert all(max(t["derivative"]) <= 2048 for t in report["textures"])
    return source, report


def verify_label_source_config(engine_config_dir):
    """Validate the two source config entries; the actual cook remains authoritative."""
    engine_file = Path(engine_config_dir) / "BaseGame.ini"
    project_file = ROOT / "Config/DefaultGame.ini"

    def label_entries(path):
        section = ""
        entries = []
        for raw in path.read_text(encoding="utf-8-sig").splitlines():
            line = raw.strip()
            if not line or line.startswith((";", "#")):
                continue
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1]
                continue
            if section != "/Script/Engine.AssetManagerSettings":
                continue
            key, separator, value = line.partition("=")
            if not separator or key.lstrip("+-!.") != "PrimaryAssetTypesToScan":
                continue
            assert not key.startswith("!"), "Unexpected primary-asset scan array reset: "+str(path)
            if 'PrimaryAssetType="PrimaryAssetLabel"' in value:
                entries.append((key[0] if key.startswith(("+", "-", ".")) else "", value))
        return entries

    inherited = label_entries(engine_file)
    assert len(inherited) == 1 and inherited[0][0] == "+", "Unreviewed engine label scan default"
    original = inherited[0][1]
    assert "bIsEditorOnly=True" in original and "CookRule=Unknown" in original
    replacement = original.replace("bIsEditorOnly=True", "bIsEditorOnly=False")
    assert label_entries(project_file) == [("-", original), ("+", replacement)], \
        "Project must replace the exact inherited label scan, keeping its type-wide Unknown cook rule"
    return dict(method="EXACT_ENGINE_AND_PROJECT_SOURCE_ENTRIES_ONLY",
                engine_config=str(engine_file), engine_sha256=sha(engine_file),
                project_config=str(project_file), project_sha256=sha(project_file),
                native_effective_config_and_cook="PENDING_ACTUAL_COOK_AND_ARCHIVE")


def author():
    import unreal as u
    lib = u.EditorAssetLibrary
    tools = u.AssetToolsHelpers.get_asset_tools()
    imported = []
    material_usage = []

    private_materials = {}
    def private_instanced_material(source_path):
        """Preserve instance overrides and clone every parent before changing usage."""
        source = lib.load_asset(source_path)
        assert isinstance(source, u.MaterialInterface), source_path
        source_path = source.get_path_name()
        if source_path in private_materials:
            return private_materials[source_path]
        target = BASE+"/Materials/"+source.get_name()
        clone = lib.load_asset(target) if lib.does_asset_exist(target) else None
        if clone:
            assert lib.get_metadata_tag(clone, "SSStationMaterialSource") == source_path, target
        else:
            clone = lib.duplicate_asset(source_path, target)
            assert clone, target
            lib.set_metadata_tag(clone, "SSStationMaterialSource", source_path)
        private_materials[source_path] = clone
        if isinstance(clone, u.MaterialInstanceConstant):
            parent = source.get_editor_property("parent")
            assert parent, "Source material instance must have a parent"
            private_parent = private_instanced_material(parent.get_path_name())
            u.MaterialEditingLibrary.set_material_instance_parent(clone, private_parent)
            u.MaterialEditingLibrary.update_material_instance(clone)
        else:
            assert isinstance(clone, u.Material), clone.get_path_name()
            clone.set_editor_property("used_with_instanced_static_meshes", True)
            clone.set_editor_property("used_with_nanite", True)
            u.MaterialEditingLibrary.recompile_material(clone)
        assert clone.get_path_name().startswith(BASE+"/Materials/")
        assert lib.save_loaded_asset(clone, only_if_is_dirty=False)
        return clone

    def author_free_cook_label():
        """Select eight presentation assets and their dependencies, not vendor examples."""
        # This build's Python DeveloperSettings wrapper does not expose the
        # AssetManagerSettings fields. Check exact source entries, then require
        # an actual cooked archive check rather than infer effective settings.
        config_check = verify_label_source_config(
            u.Paths.convert_relative_path_to_full(u.Paths.engine_config_dir()))

        selected = [lib.load_asset(path) for path in FREE_PRESENTATION_ASSETS]
        assert all(selected), "Selected station staff/electronics assets must be mounted before authoring"
        assert isinstance(selected[0], u.SkeletalMesh) and isinstance(selected[1], u.AnimSequence)
        assert all(isinstance(asset, u.StaticMesh) for asset in selected[2:])
        label_path = BASE+"/DA_StationFreePresentationCook"
        label_class = u.load_class(None, "/Script/Engine.PrimaryAssetLabel")
        assert label_class, "Engine PrimaryAssetLabel reflected class must resolve"
        label = lib.load_asset(label_path) if lib.does_asset_exist(label_path) else None
        if not label:
            factory = u.DataAssetFactory()
            factory.set_editor_property("data_asset_class", label_class)
            label = tools.create_asset("DA_StationFreePresentationCook", BASE, label_class, factory)
        assert label and label.get_class() == label_class
        # Native reflected names also work when no snake_case wrapper is
        # generated (verified in the installed PyWrapperObject/Struct code).
        rules = label.get_editor_property("Rules")
        for key, value in {"Priority": 1, "ChunkId": -1, "bApplyRecursively": True,
                           "CookRule": u.PrimaryAssetCookRule.ALWAYS_COOK}.items():
            rules.set_editor_property(key, value)
        label.set_editor_property("Rules", rules)
        label.set_editor_property("bIsRuntimeLabel", True)
        label.set_editor_property("bLabelAssetsInMyDirectory", False)
        label.set_editor_property("bIncludeRedirectors", False)
        label.set_editor_property("ExplicitAssets", selected)
        label.set_editor_property("ExplicitBlueprints", [])
        lib.set_metadata_tag(label, "SSStationVisualVersion", VERSION)
        assert lib.save_loaded_asset(label, only_if_is_dirty=False)
        assert len(label.get_editor_property("ExplicitAssets")) == len(FREE_PRESENTATION_ASSETS)
        return dict(path=label.get_path_name(), explicit_assets=list(FREE_PRESENTATION_ASSETS),
                    cook_rule="AlwaysCook", recursive_dependencies=True, runtime_label=True,
                    directory_labeling=False, source_config_check=config_check,
                    package_verification="PENDING_ACTUAL_COOK_AND_ARCHIVE")

    def ensure_material_usage(mesh_asset, flags):
        """Compile required permutations in private packages only, including reruns."""
        edit = u.MaterialEditingLibrary
        for slot in mesh_asset.get_editor_property("static_materials"):
            interface = slot.material_interface
            assert interface, "Missing material on "+mesh_asset.get_path_name()
            assert interface.get_path_name().startswith("/Game/SpaceSurvival/Licensed/"), \
                "Refusing vendor material mutation: "+interface.get_path_name()
            base_material = interface.get_base_material()
            assert base_material
            changed = False
            if base_material.get_path_name().startswith("/Game/SpaceSurvival/Licensed/"):
                for property_name, _ in flags:
                    if not base_material.get_editor_property(property_name):
                        base_material.set_editor_property(property_name, True)
                        changed = True
                if changed:
                    edit.recompile_material(base_material)
                    assert lib.save_loaded_asset(base_material, only_if_is_dirty=False)
            else:
                # UE5.8 material-instance usage overrides avoid changing the
                # engine/importer parent when Interchange emits an instance.
                assert isinstance(interface, u.MaterialInstanceConstant)
                for _, usage in flags:
                    edit.set_material_usage_override(interface, usage, True, True)
                edit.update_material_instance(interface)
                assert lib.save_loaded_asset(interface, only_if_is_dirty=False)
                changed = True
            material_usage.append(dict(material=interface.get_path_name(),
                                       base_material=base_material.get_path_name(),
                                       flags=[flag for flag, _ in flags], saved=changed))

    def mesh(key, folder, name):
        source, receipt = source_record(key)
        dest = BASE+"/"+folder
        target = dest+"/"+name
        if lib.does_asset_exist(target):
            result = lib.load_asset(target)
            assert lib.get_metadata_tag(result, "SSStationVisualSHA256") == receipt["output_sha256"], \
                "Existing derivative changed; deliberate reimport required: "+target
            imported.append(dict(path=result.get_path_name(), source=key, reused=True,
                                 triangles=receipt["triangles"], sha256=receipt["output_sha256"]))
            return result
        pipeline = u.new_object(u.InterchangeGenericAssetsPipeline, name="SSStationVisual"+folder)
        for k, v in {"asset_name": name, "use_source_name_for_asset": False,
                     "asset_type_sub_folders": False, "scene_name_sub_folder": False}.items():
            pipeline.set_editor_property(k, v)
        pipeline.get_editor_property("mesh_pipeline").set_editor_property("import_static_meshes", True)
        pipeline.get_editor_property("mesh_pipeline").set_editor_property("import_skeletal_meshes", False)
        pipeline.get_editor_property("animation_pipeline").set_editor_property("import_animations", False)
        material_pipeline = pipeline.get_editor_property("material_pipeline")
        material_pipeline.set_editor_property("import_materials", True)
        material_pipeline.get_editor_property("texture_pipeline").set_editor_property("import_textures", True)
        params = u.ImportAssetParameters()
        params.set_editor_property("is_automated", True)
        params.set_editor_property("replace_existing", False)
        params.set_editor_property("override_pipelines", [u.SoftObjectPath(pipeline.get_path_name())])
        manager = u.InterchangeManager.get_interchange_manager_scripted()
        assets = manager.import_asset(dest, manager.create_source_data(str(source)), params)
        meshes = [a for a in assets if isinstance(a, u.StaticMesh)]
        assert len(meshes) == 1, "Expected one combined presentation mesh"
        result = meshes[0]
        if result.get_path_name().split(".")[0] != target:
            assert lib.rename_asset(result.get_path_name(), target)
        result = lib.load_asset(target)
        assert len(result.static_materials) == 2
        assert all(s.material_interface for s in result.static_materials)
        u.get_editor_subsystem(u.StaticMeshEditorSubsystem).remove_collisions(result)
        bounds = result.get_bounds()
        actual = [bounds.box_extent.x*2, bounds.box_extent.y*2, bounds.box_extent.z*2]
        expected = [receipt["bounds_cm"][1][i]-receipt["bounds_cm"][0][i] for i in range(3)]
        assert all(abs(actual[i]-expected[i]) < 2 for i in range(3)), (actual, expected)
        lib.set_metadata_tag(result, "SSStationVisualSHA256", receipt["output_sha256"])
        lib.set_metadata_tag(result, "SSStationVisualVersion", VERSION)
        for asset in assets:
            if isinstance(asset, u.Texture):
                asset.set_editor_property("max_texture_size", 2048)
            assert lib.save_loaded_asset(asset, only_if_is_dirty=False)
        assert lib.save_loaded_asset(result, only_if_is_dirty=False)
        imported.append(dict(path=result.get_path_name(), source=key, bounds_cm=actual,
                             triangles=receipt["triangles"], sha256=receipt["output_sha256"]))
        return result

    cargo = mesh("ServiceCargo", "Cargo", "SM_ServiceCargo")
    exterior = mesh(EXTERIOR_SOURCE, "Meshes", "SM_Station3Exterior")
    instanced = ("used_with_instanced_static_meshes", u.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES)
    nanite = ("used_with_nanite", u.MaterialUsage.MATUSAGE_NANITE)
    ensure_material_usage(cargo, [instanced, nanite])
    ensure_material_usage(exterior, [nanite])
    previous_exterior_path = "/Game/SpaceSurvival/Licensed/StationExterior/SM_StationExterior"
    if lib.does_asset_exist(previous_exterior_path):
        ensure_material_usage(lib.load_asset(previous_exterior_path), [nanite])
    for name in ("MI_Grid_Teto01", "MI_TileTube"):
        private_instanced_material("/Game/SciFiCorridor/Materials/"+name)
    image = make_screen()
    texture_path = BASE+"/Screens/T_ServiceScreen"
    material_path = BASE+"/Screens/M_ServiceScreen"
    texture = lib.load_asset(texture_path) if lib.does_asset_exist(texture_path) else None
    if not texture:
        task = u.AssetImportTask()
        for key, value in {"filename": str(image), "destination_path": BASE+"/Screens",
                           "destination_name": "T_ServiceScreen", "automated": True,
                           "replace_existing": False, "save": False}.items():
            task.set_editor_property(key, value)
        tools.import_asset_tasks([task])
        texture = lib.load_asset(texture_path)
        assert isinstance(texture, u.Texture2D)
        texture.set_editor_property("srgb", True)
        texture.set_editor_property("compression_settings", u.TextureCompressionSettings.TC_BC7)
        texture.set_editor_property("address_x", u.TextureAddress.TA_CLAMP)
        texture.set_editor_property("address_y", u.TextureAddress.TA_CLAMP)
        lib.set_metadata_tag(texture, "SSStationVisualSHA256", sha(image))
        assert lib.save_loaded_asset(texture, only_if_is_dirty=False)
    assert lib.get_metadata_tag(texture, "SSStationVisualSHA256") == sha(image)
    material = lib.load_asset(material_path) if lib.does_asset_exist(material_path) else None
    if not material:
        material = tools.create_asset("M_ServiceScreen", BASE+"/Screens", u.Material, u.MaterialFactoryNew())
        assert material
        material.set_editor_property("shading_model", u.MaterialShadingModel.MSM_UNLIT)
        material.set_editor_property("used_with_instanced_static_meshes", True)
        edit = u.MaterialEditingLibrary
        sample = edit.create_material_expression(material, u.MaterialExpressionTextureSample, -300, 0)
        sample.set_editor_property("texture", texture)
        sample.set_editor_property("sampler_type", u.MaterialSamplerType.SAMPLERTYPE_COLOR)
        assert edit.connect_material_property(sample, "RGB", u.MaterialProperty.MP_EMISSIVE_COLOR)
        edit.recompile_material(material)
        lib.set_metadata_tag(material, "SSStationVisualVersion", VERSION)
        assert lib.save_loaded_asset(material, only_if_is_dirty=False)
    assert lib.get_metadata_tag(material, "SSStationVisualVersion") == VERSION
    cook_label = author_free_cook_label()
    result = dict(status="AUTHORED_RUNTIME_REVIEW_PENDING", engine=u.SystemLibrary.get_engine_version(),
                  ambient_structure_source=EXTERIOR_SOURCE, destination="Existing Station4 unchanged",
                  imported=imported, screen=material.get_path_name(),
                  material_usage=material_usage,
                  private_corridor_materials={source: asset.get_path_name()
                                              for source, asset in private_materials.items()},
                  selected_free_asset_cook_label=cook_label,
                  collision="No collision added; existing SSStation physical layout remains authoritative")
    (SOURCE/"UnrealAuthoring.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    u.log("STATION_VISUAL_PASS "+json.dumps(result))


if __name__ == "__main__":
    if "--prepare-only" in sys.argv:
        make_screen()
        for key in ("ServiceCargo", EXTERIOR_SOURCE):
            source_record(key)
        print("Station visual sources verified; Unreal authoring not run.")
    else:
        author()
