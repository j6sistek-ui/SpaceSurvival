"""Native asset library in a second Blender window, built once from cached proxies."""
from pathlib import Path
import hashlib
import json
import subprocess
import uuid

import bpy

from . import core

_job = {'process': None}
_watch = {'attempted': None, 'root': None}
_sync = {'id': None, 'stage': None}


def sync_library_tick():
    """Poll the one-shot editor job, then build/refresh the local Blender browser."""
    from . import editor_link
    try:
        if _sync['stage'] == 'export':
            status = editor_link.link.call("__import__('ss_catalog_refresh').manual_refresh_status(" + repr(_sync['id']) + ')')
            if status['status'] == 'failed':
                raise RuntimeError(status['error'])
            if status['status'] != 'complete':
                bpy.context.scene.ss_link.status = f"Rescanning Unreal: {status['processed']}/{status['total']} meshes"
                return 1.0
            bpy.ops.ss_link.load_catalog()
            _watch['attempted'] = catalog_digest()
            _sync['stage'] = 'prepare'
            if _job['process'] is None:
                if 'FINISHED' not in bpy.ops.ss_link.prepare_library():
                    raise RuntimeError('Could not prepare the downloaded geometry')
            return 1.0
        if _job['process'] is not None:
            return 1.0
        manifest = asset_dir() / 'build.json'
        built = json.loads(manifest.read_text()) if manifest.is_file() else {}
        if built.get('catalog_digest') != catalog_digest():
            raise RuntimeError('Library preparation failed or its catalogue changed; rescan again')
        attach_library()
        refresh_browser_windows()
        bpy.context.scene.ss_link.status = f"Library ready: {built['assets']} parts. Automatic refresh setting unchanged."
    except Exception as exc:
        bpy.context.scene.ss_link.status = f'Library rescan failed: {exc}'
    _sync.update(id=None, stage=None)
    return None


class SSLINK_OT_sync_library(bpy.types.Operator):
    bl_idname = 'ss_link.sync_library'
    bl_label = 'Rescan & Download Library'
    bl_description = 'Scan installed Unreal assets, export local geometry previews and refresh Blender; no Fab downloads or automatic refresh'

    def execute(self, context):
        from . import editor_link
        if _sync['stage'] is not None:
            self.report({'INFO'}, 'A library rescan is already running')
            return {'CANCELLED'}
        try:
            root = core.project_root()
            if not root or not (root / 'SpaceSurvival.uproject').is_file():
                raise RuntimeError('Rescanning needs the full Unreal project; use Import Library on an offline computer')
            if not editor_link.link.connected:
                editor_link.link.connect()
            node = editor_link.link.node
            if Path(node.get('project_root', '')).resolve() != root.resolve():
                raise RuntimeError('Connected Unreal editor belongs to another project')
            # A running editor can still have the previous helper in memory.
            # Upgrade it only while idle; never abandon an in-progress export.
            code = """import json, importlib, ss_catalog_refresh
if not hasattr(ss_catalog_refresh, 'request_manual_refresh'):
    if ss_catalog_refresh._state.get('busy') or ss_catalog_refresh._state.get('steps') is not None:
        raise RuntimeError('The previous automatic export is still running; retry after it finishes')
    ss_catalog_refresh.unregister()
    importlib.reload(ss_catalog_refresh)
    ss_catalog_refresh.register()
print(json.dumps(ss_catalog_refresh.request_manual_refresh()))
"""
            try:
                response = editor_link.link.run(code)
            except RuntimeError:
                if editor_link.link.connected:
                    raise  # An editor-side failure, rather than a stale socket.
                editor_link.link.connect()
                if Path(editor_link.link.node.get('project_root', '')).resolve() != root.resolve():
                    raise RuntimeError('Reconnected Unreal editor belongs to another project')
                # The request is idempotent while running: a lost reply cannot
                # start a second export when this one reconnects.
                response = editor_link.link.run(code)
            status = json.loads(response)
            _sync.update(id=status['id'], stage='export')
            context.scene.ss_link.status = 'Rescanning installed Unreal assets...'
            bpy.app.timers.register(sync_library_tick, first_interval=1.0)
        except Exception as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        return {'FINISHED'}


def catalog_digest():
    lib = core.library_dir()
    digest = hashlib.sha256()
    for name in ('catalog.json', core.SENT):
        path = lib / name
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


def refresh_browser_windows():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'FILE_BROWSER' and area.ui_type == 'ASSETS':
                with bpy.context.temp_override(window=window, area=area):
                    bpy.ops.asset.library_refresh()


def watch_catalog():
    try:
        lib = core.library_dir()
        if lib is None or not (lib / 'catalog.json').is_file():
            return 5.0
        enabled = bpy.context.scene.ss_link.auto_refresh_library
        if not enabled or _job['process'] is not None:
            return 5.0
        digest = catalog_digest()
        if _watch['root'] != str(lib):
            _watch.update(root=str(lib), attempted=None)
        manifest = asset_dir() / 'build.json'
        built = json.loads(manifest.read_text()).get('catalog_digest') if manifest.is_file() else None
        if digest != built and digest != _watch['attempted']:
            _watch['attempted'] = digest
            bpy.ops.ss_link.load_catalog()
            bpy.ops.ss_link.prepare_library()
    except Exception as exc:
        bpy.context.scene.ss_link.status = f'Library refresh: {exc}'
    return 5.0


def asset_dir():
    lib = core.library_dir()
    if not lib:
        raise RuntimeError('Choose a project or portable library folder in SS Link preferences')
    return lib / 'BlenderAssets'


def attach_library():
    folder = asset_dir()
    if not (folder / 'build.json').is_file():
        raise RuntimeError('Press Prepare Large Library first; its status appears below the button')
    libs = bpy.context.preferences.filepaths.asset_libraries
    for lib in list(libs):
        old = Path(lib.path)
        if lib.name.startswith('SpaceSurvival') and old.resolve() != folder.resolve() and (old / 'build.json').is_file():
            # Switch the registered snapshot, not its files. Otherwise ALL shows both libraries twice.
            libs.remove(lib)
    found = next((lib for lib in libs if Path(lib.path).resolve() == folder.resolve()), None)
    if not found:
        found = libs.new(name='SpaceSurvival', directory=str(folder))
    found.import_method = 'APPEND'
    return found


def build_finished():
    proc = _job['process']
    if proc is None:
        return None
    if proc.poll() is None:
        return 1.0
    _job['process'] = None
    status = 'Large library ready. Press Pop Out Library.' if proc.returncode == 0 else 'Library build failed; see Artifacts/PrefabLibrary/build-assets.log'
    for scene in bpy.data.scenes:
        scene.ss_link.status = status
    if proc.returncode == 0:
        try:
            attach_library()
            refresh_browser_windows()
        except Exception as exc:
            for scene in bpy.data.scenes:
                scene.ss_link.status = f'Library built; browser refresh needs attention: {exc}'
    return None


class SSLINK_OT_prepare_library(bpy.types.Operator):
    bl_idname = 'ss_link.prepare_library'
    bl_label = 'Prepare Large Library'
    bl_description = 'Build the large thumbnail browser from cached meshes; runs in the background without Unreal'

    def execute(self, context):
        if _job['process'] and _job['process'].poll() is None:
            self.report({'INFO'}, 'Library preparation is already running')
            return {'CANCELLED'}
        try:
            folder = asset_dir()
            folder.mkdir(parents=True, exist_ok=True)
            with (folder.parent / 'build-assets.log').open('w', encoding='utf-8') as log:
                _job['process'] = subprocess.Popen([
                    bpy.app.binary_path, '--background', '--factory-startup', '--python-exit-code', '1',
                    '--python', str(core.tool_path('build_asset_library.py')), '--',
                    '--project', str(core.project_root()), '--output', str(folder)],
                    stdout=log, stderr=subprocess.STDOUT,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            context.scene.ss_link.status = 'Preparing large library in the background...'
            bpy.app.timers.register(build_finished, first_interval=1.0)
        except Exception as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        return {'FINISHED'}


class SSLINK_OT_popout_library(bpy.types.Operator):
    bl_idname = 'ss_link.popout_library'
    bl_label = 'Pop Out Library'
    bl_description = 'Open a large searchable thumbnail window; move it to another monitor and drag assets into your scene'

    def execute(self, context):
        try:
            attach_library()
            before = set(context.window_manager.windows)
            bpy.ops.wm.window_new()
            window = next(w for w in context.window_manager.windows if w not in before)
            area = max(window.screen.areas, key=lambda a: a.width * a.height)
            area.type = 'FILE_BROWSER'
            area.ui_type = 'ASSETS'
            with bpy.context.temp_override(window=window, area=area):
                bpy.ops.screen.screen_full_area(use_hide_panels=False)
            area = next(a for a in window.screen.areas if a.type == 'FILE_BROWSER')
            root_id = str(uuid.uuid5(uuid.UUID('dc01c7de-068a-49c6-b6f5-6a47e5f77724'), 'SpaceSurvival'))

            def configure():
                try:
                    if window not in list(bpy.context.window_manager.windows):
                        return None
                    params = area.spaces.active.params
                    if params is None:
                        return 0.1
                    params.asset_library_reference = 'ALL'
                    params.catalog_id = root_id
                    params.display_size = 128
                    return None
                except (ReferenceError, TypeError, AttributeError):
                    return None

            bpy.app.timers.register(configure, first_interval=0.1)
        except Exception as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        return {'FINISHED'}


classes = (SSLINK_OT_sync_library, SSLINK_OT_prepare_library, SSLINK_OT_popout_library)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.app.timers.register(watch_catalog, first_interval=5.0, persistent=True)


def unregister():
    if bpy.app.timers.is_registered(sync_library_tick):
        bpy.app.timers.unregister(sync_library_tick)
    if bpy.app.timers.is_registered(watch_catalog):
        bpy.app.timers.unregister(watch_catalog)
    if bpy.app.timers.is_registered(build_finished):
        bpy.app.timers.unregister(build_finished)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
