"""Shared ground for the add-on: configuration, project paths, the frame conversion, the catalogue,
proxy meshes and the tagged objects that stand for Unreal assets.

This module imports nothing else from the package, so every other module can import it.
"""
from pathlib import Path
import importlib.util
import json
import math
import os
import re
import sys
import textwrap
import uuid

import bpy
import bmesh
from bpy.props import StringProperty
from mathutils import Matrix, Vector

ENGINE_ROOTS = [r'C:\Program Files\EpicGames2\UE_5.8', r'C:\Program Files\Epic Games\UE_5.8']
REMOTE_EXEC = Path('Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python/remote_execution.py')
TOOLS = Path('Tools/SSLiveLink')   # the sibling scripts: thumbnail renderer and gallery builder
PROP_ASSET, PROP_LINK, PROP_MATERIALS = 'ss_asset', 'ss_link', 'ss_materials'
PROP_SCENE = 'ss_scene_id'   # on a Blender scene that Open Scene (scenes.py) made from a game scene: the scene's id
PROP_EDIT = 'ss_edit'        # on the copy Edit Mesh (send.py) brings in to be fixed: the mesh itself, not a placement of it
SENT = 'sent.json'           # under Artifacts/PrefabLibrary, beside catalog.json: meshes sent that the catalogue does not list yet
F = (1.0, -1.0, 1.0)   # the Y flip between the two frames


# ---------------------------------------------------------------- configuration
def config_path():
    return Path(bpy.utils.user_resource('CONFIG', create=True)) / 'ss_live_link.json'


def read_config():
    try:
        return json.loads(config_path().read_text(encoding='utf-8'))
    except Exception:
        return {}


def write_config(**kw):
    cfg = read_config()
    cfg.update(kw)
    config_path().write_text(json.dumps(cfg, indent=1), encoding='utf-8')


def prefs():
    # The add-on is known to Blender by the package's name, not this module's: __package__, never __name__.
    addon = bpy.context.preferences.addons.get(__package__)
    return addon.preferences if addon else None


def project_root():
    p = prefs()
    for candidate in ((p.project_root if p else ''), read_config().get('project_root', ''), os.environ.get('SS_PROJECT_ROOT', '')):
        if candidate and (Path(candidate) / 'SpaceSurvival.uproject').exists():
            return Path(candidate)
    return None


def engine_root():
    p = prefs()
    for candidate in [(p.engine_root if p else ''), read_config().get('engine_root', '')] + ENGINE_ROOTS:
        if candidate and (Path(candidate) / REMOTE_EXEC).exists():
            return Path(candidate)
    return None


def library_dir():
    root = project_root()
    return root / 'Artifacts' / 'PrefabLibrary' if root else None


def prefabs_dir():
    root = project_root()
    return root / 'Prefabs' if root else None


def tool_path(name):
    """A sibling script in Tools/SSLiveLink, reached through the project so an installed copy of this add-on still finds it."""
    root = project_root()
    if not root:
        raise RuntimeError('set the project root in the add-on preferences')
    return root / TOOLS / name


def import_by_path(name, path):
    """Load a module from a file outside sys.path: the engine's remote_execution.py, or our own tools."""
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def import_tool(name):
    path = tool_path(name + '.py')
    if not path.exists():
        raise RuntimeError(f'missing {path}')
    return import_by_path('ss_' + name, path)


# The prefab folder's listing lives here, not in prefabs.py: the UI state in library.py fills its prefab
# menu from it, and prefabs.py already imports library.py, so library.py cannot import it back.
def prefab_files():
    root = prefabs_dir()
    if not root or not root.exists():
        return []
    return sorted(root.rglob('*.json'))


def prefab_ref(path):
    rel = path.relative_to(prefabs_dir())
    return str(rel.with_suffix('')).replace('\\', '/')


# ---------------------------------------------------------------- frames
def to_ue_rows(m):
    """Blender world matrix (metres) -> Unreal matrix rows (cm), row-vector convention."""
    rows = []
    for j in range(3):
        rows.append([F[i] * m[i][j] * F[j] for i in range(3)] + [0.0])
    rows.append([F[i] * m[i][3] * 100.0 for i in range(3)] + [1.0])
    return rows


def from_ue_rows(rows):
    m = Matrix.Identity(4)
    for i in range(3):
        for j in range(3):
            m[i][j] = F[i] * rows[j][i] * F[j]
        m[i][3] = F[i] * rows[3][i] / 100.0
    return m


def rows_from_rotator(loc, rot, scale):
    """Unreal's FScaleRotationTranslationMatrix, for recipe parts written as location/rotation/scale."""
    pitch, yaw, roll = (math.radians(v) for v in rot)
    sp, cp, sy, cy, sr, cr = math.sin(pitch), math.cos(pitch), math.sin(yaw), math.cos(yaw), math.sin(roll), math.cos(roll)
    rows = [[cp * cy, cp * sy, sp, 0.0],
            [sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, -sr * cp, 0.0],
            [-(cr * sp * cy + sr * sy), cy * sr - cr * sp * sy, cr * cp, 0.0],
            [loc[0], loc[1], loc[2], 1.0]]
    for i in range(3):
        rows[i] = [v * scale[i] for v in rows[i]]
    return rows


def ue_point(v):
    return [v.x * 100.0, -v.y * 100.0, v.z * 100.0]


# ---------------------------------------------------------------- catalogue and proxies
_catalog = {'path': None, 'data': None, 'by_asset': {}}


def load_catalog(force=False):
    lib = library_dir()
    if not lib:
        raise RuntimeError('set the project root in the add-on preferences')
    path = lib / 'catalog.json'
    if not path.exists():
        raise RuntimeError(f'no parts catalogue yet ({path}): in Unreal use SS Prefabs > Rebuild Catalogue, then Load Catalogue here')
    if force or _catalog['path'] != path or _catalog['data'] is None:
        data = json.loads(path.read_text(encoding='utf-8'))
        _catalog.update(path=path, data=data, by_asset={m['asset']: m for m in data['meshes']})
        # A mesh sent from here is a part from the moment it is sent, in this session and the next: its row
        # in sent.json answers for it until the editor's catalogue lists it.
        teach_sent([r for r in read_sent() if r['asset'] not in _catalog['by_asset']])
    return _catalog['data']


def catalog_entry(asset):
    try:
        load_catalog()
    except RuntimeError:
        return None
    return _catalog['by_asset'].get(asset)


# ---------------------------------------------------------------- the side catalogue of sent meshes
def sent_path():
    lib = library_dir()
    if not lib:
        raise RuntimeError('set the project root in the add-on preferences')
    return lib / SENT


def read_sent():
    try:
        rows = json.loads(sent_path().read_text(encoding='utf-8'))
    except (OSError, ValueError, RuntimeError):
        return []
    return [r for r in rows if isinstance(r, dict) and r.get('asset')] if isinstance(rows, list) else []


def write_sent(rows):
    path = sent_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=1), encoding='utf-8')


def teach_sent(rows):
    """Let catalog_entry answer for sent rows, which is how add_part finds their proxy and bounds."""
    for row in rows:
        _catalog['by_asset'][row['asset']] = row


def catalogued_assets(catalog=None):
    """The assets the editor's own catalogue lists; empty when there is no catalogue yet."""
    if catalog is None:
        try:
            catalog = load_catalog()
        except RuntimeError:
            return set()
    return {m['asset'] for m in catalog.get('meshes', [])}


def merged_rows(catalog=None):
    """The catalogue's mesh rows followed by the sent rows the catalogue does not list yet.

    What the parts list is filled from, in place of catalog['meshes']. A sent row whose asset the
    catalogue now lists is dropped from sent.json on the way, and the rows that remain are taught to
    catalog_entry, so add_part on a sent asset gets its real proxy and not a box.
    """
    if catalog is None:
        try:
            catalog = load_catalog()
        except RuntimeError:
            catalog = {'meshes': []}
    known = catalogued_assets(catalog)
    rows = read_sent()
    waiting = [r for r in rows if r['asset'] not in known]
    if len(waiting) != len(rows):
        write_sent(waiting)
    teach_sent(waiting)
    return list(catalog.get('meshes', [])) + waiting


def merged_catalog(catalog=None):
    """catalog with merged_rows() as its meshes and the category and group counts raised to match: a drop-in
    for the dict load_catalog() returns. The catalogue itself is left as it was."""
    if catalog is None:
        try:
            catalog = load_catalog()
        except RuntimeError:
            catalog = {'meshes': [], 'categories': {}}
    meshes = merged_rows(catalog)
    out = dict(catalog, meshes=meshes, categories=dict(catalog.get('categories', {})))
    if 'groups' in catalog:
        out['groups'] = dict(catalog['groups'])
    for row in meshes[len(catalog.get('meshes', [])):]:
        out['categories'][row['category']] = out['categories'].get(row['category'], 0) + 1
        if 'groups' in out:
            out['groups'][row['group']] = out['groups'].get(row['group'], 0) + 1
    return out


# ---------------------------------------------------------------- what the game itself loads
_game_assets = {'root': None, 'packages': None}
GAME_PATH = re.compile(r'"(/Game/[A-Za-z0-9_/.-]+)"')


def game_loaded_packages(force=False):
    """The /Game packages the game's C++ names outright (Source/**/*.cpp and *.h), lower case.

    The catalogue lists look-alikes side by side: three versions of a hazard mesh, a fallback station
    beside the live one. Only what the code loads by path is what a player sees, so those rows are marked
    in the list; fixing one of the others changes nothing in the game. Read once per session, and again
    on Load Catalogue: some eighty small files.
    """
    root = project_root()
    if not root:
        return set()
    if force or _game_assets['root'] != root or _game_assets['packages'] is None:
        found = set()
        source = root / 'Source'
        files = (list(source.rglob('*.cpp')) + list(source.rglob('*.h'))) if source.is_dir() else []
        for path in files:
            try:
                text = path.read_text(encoding='utf-8', errors='replace')
            except OSError:
                continue
            found.update(m.split('.')[0].lower() for m in GAME_PATH.findall(text))
        _game_assets.update(root=root, packages=found)
    return _game_assets['packages']


def loaded_by_game(asset):
    return str(asset).split('.')[0].lower() in game_loaded_packages()


# ---------------------------------------------------------------- which copy of the add-on is this
_repo_version = {'root': None, 'version': None}
VERSION_LINE = re.compile(r"'version':\s*\((\d+),\s*(\d+),\s*(\d+)\)")


def running_version():
    """This copy's version, from the package's bl_info."""
    info = getattr(sys.modules.get(__package__), 'bl_info', None) or {}
    return tuple(info.get('version', (0, 0, 0)))


def repo_version():
    """The version of the add-on in the project (Tools/SSLiveLink/ss_live_link), or None when it cannot be read.

    Blender runs the copy install.py put in its own folder; the project's copy moves on with the project.
    The panel compares the two, so an install that has fallen behind says so instead of quietly lacking
    the buttons the guide talks about. Read once per session.
    """
    root = project_root()
    if not root:
        return None
    if _repo_version['root'] != root:
        version = None
        try:
            found = VERSION_LINE.search((root / TOOLS / 'ss_live_link' / '__init__.py').read_text(encoding='utf-8'))
            version = tuple(int(v) for v in found.groups()) if found else None
        except OSError:
            pass
        _repo_version.update(root=root, version=version)
    return _repo_version['version']


def version_note():
    """'' while this copy is the project's, else the line the panel shows about it."""
    mine, theirs = running_version(), repo_version()
    if theirs and theirs > mine:
        return (f'This add-on is v{".".join(map(str, mine))}; the project has v{".".join(map(str, theirs))}. '
                f'Close Blender, double-click Tools/SSLiveLink/Install Blender Add-on.cmd, start Blender again.')
    return ''


def placeholder_mesh(entry):
    """A box the size of the mesh's bounds, in metres, when no proxy exists."""
    me = bpy.data.meshes.new('SSProxy:' + entry['asset'])
    bm = bmesh.new()
    o = Vector((entry['origin'][0], -entry['origin'][1], entry['origin'][2])) / 100.0
    e = Vector(entry['extent']) / 100.0
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * 2 * e.x, v.co.y * 2 * e.y, v.co.z * 2 * e.z)) + o
    bm.to_mesh(me)
    bm.free()
    return me


def proxy_mesh(entry):
    """The mesh datablock standing in for an Unreal asset: the glTF proxy, joined and cached, or a bounds box."""
    key = 'SSProxy:' + entry['asset']
    me = bpy.data.meshes.get(key)
    if me:
        return me
    lib = library_dir()
    glb = (lib / entry['proxy']) if entry.get('proxy') and lib else None
    if glb and glb.exists():
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(glb))
        new = [o for o in bpy.data.objects if o not in before]
        meshes = [o for o in new if o.type == 'MESH']
        if meshes:
            deselect_all(bpy.context)
            for o in meshes:
                o.select_set(True)
            bpy.context.view_layer.objects.active = meshes[0]
            if len(meshes) > 1:
                bpy.ops.object.join()
            joined = bpy.context.view_layer.objects.active
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            me = joined.data
            me.name = key
            for o in new:
                if o.name in bpy.data.objects and o is not joined:
                    bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.objects.remove(joined, do_unlink=True)
            me.use_fake_user = True
            return me
        for o in new:
            bpy.data.objects.remove(o, do_unlink=True)
    me = placeholder_mesh(entry)
    me.use_fake_user = True
    return me


def ensure_collection(name, parent=None):
    """The named collection, created and linked under parent (default: the scene) when missing."""
    parent = parent or bpy.context.scene.collection
    col = bpy.data.collections.get(name)
    if not col:
        col = bpy.data.collections.new(name)
        parent.children.link(col)
    elif col.name not in parent.children and not any(col.name in c.children for c in bpy.data.collections):
        parent.children.link(col)
    return col


def draw_wrapped(layout, text, context=None, icon='NONE'):
    """text as as many labels as the sidebar needs. A label does not wrap: past the panel's width it is cut
    off, and the end of a sentence is where a refusal says what to press."""
    width = 42
    region = getattr(context, 'region', None)
    if region is not None and getattr(region, 'width', 0):
        scale = getattr(getattr(getattr(context, 'preferences', None), 'system', None), 'ui_scale', 1.0) or 1.0
        width = max(24, int(region.width / (7.0 * scale)))
    col = layout.column(align=True)
    for k, line in enumerate(textwrap.wrap(str(text), width) or ['']):
        col.label(text=line, icon=icon if k == 0 else 'NONE')


def deselect_all(context):
    """Clear the selection in the view layer, before an operator selects what it made.

    An object removed earlier in the same script run (the glTF import's leftovers, in proxy_mesh) stays in
    view_layer.objects as None until the view layer syncs, and in a scene with nothing else in it that is
    what the loop meets: skip it, or Add at Cursor ends in a traceback on an empty scene.
    """
    for o in context.view_layer.objects:
        if o is not None:
            o.select_set(False)


def add_part(asset, matrix=None, collection=None, name=None, link=None, materials=None):
    entry = catalog_entry(asset) or {'asset': asset, 'name': asset.split('.')[-1], 'origin': [0, 0, 0], 'extent': [50, 50, 50]}
    me = proxy_mesh(entry)
    obj = bpy.data.objects.new(name or entry['name'], me)
    obj[PROP_ASSET] = asset
    obj[PROP_LINK] = link or uuid.uuid4().hex
    if materials:
        obj[PROP_MATERIALS] = json.dumps(materials)
    obj.matrix_world = matrix or Matrix.Translation(bpy.context.scene.cursor.location)
    (collection or ensure_collection('SS Parts')).objects.link(obj)
    return obj


def tagged_objects(selected_only=False):
    """Every mesh in the file, or in the selection, that stands for an Unreal asset, whichever scene holds it.

    Not an Edit Mesh copy (PROP_EDIT). That object is the mesh itself on the bench, wherever the 3D cursor
    happened to be; pushed or applied it would arrive in the level, or in the station, as one more door.
    """
    objs = bpy.context.selected_objects if selected_only else bpy.data.objects
    return [o for o in objs if o.type == 'MESH' and o.get(PROP_ASSET) and not o.get(PROP_EDIT)]


# link id -> the signature last pushed to, or pulled from, the open level. editor_link fills it and keeps
# it as its _last_sent; it lives here because linked_objects asks it, and this module imports no other.
pushed_links = {}


def game_scene_objects():
    """The objects that live in opened game scenes (PROP_SCENE) and in no ordinary scene."""
    game, ordinary = set(), set()
    for scene in bpy.data.scenes:
        (game if scene.get(PROP_SCENE) else ordinary).update(scene.objects)
    return game - ordinary


def linked_objects(selected_only=False):
    """The tagged objects Push and Live send: tagged_objects without the parts of opened game scenes.

    Push All and Live take every tagged mesh in the file, whichever scene the window shows. With the
    station open anywhere in the .blend, one click on Push All in the owner's own scene would put its
    231 parts into the open level as loose actors, and Live would on its first tick. A game scene goes
    back through Apply. Two things still pass: a selection, because pushing the parts picked by hand is
    the owner's own act, and a part already sent that way, which Live must go on moving and must not
    count as deleted. A part an ordinary scene uses as well is that scene's, and is pushed as before.
    """
    objects = tagged_objects(selected_only)
    if selected_only:
        return objects
    theirs = game_scene_objects()
    if not theirs:
        return objects
    return [o for o in objects if o not in theirs or o.get(PROP_LINK) in pushed_links]


# ---------------------------------------------------------------- preferences
class SSLinkPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__
    project_root: StringProperty(name='Project root', subtype='DIR_PATH', default=read_config().get('project_root', ''),
                                 description='The folder holding SpaceSurvival.uproject')
    engine_root: StringProperty(name='Engine root', subtype='DIR_PATH', default=read_config().get('engine_root', ''),
                                description='The UE_5.8 install; found automatically when empty')

    def draw(self, context):
        self.layout.prop(self, 'project_root')
        self.layout.prop(self, 'engine_root')
        root = project_root()
        self.layout.label(text=f'project: {root}' if root else 'project not found', icon='CHECKMARK' if root else 'ERROR')


classes = (SSLinkPrefs,)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
