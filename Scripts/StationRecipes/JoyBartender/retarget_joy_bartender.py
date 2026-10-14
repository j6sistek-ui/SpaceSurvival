"""Give Joy the bartender clips: retarget them onto her skeleton from each source rig.

  set SS_JOY_REPORT=<json path>   optional SS_JOY_SOURCES=biped,tavern,freeanims (default all)
  UnrealEditor-Cmd.exe <project> -unattended -NullRHI ... -ExecutePythonScript="<abs>/retarget_joy_bartender.py"

Joy (cc_base skeleton, 101 bones) has 135 clips, all made through RTG_CyborgToJoy; none is a bartender clip. Sources:
  biped     ClipLibrary/BarPeople: the 10 Bar_Counter_Bartender_Type takes Dread plays (3ds Max Biped, Bip01-* bones);
  tavern    Content/TavernAnims: AS_Bartender 1-4, AS_AtTheBar 1-2, AS_CheersAndDrink 1-3, AS_TalkAtTheBar 1-4 on the pack's
            UE5 Manny (SKM_Manny, skeleton SK_Mannequin);
  freeanims Content/FreeAnimsMixPack: PourPlateAndserve (the only pour-and-hand-over clip in the project), UE5 Manny too.
Each source gets its own IK rig here with IK_Joy's chain names (so EXACT auto-map works) and one retargeter RTG_<Source>ToJoy
in JoyBartender/Rig, built like RTG_CyborgToJoy (Scripts/StationRecipes/CpuJoy121/AuthorJoy117.py): a target retarget pose
auto-aligned chain-to-chain, FK ONE_TO_ONE on every chain but Neck. Clips land in JoyBartender/Animations as A_Joy_Bar*.
Fresh-create only per rig and retargeter; existing output clips are never overwritten.
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

# chain -> candidate (start, end) pairs; the first pair whose bones both exist is used
MANNEQUIN = {"Spine": [("spine_01", "spine_05"), ("spine_01", "spine_03")], "Neck": [("neck_01", "neck_02"), ("neck_01", "neck_01")], "Head": [("head", "head")]}
for letter, side in [("L", "l"), ("R", "r")]:
    MANNEQUIN[letter + "Clavicle"] = [(f"clavicle_{side}", f"clavicle_{side}")]
    MANNEQUIN[letter + "Arm"] = [(f"upperarm_{side}", f"hand_{side}")]
    MANNEQUIN[letter + "Leg"] = [(f"thigh_{side}", f"foot_{side}")]
    MANNEQUIN[letter + "Toe"] = [(f"ball_{side}", f"ball_{side}")]
    for finger, cc in [("thumb", "Thumb"), ("index", "Index"), ("middle", "Mid"), ("ring", "Ring"), ("pinky", "Pinky")]:
        MANNEQUIN[letter + cc] = [(f"{finger}_01_{side}", f"{finger}_03_{side}")]
BIPED = {"Spine": [("Bip01-Spine", "Bip01-Spine3")], "Neck": [("Bip01-Neck", "Bip01-Neck")], "Head": [("Bip01-Head", "Bip01-Head")]}
for letter in ("L", "R"):
    BIPED[letter + "Clavicle"] = [(f"Bip01-{letter}-Clavicle", f"Bip01-{letter}-Clavicle")]
    BIPED[letter + "Arm"] = [(f"Bip01-{letter}-UpperArm", f"Bip01-{letter}-Hand")]
    BIPED[letter + "Leg"] = [(f"Bip01-{letter}-Thigh", f"Bip01-{letter}-Foot")]
    BIPED[letter + "Toe"] = [(f"Bip01-{letter}-Toe0", f"Bip01-{letter}-Toe0")]
    for n, cc in [(0, "Thumb"), (1, "Index"), (2, "Mid"), (3, "Ring"), (4, "Pinky")]:
        BIPED[letter + cc] = [(f"Bip01-{letter}-Finger{n}", f"Bip01-{letter}-Finger{n}2")]
CORE = {"Spine", "Neck", "Head", "LClavicle", "RClavicle", "LArm", "RArm", "LLeg", "RLeg"}

SOURCES = {
    "biped": {"table": BIPED, "root": "Bip01-Pelvis", "rootmotion": "Bip01", "thigh": "Bip01-{L}-Thigh", "foot": "Bip01-{L}-Foot",
              "mesh": "/Game/SpaceSurvival/Licensed/StationAssets/ClipLibrary/BarPeople/aa_bar_counter_people",
              "folder": "/Game/SpaceSurvival/Licensed/StationAssets/ClipLibrary/BarPeople",
              "match": lambda n: "Bartender_Type" in n, "search": "aa_bar_counter_people_Anim_AA_Bar_Counter_", "replace": "A_Joy_Bar"},
    "tavern": {"table": MANNEQUIN, "root": "pelvis", "rootmotion": "root", "thigh": "thigh_{l}", "foot": "foot_{l}",
               "mesh": "/Game/TavernAnims/Demo/Mannequins/Meshes/SKM_Manny", "folder": "/Game/TavernAnims/Animations",
               "match": lambda n: n.startswith(("AS_Bartender", "AS_AtTheBar", "AS_CheersAndDrink", "AS_TalkAtTheBar")) and "/RM/" not in n,
               "search": "AS_", "replace": "A_Joy_Bar_"},
    "freeanims": {"table": MANNEQUIN, "root": "pelvis", "rootmotion": "root", "thigh": "thigh_{l}", "foot": "foot_{l}",
                  "mesh": "/Game/FreeAnimsMixPack/Demo/Mannequins/Meshes/SKM_Manny", "folder": "/Game/FreeAnimsMixPack/Animation",
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


def chain_rows(rig):
    rows = []
    for c in u.IKRigController.get_controller(rig).get_retarget_chains():
        rows.append({k: str(c.get_editor_property(k)) for k in ("chain_name", "start_bone", "end_bone")})
    return rows


def build_source_rig(name, spec, mesh):
    """A source IK rig with IK_Joy's chain names on this skeleton, so EXACT auto-map works."""
    path = DEST + "/Rig/" + name
    assert not L.does_asset_exist(path), path
    bones = bone_set(mesh)
    asset = TOOLS.create_asset(name, DEST + "/Rig", u.IKRigDefinition, u.IKRigDefinitionFactory())
    ctl = u.IKRigController.get_controller(asset)
    assert ctl.set_skeletal_mesh(mesh)
    assert spec["root"] in bones, spec["root"]
    ctl.set_retarget_root(spec["root"])
    if spec["rootmotion"] in bones:
        ctl.set_root_motion_bone(spec["rootmotion"])
    made = {}
    for chain, options in spec["table"].items():
        pair = next((p for p in options if p[0] in bones and p[1] in bones), None)
        if pair is None:
            assert chain not in CORE, (chain, options)
            continue
        assert str(ctl.add_retarget_chain(chain, pair[0], pair[1], "None")) == chain
        made[chain] = pair
    for letter in ("L", "R"):
        foot = spec["foot"].format(L=letter, l=letter.lower())
        thigh = spec["thigh"].format(L=letter, l=letter.lower())
        goal = ctl.add_new_goal(letter + "FootGoal", foot)
        solver = ctl.add_solver("/Script/IKRig.IKRigLimbSolver")
        ctl.set_start_bone(thigh, solver)
        ctl.connect_goal_to_solver(goal, solver)
        ctl.set_retarget_chain_goal(letter + "Leg", goal)
    save(asset)
    return asset, made


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
    target_chains = chain_rows(target_rig)
    mapping = {r["chain_name"]: str(ctl.get_source_chain(r["chain_name"])) for r in target_chains}
    missing = [c for c in CORE if mapping.get(c) != c]
    assert not missing, ("core chains unmapped", missing, mapping)
    pose = ctl.create_retarget_pose("JoyAlignedTo" + key.capitalize(), T)
    ctl.set_current_retarget_pose(pose, T)
    starts = [r["start_bone"] for r in target_chains if mapping.get(r["chain_name"]) == r["chain_name"]]
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


def retarget_clips(spec, rtg, source_mesh, target_mesh):
    rows = []
    for ad in R.get_assets_by_path(spec["folder"], True):
        if str(ad.asset_class_path.asset_name) != "AnimSequence":
            continue
        name = str(ad.asset_name)
        if not spec["match"](name) or "/RM/" in str(ad.package_name):
            continue
        src = ad.get_asset()
        if src.get_editor_property("skeleton") != source_mesh.skeleton:
            rows.append({"source": str(ad.package_name), "skipped": "other skeleton " + src.get_editor_property("skeleton").get_name()})
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
        assert abs(anim.get_editor_property("sequence_length") - src.get_editor_property("sequence_length")) < .001
        save(anim)
        rows.append({"source": str(ad.package_name), "target": out, "length": anim.get_editor_property("sequence_length")})
    return rows


target_mesh = u.load_asset(TARGET_MESH)
target_rig = u.load_asset(JOY_RIG)
assert isinstance(target_mesh, u.SkeletalMesh) and isinstance(target_rig, u.IKRigDefinition)
log("IK_Joy chains: " + ",".join(r["chain_name"] for r in chain_rows(target_rig)))
for key, spec in SOURCES.items():
    if key not in WANT:
        continue
    try:
        source_mesh = u.load_asset(spec["mesh"])
        assert isinstance(source_mesh, u.SkeletalMesh), spec["mesh"]
        rig_path = DEST + "/Rig/IK_Source_%sToJoy" % key.capitalize()
        rtg_path = DEST + "/Rig/RTG_%sToJoy" % key.capitalize()
        if L.does_asset_exist(rig_path) and L.does_asset_exist(rtg_path):
            # a previous run built them; only the clips are (re)done
            source_rig, built = u.load_asset(rig_path), "reused"
            rtg = u.load_asset(rtg_path)
            ctl = u.IKRetargeterController.get_controller(rtg)
            mapping = {r["chain_name"]: str(ctl.get_source_chain(r["chain_name"])) for r in chain_rows(target_rig)}
        else:
            source_rig, built = build_source_rig("IK_Source_%sToJoy" % key.capitalize(), spec, source_mesh)
            rtg, mapping = make_retargeter(key, source_rig, source_mesh, target_rig, target_mesh)
        rows = retarget_clips(spec, rtg, source_mesh, target_mesh)
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
