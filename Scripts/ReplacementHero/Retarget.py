"""Retarget body clips into the isolated replacement hero folder."""
import os
import unreal as u,json
from pathlib import Path
B='/Game/SpaceSurvival/Licensed/HeroReplacement/Final';L=u.EditorAssetLibrary;T=u.AssetToolsHelpers.get_asset_tools()
target=u.load_asset(B+'/SK_SquirrelHeroReplacement')
PAIRS={'Spine':('spine_01','spine_03'),'Neck':('neck_01','neck_01'),'Head':('head','head'),'ClavicleL':('clavicle_l','clavicle_l'),'ClavicleR':('clavicle_r','clavicle_r'),'ArmL':('upperarm_l','hand_l'),'ArmR':('upperarm_r','hand_r'),'LegL':('thigh_l','ball_l'),'LegR':('thigh_r','ball_r')}
for side in ['l','r']:
 for finger in ['thumb','index','middle','ring','pinky']:PAIRS[finger+side]=(finger+'_01_'+side,finger+'_03_'+side)
def rig(name,mesh,pairs,pelvis='pelvis',root='root',ik=False):
 path=B+'/'+name
 if L.does_asset_exist(path):return u.load_asset(path)
 r=T.create_asset(name,B,u.IKRigDefinition,u.IKRigDefinitionFactory());c=u.IKRigController.get_controller(r);assert c.set_skeletal_mesh(mesh);c.set_retarget_root(pelvis);c.set_root_motion_bone(root)
 bones=set(map(str,u.AnimPoseExtensions.get_bone_names(u.AnimPoseExtensions.get_reference_pose(mesh.skeleton))))
 for chain,(start,end) in pairs.items():
  if start in bones and end in bones:c.add_retarget_chain(chain,start,end,'None')
 if ik:
  for side in ['l','r']:
   goal=str(c.add_new_goal('Foot_'+side,'ball_'+side));i=c.add_solver('/Script/IKRig.IKRigLimbSolver');c.set_start_bone('thigh_'+side,i);c.connect_goal_to_solver(goal,i);c.set_retarget_chain_goal('Leg'+side.upper(),goal)
 L.save_loaded_asset(r);return r

def set_chains(op,field,wanted):
 s=op.get_settings();arr=s.get_editor_property(field)
 for i,chain in enumerate(arr):
  values=wanted.get(str(chain.get_editor_property('target_chain_name')), {})
  for k,v in values.items():chain.set_editor_property(k,v)
  arr[i]=chain
 s.set_editor_property(field,arr);op.set_settings(s)
def retargeter(name,source,source_pairs,pelvis='pelvis',root='root',ground=True):
 path=B+'/'+name
 if L.does_asset_exist(path):return u.load_asset(path)
 sr=rig(name+'_Source',source,source_pairs,pelvis,root);tr=rig('IK_Replacement',target,PAIRS,ik=True)
 r=T.create_asset(name,B,u.IKRetargeter,u.IKRetargetFactory());c=u.IKRetargeterController.get_controller(r);S=u.RetargetSourceOrTarget.SOURCE;D=u.RetargetSourceOrTarget.TARGET
 c.set_ik_rig(S,sr);c.set_ik_rig(D,tr);c.set_preview_mesh(S,source);c.set_preview_mesh(D,target);c.add_default_ops()
 if ground:
  c.add_retarget_op('/Script/IKRig.IKRetargetIKChainsOp');c.add_retarget_op('/Script/IKRig.IKRetargetFloorConstraintOp')
 c.assign_ik_rig_to_all_ops(S,sr);c.assign_ik_rig_to_all_ops(D,tr);c.auto_map_chains(u.AutoMapChainType.EXACT,True)
 pose=c.create_retarget_pose('ReplacementAligned',D);c.set_current_retarget_pose(pose,D)
 upper=[n for pair in PAIRS.values() for n in pair if not n.startswith(('thigh','ball'))]
 c.auto_align_bones(list(dict.fromkeys(upper)),u.RetargetAutoAlignMethod.CHAIN_TO_CHAIN,D)
 c.snap_bone_to_ground('ball_l',D)
 for i in range(c.get_num_retarget_ops()):
  op=c.get_op_controller(i)
  if isinstance(op,u.IKRetargetFKChainsController):set_chains(op,'chains_to_retarget',{n:{'rotation_mode':u.FKChainRotationMode.ONE_TO_ONE} for n in PAIRS if n not in ['Spine','Neck']})
  elif isinstance(op,u.IKRetargetIKChainsController):set_chains(op,'chains_to_retarget',{n:{'enable_ik':True} for n in ['LegL','LegR']})
  elif isinstance(op,u.IKRetargetRunIKRigController):set_chains(op,'chains',{n:{'enable_ik':ground} for n in ['LegL','LegR']})
  elif isinstance(op,u.IKRetargetFloorConstraintController):set_chains(op,'chains_to_affect',{n:{'enable_floor_constraint':True,'alpha':1.,'maintain_height_offset':1.,'use_toes':True} for n in ['LegL','LegR']})
 L.save_loaded_asset(r);return r

def clip(source_path,name,source_mesh,rt):
 if L.does_asset_exist(B+'/'+name):return u.load_asset(B+'/'+name)
 a=u.AssetRegistryHelpers.get_asset_registry().get_asset_by_object_path(source_path+'.'+source_path.split('/')[-1]);assert a.is_valid(),source_path
 x=u.IKRetargetBatchOperationInputs()
 for k,v in dict(assets_to_retarget=[a],source_mesh=source_mesh,target_mesh=target,ik_retarget_asset=rt,search=source_path.split('/')[-1],replace=name,target_path=B,use_source_path=False,include_referenced_assets=False,overwrite_existing_files=False).items():x.set_editor_property(k,v)
 made=u.IKRetargetBatchOperation.run_batch_retarget(x);assert L.does_asset_exist(B+'/'+name),str(made)
 seq=u.load_asset(B+'/'+name);assert seq.get_editor_property('skeleton')==target.skeleton;L.save_loaded_asset(seq);print('RETARGETED',name,seq.sequence_length);return seq
source=u.load_asset('/Game/SpaceSurvival/Licensed/MocapSource/SK_Mannequin');rt=retargeter('RTG_Body',source,PAIRS)
for src,name in [('MOB1_Stand_Relaxed_Idle_v2_IPC','Body_Idle'),('MOB1_Walk_F_IPC','Body_Walk'),('MOB1_Jog_F_IPC','Body_Jog'),('MOB1_Run_F_IPC','Body_Run')]:clip('/Game/SpaceSurvival/Licensed/MocapSource/'+src,name,source,rt)
old=u.load_asset('/Game/SpaceSurvival/Licensed/Hero/SK_SquirrelHero')
oldpairs={'Spine':('Waist','Spine02'),'Neck':('NeckTwist01','NeckTwist02'),'Head':('Head','Head'),'ClavicleL':('L_Clavicle','L_Clavicle'),'ClavicleR':('R_Clavicle','R_Clavicle'),'ArmL':('L_Upperarm','L_Hand'),'ArmR':('R_Upperarm','R_Hand'),'LegL':('L_Thigh','L_ToeBase'),'LegR':('R_Thigh','R_ToeBase')}
rtseat=retargeter('RTG_Pilot',old,oldpairs,'Hip','Root',False);clip('/Game/SpaceSurvival/Licensed/Hero/A_SquirrelPilot','Body_Pilot',old,rtseat)
# The existing template supplies an unarmed full-body jump; split after native pose inspection.
jump=u.load_asset('/Game/SampleAnimationPack/Demo/Characters/Mannequins/Meshes/SKM_Manny')
jpairs=dict(PAIRS);jpairs['Spine']=('spine_01','spine_05');jpairs['Neck']=('neck_01','neck_02')
rtjump=retargeter('RTG_Jump',jump,jpairs,ground=False);clip('/Game/SampleAnimationPack/Demo/Characters/Mannequins/Animations/Manny/MM_Jump','Body_Jump',jump,rtjump)
print('BODY_RETARGET_READY')



clip('/Game/SampleAnimationPack/Demo/Characters/Mannequins/Animations/Manny/MM_Fall_Loop','Body_Air',jump,rtjump)
rtland=retargeter('RTG_Land',jump,jpairs,ground=True);clip('/Game/SampleAnimationPack/Demo/Characters/Mannequins/Animations/Manny/MM_Land','Body_Land',jump,rtland)

