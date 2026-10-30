import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Locate actual quaternion discontinuities; do not edit the action library."""
import bpy,json,math
from pathlib import Path
bpy.ops.wm.open_mainfile(filepath=str(R.parents[2]/'SourceAssets/DanceRefinement_20261025/Refined_ActionLibrary.blend'),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');report=[]
for clip in ('g1','g2','b1','b2'):
 act=bpy.data.actions['A_F3_Refined_'+clip];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 steps=[];previous={}
 for f in range(round(act.frame_range[0]),round(act.frame_range[1])+1):
  s.frame_set(f)
  for b in rig.pose.bones:
   q=b.matrix_basis.to_quaternion()
   if b.name in previous:
    a=math.degrees(q.rotation_difference(previous[b.name]).angle);a=min(a,360-a)
    if a>5:steps.append({'frame':f,'bone':b.name,'step_deg':a})
   previous[b.name]=q.copy()
 report.append({'clip':clip,'steps_over5':len(steps),'worst':sorted(steps,key=lambda x:x['step_deg'],reverse=True)[:12]})
(R/'VexaDistalRepair/GBRotationSteps.json').write_text(json.dumps(report,indent=2));print('GB_STEPS',json.dumps(report),flush=True)
