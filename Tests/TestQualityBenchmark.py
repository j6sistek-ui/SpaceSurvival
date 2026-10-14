"""Synthetic parser/receipt guards only; these do not establish measured game performance."""
import copy
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location(
    "quality_benchmark", Path(__file__).resolve().parents[1] / "Scripts" / "AnalyzeQualityBenchmark.py")
BENCHMARK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BENCHMARK)


class BenchmarkEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ss-benchmark-parser-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.fixture = {
            "evidenceType": BENCHMARK.EVIDENCE, "success": True, "qualityBenchmark": True,
            "benchmarkDirectorDisabled": True, "benchmarkNormalStats": True,
            "benchmarkScriptedPhysicsInput": True, "benchmarkHealthAssistance": False,
            "benchmarkWarmupSeconds": 15., "benchmarkMeasuredSeconds": 60.,
            "benchmarkContactCount": 0, "benchmarkRunSeed": 1234,
            "benchmarkDistantAsteroidCount": 6144, "benchmarkInitialHull": 100.,
            "benchmarkInitialShield": 50., "visualCaptureEnabled": False, "visualRequests": [],
        }
        self.capture = {
            "evidenceType": BENCHMARK.EVIDENCE, "success": True, "artifactsUnchanged": True,
            "productionPreserved": True, "noTestSaveSlotsWritten": True, "processExit": 0,
            "failures": [], "images": [], "sourceBefore": {"head": "abc"},
            "sourceAfter": {"head": "abc"}, "productionBefore": [], "productionAfter": [],
            "fixture": self.fixture,
        }
        self.write_receipts()
        self.write_csv()

    def write_receipts(self):
        for name, value in (("capture.json", self.capture), ("fixture.json", self.fixture)):
            (self.root / name).write_text(json.dumps(value), encoding="utf-8")

    def write_csv(self, damage=False, short_stage=False, missing_gpu=False, nonfinite=False):
        header = ["EVENTS"] + list(BENCHMARK.TIMINGS[:3])
        if not missing_gpu:
            header.append("GPUTime")
        complete = header + [BENCHMARK.PREFIX + name for name in BENCHMARK.COUNTERS]
        with (self.root / "Endgame.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(header)
            writer.writerow(["", 20, 10, 8] + ([] if missing_gpu else [12]))
            for index in range(600):
                elapsed = 15.1 + index * .1
                stage = 1 + index // 200
                if short_stage and index < 210:
                    stage = 1
                frame = {
                    "Measured": 1, "Stage": stage, "ElapsedSeconds": elapsed,
                    "SpeedCmPerSecond": 1000, "DistantInstances": 6144, "DistantCells": 125,
                    "DistantCellX": index // 100, "DistantCellY": 0, "DistantCellZ": -1,
                    "RegionCells": 27, "RegionClutter": 280, "RegionLandmarks": 20,
                    "Hull": 99 if damage and index == 350 else 100, "Shield": 50,
                    "Boost": 50, "LaneErrorCm": 100,
                }
                timings = [100, 20, 10] + ([] if missing_gpu else [30])
                if nonfinite and index == 400:
                    timings[0] = "nan"
                writer.writerow([""] + timings + [frame[name] for name in BENCHMARK.COUNTERS])
            writer.writerow(complete)
            writer.writerow(["[captureduration]", "75", "[HasHeaderRowAtEnd]", "1"])

    def test_growing_header_stage_filter_and_transition_metrics(self):
        report = BENCHMARK.analyze(self.root)
        self.assertEqual(report["measured"]["frames"], 600)
        self.assertEqual(report["measured"]["average_fps_from_mean_frame_time"], 10)
        self.assertEqual(report["stages"]["turn"]["frames"], 200)
        self.assertEqual(report["transition_frames"]["frames"], 5)
        self.assertEqual(report["measured"]["timings"]["GPUTime"]["p95_ms"], 30)

    def test_screenshot_presence_rejected(self):
        (self.root / "unexpected.png").write_bytes(b"not a real image")
        with self.assertRaisesRegex(ValueError, "PNG present"):
            BENCHMARK.analyze(self.root)

    def test_mismatched_receipt_rejected(self):
        self.capture["fixture"] = copy.deepcopy(self.fixture)
        self.capture["fixture"]["benchmarkRunSeed"] = 999
        self.write_receipts()
        with self.assertRaisesRegex(ValueError, "do not match"):
            BENCHMARK.analyze(self.root)

    def test_changed_production_save_rejected(self):
        self.capture["productionAfter"] = [{"sha256": "changed"}]
        self.write_receipts()
        with self.assertRaisesRegex(ValueError, "Production save"):
            BENCHMARK.analyze(self.root)

    def test_actual_damage_rejected(self):
        self.write_csv(damage=True)
        with self.assertRaisesRegex(ValueError, "Hull damage"):
            BENCHMARK.analyze(self.root)

    def test_short_stage_rejected(self):
        self.write_csv(short_stage=True)
        with self.assertRaisesRegex(ValueError, "turn has less"):
            BENCHMARK.analyze(self.root)

    def test_missing_gpu_is_reported_without_inventing_values(self):
        self.write_csv(missing_gpu=True)
        report = BENCHMARK.analyze(self.root)
        self.assertEqual(report["measured"]["timings"]["GPUTime"], {"samples": 0})
        self.assertTrue(any("GPU timing is missing" in limitation for limitation in report["limits"]))

    def test_nonfinite_timing_rejected(self):
        self.write_csv(nonfinite=True)
        with self.assertRaisesRegex(ValueError, "Non-finite"):
            BENCHMARK.analyze(self.root)


if __name__ == "__main__":
    unittest.main()
