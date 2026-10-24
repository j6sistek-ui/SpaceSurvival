"""Optional stage-only rear-fill redistribution; no added lights or pulse edits.

main(False) writes a diagnostic plan only. main(True), after v4 mesh import,
moves the four existing 40 lm fill RectLights from front-right to rear-right.
All packages except the comparison map must remain byte-identical. No launch.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path
import runpy
import shutil
import traceback

WORK = Path(__file__).resolve().parent
API = runpy.run_path(str(WORK / "upgrade_cryo_fit_unreal.py"))
STAGE, BASE, MAP = (API[name] for name in ("STAGE", "BASE", "MAP"))
require, digest, hashes = (API[name] for name in ("require", "digest", "package_hashes"))
BAYS = dict(zip("ABCD", (-540.0, -180.0, 180.0, 540.0)))


def plan():
    return [{"actor": bay + "_Fill", "old_position_cm": [x + 115.0, 130.0, 150.0],
             "new_position_cm": [x + 115.0, -130.0, 180.0], "look_at_cm": [x, 0.0, 160.0],
             "unchanged_intensity_lm": 40.0, "unchanged_attenuation_radius_cm": 350.0,
             "unchanged_shadow_casting": False}
            for bay, x in BAYS.items()]


def main(apply=False):
    report = {"status": "DRY_RUN_NO_NATIVE_WRITES", "apply": apply,
              "utc": datetime.now(timezone.utc).isoformat(), "plan": plan(), "errors": [],
              "diagnosis": [
                  "Both existing RectLights were on the front (+Y); redistribute only the existing 40 lm fill.",
                  "Breathing InteriorGlow/RimGlow are shadowless omnidirectional point lights, not front-directed spots.",
                  "Keep all eight point lights, existing six-second curves, intensities, phases, positions and radii unchanged.",
                  "Glass, frost, mist and Niagara master materials were authored two-sided; verify live readback on apply/capture.",
                  "Mist cards are planar and can be edge-on from side views; native volumetric fog and camera-facing Niagara provide 360 vapor.",
                  "Niagara sprite material is unlit. Cyan point lights illuminate native volumetric fog, not the unlit sprite artwork.",
                  "Additional light cannot reveal a subject behind an opaque source-mesh wall; review geometry occlusion separately."]}
    u, allowed = None, False
    receipt = WORK / ("CryoFit360Lighting.json" if apply else "CryoFit360LightingPlan.json")
    try:
        if not apply:
            return report
        import unreal as u
        require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve() == STAGE.resolve(),
                "Restricted to isolated D-drive CryoStage")
        allowed = True
        require(not u.EditorLevelLibrary.get_pie_worlds(False), "Refusing active PIE")
        previous = json.loads((WORK / "CryoFitV4Apply.json").read_text(encoding="utf-8"))
        require(previous["status"] == "FIT_V4_SAVED_PENDING_MULTIVIEW_REVIEW", "Run after successful v4 mesh import")
        before_hashes = hashes()
        require(before_hashes == previous["native_after_hashes"], "Native stage differs from the v4 import receipt")
        world = u.EditorLoadingAndSavingUtils.load_map(MAP)
        require(world is not None, "Comparison map load failed")
        subsystem = u.get_editor_subsystem(u.EditorActorSubsystem)
        actors = {actor.get_actor_label(): actor for actor in subsystem.get_all_level_actors()}
        before = {name: API["actor_state"](u, actor) for name, actor in actors.items()}
        report["native_material_sidedness"] = []
        for name in ("M_Glass", "M_Frost", "M_Mist", "M_NiagaraColdMist"):
            mat = u.EditorAssetLibrary.load_asset(BASE + "/Materials/" + name)
            require(mat is not None and mat.get_editor_property("two_sided"), "Expected a two-sided material: " + name)
            report["native_material_sidedness"].append({"asset": mat.get_path_name(), "two_sided": True})
        for row in report["plan"]:
            actor = actors.get(row["actor"])
            require(actor is not None and isinstance(actor, u.RectLight), "Expected existing fill RectLight")
            position = actor.get_actor_location()
            require(all(abs(a - b) < 0.01 for a, b in zip(position.to_tuple(), row["old_position_cm"])), "Fill position differs from expected baseline")
            comp = actor.get_component_by_class(u.RectLightComponent)
            for prop, expected in (("intensity", 40.0), ("attenuation_radius", 350.0), ("cast_shadows", False)):
                actual = comp.get_editor_property(prop)
                require(actual == expected, "Fill setting differs from baseline: " + prop)
        map_file = STAGE / "Content/SpaceSurvival/CryoComparison/Maps/L_CryoComparison.umap"
        backup = WORK / ("pre_360_fill_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
        backup.mkdir(exist_ok=False)
        shutil.copy2(map_file, backup / map_file.name)
        require(digest(map_file) == digest(backup / map_file.name), "Map recovery hash mismatch")
        report["map_recovery"] = str(backup / map_file.name)
        expected_states = json.loads(json.dumps(before))
        for row in report["plan"]:
            position, target = row["new_position_cm"], row["look_at_cm"]
            delta = [target[i] - position[i] for i in range(3)]
            yaw = math.degrees(math.atan2(delta[1], delta[0]))
            pitch = math.degrees(math.atan2(delta[2], math.hypot(delta[0], delta[1])))
            actor = actors[row["actor"]]
            actor.set_actor_location_and_rotation(u.Vector(*position), u.Rotator(pitch=pitch, yaw=yaw), False, True)
            # Native floats may round; read the stored pose into the exact expected change.
            new_state = API["actor_state"](u, actor)
            expected_states[row["actor"]]["location"] = new_state["location"]
            expected_states[row["actor"]]["rotation"] = new_state["rotation"]
            require(all(abs(a - b) < 0.01 for a, b in zip(new_state["location"], position)), "Rear fill placement failed")
            row["rotation_pitch_yaw_roll"] = new_state["rotation"]
        after = {actor.get_actor_label(): API["actor_state"](u, actor) for actor in subsystem.get_all_level_actors()}
        require(after == expected_states, "An actor outside the four fill transforms changed")
        require(u.EditorLoadingAndSavingUtils.save_map(world, MAP), "Map save failed")
        after_hashes = hashes()
        changed = [key for key in set(before_hashes) | set(after_hashes) if before_hashes.get(key) != after_hashes.get(key)]
        require(changed == ["Content\\SpaceSurvival\\CryoComparison\\Maps\\L_CryoComparison.umap"], "Unexpected package changed")
        report.update(status="REAR_FILL_SAVED_PENDING_360_REVIEW", native_before_hashes=before_hashes,
                      native_after_hashes=after_hashes, changed_packages=changed,
                      existing_sequence_and_material_packages_unchanged=True,
                      breathing_light_actor_state_unchanged=True, new_lights=0)
        return report
    except Exception:
        report["status"] = "FAILED"
        report["errors"].append(traceback.format_exc())
        if u:
            u.log_error(report["errors"][-1])
        return report
    finally:
        receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("CRYO_360_FILL_RESULT " + json.dumps({"status": report["status"], "receipt": str(receipt)}), flush=True)
        if u and allowed:
            u.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main(False)
