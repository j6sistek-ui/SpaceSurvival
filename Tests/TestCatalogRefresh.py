"""Exercise Slate re-entry during an export without starting Unreal."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


class CatalogRefreshTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.marker = Path(self.temp.name) / 'auto-refresh.enabled'
        self.marker.touch()
        self.warnings = []
        self.playing = False
        self.registry = types.SimpleNamespace(is_loading_assets=lambda: False)
        self.levels = types.SimpleNamespace(is_in_play_in_editor=lambda: self.playing)
        unreal = types.SimpleNamespace(
            LevelEditorSubsystem=object,
            get_editor_subsystem=lambda _type: self.levels,
            AssetRegistryHelpers=types.SimpleNamespace(get_asset_registry=lambda: self.registry),
            log_warning=self.warnings.append)
        self.prefabs = types.SimpleNamespace(
            LIBRARY=Path(self.temp.name), _static_meshes=lambda: ['/Game/Test.Mesh'],
            _source_stamp=lambda _path: 'unchanged')
        with patch.dict(sys.modules, unreal=unreal, ss_prefabs=self.prefabs):
            spec = importlib.util.spec_from_file_location(
                'refresh_under_test', Path(__file__).resolve().parents[1] /
                'Content/Python/ss_catalog_refresh.py')
            self.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.module)

    def test_export_pumping_slate_finishes_once_without_restart(self):
        events = []

        def export():
            events.append('start')
            self.module.tick(0)  # Unreal export/thumbnail work pumps Slate.
            events.append('yield')
            yield None
            events.append('finish')

        self.prefabs.catalog_steps = export
        for _ in range(5):
            self.module.tick(0)
        self.assertEqual(events, ['start', 'yield', 'finish'])
        self.assertEqual(self.warnings, [])
        self.assertIsNone(self.module._state['steps'])
        self.assertFalse(self.module._state['busy'])

    def test_real_failure_releases_guard_and_backs_off(self):
        calls = []

        def export():
            calls.append('attempt')
            self.module.tick(0)
            raise RuntimeError('export failed')
            yield None

        self.prefabs.catalog_steps = export
        for _ in range(5):
            self.module.tick(0)
        self.assertEqual(calls, ['attempt'])
        self.assertEqual(len(self.warnings), 1)
        self.assertFalse(self.module._state['busy'])

    def test_disabled_mid_pass_can_resume_same_source(self):
        calls = []

        def export():
            calls.append('export')
            yield None

        self.prefabs.catalog_steps = export
        self.module.tick(0)
        self.module.tick(0)
        self.marker.unlink()
        self.module.tick(0)
        self.marker.touch()
        self.module._state['next_scan'] = 0
        self.module.tick(0)
        self.module.tick(0)
        self.assertEqual(calls, ['export', 'export'])

    def test_play_does_not_start_export(self):
        self.playing = True
        self.prefabs.catalog_steps = lambda: self.fail('export during Play')
        self.module.tick(0)
        self.assertIsNone(self.module._state['steps'])
        self.assertFalse(self.module._state['busy'])


if __name__ == '__main__':
    unittest.main()
