"""Give a bone-heat-skinned body real feet (Warden, 2026-10-09).

  blender -b <normalised>.blend -P fix_feet.py -- <out>.blend

The owner saw Warden "missing feet" in the game. Measured on her source: the crew skeleton fitted to her bounds had
foot_* pointing DOWN-BACK (foot head z 0.17 -> tail z 0.045, ball tail 8 cm UNDER the floor), and bone heat then
hung the whole foot on calf_twist_01_* (weight mass 142 + 137 vs 6 + 5 on the foot bones). Retargeted clips moved
the foot bones, almost nothing followed, and the boot read as a wedge stub that sank into the deck.

This re-aims each foot and ball bone along the boot the mesh actually has (ankle -> ball -> toe tip, from the
vertices below the ankle), then re-weights that region: foot below the ankle, ball past the ball joint, a 6 cm
blend into the calf above. Everything else is untouched. Re-import then re-retarget: the clips were authored on
the old bone frames.
"""
import json
import sys

import bpy
from mathutils import Vector

out = sys.argv[-1]
# ANKLE_Z 0.09: with the ball 10.4 cm ahead at z 0.035 the foot bone pitches -28 deg, the mannequin's -32. The
# retargeter aligns the target foot to the source foot's direction, so a steeper rest foot (0.12 gave -45 deg)
# is rotated UP in every clip - the owner saw Warden's toes pointing up.
ANKLE_Z, BLEND, BALL_AT = 0.08, 0.08, 0.70        # m; ball joint 70% of heel-to-toe
# In these Blender sources the crew face -Y (the FBX export flips it to Unreal's +Y). The first version of this
# script assumed +Y, built the feet pointing backwards, and the retargeter then swung them 100 degrees to match
# the mannequin - the boots hung vertical in the game.
FWD = -1.0
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
mesh = [o for o in bpy.data.objects if o.type == 'MESH'][0]
report = {}

feet = {}
for side in ("l", "r"):
    sign = 1 if side == "l" else -1                 # +x is the character's left
    pts = [mesh.matrix_world @ v.co for v in mesh.data.vertices
           if (mesh.matrix_world @ v.co).z < ANKLE_Z and sign * (mesh.matrix_world @ v.co).x > 0.02]
    toe = min(p.y for p in pts) if FWD < 0 else max(p.y for p in pts)
    heel = max(p.y for p in pts) if FWD < 0 else min(p.y for p in pts)
    xc = sum(p.x for p in pts) / len(pts)
    feet[side] = {"xc": xc, "heel": heel, "toe": toe, "ball": heel + BALL_AT * (toe - heel)}

bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
for side, f in feet.items():
    foot, ball = eb["foot_" + side], eb["ball_" + side]
    before = [list(foot.head), list(foot.tail), list(ball.tail)]
    foot.head = Vector((f["xc"], foot.head.y, ANKLE_Z))
    foot.tail = Vector((f["xc"], f["ball"], 0.035))
    ball.head = foot.tail.copy()
    ball.tail = Vector((f["xc"], f["toe"], 0.02))
    for b in (foot, ball):
        b.align_roll(Vector((0, 0, 1)))
    ball.parent = foot; ball.use_connect = True
    report[side] = {"before": before, "after": [list(foot.head), list(foot.tail), list(ball.tail)], **f}
bpy.ops.object.mode_set(mode='OBJECT')

groups = {g.name: g for g in mesh.vertex_groups}
for n in ("foot_l", "foot_r", "ball_l", "ball_r"):
    if n not in groups:
        groups[n] = mesh.vertex_groups.new(name=n)
names = {g.index: g.name for g in mesh.vertex_groups}
changed = 0
for v in mesh.data.vertices:
    p = mesh.matrix_world @ v.co
    if p.z >= ANKLE_Z + BLEND:
        continue
    side = "l" if p.x > 0 else "r"
    f = feet[side]
    w = min(1.0, max(0.0, (ANKLE_Z + BLEND - p.z) / BLEND))        # 1 below the ankle, 0 a blend-width above
    if w <= 0:
        continue
    span = (f["toe"] - f["ball"]) * 0.5                                                   # signed: toward the toe
    t = min(1.0, max(0.0, (p.y - f["ball"]) / span)) if abs(span) > 1e-6 else 0.0        # ball share past the joint
    keep = [(names[g.group], g.weight) for g in v.groups if names[g.group] not in ("foot_l", "foot_r", "ball_l", "ball_r", "root")]
    total = sum(wt for _, wt in keep) or 1.0
    for n, _ in keep:
        groups[n].remove([v.index])
    for n, wt in keep:
        if wt / total * (1 - w) > 1e-4:
            groups[n].add([v.index], wt / total * (1 - w), 'REPLACE')
    groups["foot_" + side].add([v.index], w * (1 - t), 'REPLACE')
    groups["ball_" + side].add([v.index], w * t, 'REPLACE')
    changed += 1
report["reweighted_vertices"] = changed
print("FEET", json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=out)
