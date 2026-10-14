"""Put a tentacle character's own lower body under every humanoid clip retargeted onto her (Kraken).

  UnrealEditor-Cmd.exe <project> -unattended -NullRHI -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/Scripts/AuthorTripoCrewTentacleBlend.py"

Kraken has a humanoid upper body (Waist, Spine, Neck, Head, arms, fingers) on a body of tentacles. A clip
retargeted from a person carries a person's hips and legs; this keeps the upper body from that clip and takes
everything below the waist - root, Hip, Pelvis, the leg tentacles, and the tentacles hanging from her arms - from
her own procedural tentacle clips (TripoCrew/<Name>/Clips, made by TripoCrewBlender/tentacles/): crawl under the
walks and carries, the matching turn under the turns, idle under everything else. The tentacle loop is fitted a
whole number of times into each clip, so every loop still closes.

Run after AuthorTripoCrew.py / AuthorTripoCrewRoles.py, and again after either re-retargets her: it always
rebuilds the lower body from the tentacle clips, so a second run replaces rather than stacks. SS_TENT_WHO=Kraken.
"""
import json
import os

import unreal as u

CREW = "/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew"
LIB = u.EditorAssetLibrary
AL = u.AnimationLibrary
# the humanoid half, kept from the retargeted clip; everything else comes from the tentacle clip
UPPER_PREFIX = ("Waist", "Spine", "Neck", "Head", "FacialBone", "L_Eye", "R_Eye", "L_Clavicle", "R_Clavicle",
                "L_Upperarm", "R_Upperarm", "L_Forearm", "R_Forearm", "L_Elbow", "R_Elbow", "L_Hand", "R_Hand",
                "L_Thumb", "R_Thumb", "L_Index", "R_Index", "L_Mid", "R_Mid", "L_Ring", "R_Ring", "L_Pinky", "R_Pinky",
                # the longer arm tentacle on each side is retargeted from the human arm (AuthorTripoCrew.py
                # EXTRA_CHAINS); the shorter one, LArmTent1/RArmTent1, keeps its own wiggle from the tentacle clip
                "LArmTent0", "RArmTent0")
GAIT = ("Walk", "Carry", "Run", "Haul")


def line(s):
    u.log_warning("TENTBLEND| " + str(s))


def source_for(name):
    # base clips say TurnL/TurnR; Space_Crew says Worker_Turn_Left - both must reach her turns, not her idle
    if any(k in name for k in ("TurnL", "Turn_L", "Turn_Left")):
        return "TurnL"
    if any(k in name for k in ("TurnR", "Turn_R", "Turn_Right")):
        return "TurnR"
    return "Crawl" if any(w in name for w in GAIT) else "Idle"


def read_tracks(seq, bones):
    frames = AL.get_num_keys(seq) if hasattr(AL, "get_num_keys") else AL.get_num_frames(seq) + 1
    return frames, {b: [AL.get_bone_pose_for_frame(seq, b, f, False) for f in range(frames)] for b in bones}


def nlerp(a, b, t):
    if a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w < 0:
        b = u.Quat(-b.x, -b.y, -b.z, -b.w)
    return u.Quat(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t, a.z + (b.z - a.z) * t, a.w + (b.w - a.w) * t).normalized()


def main():
    who = os.environ.get("SS_TENT_WHO", "Kraken")
    sources = {}
    for key in ("Crawl", "Idle", "TurnL", "TurnR"):
        seq = LIB.load_asset("%s/%s/Clips/A_%s_Tent%s" % (CREW, who, who, key))
        assert isinstance(seq, u.AnimSequence), "missing tentacle clip " + key
        tracks = [str(n) for n in AL.get_animation_track_names(seq)]
        # track names come back in whatever case the name table first saw ("hip", "tent00_0"); bone names are
        # case-insensitive in Unreal, so compare that way
        lower = [b for b in tracks if not b.lower().startswith(tuple(p.lower() for p in UPPER_PREFIX))]
        assert 0 < len(lower) < len(tracks), "upper/lower split failed: %d of %d tracks" % (len(lower), len(tracks))
        n, poses = read_tracks(seq, lower)
        sources[key] = (AL.get_sequence_length(seq), n, poses)
    clips = [p.split(".")[0] for folder in ("%s/%s" % (CREW, who), "%s/%s/Role" % (CREW, who))
             for p in LIB.list_assets(folder, recursive=False, include_folder=False)]
    clips = [p for p in clips if p.rsplit("/", 1)[1].startswith("A_")]
    report = {"done": 0, "by_source": {}, "failed": []}
    for path in clips:
        seq = LIB.load_asset(path)
        if not isinstance(seq, u.AnimSequence):
            continue
        name = path.rsplit("/", 1)[1]
        key = source_for(name)
        tlen, tn, poses = sources[key]
        length = AL.get_sequence_length(seq)
        keys = AL.get_num_keys(seq) if hasattr(AL, "get_num_keys") else AL.get_num_frames(seq) + 1
        cycles = max(1, int(round(length / tlen)))
        controller = seq.get_editor_property("controller")
        try:
            controller.open_bracket("Tentacle lower body", False)
            for bone, src in poses.items():
                pos, rot, scl = [], [], []
                for k in range(keys):
                    x = ((k / float(keys - 1)) * cycles % 1.0) * (tn - 1)
                    if k == keys - 1:
                        x = float(tn - 1)               # land exactly on the source's own last key: the loop closes
                    i = min(int(x), tn - 2); t = x - i
                    a, b = src[i], src[i + 1]
                    pos.append(a.translation + (b.translation - a.translation) * t)
                    rot.append(nlerp(a.rotation, b.rotation, t))
                    scl.append(a.scale3d + (b.scale3d - a.scale3d) * t)
                controller.add_bone_curve(bone, False)
                if not controller.set_bone_track_keys(bone, pos, rot, scl, False):
                    raise RuntimeError("set_bone_track_keys refused %s" % bone)
            controller.close_bracket(False)
            LIB.save_asset(path, only_if_is_dirty=False)
            report["done"] += 1
            report["by_source"][key] = report["by_source"].get(key, 0) + 1
        except Exception as e:
            report["failed"].append("%s: %s" % (name, e))
    report["lower_bones"] = len(next(iter(sources.values()))[2])
    line(json.dumps(report))


main()
