"""Joy's soft-tissue morphs, and optionally the Fab cyber jacket fitted onto her: the SK_Joy reimport FBX.

  blender -b --python author_soft_tissue.py -- <out_dir> [--jacket <SKM_Jacket.fbx exported from Unreal>] [--keep-waistcoat]
      [--pants <SKM_SciFi_PS_P02_UE5.fbx>] [--gstring] [--piercing] [--ring-transform joy_ring_placement.json]
      [--eyes <eyeball .glb>] [--save-blend]

  The in-game build of 2026-10-14 (outfit_v24): --jacket jacket_src/SKM_Jacket.fbx --pants pants_src/SKM_SciFi_PS_P02_UE5.fbx
  --piercing --gstring --ring-transform joy_ring_placement.json --eyes "1.7k large iris...glb" --save-blend

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
Pants + sneakers (owner 2026-10-14, the red Sci-Fi Pants Sneakers p02): fitted through the pack's own SKM_Manny body
(it walks onto her, the pants follow by a smooth displacement field), lowered 6.5 cm overall, the legs sliced level
2.5 cm under the shoe top so the hems sit inside the sneaker collars; sneakers rigid at true size, her hidden feet
removed. --gstring builds a G-string on her skin, --piercing a metal ring on her left brow (--ring-transform: the
owner's own placement from Blender), --eyes the owner's eyeball pick in place of her eyeballs and corneas.
The source joy.blend is never written (sha verified before and after). Textures are not re-exported, except the --eyes
GLB's colour and normal maps.
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
ap.add_argument("--piercing", action="store_true", help="a metal ring through the outer end of her brow")
ap.add_argument("--gstring", action="store_true", help="a G-string built on her skin replaces the briefs (with --pants)")
ap.add_argument("--ring-transform", default="", help="JSON with T_local_cm: the owner's brow ring placement (joy_ring_placement.json)")
ap.add_argument("--eyes", default="", help="an eyeball GLB that replaces her eyeballs and corneas (owner's pick)")
ap.add_argument("--save-blend", action="store_true", help="also save the dressed scene as Joy_outfit.blend (textures packed) to open and inspect")
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
# with pants on, the underwear stays under them: the pants sit low (owner 2026-10-14: "make her wear them like low rise
# ... slightly exposed butt/underwear")
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


# Her body with concave places filled (the cleft, the buttock-to-thigh folds): 20 rounds of neighbour averaging. Pants
# measured against the real skin in the cleft found a side wall facing sideways and were torn into shards pushing both
# ways (owner 2026-10-14: "butt still broken"). Garments that bridge (spec "bridge") keep clear of this surface AND of
# the real skin; the real skin wins on convex places, the bridged one in hollows.
_Pb = P.copy()
for _ in range(20):
    _acc = np.zeros_like(_Pb)
    _cnt = np.zeros(len(_Pb))
    np.add.at(_acc, edges[:, 0], _Pb[edges[:, 1]])
    np.add.at(_acc, edges[:, 1], _Pb[edges[:, 0]])
    np.add.at(_cnt, edges[:, 0], 1)
    np.add.at(_cnt, edges[:, 1], 1)
    _Pb = 0.5 * _Pb + 0.5 * _acc / np.maximum(_cnt, 1)[:, None]
bridge_bvh = BVHTree.FromPolygons([tuple(q) for q in _Pb.tolist()], [tuple(f.vertices) for f in body.data.polygons], all_triangles=False)


def nearest_bridge(q):
    loc, nrm, fi, d = bridge_bvh.find_nearest(Vector(q))
    return np.array(loc), np.array(nrm)


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
        "pants": {"name": "Pants", "keys": True, "gap_cm": 0.5, "open": False, "tighten": (0.38, 0.8), "weights": "skin_sided", "lower_cm": 6.5, "hem_into_shoe_cm": 2.5, "bridge": True, "wrap_iter": 10, "field_transfer_cm": 2.5, "layer_k": 0.35,
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
    if spec.get("wrap_iter"):
        # A fit body far smaller than her (Manny's seat against hers) tears when projected in one shot: some vertices
        # jump many cm, neighbours miss and stay, and the garment bound to it inherits the tear (the pants' seat,
        # traced to this stage 2026-10-14). Instead the fit body walks onto her: snap to her nearest skin, smooth the
        # move over its own surface, repeat.
        joy_w = coords(body, True)
        jbvh = BVHTree.FromPolygons([tuple(q) for q in joy_w.tolist()], [tuple(f.vertices) for f in body.data.polygons], all_triangles=False)
        D = np.zeros_like(P0)
        for _it in range(int(spec["wrap_iter"])):
            cur = P0 + D
            D = np.array([np.array(jbvh.find_nearest(Vector(c))[0]) for c in cur]) - P0
            for _ in range(4):
                acc = np.zeros_like(D)
                cnt = np.zeros(len(D))
                np.add.at(acc, medges[:, 0], D[medges[:, 1]])
                np.add.at(acc, medges[:, 1], D[medges[:, 0]])
                np.add.at(cnt, medges[:, 0], 1)
                np.add.at(cnt, medges[:, 1], 1)
                D = 0.5 * D + 0.5 * acc / np.maximum(cnt, 1)[:, None]
        hit = np.ones(len(D), dtype=bool)
    rep["body_wrap"] = {"vertices": int(len(D)), "projected": int(hit.sum()), "mean_move_cm": float(np.linalg.norm(D, axis=1).mean() * 100),
                        "max_move_cm": float(np.linalg.norm(D, axis=1).max() * 100)}
    P_bones = coords(g_posed)  # posed by the bones alone: rigid parts (shoes) keep this shape
    if spec.get("field_transfer_cm"):
        # The pants are separate panels overlapping a few mm at their seams. Bound by Surface Deform, neighbouring
        # panels took different local frames where the fit body changes shape a lot and their overlap flipped along the
        # back yoke (a zigzag 'tear', 2026-10-14). Here every garment point moves by a smooth Gaussian average of the fit
        # body's own move around it, so panels that touch move alike and keep their layering.
        from mathutils.kdtree import KDTree
        sig = float(spec["field_transfer_cm"]) / 100.0
        kd = KDTree(len(P0))
        for i, q in enumerate(P0):
            kd.insert(Vector(q), i)
        kd.balance()
        G = P_bones.copy()
        disp = np.zeros_like(G)
        for i, g in enumerate(G):
            near = kd.find_range(Vector(g), 2.5 * sig)
            if len(near) < 4:
                near = kd.find_n(Vector(g), 8)
            idx = np.array([j for _, j, _ in near])
            dd = np.array([dist for _, _, dist in near])
            w = np.exp(-(dd / sig) ** 2)
            disp[i] = (D[idx] * w[:, None]).sum(0) / w.sum()
        Qw = G + disp
    else:
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
    stages = {}

    def stage(name):
        if os.environ.get("SS_FIT_STAGES"):
            stages[name] = Q.copy()

    stage("1_wrapped")
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
            for scale in (1.0,):  # true size; her foot below the collar leaves the export (hide_feet_under_shoes)
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
        rep["shoe_collar_cm"] = float(min(Q[rigid & (np.sign(Q[:, 0]) == sg), 2].max() for sg in (1.0, -1.0)))

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

    stage("2_after_rigid")
    if spec["open"]:
        # open the front: front panels (y forward of -4 cm, she faces -Y) move outward from the midline, most at the
        # inner edge, none at the hinge; full through the chest band, a third at the collar top and the hem
        front_w = smoothstep5(-(Q[:, 1] + 4.0) / 4.0)
        inner = np.clip((OPEN_HINGE_CM - np.abs(Q[:, 0])) / OPEN_HINGE_CM, 0.0, 1.0)
        bandw = np.clip(1.0 - np.abs(Q[:, 2] - 135.0) / 30.0, 0.35, 1.0)
        shift = OPEN_CM * inner * bandw * front_w
        Q[:, 0] += np.sign(Q[:, 0]) * shift
        rep["opened"] = {"open_cm": OPEN_CM, "vertices": int((shift > 0.05).sum()), "max_shift_cm": float(shift.max())}

    delete_faces = set()
    hem_z = None
    stage("3_before_lower")
    if spec.get("lower_cm"):
        # Owner 2026-10-14: "all i meant was lowering them overall to sit lower on the waistline, without lengthening the
        # overall pants or making them compress". The whole pants move down as one piece; the cuffs then move up so the
        # hems stop above the sneakers, and the fabric the raised cuffs now cover is cut away (1 cm overlap).
        soft = ~rigid
        Q[soft, 2] -= spec["lower_cm"]
        # Owner 2026-10-14: "shortening overall length so they don't go over shoes", then "some coiling or something
        # above the shoe": lifting the pack's bunched cuff tore it, and cutting whole faces left a saw-toothed edge and a
        # band of bare ankle. The legs now end in a level slice of the finished mesh 'hem_into_shoe_cm' under the shoe
        # top (the collar rim is level within ~1 cm), so the hem sits inside the sneaker collar. Faces wholly 2 cm below
        # that line leave here; the slice itself is made on the finished object.
        hem_z = rep.get("shoe_collar_cm", 0.0) - spec["hem_into_shoe_cm"]
        for fi, f in enumerate(faces):
            if not rigid[f].any() and (Q[f, 2] < hem_z - 2.0).all():
                delete_faces.add(fi)
        cuff_mask = np.zeros(len(Q), dtype=bool)
        rep["lowered"] = {"lower_cm": spec["lower_cm"], "waist_top_after_cm": float(Q[soft, 2].max()), "hem_z_cm": hem_z,
                          "faces_dropped_early": len(delete_faces)}
    stage("4_after_lower")
    if spec.get("low_rise"):
        front_cm, back_cm = spec["low_rise"]
        soft = ~rigid
        z_top = float(Q[soft, 2].max())
        z_from = z_top - 34.0
        t = smoothstep5((Q[:, 2] - z_from) / (z_top - z_from))
        behind = smoothstep5((Q[:, 1] + 2.0) / 8.0)  # she faces -Y: 0 at the front, 1 at the back
        drop = (front_cm + (back_cm - front_cm) * behind) * t
        drop[rigid] = 0.0
        Q[:, 2] -= drop
        rep["low_rise"] = {"front_cm": front_cm, "back_cm": back_cm, "waist_top_before_cm": z_top, "waist_top_after_cm": float(Q[soft, 2].max())}
    if spec.get("tighten"):
        # owner 2026-10-14: "it's very baggy, more form fitting?". The fabric's distance from her skin keeps only
        # `tighten` of what the pack's cut gave it. The change is smoothed over the garment's own surface, so pockets,
        # knee pads and seams keep their relief over the tighter fabric; the shoes (below 12-18 cm) are left alone.
        off = np.zeros(len(Q))
        nrmv = np.zeros((len(Q), 3))
        for i in range(len(Q)):
            if spec.get("bridge"):
                loc, nrm = nearest_bridge(Q[i])
            else:
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
        if spec.get("field_transfer_cm"):
            # separate panels (belt over waistband) must tighten together or their gap closes and they fight: the pull
            # is averaged over space (Gaussian, 2 cm) so stacked layers get the same pull
            from mathutils.kdtree import KDTree
            kdt = KDTree(len(Q))
            for i, q in enumerate(Q):
                kdt.insert(Vector(q), i)
            kdt.balance()
            sm = np.zeros_like(delta)
            for i, q in enumerate(Q):
                near = kdt.find_range(Vector(q), 5.0)
                idx = np.array([j for _, j, _ in near])
                w = np.exp(-(np.array([dd for _, _, dd in near]) / 2.0) ** 2)
                sm[i] = (delta[idx] * w[:, None]).sum(0) / w.sum()
            delta = sm
        for _ in range(0 if spec.get("field_transfer_cm") else 12):
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
    if spec.get("weights") in ("source", "skin_sided"):
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
            if spec.get("weights") == "source" or rigid[i]:
                acc = src_w[i]
            else:
                # Owner 2026-10-14, in game: skin showed through the seat in the idle pose - the pack's weights bend the
                # pants differently from her skin. The skin under each point now drives it, except that a point on one
                # leg never takes the other leg's bones (her thighs touch at rest; that webbed the crotch). The pack's
                # weights say which leg a point is on; the shoes keep the pack's weights.
                legs = {"L": 0.0, "R": 0.0}
                for n_, w_ in src_w[i].items():
                    for sd_ in ("L", "R"):
                        if ("_%s_" % sd_) in n_:
                            legs[sd_] += w_
                total_leg = legs["L"] + legs["R"]
                if total_leg > 0.3:
                    other = "R" if legs["L"] >= legs["R"] else "L"
                    acc = {n_: w_ for n_, w_ in acc.items() if ("_%s_" % other) not in n_}
                if not acc:
                    acc = src_w[i]
        top = sorted(acc.items(), key=lambda kv: -kv[1])[:6]
        s = sum(v for _, v in top)
        gw.append({n: v / s for n, v in top})

    stage("5_after_tighten")
    # clearance. A garment with the paired keys moves with the tissue, so it only clears the skin by its gap. The jacket
    # does not (owner: "her jiggle physics should move underneath the jacket, not with the jacket"), so it clears the
    # tissue's travel where it hangs, at and below the bust line; above it the panel rests near the skin (owner,
    # reviewing the side view: "didn't need to be so tight ... not make a bulge of space").
    clear = np.full(len(Q), spec["gap_cm"])
    if spec.get("lower_cm") and "cuff_mask" in dir():
        clear[cuff_mask] += 0.3  # the lifted cuff sits over the fabric edge it overlaps
    if spec.get("layer_k"):
        # Owner, Blender close-up 2026-10-14: red fabric through the black belt. Belt and fabric under it were pushed
        # to the same 0.5 cm and fought. Each vertex now also keeps layer_k of its height over the body it was cut
        # for (rest_d), so outer layers stay outer.
        clear = clear + spec["layer_k"] * np.minimum(rest_d, 5.0)
        # islands of the garment (panels), and a ray inward from each rest vertex against the other panels
        parent_ = list(range(len(Q)))

        def find_(a):
            while parent_[a] != a:
                parent_[a] = parent_[parent_[a]]
                a = parent_[a]
            return a

        for f in faces:
            for k in range(1, len(f)):
                ra, rb = find_(f[0]), find_(f[k])
                if ra != rb:
                    parent_[rb] = ra
        island = np.array([find_(i) for i in range(len(Q))])
        face_island = np.array([island[f[0]] for f in faces])
        vfaces = [set() for _ in range(len(Q))]
        for fi, f in enumerate(faces):
            for v in f:
                vfaces[v].add(fi)
        rest_bvh_g = BVHTree.FromPolygons([tuple(q) for q in g_rest.tolist()], [tuple(f) for f in faces], all_triangles=False)
        # rest normals of the garment, by area-weighted face normals
        nrm_r = np.zeros_like(g_rest)
        for f in faces:
            a_, b_, c_ = g_rest[f[0]], g_rest[f[1]], g_rest[f[2]]
            fn = np.cross(b_ - a_, c_ - a_)
            for v in f:
                nrm_r[v] += fn
        nrm_r /= np.maximum(np.linalg.norm(nrm_r, axis=1), 1e-12)[:, None]
        b_rest_c = b_rest  # the fit body at rest (captured before it was posed onto her)
        body_rest_bvh = BVHTree.FromPolygons([tuple(q) for q in b_rest_c.tolist()], [tuple(f.vertices) for f in bm.data.polygons], all_triangles=False)
        over = np.zeros(len(Q))
        for i in range(len(Q)):
            if rigid[i]:
                continue
            # inward = towards the fit body
            bl, bn, bi, bd = body_rest_bvh.find_nearest(Vector(g_rest[i]))
            inward = np.array(bl) - g_rest[i]
            nin = np.linalg.norm(inward)
            if nin < 1e-6:
                continue
            inward /= nin
            o_ = Vector(g_rest[i] + inward * 0.0002)
            hit = rest_bvh_g.ray_cast(o_, Vector(inward), 0.012)
            if hit[0] is not None and face_island[hit[2]] != island[i]:  # other panels only (owner: belt is fine as it is)
                over[i] = hit[3] * 100.0
        clear = clear + over
        rep["layer_over"] = {"vertices_over_another_panel": int((over > 0).sum()), "max_cm": float(over.max())}
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
    if spec.get("layered_push"):
        # The pants are layered at the seat (waistband facing, pocket linings): pushing each vertex alone moved an
        # inner layer out through the outer one and tore the seat. Each push now also carries everything within R cm
        # with it (falling off to nothing at R), so stacked layers move together and the push has no hard edge.
        from mathutils.kdtree import KDTree
        R_ = float(spec["layered_push"])
        need = np.zeros_like(Q)
        for i in range(len(Q)):
            if rigid[i]:
                continue
            loc, nrm, d, verts, w = nearest_body(Q[i])
            sd0 = float(np.dot(Q[i] - loc, nrm))
            if sd0 < clear[i]:
                need[i] = (clear[i] - sd0) * nrm
        kd = KDTree(len(Q))
        for i, q in enumerate(Q):
            kd.insert(Vector(q), i)
        kd.balance()
        carry = np.zeros_like(Q)
        mag = np.zeros(len(Q))
        for i in np.flatnonzero(np.linalg.norm(need, axis=1) > 1e-6):
            for co, j, dist in kd.find_range(Vector(Q[i]), R_):
                if rigid[j]:
                    continue
                f = 1.0 - smoothstep5(dist / R_)
                m = float(np.linalg.norm(need[i])) * f
                if m > mag[j]:
                    mag[j] = m
                    carry[j] = need[i] * f
        Q = Q + carry
        rep["layered_push"] = {"radius_cm": R_, "pushed": int((np.linalg.norm(need, axis=1) > 1e-6).sum()), "carried": int((mag > 1e-6).sum()),
                               "max_cm": float(mag.max())}
    for _ in range(3):
        for i in range(len(Q)):
            if rigid[i]:
                continue
            if spec.get("bridge"):
                bl_, bn_ = nearest_bridge(Q[i])
                if float(np.dot(Q[i] - bl_, bn_)) < clear[i]:
                    Q[i] = bl_ + bn_ * clear[i]
                    moved += 1
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
    if spec.get("lower_cm") and "island" in dir():
        # Owner 2026-10-14 (Blender close-up): red fabric through the black belt. Panels whose every vertex lies in the top
        # 8 cm of the pants are the belt, loops and buckle; each is held 0.3 cm outside the rest of the pants surface.
        soft_ = ~rigid
        z_top_now = float(Q[soft_, 2].max())
        isl_ids = np.unique(island[soft_])
        belt_isl = [k for k in isl_ids if (Q[island == k, 2] > z_top_now - 8.0).all()]
        beltv = np.isin(island, belt_isl) & soft_
        rest_faces = [f for f in faces if not beltv[f].any() and not rigid[f].any()]
        if beltv.any() and rest_faces:
            fab_bvh = BVHTree.FromPolygons([tuple(q) for q in Q.tolist()], [tuple(f) for f in rest_faces], all_triangles=False)
            pushed_b = 0
            for i in np.flatnonzero(beltv):
                fl, fn, fi_, fd = fab_bvh.find_nearest(Vector(Q[i]))
                if fl is None or fd > 2.0:
                    continue
                fl, fn = np.array(fl), np.array(fn)
                # the fabric normal faces out of the body: compare with her skin normal there
                bl_, bn_, _d, _v, _w = nearest_body(fl)
                if np.dot(fn, bn_) < 0:
                    fn = -fn
                sd_ = float(np.dot(Q[i] - fl, fn))
                if sd_ < 0.3:
                    Q[i] = Q[i] + fn * (0.3 - sd_)
                    pushed_b += 1
            rep["belt_over_fabric"] = {"panels": len(belt_isl), "vertices": int(beltv.sum()), "pushed": pushed_b}
    stage("7_after_push")
    if spec.get("field_transfer_cm"):
        # Seams: panel edges that touched in the pack's own mesh (within 0.4 cm, posed) are stitched back together, so
        # a seam the fit pulled a few mm apart (the crotch, front and back) shows no skin through it
        from mathutils.kdtree import KDTree
        ecount = {}
        for f in faces:
            for k in range(len(f)):
                e = tuple(sorted((f[k], f[(k + 1) % len(f)])))
                ecount[e] = ecount.get(e, 0) + 1
        border = sorted({v for e, c in ecount.items() if c == 1 for v in e})
        Pb_cm = np.array([(BWinv @ np.r_[q, 1])[:3] for q in P_bones])
        kdb = KDTree(len(border))
        for k, v in enumerate(border):
            kdb.insert(Vector(Pb_cm[v]), k)
        kdb.balance()
        seen, stitched = set(), 0
        for k, v in enumerate(border):
            if v in seen or rigid[v]:
                continue
            group = [border[j] for _, j, _ in kdb.find_range(Vector(Pb_cm[v]), 0.4)
                     if not rigid[border[j]] and abs(rest_d[border[j]] - rest_d[v]) < 0.2]  # same layer only
            if len(group) > 1:
                Q[group] = Q[group].mean(0)
                seen.update(group)
                stitched += 1
        rep["seams_stitched"] = stitched
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
    if delete_faces:
        bpy.context.view_layer.objects.active = ob
        for o in scene.objects:
            o.select_set(o is ob)
        bpy.ops.object.mode_set(mode="EDIT")
        bmg = bmesh.from_edit_mesh(ob.data)
        bmg.faces.ensure_lookup_table()
        bmesh.ops.delete(bmg, geom=[bmg.faces[i] for i in sorted(delete_faces)], context="FACES_ONLY")
        bmesh.ops.delete(bmg, geom=[v for v in bmg.verts if not v.link_faces], context="VERTS")
        bmesh.update_edit_mesh(ob.data)
        bpy.ops.object.mode_set(mode="OBJECT")
    if hem_z is not None:
        # the level hem: the fabric (never the shoes) is sliced at hem_z and everything under the slice removed; the
        # slice interpolates UVs and bone weights on the new edge
        shoe_mi = {i for i, n in enumerate(slot_names) if n in spec.get("rigid_slots", ())}
        bpy.context.view_layer.objects.active = ob
        for o in scene.objects:
            o.select_set(o is ob)
        bpy.ops.object.mode_set(mode="EDIT")
        bmg = bmesh.from_edit_mesh(ob.data)
        fab_f = [f for f in bmg.faces if f.material_index not in shoe_mi]
        fab_e = list({e for f in fab_f for e in f.edges})
        fab_v = list({v for f in fab_f for v in f.verts})
        bmesh.ops.bisect_plane(bmg, geom=fab_f + fab_e + fab_v, dist=1e-4, plane_co=(0.0, 0.0, hem_z), plane_no=(0.0, 0.0, 1.0), clear_inner=True)
        bmesh.ops.delete(bmg, geom=[v for v in bmg.verts if not v.link_faces], context="VERTS")
        bmesh.update_edit_mesh(ob.data)
        bpy.ops.object.mode_set(mode="OBJECT")
        # inside the collar the fabric must stay inside the shoe's inner wall: a horizontal ray from the leg's axis
        # finds the wall at each vertex height, and fabric reaching within 0.25 cm of it is drawn in to that distance
        Vf = np.array([v.co[:] for v in ob.data.vertices])
        is_shoe = np.zeros(len(Vf), dtype=bool)
        is_fab = np.zeros(len(Vf), dtype=bool)
        shoe_polys = []
        for pl in ob.data.polygons:
            if pl.material_index in shoe_mi:
                is_shoe[list(pl.vertices)] = True
                shoe_polys.append(tuple(pl.vertices))
            else:
                is_fab[list(pl.vertices)] = True
        sbvh = BVHTree.FromPolygons([tuple(q) for q in Vf.tolist()], shoe_polys, all_triangles=False)
        shoe_top = float(Vf[is_shoe, 2].max())
        tucked, deepest = 0, 0.0
        for sg in (1.0, -1.0):
            leg = is_fab & (np.sign(Vf[:, 0]) == sg)
            ring = leg & (Vf[:, 2] < hem_z + 4.0)
            cx, cy = float(Vf[ring, 0].mean()), float(Vf[ring, 1].mean())
            for i in np.flatnonzero(leg & (Vf[:, 2] < shoe_top + 0.3)):
                d = np.array([Vf[i, 0] - cx, Vf[i, 1] - cy])
                r = float(np.linalg.norm(d))
                if r < 1e-6:
                    continue
                d /= r
                hit = sbvh.ray_cast(Vector((cx, cy, Vf[i, 2])), Vector((d[0], d[1], 0.0)), 40.0)
                if hit[0] is None or r <= hit[3] - 0.25:
                    continue
                deepest = max(deepest, r - (hit[3] - 0.25))
                Vf[i, :2] = np.array([cx, cy]) + d * (hit[3] - 0.25)
                tucked += 1
        ob.data.vertices.foreach_set("co", Vf.ravel())
        ob.data.update()
        rep["hem"] = {"z_cm": hem_z, "shoe_top_cm": shoe_top, "fabric_min_z_cm": float(Vf[is_fab, 2].min()),
                      "tucked_inside_collar": tucked, "deepest_tuck_cm": deepest}
    for o in new + helpers:
        bpy.data.objects.remove(o, do_unlink=True)
    if stages:
        np.savez(str(OUT / ("stages_%s.npz" % kind)), **stages)
        (OUT / ("stages_%s_faces.json" % kind)).write_text(json.dumps(faces))
    rep.update(vertices=len(ob.data.vertices), polygons=len(ob.data.polygons), bone_groups=len(ob.vertex_groups), slots=slot_names,
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
def add_gstring():
    """A G-string built on her skin (owner 2026-10-14: "create a g string", low-rise references): waist strings that
    ride high over the hip bones and dip at the front and back, a small front panel and a back string down the cleft.
    Every vertex sits 0.15 cm off her skin, takes her weights, and carries the paired hip keys like the pants."""
    ax = np.array([0.0, 2.0])  # the vertical axis through her pelvis (x, y), cm
    z_front, z_side, z_back = 101.0, 111.5, 109.0

    def waist_z(theta):  # theta 0 = front (-Y), pi/2 = her left (+X), pi = back; flat over the hip, no corner
        c = math.cos(theta)
        return z_side - (z_side - (z_front if c > 0 else z_back)) * c * c

    def surface(origin, direction):
        hit, loc, nrm, fi = body.ray_cast(Vector(origin), Vector(direction), distance=60.0)
        return (np.array(loc), np.array(nrm)) if hit else (None, None)

    verts, faces_g = [], []

    def strip(points, normals, half_w, up_dirs, closed=False):
        # owner 2026-10-14: the string's edge wobbled. Points from raw hits on her faceted skin are smoothed along the
        # string (positions and normals), and the width runs across the string (normal x tangent), not straight up.
        pts = np.array(points, dtype=np.float64)
        nrm = np.array(normals, dtype=np.float64)
        n_ = len(pts)
        for _ in range(8):
            if closed:
                pts = 0.5 * pts + 0.25 * (np.roll(pts, 1, 0) + np.roll(pts, -1, 0))
                nrm = 0.5 * nrm + 0.25 * (np.roll(nrm, 1, 0) + np.roll(nrm, -1, 0))
            else:
                pts[1:-1] = 0.5 * pts[1:-1] + 0.25 * (pts[:-2] + pts[2:])
                nrm[1:-1] = 0.5 * nrm[1:-1] + 0.25 * (nrm[:-2] + nrm[2:])
        nrm /= np.linalg.norm(nrm, axis=1)[:, None]
        base = len(verts)
        for k in range(n_):
            if closed:
                t = pts[(k + 1) % n_] - pts[(k - 1) % n_]
            else:
                t = pts[min(k + 1, n_ - 1)] - pts[max(k - 1, 0)]
            across = np.cross(nrm[k], t)
            across /= max(np.linalg.norm(across), 1e-9)
            if np.dot(across, up_dirs[k]) < 0:
                across = -across
            verts.append(pts[k] + nrm[k] * 0.2 + across * half_w)
            verts.append(pts[k] + nrm[k] * 0.2 - across * half_w)
        last = n_ if closed else n_ - 1
        for k in range(last):
            a = base + 2 * k
            b = base + 2 * ((k + 1) % n_)
            faces_g.append((a, b, b + 1, a + 1))
        return base

    # waist string: a closed loop, cast inward from outside at each angle
    loop_p, loop_n = [], []
    for k in range(192):
        th = 2 * math.pi * k / 192
        d = np.array([math.sin(th), -math.cos(th), 0.0])
        z = waist_z(th)
        o = np.array([ax[0], ax[1], z]) + d * 40.0
        loc, nrm = surface(o, -d)
        if loc is None:
            continue
        loop_p.append(loc)
        loop_n.append(nrm)
    up = [np.array([0.0, 0.0, 1.0])] * len(loop_p)
    strip(loop_p, loop_n, 0.3, up, closed=True)
    # front panel: a narrow triangle from the front of the string to the crotch, cast from the front
    rows = 10
    pts_grid = []
    for r in range(rows + 1):
        t = r / rows
        z = z_front - t * 13.0
        w = 3.2 * (1 - t) + 0.9 * t
        row = []
        for c in range(5):
            x = -w + 2 * w * c / 4
            loc, nrm = surface((x, -40.0, z), (0.0, 1.0, 0.0))
            row.append((loc, nrm))
        pts_grid.append(row)
    base = len(verts)
    for r_, row in enumerate(pts_grid):
        for c_, (loc, nrm) in enumerate(row):
            if loc is None:
                # a ray that slipped between her thighs: the nearest skin to the point it aimed at (never the origin,
                # which drew a line from her crotch to the floor)
                t = r_ / rows
                aim = np.array([-(3.2 * (1 - t) + 0.9 * t) + 2 * (3.2 * (1 - t) + 0.9 * t) * c_ / 4, -12.0, z_front - t * 13.0])
                loc, nrm, _d, _v, _w = nearest_body(aim)
            verts.append(loc + nrm * 0.15)
    for r in range(rows):
        for c in range(4):
            a = base + r * 5 + c
            faces_g.append((a, a + 1, a + 6, a + 5))
    # back string: down the cleft from the back of the string, cast from behind
    back_p, back_n = [], []
    for k in range(18):
        z = z_back - k * 1.2
        loc, nrm = surface((0.0, 40.0, z), (0.0, -1.0, 0.0))
        if loc is not None:
            back_p.append(loc)
            back_n.append(nrm)
    strip(back_p, back_n, 0.4, [np.array([1.0, 0.0, 0.0])] * len(back_p))
    me = bpy.data.meshes.new("GString")
    me.from_pydata([tuple(v) for v in verts], [], faces_g)
    me.update()
    me.uv_layers.new(name="UVMap")
    for f in me.polygons:
        f.use_smooth = True
    me.materials.append(bpy.data.materials.new("GString"))
    ob = bpy.data.objects.new("GString", me)
    scene.collection.objects.link(ob)
    ob.parent = rig
    ob.matrix_parent_inverse = rig.matrix_world.inverted()
    ob.matrix_world = body.matrix_world.copy()
    groups_ = {gr.index: gr.name for gr in body.vertex_groups if gr.name in bone_names}
    for i, v in enumerate(me.vertices):
        loc, nrm, d, fverts, w = nearest_body(np.array(v.co))
        acc = {}
        for vi, wi in zip(fverts, w):
            for g in body.data.vertices[vi].groups:
                if g.group in groups_ and g.weight > 0:
                    acc[groups_[g.group]] = acc.get(groups_[g.group], 0.0) + wi * g.weight
        tot = sum(acc.values())
        for n_, wv in acc.items():
            vg = ob.vertex_groups.get(n_) or ob.vertex_groups.new(name=n_)
            vg.add([i], wv / tot, "REPLACE")
    ob.modifiers.new("Armature", "ARMATURE").object = rig
    return ob, {"vertices": len(verts), "faces": len(faces_g), "waist_z_front_side_back_cm": [z_front, z_side, z_back]}


if opt.pants and opt.gstring:
    gs, gs_rep = add_gstring()
    meshes.append(gs)
    new_keys["GString"], garment_report["GString"] = garment_keys(gs, np.array([v.co[:] for v in gs.data.vertices], dtype=np.float64))
    report["gstring"] = gs_rep
    # the briefs leave the export: the G-string replaces them
    uwb = bpy.data.objects["Underwear_Bottoms"]
    if uwb in meshes:
        meshes.remove(uwb)
    print("JOY_GSTRING", json.dumps(gs_rep), flush=True)

if opt.pants and not opt.gstring:
    # The underwear under low-rise pants: only the strip above the waistband is ever seen. Everything within 4 cm of the
    # pants surface, inside or outside it, leaves the export, so it can never show through (pushing the pants out over
    # it tore the seat into shards, 2026-10-14).
    uw = bpy.data.objects["Underwear_Bottoms"]
    PQ = np.array([v.co[:] for v in pants.data.vertices], dtype=np.float64)
    pants_bvh = BVHTree.FromPolygons([tuple(q) for q in PQ.tolist()], [tuple(f.vertices) for f in pants.data.polygons], all_triangles=False)
    covered = set()
    for v in uw.data.vertices:
        co, nv = Vector(v.co), Vector(v.normal)
        hit_out = pants_bvh.ray_cast(co, nv, 4.0)[0]
        hit_in = pants_bvh.ray_cast(co, -nv, 4.0)[0]
        near = pants_bvh.find_nearest(co)
        if hit_out is not None or hit_in is not None or (near[0] is not None and near[3] < 0.8):
            covered.add(v.index)
    bpy.context.view_layer.objects.active = uw
    for o in scene.objects:
        o.select_set(o is uw)
    bpy.ops.object.mode_set(mode="EDIT")
    bmu = bmesh.from_edit_mesh(uw.data)
    bmu.verts.ensure_lookup_table()
    gone = [f for f in bmu.faces if all(v.index in covered for v in f.verts)]
    bmesh.ops.delete(bmu, geom=gone, context="FACES_ONLY")
    bmesh.ops.delete(bmu, geom=[v for v in bmu.verts if not v.link_faces], context="VERTS")
    bmesh.update_edit_mesh(uw.data)
    bpy.ops.object.mode_set(mode="OBJECT")
    report["underwear_under_pants"] = {"faces_removed": len(gone), "vertices_left": len(uw.data.vertices)}
    print("JOY_UNDERWEAR", json.dumps(report["underwear_under_pants"]), flush=True)
    assert len(uw.data.vertices) > 0, "no underwear left above the waistband"
jacket = None
if opt.jacket:
    under = fitted.get("pants") or (bpy.data.objects["Underwear_Bottoms"] if bpy.data.objects["Underwear_Bottoms"] in meshes else None)
    jacket, jrep = fit_garment("jacket", opt.jacket, opt.fit_body or str(Path(opt.jacket).with_name("SKM_Female_BodyMesh.fbx")), under)
    meshes.append(jacket)  # no ST keys: the tissue moves underneath it (see fit_garment's clearance)
    report["jacket"] = jrep
    print("JOY_JACKET", json.dumps({k: v for k, v in jrep.items() if k not in ("stretch",)}), flush=True)
print("JOY_ST_GARMENTS", json.dumps(garment_report), flush=True)
report["meshes"] = [o.name for o in meshes]

def add_brow_ring(side="R"):
    """A metal ring through the outer end of her brow (owner 2026-10-14: "eyebrow piercing, metal. like the image").
    The ring takes its skin weights and every expression key that moves the skin under it, so it rides the brow."""
    eye = np.array(rig.data.bones["CC_Base_%s_Eye" % side].head_local)  # armature cm == body local cm here
    sgn = 1.0 if side == "L" else -1.0
    start = eye + np.array([sgn * 2.0, -12.0, 1.9])
    hit, loc, nrm, fi = body.ray_cast(Vector(start), Vector((0.0, 1.0, 0.0)), distance=30.0)
    assert hit, "no brow under the ring"
    S, n = np.array(loc), np.array(nrm)
    up = np.array([0.0, 0.0, 1.0]) - n * n[2]
    up /= np.linalg.norm(up)
    R_, r_ = 0.5, 0.09  # ring radius and wire radius, cm
    seg, wseg = 32, 10
    verts, faces_ = [], []
    centre = S + n * 0.05
    for i in range(seg):
        a = 2 * math.pi * i / seg
        c = centre + R_ * (math.cos(a) * n + math.sin(a) * up)
        radial = (c - centre) / R_
        side_axis = np.cross(n, up)
        for j in range(wseg):
            b = 2 * math.pi * j / wseg
            verts.append(c + r_ * (math.cos(b) * radial + math.sin(b) * side_axis))
    for i in range(seg):
        for j in range(wseg):
            a0, a1 = i * wseg + j, i * wseg + (j + 1) % wseg
            b0, b1 = ((i + 1) % seg) * wseg + j, ((i + 1) % seg) * wseg + (j + 1) % wseg
            faces_.append((a0, b0, b1, a1))
    placed = None
    if opt.ring_transform:
        # owner 2026-10-14: placed by hand in Blender (joy_ring_placement.json, Kabsch from the built ring to theirs)
        T_ring = np.array(json.loads(Path(opt.ring_transform).read_text())["T_local_cm"])
        verts = [(T_ring @ np.r_[np.array(v), 1])[:3] for v in verts]
        S = (T_ring @ np.r_[S, 1])[:3]
        placed = opt.ring_transform
    me = bpy.data.meshes.new("BrowRing")
    me.from_pydata([tuple(v) for v in verts], [], faces_)
    me.update()
    for f in me.polygons:
        f.use_smooth = True
    me.materials.append(bpy.data.materials.new("Piercing"))
    ob = bpy.data.objects.new("BrowRing", me)
    scene.collection.objects.link(ob)
    ob.parent = rig
    ob.matrix_parent_inverse = rig.matrix_world.inverted()
    ob.matrix_world = body.matrix_world.copy()
    loc2, nrm2, d2, fverts, w = nearest_body(S)
    groups_ = {gr.index: gr.name for gr in body.vertex_groups if gr.name in bone_names}
    acc = {}
    for vi, wi in zip(fverts, w):
        for g in body.data.vertices[vi].groups:
            if g.group in groups_ and g.weight > 0:
                acc[groups_[g.group]] = acc.get(groups_[g.group], 0.0) + wi * g.weight
    total = sum(acc.values())
    for name_, wv in acc.items():
        ob.vertex_groups.new(name=name_).add(list(range(len(verts))), wv / total, "REPLACE")
    ob.modifiers.new("Armature", "ARMATURE").object = rig
    # every body key that moves the brow moves the ring by the same amount
    ob.shape_key_add(name="Basis", from_mix=False)
    base_v = np.array(verts)
    carried = []
    for kb in keys.key_blocks[1:]:
        dv = sum(wi * (np.array(kb.data[vi].co) - P[vi]) for vi, wi in zip(fverts, w))
        if np.linalg.norm(dv) > 0.02:
            k = ob.shape_key_add(name=kb.name, from_mix=False)
            k.data.foreach_set("co", (base_v + dv).astype(np.float32).ravel())
            carried.append(kb.name)
    return ob, {"side": side, "at_cm": S.tolist(), "normal": n.tolist(), "owner_placement": placed, "bones": {k: round(v / total, 3) for k, v in acc.items()}, "keys_carried": carried}


if opt.piercing:
    ring, ring_rep = add_brow_ring("L")  # her bob covers the right temple; the left brow end stays clear
    meshes.append(ring)
    report["piercing"] = ring_rep
    print("JOY_PIERCING", json.dumps({k: (v if k != "keys_carried" else len(v)) for k, v in ring_rep.items()}), flush=True)

def add_eye_option(path):
    """The owner's eyeball pick (2026-10-14, Blender what-if file: '1.7k large iris'): a pair from the GLB, each scaled
    to her eyeball (sphere fit of her own eye halves), centred in her sockets, weighted wholly to her eye bones, one
    material slot 'Eye_Option'. Her original eyeballs and corneas leave the export; the GLB's colour and normal maps are
    written beside the FBX for Unreal."""
    eo = bpy.data.objects["CC_Base_Eye"]
    BWi = np.linalg.inv(BODY_W)
    EW = np.array(eo.matrix_world)
    EV = np.array([(BWi @ EW @ np.r_[np.array(v.co), 1])[:3] for v in eo.data.vertices])  # Joy local cm

    def fit(Pts):
        A_ = np.c_[2 * Pts, np.ones(len(Pts))]
        c_, *_ = np.linalg.lstsq(A_, (Pts ** 2).sum(1), rcond=None)
        return c_[:3], math.sqrt(c_[3] + (c_[:3] ** 2).sum())

    cL, rL = fit(EV[EV[:, 0] > 0])
    cR, rR = fit(EV[EV[:, 0] < 0])
    before_ = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new_ = [o for o in bpy.data.objects if o not in before_]
    ms = [o for o in new_ if o.type == "MESH"]
    for o in new_:
        o.select_set(o in ms)
    bpy.context.view_layer.objects.active = ms[0]
    if len(ms) > 1:
        bpy.ops.object.join()
    src = bpy.context.view_layer.objects.active
    src.parent = None
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    G = np.array([v.co[:] for v in src.data.vertices]) * 100.0  # metres -> cm
    mid = (G.min(0) + G.max(0)) / 2
    size = float((G.max(0) - G.min(0)).max())
    out_objs, mat = [], src.data.materials[0]
    mat.name = "Eye_Option"
    # textures for Unreal
    tex = {}
    for nd in mat.node_tree.nodes:
        if nd.type == "TEX_IMAGE" and nd.image:
            to = [l.to_socket.name for l in nd.outputs["Color"].links]
            kind = "BaseColor" if "Base Color" in to else "Normal" if any(l.to_node.type == "NORMAL_MAP" for l in nd.outputs["Color"].links) else None
            if kind:
                pth = OUT / ("T_Joy_EyeOption_%s.png" % kind)
                img = nd.image
                img.filepath_raw = str(pth)
                img.file_format = "PNG"
                img.save()
                tex[kind] = str(pth)
    for side, c_, r_ in (("L", cL, rL), ("R", cR, rR)):
        V_ = (G - mid) * (2 * r_ / size) + c_
        me_ = bpy.data.meshes.new("EyeOption_" + side)
        me_.from_pydata([tuple(v) for v in V_], [], [tuple(f.vertices) for f in src.data.polygons])
        me_.update()
        if src.data.uv_layers:
            uv_ = me_.uv_layers.new(name="UVMap")
            uv_.data.foreach_set("uv", np.array([d.uv[:] for d in src.data.uv_layers.active.data]).ravel())
        for f_ in me_.polygons:
            f_.use_smooth = True
        me_.materials.append(mat)
        ob_ = bpy.data.objects.new("EyeOption_" + side, me_)
        scene.collection.objects.link(ob_)
        ob_.parent = rig
        ob_.matrix_parent_inverse = rig.matrix_world.inverted()
        ob_.matrix_world = body.matrix_world.copy()
        ob_.vertex_groups.new(name="CC_Base_%s_Eye" % side).add(list(range(len(V_))), 1.0, "REPLACE")
        ob_.modifiers.new("Armature", "ARMATURE").object = rig
        out_objs.append(ob_)
    for o in new_:
        if o.name in bpy.data.objects:
            bpy.data.objects.remove(o, do_unlink=True)
    # her own eye keys that live on no other exported mesh go with the original eyes
    eye_keys = {k.name for k in eo.data.shape_keys.key_blocks[1:]} if eo.data.shape_keys else set()
    others = set()
    for o in meshes:
        if o is not eo and o.type == "MESH" and o.data.shape_keys:
            others |= {k.name for k in o.data.shape_keys.key_blocks}
    if eo in meshes:
        meshes.remove(eo)
    return out_objs, {"source": path, "centres_cm": [cL.tolist(), cR.tolist()], "diameter_cm": [2 * rL, 2 * rR],
                      "triangles_each": sum(len(f.vertices) - 2 for f in out_objs[0].data.polygons), "textures": tex,
                      "dropped_morphs_expected": sorted(eye_keys - others)}


if opt.eyes:
    eye_objs, eye_rep = add_eye_option(opt.eyes)
    meshes.extend(eye_objs)
    report["eyes"] = eye_rep
    report["dropped_morphs_expected"] = eye_rep["dropped_morphs_expected"]
    print("JOY_EYES", json.dumps({k: v for k, v in eye_rep.items() if k != "centres_cm"}), flush=True)

if opt.pants and report.get("pants", {}).get("shoe_collar_cm"):
    # her feet below the shoe collar are never seen: they leave the export, so a toe can never show through a shoe
    cut = report["pants"]["shoe_collar_cm"] - 1.5
    bpy.context.view_layer.objects.active = body
    for o in scene.objects:
        o.select_set(o is body)
    bpy.ops.object.mode_set(mode="EDIT")
    bmh = bmesh.from_edit_mesh(body.data)
    gone = [f for f in bmh.faces if all(v.co.z < cut for v in f.verts)]
    bmesh.ops.delete(bmh, geom=gone, context="FACES_ONLY")
    loose = [v for v in bmh.verts if not v.link_faces]
    bmesh.ops.delete(bmh, geom=loose, context="VERTS")
    bmesh.update_edit_mesh(body.data)
    bpy.ops.object.mode_set(mode="OBJECT")
    report["hidden_feet"] = {"cut_z_cm": cut, "faces_removed": len(gone), "body_vertices_after": len(body.data.vertices),
                             "body_keys_after": len(body.data.shape_keys.key_blocks)}
    print("JOY_FEET", json.dumps(report["hidden_feet"]), flush=True)

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
    if opt.piercing:
        ring.data.materials[0].diffuse_color = (0.05, 0.05, 0.06, 1)
    if report.get("gstring"):
        gs.data.materials[0].diffuse_color = (0.02, 0.02, 0.02, 1)
    for g in [o for o in (jacket, fitted.get("pants")) if o]:
        for m in g.data.materials:
            m.diffuse_color = (0.12, 0.12, 0.14, 1) if g is jacket else (0.45, 0.08, 0.1, 1)
    centre = Vector((0, 0, 1.2))
    for name, direction, c, dist in (("front", (0, -1, 0.1), centre, 2.6), ("three_quarter", (0.8, -0.7, 0.1), centre, 2.6), ("side", (1, 0, 0.05), centre, 2.6),
                                     ("back", (0, 1, 0.1), centre, 2.6), ("full_front", (0, -1, 0.05), Vector((0, 0, 0.9)), 4.2), ("full_side", (1, 0, 0.03), Vector((0, 0, 0.9)), 4.2),
                                     ("hips_back", (0.25, 1, 0.05), Vector((0, 0.05, 1.0)), 1.6), ("brow", (0.35, -1, 0.05), Vector((0.05, -0.09, 1.70)), 0.4),
                                     ("hips_front", (0.25, -1, 0.05), Vector((0, -0.05, 1.02)), 1.5), ("hips_side", (1, -0.1, 0.05), Vector((0, 0.0, 1.02)), 1.5),
                                     ("rear_close", (0, 1, 0.0), Vector((0, 0.08, 0.93)), 0.9), ("rear_low_34", (0.6, 1, -0.35), Vector((0, 0.08, 0.92)), 1.0)):
        d = Vector(direction).normalized()
        centre_ = c
        cam.location = c + d * dist
        cam.rotation_euler = (centre_ - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(OUT / ("fit_%s.png" % name))
        bpy.ops.render.render(write_still=True)
print("JOY_ST_EXPORTED", json.dumps({"fbx_bytes": fbx.stat().st_size, "keys": {k: len(v) for k, v in new_keys.items()}, "meshes": report["meshes"]}), flush=True)

if opt.save_blend:
    # A self-contained file of her as exported, for the owner to open and look at (2026-10-14): the pack textures that
    # Blender has (her own are packed in joy.blend; the pants' red base colour is the exported c3 texture), simple
    # stand-ins for the rest, the dropped waistcoat and briefs removed.
    for o in list(scene.objects):
        if o.type == "MESH" and o not in meshes:
            bpy.data.objects.remove(o, do_unlink=True)
    for o in [o for o in scene.objects if o.type in ("CAMERA", "LIGHT")]:
        bpy.data.objects.remove(o, do_unlink=True)

    def simple(mat, rgb, rough=0.5, metal=0.0, image=None):
        mat.use_nodes = True
        nt = mat.node_tree
        bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Base Color"].default_value = (*rgb, 1)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
        if image is not None:
            tex = nt.nodes.new("ShaderNodeTexImage")
            tex.image = image
            nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        mat.diffuse_color = (*rgb, 1)

    if opt.pants:
        red = Path(opt.pants).with_name("T_SciFi_Pack_02_PS_c3_Base_color.tga")
        img = bpy.data.images.load(str(red)) if red.exists() else None
        for m in fitted["pants"].data.materials:
            simple(m, (0.45, 0.06, 0.08), 0.45, 0.0, img)
    if jacket:
        for m in jacket.data.materials:
            simple(m, (0.05, 0.04, 0.035), 0.35)
    if report.get("gstring"):
        simple(gs.data.materials[0], (0.01, 0.01, 0.012), 0.45)
    if opt.piercing:
        simple(ring.data.materials[0], (0.7, 0.7, 0.72), 0.2, 1.0)
    # the pack FBXes carry texture paths from their makers' machines; those dead references cannot be packed
    for im in list(bpy.data.images):
        if im.packed_file is None and im.source == "FILE" and not Path(bpy.path.abspath(im.filepath)).exists():
            bpy.data.images.remove(im)
    bpy.ops.file.pack_all()
    out_blend = OUT / "Joy_outfit.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(out_blend), copy=True, compress=True)
    print("JOY_BLEND_SAVED", str(out_blend), flush=True)
