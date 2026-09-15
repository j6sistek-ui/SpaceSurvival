"""Import the private Havolk ship/module derivatives, preserving vendor assets.

Requires read-only source export and Blender AssembleShipVisualPass.py output.
Run with the installed full Unreal editor through the integration lead. All
created meshes remain under the ignored licensed directory. No roster, tuning,
player hull, pilot, collision sphere, level or saved-game edits occur here.
"""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Artifacts/ShipVisualPass"
SOURCE = OUT / "Assembly"
BASE = "/Game/SpaceSurvival/Licensed/ShipVisualPass/Meshes"
VERSION = "HavolkVisualPass1"
LIB = u.EditorAssetLibrary


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@contextmanager
def legacy_obj_import():
    names = ("Interchange.FeatureFlags.Import.OBJ", "Interchange.FeatureFlags.Import.FBX")
    previous = {name: u.SystemLibrary.get_console_variable_int_value(name) for name in names}
    try:
        for name in names:
            u.SystemLibrary.execute_console_command(None, name + " 0")
        yield
    finally:
        for name, value in previous.items():
            u.SystemLibrary.execute_console_command(None, name + " " + str(value))


def import_mesh(row):
    path = BASE + "/" + row["name"]
    source = SOURCE / (row["name"] + ".obj")
    assert sha(source) == row["obj_sha256"]
    existing = u.load_asset(path) if LIB.does_asset_exist(path) else None
    if existing:
        assert LIB.get_metadata_tag(existing, "SSShipVisualVersion") == VERSION, "Unowned destination: " + path
        if LIB.get_metadata_tag(existing, "SSShipVisualSourceSHA256") == row["obj_sha256"]:
            return existing
    options = u.FbxImportUI()
    for key, value in {"import_mesh": True, "import_as_skeletal": False, "import_materials": False,
                       "import_textures": False, "mesh_type_to_import": u.FBXImportType.FBXIT_STATIC_MESH}.items():
        options.set_editor_property(key, value)
    data = options.get_editor_property("static_mesh_import_data")
    for key, value in {"combine_meshes": True, "auto_generate_collision": False, "generate_lightmap_u_vs": False,
                       "import_uniform_scale": 1., "convert_scene": False, "convert_scene_unit": False,
                       "force_front_x_axis": False, "normal_import_method": u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS,
                       "normal_generation_method": u.FBXNormalGenerationMethod.MIKK_T_SPACE,
                       "import_translation": u.Vector(0, 0, 0), "import_rotation": u.Rotator(0, 0, 0)}.items():
        data.set_editor_property(key, value)
    task = u.AssetImportTask()
    for key, value in {"filename": str(source), "destination_path": BASE, "destination_name": row["name"],
                       "automated": True, "replace_existing": existing is not None, "replace_existing_settings": True,
                       "save": False, "factory": u.FbxFactory(), "options": options}.items():
        task.set_editor_property(key, value)
    with legacy_obj_import():
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    meshes = [u.load_asset(p) for p in task.get_editor_property("imported_object_paths")]
    assert len(meshes) == 1 and isinstance(meshes[0], u.StaticMesh)
    mesh = meshes[0]
    assert mesh.get_path_name().split(".")[0] == path
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        name = str(slot.get_editor_property("imported_material_slot_name"))
        assert name in row["materials"], name
        material = u.load_asset(row["materials"][name])
        assert isinstance(material, u.MaterialInterface), row["materials"][name]
        mesh.set_material(index, material)
    editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    editor.remove_collisions(mesh)
    for section in range(mesh.get_num_sections(0)):
        editor.enable_section_collision(mesh, False, 0, section)
    body = mesh.get_editor_property("body_setup")
    instance = body.get_editor_property("default_instance")
    instance.set_editor_property("collision_profile_name", "NoCollision")
    instance.set_editor_property("collision_enabled", u.CollisionEnabled.NO_COLLISION)
    body.set_editor_property("default_instance", instance)
    LIB.set_metadata_tag(mesh, "SSShipVisualVersion", VERSION)
    LIB.set_metadata_tag(mesh, "SSShipVisualSourceSHA256", row["obj_sha256"])
    assert LIB.save_loaded_asset(mesh, only_if_is_dirty=False)
    return mesh


def validate(mesh, row):
    editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    bounds = mesh.get_bounds()
    actual = [[getattr(bounds.origin, axis) + sign * getattr(bounds.box_extent, axis) for axis in ("x", "y", "z")]
              for sign in (-1, 1)]
    assert all(abs(actual[edge][axis] - row["bounds_cm"][edge][axis]) < .05
               for edge in range(2) for axis in range(3)), (mesh.get_name(), actual, row["bounds_cm"])
    assert editor.get_simple_collision_count(mesh) == 0
    assert all(not editor.is_section_collision_enabled(mesh, 0, i) for i in range(mesh.get_num_sections(0)))
    assert mesh.get_editor_property("body_setup").get_editor_property("default_instance").get_editor_property(
        "collision_enabled") == u.CollisionEnabled.NO_COLLISION
    assert editor.get_num_uv_channels(mesh, 0) >= 1
    actual_materials = [slot.material_interface.get_path_name() for slot in mesh.static_materials]
    assert set(actual_materials) == set(row["materials"].values())
    return {"path": mesh.get_path_name(), "bounds_cm": actual, "triangles": mesh.get_num_triangles(0),
            "sections": mesh.get_num_sections(0), "materials": actual_materials, "collision": "NoCollision",
            "source_sha256": row["obj_sha256"]}


def main():
    report = json.loads((SOURCE / "Assembly.json").read_text(encoding="utf-8"))
    assert report["generator_sha256"] == sha(ROOT / "Scripts/AssembleShipVisualPass.py")
    expected = {"SM_Upgrade" + track + str(tier) for track in ("Hull", "Shield", "Engine", "Thrusters", "Laser", "Cannon")
                for tier in range(2, 6)}
    expected |= {"SM_UtilityVector", "SM_UtilityCooling", "SM_PursuerHavolk", "SM_FlankerHavolk"}
    expected |= {"SM_Upgrade" + track + "Swift" + str(tier) for track in ("Hull", "Shield") for tier in range(2, 6)}
    assert {row["name"] for row in report["assets"]} == expected
    originals = {p: sha(p) for directory in ("Content/Spacecraft_Pack", "Content/SpaceSurvival/Character")
                 for p in (ROOT / directory).rglob("*.uasset")}
    originals.update({p: sha(p) for p in (ROOT / "Content/SpaceSurvival/Meshes").glob("*.uasset")})
    rows = [validate(import_mesh(row), row) for row in report["assets"]]
    assert all(sha(path) == digest for path, digest in originals.items()), "Protected source asset changed"
    result = {"status": "IMPORTED_BOUNDS_MATERIAL_COLLISION_VERIFIED_REQUIRES_NATIVE_VISUAL_REVIEW",
              "engine": u.SystemLibrary.get_engine_version(), "assembly_sha256": sha(SOURCE / "Assembly.json"),
              "assets": rows, "protected_assets_unchanged": len(originals)}
    (OUT / "Import.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    u.log("SHIP_VISUAL_IMPORT_OK " + str(len(rows)))


if __name__ == "__main__":
    main()
