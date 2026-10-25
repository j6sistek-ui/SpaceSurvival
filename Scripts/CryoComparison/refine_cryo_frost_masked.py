"""Make the owned freeze master depth-writing; default dry run, no engine launch.

Only M_FrostFreeze is saved. Its existing FreezeAmount alpha blend feeds the
engine DitherTemporalAA function and OpacityMask. Full freeze has complete
coverage and depth, preventing translucent panes from sorting through it.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import runpy
import shutil
import traceback

WORK = Path(__file__).resolve().parent
API = runpy.run_path(str(WORK / "author_cryo_unreal.py"))
GUARD = runpy.run_path(str(WORK / "upgrade_cryo_fit_unreal.py"))
STAGE, BASE = GUARD["STAGE"], GUARD["BASE"]
require, digest, hashes = GUARD["require"], GUARD["digest"], GUARD["package_hashes"]
ASSET = BASE + "/Materials/M_FrostFreeze"
PACKAGE = "Content\\SpaceSurvival\\CryoComparison\\Materials\\M_FrostFreeze.uasset"
FUNCTION = "/Engine/Functions/Engine_MaterialFunctions02/Utility/DitherTemporalAA.DitherTemporalAA"


def main(apply=False):
    report = {"status": "DRY_RUN_READY", "apply": apply, "utc": datetime.now(timezone.utc).isoformat(),
              "asset": ASSET, "function": FUNCTION, "materials": [], "errors": [],
              "plan": "Preserve existing opacity blend; connect through native DitherTemporalAA to OpacityMask, set Masked, retain two-sided.",
              "limits": ["Visual acceptance requires actual-game normal and fully frozen views.",
                         "Original M_Frost, separate translucent glass and all other assets remain unchanged."]}
    receipt = WORK / ("CryoFreezeMasked.json" if apply else "CryoFreezeMaskedPlan.json")
    u, allowed = None, False
    try:
        if not apply:
            return report
        import unreal as u
        require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve() == STAGE.resolve(),
                "Restricted to isolated CryoStage")
        allowed = True
        before = hashes()
        previous = json.loads((WORK / "CryoFreezeFX.json").read_text(encoding="utf-8"))
        require(previous["status"] == "FREEZE_MATERIAL_AND_JET_SAVED_PENDING_INTERACTION_RUNTIME"
                and before.get(PACKAGE) == previous["native_after_hashes"].get(PACKAGE), "Freeze master differs from authored baseline")
        mat = u.EditorAssetLibrary.load_asset(ASSET)
        require(mat and mat.get_editor_property("blend_mode") == u.BlendMode.BLEND_TRANSLUCENT, "Expected translucent freeze master")
        require(mat.get_editor_property("two_sided"), "Expected shared two-sided windows")
        function = u.EditorAssetLibrary.load_asset(FUNCTION)
        require(function is not None, "Installed DitherTemporalAA function missing")
        edit = u.MaterialEditingLibrary
        alpha = edit.get_material_property_input_node(mat, u.MaterialProperty.MP_OPACITY)
        alpha_output = edit.get_material_property_input_node_output_name(mat, u.MaterialProperty.MP_OPACITY)
        require(alpha is not None, "Existing freeze opacity blend missing")
        backup = WORK / ("pre_masked_frost_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
        backup.mkdir(exist_ok=False)
        shutil.copy2(STAGE / PACKAGE, backup / "M_FrostFreeze.uasset")
        require(digest(backup / "M_FrostFreeze.uasset") == before[PACKAGE], "Frost recovery hash differs")
        report["recovery_asset"] = str(backup / "M_FrostFreeze.uasset")
        author = API["Author"](u, {}, "cryo-depth-writing-freeze-v2", report)
        dither = author.node(mat, "MaterialExpressionMaterialFunctionCall", material_function=function)
        inputs = [str(name) for name in edit.get_material_expression_input_names(dither)]
        require("Alpha Threshold" in inputs, "Dither function inputs did not initialize: " + str(inputs))
        author.wire(alpha, dither, "Alpha Threshold", alpha_output)
        author.prop(dither, "MP_OPACITY_MASK")
        mat.set_editor_property("blend_mode", u.BlendMode.BLEND_MASKED)
        mat.set_editor_property("opacity_mask_clip_value", .3333333)
        author.compile(mat)
        require(u.EditorAssetLibrary.save_loaded_asset(mat, False), "Masked freeze save failed")
        after = hashes()
        changed = sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key))
        require(changed == [PACKAGE], "Unexpected package changed by masked frost refinement")
        report.update(status="MASKED_FREEZE_SAVED_PENDING_VISUAL_REVIEW", native_before_hashes=before,
                      native_after_hashes=after, changed_packages=changed,
                      native_material_sidedness=[{"asset": ASSET, "two_sided": bool(mat.get_editor_property("two_sided")),
                          "blend_mode": str(mat.get_editor_property("blend_mode")),
                          "shading_model": str(mat.get_editor_property("shading_model"))}],
                      freeze_parameter="FreezeAmount", full_freeze_mask=1.0,
                      baseline_alpha_blend_preserved=True, native_depth_writing=True)
        return report
    except Exception:
        report["status"] = "FAILED"
        report["errors"].append(traceback.format_exc())
        if u:
            u.log_error(report["errors"][-1])
        return report
    finally:
        receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("CRYO_FREEZE_MASKED_RESULT " + json.dumps({"status": report["status"], "receipt": str(receipt)}), flush=True)
        if u and allowed:
            u.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main(False)
