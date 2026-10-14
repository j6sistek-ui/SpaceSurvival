"""Give Joy the bartender clips: retarget them onto her skeleton from each source rig.

  set SS_JOY_REPORT=<json path>   optional SS_JOY_SOURCES=biped,tavern,freeanims (default all)
  UnrealEditor-Cmd.exe <project> -unattended -NullRHI ... -ExecutePythonScript="<abs>/retarget_joy_bartender.py"

Joy (cc_base skeleton, 101 bones) has 135 clips, all made through RTG_CyborgToJoy; none is a bartender clip. Sources:
  biped     ClipLibrary/BarPeople: the 10 Bar_Counter_Bartender_Type takes Dread plays (3ds Max Biped) via the existing
            ClipLibrary/Rigs/IK_Source_Biped;
  tavern    Content/TavernAnims: AS_Bartender 1-4, AS_AtTheBar 1-2, AS_CheersAndDrink 1-3, AS_TalkAtTheBar 1-4 on the pack's
            own mannequin (a source IK rig is built here with the same chain names as IK_Joy);
  freeanims Content/FreeAnimsMixPack: PourPlateAndserve (the only pour-and-hand-over clip in the project).
Each source gets one retargeter RTG_<Source>ToJoy in JoyBartender/Rig, built exactly like RTG_CyborgToJoy
(Scripts/StationRecipes/CpuJoy121/AuthorJoy117.py): EXACT chain map, a target retarget pose auto-aligned chain-to-chain,
FK ONE_TO_ONE on every chain but Neck. Clips land in JoyBartender/Animations as A_Joy_Bar_<name>. Fresh-create only per
retargeter; existing output clips are never overwritten.
"""
import json
import os

import unreal as u

DEST = "/Game/SpaceSurvival/Licensed/StationAssets/JoyBartender"
JOY_RIG = "/Game/SpaceSurvival/Licensed/StationAssets/JoyLightBlue117/Rig/IK_Joy"
TARGET_MESH = DEST + "/Mesh/SK_Joy"
REPORT_PATH = os.environ.get("SS_JOY_REPORT", "")
WANT = set(os.environ.get("SS_JOY_SOURCES", "biped,tavern,freeanims").split(","))
TOOLS = u.AssetToolsHelpers.get_asset_tools()
L = u.EditorAssetLibrary
R = u.AssetRegistryHelpers.get_asset_registry()
S, T = u.RetargetSourceOrTarget.SOURCE, u.RetargetSourceOrTarget.TARGET
REPORT = {"sources": {}, "clips": [], "errors": []}

# chain -> (start, end) on a UE-mannequin-style skeleton; alternates tried in order when a bone is missing
MANNEQUIN = {
    "Spine": [("spine_01", "spine_05"), ("spine_01", "spine_03")],
    "Neck": [("neck_01", "neck_02"), ("neck_01", "neck_01")],
    "Head": [("head", "head")],
}
for letter, side in [("L", "l"), ("R", "r")]:
    MANNEQUIN[letter + "Clavicle"] = [(f"clavicle_{side}", f"clavicle_{side}")]
    MANNEQUIN[letter + "Arm"] = [(f"upperarm_{side}", f"hand_{side}")]
    MANNEQUIN[letter + "Leg"] = [(f"thigh_{side}", f"foot_{side}")]
    MANNEQUIN[letter + "Toe"] = [(f"ball_{side}", f"ball_{side}")]
    for finger, cc in [("thumb", "Thumb"), ("index", "Index"), ("middle", "Mid"), ("ring", "Ring"), ("pinky", "Pinky")]:
        MANNEQUIN[letter + cc] = [(f"{finger}_01_{side}", f"{finger}_03_{side}")]
CORE = {"Spine", "Neck", "Head", "LClavicle", "RClavicle", "LArm", "RArm", "LLeg", "RLeg"}

SOURCES = {
    "biped": {"rig": "/Game/SpaceSurvival/Licensed/StationAssets/ClipLibrary/Rigs/IK_Source_Biped",
              "mesh": "/Game/SpaceSurvival/Licensed/StationAssets/ClipLibrary/BarPeople/aa_bar_counter_people",
              "folder": "/Game/SpaceSurvival/Licensed/StationAssets/ClipLibrary/BarPeople",
              "match": lambda n: "Bartender_Type" in n, "search": "aa_bar_counter_people_Anim_AA_Bar_Counter_", "replace": "A_Joy_Bar"},
    "tavern": {"rig": None, "mesh": "/Game/TavernAnims/Demo/Mannequins/Meshes/SK_Mannequin", "folder": "/Game/TavernAnims/Animations",
               "match": lambda n: n.startswith(("AS_Bartender", "AS_AtTheBar", "AS_CheersAndDrink", "AS_TalkAtTheBar")) and "/RM/" not in n,
               "search": "AS_", "replace": "A_Joy_Bar_"},
    "freeanims": {"rig": None, "mesh": "/Game/FreeAnimsMixPack/Demo/Mannequins/Meshes/SK_Mannequin", "folder": "/Game/FreeAnimsMixPack/Animation",
                  "match": lambda n: n == "PourPlateAndserve", "search": "PourPlateAndserve", "replace": "A_Joy_Bar_PourAndServe"},
}


def log(s):
    u.log_warning("JOYRTG| " + str(s))


def save(asset):
    assert L.save_loaded_asset(asset, False), asset.get_path_name()


def bone_set(mesh):
    comp = u.SkeletalMeshComponent()
    comp.set_skeletal_mesh_asset(mesh)
    return {str(comp.get_bone_name(i)) for i in range(comp.get_num_bones())}


def build_source_rig(name, mesh):
    """A source IK rig on a mannequin-style skeleton with IK_Joy's chain names, so EXACT auto-map works."""
    path = DEST + "/Rig/" + name
    assert not L.does_asset_exist(path), path
    bones = bone_set(mesh)
    asset = TOOLS.create_asset(name, DEST + "/Rig", u.IKRigDefinition, u.IKRigDefinitionFactory())
    ctl = u.IKRigController.get_controller(asset)
    assert ctl.set_skeletal_mesh(mesh)
    ctl.set_retarget_root("pelvis")
    if "root" in bones:
        ctl.set_root_motion_bone("root")
    made = {}
    for chain, options in MANNEQUIN.items():
        pair = next((p for p in options if p[0] in bones and p[1] in bones), None)
        if pair is None:
            assert chain not in CORE, (chain, options)
            continue
        assert str(ctl.add_retarget_chain(chain, pair[0], pair[1], "None")) == chain
        made[chain] = pair
    for letter in ("L", "R"):
        goal = ctl.add_new_goal(letter + "FootGoal", "foot_" + letter.lower())
        solver = ctl.add_solver("/Script/IKRig.IKRigLimbSolver")
        ctl.set_start_bone("thigh_" + letter.lower(), solver)
        ctl.connect_goal_to_solver(goal, solver)
        ctl.set_retarget_chain_goal(letter + "Leg", goal)
    save(asset)
    return asset, made


def chain_names(rig):
    return [str(c.chain_name) for c in u.IKRigController.get_controller(rig).get_retarget_chains()]


def make_retargeter(key, source_rig, source_mesh, target_rig, target_mesh):
    name = "RTG_%sToJoy" % key.capitalize()
    path = DEST + "/Rig/" + name
    assert not L.does_asset_exist(path), path
    rtg = TOOLS.create_asset(name, DEST + "/Rig", u.IKRetargeter, u.IKRetargetFactory())
    ctl = u.IKRetargeterController.get_controller(rtg)
    ctl.set_ik_rig(S, source_rig)
    ctl.set_ik_rig(T, target_rig)
    ctl.set_preview_mesh(S, source_mesh)
    ctl.set_preview_mesh(T, target_mesh)
    ctl.add_default_ops()
    assert ctl.add_retarget_op("/Script/IKRig.IKRetargetIKChainsOp") >= 0
    ctl.assign_ik_rig_to_all_ops(S, source_rig)
    ctl.assign_ik_rig_to_all_ops(T, target_rig)
    ctl.auto_map_chains(u.AutoMapChainType.EXACT, True)
    mapping = {c: str(ctl.get_source_chain(c)) for c in chain_names(target_rig)}
    missing = [c for c in CORE if mapping.get(c) != c]
    assert not missing, ("core chains unmapped", missing, mapping)
    pose = ctl.create_retarget_pose("JoyAlignedTo" + key.capitalize(), T)
    ctl.set_current_retarget_pose(pose, T)
    target_ctl = u.IKRigController.get_controller(target_rig)
    starts = [str(c.start_bone) for c in target_ctl.get_retarget_chains() if mapping.get(str(c.chain_name)) == str(c.chain_name)]
    ctl.auto_align_bones(starts, u.RetargetAutoAlignMethod.CHAIN_TO_CHAIN, T)
    for i in range(ctl.get_num_retarget_ops()):
        op = ctl.get_op_controller(i)
        if isinstance(op, u.IKRetargetFKChainsController):
            settings = op.get_settings()
            chains = settings.get_editor_property("chains_to_retarget")
            for j, chain in enumerate(chains):
                if str(chain.target_chain_name) != "Neck":
                    chain.set_editor_property("rotation_mode", u.FKChainRotationMode.ONE_TO_ONE)
                    chains[j] = chain
            settings.set_editor_property("chains_to_retarget", chains)
            op.set_settings(settings)
    save(rtg)
    return rtg, mapping


def retarget_clips(key, spec, rtg, source_mesh, target_mesh):
    rows = []
    for ad in R.get_assets_by_path(spec["folder"], True):
        if str(ad.asset_class_path.asset_name) != "AnimSequence":
            continue
        name = str(ad.asset_name)
        if not spec["match"](name) or not spec["match"](str(ad.package_name)):
            continue
        out = DEST + "/Animations/" + name.replace(spec["search"], spec["replace"])
        if L.does_asset_exist(out):
            rows.append({"source": str(ad.package_name), "target": out, "skipped": "exists"})
            continue
        inputs = u.IKRetargetBatchOperationInputs()
        for k, v in dict(assets_to_retarget=[ad], source_mesh=source_mesh, target_mesh=target_mesh, ik_retarget_asset=rtg,
                         search=spec["search"], replace=spec["replace"], target_path=DEST + "/Animations", use_source_path=False,
                         include_referenced_assets=False, overwrite_existing_files=False).items():
            inputs.set_editor_property(k, v)
        made = u.IKRetargetBatchOperation.run_batch_retarget(inputs)
        anim = u.load_asset(out)
        if not isinstance(anim, u.AnimSequence):
            REPORT["errors"].append({"source": str(ad.package_name), "made": [str(x.package_name) for x in made]})
            continue
        assert anim.get_editor_property("skeleton") == target_mesh.skeleton
        src = ad.get_asset()
        assert abs(anim.get_editor_property("sequence_length") - src.get_editor_property("sequence_length")) < .001
        save(anim)
        rows.append({"source": str(ad.package_name), "target": out, "length": anim.get_editor_property("sequence_length")})
    return rows


target_mesh = u.load_asset(TARGET_MESH)
target_rig = u.load_asset(JOY_RIG)
assert isinstance(target_mesh, u.SkeletalMesh) and isinstance(target_rig, u.IKRigDefinition)
joy_chains = chain_names(target_rig)
log("IK_Joy chains: " + ",".join(joy_chains))
for key, spec in SOURCES.items():
    if key not in WANT:
        continue
    try:
        source_mesh = u.load_asset(spec["mesh"])
        assert isinstance(source_mesh, u.SkeletalMesh), spec["mesh"]
        if spec["rig"]:
            source_rig = u.load_asset(spec["rig"])
            assert isinstance(source_rig, u.IKRigDefinition), spec["rig"]
            have = set(chain_names(source_rig))
            missing = [c for c in CORE if c not in have]
            assert not missing, ("existing source rig lacks core chains", spec["rig"], sorted(have))
            built = None
        else:
            source_rig, built = build_source_rig("IK_Source_%sToJoy" % key.capitalize(), source_mesh)
        rtg, mapping = make_retargeter(key, source_rig, source_mesh, target_rig, target_mesh)
        rows = retarget_clips(key, spec, rtg, source_mesh, target_mesh)
        REPORT["sources"][key] = {"rig": source_rig.get_path_name(), "built_chains": built, "retargeter": rtg.get_path_name(), "mapping": mapping, "clips": rows}
        REPORT["clips"] += [r["target"] for r in rows if "length" in r]
        log("%s: %d clips -> Joy (unmapped: %s)" % (key, len([r for r in rows if "length" in r]), [c for c, s in mapping.items() if s != c]))
    except Exception as e:  # noqa
        import traceback
        REPORT["errors"].append({"source": key, "error": str(e), "trace": traceback.format_exc()[-1500:]})
        log("FAILED %s: %s" % (key, e))
if REPORT_PATH:
    json.dump(REPORT, open(REPORT_PATH, "w"), indent=1)
log("DONE clips=%d errors=%d" % (len(REPORT["clips"]), len(REPORT["errors"])))
