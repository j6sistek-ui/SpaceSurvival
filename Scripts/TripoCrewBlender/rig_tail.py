"""Give a Tripo character's tail (Crest) a real bone chain. Headless Blender, CPU only.

  blender -b <normalised>.blend -P rig_tail.py -- <out>.blend

Tripo's auto-rig has no tail, so Crest's whip tail was weighted to the pelvis and swung as one rigid piece.
Measured on Crest (1.78 m): from the curled tip (behind the right heel, ~7 cm off the floor) the tail runs
~1.02 m along its own skin to where it joins the back of the pelvis at belt height; it stays 1.2-3.1 cm wide
the whole way and balloons to 5+ cm the moment it reaches the hips. Every tail vertex is pelvis-dominant.

So: TAIL_BONES bones tail_01 (base) .. tail_NN (tip) under the pelvis, laid along the measured centreline, and
weights by distance ALONG THE TAIL'S OWN SKIN - the method that kept the tentacles and Ember's lower arms
from tearing - with a smooth falloff between neighbours and a short fade into the pelvis at the root. Nothing
past the measured root is touched, so the belt and loincloth keep their weights.

A thin cord beside the tail gets its own chain, tail_cord_01..05 from the pelvis (see the note at the bottom).

The tail is animated in Unreal, not by retargeting (no source clip has a tail): see Scripts/AuthorTripoCrewTail.py.
"""
import bmesh
import bpy
import heapq
import json
import math
import sys
from mathutils import Vector, kdtree

out = sys.argv[-1]
ATTACH_GEO = 1.00      # tip -> root along the skin, measured (the width jumps at 1.02-1.04)
TAIL_BONES = 8
SIGMA = 0.55           # falloff, in bones
ROOT_FADE = 0.08       # metres inside the tail over which it blends into the pelvis

m = [o for o in bpy.data.objects if o.type == 'MESH'][0]
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
names = {g.index: g.name for g in m.vertex_groups}
W = m.matrix_world
P = [W @ v.co for v in m.data.vertices]
# geodesics on a welded copy (Tripo leaves seams open), mapped back to the real vertices afterwards
bm = bmesh.new(); bm.from_mesh(m.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0008)
bm.verts.ensure_lookup_table()
WP = [W @ v.co for v in bm.verts]
wnb = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
kd = kdtree.KDTree(len(P))
for i, p in enumerate(P):
    kd.insert(p, i)
kd.balance()


def dominant(i):
    v = m.data.vertices[i]
    g = max(v.groups, key=lambda g: g.weight, default=None)
    return names[g.group] if g else ""


wdom = [dominant(kd.find(p)[1]) for p in WP]
# the tip: the lowest pelvis-weighted vertex behind the body (the feet point to -y)
cand = [i for i in range(len(WP)) if wdom[i] == "pelvis" and WP[i].y > 0.15 and WP[i].z < 0.5]
tip = min(cand, key=lambda i: WP[i].z)
G = {tip: 0.0}; h = [(0.0, tip)]
while h:
    d, i = heapq.heappop(h)
    if d > G[i] or d > ATTACH_GEO + 0.05:
        continue
    for j in wnb[i]:
        nd = d + (WP[i] - WP[j]).length
        if nd < G.get(j, 1e9):
            G[j] = nd; heapq.heappush(h, (nd, j))


def centroid(lo, hi):
    mem = [i for i, d in G.items() if lo <= d < hi]
    return sum((WP[i] for i in mem), Vector()) / len(mem), max(
        (WP[i] - sum((WP[k] for k in mem), Vector()) / len(mem)).length for i in mem)


seg = ATTACH_GEO / TAIL_BONES
joints, widths = [], []
for k in range(TAIL_BONES + 1):        # k=0 root ... k=N tip
    g = ATTACH_GEO - k * seg
    c, r = centroid(max(0.0, g - 0.02), max(0.03, g + 0.02))
    joints.append(c); widths.append(round(r, 3))
report = {"tip": [round(c, 3) for c in WP[tip]], "joints": [[round(c, 3) for c in j] for j in joints],
          "band_radius": widths, "tail_verts": sum(1 for d in G.values() if d <= ATTACH_GEO)}

bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
inv = arm.matrix_world.inverted()
BONES = ["tail_%02d" % (k + 1) for k in range(TAIL_BONES)]
prev = eb["pelvis"]
for k, name in enumerate(BONES):
    if name in eb:
        eb.remove(eb[name])
    b = eb.new(name)
    b.head = inv @ joints[k]; b.tail = inv @ joints[k + 1]
    b.parent = prev; b.use_connect = k > 0
    prev = b
bpy.ops.object.mode_set(mode='OBJECT')
for name in BONES:
    if name not in m.vertex_groups:
        m.vertex_groups.new(name=name)

written = 0
for wi, g in G.items():
    if g > ATTACH_GEO:
        continue                       # past the root: belt, hips, loincloth keep what they have
    s = ATTACH_GEO - g                 # metres from the root, along the tail
    t = s / seg                        # in bones
    raw = [math.exp(-(((t - (k + 0.5)) / (SIGMA * 1.6)) ** 2)) for k in range(TAIL_BONES)]
    tot = sum(raw)
    fade = max(0.0, min(1.0, s / ROOT_FADE)); fade = fade * fade * (3 - 2 * fade)
    weights = {BONES[k]: fade * raw[k] / tot for k in range(TAIL_BONES) if raw[k] / tot > 0.02}
    weights["pelvis"] = weights.get("pelvis", 0.0) + (1 - fade)
    tot2 = sum(weights.values())
    for _, ri, _ in kd.find_range(WP[wi], 0.0009):
        v = m.data.vertices[ri]
        for gr in list(v.groups):
            m.vertex_groups[gr.group].remove([ri])
        for name, x in weights.items():
            m.vertex_groups[name].add([ri], x / tot2, 'REPLACE')
        written += 1
report["weighted_verts"] = written

# A second, thinner cord hangs beside the tail: measured on Crest it leaves the right hip at belt height
# (z ~0.80) and hangs 12-15 cm outboard of the tail down to ~0.24 m, as two separate mesh pieces (Tripo broke
# it), weighted to the right thigh - so it swung with the leg while the tail swung on its own. Bolting it to the
# tail chain would swing it on a 12 cm lever, so it gets its own short chain from the pelvis. Its pieces touch
# nothing else, so weighting by projection onto its own chain cannot tear anything.
STRAND_NEAR = 0.20     # a piece counts as the cord when most of it lies this close to the tail chain...
STRAND_OFF_LEG = 0.10  # ...and this far from every leg bone (the loincloth flaps sit on the thighs)...
BELOW_HEM = 0.45      # ...and it hangs below the loincloth: its tatters all end at 0.55 m or higher, the cord at 0.24
STRAND_BONES = 5
chain = [(joints[k], joints[k + 1]) for k in range(TAIL_BONES)]
legs = [(arm.matrix_world @ b.head_local, arm.matrix_world @ b.tail_local) for b in arm.data.bones
        if b.name.startswith(("thigh", "calf", "foot", "ball"))]


def seg_d(p, a, b):
    ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared)); return (p - (a + ab * t)).length, t


names.update({g.index: g.name for g in m.vertex_groups})  # the tail groups are new
island = [-1] * len(m.data.vertices)
eb_ = bmesh.new(); eb_.from_mesh(m.data); eb_.verts.ensure_lookup_table()
count = 0
for v in eb_.verts:
    if island[v.index] >= 0:
        continue
    stack = [v]; island[v.index] = count
    while stack:
        x = stack.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if island[y.index] < 0:
                island[y.index] = count; stack.append(y)
    count += 1
members = {}
for i, k in enumerate(island):
    members.setdefault(k, []).append(i)
cord, pieces = [], []
for k, idx in members.items():
    doms = [dominant(i) for i in idx]
    if len(idx) < 20 or any(d.startswith("tail") for d in doms) or not any(d.startswith("thigh") for d in doms):
        continue
    near = sum(1 for i in idx if min(seg_d(P[i], a, b)[0] for a, b in chain) < STRAND_NEAR)
    off = sum(1 for i in idx if min(seg_d(P[i], a, b)[0] for a, b in legs) > STRAND_OFF_LEG)
    if near >= 0.8 * len(idx) and off >= 0.5 * len(idx) and min(P[i].z for i in idx) < BELOW_HEM:
        cord += idx; pieces.append({"verts": len(idx), "z": [round(min(P[i].z for i in idx), 2), round(max(P[i].z for i in idx), 2)]})
report["cord_pieces"] = pieces
if cord:
    top, low = max(P[i].z for i in cord), min(P[i].z for i in cord)
    step = (top - low) / STRAND_BONES
    cj = []
    for k in range(STRAND_BONES + 1):
        z = top - k * step
        band = [P[i] for i in cord if abs(P[i].z - z) < max(0.03, step / 2)] or [min((P[i] for i in cord), key=lambda p: abs(p.z - z))]
        c = sum(band, Vector()) / len(band); cj.append(Vector((c.x, c.y, z)))
    SB = ["tail_cord_%02d" % (k + 1) for k in range(STRAND_BONES)]
    bpy.ops.object.mode_set(mode='EDIT'); eb = arm.data.edit_bones
    prev = eb["pelvis"]
    for k, name in enumerate(SB):
        if name in eb:
            eb.remove(eb[name])
        b = eb.new(name); b.head = inv @ cj[k]; b.tail = inv @ cj[k + 1]; b.parent = prev; b.use_connect = k > 0; prev = b
    bpy.ops.object.mode_set(mode='OBJECT')
    for name in SB:
        if name not in m.vertex_groups:
            m.vertex_groups.new(name=name)
    for i in cord:
        t = (top - P[i].z) / step
        raw = [math.exp(-(((t - (b + 0.5)) / (SIGMA * 1.6)) ** 2)) for b in range(STRAND_BONES)]
        tot = sum(raw)
        fade = max(0.0, min(1.0, (top - P[i].z) / 0.06)); fade = fade * fade * (3 - 2 * fade)  # the top stays on the hip
        weights = {SB[b]: fade * raw[b] / tot for b in range(STRAND_BONES) if raw[b] / tot > 0.02}
        weights["pelvis"] = weights.get("pelvis", 0.0) + (1 - fade)
        v = m.data.vertices[i]
        for gr in list(v.groups):
            m.vertex_groups[gr.group].remove([i])
        tot2 = sum(weights.values())
        for name, x in weights.items():
            m.vertex_groups[name].add([i], x / tot2, 'REPLACE')
    report["cord_joints"] = [[round(c, 3) for c in j] for j in cj]
# Tripo also leaves a few loose crumbs (tiny separate pieces) sitting on the tail; left on the pelvis they stay
# floating where the tail used to be. Any piece lying within a few cm of the chain goes with the bone it sits on.
CRUMB = 0.05
crumbs = 0
names.update({g.index: g.name for g in m.vertex_groups})  # the cord groups are new too
bones_at = [(BONES[k], a, b) for k, (a, b) in enumerate(chain)]
if cord:
    bones_at += [(SB[k], cj[k], cj[k + 1]) for k in range(STRAND_BONES)]
for k, idx in members.items():
    if any(dominant(i).startswith("tail") for i in idx) or max(P[i].z for i in idx) > 0.85:
        continue                       # already moving, or up at the belt
    hits = [min((seg_d(P[i], a, b)[0], name) for name, a, b in bones_at) for i in idx]
    if max(d for d, _ in hits) > CRUMB:
        continue
    for i, (_, bone) in zip(idx, hits):
        v = m.data.vertices[i]
        for gr in list(v.groups):
            m.vertex_groups[gr.group].remove([i])
        m.vertex_groups[bone].add([i], 1.0, 'REPLACE')
    crumbs += len(idx)
report["crumb_verts"] = crumbs
print("TAIL", json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=out)
