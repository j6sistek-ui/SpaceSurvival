import os
from pathlib import Path
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Screen every frame for the reported elbow reversal and torso-relative arm reach.

These are rejection/inspection signals, not a claim of anatomical or visual quality.
The original motion is evaluated unchanged; the audit never clamps animation keys.
"""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
result={'policy':'Sideways reach stops at the torso frontal plane; overhead reach allows at most 10 degrees behind it. Inspect palm orientation separately. No source keys modified.', 'clips':[]}
control='--rejected-control' in sys.argv
for clip in (('g1_rejected_v8',) if control else ('g1','g2','b1','b2')):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=60
 path=R.parents[2]/'SourceAssets/ZeroGChoreography_20261025/FBX/A_F3_g1_Contact.fbx' if control else R/'SourceBaseline'/f'A_F3_Baseline_{clip}_Source_Anim.fbx'
 bpy.ops.import_scene.fbx(filepath=str(path))
 rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');act=rig.animation_data.action
 rest={b.name:rig.matrix_world@b.matrix_local for b in rig.data.bones}
 hinge={}
 for side in ('l','r'):
  a,b,c=[rest[n+'_'+side] for n in ('upperarm','lowerarm','hand')]
  hinge[side]=a.to_quaternion().inverted()@(b.translation-a.translation).cross(c.translation-b.translation).normalized()
 row={'clip':clip,'frames':0,'elbow_reversal_frames':0,'rear_reach_frames':0,'max_rear_degrees':0,'worst':[]}
 for f in range(round(act.frame_range[0]),round(act.frame_range[1])+1):
  bpy.context.scene.frame_set(f);p={n:rig.matrix_world@rig.pose.bones[n].matrix for n in ['pelvis','head','spine_05','upperarm_l','upperarm_r','lowerarm_l','lowerarm_r','hand_l','hand_r']}
  # Use the upper chest's rotation, not head-to-pelvis direction: head tilts and
  # deep torso bends otherwise move the diagnostic frame independently of the chest.
  chest=p['spine_05'].to_quaternion()@rest['spine_05'].to_quaternion().inverted()
  up=chest@Vector((0,0,1));forward=chest@Vector((0,-1,0))
  flipped=False;rear=False
  for side in ('l','r'):
   a,b,c=[p[n+'_'+side] for n in ('upperarm','lowerarm','hand')]
   upper=(b.translation-a.translation).normalized();lower=(c.translation-b.translation).normalized();h=upper.cross(lower)
   flex=math.degrees(upper.angle(lower));alignment=1.0
   if h.length>.1:alignment=(a.to_quaternion().inverted()@h.normalized()).dot(hinge[side])
   back=math.degrees(math.asin(max(-1,min(1,-upper.dot(forward)))))
   limit=10 if upper.dot(up)>0 else 0
   flipped|=alignment<0 and flex>10
   rear|=back>limit+2
   row['max_rear_degrees']=max(row['max_rear_degrees'],back)
   score=max(0,back-limit)+max(0,-alignment)*90
   row['worst'].append({'time':(f-act.frame_range[0])/60,'side':side,'elbow_flex_deg':flex,'hinge_alignment':alignment,'rear_deg':back,'overhead':upper.dot(up)>0,'score':score})
  row['frames']+=1;row['elbow_reversal_frames']+=flipped;row['rear_reach_frames']+=rear
 row['worst']=sorted(row['worst'],key=lambda x:x['score'],reverse=True)[:8]
 row['screening_pass']=row['elbow_reversal_frames']==0 and row['rear_reach_frames']==0
 result['clips'].append(row);print('ARM_SCREEN',clip,{k:v for k,v in row.items() if k!='worst'},flush=True)
(R/('RejectedControlArmScreen.json' if control else 'BaselineArmScreen.json')).write_text(json.dumps(result,indent=2))
if control:assert result['clips'][0]['elbow_reversal_frames']>0,'Screen failed to catch known backwards elbow'
