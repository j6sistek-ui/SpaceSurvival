"""Render evenly spaced frames of one exported clip in clay, headless Blender, CPU only (no VRAM).

  blender -b --factory-startup -t 6 -P render_strip.py -- <clip.fbx> <out_prefix>
  env: SS_YAW=20 (camera angle from the front; 160 = from behind), SS_FRAMES=8,
       SS_TARGET=<bone> + SS_DIST=0.9 for a close-up framed on that bone (e.g. neck_01 for shoulders, pelvis for hips)

Writes <out_prefix>_<i>f.png. Build strips and per-character sheets with sheets.py (system Python + PIL).
"""
import math
import os
import sys

import bpy
from mathutils import Vector

fbx, out = sys.argv[-2], sys.argv[-1]
YAW = float(os.environ.get("SS_YAW", "20"))
FRAMES = int(os.environ.get("SS_FRAMES", "8"))
TARGET = os.environ.get("SS_TARGET")
DIST = float(os.environ.get("SS_DIST", "0.9"))

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx, use_anim=True, automatic_bone_orientation=False)
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
act = arm.animation_data.action if arm.animation_data else None
f0, f1 = act.frame_range if act else (1, 1)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 12; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = (480, 480) if TARGET else (300, 420)
sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.25, 0.25, 0.28, 1)
mat = bpy.data.materials.new("clay"); mat.diffuse_color = (0.7, 0.68, 0.65, 1)
for m in meshes:
    m.data.materials.clear(); m.data.materials.append(mat)
for r, e in (((55, 0, 35), 3.5), ((65, 0, 215), 1.8)):
    light = bpy.data.lights.new("k", 'SUN'); light.energy = e
    o = bpy.data.objects.new("k", light); sc.collection.objects.link(o); o.rotation_euler = [math.radians(x) for x in r]
cam = bpy.data.cameras.new("c"); cam.lens = 50
co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co


def bounds():
    dg = bpy.context.evaluated_depsgraph_get(); ps = []
    for m in meshes:
        e = m.evaluated_get(dg); me = e.to_mesh()
        ps += [e.matrix_world @ v.co for k, v in enumerate(me.vertices) if k % 9 == 0]; e.to_mesh_clear()
    return Vector([min(p[i] for p in ps) for i in range(3)]), Vector([max(p[i] for p in ps) for i in range(3)])


sc.frame_set(int(f0)); mn, mx = bounds(); H = mx.z - mn.z; centre = (mn + mx) / 2
cam.clip_start = H * 0.005; cam.clip_end = H * 100
a = math.radians(YAW)
for i in range(FRAMES):
    sc.frame_set(int(f0 + (f1 - f0) * i / FRAMES)); bpy.context.view_layer.update()
    if TARGET:   # unit-aware: the FBX from Unreal is in centimetres under a 0.01 object scale
        pb = next((b for b in arm.pose.bones if b.name.lower() == TARGET.lower()), None)   # Kraken/Abyss: Pelvis, NeckTwist01
        if pb is None:
            sys.exit("SS_TARGET %r is not on this rig; bones: %s" % (TARGET, ", ".join(b.name for b in arm.pose.bones)))
        c = arm.matrix_world @ pb.head; d = DIST * H / 1.78
        co.location = (c.x + math.sin(a) * d, c.y - math.cos(a) * d, c.z - 0.05 * d)
    else:
        d = H * 1.6 / 2 / math.tan(cam.angle_y / 2)
        co.location = (centre.x + math.sin(a) * d, centre.y - math.cos(a) * d, centre.z)
    co.rotation_euler = (math.radians(90), 0, a)
    sc.render.filepath = "%s_%df.png" % (out, i); bpy.ops.render.render(write_still=True)
