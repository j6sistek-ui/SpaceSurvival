import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

import bpy,json,math
from pathlib import Path
from mathutils import Vector
report=[]
for clip in ('g1','g2','b1','b2'):
 bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.render.fps=60
 bpy.ops.import_scene.fbx(filepath=str(R/'SourceBaseline'/f'A_F3_Baseline_{clip}_Source_Anim.fbx'))
 rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');act=rig.animation_data.action
 names=['pelvis','spine_05','upperarm_r','lowerarm_r','hand_r','middle_01_r','index_01_r','pinky_01_r','upperarm_l','lowerarm_l','hand_l','middle_01_l','index_01_l','pinky_01_l','foot_r','foot_l','ball_r','ball_l','head']
 rest={b.name:rig.matrix_world@b.matrix_local for b in rig.data.bones}
 frames=[]
 for f in range(round(act.frame_range[0]),round(act.frame_range[1])+1):
  scene.frame_set(f);m={n:rig.matrix_world@rig.pose.bones[n].matrix for n in names}
  frames.append({'t':(f-act.frame_range[0])/60,'p':{n:list(a.translation) for n,a in m.items()},'q':{n:list(a.to_quaternion()) for n,a in m.items()}})
 (R/'SourceComparison'/f'{clip}_kinematics.json').write_text(json.dumps({'rest':{n:list(m.translation) for n,m in rest.items()},'frames':frames},separators=(',',':')))
 row={'clip':clip,'seconds':len(frames)/60,'hands':{}}
 for side in ('l','r'):
  name='hand_'+side
  values=[Vector(f['p'][name]) for f in frames]
  steps=[(b-a).length*60 for a,b in zip(values,values[1:])]
  row['hands'][side]={'min':[min(v[i] for v in values) for i in range(3)],'max':[max(v[i] for v in values) for i in range(3)],'max_speed':max(steps),'max_time':steps.index(max(steps))/60}
 report.append(row)
(R/'SourceComparison/ContactAnalysis.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
