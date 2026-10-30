import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Locate short rapid arm excursions for visual review, without changing keys."""
import bpy,json,math
from pathlib import Path
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
bpy.ops.wm.open_mainfile(filepath=str(D/'G2_ArmPassage_ActionLibrary.blend'),load_ui=False);s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
def angle(a,b):return math.degrees(2*math.acos(min(1,abs(a.dot(b)))))
report=[]
for clip in ('g1','g2','b1','b2'):
 action=bpy.data.actions['A_F3_ArmPassage_g2' if clip=='g2' else 'A_F3_ShoulderResponse_'+clip];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];first,last=map(round,action.frame_range)
 poses={};names=[p+'_'+side for p in ('upperarm','lowerarm') for side in ('l','r')]
 for f in range(first,last+1):
  s.frame_set(f);poses[f]={n:rig.pose.bones[n].matrix_basis.to_quaternion().normalized() for n in names}
 for side in ('l','r'):
  bones=[p+'_'+side for p in ('upperarm','lowerarm')];steps={f:max(angle(poses[f][n],poses[f-1][n]) for n in bones) for f in range(first+1,last+1)}
  fast=[f for f,v in steps.items() if v>10];groups=[]
  for f in fast:
   if not groups or f-groups[-1][-1]>15:groups.append([f])
   else:groups[-1].append(f)
  for group in groups:
   a=max(first,min(group)-15);z=min(last,max(group)+15);peak=max(group,key=steps.get);row={'clip':clip,'side':side,'first':a,'last':z,'peak':peak,'peak_step':steps[peak],'bones':{}}
   for n in bones:
    arc=sum(angle(poses[f][n],poses[f-1][n]) for f in range(a+1,z+1));chord=angle(poses[a][n],poses[z][n]);row['bones'][n]={'arc':arc,'chord':chord,'ratio':arc/max(chord,1)}
   report.append(row)
(R/'GBFastPassage/RemainingArmEvents.json').write_text(json.dumps(report,indent=2));print('EVENTS',json.dumps(report),flush=True)
