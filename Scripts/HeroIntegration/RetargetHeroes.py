"""Retarget installed locomotion, jumps and pilot clips onto each imported hero's own skeleton."""
import json
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'.agent/local/HeroIntegration_20261020';BASE='/Game/SpaceSurvival/Licensed/PlayableHeroes_20261020';L=u.EditorAssetLibrary;T=u.AssetToolsHelpers.get_asset_tools()
REPORT={'heroes':{},'source_assets_edited':False}
def persist():(OUT/'RetargetReceipt.json').write_text(json.dumps(REPORT,indent=2))
def pairs(mesh):
    names=set(map(str,u.AnimPoseExtensions.get_bone_names(u.AnimPoseExtensions.get_reference_pose(mesh.skeleton))))
    p={'Spine':('spine_01','spine_05' if 'spine_05' in names else 'spine_03'),'Neck':('neck_01','neck_02' if 'neck_02' in names else 'neck_01'),'Head':('head','head')}
    for side in ['l','r']:
        p['Clavicle'+side]=('clavicle_'+side,'clavicle_'+side);p['Arm'+side]=('upperarm_'+side,'hand_'+side);p['Leg'+side]=('thigh_'+side,'ball_'+side)
        for f in ['thumb','index','middle','ring','pinky']:p[f+side]=(f+'_01_'+side,f+'_03_'+side)
    return p
def rig(folder,name,mesh,chains,pelvis='pelvis',root='root',ik=False):
    path=folder+'/'+name
    if L.does_asset_exist(path):return L.load_asset(path)
    r=T.create_asset(name,folder,u.IKRigDefinition,u.IKRigDefinitionFactory());c=u.IKRigController.get_controller(r);assert c.set_skeletal_mesh(mesh);assert c.set_retarget_root(pelvis);c.set_root_motion_bone(root)
    names=set(map(str,u.AnimPoseExtensions.get_bone_names(u.AnimPoseExtensions.get_reference_pose(mesh.skeleton))))
    for label,(a,b) in chains.items():
        if a in names and b in names:c.add_retarget_chain(label,a,b,'None')
    if ik:
        for side in ['l','r']:
            goal=str(c.add_new_goal('Foot_'+side,'ball_'+side));i=c.add_solver('/Script/IKRig.IKRigLimbSolver');c.set_start_bone('thigh_'+side,i);c.connect_goal_to_solver(goal,i);c.set_retarget_chain_goal('Leg'+side,goal)
    assert L.save_loaded_asset(r,False);return r
def settings(op,field,wanted):
    s=op.get_settings();arr=s.get_editor_property(field)
    for i,chain in enumerate(arr):
        for k,v in wanted.get(str(chain.get_editor_property('target_chain_name')),{}).items():chain.set_editor_property(k,v)
        arr[i]=chain
    s.set_editor_property(field,arr);op.set_settings(s)
def retargeter(folder,name,source,target,target_rig,source_pairs,pelvis='pelvis',root='root',ground=True):
    path=folder+'/'+name
    if L.does_asset_exist(path):return L.load_asset(path)
    sr=rig(folder,name+'_Source',source,source_pairs,pelvis,root);r=T.create_asset(name,folder,u.IKRetargeter,u.IKRetargetFactory());c=u.IKRetargeterController.get_controller(r);S=u.RetargetSourceOrTarget.SOURCE;D=u.RetargetSourceOrTarget.TARGET
    c.set_ik_rig(S,sr);c.set_ik_rig(D,target_rig);c.set_preview_mesh(S,source);c.set_preview_mesh(D,target);c.add_default_ops()
    if ground:c.add_retarget_op('/Script/IKRig.IKRetargetIKChainsOp');c.add_retarget_op('/Script/IKRig.IKRetargetFloorConstraintOp')
    c.assign_ik_rig_to_all_ops(S,sr);c.assign_ik_rig_to_all_ops(D,target_rig);c.auto_map_chains(u.AutoMapChainType.EXACT,True)
    pose=c.create_retarget_pose('UpperBodyAligned',D);c.set_current_retarget_pose(pose,D)
    upper=[bone for label,chain in pairs(target).items() if not label.startswith('Leg') for bone in chain]
    c.auto_align_bones(list(dict.fromkeys(upper)),u.RetargetAutoAlignMethod.CHAIN_TO_CHAIN,D)
    if ground:c.snap_bone_to_ground('ball_l',D)
    for i in range(c.get_num_retarget_ops()):
        op=c.get_op_controller(i)
        if isinstance(op,u.IKRetargetFKChainsController):settings(op,'chains_to_retarget',{n:{'rotation_mode':u.FKChainRotationMode.ONE_TO_ONE} for n in pairs(target) if n not in ['Spine','Neck']})
        elif isinstance(op,u.IKRetargetIKChainsController):settings(op,'chains_to_retarget',{'Leg'+side:{'enable_ik':True} for side in ['l','r']})
        elif isinstance(op,u.IKRetargetRunIKRigController):settings(op,'chains',{'Leg'+side:{'enable_ik':ground} for side in ['l','r']})
        elif isinstance(op,u.IKRetargetFloorConstraintController):settings(op,'chains_to_affect',{'Leg'+side:{'enable_floor_constraint':True,'alpha':1.,'maintain_height_offset':1.,'use_toes':True} for side in ['l','r']})
    assert L.save_loaded_asset(r,False);return r
def clip(folder,name,src,source,target,rt):
    dst=folder+'/'+name
    if L.does_asset_exist(dst):return L.load_asset(dst)
    reg=u.AssetRegistryHelpers.get_asset_registry();data=reg.get_asset_by_object_path(src+'.'+src.rsplit('/',1)[-1]);assert data.is_valid(),src
    inp=u.IKRetargetBatchOperationInputs()
    for k,v in {'assets_to_retarget':[data],'source_mesh':source,'target_mesh':target,'ik_retarget_asset':rt,'search':src.rsplit('/',1)[-1],'replace':name,'target_path':folder,'use_source_path':False,'include_referenced_assets':False,'overwrite_existing_files':False}.items():inp.set_editor_property(k,v)
    made=u.IKRetargetBatchOperation.run_batch_retarget(inp);asset=L.load_asset(dst);assert isinstance(asset,u.AnimSequence),(dst,str(made));assert asset.get_editor_property('skeleton')==target.skeleton;assert L.save_loaded_asset(asset,False);return asset
source=L.load_asset('/Game/SpaceSurvival/Licensed/MocapSource/SK_Mannequin');assert source
jump=L.load_asset('/Game/SampleAnimationPack/Demo/Characters/Mannequins/Meshes/SKM_Manny');assert jump
pilot=L.load_asset('/Game/SpaceSurvival/Licensed/Hero/SK_SquirrelHero');assert pilot
oldpairs={'Spine':('Waist','Spine02'),'Neck':('NeckTwist01','NeckTwist02'),'Head':('Head','Head'),'Claviclel':('L_Clavicle','L_Clavicle'),'Clavicler':('R_Clavicle','R_Clavicle'),'Arml':('L_Upperarm','L_Hand'),'Armr':('R_Upperarm','R_Hand'),'Legl':('L_Thigh','L_ToeBase'),'Legr':('R_Thigh','R_ToeBase')}
for key in ['EX7','Green','Blue','Cloth']:
    folder=BASE+'/'+key;target=L.load_asset(folder+'/SK_'+key);assert target
    target_rig=rig(folder,'IK_'+key,target,pairs(target),ik=True)
    body_rt=retargeter(folder,'RTG_Body',source,target,target_rig,pairs(source));jump_rt=retargeter(folder,'RTG_Jump',jump,target,target_rig,pairs(jump),ground=False);land_rt=retargeter(folder,'RTG_Land',jump,target,target_rig,pairs(jump));pilot_rt=retargeter(folder,'RTG_Pilot',pilot,target,target_rig,oldpairs,'Hip','Root',False)
    made=[]
    for src,name in [('MOB1_Stand_Relaxed_Idle_v2_IPC','Idle'),('MOB1_Walk_F_IPC','Walk'),('MOB1_Jog_F_IPC','Jog'),('MOB1_Run_F_IPC','Run')]:
        a=clip(folder,'A_'+name,'/Game/SpaceSurvival/Licensed/MocapSource/'+src,source,target,body_rt);made.append({'clip':name,'path':a.get_path_name(),'seconds':a.sequence_length})
    for src,name,rt in [('MM_Jump','JumpStart',jump_rt),('MM_Fall_Loop','JumpAir',jump_rt),('MM_Land','JumpLand',land_rt)]:
        a=clip(folder,'A_'+name,'/Game/SampleAnimationPack/Demo/Characters/Mannequins/Animations/Manny/'+src,jump,target,rt);made.append({'clip':name,'path':a.get_path_name(),'seconds':a.sequence_length})
    a=clip(folder,'A_Pilot','/Game/SpaceSurvival/Licensed/Hero/A_SquirrelPilot',pilot,target,pilot_rt);made.append({'clip':'Pilot','path':a.get_path_name(),'seconds':a.sequence_length})
    REPORT['heroes'][key]={'mesh':target.get_path_name(),'clips':made};persist();print('HERORETARGET|',key,'COMPLETE',len(made),flush=True)
persist();print('ALL_HERO_RETARGETS_READY',flush=True)
