"""Rebuild the squirrel hero's MoCap-derived clips from the purchased pack, from nothing.

    & 'C:\\Program Files\\EpicGames2\\UE_5.8\\Engine\\Binaries\\Win64\\UnrealEditor-Cmd.exe' `
      'C:\\Users\\j6sis\\SpaceSurvival\\SpaceSurvival.uproject' -unattended -stdout `
      -FullStdOutLogOutput -DisablePlugins=UAssetBrowser `
      '-ExecutePythonScript=C:\\Users\\j6sis\\SpaceSurvival\\Scripts\\AuthorHeroMocapRetarget.py'

Everything it writes lives under Content/SpaceSurvival/Licensed/, which is git-ignored, because every
asset here is derived from a purchased Fab pack. Nothing in the tracked tree is touched; the staging
copy it needs inside Content/ is deleted again before the script returns.

WHAT IT MAKES
  Licensed/Hero/         the clips the game actually references: A_SquirrelIdle, A_SquirrelFidgetA,
                         A_SquirrelFidgetB, A_SquirrelJog, A_SquirrelRun
  Licensed/MocapSource/  everything the game does NOT reference - SK_Mannequin, the mannequin
                         skeleton, the eight raw pack clips, the two IK Rigs, the IK Retargeter,
                         RetargetReceipt.json, and the retargeted clips kept only for comparison.
                         Config/DefaultGame.ini lists that folder under DirectoriesToNeverCook, so
                         raw pack files and unused derivatives stay out of the shipping package while
                         /Game/SpaceSurvival around them is always cooked.

It does NOT touch A_SquirrelWalk or A_SquirrelPilot. The authored walk stays; the MoCap walk is
imported under a Compare name so the two can be measured against each other and nothing else.

THE DECISIONS THAT MAKE THIS WORK, AND WHY
  1. The retarget pose aligns the UPPER BODY ONLY. The squirrel ships a T-pose (L_Hand at +38.2 cm X,
     1.4 cm below the shoulder) while the mannequin is in an A-pose, so the arms, clavicles, spine,
     neck and head must be aligned or every clip holds its arms out sideways. The LEGS are
     deliberately left at the squirrel's own reference stance. Aligning them too straightens its
     knees to the human's, and since the squirrel's leg plus foot reaches 38.29 cm from a hip that
     stands at 38.073 cm, a straightened leg puts the sole under the floor.
  2. Then the toe is snapped back to the ground, which removes the constant offset the alignment
     leaves behind.
  3. The legs get real IK goals and a limb solver, an IK CHAINS op to drive those goals off the
     source's own feet, and a FLOOR CONSTRAINT op after the solve. All three are needed and the
     first two used to be missing: without an IK Chains op the goals are never given a target, so
     the limb solvers in the rig do nothing and every foot is pure FK. That is what let a planted
     foot slide - the stand clips skated 10.8 cm per foot with the feet never leaving the deck.
  4. FK rotation mode ONE_TO_ONE on every chain whose bone counts match one for one (spine 3-3,
     arms 3-3, legs 4-4, clavicle and head 1-1). The neck is left on the length-normalised default
     because the mannequin has one neck bone and the squirrel has two.
  5. No tail chain at all. The mannequin has no tail, the owner deferred tail work, and leaving
     Tail_01..05 out of every chain is what makes that deferral exact: measured, their local
     transforms deviate from frame 0 by 0.000 in every clip this script produces.
  6. No finger chains. This rig has no finger bones.

WHY EVERY PER-CHAIN SETTING IS WRITTEN BACK BY INDEX AND THEN READ BACK
  An op's settings struct hands out COPIES of its chain array. Mutating what `for chain in chains`
  yields writes nothing, and `set_editor_property(field, chains)` then stores the unchanged array -
  silently, because the top-level scalars on the same struct do take. A previous version of this
  file did exactly that and logged both tunings as applied while the saved asset carried neither:
  every chain stayed on INTERPOLATED and the floor constraint was off on both legs. The clips that
  were judged, and the two gaits that were rejected for floor penetration, were produced that way.
  So configure_chains() assigns into the array by index AND reads the values back off the op, and a
  value that did not take is an error in the receipt rather than a step that claims it did.
"""
import json
import math
import os
import shutil
import traceback
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "User downloaded assets" / "SpaceSurvival" / "Content" / "MCO_Mocap_Basics"
CONTENT = ROOT / "Content"
STAGE_PKG = "/Game/MCO_Mocap_Basics"
STAGE_DIR = CONTENT / "MCO_Mocap_Basics"
SRC_PKG = "/Game/SpaceSurvival/Licensed/MocapSource"
SRC_DIR = CONTENT / "SpaceSurvival" / "Licensed" / "MocapSource"
HERO_PKG = "/Game/SpaceSurvival/Licensed/Hero"

# Taken from the pack, and nothing else: no materials, no textures, no physics asset, no root-motion
# variants, no Conversations/Scared/Walks folders, no Overview map. The mesh is needed because the
# retargeter reads the SOURCE proportions off a skeletal mesh, not off a skeleton.
PACK_FILES = {
    "SK_Mannequin": r"Character\Mesh\SK_Mannequin.uasset",
    "UE4_Mannequin_Skeleton": r"Character\Mesh\UE4_Mannequin_Skeleton.uasset",
    "MOB1_Stand_Relaxed_Idle_v2_IPC": r"Animation\Mobility_Pro\In_Place\MOB1_Stand_Relaxed_Idle_v2_IPC.uasset",
    "MOB1_Stand_Relaxed_Fgt_v1_IPC": r"Animation\Mobility_Pro\In_Place\MOB1_Stand_Relaxed_Fgt_v1_IPC.uasset",
    "MOB1_Stand_Relaxed_Fgt_v4_IPC": r"Animation\Mobility_Pro\In_Place\MOB1_Stand_Relaxed_Fgt_v4_IPC.uasset",
    "MOB1_Run_F_IPC": r"Animation\Mobility_Pro\In_Place\MOB1_Run_F_IPC.uasset",
    "MOB1_Jog_F_IPC": r"Animation\Mobility_Pro\In_Place\MOB1_Jog_F_IPC.uasset",
    "MOB1_Run_F_to_Stand_Relaxed_RU_IPC": r"Animation\Mobility_Pro\In_Place\MOB1_Run_F_to_Stand_Relaxed_RU_IPC.uasset",
    "MOB1_Crouch_Idle_V2_IPC": r"Animation\Mobility_Pro\In_Place\MOB1_Crouch_Idle_V2_IPC.uasset",
    "MOB1_Walk_F_IPC": r"Animation\Mobility_Pro\In_Place\MOB1_Walk_F_IPC.uasset",
}
CLIP_NAMES = {
    "MOB1_Stand_Relaxed_Idle_v2_IPC": "A_SquirrelIdle",
    "MOB1_Stand_Relaxed_Fgt_v1_IPC": "A_SquirrelFidgetA",
    "MOB1_Stand_Relaxed_Fgt_v4_IPC": "A_SquirrelFidgetB",
    "MOB1_Run_F_IPC": "A_SquirrelRun",
    "MOB1_Jog_F_IPC": "A_SquirrelJog",
    "MOB1_Run_F_to_Stand_Relaxed_RU_IPC": "A_SquirrelRunStop",
    "MOB1_Crouch_Idle_V2_IPC": "A_SquirrelCrouchIdle",
    "MOB1_Walk_F_IPC": "A_SquirrelWalkMocapCompare",
}
# The clips FSSHeroDefinition actually names. Everything else this script produces is kept for
# comparison only and is written into the never-cooked source folder instead of beside the hero, so
# an unreferenced derivative cannot quietly ride into a package.
SHIPPING = {"A_SquirrelIdle", "A_SquirrelFidgetA", "A_SquirrelFidgetB", "A_SquirrelJog", "A_SquirrelRun"}

# chain name -> ((source start, source end), (target start, target end))
CHAINS = {
    "Spine": (("spine_01", "spine_03"), ("Waist", "Spine02")),
    "Neck": (("neck_01", "neck_01"), ("NeckTwist01", "NeckTwist02")),
    "Head": (("head", "head"), ("Head", "Head")),
    "LeftClavicle": (("clavicle_l", "clavicle_l"), ("L_Clavicle", "L_Clavicle")),
    "RightClavicle": (("clavicle_r", "clavicle_r"), ("R_Clavicle", "R_Clavicle")),
    "LeftArm": (("upperarm_l", "hand_l"), ("L_Upperarm", "L_Hand")),
    "RightArm": (("upperarm_r", "hand_r"), ("R_Upperarm", "R_Hand")),
    "LeftLeg": (("thigh_l", "ball_l"), ("L_Thigh", "L_ToeBase")),
    "RightLeg": (("thigh_r", "ball_r"), ("R_Thigh", "R_ToeBase")),
}
ONE_TO_ONE = {"Spine", "Head", "LeftClavicle", "RightClavicle", "LeftArm", "RightArm", "LeftLeg", "RightLeg"}
LEGS = ("LeftLeg", "RightLeg")
UPPER_BODY_BONES = [
    "Waist", "Spine01", "Spine02", "NeckTwist01", "NeckTwist02", "Head",
    "L_Clavicle", "L_Upperarm", "L_Forearm", "L_Hand",
    "R_Clavicle", "R_Upperarm", "R_Forearm", "R_Hand",
]
LEG_GOALS = {
    "LeftFootGoal": ("L_ToeBase", "LeftLeg", "L_Thigh"),
    "RightFootGoal": ("R_ToeBase", "RightLeg", "R_Thigh"),
}
LIMB_SOLVER = "/Script/IKRig.IKRigLimbSolver"
IK_CHAINS_OP = "/Script/IKRig.IKRetargetIKChainsOp"
FLOOR_OP = "/Script/IKRig.IKRetargetFloorConstraintOp"
SPEED_PLANT_OP = "/Script/IKRig.IKRetargetSpeedPlantingOp"
# chain -> (the source bone whose speed is measured, the curve that speed is written to)
SPEED_CURVES = {"LeftLeg": ("ball_l", "foot_l_speed"), "RightLeg": ("ball_r", "foot_r_speed")}
# Source cm/s, i.e. measured on the mannequin. Below this the goal is pinned where it is. It cleanly
# separates the two cases without a per-clip switch: a standing foot moves a few cm/s in the capture
# and gets pinned, while an in-place gait's stance foot is travelling backwards at 130-260 cm/s -
# which it must keep doing, because that backward slide against an actor moving forwards is the
# stride. See the module docstring for why the stand clips need this at all.
SPEED_THRESHOLD = 15.0

receipt = {"steps": [], "errors": [], "clips": [], "chain_settings": {}}


def step(message):
    receipt["steps"].append(message)
    unreal.log("HeroMocap: " + message)


def fail(message):
    receipt["errors"].append(message)
    unreal.log_error("HeroMocap: " + message)


def same(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) \
            and not isinstance(b, bool):
        return abs(float(a) - float(b)) < 1e-6
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) == bool(b)
    return str(a) == str(b)


def configure_chains(op, field, wanted, label, struct_type=None):
    """Set per-chain settings so they actually stick, then prove it by reading them back.

    See the module docstring: iterating the array yields copies, so the assignment has to go back
    into the array by index before the array is stored and the op is given the struct. struct_type
    is for ops that start with an empty chain list and expect entries to be appended."""
    settings = op.get_settings()
    chains = settings.get_editor_property(field)
    present = set()
    for index in range(len(chains)):
        chain = chains[index]
        name = str(chain.get_editor_property("target_chain_name"))
        present.add(name)
        values = wanted.get(name)
        if not values:
            continue
        for key, value in values.items():
            chain.set_editor_property(key, value)
        chains[index] = chain
    if struct_type is not None:
        for name, values in wanted.items():
            if name in present:
                continue
            chain = struct_type()
            chain.set_editor_property("target_chain_name", name)
            for key, value in values.items():
                chain.set_editor_property(key, value)
            chains.append(chain)
    settings.set_editor_property(field, chains)
    op.set_settings(settings)

    readback = {}
    for chain in op.get_settings().get_editor_property(field):
        name = str(chain.get_editor_property("target_chain_name"))
        if name not in wanted:
            continue
        readback[name] = {key: chain.get_editor_property(key) for key in wanted[name]}
    for name, values in wanted.items():
        got = readback.get(name)
        if got is None:
            fail("%s: chain '%s' is not in %s at all" % (label, name, field))
            continue
        for key, value in values.items():
            if not same(got[key], value):
                fail("%s: %s.%s did not take - wanted %r, the asset holds %r" % (label, name, key, value, got[key]))
    receipt["chain_settings"].setdefault(label, {})[field] = {
        name: {key: str(value) for key, value in values.items()} for name, values in readback.items()
    }
    step("%s: %s verified on %d chains" % (label, field, len(readback)))


def stage_pack_into_content():
    """The pack's animations import /Game/MCO_Mocap_Basics/..., so they must land there to load."""
    for relative in PACK_FILES.values():
        source = PACK / relative
        if not source.is_file():
            raise RuntimeError(
                "the MoCap Online pack is not where this script expects it: %s is missing. "
                "It is a purchased Fab download and is not in the repository." % source)
        destination = STAGE_DIR / relative
        os.makedirs(destination.parent, exist_ok=True)
        shutil.copy2(source, destination)
    unreal.AssetRegistryHelpers.get_asset_registry().scan_paths_synchronous([STAGE_PKG], force_rescan=True)
    step("staged %d pack files into %s" % (len(PACK_FILES), STAGE_PKG))


def clear_previous_run():
    """Delete last run's rigs BEFORE the meshes they point at are renamed out from under them."""
    library = unreal.EditorAssetLibrary
    for name in ("RTG_MannequinToSquirrel", "IK_UE4Mannequin", "IK_SquirrelHero"):
        package = "%s/%s" % (SRC_PKG, name)
        if library.does_asset_exist(package):
            library.delete_asset(package)
    step("removed the previous run's rigs and retargeter")


def move_pack_into_licensed():
    """Renaming fixes the cross-references; a plain file copy into the licensed tree would not."""
    library = unreal.EditorAssetLibrary
    for name, relative in PACK_FILES.items():
        folder = os.path.dirname(relative).replace("\\", "/")
        library.load_asset("%s/%s/%s" % (STAGE_PKG, folder, name))
    for name, relative in PACK_FILES.items():
        folder = os.path.dirname(relative).replace("\\", "/")
        source = "%s/%s/%s" % (STAGE_PKG, folder, name)
        destination = "%s/%s" % (SRC_PKG, name)
        if library.does_asset_exist(destination):
            library.delete_asset(destination)
        if not library.rename_asset(source, destination):
            fail("rename failed: %s -> %s" % (source, destination))
    library.save_directory(SRC_PKG, only_if_is_dirty=False, recursive=True)
    if library.does_directory_exist(STAGE_PKG):
        library.delete_directory(STAGE_PKG)
    if STAGE_DIR.is_dir():
        shutil.rmtree(STAGE_DIR, ignore_errors=True)
    step("moved %d assets into %s and removed the staging folder" % (len(PACK_FILES), SRC_PKG))


def author_speed_curves():
    """Write each source clip's own foot speed onto it, so the retarget can pin a planted foot.

    The retargeter's speed-planting op needs a curve per foot and the pack does not ship one. The
    curve is not a guess: it is the frame-to-frame horizontal travel of that foot in the capture,
    divided by the frame time, in the source's own centimetres. That is the quantity the op's
    threshold is expressed in, so what gets pinned is exactly what the actor held still."""
    pose_api = unreal.AnimPoseExtensions
    options = unreal.AnimPoseEvaluationOptions()
    written = 0
    for source_name in CLIP_NAMES:
        anim = unreal.EditorAssetLibrary.load_asset("%s/%s" % (SRC_PKG, source_name))
        if anim is None:
            fail("speed curves: %s would not load" % source_name)
            continue
        frames = unreal.AnimationLibrary.get_num_frames(anim)
        seconds = anim.get_editor_property("sequence_length")
        if not frames or not seconds:
            fail("speed curves: %s has no frames" % source_name)
            continue
        dt = seconds / float(frames)
        tracks = {}
        for frame in range(frames + 1):
            pose = pose_api.get_anim_pose_at_frame(anim, frame, options)
            for bone, _ in SPEED_CURVES.values():
                location = pose_api.get_bone_pose(pose, bone, unreal.AnimPoseSpaces.WORLD).translation
                tracks.setdefault(bone, []).append((location.x, location.y, location.z))
        for bone, curve_name in SPEED_CURVES.values():
            points = tracks[bone]
            speeds = []
            for frame in range(frames + 1):
                before = points[max(0, frame - 1)]
                after = points[min(frames, frame + 1)]
                span = dt * (min(frames, frame + 1) - max(0, frame - 1))
                moved = math.dist((before[0], before[1]), (after[0], after[1]))
                speeds.append(moved / span if span > 0 else 0.0)
            if unreal.AnimationLibrary.does_curve_exist(anim, curve_name, unreal.RawCurveTrackTypes.RCT_FLOAT):
                unreal.AnimationLibrary.remove_curve(anim, curve_name)
            unreal.AnimationLibrary.add_curve(anim, curve_name, unreal.RawCurveTrackTypes.RCT_FLOAT, False)
            unreal.AnimationLibrary.add_float_curve_keys(
                anim, curve_name, [frame * dt for frame in range(frames + 1)], speeds)
            if not unreal.AnimationLibrary.does_curve_exist(anim, curve_name, unreal.RawCurveTrackTypes.RCT_FLOAT):
                fail("speed curves: %s did not take %s" % (source_name, curve_name))
            written += 1
        unreal.EditorAssetLibrary.save_loaded_asset(anim, only_if_is_dirty=False)
    step("wrote %d foot-speed curves across %d source clips" % (written, len(CLIP_NAMES)))


def build_rig(asset_name, mesh_package, pelvis_bone, root_bone, side, goals=None):
    library = unreal.EditorAssetLibrary
    package = "%s/%s" % (SRC_PKG, asset_name)
    if library.does_asset_exist(package):
        library.delete_asset(package)
    rig = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name, SRC_PKG, unreal.IKRigDefinition, unreal.IKRigDefinitionFactory()
    )
    controller = unreal.IKRigController.get_controller(rig)

    mesh = library.load_asset(mesh_package)
    if not controller.set_skeletal_mesh(mesh):
        fail("%s rejected the mesh %s" % (asset_name, mesh_package))
    controller.set_retarget_root(pelvis_bone)
    controller.set_root_motion_bone(root_bone)
    for chain_name, pair in CHAINS.items():
        start, end = pair[side]
        controller.add_retarget_chain(chain_name, start, end, "None")

    for goal_name, (bone, chain, limb_start) in (goals or {}).items():
        made = str(controller.add_new_goal(goal_name, bone))
        solver = controller.add_solver(LIMB_SOLVER)
        controller.set_start_bone(limb_start, solver)
        controller.connect_goal_to_solver(made, solver)
        controller.set_retarget_chain_goal(chain, made)
        step("%s: goal %s on %s, limb solver %d from %s, driving chain %s"
             % (asset_name, made, bone, solver, limb_start, chain))

    step("%s: pelvis=%s root=%s chains=%s"
         % (asset_name, controller.get_retarget_root(), controller.get_root_motion_bone(),
            [str(c.chain_name) for c in controller.get_retarget_chains()]))
    library.save_loaded_asset(rig, only_if_is_dirty=False)
    return rig


def build_retargeter(source_rig, target_rig, source_mesh, target_mesh):
    library = unreal.EditorAssetLibrary
    package = "%s/RTG_MannequinToSquirrel" % SRC_PKG
    source = unreal.RetargetSourceOrTarget.SOURCE
    target = unreal.RetargetSourceOrTarget.TARGET
    if library.does_asset_exist(package):
        library.delete_asset(package)
    retargeter = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "RTG_MannequinToSquirrel", SRC_PKG, unreal.IKRetargeter, unreal.IKRetargetFactory()
    )
    controller = unreal.IKRetargeterController.get_controller(retargeter)

    controller.set_ik_rig(source, source_rig)
    controller.set_ik_rig(target, target_rig)
    controller.set_preview_mesh(source, source_mesh)
    controller.set_preview_mesh(target, target_mesh)
    controller.add_default_ops()
    # The default stack has no IK Chains op, so the leg goals the target rig carries are never given
    # a target and the limb solvers idle. This is the op that drives them off the source's own feet.
    if controller.add_retarget_op(IK_CHAINS_OP) < 0:
        fail("the IK chains op could not be added")
    if controller.add_retarget_op(FLOOR_OP) < 0:
        fail("the floor constraint op could not be added")
    if controller.add_retarget_op(SPEED_PLANT_OP) < 0:
        fail("the speed planting op could not be added")
    controller.assign_ik_rig_to_all_ops(source, source_rig)
    controller.assign_ik_rig_to_all_ops(target, target_rig)
    controller.auto_map_chains(unreal.AutoMapChainType.EXACT, True)
    receipt["chain_mapping"] = {name: str(controller.get_source_chain(name)) for name in CHAINS}

    pose = controller.create_retarget_pose("AlignedToMannequin", target)
    controller.set_current_retarget_pose(pose, target)
    controller.auto_align_bones(UPPER_BODY_BONES, unreal.RetargetAutoAlignMethod.CHAIN_TO_CHAIN, target)
    controller.snap_bone_to_ground("L_ToeBase", target)
    step("retarget pose '%s': upper body aligned chain-to-chain, legs left at the squirrel's own "
         "stance, toe snapped back to the ground" % pose)

    receipt["ops"] = [[i, str(controller.get_op_name(i))] for i in range(controller.get_num_retarget_ops())]
    step("op stack: " + json.dumps(receipt["ops"]))

    for index in range(controller.get_num_retarget_ops()):
        op = controller.get_op_controller(index)
        label = "op %d %s" % (index, controller.get_op_name(index))
        if isinstance(op, unreal.IKRetargetFKChainsController):
            configure_chains(
                op, "chains_to_retarget",
                {name: {"rotation_mode": unreal.FKChainRotationMode.ONE_TO_ONE} for name in ONE_TO_ONE},
                label)
        elif isinstance(op, unreal.IKRetargetIKChainsController):
            # This op only lists the chains that carry a goal in the target rig, which here is the
            # two legs and nothing else, so asking it about the arms or the spine is asking about
            # chains it does not have rather than finding a setting that failed.
            configure_chains(op, "chains_to_retarget", {name: {"enable_ik": True} for name in LEGS}, label)
        elif isinstance(op, unreal.IKRetargetRunIKRigController):
            configure_chains(op, "chains", {name: {"enable_ik": name in LEGS} for name in LEGS}, label)
        elif isinstance(op, unreal.IKRetargetSpeedPlantingController):
            settings = op.get_settings()
            settings.set_editor_property("speed_threshold", SPEED_THRESHOLD)
            op.set_settings(settings)
            configure_chains(
                op, "chains_to_speed_plant",
                {chain: {"speed_curve_name": curve, "alpha": 1.0}
                 for chain, (_, curve) in SPEED_CURVES.items()},
                label, unreal.RetargetSpeedPlantingSettings)
        elif isinstance(op, unreal.IKRetargetFloorConstraintController):
            settings = op.get_settings()
            settings.set_editor_property("alpha", 1.0)
            settings.set_editor_property("height_falloff_offset", 3.0)
            settings.set_editor_property("height_falloff_distance", 12.0)
            op.set_settings(settings)
            configure_chains(
                op, "chains_to_affect",
                {name: {"enable_floor_constraint": True, "alpha": 1.0,
                        # The goal sits on the toe bone, which stands 2.2 cm above the floor in the
                        # reference pose. Without this the constraint would pull the BONE to Z=0 and
                        # bury the sole by that much.
                        "maintain_height_offset": 1.0, "use_toes": True} for name in LEGS},
                label)

    library.save_loaded_asset(retargeter, only_if_is_dirty=False)
    return retargeter


def retarget_clips(retargeter, source_mesh, target_mesh):
    library = unreal.EditorAssetLibrary
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    for source_name, clip_name in CLIP_NAMES.items():
        folder = HERO_PKG if clip_name in SHIPPING else SRC_PKG
        destination = "%s/%s" % (folder, clip_name)
        for stale in ("%s/%s" % (HERO_PKG, clip_name), "%s/%s" % (SRC_PKG, clip_name)):
            if library.does_asset_exist(stale):
                library.delete_asset(stale)
        asset = registry.get_asset_by_object_path("%s/%s.%s" % (SRC_PKG, source_name, source_name))
        inputs = unreal.IKRetargetBatchOperationInputs()
        inputs.set_editor_property("assets_to_retarget", [asset])
        inputs.set_editor_property("source_mesh", source_mesh)
        inputs.set_editor_property("target_mesh", target_mesh)
        inputs.set_editor_property("ik_retarget_asset", retargeter)
        inputs.set_editor_property("search", source_name)
        inputs.set_editor_property("replace", clip_name)
        inputs.set_editor_property("target_path", folder)
        inputs.set_editor_property("use_source_path", False)
        inputs.set_editor_property("include_referenced_assets", False)
        inputs.set_editor_property("overwrite_existing_files", True)
        made = unreal.IKRetargetBatchOperation.run_batch_retarget(inputs)
        names = [str(a.get_editor_property("package_name")) for a in made]
        receipt["clips"].append({"source": source_name, "made": names, "shipping": clip_name in SHIPPING})
        if destination not in names:
            fail("%s did not produce %s (got %s)" % (source_name, destination, names))
    library.save_directory(HERO_PKG, only_if_is_dirty=False, recursive=False)
    library.save_directory(SRC_PKG, only_if_is_dirty=False, recursive=False)
    step("retargeted %d clips: %d beside the hero, %d into the never-cooked source folder"
         % (len(CLIP_NAMES), len(SHIPPING), len(CLIP_NAMES) - len(SHIPPING)))


def main():
    library = unreal.EditorAssetLibrary
    clear_previous_run()
    stage_pack_into_content()
    move_pack_into_licensed()
    author_speed_curves()
    source_mesh = library.load_asset("%s/SK_Mannequin" % SRC_PKG)
    target_mesh = library.load_asset("%s/SK_SquirrelHero" % HERO_PKG)
    if target_mesh is None:
        raise RuntimeError("the squirrel hero is not imported; nothing to retarget onto")
    source_rig = build_rig("IK_UE4Mannequin", "%s/SK_Mannequin" % SRC_PKG, "pelvis", "root", 0)
    target_rig = build_rig("IK_SquirrelHero", "%s/SK_SquirrelHero" % HERO_PKG, "Hip", "Root", 1, LEG_GOALS)
    retargeter = build_retargeter(source_rig, target_rig, source_mesh, target_mesh)
    retarget_clips(retargeter, source_mesh, target_mesh)


try:
    main()
except Exception:  # noqa: BLE001
    receipt["errors"].append(traceback.format_exc())
    unreal.log_error("HeroMocap FAILED\n" + traceback.format_exc())
finally:
    try:
        os.makedirs(SRC_DIR, exist_ok=True)
        with open(SRC_DIR / "RetargetReceipt.json", "w", encoding="utf-8") as handle:
            json.dump(receipt, handle, indent=1)
    except Exception:  # noqa: BLE001
        pass
    unreal.log("HeroMocap DONE errors=%d" % len(receipt["errors"]))
