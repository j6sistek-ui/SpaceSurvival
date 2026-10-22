"""Guarded local cryo v4 adoption. Dry-run by default; never builds or launches Unreal.

Execution layout is work/adopt_cryo_v4.py beside CryoStage and cryo-repo.
An apply needs exact successful native receipts and the lead's visual acceptance.
The old adoption receipt is immutable. The owner game DLL is never copied.
"""
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import os
import shutil
import stat
import struct
import subprocess
import tempfile

WORK = Path(__file__).resolve().parent
OUT = WORK.parent / "outputs/Cryo_Comparison"
OWNER = Path("C:/Users/j6sis/SpaceSurvival")
REPO = WORK / "cryo-repo"
STAGE = WORK / "CryoStage"
REL = Path("Content/SpaceSurvival/CryoComparison")
SOURCE = STAGE / REL
DESTINATION = OWNER / REL
PLUGIN_REL = Path("Plugins/SSCryoRuntime")
MAP = "Maps/L_CryoComparison.umap"
CONTAINED_JET = "FX/NS_CryoFreezeJet_Contained.uasset"
REAR_CONSOLE_MESHES = {
    "Meshes/FitV4/D/SM_D_Console_1_" + role + "_FitV4.uasset"
    for role in ("Backing", "Glass", "HUD", "Frame")
}
SOURCE_PATHS = {
    ".gitignore", "SpaceSurvival.uproject", "Source/SpaceSurvival/SpaceSurvival.Build.cs",
    "Source/SpaceSurvival/Public/SSOutpostSandbox.h",
    "Source/SpaceSurvival/Private/SSOutpostSandbox.cpp",
    "Source/SpaceSurvival/Private/SSStationOutpost.cpp",
    "Source/SpaceSurvival/Private/SSHUD.cpp",
}
PLUGIN_PATHS = {
    "README.md", "SSCryoRuntime.uplugin",
    "Binaries/Win64/UnrealEditor-SSCryoRuntime.dll",
    "Binaries/Win64/UnrealEditor-SSCryoRuntime.pdb", "Binaries/Win64/UnrealEditor.modules",
    "Source/SSCryoRuntime/SSCryoRuntime.Build.cs",
    "Source/SSCryoRuntime/Private/SSCryoRuntime.cpp",
    "Source/SSCryoRuntime/Private/SSCryoChamber.cpp",
    "Source/SSCryoRuntime/Private/SSCryoPreview.cpp",
    "Source/SSCryoRuntime/Public/SSCryoChamber.h",
    "Source/SSCryoRuntime/Public/SSCryoPreview.h",
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def plain_path(path):
    """Reject junctions/symlinks in every existing ancestor, including Windows ones."""
    path = Path(path).absolute()
    for part in (path, *path.parents):
        if part.exists() or part.is_symlink():
            info = part.lstat()
            require(not stat.S_ISLNK(info.st_mode) and not (
                getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)),
                "Reparse path refused: " + str(part))
    return path


def child(root, relative):
    rel = PurePosixPath(relative.replace("\\", "/"))
    require(not rel.is_absolute() and rel.parts and all(p not in (".", "..") and ":" not in p for p in rel.parts),
            "Unsafe relative path: " + relative)
    path = plain_path(Path(root).joinpath(*rel.parts))
    require(path.is_relative_to(Path(root).absolute()), "Path escaped root")
    return path


def inventory(root, native=False):
    root = plain_path(root)
    require(root.is_dir(), "Missing directory: " + str(root))
    result = {}
    for path in sorted(root.rglob("*")):
        plain_path(path)
        if not path.is_file():
            continue
        if native:
            require(path.suffix in (".uasset", ".umap", ".ubulk", ".uexp"), "Unexpected native file: " + str(path))
        relative = path.relative_to(root).as_posix()
        result[relative] = {"relative_path": relative, "bytes": path.stat().st_size, "sha256": sha(path)}
    return result


def rows_by_path(rows):
    result = {r["relative_path"].replace("\\", "/"): r for r in rows}
    require(len(result) == len(rows), "Duplicate manifest paths")
    return result


def verify_files(root, records):
    for relative, row in records.items():
        path = child(root, relative)
        require(path.is_file() and sha(path) == row["sha256"], "Hash changed: " + str(path))


def preservation_checks():
    donors = read(WORK / "niagara-source-copy.json")
    for row in donors:
        require(sha(child(OWNER / "Content", row["relative_path"])) == row["sha256"], "Donor changed")
    originals = read(WORK / "CryoFinalAuthor.json")["source_files"]
    for path, row in originals.items():
        require(sha(plain_path(path)) == row["sha256"], "Original/import source changed: " + path)
    return {"donor_files_unchanged": len(donors), "original_and_import_hashes_unchanged": len(originals)}


def native_processes():
    command = (
        "@(Get-CimInstance Win32_Process | Where-Object { "
        "$_.Name -in @('UnrealEditor.exe','UnrealEditor-Cmd.exe') -or "
        "($_.Name -eq 'dotnet.exe' -and $_.CommandLine -like '*UnrealBuildTool*') "
        "} | ForEach-Object { [int]$_.ProcessId }) | ConvertTo-Json -Compress"
    )
    result = subprocess.run(["powershell", "-NoProfile", "-Command", command],
                            capture_output=True, text=True, check=True)
    ids = json.loads(result.stdout) if result.stdout.strip() else []
    return ids if isinstance(ids, list) else [ids]


def proof(args, current):
    paths = (args.angles, args.interaction, args.visual_review)
    if not all(paths):
        require(not args.apply, "Apply requires angle, interaction and visual-review receipts")
        return {"accepted": False, "status": "PENDING_NATIVE_AND_LEAD_VISUAL_ACCEPTANCE"}
    angle, interaction, visual = [read(plain_path(p)) for p in paths]
    require(angle.get("status") == "NATIVE_FIT_V4_36_ANGLES_AND_RUNTIME_VERIFIED_PENDING_VISUAL_REVIEW", "Angle proof incomplete")
    require(interaction.get("status") == "FOUR_NATIVE_FREEZE_CYCLES_VERIFIED_PENDING_VISUAL_REVIEW", "Interaction proof incomplete")
    require(angle.get("native_cvar_restoration_verified") and
            angle.get("analysis", {}).get("four_niagara_active_with_nontrivial_bounds"), "Angle runtime proof incomplete")
    require(len(interaction.get("cycles", [])) == 4 and interaction.get("cvar_restored"), "Freeze cycles incomplete")
    expected = {REL.as_posix() + "/" + key: row["sha256"] for key, row in current.items()}
    for receipt, count in ((angle, 36), (interaction, 19)):
        require(receipt.get("capture_command") == "Shot" and
                receipt.get("capture_kind") == "ORDINARY_VIEWPORT_WITH_TSR_HISTORY" and
                receipt.get("actual_viewport_size") == [960, 1200],
                "Final proof requires the reviewed ordinary 960x1200 viewport capture")
        require(not receipt.get("errors") and receipt.get("native_hashes_unchanged") and
                receipt.get("original_source_hashes_unchanged"), "Native preservation proof failed")
        protected = {key.replace("\\", "/"): value for key, value in receipt["protected_native_hashes"].items()}
        observed = {key: value for key, value in protected.items() if key.startswith(REL.as_posix() + "/")}
        require(observed == expected, "Native proof does not match the entire current Stage namespace")
        for relative, digest in protected.items():
            require(sha(child(STAGE, relative)) == digest, "A protected native dependency changed")
        shots = receipt.get("screenshots", [])
        require(len(shots) == count, "Incomplete capture coverage")
        names = ("front", "front_left", "left", "back_left", "back", "back_right", "right", "front_right", "top") if count == 36 else (
            "jet_start", "full_frost", "hold", "restored")
        expected_shots = {(bay, name) for bay in "ABCD" for name in names}
        if count == 19:
            expected_shots.update(("C", name) for name in ("frozen_left", "frozen_back", "frozen_right"))
        require({(row["bay"], row["angle" if count == 36 else "state"]) for row in shots} == expected_shots,
                "Duplicate or missing capture views")
        for shot in shots:
            require(sha(plain_path(shot["png"])) == shot["sha256"], "Capture image changed")
            with Path(shot["png"]).open("rb") as handle:
                header = handle.read(24)
            require(header[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack_from(">II", header, 16) == (960, 1200),
                    "Capture dimensions differ from the reviewed evidence")
    require(angle["protected_native_hashes"] == interaction["protected_native_hashes"], "Native proof runs differ")
    manifest_hash = sha(plain_path(args.manifest))
    require(angle.get("fit_manifest_sha256") == manifest_hash, "Angle fit manifest differs")
    require(visual.get("accepted") is True and visual.get("fit_manifest_sha256") == manifest_hash and
            visual.get("angle_receipt_sha256") == sha(args.angles) and
            visual.get("interaction_receipt_sha256") == sha(args.interaction), "Lead visual acceptance does not match these receipts")
    return {"accepted": True, "status": "NATIVE_AND_LEAD_VISUAL_ACCEPTANCE_VERIFIED",
            "angle_receipt": str(args.angles), "angle_receipt_sha256": sha(args.angles),
            "interaction_receipt": str(args.interaction), "interaction_receipt_sha256": sha(args.interaction),
            "visual_review": str(args.visual_review), "visual_review_sha256": sha(args.visual_review),
            "fit_manifest_sha256": manifest_hash}


def guarded_copy(source, target, expected, previous=None):
    require(sha(source) == expected, "Source changed immediately before copy")
    plain_path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if previous is None:
        require(not target.exists(), "New destination already exists: " + str(target))
        with source.open("rb") as incoming, target.open("xb") as outgoing:
            shutil.copyfileobj(incoming, outgoing)
    else:
        require(sha(target) == previous, "Destination changed before replace: " + str(target))
        with tempfile.NamedTemporaryFile(prefix=target.name + ".cryo-v4-", suffix=".tmp", dir=target.parent, delete=False) as handle:
            pending = Path(handle.name)
            with source.open("rb") as incoming:
                shutil.copyfileobj(incoming, handle)
        require(sha(pending) == expected and sha(target) == previous, "Replacement preflight changed")
        os.replace(pending, target)
    require(sha(target) == expected, "Post-copy hash mismatch: " + str(target))


def main(args):
    for path in (WORK, OUT, OWNER, REPO, STAGE):
        plain_path(path)
    require(WORK.drive.upper() == "D:", "Private work/backup must remain on D:")
    old_receipt = read(args.baseline)
    require(old_receipt.get("apply") is True and str(old_receipt.get("status", "")).startswith("ADOPTED"), "Invalid baseline adoption")
    old = rows_by_path(old_receipt["files"])
    require(len(old) == 125, "Unexpected baseline count")
    installed = inventory(DESTINATION, native=True)
    require(set(installed) == set(old), "Owner namespace contains missing or unknown files")
    verify_files(DESTINATION, old)
    current = inventory(SOURCE, native=True)
    require(set(old).issubset(current), "Stage removed preserved old packages")
    added = sorted(set(current) - set(old))
    changed = sorted(key for key in old if current[key]["sha256"] != old[key]["sha256"])
    require(len(added) == 76 and CONTAINED_JET in added and changed == [MAP],
            "Only 76 new packages including the exact contained jet and the comparison map may change")
    containment_path = WORK / "CryoJetContainment.json"
    containment = read(containment_path)
    require(containment.get("apply") is True and not containment.get("errors") and
            containment.get("status") == "INWARD_JET_SAVED_PENDING_VISUAL_REVIEW",
            "Contained-jet authoring receipt incomplete")
    normalize = lambda values: sorted(value.replace("\\", "/") for value in values)
    require(normalize(containment["added_packages"]) == [REL.as_posix() + "/" + CONTAINED_JET] and
            normalize(containment["changed_packages"]) == [REL.as_posix() + "/" + MAP],
            "Contained-jet authoring scope changed")
    contained_hashes = {key.replace("\\", "/"): value for key, value in containment["native_after_hashes"].items()}
    rear_path = WORK / "CryoRearConsoleApply.json"
    rear = read(rear_path)
    require(rear.get("apply") is True and not rear.get("errors") and
            rear.get("status") == "REAR_CONSOLE_SAVED_PENDING_VISUAL_REVIEW",
            "Rear-console authoring receipt incomplete")
    rear_before = {key.replace("\\", "/"): value for key, value in rear["native_before_hashes"].items()}
    rear_after = {key.replace("\\", "/"): value for key, value in rear["native_after_hashes"].items()}
    require(rear_before == contained_hashes and set(rear_before) == set(rear_after),
            "Rear-console receipt does not continue the exact contained-jet authoring chain")
    require({key for key in rear_before if rear_before[key] != rear_after[key]} ==
            {REL.as_posix() + "/" + key for key in REAR_CONSOLE_MESHES},
            "Rear-console correction changed packages outside the exact four D meshes")
    require(rear.get("manifest_sha256") == sha(plain_path(args.manifest)),
            "Rear-console receipt differs from the requested final manifest")
    expected_hashes = {REL.as_posix() + "/" + key: row["sha256"] for key, row in current.items()}
    require({key: value for key, value in rear_after.items() if key.startswith(REL.as_posix() + "/")} == expected_hashes,
            "Current Stage namespace differs from final rear-console authoring")
    source_plan = read(args.source_plan)
    require(source_plan.get("no_owner_writes") is True and Path(source_plan["owner_root"]).resolve() == OWNER.resolve(), "Wrong source plan owner")
    source_rows = rows_by_path(source_plan["files"])
    require(set(source_rows) == SOURCE_PATHS, "Source patch scope changed")
    proposed = plain_path(source_plan["proposal_root"])
    require(proposed.is_relative_to(WORK), "Source proposals must remain inside private D: work")
    for relative, row in source_rows.items():
        require(row.get("reverse_patch_exact") is True, "Source plan lacks exact reverse guard")
        require(sha(child(OWNER, relative)) == row["before_sha256"], "Owner source drift: " + relative)
        require(sha(child(proposed, relative)) == row["after_sha256"], "Source proposal drift: " + relative)
    plugin_manifest = read(REPO / ".agent/local/CryoInteraction/plugin-collision-stage-copy.json")
    require(plugin_manifest.get("status") in ("COLLISION_PLUGIN_STAGE_COPY_HASH_VERIFIED", "RUNTIME_PLUGIN_STAGE_COPY_HASH_VERIFIED"),
            "Plugin copy not verified")
    plugin_rows = rows_by_path(plugin_manifest["files"])
    require(set(plugin_rows) == PLUGIN_PATHS, "Plugin scope changed")
    require(set(inventory(STAGE / PLUGIN_REL)) == PLUGIN_PATHS, "Unexpected Stage plugin files")
    verify_files(STAGE / PLUGIN_REL, plugin_rows)
    require(not plain_path(OWNER / PLUGIN_REL).exists(), "Owner plugin folder exists; refuse unknown overwrite")
    configuration = OWNER / "Config/DefaultGame.ini"
    require(configuration.read_bytes().count(b'+DirectoriesToNeverCook=(Path="/Game/SpaceSurvival/CryoComparison")') == 1,
            "Exact review-only cook exclusion missing or duplicated")
    require(b'/Content/SpaceSurvival/CryoComparison/' in (OWNER / '.gitignore').read_bytes(), "Private namespace ignore is missing")
    proof_record = proof(args, current)
    preserved = preservation_checks()
    running = native_processes()
    require(not args.apply or not running, "Native editor/build is running; serialize adoption")
    backup = WORK / "owner-cryo-v4-backup"
    require(not backup.exists(), "Backup exists; refuse replay")
    output = OUT / ("native-adoption-v4.json" if args.apply else "native-adoption-v4-dry-run.json")
    require(not args.apply or not output.exists(), "Final adoption receipt exists; refuse replay")
    game_dll = OWNER / "Binaries/Win64/UnrealEditor-SpaceSurvival.dll"
    game_hash = sha(game_dll) if game_dll.is_file() else None
    receipt = {"schema_version": 1, "utc": datetime.now(timezone.utc).isoformat(), "apply": args.apply,
        "status": "DRY_RUN_VALIDATED_PENDING_APPLY", "destination": str(DESTINATION),
        "files": list(current.values()), "file_count": len(current), "bytes": sum(r["bytes"] for r in current.values()),
        "new_native_files": added, "replaced_native_files": changed, "preserved_native_files": len(old) - len(changed),
        "baseline_receipt": str(args.baseline), "baseline_receipt_sha256": sha(args.baseline),
        "contained_jet_receipt": str(containment_path), "contained_jet_receipt_sha256": sha(containment_path),
        "rear_console_receipt": str(rear_path), "rear_console_receipt_sha256": sha(rear_path),
        "source_plan": str(args.source_plan), "source_plan_sha256": sha(args.source_plan),
        "source_files": list(source_rows.values()), "plugin_destination": str(OWNER / PLUGIN_REL),
        "plugin_files": list(plugin_rows.values()), "proof": proof_record, **preserved,
        "owner_loaded_in_editor": False, "owner_game_dll_before": game_hash,
        "isolated_game_dll_copied": False, "native_process_ids_at_preflight": running,
        "owner_build": {"status": "PENDING_REQUIRED_OWNER_SOURCE_BUILD", "command": "Scripts/Build.ps1 -Target Editor"},
        "backup_directory": str(backup), "completed_writes": [],
        "limits": ["Owner latest dirty source must be rebuilt separately; no isolated game DLL copy.",
                   "Review-only map remains excluded from cooking; no production-map or packaged validation."]}
    if args.apply:
        # Preflight is complete before the first owner write. Backups are exact overwritten bytes only.
        backup.mkdir(exist_ok=False)
        for relative in [REL.as_posix() + "/" + MAP, *sorted(source_rows)]:
            source = child(OWNER, relative); target = child(backup, relative)
            target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, target)
            require(sha(source) == sha(target), "Backup mismatch")
        shutil.copy2(args.baseline, backup / "native-adoption-v3.json")
        shutil.copy2(args.source_plan, backup / "source-plan.json")
        try:
            verify_files(DESTINATION, old)
            for relative, row in source_rows.items():
                require(sha(child(OWNER, relative)) == row["before_sha256"], "Source changed during backup")
            for relative in added + changed:
                receipt["in_progress_write"] = REL.as_posix() + "/" + relative
                guarded_copy(child(SOURCE, relative), child(DESTINATION, relative), current[relative]["sha256"],
                             old[relative]["sha256"] if relative in old else None)
                receipt["completed_writes"].append(REL.as_posix() + "/" + relative)
            (OWNER / PLUGIN_REL).mkdir(exist_ok=False)
            for relative, row in plugin_rows.items():
                receipt["in_progress_write"] = PLUGIN_REL.as_posix() + "/" + relative
                guarded_copy(child(STAGE / PLUGIN_REL, relative), child(OWNER / PLUGIN_REL, relative), row["sha256"])
                receipt["completed_writes"].append(PLUGIN_REL.as_posix() + "/" + relative)
            for relative, row in source_rows.items():
                receipt["in_progress_write"] = relative
                guarded_copy(child(proposed, relative), child(OWNER, relative), row["after_sha256"], row["before_sha256"])
                receipt["completed_writes"].append(relative)
            verify_files(DESTINATION, current)
            require(set(inventory(DESTINATION, native=True)) == set(current), "Owner namespace changed during apply")
            verify_files(OWNER / PLUGIN_REL, plugin_rows)
            for relative, row in source_rows.items():
                require(sha(child(OWNER, relative)) == row["after_sha256"], "Owner source verification failed")
            require((sha(game_dll) if game_dll.is_file() else None) == game_hash, "Owner game DLL changed during adoption")
            receipt.update(preservation_checks())
            receipt["status"] = "ADOPTED_V4_NATIVE_SOURCE_PLUGIN_HASH_VERIFIED"
            receipt["owner_game_dll_after"] = game_hash
            receipt.pop("in_progress_write", None)
        except Exception as error:
            receipt["status"] = "ADOPTION_INCOMPLETE_REQUIRES_REVIEW"
            receipt["error"] = str(error)
            receipt["recovery"] = "Keep this receipt and exact backups; do not rerun or overwrite owner changes. Review completed_writes before recovery."
            output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
            raise
    output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("status", "file_count", "bytes", "preserved_native_files", "destination")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--baseline", type=Path, default=OUT / "native-adoption.json")
    parser.add_argument("--source-plan", type=Path, default=WORK / "cryo-owner-runtime-source-plan.json")
    parser.add_argument("--manifest", type=Path, default=OUT / "assembly_fit_v4_4.json")
    parser.add_argument("--angles", type=Path)
    parser.add_argument("--interaction", type=Path)
    parser.add_argument("--visual-review", type=Path)
    main(parser.parse_args())
