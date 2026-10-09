"""Give a four-armed Tripo character (Ember) real bones for its second pair of arms. Headless Blender, CPU only.

  blender -b <normalised>.blend -P rig_lower_arms.py -- <out>.blend

Tripo's auto-rig has one pair of arms, so Ember's lower pair was weighted to the spine and rode with the torso.
Measured on Ember (1.78 m): each lower arm runs ~58 cm along the skin from fingertip to where it meets the
torso at ~1.14 m beside spine_02 - claw hand 0-22 cm (widening to 6 cm), forearm+upper arm 22-56 cm (a steady
~3.5 cm), torso beyond 60 cm (7-13 cm). Each lower arm gets upperarm_low / lowerarm_low / hand_low under
spine_02, laid along the measured centreline, and is weighted by distance ALONG ITS OWN SKIN (the method that
fixed the tentacles: neighbouring vertices cannot land on far-apart bones, so nothing tears), with a smooth
falloff between bones and a fade into spine_02 at the shoulder.

The arms are animated by retargeting, not keys: IK_<Name> gets LeftArmLower/RightArmLower chains and the
retargeters map the source LeftArm/RightArm onto them as well, so every clip drives all four arms.
"""
import bmesh
import bpy
import heapq
import json
import math
import sys
from mathutils import Vector, kdtree

out = sys.argv[-1]
ATTACH_GEO = 0.58      # fingertip -> shoulder, measured
WRIST_GEO = 0.22       # fingertip -> wrist, measured
SIGMA = 0.55           # bone falloff, in bones
ROOT_FADE = 0.06       # metres along the arm over which it fades into the torso

m = [o for o in bpy.data.objects if o.type == 'MESH'][0]
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
names = {g.index: g.name for g in m.vertex_groups}
W = m.matrix_world
P = [W @ v.co for v in m.data.vertices]
n = len(P)
# geodesics run on a welded copy (Tripo leaves seams open), then map back to the real vertices
bm = bmesh.new(); bm.from_mesh(m.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0008)
bm.verts.ensure_lookup_table()
WP = [W @ v.co for v in bm.verts]
wnb = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
kd = kdtree.KDTree(n)
for i, p in enumerate(P):
    kd.insert(p, i)
kd.balance()
wkd = kdtree.KDTree(len(WP))
for i, p in enumerate(WP):
    wkd.insert(p, i)
wkd.balance()


def dominant(i):
    v = m.data.vertices[i]
    g = max(v.groups, key=lambda g: g.weight, default=None)
    return names[g.group] if g else ""


wdom = [dominant(kd.find(p)[1]) for p in WP]
report = {}
chains = {}
for side, sg in (("l", 1), ("r", -1)):
    cand = [i for i in range(len(WP)) if wdom[i].startswith("spine") and sg * WP[i].x > 0.18 and WP[i].z < 1.05]
    tip = min(cand, key=lambda i: WP[i].z)
    G = {tip: 0.0}; h = [(0.0, tip)]
    while h:
        d, i = heapq.heappop(h)
        if d > G[i]:
            continue
        for j in wnb[i]:
            if wdom[j].startswith("spine"):
                nd = d + (WP[i] - WP[j]).length
                if nd < G.get(j, 1e9):
                    G[j] = nd; heapq.heappush(h, (nd, j))

    def centroid(lo, hi):
        mem = [i for i, d in G.items() if lo <= d < hi]
        return sum((WP[i] for i in mem), Vector()) / len(mem)
    shoulder = centroid(ATTACH_GEO - 0.03, ATTACH_GEO + 0.01)
    wrist = centroid(WRIST_GEO - 0.02, WRIST_GEO + 0.02)
    elbow = centroid((ATTACH_GEO + WRIST_GEO) / 2 - 0.02, (ATTACH_GEO + WRIST_GEO) / 2 + 0.02)
    hand_end = centroid(0.06, 0.10)
    joints = [shoulder, elbow, wrist, hand_end]
    chains[side] = (joints, G)
    report[side] = {"tip": [round(c, 3) for c in WP[tip]], "joints": [[round(c, 3) for c in j] for j in joints],
                    "region_verts": sum(1 for d in G.values() if d < ATTACH_GEO + ROOT_FADE)}

# bones
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
inv = arm.matrix_world.inverted()
BONES = ("upperarm_low_", "lowerarm_low_", "hand_low_")
for side, (joints, _) in chains.items():
    prev = eb["spine_02"]
    for k, stem in enumerate(BONES):
        name = stem + side
        if name in eb:
            eb.remove(eb[name])
        b = eb.new(name)
        b.head = inv @ joints[k]; b.tail = inv @ joints[k + 1]
        b.parent = prev; b.use_connect = k > 0
        prev = b
bpy.ops.object.mode_set(mode='OBJECT')
for side in chains:
    for stem in BONES:
        if (stem + side) not in m.vertex_groups:
            m.vertex_groups.new(name=stem + side)

# weights: arm position s (metres from the shoulder, along the skin) -> bone index, smooth falloff
seg = {}
for side, (joints, _) in chains.items():
    seg[side] = [ATTACH_GEO - g for g in (ATTACH_GEO, (ATTACH_GEO + WRIST_GEO) / 2, WRIST_GEO, 0.0)]
written = 0
for side, (joints, G) in chains.items():
    edges = seg[side]  # s at shoulder, elbow, wrist, tip
    centres = [(edges[k] + edges[k + 1]) / 2 for k in range(3)]
    widths = [edges[k + 1] - edges[k] for k in range(3)]
    for wi, g in G.items():
        s = ATTACH_GEO - g
        if s < -ROOT_FADE:
            continue
        raw = [math.exp(-(((s - centres[k]) / (widths[k] * SIGMA * 1.6)) ** 2)) for k in range(3)]
        tot = sum(raw)
        fade = max(0.0, min(1.0, (s + ROOT_FADE) / (2 * ROOT_FADE)))
        fade = fade * fade * (3 - 2 * fade)
        weights = {BONES[k] + side: fade * raw[k] / tot for k in range(3) if raw[k] / tot > 0.02}
        weights["spine_02"] = weights.get("spine_02", 0.0) + (1 - fade)
        # every real vertex sitting on this welded vertex gets the same weights
        for _, ri, _ in kd.find_range(WP[wi], 0.0009):
            v = m.data.vertices[ri]
            for gr in list(v.groups):
                m.vertex_groups[gr.group].remove([ri])
            tot2 = sum(weights.values())
            for name, x in weights.items():
                m.vertex_groups[name].add([ri], x / tot2, 'REPLACE')
            written += 1
report["weighted_verts"] = written
print("LOWERARMS", json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=out)
