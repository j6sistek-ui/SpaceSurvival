"""Re-orient a rig's pelvis and thigh rest frames so Unreal imports them faithfully (the Elf, 2026-10-08).

  blender -b <normalised>.blend -P fix_leg_frames.py -- <out>.blend

Symptom: on the delivered Elf, every Unreal import - the repair chat's native SK_Fantasy_Elf and ours alike, via
Interchange or the legacy FBX importer - brought the thigh and thigh-twist reference frames in rotated 110-160
degrees away from the calves, so in every clip the thigh skin collapsed into a twisted ribbon. The same clip on the
Blender-side mesh deformed cleanly, and the Cyborg (same 61-bone rig family, same pipeline) was fine.

Measured difference: the Elf's pelvis rest frame is tilted ~7.5 degrees on two axes and her thighs point exactly
straight down, which puts each thigh's FBX bind matrix at a degenerate exact -90 degree angle; the Cyborg's pelvis is
upright and her thighs lean forward ~3 degrees. This rebuilds those frames in the Cyborg's layout - pelvis upright,
thighs leaning slightly toward the knee - with the same heads, lengths and axis conventions. Only REST orientation
changes; the mesh and every weight stay exactly as they are (pose is identity, so the skin does not move).
"""
import bpy
import json
import sys
from mathutils import Vector

out = sys.argv[-1]
FORWARD_LEAN = 0.05          # the Cyborg's thighs: direction (0, -0.05, -1) - feet face -y
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
report = {}


def frame(name, direction, z_toward):
    b = eb[name]
    before = (b.tail - b.head).normalized()
    b.tail = b.head + direction.normalized() * b.length
    b.align_roll(z_toward)
    report[name] = {"dir_before": [round(c, 3) for c in before], "dir_after": [round(c, 3) for c in (b.tail - b.head).normalized()]}


frame("pelvis", Vector((0, 0, 1)), Vector((-1, 0, 0)))          # Cyborg pelvis: y up, z toward -x
for side in ("l", "r"):
    for n in ("thigh_", "thigh_twist_01_"):
        frame(n + side, Vector((0, -FORWARD_LEAN, -1)), Vector((1, 0, 0)))   # Cyborg thigh: z toward +x
bpy.ops.object.mode_set(mode='OBJECT')
print("LEGFRAMES", json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=out)
