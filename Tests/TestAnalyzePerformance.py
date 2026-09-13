"""Evidence parser tests only; synthetic CSV rows are never gameplay/performance evidence."""
import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("analysis", ROOT / "Scripts/AnalyzePerformance.py")
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


class CaptureEvidenceTests(unittest.TestCase):
    def capture(self, folder, focus=1, malformed=None, omit=None, footer=True, with_fixture=True):
        path = Path(folder) / "synthetic.csv"
        common = ["EVENTS", *analysis.TIMINGS, *analysis.STATE]
        optional = list(analysis.SOAK) if with_fixture else []
        if omit:
            optional.remove(omit)
        complete = common + optional
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(common)
            writer.writerow(["", 10, 2, 1, 2, 1, 0, 1, 0, 0, 100, 0])
            base = ["", 8, 2, 1, 2, 1, 4, 10, 1, 8, 50000, 3500]
            values = dict(zip(analysis.SOAK, [1, 8, 1, 3, 0, 0, 1, 1, 2, 0, focus]))
            if malformed:
                values[malformed[0]] = malformed[1]
            writer.writerow(base + [values[name] for name in optional])
            writer.writerow(complete)
            if footer:
                writer.writerow(["[captureduration]", "0.018", "[endtimestamp]", "1789278726", "[HasHeaderRowAtEnd]", "1"])
        return path

    def report(self, path):
        return analysis.analyze(path, None, 0, 10, ["SYNTHETIC PARSER TEST"])

    def test_plain_historical_capture_has_no_fixture_claim(self):
        with tempfile.TemporaryDirectory(prefix="ss-csv-test-") as folder:
            report = self.report(self.capture(folder, with_fixture=False))
            self.assertFalse(report["endgame_fixture"]["observed"])
            self.assertFalse(report["simulation_delta"]["available"])
            self.assertEqual(report["groups"]["all_frames"]["frames"], 2)

    def test_appended_fixture_columns_are_not_backfilled_into_startup(self):
        with tempfile.TemporaryDirectory(prefix="ss-csv-test-") as folder:
            report = self.report(self.capture(folder))
            self.assertEqual(report["endgame_fixture"]["frames"], 1)
            self.assertTrue(report["endgame_fixture"]["all_fixture_frames_foreground"])
            self.assertEqual(report["endgame_fixture"]["compound_presence_simulation_seconds"], .008)
            self.assertEqual(report["phase_segments"][-1]["timings"]["FrameTime"]["max_ms"], 8)
            self.assertEqual(report["simulation_delta"]["fixture_samples"]["samples"], 1)

    def test_background_capture_cannot_claim_all_foreground(self):
        with tempfile.TemporaryDirectory(prefix="ss-csv-test-") as folder:
            report = self.report(self.capture(folder, focus=0))
            self.assertFalse(report["endgame_fixture"]["all_fixture_frames_foreground"])

    def test_incomplete_fixture_columns_rejected(self):
        with tempfile.TemporaryDirectory(prefix="ss-csv-test-") as folder:
            with self.assertRaises(ValueError):
                self.report(self.capture(folder, omit=analysis.SOAK[2]))

    def test_missing_footer_rejected(self):
        with tempfile.TemporaryDirectory(prefix="ss-csv-test-") as folder:
            with self.assertRaises(ValueError):
                self.report(self.capture(folder, footer=False))

    def test_invalid_flags_counts_and_delta_rejected(self):
        for pair in [(analysis.SOAK[0], 2), (analysis.SOAK[-1], .5),
                     (analysis.SOAK[2], 1.5), (analysis.SOAK[1], 0), (analysis.SOAK[1], "nan")]:
            with self.subTest(pair=pair), tempfile.TemporaryDirectory(prefix="ss-csv-test-") as folder:
                with self.assertRaises(ValueError):
                    self.report(self.capture(folder, malformed=pair))


if __name__ == "__main__":
    unittest.main()
