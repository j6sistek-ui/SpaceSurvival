"""Rebuild tentacle weights continuously on an already-rigged octopus body (output of tent_rig2.py).

Fixes three defects the owner circled:
  - ring cracks mid-tentacle: weights came from 3.5 cm geodesic bands, so a tentacle bent in steps. Now each
    vertex is projected onto its own chain's centreline (continuous arc position) and weighted with a smooth
    falloff over neighbouring bones, then smoothed along the tentacle.
  - seam at the hip: the root of each chain fades in from its parent (Pelvis / Clavicle) over 1.5 bones.
  - flat strips between tentacles: Tripo fused touching tentacles; faces joining two different tentacles
    beyond their roots are deleted so no skin is shared between independently moving chains.
"""
import bmesh
import bpy
import json
import math
import re
import sys

out = sys.argv[-1]
SIGMA = 0.75          # bone falloff width, in bones
ROOT_FADE = 1.5       # bones over which a chain fades in from its parent
SMOOTH_ITERS = 6
BRIDGE_MIN_S = 1.5    # faces bridging two tentacles further than this (in bones) from both roots are removed

m = [o for o in bpy.data.objects if o.type == 'MESH'][0]
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
W = m.matrix_world
A = arm.matrix_world
chains = {}
for b in arm.data.bones:
    mm = re.match(r"((?:Tent\d+)|(?:[LR]ArmTent\d+))_(\d+)$", b.name)
    if mm:
        chains.setdefault(mm.group(1), {})[int(mm.group(2))] = b
NB = max(len(c) for c in chains.values())
parent_of = {c: ("Pelvis" if c.startswith("Tent") else c[0] + "_Clavicle") for c in chains}
segs = {c: [(A @ ch[i].head_local, A @ ch[i].tail_local) for i in range(NB)] for c, ch in chains.items()}
gidx = {g.name: g.index for g in m.vertex_groups}
gname = {g.index: g.name for g in m.vertex_groups}

# label = chain owning the largest share of the vertex's chain weight
n = len(m.data.vertices)
label = [None] * n
for v in m.data.vertices:
    best = {}
    for g in v.groups:
        mm = re.match(r"(.+)_\d+$", gname[g.group])
        if mm and mm.group(1) in chains:
            best[mm.group(1)] = best.get(mm.group(1), 0) + g.weight
    if best:
        c = max(best, key=best.get)
        if best[c] > 0.3:
            label[v.index] = c


def project(c, p):
    bestd, bests = 1e9, 0.0
    for k, (a, b) in enumerate(segs[c]):
        ab = b - a
        t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-12)))
        d = (a + ab * t - p).length
        if d < bestd:
            bestd, bests = d, k + t
    return bests


def dist_to(c, p):
    best = 1e9
    for a, b in segs[c]:
        ab = b - a
        t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-12)))
        best = min(best, (a + ab * t - p).length)
    return best


# a vertex far from its own chain was mislabelled (fused neighbour): give it the nearest chain of the same kind
relabelled = 0
for v in m.data.vertices:
    c = label[v.index]
    if c is None:
        continue
    p = W @ v.co
    own = dist_to(c, p)
    if True:  # disabled: chain centrelines of fused tentacles sit off the skin, distance is not a label test
        continue
    kind = c.startswith("Tent")
    cands = [k for k in chains if k.startswith("Tent") == kind]
    best = min(cands, key=lambda k: dist_to(k, p))
    if best != c and dist_to(best, p) < 0.06:
        label[v.index] = best; relabelled += 1
print("RELABEL", relabelled)

# islands: a patch labelled chain C that is not connected (within C) to C's root is a piece of a neighbour
# tentacle Tripo fused on. It moves to whichever chain it borders most.
adj = [[] for _ in range(n)]
for e in m.data.edges:
    a, b = e.vertices
    adj[a].append(b); adj[b].append(a)
islands_moved = 0
for _ in range(3):
    seen = [False] * n
    changed = 0
    for c in chains:
        root_pts = {v.index for v in m.data.vertices if label[v.index] == c and project(c, W @ v.co) < 1.0}
        comp_id = {}
        comps = []
        for sv in [i for i in range(n) if label[i] == c]:
            if sv in comp_id:
                continue
            st = [sv]; comp_id[sv] = len(comps); mem = []
            while st:
                a = st.pop(); mem.append(a)
                for b in adj[a]:
                    if label[b] == c and b not in comp_id:
                        comp_id[b] = len(comps); st.append(b)
            comps.append(mem)
        for mem in comps:
            if any(i in root_pts for i in mem):
                continue
            border = {}
            for a in mem:
                for b in adj[a]:
                    if label[b] is not None and label[b] != c:
                        border[label[b]] = border.get(label[b], 0) + 1
            if not border:
                continue
            new = max(border, key=border.get)
            for a in mem:
                label[a] = new
            changed += 1; islands_moved += len(mem)
    if not changed:
        break
print("ISLANDS", islands_moved)

# continuous weights
# arc position = geodesic distance along this chain's own skin from its root, scaled to bones.
# Neighbouring vertices therefore can never sit at very different positions along the chain: no tears.
import heapq
spos = [0.0] * n
wvec = [None] * n
Pw = [W @ v.co for v in m.data.vertices]
for c in chains:
    mem = [i for i in range(n) if label[i] == c]
    if not mem:
        continue
    proj = {i: project(c, Pw[i]) for i in mem}
    seeds = [i for i in mem if proj[i] < 0.35]
    if not seeds:
        seeds = sorted(mem, key=lambda i: proj[i])[:20]
    D = {i: 0.0 for i in seeds}
    h = [(0.0, i) for i in seeds]
    while h:
        d, i = heapq.heappop(h)
        if d > D.get(i, 1e9):
            continue
        for j in adj[i]:
            if label[j] == c:
                nd = d + (Pw[i] - Pw[j]).length
                if nd < D.get(j, 1e9):
                    D[j] = nd; heapq.heappush(h, (nd, j))
    length = sum((b - a).length for a, b in segs[c])
    for i in mem:
        spos[i] = min(NB - 0.01, 0.35 + D.get(i, length) / length * NB) if i in D else proj[i]
for v in m.data.vertices:
    c = label[v.index]
    if c is None:
        continue
    s = spos[v.index]
    raw = {}
    for k in range(NB):
        raw["%s_%d" % (c, k)] = math.exp(-((s - (k + 0.5)) / SIGMA) ** 2)
    tot = sum(raw.values())
    fade = min(1.0, s / ROOT_FADE)
    fade = fade * fade * (3 - 2 * fade)
    w = {k: fade * x / tot for k, x in raw.items() if x / tot > 0.02}
    w[parent_of[c]] = w.get(parent_of[c], 0) + (1 - fade)
    wvec[v.index] = w

# smooth along the tentacle (same-label neighbours only), keeps chains independent
nbr = [[] for _ in range(n)]
for e in m.data.edges:
    a, b = e.vertices
    nbr[a].append(b); nbr[b].append(a)
for _ in range(SMOOTH_ITERS):
    new = list(wvec)
    for i in range(n):
        if wvec[i] is None:
            continue
        acc = dict((k, 0.5 * x) for k, x in wvec[i].items())
        same = [j for j in nbr[i] if label[j] == label[i] and wvec[j] is not None]
        if same:
            f = 0.5 / len(same)
            for j in same:
                for k, x in wvec[j].items():
                    acc[k] = acc.get(k, 0) + f * x
        else:
            acc = dict(wvec[i])
        tot = sum(acc.values())
        new[i] = {k: x / tot for k, x in acc.items()}
    wvec = new

for i in range(n):
    if wvec[i] is None:
        continue
    v = m.data.vertices[i]
    for g in list(v.groups):
        m.vertex_groups[g.group].remove([i])
    top = sorted(wvec[i].items(), key=lambda kv: -kv[1])[:4]
    tot = sum(x for _, x in top)
    for k, x in top:
        m.vertex_groups[gidx[k]].add([i], x / tot, 'REPLACE')

# hip ring: unlabelled vertices touching labelled ones blend half-way, so the waistline has no hard edge
hip = 0
for i in range(n):
    if label[i] is not None:
        continue
    lab = [j for j in nbr[i] if label[j] is not None and label[j].startswith("Tent")]
    if not lab:
        continue
    v = m.data.vertices[i]
    acc = {}
    for g in v.groups:
        acc[gname[g.group]] = 0.5 * g.weight
    for j in lab:
        for k, x in wvec[j].items():
            acc[k] = acc.get(k, 0) + 0.5 * x / len(lab)
    for g in list(v.groups):
        m.vertex_groups[g.group].remove([i])
    tot = sum(acc.values())
    for k, x in sorted(acc.items(), key=lambda kv: -kv[1])[:4]:
        m.vertex_groups[gidx[k]].add([i], x / tot, 'REPLACE')
    hip += 1

# remove skin shared by two different tentacles away from their roots
bm = bmesh.new(); bm.from_mesh(m.data); bm.faces.ensure_lookup_table()
kill = []
for f in bm.faces:
    labs = {label[v.index] for v in f.verts}
    if len(labs) > 1 and None not in labs and min(spos[v.index] for v in f.verts) > BRIDGE_MIN_S:
        kill.append(f)
bmesh.ops.delete(bm, geom=kill, context='FACES')
loose = [v for v in bm.verts if not v.link_faces]
bmesh.ops.delete(bm, geom=loose, context='VERTS')
bm.to_mesh(m.data); m.data.update(); bm.free()

print("TENTSMOOTH", json.dumps({"chains": len(chains), "weighted": sum(1 for x in wvec if x), "hip_blended": hip,
                                "bridge_faces_removed": len(kill), "verts": len(m.data.vertices)}))
bpy.ops.wm.save_as_mainfile(filepath=out)
