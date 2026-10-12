"""Reduce a rigged character's triangles and bake its textures onto the lighter copy - one script, in Blender.

Owner 2026-10-12: "a step by step Blender walkthrough for reducing the triangles and baking a new texture... or a
full python script that does it all automatically". The guide is docs/BLENDER_OPTIMIZE_CHARACTER.md; this is the
script. It keeps the rig: the copy keeps its armature modifier, parent and vertex groups (skin weights), so it
exports to Unreal exactly like the original (Scripts/TripoCrewBlender/export_for_unreal.py).

TWO WAYS TO RUN IT

  In Blender: open the character's .blend, click the high-poly mesh (not the armature), open the Scripting
  workspace, Text > Open this file, change the SETTINGS below if you like, Run Script (Alt+P). Watch the
  System Console (Window > Toggle System Console) for progress.

  Headless (no window, processor only):
    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b "M:/.../Cyborg_new.blend"
        --python Scripts/TripoCrewBlender/optimize_character.py -- --object Cyborg --tris 30000 --size 2048
        --out "M:/.../Cyborg_optimized" --save-as "M:/.../Cyborg_optimized.blend"

WHAT IT DOES

  1. Copies the mesh (the original stays, hidden, for the bake).
  2. Decimate (collapse, triangulated) down to --tris triangles, applied before the armature so weights survive.
  3. Keeps the original UV layout for the bake (decimation preserves it, and Tripo laid it out properly); with
     --reunwrap, new UVs instead: seams from the original islands, angle-based unwrap, in a layer called "Baked".
  4. Bakes from the ORIGINAL onto the copy with Cycles on the processor: Base Color and Metallic (each through an
     emission trick: a Diffuse bake leaves metal black and Blender has no metallic pass), Normal, Roughness and
     Emissive, each to a PNG in --out.
  5. Gives the copy one new material wired to those images and prints the numbers.

WHY EARLIER BAKES CAME OUT IN PATCHES (all handled here)
  - the bake image was only the active node in ONE material slot: faces using other slots do not bake;
  - the cage/ray distance did not match the model's size (the numbers below scale with the model);
  - the new UV islands overlapped or had no margin;
  - the original was hidden from renders (hide_render) so the rays had nothing to hit.

--no-bake keeps the original UVs and textures instead (decimation preserves them; seams may smear a little). It is
the cheaper first try - look at the result in Unreal before deciding a bake is needed.
"""
import argparse
import math
import os
import sys

import bpy

# ---- SETTINGS (used when run from Blender's Text Editor; the command line overrides them) ----
SETTINGS = {
    "object": "",        # mesh object name; empty = the active (clicked) object
    "tris": 30000,       # target triangle count for the copy
    "size": 2048,        # baked texture size (square)
    "out": "",           # folder for the PNGs; empty = a "baked" folder beside the .blend
    "no_bake": False,    # True: decimate only, keep the original UVs and textures
    "reunwrap": False,   # True: new UVs for the bake (seams from the original islands); False: bake into the
                         # original UV layout, which decimation keeps and which was laid out properly to begin with
    "symmetry": False,   # True: keep the decimation mirrored on X (only for truly symmetric characters)
    "save_as": "",       # save the .blend here when done (headless runs do not save otherwise)
    "threads": 0,        # processor threads for the bake; 0 = all of them
}
PASSES = ("BaseColor", "Normal", "Roughness", "Metallic", "Emissive")


def log(msg):
    print("optimize: " + msg, flush=True)


def parse_args():
    s = dict(SETTINGS)
    if "--" in sys.argv:
        ap = argparse.ArgumentParser()
        ap.add_argument("--object", default=s["object"])
        ap.add_argument("--tris", type=int, default=s["tris"])
        ap.add_argument("--size", type=int, default=s["size"])
        ap.add_argument("--out", default=s["out"])
        ap.add_argument("--no-bake", action="store_true", default=s["no_bake"])
        ap.add_argument("--reunwrap", action="store_true", default=s["reunwrap"])
        ap.add_argument("--symmetry", action="store_true", default=s["symmetry"])
        ap.add_argument("--save-as", default=s["save_as"])
        ap.add_argument("--threads", type=int, default=s["threads"])
        a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])
        s.update(object=a.object, tris=a.tris, size=a.size, out=a.out, no_bake=a.no_bake, reunwrap=a.reunwrap,
                 symmetry=a.symmetry, save_as=a.save_as, threads=a.threads)
    return s


def triangles(mesh):
    return sum(len(p.vertices) - 2 for p in mesh.polygons)


def find_source(name):
    if name:
        obj = bpy.data.objects.get(name)
        if not obj or obj.type != "MESH":
            raise SystemExit("optimize: no mesh object named %r" % name)
        return obj
    obj = bpy.context.view_layer.objects.active
    if not obj or obj.type != "MESH":
        meshes = [o for o in bpy.context.scene.objects if o.type == "MESH" and o.modifiers]
        if len(meshes) == 1:
            return meshes[0]
        raise SystemExit("optimize: click the character's mesh first (or pass --object NAME)")
    return obj


def select_only(objs, active):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = active


def make_copy(high):
    low = high.copy()
    low.data = high.data.copy()
    low.name = high.name + "_Low"
    low.data.name = high.data.name + "_Low"
    for col in high.users_collection:
        col.objects.link(low)
    # The copy keeps the armature modifier, the parent and the vertex groups: it is rigged like the original.
    return low


def decimate(low, target, symmetry):
    """Collapse decimation carries the UVs itself (each face corner keeps an interpolated UV), so the original
    textures still fit afterwards. The modifier's Delimit option only exists in Planar mode: measured 2026-10-12 on
    the Cyborg, Collapse with and without delimit={"UV"} gave identical vertices and identical UVs."""
    before = triangles(low.data)
    ratio = min(1.0, max(0.001, target / max(1, before)))
    mod = low.modifiers.new("Optimize", "DECIMATE")
    mod.decimate_type = "COLLAPSE"
    mod.ratio = ratio
    mod.use_collapse_triangulate = True
    mod.use_symmetry = symmetry
    mod.symmetry_axis = "X"
    # First in the stack: it must work on the rest-pose mesh, before the armature deforms it.
    select_only([low], low)
    bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=0)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    after = triangles(low.data)
    log("decimated %s: %d -> %d triangles (ratio %.3f)" % (low.name, before, after, ratio))
    return before, after


def unwrap(low):
    """New UVs in a layer called "Baked": seams taken from the original UV islands, then an angle-based unwrap, so
    the layout keeps the original's island shapes (Smart UV Project on an organic mesh made hundreds of slivers
    packed into one corner, measured 2026-10-12)."""
    select_only([low], low)
    original = low.data.uv_layers.active.name
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.seams_from_islands()
    bpy.ops.object.mode_set(mode="OBJECT")
    uv = low.data.uv_layers.new(name="Baked")
    low.data.uv_layers.active = uv
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.005)
    bpy.ops.object.mode_set(mode="OBJECT")
    # Leaving Edit Mode rebuilds the mesh data: handles from before it are stale, so look the layer up again.
    uv = low.data.uv_layers["Baked"]
    uv.active_render = True
    low.data.uv_layers.active = uv
    log("new UVs: seams from the original %r islands, angle-based unwrap, layer %r" % (original, uv.name))
    return uv


def new_image(name, size, color):
    if name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[name])
    img = bpy.data.images.new(name, size, size, alpha=False, float_buffer=False)
    img.colorspace_settings.name = "sRGB" if color else "Non-Color"
    img.generated_color = (0, 0, 0, 1)
    return img


def baked_material(low, images, high_emits, metallic_value):
    """One material on the copy: the bake target during baking, the real material afterwards."""
    for _ in range(len(low.data.materials)):
        low.data.materials.pop(index=0)
    mat = bpy.data.materials.new(low.name + "_Baked")
    mat.use_nodes = True
    low.data.materials.append(mat)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    principled = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
    tex = {}
    for i, name in enumerate(PASSES):
        node = nodes.new("ShaderNodeTexImage")
        node.name = node.label = name
        node.image = images[name]
        node.location = (-700, 400 - 260 * i)
        tex[name] = node
    links.new(tex["BaseColor"].outputs["Color"], principled.inputs["Base Color"])
    links.new(tex["Roughness"].outputs["Color"], principled.inputs["Roughness"])
    if metallic_value is None:  # baked image
        links.new(tex["Metallic"].outputs["Color"], principled.inputs["Metallic"])
    else:
        principled.inputs["Metallic"].default_value = metallic_value
        nodes.remove(tex["Metallic"])
    normal_map = nodes.new("ShaderNodeNormalMap")
    normal_map.location = (-350, -150)
    links.new(tex["Normal"].outputs["Color"], normal_map.inputs["Color"])
    links.new(normal_map.outputs["Normal"], principled.inputs["Normal"])
    if high_emits:
        links.new(tex["Emissive"].outputs["Color"], principled.inputs["Emission Color"])
        principled.inputs["Emission Strength"].default_value = 1.0
    else:
        nodes.remove(tex["Emissive"])
    return mat, tex


def high_material_facts(high):
    """Does any material emit, and is metallic driven by a texture (None) or a constant (the value)?"""
    emits, metallic = False, 0.0
    for mat in high.data.materials:
        if not mat or not mat.use_nodes:
            continue
        for n in mat.node_tree.nodes:
            if n.type != "BSDF_PRINCIPLED":
                continue
            if n.inputs["Emission Color"].is_linked or n.inputs["Emission Strength"].default_value > 0 and any(
                    c > 0 for c in n.inputs["Emission Color"].default_value[:3]):
                emits = True
            if n.inputs["Metallic"].is_linked:
                metallic = None
            elif metallic is not None:
                metallic = max(metallic, n.inputs["Metallic"].default_value)
    return emits, metallic


class InputAsEmission:
    """Bake what feeds one Principled input (Base Color, Metallic...) by having each original material temporarily
    emit it, then put everything back exactly as it was. Needed because a Diffuse colour bake gives metal surfaces
    no colour at all (chrome legs came out black, 2026-10-12) and Blender has no metallic pass."""

    def __init__(self, high, input_name):
        self.high = high
        self.input_name = input_name
        self.undo = []

    def __enter__(self):
        for mat in self.high.data.materials:
            if not mat or not mat.use_nodes:
                continue
            nodes, links = mat.node_tree.nodes, mat.node_tree.links
            out = next((n for n in nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output), None)
            principled = next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
            if not out or not principled or not out.inputs["Surface"].is_linked:
                continue
            original = out.inputs["Surface"].links[0].from_socket
            emission = nodes.new("ShaderNodeEmission")
            emission.name = "OptimizeProbe"
            source = principled.inputs[self.input_name]
            if source.is_linked:
                links.new(source.links[0].from_socket, emission.inputs["Color"])
            else:
                v = source.default_value
                emission.inputs["Color"].default_value = tuple(v) if hasattr(v, "__len__") else (v, v, v, 1)
            links.new(emission.outputs["Emission"], out.inputs["Surface"])
            self.undo.append((mat, out, original, emission))
        return self

    def __exit__(self, *_):
        for mat, out, original, emission in self.undo:
            links = mat.node_tree.links
            links.new(original, out.inputs["Surface"])
            mat.node_tree.nodes.remove(emission)


def bake_all(high, low, images, tex, out_dir, high_emits, metallic_constant, threads=0):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"  # the owner needs the graphics card; a bake like this is fine on the processor
    if threads > 0:
        scene.render.threads_mode = "FIXED"
        scene.render.threads = threads
    scene.cycles.samples = 4  # colour, normal and roughness passes are not noisy: samples only cost time
    scene.cycles.use_denoising = False
    bake = scene.render.bake
    bake.use_selected_to_active = True
    bake.use_clear = True
    bake.margin = 16
    bake.target = "IMAGE_TEXTURES"
    # Rays are cast from a cage inflated by 1% of the model and may travel 5% of it: scaled to the model, which is
    # what "0.01 for everything" in the online guides gets wrong on a character measured in centimetres.
    size = max(high.dimensions)
    bake.cage_extrusion = 0.01 * size
    bake.max_ray_distance = 0.05 * size
    bake.use_cage = False
    bake.use_pass_direct = bake.use_pass_indirect = False
    bake.use_pass_color = True
    # The original must be visible to renders; the copy is the active object, the original the selected one.
    high.hide_render = False
    high.hide_viewport = False
    low.hide_render = False
    select_only([high, low], low)
    os.makedirs(out_dir, exist_ok=True)

    def run(name, bake_type, **kw):
        tex[name].select = True
        low.data.materials[0].node_tree.nodes.active = tex[name]
        log("baking %s..." % name)
        bpy.ops.object.bake(type=bake_type, use_selected_to_active=True, cage_extrusion=bake.cage_extrusion,
                            max_ray_distance=bake.max_ray_distance, margin=16, use_clear=True,
                            target="IMAGE_TEXTURES", **kw)
        path = os.path.join(out_dir, "%s_%s.png" % (low.name.replace("_Low", ""), name))
        images[name].filepath_raw = path
        images[name].file_format = "PNG"
        images[name].save()
        log("  saved %s" % path)

    with InputAsEmission(high, "Base Color"):
        run("BaseColor", "EMIT")
    run("Normal", "NORMAL", normal_space="TANGENT")
    run("Roughness", "ROUGHNESS")
    if metallic_constant is None:
        with InputAsEmission(high, "Metallic"):
            run("Metallic", "EMIT")
    if high_emits:
        run("Emissive", "EMIT")


def main():
    s = parse_args()
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    high = find_source(s["object"])
    blend_dir = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.getcwd()
    out_dir = s["out"] or os.path.join(blend_dir, "baked")
    log("source %s: %d triangles, %d vertex groups, materials %s" % (
        high.name, triangles(high.data), len(high.vertex_groups), [m.name if m else None for m in high.data.materials]))
    low = make_copy(high)
    before, after = decimate(low, s["tris"], s["symmetry"])
    if s["no_bake"]:
        log("no bake: the copy keeps the original UVs and textures")
    else:
        if s["reunwrap"]:
            unwrap(low)
        else:
            log("baking into the original UV layout %r (decimation keeps it; --reunwrap for new UVs)"
                % low.data.uv_layers.active.name)
        emits, metallic = high_material_facts(high)
        images = {name: new_image("%s_%s" % (high.name, name), s["size"], color=name in ("BaseColor", "Emissive"))
                  for name in PASSES}
        _, tex = baked_material(low, images, emits, metallic)
        bake_all(high, low, images, tex, out_dir, emits, metallic, s["threads"])
        if s["reunwrap"]:
            # Only the baked layer stays, under the name Unreal expects.
            for uv in list(low.data.uv_layers):
                if uv.name != "Baked":
                    low.data.uv_layers.remove(uv)
            low.data.uv_layers["Baked"].name = "UVMap"
    high.hide_set(True)
    high.hide_render = True
    select_only([low], low)
    log("done: %s has %d triangles (was %d); the original %s is kept hidden" % (low.name, after, before, high.name))
    if s["save_as"]:
        bpy.ops.wm.save_as_mainfile(filepath=s["save_as"])
        log("saved %s" % s["save_as"])


main()
