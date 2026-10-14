"""The owner's brow ring placement, carried to her neutral face (what the game shows).

  blender -b --factory-startup --python ring_placement_from_blend.py -- <owner's .blend with BrowRing> <joy_ring_placement.json>
  then: author_soft_tissue.py ... --piercing --ring-transform joy_ring_placement.json

Works on any .blend made by author_soft_tissue.py --save-blend (or a copy the owner edited): it reads the ring and her
body exactly as they are displayed, so whatever key values the file carries, the placement is the one the owner saw.

In the owner's saved what-if file the ring was displayed with all of its copied face keys at 1.0 (Blender 5.2 gives a
new key the value 1.0) and her body with the pack's shipped expression (13 face keys at 0.1-1.0). The owner placed the
ring against that view. Here: the ring AS SEEN (evaluated) is carried by the local rigid motion of the skin patch under it,
from the body as seen to the body at rest with every key at 0, then expressed as M_ring_local_cm: the 4x4 (Joy-local cm)
that takes the canonical ring (centre at the origin, ring plane X-Y, wire axis Z, the recipe's own vertex order) to that
neutral placement."""
import json, math, sys
import bpy
import numpy as np

owner_blend, out = sys.argv[sys.argv.index("--") + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=owner_blend, load_ui=False)
dg = bpy.context.evaluated_depsgraph_get()
body, ring, rig = bpy.data.objects["CC_Base_Body"], bpy.data.objects["BrowRing"], bpy.data.objects["Armature"]
assert rig.data.pose_position == "REST"
BW = np.array(body.matrix_world)
BWi = np.linalg.inv(BW)


def local(Pw):
    return (BWi @ np.c_[Pw, np.ones(len(Pw))].T).T[:, :3]


def evaluated_world(o):
    ev = o.evaluated_get(dg)
    m = ev.to_mesh()
    W = np.array(ev.matrix_world)
    V = np.array([v.co[:] for v in m.vertices])
    ev.to_mesh_clear()
    return (W @ np.c_[V, np.ones(len(V))].T).T[:, :3]


ring_seen = local(evaluated_world(ring))                  # cm, as the owner saw it
body_seen = local(evaluated_world(body))                  # her face with the shipped expression
body_rest = np.array([p.co[:] for p in body.data.shape_keys.key_blocks[0].data])  # Basis, every key at 0 (= game)
assert body_seen.shape == body_rest.shape
# body object-local cm == Joy-local cm (the recipe's frame); check the basis is the data
assert np.abs(body_rest - np.array([v.co[:] for v in body.data.vertices])).max() < 1e-4

c_seen = ring_seen.mean(0)
d = np.linalg.norm(body_seen - c_seen, axis=1)
patch = d < 2.5
w = np.exp(-0.5 * (d[patch] / 1.0) ** 2)


def kabsch(A, B, wt=None):
    wt = np.ones(len(A)) if wt is None else wt
    ca, cb = (A * wt[:, None]).sum(0) / wt.sum(), (B * wt[:, None]).sum(0) / wt.sum()
    H = ((A - ca) * wt[:, None]).T @ (B - cb)
    U, _, Vt = np.linalg.svd(H)
    dd = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1, 1, dd]) @ U.T
    T = np.eye(4); T[:3, :3] = R; T[:3, 3] = cb - R @ ca
    return T


T_skin = kabsch(body_seen[patch], body_rest[patch], w)
ring_rest = (T_skin @ np.c_[ring_seen, np.ones(len(ring_seen))].T).T[:, :3]
skin_fit_res = np.linalg.norm((T_skin @ np.c_[body_seen[patch], np.ones(patch.sum())].T).T[:, :3] - body_rest[patch], axis=1)

# the canonical ring, exactly as add_brow_ring builds it, with n = X, up = Y (wire axis Z = cross(X, Y))
R_, r_, seg, wseg = 0.5, 0.09, 32, 10
can = []
for i in range(seg):
    a = 2 * math.pi * i / seg
    c = R_ * np.array([math.cos(a), math.sin(a), 0.0])
    radial = c / R_
    for j in range(wseg):
        b = 2 * math.pi * j / wseg
        can.append(c + r_ * (math.cos(b) * radial + math.sin(b) * np.array([0.0, 0.0, 1.0])))
can = np.array(can)
assert len(can) == len(ring_rest), (len(can), len(ring_rest))
M = kabsch(can, ring_rest)
res = np.linalg.norm((M @ np.c_[can, np.ones(len(can))].T).T[:, :3] - ring_rest, axis=1)

# where it sits on her: nearest neutral skin to the ring centre, and how far the expression had moved that skin
from mathutils.bvhtree import BVHTree
from mathutils import Vector
faces = [tuple(p.vertices) for p in body.data.polygons]
bvh_rest = BVHTree.FromPolygons([tuple(v) for v in body_rest.tolist()], faces, all_triangles=False)
bvh_seen = BVHTree.FromPolygons([tuple(v) for v in body_seen.tolist()], faces, all_triangles=False)
cr = ring_rest.mean(0)
loc_r, n_r, _, dist_r = bvh_rest.find_nearest(Vector(cr))
loc_s, n_s, _, dist_s = bvh_seen.find_nearest(Vector(c_seen))
rep = {"source": owner_blend, "method": "owner's ring as seen (keys as saved), carried by the weighted rigid motion of the skin within 2.5 cm "
       "(sigma 1 cm) from her shipped expression to every key at 0, then fitted to the canonical ring",
       "M_ring_local_cm": M.tolist(),
       "ring_centre_seen_cm": c_seen.tolist(), "ring_centre_neutral_cm": cr.tolist(),
       "skin_shift_mm": float(np.linalg.norm(cr - c_seen) * 10), "skin_patch_vertices": int(patch.sum()),
       "skin_fit_residual_mm": {"max": float(skin_fit_res.max() * 10), "weighted_mean": float((skin_fit_res * w).sum() / w.sum() * 10)},
       "ring_fit_residual_mm": float(res.max() * 10),
       "centre_to_skin_mm": {"seen": float(dist_s * 10), "neutral": float(dist_r * 10)},
       "note": "applied by author_soft_tissue.py --ring-transform; replaces the 2026-10-14 T_local_cm, which measured the move in the "
               "key-displaced view and put the ring 14 mm low in game"}
json.dump(rep, open(out, "w"), indent=1)
print("RING_V2", json.dumps({k: v for k, v in rep.items() if k not in ("M_ring_local_cm", "method", "note")}), flush=True)
