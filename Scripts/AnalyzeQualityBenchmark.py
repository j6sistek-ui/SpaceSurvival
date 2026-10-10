"""Analyze an isolated environment/flight-cost capture, never a gameplay FPS gate.

Usage: python Scripts/AnalyzeQualityBenchmark.py CAPTURE_ROOT [--output RECEIPT.json]
Reads capture.json, fixture.json and Endgame.csv. Uses only the standard library.
Without --output the JSON receipt goes to stdout. No source artifacts are changed.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics


EVIDENCE = "ENVIRONMENT_FLIGHT_COST_BENCHMARK"
PREFIX = "SpaceSurvivalBenchmark/"
COUNTERS = (
    "Measured", "Stage", "ElapsedSeconds", "SpeedCmPerSecond", "DistantInstances",
    "DistantCells", "DistantCellX", "DistantCellY", "DistantCellZ", "RegionCells",
    "RegionClutter", "RegionLandmarks", "Hull", "Shield", "Boost", "LaneErrorCm",
)
TIMINGS = ("FrameTime", "GameThreadTime", "RenderThreadTime", "GPUTime", "RHIThreadTime")
INTEGER_COUNTERS = {
    "Measured", "Stage", "DistantInstances", "DistantCells", "DistantCellX",
    "DistantCellY", "DistantCellZ", "RegionCells", "RegionClutter", "RegionLandmarks",
}
SIGNED_COUNTERS = {"DistantCellX", "DistantCellY", "DistantCellZ"}
STAGES = {1: "cruise", 2: "turn", 3: "boost"}
TRANSITION_COUNTERS = (
    "DistantCellX", "DistantCellY", "DistantCellZ", "DistantCells", "DistantInstances",
    "RegionCells", "RegionClutter", "RegionLandmarks",
)
METADATA_KEYS = (
    "platform", "config", "buildversion", "engineversion", "enginereleaseversion", "os",
    "cpu", "gpu", "gpudriver", "deviceprofile", "targetframerate", "captureduration",
    "systemresolution.resx", "systemresolution.resy", "rhiname", "verbatimrhiname",
    "rhifeaturelevel", "shaderplatform", "vsyncenabled", "HasHeaderRowAtEnd",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value, name, minimum=0):
    require(isinstance(value, (int, float)) and not isinstance(value, bool), f"Missing/non-numeric {name}")
    require(math.isfinite(value) and value >= minimum, f"Invalid {name}: expected finite >= {minimum}")
    return value


def load_json(path):
    def invalid(value):
        raise ValueError(f"Non-finite JSON constant in {path.name}: {value}")
    return json.loads(path.read_text(encoding="utf-8-sig"), parse_constant=invalid)


def artifact(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def validate_receipts(root, capture, fixture):
    require(capture.get("evidenceType") == EVIDENCE, "Wrong capture evidence type")
    for key in ("success", "artifactsUnchanged", "productionPreserved", "noTestSaveSlotsWritten"):
        require(capture.get(key) is True, f"Capture guard did not pass: {key}")
    require(capture.get("processExit") == 0, "Capture process did not exit successfully")
    require(capture.get("failures") == [], "Capture failures must be an explicit empty list")
    require(capture.get("images") == [], "Benchmark must not contain screenshot requests")
    require(not any(path.suffix.lower() == ".png" for path in root.rglob("*")), "PNG present: screenshot stalls invalidate benchmark")
    before, after = capture.get("sourceBefore", {}), capture.get("sourceAfter", {})
    require(isinstance(before.get("head"), str) and before["head"] == after.get("head"), "Source HEAD changed or missing")
    require("productionBefore" in capture and capture["productionBefore"] == capture.get("productionAfter"),
            "Production save snapshots changed or missing")
    require(fixture.get("evidenceType") == EVIDENCE, "Wrong fixture evidence type")
    require(capture.get("fixture") == fixture, "Capture receipt and fixture JSON do not match")
    require(fixture.get("visualCaptureEnabled") is False and fixture.get("visualRequests") == [],
            "Benchmark fixture contains visual capture work")
    require(fixture.get("benchmarkHealthAssistance") is False, "Benchmark health assistance is not explicitly disabled")
    for key in ("success", "qualityBenchmark", "benchmarkDirectorDisabled", "benchmarkNormalStats", "benchmarkScriptedPhysicsInput"):
        require(fixture.get(key) is True, f"Fixture contract did not pass: {key}")
    warmup = number(fixture.get("benchmarkWarmupSeconds"), "benchmarkWarmupSeconds", 15)
    measured = number(fixture.get("benchmarkMeasuredSeconds"), "benchmarkMeasuredSeconds", 60)
    require(number(fixture.get("benchmarkContactCount"), "benchmarkContactCount") == 0, "Benchmark had physical contacts")
    for key in ("benchmarkRunSeed", "benchmarkDistantAsteroidCount"):
        value = number(fixture.get(key), key)
        require(int(value) == value, f"Noninteger {key}")
    require(fixture["benchmarkDistantAsteroidCount"] in (2048, 6144), "Unexpected population comparison setting")
    number(fixture.get("benchmarkInitialHull"), "benchmarkInitialHull", .000001)
    number(fixture.get("benchmarkInitialShield"), "benchmarkInitialShield")
    return warmup, measured


def read_csv(path):
    # Unreal appends counters during recording and repeats the completed header at EOF.
    csv.field_size_limit(32 * 1024 * 1024)
    headers, metadata = [], {}
    with path.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.reader(stream):
            if not row:
                continue
            if row[0] == "EVENTS":
                headers.append(row)
            elif row[0].startswith("["):
                require(len(row) % 2 == 0, "Malformed CSV metadata row")
                metadata.update({key.strip("[]"): value for key, value in zip(row[::2], row[1::2])})
    require(headers and "captureduration" in metadata, "Incomplete CSV: header or final metadata missing")
    require(metadata.get("HasHeaderRowAtEnd") != "1" or len(headers) >= 2, "Incomplete CSV: final header missing")
    header = headers[-1]
    require(all(header[:len(earlier)] == earlier for earlier in headers), "CSV header was reordered")
    columns = [PREFIX + name for name in COUNTERS] + list(TIMINGS[:3])
    columns += [name for name in TIMINGS[3:] if name in header]
    for name in columns:
        require(header.count(name) == 1, f"Expected one exact CSV column: {name}")
    indices = {name: header.index(name) for name in columns}
    frames, widths = [], set()
    with path.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.reader(stream):
            if not row or row[0] == "EVENTS" or row[0].startswith("["):
                continue
            widths.add(len(row))
            require(len(row) <= len(header), "CSV data row wider than final header")
            frame = {"index": len(frames)}
            for name, index in indices.items():
                # Rows before this category was registered belong to startup, not measurements.
                value = float(row[index]) if index < len(row) and row[index] else None
                key = name.removeprefix(PREFIX)
                if value is not None:
                    require(math.isfinite(value), f"Non-finite {name} at frame {frame['index']}")
                    require(value >= 0 or key in SIGNED_COUNTERS, f"Negative {name} at frame {frame['index']}")
                    if key in INTEGER_COUNTERS:
                        require(value.is_integer(), f"Noninteger {name} at frame {frame['index']}")
                frame[key] = value
            for name in TIMINGS:
                frame.setdefault(name, None)
            require(frame["Measured"] in (None, 0, 1), f"Invalid Measured flag at frame {frame['index']}")
            if frame["Measured"] == 1:
                require(all(frame[name] is not None for name in COUNTERS), "Measured frame has missing benchmark counters")
                require(frame["Stage"] in STAGES, "Measured frame has invalid stage")
                require(all(frame[name] is not None for name in TIMINGS[:3]), "Measured frame lacks required engine timing")
                require(frame["FrameTime"] > 0, "Measured frame has nonpositive FrameTime")
            frames.append(frame)
    require(frames, "CSV contains no data frames")
    return frames, metadata, {
        "header_rows_skipped": len(headers), "initial_columns": len(headers[0]), "final_columns": len(header),
        "data_row_width_min": min(widths), "data_row_width_max": max(widths),
        "selected_exact_columns": columns, "metadata_footer_excluded": True,
    }


def stats(values):
    values = sorted(value for value in values if value is not None)
    if not values:
        return {"samples": 0}
    rank = lambda fraction: values[max(0, math.ceil(len(values) * fraction) - 1)]
    return {
        "samples": len(values), "mean_ms": round(statistics.mean(values), 6),
        "p50_ms": rank(.5), "p95_ms": rank(.95), "p99_ms": rank(.99),
        "min_ms": values[0], "max_ms": values[-1], "zero_samples": values.count(0),
        "percent_above_ms": {str(limit): round(100 * sum(value > limit for value in values) / len(values), 6)
                             for limit in (16.667, 33.333, 50.0)},
    }


def value_range(frames, name):
    values = [frame[name] for frame in frames]
    return {"min": min(values), "max": max(values), "mean": round(statistics.mean(values), 6)}


def summarize(frames):
    if not frames:
        return {"frames": 0}
    mean = statistics.mean(frame["FrameTime"] for frame in frames)
    return {
        "frames": len(frames), "first_frame_index": frames[0]["index"], "last_frame_index": frames[-1]["index"],
        "elapsed_start_s": frames[0]["ElapsedSeconds"], "elapsed_end_s": frames[-1]["ElapsedSeconds"],
        "elapsed_span_s": round(frames[-1]["ElapsedSeconds"] - frames[0]["ElapsedSeconds"], 6),
        "wall_frame_time_sum_s": round(sum(frame["FrameTime"] for frame in frames) / 1000, 6),
        "average_fps_from_mean_frame_time": round(1000 / mean, 6),
        "timings": {name: stats(frame[name] for frame in frames) for name in TIMINGS},
        "counters": {name: value_range(frames, name) for name in COUNTERS if name not in ("Measured", "Stage", "ElapsedSeconds")},
    }


def analyze(root):
    paths = {name: root / name for name in ("capture.json", "fixture.json", "Endgame.csv")}
    capture, fixture = load_json(paths["capture.json"]), load_json(paths["fixture.json"])
    warmup, duration = validate_receipts(root, capture, fixture)
    frames, metadata, parser = read_csv(paths["Endgame.csv"])
    measured = [frame for frame in frames if frame["Measured"] == 1]
    require(measured, "No measured frames")
    require(all(b["index"] == a["index"] + 1 for a, b in zip(measured, measured[1:])), "Measured frames are not contiguous")
    require(all(b["ElapsedSeconds"] > a["ElapsedSeconds"] for a, b in zip(measured, measured[1:])), "ElapsedSeconds is not strictly increasing")
    require(measured[0]["ElapsedSeconds"] >= warmup - .05, "Measured window starts before warmup completes")
    require(measured[-1]["ElapsedSeconds"] - measured[0]["ElapsedSeconds"] >= duration - .5,
            "CSV measured duration is shorter than the fixture contract")
    require(measured[-1]["ElapsedSeconds"] <= warmup + duration + .5, "CSV measured window exceeds declared fixture duration")
    stage_groups = {stage: [frame for frame in measured if frame["Stage"] == stage] for stage in STAGES}
    previous_stage = 1
    for frame in measured:
        require(frame["Stage"] >= previous_stage, "Benchmark stages run out of order")
        previous_stage = frame["Stage"]
        require(frame["Hull"] >= fixture["benchmarkInitialHull"] - .001, "Hull damage invalidates environment benchmark")
        require(frame["Shield"] >= fixture["benchmarkInitialShield"] - .001, "Shield damage invalidates environment benchmark")
        require(frame["DistantInstances"] > 0 and frame["DistantCells"] > 0, "Measured field is empty")
    for stage, group in stage_groups.items():
        require(group and group[-1]["ElapsedSeconds"] - group[0]["ElapsedSeconds"] >= 19.5,
                f"Stage {STAGES[stage]} has less than 19.5 seconds of measured coverage")
    transitions = []
    for frame in measured:
        previous = frames[frame["index"] - 1] if frame["index"] else None
        changed = [name for name in TRANSITION_COUNTERS if previous and previous.get(name) is not None and previous[name] != frame[name]]
        if changed:
            transitions.append({"frame_index": frame["index"], "changed_counters": changed})
    transition_ids = {item["frame_index"] for item in transitions}
    gpu = [frame["GPUTime"] for frame in measured]
    limits = [
        "Environment/flight-cost comparison only: Director disabled, fixed run seed, scripted ordinary physics input and normal stats.",
        "No natural combat, human input/feel, packaged-build or representative sustained 60 FPS acceptance is established.",
        "Exact transition frames mark observed cell-coordinate or population changes; thread/GPU pipelining can delay costs to later frames.",
        "CSV counters cannot detect regional-cell replacements with unchanged counts; such replacements can be classified as ordinary frames.",
        "Missing timing samples are excluded and zero timing samples retained; engine thread/GPU timings must not be summed.",
        "Source HEAD/worktree listing and binary-preservation guards do not prove dirty file contents were unchanged or bind this DLL to source.",
    ]
    if any(value is None or value == 0 for value in gpu):
        limits.append("GPU timing is missing or zero for some measured frames; GPU bottleneck/headroom conclusions are limited.")
    return {
        "schema_version": 1, "evidence_type": EVIDENCE,
        "status": "VALID_ENVIRONMENT_FLIGHT_COST_ONLY_NOT_GAMEPLAY_ACCEPTANCE",
        "raw_artifacts": {name: artifact(path) for name, path in paths.items()},
        "capture_identity": {key: capture.get(key) for key in ("token", "label", "mode", "requestedResolution", "requestedUIScale")},
        "source_head": capture["sourceBefore"]["head"],
        "compiled_artifacts": capture.get("artifacts", []),
        "guards": {key: capture[key] for key in ("success", "artifactsUnchanged", "productionPreserved", "noTestSaveSlotsWritten")},
        "fixture": {key: value for key, value in fixture.items() if key.startswith("benchmark") or key in ("qualityBenchmark", "evidenceType", "success")},
        "metadata": {key: metadata[key] for key in METADATA_KEYS if key in metadata}, "parser": parser,
        "method": {
            "filter": "Only Measured==1; ElapsedSeconds includes warmup. Stages1/2/3 are cruise/turn/boost.",
            "timing_units": "Milliseconds from exact engine FrameTime/GameThreadTime/RenderThreadTime/GPUTime and optional RHIThreadTime columns.",
            "percentiles": "Nearest rank: sorted[ceil(p*n)-1], including p50; average FPS is1000/mean(FrameTime).",
            "thresholds": "Strictly greater than16.667/33.333/50ms; percentage denominator is all numeric timing samples in each group.",
            "duration_tolerance_s": .5, "stage_minimum_span_s": 19.5,
            "transition_filter": "Current CSV frame when observed coordinates or resident population differs from previous data row.",
        },
        "measured": summarize(measured),
        "stages": {STAGES[stage]: summarize(group) for stage, group in stage_groups.items()},
        "transition_frames": summarize([frame for frame in measured if frame["index"] in transition_ids]),
        "ordinary_frames": summarize([frame for frame in measured if frame["index"] not in transition_ids]),
        "transitions": transitions,
        "top10_hitches": [{"frame_index": frame["index"], "elapsed_s": frame["ElapsedSeconds"],
                            "stage": STAGES[frame["Stage"]], "transition": frame["index"] in transition_ids,
                            **{name: frame[name] for name in TIMINGS + ("SpeedCmPerSecond", "DistantInstances", "DistantCellX", "DistantCellY", "DistantCellZ", "LaneErrorCm")}}
                           for frame in sorted(measured, key=lambda item: item["FrameTime"], reverse=True)[:10]],
        "limits": limits,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        root = args.root.resolve(strict=True)
        if args.output:
            output = args.output.resolve()
            require(output not in {root / name for name in ("capture.json", "fixture.json", "Endgame.csv")}, "Output must not overwrite raw evidence")
        report = analyze(root)
        rendered = json.dumps(report, indent=2, allow_nan=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(json.dumps({"output": str(args.output.resolve()), "status": report["status"], "frames": report["measured"]["frames"]}))
        else:
            print(rendered, end="")
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.exit(2, f"Benchmark analysis rejected: {error}\n")


if __name__ == "__main__":
    main()
