import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Compare fast motion in native FK baseline and current private derivative."""
import bpy,json,math
from pathlib import Path
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
report=[]
def scan(rig,action):
 s=bpy.context.scene;rig.animation_data_create();rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
 rows=[];prev={};rest={b.name:[list(row) for row in b.matrix_local] for b in rig.data.bones};poses={}
 for f in range(round(action.frame_range[0]),round(action.frame_range[1])+1):
  s.frame_set(f)
  for pb in rig.pose.bones:
   if not pb.name.startswith(('upperarm_','lowerarm_','calf_','thigh_','neck_','spine_')) or 'twist' in pb.name:continue
   q=pb.matrix_basis.to_quaternion()
   if pb.name in prev:
    a=math.degrees(q.rotation_difference(prev[pb.name]).angle);a=min(a,360-a)
    if a>5:rows.append({'frame':f,'bone':pb.name,'step_deg':a})
   prev[pb.name]=q.copy()
  if 65<=f<=100:
   poses[f]={n:{'q':list(rig.pose.bones[n].matrix_basis.to_quaternion()),'world_head':list(rig.matrix_world@rig.pose.bones[n].head)} for n in ('upperarm_r','lowerarm_r','hand_r','spine_05')}
 rows.sort(key=lambda x:x['step_deg'],reverse=True)
 return {'range':list(action.frame_range),'fps':s.render.fps,'steps_over5':len(rows),'worst':rows[:16],'g2_event_poses':poses},rest
for clip in ('g1','g2','b1','b2'):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=60
 bpy.ops.import_scene.fbx(filepath=str(R/'SourceBaseline'/f'A_F3_Baseline_{clip}_Source_Anim.fbx'))
 rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');a,ar=scan(rig,rig.animation_data.action)
 bpy.ops.wm.open_mainfile(filepath=str(D/'GB_ShoulderResponse_ActionLibrary.blend'),load_ui=False)
 rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');b,br=scan(rig,bpy.data.actions['A_F3_ShoulderResponse_'+clip])
 assert set(ar)==set(br),(len(ar),len(br))
 delta=max(abs(ar[n][i][j]-br[n][i][j]) for n in ar for i in range(4) for j in range(4))
 report.append({'clip':clip,'rest_matrix_error':delta,'baseline':a,'current':b});print('FAST_ORIGIN',clip,delta,a['worst'][:2],b['worst'][:2],flush=True)
(R/'GBFingerShape/FastMotionOrigin.json').write_text(json.dumps(report,indent=2));print('FAST_ORIGIN_DONE',flush=True)
