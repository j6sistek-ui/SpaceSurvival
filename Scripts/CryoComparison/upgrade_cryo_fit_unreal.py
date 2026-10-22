"""New-only addon mesh import for v4; default is a filesystem-only dry run.

main(True, manifest_path) is restricted to CryoStage. Existing mesh packages,
materials, textures and sequences are never saved; only new FitV4 mesh assets
and the owned comparison map are saved. No engine launch or owner-project edit.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import runpy
import shutil
import traceback

WORK = Path(__file__).resolve().parent
OUT = WORK.parent / "outputs/Cryo_Comparison"
STAGE = WORK / "CryoStage"
BASE = "/Game/SpaceSurvival/CryoComparison"
MAP = BASE + "/Maps/L_CryoComparison"
OLD_MANIFEST = OUT / "assembly_holo_consoles.json"
API = runpy.run_path(str(WORK / "author_cryo_unreal.py"))
require, digest = API["require"], API["digest"]
API["ROLES"].update({"console_backing", "console_glass", "console_frame"})


def prepare(path):
    path = Path(path).resolve()
    require(path.is_relative_to(WORK.parent) and path != OLD_MANIFEST.resolve(), "Expected a new D-drive manifest")
    current, sources, manifest_hash = API["prepare"](path)
    previous, old_sources, old_hash = API["prepare"](OLD_MANIFEST)
    require([model["id"] for model in current["models"]] == ["A", "B", "C", "D"], "Expected ordered models A/B/C/D")
    require(current["shared"] == previous["shared"], "Shared artwork must remain unchanged")
    changes = []
    changed_names = []
    for model, old in zip(current["models"], previous["models"]):
        require(model["source"] == old["source"] and model["textures"] == old["textures"], "Body source/textures changed")
        require(digest(model["source"]) == old["source_sha256"], "Original downloaded GLB hash differs from baseline")
        require(model["height_cm"] == old["height_cm"], "Body scale changed")
        old_rows = {row["name"]: row for row in old["components"]}
        require(set(old_rows) == {row["name"] for row in model["components"]}, "Component names changed")
        require(Counter(row["role"] for row in model["components"]) == Counter(row["role"] for row in old["components"]),
                "Component roles/counts changed")
        names = set()
        for row in model["components"]:
            before = old_rows[row["name"]]
            require(row["role"] == before["role"], "Component role changed")
            old_sha, new_sha = digest(before["file"]), digest(row["file"])
            if row["role"] == "body":
                require(old_sha == new_sha, "Original body OBJ geometry changed: " + model["id"])
            if old_sha != new_sha:
                require(row["role"] != "body", "Body import forbidden")
                require(Path(row["file"]).resolve().is_relative_to(WORK.parent), "New addon OBJ must remain on D")
                names.add(row["name"])
                changes.append({"model_id": model["id"], "name": row["name"], "role": row["role"],
                                "file": row["file"], "source_sha256": new_sha, "previous_source_sha256": old_sha,
                                "actor": model["id"] + "_" + row["name"],
                                "asset": BASE + "/Meshes/FitV4/" + model["id"] + "/SM_" + model["id"] + "_" + row["name"] + "_FitV4"})
        require(names, "Each chamber must receive the fit revision")
        changed_names.append(names)
    require(all(names == changed_names[0] for names in changed_names), "The same addon components must be revised for all four")
    sources.update(old_sources)
    sources[str(path)] = {"sha256": manifest_hash}
    sources[str(OLD_MANIFEST.resolve())] = {"sha256": old_hash}
    return current, sources, manifest_hash, changes


def package_hashes():
    return {str(path.relative_to(STAGE)): digest(path) for path in sorted((STAGE / "Content").rglob("*"))
            if path.is_file() and path.suffix.lower() in (".uasset", ".umap", ".uexp", ".ubulk")}


def actor_state(u, actor):
    rotation = actor.get_actor_rotation()
    row = {"path": actor.get_path_name(), "class": actor.get_class().get_name(),
           "location": list(actor.get_actor_location().to_tuple()),
           "rotation": [rotation.pitch, rotation.yaw, rotation.roll],
           "scale": list(actor.get_actor_scale3d().to_tuple())}
    if isinstance(actor, u.StaticMeshActor):
        comp = actor.get_component_by_class(u.StaticMeshComponent)
        row.update(mesh=comp.get_editor_property("static_mesh").get_path_name(),
                   materials=[comp.get_material(i).get_path_name() for i in range(comp.get_num_materials())],
                   cast_shadow=comp.get_editor_property("cast_shadow"),
                   translucency_sort_priority=comp.get_editor_property("translucency_sort_priority"))
    elif isinstance(actor, u.PointLight):
        comp = actor.get_component_by_class(u.PointLightComponent)
        row.update(intensity=comp.get_editor_property("intensity"),
                   attenuation_radius=comp.get_editor_property("attenuation_radius"),
                   volumetric_scattering_intensity=comp.get_editor_property("volumetric_scattering_intensity"))
    elif isinstance(actor, u.NiagaraActor):
        comp = actor.get_component_by_class(u.NiagaraComponent)
        row.update(system=comp.get_asset().get_path_name(), auto_activate=comp.get_editor_property("auto_activate"))
    elif isinstance(actor, u.LevelSequenceActor):
        settings = actor.get_editor_property("playback_settings")
        row.update(sequence=actor.get_sequence().get_path_name(), auto_play=settings.get_editor_property("auto_play"),
                   loop_count=settings.get_editor_property("loop_count").get_editor_property("value"))
    return row


def import_mesh(u, change, material, manifest_hash):
    folder, name = change["asset"].rsplit("/", 1)
    options = u.FbxImportUI()
    for key, value in {"automated_import_should_detect_type": False, "import_mesh": True,
                       "import_as_skeletal": False, "import_materials": False, "import_textures": False,
                       "mesh_type_to_import": u.FBXImportType.FBXIT_STATIC_MESH}.items():
        options.set_editor_property(key, value)
    data = options.get_editor_property("static_mesh_import_data")
    for key, value in {"combine_meshes": True, "auto_generate_collision": False,
                       "generate_lightmap_u_vs": False, "build_nanite": False,
                       "import_uniform_scale": 1.0, "convert_scene": False,
                       "convert_scene_unit": False, "force_front_x_axis": False,
                       "normal_import_method": u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS}.items():
        data.set_editor_property(key, value)
    task = u.AssetImportTask()
    for key, value in {"filename": change["file"], "destination_path": folder, "destination_name": name,
                       "automated": True, "replace_existing": False, "save": False,
                       "options": options, "factory": u.FbxFactory()}.items():
        task.set_editor_property(key, value)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = list(task.get_editor_property("imported_object_paths"))
    require(len(paths) == 1, "Expected one imported mesh")
    mesh = u.EditorAssetLibrary.load_asset(paths[0])
    require(isinstance(mesh, u.StaticMesh) and mesh.get_path_name().split(".")[0] == change["asset"], "Unexpected imported asset")
    require(mesh.get_num_sections(0) == 1 and len(mesh.get_editor_property("static_materials")) == 1, "Expected one material section")
    mesh.set_material(0, material)
    editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    editor.remove_collisions(mesh)
    editor.enable_section_collision(mesh, False, 0, 0)
    for key, value in {"CryoAuthoringVersion": "CryoFitV4", "CryoManifestSHA256": manifest_hash,
                       "CryoRole": change["role"], "CryoModelID": change["model_id"],
                       "CryoSourceSHA256": change["source_sha256"],
                       "CryoAcceptance": "PENDING_MULTIVIEW_FIT_REVIEW"}.items():
        u.EditorAssetLibrary.set_metadata_tag(mesh, key, value)
    bounds = mesh.get_bounds()
    change["native_bounds_cm"] = {"origin": list(bounds.origin.to_tuple()), "extent": list(bounds.box_extent.to_tuple())}
    return mesh


def main(apply=False, manifest_path=None):
    manifest_path = Path(manifest_path or os.environ.get("CRYO_FIT_MANIFEST", OUT / "assembly_fit_v4.json"))
    receipt_path = WORK / ("CryoFitV4Apply.json" if apply else "CryoFitV4DryRun.json")
    report = {"status": "FAILED", "started_utc": datetime.now(timezone.utc).isoformat(), "apply": apply,
              "manifest": str(manifest_path), "errors": [], "changes": []}
    u, allowed_stage = None, False
    try:
        manifest, sources, manifest_hash, changes = prepare(manifest_path)
        report.update(manifest_sha256=manifest_hash, changes=changes, protected_source_files=sources)
        if not apply:
            report["status"] = "DRY_RUN_READY"
            return report
        import unreal as u
        require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve() == STAGE.resolve(),
                "Apply is restricted to isolated CryoStage")
        allowed_stage = True
        require(not u.EditorLevelLibrary.get_pie_worlds(False), "Refusing active PIE")
        before = package_hashes()
        map_relative = "Content\\SpaceSurvival\\CryoComparison\\Maps\\L_CryoComparison.umap"
        map_file = STAGE / map_relative
        backup = WORK / ("pre_fit_v4_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
        backup.mkdir(exist_ok=False)
        shutil.copy2(map_file, backup / map_file.name)
        require(digest(backup / map_file.name) == digest(map_file), "Map recovery copy failed")
        report["map_recovery"] = str(backup / map_file.name)
        world = u.EditorLoadingAndSavingUtils.load_map(MAP)
        require(world is not None, "Map load failed")
        subsystem = u.get_editor_subsystem(u.EditorActorSubsystem)
        actors = {actor.get_actor_label(): actor for actor in subsystem.get_all_level_actors()}
        before_actors = {name: actor_state(u, actor) for name, actor in actors.items()}
        for model in manifest["models"]:
            body = actors[model["id"] + "_Body"].get_component_by_class(u.StaticMeshComponent).get_editor_property("static_mesh")
            body_file = next(row["file"] for row in model["components"] if row["role"] == "body")
            require(u.EditorAssetLibrary.get_metadata_tag(body, "CryoSourceSHA256") == digest(body_file), "Native body source hash mismatch")
        # Validate every destination and every target before importing or swapping.
        for change in changes:
            require(not u.EditorAssetLibrary.does_asset_exist(change["asset"]), "New FitV4 asset already exists")
            require(change["actor"] in actors and isinstance(actors[change["actor"]], u.StaticMeshActor), "Missing addon actor")
            comp = actors[change["actor"]].get_component_by_class(u.StaticMeshComponent)
            require(comp.get_editor_property("static_mesh").get_path_name().startswith(BASE + "/Meshes/"), "Addon mesh outside namespace")
            require(comp.get_num_materials() == 1 and comp.get_material(0).get_path_name().startswith(BASE + "/Materials/"),
                    "Unexpected addon material")
        created = []
        for change in changes:
            comp = actors[change["actor"]].get_component_by_class(u.StaticMeshComponent)
            mesh = import_mesh(u, change, comp.get_material(0), manifest_hash)
            created.append(mesh)
            change["previous_mesh"] = comp.get_editor_property("static_mesh").get_path_name()
            comp.set_static_mesh(mesh)
        after_actors = {actor.get_actor_label(): actor_state(u, actor) for actor in subsystem.get_all_level_actors()}
        expected = json.loads(json.dumps(before_actors))
        for change in changes:
            expected[change["actor"]]["mesh"] = change["asset"] + "." + change["asset"].rsplit("/", 1)[1]
        require(after_actors == expected, "Actor transforms, materials, body or native effects changed beyond addon mesh swaps")
        for path, info in sources.items():
            require(digest(path) == info["sha256"], "Input changed during authoring: " + path)
        for mesh in created:
            require(u.EditorAssetLibrary.save_loaded_asset(mesh, False), "New mesh save failed")
        require(u.EditorLoadingAndSavingUtils.save_map(world, MAP), "Comparison map save failed")
        after = package_hashes()
        changed_existing = [path for path in before if before[path] != after.get(path)]
        require(changed_existing == [map_relative], "An existing package besides the comparison map changed")
        added = sorted(set(after) - set(before))
        expected_added = sorted("Content\\" + change["asset"][len("/Game/"):].replace("/", "\\") + ".uasset" for change in changes)
        require(added == expected_added, "Unexpected new native package files")
        report.update(status="FIT_V4_SAVED_PENDING_MULTIVIEW_REVIEW", changed_existing_packages=changed_existing,
                      added_packages=added, native_before_hashes=before, native_after_hashes=after,
                      unchanged_original_bodies=True, unchanged_materials_lights_niagara_sequence=True)
        return report
    except Exception:
        report["errors"].append(traceback.format_exc())
        if u:
            u.log_error(report["errors"][-1])
        return report
    finally:
        receipt_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("CRYO_FIT_V4_RESULT " + json.dumps({"status": report["status"], "receipt": str(receipt_path)}), flush=True)
        if u and allowed_stage:
            u.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main(False)
