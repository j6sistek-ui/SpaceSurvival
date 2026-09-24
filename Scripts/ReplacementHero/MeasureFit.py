import os
import unreal as u,json,statistics,builtins
from pathlib import Path
B='/Game/SpaceSurvival/Licensed/HeroReplacement/Final/';P=u.AnimPoseExtensions;opt=u.AnimPoseEvaluationOptions();m=u.load_asset(B+'SK_SquirrelHeroReplacement');scale=135/(m.get_bounds().box_extent.z*2);out={'scale':scale,'gaits':{}}
for n in ['Walk','Jog','Run']:
 a=u.load_asset(B+'A_'+n);dt=1/60;data=[]
 for i in range(round(a.sequence_length*60)+1):
  pose=P.get_anim_pose_at_time(a,min(i*dt,a.sequence_length),opt);data.append([P.get_bone_pose(pose,b,u.AnimPoseSpaces.WORLD).translation for b in ['ball_l','ball_r']])
 speeds=[]
 for side in range(2):
  zmin=min(v[side].z for v in data)
  for prev,curr in zip(data,data[1:]):
   if prev[side].z<zmin+2 and curr[side].z<zmin+2:
    dy=(curr[side].y-prev[side].y)/dt
    if dy< -5:speeds.append(abs(dy)*scale)
 out['gaits'][n]={'median_contact_speed_cm_s':statistics.median(speeds) if speeds else None,'samples':len(speeds)}
da=u.load_asset('/Game/SpaceSurvival/Data/DA_Phase1');hero=builtins.next(h for h in da.heroes if str(h.id)=='Squirrel');out['previous_definition']=hero.export_text()
old=u.load_asset(hero.pilot_clip_path);oldmesh=u.load_asset(hero.mesh_path);oldscale=hero.mesh_scale if hero.fit_height<=0 else hero.fit_height/(oldmesh.get_bounds().box_extent.z*2)
oldpose=P.get_anim_pose_at_time(old,0,opt);newpose=P.get_anim_pose_at_time(u.load_asset(B+'A_Pilot'),0,opt)
pold=P.get_bone_pose(oldpose,hero.pelvis_bone,u.AnimPoseSpaces.WORLD).translation*oldscale;pnew=P.get_bone_pose(newpose,'pelvis',u.AnimPoseSpaces.WORLD).translation*scale
rot=u.Rotator(yaw=hero.mesh_yaw);mount=u.MathLibrary.quat_rotate_vector(rot.quaternion(),pold-pnew)+hero.pilot_mount_offset;out['pilot_mount']=[mount.x,mount.y,mount.z]
(Path(os.environ['SS_HERO_SOURCE'])/'fit_measurements.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))



