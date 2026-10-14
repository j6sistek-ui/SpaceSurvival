"""Lighter character, same look: decimate with the head protected, repair the seam strays, bake into the model's
own UV layout. Measured on the Cyborg 2026-10-12 against the owner's pasted method (Smart UV Project + bake): the
generator's own layout fills 49% of the texture where Smart UV Project managed 12%, and its seams are the ones the
original already hides, so the bake goes back into that layout instead of a fresh unwrap.

Steps, on the mesh named by --object (or the only mesh):
  1. nothing is "corrected" first: Make Normals Consistent flipped faces on an already-consistent Tripo mesh and
     Unreal culled them (torn in the game, fine in Blender), and Triangles to Quads without Compare UVs joined
     triangles across texture seams (the "cooked in patches" result);
  2. a copy, Decimate Collapse to --tris, with the head protected: --head-group <vertex group> (a rigged character's
     "head" bone group) or --head-z <fraction of the height> for an unrigged mesh;
  3. repair of the stray UV corners the collapse leaves where it merges a seam vertex into another island;
  4. Cycles bakes on the processor into the kept layout: Base Color and Metallic through an Emission shader (a Diffuse
     bake of a metal is black), tangent Normal, Roughness, optional Emissive; --metallic-image bakes a hand-tuned
     metallic PNG instead of the material's;
  5. check renders, original beside result, with the original wearing the same metallic the game uses;
  6. the copy with a single material named --slot (the slot name ReimportCrewSkin.py matches) and the blend saved.

  blender -b <model.blend> --python optimize_character_v2.py -- --out <dir> --tris 45000 --head-group head \
      [--object Cyborg] [--size 4096] [--metallic-image <png>] [--slot CyborgBody] [--emissive] [--threads 6]
  blender -b --python optimize_character_v2.py -- --glb <model.glb> --out <dir> --tris 80000 --head-z 0.86
"""
import argparse
import math
import os
import sys
import time

import bmesh
import bpy
import numpy as np
from mathutils import Vector

ap = argparse.ArgumentParser()
ap.add_argument("--glb", help="import this glTF into an empty scene first")
ap.add_argument("--object", help="mesh to optimise (default: the only mesh, or the largest)")
ap.add_argument("--out", required=True)
ap.add_argument("--tris", type=int, default=45000)
ap.add_argument("--size", type=int, default=4096)
ap.add_argument("--head-group", help="vertex group that marks the head (kept at full density)")
ap.add_argument("--head-z", type=float, help="fraction of the height above which the mesh is kept at full density")
ap.add_argument("--metallic-image", help="bake this PNG as the metallic map instead of the material's own")
ap.add_argument("--slot", help="material name on the result (default: <object>Body)")
ap.add_argument("--emissive", action="store_true", help="also bake the emission colour")
ap.add_argument("--threads", type=int, default=6)
ap.add_argument("--no-render", action="store_true")
ap.add_argument("--prefix", help="texture name prefix (default: T_<object>)")
args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

if args.glb:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=args.glb)
scene = bpy.context.scene
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
if args.object:
    high = bpy.data.objects[args.object]
else:
    high = max(meshes, key=lambda o: len(o.data.polygons))
NAME = args.object or high.name
if args.glb and not args.object:
    high.name = NAME = os.path.splitext(os.path.basename(args.glb))[0][:24]
PREFIX = args.prefix or ("T_" + NAME)
SLOT = args.slot or (NAME + "Body")
tex_dir = os.path.join(args.out, "tex")
os.makedirs(tex_dir, exist_ok=True)


def log(s):
    print("OPT2| " + s, flush=True)


def tris(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def select_only(objs, active):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active


def uv_fill(o):
    uv = o.data.uv_layers.active.data
    area = 0.0
    for p in o.data.polygons:
        pts = [uv[l].uv for l in p.loop_indices]
        for i in range(1, len(pts) - 1):
            a, b, c = pts[0], pts[i], pts[i + 1]
            area += abs((b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y)) * 0.5
    return 100 * area


# ---- 0. the head group ----
if args.head_z is not None:
    lo_z = min((high.matrix_world @ v.co).z for v in high.data.vertices)
    hi_z = max((high.matrix_world @ v.co).z for v in high.data.vertices)
    cut = lo_z + (hi_z - lo_z) * args.head_z
    g = high.vertex_groups.new(name="head_protect")
    idx = [v.index for v in high.data.vertices if (high.matrix_world @ v.co).z >= cut]
    g.add(idx, 1.0, "REPLACE")
    HEAD = g.name
    log("head: %d of %d vertices above %.0f%% of the height" % (len(idx), len(high.data.vertices), 100 * args.head_z))
else:
    HEAD = args.head_group


def head_tris(o):
    if not HEAD or HEAD not in o.vertex_groups:
        return 0
    gi = o.vertex_groups[HEAD].index
    hw = [next((g.weight for g in v.groups if g.group == gi), 0.0) for v in o.data.vertices]
    return sum(len(p.vertices) - 2 for p in o.data.polygons if min(hw[i] for i in p.vertices) > 0.5)


# ---- 1. no correction macro ----
# The owner's pasted macro (Merge by Distance, Make Normals Consistent, Triangles to Quads, Delete Loose) is NOT
# run: measured 2026-10-12 on the Cyborg, Make Normals Consistent flipped 1,238 faces of a mesh whose faces were
# already consistent, and Unreal culls back faces, so the result looked torn in the game while every Blender
# render (two-sided) looked fine. The mesh is used exactly as the generator made it.
log("source: %d triangles, head %d, uv fill %.0f%%" % (tris(high.data), head_tris(high), uv_fill(high)))

# ---- 2. copy + decimate ----
low = high.copy()
low.data = high.data.copy()
low.name = NAME + "_Low"
low.data.name = NAME + "_Low"
scene.collection.objects.link(low)
before = tris(low.data)
mod = low.modifiers.new("Decimate", "DECIMATE")
mod.decimate_type = "COLLAPSE"
mod.ratio = min(1.0, args.tris / before)
mod.use_collapse_triangulate = True
if HEAD:
    mod.vertex_group = HEAD
    mod.vertex_group_factor = 1.0
    mod.invert_vertex_group = True  # measured: inverted + factor 1 leaves the group untouched
select_only([low], low)
bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=0)
t0 = time.time()
bpy.ops.object.modifier_apply(modifier=mod.name)
low = bpy.data.objects[NAME + "_Low"]
log("decimate: %d -> %d triangles, head %d, verts %d, %.0f s" % (before, tris(low.data), head_tris(low), len(low.data.vertices), time.time() - t0))


# ---- 3. stray UV corners ----
def repair_strays(o, limit=6.0):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    uv_layer = bm.loops.layers.uv.active
    ratios = []
    for f in bm.faces:
        a3 = f.calc_area()
        if a3 <= 0:
            continue
        loops = f.loops
        a2 = 0.0
        for i in range(1, len(loops) - 1):
            a, b, c = loops[0][uv_layer].uv, loops[i][uv_layer].uv, loops[i + 1][uv_layer].uv
            a2 += abs((b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y)) * 0.5
        ratios.append(a2 / a3)
    scale = float(np.sqrt(np.median(ratios)))
    strays = moved = collapsed = 0
    for f in bm.faces:
        loops = list(f.loops)
        if len(loops) < 3:
            continue
        bad = []
        for i, l in enumerate(loops):
            far = 0
            for j, m in enumerate(loops):
                if i != j and (l[uv_layer].uv - m[uv_layer].uv).length > limit * ((l.vert.co - m.vert.co).length * scale + 1e-6):
                    far += 1
            if far == len(loops) - 1:
                bad.append(i)
        if not bad or len(bad) >= len(loops) - 1:
            continue
        good = [loops[j][uv_layer].uv.copy() for j in range(len(loops)) if j not in bad]
        centre = sum(good, Vector((0.0, 0.0))) / len(good)
        for i in bad:
            l = loops[i]
            strays += 1
            best, best_d = None, None
            d_3d = (l.vert.co - loops[(i + 1) % len(loops)].vert.co).length * scale + 1e-6
            for other in l.vert.link_loops:
                if other.face is f:
                    continue
                d = (other[uv_layer].uv - centre).length
                if d < limit * d_3d and (best_d is None or d < best_d):
                    best, best_d = other[uv_layer].uv.copy(), d
            if best is not None:
                l[uv_layer].uv = best
                moved += 1
            else:
                l[uv_layer].uv = centre
                collapsed += 1
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()
    log("stray UV corners: %d found, %d moved to a neighbour's UV, %d collapsed onto the face" % (strays, moved, collapsed))


repair_strays(low)


# ---- 4. bakes ----
def new_image(name, srgb):
    im = bpy.data.images.new(name, args.size, args.size, alpha=False)
    im.colorspace_settings.name = "sRGB" if srgb else "Non-Color"
    im.generated_color = (1, 0, 1, 1)
    return im


def image_node(mat, image):
    nt = mat.node_tree
    n = nt.nodes.new("ShaderNodeTexImage")
    n.image = image
    for x in nt.nodes:
        x.select = False
    n.select = True
    nt.nodes.active = n
    return n


def save_image(im):
    path = os.path.join(tex_dir, im.name + ".png")
    im.filepath_raw = path
    im.file_format = "PNG"
    im.save()
    log("saved " + path)


def principled_of(t):
    return next(n for n in t.nodes if n.type == "BSDF_PRINCIPLED")


class AsEmission:
    """Show one Principled input of every high material (or an image) as emission for an Emit bake."""

    def __init__(self, input_name=None, image=None):
        self.input_name, self.image = input_name, image

    def __enter__(self):
        self.saved = []
        for slot in high.material_slots:
            t = slot.material.node_tree
            p = principled_of(t)
            o = next(n for n in t.nodes if n.type == "OUTPUT_MATERIAL")
            old = next((l for l in t.links if l.to_node == o and l.to_socket.name == "Surface"), None)
            old_from = old.from_socket if old else None
            e = t.nodes.new("ShaderNodeEmission")
            e.inputs["Strength"].default_value = 1.0
            extra = [e]
            if self.image is not None:
                tex = t.nodes.new("ShaderNodeTexImage")
                tex.image = self.image
                extra.append(tex)
                t.links.new(tex.outputs["Color"], e.inputs["Color"])
            else:
                src = next((l for l in t.links if l.to_node == p and l.to_socket.name == self.input_name), None)
                if src:
                    t.links.new(src.from_socket, e.inputs["Color"])
                else:
                    v = p.inputs[self.input_name].default_value
                    e.inputs["Color"].default_value = (v, v, v, 1) if isinstance(v, float) else v
            t.links.new(e.outputs["Emission"], o.inputs["Surface"])
            self.saved.append((t, extra, o, old_from))
        return self

    def __exit__(self, *a):
        for t, extra, o, from_socket in self.saved:
            for n in extra:
                t.nodes.remove(n)
            if from_socket:
                t.links.new(from_socket, o.inputs["Surface"])


scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 4
scene.render.threads_mode = "FIXED"
scene.render.threads = args.threads
high.hide_render = False
high.hide_viewport = False
low.data.materials.clear()
mat = bpy.data.materials.new(SLOT)
mat.use_nodes = True
low.data.materials.append(mat)
nt = mat.node_tree
principled = principled_of(nt)
size = max(high.dimensions)


def bake(image, bake_type, **kw):
    node = image_node(mat, image)
    select_only([high, low], low)
    t = time.time()
    bpy.ops.object.bake(type=bake_type, use_selected_to_active=True, cage_extrusion=size * 0.006,
                        max_ray_distance=0.0, margin=16, use_clear=False, target="IMAGE_TEXTURES", **kw)
    px = np.empty(image.size[0] * image.size[1] * 4, dtype=np.float32)
    image.pixels.foreach_get(px)
    px = px.reshape(-1, 4)
    unwritten = ((px[:, 0] > 0.98) & (px[:, 1] < 0.02) & (px[:, 2] > 0.98)).mean()
    log("baked %s %s in %.0f s, %.1f%% of the image unwritten" % (bake_type, image.name, time.time() - t, 100 * unwritten))
    return node


tuned = None
if args.metallic_image:
    tuned = bpy.data.images.load(args.metallic_image)
    tuned.colorspace_settings.name = "Non-Color"
im_b = new_image(PREFIX + "_BaseColor", True)
with AsEmission("Base Color"):
    n_b = bake(im_b, "EMIT")
im_n = new_image(PREFIX + "_Normal", False)
n_n = bake(im_n, "NORMAL", normal_space="TANGENT")
im_r = new_image(PREFIX + "_Roughness", False)
n_r = bake(im_r, "ROUGHNESS")
metal_name = os.path.splitext(os.path.basename(args.metallic_image))[0] if args.metallic_image else PREFIX + "_Metallic"
im_m = new_image(metal_name, False)
with AsEmission(image=tuned) if tuned else AsEmission("Metallic"):
    n_m = bake(im_m, "EMIT")
images = [im_b, im_n, im_r, im_m]
n_e = None
if args.emissive:
    im_e = new_image(PREFIX + "_Emissive", True)
    with AsEmission("Emission Color"):
        n_e = bake(im_e, "EMIT")
    images.append(im_e)
for im in images:
    save_image(im)
nt.links.new(n_b.outputs["Color"], principled.inputs["Base Color"])
nt.links.new(n_r.outputs["Color"], principled.inputs["Roughness"])
nt.links.new(n_m.outputs["Color"], principled.inputs["Metallic"])
nmap = nt.nodes.new("ShaderNodeNormalMap")
nt.links.new(n_n.outputs["Color"], nmap.inputs["Color"])
nt.links.new(nmap.outputs["Normal"], principled.inputs["Normal"])
if n_e is not None:
    nt.links.new(n_e.outputs["Color"], principled.inputs["Emission Color"])
    principled.inputs["Emission Strength"].default_value = 1.0

# ---- 5. check renders ----
if not args.no_render:
    if tuned is not None:
        for slot in high.material_slots:
            t = slot.material.node_tree
            p = principled_of(t)
            for l in list(t.links):
                if l.to_node == p and l.to_socket.name == "Metallic":
                    t.links.remove(l)
            tex = t.nodes.new("ShaderNodeTexImage")
            tex.image = tuned
            t.links.new(tex.outputs["Color"], p.inputs["Metallic"])
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.resolution_x = scene.render.resolution_y = 768
    scene.view_settings.view_transform = "Standard"
    world = bpy.data.worlds.new("Grey")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.08, 0.08, 0.09, 1)
    scene.world = world
    lo_c, hi_c = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for c in high.bound_box:
        w = high.matrix_world @ Vector(c)
        lo_c = Vector(map(min, lo_c, w))
        hi_c = Vector(map(max, hi_c, w))
    centre = (lo_c + hi_c) * 0.5
    h = hi_c.z - lo_c.z
    for name, off, energy in (("Key", (1.5, -1.5, 1.2), 300), ("Fill", (-1.5, -1.0, 0.4), 120)):
        light = bpy.data.lights.new(name, "POINT")
        light.energy = energy * (h / 1.8)
        light.shadow_soft_size = 0.4
        l = bpy.data.objects.new(name, light)
        l.location = centre + Vector(off)
        scene.collection.objects.link(l)
    cam_data = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    shots = {"front": (0.5, h * 1.6, 50, 0.0), "side": (0.5, h * 1.6, 50, math.pi * 0.5),
             "chest": (0.72, 0.75, 85, 0.2), "face": (0.9, 0.45, 85, 0.2)}
    for o in (high, low):
        o.hide_render = True
    for o, tag in ((high, "original"), (low, "optimized")):
        o.hide_render = False
        for crop, (frac, dist, lens, yaw) in shots.items():
            cam_data.lens = lens
            target = Vector((centre.x, centre.y, lo_c.z + h * frac))
            cam.location = target + Vector((math.sin(yaw) * dist, -math.cos(yaw) * dist, 0.03 if lens == 85 else h * 0.1))
            cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
            scene.render.filepath = os.path.join(args.out, "%s_%s.png" % (crop, tag))
            bpy.ops.render.render(write_still=True)
            log("render " + scene.render.filepath)
        o.hide_render = True
    for o in (high, low):
        o.hide_render = False
high.hide_set(True)
high.hide_viewport = True
blend = os.path.join(args.out, NAME + "_%dk.blend" % round(tris(low.data) / 1000))
bpy.ops.wm.save_as_mainfile(filepath=blend)
log("saved " + blend)
