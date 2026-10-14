"""Create one private Nyxar seated clip; callable by the lead's serialized author pass.

No map load/save, process exit, or vendor mutation. This uses the same UE5.8 native
retarget APIs as ReplacementHero/Retarget.py and AuthorAlienFemalePresentation.py.
The owned seated pilot body supplies real bent legs/arms, not a lowered standing idle.
"""
import math

BASE = '/Game/OutpostSandbox/StationRefinement/OperationsCrew'
SOURCE = '/Game/SpaceSurvival/Licensed/HeroReplacement/Final'
TARGET = '/Game/Nyxar/Meshes/SKM_Nyxar'
CLIP = BASE + '/A_Nyxar_SeatedOperations'
CHAINS = {
    'Spine': ('spine_01', 'spine_03'), 'Neck': ('neck_01', 'neck_01'),
    'Head': ('head', 'head'), 'ClavicleL': ('clavicle_l', 'clavicle_l'),
    'ClavicleR': ('clavicle_r', 'clavicle_r'), 'ArmL': ('upperarm_l', 'hand_l'),
    'ArmR': ('upperarm_r', 'hand_r'), 'LegL': ('thigh_l', 'ball_l'),
    'LegR': ('thigh_r', 'ball_r'),
}


def pose_evidence(clip):
    import unreal as u
    api = u.AnimPoseExtensions
    pose = api.get_anim_pose_at_frame(clip, 0, u.AnimPoseEvaluationOptions())
    points = {}
    for name in ('pelvis', 'thigh_l', 'calf_l', 'foot_l', 'ball_l',
                 'thigh_r', 'calf_r', 'foot_r', 'ball_r', 'hand_l', 'hand_r'):
        p = api.get_bone_pose(pose, name, u.AnimPoseSpaces.WORLD).translation
        points[name] = [p.x, p.y, p.z]
    knees = []
    for side in ('l', 'r'):
        hip, knee, ankle = (points[n + '_' + side] for n in ('thigh', 'calf', 'foot'))
        a = [hip[i] - knee[i] for i in range(3)]
        b = [ankle[i] - knee[i] for i in range(3)]
        lengths = math.sqrt(sum(x*x for x in a) * sum(x*x for x in b))
        assert lengths > 1., 'Retargeted crew has missing/collapsed leg bones'
        angle = math.degrees(math.acos(max(-1., min(1., sum(a[i]*b[i] for i in range(3))/lengths))))
        assert 45. < angle < 145., 'Retarget is not a seated knee: ' + str(angle)
        assert knee[2] - ankle[2] > 15., 'Retargeted seated shin does not descend toward the footrest'
        knees.append(angle)
    return {'clip': clip.get_path_name(), 'knee_angles_degrees': knees,
            'component_bones_cm': points,
            'limits': 'Bone-space seated check only; chair contact, hand placement and appearance need rendered review.'}


def ensure():
    import unreal as u
    lib = u.EditorAssetLibrary
    tools = u.AssetToolsHelpers.get_asset_tools()
    target = u.load_asset(TARGET)
    source = u.load_asset(SOURCE + '/SK_SquirrelHeroReplacement')
    body = u.load_asset(SOURCE + '/Body_Pilot')
    assert target and source and body, 'Owned source pilot/target crew assets are required'
    if lib.does_asset_exist(CLIP):
        clip = u.load_asset(CLIP)
        assert clip.get_editor_property('skeleton') == target.skeleton, 'Existing private seated clip has wrong rig'
        return clip, pose_evidence(clip)
    # A partial author attempt is preserved for diagnosis; never overwrite private work.
    for name in ('IK_SeatedSource', 'IK_SeatedNyxar', 'RTG_SeatedNyxar'):
        assert not lib.does_asset_exist(BASE + '/' + name), 'Partial seated authoring exists: ' + name

    def rig(name, mesh):
        r = tools.create_asset(name, BASE, u.IKRigDefinition, u.IKRigDefinitionFactory())
        assert r
        c = u.IKRigController.get_controller(r)
        assert c.set_skeletal_mesh(mesh)
        assert c.set_retarget_root('pelvis')
        assert c.set_root_motion_bone('root')
        names = set(map(str, u.AnimPoseExtensions.get_bone_names(
            u.AnimPoseExtensions.get_reference_pose(mesh.skeleton))))
        for chain, (start, end) in CHAINS.items():
            assert start in names and end in names, 'Missing seated retarget chain: ' + chain
            assert str(c.add_retarget_chain(chain, start, end, 'None')) == chain
        assert lib.save_loaded_asset(r, only_if_is_dirty=False)
        return r

    sr, tr = rig('IK_SeatedSource', source), rig('IK_SeatedNyxar', target)
    rt = tools.create_asset('RTG_SeatedNyxar', BASE, u.IKRetargeter, u.IKRetargetFactory())
    assert rt
    c = u.IKRetargeterController.get_controller(rt)
    source_side, target_side = u.RetargetSourceOrTarget.SOURCE, u.RetargetSourceOrTarget.TARGET
    for side, r, mesh in ((source_side, sr, source), (target_side, tr, target)):
        c.set_ik_rig(side, r)
        c.set_preview_mesh(side, mesh)
    c.add_default_ops()
    for side, r in ((source_side, sr), (target_side, tr)):
        c.assign_ik_rig_to_all_ops(side, r)
    c.auto_map_chains(u.AutoMapChainType.EXACT, True)
    # No floor-plant solver: the pilot's bent legs must remain seated above its footrest.
    pose = c.create_retarget_pose('SeatedAligned', target_side)
    assert str(pose) == 'SeatedAligned' and c.set_current_retarget_pose(pose, target_side)
    c.auto_align_all_bones(target_side, u.RetargetAutoAlignMethod.CHAIN_TO_CHAIN)
    assert lib.save_loaded_asset(rt, only_if_is_dirty=False)
    registry = u.AssetRegistryHelpers.get_asset_registry()
    data = registry.get_asset_by_object_path(body.get_path_name())
    assert data.is_valid()
    inputs = u.IKRetargetBatchOperationInputs()
    for key, value in dict(assets_to_retarget=[data], source_mesh=source, target_mesh=target,
                           ik_retarget_asset=rt, search='Body_Pilot', replace='A_Nyxar_SeatedOperations',
                           target_path=BASE, use_source_path=False, include_referenced_assets=False,
                           overwrite_existing_files=False).items():
        inputs.set_editor_property(key, value)
    result = u.IKRetargetBatchOperation.run_batch_retarget(inputs)
    assert result and lib.does_asset_exist(CLIP), 'Native retarget did not create the one requested seated clip'
    clip = u.load_asset(CLIP)
    assert clip.get_editor_property('skeleton') == target.skeleton
    evidence = pose_evidence(clip)
    assert lib.save_loaded_asset(clip, only_if_is_dirty=False)
    return clip, evidence
