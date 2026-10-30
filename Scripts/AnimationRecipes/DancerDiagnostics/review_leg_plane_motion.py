import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Full character and opposing close-ups of the isolated leg-plane proof."""
import bpy,sys,math,json,os
from pathlib import Path
from mathutils import Vector,Matrix
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025'
CHARACTER=os.environ.get('SS_REVIEW_CHARACTER','Roxie');assert CHARACTER in ('Roxie','Vexa','Jinx','Vesper')
SHOULDER=os.environ.get('SS_REVIEW_SHOULDER')=='1'
assert not SHOULDER or CHARACTER=='Vexa', 'One repair target: Vexa'
stem='Vexa_Shoulder' if SHOULDER else CHARACTER+'_LegPlane'
O=R/('VexaShoulderProof' if SHOULDER else 'LegPlaneHipProof'+('' if CHARACTER=='Roxie' else '_'+CHARACTER));O.mkdir(exist_ok=True)
import forearm_markers
bpy.ops.wm.open_mainfile(filepath=str(P/'SourceAssets/CharacterWorkshop_20261021'/(CHARACTER+'_Character_Options.blend')),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');rig.animation_data_clear()
for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
replacement=tuple(CHARACTER+x for x in ('_Nude_Legs','_Nude_Torso','_Bottom'))
for n in replacement:
 ob=bpy.data.objects.get(n)
 if ob:bpy.data.objects.remove(ob,do_unlink=True)
with bpy.data.libraries.load(str(D/(stem+'_Proof.blend')),link=False) as (a,b):
 b.objects=list(replacement);b.actions=['A_F3_Vexa_Shoulder_ZeroG_02_Spiral' if SHOULDER else 'A_F3_LegPlane_ZeroG_02_Spiral']
for ob in b.objects:
 s.collection.objects.link(ob);world=ob.matrix_world.copy();ob.parent=rig;ob.matrix_world=world
 for mod in ob.modifiers:
  if mod.type=='ARMATURE':mod.object=rig;mod.use_deform_preserve_volume=False
act=b.actions[0];rig.animation_data_create();rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
bpy.context.view_layer.update();forearm_markers.add(rig)
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_cavity=True
s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('LegMotionReview');s.world.color=(.035,.045,.055)
s.render.resolution_x=800;s.render.resolution_y=800;s.render.resolution_percentage=100;s.render.fps=60
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO'
for t in (0,4,6,8,9.033333,9.5,10.066667,12.2,14,16):
 s.frame_set(round(t*60)+1);bpy.context.view_layer.update()
 h,k,a=[(rig.matrix_world@rig.pose.bones[n].matrix).translation for n in ('thigh_l','calf_l','foot_l')]
 normal=(k-h).cross(a-k).normalized();pelvis=(rig.matrix_world@rig.pose.bones['pelvis'].matrix).translation
 views=[('body_front',pelvis,2.4,Vector((0,-6,1))),('body_back',pelvis,2.4,Vector((0,6,1)))]
 if 8<=t<=10.1:views += [('knee_outer',k,.72,normal*3),('knee_inner',k,.72,-normal*3)]
 for view,center,scale,delta in views:
  cam.data.ortho_scale=scale;cam.location=center+delta;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'{t:g}_{view}.png');bpy.ops.render.render(write_still=True)
if '--video' in sys.argv:
 # Continuous diagnostic keeps the body large; camera follows pelvis only.
 s.render.resolution_x=640;s.render.resolution_y=800;cam.data.ortho_scale=2.7
 actions={act}|{ob.data.shape_keys.animation_data.action for ob in s.objects if ob.type=='MESH' and ob.data.shape_keys and ob.data.shape_keys.animation_data and ob.data.shape_keys.animation_data.action}
 for action in actions:
  for layer in action.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for key in fc.keyframe_points:
       key.co.x=(key.co.x-1)*.4+1;key.handle_left.x=(key.handle_left.x-1)*.4+1;key.handle_right.x=(key.handle_right.x-1)*.4+1
      fc.update()
 for f in range(1,386):
  s.frame_set(f);center=(rig.matrix_world@rig.pose.bones['pelvis'].matrix).translation
  cam.location=center+Vector((4,-6,1.5));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.keyframe_insert('location',frame=f);cam.keyframe_insert('rotation_euler',frame=f)
 s.render.fps=24;s.frame_start=1;s.frame_end=385
 s.render.image_settings.media_type='VIDEO';s.render.image_settings.file_format='FFMPEG';s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264';s.render.ffmpeg.constant_rate_factor='MEDIUM';s.render.filepath=str(D/(stem+'_MotionReview.mp4'));bpy.ops.render.render(animation=True)
print('LEG_PLANE_MOTION_REVIEW_DONE',flush=True)
