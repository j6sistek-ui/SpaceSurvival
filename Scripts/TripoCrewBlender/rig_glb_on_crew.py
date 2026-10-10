"""An unrigged GLB onto an existing crew skeleton: the donor's bones, fresh bone-heat weights. Headless, CPU only.

  blender -b <donor.blend> --factory-startup -P rig_glb_on_crew.py -- <in.glb> <out.blend> <Name>

Written for the Cyborg (2026-10-09): the owner regenerated her as one 124k-face GLB with one 4K PBR set
(M:/Local AI/Projects/newCYBORG) and asked for it rigged and animated. Measured against the previous Cyborg
(TripoCrew_Sources_20261008/Cyborg.blend), every landmark - arm centreline, shoulder line, crotch, leg centres,
ankles, feet, hands - agrees to within 1 cm once both stand 1.78 m, so that rig IS the fit: only the arm span is
scaled about each clavicle (0.643 -> 0.631 m). The body is normalised like every crew member (1.78 m, feet on
z=0, centred), welded at 0.5 mm so bone heat sees one surface, and weighted with `root` excluded (see
strip_root_weights.py). The one material is renamed <Name>Body so the Unreal slot has a stable name
(ImportTripoCrew.py MATERIAL_SLOTS). Then export_for_unreal.py and check_weights.py as usual.

Use it again only for a model whose proportions match its donor: check with a landmark probe first
(arm tips, arm z at a few x, leg x at a few z, crotch, ankle) - a bounds-only fit put the Warden's feet wrong.
"""
import json
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector, kdtree

GLB, OUT, NAME = sys.argv[-3], sys.argv[-2], sys.argv[-1]
H = 1.78
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
for o in [o for o in bpy.data.objects if o.type == 'MESH']:
    bpy.data.objects.remove(o)
for me in [d for d in bpy.data.meshes if d.users == 0]:
    bpy.data.meshes.remove(me)
bpy.ops.import_scene.gltf(filepath=GLB)
m = [o for o in bpy.data.objects if o.type == 'MESH'][0]
m.name = NAME; m.data.name = NAME; me = m.data


def coords():
    co = np.empty(len(me.vertices) * 3, dtype=np.float32); me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3); M = np.array(m.matrix_world); return co @ M[:3, :3].T + M[:3, 3]


co = coords(); mn, mx = co.min(0), co.max(0)
k = H / (mx[2] - mn[2]); c = Vector(((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, mn[2]))
me.transform(Matrix.Diagonal((k, k, k, 1)) @ Matrix.Translation(-c) @ m.matrix_world); me.update()
m.matrix_world = Matrix.Identity(4)
for slot in me.materials:
    slot.name = NAME + "Body"
# arm span: scale the arm bones about each clavicle head so the hands end where the new hands end
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT'); eb = arm.data.edit_bones
tip_new = float(np.abs(coords()[:, 0]).max()); tip_old = max(abs(b.tail.x) for b in eb)
for side in ("l", "r"):
    cx = eb["clavicle_" + side].head.x
    s = (tip_new - abs(cx)) / (tip_old - abs(cx))
    for b in eb:
        if b.name.endswith("_" + side) and not b.name.startswith(("thigh", "calf", "foot", "ball")):
            for attr in ("head", "tail"):
                p = getattr(b, attr); setattr(b, attr, Vector((cx + (p.x - cx) * s, p.y, p.z)))
print("RIG| arm x scale %.4f (tip %.3f -> %.3f)" % (s, tip_old, tip_new))
bpy.ops.object.mode_set(mode='OBJECT')
for b in arm.data.bones:
    if b.name in ("root", "Armature"):
        b.use_deform = False
bpy.ops.object.select_all(action='DESELECT'); m.select_set(True); bpy.context.view_layer.objects.active = m
nv = len(me.vertices)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.0005); bpy.ops.object.mode_set(mode='OBJECT')
print("RIG| weld %d -> %d verts" % (nv, len(me.vertices)))
bpy.ops.object.select_all(action='DESELECT'); m.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
weighted = [v for v in me.vertices if v.groups]; lonely = [v for v in me.vertices if not v.groups]
if lonely and weighted:
    kd = kdtree.KDTree(len(weighted))
    for i, v in enumerate(weighted):
        kd.insert(v.co, i)
    kd.balance()
    for v in lonely:
        _, i, _ = kd.find(v.co)
        for g in weighted[i].groups:
            m.vertex_groups[g.group].add([v.index], g.weight, 'REPLACE')
names = {g.index: g.name for g in m.vertex_groups}; dom = {}
for v in me.vertices:
    g = max(v.groups, key=lambda g: g.weight, default=None); n = names[g.group] if g else None; dom[n] = dom.get(n, 0) + 1
print("RIG| verts %d lonely_filled %d groups %d unweighted %d" % (
    len(me.vertices), len(lonely), len(m.vertex_groups), sum(1 for v in me.vertices if not v.groups)))
print("RIG| dominant", json.dumps(sorted(dom.items(), key=lambda kv: -kv[1])[:12]))
arm.name = "Armature"; arm.data.name = "Armature"
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("RIG| saved", OUT)
