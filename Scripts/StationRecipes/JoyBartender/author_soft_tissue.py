"""Joy's soft-tissue morphs: the ST_<Region>_<Axis> shape keys that Silver's BodyDynamics spring component
(USSSoftTissueComponent) drives, authored on the ORIGINAL Fab Joy body, her waistcoat and her bottoms, then exported as
the SK_Joy reimport FBX together with the bone anchors the component reads at BeginPlay.

  blender -b --python author_soft_tissue.py -- <out_dir>

Owner 2026-10-14: "add the same jiggle physics on silvers new character to bartender joy" / "blueprint driven with a
spring something". Silver's mechanism (ViableEld scripts/author_soft_tissue.py, .agent/local/ViableEldFinish_20261013):
four masked regions (Breast_L/R, Hip_L/R), three shape keys per region displacing the masked skin 1 cm along the rest
X/Y/Z, the garment carrying paired keys of the same names, and per-region anchors (mask^2-weighted bone influences and
rest centroids, in centimetres) for the component. The spring values are copied unchanged from Silver's adopted
component by place_joy_soft_tissue.py. Masks here are Joy's own measurements (scratchpad measure_joy_tissue.py,
2026-10-14): breast apex (+-10.1, -15.1, 135.3) cm on a chest wall at y -10, glute apex (+-7.8, 15.0, 95.2) cm with the
bulge spanning z 86..103. CC objects are scaled 0.01, so object-local units are centimetres and 1 local unit = 1 cm.
The source joy.blend is never written (sha verified before and after). Textures are not re-exported: the reimport keeps
SK_Joy's materials.
"""
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

SRC = Path("M:/SpaceSurvival/UserDownloadedAssets_SpaceSurvival/Content/VaultCache/FabLibrary/Joy-c6f24fcb/blender/joy.blend")
SRC_SHA = "8582f2f269e8"
OUT = Path(sys.argv[sys.argv.index("--") + 1])
OUT.mkdir(parents=True, exist_ok=False)
KEY_CM = 1.0  # one morph unit moves the mask centre one centimetre (CentimetresPerMorphUnit = 1)
REGIONS = ("Breast_L", "Breast_R", "Hip_L", "Hip_R")
GARMENTS = ("waistcoat", "Underwear_Bottoms")
REFERENCE_BONES = ("CC_Base_Pelvis", "CC_Base_Head", "CC_Base_L_Hand", "CC_Base_R_Hand", "CC_Base_L_Foot", "CC_Base_R_Foot")


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
for o in [body] + [bpy.data.objects[g] for g in GARMENTS]:
    s = np.array(o.matrix_world)[:3, :3]
    assert np.allclose(s, np.eye(3) * 0.01, atol=1e-6), (o.name, s)  # CC: local centimetres, world metres
    assert [m.type for m in o.modifiers] == ["ARMATURE"], (o.name, [m.type for m in o.modifiers])
keys = body.data.shape_keys
assert keys and keys.key_blocks[0].name == "Basis" and not any(k.name.startswith("ST_") for k in keys.key_blocks)
P = np.array([v.co[:] for v in body.data.vertices], dtype=np.float64)  # cm
x, y, z = P.T
edges = np.array([e.vertices[:] for e in body.data.edges], dtype=np.int32)

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


new_keys = {body.name: add_keys(body, P, masks)}

# --- the garments carry the same keys: each garment vertex takes the mask of its nearest body surface point
bvh = BVHTree.FromPolygons([tuple(p) for p in P.tolist()], [tuple(f.vertices) for f in body.data.polygons], all_triangles=False)
garment_report = {}
for gname in GARMENTS:
    g = bpy.data.objects[gname]
    Q = np.array([v.co[:] for v in g.data.vertices], dtype=np.float64)
    gmask = {r: np.zeros(len(Q)) for r in REGIONS}
    dist = np.zeros(len(Q))
    for i, q in enumerate(Q):
        loc, nrm, fi, d = bvh.find_nearest(Vector(q))
        dist[i] = d
        verts = body.data.polygons[fi].vertices
        w = 1.0 / (np.linalg.norm(P[list(verts)] - np.array(loc), axis=1) + 0.05)
        w /= w.sum()
        for r in REGIONS:
            gmask[r][i] = float((masks[r][list(verts)] * w).sum())
    new_keys[gname] = add_keys(g, Q, gmask)
    garment_report[gname] = {"vertices": int(len(Q)), "max_distance_to_body_cm": float(dist.max()), "mean_distance_cm": float(dist.mean()),
                             "masked": {r: {"vertices": int((gmask[r] > 0).sum()), "max": float(gmask[r].max())} for r in REGIONS}}

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
          "new_keys": new_keys, "regions": anchors, "reference_bones_blender_cm": reference,
          "body_keys": len(keys.key_blocks), "meshes": [o.name for o in meshes]}
print("JOY_ST_MASKS", json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "bounds_cm"} for k, v in mask_report.items()}), flush=True)
print("JOY_ST_GARMENTS", json.dumps(garment_report), flush=True)
print("JOY_ST_ANCHORS", json.dumps({k: [(r["bone"], round(r["weight"], 3)) for r in v["anchors"]] for k, v in anchors.items()}), flush=True)

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
print("JOY_ST_EXPORTED", json.dumps({"fbx_bytes": fbx.stat().st_size, "keys": {k: len(v) for k, v in new_keys.items()}}), flush=True)
