"""Derive bounded seated visitor clips from the existing owned lounge motion.

No map edits, source edits, external tools or new behavior framework. Call after
visually screening the target cast for common-area suitability. Native fitting
and motion/contact review are still required before placing a derivative.
"""
import hashlib
from pathlib import Path

ROOT = '/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew'
BASE = '/Game/OutpostSandbox/StationRefinement/VisitorSeats20261009'
SOURCE_MESH = '/Game/Nyxar/Meshes/SKM_Nyxar'
SOURCE_CLIP = '/Game/OutpostSandbox/StationRefinement/SocialCrew/A_Nyxar_SeatedLounge'
CHAINS = {
    'Spine':('spine_01','spine_03'), 'Neck':('neck_01','neck_01'), 'Head':('head','head'),
    'ClavicleL':('clavicle_l','clavicle_l'), 'ClavicleR':('clavicle_r','clavicle_r'),
    'ArmL':('upperarm_l','hand_l'), 'ArmR':('upperarm_r','hand_r'),
    'LegL':('thigh_l','ball_l'), 'LegR':('thigh_r','ball_r'),
}


def author(u, names=('Robe','Tendril')):
    assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    assert not u.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    assert all(n in ('Robe','Tendril','Seer','Glyph') for n in names), 'Visually screen additional cast first'
    lib=u.EditorAssetLibrary
    tools=u.AssetToolsHelpers.get_asset_tools()
    source=u.load_asset(SOURCE_MESH)
    body=u.load_asset(SOURCE_CLIP)
    assert body.get_editor_property('skeleton') == source.skeleton
    source_file=Path(u.Paths.project_content_dir())/(SOURCE_CLIP.removeprefix('/Game/')+'.uasset')
    source_sha=hashlib.sha256(source_file.read_bytes()).hexdigest()
    api=u.AnimPoseExtensions
    result=[]

    def save(asset):
        assert lib.save_loaded_asset(asset,only_if_is_dirty=False)

    def rig(folder,name,mesh):
        r=tools.create_asset(name,folder,u.IKRigDefinition,u.IKRigDefinitionFactory())
        assert r
        c=u.IKRigController.get_controller(r)
        assert c.set_skeletal_mesh(mesh) and c.set_retarget_root('pelvis') and c.set_root_motion_bone('root')
        for chain,(start,end) in CHAINS.items():
            assert str(c.add_retarget_chain(chain,start,end,'None')) == chain
        save(r)
        return r

    for name in names:
        folder=BASE+'/'+name
        target=u.load_asset(ROOT+'/'+name+'/Mesh/SK_'+name)
        assert isinstance(target,u.SkeletalMesh)
        for m in (source,target):
            bones=set(map(str,api.get_bone_names(api.get_reference_pose(m.skeleton))))
            assert {'root','pelvis'}|{b for ends in CHAINS.values() for b in ends} <= bones
        paths=[folder+'/'+n for n in ('IK_Source','IK_'+name,'RTG_'+name,'A_'+name+'_SeatedVisitor')]
        assert all(not lib.does_asset_exist(p) for p in paths), 'Preserve and inspect any earlier derivative'
        sr,tr=rig(folder,'IK_Source',source),rig(folder,'IK_'+name,target)
        rt=tools.create_asset('RTG_'+name,folder,u.IKRetargeter,u.IKRetargetFactory())
        assert rt
        c=u.IKRetargeterController.get_controller(rt)
        ss,ts=u.RetargetSourceOrTarget.SOURCE,u.RetargetSourceOrTarget.TARGET
        for side,r,m in ((ss,sr,source),(ts,tr,target)):
            c.set_ik_rig(side,r)
            c.set_preview_mesh(side,m)
        c.add_default_ops()
        c.assign_ik_rig_to_all_ops(ss,sr)
        c.assign_ik_rig_to_all_ops(ts,tr)
        c.auto_map_chains(u.AutoMapChainType.EXACT,True)
        pose=c.create_retarget_pose('SeatedAligned',ts)
        assert c.set_current_retarget_pose(pose,ts)
        c.auto_align_all_bones(ts,u.RetargetAutoAlignMethod.CHAIN_TO_CHAIN)
        save(rt)
        data=u.AssetRegistryHelpers.get_asset_registry().get_asset_by_object_path(body.get_path_name())
        inputs=u.IKRetargetBatchOperationInputs()
        for k,v in dict(assets_to_retarget=[data],source_mesh=source,target_mesh=target,ik_retarget_asset=rt,
                search=body.get_name(),replace='A_'+name+'_SeatedVisitor',target_path=folder,
                use_source_path=False,include_referenced_assets=False,overwrite_existing_files=False).items():
            inputs.set_editor_property(k,v)
        assert u.IKRetargetBatchOperation.run_batch_retarget(inputs)
        clip=u.load_asset(paths[-1])
        assert isinstance(clip,u.AnimSequence) and clip.get_editor_property('skeleton')==target.skeleton
        assert abs(clip.sequence_length-body.sequence_length)<.0001
        save(clip)
        pose=api.get_anim_pose_at_time(clip,0.,u.AnimPoseEvaluationOptions(optional_skeletal_mesh=target,evaluation_type=u.AnimDataEvalType.RAW))
        points={n:list(api.get_bone_pose(pose,n,u.AnimPoseSpaces.WORLD).translation.to_tuple())
                for n in ('pelvis','head','thigh_l','calf_l','foot_l','ball_l','thigh_r','calf_r','foot_r','ball_r','hand_l','hand_r')}
        result.append({'name':name,'clip':clip.get_path_name(),'length':clip.sequence_length,'bones_cm':points})
    assert hashlib.sha256(source_file.read_bytes()).hexdigest()==source_sha
    return {'source_unchanged':True,'source_sha256':source_sha,'derivatives':result,
            'placement_and_contact_review':'PENDING'}
