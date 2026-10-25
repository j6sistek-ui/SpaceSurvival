import os
from pathlib import Path
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Read-only reload of the six adopted reference/concatenation repairs."""
import unreal as u,json,traceback,math
from pathlib import Path
P=R.parents[2]
report={'clips':[],'errors':[],'quality':'Reference/proportion check only; not motion acceptance'}
try:
 assert Path(u.Paths.get_project_file_path()).resolve()==P/'SpaceSurvival.uproject'
 mesh=u.load_asset('/Game/XANDRA/Characters/F3/Base/Models/SK_F3_FullCharacter_Quinn_Base');assert mesh
 for key in ('g1','g2','b1','b2','G1_G2_Routine','B1_B2_Routine'):
  anim=u.load_asset('/Game/SpaceSurvival/Licensed/CharacterWorkshop/Animations/A_F3_'+key);assert anim
  normal=u.AnimPoseEvaluationOptions();normal.optional_skeletal_mesh=mesh
  raw=u.AnimPoseEvaluationOptions();raw.optional_skeletal_mesh=mesh;raw.should_retarget=False
  errors=[]
  for t in (0,anim.sequence_length*.5,anim.sequence_length):
   a=u.AnimPoseExtensions.get_anim_pose_at_time(anim,t,normal);b=u.AnimPoseExtensions.get_anim_pose_at_time(anim,t,raw)
   for n in ('pelvis','head','lowerarm_l','lowerarm_r','hand_l','hand_r','foot_l','foot_r'):
    x=u.AnimPoseExtensions.get_bone_pose(a,n,u.AnimPoseSpaces.WORLD).translation;y=u.AnimPoseExtensions.get_bone_pose(b,n,u.AnimPoseSpaces.WORLD).translation
    errors.append((x-y).length())
  report['clips'].append({'clip':key,'max_retarget_delta_cm':max(errors)});assert max(errors)<.01
 report['ok']=True
except Exception:report['errors'].append(traceback.format_exc())
(R/'OriginalRepairFreshReload.json').write_text(json.dumps(report,indent=2));print('ORIGINAL_RELOAD_RESULT',report,flush=True)
