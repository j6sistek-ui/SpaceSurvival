"""Portable stale/wrong-destination and transform rejection tests; no engine needed."""
import copy
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('wayfarer_safety', ROOT / 'Content/Python/ss_wayfarer.py')
module = importlib.util.module_from_spec(spec)
unreal = types.SimpleNamespace(Paths=types.SimpleNamespace(project_dir=lambda: str(ROOT), convert_relative_path_to_full=lambda p: p))
with patch.dict(sys.modules, {'unreal': unreal, 'ss_prefabs': types.SimpleNamespace()}):
    spec.loader.exec_module(module)

MATRIX = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [100, 200, 300, 1]]


class WayfarerSafetyTests(unittest.TestCase):
    def setUp(self):
        self.state = {'guid': 'actor1', 'asset': '/Game/Wall.Wall', 'matrix': copy.deepcopy(MATRIX), 'materials': ['/Game/Surface.Surface'], 'name': 'Wall', 'parent': ''}
        self.snapshot = {'project_root': str(ROOT), 'target_map': module.TARGET, 'snapshot_id': 'snapshot1'}
        self.payload = dict(self.snapshot, objects=[dict(self.state, link='link1', base=module.state_digest(self.state))])
        self.current = {'actor1': self.state}

    def validate(self):
        return module.preflight(self.payload, self.snapshot, self.current, ROOT, module.TARGET)

    def test_selected_transform_change_is_allowed(self):
        self.payload['objects'][0]['matrix'] = copy.deepcopy(MATRIX)
        self.payload['objects'][0]['matrix'][3][0] += 25
        self.assertTrue(self.validate())

    def test_native_guid_script_method_preserves_32_hex_identity(self):
        value = '00112233AABBCCDDFFEEDDCC98765432'
        # Match the native wrapper: a ScriptMethod, with no a/b/c/d attributes.
        guid = types.SimpleNamespace(to_string=lambda: value)
        actor = types.SimpleNamespace(get_editor_property=lambda name: guid if name == 'actor_guid' else None)
        self.assertEqual(module._guid(actor), value.lower())
        guid.to_string = lambda: '0' * 32
        self.assertEqual(module._guid(actor), '')
        guid.to_string = lambda: '<Struct Guid at 0x1234>'
        with self.assertRaisesRegex(ValueError, 'invalid persistent actor GUID'):
            module._guid(actor)

    def test_new_placement_is_explicit(self):
        row = self.payload['objects'][0]
        row.pop('guid')
        with self.assertRaisesRegex(ValueError, 'not marked as new'):
            self.validate()
        row['new'] = True
        self.assertTrue(self.validate())

    def test_other_map_refused(self):
        self.payload['target_map'] = '/Game/OutpostSandbox/L_AsteroidOutpost'
        with self.assertRaisesRegex(ValueError, 'destination map'):
            self.validate()

    def test_other_checkout_refused(self):
        self.payload['project_root'] = str(ROOT / 'wrong-checkout')
        with self.assertRaisesRegex(ValueError, 'another project'):
            self.validate()

    def test_mismatched_snapshot_refused(self):
        self.payload['snapshot_id'] = 'different'
        with self.assertRaisesRegex(ValueError, 'snapshot identity'):
            self.validate()

    def test_unreal_edits_require_fresh_snapshot(self):
        for field, value in [('name', 'Unreal rename'), ('materials', ['NewMaterial']), ('parent', 'NewParent'), ('matrix', MATRIX[:3] + [[999, 0, 0, 1]])]:
            with self.subTest(field=field):
                self.current = {'actor1': dict(self.state, **{field: value})}
                with self.assertRaisesRegex(ValueError, 'Unreal changed'):
                    self.validate()

    def test_missing_actor_is_never_recreated(self):
        self.current = {}
        with self.assertRaisesRegex(ValueError, 'missing or no longer editable'):
            self.validate()

    def test_blueprint_context_cannot_replace_actor(self):
        self.payload['objects'][0]['asset'] = '/Game/Another.Another'
        with self.assertRaisesRegex(ValueError, 'cannot replace'):
            self.validate()

    def test_duplicate_original_refused(self):
        self.payload['objects'].append(dict(self.payload['objects'][0], link='link2'))
        with self.assertRaisesRegex(ValueError, 'share an Unreal actor identity'):
            self.validate()

    def test_duplicate_new_link_refused(self):
        self.payload['objects'].append(dict(self.payload['objects'][0], guid=None, new=True))
        with self.assertRaisesRegex(ValueError, 'distinct link identity'):
            self.validate()

    def test_remove_refused(self):
        self.payload['remove'] = ['actor1']
        with self.assertRaisesRegex(ValueError, 'never deletes'):
            self.validate()

    def test_invalid_pose_refused(self):
        for matrix in [[], [[float('nan'), 0, 0, 0]] + MATRIX[1:], [[0, 0, 0, 0]] + MATRIX[1:], [[1, 1, 0, 0]] + MATRIX[1:]]:
            with self.subTest(matrix=matrix):
                with self.assertRaises(ValueError):
                    module.checked_matrix(matrix)

    def test_required_apartment_must_be_loaded_with_mesh_children(self):
        package = module.REQUIRED_LEVELS[0]
        instances = [{'package': package}]
        ready = {'package': package, 'loaded': True, 'visible': True, 'pending': False, 'mesh_placements': 100}
        self.assertEqual(module.level_readiness(instances, [ready]), [])
        self.assertTrue(module.level_readiness([], []))
        self.assertTrue(module.level_readiness(instances, []))
        for change in ({'loaded': False}, {'visible': False}, {'pending': True}, {'mesh_placements': 0}):
            with self.subTest(change=change):
                self.assertTrue(module.level_readiness(instances, [dict(ready, **change)]))

    def test_one_loaded_copy_cannot_mask_second_unloaded_instance(self):
        package = module.REQUIRED_LEVELS[0]
        instances = [{'package': package}, {'package': package}]
        ready = {'package': package, 'loaded': True, 'visible': True, 'pending': False, 'mesh_placements': 100}
        self.assertTrue(module.level_readiness(instances, [ready]))

    def test_non_required_unloaded_instance_is_also_refused(self):
        package = '/Game/OtherRoom'
        self.assertTrue(module.level_readiness([{'package': package}], [], required_levels=()))

    def test_stream_package_normalizes_editor_level_instance_package(self):
        original = '/Game/BuildingLibrary/Home/L_CrewApartment'
        stream = types.SimpleNamespace(get_world_asset_package_f_name=lambda:
                                       '/Temp/Game/BuildingLibrary/Home/L_CrewApartment_LevelInstance_55904599a21b4371_0')
        self.assertEqual(module._stream_package(stream), original)

    def test_stream_iterator_excludes_other_world_and_class_defaults(self):
        class Stream:
            def __init__(self, outer):
                self.outer = outer

            def get_outer(self):
                return self.outer

        world, other_world = object(), object()
        owned, foreign, default = Stream(world), Stream(other_world), Stream(Stream)
        with patch.object(module.u, 'LevelStreaming', Stream, create=True), \
                patch.object(module.u, 'ObjectIterator', lambda cls: [owned, foreign, default, Stream], create=True):
            self.assertEqual(module._streams(world), [owned])

    def test_stream_package_preserves_regular_package(self):
        package = '/Game/BuildingLibrary/Home/My_LevelInstance_Collection'
        stream = types.SimpleNamespace(get_world_asset_package_f_name=lambda: package)
        self.assertEqual(module._stream_package(stream), package)


if __name__ == '__main__':
    unittest.main()
