"""Regression coverage for exact source integrity across Git text checkouts."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ss_source_digests", ROOT / "Scripts/SourceDigests.py")
digest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(digest)


class SourceDigestTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="spacesurvival-digest-")
        self.folder = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def check(self, suffix, actual, expected, wanted):
        path = self.folder / ("source" + suffix)
        path.write_bytes(actual)
        self.assertEqual(digest.matches(path, hashlib.sha256(expected).hexdigest()), wanted)
        self.assertEqual(path.read_bytes(), actual, "A digest comparison must never rewrite input")

    def test_obj_mtl_json_both_complete_serializations(self):
        for suffix in (".obj", ".mtl", ".json"):
            with self.subTest(suffix=suffix):
                lf = b"first\nsecond\n"
                crlf = b"first\r\nsecond\r\n"
                self.check(suffix, lf, crlf, True)
                self.check(suffix, crlf, lf, True)
                self.check(suffix, lf, lf, True)
                self.check(suffix, crlf, crlf, True)

    def test_no_newline_or_missing_final_newline_is_not_added(self):
        self.check(".obj", b"first", b"first\n", False)
        self.check(".obj", b"first\nsecond", b"first\r\nsecond", True)

    def test_geometry_material_and_json_values_remain_exact(self):
        for suffix, original, changed in (
            (".obj", b"v 1 2 3\n", b"v 1 2 4\r\n"),
            (".mtl", b"Kd 1 0 0\n", b"Kd 0 1 0\r\n"),
            (".json", b'{"price":150}\n', b'{"price":0}\r\n'),
        ):
            with self.subTest(suffix=suffix):
                self.check(suffix, changed, original, False)

    def test_json_whitespace_and_key_order_are_not_canonicalized(self):
        original = b'{"a":1,"b":2}\n'
        self.check(".json", b'{"a": 1,"b": 2}\r\n', original, False)
        self.check(".json", b'{"b":2,"a":1}\r\n', original, False)

    def test_mixed_line_endings_only_match_their_own_raw_hash(self):
        mixed = b"first\r\nsecond\n"
        self.check(".obj", mixed, mixed, True)
        self.check(".obj", mixed, b"first\nsecond\n", False)
        self.check(".obj", b"first\nsecond\n", mixed, False)

    def test_bare_carriage_return_is_not_normalized(self):
        self.check(".mtl", b"first\rsecond\r", b"first\nsecond\n", False)

    def test_binary_and_non_allowlisted_text_remain_raw_only(self):
        for suffix in (".glb", ".uasset", ".umap", ".png", ".wav", ".blend", ".py", ".hlsl", ".txt"):
            with self.subTest(suffix=suffix):
                self.check(suffix, b"binary\r\nbytes", b"binary\nbytes", False)
                self.check(suffix, b"binary\r\nbytes", b"binary\r\nbytes", True)

    def test_invalid_utf8_and_nul_are_not_text_variants(self):
        self.check(".obj", b"\xff\r\n", b"\xff\n", False)
        self.check(".json", b'{"a":"\0"}\r\n', b'{"a":"\0"}\n', False)

    def test_utf8_bom_and_non_ascii_are_preserved(self):
        lf = b"\xef\xbb\xbf" + "name cafÃ©\n".encode("utf-8")
        self.check(".mtl", lf.replace(b"\n", b"\r\n"), lf, True)
        self.check(".mtl", lf[3:], lf, False)

    def test_invalid_expected_hash_fails_closed(self):
        path = self.folder / "source.obj"
        path.write_bytes(b"source\n")
        for expected in (None, "", "0" * 63, "z" * 64, 0):
            with self.subTest(expected=expected):
                self.assertFalse(digest.matches(path, expected))


class FreshExportCandidateGateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="spacesurvival-candidate-gate-")
        self.folder = Path(self.temporary.name)
        self.gate = runpy.run_path(str(ROOT / "Scripts/TestFreshCheckout.py"))["require_registered_candidates"]

    def tearDown(self):
        self.temporary.cleanup()

    def test_historical_pipeline_can_omit_unregistered_candidates(self):
        self.assertEqual(self.gate("pass", self.folder), [])

    def test_registered_swift_report_is_required(self):
        source = 'path = "Scripts/AuthorSwiftCandidate.py"'
        with self.assertRaisesRegex(AssertionError, "SwiftCandidate/Report.json"):
            self.gate(source, self.folder)
        report = self.folder / "ContentSource/SwiftCandidate/Report.json"
        report.parent.mkdir(parents=True)
        report.write_text("{}\n", encoding="utf-8")
        self.assertEqual(self.gate(source, self.folder), ["ContentSource/SwiftCandidate/Report.json"])

    def test_registered_v3_report_is_required_but_comments_do_not_register(self):
        self.assertEqual(self.gate("# Scripts/AuthorFieldCandidatesV3.py", self.folder), [])
        with self.assertRaisesRegex(AssertionError, "FieldCandidates/V3/SourceReport.json"):
            self.gate('path = "Scripts/AuthorFieldCandidatesV3.py"', self.folder)


if __name__ == "__main__":
    unittest.main()
