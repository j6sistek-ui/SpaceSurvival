"""Diagnose the owner's report on A_Cyborg_PoleHipCircle (2026-10-10, in game): "during the lean there is tearing in
the breast and a twisted arm". Re-authors the clip exactly as pole_dance.py does, then
  1. prints, per frame, the roll of each hand about its forearm (wrist twist the skin has to absorb);
  2. lists the breast-region vertices most weighted to the raised arm's bones;
  3. renders close-ups of the chest/right arm at the frames of maximum twist and maximum lean.
  blender -b Cyborg_new.blend --factory-startup -P diag_hipcircle.py -- <outdir> [Clip]"""
import math
import os
import sys

import bpy
from mathutils import Vector

POLE = __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "pole_dance.py")
args = sys.argv[sys.argv.index("--") + 1:]
OUT = args[0]
CLIP = args[1] if len(args) > 1 else "HipCircle"
os.makedirs(OUT, exist_ok=True)

src = open(POLE, encoding="utf-8").read()
cut = src.index("action = author(CLIP)")
sys.argv = [sys.argv[0], "--", OUT, "Cyborg", CLIP]
g = {"__name__": "pole_dance", "__file__": POLE}
exec(compile(src[:cut], POLE, "exec"), g)
act = g["author"](CLIP)
arm, mesh, PB, sc = g["arm"], g["mesh"], g["PB"], g["sc"]
n = sc.frame_end


def roll_about_forearm(side):
    """Angle between the hand's X axis and the forearm's X axis, both projected onto the plane normal to the forearm."""
    fa = PB["lowerarm_" + side].matrix.to_3x3(); hd = PB["hand_" + side].matrix.to_3x3()
    axis = fa.col[1].normalized()
    a = fa.col[0] - axis * fa.col[0].dot(axis); b = hd.col[0] - axis * hd.col[0].dot(axis)
    a.normalize(); b.normalize()
    ang = math.degrees(math.atan2(axis.dot(a.cross(b)), a.dot(b)))
    bend = math.degrees(fa.col[1].angle(hd.col[1]))
    return ang, bend


def upperarm_raise(side):
    v = (PB["upperarm_" + side].tail - PB["upperarm_" + side].head).normalized()
    return math.degrees(math.asin(max(-1, min(1, v.z))))          # 0 = horizontal, 90 = straight up


rows = []
for f in range(1, n + 1):
    sc.frame_set(f)
    r_roll, r_bend = roll_about_forearm("r"); l_roll, l_bend = roll_about_forearm("l")
    lean = math.degrees(PB["spine_03"].matrix.to_3x3().col[1].angle(Vector((0, 0, 1))))
    rows.append((f, r_roll, r_bend, l_roll, l_bend, upperarm_raise("r"), lean))
print("DIAG| frame  R-wrist-roll R-wrist-bend  L-wrist-roll L-wrist-bend  R-upperarm-raise  chest-lean")
for r in rows[::6]:
    print("DIAG| %4d   %8.1f   %8.1f    %8.1f   %8.1f   %8.1f   %8.1f" % r)
worst_twist = max(rows, key=lambda r: abs(r[1]))
worst_lean = max(rows, key=lambda r: r[6])
print("DIAG| max |R wrist roll| %.1f deg at frame %d; max chest lean %.1f deg at frame %d; R upperarm raise %.0f..%.0f deg"
      % (abs(worst_twist[1]), worst_twist[0], worst_lean[6], worst_lean[0], min(r[5] for r in rows), max(r[5] for r in rows)))

# vertices in the right breast / armpit region and how much the raised arm drags them
names = {vg.index: vg.name for vg in mesh.vertex_groups}
mw = mesh.matrix_world
cand = []
for v in mesh.data.vertices:
    p = mw @ v.co                                       # rest pose, metres; she faces -Y, her right is -X
    if -0.22 < p.x < -0.02 and p.y < 0.05 and 1.18 < p.z < 1.42:
        w = {names[g.group]: g.weight for g in v.groups if g.weight > 0.02}
        arm_w = sum(wt for k, wt in w.items() if k.endswith("_r") and ("upperarm" in k or "clavicle" in k or "lowerarm" in k))
        cand.append((arm_w, v.index, tuple(round(c, 3) for c in p), w))
cand.sort(reverse=True)
heavy = [c for c in cand if c[0] > 0.25]
print("DIAG| breast/armpit region: %d verts, %d with >25%% weight on the right arm/clavicle" % (len(cand), len(heavy)))
for c in cand[:12]:
    print("DIAG|   v%-6d arm %.2f at %s  %s" % (c[1], c[0], c[2], {k: round(x, 2) for k, x in sorted(c[3].items(), key=lambda kv: -kv[1])[:4]}))

# close-up renders: clay with a dark backface so tears show as black
mat = bpy.data.materials.new("diag"); mat.use_nodes = True
nt = mat.node_tree; nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial"); mix = nt.nodes.new("ShaderNodeMixShader")
geo = nt.nodes.new("ShaderNodeNewGeometry"); front = nt.nodes.new("ShaderNodeBsdfDiffuse"); back = nt.nodes.new("ShaderNodeEmission")
front.inputs[0].default_value = (0.75, 0.62, 0.7, 1); back.inputs[0].default_value = (0.02, 0.0, 0.0, 1)
nt.links.new(geo.outputs["Backfacing"], mix.inputs[0]); nt.links.new(front.outputs[0], mix.inputs[1])
nt.links.new(back.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], out.inputs[0])
mesh.data.materials.clear(); mesh.data.materials.append(mat)
sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 640, 640
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.35, 0.35, 0.38, 1)
for rot, e in (((50, 0, -30), 3.0), ((60, 0, 150), 1.5)):
    L = bpy.data.lights.new("k", 'SUN'); L.energy = e; o = bpy.data.objects.new("k", L); sc.collection.objects.link(o)
    o.rotation_euler = [math.radians(x) for x in rot]
cam = bpy.data.cameras.new("c"); cam.lens = 50; co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co


def shot(frame, tag, loc, look):
    sc.frame_set(frame)
    co.location = Vector(loc)
    co.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUT, "%s_%s_f%03d.png" % (CLIP, tag, frame)); bpy.ops.render.render(write_still=True)


for frame, tag in ((worst_twist[0], "twist"), (worst_lean[0], "lean")):
    sc.frame_set(frame)
    chest = PB["spine_03"].head.copy(); hand = PB["hand_r"].head.copy()
    shot(frame, tag + "_chest", chest + Vector((-0.35, -0.75, 0.15)), chest + Vector((-0.08, 0, 0.05)))
    shot(frame, tag + "_arm", (hand + chest) / 2 + Vector((-0.9, -0.6, 0.0)), (hand + chest) / 2)
print("DIAG| renders in", OUT)
