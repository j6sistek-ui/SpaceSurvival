import os
from pathlib import Path
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Set the animation's actual authored reference mesh; never change shared skeleton modes."""
import unreal as u,json,math,traceback
from pathlib import Path
B='/Game/SpaceSurvival/Licensed/CharacterWorkshop/Animations';report={'clips':[],'errors':[]}
try:
 assert 'CharacterWorkbench' in u.Paths.get_project_file_path()
 mesh=u.load_asset('/Game/XANDRA/Characters/F3/Base/Models/SK_F3_FullCharacter_Quinn_Base');assert mesh
 for n in ('g1','g2','b1','b2','G1_G2_Routine','B1_B2_Routine'):
  a=u.load_asset(B+'/A_F3_'+n);assert a
  options=u.AnimPoseEvaluationOptions();options.should_retarget=False;options.optional_skeletal_mesh=mesh
  rebuilt='_Routine' in n
  if rebuilt:
   first,second=('g1','g2') if n.startswith('G1') else ('b1','b2')
   ca=u.load_asset(B+'/A_F3_'+first);cb=u.load_asset(B+'/A_F3_'+second);tracks=u.AnimationLibrary.get_animation_track_names(ca)
   def rows(clip):
    result=[]
    for f in range(round(clip.sequence_length*25)+1):
     p=u.AnimPoseExtensions.get_anim_pose_at_time(clip,f/25,options)
     result.append({str(b):u.AnimPoseExtensions.get_bone_pose(p,b,u.AnimPoseSpaces.LOCAL) for b in tracks})
    return result
   aa=rows(ca);bb=rows(cb);offset=aa[-1]['pelvis'].translation-bb[0]['pelvis'].translation;offset.z=0
   for row in bb:
    t=row['pelvis'];t.translation=t.translation+offset;row['pelvis']=t
   bridge=[]
   for i in range(1,12):
    w=i/12;w=w*w*(3-2*w);row={}
    for b in tracks:
     x=aa[-1][str(b)];y=bb[0][str(b)]
     row[str(b)]=u.Transform(location=x.translation+(y.translation-x.translation)*w,rotation=u.MathLibrary.quat_slerp(x.rotation,y.rotation,w).rotator(),scale=x.scale3d+(y.scale3d-x.scale3d)*w)
    bridge.append(row)
   allrows=aa+bridge+bb;controller=a.get_editor_property('controller');controller.open_bracket('Rebuild from authored unretargeted source poses',False);controller.set_number_of_frames(u.FrameNumber(len(allrows)-1),False)
   for b in tracks:
    transforms=[r[str(b)] for r in allrows];assert controller.set_bone_track_keys(b,[t.translation for t in transforms],[t.rotation for t in transforms],[t.scale3d for t in transforms],False)
   controller.close_bracket(False)
  names=['pelvis','head','hand_l','hand_r','foot_l','foot_r','ball_l','ball_r']
  raw=[];times=[i*a.sequence_length/120 for i in range(121)]
  for t in times:
   p=u.AnimPoseExtensions.get_anim_pose_at_time(a,t,options);raw.append([u.AnimPoseExtensions.get_bone_pose(p,b,u.AnimPoseSpaces.WORLD).translation for b in names])
  a.set_retarget_source_asset(mesh);a.update_retarget_source_asset_data();u.EditorAssetLibrary.set_metadata_tag(a,'SS.RetargetRepair','2026-10-25: F3 authored reference mesh; shared mannequin retarget was applying a second proportion change')
  assert u.EditorAssetLibrary.save_loaded_asset(a)
  options.should_retarget=True;errors=[]
  for t,ex in zip(times,raw):
   p=u.AnimPoseExtensions.get_anim_pose_at_time(a,t,options)
   for name,e in zip(names,ex):
    v=u.AnimPoseExtensions.get_bone_pose(p,name,u.AnimPoseSpaces.WORLD).translation;errors.append(math.dist((v.x,v.y,v.z),(e.x,e.y,e.z)))
  report['clips'].append({'asset':a.get_path_name(),'seconds':a.sequence_length,'samples':len(errors),'max_retarget_delta_cm':max(errors),'key_data_changed':rebuilt});print('REPAIRED_REFERENCE',n,max(errors),flush=True)
 report['ok']=all(r['max_retarget_delta_cm']<.02 for r in report['clips'])
except Exception:report['errors'].append(traceback.format_exc())
(R/'ExistingRetargetRepair.json').write_text(json.dumps(report,indent=2));print('REPAIR_RESULT',report.get('ok',False),report['errors'],flush=True)
