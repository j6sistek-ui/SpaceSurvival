"""Run inside Unreal. Dry-run by default; -SSLiraCopy saves new packages only."""
import hashlib
import json
from pathlib import Path

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
SOURCE = "/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew/Lira"
DESTINATION = "/Game/SpaceSurvival/Licensed/AnimationLibrary/Lira_20261020"
OUT = ROOT / ".agent/local/LiraAnimationLibrary_20261020"
OUT.mkdir(parents=True, exist_ok=True)
APPLY = "-SSLiraCopy" in u.SystemLibrary.get_command_line().split()
assets = u.get_editor_subsystem(u.EditorAssetSubsystem)


def disk(package):
    return ROOT / "Content" / (package.removeprefix("/Game/") + ".uasset")


def digest(package):
    return hashlib.sha256(disk(package).read_bytes()).hexdigest()


def metadata(clip):
    return {
        "duration_seconds": clip.sequence_length,
        "skeleton": clip.get_editor_property("skeleton").get_path_name(),
        "additive_type": str(clip.get_editor_property("additive_anim_type")),
        "root_motion_enabled": clip.get_editor_property("enable_root_motion"),
    }


mesh = u.load_asset(SOURCE + "/Rig/SK_Lira")
assert mesh and mesh.skeleton, "Lira source mesh/skeleton missing"
guard = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
         for p in (ROOT / "Content/SpaceSurvival/Licensed/StationAssets/TripoCrew/Lira").rglob("*.uasset")}
rows = []
for key in ("IMG9447", "IMG9451", "IMG9452"):
    source = SOURCE + "/Role/A_Lira_" + key
    destination = DESTINATION + "/A_Lira_Source_" + key
    clip = u.load_asset(source)
    assert isinstance(clip, u.AnimSequence), source
    assert clip.get_editor_property("skeleton") == mesh.skeleton, source
    assert not assets.does_asset_exist(destination), "Destination already exists; inspect instead of overwriting"
    rows.append({"source": source, "source_sha256": digest(source), "destination": destination,
                 "metadata": metadata(clip)})
plan = {"operation": "Create traceable native animation copies without retargeting or source edits",
        "source_mesh": mesh.get_path_name(), "copies": rows, "apply": APPLY}
receipt = OUT / ("Applied.json" if APPLY else "DryRun.json")
assert not receipt.exists(), "Receipt exists; inspect it before retrying"
if APPLY:
    assert (OUT / "DryRun.json").exists(), "Run without -SSLiraCopy first"
    dry = json.loads((OUT / "DryRun.json").read_text(encoding="utf-8"))
    assert dry["copies"] == rows, "Sources/destinations changed since dry-run"
    for row in rows:
        copied = assets.duplicate_asset(row["source"], row["destination"])
        assert copied and metadata(copied) == row["metadata"], row
        assets.set_metadata_tag(copied, "SS.SourcePackage", row["source"])
        assets.set_metadata_tag(copied, "SS.SourceSHA256", row["source_sha256"])
        assets.set_metadata_tag(copied, "SS.ReuseIntent", "Preserved source for future zero-G dance retargeting; contacts/joins unvalidated")
        assert assets.save_loaded_asset(copied, False), row
        row["copy_sha256"] = digest(row["destination"])
        row["saved_bytes"] = disk(row["destination"]).stat().st_size
plan["source_files_unchanged"] = all(
    hashlib.sha256(Path(path).read_bytes()).hexdigest() == value for path, value in guard.items()
)
plan["protected_source_files"] = len(guard)
assert plan["source_files_unchanged"]
receipt.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
print("LIRA_ANIMATION_COPY", "applied" if APPLY else "dry-run", len(rows), flush=True)
