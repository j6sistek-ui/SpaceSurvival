"""Take the floor `root` bone out of a crew mesh's skin weights. Headless Blender, CPU only.

  blender -b <final>.blend -P strip_root_weights.py -- <out>.blend

Blender's automatic weights treat every deform bone as skin, and `root` sits on the floor between the feet, so
bone heat gave it the feet and anything else low (on Dread, 5,028 vertices were mostly root). In place that hides;
the moment the body leaves the root - sitting, crouching, a jump, a zero-G root-motion float - those vertices stay
on the floor and stretch into spikes. Each vertex keeps its other bones, renormalised; one that had only root takes
its nearest properly weighted neighbour's weights.
"""
import bpy
import json
import sys
from mathutils import kdtree

out = sys.argv[-1]
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
NOT_SKIN = ("root", "Armature")
for b in arm.data.bones:
    if b.name in NOT_SKIN:
        b.use_deform = False
report = {}
for m in [o for o in bpy.data.objects if o.type == 'MESH']:
    bad = [m.vertex_groups[n] for n in NOT_SKIN if n in m.vertex_groups]
    bad_ix = {g.index for g in bad}
    touched, lonely = 0, []
    for v in m.data.vertices:
        if not any(g.group in bad_ix for g in v.groups):
            continue
        touched += 1
        rest = [(g.group, g.weight) for g in v.groups if g.group not in bad_ix and g.weight > 0.0]
        for g in bad:
            g.remove([v.index])
        tot = sum(w for _, w in rest)
        if tot <= 1e-6:
            lonely.append(v.index); continue
        for gi, w in rest:
            m.vertex_groups[gi].add([v.index], w / tot, 'REPLACE')
    good = [v for v in m.data.vertices if v.groups and v.index not in set(lonely)]
    kd = kdtree.KDTree(len(good))
    for i, v in enumerate(good):
        kd.insert(v.co, i)
    kd.balance()
    for vi in lonely:
        src = good[kd.find(m.data.vertices[vi].co)[1]]
        for g in src.groups:
            m.vertex_groups[g.group].add([vi], g.weight, 'REPLACE')
    for g in bad:
        m.vertex_groups.remove(g)
    report[m.name] = {"verts": len(m.data.vertices), "had_root": touched, "root_only_refilled": len(lonely),
                      "unweighted_after": sum(1 for v in m.data.vertices if not v.groups)}
print("STRIPROOT", json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=out)
