"""Author the station's alien crew: recoloured skins and retargeted clips.

  UnrealEditor-Cmd.exe <project> -unattended -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser -ExecutePythonScript="<abs path>/Scripts/AuthorAlienCrew.py"

Everything this writes lands under /Game/SpaceSurvival/Licensed/StationAssets/AlienCrew, which is
inside the always-cooked /Game/SpaceSurvival root. Nothing in the licensed packs is modified: the
alien pack's own IK retargeter is duplicated out before its empty source side is filled in.

Two things the packs already did, which is why there is no rigging here:
  - the alien ships a standard-proportion UE5 skeleton, its own IK rig (IK_Nixar) and a retargeter
    (RTG_Nyxar) whose target side is authored and whose source side is left blank on purpose;
  - the project already built IK_UE4Mannequin for the squirrel hero's MoCap retarget, and that is
    exactly the source side the alien pack left for the caller to supply.

Run with -NullRHI only if you do not need the retarget: batch retargeting needs a real RHI.
"""
import unreal

OUT = "/Game/SpaceSurvival/Licensed/StationAssets/AlienCrew"
ANIM_OUT = OUT + "/Anims"
OUR_RTG = OUT + "/RTG_MannequinToNyxar"

PACK_RTG = "/Game/Nyxar/Meshes/RTG_Nyxar"
BODY_MI = "/Game/Nyxar/Materials/MI_Nyxar_Body_Inst"
TGT_MESH = "/Game/Nyxar/Meshes/SKM_Nyxar"
SRC_RIG = "/Game/SpaceSurvival/Licensed/MocapSource/IK_UE4Mannequin"
SRC_MESH = "/Game/MCO_Mocap_Basics/Character/Mesh/SK_Mannequin"

# The pack exposes Emiss Color Body / Emiss Color Hands and separate emissive strengths for body,
# eyes and hands. Varying those plus Brightness and Saturation is the variation the listing offers,
# and it costs one material instance per crew member rather than a second mesh.
#   name, emissive rgb, body emissive strength, skin brightness, skin saturation
CREW_SKINS = [
    ("Teal", (0.055, 0.463, 0.698), 5.00, 1.00, 1.00),
    ("Amber", (0.820, 0.330, 0.055), 4.20, 1.06, 0.88),
    ("Violet", (0.400, 0.120, 0.730), 5.60, 0.94, 1.12),
    ("Jade", (0.080, 0.620, 0.300), 4.60, 1.02, 0.94),
    ("Rose", (0.740, 0.110, 0.290), 5.20, 0.96, 1.06),
    ("Pale", (0.560, 0.640, 0.720), 3.40, 1.10, 0.72),
]

# Resolved by name through the asset registry, because these packs put the in-place and root-motion
# variants of the same clip in sibling folders and the folder names differ between the two packs.
CLIPS = [
    "Convo_01_Low_Key_Loop",
    "Convo_11_Listening_Loop",
    "Walk_06_Look_Around_Loop_IP",
    "Walk_02_Cheerful_Loop_IP",
    "Walk_13_Power_Walk_Loop_IP",
    "Walk_04_Texting_Loop_IP",
    "MOB1_Stand_Relaxed_Idle_v2_IPC",
    "MOB1_Stand_Relaxed_Fgt_v1_IPC",
    "MOB1_Stand_Relaxed_Fgt_v4_IPC",
    "MOB1_Stand_Rlx_Turn_In_Place_L_Loop_IPC",
    "MOB1_Stand_Rlx_Turn_In_Place_R_Loop_IPC",
    "MOB1_Walk_F_Loop_IPC",
    # Jog and run: not needed by the standing crew, but ASSWalker's gait ladder wants a rung above
    # walk, and a hero with only a walk clip can never move faster than one.
    "MOB1_Jog_F_IPC",
    "MOB1_Run_F_IPC",
    "MOB1_Stand_Relaxed_Look_Center",
    "MOB1_Stand_Relaxed_Look_L90",
    "MOB1_Stand_Relaxed_Look_R90",
    "MOB1_Stand_Relaxed_Look_U90",
]
CLIP_ROOTS = ["/Game/MCO_Mocap_Basics", "/Game/Mobility"]

EAL = unreal.EditorAssetLibrary


def line(s=""):
    unreal.log_warning("CREW| " + str(s))


def section(t):
    line()
    line("=" * 70)
    line(t)
    line("=" * 70)


def require(paths):
    missing = [p for p in paths if not EAL.does_asset_exist(p)]
    for p in missing:
        line("  MISSING %s" % p)
    return not missing


def author_skins():
    section("CREW SKINS")
    parent = EAL.load_asset(BODY_MI)
    if parent is None:
        line("  parent material instance missing - skipping skins")
        return []
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    lib = unreal.MaterialEditingLibrary
    made = []
    for name, rgb, emissive, brightness, saturation in CREW_SKINS:
        asset = "MI_NyxarCrew_" + name
        full = OUT + "/" + asset
        if EAL.does_asset_exist(full):
            EAL.delete_asset(full)
        mi = tools.create_asset(asset, OUT, unreal.MaterialInstanceConstant,
                                unreal.MaterialInstanceConstantFactoryNew())
        if mi is None:
            line("  %-24s FAILED" % asset)
            continue
        lib.set_material_instance_parent(mi, parent)
        colour = unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0)
        lib.set_material_instance_vector_parameter_value(mi, "Emiss Color Body", colour)
        lib.set_material_instance_vector_parameter_value(mi, "Emiss Color Hands", colour)
        lib.set_material_instance_scalar_parameter_value(mi, "Emissive Body", emissive)
        lib.set_material_instance_scalar_parameter_value(mi, "Emissive Hands", emissive * 0.26)
        lib.set_material_instance_scalar_parameter_value(mi, "Emissive Eyes", emissive * 1.12)
        lib.set_material_instance_scalar_parameter_value(mi, "Brightness", brightness)
        lib.set_material_instance_scalar_parameter_value(mi, "Saturation", saturation)
        EAL.save_asset(full)
        made.append(asset)
        line("  %-24s rgb=(%.3f, %.3f, %.3f) emissive=%.2f" % (asset, rgb[0], rgb[1], rgb[2], emissive))
    return made


def author_clips():
    section("RETARGET")
    if not require([PACK_RTG, BODY_MI, TGT_MESH, SRC_RIG, SRC_MESH]):
        line("  aborting retarget")
        return []

    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    registry.wait_for_completion()
    by_name = {}
    for root in CLIP_ROOTS:
        for data in registry.get_assets_by_path(root, recursive=True):
            if str(data.asset_class_path.asset_name) == "AnimSequence":
                by_name.setdefault(str(data.asset_name), data)
    wanted = unreal.Array(unreal.AssetData)
    for name in CLIPS:
        data = by_name.get(name)
        if data is None:
            line("  NOT FOUND %s" % name)
        else:
            wanted.append(data)
    if len(wanted) == 0:
        line("  no source clips resolved - is the MoCap content installed?")
        return []
    line("  resolved %d / %d clips" % (len(wanted), len(CLIPS)))

    # The pack's retargeter has its target side authored and its source side empty. Duplicate it out
    # so the licensed asset is never written to, then fill in the source and let it map the chains.
    if EAL.does_asset_exist(OUR_RTG):
        EAL.delete_asset(OUR_RTG)
    EAL.duplicate_asset(PACK_RTG, OUR_RTG)
    retargeter = EAL.load_asset(OUR_RTG)
    controller = unreal.IKRetargeterController.get_controller(retargeter)
    controller.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, EAL.load_asset(SRC_RIG))
    controller.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE, EAL.load_asset(SRC_MESH))
    controller.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
    EAL.save_asset(OUR_RTG)
    line("  %s ready" % OUR_RTG)

    if not EAL.does_directory_exist(ANIM_OUT):
        EAL.make_directory(ANIM_OUT)

    # duplicate_and_retarget is deprecated in 5.8 and wants Array[AssetData], not objects; the struct
    # form is the supported one and is the only place target_path is honoured.
    inputs = unreal.IKRetargetBatchOperationInputs()
    for prop, value in (("assets_to_retarget", wanted),
                        ("source_mesh", EAL.load_asset(SRC_MESH)),
                        ("target_mesh", EAL.load_asset(TGT_MESH)),
                        ("ik_retarget_asset", retargeter),
                        ("search", ""), ("replace", ""),
                        ("prefix", "A_Alien_"), ("suffix", ""),
                        ("target_path", ANIM_OUT),
                        ("use_source_path", False),
                        ("include_referenced_assets", False),
                        ("overwrite_existing_files", True)):
        inputs.set_editor_property(prop, value)
    result = unreal.IKRetargetBatchOperation.run_batch_retarget(inputs)
    made = [str(a.asset_name) for a in result] if result else []
    for name in made:
        line("  %s" % name)
    line("  retargeted %d clips into %s" % (len(made), ANIM_OUT))
    return made


skins = author_skins()
clips = author_clips()
EAL.save_directory(OUT, only_if_is_dirty=False, recursive=True)

section("SUMMARY")
line("  skins   %d" % len(skins))
line("  clips   %d" % len(clips))
line("  Config/DefaultGame.ini must cook /Game/Nyxar/Meshes, /Materials and /TXT:")
line("  the crew mesh is loaded by string path and the cooker cannot follow a string.")
line()
line("CREW| DONE")
