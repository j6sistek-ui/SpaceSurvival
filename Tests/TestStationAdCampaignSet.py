"""Source-boundary and partial-staging regressions; no Unreal is invoked."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import runpy
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "Scripts/StationAdCampaignSet.py"
spec = importlib.util.spec_from_file_location("station_ads", SCRIPT)
ads = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ads)


class NativeObject:
    def __init__(self, path=None):
        self.path, self.properties = path, {"imported_object_paths": []}

    def set_editor_property(self, key, value):
        self.properties[key] = value

    def get_editor_property(self, key):
        return self.properties[key]

    def get_path_name(self):
        return self.path


class FakeEngine:
    Texture2D = NativeObject
    AssetImportTask = NativeObject
    TextureCompressionSettings = SimpleNamespace(TC_BC7="BC7")
    TextureGroup = SimpleNamespace(TEXTUREGROUP_WORLD="WORLD")
    TextureMipGenSettings = SimpleNamespace(TMGS_FROM_TEXTURE_GROUP="GROUP")
    TextureAddress = SimpleNamespace(TA_CLAMP="CLAMP")

    def __init__(self, fail_on=None, unexpected_name=False):
        self.assets, self.calls, self.checked = {}, [], []
        self.folder, self.fail_on, self.unexpected_name = False, fail_on, unexpected_name
        self.EditorAssetLibrary = SimpleNamespace(does_asset_exist=self.exists,
                                                 does_directory_exist=lambda path: self.folder)
        self.AssetToolsHelpers = SimpleNamespace(get_asset_tools=lambda: self)

    def exists(self, path):
        self.checked.append(path)
        return path in self.assets

    def load_asset(self, path):
        return self.assets.get(path)

    def import_asset_tasks(self, tasks):
        task = tasks[0]
        self.calls.append(dict(task.properties))
        path = task.properties["destination_path"] + "/" + task.properties["destination_name"]
        if self.unexpected_name:
            path += "_Unexpected"
        self.folder = True
        identity = path + "." + path.rsplit("/", 1)[1]
        self.assets[path] = NativeObject(identity)
        task.properties["imported_object_paths"] = [identity]
        if len(self.calls) == self.fail_on:
            raise RuntimeError("Import failed after creating a texture")


class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT, prefix=".station-ad-test-")
        self.folder = Path(self.temp.name) / "art"
        self.folder.mkdir()
        self.manifest = self.folder / "manifest5.json"
        self.rows = []
        for index in range(5):
            path = self.folder / (str(index) + ".png")
            path.write_bytes(("reviewed source " + str(index)).encode())
            self.rows.append({"campaign_id": "M0" + str(index), "file": path.name,
                              "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        self.write_manifest()

    def tearDown(self):
        self.temp.cleanup()

    def write_manifest(self):
        self.manifest.write_text(json.dumps({"room": "Market", "campaign_count": 5,
                                            "campaigns": self.rows}), encoding="utf-8")
        self.sha = hashlib.sha256(self.manifest.read_bytes()).hexdigest()

    def stage(self, engine, stage_id="Test1"):
        return ads.stage_textures(engine, self.manifest, self.sha, "Market", stage_id)

    def test_read_only_cli_and_variants_do_not_increase_count(self):
        self.rows[0]["variants"] = [{"file": "nonselected.png"}]
        self.write_manifest()
        before = {p.name: p.read_bytes() for p in self.folder.iterdir()}
        with patch.object(sys, "argv", [str(SCRIPT), str(self.manifest), self.sha, "--room", "Market"]):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                runpy.run_path(str(SCRIPT), run_name="__main__")
        self.assertEqual(len(json.loads(output.getvalue())["campaigns"]), 5)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.folder.iterdir()})

    def test_changed_manifest_and_source_are_rejected(self):
        self.manifest.write_bytes(self.manifest.read_bytes() + b" ")
        with self.assertRaises(ValueError): self.stage(FakeEngine())
        self.write_manifest()
        (self.folder / "0.png").write_bytes(b"changed")
        with self.assertRaises(ValueError): self.stage(FakeEngine())

    def test_escape_absolute_path_and_destination_traversal(self):
        outside = self.folder.parent / "outside.png"
        outside.write_bytes(b"outside")
        for filename in ("../outside.png", str(outside)):
            self.rows[0].update(file=filename, sha256=hashlib.sha256(outside.read_bytes()).hexdigest())
            self.write_manifest()
            with self.assertRaises(ValueError): self.stage(FakeEngine())
        self.rows[0].update(file="0.png", sha256=hashlib.sha256((self.folder / "0.png").read_bytes()).hexdigest())
        self.write_manifest()
        for suffix in ("../Operations", "/Game/Other", "bad/name"):
            with self.assertRaises(ValueError): self.stage(FakeEngine(), suffix)

    def test_duplicate_ids_families_and_same_bitmap_are_not_five(self):
        for field, value in (("campaign_id", "m00"), ("family_id", "Shared"),
                             ("file", "0.png")):
            original = json.loads(json.dumps(self.rows))
            if field == "family_id": self.rows[0][field] = value
            self.rows[1][field] = value
            if field == "file": self.rows[1]["sha256"] = self.rows[0]["sha256"]
            self.write_manifest()
            with self.assertRaises(ValueError): self.stage(FakeEngine())
            self.rows = original

    def test_existing_last_destination_blocks_all_mutation(self):
        engine = FakeEngine()
        target = ads.BASE + "MarketCampaignsTest1/Textures/T_M04"
        engine.assets[target] = NativeObject(target)
        with self.assertRaises(ValueError): self.stage(engine)
        self.assertEqual(len(engine.checked), 5)
        self.assertEqual(engine.calls, [])

    def test_success_remains_unsaved_and_unverified(self):
        engine = FakeEngine()
        report = self.stage(engine)
        self.assertEqual(len(report["created_paths"]), 5)
        self.assertEqual(report["status"], "STAGED_UNVERIFIED")
        self.assertFalse(report["saved"] or report["compilation_verified"] or report["dimensions_verified"])
        self.assertTrue(all(c["replace_existing"] is False and c["save"] is False for c in engine.calls))

    def test_partial_error_retains_created_identity_and_blocks_retry(self):
        engine = FakeEngine(fail_on=2)
        with self.assertRaises(ads.StageError) as failure: self.stage(engine)
        report = failure.exception.report
        self.assertEqual(len(report["observed_existing_paths"]), 2)
        self.assertIn("Import failed", report["error"])
        self.assertEqual(len(report["last_task_imported_paths"]), 1)
        with self.assertRaises(ValueError): self.stage(engine)
        self.assertEqual(len(engine.calls), 2)

    def test_unexpected_import_name_is_retained_and_blocks_retry(self):
        engine = FakeEngine(unexpected_name=True)
        with self.assertRaises(ads.StageError) as failure: self.stage(engine)
        self.assertIn("Unexpected", failure.exception.report["import_results"][0]["imported_object_paths"][0])
        with self.assertRaises(ValueError): self.stage(engine)
        self.assertEqual(len(engine.calls), 1)

    def test_held_rooms_and_wrong_manifest_room_are_rejected(self):
        for room in ("T", "Central", "L", "R"):
            with self.assertRaises(ValueError): ads.inspect_sources(self.manifest, self.sha, room)


if __name__ == "__main__":
    unittest.main()
