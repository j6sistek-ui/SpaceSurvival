"""New shared inward/downward jet for the curved chamber windows; stage only.

Default dry run. Creates NS_CryoFreezeJet_Contained, replaces only the four
interaction actors' JetSystem references and saves only that system + map.
Original jet, materials, nozzle transforms, timing and original bodies persist.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import runpy
import shutil
import traceback

WORK = Path(__file__).resolve().parent
GUARD = runpy.run_path(str(WORK / "upgrade_cryo_fit_unreal.py"))
FX = runpy.run_path(str(WORK / "author_cryo_freeze_fx.py"))
STAGE, BASE, MAP = (GUARD[key] for key in ("STAGE", "BASE", "MAP"))
require, digest, hashes = (GUARD[key] for key in ("require", "digest", "package_hashes"))
NAME = "NS_CryoFreezeJet_Contained"
ASSET = BASE + "/FX/" + NAME
MAP_FILE = "Content\\SpaceSurvival\\CryoComparison\\Maps\\L_CryoComparison.umap"
ASSET_FILE = "Content\\SpaceSurvival\\CryoComparison\\FX\\" + NAME + ".uasset"


def main(apply=False):
    report = {"status": "DRY_RUN_READY", "apply": apply, "utc": datetime.now(timezone.utc).isoformat(),
              "asset": ASSET, "errors": [], "materials": [],
              "diagnosis": "A right glass front decreases from nozzleY68.3cm to61.3cm after25cm drop; straight jet intersects it.",
              "recipe": {"velocity_min_cm_s": [-3, -85, -140], "velocity_max_cm_s": [3, -75, -110],
                         "sprite_size_cm": [10, 18], "all_four_same_system": True,
                         "nozzle_world_origins_unchanged": True},
              "limits": ["Actual-game jet and full-frost images must verify containment."]}
    receipt = WORK / ("CryoJetContainment.json" if apply else "CryoJetContainmentPlan.json")
    u, allowed = None, False
    try:
        if not apply:
            return report
        import unreal as u
        require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve() == STAGE.resolve(), "Stage only")
        allowed = True
        require(not u.EditorAssetLibrary.does_asset_exist(ASSET), "Contained jet already exists; refusing overwrite")
        require(hasattr(u, "FXConverterUtilitiesLibrary"), "Converter authoring plugin unavailable")
        before = hashes()
        world = u.EditorLoadingAndSavingUtils.load_map(MAP)
        require(world is not None, "Map load failed")
        actors = [a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
                  if isinstance(a, u.SSCryoChamber)]
        require(len(actors) == 4, "Expected four native interaction actors")
        poses = {}
        for actor in actors:
            old = actor.get_editor_property("jet_system")
            require(old and old.get_path_name().split(".")[0] == BASE + "/FX/NS_CryoFreezeJet", "Unexpected original jet binding")
            poses[actor.get_actor_label()] = [list(actor.get_editor_property(key).get_world_location().to_tuple())
                                            for key in ("left_nozzle", "right_nozzle")]
        material = u.EditorAssetLibrary.load_asset(BASE + "/Materials/M_NiagaraFreezeJet")
        require(material and not material.get_editor_property("disable_depth_test"), "Jet material unexpectedly disables depth testing")
        report["material_depth_test_enabled"] = True
        backup = WORK / ("pre_inward_jet_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
        backup.mkdir(exist_ok=False)
        shutil.copy2(STAGE / MAP_FILE, backup / "L_CryoComparison.umap")
        require(digest(backup / "L_CryoComparison.umap") == before[MAP_FILE], "Map recovery hash failed")
        report["map_recovery"] = str(backup / "L_CryoComparison.umap")
        system = FX["jet_system"](u, material, report, NAME, (-3.0, -85.0, -140.0), (3.0, -75.0, -110.0), (10.0, 18.0))
        for actor in actors:
            actor.set_editor_property("jet_system", system)
            after_pose = [list(actor.get_editor_property(key).get_world_location().to_tuple())
                          for key in ("left_nozzle", "right_nozzle")]
            require(after_pose == poses[actor.get_actor_label()], "Nozzle origin changed")
        require(u.EditorLoadingAndSavingUtils.save_map(world, MAP), "Contained jet map binding save failed")
        after = hashes()
        changed = sorted(key for key in before if before[key] != after.get(key))
        added = sorted(set(after) - set(before))
        require(changed == [MAP_FILE] and added == [ASSET_FILE], "Unexpected package mutation")
        report.update(status="INWARD_JET_SAVED_PENDING_VISUAL_REVIEW", native_before_hashes=before, native_after_hashes=after,
                      changed_packages=changed, added_packages=added, nozzle_origins_cm=poses)
        return report
    except Exception:
        report["status"] = "FAILED"
        report["errors"].append(traceback.format_exc())
        if u:
            u.log_error(report["errors"][-1])
        return report
    finally:
        receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("CRYO_JET_CONTAINMENT_RESULT " + json.dumps({"status": report["status"], "receipt": str(receipt)}), flush=True)
        if u and allowed:
            u.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main(False)
