"""The visual browser: the gallery page any web browser can open, and the thumbnails behind it.

The work is done by the sibling scripts in Tools/SSLiveLink (render_thumbnails.py in a second Blender,
build_gallery.py in this one); these operators only start them and report.
"""
import subprocess

import bpy

from . import core, library


def count_summary(result):
    """One status line from what build_gallery.build() returns: a dict of counts, or a bare number of cards."""
    if isinstance(result, dict):
        return ', '.join(f'{k} {v}' for k, v in result.items() if isinstance(v, (int, float, str)))
    return f'{result} cards'


class SSLINK_OT_open_browser(bpy.types.Operator):
    bl_idname = 'ss_link.open_browser'
    bl_label = 'Open Visual Browser'
    bl_description = 'Show the thumbnail gallery page, Artifacts/PrefabLibrary/index.html, in the web browser'

    def execute(self, context):
        lib = core.library_dir()
        page = lib / 'index.html' if lib else None
        if not page or not page.exists():
            self.report({'ERROR'}, f'no gallery page at {page or "Artifacts/PrefabLibrary/index.html"}: '
                                   'run Build Browser (Tools/SSLiveLink/build_gallery.py) first')
            return {'CANCELLED'}
        bpy.ops.wm.url_open(url=page.resolve().as_uri())
        return {'FINISHED'}


class SSLINK_OT_build_browser(bpy.types.Operator):
    bl_idname = 'ss_link.build_browser'
    bl_label = 'Build Browser'
    bl_description = 'Write the gallery page from the catalogue and whatever thumbnails exist'

    def execute(self, context):
        st = context.scene.ss_link
        try:
            result = core.import_tool('build_gallery').build(core.project_root())
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        st.status = 'gallery: ' + count_summary(result)
        self.report({'INFO'}, st.status)
        return {'FINISHED'}


_render = {'proc': None}   # the background thumbnail render, so a second click reports instead of racing it


class SSLINK_OT_render_thumbnails(bpy.types.Operator):
    bl_idname = 'ss_link.render_thumbnails'
    bl_label = 'Render Thumbnails'
    bl_description = 'Render a thumbnail of every proxy in a second, background Blender; this one stays free'

    def execute(self, context):
        st = context.scene.ss_link
        proc = _render['proc']
        if proc is not None and proc.poll() is None:
            self.report({'WARNING'}, 'a thumbnail render is still running; Reload Thumbnails when it finishes')
            return {'CANCELLED'}
        try:
            script = core.tool_path('render_thumbnails.py')
            if not script.exists():
                raise RuntimeError(f'missing {script}')
            log = core.library_dir() / 'render_thumbnails.log'
            cmd = [bpy.app.binary_path, '--background', '--factory-startup', '--python', str(script), '--', '--project', str(core.project_root())]
            with open(log, 'w', encoding='utf-8') as out:
                _render['proc'] = subprocess.Popen(cmd, stdout=out, stderr=subprocess.STDOUT,
                                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        st.status = f'rendering thumbnails in the background (log: {log.name}); Reload Thumbnails when done'
        self.report({'INFO'}, st.status)
        return {'FINISHED'}


class SSLINK_OT_reload_thumbnails(bpy.types.Operator):
    bl_idname = 'ss_link.reload_thumbnails'
    bl_label = 'Reload Thumbnails'
    bl_description = "Forget the cached previews and re-read the catalogue's thumbnail paths, after a render finishes"

    def execute(self, context):
        st = context.scene.ss_link
        library.clear_previews()
        if not st.parts:
            return bpy.ops.ss_link.load_catalog()
        try:
            core.load_catalog(force=True)
        except RuntimeError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        have = 0
        for it in st.parts:
            entry = core.catalog_entry(it.asset)
            it.thumb = entry.get('thumb', '') if entry else ''
            have += 1 if library.get_icon(it.thumb) else 0
        library.refresh_pick_items(st)
        proc = _render['proc']
        running = proc is not None and proc.poll() is None
        st.status = f'thumbnails: {have} of {len(st.parts)}' + (' (render still running)' if running else '')
        return {'FINISHED'}


classes = (SSLINK_OT_open_browser, SSLINK_OT_build_browser, SSLINK_OT_render_thumbnails, SSLINK_OT_reload_thumbnails)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
