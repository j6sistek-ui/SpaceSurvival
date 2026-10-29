"""Exercise the manual Blender button with a simulated editor and real proxy preparation.

Run in isolated background Blender; no Unreal connection or owner preferences are used.
"""
import json
from pathlib import Path
import sys
import tempfile
import time

import bpy

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import ss_live_link as sl

with tempfile.TemporaryDirectory(prefix='ss-sync-') as scratch:
    root = Path(scratch)
    lib = root / 'Artifacts/PrefabLibrary'
    lib.mkdir(parents=True)
    project = root / 'SpaceSurvival.uproject'
    project.touch()
    sl.core.project_root = lambda: root
    sl.core.tool_path = lambda name: TOOLS / name
    sl.register()
    bpy.ops.mesh.primitive_cube_add()
    original = bpy.context.object
    original.name = 'OwnerPlacement'
    matrix = original.matrix_world.copy()
    bpy.ops.export_scene.gltf(filepath=str(lib / 'cube.glb'), export_format='GLB', use_selection=True)
    row = {'asset': '/Game/Test/Old.Old', 'name': 'Old', 'pack': 'Test', 'group': 'Building',
           'category': 'Walls', 'proxy': 'cube.glb', 'materials': [],
           'origin': [0, 0, 0], 'extent': [100, 100, 100], 'triangles': 12}
    fresh = dict(row, asset='/Game/Test/New.New', name='New')
    (lib / 'catalog.json').write_text(json.dumps({'meshes': [row]}))
    bpy.ops.ss_link.load_catalog()

    class Editor:
        connected = True
        node = {'project_root': str(root)}
        attempts = 0
        polls = 0
        connections = 0

        def connect(self):
            self.connected = True
            self.connections += 1

        def disconnect(self):
            self.connected = False

        def run(self, _code):
            self.attempts += 1
            if self.attempts == 1:
                self.connected = False
                raise RuntimeError('Stale socket')
            return json.dumps({'id': 'one-shot', 'status': 'queued'})

        def call(self, _expression):
            self.polls += 1
            if self.polls == 1:
                return {'status': 'running', 'processed': 1, 'total': 2}
            (lib / 'catalog.json').write_text(json.dumps({'meshes': [row, fresh]}))
            return {'status': 'complete'}

    editor = Editor()
    sl.editor_link.link = editor
    assert not bpy.context.scene.ss_link.auto_refresh_library
    assert 'FINISHED' in bpy.ops.ss_link.sync_library()
    assert editor.connections == 1 and editor.attempts == 2
    assert 'CANCELLED' in bpy.ops.ss_link.sync_library(), 'Duplicate click started a second job'
    assert sl.popout.sync_library_tick() == 1.0
    assert '1/2' in bpy.context.scene.ss_link.status
    assert sl.popout.sync_library_tick() == 1.0
    assert len(bpy.context.scene.ss_link.parts) == 2, 'New Unreal entry never reached Blender'
    deadline = time.monotonic() + 30
    while sl.popout._job['process'].poll() is None and time.monotonic() < deadline:
        time.sleep(0.05)
    assert sl.popout._job['process'].poll() == 0
    sl.popout.build_finished()
    assert sl.popout.sync_library_tick() is None
    assert 'Library ready: 2 parts' in bpy.context.scene.ss_link.status
    built = json.loads((lib / 'BlenderAssets/build.json').read_text())
    assert fresh['asset'] in built['entries']
    assert (lib / 'BlenderAssets' / built['entries'][fresh['asset']]['file']).is_file()
    assert not (lib / 'auto-refresh.enabled').exists()
    assert original.name in bpy.data.objects and original.matrix_world == matrix

    editor.call = lambda _expression: {'status': 'failed', 'error': 'Export refused'}
    sl.popout._sync.update(id='failure', stage='export')
    assert sl.popout.sync_library_tick() is None
    assert 'Export refused' in bpy.context.scene.ss_link.status
    assert sl.popout._job['process'] is None
    editor.node = {'project_root': str(root / 'other-project')}
    try:
        bpy.ops.ss_link.sync_library()
        raise AssertionError('Wrong editor project was accepted')
    except RuntimeError as exc:
        assert 'another project' in str(exc)
    assert editor.attempts == 2
    sl.unregister()
print('SS_LIBRARY_SYNC_OK: stale-link retry, duplicate guard, new asset, real preparation, auto-off, owner placement, failure and project isolation')
