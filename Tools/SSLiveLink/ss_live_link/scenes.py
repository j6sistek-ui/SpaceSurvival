"""Open Scene / Apply: a game scene opened here as proxies, fixed by hand, and applied back.

When describing a fix in words is not working, the owner opens the scene in Blender, moves things, and
presses Apply. A scene is a recipe file in the project: the station hangar's interior recipe, or any
prefab. Opening one makes a Blender scene 'SS <name>' with three collections:

  Parts             every static mesh of the recipe, as a tagged proxy at its real transform
  Lights            the recipe's point lights
  Context (locked)  what the game's native code fixes in place (deck, walls, the flight lane, the mouth,
                    the docked ship, the service anchors), from Tools/SSLiveLink/context/<scene>.json.
                    Unselectable, never written back: it is there to be worked around.
  Built by the game (locked)
                    the other half of the room: the wall, ceiling and pipe panels, the lamps, crates and
                    staff that the station's own code adds to the layout and no recipe lists. Read from the
                    newest layout receipt (.agent/local/StationVisualPass/EditableLayout-*/Authoring.json),
                    shown as locked proxies so a part is not set through a wall nobody could see.

Apply validates the scene first and refuses, naming and selecting the offenders, when a part sits in the
flight lane, is not an Unreal part yet, holds a transform Unreal cannot, uses a mesh with an empty material
slot and names no material, or belongs to another scene as well (Move Selected into Parts settles that
one). It also refuses, until Apply Anyway is pressed, when the recipe file changed on disk since this
scene was opened or last applied, and when more than a quarter of the parts the scene was opened with are
gone; an emptied scene is never written. Otherwise it writes the recipe in the schema it was read in
(the file it replaces is kept under Artifacts/LiveLink/Backups/Scenes), and for the station it asks the
open editor to rebuild BP_StationVisualLayout (Content/Python/ss_scenes.py), or says what to do when no
editor answers. An Edit Mesh copy standing in the scene is the mesh on the bench, not a part: it is
left out.

A station part is written in both forms: 'matrix', which this add-on and the editor's prefab code read
first, and 'location'/'rotation'/'scale', which is all the station's layout library reads
(SSStationVisualLayout.cpp, JsonTransform). A recipe with the matrix alone would build every part at
the origin.

What a part carried in the recipe and Blender has no place for (materials, cast_shadows, its exact
numbers) rides on the object as custom properties, so an untouched part is written back exactly as read
and a duplicate keeps its material overrides.

An opened scene's parts carry the same ss_asset tag as any other part, and Push All and Live send every
tagged part in the file to the open level. A game scene goes back through Apply, never as loose actors,
so core.linked_objects leaves out the parts of any scene that carries SCENE_ID (core.PROP_SCENE).

State lives in this module's own PropertyGroup, scene.ss_scenes.
"""
from datetime import datetime
from pathlib import Path
import hashlib
import json
import math
import re
import zlib

import bpy
from bpy.props import BoolProperty, EnumProperty, PointerProperty, StringProperty
from mathutils import Matrix, Vector

from . import core, editor_link

# Scenes that are more than a prefab. 'target' is where Apply writes and where Open reads once it exists;
# 'fallback' is the generated recipe the first Open starts from. 'apply' runs in the open editor: through
# __import__ because the link's call() imports ss_prefabs only. 'headless' is the script that does the
# same from a command line. The self-test points 'target' somewhere harmless, so these stay plain dicts.
RECIPE_SCENES = [
    {'id': 'station_interior', 'label': 'Station interior',
     'target': 'Prefabs/Scenes/StationInterior.json',
     'fallback': '.agent/local/StationVisualPass/PitStopLayout.json',
     'context': 'station_interior.json',
     # Where the editor leaves a receipt of every layout build, and the Blueprint those receipts must be about:
     # the newest one lists the components the game itself adds (built_by_game).
     'built': {'receipts': '.agent/local/StationVisualPass', 'package': '/Game/SpaceSurvival/Licensed/StationVisualPass/BP_StationVisualLayout'},
     'apply': "__import__('ss_scenes').apply_station_recipe({path}, force={force})",
     'headless': 'Scripts/AuthorStationEditableLayout.py'},
]
BACKUPS = Path('Artifacts/LiveLink/Backups/Scenes')   # under the project root: the recipe file each Apply replaced

# On the Blender scene. SCENE_ID is core's name for it: core.linked_objects keeps a tagged scene's parts out of Push All and Live.
SCENE_ID, SCENE_HEADER, SCENE_RULES = core.PROP_SCENE, 'ss_scene_header', 'ss_scene_rules'
SCENE_MATERIALS = 'ss_scene_materials'  # on the Blender scene: {asset: materials} from the recipe's parts that named any
SCENE_FILE = 'ss_scene_file'            # on the Blender scene: {'path', 'sha256'} of the recipe file it was opened from or last applied to
SCENE_COUNTS = 'ss_scene_counts'        # on the Blender scene: {'parts', 'lights'} as opened or last applied
ROLE = 'ss_scene_role'                  # on a collection: 'parts', 'lights', 'context' or 'native'
ROLES = (('parts', 'Parts'), ('lights', 'Lights'), ('context', 'Context (locked)'), ('native', 'Built by the game (locked)'))
DROP_LIMIT = 0.25                       # Apply asks before writing a scene that lost more than this share of its parts
STALE_EDITOR = 'layout changed outside a recipe'   # how ss_scenes.apply_station_recipe begins the refusal that force=True overrides
PROP_CONTEXT = 'ss_context'             # on a locked context object
PROP_SOURCE = 'ss_part_source'          # the part or light exactly as the recipe had it, as JSON
PROP_ORDER = 'ss_order'                 # its place in the recipe, so Apply keeps the file's order
PROP_LOADED_AS = 'ss_loaded_as'         # the Blender name it was given, to tell a rename from a '.001'
PROP_LOADED_ROWS = 'ss_loaded_rows'     # its Unreal matrix as loaded, flat, to tell a moved part from an untouched one
TRANSFORM_KEYS = ('matrix', 'location', 'rotation', 'scale')
# Characters Unreal refuses in an object name; Blender's own '.001' is the one that turns up.
BAD_NAME = re.compile(r'''["' ,/.:|&!~\n\r\t@#(){}\[\]=;^%$`]''')
LANE_EPSILON = 0.01   # cm. matrix_world is single precision: a part set exactly against the lane must not read as inside it


# ---------------------------------------------------------------- the registry
def registry():
    """Every scene that can be opened: the recipe scenes, then each prefab in the project."""
    root = core.project_root()
    if not root:
        return []
    out = []
    for spec in RECIPE_SCENES:
        target = root / spec['target']
        out.append(dict(spec, kind='recipe', target=target, source=target if target.exists() else root / spec['fallback']))
    targets = {e['target'] for e in out}
    for path in core.prefab_files():
        if path not in targets:   # an applied recipe scene lives under Prefabs/ too, and is already listed above
            ref = core.prefab_ref(path)
            out.append({'id': 'prefab:' + ref, 'label': ref, 'kind': 'prefab', 'source': path, 'target': path})
    return out


def entry_for(ident):
    """The registry entry for an id. A prefab whose file has gone still gets one, so Apply can write it again."""
    for entry in registry():
        if entry['id'] == ident:
            return entry
    if ident.startswith('prefab:') and core.prefabs_dir():
        path = core.prefabs_dir() / (ident[len('prefab:'):] + '.json')
        return {'id': ident, 'label': ident[len('prefab:'):], 'kind': 'prefab', 'source': path, 'target': path}
    return None


# Blender keeps pointers into the list an EnumProperty callback returns, so it lives at module level.
_scene_items = [('', '(set the project root)', '', 'ERROR', 0)]


def scene_items(self, context):
    return _scene_items


# An enum is stored as its item's number. A recipe scene's is its place in RECIPE_SCENES, which puts the
# station interior on 0, the value a scene that has never chosen holds: its menu then shows the station
# instead of nothing. A prefab's comes from its id, so one added or removed elsewhere in the folder does
# not move the selection onto a different scene; the table only keeps two ids from sharing a number.
# The same scheme as library.py's menus, and for its reason: numbers stay under 2**24 because a button
# carries an enum's value as a float (Blender before 5.2), and a larger one comes back rounded to a
# number no item has, so nothing could be chosen from the menu at all.
NUMBER_SPAN = 0x7FFFFF
_numbers = {spec['id']: place for place, spec in enumerate(RECIPE_SCENES)}


def scene_number(ident):
    if ident not in _numbers:
        n = zlib.crc32(ident.encode('utf-8')) % NUMBER_SPAN + 1
        while n in _numbers.values():
            n = n % NUMBER_SPAN + 1
        _numbers[ident] = n
    return _numbers[ident]


def refresh_scene_items():
    """Rebuild the menu from the registry."""
    items = []
    for entry in registry():
        what = 'interior recipe' if entry['kind'] == 'recipe' else 'prefab'
        items.append((entry['id'], entry['label'], f'{what}: {entry["source"]}', 'SCENE_DATA' if entry['kind'] == 'recipe' else 'OUTLINER_COLLECTION',
                      scene_number(entry['id'])))
    _scene_items[:] = items or [('', '(set the project root)', '', 'ERROR', 0)]


# ---------------------------------------------------------------- transforms
def bl_point(p):
    """An Unreal point in cm as a Blender point in metres; the reverse of core.ue_point."""
    return Vector((p[0], -p[1], p[2])) / 100.0


def part_rows(part, prefer_matrix):
    """A recipe part's Unreal matrix rows.

    A part may carry both forms. The station's layout library reads location/rotation/scale and nothing
    else, so for a recipe scene those are the truth and the matrix is only used when they are absent; a
    prefab is read the way the editor reads it, matrix first.
    """
    if 'matrix' in part and (prefer_matrix or 'location' not in part):
        return [[float(v) for v in row] for row in part['matrix']]
    scale = part.get('scale', [1, 1, 1])
    scale = list(scale) if isinstance(scale, (list, tuple)) else [scale] * 3
    return core.rows_from_rotator(part.get('location', [0, 0, 0]), part.get('rotation', [0, 0, 0]), scale)


def decompose_rows(rows):
    """Unreal rows -> (location, [pitch, yaw, roll] in degrees, scale), or None when that cannot hold them.

    The same steps as FTransform's SetFromMatrix and FMatrix::Rotator: a mirror goes into the X scale, the
    angles come from the X axis and then the roll about it. Shear has no place in a location, a rotator
    and a scale, so the result is rebuilt and compared; a sheared matrix returns None.
    """
    # Plain floats, not mathutils: its vectors are single precision, and these numbers go into a file.
    if any(math.isnan(v) or math.isinf(v) for row in rows for v in row):
        return None
    a, b, c = ([float(v) for v in rows[i][:3]] for i in range(3))
    scale = [math.sqrt(sum(v * v for v in axis)) for axis in (a, b, c)]
    if min(scale) <= 1e-8:
        return None
    if a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0]) + a[2] * (b[0] * c[1] - b[1] * c[0]) < 0.0:
        scale[0] = -scale[0]
    x, y, z = ([v / scale[i] for v in axis] for i, axis in enumerate((a, b, c)))
    pitch = math.atan2(x[2], math.hypot(x[0], x[1]))
    yaw = math.atan2(x[1], x[0])
    side = (-math.sin(yaw), math.cos(yaw))   # the Y axis before any roll; its Z is 0
    roll = math.atan2(z[0] * side[0] + z[1] * side[1], y[0] * side[0] + y[1] * side[1])
    location = [round(float(v), 4) + 0.0 for v in rows[3][:3]]
    rotation = [round(math.degrees(v), 6) + 0.0 for v in (pitch, yaw, roll)]   # + 0.0 turns -0.0 into 0.0
    scale = [round(v, 6) for v in scale]
    rebuilt = core.rows_from_rotator(location, rotation, scale)
    slack = 1e-4 * max(1.0, max(abs(v) for v in scale))
    if any(abs(rebuilt[i][j] - rows[i][j]) > slack for i in range(3) for j in range(3)):
        return None
    return location, rotation, scale


def flat_rows(obj):
    return [v for row in core.to_ue_rows(obj.matrix_world) for v in row]


def untouched(obj):
    """True while the object is where Open put it, to the precision Blender holds a matrix."""
    then = obj.get(PROP_LOADED_ROWS)
    if then is None or len(then) != 16:
        return False
    now = flat_rows(obj)
    return all(abs(now[k] - then[k]) <= (1e-4 if k >= 12 else 1e-6) for k in range(16))


def part_bounds_ue(obj):
    """The part's world bounds in Unreal cm: (lo, hi).

    From the catalogue's measured bounds of the real mesh, carried through the object's matrix, which is
    the generator's rule for any rotation; the proxy is a lighter mesh and may be a little smaller. An
    asset the catalogue does not know falls back to the proxy's own box.
    """
    entry = core.catalog_entry(obj.get(core.PROP_ASSET) or '')
    if entry:
        rows = core.to_ue_rows(obj.matrix_world)
        o, e = entry['origin'], entry['extent']
        centre = [sum(o[k] * rows[k][i] for k in range(3)) + rows[3][i] for i in range(3)]
        half = [sum(abs(rows[k][i]) * e[k] for k in range(3)) for i in range(3)]
        return [centre[i] - half[i] for i in range(3)], [centre[i] + half[i] for i in range(3)]
    pts = [core.ue_point(obj.matrix_world @ Vector(corner)) for corner in obj.bound_box]
    return [min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]


def in_lane(lo, hi, lane):
    """The generator's overlap test (Scripts/PrepareStationPitStopLayout.py), with the floor panel exception."""
    floor = lane.get('floor_top_z')
    if floor is not None and hi[2] <= floor + lane.get('floor_tolerance', 0.0):
        return False
    return all(lo[i] < lane['max'][i] - LANE_EPSILON and hi[i] > lane['min'][i] + LANE_EPSILON for i in range(3))


# ---------------------------------------------------------------- the locked context
def context_path(entry):
    return core.tool_path('context') / entry['context'] if entry.get('context') else None


def read_context(entry):
    path = context_path(entry)
    if not path:
        return None
    if not path.exists():
        raise RuntimeError(f'missing {path}')
    return json.loads(path.read_text(encoding='utf-8'))


def box_corners(spec, rules):
    """(lo, hi) in Unreal cm for a context box given as min/max, as center/size, or as a named rule's volume."""
    if spec.get('rule'):
        spec = rules[spec['rule']]
    if 'min' in spec:
        return list(spec['min']), list(spec['max'])
    c, s = spec['center'], spec['size']
    return [c[i] - s[i] / 2.0 for i in range(3)], [c[i] + s[i] / 2.0 for i in range(3)]


def boxes_mesh(name, boxes, centre):
    """One mesh of axis-aligned boxes, in metres about centre. A box with no thickness on an axis is a single quad."""
    verts, faces = [], []
    for lo, hi in boxes:
        a, b = bl_point(lo) - centre, bl_point(hi) - centre
        lo_b = [min(a[i], b[i]) for i in range(3)]
        hi_b = [max(a[i], b[i]) for i in range(3)]
        base = len(verts)
        flat = [i for i in range(3) if hi_b[i] - lo_b[i] < 1e-9]
        if flat:
            u, v = [i for i in range(3) if i != flat[0]]
            for su, sv in ((0, 0), (1, 0), (1, 1), (0, 1)):
                p = list(lo_b)
                p[u], p[v] = (hi_b if su else lo_b)[u], (hi_b if sv else lo_b)[v]
                verts.append(p)
            faces.append([base, base + 1, base + 2, base + 3])
            continue
        for k in range(8):
            verts.append([(hi_b if k >> i & 1 else lo_b)[i] for i in range(3)])
        faces += [[base + i for i in f] for f in ((0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5))]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    return me


def lock(obj, spec):
    """Context is looked at and worked around: it cannot be picked, moved or rendered, and Apply skips it."""
    obj[PROP_CONTEXT] = 1
    obj.hide_select = True
    obj.hide_render = True
    obj.lock_location = obj.lock_rotation = obj.lock_scale = (True, True, True)
    for key in ('note', 'source'):
        if spec.get(key):
            obj['ss_' + key] = spec[key] if isinstance(spec[key], str) else '; '.join(spec[key])


def build_context(data, collection, view_layer):
    """The context file's objects, converted to Blender's frame, in the locked collection."""
    rules = data.get('rules', {})
    made, hidden = [], []
    for spec in data.get('objects', []):
        kind = spec.get('kind')
        if kind in ('box', 'boxes'):
            boxes = [box_corners(b, rules) for b in (spec['boxes'] if kind == 'boxes' else [spec])]
            lo = [min(b[0][i] for b in boxes) for i in range(3)]
            hi = [max(b[1][i] for b in boxes) for i in range(3)]
            centre = bl_point([(lo[i] + hi[i]) / 2.0 for i in range(3)])
            obj = bpy.data.objects.new(spec['name'], boxes_mesh(spec['name'], boxes, centre))
            obj.location = centre
            color = list(spec.get('color', [0.8, 0.8, 0.8, 1.0]))
            obj.color = color
            if spec.get('display', 'WIRE') == 'GHOST':
                # Solid view shows a material's viewport colour with its alpha, which is all a see-through slab needs.
                mat = bpy.data.materials.new('SSContext ' + spec['name'])
                mat.diffuse_color = color
                obj.data.materials.append(mat)
                obj.display_type = 'SOLID'
            else:
                obj.display_type = 'WIRE'
        elif kind in ('point', 'service'):
            name = spec['name'] if kind == 'point' else 'Service: ' + spec['label']
            obj = bpy.data.objects.new(name, None)
            obj.empty_display_type = spec.get('empty', 'SINGLE_ARROW' if kind == 'service' else 'PLAIN_AXES')
            obj.empty_display_size = float(spec.get('size', 150)) / 100.0
            obj.location = bl_point(spec['location'])
            obj.show_name = True   # the label is the point of a service anchor
            for key in ('label', 'home_label', 'stations_only'):
                if key in spec:
                    obj['ss_' + key] = spec[key]
        else:
            raise RuntimeError(f'context object {spec.get("name", "?")!r} has an unknown kind {kind!r}')
        lock(obj, spec)
        collection.objects.link(obj)
        made.append(obj)
        if spec.get('hidden'):
            hidden.append(obj)
    view_layer.update()
    for obj in hidden:   # hidden from View All as well, which a 150 m corridor would otherwise own
        obj.hide_set(True, view_layer=view_layer)
    return made


def built_by_game(entry, recipe):
    """[{'name', 'asset', 'class', 'matrix'}]: the layout's components that no recipe lists, from the newest receipt.

    The station's own code adds the shell (wall, ceiling and pipe panels, lamps), crates and the staff to
    the layout Blueprint: 234 of its 483 components on 2026-09-17, in neither the recipe nor the context
    file. Every build of the layout leaves a receipt whose native_audit names each component with its mesh
    and transform; the newest receipt about the layout Blueprint is read, and whatever the recipe does not
    name is the game's. Empty when there is no receipt (a checkout without the private folder).
    """
    spec, root = entry.get('built'), core.project_root()
    if not spec or not root:
        return []
    newest = None
    for path in (root / spec['receipts']).glob('EditableLayout-*/Authoring.json'):
        try:
            when = path.stat().st_mtime
            if newest is not None and when <= newest[0]:
                continue
            data = json.loads(path.read_text(encoding='utf-8'))
            if str(data.get('blueprint', '')).lower() == spec['package'].lower() and isinstance(data.get('native_audit'), dict):
                newest = (when, data)
        except (OSError, ValueError):
            continue
    if newest is None:
        return []
    named = {str(row.get('name', '')).lower() for key in ('static_meshes', 'point_lights') for row in recipe.get(key, []) if isinstance(row, dict)}
    out = []
    for component in newest[1]['native_audit'].get('components', []):
        try:
            if component['name'].lower() in named or component.get('class') not in ('StaticMeshComponent', 'SkeletalMeshComponent'):
                continue
            # FTransform::ToString: 'X,Y,Z|Pitch,Yaw,Roll|SX,SY,SZ'
            location, rotation, scale = ([float(v) for v in chunk.split(',')] for chunk in component['transform'].split('|'))
            out.append({'name': component['name'], 'asset': component.get('mesh') or '', 'class': component['class'],
                        'matrix': core.from_ue_rows(core.rows_from_rotator(location, rotation, scale))})
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
    return out


def build_native(native, collection):
    """The game's own components as locked stand-ins: the mesh's proxy where the catalogue has one, else a named marker."""
    made = []
    for row in native:
        known = core.catalog_entry(row['asset']) if row['class'] == 'StaticMeshComponent' else None
        if known:
            obj = bpy.data.objects.new(row['name'], core.proxy_mesh(known))
        else:
            obj = bpy.data.objects.new(row['name'], None)   # staff (skeletal), or a mesh of a pack the catalogue leaves out
            obj.empty_display_type = 'CUBE' if row['class'] == 'StaticMeshComponent' else 'ARROWS'
            obj.empty_display_size = 0.3
            obj.show_name = True
        obj.matrix_world = row['matrix']
        obj['ss_context_asset'] = row['asset']   # never ss_asset: that tag is what makes a part, and this is not one
        lock(obj, {'note': 'Built by the game, not by the recipe: shown so parts can be placed around it. Not written back by Apply.'})
        collection.objects.link(obj)
        made.append(obj)
    return made


# ---------------------------------------------------------------- open
def file_sha(path):
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def remember_file(scene, path, parts, lights):
    """Note which recipe file this scene now agrees with, and how much it held: what Apply compares against."""
    scene[SCENE_FILE] = json.dumps({'path': str(path), 'sha256': file_sha(path)})
    scene[SCENE_COUNTS] = json.dumps({'parts': parts, 'lights': lights})


def changed_outside(scene, entry):
    """'' while the recipe on disk is the one this scene was opened from or last applied to, else what changed.

    Blender is not the only writer. The pit stop generator writes the first recipe again when it is re-run,
    another .blend may have applied, the file may have been edited by hand. Open shows a scene 'as it was
    left' without reading the file, so without this an Apply writes an old scene over whatever happened
    since, and nothing says that anything was lost.
    """
    try:
        known = json.loads(scene.get(SCENE_FILE) or '{}')
    except ValueError:
        known = {}
    if not known.get('sha256'):
        return ''
    target, was = Path(entry['target']), Path(known.get('path', ''))
    if target.exists():
        if file_sha(target) == known['sha256']:
            return ''
        if was == target:
            return f'{target.name} changed on disk since this scene was opened or last applied (something other than this scene wrote it).'
        return f'{target.name} has been written by something else since this scene was opened from {was.name}.'
    if was != target and was.exists() and file_sha(was) != known['sha256']:
        return f'{was.name}, which this scene was opened from, has been written again since.'
    return ''


def blender_scene_for(entry):
    """The Blender scene already holding entry, found by the id Open left on it, so a rename does not lose it."""
    for scene in bpy.data.scenes:
        if scene.get(SCENE_ID) == entry['id']:
            return scene
    return None


def role_collections(scene):
    return {c[ROLE]: c for c in scene.collection.children_recursive if c.get(ROLE)}


def make_collections(scene):
    """Parts, Lights and Context (locked), found again by role: Blender renames a second scene's to 'Parts.001'."""
    cols = role_collections(scene)
    for role, name in ROLES:
        if role not in cols:
            cols[role] = bpy.data.collections.new(name)
            cols[role][ROLE] = role
            scene.collection.children.link(cols[role])
    return cols


def clear_loaded(scene):
    """Take out what Open made and everything else Apply would write, for a reload. Returns the parts left.

    Not the role collections alone. Apply writes every tagged mesh and point light in the scene, so a part
    added with Add at Cursor ('SS Parts'), pulled ('SS Pulled'), loaded from a prefab or filed under a
    collection of the owner's is in the file once it has been applied. Left in place it would sit exactly
    on the copy the reload reads back, unseen, and the next Apply would write both.

    A part another scene uses as well is left (and returned): it is not this scene's to delete, and Apply
    refuses it until Move Selected into Parts settles whose it is. Proxy meshes stay, shared and cached.
    So does a mesh the owner modelled (Edit Mesh, Send to Unreal), held by a fake user: the object was the
    scene's, the modelling is not.
    """
    cols = role_collections(scene)
    doomed = {obj: True for col in cols.values() for obj in col.all_objects}   # a dict, to keep each object once and in order
    parts, lights, _ = scene_objects(scene)
    left = []   # (an Edit Mesh copy is not among parts: scene_objects leaves it out, so a reload leaves it be)
    for obj in [o for o in parts if o.get(core.PROP_ASSET)] + lights:
        if obj in doomed:
            continue
        if any(s != scene for s in obj.users_scene):
            left.append(obj)
        else:
            doomed[obj] = True
    for obj in doomed:
        data = obj.data
        ours = bool(obj.get(PROP_CONTEXT)) or obj.type == 'LIGHT' or (data is not None and data.name.startswith('SSProxy:'))
        materials = [m for m in getattr(data, 'materials', []) if m is not None] if obj.get(PROP_CONTEXT) else []
        bpy.data.objects.remove(obj, do_unlink=True)
        if data is None or data.users or data.use_fake_user:
            continue
        if ours:   # a context box, a light, or a copy of a proxy that Shift+D made
            bpy.data.batch_remove([data])
            bpy.data.batch_remove([m for m in materials if m.users == 0])   # a context slab's see-through colour
        else:
            data.use_fake_user = True
    for col in cols.values():
        bpy.data.collections.remove(col)
    return left


def add_light(light, order, collection):
    data = bpy.data.lights.new(light.get('name', 'Light'), 'POINT')
    c = light.get('color', [1, 1, 1])
    data.color = (c[0], c[1], c[2])
    data.energy = float(light.get('intensity', 5000)) / 8.0   # the same scale prefabs.py uses, so both agree
    data.use_custom_distance = True
    data.cutoff_distance = float(light.get('attenuation_radius', 1000)) / 100.0
    data.use_shadow = bool(light.get('cast_shadows', False))
    obj = bpy.data.objects.new(light.get('name', 'Light'), data)
    obj.matrix_world = Matrix.Translation(bl_point(light.get('location', [0, 0, 0])))
    obj[PROP_SOURCE] = json.dumps(light)
    obj[PROP_ORDER] = order
    obj[PROP_LOADED_AS] = obj.name
    collection.objects.link(obj)
    return obj


def checked_recipe(recipe, prefer_matrix):
    """[(part, Blender matrix)] for the recipe's static meshes, every part and light looked at before a
    scene is made or emptied for them. Raises RuntimeError naming the one that cannot be placed."""
    def numbers(values, count):
        values = [float(v) for v in values]
        if len(values) != count or any(math.isnan(v) or math.isinf(v) for v in values):
            raise ValueError(f'expected {count} numbers, got {values}')

    placed = []
    for order, part in enumerate(recipe.get('static_meshes', [])):
        try:
            if not isinstance(part['asset'], str) or not part['asset']:
                raise ValueError('its asset is not a path')
            rows = part_rows(part, prefer_matrix)
            for row in rows[:4]:
                numbers(row[:3], 3)
            placed.append((part, core.from_ue_rows(rows)))
        except (AttributeError, IndexError, KeyError, TypeError, ValueError) as e:
            name = part.get('name', '?') if isinstance(part, dict) else '?'
            raise RuntimeError(f'part {order} ({name}) cannot be placed: {type(e).__name__}: {e}')
    for order, light in enumerate(recipe.get('point_lights', [])):
        try:
            numbers(light.get('location', [0, 0, 0]), 3)
            numbers(light.get('color', [1, 1, 1])[:3], 3)
            numbers([light.get('intensity', 5000), light.get('attenuation_radius', 1000)], 2)
        except (AttributeError, IndexError, KeyError, TypeError, ValueError) as e:
            name = light.get('name', '?') if isinstance(light, dict) else '?'
            raise RuntimeError(f'light {order} ({name}) cannot be placed: {type(e).__name__}: {e}')
    return placed


def fill_scene(scene, recipe, placed, context_data, native=()):
    """Build the recipe into scene, which holds nothing of it yet. Returns (parts, lights, locked, built by the game)."""
    view_layer = scene.view_layers[0]
    cols = make_collections(scene)
    parts = []
    for order, (part, matrix) in enumerate(placed):
        obj = core.add_part(part['asset'], matrix, cols['parts'], name=part.get('name'), materials=part.get('materials'))
        obj[PROP_SOURCE] = json.dumps(part)
        obj[PROP_ORDER] = order
        obj[PROP_LOADED_AS] = obj.name
        parts.append(obj)
    lights = [add_light(light, order, cols['lights']) for order, light in enumerate(recipe.get('point_lights', []))]
    locked = build_context(context_data, cols['context'], view_layer) if context_data else []
    if not locked:
        bpy.data.collections.remove(cols['context'])
    game = build_native(native, cols['native'])
    if not game:
        bpy.data.collections.remove(cols['native'])
    # Blender rebuilds matrix_world from location, rotation and scale on its next update; record what it
    # settles on, or every part would read as moved.
    view_layer.update()
    for obj in parts:
        obj[PROP_LOADED_ROWS] = flat_rows(obj)
    return parts, lights, locked, game


def abandon(scene, made):
    """After an Open that failed with the scene made or emptied: take the half-built scene apart.

    Left tagged, the next Open would show it 'as it was left', 40 parts of 231, and Apply would write that
    over the recipe with nothing in validate() to object. A scene Open made is removed with what it
    holds. A reloaded scene was the owner's before it was emptied and may hold other things of theirs, so
    it stays, without the tag: an ordinary scene, which Apply refuses and the next Open does not reuse.
    """
    for key in (SCENE_ID, SCENE_HEADER, SCENE_RULES, SCENE_MATERIALS, SCENE_FILE, SCENE_COUNTS):
        if key in scene:
            del scene[key]
    try:
        clear_loaded(scene)
    finally:
        if made:
            bpy.data.scenes.remove(scene)


def open_scene(entry, window=None, reload=False):
    """Make (or show) the Blender scene for entry. Returns (scene, summary); summary is None when an
    existing scene was shown as it is, hand edits and all.

    All or nothing. What can be wrong with the file is met before anything is made, and the proxies are
    imported before an open scene is emptied for a reload, so a reload that fails there leaves the scene
    as it was. A failure past that point ends in abandon(), and the window goes back where it was.
    """
    scene = blender_scene_for(entry)
    window = window or bpy.context.window
    if scene is not None and not reload:
        if window:
            window.scene = scene
        return scene, None
    made = scene is None
    try:
        source = Path(entry['source'])
        if not source.exists():
            raise RuntimeError(f'no recipe at {source}')
        recipe = json.loads(source.read_text(encoding='utf-8-sig'))
        context_data = read_context(entry)
        placed = checked_recipe(recipe, prefer_matrix=entry['kind'] == 'prefab')
        native = built_by_game(entry, recipe)
    except Exception as e:
        if made:
            raise
        raise RuntimeError(f'{e} ({scene.name} is as it was)')
    previous = window.scene if window else None
    if made:
        scene = bpy.data.scenes.new('SS ' + entry['label'])
    # Proxies are imported through operators, which work on the window's scene: show it before filling it.
    if window:
        window.scene = scene
    emptied, left = made, []
    try:
        for asset in dict.fromkeys([part['asset'] for part, _ in placed] + [row['asset'] for row in native if row['class'] == 'StaticMeshComponent']):
            known = core.catalog_entry(asset)
            if known:
                core.proxy_mesh(known)   # the glTF import, the one step here that leans on another add-on
        if not made:
            emptied = True
            left = clear_loaded(scene)
        parts, lights, locked, game = fill_scene(scene, recipe, placed, context_data, native)
    except Exception as e:
        if window and previous:
            window.scene = previous
        if not emptied:
            raise RuntimeError(f'{e} ({scene.name} is as it was)')
        name = scene.name
        abandon(scene, made)
        raise RuntimeError(f'{e} (nothing was opened)' if made else
                           f'{e} ({name} was already emptied and is no longer tied to the recipe: Open Scene builds it again)')
    # The tag goes on last: a scene that carries it is one Apply may write.
    scene[SCENE_ID] = entry['id']
    # Everything but the parts and lights, in the file's own key order, for Apply to write around them.
    scene[SCENE_HEADER] = json.dumps({k: ([] if k in ('static_meshes', 'point_lights') else v) for k, v in recipe.items()})
    scene[SCENE_RULES] = json.dumps((context_data or {}).get('rules', {}))
    scene[SCENE_MATERIALS] = json.dumps({p['asset']: p['materials'] for p in recipe.get('static_meshes', []) if p.get('materials')})
    remember_file(scene, source, len(parts), len(lights))
    return scene, {'parts': len(parts), 'lights': len(lights), 'context': len(locked), 'native': len(game), 'left': len(left), 'source': str(source),
                   'native_expected': bool(entry.get('built'))}


# ---------------------------------------------------------------- validate
def scene_objects(scene):
    """(parts, lights, skipped): meshes that are not context, point lights, and how many other lights were left out.

    An Edit Mesh copy (core.PROP_EDIT) is no part. It carries ss_asset, and Edit Mesh sets it down at the 3D
    cursor, which in a new scene is the middle of the flight lane: counted, it made Apply blame a door for
    being in the lane, and moved aside it was written into the station as one more door.
    """
    parts, lights, skipped = [], [], 0
    for obj in scene.objects:
        if obj.get(PROP_CONTEXT) or obj.get(core.PROP_EDIT):
            continue
        if obj.type == 'MESH':
            parts.append(obj)
        elif obj.type == 'LIGHT':
            if obj.data.type == 'POINT':
                lights.append(obj)
            else:
                skipped += 1

    def order(obj):
        # The recipe's order; then a part as loaded before its copies, so the original keeps its name.
        return (obj.get(PROP_ORDER, 1 << 30), obj.name != obj.get(PROP_LOADED_AS), obj.name)
    return sorted(parts, key=order), sorted(lights, key=order), skipped


def empty_slot(asset, materials):
    """The first material slot the mesh ships empty and materials leaves empty, or None.

    The layout library refuses such a part (SM_MonitorScreen is one). The catalogue lists a mesh's slots,
    '' for an empty one.
    """
    entry = core.catalog_entry(asset or '')
    for slot, material in enumerate((entry or {}).get('materials', [])):
        if not material and not (slot < len(materials) and materials[slot]):
            return slot
    return None


def part_materials(obj, scene):
    """The material overrides the part is written with.

    Its own ss_materials first; then what the recipe said for it, should the property have been cleared;
    and for a part added here whose mesh ships an empty slot, what the recipe gave another part of the
    same mesh. That last step is only taken to fill an empty slot: a platform painted cyan must not turn
    every new floor tile cyan.
    """
    try:
        own = json.loads(obj.get(core.PROP_MATERIALS) or '[]')
    except ValueError:
        own = []
    if not isinstance(own, list) or not own:
        own = json.loads(obj.get(PROP_SOURCE) or '{}').get('materials') or []
    if own:
        return own
    asset = obj.get(core.PROP_ASSET)
    if empty_slot(asset, []) is not None:
        return json.loads(scene.get(SCENE_MATERIALS) or '{}').get(asset, [])
    return []


def validate(scene, kind, rules):
    """[(object, reason)] for everything that stops Apply. An empty list means the scene may be written."""
    parts, lights, _ = scene_objects(scene)
    lane = rules.get('flight_lane') if kind == 'recipe' else None
    problems = []
    for obj in parts:
        others = [s.name for s in obj.users_scene if s != scene]
        # Every reason ends in the click that settles it: the owner reads these, not the code.
        if not obj.get(core.PROP_ASSET):
            problems.append((obj, 'not in Unreal yet: select it and press Send to Unreal (it becomes a part), or delete it'))
        elif others:
            # core.add_part's 'SS Parts' collection is one per file, so a part added here can drag another
            # scene's parts in with it. Writing those into the recipe unasked would be worse than asking.
            problems.append((obj, f'also in scene {others[0]!r}: select only what belongs here, then press Move Selected into Parts'))
        elif decompose_rows(core.to_ue_rows(obj.matrix_world)) is None:
            problems.append((obj, 'skewed or squashed flat, which Unreal cannot hold: clear its parent (Alt+P) or apply its scale (Ctrl+A, Scale)'))
        elif lane and in_lane(*part_bounds_ue(obj), lane):
            problems.append((obj, 'in the flight lane, the wire box a docking ship flies through: move it out to the side, or above it'))
        elif kind == 'recipe' and empty_slot(obj[core.PROP_ASSET], part_materials(obj, scene)) is not None:
            # Caught here, by name, before the layout library meets it with the Blueprint already cleared.
            problems.append((obj, 'its mesh has a material slot with nothing in it, which the station refuses: use another part here'))
    return problems


def describe(problems, limit=8):
    """'a, b, c: reason' per reason, the names capped so the line stays readable."""
    by_reason = {}
    for obj, reason in problems:
        by_reason.setdefault(reason, []).append(obj.name)
    lines = []
    for reason, names in by_reason.items():
        more = f' and {len(names) - limit} more' if len(names) > limit else ''
        lines.append(f'{", ".join(names[:limit])}{more}: {reason}')
    return lines


def adopt(scene, objects):
    """Make objects this scene's own parts: into Parts, out of every other collection. Returns (moved, unlinked).

    Add at Cursor puts a part in 'SS Parts', one collection for the whole file; used inside an opened
    scene it links that collection here, and with it whatever another scene keeps there. Once the chosen
    parts are in Parts, a collection this scene still shares with another and that holds nothing but
    tagged parts is unlinked from here (its parts stay in their own scene), so Apply sees this scene only.
    """
    cols = role_collections(scene)
    if 'parts' not in cols:
        raise RuntimeError('this is not an opened game scene: use Open Scene first')
    moved = 0
    for obj in objects:
        if obj.get(PROP_CONTEXT) or not obj.get(core.PROP_ASSET):
            continue
        for col in list(obj.users_collection):
            col.objects.unlink(obj)
        cols['parts'].objects.link(obj)
        moved += 1
    unlinked = []
    for col in list(scene.collection.children):
        elsewhere = any(other != scene and col in other.collection.children_recursive for other in bpy.data.scenes)
        if elsewhere and not col.get(ROLE) and all(o.get(core.PROP_ASSET) for o in col.all_objects):
            scene.collection.children.unlink(col)
            unlinked.append(col.name)
    return moved, unlinked


# ---------------------------------------------------------------- write
def recipe_name(obj):
    """The name the recipe gets: the one it was read with while Blender's is unchanged (Blender may have
    had to call it 'Deck.001'), else Blender's, made safe for Unreal."""
    source = obj.get(PROP_SOURCE)
    if source and obj.name == obj.get(PROP_LOADED_AS):
        return json.loads(source).get('name') or BAD_NAME.sub('_', obj.name)
    return BAD_NAME.sub('_', obj.name)


def unique_names(objects):
    """{object: name}, no two alike. Unreal compares names without case, and parts and lights share one
    list of components, so they are numbered apart together. Returns the map and how many were changed."""
    used, names, changed = set(), {}, 0
    for obj in objects:
        base = recipe_name(obj)
        name, n = base, 2
        while name.lower() in used:
            name = f'{base}_{n}'
            n += 1
        used.add(name.lower())
        names[obj] = name
        changed += name != base
    return names, changed


def part_record(obj, name, kind, scene):
    """One static_meshes row. An untouched part keeps the numbers it was read with; a moved or new one
    gets its matrix from Blender. A recipe scene's rows carry both forms: the matrix this add-on and the
    editor read first, and the location/rotation/scale the station's layout library reads."""
    source = json.loads(obj[PROP_SOURCE]) if obj.get(PROP_SOURCE) else {}
    keep = untouched(obj)
    transform = {k: source[k] for k in TRANSFORM_KEYS if k in source} if keep else {}
    if not transform:
        transform = {'matrix': [[round(v, 6) + 0.0 for v in row] for row in core.to_ue_rows(obj.matrix_world)]}
    if kind == 'recipe':
        if 'location' not in transform:
            # validate() has already passed the object's own matrix, which stands in should the recipe's be sheared.
            location, rotation, scale = decompose_rows(transform['matrix']) or decompose_rows(core.to_ue_rows(obj.matrix_world))
            transform.update(location=location, rotation=rotation, scale=scale)
        elif 'matrix' not in transform:
            transform['matrix'] = [[round(v, 6) + 0.0 for v in row] for row in part_rows(transform, prefer_matrix=False)]
    record = {'name': name, 'asset': obj[core.PROP_ASSET]}
    record.update({k: transform[k] for k in TRANSFORM_KEYS if k in transform})
    materials = part_materials(obj, scene)
    if materials:
        record['materials'] = materials
    # Whatever else the recipe said about the part (cast_shadows today) goes back as it came.
    record.update({k: v for k, v in source.items() if k not in record and k not in TRANSFORM_KEYS and k != 'materials'})
    return record


def near(a, b, slack):
    return abs(a - b) <= slack * max(1.0, abs(b))


def light_record(obj, name):
    """One point_lights row, in the recipe's units; a value Blender still holds as read is written as it was read."""
    source = json.loads(obj[PROP_SOURCE]) if obj.get(PROP_SOURCE) else {}
    data = obj.data
    location = [round(v, 3) + 0.0 for v in core.ue_point(obj.matrix_world.translation)]
    color = [round(v, 5) for v in list(data.color)[:3]]
    intensity = round(data.energy * 8.0, 3)
    radius = round(data.cutoff_distance * 100.0, 3) if data.use_custom_distance else source.get('attenuation_radius', 1000.0)
    was = source.get('location')
    if was and all(near(location[i], was[i], 1e-3) for i in range(3)):
        location = was
    was = source.get('color')
    if was and all(near(color[i], was[i], 1e-5) for i in range(3)):
        color = was
    if 'intensity' in source and near(intensity, source['intensity'], 1e-5):
        intensity = source['intensity']
    if 'attenuation_radius' in source and near(radius, source['attenuation_radius'], 1e-5):
        radius = source['attenuation_radius']
    record = {'name': name, 'location': location, 'color': color, 'intensity': intensity, 'attenuation_radius': radius,
              'cast_shadows': bool(data.use_shadow)}
    record.update({k: v for k, v in source.items() if k not in record})
    return record


def build_recipe(scene, kind):
    """The recipe for the scene as it stands: (recipe, names changed to keep them unique, lights left out)."""
    parts, lights, skipped = scene_objects(scene)
    names, renamed = unique_names(parts + lights)
    header = json.loads(scene.get(SCENE_HEADER) or '{}')
    header.setdefault('schema_version', 1)
    header.setdefault('static_meshes', [])
    header.setdefault('point_lights', [])
    recipe = dict(header)
    recipe['static_meshes'] = [part_record(o, names[o], kind, scene) for o in parts]
    recipe['point_lights'] = [light_record(o, names[o]) for o in lights]
    return recipe, renamed, skipped


def dump_recipe(recipe):
    """JSON with one part or light to a line: Prefabs/ is committed, and a moved crate should be a one-line diff."""
    chunks = []
    for key, value in recipe.items():
        if key in ('static_meshes', 'point_lights') and value:
            rows = ',\n'.join('  ' + json.dumps(row) for row in value)
            chunks.append(f' {json.dumps(key)}: [\n{rows}\n ]')
        else:
            chunks.append(f' {json.dumps(key)}: ' + json.dumps(value, indent=1).replace('\n', '\n '))
    return '{\n' + ',\n'.join(chunks) + '\n}\n'


class SceneRefused(Exception):
    """Apply's refusal: problems is [(object, reason)], for the operator to select and report."""

    def __init__(self, problems):
        super().__init__('; '.join(describe(problems)))
        self.problems = problems


class SceneStale(Exception):
    """Apply's question: nothing in the scene is wrong, but writing it would lose something. Apply Anyway (force) writes it."""


def current_rules(scene, entry):
    """The rules Apply checks: the context file as it is now, else the copy taken when the scene was opened."""
    try:
        data = read_context(entry)
        if data:
            return data.get('rules', {})
    except (RuntimeError, ValueError):
        pass
    return json.loads(scene.get(SCENE_RULES) or '{}')


def keep_previous(path):
    """Copy the recipe file about to be replaced into BACKUPS; returns the copy, or None when there was no file."""
    root = core.project_root()
    if not path.is_file() or not root:
        return None
    folder = root / BACKUPS
    folder.mkdir(parents=True, exist_ok=True)
    copy = folder / f'{datetime.now().strftime("%Y%m%d-%H%M%S")}-{path.name}'
    n = 1
    while copy.exists():
        n += 1
        copy = folder / f'{datetime.now().strftime("%Y%m%d-%H%M%S")}-{n}-{path.name}'
    copy.write_bytes(path.read_bytes())
    return copy


def write_scene(scene, entry, force=False):
    """Validate, then write the recipe. Returns (path, summary).

    Raises SceneRefused with the offenders; RuntimeError for a scene with nothing in it, which is never
    written; and SceneStale, unless force, when writing would lose something nobody asked to lose: the
    recipe changed on disk behind this scene's back, or a large share of the scene's parts is gone.
    """
    for view_layer in scene.view_layers:   # a part moved by a script has no matrix_world yet
        view_layer.update()
    problems = validate(scene, entry['kind'], current_rules(scene, entry))
    if problems:
        raise SceneRefused(problems)
    recipe, renamed, skipped = build_recipe(scene, entry['kind'])
    parts, lights = len(recipe['static_meshes']), len(recipe['point_lights'])
    # validate() looks at what is there, so a scene emptied by one wrong Delete has nothing wrong with it.
    if not parts and (entry['kind'] == 'recipe' or not lights):
        raise RuntimeError('there are no parts in this scene, and an empty scene is never applied: undo the delete (Ctrl+Z), or use '
                           'Reload from file (the round arrow beside Open Scene) to get them back')
    if not force:
        try:
            then = int(json.loads(scene.get(SCENE_COUNTS) or '{}').get('parts', 0))
        except (ValueError, TypeError, AttributeError):
            then = 0
        if then and parts < then * (1.0 - DROP_LIMIT):
            raise SceneStale(f'{then - parts} of the {then} parts this scene had are gone ({parts} left). If that is meant, press Apply Anyway; '
                             f'if not, undo (Ctrl+Z) or Reload from file.')
        changed = changed_outside(scene, entry)
        if changed:
            raise SceneStale(changed + ' Reload from file (the round arrow beside Open Scene) takes that version and drops what was changed '
                             'here; Apply Anyway writes this scene over it (the file it replaces is kept as a backup).')
    path = Path(entry['target'])
    path.parent.mkdir(parents=True, exist_ok=True)
    text = dump_recipe(recipe)
    previous = None
    try:
        same = path.is_file() and path.read_text(encoding='utf-8') == text
    except (OSError, ValueError):
        same = False
    if not same:
        previous = keep_previous(path)
    path.write_text(text, encoding='utf-8')
    remember_file(scene, path, parts, lights)
    edits = sum(1 for o in scene.objects if o.get(core.PROP_EDIT))
    return path, {'parts': parts, 'lights': lights, 'renamed': renamed, 'skipped_lights': skipped, 'skipped_edits': edits,
                  'previous': str(previous) if previous else None}


def headless_command(entry, path):
    """The command that applies the written recipe with no editor open, as docs/BUILD_RUN.md runs it."""
    root = core.project_root()
    engine = core.engine_root() or Path(core.ENGINE_ROOTS[0])
    exe = engine / 'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
    return (f'& "{exe.as_posix()}" "{(root / "SpaceSurvival.uproject").as_posix()}" -unattended -stdout -FullStdOutLogOutput '
            f'-DisablePlugins=UAssetBrowser "-ExecutePythonScript={(root / entry["headless"]).as_posix()} '
            f'--layout-recipe {Path(path).resolve().as_posix()} --reset-layout"')


def last_line(text):
    """The sentence at the end of what the editor sent back, which for a refusal is a whole Python traceback."""
    lines = [line.strip() for line in str(text).splitlines() if line.strip()]
    return re.sub(r'^(?:[A-Za-z_.]*(?:Error|Exception)):\s*', '', lines[-1]) if lines else str(text)


def send_to_editor(entry, path, force=False):
    """Ask the open editor to apply the written recipe. force: over a layout that was changed outside a recipe.

    Returns ('applied', summary), ('no editor', why) when nothing answered, or ('refused', why) when an
    editor answered and the apply failed there.
    """
    link = editor_link.link
    try:
        if not link.connected:
            link.connect()
    except Exception as e:
        return 'no editor', str(e)
    try:
        return 'applied', link.call(entry['apply'].format(path=repr(Path(path).resolve().as_posix()), force=bool(force)))
    except Exception as e:
        # The editor closing under the call is no editor, not a verdict on the recipe.
        return ('no editor' if str(e).startswith('editor link dropped') else 'refused'), str(e)


# ---------------------------------------------------------------- state and operators
class SSSceneState(bpy.types.PropertyGroup):
    scene: EnumProperty(name='Scene', items=scene_items, description='A game scene to open here: the station interior, or any prefab')
    status: StringProperty(default='')
    report: StringProperty(default='')    # the last Apply's lines, one per reason, newline separated
    command: StringProperty(default='')   # the headless command the last Apply left to be run
    can_force: BoolProperty(default=False)   # the last Apply stopped to ask; Apply Anyway is offered


def set_report(st, status, lines=(), command='', can_force=False):
    st.status, st.report, st.command, st.can_force = status, '\n'.join(lines), command, can_force


class SSLINK_OT_refresh_scenes(bpy.types.Operator):
    bl_idname = 'ss_link.refresh_scenes'
    bl_label = 'Refresh'
    bl_description = 'Re-read the scenes: the station interior and every prefab in Prefabs/'

    def execute(self, context):
        refresh_scene_items()
        return {'FINISHED'}


class SSLINK_OT_open_scene(bpy.types.Operator):
    bl_idname = 'ss_link.open_scene'
    bl_label = 'Open Scene'
    bl_description = "Open the chosen scene as a Blender scene 'SS <name>': parts, lights, and the locked context around them"
    bl_options = {'REGISTER', 'UNDO'}
    reload: BoolProperty(name='Reload from file', default=False,
                         description=('Rebuild an already open scene from its file: every part and point light in it, in whatever '
                                      'collection, is replaced by the file\'s, so hand edits since the last Apply are lost'))

    def invoke(self, context, event):
        if self.reload:
            return context.window_manager.invoke_confirm(self, event)
        return self.execute(context)

    def execute(self, context):
        refresh_scene_items()
        entry = entry_for(context.scene.ss_scenes.scene) if context.scene.ss_scenes.scene else None
        if not entry:
            self.report({'ERROR'}, 'choose a scene (and set the project root in the add-on preferences)')
            return {'CANCELLED'}
        try:
            # Without the catalogue every part is a grey one-metre box, and Apply then blames untouched floor
            # panels for reaching into the flight lane: better to open nothing and say what is missing.
            core.load_catalog()
        except RuntimeError as e:
            context.scene.ss_scenes.status = str(e)
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        try:
            scene, summary = open_scene(entry, context.window, reload=self.reload)
        except Exception as e:
            context.scene.ss_scenes.status = str(e)
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        st = scene.ss_scenes
        try:
            st.scene = entry['id']   # the new scene's own menu should show what it holds
        except TypeError:
            pass
        if summary is None:
            changed = changed_outside(scene, entry)
            set_report(st, f'showing {scene.name} as it was left; Reload reads the file again',
                       [changed + ' Reload from file (the round arrow) reads it; what was changed here since the last Apply would be lost.'] if changed else [])
            return {'FINISHED'}
        try:
            # State is per Blender scene, so the new one starts with an empty parts list; fill it so parts can be added here.
            bpy.ops.ss_link.load_catalog()
        except Exception:
            pass
        core.deselect_all(context)
        lines = [f'from {summary["source"]}']
        if summary['native']:
            lines.append(f'{summary["native"]} more are built by the game itself (walls, ceiling, pipes, lamps, crates, staff): shown locked, '
                         f'as they were the last time the layout was built. To change the shape of one, find its mesh in the parts list and use Edit Mesh.')
        elif summary['native_expected']:
            lines.append('Walls, ceiling, pipes and staff are built by the game and are NOT shown here: no layout receipt was found to read them from.')
        if summary['left']:
            lines.append(f'{summary["left"]} objects shared with another scene were left as they are; Apply will ask about them')
        set_report(st, f'opened {entry["label"]}: {summary["parts"]} parts, {summary["lights"]} lights, '
                       f'{summary["context"] + summary["native"]} locked', lines)
        return {'FINISHED'}


class SSLINK_OT_apply_scene(bpy.types.Operator):
    bl_idname = 'ss_link.apply_scene'
    bl_label = 'Apply Scene'
    bl_description = ('Check this scene, write its recipe back, and have the open Unreal editor rebuild from it. For the station that '
                      'replaces the whole layout Blueprint; the previous Blueprint and recipe are kept as backups')
    force: BoolProperty(name='Apply anyway', default=False, options={'SKIP_SAVE'},
                        description='Write this scene although the recipe file, or the layout Blueprint, was changed by something else '
                                    'since, or although many of its parts are gone')

    def invoke(self, context, event):
        entry = entry_for(context.scene.get(SCENE_ID) or '')
        if not entry or entry['kind'] != 'recipe':
            return self.execute(context)   # a prefab is one file, saved; nothing else is rebuilt from it
        message = (f'Rebuild the {entry["label"].lower()} in Unreal from this scene? Everything in its layout Blueprint is replaced by what is '
                   f'here. Work done in the Station Workshop or the Blueprint editor is not in this scene and would be lost. '
                   f'The previous Blueprint and recipe are kept as backups.')
        try:
            return context.window_manager.invoke_confirm(self, event, title='Apply anyway' if self.force else 'Apply', message=message,
                                                         confirm_text='Apply Anyway' if self.force else 'Apply')
        except TypeError:   # a Blender whose confirm takes no wording of its own
            return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        scene = context.scene
        st = scene.ss_scenes
        entry = entry_for(scene.get(SCENE_ID) or '')
        if not entry:
            self.report({'ERROR'}, 'set the project root in the add-on preferences' if scene.get(SCENE_ID) and not core.project_root()
                        else 'this is not an opened game scene: use Open Scene first')
            return {'CANCELLED'}
        try:
            path, summary = write_scene(scene, entry, force=self.force)
        except SceneStale as e:
            set_report(st, 'not applied: it would lose something', [str(e)], can_force=True)
            self.report({'ERROR'}, f'Not applied. {e}')
            return {'CANCELLED'}
        except SceneRefused as e:
            core.deselect_all(context)
            for obj, _ in e.problems:
                if obj.name in context.view_layer.objects:
                    obj.hide_set(False)
                    obj.select_set(True)
                    context.view_layer.objects.active = obj
            lines = describe(e.problems)
            set_report(st, f'refused: {len(e.problems)} to fix (selected)', lines)
            self.report({'ERROR'}, 'Apply refused. ' + '; '.join(lines))
            return {'CANCELLED'}
        except Exception as e:
            set_report(st, str(e))
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        root = core.project_root()
        where = path.relative_to(root).as_posix() if root and root in path.parents else str(path)
        wrote = f'wrote {where}: {summary["parts"]} parts, {summary["lights"]} lights'
        lines = []
        if summary['renamed']:
            lines.append(f'{summary["renamed"]} names numbered apart to keep them unique')
        if summary['skipped_lights']:
            lines.append(f'{summary["skipped_lights"]} lights left out: the recipe holds point lights only')
        if summary['skipped_edits']:
            lines.append(f'{summary["skipped_edits"]} Edit Mesh copies left out: they are meshes being fixed, not parts of the scene')
        if summary['previous']:
            lines.append(f'the file it replaced is kept at {summary["previous"]}')
        if entry['kind'] != 'recipe':
            set_report(st, wrote, lines)
            return {'FINISHED'}
        outcome, detail = send_to_editor(entry, path, force=self.force)
        if outcome == 'applied':
            if isinstance(detail, dict):
                if detail.get('backup'):
                    lines.append(f'the previous Blueprint is kept at {detail["backup"]}')
                detail = f'{detail.get("components", "?")} components in {detail.get("blueprint", "the layout Blueprint")}'
            set_report(st, 'applied: ' + wrote, [f'Unreal rebuilt the layout: {detail}'] + lines)
            return {'FINISHED'}
        if outcome == 'refused':
            why = last_line(detail)
            stale = STALE_EDITOR in str(detail)
            set_report(st, 'saved, but NOT in the game: Unreal refused it', [why] + (['Apply Anyway rebuilds it all the same.'] if stale else []) + lines,
                       can_force=stale)
            self.report({'ERROR'}, f'{wrote}, but Unreal refused it: {why}')
            return {'FINISHED'}
        command = headless_command(entry, path)
        set_report(st, 'saved, but NOT in the game yet', ['Unreal is not open. Open the project in the Unreal editor, then press Apply again.',
                                                          '(Copy Command is the command-line route, for use with the editor closed.)', wrote] + lines, command)
        self.report({'WARNING'}, f'Saved, but NOT in the game yet: open the Unreal editor and press Apply again. ({wrote})')
        return {'FINISHED'}


class SSLINK_OT_adopt_parts(bpy.types.Operator):
    bl_idname = 'ss_link.adopt_parts'
    bl_label = 'Move Selected into Parts'
    bl_description = ("Make the selected tagged parts this scene's own. For parts added from the library here, which land in a "
                      "collection shared with other scenes; that collection is then unlinked from this scene")
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            moved, unlinked = adopt(context.scene, list(context.selected_objects))
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        if not moved:
            self.report({'ERROR'}, 'select the tagged parts that belong in this scene')
            return {'CANCELLED'}
        set_report(context.scene.ss_scenes, f'{moved} parts moved into Parts', [f'unlinked from this scene: {", ".join(unlinked)}'] if unlinked else [])
        return {'FINISHED'}


class SSLINK_OT_copy_scene_command(bpy.types.Operator):
    bl_idname = 'ss_link.copy_scene_command'
    bl_label = 'Copy Command'
    bl_description = 'Copy the PowerShell command that applies the written recipe without an open editor'

    def execute(self, context):
        command = context.scene.ss_scenes.command
        if not command:
            self.report({'ERROR'}, 'no command yet: Apply writes one when no editor answers')
            return {'CANCELLED'}
        context.window_manager.clipboard = command
        self.report({'INFO'}, 'copied')
        return {'FINISHED'}


classes = (SSSceneState, SSLINK_OT_refresh_scenes, SSLINK_OT_open_scene, SSLINK_OT_apply_scene, SSLINK_OT_adopt_parts,
           SSLINK_OT_copy_scene_command)


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.ss_scenes = PointerProperty(type=SSSceneState)
    refresh_scene_items()


def unregister():
    del bpy.types.Scene.ss_scenes
    for c in reversed(classes):
        bpy.utils.unregister_class(c)


def draw(layout, context):
    st = context.scene.ss_scenes
    row = layout.row(align=True)
    row.prop(st, 'scene', text='')
    row.operator('ss_link.refresh_scenes', text='', icon='FILE_REFRESH')
    row = layout.row(align=True)
    row.operator('ss_link.open_scene', icon='SCENE_DATA').reload = False
    row.operator('ss_link.open_scene', text='', icon='LOOP_BACK').reload = True
    opened = entry_label(context.scene)
    col = layout.column(align=True)
    col.enabled = bool(opened)
    col.operator('ss_link.apply_scene', text=f'Apply {opened}' if opened else 'Apply Scene', icon='CHECKMARK').force = False
    col.operator('ss_link.adopt_parts', icon='OUTLINER_COLLECTION')
    if st.status:
        core.draw_wrapped(layout, st.status, context)
    if st.report:
        for line in st.report.split('\n')[:8]:
            core.draw_wrapped(layout, line, context)
    if st.can_force and opened:
        layout.operator('ss_link.apply_scene', text='Apply Anyway', icon='ERROR').force = True
    if st.command:
        layout.operator('ss_link.copy_scene_command', icon='COPYDOWN')
    if not opened:
        core.draw_wrapped(layout, 'One mesh and not a scene (a hazard, the station exterior)? Select it, or pick it in the parts list, '
                                  'and use Edit Mesh from Unreal.', context, icon='INFO')


def entry_label(scene):
    """The label of the game scene this Blender scene holds, or '' when it is an ordinary scene."""
    ident = scene.get(SCENE_ID) or ''
    for spec in RECIPE_SCENES:
        if spec['id'] == ident:
            return spec['label']
    return ident[len('prefab:'):] if ident.startswith('prefab:') else ''
