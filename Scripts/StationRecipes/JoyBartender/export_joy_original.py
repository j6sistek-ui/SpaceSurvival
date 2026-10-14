"""Export the ORIGINAL Fab Joy (original skin, waistcoat worn open, bottoms, pack hair cards) for Unreal.

  blender -b --python export_joy_original.py -- <out_dir> [gilet_key]

Owner 2026-10-14: "take the original joy files... she's going to replace the bartender... keep the original skin tone...
slutty bartender sci fi outfit". Source = the Fab pack's own joy.blend (still in the launcher vault cache). The export
mirrors .agent/local/StationRefinement/Lineup92/export_joy.py (the route that imported the light-blue Joy): frame 1,
armature action cleared, REST pose, packed images dumped as T_Joy_<name>, FBX -Z forward / Y up, no leaf bones, no
modifiers baked. New here: the waistcoat's EV_gilet_open_<n> shape key is baked into the base mesh so the shirt hangs open,
and every material's alpha link is recorded so the import can pick Masked/Translucent/Opaque. The source file is never
written (sha verified before and after).
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import bpy

SRC = Path("M:/SpaceSurvival/UserDownloadedAssets_SpaceSurvival/Content/VaultCache/FabLibrary/Joy-c6f24fcb/blender/joy.blend")
SRC_SHA = "8582f2f269e8"
argv = sys.argv[sys.argv.index("--") + 1:]
OUT = Path(argv[0])
GILET = argv[1] if len(argv) > 1 else "none"  # owner 2026-10-14: "making it cover up better" - the vest stays closed
GILET = "" if GILET.lower() in ("none", "closed", "basis") else GILET
# owner 2026-10-14: "nothing has to be underneath, except a small strap. keep it minimal" - only the strap is painted
LABELS = set((argv[2] if len(argv) > 2 else "strap").split(","))
OUT.mkdir(parents=True, exist_ok=False)

before = hashlib.sha256(SRC.read_bytes()).hexdigest()
assert before.startswith(SRC_SHA), before
bpy.ops.wm.open_mainfile(filepath=str(SRC), load_ui=False, use_scripts=False)
scene = bpy.context.scene
scene.frame_set(1)
rig = bpy.data.objects["Armature"]
rig.animation_data_clear()
rig.data.pose_position = "REST"
meshes = [o for o in scene.objects if o.type == "MESH" and not o.hide_render]
report = {"source": str(SRC), "source_sha256": before, "blender": bpy.app.version_string, "gilet_key": GILET,
          "materials": [], "images": [], "meshes": [], "bone_count": len(rig.data.bones)}


def safe(s):
    return re.sub("[^A-Za-z0-9_]", "_", s)


# the waistcoat worn open: bake the chosen shape key into the base shape, drop the other keys
coat = bpy.data.objects["waistcoat"]
if GILET and coat.data.shape_keys:
    kb = coat.data.shape_keys.key_blocks
    assert GILET in kb, [k.name for k in kb]
    for k in kb:
        k.value = 1.0 if k.name == GILET else 0.0
    bpy.context.view_layer.objects.active = coat
    coat.select_set(True)
    # apply the mix as the new basis (object mode, no modifiers touched)
    bpy.ops.object.shape_key_add(from_mix=True)
    mixed = kb[-1]
    mixed.name = "Open"
    for k in list(kb):
        if k.name not in ("Open",):
            coat.shape_key_remove(k)
    coat.shape_key_remove(kb["Open"]) if False else None  # keep "Open" as the sole basis; Blender treats it as Basis now
    report["gilet_applied"] = True
    coat.select_set(False)

used = {m for o in meshes for m in o.data.materials if m}
images = set()
for mat in sorted(used, key=lambda m: m.name):
    nodes = mat.node_tree.nodes
    bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
    row = {"name": mat.name, "unreal_name": "MI_Joy_" + safe(mat.name), "textures": {},
           "roughness": float(bsdf.inputs["Roughness"].default_value), "metallic": float(bsdf.inputs["Metallic"].default_value),
           "specular_ior_level": float(bsdf.inputs["Specular IOR Level"].default_value), "ior": float(bsdf.inputs["IOR"].default_value),
           "base_color": list(bsdf.inputs["Base Color"].default_value), "base_color_linked": bsdf.inputs["Base Color"].is_linked,
           "alpha": float(bsdf.inputs["Alpha"].default_value), "alpha_linked": bsdf.inputs["Alpha"].is_linked}
    for n in nodes:
        if n.type == "TEX_IMAGE" and n.image and n.image.name != "Render Result":
            name = n.image.name
            channel = "Normal" if name.endswith("_Normal") else "Opacity" if name.endswith("_Opacity") else "BaseColor" if name.endswith("_Diffuse") else None
            if channel is None:
                continue  # Specular / Bump maps have no slot in M_JoyOpaque
            images.add(n.image)
            row["textures"][channel] = "T_Joy_" + safe(name)
    report["materials"].append(row)
for im in sorted(images, key=lambda i: i.name):
    target = OUT / ("T_Joy_" + safe(im.name) + ".png")
    assert im.packed_file, im.name
    data = bytes(im.packed_file.data)
    suffix = ".png" if data[:8] == b"\x89PNG\r\n\x1a\n" else ".jpg" if data[:2] == b"\xff\xd8" else Path(im.filepath).suffix
    assert suffix in (".png", ".jpg", ".jpeg", ".tga", ".bmp"), (im.name, suffix)
    target = target.with_suffix(suffix)
    target.write_bytes(data)
    report["images"].append({"name": "T_Joy_" + safe(im.name), "path": str(target), "size": list(im.size),
                             "srgb": im.colorspace_settings.name == "sRGB", "sha256": hashlib.sha256(data).hexdigest()})
for o in meshes:
    report["meshes"].append({"name": o.name, "vertices": len(o.data.vertices), "polygons": len(o.data.polygons),
                             "morphs": len(o.data.shape_keys.key_blocks) - 1 if o.data.shape_keys else 0,
                             "materials": [m.name for m in o.data.materials if m]})
# --- the outfit painted onto the skin: bodysuit (deep V, ends at the panty line), thigh boots, fingerless gloves ---
# Regions come from the body's own bone weights, so they deform exactly with the skin. Written as UV polygons per skin
# material; paint_outfit.py rasterises them into the diffuse maps and a gloss mask.
body = bpy.data.objects["CC_Base_Body"]
me = body.data
gname = {g.index: g.name for g in body.vertex_groups}
W = body.matrix_world
A = rig.matrix_world


def bone_z(name):
    return (A @ rig.data.bones[name].head_local).z


z_breast = bone_z("CC_Base_L_Breast")
z_collar = bone_z("CC_Base_L_Clavicle")
z_knee = bone_z("CC_Base_L_Calf")
z_hip = bone_z("CC_Base_L_Thigh")
y_spine = (A @ rig.data.bones["CC_Base_Spine01"].head_local).y
uw = bpy.data.objects["Underwear_Bottoms"]
z_panty = max((uw.matrix_world @ v.co).z for v in uw.data.vertices)
z0, z1, w0, w1 = z_breast - 0.06, z_collar, 0.015, 0.06  # the V: 1.5 cm wide at the sternum bottom, 12 cm at the collar


def vwidth(z):
    t = max(0.0, min(1.0, (z - z0) / (z1 - z0)))
    return w0 + (w1 - w0) * t


def weights(v):
    w = {"suit": 0.0, "arm": 0.0, "hand": 0.0, "finger": 0.0, "calf": 0.0, "thigh": 0.0, "head": 0.0}
    for g in v.groups:
        n = gname.get(g.group, "")
        if any(k in n for k in ("Hip", "Pelvis", "Waist", "Spine", "Breast", "Ribs", "Clavicle")):
            w["suit"] += g.weight
        if any(k in n for k in ("Upperarm", "Forearm", "Elbow")):
            w["arm"] += g.weight
        if "_Hand" in n:
            w["hand"] += g.weight
        if any(k in n for k in ("Thumb", "Index", "Mid", "Ring", "Pinky")):
            w["finger"] += g.weight
        if any(k in n for k in ("Calf", "Foot", "Toe", "Knee")):
            w["calf"] += g.weight
        if "Thigh" in n:
            w["thigh"] += g.weight
        if any(k in n for k in ("Neck", "Head", "Jaw", "Eye", "Teeth", "Tongue", "Facial")):
            w["head"] += g.weight
    return w


vw = [weights(v) for v in me.vertices]
uv_layer = me.uv_layers.active.data
regions = {}
counts = {"strap": 0, "suit": 0, "boot": 0, "glove": 0}
for f in me.polygons:
    ws = {k: sum(vw[i][k] for i in f.vertices) / len(f.vertices) for k in vw[0]}
    c = W @ f.center
    label = None
    if ws["head"] > 0.3:
        label = None
    elif ws["suit"] >= 0.5 and ws["arm"] < 0.3 and ws["thigh"] < 0.3:
        if z_breast - 0.075 <= c.z <= z_breast + 0.045:
            label = "strap"  # a bandeau round the chest under the vest, 12 cm tall, nipples covered
        elif c.z >= z_panty - 0.01 and not (c.y < y_spine and c.z > z0 and abs(c.x) < vwidth(c.z)):
            label = "suit"
    elif ws["calf"] >= 0.5 or (ws["thigh"] >= 0.5 and c.z < z_knee + 0.55 * (z_hip - z_knee)):
        label = "boot"
    elif ws["hand"] >= 0.5 and ws["finger"] < 0.3:
        label = "glove"
    if label is None or label not in LABELS:
        continue
    mat = me.materials[f.material_index].name
    regions.setdefault(mat, {}).setdefault(label, []).append([[float(uv_layer[l].uv.x), float(uv_layer[l].uv.y)] for l in f.loop_indices])
    counts[label] += 1
(OUT / "uv_regions.json").write_text(json.dumps({"refs": {"z_breast": z_breast, "z_collar": z_collar, "z_knee": z_knee, "z_hip": z_hip, "z_panty": z_panty, "y_spine": y_spine},
                                                "counts": counts, "regions": regions}))
report["outfit_regions"] = counts
print("JOY_REGIONS", json.dumps(counts), {m: {k: len(v) for k, v in r.items()} for m, r in regions.items()}, flush=True)

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
(OUT / "Export.json").write_text(json.dumps(report, indent=2))
print("JOY_EXPORTED", json.dumps({"fbx_bytes": fbx.stat().st_size, "textures": len(images), "meshes": [m["name"] for m in report["meshes"]], "gilet": GILET}), flush=True)
