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
        if (core.project_root() / 'SpaceSurvival.uproject').exists():
            marker = lib / 'auto-refresh.enabled'
            if enabled and not marker.exists():
                marker.touch()
            elif not enabled and marker.exists():
                marker.unlink()
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


classes = (SSLINK_OT_prepare_library, SSLINK_OT_popout_library)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.app.timers.register(watch_catalog, first_interval=5.0, persistent=True)


def unregister():
    if bpy.app.timers.is_registered(watch_catalog):
        bpy.app.timers.unregister(watch_catalog)
    if bpy.app.timers.is_registered(build_finished):
        bpy.app.timers.unregister(build_finished)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
