"""Portable library export/import. Imports validate and extract into a fresh folder."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tempfile
import zipfile

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper, ImportHelper

from . import core, popout


def import_archive(path, destination):
    """No source code from the ZIP is executed. Existing libraries and scenes are never overwritten."""
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        names = [i.filename for i in members]
        if len(names) != len(set(names)):
            raise ValueError('Archive contains duplicate file names')
        for info in members:
            parts = PurePosixPath(info.filename)
            if (parts.is_absolute() or '..' in parts.parts or '\\' in info.filename
                    or ':' in info.filename or not parts.parts or parts.parts[0] != 'SpaceSurvivalLibrary'):
                raise ValueError('Archive contains an unsafe path')
            if ((info.external_attr >> 16) & 0o170000) == 0o120000:
                raise ValueError('Archive contains a symbolic link')
        prefix = 'SpaceSurvivalLibrary/'
        manifest = json.loads(archive.read(prefix + 'SSPortableLibrary.json'))
        if manifest.get('schema_version') != 1 or not isinstance(manifest.get('files'), dict):
            raise ValueError('Unsupported library package')
        # Verify before creating any files. Unlisted executable/data payloads are not accepted.
        expected = {prefix + n for n in manifest['files']} | {prefix + 'SSPortableLibrary.json', prefix + 'README.txt'}
        if set(names) != expected:
            raise ValueError('Archive contents do not match the manifest')
        required = {'Artifacts/PrefabLibrary/catalog.json', 'Artifacts/PrefabLibrary/BlenderAssets/build.json',
                    'Artifacts/PrefabLibrary/BlenderAssets/blender_assets.cats.txt'}
        if not required.issubset(manifest['files']):
            raise ValueError('Archive is missing its catalog or prepared Blender library')
        for name, digest in manifest['files'].items():
            with archive.open(prefix + name) as source:
                actual = hashlib.file_digest(source, 'sha256').hexdigest()
            if actual != digest:
                raise ValueError(f'Library checksum failed: {name}')
        catalog = json.loads(archive.read(prefix + 'Artifacts/PrefabLibrary/catalog.json'))
        built = json.loads(archive.read(prefix + 'Artifacts/PrefabLibrary/BlenderAssets/build.json'))
        if not isinstance(catalog.get('meshes'), list) or not isinstance(built.get('entries'), dict):
            raise ValueError('Archive contains an invalid catalog')
        for entry in built['entries'].values():
            if 'Artifacts/PrefabLibrary/BlenderAssets/' + entry['file'] not in manifest['files']:
                raise ValueError('Archive is missing a prepared mesh')
        destination.mkdir(parents=True, exist_ok=True)
        needed = sum(info.file_size for info in members) + 256 * 1024 ** 2
        if shutil.disk_usage(destination).free < needed:
            raise RuntimeError(f'Import needs about {needed / 1024 ** 3:.1f} GiB free; the previous library is retained')
        fresh = Path(tempfile.mkdtemp(prefix='library-', dir=str(destination)))
        archive.extractall(fresh)
    return fresh / 'SpaceSurvivalLibrary'


class SSLINK_OT_export_library(bpy.types.Operator, ExportHelper):
    bl_idname = 'ss_link.export_library'
    bl_label = 'Export Library'
    bl_description = 'Package the current prepared library for another computer, without Unreal'
    filename_ext = '.zip'
    filter_glob: StringProperty(default='*.zip', options={'HIDDEN'})

    def execute(self, context):
        try:
            if popout._job['process'] is not None:
                raise RuntimeError('Wait for library preparation to finish before exporting')
            result = core.import_tool('package_portable').package(
                core.project_root(), core.project_root(), popout.asset_dir(), Path(self.filepath))
            context.scene.ss_link.status = f"Exported {result['assets']} library entries to {self.filepath}"
        except Exception as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        return {'FINISHED'}


class SSLINK_OT_import_library(bpy.types.Operator, ImportHelper):
    bl_idname = 'ss_link.import_library'
    bl_label = 'Import Library'
    bl_description = 'Import an offline library snapshot into a new folder; keep the previous library and open scene'
    filter_glob: StringProperty(default='*.zip', options={'HIDDEN'})

    def execute(self, context):
        try:
            folder = Path(bpy.utils.user_resource('DATAFILES', path='SSLinkLibraries', create=True))
            root = import_archive(self.filepath, folder)
            preferences = core.prefs()
            if preferences:
                preferences.project_root = str(root)
            core.write_config(project_root=str(root))
            core.load_catalog(force=True)
            bpy.ops.ss_link.load_catalog()
            popout.attach_library()
            bpy.ops.wm.save_userpref()
            context.scene.ss_link.status = 'Library imported. Open Pop Out Library; your current scene is unchanged.'
        except Exception as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        return {'FINISHED'}


classes = (SSLINK_OT_export_library, SSLINK_OT_import_library)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
