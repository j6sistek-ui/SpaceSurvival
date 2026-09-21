"""Import the reviewed private colony assembly; integration lead serializes Unreal.

Default is a read-only dry-run with receipt. -SSApplyStationColonyHabitat imports
only this dedicated folder, verifies centimetre bounds and stores ownership hashes.
The original Figur source and existing station/layout assets are never modified.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
OUT = ROOT / "Artifacts/StationReset/ColonyHabitat"
BASE = "/Game/SpaceSurvival/Licensed/StationReset/ColonyHabitat"
NAME = "SM_ColonyHabitat"
TARGET = BASE + "/" + NAME
LIB = u.EditorAssetLibrary


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def package_file(package):
    name = package.split(".")[0]
    assert name.startswith(BASE + "/"), "Import output escaped owned folder"
    return ROOT / "Content" / (name.removeprefix("/Game/") + ".uasset")


def main():
    apply = "-SSApplyStationColonyHabitat" in u.SystemLibrary.get_command_line()
    authored = json.loads((OUT / "author.json").read_text(encoding="utf-8"))
    source = OUT / (NAME + ".glb")
    original = Path(authored["source"])
    assert authored["status"] == "complete" and authored["source_preserved"]
    assert sha(source) == authored["output_sha256"], "Derivative GLB changed since preview"
    assert sha(original) == authored["source_sha256"], "Original Figur source changed"
    assert authored["target"] == TARGET
    existing = LIB.list_assets(BASE, recursive=True, include_folder=False) if LIB.does_directory_exist(BASE) else []
    prior_path = OUT / "import.json"
    prior = json.loads(prior_path.read_text(encoding="utf-8")) if prior_path.exists() else None
    if existing:
        assert prior and prior.get("status") == "complete", "Preserving existing unowned/partial import"
        for package in existing:
            path = package_file(package)
            expected = prior.get("output_hashes", {}).get(package.split(".")[0])
            assert expected and path.is_file() and sha(path) == expected, "Preserving edited output: " + package
    record = {"utc": datetime.now(timezone.utc).isoformat(), "mode": "apply" if apply else "dry-run",
              "source": str(source), "source_sha256": authored["output_sha256"],
              "original_source_sha256": authored["source_sha256"], "target": TARGET,
              "expected_bounds_cm": authored["bounds_cm"], "source_triangles": authored["triangles"],
              "collision": "Disabled; decorative building sits on existing physically bounded terrace",
              "source_preserved": False}
    if apply:
        if existing:
            backup = OUT / "Backups" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            for package in existing:
                path = package_file(package)
                destination = backup / path.relative_to(ROOT / "Content")
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, destination)
        pipeline = u.new_object(u.InterchangeGenericAssetsPipeline, name="SSColonyHabitatImport")
        for key, value in {"asset_name": NAME, "use_source_name_for_asset": False,
                           "import_offset_uniform_scale": 1., "asset_type_sub_folders": False,
                           "scene_name_sub_folder": False}.items():
            pipeline.set_editor_property(key, value)
        meshes = pipeline.get_editor_property("mesh_pipeline")
        meshes.set_editor_property("import_static_meshes", True)
        meshes.set_editor_property("combine_static_meshes_behavior", u.InterchangeCombineStaticMeshesBehavior.ALL)
        meshes.set_editor_property("import_skeletal_meshes", False)
        pipeline.get_editor_property("animation_pipeline").set_editor_property("import_animations", False)
        materials = pipeline.get_editor_property("material_pipeline")
        materials.set_editor_property("import_materials", True)
        materials.get_editor_property("texture_pipeline").set_editor_property("import_textures", True)
        params = u.ImportAssetParameters()
        params.set_editor_property("is_automated", True)
        params.set_editor_property("replace_existing", bool(existing))
        params.set_editor_property("override_pipelines", [u.SoftObjectPath(pipeline.get_path_name())])
        manager = u.InterchangeManager.get_interchange_manager_scripted()
        imported = manager.import_asset(BASE, manager.create_source_data(str(source)), params)
        static_meshes = [asset for asset in imported if isinstance(asset, u.StaticMesh)]
        assert len(static_meshes) == 1, "Expected one complete assembly"
        mesh = static_meshes[0]
        if mesh.get_path_name().split(".")[0] != TARGET:
            assert not LIB.does_asset_exist(TARGET), "Refusing to replace a different mesh identity"
            assert LIB.rename_asset(mesh.get_path_name(), TARGET)
        bounds = mesh.get_bounds()
        center = [bounds.origin.x, bounds.origin.y, bounds.origin.z]
        extent = [bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z]
        low, high = authored["bounds_cm"]
        for i in range(3):
            expected_size = high[i] - low[i]
            assert abs(extent[i] * 2 - expected_size) < max(.5, expected_size * .001), "Import dimension mismatch"
            expected_center = (high[i] + low[i]) / 2
            assert abs(center[i] - expected_center) < .5, "Import pivot mismatch"
        assert max(extent[0], extent[1]) * 2 <= 1800.5 and extent[2] * 2 <= 4500
        assert all(slot.material_interface for slot in mesh.static_materials), "Missing authored PBR slot"
        subsystem = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
        subsystem.remove_collisions(mesh)
        body = mesh.get_editor_property("body_setup")
        body.set_editor_property("collision_trace_flag", u.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
        for section in range(mesh.get_num_sections(0)):
            subsystem.enable_section_collision(mesh, False, 0, section)
        nanite = subsystem.get_nanite_settings(mesh)
        nanite.enabled = True
        subsystem.set_nanite_settings(mesh, nanite, apply_changes=True)
        for asset in imported:
            assert LIB.save_loaded_asset(asset, only_if_is_dirty=False)
        assert LIB.save_loaded_asset(mesh, only_if_is_dirty=False)
        record.update(bounds_cm=[[center[i] - extent[i] for i in range(3)],
                                 [center[i] + extent[i] for i in range(3)]],
                      nanite_triangles=mesh.get_num_nanite_triangles(), fallback_triangles=mesh.get_num_triangles(0),
                      materials=[slot.material_interface.get_path_name() for slot in mesh.static_materials],
                      output_hashes={package.split(".")[0]: sha(package_file(package))
                                     for package in LIB.list_assets(BASE, recursive=True, include_folder=False)})
    record["source_preserved"] = sha(original) == authored["source_sha256"]
    assert record["source_preserved"]
    record["status"] = "complete"
    path = prior_path if apply else OUT / "import-dry-run.json"
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("COLONY_HABITAT_IMPORT_COMPLETE " + record["mode"])


main()
