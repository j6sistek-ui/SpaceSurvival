"""A changed proxy must not alias an old scene mesh or cached placeholder."""
import ast
import importlib.util
import os
from pathlib import Path
import tempfile
import types
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('proxy_cache', HERE / 'ss_live_link/proxy_cache.py')
cache = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cache)


class SnapshotProxyCacheTests(unittest.TestCase):
    def test_changed_bytes_same_path_size_and_time_get_new_mesh(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'wall.glb'
            path.write_bytes(b'first mesh')
            stamp = path.stat()
            old = cache.snapshot_mesh_key('/Game/Wall.Wall', path)
            path.write_bytes(b'other mesh')
            os.utime(path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
            self.assertNotEqual(old, cache.snapshot_mesh_key('/Game/Wall.Wall', path))

    def test_same_content_reuses_short_key_without_aliasing_assets(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / 'a.glb', Path(folder) / 'b.glb'
            a.write_bytes(b'geometry')
            b.write_bytes(a.read_bytes())
            asset = '/Game/' + 'VeryLongAssetName' * 20
            key = cache.snapshot_mesh_key(asset, a)
            self.assertEqual(key, cache.snapshot_mesh_key(asset, b))
            self.assertLessEqual(len(key.encode()), 63)
            self.assertNotEqual(key, cache.snapshot_mesh_key(asset + '2', a))
            self.assertNotEqual(key, 'SSProxy:' + asset)

    def test_missing_geometry_never_falls_back_to_old_cached_box(self):
        # Execute the real helper against a minimal Blender mesh registry. The old
        # cached placeholder must remain untouched and must not satisfy this import.
        parsed = ast.parse((HERE / 'ss_live_link/core.py').read_text(encoding='utf-8'))
        function = next(node for node in parsed.body if isinstance(node, ast.FunctionDef) and node.name == 'proxy_mesh')
        old_mesh = object()
        registry = {'SSProxy:/Game/Wall.Wall': old_mesh}
        with tempfile.TemporaryDirectory() as folder:
            scope = {'bpy': types.SimpleNamespace(data=types.SimpleNamespace(meshes=registry)),
                     'library_dir': lambda: Path(folder),
                     'placeholder_mesh': lambda row: self.fail('Snapshot used a bounds box')}
            exec(compile(ast.Module(body=[function], type_ignores=[]), 'core.proxy_mesh', 'exec'), scope)
            with self.assertRaisesRegex(RuntimeError, 'No real mesh geometry'):
                scope['proxy_mesh']({'asset': '/Game/Wall.Wall', 'proxy': 'missing.glb'},
                                    cache_key='SSSnapshot:newrevision', require_geometry=True)
        self.assertIs(registry['SSProxy:/Game/Wall.Wall'], old_mesh)


if __name__ == '__main__':
    unittest.main()
