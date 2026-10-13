"""Octopus-bodied crew rig, v2.

Every tentacle - the lower ones and each arm tentacle on its own - gets an 8-bone chain laid down its
centreline. Centrelines come from a Reeb graph: geodesic distance bands from a seed, split into connected
pieces per band, linked band to band. Each vertex is weighted to its own tentacle's chain only.

Tripo fused touching tentacles into one surface, so the faces bridging two tentacles would stretch into
sheets once they move apart. Edges whose two ends belong to different tentacles are split (beyond the root
fifth of each tentacle, so roots stay sewn to the body): every tentacle becomes its own piece of skin.
"""
import bmesh
import bpy
import heapq
import json
import sys
from mathutils import Vector

out = sys.argv[-1]
BW = 0.035
NB = 8
CHAIN_TOP_Z = 0.80
LOWER_Z = 0.86
ARM_PARTS = ('Upperarm', 'Forearm', 'Hand', 'Thumb', 'Index', 'Mid', 'Ring', 'Pinky', 'Elbow')

m = [o for o in bpy.data.objects if o.type == 'MESH'][0]
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
bm = bmesh.new(); bm.from_mesh(m.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0008)
bm.to_mesh(m.data); m.data.update(); bm.free()
bm = bmesh.new(); bm.from_mesh(m.data); bm.verts.ensure_lookup_table()
W = m.matrix_world
P = [W @ v.co for v in bm.verts]
n = len(P)
nb = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
bm.free()
gname = {g.index: g.name for g in m.vertex_groups}


def side_arm_weight(i, side):
    return sum(g.weight for g in m.data.vertices[i].groups
               if gname[g.group].startswith(side + '_') and any(a in gname[g.group] for a in ARM_PARTS))


def reeb(allowed, seed_pt, seed_r, min_len, keep):
    """Branch centrelines inside the vertex set `allowed`, grown from vertices near seed_pt."""
    D = {}
    h = []
    for s in allowed:
        if (P[s] - seed_pt).length < seed_r:
            D[s] = 0.0; heapq.heappush(h, (0.0, s))
    while h:
        d, i = heapq.heappop(h)
        if d > D.get(i, 1e9):
            continue
        for j in nb[i]:
            if j in allowed:
                nd = d + (P[i] - P[j]).length
                if nd < D.get(j, 1e9):
                    D[j] = nd; heapq.heappush(h, (nd, j))
    band = {i: int(d / BW) for i, d in D.items()}
    node_of = {}
    nodes = []
    for i in D:
        if i in node_of:
            continue
        b = band[i]; st = [i]; node_of[i] = len(nodes); mem = []
        while st:
            a = st.pop(); mem.append(a)
            for j in nb[a]:
                if j in band and j not in node_of and band[j] == b:
                    node_of[j] = len(nodes); st.append(j)
        nodes.append({"band": b, "c": sum((P[k] for k in mem), Vector()) / len(mem), "n": len(mem)})
    links = {}
    for i in D:
        for j in nb[i]:
            if j in node_of:
                a, b = node_of[i], node_of[j]
                if nodes[b]["band"] == nodes[a]["band"] + 1:
                    links.setdefault(b, {}).setdefault(a, 0); links[b][a] += 1
    par = {b: max(ps, key=ps.get) for b, ps in links.items()}
    kids = set(par.values())

    def path(x):
        p = [x]
        while p[-1] in par:
            p.append(par[p[-1]])
        return p[::-1]

    def L(p):
        return sum((nodes[p[k]]["c"] - nodes[p[k - 1]]["c"]).length for k in range(1, len(p)))

    paths = sorted([path(x) for x in range(len(nodes)) if x not in kids and nodes[x]["n"] >= 4], key=lambda p: -L(p))
    chosen, owned = [], {}
    for p in paths:
        if L(p) < min_len:
            continue
        k = 0
        while k < len(p) and p[k] in owned:
            k += 1
        seg = p[max(0, k - 1):]
        if L(seg) > min_len * 0.8:
            for x in p:
                owned.setdefault(x, len(chosen))
            chosen.append(seg)
    segs = [s for s in (keep(s, nodes, L) for s in chosen) if s]
    return nodes, node_of, par, segs, L


def chain_points(seg, nodes):
    a = [0.0]
    for k in range(1, len(seg)):
        a.append(a[-1] + (nodes[seg[k]]["c"] - nodes[seg[k - 1]]["c"]).length)

    def at(s):
        for k in range(1, len(seg)):
            if a[k] >= s:
                t = (s - a[k - 1]) / max(a[k] - a[k - 1], 1e-9)
                return nodes[seg[k - 1]]["c"].lerp(nodes[seg[k]]["c"], t)
        return nodes[seg[-1]]["c"]
    return [at(a[-1] * i / NB) for i in range(NB + 1)], a


tentacles = []   # (bone prefix, parent bone, seg, nodes, node_of, par)

# lower tentacles
pel = arm.matrix_world @ arm.data.bones['Pelvis'].head_local
ARMX = 0.135
def in_arm(i, side):
    x = P[i].x if side == 'L' else -P[i].x
    return x > ARMX and 0.70 < P[i].z < 1.55 and (side_arm_weight(i, side) > 0.2 or x > 0.2)
lower = {i for i in range(n) if P[i].z <= 1.10 and not in_arm(i, 'L') and not in_arm(i, 'R')}


def keep_lower(seg, nodes, L):
    pts = [nodes[x]["c"] for x in seg]
    if pts[-1].z > 0.45:
        return None
    k0 = next((k for k, p in enumerate(pts) if p.z < CHAIN_TOP_Z), None)
    if k0 is None or L(seg[k0:]) < 0.30:
        return None
    return seg[k0:]


nodes, node_of, par, segs, _ = reeb(lower, pel, 0.12, 0.35, keep_lower)
for s in segs:
    tentacles.append(("Tent%02d" % len(tentacles), "Pelvis", s, nodes, node_of, par))
lower_count = len(tentacles)

# arm tentacles, each side separately: tips of the geodesic field, traced back by steepest descent.
# (The two arm tentacles per side run parallel and touch, so band slicing sees them as one.)
arm_paths = []   # (prefix, parent, [points], vertex set)
for side in ('L', 'R'):
    allowed = {i for i in range(n) if in_arm(i, side)}
    root = arm.matrix_world @ arm.data.bones[side + '_Upperarm'].head_local
    D = {}; h = []
    for s0 in allowed:
        if (P[s0] - root).length < 0.10:
            D[s0] = 0.0; heapq.heappush(h, (0.0, s0))
    while h:
        d, i = heapq.heappop(h)
        if d > D.get(i, 1e9):
            continue
        for j in nb[i]:
            if j in allowed:
                nd = d + (P[i] - P[j]).length
                if nd < D.get(j, 1e9):
                    D[j] = nd; heapq.heappush(h, (nd, j))
    tips = []
    for i in sorted(D, key=lambda i: -D[i]):
        if D[i] < 0.30:
            break
        if all((P[i] - P[t]).length > 0.25 for t in tips):
            tips.append(i)
        if len(tips) == 2:
            break
    for k, tip in enumerate(tips):
        pathv = [tip]
        while D[pathv[-1]] > 0.03:
            cur = pathv[-1]
            nxt = min((j for j in nb[cur] if j in D), key=lambda j: D[j], default=None)
            if nxt is None or D[nxt] >= D[cur]:
                break
            pathv.append(nxt)
        pts = [P[i] for i in reversed(pathv)]
        # pull the surface path toward the tentacle axis: average each point with nearby allowed vertices
        axis = []
        for p in pts[::3] + [pts[-1]]:
            near = [P[j] for j in allowed if (P[j] - p).length < 0.035]
            axis.append(sum(near, Vector()) / len(near) if near else p)
        print('ARMTIP', side, k, [round(c, 2) for c in P[tip]], 'geo', round(D[tip], 2), 'pts', len(axis))
        arm_paths.append(("%sArmTent%d" % (side, k), side + "_Clavicle", axis, allowed))

# bones
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
inv = arm.matrix_world.inverted()
arcs = []
for prefix, parent, seg, nodes, _, _ in tentacles:
    pts, a = chain_points(seg, nodes)
    arcs.append(a)
    prev = eb[parent]
    for i in range(NB):
        b = eb.new("%s_%d" % (prefix, i))
        b.head = inv @ pts[i]; b.tail = inv @ pts[i + 1]
        b.parent = prev; b.use_connect = (i > 0); prev = b
def resample(pts):
    a = [0.0]
    for k in range(1, len(pts)):
        a.append(a[-1] + (pts[k] - pts[k - 1]).length)
    def at(sv):
        for k in range(1, len(pts)):
            if a[k] >= sv:
                t = (sv - a[k - 1]) / max(a[k] - a[k - 1], 1e-9)
                return pts[k - 1].lerp(pts[k], t)
        return pts[-1]
    return [at(a[-1] * i / NB) for i in range(NB + 1)]
arm_chain_pts = []
for prefix, parent, pts, _ in arm_paths:
    cp = resample(pts); arm_chain_pts.append(cp)
    prev = eb[parent]
    for i in range(NB):
        b = eb.new("%s_%d" % (prefix, i)); b.head = inv @ cp[i]; b.tail = inv @ cp[i + 1]
        b.parent = prev; b.use_connect = (i > 0); prev = b
bpy.ops.object.mode_set(mode='OBJECT')
for prefix, *_ in arm_paths:
    for i in range(NB):
        m.vertex_groups.new(name="%s_%d" % (prefix, i))
for prefix, *_ in tentacles:
    for i in range(NB):
        m.vertex_groups.new(name="%s_%d" % (prefix, i))

# weights: each vertex follows the tentacle segment its geodesic band piece belongs to
label = [-1] * n
arcpos = [0.0] * n
pg = m.vertex_groups['Pelvis']
for t, (prefix, parent, seg, nodes, node_of, par) in enumerate(tentacles):
    a = arcs[t]
    pos = {x: a[k] / max(a[-1], 1e-9) for k, x in enumerate(seg)}
    for i, x in node_of.items():
        if t < lower_count and (P[i].z > LOWER_Z):
            continue
        y = x; hops = 0
        while y not in pos and y in par and hops < 400:
            y = par[y]; hops += 1
        if y not in pos:
            continue
        if label[i] >= 0:
            continue
        label[i] = t; arcpos[i] = pos[y]
# unlabelled lower vertices inherit the tentacle of their nearest labelled neighbour along the surface
front = [i for i in range(n) if label[i] >= 0]
while front:
    nxt = []
    for i in front:
        for j in nb[i]:
            if label[j] < 0 and j in lower and P[j].z <= CHAIN_TOP_Z:
                label[j] = label[i]; arcpos[j] = arcpos[i]; nxt.append(j)
    front = nxt
for i in range(n):
    t = label[i]
    v = m.data.vertices[i]
    if t < 0:
        if P[i].z <= CHAIN_TOP_Z and i in lower:
            for g in list(v.groups):
                m.vertex_groups[g.group].remove([i])
            pg.add([i], 1.0, 'REPLACE')
        continue
    prefix, parent = tentacles[t][0], tentacles[t][1]
    for g in list(v.groups):
        m.vertex_groups[g.group].remove([i])
    f = arcpos[i] * NB - 0.5
    if f < 0:
        m.vertex_groups["%s_0" % prefix].add([i], 0.6, 'REPLACE')
        m.vertex_groups[parent].add([i], 0.4, 'REPLACE')
        continue
    i0 = min(NB - 1, int(f)); w = f - int(f) if i0 < NB - 1 else 0.0
    m.vertex_groups["%s_%d" % (prefix, i0)].add([i], 1 - w, 'REPLACE')
    if w > 0:
        m.vertex_groups["%s_%d" % (prefix, i0 + 1)].add([i], w, 'REPLACE')

def nearest_on(cp, p):
    best = (1e9, 0.0)
    for k in range(NB):
        a, b = cp[k], cp[k + 1]; ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-12)))
        d = (a + ab * t - p).length
        if d < best[0]:
            best = (d, (k + t) / NB)
    return best
side_groups = {}
for idx, (prefix, parent, pts, allowed) in enumerate(arm_paths):
    side_groups.setdefault(prefix[0], []).append(idx)
for side, idxs in side_groups.items():
    for i in arm_paths[idxs[0]][3]:
        best = min(((nearest_on(arm_chain_pts[q], P[i]), q) for q in idxs), key=lambda r: r[0][0])
        (d, s_), q = best
        prefix, parent = arm_paths[q][0], arm_paths[q][1]
        v = m.data.vertices[i]
        for g in list(v.groups):
            m.vertex_groups[g.group].remove([i])
        label[i] = 1000 + q; arcpos[i] = s_
        f = s_ * NB - 0.5
        if f < 0:
            m.vertex_groups["%s_0" % prefix].add([i], 0.5, 'REPLACE'); m.vertex_groups[parent].add([i], 0.5, 'REPLACE'); continue
        i0 = min(NB - 1, int(f)); w = f - int(f) if i0 < NB - 1 else 0.0
        m.vertex_groups["%s_%d" % (prefix, i0)].add([i], 1 - w, 'REPLACE')
        if w > 0:
            m.vertex_groups["%s_%d" % (prefix, i0 + 1)].add([i], w, 'REPLACE')

# clean-up: a vertex whose neighbours mostly belong to another tentacle joins it (kills spikes and plates)
def chain_of(t):
    return (tentacles[t][0], tentacles[t][1]) if t < 1000 else (arm_paths[t - 1000][0], arm_paths[t - 1000][1])
def write(i):
    prefix, parent = chain_of(label[i]); v = m.data.vertices[i]
    for g in list(v.groups):
        m.vertex_groups[g.group].remove([i])
    f = arcpos[i] * NB - 0.5
    if f < 0:
        m.vertex_groups["%s_0" % prefix].add([i], 0.6, 'REPLACE'); m.vertex_groups[parent].add([i], 0.4, 'REPLACE'); return
    i0 = min(NB - 1, int(f)); w = f - int(f) if i0 < NB - 1 else 0.0
    m.vertex_groups["%s_%d" % (prefix, i0)].add([i], 1 - w, 'REPLACE')
    if w > 0:
        m.vertex_groups["%s_%d" % (prefix, i0 + 1)].add([i], w, 'REPLACE')
flipped = 0
for _ in range(4):
    changes = []
    for i in range(n):
        if label[i] < 0:
            continue
        cnt = {}
        for j in nb[i]:
            if label[j] >= 0:
                cnt[label[j]] = cnt.get(label[j], 0) + 1
        if not cnt:
            continue
        best = max(cnt, key=cnt.get)
        if best != label[i] and cnt[best] >= 0.6 * len(nb[i]):
            ap = [arcpos[j] for j in nb[i] if label[j] == best]
            changes.append((i, best, sum(ap) / len(ap)))
    for i, b, a in changes:
        label[i] = b; arcpos[i] = a; write(i)
    flipped += len(changes)
print('CLEANUP flipped', flipped)

# split the skin between different tentacles (past the root fifth), so fused contacts separate cleanly
bm = bmesh.new(); bm.from_mesh(m.data); bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
cut = [e for e in bm.edges
       if label[e.verts[0].index] >= 0 and label[e.verts[1].index] >= 0
       and label[e.verts[0].index] != label[e.verts[1].index]
       and arcpos[e.verts[0].index] > 0.2 and arcpos[e.verts[1].index] > 0.2]
bmesh.ops.split_edges(bm, edges=cut)
bm.to_mesh(m.data); m.data.update(); bm.free()

print("TENTRIG2", json.dumps({"lower": lower_count, "arm": [a[0] for a in arm_paths],
                              "labelled": sum(1 for x in label if x >= 0), "cut_edges": len(cut),
                              "verts_after": len(m.data.vertices)}))
bpy.ops.wm.save_as_mainfile(filepath=out + ".blend")
