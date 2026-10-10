"""Bake a tail sway into every clip of a tailed crew member (Crest). No source clip has a tail, so the
retargeter leaves the tail at its reference pose; this writes the motion straight onto the tail tracks.

  UnrealEditor-Cmd.exe <project> -unattended -NullRHI -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/Scripts/AuthorTripoCrewTail.py"

Needs the tail rig from Scripts/TripoCrewBlender/rig_tail.py (tail_01..08 and tail_cord_01..05 under the pelvis)
and the clips from AuthorTripoCrew.py / AuthorTripoCrewRoles.py. SS_TAIL_WHO=Crest (default).

The motion is a travelling wave: each bone lags the one above it, and the swing grows toward the tip, so it
reads as a whip passing along the tail rather than the whole thing turning at once. Its pace follows what the
body is doing - one sway per stride in walks, a slow drift in idles and talk, a faster and bigger flick in the
scuffles and taunts - and a whole number of cycles always fits the clip, so the loop closes. The cord beside the
tail runs a quarter cycle behind it and smaller, so the two never move in lockstep.

IDEMPOTENT: the sway is composed onto the skeleton's reference pose, never onto what is in the clip, so running
this again after a re-retarget or a re-tune replaces the sway instead of stacking a second one on it.
"""
import json
import math
import os

import unreal as u

CREW = "/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew"
LIB = u.EditorAssetLibrary
TAIL = ["tail_%02d" % k for k in range(1, 9)]
CORD = ["tail_cord_%02d" % k for k in range(1, 6)]
UP = u.Vector(0.0, 0.0, 1.0)

# (period in seconds, tip swing in degrees) by what the body is doing; first matching word wins
AGITATED = ("Scuffle", "Taunt", "BringItOn", "ComeGetSome", "ThrowDown", "Stomp", "RaisedFist", "Push", "Fuming",
            "ShakeFist", "Spit", "TalkToHand", "MonkeyTaunt", "HitReact", "Gesture_Disapproval", "FingerWag")
GAIT = ("Walk", "Run", "Carry", "Haul", "Move_Forward", "Turn")
PACE = {"agitated": (0.9, 22.0), "gait": (1.1, 15.0), "relaxed": (3.2, 9.0)}


def line(s):
    u.log_warning("TAIL| " + str(s))


def mood(name):
    if any(w in name for w in AGITATED):
        return "agitated"
    if any(w in name for w in GAIT):
        return "gait"
    return "relaxed"


def axis_angle(axis, degrees):
    half = math.radians(degrees) / 2.0
    s = math.sin(half)
    return u.Quat(axis.x * s, axis.y * s, axis.z * s, math.cos(half))


def body_axes(skeleton):
    """The tail hangs nearly straight down, so a sway about the vertical would only twist it in place. Side to side
    is a turn about the body's back-to-front line (taken from the pelvis to where the tail leaves the back), and
    the lift is a turn about the line across the hips."""
    ref = u.AnimPoseExtensions.get_reference_pose(skeleton)
    at = lambda b: u.AnimPoseExtensions.get_bone_pose(ref, b, u.AnimPoseSpaces.WORLD).translation
    back = at(TAIL[0]) - at("pelvis")
    back = u.Vector(back.x, back.y, 0.0)
    back = back * (1.0 / max(back.length(), 1e-6))
    across = UP.cross(back)
    return ref, back, across


def chain_frames(skeleton, bones):
    """Per bone: reference local transform, plus the sway and lift axes expressed in the bone's own frame."""
    ref, back, across = body_axes(skeleton)
    out = []
    for bone in bones:
        local = u.AnimPoseExtensions.get_bone_pose(ref, bone, u.AnimPoseSpaces.LOCAL)
        inv = u.AnimPoseExtensions.get_bone_pose(ref, bone, u.AnimPoseSpaces.WORLD).rotation.inversed()
        out.append((local, inv.rotate_vector(back), inv.rotate_vector(across)))
    return out


def write(seq, frames, bones, keys_n, cycles, tip_deg, lag, offset):
    controller = seq.get_editor_property("controller")
    n = len(bones)
    for k, (bone, (local, sway_axis, lift_axis)) in enumerate(zip(bones, frames)):
        share = 0.3 + 0.7 * (k + 1) / n
        pos, rot, scl = [], [], []
        for key in range(keys_n):
            phase = math.tau * cycles * key / float(keys_n - 1) + offset - k * lag
            yaw = tip_deg * share * math.sin(phase)
            lift = 0.35 * tip_deg * share * math.sin(2.0 * phase + 0.8)
            delta = axis_angle(sway_axis, yaw) * axis_angle(lift_axis, lift)
            rot.append((local.rotation * delta).normalized())
            pos.append(local.translation)
            scl.append(local.scale3d)
        controller.add_bone_curve(bone, False)
        if not controller.set_bone_track_keys(bone, pos, rot, scl, False):
            raise RuntimeError("set_bone_track_keys refused %s (%d keys)" % (bone, keys_n))


def main():
    who = os.environ.get("SS_TAIL_WHO", "Crest")
    clips = [p.split(".")[0] for folder in ("%s/%s" % (CREW, who), "%s/%s/Role" % (CREW, who))
             for p in LIB.list_assets(folder, recursive=False, include_folder=False)]
    clips = [p for p in clips if p.rsplit("/", 1)[1].startswith("A_")]
    report = {"done": 0, "failed": [], "moods": {}}
    frames_cache = {}
    for path in clips:
        seq = LIB.load_asset(path)
        if not isinstance(seq, u.AnimSequence):
            continue
        skel = seq.get_editor_property("skeleton")
        key = skel.get_path_name()
        if key not in frames_cache:
            frames_cache[key] = (chain_frames(skel, TAIL), chain_frames(skel, CORD))
        tail_f, cord_f = frames_cache[key]
        length = u.AnimationLibrary.get_sequence_length(seq)
        keys_n = u.AnimationLibrary.get_num_keys(seq) if hasattr(u.AnimationLibrary, "get_num_keys") else \
            u.AnimationLibrary.get_num_frames(seq) + 1
        m = mood(path.rsplit("/", 1)[1])
        period, tip = PACE[m]
        cycles = max(1, int(round(length / period)))
        try:
            controller = seq.get_editor_property("controller")
            controller.open_bracket("Tail sway", False)
            write(seq, tail_f, TAIL, keys_n, cycles, tip, math.tau / 6.0, 0.0)
            write(seq, cord_f, CORD, keys_n, cycles, tip * 0.6, math.tau / 7.0, math.pi / 2.0)
            controller.close_bracket(False)
            LIB.save_asset(path, only_if_is_dirty=False)
            report["done"] += 1
            report["moods"][m] = report["moods"].get(m, 0) + 1
        except Exception as e:  # keep going; name what failed
            report["failed"].append("%s: %s" % (path.rsplit("/", 1)[1], e))
    line(json.dumps(report))


main()
