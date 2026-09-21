"""Import the reviewed private colony assembly; integration lead serializes Unreal.

Default is a read-only dry-run with receipt. -SSApplyStationColonyHabitat imports
only this dedicated folder, verifies centimetre bounds and stores ownership hashes.
Add -SSRepairStationColonyMaterials to inspect/repair material Nanite usage without
reimporting geometry or textures; that mode still requires the apply flag to write.
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


def output_hashes():
    return {package.split(".")[0]: sha(package_file(package))
            for package in LIB.list_assets(BASE, recursive=True, include_folder=False)}


def backup_existing(existing, prior_path):
    backup = OUT / "Backups" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    for package in existing:
        path = package_file(package)
        destination = backup / path.relative_to(ROOT / "Content")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
    if prior_path.exists():
        backup.mkdir(parents=True, exist_ok=True)
        shutil.copy2(prior_path, backup / "import.json")
    return str(backup)


def prepare_nanite_materials(mesh, apply):
    """Use UE5.8 usage APIs; never save a material outside this owned output."""
    edit = u.MaterialEditingLibrary
    usage = u.MaterialUsage.MATUSAGE_NANITE
    records, saved = [], set()
    for slot in mesh.static_materials:
        interface = slot.material_interface
        assert interface, "Missing authored PBR slot"
        package_file(interface.get_path_name())
        base = interface.get_base_material()
        assert base, "Material has no resolved base: " + interface.get_path_name()
        private_base = base.get_path_name().startswith(BASE + "/")
        instance = isinstance(interface, u.MaterialInstanceConstant)
        assert private_base or instance, "Refusing external base material mutation"
        item = {"material": interface.get_path_name(), "base_material": base.get_path_name(),
                "nanite_before": bool(edit.has_material_usage(interface, usage)), "saved": []}
        if apply:
            to_save = []
            if private_base:
                edit.set_base_material_usage(base, usage, True)
                edit.recompile_material(base)
                to_save.append(base)
            if instance:
                # Interchange may use an engine/importer parent. Its private child can carry the
                # required permutation override without modifying that external parent package.
                edit.set_material_usage_override(interface, usage, True, True)
                edit.update_material_instance(interface)
                to_save.append(interface)
            for material in to_save:
                package = material.get_path_name().split(".")[0]
                package_file(package)
                if package not in saved:
                    assert LIB.save_loaded_asset(material, only_if_is_dirty=False)
                    saved.add(package)
                    item["saved"].append(package)
            assert edit.has_material_usage(interface, usage), "Nanite material usage was not enabled"
        item["nanite_after"] = bool(edit.has_material_usage(interface, usage))
        records.append(item)
    return records, saved


def main():
    command_line = u.SystemLibrary.get_command_line()
    apply = "-SSApplyStationColonyHabitat" in command_line
    usage_only = "-SSRepairStationColonyMaterials" in command_line
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
        assert {package.split(".")[0] for package in existing} == set(prior.get("output_hashes", {})), \
            "Preserving changed output inventory"
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
    if usage_only:
        assert existing and prior and prior.get("target") == TARGET, "Material repair requires the owned import"
        mesh = LIB.load_asset(TARGET)
        assert isinstance(mesh, u.StaticMesh), "Owned colony mesh is unavailable"
        before = output_hashes()
        record.update(operation="nanite-material-usage-only", reimported=False, previous_output_hashes=before)
        if apply:
            record["backup"] = backup_existing(existing, prior_path)
        records, saved = prepare_nanite_materials(mesh, apply)
        after = output_hashes()
        assert before.keys() == after.keys(), "Material repair changed the owned asset inventory"
        assert all(before[package] == value for package, value in after.items() if package not in saved), \
            "Material repair modified a mesh, texture or other unrelated output"
        record.update(material_usage=records, output_hashes=after,
                      changed_packages=sorted(package for package in after if after[package] != before[package]),
                      mesh_textures_preserved=True, source_preserved=sha(original) == authored["source_sha256"],
                      status="complete")
        assert record["source_preserved"]
        path = OUT / ("material-usage-author.json" if apply else "material-usage-dry-run.json")
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        if apply:
            # Retain the original import's geometry/material provenance and refresh its authoritative
            # output hashes. The complete previous receipt is in the timestamped backup above.
            prior.update(output_hashes=after, material_usage=records, last_material_usage_repair=record["utc"],
                         material_usage_receipt=str(path))
            prior_path.write_text(json.dumps(prior, indent=2) + "\n", encoding="utf-8")
        print("COLONY_HABITAT_MATERIAL_USAGE_COMPLETE " + record["mode"])
        return
    if apply:
        if existing:
            record["backup"] = backup_existing(existing, prior_path)
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
        record["material_usage"], _ = prepare_nanite_materials(mesh, True)
        for asset in imported:
            assert LIB.save_loaded_asset(asset, only_if_is_dirty=False)
        assert LIB.save_loaded_asset(mesh, only_if_is_dirty=False)
        record.update(bounds_cm=[[center[i] - extent[i] for i in range(3)],
                                 [center[i] + extent[i] for i in range(3)]],
                      nanite_triangles=mesh.get_num_nanite_triangles(), fallback_triangles=mesh.get_num_triangles(0),
                      materials=[slot.material_interface.get_path_name() for slot in mesh.static_materials],
                      output_hashes=output_hashes())
    record["source_preserved"] = sha(original) == authored["source_sha256"]
    assert record["source_preserved"]
    record["status"] = "complete"
    path = prior_path if apply else OUT / "import-dry-run.json"
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("COLONY_HABITAT_IMPORT_COMPLETE " + record["mode"])


main()
