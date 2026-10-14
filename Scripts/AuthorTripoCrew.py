"""Give the Tripo-rigged station NPCs their own IK rig, retargeter and clips.

  UnrealEditor-Cmd.exe <project> -unattended -RenderOffscreen -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/Scripts/AuthorTripoCrew.py"

Batch retargeting needs a real RHI, so this never runs under -NullRHI. NwiroIntegrationKit is disabled
because a hidden editor that loads it takes TCP 5353 from the owner's editor.

Nothing under /Game/TripoModels is written. Every output lands in OUT/<Name>/, one folder per
character, and a rerun deletes and rebuilds only those folders.

Tripo's auto-rig names its bones exactly like the UE4 mannequin (root, pelvis, spine_01..03, thigh_l,
index_01_l...), so one chain table serves both the source rig and thirteen of the targets. The two
octopus-bodied characters carry a second humanoid naming (Hip, Pelvis, Spine01, L_Thigh, L_Mid1...),
and their legs are tentacles: the leg chains still drive them, which is what makes the tentacles sway
with the walk instead of hanging rigid.

Targets are the repaired meshes ImportTripoCrew.py writes to OUT/<Name>/Mesh: unit-scale bones, a floor
root, 178 cm. Retargeting the raw Tripo meshes does not work: their limbs sit under a x100-scaled bone the
retargeter ignores, and every limb collapsed onto the pelvis.

The octopus-bodied pair is skipped by default. The owner wants them to move in their own way, not on
borrowed biped clips; set SS_TRIPOCREW_ONLY to include them deliberately.
"""
import json
import os

import unreal as u

OUT = "/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew"
SOURCE_MESH = "/Game/MCO_Mocap_Basics/Character/Mesh/SK_Mannequin"
SOURCE_RIG = OUT + "/IK_TripoSource"
LIB = u.EditorAssetLibrary

# Short name -> Tripo folder. The short names are what the station roster and the owner use.
CREW = {
    "Glyph": "alien_creature_3d_model",
    "Olive": "alien_creature_3d_model_1",
    "Robe": "alien_creature_3d_model_2",
    "Finhead": "alien_creature_3d_model_3",
    "Tendril": "alien_humanoid_3d_model",
    "Dread": "alien_warrior_3d_model",
    "Seer": "alien_warrior_3d_model_1",
    "Ember": "demon_creature_3d_model",
    "Crest": "demonic_humanoid_3d_model",
    "Silver": "fantasy_elf_3d_model",
    "Violet": "purple_alien_cyborg_3d_model_Clone1",
    "Crystal": "sci-fi_alien_3d_model",
    "Cyan": "alien_female_3d_model",
    "Warden": "armored_humanoid_3d_model",
    "Tribal": "fantasy_creature_3d_model",
    "Amethyst": "fantasy_elf_3d_model_Clone1",
    "Abyss": "sci-fi_octopus_humanoid_3d_model_Clone1",      # Kraken (the other octopus) was deleted 2026-10-09
    "Elf": "CharacterRepairs_20261008/Elf",
    "Cyborg": "newCYBORG_20261009",
}
OCTOPUS = {"Abyss"}
RIG_FOLDER = OCTOPUS | {"Ember", "Crest", "Olive", "Elf", "Cyborg"}  # see ImportTripoCrew.py
# Ember's second pair of arms: own chains, driven by the SAME source arm chains, so every clip moves all four.
EXTRA_CHAINS = {"Ember": {"LeftArmLower": ("upperarm_low_l", "hand_low_l", "LeftArm"),
                          "RightArmLower": ("upperarm_low_r", "hand_low_r", "RightArm")},
                # An octopus's arms ARE tentacles (two per shoulder, off the clavicle; the humanoid arm bones carry
                # almost no skin), so the longer tentacle on each side takes the human arm's motion - it points,
                # waves and carries - while the other keeps its own wiggle (AuthorTripoCrewTentacleBlend.py).
                # Kraken had {"LeftArmTent": ("LArmTent0_0", "LArmTent0_7", "LeftArm"), "RightArmTent": (...)};
                # Abyss needs the same once her longer arm tentacle per side is confirmed (index 0 or 1).
                }


def mesh_path(base, short):
    return "%s/%s/SK_%s" % (base, "Rig" if short in RIG_FOLDER else "Mesh", short)
SKIP_BY_DEFAULT = OCTOPUS


def mannequin_chains():
    chains = {"Spine": ("spine_01", "spine_03"), "Neck": ("neck_01", "neck_01"), "Head": ("head", "head")}
    for side, word in (("l", "Left"), ("r", "Right")):
        chains[word + "Clavicle"] = ("clavicle_" + side, "clavicle_" + side)
        chains[word + "Arm"] = ("upperarm_" + side, "hand_" + side)
        chains[word + "Leg"] = ("thigh_" + side, "ball_" + side)
        for finger in ("thumb", "index", "middle", "ring", "pinky"):
            chains[word + finger.title()] = (finger + "_01_" + side, finger + "_03_" + side)
    return chains


def octopus_chains():
    chains = {"Spine": ("Spine01", "Spine02"), "Neck": ("NeckTwist01", "NeckTwist02"), "Head": ("Head", "Head")}
    for side, word in (("L", "Left"), ("R", "Right")):
        chains[word + "Clavicle"] = (side + "_Clavicle", side + "_Clavicle")
        chains[word + "Arm"] = (side + "_Upperarm", side + "_Hand")
        chains[word + "Leg"] = (side + "_Thigh", side + "_ToeBase")
        for finger, own in (("thumb", "Thumb"), ("index", "Index"), ("middle", "Mid"), ("ring", "Ring"),
                            ("pinky", "Pinky")):
            chains[word + finger.title()] = (side + "_" + own + "1", side + "_" + own + "3")
    return chains


# Minimum NPC set the owner asked for: walk, turn, conversation, idle, plus the small behaviours that
# stop a standing NPC reading as a statue. Resolved by name, because these packs keep in-place and
# root-motion variants of one clip in sibling folders whose names differ between packs.
CLIPS = {
    "Idle": "MOB1_Stand_Relaxed_Idle_v2_IPC",
    "Fidget1": "MOB1_Stand_Relaxed_Fgt_v1_IPC",
    "Fidget2": "MOB1_Stand_Relaxed_Fgt_v4_IPC",
    "LookL": "MOB1_Stand_Relaxed_Look_L90",
    "LookR": "MOB1_Stand_Relaxed_Look_R90",
    "Walk": "MOB1_Walk_F_Loop_IPC",
    "WalkStart": "MOB1_Stand_Relaxed_To_Walk_F_IPC",
    "WalkStop": "MOB1_Walk_F_To_Stand_Relaxed_RU_IPC",
    "WalkLookAround": "Walk_06_Look_Around_Loop_IP",
    "WalkCheerful": "Walk_02_Cheerful_Loop_IP",
    "TurnL": "MOB1_Stand_Rlx_Turn_In_Place_L_Loop_IPC",
    "TurnR": "MOB1_Stand_Rlx_Turn_In_Place_R_Loop_IPC",
    "Talk": "Convo_01_Low_Key_Loop",
    "Listen": "Convo_11_Listening_Loop",
    "TalkDramatic1": "TalkGesture_Dramatic01",
    "TalkDramatic2": "TalkGesture_Dramatic02",
}
CLIP_ROOTS = ["/Game/MCO_Mocap_Basics", "/Game/Mobility", "/Game/RamsterZ_FreeAnims_Volume1"]

receipt = {"crew": {}, "errors": []}


def line(s=""):
    u.log_warning("TRIPOCREW| " + str(s))


def build_rig(path, mesh, chains, root, motion_root):
    folder, name = path.rsplit("/", 1)
    # A rig older retargeters still reference cannot be deleted, so an existing one is rebuilt in place.
    rig = LIB.load_asset(path) if LIB.does_asset_exist(path) else None
    if rig is None:
        rig = u.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, u.IKRigDefinition, u.IKRigDefinitionFactory())
    control = u.IKRigController.get_controller(rig)
    for chain in list(control.get_retarget_chains()):
        control.remove_retarget_chain(chain.get_editor_property("chain_name"))
    assert control.set_skeletal_mesh(mesh), "set_skeletal_mesh " + path
    assert control.set_retarget_root(root), "retarget root %s on %s" % (root, path)
    if motion_root:
        control.set_root_motion_bone(motion_root)
    for chain, (start, end) in chains.items():
        made = str(control.add_retarget_chain(chain, start, end, "None"))
        if made != chain:
            receipt["errors"].append("%s: chain %s (%s..%s) not created" % (path, chain, start, end))
    LIB.save_loaded_asset(rig, only_if_is_dirty=False)
    return rig


def resolve_clips():
    registry = u.AssetRegistryHelpers.get_asset_registry()
    registry.wait_for_completion()
    by_name = {}
    for root in CLIP_ROOTS:
        for data in registry.get_assets_by_path(root, recursive=True):
            if str(data.asset_class_path.asset_name) == "AnimSequence":
                by_name.setdefault(str(data.asset_name), data)
    found = {}
    for short, name in CLIPS.items():
        if name in by_name:
            found[short] = by_name[name]
        else:
            receipt["errors"].append("clip not installed: " + name)
    return found


def height_cm(mesh):
    box = mesh.get_bounds().box_extent
    imported = mesh.get_imported_bounds()
    return round(2 * imported.box_extent.z, 1), round(2 * box.z, 1)


def author(short, folder, source_mesh, source_rig, clips):
    base = OUT + "/" + short
    mesh = LIB.load_asset(mesh_path(base, short))
    if not isinstance(mesh, u.SkeletalMesh):
        receipt["errors"].append("%s: no repaired mesh - run ImportTripoCrew.py first" % short)
        return
    # rebuild this character's rig, retargeter and clips; never touch its Mesh/Rig/Role folders
    for path in LIB.list_assets(base, recursive=False, include_folder=False):
        LIB.delete_asset(path.split(".")[0])
    if short in OCTOPUS:
        chains = octopus_chains()
        chains.update({k: (a, b) for k, (a, b, _) in EXTRA_CHAINS.get(short, {}).items()})
        rig = build_rig(base + "/IK_" + short, mesh, chains, "Hip", "root")
    else:
        chains = mannequin_chains()
        chains.update({k: (a, b) for k, (a, b, _) in EXTRA_CHAINS.get(short, {}).items()})
        rig = build_rig(base + "/IK_" + short, mesh, chains, "pelvis", "root")

    retargeter = u.AssetToolsHelpers.get_asset_tools().create_asset("RTG_" + short, base, u.IKRetargeter, u.IKRetargetFactory())
    control = u.IKRetargeterController.get_controller(retargeter)
    src, tgt = u.RetargetSourceOrTarget.SOURCE, u.RetargetSourceOrTarget.TARGET
    control.set_ik_rig(src, source_rig)
    control.set_preview_mesh(src, source_mesh)
    control.set_ik_rig(tgt, rig)
    control.set_preview_mesh(tgt, mesh)
    control.add_default_ops()
    control.assign_ik_rig_to_all_ops(src, source_rig)
    control.assign_ik_rig_to_all_ops(tgt, rig)
    control.auto_map_chains(u.AutoMapChainType.EXACT, True)
    for target_chain, (_, _, source_chain) in EXTRA_CHAINS.get(short, {}).items():
        control.set_source_chain(source_chain, target_chain)
    pose = control.create_retarget_pose(short + "Aligned", tgt)
    control.set_current_retarget_pose(pose, tgt)
    control.auto_align_all_bones(tgt, u.RetargetAutoAlignMethod.CHAIN_TO_CHAIN)
    LIB.save_loaded_asset(retargeter, only_if_is_dirty=False)

    made = []
    for clip_short, data in clips.items():
        inputs = u.IKRetargetBatchOperationInputs()
        for prop, value in (("assets_to_retarget", [data]), ("source_mesh", source_mesh), ("target_mesh", mesh),
                            ("ik_retarget_asset", retargeter), ("search", str(data.asset_name)),
                            ("replace", "A_%s_%s" % (short, clip_short)), ("prefix", ""), ("suffix", ""),
                            ("target_path", base), ("use_source_path", False),
                            ("include_referenced_assets", False), ("overwrite_existing_files", True)):
            inputs.set_editor_property(prop, value)
        try:
            out = u.IKRetargetBatchOperation.run_batch_retarget(inputs)
        except Exception as exc:  # one clip from an incompatible pack must not cost the other fifteen
            receipt["errors"].append("%s/%s: %s" % (short, clip_short, exc))
            continue
        if out:
            made.append(clip_short)
        else:
            receipt["errors"].append("%s/%s: retarget produced nothing" % (short, clip_short))
    LIB.save_directory(base, only_if_is_dirty=False, recursive=True)
    imported, bounds = height_cm(mesh)
    receipt["crew"][short] = {"folder": folder, "height_cm": imported, "bounds_cm": bounds,
                              "chains": len(u.IKRigController.get_controller(rig).get_retarget_chains()),
                              "clips": made}
    line("%-8s %-40s %5.1f cm  %2d clips" % (short, folder, imported, len(made)))


def main():
    if not LIB.does_directory_exist(OUT):
        LIB.make_directory(OUT)
    source_mesh = LIB.load_asset(SOURCE_MESH)
    assert isinstance(source_mesh, u.SkeletalMesh), "MCO mannequin missing: " + SOURCE_MESH
    source_rig = build_rig(SOURCE_RIG, source_mesh, mannequin_chains(), "pelvis", "root")
    clips = resolve_clips()
    line("resolved %d / %d clips" % (len(clips), len(CLIPS)))
    only = os.environ.get("SS_TRIPOCREW_ONLY")
    touched = set()
    for short, folder in CREW.items():
        if only and short not in only.split(","):
            continue
        if not only and short in SKIP_BY_DEFAULT:
            continue
        author(short, folder, source_mesh, source_rig, clips)
        touched.add(short)
    path = os.path.join(u.Paths.project_dir(), "Artifacts", "TripoCrew", "authoring.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2)
    for error in receipt["errors"]:
        line("ERROR " + error)
    if os.environ.get("SS_POST", "1") != "0" and touched:
        # tail / tentacle / hair bakes: a retarget writes those bones at rest and would silently undo them
        import runpy
        runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "AuthorTripoCrewPost.py"),
                       run_name="tripo_post")["run"](sorted(touched))
    line("DONE %d characters, %d errors" % (len(receipt["crew"]), len(receipt["errors"])))


main()
