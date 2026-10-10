"""Import the measured four-cue combat palette into a new private derivative folder.

Lead runs this inside Unreal after PrepareCombatAudioPolish.py. --dry-run is the
default: append -SSAuthorCombatAudio on the Unreal command line to create assets.
Existing differing assets fail closed; original licensed role sounds are preserved.
"""
from pathlib import Path
import hashlib
import json

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".agent/local/CombatAudioPolish"
DEST = "/Game/SpaceSurvival/Licensed/Audio/CombatPolish1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    prepared = json.loads((OUT / "Preparation.json").read_text(encoding="utf-8"))
    author = "-SSAuthorCombatAudio" in u.SystemLibrary.get_command_line().split()
    library = u.EditorAssetLibrary
    tools = u.AssetToolsHelpers.get_asset_tools()
    rows = []
    # Verify all inputs and all existing destinations before any mutation.
    for name, record in prepared["outputs"].items():
        source = ROOT / record["wav"]
        if sha(source) != record["sha256"] or record["clipped_samples"] != 0:
            raise RuntimeError(f"Changed/unverified audio source: {source}")
        path = f"{DEST}/{name}"
        existing = library.load_asset(path) if library.does_asset_exist(path) else None
        if existing and (not isinstance(existing, u.SoundWave) or
                         library.get_metadata_tag(existing, "SSCombatAudioSourceSHA256") != record["sha256"]):
            raise RuntimeError(f"Existing derivative differs; preserve and reconcile before import: {path}")
        rows.append({"role": name, "path": path, "source": str(source), "sha256": record["sha256"],
                     "action": "reuse" if existing else "import", "expected_seconds": record["seconds"]})
    if author:
        library.make_directory(DEST)
        for row in rows:
            if row["action"] == "import":
                task = u.AssetImportTask()
                for key, value in {"filename": row["source"], "destination_path": DEST,
                                   "destination_name": row["role"], "automated": True,
                                   "replace_existing": False, "save": False}.items():
                    task.set_editor_property(key, value)
                tools.import_asset_tasks([task])
            sound = library.load_asset(row["path"])
            if not isinstance(sound, u.SoundWave):
                raise RuntimeError(f"Imported role did not resolve as SoundWave: {row['path']}")
            sound.set_editor_property("looping", False)
            library.set_metadata_tag(sound, "SSCombatAudioSourceSHA256", row["sha256"])
            library.set_metadata_tag(sound, "SSCombatAudioRecipe", prepared["recipe"])
            if not library.save_loaded_asset(sound):
                raise RuntimeError(f"Failed to save private derivative: {row['path']}")
            row["duration"] = sound.get_editor_property("duration")
            if abs(row["duration"] - row["expected_seconds"]) > .01:
                raise RuntimeError(f"Imported duration changed: {row['path']}")
    report = {"status": "AUTHORED_REQUIRES_LISTENING" if author else "DRY_RUN_NO_ASSET_WRITES",
              "engine": u.SystemLibrary.get_engine_version(), "roles": rows,
              "preparation_sha256": sha(OUT / "Preparation.json"),
              "limits": "Native import/duration/hash checks do not establish game mix or listening quality."}
    filename = "UnrealAuthoring.json" if author else "UnrealDryRun.json"
    (OUT / filename).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    u.log("COMBAT_AUDIO_POLISH " + json.dumps(report))


if __name__ == "__main__":
    main()
