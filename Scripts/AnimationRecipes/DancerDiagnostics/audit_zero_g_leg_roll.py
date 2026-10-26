import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Locate roll maxima and their knee geometry; no edits."""
import bpy,json,math
from pathlib import Path
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
bpy.ops.wm.open_mainfile(filepath=str(D/'ZeroG_Coordinated_ActionLibrary.blend'),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');rows=[]
for a in bpy.data.actions:
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];previous={};peaks={}
 for f in range(1,round(a.frame_range[1])+1):
  s.frame_set(f)
  for side in ('l','r'):
   t,c,foot=[rig.pose.bones[x+'_'+side] for x in ('thigh','calf','foot')];q=t.matrix_basis.to_quaternion();bend=math.degrees((c.matrix.translation-t.matrix.translation).angle(foot.matrix.translation-c.matrix.translation))
   if side in previous:
    diff=q.rotation_difference(previous[side]).angle;d=math.degrees(min(diff,2*math.pi-diff))
    if d>peaks.get(side,{}).get('step_deg',0):peaks[side]={'side':side,'frame':f,'step_deg':d,'knee_bend_deg':bend}
   previous[side]=q.copy()
 rows.append({'action':a.name,'peaks':peaks})
(R/'ZeroGJointBake/LegPeaks.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows),flush=True)
