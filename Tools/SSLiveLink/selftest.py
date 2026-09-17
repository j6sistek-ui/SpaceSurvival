"""Headless check of the Blender add-on against the project's catalogue and prefab folder.

  blender --background --factory-startup --python Tools/SSLiveLink/selftest.py -- --project <root> [--live]

Imports the add-on package from this folder, proves it registers, unregisters and registers again without
leaving anything behind, loads the catalogue, adds proxies, checks the proxy sits where the catalogue says
the mesh's bounds are (which proves the axis mapping, not just the code path), saves a prefab, reloads it,
round-trips the frame conversion, drives the operators of every module, the panel's feature boxes, and
push/pull/live against a stand-in editor. With --live it also pushes to and pulls from an open editor.
Prints SSLIVELINK_SELFTEST_OK with the numbers, or raises.
"""
from pathlib import Path
import ast
import json
import math
import os
import shutil
import sys
import types

import bpy
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ROOT = Path(argv[argv.index('--project') + 1]) if '--project' in argv else Path(__file__).resolve().parents[2]
LIVE = '--live' in argv
os.environ['SS_PROJECT_ROOT'] = str(ROOT)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ss_live_link as sl  # noqa: E402

# The parts list is the catalogue plus the meshes the owner has sent (sent.json). Every count below is taken from
# the catalogue file, so for this run the side catalogue is a file that does not exist.
sl.core.SENT = '_selftest_no_sent_rows.json'

# ---------------------------------------------------------------- the package and its registration
assert Path(sl.__file__).name == '__init__.py', f'expected the package, got {sl.__file__}'
names = [m.__name__.split('.')[-1] for m in sl.MODULES]
assert names == ['core', 'editor_link', 'library', 'prefabs', 'browser', 'groups', 'send', 'scenes', 'panel'], names
for module in sl.MODULES:
    assert callable(getattr(module, 'register', None)) and callable(getattr(module, 'unregister', None)), module.__name__
for feature in (sl.groups, sl.send, sl.scenes):
    assert callable(getattr(feature, 'draw', None)), feature.__name__
# What the single-file add-on offered as ss_live_link.<name> must still be there.
for name in ('project_root', 'library_dir', 'prefabs_dir', 'load_catalog', 'add_part', 'linked_objects', 'to_ue_rows', 'from_ue_rows',
             'rows_from_rotator', 'save_prefab', 'load_prefab', 'push', 'pull', 'link', 'get_icon', 'PROP_ASSET', 'PROP_LINK'):
    assert hasattr(sl, name), f'ss_live_link.{name} is gone'

OPERATORS = ('load_catalog', 'add_part', 'connect', 'push', 'pull', 'live', 'save_prefab', 'load_prefab', 'refresh_prefabs',
             'open_browser', 'build_browser', 'render_thumbnails', 'reload_thumbnails')


def footprint():
    """Everything registering may leave behind: classes in bpy.types, and properties on Scene."""
    return set(dir(bpy.types)), set(bpy.types.Scene.bl_rna.properties.keys())


def assert_clean(before, when):
    now = footprint()
    assert now[0] == before[0], (when, 'classes left behind', sorted(now[0] ^ before[0]))
    assert now[1] == before[1], (when, 'Scene properties left behind', sorted(now[1] ^ before[1]))
    # Property groups and preferences do not show in dir(bpy.types); ask the classes themselves.
    still = [c.__name__ for module in sl.MODULES for c in getattr(module, 'classes', ()) if c.is_registered]
    assert not still, (when, 'still registered', still)
    assert not hasattr(bpy.types.Scene, 'ss_link'), when
    assert not bpy.app.timers.is_registered(sl.live_tick), when
    assert sl.library._previews['collection'] is None, when


clean = footprint()
sl.register()
assert hasattr(bpy.types, 'SSLINK_PT_panel') and hasattr(bpy.types, 'SSLINK_UL_parts') and 'ss_link' in footprint()[1]
for op in OPERATORS:
    assert hasattr(bpy.types, 'SS_LINK_OT_' + op), op   # bpy.types names an operator after its idname, ss_link.<op>
assert bpy.types.SSLINK_PT_panel.bl_category == 'SS Link'
sl.unregister()
assert_clean(clean, 'after the first unregister')
sl.register()
print('SELFTEST package', names, 'registers, unregisters and registers again')

sc = bpy.context.scene
# a clean scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# ---------------------------------------------------------------- frame conversion
m = Matrix.Translation(Vector((1.2, -3.4, 0.55))) @ Matrix.Rotation(math.radians(37), 4, 'Z') @ Matrix.Rotation(math.radians(-12), 4, 'X')
rows = sl.to_ue_rows(m)
# mathutils is single precision: a hundredth of a millimetre is the honest tolerance in centimetres.
assert abs(rows[3][0] - 120) < 1e-3 and abs(rows[3][1] - 340) < 1e-3 and abs(rows[3][2] - 55) < 1e-3, rows[3]
back = sl.from_ue_rows(rows)
for i in range(4):
    for j in range(4):
        assert abs(back[i][j] - m[i][j]) < 1e-5, (i, j, back[i][j], m[i][j])
# A Blender +90 yaw (X toward +Y) is an Unreal -90 yaw (X toward -Y): forward vectors must agree after the flip.
rows = sl.to_ue_rows(Matrix.Rotation(math.radians(90), 4, 'Z'))
assert abs(rows[0][0]) < 1e-5 and abs(rows[0][1] + 1) < 1e-5, rows[0]
r90 = sl.rows_from_rotator([0, 0, 0], [0, -90, 0], [1, 1, 1])
assert all(abs(r90[i][j] - rows[i][j]) < 1e-5 for i in range(3) for j in range(3)), (r90, rows)

# ---------------------------------------------------------------- catalogue and proxies
cat = sl.load_catalog(force=True)
assert cat['meshes'], 'empty catalogue'
with_proxy = [x for x in cat['meshes'] if x.get('proxy')]
print('SELFTEST catalogue', len(cat['meshes']), 'meshes,', len(with_proxy), 'with proxies')
# Proxies must land where the catalogue's bounds say: pick assets whose bounds are off-centre so a mirror shows.
picks = sorted(with_proxy, key=lambda x: -abs(x['origin'][1]))[:3] + sorted(with_proxy, key=lambda x: -abs(x['origin'][0]))[:2]
checked = []
for entry in picks:
    obj = sl.add_part(entry['asset'])
    bpy.context.view_layer.update()
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    lo = [min(p[i] for p in pts) for i in range(3)]; hi = [max(p[i] for p in pts) for i in range(3)]
    centre_ue = [(lo[0] + hi[0]) / 2 * 100, -(lo[1] + hi[1]) / 2 * 100, (lo[2] + hi[2]) / 2 * 100]
    size_ue = [(hi[i] - lo[i]) * 100 for i in range(3)]
    expect_c = entry['origin']; expect_s = [2 * e for e in entry['extent']]
    tol = max(8.0, 0.03 * max(expect_s))
    for i in range(3):
        assert abs(centre_ue[i] - expect_c[i]) < tol, (entry['asset'], 'centre', 'xyz'[i], centre_ue[i], expect_c[i])
        assert abs(size_ue[i] - expect_s[i]) < tol, (entry['asset'], 'size', 'xyz'[i], size_ue[i], expect_s[i])
    checked.append(entry['name'])
print('SELFTEST proxies match catalogue bounds:', checked)

# ---------------------------------------------------------------- prefab save and load
parts = sl.linked_objects()
for k, o in enumerate(parts):
    o.matrix_world = Matrix.Translation(Vector((k * 3.0, 1.0 - k, 0.0))) @ Matrix.Rotation(math.radians(20 * k), 4, 'Z')
    o.select_set(True)
bpy.context.view_layer.update()
tmp_dir = sl.prefabs_dir() / '_SelfTest'
path = sl.save_prefab(parts, '_SelfTest', 'Cluster')
recipe = json.loads(path.read_text(encoding='utf-8'))
assert len(recipe['static_meshes']) == len(parts), recipe
world_before = {o[sl.PROP_ASSET] + o.name: o.matrix_world.copy() for o in parts}
pair = (parts[0].matrix_world.translation - parts[-1].matrix_world.translation).length
for o in parts:
    bpy.data.objects.remove(o, do_unlink=True)
made = sl.load_prefab('_SelfTest/Cluster', at=Vector((10.0, 10.0, 2.0)))
bpy.context.view_layer.update()
meshes = [o for o in made if o.type == 'MESH']
assert len(meshes) == len(recipe['static_meshes'])
pair2 = (meshes[0].matrix_world.translation - meshes[-1].matrix_world.translation).length
assert abs(pair - pair2) < 1e-4, (pair, pair2)
print('SELFTEST prefab round trip ok, pair distance', round(pair, 4))

# ---------------------------------------------------------------- operators, across the modules
# The operators live in different modules from the state and helpers they use; run them so a missing
# import shows here and not under the owner's mouse. The prefab written above is still on disk for this.
try:
    st = sc.ss_link
    assert bpy.ops.ss_link.load_catalog() == {'FINISHED'}
    assert len(st.parts) == len(cat['meshes']), (len(st.parts), len(cat['meshes']))
    assert st.category == 'All' and st.pack == 'All' and st.status.startswith('catalogue:'), st.status
    some = next(c for c in cat['categories'] if cat['categories'][c])
    st.category = some
    visible = [it for it in st.parts if sl.part_visible(it, st.category, st.pack)]
    assert visible and len(visible) == cat['categories'][some], (some, len(visible))
    assert st.parts[st.part_index].category == some, 'the filter must move the active part into view'
    before = len(sl.linked_objects())
    assert bpy.ops.ss_link.add_part() == {'FINISHED'}
    assert len(sl.linked_objects()) == before + 1 and bpy.context.view_layer.objects.active[sl.PROP_ASSET] == st.parts[st.part_index].asset
    bpy.data.objects.remove(bpy.context.view_layer.objects.active, do_unlink=True)
    st.category = 'All'
    assert bpy.ops.ss_link.refresh_prefabs() == {'FINISHED'}
    assert '_SelfTest/Cluster' in [i[0] for i in sl.library.prefab_items(st, bpy.context)]
    st.prefab = '_SelfTest/Cluster'
    assert bpy.ops.ss_link.load_prefab() == {'FINISHED'}
    loaded = [o for o in bpy.context.selected_objects if o.get(sl.PROP_ASSET)]
    assert len(loaded) == len(recipe['static_meshes']) and st.status.startswith('loaded _SelfTest/Cluster')
    st.save_category, st.save_name = '_SelfTest', 'Again'
    assert bpy.ops.ss_link.save_prefab() == {'FINISHED'}
    assert (tmp_dir / 'Again.json').exists() and '_SelfTest/Again' in [i[0] for i in sl.library.prefab_items(st, bpy.context)]
    for o in loaded:
        bpy.data.objects.remove(o, do_unlink=True)
    assert bpy.ops.ss_link.reload_thumbnails() == {'FINISHED'}
    assert st.status.startswith('thumbnails:'), st.status
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)   # Prefabs/ is committed: never leave the scratch prefabs in it
print('SELFTEST operators ok:', st.status)


# ---------------------------------------------------------------- the panel's feature boxes
class Recorder:
    """Stands in for a UILayout: any call is logged and answers with a child that does the same."""

    def __init__(self, log, name='panel'):
        self.__dict__.update(log=log, name=name)

    def __getattr__(self, call):
        if call.startswith('__'):
            raise AttributeError(call)

        def method(*args, **kw):
            self.log.append((self.name, call, args[0] if args else kw.get('text'), kw.get('icon')))   # an operator's idname, a label's text
            return Recorder(self.log, call)
        return method

    def __setattr__(self, key, value):
        self.log.append((self.name, 'set ' + key, value, None))


def silent(layout, context):
    pass


def talks(layout, context):
    layout.enabled = True
    layout.row(align=True).operator('ss_link.connect')


def breaks(layout, context):
    raise RuntimeError('boom')


log = []
real_features = sl.panel.FEATURES
sl.panel.FEATURES = tuple((types.SimpleNamespace(draw=fn), title, 'NONE') for fn, title in ((silent, 'Silent'), (talks, 'Talks'), (breaks, 'Breaks')))
try:
    drawn = sl.panel.draw_features(Recorder(log), bpy.context)
finally:
    sl.panel.FEATURES = real_features
assert drawn == ['Talks', 'Breaks'], drawn   # a feature that draws nothing gets no box at all
assert [e for e in log if e[:2] == ('panel', 'box')] == [('panel', 'box', None, None)] * 2, log
assert log[1] == ('box', 'label', 'Talks', 'NONE') and log[2] == ('box', 'set enabled', True, None), log   # title first, then the feature
assert ('box', 'label', 'RuntimeError: boom', 'ERROR') in log, log   # a failing feature says so in its own box
assert [(title, icon) for _, title, icon in real_features] == [('Send to Unreal', 'EXPORT'), ('Scenes', 'SCENE_DATA')]
assert [mod for mod, _, _ in real_features] == [sl.send, sl.scenes]
log = []
feature_boxes = sl.panel.draw_features(Recorder(log), bpy.context)
assert not [e for e in log if e[3] == 'ERROR'], log
# The whole panel, drawn into the recorder: its four boxes in order, and a button for every operator.
log = []
sl.panel.SSLINK_PT_panel.draw(types.SimpleNamespace(layout=Recorder(log)), bpy.context)
titles = [e[2] for e in log if e[:2] == ('box', 'label') and e[3] in ('LINKED', 'ASSET_MANAGER', 'IMAGE_DATA', 'OUTLINER_COLLECTION')]   # the title icons
assert titles == ['Editor', 'Parts library', 'Visual browser', 'Prefabs'], titles
buttons = {e[2].split('.', 1)[1] for e in log if e[1] == 'operator' and e[2].startswith('ss_link.')}
assert set(OPERATORS) <= buttons, sorted(set(OPERATORS) - buttons)
assert any(e[1] == 'label' and e[2] == st.parts[st.part_index].name for e in log), 'the active part is not described'
# The type buttons belong to the list they filter: inside the Parts library box, after Load Catalogue and before the
# category menu, the picture grid and the list. They were three boxes further down, filtering a list out of sight.
order = [k for k, e in enumerate(log) if (e[1], e[2]) in (('operator', 'ss_link.load_catalog'), ('template_list', 'SSLINK_UL_parts'))
         or e[1] == 'prop_enum' or (e[1] == 'label' and e[2] == 'Visual browser')]
kinds = [log[k][1] for k in order]
assert kinds[0] == 'operator' and kinds[-2:] == ['template_list', 'label'] and set(kinds[1:-2]) == {'prop_enum'} and len(kinds) > 5, kinds
assert 'edit_mesh' in buttons and [e[2] for e in log if e[1] == 'operator'].count('ss_link.edit_mesh') == 2, 'Edit Mesh sits under the list as well'
# The panel says which copy of the add-on this is; run from the project, it is the project's, so nothing is out of date.
assert sl.core.running_version() == sl.core.repo_version() == tuple(sl.bl_info['version']) and sl.core.version_note() == ''
assert any(e[1] == 'label' and str(e[2]).startswith('SS Live Link v' + '.'.join(map(str, sl.bl_info['version']))) for e in log), 'no version on the panel'
real_running = sl.core.running_version
sl.core.running_version = lambda: (0, 1, 0)
try:
    assert 'Install Blender Add-on.cmd' in sl.core.version_note(), sl.core.version_note()
finally:
    sl.core.running_version = real_running
print('SELFTEST panel draws', titles, 'and feature boxes', feature_boxes)


# ---------------------------------------------------------------- push, pull and live against a stand-in editor
class FakeEditor:
    """Answers apply_link and pull_selection the way ss_prefabs does in the editor, with no socket opened."""
    connected = True

    def __init__(self):
        self.actors = {}

    def connect(self, timeout=0.0):
        return {'project_name': 'Fake', 'machine': 'here'}

    def disconnect(self):
        pass

    def call(self, expr):
        if expr == 'ss_prefabs.pull_selection()':
            return {'objects': list(self.actors.values())}
        head = 'ss_prefabs.apply_link('
        assert expr.startswith(head) and expr.endswith(')'), expr
        payload = json.loads(ast.literal_eval(expr[len(head):-1]))
        s = {'created': 0, 'moved': 0, 'removed': 0}
        for row in payload['objects']:
            s['moved' if row['link'] in self.actors else 'created'] += 1
            self.actors[row['link']] = row
        for gone in payload['remove']:
            s['removed'] += 1 if self.actors.pop(gone, None) else 0
        return s


fake, real_link = FakeEditor(), sl.editor_link.link
sl.editor_link.link = fake
try:
    s = sl.push(meshes)
    assert s['created'] == len(meshes) and len(fake.actors) == len(meshes), s
    meshes[0].matrix_world = Matrix.Translation(Vector((-4.0, 2.0, 1.0)))
    # Live: one part moved, so one row goes; then one part deleted, so its actor goes.
    st.live = True
    assert sl.live_tick() == 0.5 and st.status.startswith('live: +0 ~1 -0'), st.status
    assert abs(fake.actors[meshes[0][sl.PROP_LINK]]['matrix'][3][1] + 200.0) < 1e-3   # Blender +2 m in Y is Unreal -200 cm
    dropped = meshes.pop()
    dropped_link = dropped[sl.PROP_LINK]
    bpy.data.objects.remove(dropped, do_unlink=True)
    assert sl.live_tick() == 0.5 and dropped_link not in fake.actors and st.status.startswith('live: +0 ~0 -1'), st.status
    st.live = False
    assert sl.live_tick() is None
    # Many parts gone at once: Live stops and asks before it removes that many actors; pressing Live again is the yes.
    real_cap, sl.editor_link.LIVE_REMOVE_CAP = sl.editor_link.LIVE_REMOVE_CAP, 0
    try:
        second = meshes.pop()
        second_link = second[sl.PROP_LINK]
        bpy.data.objects.remove(second, do_unlink=True)
        st.live = True
        assert sl.live_tick() is None and st.live is False and second_link in fake.actors, st.status
        assert st.status.startswith('live stopped: 1 pushed parts are no longer in this file') and 'Press Live again' in st.status, st.status
        st.live = True
        assert sl.live_tick() == 0.5 and second_link not in fake.actors and st.status.startswith('live: +0 ~0 -1'), st.status
        st.live = False
    finally:
        sl.editor_link.LIVE_REMOVE_CAP = real_cap
    # Pull: the known actors move their proxies, an actor Blender has not seen arrives as a new proxy with its link.
    stranger = dict(fake.actors[meshes[0][sl.PROP_LINK]], link='f' * 32, name='Stranger', matrix=sl.to_ue_rows(Matrix.Translation(Vector((7.0, 7.0, 0.0)))))
    fake.actors[stranger['link']] = stranger
    s = sl.pull()
    assert s == {'created': 1, 'moved': len(meshes)}, s
    arrived = next(o for o in sl.linked_objects() if o[sl.PROP_LINK] == stranger['link'])
    assert (arrived.matrix_world.translation - Vector((7.0, 7.0, 0.0))).length < 1e-5
    assert bpy.ops.ss_link.pull() == {'FINISHED'} and st.status == f'pulled: +0 ~{len(meshes) + 1}', st.status
    assert bpy.ops.ss_link.push(selected_only=False) == {'FINISHED'} and st.status.startswith(f'pushed {len(meshes) + 1}: +0 ~'), st.status
    assert bpy.ops.ss_link.connect() == {'FINISHED'} and st.status == 'connected: Fake on here', st.status
    bpy.data.objects.remove(arrived, do_unlink=True)
    # File > Open, New and Revert. What was pushed is this session's memory of THIS file. Carried into another
    # .blend, every remembered link is missing there, and the first Live tick removed the first file's actors from
    # the open level. The handler forgets it (and Live, whose timer a file load drops): nothing is removed.
    assert len(sl.editor_link._last_sent) >= len(meshes) and sl.editor_link._last_sent is sl.core.pushed_links
    assert [h for h in bpy.app.handlers.load_post if getattr(h, '__name__', '') == 'file_loaded'] == [sl.editor_link.file_loaded]
    before_load = dict(fake.actors)
    held = [(o, o[sl.PROP_LINK]) for o in meshes]
    st.live = True
    sl.editor_link.file_loaded()
    assert not sl.core.pushed_links and st.live is False, 'a file load must forget what was pushed and switch Live off'
    for o, _ in held:          # as in the other file: none of the first file's links exist
        del o[sl.PROP_LINK]
        del o[sl.PROP_ASSET]
    st.live = True
    assert sl.live_tick() == 0.5 and set(fake.actors) == set(before_load), ('Live in another file removed the first file\'s actors', st.status)
    st.live = False
    for o, link_id in held:
        o[sl.PROP_LINK] = link_id
        o[sl.PROP_ASSET] = before_load[link_id]['asset']
finally:
    sl.editor_link.link = real_link
    sl.editor_link._last_sent.clear()
print('SELFTEST push, pull and live ok against a stand-in editor')

# ---------------------------------------------------------------- live, only with an editor open
live = None
if LIVE:
    node = sl.link.connect()
    s = sl.push(meshes)
    assert s['created'] == len(meshes), s
    meshes[0].matrix_world = Matrix.Translation(Vector((-4.0, 2.0, 1.0)))
    s2 = sl.push(meshes[:1])
    assert s2['moved'] == 1, s2
    pulled = sl.link.call('ss_prefabs.pull_selection()')
    s3 = sl.push([], remove=[o[sl.PROP_LINK] for o in meshes])
    assert s3['removed'] == len(meshes), s3
    live = {'node': node.get('project_name'), 'created': s['created'], 'moved': s2['moved'], 'removed': s3['removed'],
            'pulled': len(pulled.get('objects', []))}
    sl.link.disconnect()

# ================================================================ [send] Send to Unreal and Edit Mesh (send.py)
# Everything here writes to a scratch Outbox and a scratch side catalogue, so a crash half way leaves nothing
# an editor would import. In a function, so its names stay out of the other sections' way.
def send_selftest():
    import bmesh
    import struct
    snd = sl.send
    real = (snd.OUTBOX, sl.core.SENT, sl.editor_link.link)
    snd.OUTBOX, sl.core.SENT = Path('Artifacts/LiveLink/_SelfTestOutbox'), '_selftest_sent.json'
    scratch, sent_file = ROOT / snd.OUTBOX, sl.library_dir() / sl.core.SENT
    shutil.rmtree(scratch, ignore_errors=True)
    sent_file.unlink(missing_ok=True)
    made, calls, free = [], [], None

    class NoEditor:
        connected = False

        def call(self, expr):
            calls.append(expr)
            raise RuntimeError('no editor answered: is it open, with Python remote execution enabled?')

    class FakeEditor:
        """Answers the two ss_send calls; its export for Edit Mesh is a GLB this test sent a moment before."""
        connected = True

        def __init__(self, glb):
            self.glb = glb

        def call(self, expr):
            calls.append(expr)
            if expr == snd.REMOTE + 'import_outbox()':
                return {'imported': sorted(p.stem for p in scratch.rglob('*.glb')), 'kept': [], 'failed': []}
            head = snd.REMOTE + 'export_for_edit('
            assert expr.startswith(head) and expr.endswith(')'), expr
            return {'glb': str(self.glb), 'asset': ast.literal_eval(expr[len(head):-1])}

    def run(op):
        """An operator that reports an error raises when called from Python; here that is an answer, not a failure."""
        try:
            return op()
        except RuntimeError as e:
            return {'CANCELLED', str(e)}

    def select(*objects):
        sl.core.deselect_all(bpy.context)
        for o in objects:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]

    def local_bounds(obj):
        """The evaluated (modifiers applied) local bounds as Unreal would state them: centimetres, Y flipped."""
        bpy.context.view_layer.update()
        ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        me = ev.to_mesh()
        lo = [min(v.co[i] for v in me.vertices) for i in range(3)]
        hi = [max(v.co[i] for v in me.vertices) for i in range(3)]
        ev.to_mesh_clear()
        return [(lo[0] + hi[0]) * 50, -(lo[1] + hi[1]) * 50, (lo[2] + hi[2]) * 50], [(hi[i] - lo[i]) * 50 for i in range(3)]

    def close(a, b, tol=0.02):
        return all(abs(x - y) < tol for x, y in zip(a, b))

    def glb_materials(path):
        """The material names a GLB itself carries: what the editor will read, whatever Blender calls them meanwhile."""
        raw = path.read_bytes()
        return [m.get('name') for m in json.loads(raw[20:20 + struct.unpack('<I', raw[12:16])[0]]).get('materials', [])]

    def outbox_state():
        """Every file in the scratch Outbox with its time and size, and the side catalogue: a refused send changes none of it."""
        return ({str(p.relative_to(scratch)): (p.stat().st_mtime_ns, p.stat().st_size) for p in scratch.rglob('*') if p.is_file()},
                sent_file.read_text(encoding='utf-8') if sent_file.exists() else None)

    def box(name, lo, hi, materials=()):
        me = bpy.data.meshes.new(name)
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co = Vector([lo[i] + (v.co[i] + 0.5) * (hi[i] - lo[i]) for i in range(3)])
        for k, f in enumerate(bm.faces):
            f.material_index = k % max(1, len(materials))
        bm.to_mesh(me)
        bm.free()
        for m in materials:
            me.materials.append(m)
        obj = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(obj)
        made.append(obj)
        return obj

    try:
        assert hasattr(bpy.types, 'SS_LINK_OT_send_mesh') and hasattr(bpy.types, 'SS_LINK_OT_edit_mesh') and hasattr(sc, 'ss_send')
        log = []
        assert 'Send to Unreal' in sl.panel.draw_features(Recorder(log), bpy.context), log
        assert {'ss_link.send_mesh', 'ss_link.edit_mesh'} <= {e[2] for e in log if e[1] == 'operator'}, log
        assert snd.safe_name('  Pipes & Cables / v2!') == 'Pipes_Cables_v2' and snd.group_of('Lights') == 'Decoration' and snd.group_of('?') == 'Misc'

        # A mesh of the owner's own: two materials, an Array modifier (so 'modifiers applied' shows in the bounds),
        # off-centre in Y (so a mirror shows), and a world transform that must not reach the file.
        mats = [bpy.data.materials.new('SelfTest_Hull'), bpy.data.materials.new('SelfTest_Trim')]
        mats[0].diffuse_color, mats[1].diffuse_color = (0.8, 0.1, 0.1, 1.0), (0.1, 0.1, 0.8, 1.0)
        crate = box('SelfTest Crate!', (0.2, 0.5, 0.0), (1.2, 0.9, 0.3), mats)
        array = crate.modifiers.new('Array', 'ARRAY')
        array.count, array.relative_offset_displace = 2, (1.0, 0.0, 0.0)
        crate.matrix_world = Matrix.Translation(Vector((5.0, -3.0, 2.0))) @ Matrix.Rotation(math.radians(40), 4, 'Z') @ Matrix.Diagonal((1.5, 1.5, 1.5, 1.0))
        world = crate.matrix_world.copy()
        origin, extent = local_bounds(crate)
        assert close(origin, [120.0, -70.0, 15.0]) and close(extent, [100.0, 20.0, 15.0]), (origin, extent)

        # ---- sent with no editor to answer: queued
        sl.editor_link.link = NoEditor()
        select(crate)
        sc.ss_send.category, sc.ss_send.name, sc.ss_send.one_asset = 'Props', 'SelfTest Crate!', False
        assert bpy.ops.ss_link.send_mesh() == {'FINISHED'}, sc.ss_send.status
        assert 'queued' in sc.ss_send.status and calls == [snd.REMOTE + 'import_outbox()'], (sc.ss_send.status, calls)
        glb, side_path = scratch / 'Props' / 'SelfTest_Crate.glb', scratch / 'Props' / 'SelfTest_Crate.json'
        assert glb.exists() and glb.stat().st_size > 500 and side_path.exists(), list(scratch.rglob('*'))
        side = json.loads(side_path.read_text(encoding='utf-8'))
        # Outside /Game/SpaceSurvival, which is always cooked: an experiment sent once would ship to testers for good.
        assert snd.BLENDER_BASE == '/Game/Blender' and not snd.BLENDER_BASE.startswith('/Game/SpaceSurvival')
        target = '/Game/Blender/Props/SM_SelfTest_Crate'
        assert side['target'] == target and side['category'] == 'Props' and side['edit'] is False, side
        assert (ROOT / side['glb']) == glb and side['materials'] == ['SelfTest_Hull', 'SelfTest_Trim'] and side['triangles'] == 24, side
        assert close(side['bounds_cm']['origin'], origin) and close(side['bounds_cm']['extent'], extent), (side['bounds_cm'], origin, extent)
        asset = target + '.SM_SelfTest_Crate'
        assert crate[sl.PROP_ASSET] == asset and crate.get(sl.PROP_LINK) and crate in sl.linked_objects(), dict(crate.items())
        assert crate[snd.PROP_SENT] == asset and snd.sendable(crate), 'the object an asset was sent from is marked: only it sends there again'
        assert sc.ss_send.name == '', 'a name left in the field would send the next mesh over this one'
        assert crate.modifiers.get('Array') and crate.matrix_world == world and len(crate.data.vertices) == 8, 'the object itself must be left as it was'
        assert crate.select_get() and bpy.context.view_layer.objects.active == crate, 'the selection must come back'
        assert not [o for o in bpy.data.objects if o.name.startswith('SM_SelfTest')], 'the temporary copy must go'
        rows = json.loads(sent_file.read_text(encoding='utf-8'))
        assert len(rows) == 1 and rows[0]['asset'] == asset and rows[0]['group'] == 'Decoration' and rows[0]['pack'] == 'Blender', rows
        assert rows[0]['proxy'].startswith('../LiveLink/') and (sl.library_dir() / rows[0]['proxy']).resolve() == glb.resolve(), rows[0]['proxy']

        # ---- a mesh that has just become an asset is a part: in the list at once, under its type and category, and
        # still there after Load Catalogue (which used to fill the list from the catalogue alone, so a sent mesh could
        # never be found by type or picture until the editor rebuilt the catalogue)
        listed_now = [it for it in sc.ss_link.parts if it.asset == asset]
        assert len(listed_now) == 1 and listed_now[0].category == 'Props' and listed_now[0].group == 'Decoration', [it.asset for it in listed_now]
        assert sc.ss_link.parts[sc.ss_link.part_index].asset == asset, 'the mesh just sent is the highlighted part'
        assert bpy.ops.ss_link.load_catalog() == {'FINISHED'}
        assert [it.asset for it in sc.ss_link.parts].count(asset) == 1 and len(sc.ss_link.parts) == len(cat['meshes']) + 1
        assert '1 sent from here' in sc.ss_link.status, sc.ss_link.status
        sl.load_catalog(force=True)
        assert sl.catalog_entry(asset) is not None, 'a new session knows a sent mesh from sent.json alone: no grey box for it'

        # ---- sent again after a change: the same asset, the same two files, the one row
        crate.data.transform(Matrix.Diagonal((1.0, 1.0, 2.0, 1.0)))
        origin, extent = local_bounds(crate)
        assert bpy.ops.ss_link.send_mesh() == {'FINISHED'}, sc.ss_send.status
        assert sorted(p.name for p in scratch.rglob('*') if p.is_file()) == ['SelfTest_Crate.glb', 'SelfTest_Crate.json'], list(scratch.rglob('*'))
        side = json.loads(side_path.read_text(encoding='utf-8'))
        assert side['target'] == target and close(side['bounds_cm']['extent'], [100.0, 20.0, 30.0]) and close(side['bounds_cm']['origin'], origin), side
        rows = json.loads(sent_file.read_text(encoding='utf-8'))
        assert len(rows) == 1 and close(rows[0]['extent'], extent) and crate[sl.PROP_ASSET] == asset, rows

        # ---- the side catalogue: merged after the real rows, and add_part builds the sent shape from it
        catalog = sl.load_catalog(force=True)
        merged = snd.merged_rows(catalog)
        assert len(merged) == len(catalog['meshes']) + 1 and merged[-1]['asset'] == asset and len(catalog['meshes']) == len(cat['meshes'])
        both = snd.merged_catalog(catalog)
        assert both['categories'].get('Props', 0) == catalog['categories'].get('Props', 0) + 1 and len(both['meshes']) == len(merged)
        assert sl.catalog_entry(asset) == rows[0]
        for route in ('the stand-in kept from the send', 'the GLB named by sent.json'):
            part = sl.add_part(asset)
            made.append(part)
            o2, e2 = local_bounds(part)
            assert close(o2, origin) and close(e2, extent), (route, o2, e2, origin, extent)
            assert [m.name.split('.')[0] for m in part.data.materials] == ['SelfTest_Hull', 'SelfTest_Trim'], (route, list(part.data.materials))
            assert part[sl.PROP_ASSET] == asset and part.data.name == 'SSProxy:' + asset and not snd.sendable(part), (route, 'a placed copy is a proxy')
            if route.startswith('the stand-in'):
                bpy.data.objects.remove(made.pop(), do_unlink=True)
                bpy.data.meshes.remove(bpy.data.meshes['SSProxy:' + asset])   # so the second pass has to read the file

        # ---- a placed proxy of the owner's OWN asset is tagged exactly like the original, and is no more sent than a pack's
        still = outbox_state()
        twin = sl.add_part(asset)
        made.append(twin)
        for picked in ((part,), (part, twin)):   # two placed copies used to be told 'rename one', which cannot help
            select(*picked)
            assert 'CANCELLED' in run(bpy.ops.ss_link.send_mesh) and 'proxy is not sent back' in sc.ss_send.status, sc.ss_send.status
        # Made single-user, even renamed, a copy still is not the object the asset was sent from: the tag alone proves nothing.
        loose = part.copy()
        loose.data = part.data.copy()
        bpy.context.scene.collection.objects.link(loose)
        made.append(loose)
        assert loose.data.name.startswith('SSProxy:') and not snd.sendable(loose), loose.data.name
        loose.data.name = 'SelfTest Loose'
        assert loose[sl.PROP_ASSET] == asset and not loose.get(snd.PROP_SENT) and not snd.sendable(loose)
        select(loose)
        assert 'CANCELLED' in run(bpy.ops.ss_link.send_mesh) and outbox_state() == still, (sc.ss_send.status, 'a refused send must write nothing')
        # The original among its proxies: it alone goes, the proxies are counted, and they show what was sent.
        select(crate, part, twin)
        assert bpy.ops.ss_link.send_mesh() == {'FINISHED'} and '(2 library proxies left alone)' in sc.ss_send.status, sc.ss_send.status
        assert outbox_state() != still and json.loads(side_path.read_text(encoding='utf-8'))['source_objects'] == [crate.name]
        assert part.data is twin.data and part.data.name == 'SSProxy:' + asset and crate.data.name != part.data.name
        # A duplicate of the original is the owner's work, but both cannot be the one asset, and renaming would change nothing.
        dup = crate.copy()
        dup.data = crate.data.copy()
        bpy.context.scene.collection.objects.link(dup)
        made.append(dup)
        select(crate, dup)
        assert snd.sendable(dup) and 'CANCELLED' in run(bpy.ops.ss_link.send_mesh) and 'send one of them alone' in sc.ss_send.status, sc.ss_send.status
        bpy.data.objects.remove(made.pop(), do_unlink=True)

        # ---- a library proxy is never sent back over its asset
        assert bpy.ops.ss_link.load_catalog() == {'FINISHED'}
        cached = next((m['asset'] for m in catalog['meshes'] if 'SSProxy:' + m['asset'] in bpy.data.meshes), catalog['meshes'][0]['asset'])
        proxy = sl.add_part(cached)
        made.append(proxy)
        select(proxy)
        assert 'CANCELLED' in run(bpy.ops.ss_link.send_mesh) and sc.ss_send.status.startswith('not sent'), sc.ss_send.status
        assert len(list(scratch.rglob('*.glb'))) == 1

        # ---- One asset: the selection joined, the active object its pivot and the one that carries the tag
        a = box('SelfTest A', (-0.5, -0.5, 0.0), (0.5, 0.5, 1.0), mats[:1])
        b = box('SelfTest B', (-0.25, -0.25, 0.0), (0.25, 0.25, 0.5), mats[1:])
        a.matrix_world = Matrix.Translation(Vector((10.0, 0.0, 0.0))) @ Matrix.Rotation(math.radians(90), 4, 'Z')
        b.matrix_world = Matrix.Translation(Vector((10.0, 2.0, 0.0)))   # 2 m along world +Y is 2 m along a's local +X
        select(a, b)
        sc.ss_send.name, sc.ss_send.one_asset = 'SM_SelfTest Pair', True
        assert bpy.ops.ss_link.send_mesh() == {'FINISHED'}, sc.ss_send.status
        pair = json.loads((scratch / 'Props' / 'SelfTest_Pair.json').read_text(encoding='utf-8'))
        assert pair['target'].endswith('/Props/SM_SelfTest_Pair') and pair['source_objects'] == ['SelfTest A', 'SelfTest B'], pair
        assert close(pair['bounds_cm']['origin'], [87.5, 0.0, 50.0]) and close(pair['bounds_cm']['extent'], [137.5, 50.0, 50.0]), pair['bounds_cm']
        assert a.get(sl.PROP_ASSET) == pair['target'] + '.SM_SelfTest_Pair' and not b.get(sl.PROP_ASSET)
        assert {o.name for o in (a, b)} <= {o.name for o in bpy.data.objects} and len(a.data.vertices) == 8, 'the sources stay as they were'
        sc.ss_send.one_asset = False

        # ---- Edit Mesh: needs the editor, brings one flagged object to the cursor, and sends back over the asset
        # A mesh of the owner's own is selected (a): there is nothing to fetch for it, and the panel says what to do instead.
        assert a.select_get() and bpy.context.view_layer.objects.active == a
        assert 'CANCELLED' in run(bpy.ops.ss_link.edit_mesh) and 'mesh of your own' in sc.ss_send.status and not calls[-1].startswith(snd.REMOTE + 'export'), sc.ss_send.status
        sl.core.deselect_all(bpy.context)
        assert 'CANCELLED' in run(bpy.ops.ss_link.edit_mesh) and sc.ss_send.status.startswith('Edit Mesh needs the open editor'), sc.ss_send.status
        sl.editor_link.link = FakeEditor(glb)
        # The thing clicked on is the thing fetched, whatever row the list happens to highlight: 'this looks wrong, let
        # me fix it' is a click on the part and then the button.
        clicked = next(m['asset'] for m in catalog['meshes'] if m['asset'] != cached)
        sc.ss_link.part_index = next(i for i, it in enumerate(sc.ss_link.parts) if it.asset == clicked)
        select(proxy)
        assert bpy.ops.ss_link.edit_mesh() == {'FINISHED'}, sc.ss_send.status
        assert calls[-1] == snd.REMOTE + 'export_for_edit(' + repr(cached) + ')' and 'the selected part' in sc.ss_send.status, (calls[-1], sc.ss_send.status)
        by_click = bpy.context.view_layer.objects.active
        assert by_click[sl.PROP_ASSET] == cached and snd.is_edit_copy(by_click) and 'Shape only' in sc.ss_send.note, sc.ss_send.note
        # An Edit Mesh copy is the mesh on the bench, not a placement of it: Push All and Live leave it alone.
        assert by_click not in sl.core.tagged_objects() and by_click not in sl.linked_objects() and proxy in sl.linked_objects()
        assert 'CANCELLED' in run(bpy.ops.ss_link.edit_mesh) and 'already the mesh to fix' in sc.ss_send.status, sc.ss_send.status
        bpy.data.objects.remove(by_click, do_unlink=True)
        sl.core.deselect_all(bpy.context)
        # Edit a part nothing in this scene stands for: the send replaces the cached stand-in of what it edits.
        free = next(m['asset'] for m in catalog['meshes'] if 'SSProxy:' + m['asset'] not in bpy.data.meshes)
        sc.ss_link.part_index = next(i for i, it in enumerate(sc.ss_link.parts) if it.asset == free)
        sc.cursor.location = (2.0, 3.0, 1.0)
        assert bpy.ops.ss_link.edit_mesh() == {'FINISHED'}, sc.ss_send.status
        assert 'the parts list' in sc.ss_send.status, sc.ss_send.status
        fix = bpy.context.view_layer.objects.active
        made.append(fix)
        assert fix[sl.PROP_ASSET] == free and fix[snd.PROP_EDIT] and [c.name for c in fix.users_collection] == [snd.EDIT_COLLECTION]
        assert snd.is_edit_copy(fix) and fix[snd.PROP_EDIT_AS] == fix.name

        # ---- a copy of the Edit Mesh object is NOT the edit. Shift+D and Separate copy ss_edit and ss_asset with
        # everything else, so a new part begun from a piece of a pack door used to be sent over the pack's door: licensed,
        # git-ignored, every placed instance changed, no way back. Renamed, with a Name typed, Replace unticked: all the same.
        still = outbox_state()
        piece = fix.copy()
        piece.data = fix.data.copy()
        bpy.context.scene.collection.objects.link(piece)
        made.append(piece)
        assert piece.get(snd.PROP_EDIT) and piece[sl.PROP_ASSET] == free and piece.name != fix.name, 'Blender copies the flags: that is the trap'
        assert not snd.is_edit_copy(piece) and snd.sendable(piece)
        for called, typed in ((piece.name, ''), ('MyNewPanel', ''), ('MyNewPanel', 'MyNewPanel')):
            piece.name = called
            where = snd.plan(piece, 'Props', typed)
            assert where['edit'] is False and where['target'].startswith(snd.BLENDER_BASE + '/Props/SM_') and where['folder'] == 'Props', (called, typed, where)
            assert not snd.owns(piece, where)
        assert snd.plan(fix, 'Props', 'AsANewAsset')['target'] == snd.BLENDER_BASE + '/Props/SM_AsANewAsset', 'a Name typed means a new asset, as its tooltip says'
        assert snd.plan(fix, 'Props')['target'] == free.split('.')[0] and snd.plan(fix, 'Props')['edit'] is True
        piece.name = 'MyNewPanel'
        select(piece)
        sc.ss_send.name, sc.ss_send.replace = 'SelfTest NewPanel', False
        assert snd.replaced_by(bpy.context, sc.ss_send) == [], 'nothing of the project is replaced by this send'
        assert bpy.ops.ss_link.send_mesh() == {'FINISHED'}, sc.ss_send.status
        panel_side = json.loads((scratch / 'Props' / 'SelfTest_NewPanel.json').read_text(encoding='utf-8'))
        assert panel_side['target'] == snd.BLENDER_BASE + '/Props/SM_SelfTest_NewPanel' and panel_side['edit'] is False, panel_side
        assert panel_side['source_objects'] == ['MyNewPanel'], panel_side
        assert not (scratch / snd.EDITS).exists(), 'a copy must never reach the _Edits folder, from where the editor replaces pack assets'
        assert not piece.get(snd.PROP_EDIT) and piece[sl.PROP_ASSET] == piece[snd.PROP_SENT] == panel_side['target'] + '.SM_SelfTest_NewPanel'
        assert outbox_state() != still and snd.is_edit_copy(fix) and fix[sl.PROP_ASSET] == free, 'the real edit copy is untouched by all this'
        (scratch / 'Props' / 'SelfTest_NewPanel.json').unlink()
        (scratch / 'Props' / 'SelfTest_NewPanel.glb').unlink()
        sl.core.write_sent([r for r in sl.core.read_sent() if 'NewPanel' not in r['asset']])
        # From the button, a send that does go over a project asset asks first and names it.
        select(fix)
        assert snd.replaced_by(bpy.context, sc.ss_send) == [free.split('.')[0]], snd.replaced_by(bpy.context, sc.ss_send)
        assert (fix.matrix_world.translation - Vector((2.0, 3.0, 1.0))).length < 1e-6 and fix.name == free.split('.')[-1], (fix.name, fix.matrix_world)
        o2, e2 = local_bounds(fix)
        assert close(o2, origin) and close(e2, extent), ('the edit copy must hold the asset in its own frame', o2, e2)
        # The crate's own materials are in this file, so Blender brought the copy's in as 'SelfTest_Hull.00N'. The editor
        # gives a slot its old material back by name: the file that returns has to say the names the asset knows.
        renamed = [m.name for m in fix.data.materials]
        real_names = ['SelfTest_Hull', 'SelfTest_Trim']
        assert [snd.COPY_SUFFIX.sub('', n) for n in renamed] == real_names and not set(renamed) & set(real_names), renamed
        assert [m.get(snd.PROP_SLOT) for m in fix.data.materials] == real_names, 'Edit Mesh must remember what the asset calls them'
        fix.data.materials.append(bpy.data.materials.new('SelfTest_Added'))   # and the fix adds a slot, so nothing falls back on position
        fix.data.polygons[0].material_index = 2
        fix.data.transform(Matrix.Diagonal((1.0, 1.0, 0.5, 1.0)))
        select(fix)
        assert bpy.ops.ss_link.send_mesh() == {'FINISHED'} and 'imported' in sc.ss_send.status, sc.ss_send.status
        assert 'its shape only' in sc.ss_send.note and 'can be deleted' in sc.ss_send.note, sc.ss_send.note
        assert snd.is_edit_copy(fix) and not fix.get(snd.PROP_SENT) and not fix.get(sl.PROP_LINK), 'an edit copy stays an edit copy, and is never a placed part'
        edits = [json.loads(p.read_text(encoding='utf-8')) for p in (scratch / snd.EDITS).glob('*.json')]
        assert len(edits) == 1 and edits[0]['target'] == free.split('.')[0] and edits[0]['edit'] is True, edits
        assert close(edits[0]['bounds_cm']['extent'], [100.0, 20.0, 15.0]) and fix[sl.PROP_ASSET] == free, edits
        sent_back = glb_materials(next((scratch / snd.EDITS).glob('*.glb')))
        assert sorted(sent_back) == sorted(real_names + ['SelfTest_Added']) and edits[0]['materials'] == real_names + ['SelfTest_Added'], (sent_back, edits[0])
        # ... and only the file: every name in Blender is as it was, the crate's own materials above all.
        assert [m.name for m in fix.data.materials] == renamed + ['SelfTest_Added'] and [m.name for m in mats] == real_names, [m.name for m in bpy.data.materials]
        assert list(crate.data.materials) == mats and not [m.name for m in bpy.data.materials if m.name.endswith('.aside')]
        assert [r['asset'] for r in snd.read_sent()] == [asset, pair['target'] + '.SM_SelfTest_Pair'], 'an asset the catalogue lists needs no sent row'

        # ---- a sent row leaves sent.json once the catalogue lists its asset
        after = snd.merged_rows({'meshes': [{'asset': asset}]})
        assert [r['asset'] for r in after] == [asset, pair['target'] + '.SM_SelfTest_Pair'] and [r['asset'] for r in snd.read_sent()] == [after[1]['asset']], after

        # ---- a new mesh never lands on an asset that exists because its name is taken ('Cube' is everyone's first name)
        # Known three ways: a sent row (the pair), the Outbox alone (the crate, whose row has just left), the catalogue.
        listed = '/Game/Blender/Props/SM_SelfTest_Listed'
        sl.load_catalog()['meshes'].append({'asset': listed + '.SM_SelfTest_Listed'})   # the forced reload at the end forgets it
        still = outbox_state()
        thieves = {}
        for why, called, typed in (('a sent row', 'SelfTest Pair', ''), ('a sent row, another case', 'SelfTest Other', 'selftest PAIR'),
                                   ('the Outbox alone', 'SelfTest_Crate', ''), ('the catalogue', 'SelfTest Listed', '')):
            thief = thieves[why] = box(called, (0.0, 0.0, 0.0), (5.0, 5.0, 5.0))
            assert thief.name == called and snd.sendable(thief)
            select(thief)
            sc.ss_send.name = typed
            assert 'CANCELLED' in run(bpy.ops.ss_link.send_mesh), (why, sc.ss_send.status)
            assert sc.ss_send.status.startswith('not sent: SM_') and 'already exists' in sc.ss_send.status, (why, sc.ss_send.status)
            assert not thief.get(sl.PROP_ASSET) and not thief.get(snd.PROP_SENT) and outbox_state() == still, (why, 'a refused send must change nothing')
        sc.ss_send.name = ''
        assert a.get(sl.PROP_ASSET) == pair['target'] + '.SM_SelfTest_Pair' and snd.owns(a, snd.plan(a, 'Props')), 'the object it came from still owns it'
        # Replace existing is the owner saying so: the send goes over the asset, once, and the tick does not stay on.
        props = []

        class Box:
            def __getattr__(self, call):
                if call.startswith('__'):
                    raise AttributeError(call)

                def method(*args, **kw):
                    props.append((call,) + tuple(args[1:2]))
                    return Box()
                return method

        snd.draw(Box(), bpy.context)
        assert ('prop', 'replace') in props, props
        thief = thieves['a sent row']
        select(thief)
        sc.ss_send.replace = True
        assert bpy.ops.ss_link.send_mesh() == {'FINISHED'} and sc.ss_send.replace is False, sc.ss_send.status
        took = json.loads((scratch / 'Props' / 'SelfTest_Pair.json').read_text(encoding='utf-8'))
        assert took['target'] == pair['target'] and took['source_objects'] == ['SelfTest Pair'] and close(took['bounds_cm']['extent'], [250.0, 250.0, 250.0]), took
        assert thief[sl.PROP_ASSET] == thief[snd.PROP_SENT] == pair['target'] + '.SM_SelfTest_Pair'
        assert bpy.ops.ss_link.send_mesh() == {'FINISHED'}, ('its own asset now: no tick needed', sc.ss_send.status)

        # ---- the editor's half of a fix coming back, against a stand-in 'unreal': a '.001' Blender added (the add-on
        # now sends the real names, a file made some other way may not) must not cost a pack asset its materials.
        class Mat:
            def __init__(self, name, path=None):
                self.name, self.path = name, path or f'/Game/SelfTest/{name}.{name}'

            def get_name(self):
                return self.name

            def get_path_name(self):
                return self.path

        class Mesh:
            def __init__(self, slots, wearing=None):
                self.static_materials = [types.SimpleNamespace(material_slot_name=n, material_interface=wearing) for n in slots]

            def set_material(self, i, mat):
                self.static_materials[i].material_interface = mat

        # What Interchange really leaves on a slot whose material it was told not to import (Scripts/TestSendScenes.py
        # met it in the editor): not nothing, the engine's grid. Such a slot is as empty as one holding None.
        grid = Mat('WorldGridMaterial', '/Engine/EngineMaterials/WorldGridMaterial.WorldGridMaterial')

        def restored(before, arriving):
            mesh = Mesh(arriving)
            empty = ue._restore_materials(mesh, before)
            gridded = Mesh(arriving, wearing=grid)
            assert ue._restore_materials(gridded, before) == empty, ('a slot left on the engine grid is an empty slot', arriving)
            assert [None if s.material_interface is grid else s.material_interface for s in gridded.static_materials] == \
                [s.material_interface for s in mesh.static_materials], ('the grid never stands in the way of a slot\'s own material', arriving)
            return [s.material_interface for s in mesh.static_materials], empty

        stub = types.ModuleType('unreal')
        stub.Paths = types.SimpleNamespace(project_dir=lambda: str(ROOT))
        stub.EditorAssetLibrary = None
        had = sys.modules.get('unreal')
        sys.modules['unreal'] = stub
        try:
            ue = sl.core.import_by_path('ss_send_selftest', ROOT / 'Content' / 'Python' / 'ss_send.py')
        finally:
            sys.modules.pop('unreal')
            if had is not None:
                sys.modules['unreal'] = had
        frame, glass, wall, wall_1 = Mat('MI_Frame'), Mat('MI_Glass'), Mat('M_Wall'), Mat('M_Wall_001')
        door = [('frame_slot', frame), ('lambert2', glass)]
        assert restored(door, ['MI_Frame', 'MI_Glass', 'SelfTest_Added']) == ([frame, glass, None], ['SelfTest_Added']), 'real names, a slot added'
        assert restored(door, ['MI_Glass.001', 'MI_Frame.001', 'NewInBlender']) == ([glass, frame, None], ['NewInBlender']), 'Blender\'s suffix, a slot added'
        assert restored(door, ['MI_Frame_001', 'MI_Glass_002', 'NewInBlender']) == ([frame, glass, None], ['NewInBlender']), 'the suffix as an asset name'
        assert restored(door, ['MI_Glass.001']) == ([glass], []), 'a slot removed: the count changes, the names still find their material'
        assert restored(door, ['frame_slot', 'lambert2']) == ([frame, glass], []) and restored(door, ['Material', 'Material.001']) == ([frame, glass], [])
        assert restored([('a', wall), ('b', wall_1)], ['M_Wall_001', 'M_Wall', 'M_Wall_001.001', 'New']) == ([wall_1, wall, wall_1, None], ['New']), \
            'an exact name wins: a pack\'s own M_Wall_001 is not a copy of M_Wall'
        return {'glb_bytes': glb.stat().st_size, 'bounds_cm': side['bounds_cm'], 'edited': free.split('.')[-1], 'calls': len(calls)}
    finally:
        snd.OUTBOX, sl.core.SENT, sl.editor_link.link = real
        shutil.rmtree(scratch, ignore_errors=True)
        sent_file.unlink(missing_ok=True)
        try:
            scratch.parent.rmdir()   # Artifacts/LiveLink, when this test is all that ever made it
        except OSError:
            pass
        for o in made:
            if o.name in bpy.data.objects:
                bpy.data.objects.remove(o, do_unlink=True)
        for me in [m for m in bpy.data.meshes if m.name.startswith('SSProxy:') and ('SelfTest' in m.name or m.name == f'SSProxy:{free}')]:
            if not any(o.data is me for o in bpy.data.objects):
                bpy.data.meshes.remove(me)
        sl.load_catalog(force=True)   # forget the sent rows this test taught the catalogue


send_result = send_selftest()
print('SELFTEST send ok:', json.dumps(send_result))
# ================================================================ [send] ends

# ================================================================ feature 'groups': the type filter (begin)
def selftest_groups():
    """Types over the categories: the counts, the narrowed category menu, one filter for list, grid and counts,
    a catalogue from before the types, the Types box, a filter put back by File > Open, undo and redo, and the
    gallery's side of it."""
    import tempfile

    global sc   # reopening a file, below, replaces the scene
    lib, ctx, st = sl.library, bpy.context, sc.ss_link
    total = len(cat['meshes'])
    assert hasattr(bpy.types, 'SS_LINK_OT_clear_filters'), 'groups.py did not register its operator'
    assert bpy.ops.ss_link.load_catalog() == {'FINISHED'}
    assert (st.group, st.category, st.pack, st.search) == ('All', 'All', 'All', ''), (st.group, st.category, st.pack, st.search)
    assert ' types, ' in st.status, st.status

    def group_of(m):
        return m.get('group') or lib.group_of(m['category'], cat.get('group_categories'))

    def expect(group='All', category='All', pack='All', words=()):
        """Counted from the catalogue file and never from the add-on's state: what the panel has to agree with."""
        return sum(1 for m in cat['meshes'] if group in ('All', group_of(m)) and category in ('All', m['category'])
                   and pack in ('All', m['pack']) and all(w in m['name'].lower() for w in words))

    def listed(name=''):
        """Rows the parts list would show, asked of the list's own filter with its own name field set to 'name'."""
        ui = types.SimpleNamespace(filter_name=name, bitflag_filter_item=1 << 30)
        flags, _ = lib.SSLINK_UL_parts.filter_items(ui, ctx, st, 'parts')
        return sum(1 for f in flags if f)

    def agree(n, why):
        shown = [it for it in st.parts if lib.part_visible(it, *lib.current_filter(st))]
        pictures = [i for i in lib.pick_items(st, ctx) if i[0]]
        assert len(shown) == n, (why, 'filter', len(shown), n)
        assert listed() == n, (why, 'list', listed(), n)
        assert len(pictures) == min(n, lib.PICK_CAP), (why, 'picture grid', len(pictures), n)
        assert {st.parts[i[4]].asset for i in pictures} <= {it.asset for it in shown}, (why, 'the grid shows a part the filter hides')
        assert lib.shown_label(st) == f'{n} of {total} parts', (why, lib.shown_label(st))
        if n:
            active = st.parts[st.part_index].asset
            assert active in {it.asset for it in shown} and st.part_pick == active, (why, 'the active part is out of view')

    def labels(items):
        return {i[0]: i[1] for i in items}

    # ---- the types are there, every part has one, and their counts add up to the catalogue
    items = lib.group_items(st, ctx)
    idents = [i[0] for i in items]
    known = [g for g, _ in lib.GROUPS]
    assert idents[0] == 'All' and idents[-1] == lib.MISC and [g for g in idents if g in known] == known, idents
    assert len({i[3] for i in items}) == len(items) and items[0][3] == 0, 'every type needs a number of its own, All the default 0'
    assert all(it.group for it in st.parts)
    counts = {g: lib.type_count(g) for g in idents[1:]}
    assert sum(counts.values()) == total == len(st.parts), (counts, total)
    for g, n in counts.items():
        assert n == expect(group=g) and labels(items)[g] == f'{g} ({n})', (g, n, expect(group=g), labels(items)[g])
    assert labels(items)['All'] == f'All ({total})'
    if 'groups' in cat:
        assert {g: n for g, n in counts.items() if n} == cat['groups'], (counts, cat['groups'])
    agree(total, 'nothing filtered')
    all_categories = [i[0] for i in lib.category_items(st, ctx)]
    assert all_categories == ['All'] + sorted(c for c, n in cat['categories'].items() if n), all_categories

    # ---- choosing Building leaves only its categories, and exactly its parts
    assert counts.get('Building'), 'the catalogue has no Building parts to test with'
    st.group = 'Building'
    building = sorted({m['category'] for m in cat['meshes'] if group_of(m) == 'Building'})
    menu = lib.category_items(st, ctx)
    assert [i[0] for i in menu] == ['All'] + building, [i[0] for i in menu]
    assert set(building) <= set(cat.get('group_categories', dict(lib.GROUPS))['Building']), building
    assert labels(menu)['All'] == f'All ({counts["Building"]})', labels(menu)['All']
    for c in building:
        assert labels(menu)[c] == f'{c} ({expect(group="Building", category=c)})', labels(menu)[c]
    agree(counts['Building'], 'Building')
    assert all(it.group == 'Building' for it in st.parts if lib.part_visible(it, *lib.current_filter(st)))
    assert {g: lib.type_count(g) for g in counts} == counts, 'choosing a type must not zero the other types\' counts'

    # ---- a category of the chosen type stays; one of another type goes back to All, quietly
    st.category = building[0]
    st.group = 'Building'
    assert st.category == building[0]
    agree(expect(group='Building', category=building[0]), 'Building and a category')
    other = next(g for g in idents[1:] if g != 'Building' and counts[g])
    st.group = other
    assert st.category == 'All' and st.group == other, (st.category, st.group)
    agree(counts[other], other)
    st.group = 'All'
    foreign = next(c for c in all_categories[1:] if c not in building)
    st.category = foreign
    st.group = 'Building'
    assert st.category == 'All', 'a category from another type survived the type change'
    agree(counts['Building'], 'Building after a foreign category')

    # ---- type AND category AND pack AND name, in the list, the grid and every count
    per_pack = {}
    for m in cat['meshes']:
        if group_of(m) == 'Building':
            per_pack[m['pack']] = per_pack.get(m['pack'], 0) + 1
    pack = max(per_pack, key=per_pack.get)
    st.pack = pack
    agree(per_pack[pack], 'Building in one pack')
    word = next((w for w in ('wall', 'floor', 'door', 'a') if 0 < expect('Building', 'All', pack, (w,)) < per_pack[pack]), 'a')
    st.search = word.upper() + '  '   # case and stray spaces must not matter
    words = (word,)
    agree(expect('Building', 'All', pack, words), 'Building, a pack and a name')
    assert listed('e') == sum(1 for m in cat['meshes'] if group_of(m) == 'Building' and m['pack'] == pack and word in m['name'].lower()
                              and 'e' in m['name'].lower()), 'the list\'s own name field must narrow further, not instead'
    for g in counts:
        assert lib.type_count(g) == expect(g, 'All', pack, words), (g, lib.type_count(g))
    assert labels(lib.group_items(st, ctx))['All'] == f'All ({expect("All", "All", pack, words)})'
    for ident, label in labels(lib.category_items(st, ctx)).items():
        assert label == f'{ident} ({expect("Building", ident, pack, words)})', label
    for ident, label in labels(lib.pack_items(st, ctx)).items():
        assert ident == 'All' or label == f'{ident} ({expect("Building", "All", ident, words)})', label

    # ---- the Types box: a toggle per type, greyed when it would show nothing, the name field, the way back
    calls = []

    class Layout:
        def __getattr__(self, name):
            if name.startswith('__'):
                raise AttributeError(name)

            def call(*args, **kw):
                calls.append((name, args, kw))
                return Layout()
            return call

        def __setattr__(self, key, value):
            calls.append(('set ' + key, (value,), {}))

    sl.groups.draw(Layout(), ctx)
    toggles = [args[2] for name, args, _ in calls if name == 'prop_enum' and args[0] == st and args[1] == 'group']
    enabled = [args[0] for name, args, _ in calls if name == 'set enabled']
    assert toggles == idents and len(enabled) == len(idents) + 1, (toggles, enabled)   # a cell per type, then Show All
    assert enabled[-1] is True, 'with a filter on, Show All must be live'
    for g, on in zip(idents, enabled):
        assert on == (g in ('All', 'Building') or expect(g, 'All', pack, words) > 0), (g, on)
    assert any(name == 'prop' and args[1] == 'search' for name, args, _ in calls)
    assert any(name == 'operator' and args[0] == 'ss_link.clear_filters' for name, args, _ in calls)
    assert any(name == 'label' and kw.get('text') == lib.shown_label(st) for name, _, kw in calls)
    assert 'Types' not in feature_boxes, 'the type filter is drawn inside the Parts library box, not as a box of its own'

    # ---- a card clicked in the visual browser copies its asset path; pasted into the name field it finds the part
    st.group, st.pack, st.search = 'All', 'All', ''
    some_part = cat['meshes'][len(cat['meshes']) // 2]
    st.search = some_part['asset']
    agree(1, 'a pasted asset path')
    assert st.parts[st.part_index].asset == some_part['asset']
    st.search = some_part['asset'].rsplit('/', 1)[0] + '/'
    agree(sum(1 for m in cat['meshes'] if (some_part['asset'].rsplit('/', 1)[0] + '/').lower() in m['asset'].lower()), 'a pasted folder path')
    st.search = ''
    # The picture grid stops at its cap, and says so: parts are sorted by category, so a cut grid loses Walls and Wreckage.
    assert lib.PICK_CAP >= total and lib.grid_note(st) == '', (lib.PICK_CAP, total, lib.grid_note(st))
    real_cap, lib.PICK_CAP = lib.PICK_CAP, 25
    try:
        lib.refresh_pick_items(st)
        assert len([i for i in lib.pick_items(st, ctx) if i[0]]) == 25 and 'the first 25 of ' + str(total) in lib.grid_note(st), lib.grid_note(st)
    finally:
        lib.PICK_CAP = real_cap
        lib.refresh_pick_items(st)
    # What the game's code loads by name is marked, and comes first in its category: of three look-alike hazard meshes
    # it is the one a fix shows up in.
    marked = [it for it in st.parts if it.in_game]
    assert all(sl.core.loaded_by_game(it.asset) for it in marked) and not any(sl.core.loaded_by_game(it.asset) for it in st.parts if not it.in_game)
    if (ROOT / 'Source').is_dir() and marked:
        for category in {it.category for it in marked}:
            flags = [it.in_game for it in st.parts if it.category == category]
            assert flags == sorted(flags, reverse=True), (category, 'what the game loads comes first')

    # ---- nothing matching is a state, not an error; one button undoes every filter
    st.group, st.pack = 'Building', pack
    st.search = 'no part is called this'
    agree(0, 'a name nothing has')
    assert [i[0] for i in lib.pick_items(st, ctx)] == [''], lib.pick_items(st, ctx)
    st.group = other
    agree(0, 'another type, still nothing')
    assert bpy.ops.ss_link.clear_filters() == {'FINISHED'}
    assert (st.group, st.category, st.pack, st.search) == ('All', 'All', 'All', '')
    agree(total, 'after Show Everything')
    calls.clear()
    sl.groups.draw(Layout(), ctx)
    assert [args[0] for name, args, _ in calls if name == 'set enabled'] == [True] * len(idents) + [False], 'nothing filtered: every type live, Show All idle'

    # ---- a catalogue from before the types: the fallback map gives every part the type the editor would have
    typed = {it.asset: it.group for it in st.parts}
    old = json.loads(json.dumps(cat))
    old.pop('groups', None)
    old.pop('group_categories', None)
    for m in old['meshes']:
        m.pop('group', None)
    real_load = sl.core.load_catalog
    sl.core.load_catalog = lambda force=False: old
    try:
        assert bpy.ops.ss_link.load_catalog() == {'FINISHED'}
        assert {it.asset: it.group for it in st.parts} == typed, 'the fallback map disagrees with the catalogue\'s types'
        assert {g: lib.type_count(g) for g in counts} == counts
        it = st.parts[0]
        kept, it.group = it.group, ''   # and a part kept in a .blend from before the types has none at all
        assert lib.part_group(it) == kept
        it.group = kept
    finally:
        sl.core.load_catalog = real_load
    assert lib.group_of('Walls') == 'Building' and lib.group_of('Lights') == 'Decoration' and lib.group_of('Ship Parts') == 'Ships'
    assert lib.group_of('Something new') == lib.MISC and lib.group_of('Walls', {'Shell': ['Walls']}) == 'Shell'
    st.parts.clear()
    calls.clear()
    sl.groups.draw(Layout(), ctx)
    assert not calls, 'with no catalogue loaded the feature must draw nothing, so the panel shows no empty box'
    assert bpy.ops.ss_link.load_catalog() == {'FINISHED'} and len(st.parts) == total

    # ---- the filter put back without its callbacks: File > Open, undo and redo. The menus, counts and grid those
    # callbacks rebuild are module state, not in the file and not in an undo step, so a handler resyncs them.
    hooks = (bpy.app.handlers.load_post, bpy.app.handlers.undo_post, bpy.app.handlers.redo_post)

    def hooked():
        return [sum(1 for h in handlers if getattr(h, '__module__', '') == lib.__name__) for handlers in hooks]

    def poke(name, number):
        """Store a choice as undo and File > Open do: as its number, and with no callback told."""
        raw = st.bl_system_properties_get() if hasattr(st, 'bl_system_properties_get') else st   # 5.0 moved them out of st[...]
        raw[name] = number

    assert hooked() == [1, 1, 1], ('one handler each: the first unregister must have taken its own off', hooked())
    numbers = {kind: dict(table) for kind, table in lib._numbers.items()}
    for kind, table in numbers.items():
        assert table['All'] == 0 and len(set(table.values())) == len(table), (kind, 'every choice needs a number of its own')
        assert all(0 < n < 2 ** 24 for ident, n in table.items() if ident != 'All'), (kind, 'a button carries an enum value as a float')
    st.category = foreign
    with tempfile.TemporaryDirectory() as tmp:
        blend = str(Path(tmp) / 'filter.blend')
        assert bpy.ops.wm.save_as_mainfile(filepath=blend, copy=True) == {'FINISHED'}
        for table in lib._numbers.values():
            table.clear()       # as in a new session, which meets the names in its own order: Building's categories first, here
            table['All'] = 0
        st.group = 'Building'   # the menus now list Building's categories, and the file's choice is not one of them
        assert st.category == 'All'
        assert bpy.ops.wm.open_mainfile(filepath=blend) == {'FINISHED'}
    sc = bpy.context.scene      # the old scene went with the old file
    st = sc.ss_link
    assert (st.group, st.category, st.pack, st.search) == ('All', foreign, 'All', ''), (st.group, st.category)
    assert [i[0] for i in lib.category_items(st, ctx)] == all_categories, 'the reopened file shows another filter\'s category menu'
    agree(expect(category=foreign), 'a file reopened with a category chosen')
    # (Every name this session has met, a pack of sent meshes among them, is in the old tables; the reopened file names fewer.)
    assert all(numbers[kind].get(name) == n for kind, table in lib._numbers.items() for name, n in table.items()) and \
        all(len(table) > 1 for table in lib._numbers.values()), \
        'a choice\'s number follows the order the names were met in: a saved file would reopen on another choice'
    assert hooked() == [1, 1, 1], 'opening a file dropped the handlers: they have to be persistent'
    assert [h for h in bpy.app.handlers.load_post if getattr(h, '__module__', '') == sl.editor_link.__name__] == [sl.editor_link.file_loaded], \
        'the handler that forgets what was pushed has to outlive the file load it is there for'

    st.category = 'All'
    st.group = 'Building'
    st.category = building[-1]
    bpy.ops.ed.undo_push(message='selftest: Building and a category')
    st.group = other            # which sends the category back to All in the same step
    bpy.ops.ed.undo_push(message='selftest: another type')
    assert bpy.ops.ed.undo() == {'FINISHED'}
    st = bpy.context.scene.ss_link
    assert (st.group, st.category) == ('Building', building[-1]), ('undo', st.group, st.category)
    assert [i[0] for i in lib.category_items(st, ctx)] == ['All'] + building, 'undo left the other type\'s category menu'
    agree(expect('Building', building[-1]), 'after undo')
    assert bpy.ops.ed.redo() == {'FINISHED'}
    st = bpy.context.scene.ss_link
    assert (st.group, st.category) == (other, 'All'), ('redo', st.group, st.category)
    agree(counts[other], 'after redo')

    # ---- where nothing resyncs (told here by taking the handlers off), old numbers are not passed off as this filter's
    lib.hook_restores(False)
    try:
        assert hooked() == [0, 0, 0], hooked()
        st.search = 'no part is called this'     # every type counts 0 now
        poke('search', '')
        assert lib.current_filter(st) == ('All', 'All', other, ()) and not lib.counts_known(st)
        assert lib.shown_label(st) == f'{total} parts', lib.shown_label(st)
        calls.clear()
        sl.groups.draw(Layout(), ctx)
        assert [args[0] for name, args, _ in calls if name == 'set enabled'][:len(idents)] == [True] * len(idents), 'a stale 0 greyed a type out'
        lib.resync(st)
        agree(counts[other], 'resync by hand')
        # a state that never went through group_changed: the category of one type under another
        st.group = 'All'
        st.category = foreign
        poke('group', numbers['groups']['Building'])
        assert not lib.counts_known(st)
        lib.resync(st)
        assert (st.group, st.category) == ('Building', 'All'), (st.group, st.category)
        agree(counts['Building'], 'a category its type does not have')
        # and a choice these parts no longer name (Blender warns once that the number matches no enum: that is the case tested)
        poke('pack', 7)
        assert 7 not in numbers['packs'].values()
        lib.resync(st)
        assert st.pack == 'All'
        agree(counts['Building'], 'a pack the catalogue has lost')
    finally:
        lib.hook_restores(True)
    assert hooked() == [1, 1, 1], hooked()
    assert bpy.ops.ss_link.clear_filters() == {'FINISHED'}
    agree(total, 'after the restores')

    # ---- the gallery: a type on every card, sections type by type, a bad recipe skipped with a note
    gallery = sl.import_tool('build_gallery')
    data = gallery.gallery_data(sl.project_root())
    assert len(data['meshes']) == total and all(card.get('group') for card in data['meshes'])
    assert {card['asset']: card['group'] for card in data['meshes']} == typed, 'the page and the panel sort a part differently'
    assert dict(data['groups']) == {g: n for g, n in counts.items() if n} and [g for g, _ in data['groups']] == [g for g in idents if counts.get(g)]
    assert list(dict.fromkeys(row[2] for row in data['categories'])) == [g for g, _ in data['groups']], 'sections must run type by type'
    page = gallery.render(data)
    blob = page.split('<script id="ss-data" type="application/json">', 1)[1].split('</script>', 1)[0]
    embedded = json.loads(blob)
    assert len(embedded['meshes']) == total and all(card.get('group') for card in embedded['meshes'])
    assert 'id="types"' in page and page.index('id="types"') < page.index('id="chips"'), 'type chips go above the category chips'
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / 'Artifacts' / 'PrefabLibrary').mkdir(parents=True)
        (tmp / 'Artifacts' / 'PrefabLibrary' / 'catalog.json').write_text(json.dumps({'categories': old['categories'], 'meshes': old['meshes'][:6]}), encoding='utf-8')
        recipes = {'Good': {'static_meshes': [{'asset': old['meshes'][0]['asset']}], 'point_lights': []},
                   'MeshesNumber': {'static_meshes': 5}, 'AssetList': {'static_meshes': [{'asset': ['/Game/A.A']}]},
                   'PartNumber': {'static_meshes': [7]}, 'NotARecipe': [1, 2]}
        (tmp / 'Prefabs' / 'T').mkdir(parents=True)
        for name, recipe in recipes.items():
            (tmp / 'Prefabs' / 'T' / (name + '.json')).write_text(json.dumps(recipe), encoding='utf-8')
        built = gallery.build(tmp)
        assert built['cards'] == 6 and built['prefabs'] == 5 and built['skipped'] == 4 and len(built['notes']) == 4, built
        assert all('wrong value type' in note for note in built['notes']) and not any('Good.json' in note for note in built['notes']), built['notes']
        assert all(card['group'] for card in gallery.gallery_data(tmp)['meshes'])
        assert (tmp / 'Artifacts' / 'PrefabLibrary' / 'index.html').exists()
    return {'types': counts, 'building_categories': building, 'other_type': other, 'pack': pack, 'word': word, 'gallery_cards': len(embedded['meshes'])}


groups_result = selftest_groups()
print('SELFTEST groups ok:', json.dumps(groups_result))
# ================================================================ feature 'groups': the type filter (end)

# ================================================================ feature 'scenes': Open Scene / Apply (begin)
# Opens the station interior from the real recipe, checks where things landed and what is locked, makes Apply
# refuse a part in the flight lane and then accept the scene, and reads back what it wrote. Apply's target is
# pointed at Prefabs/_SelfTest for the run, so an applied StationInterior.json of the owner's is never touched,
# and the editor link is a stand-in, so an editor that happens to be open is never asked to rebuild anything.
def selftest_scenes():
    import struct
    scn = sl.scenes
    spec = scn.RECIPE_SCENES[0]
    real = (dict(spec), sl.editor_link.link)
    home = bpy.context.window.scene
    scenes_before = len(bpy.data.scenes)
    scratch = sl.prefabs_dir() / '_SelfTest'
    shutil.rmtree(scratch, ignore_errors=True)
    real_backups, scn.BACKUPS = scn.BACKUPS, Path('Artifacts/LiveLink/_SelfTestSceneBackups')
    shutil.rmtree(ROOT / scn.BACKUPS, ignore_errors=True)
    calls = []

    class NoEditor:
        connected = False

        def connect(self, timeout=0.0):
            raise RuntimeError('no editor answered: is it open, with Python remote execution enabled?')

        def call(self, expr):
            raise AssertionError('Apply called an editor that never answered')

    class FakeEditor:
        connected = True

        def call(self, expr):
            calls.append(expr)
            return {'components': 483, 'blueprint': '/Game/SpaceSurvival/Licensed/StationVisualPass/BP_StationVisualLayout'}

    def refused(op):
        """An operator that reports an error raises in a script; hand back what it said."""
        try:
            result = op()
        except RuntimeError as e:
            return str(e)
        raise AssertionError(f'expected a refusal, got {result}')

    def rows_of(part):
        return scn.part_rows(part, prefer_matrix=False)

    def close(a, b, tol):
        return all(abs(a[i][j] - b[i][j]) <= tol for i in range(4) for j in range(3))

    try:
        assert hasattr(bpy.types.Scene, 'ss_scenes'), 'scenes.py did not register scene.ss_scenes'
        for op in ('open_scene', 'apply_scene', 'adopt_parts', 'refresh_scenes', 'copy_scene_command'):
            assert hasattr(bpy.types, 'SS_LINK_OT_' + op), op
        spec['target'] = 'Prefabs/_SelfTest/Scenes/StationInterior.json'
        source = ROOT / spec['fallback']
        synthetic = not source.exists()
        if synthetic:
            # A checkout without the private recipe still runs the feature: a small recipe of catalogued parts, clear of the lane.
            spec['fallback'] = 'Prefabs/_SelfTest/Scenes/Synthetic.json'
            source = ROOT / spec['fallback']
            source.parent.mkdir(parents=True, exist_ok=True)
            small = sorted((m for m in with_proxy if max(m['extent']) < 150), key=lambda m: m['name'])[:6]
            source.write_text(json.dumps({'schema_version': 1, 'purpose': 'self-test', 'exclude_harvested': ['BayLight_*'], 'static_meshes': [
                {'name': f'Part_{k}', 'asset': m['asset'], 'location': [-1200.0 + 400 * k, 1100.0 * (1 if k % 2 else -1), 300.0],
                 'rotation': [0, 35.0 * k, 0], 'scale': [1, 1.25, 1]} for k, m in enumerate(small)], 'point_lights': [
                {'name': 'Lamp', 'location': [0, 1200, 500], 'color': [1.0, 0.62, 0.3], 'intensity': 26000, 'attenuation_radius': 1500,
                 'cast_shadows': False}], 'notes': ['synthetic']}), encoding='utf-8')
        recipe = json.loads(source.read_text(encoding='utf-8-sig'))
        src_parts = {p['name']: p for p in recipe['static_meshes']}
        sl.editor_link.link = NoEditor()

        # ---- the registry and the menu
        bpy.ops.ss_link.refresh_scenes()
        entries = scn.registry()
        assert entries[0]['id'] == 'station_interior' and entries[0]['kind'] == 'recipe' and entries[0]['source'] == source, entries[0]
        assert all(e['kind'] == 'prefab' and e['id'] == 'prefab:' + e['label'] for e in entries[1:]), entries
        assert 'station_interior' in [i[0] for i in scn.scene_items(None, bpy.context)]
        assert refused(bpy.ops.ss_link.apply_scene).count('Open Scene'), 'Apply must refuse an ordinary Blender scene'

        # ---- the menu's numbers. Before Blender 5.2 a button carries an enum's value as a float, so a number
        # float32 cannot hold comes back as one no item has and nothing can be chosen from the dropdown. And 0,
        # which a scene that has never chosen holds, must be the station, or the dropdown starts out blank.
        def menu_numbers():
            items = scn.scene_items(None, bpy.context)
            numbers = {i[0]: i[4] for i in items}
            assert len(set(numbers.values())) == len(items), 'two scenes share a number'
            for ident, n in numbers.items():
                assert 0 <= n < 2 ** 24 and struct.unpack('f', struct.pack('f', n))[0] == n, (ident, n)
            return numbers
        assert menu_numbers()['station_interior'] == 0, menu_numbers()
        fresh = bpy.data.scenes.new('SelfTest fresh')
        assert fresh.ss_scenes.scene == 'station_interior', repr(fresh.ss_scenes.scene)
        bpy.data.scenes.remove(fresh)
        kept_numbers = dict(scn._numbers)
        many = [scn.scene_number(f'prefab:Crowd/Piece_{k}') for k in range(3000)]
        assert len(set(many)) == 3000 and min(many) >= len(scn.RECIPE_SCENES) and max(many) < 2 ** 24, (min(many), max(many))
        assert scn.scene_number('prefab:Crowd/Piece_7') == many[7], 'a scene keeps its number'
        scn._numbers.clear()
        scn._numbers.update(kept_numbers)

        # ---- an Open that fails opens nothing: no half-built scene is left tagged for the next Open to show as
        # complete and for Apply to write over the recipe, and the window is back on the scene it came from
        objects_before = len(bpy.data.objects)

        def nothing_opened(when):
            assert bpy.context.window.scene is home, (when, bpy.context.window.scene.name)
            assert len(bpy.data.scenes) == scenes_before and not [s for s in bpy.data.scenes if s.get(scn.SCENE_ID)], when
            assert len(bpy.data.objects) == objects_before, (when, len(bpy.data.objects), objects_before)

        def add_part_failing_after(count):
            """core.add_part, good for count parts and then failing the way a switched-off glTF importer would."""
            real_add, calls_made = sl.core.add_part, [0]

            def failing(*args, **kw):
                calls_made[0] += 1
                if calls_made[0] > count:
                    raise RuntimeError('the importer is switched off')
                return real_add(*args, **kw)
            sl.core.add_part = failing
            return real_add
        good_fallback = spec['fallback']
        broken = json.loads(json.dumps(recipe))
        bad = min(40, len(broken['static_meshes']) - 1)
        broken['static_meshes'][bad]['location'] = broken['static_meshes'][bad]['location'][:2]
        spec['fallback'] = 'Prefabs/_SelfTest/Scenes/Broken.json'
        (ROOT / spec['fallback']).parent.mkdir(parents=True, exist_ok=True)
        (ROOT / spec['fallback']).write_text(json.dumps(broken), encoding='utf-8')
        home.ss_scenes.scene = 'station_interior'
        said = refused(bpy.ops.ss_link.open_scene)
        assert f'part {bad} ({broken["static_meshes"][bad]["name"]})' in said, said
        nothing_opened('a recipe with a malformed part')
        (ROOT / spec['fallback']).unlink()
        spec['fallback'] = good_fallback
        real_add = add_part_failing_after(3)
        try:
            said = refused(bpy.ops.ss_link.open_scene)
        finally:
            sl.core.add_part = real_add
        assert 'switched off' in said and 'nothing was opened' in said, said
        nothing_opened('a build that failed part way')
        assert refused(bpy.ops.ss_link.apply_scene).count('Open Scene'), 'a failed Open must leave nothing for Apply'

        # ---- with no catalogue every part would be a grey one-metre box, and Apply would blame untouched floor panels for
        # reaching into the lane: Open says what is missing and opens nothing
        real_load = sl.core.load_catalog

        def no_catalogue(force=False):
            raise RuntimeError('no parts catalogue yet (test): in Unreal use SS Prefabs > Rebuild Catalogue, then Load Catalogue here')
        sl.core.load_catalog = no_catalogue
        try:
            said = refused(bpy.ops.ss_link.open_scene)
        finally:
            sl.core.load_catalog = real_load
        assert 'Rebuild Catalogue' in said, said
        nothing_opened('no catalogue')

        # ---- open: the parts where the recipe says, the lights, the locked context
        assert bpy.ops.ss_link.open_scene() == {'FINISHED'}
        scene = bpy.context.window.scene
        assert scene.name == 'SS Station interior' and scene is not home and scene[scn.SCENE_ID] == 'station_interior', scene.name
        cols = scn.role_collections(scene)
        assert [cols[r].name.split('.')[0] for r in ('parts', 'lights', 'context')] == ['Parts', 'Lights', 'Context (locked)'], cols
        parts = [o for o in cols['parts'].objects]
        assert len(parts) == len(recipe['static_meshes']) and all(o.get(sl.PROP_ASSET) for o in parts), (len(parts), len(recipe['static_meshes']))
        assert len(cols['lights'].objects) == len(recipe['point_lights'])
        by_name = {json.loads(o[scn.PROP_SOURCE])['name']: o for o in parts}
        assert set(by_name) == set(src_parts)
        # Three parts, the most turned ones first so a wrong yaw sign shows: position by the plain rule
        # (cm to m, Y flipped), facing by the plain rule (an Unreal yaw turns X toward -Y here).
        sampled = sorted(recipe['static_meshes'], key=lambda p: (-abs(math.sin(math.radians(p['rotation'][1]))), p['name']))[:2] + [recipe['static_meshes'][0]]
        for p in sampled:
            o, loc, yaw = by_name[p['name']], p['location'], math.radians(p['rotation'][1])
            want = Vector((loc[0] / 100.0, -loc[1] / 100.0, loc[2] / 100.0))
            assert (o.matrix_world.translation - want).length < 1e-5, (p['name'], tuple(o.matrix_world.translation), tuple(want))
            if not p['rotation'][0] and not p['rotation'][2]:
                x_axis = o.matrix_world.to_3x3() @ Vector((1, 0, 0))
                facing = Vector((math.cos(yaw), -math.sin(yaw), 0.0)) * p['scale'][0]
                assert (x_axis - facing).length < 1e-5, (p['name'], tuple(x_axis), tuple(facing))
            assert close(sl.to_ue_rows(o.matrix_world), rows_of(p), 1e-3), p['name']
        locked = {o.name: o for o in cols['context'].objects}
        services = ['Service: ' + s for s in ('CORE UPGRADES I - V', 'REPAIR BAY', 'CONTRACT BOARD', 'SUSPEND / SAVE & QUIT', 'LAUNCH CONTROL',
                                              'PAINT BAY', 'ALIEN WORLD', 'ENGINEER MICA / MODULES', 'BEACON LOG / LOST CREW')]
        for name in ['Deck', 'Wall boundaries', 'Flight lane', 'Mouth', 'Bay ship spot'] + services:
            assert name in locked, (name, sorted(locked))
        for o in locked.values():
            assert o.hide_select and o.get(scn.PROP_CONTEXT) and not o.get(sl.PROP_ASSET) and all(o.lock_location), o.name
            o.select_set(True)
            assert not o.select_get(), f'{o.name} can be selected'
        assert all(locked[s].type == 'EMPTY' and locked[s].show_name for s in services)
        assert locked['Flight lane'].display_type == 'WIRE' and locked['Wall boundaries'].display_type == 'WIRE'
        assert locked['Mouth'].data.materials[0].diffuse_color[3] < 1.0, 'the mouth should be see-through'

        def span(o):
            pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
            return [round(min(p[i] for p in pts), 4) for i in range(3)] + [round(max(p[i] for p in pts), 4) for i in range(3)]
        assert span(locked['Flight lane']) == [-19.0, -7.0, -0.1, 17.15, 7.0, 9.675], span(locked['Flight lane'])
        assert span(locked['Deck']) == [-17.0, -14.0, -1.1, 17.0, 14.0, -0.1], span(locked['Deck'])
        assert span(locked['Mouth']) == [-17.0, -7.0, -0.1, -17.0, 7.0, 9.675], span(locked['Mouth'])
        assert span(locked['Wall boundaries']) == [-17.25, -14.25, -0.55, 17.15, 14.25, 10.0], span(locked['Wall boundaries'])
        # The paint bay is on the starboard wall, Unreal Y -1000: Blender +10 m. A missed flip would put it at -10.
        assert (locked['Service: PAINT BAY'].location - Vector((-14.0, 10.0, 0.0))).length < 1e-6
        assert (locked['Bay ship spot'].location - Vector((8.5, 0.0, 2.2))).length < 1e-6
        assert locked['Approach corridor'].hide_get(), 'the 150 m corridor should not own View All'
        # Parts and context are converted by different code; the paint bay's platform must sit on the paint bay's anchor.
        if 'PaintBay_Platform' in by_name:
            lo, hi = scn.part_bounds_ue(by_name['PaintBay_Platform'])
            centre = Vector(((lo[0] + hi[0]) / 200.0, -(lo[1] + hi[1]) / 200.0, 0.0))
            assert (centre - locked['Service: PAINT BAY'].location).length < 0.05, (tuple(centre), tuple(locked['Service: PAINT BAY'].location))
        context_names = sorted(locked)
        # The other half of the room: what the game's own code adds to the layout (walls, ceiling, pipes, lamps, crates,
        # staff) is in no recipe. Read from the newest layout receipt and shown locked, or a part goes through a wall
        # nobody could see. Never tagged: a tag is what makes a part, and Apply and Push must not count these.
        native = list(cols['native'].objects) if 'native' in cols else []
        expected = scn.built_by_game(scn.entry_for('station_interior'), recipe)
        assert len(native) == len(expected) and (synthetic or not expected or len(expected) > 100), (len(native), len(expected))
        for o in native:
            assert o.hide_select and o.get(scn.PROP_CONTEXT) and not o.get(sl.PROP_ASSET) and all(o.lock_location), o.name
        if expected:
            assert not {o.name for o in native} & set(by_name), 'a component the recipe names is a part, not the game\'s'
            assert sum(1 for o in native if o.type == 'MESH') > len(native) // 2, 'most of the shell has a proxy in the catalogue'
            wall = next(o for o in native if o.type == 'MESH')
            row = next(r for r in expected if r['name'] == wall.name.split('.')[0])
            assert (wall.matrix_world.translation - row['matrix'].translation).length < 1e-4 and wall.data.name == 'SSProxy:' + row['asset']
            assert 'built by the game' in scene.ss_scenes.report and f'{len(locked) + len(native)} locked' in scene.ss_scenes.status, scene.ss_scenes.status
        # The Scenes box, drawn in the opened scene: Apply names what it will apply.
        log = []
        assert 'Scenes' in sl.panel.draw_features(Recorder(log), bpy.context) and not [e for e in log if e[3] == 'ERROR'], log
        assert any(e[1] == 'operator' and e[2] == 'ss_link.apply_scene' for e in log), log
        assert bpy.ops.ss_link.open_scene() == {'FINISHED'} and len(bpy.data.scenes) == scenes_before + 1, 'opening again shows the scene, it does not make another'

        # ---- apply refuses a part in the flight lane, and names it
        target = ROOT / spec['target']
        victim = by_name[sampled[0]['name']]
        was, victim_name = victim.matrix_world.copy(), victim.name   # the name outlives the object, which a reload below replaces
        victim.matrix_world = Matrix.Translation(Vector((0.0, 0.0, 3.0))) @ was.to_3x3().to_4x4()   # mid-hangar, 3 m up: in the lane
        said = refused(bpy.ops.ss_link.apply_scene)
        assert 'flight lane' in said and victim.name in said, said
        assert [o.name for o in bpy.context.selected_objects] == [victim.name], [o.name for o in bpy.context.selected_objects]
        assert scene.ss_scenes.status.startswith('refused') and victim.name in scene.ss_scenes.report, scene.ss_scenes.status
        assert not target.exists(), 'a refused scene must write nothing'
        untagged = bpy.data.objects.new('Stray', bpy.data.meshes.new('Stray'))
        cols['parts'].objects.link(untagged)
        said = refused(bpy.ops.ss_link.apply_scene)
        assert 'Stray' in said and 'press Send to Unreal' in said and 'ss_asset' not in said and victim.name in said, said
        bpy.data.objects.remove(untagged, do_unlink=True)
        # An Edit Mesh copy left standing in the scene (Edit Mesh sets it at the 3D cursor: mid-lane, in a new scene) is
        # the mesh on the bench, not a part: not blamed for the lane, not written into the station as one more door.
        bench = bpy.data.objects.new('SM_OnTheBench', bpy.data.meshes.new('SM_OnTheBench'))
        bench[sl.PROP_ASSET], bench[sl.core.PROP_EDIT] = by_name[sampled[0]['name']][sl.PROP_ASSET], True
        bench.matrix_world = Matrix.Translation(Vector((0.0, 0.0, 3.0)))
        edit_col = bpy.data.collections.new('SS Edit (selftest)')
        scene.collection.children.link(edit_col)
        edit_col.objects.link(bench)
        said = refused(bpy.ops.ss_link.apply_scene)
        assert 'SM_OnTheBench' not in said and victim.name in said, said

        # ---- moved back, it applies: same parts, untouched ones exactly where the source had them
        victim.matrix_world = was
        assert bpy.ops.ss_link.apply_scene() == {'FINISHED'}, scene.ss_scenes.status
        st = scene.ss_scenes
        # With Unreal closed the file is written and nothing else: the panel must not read like success, and the next
        # click it names is the easy one (open Unreal, Apply again), not a command line.
        assert st.status.startswith('saved, but NOT in the game yet') and 'Open the project in the Unreal editor, then press Apply again' in st.report, (st.status, st.report)
        assert 'wrote Prefabs/_SelfTest/Scenes/StationInterior.json' in st.report and '1 Edit Mesh copies left out' in st.report, st.report
        assert 'SM_OnTheBench' not in (ROOT / spec['target']).read_text(encoding='utf-8')
        bpy.data.objects.remove(bench, do_unlink=True)
        bpy.data.collections.remove(edit_col)
        for piece in ('UnrealEditor-Cmd.exe', 'SpaceSurvival.uproject', (ROOT / 'Scripts/AuthorStationEditableLayout.py').as_posix(),
                      '--layout-recipe ' + target.resolve().as_posix(), '--reset-layout'):
            assert piece in st.command, (piece, st.command)
        assert bpy.ops.ss_link.copy_scene_command() == {'FINISHED'}
        assert bpy.app.background or bpy.context.window_manager.clipboard == st.command   # there is no clipboard headless
        written = json.loads(target.read_text(encoding='utf-8'))
        assert list(written) == list(recipe), (list(written), list(recipe))   # the same keys in the same order
        for key in ('schema_version', 'purpose', 'exclude_harvested', 'notes'):
            assert written.get(key) == recipe.get(key), key
        assert len(written['static_meshes']) == len(recipe['static_meshes'])
        assert [p['name'] for p in written['static_meshes']] == [p['name'] for p in recipe['static_meshes']]
        worst = 0.0
        for got, want in zip(written['static_meshes'], recipe['static_meshes']):
            assert got['asset'] == want['asset'] and got.get('materials') == want.get('materials') and got.get('cast_shadows') == want.get('cast_shadows'), got['name']
            assert [got[k] for k in ('location', 'rotation', 'scale')] == [want[k] for k in ('location', 'rotation', 'scale')], got['name']
            want_rows = rows_of(want)
            worst = max(worst, max(abs(got['matrix'][i][j] - want_rows[i][j]) for i in range(4) for j in range(3)))
        assert worst < 1e-3, worst
        assert written['point_lights'] == recipe['point_lights'], 'lights should come back as they were read'

        # ---- Add at Cursor inside the opened scene: the part lands in the file-wide 'SS Parts', which drags the first
        # scene's parts in with it. Apply must not write those into the station; Move Selected into Parts sorts it out.
        small = next(m for m in with_proxy if max(m['extent']) < 100)
        homer = sl.add_part(small['asset'], Matrix.Translation(Vector((0.0, 30.0, 0.0))), name='HomeOnly')
        scene.ss_link.part_index = next(i for i, it in enumerate(scene.ss_link.parts) if it.asset == small['asset'])
        scene.cursor.location = Vector((-13.0, -12.5, 5.0))
        assert bpy.ops.ss_link.add_part() == {'FINISHED'}
        added = bpy.context.view_layer.objects.active
        assert added[sl.PROP_ASSET] == small['asset'] and len(added.users_scene) == 2, [s.name for s in added.users_scene]
        said = refused(bpy.ops.ss_link.apply_scene)
        assert 'also in scene' in said and 'Move Selected into Parts' in said and added.name in said and 'HomeOnly' in said, said
        sl.core.deselect_all(bpy.context)
        added.select_set(True)
        assert bpy.ops.ss_link.adopt_parts() == {'FINISHED'}, scene.ss_scenes.status
        assert list(added.users_scene) == [scene] and added.name in cols['parts'].objects and scene not in homer.users_scene and homer.users_scene
        assert bpy.ops.ss_link.apply_scene() == {'FINISHED'}, scene.ss_scenes.status
        names = [p['name'] for p in json.loads(target.read_text(encoding='utf-8'))['static_meshes']]
        assert len(names) == len(recipe['static_meshes']) + 1 and 'HomeOnly' not in names and names[-1] == added.name.replace('.', '_'), names[-3:]
        bpy.data.objects.remove(added, do_unlink=True)
        bpy.data.objects.remove(homer, do_unlink=True)

        # ---- a real edit: one part moved clear of the lane, one duplicated; an editor that answers
        sl.editor_link.link = FakeEditor()
        mover = by_name[sampled[1]['name']]
        mover.matrix_world = Matrix.Translation(Vector((0.0, 0.0, 0.25))) @ mover.matrix_world
        twin = mover.copy()
        cols['parts'].objects.link(twin)
        twin.matrix_world = Matrix.Translation(Vector((0.0, 0.0, 0.5))) @ mover.matrix_world
        assert bpy.ops.ss_link.apply_scene() == {'FINISHED'}, scene.ss_scenes.status
        assert len(calls) == 1 and 'ss_scenes' in calls[0] and calls[0].endswith('.apply_station_recipe(' + repr(target.resolve().as_posix()) + ', force=False)'), calls
        assert st.status.startswith('applied: wrote ') and '483 components' in st.report and not st.command, (st.status, st.report)
        # The file each Apply replaced is kept, and the panel says where.
        kept = sorted((ROOT / scn.BACKUPS).glob('*-StationInterior.json'), key=lambda f: f.stat().st_mtime_ns)   # two may share a second
        assert kept and 'the file it replaced is kept at' in st.report and str(kept[-1]) in st.report, (kept, st.report)
        written = json.loads(target.read_text(encoding='utf-8'))
        assert len(written['static_meshes']) == len(recipe['static_meshes']) + 1
        rows = {p['name']: p for p in written['static_meshes']}
        assert len(rows) == len(written['static_meshes']), 'names must be unique'
        moved, source_part = rows[sampled[1]['name']], sampled[1]
        assert abs(moved['location'][2] - (source_part['location'][2] + 25.0)) < 1e-3 and abs(moved['matrix'][3][2] - moved['location'][2]) < 1e-3, moved
        assert max(abs(moved['location'][i] - source_part['location'][i]) for i in (0, 1)) < 1e-3
        assert max(abs(((moved['rotation'][i] - source_part['rotation'][i]) + 180.0) % 360.0 - 180.0) for i in range(3)) < 1e-3, (moved['rotation'], source_part['rotation'])
        assert max(abs(moved['scale'][i] - source_part['scale'][i]) for i in range(3)) < 1e-5, (moved['scale'], source_part['scale'])
        assert close(scn.part_rows(moved, True), scn.part_rows({k: moved[k] for k in ('location', 'rotation', 'scale')}, False), 1e-3), 'the two forms must agree'
        copy_name = twin.name.replace('.', '_')
        assert copy_name in rows and '.' not in copy_name and rows[copy_name].get('materials') == source_part.get('materials'), sorted(rows)[:5]
        others = [p for p in written['static_meshes'] if p['name'] not in (moved['name'], copy_name)]
        assert all([p[k] for k in ('location', 'rotation', 'scale')] == [src_parts[p['name']][k] for k in ('location', 'rotation', 'scale')] for p in others)

        # ---- Blender is not the recipe's only writer. Something else wrote the file since this scene was opened or last
        # applied (the generator re-run, another .blend, a hand edit): Open shows the scene 'as it was left' and says so,
        # and Apply refuses to write the old scene over it until Apply Anyway; the file it then replaces is kept.
        mine_text = target.read_text(encoding='utf-8')
        outside = json.loads(mine_text)
        outside['static_meshes'].append(dict(outside['static_meshes'][0], name='Added_Outside_Blender'))
        target.write_text(scn.dump_recipe(outside), encoding='utf-8')
        calls_before = len(calls)
        assert bpy.ops.ss_link.open_scene() == {'FINISHED'} and 'as it was left' in st.status and 'changed on disk' in st.report, (st.status, st.report)
        said = refused(bpy.ops.ss_link.apply_scene)
        assert 'changed on disk' in said and 'Apply Anyway' in said and st.can_force, (said, st.can_force)
        assert 'Added_Outside_Blender' in target.read_text(encoding='utf-8') and len(calls) == calls_before, 'a refused Apply writes nothing and calls nobody'
        log = []
        sl.panel.draw_features(Recorder(log), bpy.context)
        assert [e for e in log if e[1] == 'operator' and e[2] == 'ss_link.apply_scene' and e[0] != 'column'], 'Apply Anyway is offered'
        assert bpy.ops.ss_link.apply_scene(force=True) == {'FINISHED'} and not st.can_force, st.status
        assert calls[-1].endswith(', force=True)') and 'Added_Outside_Blender' not in target.read_text(encoding='utf-8')
        newest_kept = sorted((ROOT / scn.BACKUPS).glob('*-StationInterior.json'), key=lambda f: f.stat().st_mtime_ns)[-1]
        assert 'Added_Outside_Blender' in newest_kept.read_text(encoding='utf-8'), 'the version that was overwritten is kept'
        assert bpy.ops.ss_link.apply_scene() == {'FINISHED'}, 'what this scene wrote itself is no change from outside'
        # The editor refusing because the Blueprint was changed outside a recipe is the same question, asked by Unreal.

        class StaleEditor(FakeEditor):
            def call(self, expr):
                calls.append(expr)
                if 'force=True' not in expr:
                    raise RuntimeError('editor error: Traceback (most recent call last):\n  File "x.py", line 1\nRuntimeError: '
                                       + scn.STALE_EDITOR + ': BP_StationVisualLayout: its saved file is not the one the last recipe build left')
                return {'components': 483, 'blueprint': 'BP', 'backup': 'C:/kept/BP_StationVisualLayout.uasset'}
        sl.editor_link.link = StaleEditor()
        said = refused(bpy.ops.ss_link.apply_scene)   # written, and refused by Unreal: an error report, which raises in a script
        assert st.can_force and 'NOT in the game' in st.status and 'Traceback' not in said, (st.status, said)
        assert 'Traceback' not in st.report and scn.STALE_EDITOR in st.report, st.report
        assert bpy.ops.ss_link.apply_scene(force=True) == {'FINISHED'} and not st.can_force and 'C:/kept/BP_StationVisualLayout.uasset' in st.report, st.report
        sl.editor_link.link = FakeEditor()

        # ---- an emptied scene has nothing wrong with it, part by part, and used to replace the recipe and the layout
        # with nothing. It is never written; a scene that lost more than a quarter of its parts asks first.
        good_text = target.read_text(encoding='utf-8')
        calls_before = len(calls)
        all_parts = [o for o in scene.objects if o.type == 'MESH' and o.get(sl.PROP_ASSET)]
        elsewhere = bpy.data.collections.new('SelfTest elsewhere')
        homes = {o: list(o.users_collection) for o in all_parts}

        def take_out(objects):
            for o in objects:
                for c in homes[o]:
                    if o.name in c.objects:
                        c.objects.unlink(o)
                elsewhere.objects.link(o)

        def put_back(objects):
            for o in objects:
                elsewhere.objects.unlink(o)
                for c in homes[o]:
                    c.objects.link(o)
        third = all_parts[:len(all_parts) // 3 + 1]
        take_out(third)
        said = refused(bpy.ops.ss_link.apply_scene)
        assert f'{len(third)} of the {len(all_parts)} parts' in said and st.can_force and target.read_text(encoding='utf-8') == good_text, said
        take_out(all_parts[len(third):])
        for forced in (False, True):
            said = refused(lambda: bpy.ops.ss_link.apply_scene(force=forced))
            assert 'no parts in this scene' in said and 'never applied' in said, said
        assert target.read_text(encoding='utf-8') == good_text and len(calls) == calls_before, 'an empty scene writes nothing and calls nobody'
        put_back(all_parts)
        bpy.data.collections.remove(elsewhere)
        assert bpy.ops.ss_link.apply_scene() == {'FINISHED'} and target.read_text(encoding='utf-8') == good_text, scene.ss_scenes.status

        # ---- once applied, the written file is what Open reads next
        assert scn.registry()[0]['source'] == target
        bpy.ops.ss_link.open_scene(reload=True)
        assert len(scn.role_collections(scene)['parts'].objects) == len(written['static_meshes']) and len(bpy.data.scenes) == scenes_before + 1

        # ---- Reload replaces everything Apply writes, wherever it is filed. Two parts moved to a collection of the
        # owner's, a new part, a hand-modelled one and a lamp beside them: applied, they are in the file, and a Reload
        # that kept them would set each exactly on its reloaded copy, for the next Apply to write both.
        def tagged(s):
            return [o for o in s.objects if o.type == 'MESH' and o.get(sl.PROP_ASSET)]

        def point_lights(s):
            return [o for o in s.objects if o.type == 'LIGHT']
        cols = scn.role_collections(scene)
        fixes = bpy.data.collections.new('My fixes')
        scene.collection.children.link(fixes)
        for o in list(cols['parts'].objects)[:2]:
            cols['parts'].objects.unlink(o)
            fixes.objects.link(o)
        sl.add_part(small['asset'], Matrix.Translation(Vector((-13.0, -12.5, 5.0))), fixes, name='FiledExtra')
        handmade = bpy.data.objects.new('Handmade', bpy.data.meshes.new('HandmadeMesh'))
        handmade[sl.PROP_ASSET] = small['asset']
        handmade.matrix_world = Matrix.Translation(Vector((-13.0, -11.0, 5.0)))
        fixes.objects.link(handmade)
        lamp = bpy.data.objects.new('FiledLamp', bpy.data.lights.new('FiledLamp', 'POINT'))
        lamp.matrix_world = Matrix.Translation(Vector((-13.0, -11.0, 6.0)))
        fixes.objects.link(lamp)
        want_parts, want_lights = len(written['static_meshes']) + 2, len(written['point_lights']) + 1
        assert bpy.ops.ss_link.apply_scene() == {'FINISHED'}, scene.ss_scenes.status
        first = json.loads(target.read_text(encoding='utf-8'))
        assert (len(first['static_meshes']), len(first['point_lights'])) == (want_parts, want_lights)
        for again in range(2):
            assert bpy.ops.ss_link.open_scene(reload=True) == {'FINISHED'}
            assert (len(tagged(scene)), len(point_lights(scene)), len(fixes.all_objects)) == (want_parts, want_lights, 0), (again, len(tagged(scene)))
            assert bpy.ops.ss_link.apply_scene() == {'FINISHED'}, scene.ss_scenes.status
            assert json.loads(target.read_text(encoding='utf-8')) == first, f'reload {again + 1} changed what Apply writes'
        # The hand-modelled object went with the rest; its mesh, which is the owner's work, did not.
        assert 'HandmadeMesh' in bpy.data.meshes and bpy.data.meshes['HandmadeMesh'].use_fake_user
        bpy.data.meshes.remove(bpy.data.meshes['HandmadeMesh'])
        bpy.data.collections.remove(fixes)
        # A part the home scene uses as well is not Reload's to delete: it stays, Open says so, and Apply asks.
        both = sl.add_part(small['asset'], Matrix.Translation(Vector((0.0, 40.0, 0.0))), name='BothScenes')
        assert len(both.users_scene) == 2, [s.name for s in both.users_scene]
        assert bpy.ops.ss_link.open_scene(reload=True) == {'FINISHED'}
        assert both.name in bpy.data.objects and home in both.users_scene and 'shared with another scene' in scene.ss_scenes.report, scene.ss_scenes.report
        assert 'BothScenes' in refused(bpy.ops.ss_link.apply_scene)
        bpy.data.objects.remove(both, do_unlink=True)
        scene.collection.children.unlink(bpy.data.collections['SS Parts'])
        assert bpy.ops.ss_link.apply_scene() == {'FINISHED'} and json.loads(target.read_text(encoding='utf-8')) == first

        # ---- a Reload that fails. Over a bad file it touches nothing: the scene is as it was and still the station's.
        good_text = target.read_text(encoding='utf-8')
        broken = json.loads(good_text)
        broken['static_meshes'][bad]['location'] = broken['static_meshes'][bad]['location'][:2]
        target.write_text(json.dumps(broken), encoding='utf-8')
        said = refused(lambda: bpy.ops.ss_link.open_scene(reload=True))
        target.write_text(good_text, encoding='utf-8')
        assert f'part {bad} ' in said and 'is as it was' in said, said
        assert scene.get(scn.SCENE_ID) == 'station_interior' and len(tagged(scene)) == want_parts and bpy.context.window.scene is scene
        # Nor over a proxy that will not import: the proxies are fetched before the scene is emptied for them.
        real_proxy = sl.core.proxy_mesh

        def no_proxy(entry):
            raise RuntimeError('the importer is switched off')
        sl.core.proxy_mesh = no_proxy
        try:
            said = refused(lambda: bpy.ops.ss_link.open_scene(reload=True))
        finally:
            sl.core.proxy_mesh = real_proxy
        assert 'switched off' in said and 'is as it was' in said, said
        assert scene.get(scn.SCENE_ID) == 'station_interior' and len(tagged(scene)) == want_parts and bpy.context.window.scene is scene
        # Part way through the build, the scene is already emptied. It must not stay the station's: shown 'as it was
        # left' by the next Open and then applied, its three parts would replace the recipe.
        real_add = add_part_failing_after(3)
        try:
            said = refused(lambda: bpy.ops.ss_link.open_scene(reload=True))
        finally:
            sl.core.add_part = real_add
        assert 'switched off' in said and 'no longer tied to the recipe' in said, said
        assert scene.get(scn.SCENE_ID) is None and not tagged(scene) and not scn.role_collections(scene), scene.name
        assert refused(bpy.ops.ss_link.apply_scene).count('Open Scene') and target.read_text(encoding='utf-8') == good_text
        abandoned = scene
        assert bpy.ops.ss_link.open_scene() == {'FINISHED'}
        scene = bpy.context.window.scene
        assert scene is not abandoned and scene[scn.SCENE_ID] == 'station_interior' and len(tagged(scene)) == want_parts, scene.name
        assert scene.ss_scenes.status.startswith('opened Station interior'), scene.ss_scenes.status
        bpy.data.scenes.remove(abandoned)

        # ---- Push All and Live from the owner's own scene, with the station open in the same file: its parts carry
        # ss_asset like any other, and must not arrive in the open level as loose actors
        class PushEditor:
            connected = True

            def __init__(self):
                self.rows, self.removed = [], []

            def call(self, expr):
                head = 'ss_prefabs.apply_link('
                assert expr.startswith(head) and expr.endswith(')'), expr
                payload = json.loads(ast.literal_eval(expr[len(head):-1]))
                self.rows += payload['objects']
                self.removed += payload['remove']
                return {'created': len(payload['objects']), 'moved': 0, 'removed': len(payload['remove'])}

        # The rule is core's own: nothing wraps core.linked_objects, and the add-on's name for it is the same function.
        assert sl.core.linked_objects.__module__ == sl.core.__name__ and sl.linked_objects is sl.core.linked_objects
        assert not hasattr(scn, 'install_push_filter') and not hasattr(scn, 'linked_objects') and scn.SCENE_ID == sl.core.PROP_SCENE
        assert sl.editor_link._last_sent is sl.core.pushed_links
        station_links = {o[sl.PROP_LINK] for o in tagged(scene)}
        assert len(station_links) == want_parts
        pusher, answering = PushEditor(), sl.editor_link.link
        sl.editor_link.link = pusher
        sl.editor_link._last_sent.clear()
        bpy.context.window.scene = home
        mine = sl.add_part(small['asset'], Matrix.Translation(Vector((0.0, 50.0, 0.0))), name='MineAlone')
        scene.collection.children.link(bpy.data.collections['SS Parts'])   # as Add at Cursor in the station leaves it
        try:
            assert len(mine.users_scene) == 2 and len(sl.core.tagged_objects()) >= want_parts + 1
            kept_out = [o for o in sl.core.tagged_objects() if o not in sl.core.linked_objects()]
            assert {o[sl.PROP_LINK] for o in kept_out} == station_links and mine in sl.core.linked_objects(), len(kept_out)
            assert bpy.ops.ss_link.push(selected_only=False) == {'FINISHED'}, home.ss_link.status
            pushed = {r['link'] for r in pusher.rows}
            assert mine[sl.PROP_LINK] in pushed and not pushed & station_links, (len(pushed), len(pushed & station_links))
            assert home.ss_link.status.startswith(f'pushed {len(pushed)}:'), home.ss_link.status
            pusher.rows.clear()
            sl.editor_link._last_sent.clear()
            home.ss_link.live = True
            assert sl.live_tick() == 0.5, home.ss_link.status
            assert {r['link'] for r in pusher.rows} == pushed and not pusher.removed, (len(pusher.rows), len(pushed))
            home.ss_link.live = False
            # Parts picked by hand in the station are the owner's to push, and Live then moves them; it must not read them as deleted.
            bpy.context.window.scene = scene
            picked = tagged(scene)[:2]
            sl.core.deselect_all(bpy.context)
            for o in picked:
                o.select_set(True)
            pusher.rows.clear()
            assert bpy.ops.ss_link.push(selected_only=True) == {'FINISHED'}, scene.ss_link.status
            assert {r['link'] for r in pusher.rows} == {o[sl.PROP_LINK] for o in picked}
            pusher.rows.clear()
            resting = picked[0].matrix_world.copy()
            picked[0].matrix_world = Matrix.Translation(Vector((0.0, 0.0, 0.1))) @ resting
            scene.ss_link.live = True
            assert sl.live_tick() == 0.5, scene.ss_link.status
            assert [r['link'] for r in pusher.rows] == [picked[0][sl.PROP_LINK]] and not pusher.removed, (len(pusher.rows), pusher.removed)
            picked[0].matrix_world = resting
            pushed_from_home = len(pushed)
        finally:
            home.ss_link.live = scene.ss_link.live = False
            sl.editor_link.link = answering
            sl.editor_link._last_sent.clear()
        scene.collection.children.unlink(bpy.data.collections['SS Parts'])
        bpy.data.objects.remove(mine, do_unlink=True)
        # The rule holds by the scene's tag alone: a scene that loses it is an ordinary scene again, and its parts are pushed.
        ident = scene[scn.SCENE_ID]
        del scene[scn.SCENE_ID]
        assert len(sl.core.linked_objects()) == len(sl.core.tagged_objects()) >= want_parts
        scene[scn.SCENE_ID] = ident
        assert not {o[sl.PROP_LINK] for o in sl.core.linked_objects()} & station_links

        # ---- a prefab opens the same way and Apply saves it back to its own file
        pick = with_proxy[0]['asset']
        pair = {'schema_version': 1, 'purpose': 'self-test pair', 'origin': 'kept as it is', 'static_meshes': [
            {'name': 'Left', 'asset': pick, 'matrix': sl.to_ue_rows(Matrix.Translation(Vector((-2.0, 1.0, 0.0))))},
            {'name': 'Right', 'asset': pick, 'matrix': sl.to_ue_rows(Matrix.Translation(Vector((2.0, 1.0, 0.0))) @ Matrix.Rotation(math.radians(30), 4, 'Z')),
             'materials': ['/Game/SpaceSurvival/Materials/M_Cyan.M_Cyan']}],
            'point_lights': [{'name': 'Glow', 'location': [0, -100, 250], 'color': [0.25, 0.75, 1.0], 'intensity': 9000, 'attenuation_radius': 1400,
                              'cast_shadows': False}], 'notes': []}
        pair_path = scratch / 'Pair.json'
        pair_path.write_text(json.dumps(pair), encoding='utf-8')
        bpy.ops.ss_link.refresh_scenes()
        assert 'prefab:_SelfTest/Pair' in [i[0] for i in scn.scene_items(None, bpy.context)]
        assert 'prefab:_SelfTest/Scenes/StationInterior' not in [i[0] for i in scn.scene_items(None, bpy.context)], 'an applied scene is not also a prefab'
        numbers = menu_numbers()   # with prefabs in the menu: all under 2**24, the station still on 0
        assert numbers['station_interior'] == 0 and numbers['prefab:_SelfTest/Pair'] == scn.scene_number('prefab:_SelfTest/Pair') > 0, numbers
        scene.ss_scenes.scene = 'prefab:_SelfTest/Pair'
        assert scene.ss_scenes.scene == 'prefab:_SelfTest/Pair'
        assert bpy.ops.ss_link.open_scene() == {'FINISHED'}
        pscene = bpy.context.window.scene
        assert pscene.name == 'SS _SelfTest/Pair' and 'context' not in scn.role_collections(pscene), pscene.name
        left = next(o for o in pscene.objects if o.name.startswith('Left'))
        assert (left.matrix_world.translation - Vector((-2.0, 1.0, 0.0))).length < 1e-6
        left.matrix_world = Matrix.Translation(Vector((0.0, 0.0, 3.0)))   # the lane is the station's rule, not a prefab's
        station_calls = len(calls)
        assert bpy.ops.ss_link.apply_scene() == {'FINISHED'}, pscene.ss_scenes.status
        assert len(calls) == station_calls, 'a prefab is saved, not sent to the layout Blueprint'
        saved = json.loads(pair_path.read_text(encoding='utf-8'))
        assert saved['origin'] == 'kept as it is' and [p['name'] for p in saved['static_meshes']] == ['Left', 'Right']
        assert abs(saved['static_meshes'][0]['matrix'][3][2] - 300.0) < 1e-3 and 'location' not in saved['static_meshes'][0], saved['static_meshes'][0]
        assert saved['static_meshes'][1] == json.loads(json.dumps(pair['static_meshes'][1])) and saved['point_lights'] == pair['point_lights']
        return {'parts': len(recipe['static_meshes']), 'lights': len(recipe['point_lights']), 'context': len(context_names), 'sampled': [p['name'] for p in sampled],
                'refused': victim_name, 'worst_untouched_cm': worst, 'synthetic_recipe': synthetic, 'reloads_hold_parts': want_parts,
                'pushed_from_home': pushed_from_home, 'kept_from_push': len(station_links), 'built_by_game_shown_locked': len(native)}
    finally:
        spec.clear()
        spec.update(real[0])
        sl.editor_link.link = real[1]
        shutil.rmtree(ROOT / scn.BACKUPS, ignore_errors=True)
        scn.BACKUPS = real_backups
        try:
            (ROOT / 'Artifacts' / 'LiveLink').rmdir()   # when this test is all that ever made it
        except OSError:
            pass
        bpy.context.window.scene = home
        for scene in [s for s in bpy.data.scenes if s.get(scn.SCENE_ID)]:
            scn.clear_loaded(scene)
            for o in list(scene.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.scenes.remove(scene)
        shutil.rmtree(scratch, ignore_errors=True)   # Prefabs/ is committed: the written recipe must not stay in it
        scn.refresh_scene_items()


scenes_result = selftest_scenes()
print('SELFTEST scenes ok:', json.dumps(scenes_result))
# ================================================================ feature 'scenes': Open Scene / Apply (end)

# ---------------------------------------------------------------- and it all comes off again
sl.unregister()
assert_clean(clean, 'after the final unregister')
print('SSLIVELINK_SELFTEST_OK ' + json.dumps({'meshes': len(cat['meshes']), 'proxies': len(with_proxy), 'bounds_checked': checked, 'live': live,
                                              'modules': names, 'feature_boxes': feature_boxes, 'unregistered_clean': True}))
