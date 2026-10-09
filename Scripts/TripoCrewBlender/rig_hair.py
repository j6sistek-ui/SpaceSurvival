"""Give long hanging hair real bone chains so it can move (Elf, Silver). Headless Blender, CPU only.

  blender -b <normalised>.blend -P rig_hair.py -- <out>.blend

Tripo skins hair to head/neck/spine_03, so it can only ride rigidly with the head. The owner wants it to "move
fluidly with motions/physics". This adds one chain per azimuth sector around the head where hair actually hangs
(measured: hair that falls at least MIN_DROP below the head bone), HAIR_BONES bones each, parented to `head`, laid
along the hair's own centroid path from ear level down to the sector's lowest hair. The motion itself is a
spring-and-collision simulation baked into every clip by Scripts/AuthorTripoCrewHair.py.

Which vertices are hair: every vertex of a mesh named like *Hair*; on other meshes, vertices dominated by head /
neck / spine_03 that sit farther than CORE_R from the neck-head axis (so neck, throat and skull skin are not hair).
Each hair vertex is shared between the two nearest sector chains by angle, spread along its chain by height, and
faded in from the scalp over ROOT_FADE, so the face and crown never move. Whatever the chains do not take keeps
the vertex's original weights.
"""
import bpy
import json
import math
import sys
from mathutils import Vector

out = sys.argv[-1]
SECTOR_DEG = 30.0
MIN_DROP = 0.25       # metres below the head bone a sector's hair must fall to earn a chain (short neck/front
                      # tufts at 0.17-0.24 m got chains at 0.15 and dragged throat skin with them)
HAIR_BONES = 7
CORE_R = 0.075        # neck/throat/skull core radius around the neck-head axis
ROOT_FADE = 0.08      # metres below the root over which a vertex fades onto the chain
SPREAD_DEG = 22.0     # a vertex shares weight with chains within this angle
HAIRISH = ("head", "neck_01", "neck_02", "spine_03")

arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
AW = arm.matrix_world
head = arm.data.bones["head"]
hb, ht = AW @ head.head_local, AW @ head.tail_local
neck = arm.data.bones["neck_01"]
nb = AW @ neck.head_local
ROOT_Z = hb.z + 0.01


def axis_dist(p):
    a, b = nb, ht; ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
    return (p - (a + ab * t)).length


def azimuth(p):  # degrees from the back (+y; the feet face -y), increasing toward +x
    return (math.degrees(math.atan2(p.x - hb.x, p.y - hb.y)) + 360.0) % 360.0


def angdiff(a, b):
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


hair = []   # (mesh, vertex index, world position)
for m in [o for o in bpy.data.objects if o.type == 'MESH']:
    names = {g.index: g.name for g in m.vertex_groups}
    whole = "hair" in m.name.lower()
    for v in m.data.vertices:
        p = m.matrix_world @ v.co
        if whole:
            hair.append((m, v.index, p)); continue
        g = max(v.groups, key=lambda g: g.weight, default=None)
        face_side = angdiff(azimuth(p), 180.0) < 80.0 and p.z > hb.z - 0.05   # jaw, chin, cheeks
        if g and names[g.group] in HAIRISH and axis_dist(p) > CORE_R and p.z < hb.z + 0.18 and not face_side:
            hair.append((m, v.index, p))

sectors = {}
for k in range(int(360 / SECTOR_DEG)):
    az = k * SECTOR_DEG
    mem = [p for _, _, p in hair if angdiff(azimuth(p), az) <= SECTOR_DEG / 2 and p.z < ROOT_Z]
    if not mem:
        continue
    low = min(p.z for p in mem)
    if hb.z - low < MIN_DROP:
        continue
    joints = []
    for j in range(HAIR_BONES + 1):
        z = ROOT_Z - (ROOT_Z - low) * j / HAIR_BONES
        band = [p for p in mem if abs(p.z - z) < max(0.025, (ROOT_Z - low) / HAIR_BONES / 2)]
        if not band:
            joints.append(joints[-1].copy() if joints else Vector((hb.x, hb.y, z))); joints[-1].z = z; continue
        # On the hair, not through the body: a lock draped over a shoulder has hair in front of AND behind it, and
        # its plain centroid fell inside the shoulder (measured 0.6 cm from the spine axis on the Elf's left lock).
        # Keep the lock's direction from the head axis but put the joint at its median distance out.
        offs = [Vector((p.x - hb.x, p.y - hb.y)) for p in band]
        mean = sum(offs, Vector((0.0, 0.0))) / len(offs)
        radius = sorted(o.length for o in offs)[len(offs) // 2]
        d = mean.normalized() if mean.length > 1e-6 else Vector((math.sin(math.radians(az)), math.cos(math.radians(az))))
        joints.append(Vector((hb.x + d.x * radius, hb.y + d.y * radius, z)))
    sectors[int(az)] = {"low": low, "joints": joints}

bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
inv = AW.inverted()
names_by_sector = {}
for az, s in sectors.items():
    prev = eb["head"]; chain = []
    for j in range(HAIR_BONES):
        n = "hair_%03d_%d" % (az, j + 1)
        if n in eb:
            eb.remove(eb[n])
        b = eb.new(n); b.head = inv @ s["joints"][j]; b.tail = inv @ s["joints"][j + 1]
        b.parent = prev; b.use_connect = j > 0; prev = b; chain.append(n)
    names_by_sector[az] = chain
bpy.ops.object.mode_set(mode='OBJECT')

# Hair that lies ON a shoulder must ride the shoulder. The bind pose is a T-pose, so in nearly every clip the arms
# come down and the back of the shoulder and upper arm roll into the hair; a chain only steers a card's centre line,
# so wide cards still poked through (the owner's "biggest concern"). Within SHOULDER_ZONE of a clavicle-to-deltoid
# line a hair vertex takes up to SHOULDER_SHARE of its weight from that clavicle and upper arm.
SHOULDER_ZONE, SHOULDER_INNER, SHOULDER_SHARE = 0.10, 0.06, 0.7
shoulders = {}
for side in ("l", "r"):
    c, ua = arm.data.bones["clavicle_" + side], arm.data.bones["upperarm_" + side]
    a0 = AW @ c.head_local; uh = AW @ ua.head_local; ut = AW @ ua.tail_local
    shoulders[side] = (a0, uh + (ut - uh) * 0.3)


def seg_d(p, a, b):
    ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared)); return (p - (a + ab * t)).length


written = shoulder_touched = 0
for m, vi, p in hair:
    v = m.data.vertices[vi]
    old = {m.vertex_groups[g.group].name: g.weight for g in v.groups}
    tot_o = sum(old.values()) or 1.0
    final = {n: w / tot_o for n, w in old.items()}
    az = azimuth(p)
    near = [(s, math.exp(-(angdiff(az, s) / (SPREAD_DEG * 0.7)) ** 2)) for s in sectors if angdiff(az, s) <= SPREAD_DEG + SECTOR_DEG / 2]
    fade = max(0.0, min(1.0, (ROOT_Z - p.z) / ROOT_FADE)); fade = fade * fade * (3 - 2 * fade)
    if near and fade > 0.0:
        tot_s = sum(w for _, w in near)
        adds = {}
        for s, ws in near:
            low = sectors[s]["low"]
            t = max(0.0, min(1.0, (ROOT_Z - p.z) / max(ROOT_Z - low, 1e-3))) * HAIR_BONES
            raw = [math.exp(-((t - (j + 0.5)) / 0.9) ** 2) for j in range(HAIR_BONES)]
            rt = sum(raw)
            for j in range(HAIR_BONES):
                w = fade * (ws / tot_s) * raw[j] / rt
                if w > 0.01:
                    adds[names_by_sector[s][j]] = adds.get(names_by_sector[s][j], 0.0) + w
        share = min(1.0, sum(adds.values())); ta = max(sum(adds.values()), 1e-6)
        final = {n: (1.0 - share) * w for n, w in final.items()}
        for n, w in adds.items():
            final[n] = final.get(n, 0.0) + w * share / ta
        written += 1
    side, d = min(((sd, seg_d(p, *shoulders[sd])) for sd in shoulders), key=lambda t: t[1])
    if d < SHOULDER_ZONE:
        x = max(0.0, min(1.0, (SHOULDER_ZONE - d) / (SHOULDER_ZONE - SHOULDER_INNER))); sh = SHOULDER_SHARE * x * x * (3 - 2 * x)
        final = {n: (1.0 - sh) * w for n, w in final.items()}
        final["clavicle_" + side] = final.get("clavicle_" + side, 0.0) + sh * 0.6
        final["upperarm_" + side] = final.get("upperarm_" + side, 0.0) + sh * 0.4
        shoulder_touched += 1
    for g in list(v.groups):
        m.vertex_groups[g.group].remove([vi])
    tot = sum(final.values()) or 1.0
    for n, w in final.items():
        if w > 1e-4:
            (m.vertex_groups.get(n) or m.vertex_groups.new(name=n)).add([vi], w / tot, 'REPLACE')
report = {"hair_verts": len(hair), "weighted": written, "shoulder_follow": shoulder_touched, "chains": {str(k): {"low_z": round(s["low"], 3), "len_m": round((s["joints"][0] - s["joints"][-1]).length, 3)} for k, s in sectors.items()}}
print("HAIR", json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=out)
