"""Joy's soft-tissue morphs, and optionally the Fab cyber jacket fitted onto her: the SK_Joy reimport FBX.

  blender -b --python author_soft_tissue.py -- <out_dir> [--jacket <SKM_Jacket.fbx exported from Unreal>] [--keep-waistcoat]

Soft tissue (owner 2026-10-14: "add the same jiggle physics on silvers new character to bartender joy"): the
ST_<Region>_<Axis> shape keys that Silver's BodyDynamics spring component (USSSoftTissueComponent) drives. Four masked
regions (Breast_L/R, Hip_L/R), three keys per region displacing the masked skin 1 cm along the rest X/Y/Z, every garment
carrying paired keys of the same names, and per-region anchors (mask^2-weighted bone influences and rest centroids, in
centimetres) for the component. Masks are Joy's own measurements (scratchpad measure_joy_tissue.py): breast apex
(+-10.1, -15.1, 135.3) cm on a chest wall at y -10, glute apex (+-7.8, 15.0, 95.2) cm, bulge z 86..103. CC objects are
scaled 0.01, so object-local units are centimetres.

Jacket (owner 2026-10-14: "I have a new jacket for her ... fully rigged, so it can move with her. remove the black tub
top you created, this will be the slight cover up"): the pack's SKM_Jacket is skinned to a 74-bone MetaHuman-style rig,
not Joy's CC_Base rig, so it is re-skinned here: that rig is posed bone by bone onto Joy's joints (head, direction and
length, spine mapped by height), which deforms the jacket to her proportions and rest pose; the deformed shell takes her
body's skin weights from the nearest surface point, is pushed 4 mm clear of her skin and bottoms where it sank in, gets
no ST keys of its own (the tissue moves underneath it, held clear by each region's full travel), and replaces the waistcoat in the export (the painted strap is removed on the Unreal side). The pack's
material slot name M_jacket is kept so the import can assign the pack's MI_Jacket.
The source joy.blend is never written (sha verified before and after). Textures are not re-exported.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

SRC = Path("M:/SpaceSurvival/UserDownloadedAssets_SpaceSurvival/Content/VaultCache/FabLibrary/Joy-c6f24fcb/blender/joy.blend")
SRC_SHA = "8582f2f269e8"
ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--jacket", default="")
ap.add_argument("--keep-waistcoat", action="store_true")
opt = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])
OUT = Path(opt.out)
OUT.mkdir(parents=True, exist_ok=False)
KEY_CM = 1.0  # one morph unit moves the mask centre one centimetre (CentimetresPerMorphUnit = 1)
REGIONS = ("Breast_L", "Breast_R", "Hip_L", "Hip_R")
MAX_OFFSET_CM = {"Breast_L": 2.0, "Breast_R": 2.0, "Hip_L": 1.5, "Hip_R": 1.5}  # place_joy_soft_tissue.py's caps
REFERENCE_BONES = ("CC_Base_Pelvis", "CC_Base_Head", "CC_Base_L_Hand", "CC_Base_R_Hand", "CC_Base_L_Foot", "CC_Base_R_Foot")
JACKET_GAP_CM = 0.4
JACKET_SLOT = "M_jacket"


def smoothstep5(v):
    t = np.clip(v, 0.0, 1.0)
    return t * t * t * (t * (t * 6 - 15) + 10)


before = hashlib.sha256(SRC.read_bytes()).hexdigest()
assert before.startswith(SRC_SHA), before
bpy.ops.wm.open_mainfile(filepath=str(SRC), load_ui=False, use_scripts=False)
scene = bpy.context.scene
scene.frame_set(1)
rig = bpy.data.objects["Armature"]
rig.animation_data_clear()
rig.data.pose_position = "REST"
body = bpy.data.objects["CC_Base_Body"]
meshes = [o for o in scene.objects if o.type == "MESH" and not o.hide_render]
garments = ["waistcoat", "Underwear_Bottoms"]
if opt.jacket and not opt.keep_waistcoat:
    coat = bpy.data.objects["waistcoat"]
    meshes.remove(coat)
    garments.remove("waistcoat")
for o in [body] + [bpy.data.objects[g] for g in garments]:
    s = np.array(o.matrix_world)[:3, :3]
    assert np.allclose(s, np.eye(3) * 0.01, atol=1e-6), (o.name, s)  # CC: local centimetres, world metres
    assert [m.type for m in o.modifiers] == ["ARMATURE"], (o.name, [m.type for m in o.modifiers])
keys = body.data.shape_keys
assert keys and keys.key_blocks[0].name == "Basis" and not any(k.name.startswith("ST_") for k in keys.key_blocks)
P = np.array([v.co[:] for v in body.data.vertices], dtype=np.float64)  # cm
x, y, z = P.T
edges = np.array([e.vertices[:] for e in body.data.edges], dtype=np.int32)
BODY_W = np.array(body.matrix_world)
RIG_W = np.array(rig.matrix_world)

# --- masks (centimetres; the same shape as Silver's: elliptical radial falloff x forward/backward gate x midline gate)
masks, mask_report = {}, {}
for family in ("Breast", "Hip"):
    for side, sign in (("L", 1.0), ("R", -1.0)):
        if family == "Breast":
            radial = np.sqrt(((x - sign * 10.0) / 6.5) ** 2 + ((z - 135.0) / 6.8) ** 2)
            axial = smoothstep5((-y - 10.0) / 3.5)  # chest wall at y -10, full from 3.5 cm in front of it
        else:
            radial = np.sqrt(((x - sign * 7.8) / 9.5) ** 2 + ((z - 95.0) / 11.0) ** 2)
            axial = smoothstep5((y - 7.0) / 5.0)  # the small of the back at y 7, full on the bulge beyond 12
        gate = smoothstep5((sign * x - 0.4) / 1.9)
        mask = (1 - smoothstep5((radial - 0.38) / 0.62)) * axial * gate
        # the CC body is coarse where it matters (1-2 cm edges on the chest and glutes): two neighbour-averaging passes
        # soften the falloff so adjacent vertices never differ by more than ~0.3 of a morph unit; the gate is re-applied
        for _ in range(2):
            acc = np.zeros_like(mask)
            cnt = np.zeros_like(mask)
            np.add.at(acc, edges[:, 0], mask[edges[:, 1]])
            np.add.at(acc, edges[:, 1], mask[edges[:, 0]])
            np.add.at(cnt, edges[:, 0], 1)
            np.add.at(cnt, edges[:, 1], 1)
            mask = (0.5 * mask + 0.5 * acc / np.maximum(cnt, 1)) * gate
        mask[mask < 1e-7] = 0
        assert mask.max() > 0.5, (family, side, mask.max())
        mask /= mask.max()
        name = family + "_" + side
        masks[name] = mask
        ids = np.flatnonzero(mask)
        mask_report[name] = {"vertices": int(len(ids)), "bounds_cm": [P[ids].min(0).tolist(), P[ids].max(0).tolist()], "mean_mask": float(mask[ids].mean()),
                             "centre_cm": ((P[ids] * mask[ids, None]).sum(0) / mask[ids].sum()).tolist(),
                             "max_edge_mask_jump": float(np.abs(mask[edges[:, 0]] - mask[edges[:, 1]]).max())}
assert not np.any((masks["Breast_L"] > 0) & (masks["Breast_R"] > 0)) and not np.any((masks["Hip_L"] > 0) & (masks["Hip_R"] > 0))
assert not np.any((masks["Breast_L"] + masks["Breast_R"] > 0) & (masks["Hip_L"] + masks["Hip_R"] > 0))

body_bvh = BVHTree.FromPolygons([tuple(p) for p in P.tolist()], [tuple(f.vertices) for f in body.data.polygons], all_triangles=False)
body_faces = [list(f.vertices) for f in body.data.polygons]


def nearest_body(q):
    """Nearest body surface point (local cm): location, normal, inverse-distance weights over that face's vertices."""
    loc, nrm, fi, d = body_bvh.find_nearest(Vector(q))
    verts = body_faces[fi]
    w = 1.0 / (np.linalg.norm(P[verts] - np.array(loc), axis=1) + 0.05)
    return np.array(loc), np.array(nrm), d, verts, w / w.sum()


def add_keys(obj, base, mask_of):
    """ST_<region>_<X|Y|Z> keys on obj: base positions + mask * 1 cm along the axis. Returns the key names."""
    if not obj.data.shape_keys:
        obj.shape_key_add(name="Basis", from_mix=False)
    basis = obj.data.shape_keys.key_blocks[0]
    names = []
    for region in REGIONS:
        m = mask_of[region]
        for axis, letter in enumerate("XYZ"):
            delta = np.zeros_like(base)
            delta[:, axis] = m * KEY_CM
            k = obj.shape_key_add(name="ST_%s_%s" % (region, letter), from_mix=False)
            k.relative_key = basis
            k.slider_min, k.slider_max, k.value = -1.0, 1.0, 0.0
            k.data.foreach_set("co", (base + delta).astype(np.float32).ravel())
            names.append(k.name)
    return names


def garment_keys(obj, Q):
    """Paired keys: each garment vertex takes the mask of its nearest body surface point."""
    gmask = {r: np.zeros(len(Q)) for r in REGIONS}
    dist = np.zeros(len(Q))
    for i, q in enumerate(Q):
        loc, nrm, d, verts, w = nearest_body(q)
        dist[i] = d
        for r in REGIONS:
            gmask[r][i] = float((masks[r][verts] * w).sum())
    names = add_keys(obj, Q, gmask)
    return names, {"vertices": int(len(Q)), "max_distance_to_body_cm": float(dist.max()), "mean_distance_cm": float(dist.mean()),
                   "masked": {r: {"vertices": int((gmask[r] > 0).sum()), "max": float(gmask[r].max())} for r in REGIONS}}


new_keys = {body.name: add_keys(body, P, masks)}
garment_report = {}
for gname in garments:
    g = bpy.data.objects[gname]
    Q = np.array([v.co[:] for v in g.data.vertices], dtype=np.float64)
    new_keys[gname], garment_report[gname] = garment_keys(g, Q)

# --- anchors: mask^2-weighted bone influences and rest centroids (centimetres, Blender rest space), as Silver's extractor
bone_names = set(rig.data.bones.keys())
groups = {gr.index: gr.name for gr in body.vertex_groups if gr.name in bone_names}
anchors = {}
for region in REGIONS:
    prob = masks[region] ** 2
    prob /= prob.sum()
    weights, points = {}, {}
    for i in np.flatnonzero(prob > 1e-14):
        inf = [(groups[gg.group], gg.weight) for gg in body.data.vertices[int(i)].groups if gg.group in groups and gg.weight > 0]
        total = sum(w for _, w in inf)
        for n, w in inf:
            ww = float(prob[i] * w / total)
            weights[n] = weights.get(n, 0.0) + ww
            points[n] = points.get(n, np.zeros(3)) + ww * P[i]
    rows = [{"bone": n, "weight": w, "rest_position_blender_cm": (points[n] / w).tolist()} for n, w in weights.items() if w > 1e-6]
    s = sum(r["weight"] for r in rows)
    for r in rows:
        r["weight"] /= s
    anchors[region] = {"anchors": sorted(rows, key=lambda r: -r["weight"])}
    assert abs(sum(r["weight"] for r in rows) - 1) < 1e-9 and len(rows) >= 2, region
reference = {b: list(rig.data.bones[b].head_local) for b in REFERENCE_BONES}
report = {"source": str(SRC), "source_sha256": before, "blender": bpy.app.version_string, "key_cm": KEY_CM, "masks": mask_report, "garments": garment_report,
          "new_keys": new_keys, "regions": anchors, "reference_bones_blender_cm": reference, "body_keys": len(keys.key_blocks)}
print("JOY_ST_MASKS", json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "bounds_cm"} for k, v in mask_report.items()}), flush=True)
print("JOY_ST_ANCHORS", json.dumps({k: [(r["bone"], round(r["weight"], 3)) for r in v["anchors"]] for k, v in anchors.items()}), flush=True)


# ----------------------------------------------------------------------------------------------------------------------
def fit_jacket(path):
    """Re-skin the pack's jacket from its MetaHuman-style rig onto Joy. Returns the new jacket object and a report."""
    rep = {"source": path}
    existing = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path, ignore_leaf_bones=False, automatic_bone_orientation=False)
    new = [o for o in bpy.data.objects if o not in existing]
    jarm = next(o for o in new if o.type == "ARMATURE")
    jm = next(o for o in new if o.type == "MESH")
    assert jm.vertex_groups and any(m.type == "ARMATURE" for m in jm.modifiers), "the jacket export must be skinned"
    bpy.context.view_layer.update()
    JW = np.array(jarm.matrix_world)

    def jb(name):  # jacket bone rest head/tail, world metres
        b = jarm.data.bones[name]
        return (JW @ np.r_[np.array(b.head_local), 1])[:3], (JW @ np.r_[np.array(b.tail_local), 1])[:3]

    def cb(name):  # Joy bone rest head/tail, world metres
        b = rig.data.bones[name]
        return (RIG_W @ np.r_[np.array(b.head_local), 1])[:3], (RIG_W @ np.r_[np.array(b.tail_local), 1])[:3]

    # the torso is mapped by height along the two spine chains (both upright in rest); limbs bone to bone
    j_chain = ["pelvis", "spine_01", "spine_02", "spine_03", "spine_04", "spine_05", "neck_01", "neck_02", "head"]
    c_chain = ["CC_Base_Pelvis", "CC_Base_Waist", "CC_Base_Spine01", "CC_Base_Spine02", "CC_Base_NeckTwist01", "CC_Base_NeckTwist02", "CC_Base_Head"]
    c_pts = [cb(n)[0] for n in c_chain] + [cb(c_chain[-1])[1]]
    j_pts = [jb(n)[0] for n in j_chain] + [jb(j_chain[-1])[1]]
    j_neck, c_neck = jb("neck_01")[0][2], cb("CC_Base_NeckTwist01")[0][2]
    j_pel, c_pel = jb("pelvis")[0][2], cb("CC_Base_Pelvis")[0][2]
    torso_scale = (c_neck - c_pel) / (j_neck - j_pel)
    width_scale = np.linalg.norm(cb("CC_Base_L_Upperarm")[0] - cb("CC_Base_R_Upperarm")[0]) / np.linalg.norm(jb("upperarm_l")[0] - jb("upperarm_r")[0])
    rep.update(torso_scale=float(torso_scale), shoulder_width_scale=float(width_scale))

    def chain_point(zj):
        """The point on Joy's spine polyline at the height that the jacket rig's z maps to."""
        zc = c_pel + (zj - j_pel) * torso_scale
        zs = [p[2] for p in c_pts]
        for a, b in zip(range(len(c_pts) - 1), range(1, len(c_pts))):
            if zs[a] <= zc <= zs[b] or b == len(c_pts) - 1:
                t = 0.0 if zs[b] == zs[a] else (zc - zs[a]) / (zs[b] - zs[a])
                return c_pts[a] + (c_pts[b] - c_pts[a]) * np.clip(t, 0, 1.5)
        return c_pts[-1]

    def jlen(a, b):
        return float(np.linalg.norm(jb(b)[0] - jb(a)[0]))

    # CC bone tails stop at the twist helpers, so limb targets are joint to joint; the jacket rig has no wrist or knee
    # joints, so its forearms keep the upper arm's length ratio and its thighs keep their own length
    targets = {}  # jacket bone -> (head, unit direction, Y scale) in world metres
    for i, n in enumerate(j_chain):
        h = jb(n)[0]
        nxt = jb(j_chain[i + 1])[0] if i + 1 < len(j_chain) else h + np.array([0, 0, 0.10])
        th, tt = chain_point(h[2]), chain_point(nxt[2])
        d = tt - th
        L, Lj = np.linalg.norm(d), np.linalg.norm(nxt - h)
        targets[n] = (th, d / L, float(L / Lj) if Lj > 1e-6 else 1.0)
    ratios = {}
    for side in ("l", "r"):
        S = side.upper()
        h, t = cb("CC_Base_%s_Clavicle" % S)[0], cb("CC_Base_%s_Upperarm" % S)[0]
        d = t - h
        targets["clavicle_" + side] = (h, d / np.linalg.norm(d), float(np.linalg.norm(d) / jlen("clavicle_" + side, "upperarm_" + side)))
        h, t = cb("CC_Base_%s_Upperarm" % S)[0], cb("CC_Base_%s_Forearm" % S)[0]
        d = t - h
        ratios[side] = float(np.linalg.norm(d) / jlen("upperarm_" + side, "lowerarm_" + side))
        targets["upperarm_" + side] = (h, d / np.linalg.norm(d), ratios[side])
        h, t = cb("CC_Base_%s_Forearm" % S)[0], cb("CC_Base_%s_Hand" % S)[0]
        d = t - h
        targets["lowerarm_" + side] = (h, d / np.linalg.norm(d), ratios[side])
        h, t = cb("CC_Base_%s_Thigh" % S)[0], cb("CC_Base_%s_Calf" % S)[0]
        d = t - h
        targets["thigh_" + side] = (h, d / np.linalg.norm(d), 1.0)
    rep["arm_length_ratio"] = ratios

    def rot_between(a, b):
        a = a / np.linalg.norm(a)
        b = b / np.linalg.norm(b)
        v = np.cross(a, b)
        c = float(np.dot(a, b))
        if np.linalg.norm(v) < 1e-9:
            return np.eye(3) if c > 0 else -np.eye(3)
        vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        return np.eye(3) + vx + vx @ vx * (1 / (1 + c))

    # pose the jacket rig onto Joy's joints, parents before children; roll follows the minimal rotation of the rest axis
    JWinv = np.linalg.inv(JW)
    order = []

    def walk(b):
        order.append(b.name)
        for c in b.children:
            walk(c)

    for b in jarm.data.bones:
        if b.parent is None:
            walk(b)
    posed = 0
    for name in order:
        if name not in targets:
            continue
        head, direction, scale_y = targets[name]
        b = jarm.data.bones[name]
        rest = np.array(b.matrix_local)  # armature space
        rest_w = JW @ rest
        rest_dir = rest_w[:3, 1] / np.linalg.norm(rest_w[:3, 1])
        R = rot_between(rest_dir, direction)
        X = R @ (rest_w[:3, 0] / np.linalg.norm(rest_w[:3, 0]))
        Z = np.cross(X, direction)
        Z /= np.linalg.norm(Z)
        X = np.cross(direction, Z)
        M = np.eye(4)
        M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = X, direction * scale_y, Z, head
        pb = jarm.pose.bones[name]
        pb.matrix = Matrix((JWinv @ M).tolist())
        bpy.context.view_layer.update()
        posed += 1
    rep["bones_posed"] = posed
    # the deformed shell, world metres -> Joy's local centimetres
    dg = bpy.context.evaluated_depsgraph_get()
    ev = jm.evaluated_get(dg)
    me_ev = ev.to_mesh()
    EW = np.array(ev.matrix_world)
    Qw = np.array([(EW @ np.r_[np.array(v.co), 1])[:3] for v in me_ev.vertices], dtype=np.float64)
    faces = [list(f.vertices) for f in me_ev.polygons]
    uv_src = me_ev.uv_layers.active
    uvs = [tuple(d.uv) for d in uv_src.data] if uv_src else None
    smooth = [f.use_smooth for f in me_ev.polygons]
    ev.to_mesh_clear()
    BWinv = np.linalg.inv(BODY_W)
    Q = np.array([(BWinv @ np.r_[q, 1])[:3] for q in Qw])  # cm, Joy local
    rep["bounds_before_cm"] = [Q.min(0).tolist(), Q.max(0).tolist()]

    # skin weights from Joy's body, nearest surface point, inverse-distance over that face's vertices
    body_groups = {gr.index: gr.name for gr in body.vertex_groups if gr.name in bone_names}
    vert_groups = [{body_groups[gg.group]: gg.weight for gg in v.groups if gg.group in body_groups and gg.weight > 0} for v in body.data.vertices]
    jw = []
    pen_before = []
    for i in range(len(Q)):
        loc, nrm, d, verts, w = nearest_body(Q[i])
        acc = {}
        for vi, wi in zip(verts, w):
            for n, ww in vert_groups[vi].items():
                acc[n] = acc.get(n, 0.0) + wi * ww
        top = sorted(acc.items(), key=lambda kv: -kv[1])[:6]
        s = sum(v for _, v in top)
        jw.append({n: v / s for n, v in top})
        pen_before.append(float(np.dot(Q[i] - loc, nrm)))
    pen_before = np.array(pen_before)
    rep["penetration_before"] = {"inside_vertices": int((pen_before < 0).sum()), "deepest_cm": float(-pen_before.min()), "within_gap": int((pen_before < JACKET_GAP_CM).sum())}

    # push the shell clear of the skin and of the bottoms (whose own surface sits on the skin). Owner 2026-10-14: "her
    # jiggle physics should move underneath the jacket, not with the jacket" - so the jacket carries no ST keys and is
    # instead held off the skin by the region's full travel (MAX_OFFSET per region, mask-weighted) plus the base gap
    clear = np.full(len(Q), JACKET_GAP_CM)
    for i in range(len(Q)):
        loc, nrm, d, verts, w = nearest_body(Q[i])
        clear[i] += sum(MAX_OFFSET_CM[r] * float((masks[r][verts] * w).sum()) for r in REGIONS)
    rep["clearance_cm"] = {"min": float(clear.min()), "max": float(clear.max()), "vertices_over_tissue": int((clear > JACKET_GAP_CM + 0.05).sum())}
    bottoms = bpy.data.objects["Underwear_Bottoms"]
    BQ = np.array([v.co[:] for v in bottoms.data.vertices], dtype=np.float64)
    bot_bvh = BVHTree.FromPolygons([tuple(p) for p in BQ.tolist()], [tuple(f.vertices) for f in bottoms.data.polygons], all_triangles=False)
    moved = 0
    for _ in range(3):
        for i in range(len(Q)):
            loc, nrm, d, verts, w = nearest_body(Q[i])
            sd = float(np.dot(Q[i] - loc, nrm))
            if sd < clear[i]:
                Q[i] = loc + nrm * clear[i]
                moved += 1
            bl, bn, bi, bd = bot_bvh.find_nearest(Vector(Q[i]))
            if bl is not None and bd < 2.0:
                sd = float(np.dot(Q[i] - np.array(bl), np.array(bn)))
                if 0 > sd > -1.5 or 0 <= sd < clear[i] * 0.75:
                    Q[i] = np.array(bl) + np.array(bn) * clear[i] * 0.75
                    moved += 1
    pen_after = np.array([float(np.dot(Q[i] - nearest_body(Q[i])[0], nearest_body(Q[i])[1])) for i in range(len(Q))])
    rep["penetration_after"] = {"inside_vertices": int((pen_after < 0).sum()), "deepest_cm": float(-pen_after.min()), "moves": moved}
    rep["bounds_after_cm"] = [Q.min(0).tolist(), Q.max(0).tolist()]

    # the final jacket object in Joy's convention: scale 0.01, parented to her armature, her bone groups, M_jacket slot
    me = bpy.data.meshes.new("Jacket")
    me.from_pydata([tuple(q) for q in Q.tolist()], [], faces)
    me.update()
    if uvs:
        uv = me.uv_layers.new(name="UVMap")
        for li, t in enumerate(uvs):
            uv.data[li].uv = t
    for f, s in zip(me.polygons, smooth):
        f.use_smooth = True
    bm = bmesh.new()
    bm.from_mesh(me)
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(55):
            e.smooth = False
    bm.to_mesh(me)
    bm.free()
    mat = bpy.data.materials.new(JACKET_SLOT)
    me.materials.append(mat)
    ob = bpy.data.objects.new("Jacket", me)
    scene.collection.objects.link(ob)
    ob.parent = rig
    ob.matrix_parent_inverse = rig.matrix_world.inverted()
    ob.matrix_world = body.matrix_world.copy()
    for n in sorted({n for d in jw for n in d}):
        ob.vertex_groups.new(name=n)
    for i, d in enumerate(jw):
        for n, v in d.items():
            ob.vertex_groups[n].add([i], float(v), "REPLACE")
    mod = ob.modifiers.new("Armature", "ARMATURE")
    mod.object = rig
    # the pack's rig and mesh leave the scene so they are not exported
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    rep.update(vertices=len(Q), polygons=len(faces), bone_groups=len(ob.vertex_groups))
    return ob, rep


jacket = None
if opt.jacket:
    jacket, jrep = fit_jacket(opt.jacket)
    meshes.append(jacket)  # no ST keys: the tissue moves underneath it (see fit_jacket's clearance)
    report["jacket"] = jrep
    print("JOY_JACKET", json.dumps({k: v for k, v in jrep.items() if "bounds" not in k}), flush=True)
print("JOY_ST_GARMENTS", json.dumps(garment_report), flush=True)
report["meshes"] = [o.name for o in meshes]

# --- export exactly as export_joy_original.py does (REST pose, action cleared, no modifiers baked, -Z forward / Y up)
bpy.ops.object.select_all(action="DESELECT")
rig.select_set(True)
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = rig
fbx = OUT / "SK_Joy.fbx"
bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, object_types={"ARMATURE", "MESH"}, add_leaf_bones=False,
                         use_mesh_modifiers=False, use_armature_deform_only=False, bake_anim=False,
                         axis_forward="-Z", axis_up="Y", path_mode="AUTO")
report["fbx"] = {"path": str(fbx), "sha256": hashlib.sha256(fbx.read_bytes()).hexdigest(), "bytes": fbx.stat().st_size}
assert hashlib.sha256(SRC.read_bytes()).hexdigest() == before
report["source_unchanged"] = True
(OUT / "SoftTissue.json").write_text(json.dumps(report, indent=1))
# a few workbench views of the dressed body for the geometric check sheet (hair hidden: it is cards)
if opt.jacket:
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_cavity = True
    scene.render.resolution_x, scene.render.resolution_y = 640, 900
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.lens = 70
    for o in meshes:
        o.hide_render = o.name == "Hair"
    jacket.data.materials[0].diffuse_color = (0.12, 0.12, 0.14, 1)
    centre = Vector((0, 0, 1.2))
    for name, direction in (("front", (0, -1, 0.1)), ("three_quarter", (0.8, -0.7, 0.1)), ("side", (1, 0, 0.05)), ("back", (0, 1, 0.1))):
        d = Vector(direction).normalized()
        cam.location = centre + d * 2.6
        cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(OUT / ("fit_%s.png" % name))
        bpy.ops.render.render(write_still=True)
print("JOY_ST_EXPORTED", json.dumps({"fbx_bytes": fbx.stat().st_size, "keys": {k: len(v) for k, v in new_keys.items()}, "meshes": report["meshes"]}), flush=True)
