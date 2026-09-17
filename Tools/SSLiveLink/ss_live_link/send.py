"""Send to Unreal / Edit Mesh: meshes authored or fixed here, sent to the project as real assets.

Send to Unreal writes each selected mesh as a GLB with a sidecar into Artifacts/LiveLink/Outbox, which the
editor side (Content/Python/ss_send.py) imports: at once when an editor answers, otherwise when one next
starts. The object is then tagged with the asset it became, so Push places it like any library part.
Until the editor's catalogue lists the new asset, a row in Artifacts/PrefabLibrary/sent.json stands in for
it; core.merged_rows() is how the parts list and add_part come to know those rows.

Edit Mesh asks the editor for the real mesh of the selected part (or, with nothing selected, of the
highlighted row), brings it in as one object flagged ss_edit, and Send to Unreal on that object replaces
the original asset in place: its shape only, the asset keeps its own materials.

Only three things ever send over an asset that exists: the object it was sent from (marked ss_sent), the
one object Edit Mesh made from it (is_edit_copy), and a mesh sent with Replace existing ticked. A placed
proxy never does, a new mesh whose name happens to be taken is refused, and a duplicate or a separated
piece of an Edit Mesh copy is new work: Blender copies the ss_edit flag with everything else, so the flag
alone proves nothing, and such a copy is sent as a new asset under BLENDER_BASE, never over the pack's.
The editor keeps a copy of every asset file it imports over (Artifacts/LiveLink/Backups).

The asset's pivot is the object's origin and its shape is the object's local shape with modifiers applied:
the world transform is left out of the file, because Push sends it as the actor's transform.

The interface every feature module shares:
  register() / unregister()   called with the rest of the add-on, after library.py and before panel.py
                              (unregister in the reverse order).
  draw(layout, context)       called by the panel after its own boxes. layout is this feature's box, titled
                              'Send to Unreal'.
State lives in a PropertyGroup of this module's own, scene.ss_send, not in library.py's SSLinkState.
"""
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import hashlib
import json
import os
import re
import uuid

import bpy
from bpy.props import BoolProperty, EnumProperty, PointerProperty, StringProperty
from mathutils import Matrix

from . import core, editor_link, library

# Where meshes authored here live in the project. Outside /Game/SpaceSurvival on purpose: that folder is always
# cooked (Config/DefaultGame.ini), so every experiment sent would ship to testers with its materials and
# textures. Here a sent mesh ships exactly when something in the game uses it. Content/Python/ss_send.py has the same.
BLENDER_BASE = '/Game/Blender'
OUTBOX = Path('Artifacts/LiveLink/Outbox')     # under the project root; the self-test points it elsewhere
EDITS = '_Edits'                               # the Outbox folder for fixes that go back over the asset Edit Mesh fetched
PROP_EDIT = core.PROP_EDIT                     # set on the copy Edit Mesh brings in: sending it replaces its asset
PROP_EDIT_AS = 'ss_edit_as'                    # the name Edit Mesh gave that copy: a duplicate of it carries another
PROP_SENT = 'ss_sent'                          # set on the object an asset was sent from: only it sends to that asset again
PROP_SLOT = 'ss_slot'                          # on a material Blender renamed as Edit Mesh brought it in: its name in the asset
STAND_IN = 'SSProxy:'                          # how core.proxy_mesh names the cached mesh every proxy of an asset shares
COPY_SUFFIX = re.compile(r'\.\d{3,}$')         # the '.001' Blender adds to a name that is taken
EDIT_COLLECTION = 'SS Edit'
# The editor runs a remote call in a scope of its own where only json and ss_prefabs are imported, so the
# expression brings its module with it.
REMOTE = "__import__('ss_send')."
# The types above the categories, as GROUPS in Content/Python/ss_prefabs.py has them. A catalogue written
# before groups existed carries no mapping of its own, so this is what a sent row's group falls back to.
GROUPS = (
    ('Building', ('Walls', 'Floors', 'Ceilings', 'Doors', 'Stairs & Rails', 'Pillars & Frames')),
    ('Decoration', ('Props', 'Furniture', 'Containers', 'Signs & Banners', 'Pipes & Cables', 'Machines',
                    'Consoles & Screens', 'Lights')),
    ('Exterior & Space', ('Station Exterior', 'Asteroids & Debris', 'Wreckage', 'Planets & Sky')),
    ('Ships', ('Ship Parts',)),
    ('Characters & Robots', ('Characters & Robots',)),
    ('Game Objects', ('Game Objects',)),
)
CATEGORY_NAMES = [c for _, categories in GROUPS for c in categories] + ['Misc']


# ---------------------------------------------------------------- names and places
def safe_name(text, fallback='Mesh'):
    """text as an Unreal asset or folder name: [A-Za-z0-9_] only, no doubled or outer underscores."""
    return re.sub(r'_+', '_', re.sub(r'[^A-Za-z0-9_]+', '_', text or '')).strip('_') or fallback


def category_folder(category):
    """'Pipes & Cables' -> 'Pipes_Cables': the category as the folder under BLENDER_BASE and under the Outbox."""
    return safe_name(category, 'Misc')


FOLDER_CATEGORY = {category_folder(c): c for c in CATEGORY_NAMES}


def group_of(category, catalog=None):
    mapping = (catalog or {}).get('group_categories') or dict(GROUPS)
    return next((group for group, categories in mapping.items() if category in categories), 'Misc')


def pack_of(asset):
    """The pack an asset path belongs to, by the same rule as pack_of in Content/Python/ss_prefabs.py."""
    parts = asset.split('/')
    if len(parts) > 3 and parts[2] in ('StarterBundle', 'SpaceSurvival'):
        return parts[2] + '/' + parts[3]
    return parts[2] if len(parts) > 2 else 'Game'


def outbox_dir():
    root = core.project_root()
    if not root:
        raise RuntimeError('set the project root in the add-on preferences')
    return root / OUTBOX


def is_edit_copy(obj):
    """True for the one object Edit Mesh made from an asset, which alone may be sent back over it.

    Shift+D, Alt+D and Separate all copy custom properties, so a new part begun from a piece of a pack door
    still says ss_edit and still names the door as its asset. What a copy cannot have is the name: Blender
    calls it 'SM_Door.001', or the owner calls it something of their own. import_edit_copy records the
    name its object ended up with; only the object still wearing it is the edit.
    """
    return bool(obj.get(PROP_EDIT)) and bool(obj.get(core.PROP_ASSET)) and obj.name == obj.get(PROP_EDIT_AS)


def sendable(obj):
    """A mesh this feature may turn into an asset: the owner's own work, never a proxy of a library part.

    Untagged is new work. ss_edit came in through Edit Mesh to be fixed, or is a piece copied from such
    an object, which plan() files as a new asset. Tagged under BLENDER_BASE AND marked ss_sent with that
    same asset is the object the asset was sent from. Any other tagged object is
    a stand-in, and sending it would replace the asset with its proxy: Add at Cursor, Load Prefab and Pull
    tag a proxy of the owner's own asset exactly as they tag a pack's, and after a Rebuild Catalogue that
    proxy is the editor's export without textures. So the tag alone proves nothing; the mark does, and
    whatever shows the cached stand-in mesh is a proxy whatever else it carries.
    """
    if obj.type != 'MESH' or obj.data.name.startswith(STAND_IN):
        return False
    asset = str(obj.get(core.PROP_ASSET) or '')
    return not asset or bool(obj.get(PROP_EDIT)) or (asset.startswith(BLENDER_BASE + '/') and obj.get(PROP_SENT) == asset)


def plan(obj, category, name=''):
    """Where obj goes: the target package, the asset path it is tagged with, and its files in the Outbox.

    The object Edit Mesh made goes back over the asset it came from. An object sent before keeps its
    asset, so every instance already placed in a level takes the change. Typing a name sends either of
    them as a new asset instead, as the Name field's tooltip says. Anything else, a copy of an Edit Mesh
    object included, becomes BLENDER_BASE/<category>/SM_<name or the object's name>.
    """
    asset = str(obj.get(core.PROP_ASSET) or '')
    package = asset.split('.')[0]
    if is_edit_copy(obj) and not name:
        leaf = package.rsplit('/', 1)[-1]
        entry = core.catalog_entry(asset)
        # Two packs can each own an SM_Door: the hash keeps their fixes apart in the one _Edits folder.
        stem = f'{safe_name(leaf)}_{hashlib.md5(package.encode("utf-8")).hexdigest()[:4]}'
        return {'target': package, 'asset': asset, 'folder': EDITS, 'stem': stem, 'edit': True,
                'category': entry['category'] if entry else 'Misc'}
    if (package.startswith(BLENDER_BASE + '/') and not name and obj.get(PROP_SENT) == asset and not obj.get(PROP_EDIT)
            and package.count('/') == BLENDER_BASE.count('/') + 2):
        folder, leaf = package[len(BLENDER_BASE) + 1:].split('/')
        return {'target': package, 'asset': asset, 'folder': folder, 'stem': leaf[3:] if leaf.startswith('SM_') else leaf,
                'edit': False, 'category': FOLDER_CATEGORY.get(folder, category)}
    stem = safe_name(name or obj.name)
    stem = safe_name(stem[3:]) if stem.upper().startswith('SM_') else stem   # SM_SM_Crate helps nobody
    folder = category_folder(category)
    package = f'{BLENDER_BASE}/{folder}/SM_{stem}'
    return {'target': package, 'asset': f'{package}.SM_{stem}', 'folder': folder, 'stem': stem, 'edit': False, 'category': category}


# ---------------------------------------------------------------- the mesh that is sent
def local_copy(context, objects, anchor, name):
    """A temporary object at the world origin: objects' evaluated geometry, joined, in anchor's local frame.

    Evaluated, so modifiers are applied without touching the owner's objects; at the origin, so the file
    holds no world transform and the asset's pivot is anchor's origin.
    """
    depsgraph = context.evaluated_depsgraph_get()
    inverse = anchor.matrix_world.inverted() if len(objects) > 1 else None
    temps, meshes = [], []
    for o in [anchor] + [o for o in objects if o is not anchor]:
        me = bpy.data.meshes.new_from_object(o.evaluated_get(depsgraph), preserve_all_data_layers=True, depsgraph=depsgraph)
        if o is not anchor:
            into_anchor = inverse @ o.matrix_world
            me.transform(into_anchor)
            if into_anchor.determinant() < 0:
                me.flip_normals()   # a mirrored object would otherwise arrive inside out
        temp = bpy.data.objects.new(name, me)
        context.scene.collection.objects.link(temp)
        temps.append(temp)
        meshes.append(me)
    core.deselect_all(context)
    for temp in temps:
        temp.select_set(True)
    context.view_layer.objects.active = temps[0]
    if len(temps) > 1:
        bpy.ops.object.join()
    for me in meshes[1:]:
        if me.users == 0:
            bpy.data.meshes.remove(me)   # join removes the objects it folded in and leaves their meshes behind
    return temps[0]


def measure(me):
    """(origin, extent) of a mesh's local bounds in Unreal's frame, centimetres, and its triangle count."""
    if not me.vertices:
        raise RuntimeError('there is no geometry to send')
    co = [0.0] * (3 * len(me.vertices))
    me.vertices.foreach_get('co', co)
    lo = [min(co[i::3]) for i in range(3)]
    hi = [max(co[i::3]) for i in range(3)]
    flip = (1.0, -1.0, 1.0)
    origin = [round(flip[i] * (lo[i] + hi[i]) / 2 * 100.0, 4) for i in range(3)]
    extent = [round((hi[i] - lo[i]) / 2 * 100.0, 4) for i in range(3)]
    me.calc_loop_triangles()
    return origin, extent, len(me.loop_triangles)


def export_glb(context, temp, path):
    """temp, alone, as a GLB: +Y up, materials and their images inside the file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    core.deselect_all(context)
    temp.select_set(True)
    context.view_layer.objects.active = temp
    # Written beside the real name and moved over it: the editor never reads half a file, and a failed
    # export leaves the last good one in place.
    part = path.with_name(path.stem + '.part.glb')
    result = bpy.ops.export_scene.gltf(filepath=str(part), export_format='GLB', use_selection=True, export_apply=True,
                                       export_yup=True, export_materials='EXPORT', export_animations=False, export_extras=False)
    if 'FINISHED' not in result or not part.exists():
        raise RuntimeError(f'the glTF exporter wrote nothing for {path.name}')
    os.replace(part, path)


@contextmanager
def asset_material_names(me):
    """While the file is written, the materials Edit Mesh brought in carry the names their asset knows them by.

    Blender names an imported material 'Drone01.001' when the file already holds a 'Drone01', and one
    placed proxy of the part is enough for that. The editor gives a slot its old material back by that
    name, so the '.001' would cost a pack asset every material it has. Whatever holds the name steps
    aside for the export and all names are put back after it: a lasting rename would change what the
    owner's other meshes send.
    """
    on_mesh = [m for m in me.materials if m]
    swaps = []   # (material, its name here, its name in the asset, the material that held that name or None)
    try:
        for mat in on_mesh:
            want, here = mat.get(PROP_SLOT), mat.name
            if not want or here == want or COPY_SUFFIX.sub('', here) != want:
                continue   # never renamed, or renamed since by the owner, whose choice stands
            holder = bpy.data.materials.get(want)
            if holder is not None and (holder.library or any(holder == m for m in on_mesh)):
                continue   # both go into this one file; the editor tells a '.001' from its original itself
            if holder is not None:
                holder.name = want + '.aside'
            mat.name = want
            swaps.append((mat, here, want, holder))
        yield
    finally:
        for mat, here, want, holder in reversed(swaps):
            mat.name = here
            if holder is not None:
                holder.name = want


def adopt_as_proxy(asset, me):
    """Make me the cached stand-in for asset, so Add at Cursor and every proxy already placed show what was sent.

    Nothing that is sent shows the old stand-in (sendable() refuses it), so the old one can simply go.
    """
    key = STAND_IN + asset
    old = bpy.data.meshes.get(key)
    if old and old is not me:
        old.user_remap(me)
        bpy.data.meshes.remove(old)
    me.name = key
    me.use_fake_user = True


# ---------------------------------------------------------------- the side catalogue
# sent.json itself is core's (read_sent, merged_rows, merged_catalog): the parts list in library.py is filled
# from it, and library.py sits above this module. The names stay here for whoever knew them as send.<name>.
read_sent, write_sent, catalogued_assets = core.read_sent, core.write_sent, core.catalogued_assets
merged_rows, merged_catalog, teach_core = core.merged_rows, core.merged_catalog, core.teach_sent


def record_sent(row):
    """Put row in sent.json, replacing an older row for the same asset. An asset the catalogue lists needs none."""
    rows = [r for r in read_sent() if r['asset'] != row['asset']]
    if row['asset'] not in catalogued_assets():
        rows.append(row)
        teach_core([row])
    write_sent(rows)


# ---------------------------------------------------------------- sending
def send_one(context, objects, anchor, where):
    """Write the GLB and its sidecar for one asset, tag anchor with it, and return what was written."""
    root = core.project_root()
    glb = outbox_dir() / where['folder'] / (where['stem'] + '.glb')
    temp = local_copy(context, objects, anchor, where['target'].rsplit('/', 1)[-1])
    me = temp.data
    try:
        origin, extent, triangles = measure(me)
        with asset_material_names(me):
            materials = [m.name if m else '' for m in me.materials]   # as the file names them
            export_glb(context, temp, glb)
    except Exception:
        bpy.data.objects.remove(temp, do_unlink=True)
        bpy.data.meshes.remove(me)
        raise
    bpy.data.objects.remove(temp, do_unlink=True)
    adopt_as_proxy(where['asset'], me)
    exported = datetime.now().isoformat(timespec='seconds')
    sidecar = {'target': where['target'], 'glb': str(glb.relative_to(root)).replace('\\', '/'), 'name': where['stem'],
               'category': where['category'], 'edit': where['edit'], 'source_blend': bpy.data.filepath,
               'source_objects': [o.name for o in objects], 'exported': exported, 'triangles': triangles,
               'materials': materials, 'bounds_cm': {'origin': origin, 'extent': extent}}
    glb.with_suffix('.json').write_text(json.dumps(sidecar, indent=1), encoding='utf-8')
    name = where['asset'].split('.')[-1]
    record_sent({'asset': where['asset'], 'name': name, 'pack': pack_of(where['asset']),
                 'group': group_of(where['category'], core._catalog['data']), 'category': where['category'],
                 'origin': origin, 'extent': extent, 'radius': round(sum(e * e for e in extent) ** 0.5, 4), 'triangles': triangles,
                 'materials': [], 'proxy': os.path.relpath(glb, core.library_dir()).replace('\\', '/'), 'sent': exported})
    anchor[core.PROP_ASSET] = where['asset']
    if not where['edit']:
        # New work, or a copy of an Edit Mesh object sent as an asset of its own: from here on it is the object
        # that asset was sent from, and nothing of the mesh it was copied from.
        for key in (PROP_EDIT, PROP_EDIT_AS):
            if key in anchor:
                del anchor[key]
        anchor[PROP_SENT] = where['asset']   # what sendable() asks for before this object may send to the asset again
        if not anchor.get(core.PROP_LINK):
            anchor[core.PROP_LINK] = uuid.uuid4().hex
    return {'name': name, 'asset': where['asset'], 'glb': glb, 'triangles': triangles, 'edit': where['edit'], 'target': where['target']}


def owns(anchor, where):
    """True when sending anchor to where replaces nothing but anchor's own earlier send, or the asset Edit Mesh took it from.

    plan() says 'edit' for the one object Edit Mesh made and for nothing else, and the mark of an earlier
    send is ss_sent, never the ss_asset tag: a tag is copied with the object, and a proxy carries one too.
    """
    if where['edit']:
        return is_edit_copy(anchor)
    return str(anchor.get(PROP_SENT) or '').lower() == where['asset'].lower()


def taken(jobs):
    """The asset names among jobs' targets that exist already and belong to something other than the object sent.

    A new mesh is filed under its object's name, and names like 'Cube' repeat: without this the second
    Cube lands on the first one's asset and every instance placed in a level changes shape. Asked of all
    Blender can see without the editor: the sent rows, the catalogue, and the files waiting in the Outbox.
    Unreal's asset names ignore case, and so do the Outbox's file names on Windows.
    """
    known = {r['asset'].lower() for r in read_sent()} | {a.lower() for a in catalogued_assets()}
    names = []
    for _, anchor, where in jobs:
        side = outbox_dir() / where['folder'] / (where['stem'] + '.json')
        if not owns(anchor, where) and (where['asset'].lower() in known or side.exists() or side.with_suffix('.glb').exists()):
            names.append(where['target'].rsplit('/', 1)[-1])
    return names


def send_objects(context, objects, category, name='', one_asset=False, replace=False):
    """Send objects as one asset each, or joined as a single asset whose pivot is the active object's origin.

    replace lets a mesh that does not own its target (see owns) be sent over the asset that has it.
    """
    objects = [o for o in objects if sendable(o)]
    if not objects:
        raise RuntimeError('select a mesh of your own: a library proxy is not sent back (Edit Mesh brings the real mesh in)')
    active = context.view_layer.objects.active
    selected = [o for o in context.view_layer.objects if o is not None and o.select_get()]
    mode = active.mode if active else 'OBJECT'
    if mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')   # edit-mode changes only reach the mesh on the way out
    try:
        if one_asset and len(objects) > 1:
            anchor = active if active in objects else objects[0]
            jobs = [(objects, anchor, plan(anchor, category, name))]
        else:
            jobs = [([o], o, plan(o, category, name if len(objects) == 1 else '')) for o in objects]
        targets = [where['target'].lower() for _, _, where in jobs]
        twice = [(anchor, where) for _, anchor, where in jobs if targets.count(where['target'].lower()) > 1]
        if twice:
            names = ', '.join(sorted({where['target'].rsplit('/', 1)[-1] for _, where in twice}))
            # An object sent before goes to its asset whatever it is called, so renaming a copy of it changes nothing.
            if any(anchor.get(core.PROP_ASSET) for anchor, _ in twice):
                raise RuntimeError(f'two objects would both become {names}: send one of them alone (with a Name, a sent mesh becomes a new asset)')
            raise RuntimeError(f'two objects would both become {names}: rename one')
        exists = [] if replace else taken(jobs)
        if exists:
            raise RuntimeError(f'{", ".join(exists)} already exists: give yours another name, or tick Replace existing to send over it')
        return [send_one(context, group, anchor, where) for group, anchor, where in jobs]
    finally:
        core.deselect_all(context)
        for o in selected:
            o.select_set(True)
        context.view_layer.objects.active = active
        if mode != 'OBJECT' and active:
            bpy.ops.object.mode_set(mode=mode)


def notify_editor():
    """Ask the open editor to import the Outbox now. Returns (its summary or None, the line to show)."""
    try:
        summary = editor_link.link.call(REMOTE + 'import_outbox()')
    except Exception as e:
        if str(e).startswith('editor error'):
            return None, 'sent, but the editor could not import: ' + (str(e).strip().splitlines() or ['?'])[-1]
        return None, 'queued: Unreal is not open, so it imports by itself when the Unreal editor next starts'
    if not isinstance(summary, dict):
        return None, f'sent, but the editor answered {summary!r}'
    text = f'imported {len(summary.get("imported", []))}: {", ".join(summary.get("imported", [])) or "nothing new"}'
    if summary.get('failed'):
        text += '; failed: ' + ', '.join(f'{n} ({err})' for n, err in summary['failed'])
    if summary.get('backups'):
        text += '; the old file is kept at ' + ', '.join(str(path) for _, path in summary['backups'])
    return summary, text


# ---------------------------------------------------------------- editing a project mesh
def import_edit_copy(context, asset, glb):
    """The editor's export of asset as one object at the 3D cursor, flagged so Send to Unreal replaces the asset."""
    before = set(bpy.data.objects)
    held = {m.name for m in bpy.data.materials}
    bpy.ops.import_scene.gltf(filepath=str(glb))
    context.view_layer.update()
    # A name that was taken came in as 'Name.001'; an asset's own names hold no dot, so the suffix is
    # Blender's. Remember the real one, for asset_material_names to write into the file that goes back.
    for mat in [m for m in bpy.data.materials if m.name not in held]:
        real = COPY_SUFFIX.sub('', mat.name)
        if real != mat.name and real in held:
            mat[PROP_SLOT] = real
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    if not meshes:
        for o in new:
            bpy.data.objects.remove(o, do_unlink=True)
        raise RuntimeError(f'{glb.name} holds no mesh')
    # Whatever nodes the file had, the asset's own frame is the file's world: bake each node's place into
    # its mesh, so the one object that remains has the asset's pivot as its origin.
    for o in meshes:
        world = o.matrix_world.copy()
        o.parent = None
        if o.data.users > 1:
            o.data = o.data.copy()
        o.data.transform(world)
        if world.determinant() < 0:
            o.data.flip_normals()
        o.matrix_world = Matrix.Identity(4)
    core.deselect_all(context)
    for o in meshes:
        o.select_set(True)
    context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = context.view_layer.objects.active
    for o in new:
        if o is not obj and o.name in bpy.data.objects:
            bpy.data.objects.remove(o, do_unlink=True)
    col = core.ensure_collection(EDIT_COLLECTION)
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)
    obj.name = obj.data.name = asset.split('.')[-1]
    obj[core.PROP_ASSET] = asset
    obj[PROP_EDIT] = True
    obj[PROP_EDIT_AS] = obj.name   # as Blender settled it ('SM_Door.001' when a placed proxy holds 'SM_Door'): see is_edit_copy
    obj.matrix_world = Matrix.Translation(context.scene.cursor.location)
    core.deselect_all(context)
    obj.select_set(True)
    context.view_layer.objects.active = obj
    return obj


# ---------------------------------------------------------------- UI state and operators
class SSSendState(bpy.types.PropertyGroup):
    category: EnumProperty(name='Category', items=[(c, c, '') for c in CATEGORY_NAMES], default='Props',
                           description='The library category, and the folder under ' + BLENDER_BASE + ', a new mesh is filed in')
    name: StringProperty(name='Name', default='',
                         description='Asset name (SM_ is added). Empty: the object\'s own name, and a mesh sent before keeps its asset')
    one_asset: BoolProperty(name='One asset', default=False,
                            description='Join the selection into a single asset whose pivot is the active object\'s origin')
    replace: BoolProperty(name='Replace existing', default=False,
                          description='Send a new mesh over the asset that already has its name: every placed instance of that asset '
                                      'takes the new shape. Unticks itself after the send')
    status: StringProperty(default='')
    note: StringProperty(default='')   # what the last Edit Mesh or send wants the owner to know, under the status


def replaced_by(context, ss):
    """The project assets a press of Send to Unreal would go over that are not the sender's own earlier sends:
    the asset an Edit Mesh copy came from, and anything at all while Replace existing is ticked."""
    picked = [o for o in context.selected_objects if o.type == 'MESH' and sendable(o)]
    name = ss.name.strip()
    over = [str(o[core.PROP_ASSET]).split('.')[0] for o in picked if is_edit_copy(o) and not name]
    if ss.replace:
        try:   # only what is really there to be replaced; the send itself decides, this is the question's wording
            over += taken([([o], o, plan(o, ss.category, name if len(picked) == 1 else '')) for o in picked])
        except Exception:
            pass
    return list(dict.fromkeys(over))


class SSLINK_OT_send_mesh(bpy.types.Operator):
    bl_idname = 'ss_link.send_mesh'
    bl_label = 'Send to Unreal'
    bl_description = ('Export the selected meshes of your own to the project (Artifacts/LiveLink/Outbox) and import them as '
                      'static meshes: now when the editor is open, otherwise when it next starts')
    bl_options = {'UNDO'}

    def invoke(self, context, event):
        # From the button, a send that goes over something in the project asks first and names it.
        over = replaced_by(context, context.scene.ss_send)
        if not over:
            return self.execute(context)
        message = (f'Replace {", ".join(over)} in the Unreal project? Every placed copy takes the new shape. '
                   f'The old file is kept under Artifacts/LiveLink/Backups.')
        try:
            return context.window_manager.invoke_confirm(self, event, title='Send to Unreal', message=message, confirm_text='Replace')
        except TypeError:   # a Blender whose confirm takes no wording of its own
            return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        ss = context.scene.ss_send
        picked = [o for o in context.selected_objects if o.type == 'MESH']
        proxies = [o.name for o in picked if not sendable(o)]
        try:
            sent = send_objects(context, picked, ss.category, ss.name.strip(), ss.one_asset, ss.replace)
        except Exception as e:
            ss.status, ss.note = f'not sent: {e}', ''
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        summary, text = notify_editor()
        ss.name = ''   # a name left in the field would send the next mesh over this one
        ss.replace = False   # and a tick left on would let the next mesh take whatever asset shares its name
        ss.status = f'{", ".join(s["name"] for s in sent)}: {text}'
        if proxies:
            ss.status += f' ({len(proxies)} library proxies left alone)'
        notes = []
        edits = [s for s in sent if s['edit']]
        if edits:
            notes.append(f'{", ".join(s["target"] for s in edits)} is replaced in place: its shape only, the materials it has in '
                         f'Unreal are kept whatever was painted here. Placed parts show the fix; this copy can be deleted.')
        news = [s for s in sent if not s['edit']]
        if news:
            notes.append(f'New assets are filed under {BLENDER_BASE}/<Category>: they are in the parts list now, and Push places them.')
        ss.note = ' '.join(notes)
        # A mesh that has just become an asset is a part: show it in the list this scene already has.
        st = context.scene.ss_link
        if st.parts:
            for s in news:
                row = core.catalog_entry(s['asset'])
                if row:
                    library.show_row(st, row)
        failed = summary is None and not text.startswith('queued') or bool(summary and summary.get('failed'))
        self.report({'WARNING'} if failed else {'INFO'}, ss.status)
        return {'FINISHED'}


def edit_target(context):
    """(asset, how it was chosen), or (None, why not): what Edit Mesh fetches.

    The thing the owner clicked on comes first. 'This looks wrong, let me fix it' is a click on the thing
    and then the button; reading the list's highlighted row instead fetched whatever that happened to be
    (the first row, after Open Scene). With nothing tagged selected, the list's row it is.
    """
    obj = context.view_layer.objects.active
    if obj is not None and obj.type == 'MESH' and obj.select_get() and obj.get(core.PROP_ASSET):
        if is_edit_copy(obj):
            return None, f'{obj.name} is already the mesh to fix: change it, then press Send to Unreal'
        if obj.get(PROP_SENT):
            return None, (f'{obj.name} is a mesh of your own: change it here and press Send to Unreal. '
                          f'(To fetch a library part instead, click on empty space first, then pick it in the list.)')
        return str(obj[core.PROP_ASSET]), f'the selected part, {obj.name}'
    st = context.scene.ss_link
    if not st.parts or st.part_index >= len(st.parts):
        return None, 'select a part in the viewport, or press Load Catalogue and pick one in the list'
    return st.parts[st.part_index].asset, 'the row highlighted in the parts list'


def edit_note(asset):
    """What the owner should know before fixing this mesh, beyond 'shape only'."""
    leaf = asset.split('.')[-1]
    entry = core.catalog_entry(asset)
    if leaf == 'SM_StationPitStop':
        return ('The ship collides with boxes generated separately from this shape (Artifacts/StationPitStop): they will not '
                'follow a change, and the pit stop pipeline writes this mesh again when it is re-run.')
    if entry and entry.get('category') in ('Game Objects', 'Station Exterior') and not core.loaded_by_game(asset):
        return ('The game does not load this mesh by name: it may be an unused version. The rows marked "in game" in the '
                'parts list are the ones a player sees.')
    return ''


class SSLINK_OT_edit_mesh(bpy.types.Operator):
    bl_idname = 'ss_link.edit_mesh'
    bl_label = 'Edit Mesh from Unreal'
    bl_description = ('Bring in the real mesh of the part selected in the viewport (with nothing selected: of the row highlighted '
                      'in the parts list) from the open Unreal editor, to fix its shape here; Send to Unreal then replaces the '
                      'original asset, keeping its materials')
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ss = context.scene.ss_send
        asset, how = edit_target(context)
        if not asset:
            ss.status, ss.note = how, ''
            self.report({'ERROR'}, how)
            return {'CANCELLED'}
        try:
            answer = editor_link.link.call(REMOTE + 'export_for_edit(' + repr(asset) + ')')
        except Exception as e:
            ss.status = f'Edit Mesh needs the open editor: {e}'
            self.report({'ERROR'}, ss.status)
            return {'CANCELLED'}
        glb = Path(answer['glb']) if isinstance(answer, dict) and answer.get('glb') else None
        if not glb or not glb.exists():
            ss.status = f'the editor exported nothing for {asset.split(".")[-1]}: {answer!r}'
            self.report({'ERROR'}, ss.status)
            return {'CANCELLED'}
        try:
            if context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            obj = import_edit_copy(context, asset, glb)
        except Exception as e:
            ss.status = f'could not bring in {glb.name}: {e}'
            self.report({'ERROR'}, ss.status)
            return {'CANCELLED'}
        ss.status = f'editing {obj.name} ({how}): Send to Unreal replaces {asset.split(".")[0]}'
        ss.note = ('Shape only: the asset keeps the materials it has in Unreal, so it may look grey here and repainting it '
                   'changes nothing in the game. ' + edit_note(asset)).strip()
        self.report({'INFO'}, ss.status)
        return {'FINISHED'}


classes = (SSSendState, SSLINK_OT_send_mesh, SSLINK_OT_edit_mesh)


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.ss_send = PointerProperty(type=SSSendState)


def unregister():
    del bpy.types.Scene.ss_send
    for c in reversed(classes):
        bpy.utils.unregister_class(c)


def draw(layout, context):
    ss = context.scene.ss_send
    col = layout.column(align=True)
    col.prop(ss, 'category')
    col.prop(ss, 'name')
    layout.prop(ss, 'one_asset')
    layout.prop(ss, 'replace')
    layout.operator('ss_link.send_mesh', icon='EXPORT')
    layout.operator('ss_link.edit_mesh', icon='EDITMODE_HLT')
    if ss.status:
        core.draw_wrapped(layout, ss.status, context)
    if ss.note:
        core.draw_wrapped(layout, ss.note, context, icon='INFO')
