"""Geometry-only v5_3 -> v5_4 patch, restricted to isolated CryoStage.

No engine launch or material changes. Existing DisplayV5 meshes are backed up
and reimported. If D's housing changes, import a new DisplayV5 mesh and rebind
only D_Housing in the map, preserving the previous housing package. Every run
writes a new receipt. Canonical apply promotion occurs only after all guards.
"""
from __future__ import annotations

from copy import deepcopy
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import runpy
import shutil
import traceback

WORK = Path(__file__).resolve().parent
API = runpy.run_path(str(WORK / "apply_cryo_displays_v5.py"))
REFINE = runpy.run_path(str(WORK / "refine_cryo_displays_v5.py"))
FIT = API["FIT"]
BASE, STAGE, OUT, MAP = (API[key] for key in ("BASE", "STAGE", "OUT", "MAP"))
require, digest, hashes = (API[key] for key in ("require", "digest", "hashes"))
MANIFEST = OUT / "assembly_displays_v5_4.json"
PREVIOUS = OUT / "assembly_displays_v5_3.json"
AUDIT = WORK / "cryo-display-v5_4-independent-audit.json"
CANONICAL = WORK / "CryoDisplayV5Apply.json"
ALLOWED_ROLES = {"console_backing", "console_glass", "console", "console_frame", "status", "display_glass", "housing"}
ALLOWED_ACTORS = {f"{bay}_Console_{index}_{part}" for bay in "BC" for index in (1, 2)
                  for part in ("Backing", "Glass", "HUD", "Frame")} | {"D_Housing", "D_Status", "D_Status_Glass"}


def prepare():
    original = json.loads(CANONICAL.read_text(encoding="utf-8"))
    require(original["status"] == "DISPLAY_V5_SAVED_PENDING_VISUAL_REVIEW", "Expected successful canonical v5 apply")
    require(Path(original["manifest"]).resolve() == PREVIOUS.resolve() and original.get("revision") == "v5_3",
            "Patch only advances the current v5_3 stage")
    require(digest(PREVIOUS) == original["manifest_sha256"], "v5_3 manifest changed")
    before = hashes()
    require(before == original["native_after_hashes"], "Stage differs from canonical v5_3 apply")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8-sig"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    require(audit["status"] == "PASS_STATIC_GEOMETRY_PENDING_NATIVE_VISUAL_REVIEW" and audit["manifest_sha256"] == digest(MANIFEST),
            "Final v5_4 static geometry audit has not passed for this manifest")
    require(not audit.get("errors") and audit.get("protected_inputs_unchanged"), "Geometry audit reported an error or changed protected input")
    require([m["id"] for m in manifest["models"]] == list("ABCD"), "Expected all four assemblies")
    require(manifest["shared"] == previous["shared"], "Shared artwork changed")
    old_changes = {row["actor"]: row for row in original["changes"]}
    sources = deepcopy(original["protected_source_files"])
    sources[str(MANIFEST)] = {"sha256": digest(MANIFEST)}
    sources[str(AUDIT)] = {"sha256": digest(AUDIT)}
    changes = []
    for model, old in zip(manifest["models"], previous["models"]):
        for key in ("source", "textures", "height_cm"):
            require(model[key] == old[key], "Body source/texture/scale changed")
        require(digest(model["source"]) == old["source_sha256"], "Original GLB changed")
        old_rows = {row["name"]: row for row in old["components"]}
        require(len(model["components"]) == 21 and set(old_rows) == {r["name"] for r in model["components"]}, "Component set changed")
        for row in model["components"]:
            prior = old_rows[row["name"]]
            require(row["role"] == prior["role"], "Existing role changed")
            path = Path(row["file"]).resolve()
            require(path.is_relative_to(WORK.parent) and path.suffix.lower() == ".obj", "Only D-drive OBJ sources allowed")
            new_sha, old_sha = digest(path), digest(prior["file"])
            sources[str(path)] = {"sha256": new_sha}
            if new_sha == old_sha:
                continue
            actor = model["id"] + "_" + row["name"]
            require(row["role"] in ALLOWED_ROLES and actor in ALLOWED_ACTORS,
                    "Non-display or unplanned geometry changed: " + actor)
            new_asset = actor not in old_changes
            if new_asset:
                require(actor == "D_Housing" and row["role"] == "housing", "Only D housing may require a new native mesh")
                asset = BASE + "/Meshes/DisplayV5/D/SM_D_Housing_DisplaysV5"
            else:
                prior_change = old_changes[actor]
                require(prior_change["source_sha256"] == old_sha, "Canonical source provenance differs")
                asset = prior_change["asset"]
            require(asset.startswith(BASE + "/Meshes/DisplayV5/"), "Destination outside new DisplayV5 namespace")
            changes.append({"actor": actor, "model_id": model["id"], "name": row["name"], "role": row["role"],
                            "asset": asset, "new_native_asset": new_asset, "file": str(path), "source_sha256": new_sha,
                            "previous_file": prior["file"], "previous_source_sha256": old_sha,
                            "package": API["package_path"](asset)})
    require(changes, "No correction geometry found")
    require(all(digest(path) == info["sha256"] for path, info in sources.items()), "Protected source input changed")
    for row in changes:
        if row["new_native_asset"]:
            require(row["package"] not in before, "New housing destination already exists")
        else:
            require(row["package"] in original["added_packages"], "Refusing mutation of a pre-v5 package")
    return original, manifest, audit, changes, sources, before


def main(apply=False):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_" + str(os.getpid())
    receipt = WORK / (("CryoDisplayV5Patch4_" if apply else "CryoDisplayV5Patch4Plan_") + stamp + ".json")
    report = {"status": "FAILED", "apply": apply, "utc": datetime.now(timezone.utc).isoformat(), "errors": [],
              "manifest": str(MANIFEST), "geometry_audit": str(AUDIT), "receipt": str(receipt),
              "limits": ["Geometry fit still requires native closeup review after import.",
                         "No material, frost, Niagara, sequence, light, owner or config behavior changes."]}
    u, allowed = None, False
    try:
        require(not receipt.exists(), "Receipt already exists")
        original, manifest, audit, changes, sources, before = prepare()
        manifest_hash = digest(MANIFEST)
        new_rows = [row for row in changes if row["new_native_asset"]]
        expected_added = sorted(row["package"] for row in new_rows)
        expected_changed = sorted([row["package"] for row in changes if not row["new_native_asset"]]
                                  + ([API["MAP_RELATIVE"]] if new_rows else []))
        report.update(manifest_sha256=manifest_hash, geometry_audit_sha256=digest(AUDIT), changes=changes,
                      native_before_hashes=before, planned_changed_packages=expected_changed, planned_added_packages=expected_added)
        if not apply:
            report["status"] = "DRY_RUN_READY"
            return report
        import unreal as u
        require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve() == STAGE.resolve(), "Only isolated CryoStage is allowed")
        require(not u.EditorLevelLibrary.get_pie_worlds(False), "Refusing active PIE")
        allowed = True
        world = u.EditorLoadingAndSavingUtils.load_map(MAP)
        require(world is not None, "Owned map load failed")
        subsystem = u.get_editor_subsystem(u.EditorActorSubsystem)
        actors = {actor.get_actor_label(): actor for actor in subsystem.get_all_level_actors()}
        before_states = {name: FIT["actor_state"](u, actor) for name, actor in actors.items()}
        materials = {}
        for row in changes:
            actor = actors.get(row["actor"])
            require(isinstance(actor, u.StaticMeshActor), "Expected existing display actor")
            comp = actor.get_component_by_class(u.StaticMeshComponent)
            old_mesh = comp.get_editor_property("static_mesh")
            require(old_mesh and comp.get_num_materials() == 1, "Expected one material slot")
            require(u.EditorAssetLibrary.get_metadata_tag(old_mesh, "CryoSourceSHA256") == row["previous_source_sha256"],
                    "Actual native mesh source differs: " + row["actor"])
            if not row["new_native_asset"]:
                require(old_mesh.get_path_name().split(".")[0] == row["asset"], "Actor mesh differs from canonical apply")
            else:
                require(not u.EditorAssetLibrary.does_asset_exist(row["asset"]), "New housing asset exists")
            material = comp.get_material(0)
            require(material and material.get_path_name().startswith(BASE + "/Materials/"), "Unexpected display material")
            materials[row["actor"]] = material
            row.update(previous_native_mesh=old_mesh.get_path_name(), material=material.get_path_name())
        backup = WORK / ("pre_display_v5_4_" + stamp)
        backup.mkdir(exist_ok=False)
        archived = backup / CANONICAL.name
        shutil.copy2(CANONICAL, archived)
        require(digest(archived) == digest(CANONICAL), "Canonical apply archive differs")
        report.update(archived_apply=str(archived), archived_apply_sha256=digest(archived), backup_directory=str(backup))
        for relative in expected_changed:
            dest = backup / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(STAGE / relative, dest)
            require(digest(dest) == before[relative], "Package recovery copy differs")
        saved = []
        for row in changes:
            if row["new_native_asset"]:
                mesh = FIT["import_mesh"](u, row, materials[row["actor"]], manifest_hash)
                actors[row["actor"]].get_component_by_class(u.StaticMeshComponent).set_static_mesh(mesh)
            else:
                mesh = REFINE["reimport_mesh"](u, row, materials[row["actor"]], manifest_hash)
            u.EditorAssetLibrary.set_metadata_tag(mesh, "CryoAuthoringVersion", "CryoVectorDisplaysV5_4")
            u.EditorAssetLibrary.set_metadata_tag(mesh, "CryoAcceptance", "PENDING_CORRECTED_NATIVE_SCREEN_FIT_REVIEW")
            bounds = mesh.get_bounds()
            row["native_bounds_cm"] = {"origin": list(bounds.origin.to_tuple()), "extent": list(bounds.box_extent.to_tuple())}
            saved.append(mesh)
        after_states = {actor.get_actor_label(): FIT["actor_state"](u, actor) for actor in subsystem.get_all_level_actors()}
        expected_states = deepcopy(before_states)
        for row in new_rows:
            expected_states[row["actor"]]["mesh"] = row["asset"] + "." + row["asset"].rsplit("/", 1)[-1]
        require(after_states == expected_states, "Actor transforms, material slots or native effects changed unexpectedly")
        for mesh in saved:
            require(u.EditorAssetLibrary.save_loaded_asset(mesh, False), "Display mesh save failed")
        if new_rows:
            require(u.EditorLoadingAndSavingUtils.save_map(world, MAP), "Owned map housing rebind save failed")
        after = hashes()
        changed = sorted(path for path in before if before[path] != after.get(path))
        added = sorted(set(after) - set(before))
        require(changed == expected_changed and added == expected_added, "Unexpected native package change")
        require(all(digest(path) == info["sha256"] for path, info in sources.items()), "Protected source changed during apply")
        material_keys = [key for key in before if "\\Materials\\" in key]
        require(all(before[key] == after[key] for key in material_keys), "A material package changed")
        baseline_changed = sorted(key for key in original["native_before_hashes"] if original["native_before_hashes"][key] != after.get(key))
        require(baseline_changed == [API["MAP_RELATIVE"]], "A protected pre-v5 package beyond the owned map changed")
        report.update(status="DISPLAY_V5_4_GEOMETRY_SAVED_PENDING_NATIVE_REVIEW", native_after_hashes=after,
                      changed_packages=changed, added_packages=added, materials_unchanged=True,
                      pre_v5_packages_unchanged_except_owned_map=True, unchanged_actor_transforms_effects_material_bindings=True,
                      protected_source_files=sources, canonical_receipt_promoted=True)
        canonical = deepcopy(original)
        deltas = {row["actor"]: row for row in changes}
        final_rows = {model["id"] + "_" + row["name"]: row for model in manifest["models"] for row in model["components"]}
        for row in canonical["changes"]:
            current = final_rows[row["actor"]]
            row.update(file=current["file"], source_sha256=digest(current["file"]))
            if row["actor"] in deltas:
                row["native_bounds_cm"] = deltas[row["actor"]]["native_bounds_cm"]
        for row in new_rows:
            canonical["changes"].append({**row, "new_actor": False, "previous_mesh": row["previous_native_mesh"]})
            comp = actors[row["actor"]].get_component_by_class(u.StaticMeshComponent)
            canonical["role_bindings"].append({"actor": row["actor"], "role": row["role"], "material": row["material"].split(".")[0],
                                               "previous_material": row["material"], "readback_material": comp.get_material(0).get_path_name(),
                                               "readback_sort_priority": int(comp.get_editor_property("translucency_sort_priority"))})
        canonical.update(utc=datetime.now(timezone.utc).isoformat(), manifest=str(MANIFEST), manifest_sha256=manifest_hash,
                         revision="v5_4", native_after_hashes=after, protected_source_files=sources,
                         added_packages=sorted(set(after) - set(original["native_before_hashes"])),
                         changed_component_counts=dict(Counter(row["model_id"] for row in canonical["changes"])),
                         latest_archived_apply=str(archived), latest_archived_apply_sha256=digest(archived),
                         latest_geometry_patch_receipt=str(receipt), latest_geometry_audit=str(AUDIT), latest_geometry_audit_sha256=digest(AUDIT))
        canonical["saved_assets"] = sorted(set(canonical["saved_assets"]) | {mesh.get_path_name() for mesh in saved})
        report["canonical_receipt"] = str(CANONICAL)
        receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        canonical.setdefault("geometry_patch_receipts", []).append({"path": str(receipt), "sha256": digest(receipt)})
        temporary = CANONICAL.with_name("CryoDisplayV5Apply_next_" + stamp + ".json")
        temporary.write_text(json.dumps(canonical, indent=2) + "\n", encoding="utf-8")
        temporary.replace(CANONICAL)
        return report
    except Exception:
        report["status"] = "FAILED"
        report["errors"].append(traceback.format_exc())
        if u:
            u.log_error(report["errors"][-1])
        return report
    finally:
        receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("CRYO_DISPLAY_V5_4_RESULT " + json.dumps({"status": report["status"], "receipt": str(receipt)}), flush=True)
        if u and allowed:
            u.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main(False)
