import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Create a separate 48s diagnostic sweep on the exact Vexa proof skeleton."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Matrix,Quaternion
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025'
code=(Path(__file__).resolve().parent/'stress_vexa_distal_joints.py').read_text().split('for bone,axis,label,angle,focus in cases:')[0]
code=code.replace('Vexa_AxillaLocal_Proof.blend','Vexa_ContinuousDistal_Proof.blend')
code=code.replace("out=R/'VexaJointStress'","out=R/'VexaDistalRepair/NativeStress'")
exec(compile(code,'distal_sweep_setup','exec'))
for b in rig.pose.bones:b.rotation_mode='QUATERNION'
rows=[]
for index,(bone,axis,label,angle,focus) in enumerate(cases):
 for phase,pose_angle in ((0,0),(30,angle),(60,0),(120,0)):
  frame=1+index*120+phase
  for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
  bpy.context.view_layer.update()
  origin=rest[bone].translation
  rig.pose.bones[bone].matrix=Matrix.Translation(origin)@Quaternion(axis,math.radians(pose_angle)).to_matrix().to_4x4()@Matrix.Translation(-origin)@rest[bone]
  bpy.context.view_layer.update()
  for b in rig.pose.bones:
   b.keyframe_insert('location',frame=frame);b.keyframe_insert('rotation_quaternion',frame=frame);b.keyframe_insert('scale',frame=frame)
 rows.append({'index':index,'seconds':(index*120+30)/60,'bone':bone,'test':label,'angle':angle,'focus':focus})
rig.animation_data.action.name='REVIEW_Vexa_Distal_Stress_48s'
for layer in rig.animation_data.action.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
s.frame_start=1;s.frame_end=2881;s.render.fps=60
for row,case in zip(rows,cases):
 bone,axis,label,angle,focus=case
 s.frame_set(1+row['index']*120+30);bpy.context.view_layer.update()
 origin=rest[bone].translation
 expected=Matrix.Translation(origin)@Quaternion(axis,math.radians(angle)).to_matrix().to_4x4()@Matrix.Translation(-origin)@rest[bone]
 err=max(abs(rig.pose.bones[bone].matrix[r][c]-expected[r][c]) for r in range(4) for c in range(4))
 assert err<1e-4,(row,err)
 row['saved_animation_matrix_error']=err
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(D/'Vexa_DistalStress_48s.fbx'),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z')
(R/'VexaDistalRepair/NativeStress/Cases.json').write_text(json.dumps({'scope':'Diagnostic sweep; angles are samples, not certified anatomical limits','seconds':48,'cases':rows},indent=2))
print('DISTAL_STRESS_EXPORTED',len(rows),flush=True)
