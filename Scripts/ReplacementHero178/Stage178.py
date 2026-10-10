"""178 cm squirrel candidate, step 1: move the delivered packages into the ignored Licensed tree, then compare its
skeleton and bounds with the live replacement's. Nothing else is saved; DA_Phase1 is only read.

  copy <Delivery>/UnrealContent/Diagnostic -> Content/Diagnostic   (the packages reference that path)
  set SS_SQ_OUT=<folder for the JSON receipt>
  UnrealEditor-Cmd.exe <project> -unattended -NullRHI -stdout -FullStdOutLogOutput \
      (project = .agent/local/CharacterAssets/Squirrel178_Sandbox/Squirrel178Sandbox.uproject: same /Game paths as
       the game, so everything made here migrates into the game project by plain copy)
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/Stage178.py"

The delivery's own rule: move through Unreal, never Explorer, so the internal references follow. Licensed/* is
git-ignored, so the owner's art never shows up as untracked files in a shared checkout.
"""
import json
import math
import os
import statistics

import unreal as u

# The current delivery is the colour fix, Delivery_RedStreaks (see HeroSquirrel_20261008/CURRENT_HANDOFF.txt): same
# geometry, bones and weights as the first 178 cm delivery, but its packages carry their own names and a fresh skeleton.
PKG = os.environ.get("SS_SQ_PKG", "HeroSquirrel178_RedStreaks_20261008")
MESH = os.environ.get("SS_SQ_MESH", "SK_SquirrelHero178_RedStreaks")
SRC = "/Game/Diagnostic/" + PKG
DST = "/Game/SpaceSurvival/Licensed/HeroReplacement178"
OLD = "/Game/SpaceSurvival/Licensed/HeroReplacement/Final"
L = u.EditorAssetLibrary
P = u.AnimPoseExtensions
out = os.environ["SS_SQ_OUT"]

if L.does_directory_exist(SRC) and L.list_assets(SRC, recursive=True, include_folder=False):
    assert not L.list_assets(DST, recursive=True, include_folder=False), "destination occupied: " + DST
    assert L.rename_directory(SRC, DST), "rename failed"
    left = [L.load_asset(p) for p in L.list_assets(SRC, recursive=True, include_folder=False)]
    redirectors = [r for r in left if isinstance(r, u.ObjectRedirector)]
    if redirectors:
        u.AssetToolsHelpers.get_asset_tools().fixup_referencers(redirectors)
    L.delete_directory(SRC)      # only the folder that was moved; anything else under /Game/Diagnostic is not ours
moved = sorted(p.split(".")[0] for p in L.list_assets(DST, recursive=False, include_folder=False))


def ref(skeleton):
    pose = P.get_reference_pose(skeleton)
    return {str(n): (P.get_bone_pose(pose, n, u.AnimPoseSpaces.LOCAL), P.get_bone_pose(pose, n, u.AnimPoseSpaces.WORLD))
            for n in P.get_bone_names(pose)}


def angle(a, b):
    dot = abs(a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w)
    return math.degrees(2 * math.acos(min(1.0, dot)))


def vec(v):
    return [v.x, v.y, v.z]


new_mesh = L.load_asset(DST + "/" + MESH)
old_mesh = L.load_asset(OLD + "/SK_SquirrelHeroReplacement")
new, old = ref(new_mesh.skeleton), ref(old_mesh.skeleton)
common = [b for b in old if b in new]
ratios = [new[b][0].translation.length() / old[b][0].translation.length()
          for b in common if old[b][0].translation.length() > 0.5]
k = statistics.median(ratios)
rot_err = max(angle(old[b][0].rotation, new[b][0].rotation) for b in common)
# World positions should be k x the old ones plus one constant offset (the delivery recentred the root).
offs = [new[b][1].translation - old[b][1].translation * k for b in common]
med = u.Vector(statistics.median(o.x for o in offs), statistics.median(o.y for o in offs),
               statistics.median(o.z for o in offs))
resid = max((o - med).length() for o in offs)


def bounds(m):
    b = m.get_bounds()
    return {"origin": vec(b.origin), "extent": vec(b.box_extent)}


clips = {}
for p in sorted(L.list_assets(OLD, recursive=False, include_folder=False)):
    if not p.rsplit("/", 1)[1].startswith("A_"):
        continue
    a = L.load_asset(p)
    if isinstance(a, u.AnimSequence):
        frames = u.AnimationLibrary.get_num_frames(a)
        clips[a.get_name()] = {
            "length": a.sequence_length, "frames": frames, "fps": frames / a.sequence_length,
            "notifies": len(u.AnimationLibrary.get_animation_notify_events(a)),
            "curves": len(u.AnimationLibrary.get_animation_curve_names(a, u.RawCurveTrackTypes.RCT_FLOAT)),
            "root_motion": a.get_editor_property("enable_root_motion"),
            "skeleton_is_old": a.get_editor_property("skeleton") == old_mesh.skeleton}
# The sandbox is content-only, so DA_Phase1 (a C++ class) only loads in the game project; the delivery's
# saved_tuning_readonly.json carries the same Squirrel row for the sandbox.
da = L.load_asset("/Game/SpaceSurvival/Data/DA_Phase1") if L.does_asset_exist("/Game/SpaceSurvival/Data/DA_Phase1") else None
row = next(h for h in da.get_editor_property("heroes") if str(h.id) == "Squirrel") if da else None
receipt = {
    "moved": moved, "bones_old": len(old), "bones_new": len(new),
    "missing_in_new": sorted(set(old) - set(new)), "extra_in_new": sorted(set(new) - set(old)),
    "scale_k_median": k, "scale_k_min": min(ratios), "scale_k_max": max(ratios),
    "rest_rotation_max_deg": rot_err, "world_offset": vec(med), "world_residual_cm": resid,
    "root_rest_old": vec(old["root"][0].translation), "root_rest_new": vec(new["root"][0].translation),
    "pelvis_world_old": vec(old["pelvis"][1].translation), "pelvis_world_new": vec(new["pelvis"][1].translation),
    "bounds_old": bounds(old_mesh), "bounds_new": bounds(new_mesh),
    "materials_new": [m.material_interface.get_path_name() if m.material_interface else None for m in new_mesh.materials],
    "old_clips": clips, "squirrel_row": row.export_text() if row else None}
os.makedirs(out, exist_ok=True)
with open(os.path.join(out, "stage178.json"), "w") as f:
    json.dump(receipt, f, indent=2)
u.log_warning("STAGE178| k=%.6f rot=%.4f resid=%.4f moved=%d" % (k, rot_err, resid, len(moved)))
