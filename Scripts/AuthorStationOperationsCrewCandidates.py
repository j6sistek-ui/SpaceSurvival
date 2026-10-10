"""Private seated human/robot animation candidates only; root owns native execution.

Uses the proven seated Body_Pilot retarget pipeline. No actor/map mutation or
level save. Bone evidence is preliminary; real chair/feet/hand contact and pixels
must pass separately before any candidate replaces an Operations operator.
"""
import hashlib
import json
import math
from pathlib import Path

BASE = '/Game/OutpostSandbox/StationRefinement/OperationsCrewNonAlien20261007'
SOURCE = '/Game/SpaceSurvival/Licensed/HeroReplacement/Final'
SURVEY_SHA = 'b84699a20232f73c3af6de762cb62a94fc0ea76a82ccf40051aac6e6711dce59'
TARGETS = (
    ('Human', '/Game/SciFITrooper_Man_03/SkeletalMesh/SK_SciFITrooper_Man_03', 184.11260198056698),
    ('Robot', '/Game/Robot_scout_R_21/Mesh/SK_Robot_scout_R21', 178.57688903808594),
)
CHAINS = {
    'Spine': ('spine_01', 'spine_03'), 'Neck': ('neck_01', 'neck_01'), 'Head': ('head', 'head'),
    'ClavicleL': ('clavicle_l', 'clavicle_l'), 'ClavicleR': ('clavicle_r', 'clavicle_r'),
    'ArmL': ('upperarm_l', 'hand_l'), 'ArmR': ('upperarm_r', 'hand_r'),
    'LegL': ('thigh_l', 'ball_l'), 'LegR': ('thigh_r', 'ball_r'),
}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(file):
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()


def native_api_preflight(u):
    methods = {
        'AssetToolsHelpers': ('get_asset_tools',),
        'IKRigController': ('get_controller', 'set_skeletal_mesh', 'set_retarget_root',
                            'set_root_motion_bone', 'add_retarget_chain'),
        'IKRetargeterController': ('get_controller', 'set_ik_rig', 'set_preview_mesh', 'add_default_ops',
                                  'assign_ik_rig_to_all_ops', 'auto_map_chains', 'create_retarget_pose',
                                  'set_current_retarget_pose', 'auto_align_all_bones'),
        'IKRetargetBatchOperation': ('run_batch_retarget',),
        'AnimPoseExtensions': ('get_reference_pose', 'get_bone_names', 'get_anim_pose_at_time', 'get_bone_pose'),
        'EditorAssetLibrary': ('does_asset_exist', 'save_loaded_asset'),
    }
    checked = {cls + '.' + name: callable(getattr(getattr(u, cls, None), name, None))
               for cls, names in methods.items() for name in names}
    require(all(checked.values()), 'Proven seated retarget API missing in current native build')
    inputs = u.IKRetargetBatchOperationInputs()
    properties = ('assets_to_retarget', 'source_mesh', 'target_mesh', 'ik_retarget_asset', 'search', 'replace',
                  'target_path', 'use_source_path', 'include_referenced_assets', 'overwrite_existing_files')
    for name in properties:
        inputs.get_editor_property(name)
    return {'methods': checked, 'input_properties_read': list(properties), 'no_assets_created': True}


def ensure(progress=None):
    """Create seven new private assets, preserve all native source bytes, return evidence."""
    import unreal as u
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    survey_file = root / '.agent/local/StationRefinement/StationOperationsServicesProbe5.json'
    require(sha(survey_file) == SURVEY_SHA, 'Exact preserved NPC survey changed')
    survey = json.loads(survey_file.read_text(encoding='utf-8'))
    npc = survey['npc_candidates']
    require(not survey['success'] and survey['preservation_pass'] and survey['pie_stopped'] and
            npc['success'] and npc['scene_unchanged'] and npc['sources_unchanged'],
            'Require independently successful NPC section; aggregate/native crash is retained as failed history')
    protected = dict(npc['source_sha256'])
    protected[str(survey_file)] = SURVEY_SHA
    protected[str(Path(__file__).resolve())] = sha(__file__)
    def protect(package):
        require(package.startswith('/Game/') and '..' not in package and ':' not in package,
                'Only owned local source packages allowed')
        file = root / ('Content/' + package.split('.')[0][6:] + '.uasset')
        require(file.is_file(), 'Native source file unavailable: ' + package)
        protected.setdefault(str(file.resolve()), sha(file))
    for package in (SOURCE + '/SK_SquirrelHeroReplacement', SOURCE + '/Body_Pilot'):
        protect(package)
    require(all(sha(file) == digest for file, digest in protected.items()), 'NPC/source file differs')
    private_names = ['IK_SeatedSource'] + [prefix + kind for kind, _, _ in TARGETS
        for prefix in ('IK_Seated', 'RTG_Seated')] + ['A_' + kind + '_SeatedOperations' for kind, _, _ in TARGETS]
    require(len(private_names) == len(set(private_names)) == 7, 'Private candidate scope changed')
    folder = root / ('Content/' + BASE[6:])
    require(not folder.exists(), 'Preserve partial or previously created private candidate folder')
    lib, tools = u.EditorAssetLibrary, u.AssetToolsHelpers.get_asset_tools()
    require(all(not lib.does_asset_exist(BASE + '/' + name) for name in private_names), 'Private candidate already exists')
    source = u.load_asset(SOURCE + '/SK_SquirrelHeroReplacement')
    body = u.load_asset(SOURCE + '/Body_Pilot')
    require(isinstance(source, u.SkeletalMesh) and isinstance(body, u.AnimSequence) and
            body.get_editor_property('skeleton') == source.skeleton, 'Owned actual seated source rig/clip unavailable')
    protect(source.skeleton.get_path_name())
    source_model = body.get_editor_property('data_model_interface')
    require(0. < float(body.sequence_length) <= 6. and 2 <= source_model.get_number_of_keys() <= 600,
            'Seated source clip exceeded bounded native cadence')
    api = u.AnimPoseExtensions
    meshes = {}
    for kind, package, height in TARGETS:
        mesh = u.load_asset(package)
        expected = next(row for row in npc['candidates'] if row['mesh'].split('.')[0] == package)
        require(isinstance(mesh, u.SkeletalMesh) and mesh.skeleton.get_path_name() == expected['skeleton'] and
                abs(mesh.get_bounds().box_extent.z * 2. - height) < .001,
                'Exact surveyed owned candidate rig/proportions changed: ' + kind)
        meshes[kind] = mesh
    for mesh in (source, *meshes.values()):
        names = set(map(str, api.get_bone_names(api.get_reference_pose(mesh.skeleton))))
        require({'root', 'pelvis'} | {name for ends in CHAINS.values() for name in ends} <= names,
                'Exact nine seated chains do not exist on source/target')
    dirty = []
    def checkpoint(stage):
        if progress:
            progress({'stage': stage, 'private_assets_created': list(dirty)})
    def save(asset):
        require(lib.save_loaded_asset(asset, only_if_is_dirty=False), 'Cannot save private candidate derivative')
        dirty.append(asset.get_path_name())
    def rig(name, mesh):
        asset = tools.create_asset(name, BASE, u.IKRigDefinition, u.IKRigDefinitionFactory())
        require(asset, 'Cannot create private seated rig')
        controller = u.IKRigController.get_controller(asset)
        require(controller.set_skeletal_mesh(mesh) and controller.set_retarget_root('pelvis') and
                controller.set_root_motion_bone('root'), 'Native seated retarget root setup failed')
        for chain, (first, last) in CHAINS.items():
            require(str(controller.add_retarget_chain(chain, first, last, 'None')) == chain,
                    'Native seated chain setup failed: ' + chain)
        save(asset)
        return asset
    evidence = []
    checkpoint('BEFORE_PRIVATE_SOURCE_RIG')
    source_rig = rig('IK_SeatedSource', source)
    for kind, _, _ in TARGETS:
        checkpoint('BEFORE_' + kind.upper() + '_RETARGET')
        mesh = meshes[kind]
        target_rig = rig('IK_Seated' + kind, mesh)
        retargeter = tools.create_asset('RTG_Seated' + kind, BASE, u.IKRetargeter, u.IKRetargetFactory())
        require(retargeter, 'Cannot create private seated retargeter')
        controller = u.IKRetargeterController.get_controller(retargeter)
        source_side, target_side = u.RetargetSourceOrTarget.SOURCE, u.RetargetSourceOrTarget.TARGET
        for side, ik, skeletal in ((source_side, source_rig, source), (target_side, target_rig, mesh)):
            controller.set_ik_rig(side, ik)
            controller.set_preview_mesh(side, skeletal)
        controller.add_default_ops()
        for side, ik in ((source_side, source_rig), (target_side, target_rig)):
            controller.assign_ik_rig_to_all_ops(side, ik)
        controller.auto_map_chains(u.AutoMapChainType.EXACT, True)
        aligned = controller.create_retarget_pose('SeatedAligned', target_side)
        require(str(aligned) == 'SeatedAligned' and controller.set_current_retarget_pose(aligned, target_side),
                'Native seated alignment pose failed')
        controller.auto_align_all_bones(target_side, u.RetargetAutoAlignMethod.CHAIN_TO_CHAIN)
        save(retargeter)
        data = u.AssetRegistryHelpers.get_asset_registry().get_asset_by_object_path(body.get_path_name())
        require(data.is_valid(), 'Native seated source registry identity missing')
        name = 'A_' + kind + '_SeatedOperations'
        inputs = u.IKRetargetBatchOperationInputs()
        for key, value in dict(assets_to_retarget=[data], source_mesh=source, target_mesh=mesh,
                ik_retarget_asset=retargeter, search='Body_Pilot', replace=name, target_path=BASE,
                use_source_path=False, include_referenced_assets=False, overwrite_existing_files=False).items():
            inputs.set_editor_property(key, value)
        require(u.IKRetargetBatchOperation.run_batch_retarget(inputs), 'Native private seated retarget failed')
        clip = u.load_asset(BASE + '/' + name)
        require(isinstance(clip, u.AnimSequence) and clip.get_editor_property('skeleton') == mesh.skeleton,
                'Native retarget did not produce the exact compatible private clip')
        require(abs(float(clip.sequence_length) - float(body.sequence_length)) < .0001,
                'Private seated candidate changed the owned motion cadence')
        samples = []
        options = u.AnimPoseEvaluationOptions(optional_skeletal_mesh=mesh, evaluation_type=u.AnimDataEvalType.RAW)
        for fraction in (0., .25, .5, .75, 1.):
            seconds = float(clip.sequence_length) * fraction
            pose = api.get_anim_pose_at_time(clip, seconds, options)
            points = {bone: list(api.get_bone_pose(pose, bone, u.AnimPoseSpaces.WORLD).translation.to_tuple())
                      for bone in ('pelvis', 'thigh_l', 'calf_l', 'foot_l', 'ball_l',
                                   'thigh_r', 'calf_r', 'foot_r', 'ball_r', 'hand_l', 'hand_r')}
            knees = []
            for side in ('l', 'r'):
                hip, knee, foot = (points[name + '_' + side] for name in ('thigh', 'calf', 'foot'))
                first = [hip[i] - knee[i] for i in range(3)]
                second = [foot[i] - knee[i] for i in range(3)]
                length = math.sqrt(sum(x*x for x in first) * sum(x*x for x in second))
                require(length > 1., 'Retargeted seated limb collapsed')
                angle = math.degrees(math.acos(max(-1., min(1., sum(a*b for a,b in zip(first,second))/length))))
                require(45. < angle < 145. and knee[2] - foot[2] > 15., 'Candidate is not actual seated motion')
                knees.append(angle)
            samples.append({'seconds': seconds, 'component_bones_cm': points, 'knee_angles_degrees': knees})
        save(clip)
        evidence.append({'kind': kind, 'mesh': mesh.get_path_name(), 'skeleton': mesh.skeleton.get_path_name(),
                         'clip': clip.get_path_name(), 'duration_seconds': float(clip.sequence_length),
                         'bone_only_samples': samples, 'real_contact_proved': False})
        checkpoint('SAVED_' + kind.upper() + '_PRELIMINARY_CLIP')
    require(len(dirty) == 7 and {file.stem for file in folder.rglob('*.uasset')} == set(private_names),
            'Native derivative-only asset count differs')
    require(all(sha(file) == digest for file, digest in protected.items()), 'Native seated source bytes changed')
    return {'success': True, 'scope': 'SEVEN_PRIVATE_RETARGET_DERIVATIVES_ONLY_NO_LEVEL_SAVE_OR_OPERATOR_REPLACEMENT',
            'saved_assets': dirty, 'candidate_evidence': evidence, 'source_sha256': protected,
            'sources_unchanged': True, 'actual_contacts_and_visuals_pass': False,
            'limits': ['Native bone-space seating only; do not install before skin/floor/seat/hand contact and pixels.',
                       'Services5 aggregate/native0xC0000005 retained; successful NPC section is independently guarded.',
                       'Female alien bartender and all current four T operators remain unchanged.']}
