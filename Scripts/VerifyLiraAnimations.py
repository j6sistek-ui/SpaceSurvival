"""Fresh-editor readback of saved Lira copies; no asset or map writes."""
import hashlib
import json
import math
import traceback
from pathlib import Path

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
OUT = ROOT / ".agent/local/LiraAnimationLibrary_20261020"
receipt = OUT / "FreshReload.json"
assert not receipt.exists(), "Keep earlier evidence; use a new review directory for another trial"
report = {"copies": [], "errors": [], "assets_saved": False}


def coordinates(v):
    return [v.x, v.y, v.z]


def disk(package):
    return ROOT / "Content" / (package.removeprefix("/Game/") + ".uasset")


try:
    applied = json.loads((OUT / "Applied.json").read_text(encoding="utf-8"))
    assets = u.get_editor_subsystem(u.EditorAssetSubsystem)
    pose_tools = u.AnimPoseExtensions
    options = u.AnimPoseEvaluationOptions()
    for row in applied["copies"]:
        source, copy = u.load_asset(row["source"]), u.load_asset(row["destination"])
        assert isinstance(copy, u.AnimSequence) and isinstance(source, u.AnimSequence)
        assert copy.sequence_length == source.sequence_length
        assert copy.get_editor_property("skeleton") == source.get_editor_property("skeleton")
        assert assets.get_metadata_tag(copy, "SS.SourcePackage") == row["source"]
        assert assets.get_metadata_tag(copy, "SS.SourceSHA256") == row["source_sha256"]
        assert hashlib.sha256(disk(row["source"]).read_bytes()).hexdigest() == row["source_sha256"]
        assert hashlib.sha256(disk(row["destination"]).read_bytes()).hexdigest() == row["copy_sha256"]
        max_position = max_rotation = max_scale = 0.0
        comparisons = 0
        for i in range(25):
            seconds = copy.sequence_length * i / 24
            original = pose_tools.get_anim_pose_at_time(source, seconds, options)
            duplicate = pose_tools.get_anim_pose_at_time(copy, seconds, options)
            names = pose_tools.get_bone_names(original)
            assert list(names) == list(pose_tools.get_bone_names(duplicate)) and names
            for name in names:
                a = pose_tools.get_bone_pose(original, name, u.AnimPoseSpaces.WORLD)
                b = pose_tools.get_bone_pose(duplicate, name, u.AnimPoseSpaces.WORLD)
                max_position = max(max_position, math.dist(coordinates(a.translation), coordinates(b.translation)))
                max_scale = max(max_scale, math.dist(coordinates(a.scale3d), coordinates(b.scale3d)))
                qa = [a.rotation.x, a.rotation.y, a.rotation.z, a.rotation.w]
                qb = [b.rotation.x, b.rotation.y, b.rotation.z, b.rotation.w]
                max_rotation = max(max_rotation, min(math.dist(qa, qb), math.dist(qa, [-v for v in qb])))
                comparisons += 1
        assert max_position < 1e-5 and max_rotation < 1e-6 and max_scale < 1e-6
        report["copies"].append({"asset": copy.get_path_name(), "duration_seconds": copy.sequence_length,
                                 "bone_comparisons": comparisons, "position_error_cm": max_position,
                                 "quaternion_error": max_rotation, "scale_error": max_scale})
    registry = u.AssetRegistryHelpers.get_asset_registry()
    report["lira_mesh_referencers"] = [str(p) for p in registry.get_referencers(
        "/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew/Lira/Rig/SK_Lira",
        u.AssetRegistryDependencyOptions())]
    report["success"] = len(report["copies"]) == 3
except Exception:
    report["errors"].append(traceback.format_exc())
    report["success"] = False
    u.log_error(report["errors"][-1])
finally:
    receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("LIRA_FRESH_RELOAD", report.get("success"), flush=True)
    u.SystemLibrary.quit_editor()
