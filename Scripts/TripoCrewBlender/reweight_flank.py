"""Owner, in game 2026-10-10: "tearing in the breast" on the Cyborg when her arm is raised (A_Cyborg_PoleHipCircle).
Measured: of 860 vertices on the right side of the chest/flank, 368 carried more than 25% weight on the right arm, and
with the upper arm only 22-40 deg above horizontal the flank folds through itself from the armpit to the ribs (bone-heat
weights bleeding from the arm into the torso). Below the armpit line torso skin now follows the chest instead of the
arm, with a smoothed blend through the armpit band so there is no seam. Both sides. Saves the .blend in place (a copy
was taken first: Cyborg_new_before_flankfix_20261010.blend).
  blender -b Cyborg_new.blend --factory-startup -P reweight_flank.py"""
import bpy
import bmesh

ARMPIT_TOP, ARMPIT_LOW = 1.40, 1.30      # z (m): full arm influence above the top, none below the low line
TORSO_HALF_WIDTH = 0.21                  # |x| (m): the upper arm itself starts outside this in the T pose
MEDIAL = (0.09, 0.17)                    # |x| (m): arm influence fades out toward the sternum
SHOULDER_TOP = 1.50                      # z (m): above this the shoulder cap keeps its weights
BAND = (1.12, 1.46)                      # z range smoothed afterwards (down the breastbone too)
CHEST = "spine_03"

mesh = [o for o in bpy.data.objects if o.type == 'MESH'][0]
vg = mesh.vertex_groups
index = {g.name: g.index for g in vg}
arm_groups = {s: [n for n in index if n.endswith("_" + s) and any(k in n for k in ("upperarm", "lowerarm", "hand"))]
              for s in ("l", "r")}
mw = mesh.matrix_world


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


me = mesh.data
weights = [{g.group: g.weight for g in v.groups} for v in me.vertices]
pos = [mw @ v.co for v in me.vertices]
moved = 0
clav = {s: index["clavicle_" + s] for s in ("l", "r")}
for i, p in enumerate(pos):
    if abs(p.x) >= TORSO_HALF_WIDTH or p.z >= SHOULDER_TOP or p.z < 0.9:
        continue
    side = "r" if p.x < 0 else "l"
    # below the armpit line nothing follows the arm; toward the sternum nothing follows it either (the overhead
    # back-slide split the upper chest along the collarbones and the breastbone otherwise)
    f = max(smoothstep(ARMPIT_LOW, ARMPIT_TOP, p.z) * smoothstep(MEDIAL[0], MEDIAL[1], abs(p.x)),
            smoothstep(ARMPIT_TOP, SHOULDER_TOP, p.z))
    removed = 0.0
    for name in arm_groups[side]:
        gi = index[name]
        w = weights[i].get(gi, 0.0)
        if w > 0:
            weights[i][gi] = w * f
            removed += w * (1 - f)
    fc = smoothstep(ARMPIT_LOW, ARMPIT_TOP, p.z)          # the chest below the armpit line ignores the collarbone
    w = weights[i].get(clav[side], 0.0)
    if w > 0 and fc < 1:
        weights[i][clav[side]] = w * fc
        removed += w * (1 - fc)
    if removed > 1e-4:
        weights[i][index[CHEST]] = weights[i].get(index[CHEST], 0.0) + removed
        moved += 1

# smooth the armpit band so the hand-over from arm to chest has no seam
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
band = [i for i, p in enumerate(pos) if BAND[0] < p.z < BAND[1] and abs(p.x) < TORSO_HALF_WIDTH + 0.03]
touched = {index[n] for s in ("l", "r") for n in arm_groups[s]} | {index[CHEST]} | \
          {index[n] for n in index if n.startswith("clavicle")}
for _ in range(6):
    new = {}
    for i in band:
        nb = [e.other_vert(bm.verts[i]).index for e in bm.verts[i].link_edges]
        if not nb:
            continue
        w = dict(weights[i])
        for gi in touched:
            avg = sum(weights[j].get(gi, 0.0) for j in nb) / len(nb)
            w[gi] = 0.5 * weights[i].get(gi, 0.0) + 0.5 * avg
        new[i] = w
    for i, w in new.items():
        weights[i] = w
bm.free()

# normalise and write back
for i, w in enumerate(weights):
    total = sum(x for x in w.values() if x > 0)
    if total <= 0:
        continue
    for gi, x in w.items():
        x = x / total
        if x > 1e-4:
            vg[gi].add([i], x, 'REPLACE')
        else:
            vg[gi].remove([i])

left_over = max((sum(weights[i].get(index[n], 0) for n in arm_groups["r" if pos[i].x < 0 else "l"]) / max(1e-6, sum(weights[i].values())))
                for i, p in enumerate(pos) if abs(p.x) < TORSO_HALF_WIDTH and 0.9 < p.z < ARMPIT_LOW - 0.02)
print("FLANK| moved arm weight to %s on %d vertices, smoothed %d in the armpit band; max arm share below %.2f m now %.3f"
      % (CHEST, moved, len(band), ARMPIT_LOW - 0.02, left_over))
bpy.ops.wm.save_mainfile()
print("FLANK| saved", bpy.data.filepath)
