"""Stop a cloak or robe that hangs past the legs from fanning out when the knees bend (Seer, Tendril).

  blender -b <final>.blend -P cloak_to_pelvis.py -- <out>.blend

Tripo weighted these characters' cloak tails and robe tatters to the thighs and calves, so any clip that bends the
knees - the seated terminal work on the desk clerks, a squat, a bow - swings every tail with its leg and the cloak
splays into spikes. Cloth that hangs AWAY from a leg should mostly follow the hips. So each vertex dominated by a
leg bone is blended toward the pelvis by how far it sits from that leg's bones: on the leg it is untouched, past
OUTSIDE it follows the pelvis by HIP_SHARE, in between it blends smoothly. Nothing above the hips is touched.
"""
import bpy
import json
import sys
from mathutils import Vector

out = sys.argv[-1]
INSIDE = 0.07     # metres from the leg bones: this close, it is the leg itself (or cloth lying on it)
OUTSIDE = 0.16    # this far, it is cloth hanging free
HIP_SHARE = 0.85  # how much of a free-hanging vertex goes to the pelvis (a little leg keeps it from looking rigid)
LEG = ("thigh", "calf", "foot", "ball")

arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
W = arm.matrix_world
segs = {b.name: (W @ b.head_local, W @ b.tail_local) for b in arm.data.bones if b.name.lower().startswith(LEG)}
pelvis = next(b for b in arm.data.bones if b.name.lower() == "pelvis")
hip_z = (W @ pelvis.head_local).z


def dist(p):
    best = 9.0
    for a, b in segs.values():
        ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
        best = min(best, (p - (a + ab * t)).length)
    return best


report = {}
for m in [o for o in bpy.data.objects if o.type == 'MESH']:
    names = {g.index: g.name for g in m.vertex_groups}
    pg = m.vertex_groups.get(pelvis.name) or m.vertex_groups.new(name=pelvis.name)
    moved = 0
    for v in m.data.vertices:
        if not v.groups:
            continue
        top = max(v.groups, key=lambda g: g.weight)
        if not names[top.group].lower().startswith(LEG):
            continue
        p = m.matrix_world @ v.co
        if p.z > hip_z:
            continue
        x = (dist(p) - INSIDE) / (OUTSIDE - INSIDE)
        if x <= 0:
            continue
        x = min(1.0, x); a = HIP_SHARE * x * x * (3 - 2 * x)
        old = {g.group: g.weight for g in v.groups}
        tot = sum(old.values()) or 1.0
        new = {gi: (1 - a) * w / tot for gi, w in old.items()}
        new[pg.index] = new.get(pg.index, 0.0) + a
        for gi, w in new.items():
            m.vertex_groups[gi].add([v.index], w, 'REPLACE')
        moved += 1
    report[m.name] = {"verts": len(m.data.vertices), "blended_toward_pelvis": moved}
print("CLOAK", json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=out)
