"""178 cm squirrel candidate, step 2: rebase the live squirrel's eight clips onto the 178 cm skeleton, prove them, and
measure what the hero row needs (gait speeds, seat, height in motion). Run after Stage178.py, same project and flags.

  set SS_SQ_OUT=<folder for the receipt>      optional SS_SQ_REDO=1 replaces clips already derived

Why rebasing and not the IK retargeter: Stage178 measured the 178 cm skeleton as EXACTLY the live one scaled by
K = 1.991773 (all 69 bones, rest rotations within 0.001 deg, world residual 0.0001 cm) plus one constant shift - the
delivery recentred the root, so the pelvis now sits over the origin instead of 21.3 cm forward. For that relation the
exact conversion is per bone, per key: rotation and scale unchanged, translation = rest_new + K * (key - rest_old).
A retargeter would only approximate it. The live clips carry translation keys on every bone (Compose.py writes all
three channels), so assigning them to the new skeleton unchanged would shrink the body back to the old bone lengths.

The proof: every bone, every third frame, component space - the new clip must equal K x the old clip plus that same
shift. Anything else is a conversion fault, not a judgement call.
"""
import json
import os
import statistics

import unreal as u

OLD = "/Game/SpaceSurvival/Licensed/HeroReplacement/Final"
NEW = "/Game/SpaceSurvival/Licensed/HeroReplacement178"
NAMES = ["Idle", "Walk", "Jog", "Run", "Pilot", "JumpStart", "JumpAir", "JumpLand"]
FPS = 30
# The live Squirrel row (DA_Phase1, read by the delivery's saved_tuning_readonly.json): fitted to 135 cm.
OLD_FIT, OLD_YAW = 135.0, -90.0
OLD_MOUNT = u.Vector(-12.5, 0.0, 22.468996532693353)
OLD_SPEEDS = {"Walk": 77.36325073242188, "Jog": 204.88134765625, "Run": 377.5804443359375}
NEW_FIT = 178.0
L = u.EditorAssetLibrary
P = u.AnimPoseExtensions
LOCAL, WORLD = u.AnimPoseSpaces.LOCAL, u.AnimPoseSpaces.WORLD
out = os.environ["SS_SQ_OUT"]
redo = os.environ.get("SS_SQ_REDO") == "1"

mesh = L.load_asset(NEW + "/" + os.environ.get("SS_SQ_MESH", "SK_SquirrelHero178_RedStreaks"))
old_mesh = L.load_asset(OLD + "/SK_SquirrelHeroReplacement")
ref_new, ref_old = P.get_reference_pose(mesh.skeleton), P.get_reference_pose(old_mesh.skeleton)
bones = [str(b) for b in P.get_bone_names(ref_old)]
rest_new = {b: P.get_bone_pose(ref_new, b, LOCAL).translation for b in bones}
rest_old = {b: P.get_bone_pose(ref_old, b, LOCAL).translation for b in bones}
K = statistics.median(rest_new[b].length() / rest_old[b].length() for b in bones
                      if b != "root" and rest_old[b].length() > 0.5)
shift = statistics.median(((P.get_bone_pose(ref_new, b, WORLD).translation
                            - P.get_bone_pose(ref_old, b, WORLD).translation * K).y) for b in bones)
SHIFT = u.Vector(0, shift, 0)

made = []
for name in NAMES:
    src = L.load_asset("%s/A_%s" % (OLD, name))
    dst = "%s/A_%s" % (NEW, name)
    if L.does_asset_exist(dst):
        if not redo:
            assert L.load_asset(dst).get_editor_property("skeleton") == mesh.skeleton, dst
            continue
        L.delete_asset(dst)
    frames = u.AnimationLibrary.get_num_frames(src)
    factory = u.AnimSequenceFactory()
    factory.set_editor_property("target_skeleton", mesh.skeleton)
    factory.set_editor_property("preview_skeletal_mesh", mesh)
    seq = u.AssetToolsHelpers.get_asset_tools().create_asset("A_" + name, NEW, u.AnimSequence, factory)
    c = seq.get_editor_property("controller")
    c.open_bracket("Rebase onto the 178 cm skeleton", False)
    c.set_frame_rate(u.FrameRate(FPS, 1), False)
    c.set_number_of_frames(u.FrameNumber(frames), False)
    for bone in bones:
        keys = [u.AnimationLibrary.get_bone_pose_for_time(src, bone, min(i / FPS, src.sequence_length), False)
                for i in range(frames + 1)]
        c.add_bone_curve(bone, False)
        assert c.set_bone_track_keys(bone, [rest_new[bone] + (k.translation - rest_old[bone]) * K for k in keys],
                                     [k.rotation for k in keys], [k.scale3d for k in keys], False), bone
    c.close_bracket(False)
    for prop in ("enable_root_motion", "force_root_lock", "root_motion_root_lock", "interpolation", "rate_scale"):
        seq.set_editor_property(prop, src.get_editor_property(prop))
    assert L.save_loaded_asset(seq, False), dst
    made.append(name)

opt = u.AnimPoseEvaluationOptions()
s_old = OLD_FIT / (old_mesh.get_bounds().box_extent.z * 2)
s_new = NEW_FIT / (mesh.get_bounds().box_extent.z * 2)
body = [b for b in bones if not b.startswith("tail_")]
ref_top_new = max(P.get_bone_pose(ref_new, b, WORLD).translation.z for b in body)
report = {"K": K, "shift_y_cm": shift, "made": made, "rendered_scale_old": s_old, "rendered_scale_new": s_new,
          "bones": bones, "clips": {}}


def gait_speed(clip, scale, unit):
    """MeasureFit.py's method: planted ball travel at 60 Hz, contact = within 2 cm of the clip's lowest point."""
    dt = 1 / 60.0
    data = []
    for i in range(round(clip.sequence_length * 60) + 1):
        pose = P.get_anim_pose_at_time(clip, min(i * dt, clip.sequence_length), opt)
        data.append([P.get_bone_pose(pose, b, WORLD).translation for b in ("ball_l", "ball_r")])
    speeds = []
    for side in range(2):
        zmin = min(v[side].z for v in data)
        for prev, curr in zip(data, data[1:]):
            if prev[side].z < zmin + 2 * unit and curr[side].z < zmin + 2 * unit:
                dy = (curr[side].y - prev[side].y) / dt
                if dy < -5 * unit:
                    speeds.append(abs(dy) * scale)
    return statistics.median(speeds) if speeds else None


for name in NAMES:
    a_old, a_new = L.load_asset("%s/A_%s" % (OLD, name)), L.load_asset("%s/A_%s" % (NEW, name))
    frames = u.AnimationLibrary.get_num_frames(a_new)
    worst, top = 0.0, -1e9
    for f in range(0, frames + 1, 3):
        po, pn = P.get_anim_pose_at_frame(a_old, f, opt), P.get_anim_pose_at_frame(a_new, f, opt)
        for b in bones:
            n = P.get_bone_pose(pn, b, WORLD).translation
            worst = max(worst, (n - (P.get_bone_pose(po, b, WORLD).translation * K + SHIFT)).length())
            if b in body:
                top = max(top, n.z)
    entry = {"frames": frames, "length": a_new.sequence_length, "max_error_cm": worst,
             "crown_rise_cm": (top - ref_top_new) * s_new,
             "skeleton_ok": a_new.get_editor_property("skeleton") == mesh.skeleton}
    if name in OLD_SPEEDS:
        entry["speed_old_remeasured"] = gait_speed(a_old, s_old, 1.0)
        entry["speed_old_saved"] = OLD_SPEEDS[name]
        entry["speed_new"] = gait_speed(a_new, s_new, K)
    report["clips"][name] = entry

# Seat: keep the seated pelvis where the live squirrel's sits (MeasureFit.py's anchor), so only the body around it grows.
pold = P.get_bone_pose(P.get_anim_pose_at_time(L.load_asset(OLD + "/A_Pilot"), 0, opt), "pelvis", WORLD).translation * s_old
pnew = P.get_bone_pose(P.get_anim_pose_at_time(L.load_asset(NEW + "/A_Pilot"), 0, opt), "pelvis", WORLD).translation * s_new
mount = u.MathLibrary.quat_rotate_vector(u.Rotator(yaw=OLD_YAW).quaternion(), pold - pnew) + OLD_MOUNT
report["pilot_mount_offset"] = [mount.x, mount.y, mount.z]
report["height_in_motion_cm"] = NEW_FIT + max(e["crown_rise_cm"] for e in report["clips"].values())
with open(os.path.join(out, "derive178.json"), "w") as f:
    json.dump(report, f, indent=2)
u.log_warning("DERIVE178| made=%s worst=%.5f" % (made, max(e["max_error_cm"] for e in report["clips"].values())))
