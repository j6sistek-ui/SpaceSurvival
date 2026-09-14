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

    def station_capture(self, folder, mutate=None, omit=None):
        path = Path(folder) / "station-synthetic.csv"
        header = ["EVENTS", *analysis.TIMINGS, *analysis.STATE, *analysis.SOAK, *analysis.STAGES]
        if omit:
            header.remove(omit)
        rows = []
        for phase, stage, milliseconds in [(3, 3, 8000), (4, 4, 40000), (6, 6, 3000), (7, 7, 2400), (7, 8, 15000)]:
            row = dict(zip(["EVENTS", *analysis.TIMINGS, *analysis.STATE],
                           ["", milliseconds, 2, 1, 2, 1, phase, 5, 1, 4, 50000, 3500]))
            row.update(zip(analysis.SOAK, [1, milliseconds, 0, 1, 0, 0, 1, 0, 0, 0, 1]))
            row.update(zip(analysis.STAGES, [2, stage, phase]))
            rows.append(row)
        if mutate:
            mutate(rows)
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(header)
            writer.writerows([[row[name] for name in header] for row in rows])
            writer.writerow(header)
            writer.writerow(["[captureduration]", "68.4", "[endtimestamp]", "1789278726", "[HasHeaderRowAtEnd]", "1"])
        return path

    def test_station_exit_and_idle_retained_separately_from_historical_flight(self):
        with tempfile.TemporaryDirectory(prefix="ss-csv-test-") as folder:
            report = self.report(self.station_capture(folder))
            self.assertEqual(report["status"], "RENDERED_STATION_FIXTURE_ONLY_NOT_60_FPS_ACCEPTANCE")
            self.assertFalse(report["endgame_fixture"]["observed"])
            self.assertTrue(report["station_fixture"]["all_fixture_frames_foreground"])
            self.assertEqual(report["groups"]["gameplay_all"]["frames"], 3)
            stages = report["station_fixture"]["stages"]
            self.assertEqual(stages["AuthoredExit"]["simulation_seconds"], 2.4)
            self.assertEqual(stages["StationIdle"]["simulation_seconds"], 15)
            self.assertEqual(stages["AuthoredExit"]["timings"]["FrameTime"]["max_ms"], 2400)
            self.assertEqual(report["simulation_delta"]["fixture_samples"]["samples"], 5)

    def test_station_unknown_mixed_or_phase_mismatched_scenarios_rejected(self):
        mutations = [lambda rows: rows[0].update({analysis.STAGES[0]: 3}),
                     lambda rows: rows[0].update({analysis.STAGES[0]: 1}),
                     lambda rows: rows[0].update({analysis.STAGES[1]: 7}),
                     lambda rows: rows[0].update({analysis.STAGES[1]: 3.5})]
        for mutation in mutations:
            with tempfile.TemporaryDirectory(prefix="ss-csv-test-") as folder:
                with self.assertRaises(ValueError):
                    self.report(self.station_capture(folder, mutate=mutation))
        with tempfile.TemporaryDirectory(prefix="ss-csv-test-") as folder:
            with self.assertRaises(ValueError):
                self.report(self.station_capture(folder, omit=analysis.STAGES[0]))

    def test_post_update_docking_phase_can_differ_from_earlier_gamemode_sample(self):
        with tempfile.TemporaryDirectory(prefix="ss-csv-test-") as folder:
            report = self.report(self.station_capture(folder, mutate=lambda rows: rows[2].update({analysis.STATE[0]: 5})))
            self.assertEqual(report["station_fixture"]["phase_sample_differences"], 1)
            self.assertEqual(report["station_fixture"]["stages"]["Docking"]["simulation_seconds"], 3)
            self.assertEqual(report["phase_segments"][2]["phase_name"], "Approach")

    def test_station_focus_loss_cannot_claim_all_foreground(self):
        with tempfile.TemporaryDirectory(prefix="ss-csv-test-") as folder:
            report = self.report(self.station_capture(folder, mutate=lambda rows: rows[-1].update({analysis.SOAK[-1]: 0})))
            self.assertFalse(report["station_fixture"]["all_fixture_frames_foreground"])


if __name__ == "__main__":
    unittest.main()
