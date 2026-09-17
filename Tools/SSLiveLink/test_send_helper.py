"""The Blender half of Scripts/TestSendScenes.py: real sends, made by the real add-on, for Unreal to import.

  blender --background --factory-startup --python Tools/SSLiveLink/test_send_helper.py -- \
      --project <root> --mode new|resend|edit --blend <scratch .blend> --out <result .json> [--asset <path> --glb <file>]

Run by the Unreal test, once per step, because the editor has to import between the steps:

  new     Builds SSTestWedge, a slab with a tower on one corner, in two materials, places it rotated and away
          from the origin, and sends it with send.send_objects into the category '_SelfTest'. The .blend is
          saved so the next step finds the same object, tagged as the add-on tagged it.
  resend  Opens that .blend, makes the slab a metre longer, and sends the same object again.
  edit    import_edit_copy() of the GLB the editor exported for --asset, the top raised 30 cm, a material
          slot added, and sent back: a fix to a mesh that is not under /Game/Blender.

Nothing here talks to an editor. send_objects writes the files and stops; the operator's notify_editor()
would reach the owner's open editor, which is not this test's to drive. The side catalogue (sent.json) is
pointed at a scratch file so the owner's parts list never shows a test mesh.

The shape has no symmetry: X 0..2 m, Y 0..1 m, Z 0..0.8 m from the object's origin, the tower (second
material) on X 0..0.5, Y 0.6..1. Any mirror, axis swap or lost pivot moves its bounds or the tower's.
"""
from pathlib import Path
import json
import math
import os
import sys
import traceback

import bpy
import bmesh
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


ROOT = Path(arg('--project') or Path(__file__).resolve().parents[2])
MODE, BLEND, OUT = arg('--mode'), Path(arg('--blend')), Path(arg('--out'))
CATEGORY = '_SelfTest'
SENT_SCRATCH = '_sendscenes_test_sent.json'
WEDGE = 'SSTestWedge'
SLAB = ((0.0, 0.0, 0.0), (2.0, 0.6, 0.4))
TOWER = ((0.0, 0.6, 0.0), (0.5, 1.0, 0.8))

os.environ['SS_PROJECT_ROOT'] = str(ROOT)
sys.path.insert(0, str(Path(__file__).resolve().parent))


def add_box(bm, lo, hi, material_index):
    made = bmesh.ops.create_cube(bm, size=1.0, calc_uvs=True)
    for v in made['verts']:
        v.co = Vector([lo[i] + (v.co[i] + 0.5) * (hi[i] - lo[i]) for i in range(3)])
    for f in {f for v in made['verts'] for f in v.link_faces}:
        f.material_index = material_index


def material(name, color):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf:
        bsdf.inputs['Base Color'].default_value = color
    mat.diffuse_color = color
    return mat


def build_wedge():
    me = bpy.data.meshes.new(WEDGE)
    bm = bmesh.new()
    add_box(bm, *SLAB, 0)
    add_box(bm, *TOWER, 1)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material('M_SSTestRed', (0.8, 0.1, 0.1, 1.0)))
    me.materials.append(material('M_SSTestBlue', (0.1, 0.2, 0.8, 1.0)))
    obj = bpy.data.objects.new(WEDGE, me)
    bpy.context.scene.collection.objects.link(obj)
    # Away from the origin and turned: the asset must hold the local shape about the object's origin, none of this.
    obj.matrix_world = Matrix.Translation(Vector((3.0, -2.0, 1.5))) @ Matrix.Rotation(math.radians(35.0), 4, 'Z')
    return obj


def local_bounds(obj, material_index=None):
    me = obj.data
    if material_index is None:
        points = [v.co for v in me.vertices]
    else:
        points = [me.vertices[i].co for p in me.polygons if p.material_index == material_index for i in p.vertices]
    return [min(p[i] for p in points) for i in range(3)], [max(p[i] for p in points) for i in range(3)]


def describe(obj, sent):
    lo, hi = local_bounds(obj)
    slots = []
    for index, mat in enumerate(obj.data.materials):
        faces = sum(1 for p in obj.data.polygons if p.material_index == index)
        slot_lo, slot_hi = local_bounds(obj, index) if faces else (None, None)
        slots.append({'material': mat.name if mat else '', 'faces': faces, 'lo_m': slot_lo, 'hi_m': slot_hi})
    side = json.loads(Path(sent['glb']).with_suffix('.json').read_text(encoding='utf-8'))
    return {'object': obj.name, 'asset': sent['asset'], 'glb': str(sent['glb']), 'sidecar': str(Path(sent['glb']).with_suffix('.json')),
            'target': side['target'], 'sidecar_materials': side['materials'], 'sidecar_bounds_cm': side['bounds_cm'],
            'lo_m': lo, 'hi_m': hi, 'dimensions_m': list(obj.dimensions), 'scale': list(obj.scale),
            'world_translation_m': list(obj.matrix_world.translation), 'slots': slots,
            'tags': {k: obj.get(k) for k in ('ss_asset', 'ss_sent', 'ss_edit', 'ss_link')}, 'triangles': sent['triangles']}


def select_only(obj):
    for o in bpy.context.view_layer.objects:
        if o is not None:
            o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def main():
    import ss_live_link as sl
    snd = sl.send
    sl.register()
    sl.core.SENT = SENT_SCRATCH   # the side catalogue is core's; the parts list is filled from it
    result = {'mode': MODE, 'blender': bpy.app.version_string, 'outbox': str(snd.outbox_dir())}
    BLEND.parent.mkdir(parents=True, exist_ok=True)
    try:
        if MODE == 'new':
            for o in list(bpy.data.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            obj = build_wedge()
            bpy.context.view_layer.update()
            select_only(obj)
            sent = snd.send_objects(bpy.context, [obj], CATEGORY)
            assert len(sent) == 1, sent
            result['sent'] = describe(obj, sent[0])
            result['expected_folder'] = snd.category_folder(CATEGORY)
            bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), check_existing=False)
        elif MODE == 'resend':
            bpy.ops.wm.open_mainfile(filepath=str(BLEND))
            obj = bpy.data.objects[WEDGE]
            assert snd.sendable(obj) and obj.get(snd.PROP_SENT), dict(obj.items())
            for v in obj.data.vertices:
                if v.co.x > SLAB[1][0] - 1e-4:
                    v.co.x += 1.0
            obj.data.update()
            bpy.context.view_layer.update()
            select_only(obj)
            # No name, another category: a mesh sent before keeps its asset whatever the panel says now.
            sent = snd.send_objects(bpy.context, [obj], 'Props')
            assert len(sent) == 1, sent
            result['sent'] = describe(obj, sent[0])
            bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), check_existing=False)
        elif MODE == 'edit':
            asset, glb = arg('--asset'), Path(arg('--glb'))
            for o in list(bpy.data.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            obj = snd.import_edit_copy(bpy.context, asset, glb)
            bpy.context.view_layer.update()
            came_lo, came_hi = local_bounds(obj)
            result['arrived'] = {'lo_m': came_lo, 'hi_m': came_hi, 'materials': [m.name if m else '' for m in obj.data.materials],
                                 'faces': [sum(1 for p in obj.data.polygons if p.material_index == i) for i in range(len(obj.data.materials))]}
            top = came_hi[2]
            for v in obj.data.vertices:
                if v.co.z > top - 1e-4:
                    v.co.z += 0.3
            # A slot the asset never had, on half the faces of its largest slot, so no old slot is left without faces.
            counts = result['arrived']['faces']
            donor = counts.index(max(counts))
            obj.data.materials.append(material('M_SSTestAdded', (0.1, 0.8, 0.2, 1.0)))
            added = len(obj.data.materials) - 1
            donors = [p for p in obj.data.polygons if p.material_index == donor]
            for p in donors[:max(1, len(donors) // 2)]:
                p.material_index = added
            obj.data.update()
            bpy.context.view_layer.update()
            select_only(obj)
            sent = snd.send_objects(bpy.context, [obj], 'Misc')
            assert len(sent) == 1, sent
            result['sent'] = describe(obj, sent[0])
            result['added_slot'] = added
            result['raised_m'] = 0.3
        else:
            raise SystemExit(f'unknown --mode {MODE!r}')
        result['ok'] = True
    finally:
        scratch = sl.library_dir() / SENT_SCRATCH
        if scratch.exists():
            scratch.unlink()
        sl.unregister()
    return result


try:
    outcome = main()
except BaseException as e:  # the Unreal test reads the file, not this process's output
    outcome = {'ok': False, 'mode': MODE, 'error': f'{type(e).__name__}: {e}', 'traceback': traceback.format_exc()}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(outcome, indent=1, default=str), encoding='utf-8')
print('SENDHELPER ' + ('OK' if outcome.get('ok') else 'FAIL ' + str(outcome.get('error'))))
