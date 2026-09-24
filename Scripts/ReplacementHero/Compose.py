"""Bake body animation and only the seven authored tail tracks onto one skeleton."""
import os
import unreal as u,json
from pathlib import Path
B='/Game/SpaceSurvival/Licensed/HeroReplacement/Final';L=u.EditorAssetLibrary
mesh=u.load_asset(B+'/SK_SquirrelHeroReplacement');bones=list(u.AnimPoseExtensions.get_bone_names(u.AnimPoseExtensions.get_reference_pose(mesh.skeleton)))
recipes=[('Idle','Idle','Idle',12.2666667),('Walk','Walk','Walk',1.2),('Jog','Jog','Run',.8),('Run','Run','Run',.5666667),('Pilot','Pilot',None,4),('JumpStart','Jump','JumpStart',.3),('JumpAir','Air','JumpAir',.8),('JumpLand','Land','JumpLand',.8666667)]
report=[]
for name,bodyname,tailname,duration in recipes:
 body=u.load_asset(B+'/Body_'+bodyname);tail=u.load_asset(B+'/Tail_'+tailname) if tailname else None
 dst=B+'/A_'+name
 if L.does_asset_exist(dst):
  existing=u.load_asset(dst);assert existing.get_editor_property('skeleton')==mesh.skeleton,dst
  continue
 factory=u.AnimSequenceFactory();factory.target_skeleton=mesh.skeleton;factory.preview_skeletal_mesh=mesh
 seq=u.AssetToolsHelpers.get_asset_tools().create_asset('A_'+name,B,u.AnimSequence,factory);c=seq.get_editor_property('controller');frames=round(duration*30)
 c.open_bracket('Compose body and isolated tail tracks',False);c.set_frame_rate(u.FrameRate(30,1),False);c.set_number_of_frames(u.FrameNumber(frames),False)
 for bone in bones:
  is_tail=str(bone).startswith('tail_');keys=[]
  for frame in range(frames+1):
   phase=frame/frames
   if is_tail and tail:
    clip=tail;t=phase*tail.sequence_length
   else:
    clip=body
    if name=='Idle':t=(phase*2%1)*body.sequence_length
    elif name=='JumpStart':t=phase*.25
    else:t=phase*body.sequence_length
   keys.append(u.AnimationLibrary.get_bone_pose_for_time(clip,bone,t,False))
  c.add_bone_curve(bone,False)
  assert c.set_bone_track_keys(bone,[k.translation for k in keys],[k.rotation for k in keys],[k.scale3d for k in keys],False),str(bone)
 c.close_bracket(False);L.save_loaded_asset(seq)
 report.append({'name':name,'body':body.get_path_name(),'tail':tail.get_path_name() if tail else None,'duration':seq.sequence_length,'bones':len(bones)})
 print('COMPOSED',name,seq.sequence_length)
(Path(os.environ['SS_HERO_SOURCE'])/'composed_clips.json').write_text(json.dumps(report,indent=2))
