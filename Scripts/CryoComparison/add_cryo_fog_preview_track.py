"""Add one restoring native CVar track to the owned cyan breathing sequence.

Dry run: python add_cryo_fog_preview_track.py
Apply in the isolated full CryoStage editor: runpy.run_path(path)['main'](True)
No launch is performed. Only the existing owned sequence package is saved.
The track sets near local-fog visibility to 10 cm while playing and restores
the previous process value on stop; it does not write renderer configuration.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import traceback


WORK = Path(__file__).resolve().parent
STAGE = WORK / "CryoStage"
SEQUENCE = "/Game/SpaceSurvival/CryoComparison/Sequences/LS_CryoBreathing_Cyan"
PACKAGE = "Content/SpaceSurvival/CryoComparison/Sequences/LS_CryoBreathing_Cyan.uasset"
CVAR = "r.LocalFogVolume.GlobalStartDistance"
COMMAND = CVAR + " 10"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(path):
    hasher = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def native_hashes():
    return {path.relative_to(STAGE).as_posix(): digest(path) for path in sorted((STAGE / "Content").rglob("*"))
            if path.is_file() and path.suffix.lower() in (".uasset", ".umap", ".uexp", ".ubulk")}


def intensity_signature(u, sequence):
    rows = []
    for binding in sequence.get_bindings():
        for track in binding.get_tracks():
            require(isinstance(track, u.MovieSceneFloatTrack), "Unexpected bound track type; refuse to change this sequence")
            require(str(track.get_property_name()) == "Intensity" and str(track.get_property_path()) == "Intensity",
                    "Unexpected float property track; refuse to change this sequence")
            sections = list(track.get_sections())
            require(len(sections) == 1, "Expected one section per breathing intensity track")
            channels = sections[0].get_channels_by_type(u.MovieSceneScriptingFloatChannel)
            require(len(channels) == 1, "Expected one intensity channel")
            keys = channels[0].get_keys()
            require(len(keys) == 5, "Expected five keys in each existing breathing track")
            key_rows = []
            for key in keys:
                key_time = key.get_time(u.MovieSceneTimeUnit.DISPLAY_RATE)
                value = float(key.get_value())
                sub_frame = float(key_time.get_editor_property("sub_frame"))
                require(math.isfinite(value) and math.isfinite(sub_frame), "Nonfinite existing intensity key")
                key_rows.append({"frame": int(key_time.frame_number.value), "sub_frame": sub_frame,
                                 "value": value, "interpolation": int(key.get_interpolation_mode().value),
                                 "tangent": int(key.get_tangent_mode().value)})
            # str(Guid) contains a temporary wrapper address in UE Python.
            # Convert the actual native GUID value, never its wrapper repr.
            guid = u.GuidLibrary.conv_guid_to_string(binding.get_id())
            require(bool(guid), "Could not read the native binding GUID")
            rows.append({"binding_guid": guid, "track_path": track.get_path_name(), "property": "Intensity",
                         "keys": sorted(key_rows, key=lambda row: (row["frame"], row["sub_frame"]))})
    require(len(rows) == 8, "Expected exactly eight existing breathing intensity tracks")
    require(len({row["binding_guid"] for row in rows}) == 8, "Expected eight distinct native intensity bindings")
    return sorted(rows, key=lambda row: (row["binding_guid"], row["track_path"]))


def main(do_apply=False):
    report = {"utc": datetime.now(timezone.utc).isoformat(), "apply": bool(do_apply),
              "status": "DRY_RUN_NO_UNREAL_WRITES", "sequence": SEQUENCE,
              "cvar": CVAR, "active_value_cm": 10.0, "completion_mode": "RESTORE_STATE",
              "persistent_renderer_config_write": False, "errors": [],
              "limits": ["CVar is process-global while the comparison sequence plays; it is not a per-volume override.",
                         "Native SIE must verify 1000 before play, 10 during looping, and restored 1000 after EndPlay.",
                         "This script saves only the sequence; it neither starts playback nor changes renderer config."]}
    try:
        require(STAGE.is_dir() and (STAGE / PACKAGE).is_file(), "Owned stage sequence package is missing")
        if do_apply:
            import unreal as u
            report["status"] = "FAILED"
            project = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
            require(project == STAGE.resolve(), "Refusing writes outside the isolated D-drive CryoStage")
            require(not list(u.EditorLevelLibrary.get_pie_worlds(False)), "Refusing authoring while SIE/PIE is running")
            assets = u.EditorAssetLibrary
            sequence = assets.load_asset(SEQUENCE)
            require(isinstance(sequence, u.LevelSequence), "Owned Level Sequence failed to load")
            require(assets.get_metadata_tag(sequence, "CryoAuthoringVersion") == "CryoBreathingCyanV1",
                    "Sequence ownership/version metadata mismatch")
            require(not list(sequence.get_tracks()), "Sequence already has a master track; refuse a duplicate or unexpected edit")
            before_tracks = intensity_signature(u, sequence)
            report["intensity_signature_before"] = before_tracks
            before_files = native_hashes()
            report["engine"] = u.SystemLibrary.get_engine_version()
            report["cvar_before_authoring"] = u.SystemLibrary.get_console_variable_float_value(CVAR)
            track = sequence.add_track(u.MovieSceneCVarTrack)
            require(track is not None, "Native CVar track creation failed")
            section = track.add_section()
            require(section is not None, "Native CVar section creation failed")
            section.set_start_frame_bounded(False)
            section.set_end_frame_bounded(False)
            # Space syntax matches the installed UE5.8 parser.
            section.set_from_string(COMMAND)
            section.set_completion_mode(u.MovieSceneCompletionMode.RESTORE_STATE)
            require(section.get_string().strip() == COMMAND, "CVar section string readback mismatch")
            require(section.get_completion_mode() == u.MovieSceneCompletionMode.RESTORE_STATE,
                    "CVar section must restore the previous process value")
            require(len(sequence.get_tracks()) == 1, "Expected exactly one new master CVar track")
            after_tracks = intensity_signature(u, sequence)
            report["intensity_signature_after"] = after_tracks
            report["intensity_signature_sha256_before"] = hashlib.sha256(
                json.dumps(before_tracks, sort_keys=True, allow_nan=False).encode("utf-8")).hexdigest()
            report["intensity_signature_sha256_after"] = hashlib.sha256(
                json.dumps(after_tracks, sort_keys=True, allow_nan=False).encode("utf-8")).hexdigest()
            require(after_tracks == before_tracks,
                    "Existing native breathing tracks changed; inspect primitive before/after signatures in this receipt")
            assets.set_metadata_tag(sequence, "CryoNearFogPreview", "10cm during playback; restore previous value on stop")
            require(assets.save_loaded_asset(sequence, only_if_is_dirty=False), "Sequence save failed")
            after_files = native_hashes()
            changed = sorted(path for path in set(before_files) | set(after_files)
                             if before_files.get(path) != after_files.get(path))
            require(changed == [PACKAGE], "Unexpected native package changes: " + str(changed))
            report["changed_native_packages"] = changed
            report["sequence_sha256_before"] = before_files[PACKAGE]
            report["sequence_sha256_after"] = after_files[PACKAGE]
            report["eight_intensity_tracks_unchanged"] = True
            report["cvar_after_authoring"] = u.SystemLibrary.get_console_variable_float_value(CVAR)
            require(abs(report["cvar_after_authoring"] - report["cvar_before_authoring"]) < 0.01,
                    "Authoring unexpectedly changed the runtime CVar")
            report["status"] = "SAVED_ONE_RESTORING_CVAR_TRACK_RUNTIME_VERIFICATION_PENDING"
    except Exception:
        report["status"] = "FAILED"
        report["errors"].append(traceback.format_exc())
    receipt = WORK / ("CryoFogPreviewTrack.json" if do_apply else "CryoFogPreviewTrackDryRun.json")
    receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("CRYO_FOG_PREVIEW_TRACK_RESULT " + json.dumps({"status": report["status"], "receipt": str(receipt),
                                                       "errors": len(report["errors"])}), flush=True)
    if report["errors"]:
        raise RuntimeError("Fog preview track authoring failed; inspect " + str(receipt))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args, _unknown = parser.parse_known_args()
    main(args.apply)
