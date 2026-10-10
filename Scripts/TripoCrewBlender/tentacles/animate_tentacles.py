"""Procedural tentacle clips: Crawl, Idle, TurnL, TurnR (in place, looping). Each tentacle phased by azimuth."""
import bpy, math, random, re, sys
from mathutils import Matrix, Vector
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
pb = arm.pose.bones
random.seed(7)
tent = {}
for b in pb:
    mm = re.match(r"Tent(\d+)_(\d+)", b.name)
    if mm:
        tent.setdefault(int(mm.group(1)), {})[int(mm.group(2))] = b
pel = arm.data.bones['Pelvis'].head_local
az = {}
for t, ch in tent.items():
    tip = arm.data.bones[ch[max(ch)].name].tail_local
    az[t] = math.atan2(tip.y - pel.y, tip.x - pel.x)
jit = {t: random.uniform(-0.4, 0.4) for t in tent}
armt = {}
for b in pb:
    mm = re.match(r"([LR])ArmTent(\d+)_(\d+)", b.name)
    if mm:
        armt.setdefault(mm.group(1) + mm.group(2), {})[int(mm.group(3))] = b
armph = {k: random.uniform(0, 6.28) for k in armt}
for b in pb:
    b.rotation_mode = 'XYZ'
rest_inv = {b.name: b.matrix_local.inverted() for b in arm.data.bones}
mesh = [o for o in bpy.data.objects if o.type == 'MESH'][0]
gname = {g.index: g.name for g in mesh.vertex_groups}
samples = {}
for v in mesh.data.vertices:
    if not v.groups:
        continue
    g = max(v.groups, key=lambda g: g.weight)
    nm = gname[g.group]
    if nm.startswith('Tent') and g.weight > 0.5:
        samples.setdefault(nm, []).append(v.co.copy())
for nm, pts in samples.items():
    pts.sort(key=lambda p: p.z)
    keep = pts[:24] + pts[24::max(1, len(pts) // 16)]
    samples[nm] = [(p, max(p.z, 0.0)) for p in keep]


def clear():
    for b in pb:
        b.location = (0, 0, 0)
        b.rotation_euler = (0, 0, 0)


def key(f):
    for b in pb:
        b.keyframe_insert("rotation_euler", frame=f)
        if b.name == "Pelvis":
            b.keyframe_insert("location", frame=f)


def make(name, frames, amp0, amp1, cycles, phase_fn, bob, sway, arm_amp, travel=0.75, floor_guard=True):
    act = bpy.data.actions.new(name)
    arm.animation_data_create()
    arm.animation_data.action = act
    for f in range(frames + 1):
        T = 2 * math.pi * cycles * f / frames
        clear()
        for t, ch in tent.items():
            ph = phase_fn(t)
            nb = len(ch)
            for i, b in ch.items():
                a = math.radians(amp0 + (amp1 - amp0) * i / (nb - 1))
                w = T + ph - i * travel
                b.rotation_euler = (a * math.sin(w), 0.0, 0.6 * a * math.cos(w))  # no twist: it rolls curled loops into the floor
        # floor contact on the skin itself: every tentacle bone carries samples of the skin it drives; if any
        # sample would sink below its own rest height, the bone pivots up about its head by exactly that much.
        if floor_guard:
            for t, ch in tent.items():
                for i in sorted(ch):
                    b = ch[i]
                    smp = samples.get(b.name)
                    if not smp:
                        continue
                    for _ in range(3):
                        bpy.context.view_layer.update()
                        M = b.matrix @ rest_inv[b.name]
                        h = b.head.copy()
                        worst, wp = 0.0, None
                        for p_rest, zr in smp:
                            q = M @ p_rest
                            if zr - q.z > worst:
                                worst, wp = zr - q.z, q
                        if wp is None or worst < 0.003:
                            break
                        r = wp - h
                        horiz = Vector((r.x, r.y, 0.0))
                        if horiz.length < 1e-4:
                            break
                        axis = horiz.normalized().cross(Vector((0, 0, 1)))
                        ang = math.atan2(worst, horiz.length)
                        b.matrix = Matrix.Translation(h) @ Matrix.Rotation(ang, 4, axis) @ Matrix.Translation(-h) @ b.matrix
        p = pb['Pelvis']
        p.location = (0, bob * math.sin(2 * T), 0)
        p.rotation_euler = (0, math.radians(sway * math.sin(T + 0.7)), 0)  # twist about the spine only, no tilt
        for s in ('Spine01', 'Spine02'):
            if s in pb:
                pb[s].rotation_euler = (0, math.radians(-sway * 0.45 * math.sin(T + 0.7)), 0)
        for k, ch in armt.items():
            nb2 = len(ch)
            for i, b in ch.items():
                a = math.radians(arm_amp * (0.6 + 2.2 * i / (nb2 - 1)))
                w = T * (1.0 if k.endswith('0') else 1.3) + armph[k] - i * 0.6
                b.rotation_euler = (a * math.sin(w), 0, 0.7 * a * math.cos(0.8 * w))
        for side, sg in ():
            for k, bn in enumerate((side + '_Forearm', side + '_Hand')):
                if bn in pb:
                    pb[bn].rotation_euler = (math.radians(arm_amp * math.sin(T * 0.5 + k * 0.9 + sg)), 0,
                                             math.radians(arm_amp * 0.6 * math.cos(T * 0.5 + k * 0.9)))
            for fn in ('Index', 'Mid', 'Ring', 'Pinky', 'Thumb'):
                for j in (1, 2, 3):
                    bn = "%s_%s%d" % (side, fn, j)
                    if bn in pb:
                        pb[bn].rotation_euler = (math.radians(arm_amp * 1.4 * math.sin(T * 0.5 - j * 0.8 + sg)), 0, 0)
        key(f)
    act.use_fake_user = True
    return act


make("TentCrawl", 48, 5, 13, 1, lambda t: az[t] + jit[t], 0.012, 2.5, 6)  # bob in metres
make("TentIdle", 96, 2, 7, 1, lambda t: 2.7 * t + jit[t] * 3, 0.005, 1.0, 4, travel=0.55)
make("TentTurnL", 48, 4, 11, 1, lambda t: 2 * az[t], 0.006, 1.5, 5)
make("TentTurnR", 48, 4, 11, 1, lambda t: -2 * az[t], 0.006, 1.5, 5)
arm.animation_data.action = bpy.data.actions["TentCrawl"]
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[-1])
print("TENTANIM", [a.name for a in bpy.data.actions], "tentacles", len(tent))
