"""Bake physically simulated hair motion into every clip of a long-haired crew member (Elf, Silver).

  UnrealEditor-Cmd.exe <project> -unattended -NullRHI -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/Scripts/AuthorTripoCrewHair.py"

The owner: hair must "move fluidly with motions/physics", not ride the head rigidly. The hair chains come from
Scripts/TripoCrewBlender/rig_hair.py (hair_<azimuth>_<n> under `head`); no source clip has them, so the retargeter
leaves them at the reference pose and this writes their motion.

Per clip, each chain is simulated as a strand of particles (Verlet integration, SUBSTEPS per key): the root is
pinned to the scalp, every particle is pulled toward where the rest pose would put it (stiffer at the root, looser
at the tips), segment lengths are held, there is a little gravity and air damping, and particles are pushed out of
capsules around the neck, torso, shoulders and upper arms so hair does not pass through the body. Each capsule is
shrunk, per chain, until no rest-pose hair particle is inside it - hair that lies on the back at rest must not be
shoved off it. That gives follow-through on turns, bounce on steps, swing in dances and settling after big moves.
The clip is simulated twice and the second pass recorded; its last LOOP_BLEND eases back onto its own start (in head
space), so loops close.

IDEMPOTENT: the sim reads the body from the clip and the hair rest pose from the skeleton, never the clip's hair
tracks, so re-running replaces the bake. SS_HAIR_WHO=Elf,Silver (default both). The maths is plain Python on
tuples: unreal.Vector per operation made a clip take tens of seconds.
"""
import json
import math
import os

import unreal as u

CREW = "/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew"
LIB = u.EditorAssetLibrary
AP = u.AnimPoseExtensions
SUBSTEPS = 4
DAMPING = 0.06            # fraction of velocity lost per substep
GRAVITY = -980.0 * 0.35   # cm/s^2: the rest pose already hangs, so only a share of real gravity adds sag
STIFF_ROOT, STIFF_TIP = 0.35, 0.04   # per-substep pull toward the rest-pose position
HAIR_R = 1.2              # cm, strand thickness for collision
LOOP_BLEND = 0.15
# (bone a, bone b, radius cm, floor cm). A capsule shrinks toward its floor to keep rest-pose hair outside it, but
# never below: with no floor, locks draped over a shoulder shrank the shoulder capsules to nothing and the rising
# shoulder cut straight through the hair cards (the owner's "biggest concern").
CAPSULES = [("spine_02", "neck_01", 11.0, 8.0), ("neck_01", "head", 6.0, 5.0), ("clavicle_l", "upperarm_l", 7.0, 6.0),
            ("clavicle_r", "upperarm_r", 7.0, 6.0), ("upperarm_l", "lowerarm_l", 5.0, 4.5), ("upperarm_r", "lowerarm_r", 5.0, 4.5)]
BODY = sorted({b for a, c, _, _ in CAPSULES for b in (a, c)})


def line(s):
    u.log_warning("HAIR| " + str(s))


def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def mul(a, k): return (a[0] * k, a[1] * k, a[2] * k)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def length(a): return math.sqrt(dot(a, a))
def norm(a):
    n = length(a); return mul(a, 1.0 / n) if n > 1e-9 else (0.0, 0.0, -1.0)


# quaternions as (x, y, z, w)
def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)
def qinv(q): return (-q[0], -q[1], -q[2], q[3])
def qnorm(q):
    n = math.sqrt(sum(c * c for c in q)) or 1.0; return tuple(c / n for c in q)
def qrot(q, v):
    qv = q[:3]; t = mul(cross(qv, v), 2.0)
    return add(add(v, mul(t, q[3])), cross(qv, t))
def qbetween(a, b):
    a, b = norm(a), norm(b); c = dot(a, b)
    if c > 0.999999: return (0.0, 0.0, 0.0, 1.0)
    if c < -0.999999:
        ax = norm(cross(a, (1.0, 0.0, 0.0)) if abs(a[0]) < 0.9 else cross(a, (0.0, 1.0, 0.0))); return (ax[0], ax[1], ax[2], 0.0)
    ax = cross(a, b); s = math.sqrt((1 + c) * 2); return qnorm((ax[0] / s, ax[1] / s, ax[2] / s, s / 2))


def tup(v): return (v.x, v.y, v.z)
def qtup(q): return (q.x, q.y, q.z, q.w)
def xform(T): return (qtup(T.rotation), tup(T.translation))       # (rot, pos); crew transforms have no scale
def apply(T, p): return add(qrot(T[0], p), T[1])
def unapply(T, p): return qrot(qinv(T[0]), sub(p, T[1]))


def seg_dist(p, a, b):
    ab = sub(b, a); t = max(0.0, min(1.0, dot(sub(p, a), ab) / max(dot(ab, ab), 1e-9)))
    c = add(a, mul(ab, t)); d = sub(p, c); return length(d), c, d


def push_out(p, a, b, r):
    n, c, d = seg_dist(p, a, b)
    return add(c, mul(norm(d) if n > 1e-6 else (0.0, 1.0, 0.0), r)) if n < r else p


def chains_of(bones):
    ch = {}
    for b in bones:
        if b.lower().startswith("hair_"):
            _, az, j = b.split("_"); ch.setdefault(az, []).append((int(j), b))
    return {az: [b for _, b in sorted(v)] for az, v in ch.items()}


def main():
    who_list = [w for w in os.environ.get("SS_HAIR_WHO", "Elf,Silver").split(",") if w]
    opts = u.AnimPoseEvaluationOptions()
    report = {}
    for who in who_list:
        clips = [p.split(".")[0] for f in ("%s/%s" % (CREW, who), "%s/%s/Role" % (CREW, who))
                 for p in LIB.list_assets(f, recursive=False, include_folder=False)]
        clips = [p for p in clips if p.rsplit("/", 1)[1].startswith("A_")]
        if not clips:
            report[who] = "no clips"; continue
        skel = LIB.load_asset(clips[0]).get_editor_property("skeleton")
        ref = AP.get_reference_pose(skel)
        chains = chains_of([str(n) for n in AP.get_bone_names(ref)])
        if not chains:
            report[who] = "no hair bones"; continue
        W = lambda pose, b: xform(AP.get_bone_pose(pose, b, u.AnimPoseSpaces.WORLD))
        head_ref = W(ref, "head")
        body_ref = {b: W(ref, b)[1] for b in BODY}
        rest_local, rest_pts, tip_local, caps = {}, {}, {}, {}
        for az, c in chains.items():
            for b in c:
                L = AP.get_bone_pose(ref, b, u.AnimPoseSpaces.LOCAL); rest_local[b] = (qtup(L.rotation), tup(L.translation), L.scale3d)
            pts_c = [W(ref, b)[1] for b in c]
            tip_dir = norm(sub(pts_c[-1], pts_c[-2])); seg = length(sub(pts_c[-1], pts_c[-2]))
            pts_c.append(add(pts_c[-1], mul(tip_dir, seg)))
            tip_local[az] = qrot(qinv(W(ref, c[-1])[0]), tip_dir)
            rest_pts[az] = [unapply(head_ref, p) for p in pts_c]          # head space
            caps[az] = []
            for a, b2, r, floor in CAPSULES:
                closest = min(seg_dist(p, body_ref[a], body_ref[b2])[0] for p in pts_c[1:])
                caps[az].append((a, b2, max(floor, min(r, closest - HAIR_R - 0.3))))
        done, failed = 0, []
        for path in clips:
            seq = LIB.load_asset(path)
            if not isinstance(seq, u.AnimSequence):
                continue
            try:
                n = u.AnimationLibrary.get_num_keys(seq) if hasattr(u.AnimationLibrary, "get_num_keys") else u.AnimationLibrary.get_num_frames(seq) + 1
                dt = u.AnimationLibrary.get_sequence_length(seq) / max(n - 1, 1)
                heads, bodies = [], []
                for f in range(n):
                    pose = AP.get_anim_pose_at_frame(seq, f, opts)
                    heads.append(W(pose, "head")); bodies.append({b: W(pose, b)[1] for b in BODY})
                controller = seq.get_editor_property("controller")
                controller.open_bracket("Hair sim", False)
                for az, c in chains.items():
                    rp = rest_pts[az]; N = len(rp)
                    seglen = [length(sub(rp[i + 1], rp[i])) for i in range(N - 1)]
                    x = [apply(heads[0], p) for p in rp]; xp = list(x)
                    rec = []
                    for rnd in range(2):
                        rec = []
                        for f in range(n):
                            H, Bd = heads[f], bodies[f]
                            tgt = [apply(H, p) for p in rp]
                            h = dt / SUBSTEPS
                            for _ in range(SUBSTEPS):
                                for i in range(1, N):
                                    v = mul(sub(x[i], xp[i]), 1.0 - DAMPING)
                                    nx = add(add(x[i], v), (0.0, 0.0, GRAVITY * h * h))
                                    xp[i] = x[i]
                                    k = STIFF_ROOT + (STIFF_TIP - STIFF_ROOT) * (i / (N - 1))
                                    x[i] = add(nx, mul(sub(tgt[i], nx), k))
                                x[0] = tgt[0]; xp[0] = x[0]
                                for _ in range(3):
                                    for i in range(N - 1):
                                        d = sub(x[i + 1], x[i]); L = length(d) or 1e-6
                                        corr = mul(d, (L - seglen[i]) / L)
                                        if i == 0:
                                            x[1] = sub(x[1], corr)
                                        else:
                                            x[i] = add(x[i], mul(corr, 0.5)); x[i + 1] = sub(x[i + 1], mul(corr, 0.5))
                                    for i in range(1, N):
                                        for a, b2, r in caps[az]:
                                            if r > 0:
                                                x[i] = push_out(x[i], Bd[a], Bd[b2], r + HAIR_R)
                            rec.append(list(x))
                    m = max(1, int(n * LOOP_BLEND))
                    start = [unapply(heads[0], p) for p in rec[0]]
                    for k in range(m):
                        f = n - m + k; a = (k + 1) / float(m); a = a * a * (3 - 2 * a)
                        rec[f] = [apply(heads[f], add(mul(unapply(heads[f], rec[f][i]), 1 - a), mul(start[i], a))) for i in range(N)]
                    tracks = {b: ([], [], []) for b in c}
                    for f in range(n):
                        parent = heads[f][0]
                        for j, b in enumerate(c):
                            lr, lt, ls = rest_local[b]
                            rest_world = qnorm(qmul(parent, lr))
                            local_dir = norm(rest_local[c[j + 1]][1]) if j + 1 < len(c) else tip_local[az]
                            d_rest = qrot(rest_world, local_dir)
                            d_sim = sub(rec[f][j + 1], rec[f][j])
                            new_world = qnorm(qmul(qbetween(d_rest, d_sim), rest_world))
                            local = qnorm(qmul(qinv(parent), new_world))
                            tracks[b][0].append(u.Vector(*lt)); tracks[b][1].append(u.Quat(*local)); tracks[b][2].append(ls)
                            parent = new_world
                    for b, (pos, rot, scl) in tracks.items():
                        controller.add_bone_curve(b, False)
                        if not controller.set_bone_track_keys(b, pos, rot, scl, False):
                            raise RuntimeError("set_bone_track_keys refused " + b)
                controller.close_bracket(False)
                LIB.save_asset(path, only_if_is_dirty=False)
                done += 1
            except Exception as e:
                failed.append("%s: %s" % (path.rsplit("/", 1)[1], str(e)[:200]))
        report[who] = {"chains": len(chains), "clips": done, "n_failed": len(failed), "failed": failed[:4],
                       "capsules_used": {az: [round(r, 1) for _, _, r in cs] for az, cs in list(caps.items())[:3]}}
    line(json.dumps(report))


main()
