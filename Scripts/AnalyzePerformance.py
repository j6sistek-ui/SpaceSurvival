"""Analyze a completed Unreal CSV capture without claiming representative gameplay acceptance.

Example: python Scripts/AnalyzePerformance.py capture.csv --log PackagedSmoke.log
         --output docs/validation/performance.json --gameplay-warmup-seconds 5
Only the requested JSON output is written. Raw CSV/log command lines and login IDs
are deliberately excluded from the receipt. Uses Python's standard library only.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

csv.field_size_limit(32 * 1024 * 1024)
TIMINGS = ("FrameTime", "GPUTime", "GameThreadTime", "RenderThreadTime", "RHIThreadTime")
STATE = tuple("SpaceSurvival/" + name for name in (
    "Phase", "Wave", "RunActive", "ActiveThreats", "Hull", "ShipSpeedCmPerSec"))
SOAK_NAMES = ("Fixture", "SimulationDeltaMs", "Gravity", "Asteroids", "Wreckage", "Electrical",
              "Pursuers", "Flankers", "Projectiles", "Pickups", "ApplicationForeground")
SOAK = tuple("SpaceSurvivalSoak/" + name for name in SOAK_NAMES)
STAGES = ("SpaceSurvivalSoak/Scenario", "SpaceSurvivalSoak/Stage", "SpaceSurvivalSoak/Phase")
STAGE_NAMES = ("Waiting", "Flight", "Breathing", "Wormhole", "Climax", "Approach", "Docking", "AuthoredExit", "StationIdle")
PHASES = ("Hangar", "Flight", "Breathing", "Wormhole", "Climax", "Approach", "Docking", "Station", "Dead")
METADATA_KEYS = (
    "platform", "config", "buildversion", "engineversion", "enginereleaseversion", "os", "cpu",
    "gpu", "gpudriver", "deviceprofile", "targetframerate", "starttimestamp", "endtimestamp",
    "captureduration", "systemresolution.resx", "systemresolution.resy", "verbatimrhiname",
    "rhiname", "rhifeaturelevel", "shaderplatform", "vsyncenabled", "raytracing",
    "streamingpoolsizemb", "csvmaxfilebytesreached", "HasHeaderRowAtEnd", "EventTimestamps")


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_path(path):
    path = path.resolve()
    root = Path(__file__).resolve().parents[1]
    return path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)


def read_capture(path):
    # Unreal appends columns during capture, then writes the complete header at the end.
    headers, metadata, lengths = [], {}, set()
    with path.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.reader(stream):
            if not row:
                continue
            if row[0] == "EVENTS":
                headers.append(row)
            elif row[0].startswith("["):
                if len(row) % 2:
                    raise ValueError("Malformed metadata row")
                metadata.update({key.strip("[]"): value for key, value in zip(row[::2], row[1::2])})
            else:
                lengths.add(len(row))
    if not headers or "captureduration" not in metadata:
        raise ValueError("Capture is incomplete: final metadata is absent")
    if metadata.get("HasHeaderRowAtEnd") == "1" and len(headers) < 2:
        raise ValueError("Capture is incomplete: final header is absent")
    header = headers[-1]
    if any(header[:len(earlier)] != earlier for earlier in headers):
        raise ValueError("Header columns were reordered; append-only schema expected")
    required = TIMINGS + STATE
    for name in required:
        if header.count(name) != 1:
            raise ValueError(f"Expected one exact counter named {name!r}; found {header.count(name)}")
    indices = {name: header.index(name) for name in required}
    if header.count("MaxFrameTime") == 1:
        indices["MaxFrameTime"] = header.index("MaxFrameTime")
    if any(name in header for name in SOAK):
        if any(header.count(name) != 1 for name in SOAK):
            raise ValueError("Incomplete or duplicate endgame fixture counter set")
        indices.update({name: header.index(name) for name in SOAK})
    if any(name in header for name in STAGES):
        if any(header.count(name) != 1 for name in STAGES) or SOAK[0] not in indices:
            raise ValueError("Incomplete scenario/stage fixture columns")
        indices.update({name: header.index(name) for name in STAGES})
    frames, events, elapsed = [], [], 0.0
    with path.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.reader(stream):
            if not row or row[0] == "EVENTS" or row[0].startswith("["):
                continue
            if len(row) > len(header):
                raise ValueError("Data row is wider than final header")
            frame = {"index": len(frames), "elapsed_start_s": elapsed}
            for name, index in indices.items():
                value = float(row[index]) if index < len(row) and row[index] else (0.0 if name in SOAK + STAGES else None)
                if value is not None and (not math.isfinite(value) or value < 0):
                    raise ValueError(f"Invalid {name} at frame {len(frames)}")
                if name in required and value is None:
                    raise ValueError(f"Missing required {name} at frame {len(frames)}")
                frame[name] = value
            if frame["FrameTime"] <= 0:
                raise ValueError(f"Nonpositive FrameTime at frame {len(frames)}")
            for name in STATE[:4]:
                if not frame[name].is_integer():
                    raise ValueError(f"Noninteger state {name} at frame {len(frames)}")
            if frame[STATE[0]] not in range(len(PHASES)) or frame[STATE[2]] not in (0, 1):
                raise ValueError(f"Invalid phase/run state at frame {len(frames)}")
            if SOAK[0] in frame:
                for name in (SOAK[0], *SOAK[2:]):
                    if not frame[name].is_integer():
                        raise ValueError(f"Noninteger fixture count {name} at frame {len(frames)}")
                if frame[SOAK[0]] not in (0, 1) or frame[SOAK[-1]] not in (0, 1):
                    raise ValueError(f"Invalid fixture/foreground flag at frame {len(frames)}")
                if frame[SOAK[0]] == 1 and frame[SOAK[1]] <= 0:
                    raise ValueError(f"Nonpositive fixture simulation delta at frame {len(frames)}")
            if STAGES[0] in frame:
                scenario, stage, fixture_phase = (frame[name] for name in STAGES)
                if not scenario.is_integer() or not stage.is_integer() or not fixture_phase.is_integer():
                    raise ValueError("Noninteger fixture scenario/stage")
                if frame[SOAK[0]] == 1:
                    if scenario not in (1, 2) or stage not in range(1, 9):
                        raise ValueError("Unknown fixture scenario/stage")
                    expected_phase = 7 if stage in (7, 8) else stage
                    if fixture_phase != expected_phase:
                        raise ValueError("Fixture stage disagrees with its post-update phase")
            elapsed += frame["FrameTime"] / 1000
            frames.append(frame)
            for event in re.findall(r"(?:^|;)(SpaceSurvival/Phase[^;]*)", row[0]):
                events.append({"frame_index": frame["index"], "event": event})
    return frames, metadata, events, {
        "header_rows_skipped": len(headers), "initial_columns": len(headers[0]),
        "final_columns": len(header), "data_row_width_min": min(lengths),
        "data_row_width_max": max(lengths), "csv_field_size_limit_bytes": csv.field_size_limit(),
        "selected_exact_columns": list(indices), "metadata_footer_excluded": True,
    }


def stats(values):
    values = sorted(value for value in values if value is not None)
    if not values:
        return {"samples": 0}
    percentile = lambda fraction: values[max(0, math.ceil(len(values) * fraction) - 1)]
    return {
        "samples": len(values), "mean_ms": round(statistics.mean(values), 6),
        "median_ms": round(statistics.median(values), 6), "p95_ms": percentile(.95),
        "p99_ms": percentile(.99), "min_ms": values[0], "max_ms": values[-1],
        "zero_samples": values.count(0),
        "percent_above_ms": {str(threshold): round(100 * sum(value > threshold for value in values) / len(values), 6)
                             for threshold in (16.667, 33.333, 50.0)},
    }


def summarize(frames):
    if not frames:
        return {"frames": 0}
    duration = sum(frame["FrameTime"] for frame in frames) / 1000
    return {
        "frames": len(frames), "first_frame_index": frames[0]["index"], "last_frame_index": frames[-1]["index"],
        "wall_frame_time_sum_s": round(duration, 6), "fps_from_frame_time_sum": round(len(frames) / duration, 6),
        "timings": {name: stats(frame[name] for frame in frames) for name in TIMINGS},
        "max_active_threats": int(max(frame[STATE[3]] for frame in frames)),
        "hull_min": min(frame[STATE[4]] for frame in frames), "hull_max": max(frame[STATE[4]] for frame in frames),
        "ship_speed_cm_per_s_max": max(frame[STATE[5]] for frame in frames),
    }


def read_log(path, capture_end_epoch):
    if not path:
        return {"available": False}
    raw = path.read_bytes()
    quality, after_quality, cvars, stalls = {}, {}, {}, []
    for number, line in enumerate(raw.decode("utf-8-sig", errors="replace").splitlines(), 1):
        stamp = re.search(r"\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\]", line)
        if not stamp:
            continue
        timestamp = datetime.strptime(stamp[1], "%Y.%m.%d-%H.%M.%S:%f").replace(tzinfo=timezone.utc)
        before_end = timestamp.timestamp() < capture_end_epoch + 1
        section = re.search(r"Applying CVar settings from Section \[([^\]]*Quality)@(\d+)\]", line)
        if section:
            target = quality if before_end else after_quality
            target[section[1]] = {"level": int(section[2]), "log_line": number, "timestamp_utc": timestamp.isoformat()}
        cvar = re.search(r"Set CVar \[\[(r\.(?:GenerateMeshDistanceFields|DynamicGlobalIlluminationMethod|ReflectionMethod)):(\d+)\]\]", line)
        if before_end and cvar:
            cvars[cvar[1]] = {"value": int(cvar[2]), "log_line": number}
        if before_end and "Waited for PSO creation" in line:
            stalls.append({"log_line": number, "message": line.split("]", 2)[-1].strip()})
    return {
        "available": True, "path": source_path(path), "snapshot_bytes": len(raw),
        "snapshot_sha256": hashlib.sha256(raw).hexdigest(),
        "quality_last_logged_by_capture_end": quality, "quality_logged_after_capture": after_quality,
        "render_cvars_last_logged_by_capture_end": cvars, "pso_creation_waits_during_capture": stalls,
        "boundary_note": "CSV endtimestamp has whole-second precision; log cutoff includes that UTC second.",
    }


def analyze(path, log_path, warmup, startup_warmup, context_notes):
    frames, metadata, events, parser = read_capture(path)
    gameplay = [frame for frame in frames if frame[STATE[2]] == 1 and 1 <= frame[STATE[0]] <= 6]
    gameplay_ids = {frame["index"] for frame in gameplay}
    # Reset warmup only when flight resumes after a non-gameplay phase, not at every wave.
    run_start, previous = 0.0, -2
    warm_ids = set()
    for frame in gameplay:
        if frame["index"] != previous + 1:
            run_start = frame["elapsed_start_s"]
        if frame["elapsed_start_s"] - run_start < warmup:
            warm_ids.add(frame["index"])
        previous = frame["index"]
    filtered = [frame for frame in gameplay if frame["index"] not in warm_ids]
    non_gameplay = [frame for frame in frames if frame["index"] not in gameplay_ids]
    segments = []
    for frame in frames:
        state = tuple(int(frame[name]) for name in STATE[:3])
        if not segments or segments[-1][0] != state:
            segments.append((state, []))
        segments[-1][1].append(frame)
    targets = [frame.get("MaxFrameTime") for frame in gameplay if frame.get("MaxFrameTime", 0) > 0]
    all_soak_frames = [frame for frame in frames if frame.get(SOAK[0]) == 1]
    scenarios = {frame.get(STAGES[0], 1) for frame in all_soak_frames}
    if len(scenarios) > 1:
        raise ValueError("Multiple fixture scenarios in one capture")
    station_frames = [frame for frame in all_soak_frames if frame.get(STAGES[0]) == 2]
    soak_frames = [frame for frame in all_soak_frames if frame.get(STAGES[0], 1) == 1]
    report = {
        "schema_version": 2,
        "status": ("RENDERED_STATION_FIXTURE_ONLY_NOT_60_FPS_ACCEPTANCE" if station_frames else
                   "RENDERED_ENDGAME_FIXTURE_ONLY_NOT_60_FPS_ACCEPTANCE" if soak_frames else
                   "OBSERVED_PHASE_CAPTURE_ONLY_NOT_60_FPS_ACCEPTANCE"),
        "source_csv": {"path": source_path(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)},
        "metadata": {key: metadata[key] for key in METADATA_KEYS if key in metadata},
        "parser": parser,
        "method": {
            "counter_units": "All five timing counters are milliseconds. No similarly named exclusive scopes are substituted.",
            "percentiles": "Nearest rank: sorted[ceil(p*n)-1]; median uses the mean of the middle pair when n is even.",
            "thresholds": "Strictly greater than 16.667, 33.333 and 50.0 ms; denominator is all numeric samples in each group.",
            "gameplay_filter": "RunActive == 1 and Phase in 1..6; station, hangar and dead frames excluded.",
            "gameplay_warmup_seconds": warmup,
            "gameplay_warmup_filter": "Exclude frames whose start (cumulative FrameTime) is less than warmup seconds after each contiguous gameplay interval starts.",
            "startup_warmup_seconds": startup_warmup,
            "startup_filter": "Non-gameplay frames with cumulative FrameTime start below startup warmup; this is an explicit time window, not a loading detector.",
            "zero_timing_values": "Retained and counted, including unavailable startup GPU/thread samples recorded as zero by Unreal.",
            "frame_index": "Zero-based CSV data-row index; repeated headers and metadata are excluded.",
        },
        "effective_frame_limit": {
            "counter": "MaxFrameTime", "meaning": "Target frame budget, NOT actual frame time or simulation delta (UE LaunchEngineLoop.cpp).",
            "gameplay_budget_ms_unique": sorted(set(targets)),
            "fps_from_median_budget": round(1000 / statistics.median(targets), 4) if targets else None,
            "note": "CSV targetframerate metadata is retained separately; it can differ from the applied runtime cap.",
        },
        "simulation_delta": {
            "available": bool(all_soak_frames), "counter": SOAK[1] if all_soak_frames else None,
            "fixture_samples": stats(frame[SOAK[1]] for frame in all_soak_frames),
            "reason": ("Fixture actor DeltaSeconds from normal engine frames; excludes startup/CSV drain. This is not physical input latency." if all_soak_frames else
                       "No simulation-delta counter. FrameTime is wall duration and MaxFrameTime is cap budget; no simulation-rate inference."),
        },
        "station_fixture": {
            "observed": bool(station_frames), "frames": len(station_frames),
            "all_fixture_frames_foreground": bool(station_frames) and all(frame[SOAK[-1]] == 1 for frame in station_frames),
            "phase_sample_differences": sum(frame[STATE[0]] != frame[STAGES[2]] for frame in station_frames),
            "phase_sample_note": "GameMode phase is sampled after Session.Tick and before BeginDocking. Fixture phase/stage are sampled at PostUpdate; docking can differ for one frame. Historical phase groups retain their original timing point.",
            "stages": {name: {**summarize([frame for frame in station_frames if frame[STAGES[1]] == stage]),
                               "simulation_seconds": round(sum(frame[SOAK[1]] / 1000 for frame in station_frames if frame[STAGES[1]] == stage), 6)}
                       for stage, name in enumerate(STAGE_NAMES) if stage > 0},
            "limits": "Scenario2: seeded normal Wave5, scripted ordinary approach, actual docking/exit and stationary hub. Stage7 means authored exit, stage8 means stationary hub; neither establishes human interaction or feel. Historical flight-only aggregate filters are unchanged.",
        },
        "endgame_fixture": {
            "observed": bool(soak_frames), "frames": len(soak_frames),
            "foreground_frames": sum(frame[SOAK[-1]] == 1 for frame in soak_frames),
            "all_fixture_frames_foreground": bool(soak_frames) and all(frame[SOAK[-1]] == 1 for frame in soak_frames),
            "kind_counts": {name: {"maximum": int(max(frame[counter] for frame in soak_frames)),
                                    "mean": round(statistics.mean(frame[counter] for frame in soak_frames), 6)}
                            for name, counter in zip(SOAK_NAMES[2:-1], SOAK[2:-1])} if soak_frames else {},
            "compound_presence_simulation_seconds": round(sum(frame[SOAK[1]] / 1000 for frame in soak_frames
                if frame[STATE[0]] == 4 and frame[STATE[1]] == 10 and frame[SOAK[2]] > 0 and
                frame[SOAK[3]] > 0 and frame[SOAK[6]] + frame[SOAK[7]] > 0), 6),
            "limits": "Marker identifies a seeded scripted fixture with enlarged durability; counts include telegraphs/offscreen actors. It does not establish contact, visibility, natural progression, fairness or human feel.",
        },
        "groups": {
            "all_frames": summarize(frames),
            "startup_menu_or_other_non_gameplay": summarize(non_gameplay),
            "startup_warmup_non_gameplay": summarize([f for f in non_gameplay if f["elapsed_start_s"] < startup_warmup]),
            "non_gameplay_after_startup_warmup": summarize([f for f in non_gameplay if f["elapsed_start_s"] >= startup_warmup]),
            "gameplay_all": summarize(gameplay),
            "gameplay_warmup_excluded": summarize([f for f in gameplay if f["index"] in warm_ids]),
            "gameplay_after_warmup": summarize(filtered),
        },
        "early_waves": {str(wave): summarize([frame for frame in filtered if frame[STATE[1]] == wave])
                        for wave in sorted({int(frame[STATE[1]]) for frame in gameplay})},
        "phase_segments": [{"phase": state[0], "phase_name": PHASES[state[0]], "wave": state[1], "run_active": state[2],
                            "frames": len(group), "first_frame_index": group[0]["index"], "last_frame_index": group[-1]["index"],
                            "wall_frame_time_sum_s": round(sum(f["FrameTime"] for f in group) / 1000, 6),
                            "max_active_threats": int(max(f[STATE[3]] for f in group)),
                            "timings": {name: stats(f[name] for f in group) for name in TIMINGS},
                            "simulation_delta": stats(f[SOAK[1]] for f in group if f.get(SOAK[0]) == 1)}
                           for state, group in segments],
        "phase_events": events,
        "worst_gameplay_frames": [{"frame_index": frame["index"], "phase": int(frame[STATE[0]]), "wave": int(frame[STATE[1]]),
                                   "active_threats": int(frame[STATE[3]]), **{name: frame[name] for name in TIMINGS}}
                                  for frame in sorted(gameplay, key=lambda f: f["FrameTime"], reverse=True)[:5]],
        "log_evidence": read_log(log_path, float(metadata["endtimestamp"])),
        "operator_context": context_notes,
        "limits": [
            "Only the phases/waves listed above were captured; recorded fixture phases do not establish a natural full ten-wave run or representative performance acceptance.",
            "A capped sample or scripted fixture is not evidence of uncapped headroom, representative worst-case performance or a sustained 60 FPS gate pass.",
            "No physical input responsiveness, controller feel, natural gameplay acceptance, final-art approval or clean-machine benchmark is established.",
            "RunActive/Phase identify simulation state, not a menu-open flag; live gameplay menus can be included. Loading/menu separation uses stated state/time filters.",
            "GPU and thread counters can reflect pipelined earlier work and must not be summed or treated as exact causal attribution for one frame.",
        ],
    }
    report["waves"] = report["early_waves"]  # Preserve the historical key for existing receipts/tools.
    report["frame_sum_minus_metadata_duration_s"] = round(sum(f["FrameTime"] for f in frames) / 1000 - float(metadata["captureduration"]), 6)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--log", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--gameplay-warmup-seconds", type=float, default=5.0)
    parser.add_argument("--startup-warmup-seconds", type=float, default=10.0)
    parser.add_argument("--context-note", action="append", default=[])
    args = parser.parse_args()
    for value in (args.gameplay_warmup_seconds, args.startup_warmup_seconds):
        if not math.isfinite(value) or value < 0:
            parser.error("Warmup seconds must be finite and nonnegative")
    if args.output.resolve() in {args.csv.resolve(), args.log.resolve() if args.log else None}:
        parser.error("Output must not overwrite a source capture or log")
    report = analyze(args.csv, args.log, args.gameplay_warmup_seconds, args.startup_warmup_seconds, args.context_note)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    gameplay = report["groups"]["gameplay_after_warmup"]
    print(json.dumps({"output": str(args.output), "frames": report["groups"]["all_frames"]["frames"],
                      "gameplay_after_warmup": gameplay, "status": report["status"]}, indent=2))


if __name__ == "__main__":
    main()
