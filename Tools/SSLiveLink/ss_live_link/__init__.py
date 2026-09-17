"""SpaceSurvival Live Link: the project's Unreal asset library and prefabs, inside Blender, live.

Install: double-click Tools/SSLiveLink/Install Blender Add-on.cmd (it runs install.py in every Blender it
         finds), or zip this folder and use Blender > Edit > Preferences > Add-ons > Install from Disk.
Panel:   3D Viewport > Sidebar (N) > SS Link.

What it does
  Parts     The catalogue Unreal writes (SS Prefabs > Rebuild Catalogue, or Scripts/ExportPrefabCatalog.py)
            lists every static mesh the project owns by category. Add one and a glTF proxy of the real
            mesh appears at the 3D cursor, tagged with its Unreal asset path.
  Prefabs   Save a selection of tagged objects as Prefabs/<Category>/<Name>.json (the same recipe the
            editor reads and writes), or load one back as proxies. Prefabs are plain files in the repo,
            organised by directory, so they can decorate any level.
  Live      With the editor open (Python remote execution is on in DefaultEngine.ini), Push creates or
            moves the matching actors in the open level; Live keeps doing that as you move things; Pull
            mirrors the editor's selected actors here. Links survive both ways through an id tag.
  Browser   Thumbnails (Render Thumbnails runs Tools/SSLiveLink/render_thumbnails.py in a second Blender)
            show in the parts list, in a picture grid, and on a gallery page any browser can open
            (Artifacts/PrefabLibrary/index.html, written by Tools/SSLiveLink/build_gallery.py).

Frames: Blender metres, Z up, right-handed. Unreal centimetres, Z up, left-handed. The conversion is
a Y flip and x100; rotations are conjugated by the same flip, so nothing here ever talks in Euler angles.

The modules
  core         configuration, project paths, frames, the catalogue, proxy meshes, tagged objects
  editor_link  the remote-execution link to the open editor: connect, push, pull, live
  library      the scene state (scene.ss_link), thumbnail previews, the parts list and picture picker
  prefabs      prefab save and load
  browser      the gallery page and the thumbnail render
  groups       the type filter          \
  send         Send to Unreal            > features: register(), unregister(), draw(layout, context)
  scenes       Open Scene / Apply       /
  panel        the sidebar panel: the type filter inside the Parts library box, a box each for the other two
A module imports only modules listed above it, and reaches them as 'from . import core'.
"""
bl_info = {
    'name': 'SpaceSurvival Live Link',
    'author': 'SpaceSurvival',
    'version': (0, 3, 0),
    'blender': (4, 2, 0),
    'location': '3D Viewport > Sidebar > SS Link',
    'description': 'Unreal asset library as proxies with thumbnails, prefab save/load, live push/pull to the open editor',
    'category': 'Import-Export',
}

# Blender's Reload Scripts re-runs this file over the live module and nothing else; the submodules are
# reloaded by hand below, or an edit to any of them would only show after a restart.
_reloading = 'MODULES' in globals()

from . import core, editor_link, library, prefabs, browser, groups, send, scenes, panel  # noqa: E402

# Registration order, which is also a valid import order. Unregistering runs it backwards.
MODULES = [core, editor_link, library, prefabs, browser, groups, send, scenes, panel]

if _reloading:
    import importlib
    for _module in MODULES:
        importlib.reload(_module)

# The add-on's helpers under its own name, as they were when it was a single file: the self-test and
# the Blender console call them as ss_live_link.<name>.
from .core import (PROP_ASSET, PROP_LINK, PROP_MATERIALS, read_config, write_config, project_root, engine_root,  # noqa: E402,F401
                   library_dir, prefabs_dir, tool_path, import_tool, prefab_files, prefab_ref, to_ue_rows, from_ue_rows,
                   rows_from_rotator, ue_point, load_catalog, catalog_entry, proxy_mesh, ensure_collection, add_part,
                   linked_objects, tagged_objects)
from .editor_link import EditorLink, link, link_payload, push, pull, signature, live_tick  # noqa: E402,F401
from .library import get_icon, clear_previews, size_label, refresh_prefab_items, refresh_pick_items, part_visible  # noqa: E402,F401
from .prefabs import save_prefab, load_prefab  # noqa: E402,F401
from .browser import count_summary  # noqa: E402,F401


def register():
    done = []
    try:
        for module in MODULES:
            module.register()
            done.append(module)
    except Exception:
        # Take back what did register: classes left behind make every later enable fail with 'already registered'.
        for module in reversed(done):
            try:
                module.unregister()
            except Exception:
                pass
        raise


def unregister():
    for module in reversed(MODULES):
        module.unregister()
