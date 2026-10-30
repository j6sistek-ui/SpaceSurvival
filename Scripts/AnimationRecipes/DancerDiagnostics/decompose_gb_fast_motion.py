import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Distinguish segment-direction change from rapid axial rotation."""
import bpy,json,math
from pathlib import Path
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
bpy.ops.wm.open_mainfile(filepath=str(D/'GB_ShoulderResponse_ActionLibrary.blend'),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
pairs={f'{a}_{side}':f'{b}_{side}' for side in ('l','r') for a,b in [('upperarm','lowerarm'),('lowerarm','hand'),('thigh','calf'),('calf','foot')]}
axes={n:(rig.data.bones[n].matrix_local.inverted()@rig.data.bones[end].head_local).normalized() for n,end in pairs.items()};report=[]
for clip in ('g1','g2','b1','b2'):
 action=bpy.data.actions['A_F3_ShoulderResponse_'+clip];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];rows=[];prev={}
 for frame in range(round(action.frame_range[0]),round(action.frame_range[1])+1):
  s.frame_set(frame)
  for n,axis in axes.items():
   q=rig.pose.bones[n].matrix_basis.to_quaternion().normalized();v=q@axis
   if n in prev:
    pq,pv=prev[n];step=math.degrees(q.rotation_difference(pq).angle);step=min(step,360-step);swing=math.degrees(v.angle(pv))
    if step>5:rows.append({'frame':frame,'bone':n,'step':step,'direction_change':swing})
   prev[n]=(q.copy(),v.copy())
 rows.sort(key=lambda r:r['step'],reverse=True);report.append({'clip':clip,'worst':rows[:30]});print('DIRECTION_COMPONENT',clip,rows[:5],flush=True)
(R/'GBFingerShape/FastMotionDecomposition.json').write_text(json.dumps(report,indent=2))
