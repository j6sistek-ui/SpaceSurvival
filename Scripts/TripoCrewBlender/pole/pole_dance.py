"""Pole-dance clips for a crew character, authored procedurally in Blender on the rigged rest-pose .blend.

  blender -b <rig>.blend --factory-startup -P pole_dance.py -- <outdir> <Name> [<Clip> ...]
  clips: Idle HipCircle BodyWave BackSlide Spin Kick        (all of them when none is given; one Blender per clip)

No pack the owner has contains pole work (checked 2026-10-09: every vault, Content/ and M:), so these are built
from scratch. THE POLE STANDS ON THE CLIP ORIGIN (x = y = 0, vertical, 2.5 cm radius): place a pole mesh on the
actor's origin and every clip lines up. Her plain clips (idle, walk) also stand on that origin, so a pole dancer is
her own actor. In place, 30 fps, loops where the table says so.

How: the rest pose faces -Y (crew convention; her left is +x). Wrists and ankles are driven by 2-bone IK on empties
(the targets sit where the forearm/calf TAIL must be, solved by iteration, because on this skeleton the calf ends
11 cm above the ankle and the forearm 4 cm short of the hand); feet keep a world orientation (copy-rotation to an
empty: flat on the floor unless a move points them); the head damped-tracks a look target; a gripping hand is set
in world space with its palm into the pole and fingers curled; pelvis, spine and chest are keyed as world-space
matrices. Everything is baked to plain FK keys and exported one FBX per clip in centimetres (scale_length 0.01,
x100 applied, location keys x100 - the tentacles/export_for_unreal.py recipe) for Scripts/ImportCrewClips.py.
Eight clay frames per clip land beside the FBX for a first look; the owner judges the real thing in the studio.
"""
import math
import os
import subprocess
import sys

import bpy
from mathutils import Matrix, Vector

args = sys.argv[sys.argv.index("--") + 1:]
OUTDIR, NAME = args[0], args[1]
ALL = ["Idle", "HipCircle", "BodyWave", "BackSlide", "Spin", "Kick"]
CLIPS = args[2:] or ALL
FPS = 30
POLE_R = 0.025
os.makedirs(OUTDIR, exist_ok=True)

if len(CLIPS) > 1:                       # a fresh Blender per clip: the bake and the x100 export must not leak
    for clip in CLIPS:
        subprocess.check_call([bpy.app.binary_path, "-b", bpy.data.filepath, "--factory-startup", "-P",
                               os.path.abspath(__file__), "--", OUTDIR, NAME, clip])
    sys.exit(0)
CLIP = CLIPS[0]

sc = bpy.context.scene
sc.render.fps = FPS
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
mesh = [o for o in bpy.data.objects if o.type == 'MESH'][0]
PB = arm.pose.bones
REST = {b.name: b.matrix_local.copy() for b in arm.data.bones}
TAIL = {b.name: b.matrix_local @ Vector((0, b.length, 0)) for b in arm.data.bones}
for b in PB:
    b.rotation_mode = 'QUATERNION'


def up():
    bpy.context.view_layer.update()


def empty(name, loc=(0, 0, 0)):
    o = bpy.data.objects.new(name, None); sc.collection.objects.link(o)
    o.location = loc; o.rotation_mode = 'XYZ'
    return o


# ---------------------------------------------------------------- rig controls
E = {}
GAP = {}                                  # end-effector gap in the IK bone's local frame: (bone, child head - bone tail)
for side in ("l", "r"):
    E["wrist_" + side] = empty("tgt_wrist_" + side, TAIL["lowerarm_" + side])
    E["ankle_" + side] = empty("tgt_ankle_" + side, TAIL["calf_" + side])
    E["elbow_" + side] = empty("pole_elbow_" + side)
    E["knee_" + side] = empty("pole_knee_" + side)
    E["foot_" + side] = empty("rot_foot_" + side)
    E["foot_" + side].rotation_euler = REST["foot_" + side].to_euler('XYZ')
    GAP["lowerarm_" + side] = REST["lowerarm_" + side].to_3x3().inverted() @ (REST["hand_" + side].translation - TAIL["lowerarm_" + side])
    GAP["calf_" + side] = REST["calf_" + side].to_3x3().inverted() @ (REST["foot_" + side].translation - TAIL["calf_" + side])
E["look"] = empty("tgt_look", (0, -3, 1.6))


def add_ik(bone, target, pole):
    c = PB[bone].constraints.new('IK'); c.target = target; c.pole_target = pole; c.chain_count = 2
    c.use_tail = True; c.iterations = 200
    return c


IK = {}
for side, sgn in (("l", 1), ("r", -1)):
    E["elbow_" + side].location = REST["lowerarm_" + side].translation + Vector((0, 0.6, -0.5))   # elbows back and down
    E["knee_" + side].location = REST["calf_" + side].translation + Vector((0.08 * sgn, -0.8, 0))   # knees forward
    IK["arm_" + side] = add_ik("lowerarm_" + side, E["wrist_" + side], E["elbow_" + side])
    IK["leg_" + side] = add_ik("calf_" + side, E["ankle_" + side], E["knee_" + side])
    c = PB["foot_" + side].constraints.new('COPY_ROTATION'); c.target = E["foot_" + side]
    c.owner_space = 'WORLD'; c.target_space = 'WORLD'
c = PB["head"].constraints.new('DAMPED_TRACK'); c.target = E["look"]; c.track_axis = 'TRACK_X'; c.influence = 0.55


def calibrate(ik_name, bone):
    """pole_angle that reproduces the rest pose when the target sits on the rest tail."""
    c = IK[ik_name]; want = REST[bone].translation.copy(); best = (1e9, 0.0)
    for sweep in (range(-180, 180, 10), None):
        degs = sweep if sweep is not None else [best[1] + k for k in range(-10, 11)]
        for deg in degs:
            c.pole_angle = math.radians(deg); up()
            d = (PB[bone].head - want).length
            if d < best[0]:
                best = (d, deg)
    c.pole_angle = math.radians(best[1]); up()
    print("POLE| %s pole_angle %d deg (rest error %.1f mm)" % (ik_name, best[1], best[0] * 1000))


for side in ("l", "r"):
    calibrate("arm_" + side, "lowerarm_" + side)
    calibrate("leg_" + side, "calf_" + side)

# finger curl: about each finger bone's local X (the palm faces -Z in the T-pose, fingers run along local Y)
CURL = {"thumb": (-20, -30, -20), "index": (-55, -75, -45), "middle": (-60, -80, -45), "ring": (-60, -80, -45), "pinky": (-55, -75, -45)}


def grip_fingers(side, amount=1.0):
    for finger, degs in CURL.items():
        for i, deg in enumerate(degs):
            PB["%s_%02d_%s" % (finger, i + 1, side)].rotation_quaternion = Matrix.Rotation(math.radians(deg * amount), 4, 'X').to_quaternion()


# ---------------------------------------------------------------- world-space posing helpers
def set_world(name, M):
    PB[name].matrix = M; up()


def rot_about(M, axis, deg, pivot=None):
    p = M.translation if pivot is None else Vector(pivot)
    return Matrix.Translation(p) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-p) @ M


def pelvis_at(pos, yaw=0, pitch=0, roll=0):
    M = REST["pelvis"].copy(); M.translation = Vector(pos)
    M = rot_about(M, 'Z', yaw); M = rot_about(M, 'X', pitch); M = rot_about(M, 'Y', roll)
    set_world("pelvis", M)


def bend(name, pitch=0, roll=0, yaw=0):
    """Spine/neck/head: a bend relative to the parent's CURRENT pose, so a chain adds up."""
    parent = PB[name].parent
    M = parent.matrix @ (REST[parent.name].inverted() @ REST[name])
    M = rot_about(M, 'X', pitch); M = rot_about(M, 'Y', roll); M = rot_about(M, 'Z', yaw)
    set_world(name, M)


def solve(want):
    """Put the IK targets where the forearm/calf tails must be for the hands/ankles to land on `want`."""
    for _ in range(5):
        for bone, key in (("lowerarm_l", "hand_l"), ("lowerarm_r", "hand_r"), ("calf_l", "foot_l"), ("calf_r", "foot_r")):
            if key in want:
                E[("wrist_" if "arm" in bone else "ankle_") + bone[-1]].location = Vector(want[key]) - PB[bone].matrix.to_3x3() @ GAP[bone]
        up()


def hand_on_pole(side, fingers=1.0):
    """Wrap the hand around the pole where it is: palm into the pole, fingers tangent, continuing the forearm."""
    g = PB["hand_" + side].head; d = Vector((-g.x, -g.y, 0)).normalized()
    fwd = PB["lowerarm_" + side].vector.normalized()
    y = Vector((0, 0, 1)).cross(d); y = y if y.dot(fwd) >= 0 else -y
    z = -d; x = y.cross(z)
    M = Matrix((x, y, z)).transposed().to_4x4(); M.translation = g
    set_world("hand_" + side, M); grip_fingers(side, fingers)


def hand_free(side, roll=0):
    M = PB["lowerarm_" + side].matrix @ (REST["lowerarm_" + side].inverted() @ REST["hand_" + side])
    set_world("hand_" + side, rot_about(M, 'Y', roll)); grip_fingers(side, 0.35)


def key_all(f):
    for b in PB:
        b.keyframe_insert("rotation_quaternion", frame=f); b.keyframe_insert("location", frame=f)
    for o in E.values():
        o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)


def on_pole(azimuth_deg, z, r=POLE_R + 0.012):
    """A grip point: the hand's head sits just outside the pole surface, the curled fingers do the rest."""
    a = math.radians(azimuth_deg); return Vector((r * math.cos(a), r * math.sin(a), z))


def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, t)))


REST_PELVIS = REST["pelvis"].translation.copy()          # (0.004, 0.024, 1.046)
ANKLE = {s: REST["foot_" + s].translation.copy() for s in ("l", "r")}   # z 0.143, x +-0.10
STAND_Z = REST_PELVIS.z
FEET_FLAT = {s: REST["foot_" + s].to_euler('XYZ') for s in ("l", "r")}


def feet_planted(want, centre, width=1.0, yaw_deg=0.0):
    cx, cy = centre; a = math.radians(yaw_deg); left = Vector((math.cos(a), math.sin(a), 0))
    for side, sgn in (("l", 1), ("r", -1)):
        p = Vector((cx, cy, 0)) + left * (0.10 * width * sgn) + Vector((0, 0.017, ANKLE[side].z))
        want["foot_" + side] = p
        E["foot_" + side].rotation_euler = (Matrix.Rotation(a, 4, 'Z') @ REST["foot_" + side]).to_euler('XYZ')


# ---------------------------------------------------------------- the moves (t in [0,1) for loops)
def clip_idle(t):
    """Standing at the pole's right, right hand resting high on it, weight shifting. 4 s loop."""
    w = 2 * math.pi * t; cx = 0.34; want = {}
    feet_planted(want, (cx, 0.0), width=1.1)
    sway = 0.03 * math.sin(w)
    pelvis_at((cx + sway, 0.01 * math.sin(2 * w), STAND_Z - 0.012 + 0.01 * math.cos(2 * w)), yaw=-6 + 3 * math.sin(w), roll=-3 * math.sin(w))
    bend("spine_01", pitch=2, roll=2 * math.sin(w)); bend("spine_02", roll=1.5 * math.sin(w)); bend("spine_03", roll=2 * math.sin(w), yaw=4)
    bend("neck_01"); bend("head")
    want["hand_r"] = on_pole(10, 1.56 + 0.01 * math.sin(w)); E["elbow_r"].location = (-0.25, 0.35, 1.2)
    want["hand_l"] = (cx + 0.25 + 0.02 * math.sin(w), 0.04, 0.86 + 0.01 * math.sin(w)); E["elbow_l"].location = (cx + 0.5, 0.5, 0.9)
    E["look"].location = (cx - 0.3 + 0.4 * math.sin(w * 0.5), -2.5, 1.55)
    solve(want); hand_on_pole("r"); hand_free("l")


def clip_hipcircle(t):
    """Hips circling beside the pole, right hand gripping high, left hand on the hip. 4 s loop."""
    w = 2 * math.pi * t; cx = 0.34; want = {}
    feet_planted(want, (cx, 0.0), width=1.25)
    pelvis_at((cx + 0.06 * math.sin(w), 0.05 * math.cos(w), STAND_Z - 0.05 - 0.02 * math.cos(2 * w)),
              yaw=-5 + 4 * math.sin(w), pitch=-6 * math.cos(w), roll=-7 * math.sin(w))
    bend("spine_01", pitch=4 * math.cos(w), roll=3 * math.sin(w)); bend("spine_02", pitch=3 * math.cos(w))
    bend("spine_03", pitch=-5 * math.cos(w), roll=-4 * math.sin(w), yaw=6); bend("neck_01"); bend("head")
    want["hand_r"] = on_pole(10, 1.62); E["elbow_r"].location = (-0.25, 0.3, 1.3)
    want["hand_l"] = PB["pelvis"].head + Vector((0.19, -0.03, -0.02)); E["elbow_l"].location = (cx + 0.6, 0.4, 0.95)
    E["look"].location = (cx - 0.2 + 0.3 * math.sin(w), -2.5, 1.5)
    solve(want); hand_on_pole("r"); hand_free("l", roll=-20)


def clip_bodywave(t):
    """Facing the pole, both hands on it at chest height, a body wave travelling down. 3 s loop."""
    w = 2 * math.pi * t; cy = 0.40; want = {}
    feet_planted(want, (0.0, cy), width=1.2)
    push = math.sin(w)
    pelvis_at((0.0, cy - 0.06 * push, STAND_Z - 0.04 - 0.04 * ease(0.5 + 0.5 * push)), pitch=-8 * push)
    bend("spine_01", pitch=10 * math.sin(w - 0.7)); bend("spine_02", pitch=8 * math.sin(w - 1.4))
    bend("spine_03", pitch=8 * math.sin(w - 2.1)); bend("neck_01", pitch=6 * math.sin(w - 2.8)); bend("head", pitch=-4 * math.sin(w - 2.8))
    want["hand_l"] = on_pole(60, 1.24 + 0.02 * math.sin(w - 1.4)); want["hand_r"] = on_pole(120, 1.24 + 0.02 * math.sin(w - 1.4))
    E["elbow_l"].location = (0.45, 0.8, 1.0); E["elbow_r"].location = (-0.45, 0.8, 1.0)
    E["look"].location = (0.0, -1.0, 1.75)
    solve(want); hand_on_pole("l"); hand_on_pole("r")


def clip_backslide(t):
    """Back to the pole, hands overhead on it, knees bend to slide down and back up with a hip sway. 6 s loop."""
    w = 2 * math.pi * t; cy = -0.15; want = {}
    feet_planted(want, (0.0, cy + 0.08), width=1.5)
    down = ease(0.5 - 0.5 * math.cos(w))                                     # 0 standing -> 1 low -> 0
    for side, sgn in (("l", 1), ("r", -1)):
        E["knee_" + side].location = (sgn * (0.3 + 0.5 * down), -0.8, 0.3)
    pelvis_at((0.04 * math.sin(2 * w) * down, cy - 0.02 * down, STAND_Z - 0.36 * down), pitch=6 * down, roll=4 * math.sin(2 * w) * down)
    bend("spine_01", pitch=-4 * down); bend("spine_02", pitch=-3); bend("spine_03", pitch=-5 + 2 * down, roll=-3 * math.sin(2 * w) * down)
    bend("neck_01", pitch=-6); bend("head", pitch=-4)
    hz = 1.76 - 0.10 * down
    want["hand_l"] = on_pole(30, hz); want["hand_r"] = on_pole(150, hz)
    E["elbow_l"].location = (0.45, 0.1, 1.9); E["elbow_r"].location = (-0.45, 0.1, 1.9)
    E["look"].location = (0.3 * math.sin(w), -2.5, 1.5)
    solve(want); hand_on_pole("l"); hand_on_pole("r")


def clip_spin(t):
    """Fireman spin: hands high, the body carried once and a quarter forward around the pole while sliding down,
    knees bent and ankles tucked, landing in a crouch and standing back up. 5 s, one shot."""
    s_in, s_spin, s_out = 0.16, 0.62, 0.22
    r0, r1 = 0.33, 0.21; want = {}
    if t < s_in:
        u_ = ease(t / s_in); theta = 0.0; r = r0 - (r0 - r1) * 0.5 * u_; z = STAND_Z - 0.02 * u_; lift = 0.0; crouch = 0.0
    elif t < s_in + s_spin:
        u_ = (t - s_in) / s_spin; theta = -450 * ease(u_) ** 0.9; r = r1; z = STAND_Z - 0.02 - 0.40 * ease(u_)
        lift = math.sin(math.pi * min(1.0, u_ * 1.1)); crouch = 1.0
    else:
        u_ = ease((t - s_in - s_spin) / s_out); theta = -450; r = r1 + (r0 - r1) * 0.3 * u_; z = STAND_Z - 0.42 + 0.42 * u_; lift = 0.0; crouch = 1.0 - u_
    a = math.radians(theta)
    radial = Vector((math.cos(a), math.sin(a), 0)); fwd = Vector((math.sin(a), -math.cos(a), 0))   # radial = her left
    pel = radial * r + Vector((0, 0, z))
    pelvis_at(pel, yaw=theta - 8, pitch=4 * crouch, roll=-10 * lift)
    bend("spine_01", pitch=-3 * crouch); bend("spine_02"); bend("spine_03", pitch=-4 * crouch, yaw=-10 * lift); bend("neck_01", pitch=-6 * lift); bend("head")
    for side, sgn in (("l", 1), ("r", -1)):
        planted = radial * (r + 0.10 * sgn) + fwd * 0.02 + Vector((0, 0, ANKLE[side].z))
        tucked = radial * (r + 0.04 * sgn) + fwd * (0.06 if side == "l" else 0.02) + Vector((0, 0, z - 0.52 + (0.06 if side == "l" else 0)))
        want["foot_" + side] = planted.lerp(tucked, lift)
        E["knee_" + side].location = radial * (r + 0.25 * sgn) + fwd * 0.6 + Vector((0, 0, 0.5))
        E["foot_" + side].rotation_euler = (Matrix.Rotation(a, 4, 'Z') @ Matrix.Rotation(math.radians(-35 * lift), 4, 'X') @ REST["foot_" + side]).to_euler('XYZ')
    hz = 1.78 - 0.30 * (1 - (z - 0.56) / (STAND_Z - 0.56))
    want["hand_r"] = on_pole(theta - 10, hz + 0.08); want["hand_l"] = on_pole(theta - 40, hz - 0.08)
    E["elbow_r"].location = pel + Vector((0, 0, 0.3)) - fwd * 0.3 - radial * 0.3; E["elbow_l"].location = pel + Vector((0, 0, 0.2)) - fwd * 0.2 + radial * 0.2
    E["look"].location = pel + Vector((0, 0, 0.5)) + fwd * 1.5
    solve(want); hand_on_pole("r"); hand_on_pole("l")


def clip_kick(t):
    """Right hand high on the pole, the left leg sweeps up into a side extension, holds, comes down. 3 s, one shot."""
    cx = 0.34; want = {}
    lift = ease((t - 0.15) / 0.35) * (1 - ease((t - 0.65) / 0.3))
    want["foot_r"] = (cx - 0.08, 0.017, ANKLE["r"].z); E["foot_r"].rotation_euler = FEET_FLAT["r"]
    want["foot_l"] = Vector((cx + 0.11, 0.017, ANKLE["l"].z)).lerp(Vector((cx + 0.78, 0.05, 0.95)), lift)
    E["foot_l"].rotation_euler = (Matrix.Rotation(math.radians(-70 * lift), 4, 'Y') @ Matrix.Rotation(math.radians(-30 * lift), 4, 'X') @ REST["foot_l"]).to_euler('XYZ')
    E["knee_l"].location = (cx + 0.6, -0.6, 0.6 + 0.4 * lift); E["knee_r"].location = (cx - 0.15, -0.8, 0.5)
    pelvis_at((cx - 0.05 * lift, 0.0, STAND_Z - 0.03 - 0.03 * lift), yaw=-8, roll=14 * lift)
    bend("spine_01", roll=-6 * lift); bend("spine_02", roll=-5 * lift); bend("spine_03", roll=-6 * lift, yaw=6); bend("neck_01", roll=4 * lift); bend("head")
    want["hand_r"] = on_pole(10, 1.66); E["elbow_r"].location = (-0.25, 0.3, 1.3)
    want["hand_l"] = Vector((cx + 0.26, 0.04, 0.88)).lerp(Vector((cx + 0.55, -0.1, 1.45)), lift); E["elbow_l"].location = (cx + 0.6, 0.5, 1.0)
    E["look"].location = (cx + 0.5 * lift, -2.5, 1.6)
    solve(want); hand_on_pole("r"); hand_free("l", roll=-30 * lift)


MOVES = {"Idle": (clip_idle, 4.0, True), "HipCircle": (clip_hipcircle, 4.0, True), "BodyWave": (clip_bodywave, 3.0, True),
         "BackSlide": (clip_backslide, 6.0, True), "Spin": (clip_spin, 5.0, False), "Kick": (clip_kick, 3.0, False)}


def fcurves(a):
    if hasattr(a, "fcurves"):
        return list(a.fcurves)
    return [fc for layer in a.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]


def render_strip(n, prefix):
    """Eight clay frames from the front-right with the pole drawn: a first look, not the judgement."""
    bpy.ops.mesh.primitive_cylinder_add(radius=POLE_R, depth=2.6, location=(0, 0, 1.3)); pole = bpy.context.active_object
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0)); floor = bpy.context.active_object
    clay = bpy.data.materials.new("clay"); clay.diffuse_color = (0.7, 0.68, 0.65, 1)
    steel = bpy.data.materials.new("steel"); steel.diffuse_color = (0.9, 0.8, 0.25, 1)
    mesh.data.materials.clear(); mesh.data.materials.append(clay); pole.data.materials.append(steel)
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 8; sc.cycles.use_denoising = False
    sc.render.resolution_x, sc.render.resolution_y = 360, 480; sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.3, 0.3, 0.33, 1)
    for r, e in (((55, 0, 35), 3.0), ((65, 0, 215), 1.5)):
        light = bpy.data.lights.new("k", 'SUN'); light.energy = e; o = bpy.data.objects.new("k", light); sc.collection.objects.link(o)
        o.rotation_euler = [math.radians(x) for x in r]
    cam = bpy.data.cameras.new("c"); cam.lens = 40; co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co
    co.location = (2.2, -3.0, 1.3); co.rotation_euler = (math.radians(80), 0, math.radians(36))
    for i in range(8):
        sc.frame_set(1 + int(i * (n - 1) / 7)); sc.render.filepath = "%s_%d.png" % (prefix, i); bpy.ops.render.render(write_still=True)
    for o in (pole, floor):
        bpy.data.objects.remove(o)


def author(clip):
    fn, seconds, loop = MOVES[clip]
    n = int(seconds * FPS); last = n + 1 if loop else n          # a loop keys its wrap-around frame too
    for f in range(1, last + 1):
        sc.frame_set(f)
        fn(((f - 1) % n) / n if loop else (f - 1) / (n - 1))
        key_all(f)
    sc.frame_start, sc.frame_end = 1, last
    bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.nla.bake(frame_start=1, frame_end=last, only_selected=False, visual_keying=True, clear_constraints=False,
                     use_current_action=False, bake_types={'POSE'})
    bpy.ops.object.mode_set(mode='OBJECT')
    act = arm.animation_data.action; act.name = "Pole" + clip
    for b in PB:
        for c in b.constraints:
            c.mute = True
    print("POLE| %s: %d frames (%s)" % (clip, last, "loop" if loop else "one shot"))
    return act


def export(clip, act):
    sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 0.01
    for o in (arm, mesh):
        if o.parent is None:
            o.scale = (100, 100, 100); o.location = o.location * 100
    bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); mesh.select_set(True); bpy.context.view_layer.objects.active = arm
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for fc in fcurves(act):
        if fc.data_path.endswith(".location"):
            for k in fc.keyframe_points:
                k.co.y *= 100; k.handle_left.y *= 100; k.handle_right.y *= 100
    arm.animation_data.action = act
    path = os.path.join(OUTDIR, "%s_Pole%s.fbx" % (NAME, clip))
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                             apply_scale_options='FBX_SCALE_ALL', use_armature_deform_only=False, mesh_smooth_type='FACE',
                             primary_bone_axis='Y', secondary_bone_axis='X', path_mode='STRIP', bake_anim=True,
                             bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True,
                             bake_anim_simplify_factor=0.0)
    print("POLE| wrote", path)


action = author(CLIP)
render_strip(sc.frame_end, os.path.join(OUTDIR, "%s_Pole%s_strip" % (NAME, CLIP)))
export(CLIP, action)
