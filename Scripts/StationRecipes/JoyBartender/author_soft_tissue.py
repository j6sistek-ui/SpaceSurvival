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
import os
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
ap.add_argument("--fit-body", default="", help="the body the jacket was cut for (SKM_Female_BodyMesh.fbx); default: beside the jacket")
ap.add_argument("--pants", default="", help="a pants (+ shoes) garment exported from Unreal; replaces Underwear_Bottoms in the export")
ap.add_argument("--pants-body", default="", help="the body the pants were cut for (SKM_Manny_500_Simple.fbx); default: beside the pants")
ap.add_argument("--keep-waistcoat", action="store_true")
opt = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])
OUT = Path(opt.out)
OUT.mkdir(parents=True, exist_ok=False)
KEY_CM = 1.0  # one morph unit moves the mask centre one centimetre (CentimetresPerMorphUnit = 1)
REGIONS = ("Breast_L", "Breast_R", "Hip_L", "Hip_R")
MAX_OFFSET_CM = {"Breast_L": 2.0, "Breast_R": 2.0, "Hip_L": 1.5, "Hip_R": 1.5}  # place_joy_soft_tissue.py's caps
# owner 2026-10-14: "loosen the front off the chest area a bit, and open slightly, so the breasts are tastefully almost
# exposed and free to jiggle and be seen": the front panels swing open about the sides of her chest (inner edge out by
# OPEN_CM through the chest band) and stand LOOSE_CM further off the breasts than the spring travel needs
OPEN_CM = 4.0
OPEN_HINGE_CM = 18.0
LOOSE_CM = 0.0  # 1.5 made a box over the chest (owner, side view 2026-10-14: "not make a bulge of space")
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
if opt.pants:
    meshes.remove(bpy.data.objects["Underwear_Bottoms"])
    garments.remove("Underwear_Bottoms")
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
def import_skinned(path):
    existing = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path, ignore_leaf_bones=False, automatic_bone_orientation=False)
    new = [o for o in bpy.data.objects if o not in existing]
    arm = next(o for o in new if o.type == "ARMATURE")
    mesh = next(o for o in new if o.type == "MESH")
    assert mesh.vertex_groups and any(m.type == "ARMATURE" for m in mesh.modifiers), path + " must be skinned"
    return arm, mesh, new


def baked_copy(obj, name):
    """The object's evaluated (posed) mesh as a new world-space object with an identity transform."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
    me.transform(ev.matrix_world)
    o = bpy.data.objects.new(name, me)
    scene.collection.objects.link(o)
    return o


def coords(obj, evaluated=False):
    if evaluated:
        dg = bpy.context.evaluated_depsgraph_get()
        ev = obj.evaluated_get(dg)
        me = ev.to_mesh()
        W = np.array(ev.matrix_world)
        out = np.array([(W @ np.r_[np.array(v.co), 1])[:3] for v in me.vertices], dtype=np.float64)
        ev.to_mesh_clear()
        return out
    W = np.array(obj.matrix_world)
    return np.array([(W @ np.r_[np.array(v.co), 1])[:3] for v in obj.data.vertices], dtype=np.float64)


def rot_between(a, b):
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3) if c > 0 else -np.eye(3)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx * (1 / (1 + c))


def cb(name):  # Joy bone rest head/tail, world metres
    b = rig.data.bones[name]
    return (RIG_W @ np.r_[np.array(b.head_local), 1])[:3], (RIG_W @ np.r_[np.array(b.tail_local), 1])[:3]


# per garment: object name, the height band it must stay inside (Joy local cm), whether it carries the paired ST keys
# (moves WITH the tissue, like the bottoms) or is held clear of it (the tissue moves underneath, like the jacket)
SPEC = {"jacket": {"name": "Jacket", "keys": False, "gap_cm": JACKET_GAP_CM, "open": True},
        "pants": {"name": "Pants", "keys": True, "gap_cm": 0.3, "open": False, "tighten": (0.45, 0.8), "weights": "source",
                  "rigid_slots": ("M_SciFi_S_Pack_02L", "M_SciFi_S_Pack_02R")}}
# UE5 Manny / MetaHuman bone -> Joy's CC bone, for garments that keep the pack's own skin weights. Joy's thighs touch at
# rest, so nearest-skin weights gave inner-leg fabric the OTHER leg and it webbed between her legs when they parted
# (front still, 2026-10-14). The pack's weights know which leg every vertex belongs to.
UE_TO_CC = {"pelvis": "CC_Base_Pelvis", "spine_01": "CC_Base_Waist", "spine_02": "CC_Base_Spine01", "spine_03": "CC_Base_Spine02",
            "spine_04": "CC_Base_Spine02", "spine_05": "CC_Base_Spine02"}
for _s, _S in (("l", "L"), ("r", "R")):
    UE_TO_CC.update({"thigh_" + _s: "CC_Base_%s_Thigh" % _S, "thigh_twist_01_" + _s: "CC_Base_%s_ThighTwist01" % _S,
                     "thigh_twist_02_" + _s: "CC_Base_%s_ThighTwist02" % _S, "calf_" + _s: "CC_Base_%s_Calf" % _S,
                     "calf_twist_01_" + _s: "CC_Base_%s_CalfTwist01" % _S, "calf_twist_02_" + _s: "CC_Base_%s_CalfTwist02" % _S,
                     "foot_" + _s: "CC_Base_%s_Foot" % _S, "ball_" + _s: "CC_Base_%s_ToeBase" % _S})
NEXT = {"pelvis": "spine_01", "spine_01": "spine_02", "spine_02": "spine_03", "spine_03": "spine_04", "spine_04": "spine_05",
        "spine_05": "neck_01", "neck_01": "neck_02", "neck_02": "head", "clavicle_l": "upperarm_l", "clavicle_r": "upperarm_r",
        "upperarm_l": "lowerarm_l", "upperarm_r": "lowerarm_r", "lowerarm_l": "hand_l", "lowerarm_r": "hand_r",
        "thigh_l": "calf_l", "thigh_r": "calf_r", "calf_l": "foot_l", "calf_r": "foot_r", "foot_l": "ball_l", "foot_r": "ball_r"}


def fit_garment(kind, path, body_path, under=None):
    """Fit a pack garment onto Joy and re-skin it to her rig. Returns the new object and a report.

    Owner 2026-10-14: "jackets parametric so needs to be fit". A pack garment is cut for the pack's own body (the jacket
    for a female MetaHuman, the pants and sneakers for the UE5 Manny), exported beside it. Garment and body are posed onto
    Joy's joints by the same bone targets, that body is projected along its normals onto Joy's skin (Shrinkwrap,
    smoothed), and the garment follows it through a Surface Deform bound to the posed body: every garment vertex keeps
    its offset from the body it was made for, now on hers. `under` is the layer the garment must stay outside of.
    """
    spec = SPEC[kind]
    rep = {"kind": kind, "source": path, "fit_body": body_path}
    garm, gm, new = import_skinned(path)
    barm, bm, new_b = import_skinned(body_path)
    new += new_b
    bpy.context.view_layer.update()
    GW = np.array(garm.matrix_world)
    BWm = np.array(barm.matrix_world)

    def gb(name):  # the fit body's rest joint (the garment shares it), world metres
        return (BWm @ np.r_[np.array(barm.data.bones[name].head_local), 1])[:3]

    # the garment's rig and the body's rig must agree where they share bones, or the body is not the garment's
    shared = [b.name for b in garm.data.bones if b.name in barm.data.bones]
    head_gap = max(float(np.linalg.norm((GW @ np.r_[np.array(garm.data.bones[n].head_local), 1])[:3] - gb(n))) for n in shared)
    rep["rig_head_gap_cm"] = head_gap * 100
    assert head_gap < 0.01, ("the fit body's skeleton does not match the garment's", head_gap)
    have = set(barm.data.bones.keys())

    # the torso is mapped by height along the two spine chains (both upright in rest); limbs joint to joint
    j_chain = [n for n in ("pelvis", "spine_01", "spine_02", "spine_03", "spine_04", "spine_05", "neck_01", "neck_02", "head") if n in have]
    c_chain = ["CC_Base_Pelvis", "CC_Base_Waist", "CC_Base_Spine01", "CC_Base_Spine02", "CC_Base_NeckTwist01", "CC_Base_NeckTwist02", "CC_Base_Head"]
    c_pts = [cb(n)[0] for n in c_chain] + [cb(c_chain[-1])[1]]
    j_pel, c_pel = gb("pelvis")[2], cb("CC_Base_Pelvis")[0][2]
    torso_scale = (cb("CC_Base_NeckTwist01")[0][2] - c_pel) / (gb("neck_01")[2] - j_pel)
    rep["torso_scale"] = float(torso_scale)

    def chain_point(zj):
        zc = c_pel + (zj - j_pel) * torso_scale
        zs = [p[2] for p in c_pts]
        for a, b in zip(range(len(c_pts) - 1), range(1, len(c_pts))):
            if zs[a] <= zc <= zs[b] or b == len(c_pts) - 1:
                t = 0.0 if zs[b] == zs[a] else (zc - zs[a]) / (zs[b] - zs[a])
                return c_pts[a] + (c_pts[b] - c_pts[a]) * np.clip(t, 0, 1.5)
        return c_pts[-1]

    def joint_target(bone, child, joy_from, joy_to):
        h, t = cb(joy_from)[0], cb(joy_to)[0]
        d = t - h
        scale = float(np.linalg.norm(d) / np.linalg.norm(gb(child) - gb(bone))) if child in have else 1.0
        return h, d / np.linalg.norm(d), scale

    targets = {}  # rig bone -> (head, unit direction, stretch along the limb) in world metres
    for i, n in enumerate(j_chain):
        h = gb(n)
        nxt = gb(j_chain[i + 1]) if i + 1 < len(j_chain) else h + np.array([0, 0, 0.10])
        th, tt = chain_point(h[2]), chain_point(nxt[2])
        d = tt - th
        L, Lj = np.linalg.norm(d), np.linalg.norm(nxt - h)
        targets[n] = (th, d / L, float(L / Lj) if Lj > 1e-6 else 1.0)
    for side in ("l", "r"):
        S = side.upper()
        toe = "CC_Base_%s_ToeBase" % S
        pairs = [("clavicle", "upperarm", "Clavicle", "Upperarm"), ("upperarm", "lowerarm", "Upperarm", "Forearm"), ("lowerarm", "hand", "Forearm", "Hand"),
                 ("thigh", "calf", "Thigh", "Calf"), ("calf", "foot", "Calf", "Foot")]
        if toe in rig.data.bones:
            pairs.append(("foot", "ball", "Foot", "ToeBase"))
        for bone, child, jf, jt in pairs:
            if bone + "_" + side in have:
                targets[bone + "_" + side] = joint_target(bone + "_" + side, child + "_" + side, "CC_Base_%s_%s" % (S, jf), "CC_Base_%s_%s" % (S, jt))
    rep["stretch"] = {k: round(v[2], 3) for k, v in targets.items()}

    def rest_dir(n):
        if n == "head":
            return np.array([0.0, 0.0, 1.0])
        d = gb(NEXT[n]) - gb(n)
        return d / np.linalg.norm(d)

    # Bones from Unreal rigs run along their local X; Blender's importer gives each a Y axis that is NOT the limb, so a
    # bone's direction is taken joint to joint. Rotating the bone's Y onto her limbs swung every limb ~90 degrees.
    def pose_rig(arm):
        AW = np.array(arm.matrix_world)
        AWinv = np.linalg.inv(AW)
        order = []

        def walk(bone):
            order.append(bone.name)
            for c in bone.children:
                walk(c)

        for bone in arm.data.bones:
            if bone.parent is None:
                walk(bone)
        count = 0
        for name in order:
            if name not in targets or (name != "head" and NEXT.get(name) not in have):
                continue
            head, direction, scale_along = targets[name]
            rest_w = AW @ np.array(arm.data.bones[name].matrix_local)
            F = rest_w[:3, :3] / np.linalg.norm(rest_w[:3, :3], axis=0)
            rd = rest_dir(name)
            M = np.eye(4)
            M[:3, :3] = rot_between(rd, direction) @ F
            M[:3, 3] = head
            # The pack's armature object carries the FBX unit scale (0.01): taking a world matrix into armature space
            # scales its axes by 100 as well, which skinned the jacket 100x too large (it filled the bar in Play,
            # 2026-10-14). The axes are re-normalised; the stretch goes on the local axis that runs along the limb.
            Ma = AWinv @ M
            Ma[:3, :3] /= np.linalg.norm(Ma[:3, :3], axis=0)
            Ma[:3, int(np.argmax(np.abs(F.T @ rd)))] *= scale_along
            arm.pose.bones[name].matrix = Matrix(Ma.tolist())
            bpy.context.view_layer.update()
            count += 1
        return count

    # the garment must sit on its own body at rest
    g_rest, b_rest = coords(gm, True), coords(bm, True)
    rest_bvh = BVHTree.FromPolygons([tuple(q) for q in b_rest.tolist()], [tuple(f.vertices) for f in bm.data.polygons], all_triangles=False)
    rest_d = np.array([rest_bvh.find_nearest(Vector(q))[3] for q in g_rest]) * 100
    rep["garment_on_its_body_cm"] = {"p50": float(np.percentile(rest_d, 50)), "p95": float(np.percentile(rest_d, 95)), "max": float(rest_d.max())}
    rep["bones_posed"] = pose_rig(garm)
    pose_rig(barm)
    # the posed body projected onto Joy's skin, the posed garment bound to it, then the body takes her shape
    fit_posed = baked_copy(bm, "FitBodyPosed")
    g_posed = baked_copy(gm, "GarmentPosed")
    helpers = [fit_posed, g_posed]
    target = fit_posed.copy()
    target.data = fit_posed.data.copy()
    target.name = "FitBodyOnJoy"
    scene.collection.objects.link(target)
    helpers.append(target)
    sw = target.modifiers.new("Wrap", "SHRINKWRAP")
    sw.target = body
    sw.wrap_method = "PROJECT"
    sw.use_negative_direction = True
    sw.use_positive_direction = True
    sw.project_limit = 0.10  # metres along the body's own normals; farther than that is not the same surface
    sw.wrap_mode = "ON_SURFACE"
    P0 = coords(fit_posed)
    D = coords(target, True) - P0
    hit = np.linalg.norm(D, axis=1) > 1e-6
    medges = np.array([e.vertices[:] for e in fit_posed.data.edges], dtype=np.int32)
    for _ in range(6):
        acc = np.zeros_like(D)
        cnt = np.zeros(len(D))
        np.add.at(acc, medges[:, 0], D[medges[:, 1]])
        np.add.at(acc, medges[:, 1], D[medges[:, 0]])
        np.add.at(cnt, medges[:, 0], 1)
        np.add.at(cnt, medges[:, 1], 1)
        D = 0.5 * D + 0.5 * acc / np.maximum(cnt, 1)[:, None]
    rep["body_wrap"] = {"vertices": int(len(D)), "projected": int(hit.sum()), "mean_move_cm": float(np.linalg.norm(D, axis=1).mean() * 100),
                        "max_move_cm": float(np.linalg.norm(D, axis=1).max() * 100)}
    P_bones = coords(g_posed)  # posed by the bones alone: rigid parts (shoes) keep this shape
    sd = g_posed.modifiers.new("Follow", "SURFACE_DEFORM")
    sd.target = fit_posed
    sd.falloff = 4.0
    with bpy.context.temp_override(object=g_posed, active_object=g_posed, selected_objects=[g_posed], selected_editable_objects=[g_posed]):
        bpy.ops.object.surfacedeform_bind(modifier="Follow")
    bpy.context.view_layer.update()
    coords(g_posed, True)  # the bind happens on evaluation
    assert sd.is_bound, "Surface Deform did not bind the garment to its body"
    fit_posed.data.vertices.foreach_set("co", (P0 + D).astype(np.float32).ravel())
    fit_posed.data.update()
    bpy.context.view_layer.update()
    Qw = coords(g_posed, True)
    if os.environ.get("SS_FIT_DEBUG"):
        rep["debug_blend"] = str(OUT / ("fit_debug_%s.blend" % kind))
        bpy.ops.wm.save_as_mainfile(filepath=rep["debug_blend"], copy=True)
    me_src = g_posed.data
    faces = [list(f.vertices) for f in me_src.polygons]
    mat_index = [f.material_index for f in me_src.polygons]
    slot_names = [m.name.split(".")[0] if m else "Garment" for m in me_src.materials]
    # the FBX names materials after their instances; the pack's own slot names (in the export report beside the FBX,
    # same order) are what the reimport maps materials onto
    for cand in (Path(path).with_suffix(".json"), Path(path).parent / "Jacket.json"):
        if cand.exists():
            info = json.loads(cand.read_text())
            if Path(path).stem in info.get("mesh", "") and len(info.get("materials", [])) == len(slot_names):
                slot_names = [m[0] for m in info["materials"]]
                break
    uv_src = me_src.uv_layers.active
    uvs = [tuple(d.uv) for d in uv_src.data] if uv_src else None
    BWinv = np.linalg.inv(BODY_W)
    Q = np.array([(BWinv @ np.r_[q, 1])[:3] for q in Qw])  # cm, Joy local
    rigid = np.zeros(len(Q), dtype=bool)
    if spec.get("rigid_slots"):
        # Owner 2026-10-14 circled a crumpled sneaker toe: shoes are rigid, so they follow her foot bones only (no wrap,
        # no tightening, no push). Each shoe is then scaled about its sole until her foot no longer shows through it.
        rs = {i for i, n in enumerate(slot_names) if n in spec["rigid_slots"]}
        on_rigid = np.zeros(len(Q), dtype=bool)
        on_soft = np.zeros(len(Q), dtype=bool)
        for f, mi in zip(faces, mat_index):
            (on_rigid if mi in rs else on_soft)[f] = True
        rigid = on_rigid & ~on_soft
        Q[rigid] = np.array([(BWinv @ np.r_[q, 1])[:3] for q in P_bones[rigid]])
        foot_v = P[(P[:, 2] < 14.0)]
        shoes = {}
        for side, sign in (("L", 1.0), ("R", -1.0)):
            sel = rigid & (np.sign(Q[:, 0]) == sign)
            if not sel.any():
                continue
            idx = np.flatnonzero(sel)
            sfaces = [f for f, mi in zip(faces, mat_index) if mi in rs and all(sel[v] for v in f)]
            remap = {v: k for k, v in enumerate(idx)}
            # hung from her ankle joint, the shoe keeps Manny's ankle height above its sole; her ankle is lower, so
            # the shoe is raised by the difference and its inner sole meets hers, as the pack placed it on Manny
            lift_cm = (gb("foot_" + side.lower())[2] - cb("CC_Base_%s_Foot" % side)[0][2]) * 100.0
            Q[idx, 2] += lift_cm
            fv = foot_v[np.sign(foot_v[:, 0]) == sign]
            base = np.array([Q[idx, 0].mean(), Q[idx, 1].mean(), Q[idx, 2].min()])
            collar = Q[idx, 2].max() - 2.0
            fv = fv[fv[:, 2] < collar]
            scale, out = 1.0, None
            for scale in (1.0, 1.03, 1.06, 1.09, 1.12, 1.15):
                pts = base + (Q[idx] - base) * scale
                bvh = BVHTree.FromPolygons([tuple(q) for q in pts.tolist()], [tuple(remap[v] for v in f) for f in sfaces], all_triangles=False)
                out = 0
                for q in fv:
                    loc, nrm, fi, d = bvh.find_nearest(Vector(q))
                    if loc is not None and float(np.dot(q - np.array(loc), np.array(nrm))) > 0.05:
                        out += 1
                if out <= 0.01 * max(1, len(fv)):
                    break
            Q[idx] = base + (Q[idx] - base) * scale
            shoes[side] = {"vertices": int(len(idx)), "raised_cm": float(lift_cm), "scale": scale, "foot_vertices_tested": int(len(fv)), "foot_vertices_outside": int(out)}
        rep["rigid_shoes"] = shoes

    # The fitted shell must sit on HER: inside its height band, no wider than her arms, close to her skin. A fit that
    # fails these is a math error, not a fitting problem.
    z_pel = (BWinv @ np.r_[cb("CC_Base_Pelvis")[0], 1])[2]
    z_head = (BWinv @ np.r_[cb("CC_Base_Head")[0], 1])[2]
    # shoes put soles under her bare feet: up to 6 cm below her floor, and she is raised by that much in game
    band = (z_pel - 25, z_head) if kind == "jacket" else (-6.0, z_pel + 20)
    near = np.array([nearest_body(q)[2] for q in Q])
    rep["sanity"] = {"z_range_cm": [float(Q[:, 2].min()), float(Q[:, 2].max())], "allowed_z_cm": [float(band[0]), float(band[1])],
                     "half_width_cm": float(np.abs(Q[:, 0]).max()), "p99_distance_to_body_cm": float(np.percentile(near, 99)), "max_distance_to_body_cm": float(near.max())}
    assert band[0] <= Q[:, 2].min() and Q[:, 2].max() <= band[1], (kind + " outside its height band", rep["sanity"])
    assert np.abs(Q[:, 0]).max() < 80, (kind + " wider than her arms", rep["sanity"])
    assert near.max() < 40, (kind + " far from her skin", rep["sanity"])  # an exploded fit is metres away

    if spec["open"]:
        # open the front: front panels (y forward of -4 cm, she faces -Y) move outward from the midline, most at the
        # inner edge, none at the hinge; full through the chest band, a third at the collar top and the hem
        front_w = smoothstep5(-(Q[:, 1] + 4.0) / 4.0)
        inner = np.clip((OPEN_HINGE_CM - np.abs(Q[:, 0])) / OPEN_HINGE_CM, 0.0, 1.0)
        bandw = np.clip(1.0 - np.abs(Q[:, 2] - 135.0) / 30.0, 0.35, 1.0)
        shift = OPEN_CM * inner * bandw * front_w
        Q[:, 0] += np.sign(Q[:, 0]) * shift
        rep["opened"] = {"open_cm": OPEN_CM, "vertices": int((shift > 0.05).sum()), "max_shift_cm": float(shift.max())}

    if spec.get("tighten"):
        # owner 2026-10-14: "it's very baggy, more form fitting?". The fabric's distance from her skin keeps only
        # `tighten` of what the pack's cut gave it. The change is smoothed over the garment's own surface, so pockets,
        # knee pads and seams keep their relief over the tighter fabric; the shoes (below 12-18 cm) are left alone.
        off = np.zeros(len(Q))
        nrmv = np.zeros((len(Q), 3))
        for i in range(len(Q)):
            loc, nrm, d, verts, w = nearest_body(Q[i])
            off[i] = float(np.dot(Q[i] - loc, nrm))
            nrmv[i] = nrm
        # owner, after the first tightening: "the lower legs are too tight, i think the top is too baggy" - the fabric
        # keeps `upper` of its room over the hips and thighs and `lower` over the calves, blended through the knee
        g = spec["gap_cm"]
        upper, lower = spec["tighten"]
        z_knee = (np.linalg.inv(BODY_W) @ np.r_[cb("CC_Base_L_Calf")[0], 1])[2]
        keep = lower + (upper - lower) * smoothstep5((Q[:, 2] - (z_knee - 10.0)) / 20.0)
        want = np.where(off > g, g + (off - g) * keep, off)
        delta = (want - off)[:, None] * nrmv * smoothstep5((Q[:, 2] - 12.0) / 6.0)[:, None]
        delta[rigid] = 0.0
        tedges = np.array(sorted({tuple(sorted((f[k], f[(k + 1) % len(f)]))) for f in faces for k in range(len(f))}), dtype=np.int32)
        for _ in range(12):
            acc = np.zeros_like(delta)
            cnt = np.zeros(len(delta))
            np.add.at(acc, tedges[:, 0], delta[tedges[:, 1]])
            np.add.at(acc, tedges[:, 1], delta[tedges[:, 0]])
            np.add.at(cnt, tedges[:, 0], 1)
            np.add.at(cnt, tedges[:, 1], 1)
            delta = 0.5 * delta + 0.5 * acc / np.maximum(cnt, 1)[:, None]
        delta[rigid] = 0.0
        Q = Q + delta
        rep["tightened"] = {"keep_upper_lower": list(spec["tighten"]), "knee_z_cm": float(z_knee), "offset_p50_before_cm": float(np.percentile(off, 50)), "offset_p95_before_cm": float(np.percentile(off, 95)),
                            "mean_pull_cm": float(np.linalg.norm(delta, axis=1).mean()), "max_pull_cm": float(np.linalg.norm(delta, axis=1).max())}

    # the pack's own weights, mapped bone to bone (unmapped bones climb to their nearest mapped parent)
    src_w = None
    if spec.get("weights") == "source":
        def mapped(bone_name):
            b = garm.data.bones.get(bone_name)
            while b is not None:
                if b.name in UE_TO_CC and UE_TO_CC[b.name] in rig.data.bones:
                    return UE_TO_CC[b.name]
                b = b.parent
            return None
        gnames = {g.index: g.name for g in gm.vertex_groups}
        src_w, unmapped = [], set()
        for v in gm.data.vertices:
            acc = {}
            for g in v.groups:
                if g.weight <= 0:
                    continue
                cc = mapped(gnames[g.group])
                if cc is None:
                    unmapped.add(gnames[g.group])
                    continue
                acc[cc] = acc.get(cc, 0.0) + g.weight
            src_w.append(acc)
        assert len(src_w) == len(Q), (len(src_w), len(Q))
        rep["source_weights"] = {"unmapped_bones": sorted(unmapped), "vertices_without_weight": int(sum(1 for a in src_w if not a))}
    # skin weights from Joy's body, nearest surface point, inverse-distance over that face's vertices
    body_groups = {gr.index: gr.name for gr in body.vertex_groups if gr.name in bone_names}
    vert_groups = [{body_groups[gg.group]: gg.weight for gg in v.groups if gg.group in body_groups and gg.weight > 0} for v in body.data.vertices]
    gw = []
    for i in range(len(Q)):
        loc, nrm, d, verts, w = nearest_body(Q[i])
        acc = {}
        for vi, wi in zip(verts, w):
            for n, ww in vert_groups[vi].items():
                acc[n] = acc.get(n, 0.0) + wi * ww
        if src_w is not None and src_w[i]:
            acc = src_w[i]
        top = sorted(acc.items(), key=lambda kv: -kv[1])[:6]
        s = sum(v for _, v in top)
        gw.append({n: v / s for n, v in top})

    # clearance. A garment with the paired keys moves with the tissue, so it only clears the skin by its gap. The jacket
    # does not (owner: "her jiggle physics should move underneath the jacket, not with the jacket"), so it clears the
    # tissue's travel where it hangs, at and below the bust line; above it the panel rests near the skin (owner,
    # reviewing the side view: "didn't need to be so tight ... not make a bulge of space").
    clear = np.full(len(Q), spec["gap_cm"])
    if not spec["keys"]:
        hang = np.clip(0.35 + 0.65 * (140.0 - Q[:, 2]) / 5.0, 0.35, 1.0)
        for i in range(len(Q)):
            loc, nrm, d, verts, w = nearest_body(Q[i])
            clear[i] += hang[i] * sum(MAX_OFFSET_CM[r] * float((masks[r][verts] * w).sum()) for r in REGIONS)
    rep["clearance_cm"] = {"min": float(clear.min()), "max": float(clear.max())}
    under_bvh = None
    if under is not None:
        UQ = np.array([v.co[:] for v in under.data.vertices], dtype=np.float64)
        under_bvh = BVHTree.FromPolygons([tuple(q) for q in UQ.tolist()], [tuple(f.vertices) for f in under.data.polygons], all_triangles=False)
    pen0 = np.array([float(np.dot(Q[i] - nearest_body(Q[i])[0], nearest_body(Q[i])[1])) for i in range(len(Q))])
    rep["penetration_before"] = {"inside_vertices": int((pen0 < 0).sum()), "deepest_cm": float(-pen0.min())}
    moved = 0
    for _ in range(3):
        for i in range(len(Q)):
            if rigid[i]:
                continue
            loc, nrm, d, verts, w = nearest_body(Q[i])
            sd_ = float(np.dot(Q[i] - loc, nrm))
            if sd_ < clear[i]:
                Q[i] = loc + nrm * clear[i]
                moved += 1
            if under_bvh is not None:
                bl, bn, bi, bd = under_bvh.find_nearest(Vector(Q[i]))
                if bl is not None and bd < 2.0:
                    sd_ = float(np.dot(Q[i] - np.array(bl), np.array(bn)))
                    if 0 > sd_ > -1.5 or 0 <= sd_ < 0.3:
                        Q[i] = np.array(bl) + np.array(bn) * 0.3
                        moved += 1
    pen1 = np.array([float(np.dot(Q[i] - nearest_body(Q[i])[0], nearest_body(Q[i])[1])) for i in range(len(Q))])
    rep["penetration_after"] = {"inside_vertices": int((pen1 < 0).sum()), "deepest_cm": float(-pen1.min()), "moves": moved}

    # the final object in Joy's convention: scale 0.01, parented to her armature, her bone groups, the pack's slot names
    me = bpy.data.meshes.new(spec["name"])
    me.from_pydata([tuple(q) for q in Q.tolist()], [], faces)
    me.update()
    if uvs:
        uv = me.uv_layers.new(name="UVMap")
        for li, t in enumerate(uvs):
            uv.data[li].uv = t
    for n in slot_names:
        me.materials.append(bpy.data.materials.get(n) or bpy.data.materials.new(n))
    for f, mi in zip(me.polygons, mat_index):
        f.material_index = mi
        f.use_smooth = True
    bmh = bmesh.new()
    bmh.from_mesh(me)
    for e in bmh.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(55):
            e.smooth = False
    bmh.to_mesh(me)
    bmh.free()
    ob = bpy.data.objects.new(spec["name"], me)
    scene.collection.objects.link(ob)
    ob.parent = rig
    ob.matrix_parent_inverse = rig.matrix_world.inverted()
    ob.matrix_world = body.matrix_world.copy()
    for n in sorted({n for d in gw for n in d}):
        ob.vertex_groups.new(name=n)
    for i, d in enumerate(gw):
        for n, v in d.items():
            ob.vertex_groups[n].add([i], float(v), "REPLACE")
    ob.modifiers.new("Armature", "ARMATURE").object = rig
    for o in new + helpers:
        bpy.data.objects.remove(o, do_unlink=True)
    rep.update(vertices=len(Q), polygons=len(faces), bone_groups=len(ob.vertex_groups), slots=slot_names,
               sole_depth_cm=float(max(0.0, -Q[:, 2].min())))
    return ob, rep


fitted = {}
if opt.pants:
    pants, prep = fit_garment("pants", opt.pants, opt.pants_body or str(Path(opt.pants).with_name("SKM_Manny_500_Simple.fbx")))
    meshes.append(pants)
    new_keys["Pants"], garment_report["Pants"] = garment_keys(pants, np.array([v.co[:] for v in pants.data.vertices], dtype=np.float64))
    report["pants"] = prep
    fitted["pants"] = pants
    print("JOY_PANTS", json.dumps({k: v for k, v in prep.items() if k not in ("stretch",)}), flush=True)
jacket = None
if opt.jacket:
    under = fitted.get("pants") or (bpy.data.objects["Underwear_Bottoms"] if bpy.data.objects["Underwear_Bottoms"] in meshes else None)
    jacket, jrep = fit_garment("jacket", opt.jacket, opt.fit_body or str(Path(opt.jacket).with_name("SKM_Female_BodyMesh.fbx")), under)
    meshes.append(jacket)  # no ST keys: the tissue moves underneath it (see fit_garment's clearance)
    report["jacket"] = jrep
    print("JOY_JACKET", json.dumps({k: v for k, v in jrep.items() if k not in ("stretch",)}), flush=True)
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
if opt.jacket or opt.pants:
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_cavity = True
    scene.render.resolution_x, scene.render.resolution_y = 640, 900
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.lens = 70
    for o in scene.objects:
        if o.type == "MESH":
            o.hide_render = o not in meshes or o.name == "Hair"  # the dropped waistcoat is not rendered either
    for g in [o for o in (jacket, fitted.get("pants")) if o]:
        for m in g.data.materials:
            m.diffuse_color = (0.12, 0.12, 0.14, 1) if g is jacket else (0.45, 0.08, 0.1, 1)
    centre = Vector((0, 0, 1.2))
    for name, direction, c, dist in (("front", (0, -1, 0.1), centre, 2.6), ("three_quarter", (0.8, -0.7, 0.1), centre, 2.6), ("side", (1, 0, 0.05), centre, 2.6),
                                     ("back", (0, 1, 0.1), centre, 2.6), ("full_front", (0, -1, 0.05), Vector((0, 0, 0.9)), 4.2), ("full_side", (1, 0, 0.03), Vector((0, 0, 0.9)), 4.2)):
        d = Vector(direction).normalized()
        centre_ = c
        cam.location = c + d * dist
        cam.rotation_euler = (centre_ - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(OUT / ("fit_%s.png" % name))
        bpy.ops.render.render(write_still=True)
print("JOY_ST_EXPORTED", json.dumps({"fbx_bytes": fbx.stat().st_size, "keys": {k: len(v) for k, v in new_keys.items()}, "meshes": report["meshes"]}), flush=True)
