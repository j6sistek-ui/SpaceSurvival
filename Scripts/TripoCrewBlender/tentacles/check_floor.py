"""Floor contact for one tentacle clip, EVERY frame of the action: vertices below the floor, the lowest skin point,
and the worst edge stretch against the rest pose.

  blender -b <animated>.blend -P check_floor.py -- <action>
"""
import sys

import bpy

act = sys.argv[-1]; sc = bpy.context.scene
arm = [o for o in sc.objects if o.type == 'ARMATURE'][0]; m = [o for o in sc.objects if o.type == 'MESH'][0]
arm.data.pose_position = 'REST'; bpy.context.view_layer.update()          # stretch is measured against the rest pose
dg = bpy.context.evaluated_depsgraph_get(); e0 = m.evaluated_get(dg); me = e0.to_mesh()
base = [e0.matrix_world @ v.co for v in me.vertices]; e0.to_mesh_clear()
arm.data.pose_position = 'POSE'; arm.animation_data.action = bpy.data.actions[act]
f0, f1 = (int(v) for v in bpy.data.actions[act].frame_range)
rows = []
for f in range(f0, f1 + 1):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); e = m.evaluated_get(dg); me = e.to_mesh()
    P = [e.matrix_world @ v.co for v in me.vertices]
    st = max((P[a] - P[b]).length / max((base[a] - base[b]).length, 1e-6) for a, b in (ed.vertices for ed in me.edges))
    rows.append((f, sum(1 for p in P if p.z < -0.01), round(min(p.z for p in P), 3), round(st, 2))); e.to_mesh_clear()
print("FLOOR", act, "frames", f0, f1, "worst_below", max(r[1] for r in rows), "lowest", min(r[2] for r in rows),
      "max_stretch", max(r[3] for r in rows))
print("FLOOR_FRAMES", act, rows)
