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
CHARACTER='Vexa';assert CHARACTER in ('Roxie','Vexa','Jinx','Vesper')
SHOULDER=True
assert not SHOULDER or CHARACTER=='Vexa', 'One repair target: Vexa'
stem='Vexa_Underarm'
DELTOID=os.environ.get('SS_REVIEW_DELTOID')=='1'
O=R/('VexaDeltoidStudy' if DELTOID else 'VexaGirdleStudy');O.mkdir(exist_ok=True)
import forearm_markers
bpy.ops.wm.open_mainfile(filepath=str(P/'SourceAssets/CharacterWorkshop_20261021'/(CHARACTER+'_Character_Options.blend')),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');rig.animation_data_clear()
for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
replacement=tuple(CHARACTER+x for x in ('_Nude_Legs','_Nude_Torso','_Bottom'))
for n in replacement:
 ob=bpy.data.objects.get(n)
 if ob:bpy.data.objects.remove(ob,do_unlink=True)
old_rig=rig
with bpy.data.libraries.load(str(D/('Vexa_Deltoid_Study.blend' if DELTOID else 'Vexa_ShoulderGirdle_Study.blend')),link=False) as (a,b):
 b.objects=[n for n in a.objects if n in replacement or n==old_rig.name]
for ob in b.objects:s.collection.objects.link(ob)
bpy.context.view_layer.update()
rig=next(ob for ob in b.objects if ob.type=='ARMATURE')
for ob in s.objects:
 if ob==old_rig or ob.type!='MESH':continue
 world=ob.matrix_world.copy()
 if ob.parent==old_rig:ob.parent=rig;ob.matrix_world=world
 for mod in ob.modifiers:
  if mod.type=='ARMATURE':mod.object=rig
bpy.data.objects.remove(old_rig,do_unlink=True)
bpy.context.view_layer.update();forearm_markers.add(rig)
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_cavity=True
s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('LegMotionReview');s.world.color=(.035,.045,.055)
s.render.resolution_x=800;s.render.resolution_y=800;s.render.resolution_percentage=100;s.render.fps=60
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO'

# Hide hair only in this diagnostic session, preserving the saved character.
hidden=[]
for ob in s.objects:
 if ob.type=='MESH' and 'hair' in ob.name.casefold():ob.hide_render=True;hidden.append(ob.name)
report={'hidden_for_inspection':hidden,'captures':[]}
for t in (0,4,8,9.033333,12.2,16):
 s.frame_set(round(1+t*60));bpy.context.view_layer.update()
 chest=(rig.matrix_world@rig.pose.bones['spine_05'].matrix).to_quaternion()@(rig.matrix_world@rig.data.bones['spine_05'].matrix_local).to_quaternion().inverted()
 center=((rig.matrix_world@rig.pose.bones['upperarm_l'].matrix).translation+(rig.matrix_world@rig.pose.bones['upperarm_r'].matrix).translation)*.5
 for view,offset in [('front',Vector((0,-3,.15))),('back',Vector((0,3,.15))),('side',Vector((3,0,.15)))]:
  cam.data.ortho_scale=.9;cam.location=center+chest@offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'{t:g}_{view}.png');bpy.ops.render.render(write_still=True);report['captures'].append(s.render.filepath)
(O/'ReloadViews.json').write_text(json.dumps(report,indent=2));print('VEXA_GIRDLE_RELOAD_DONE',flush=True)
if '--video' in sys.argv:
 # Scale only this disposable scene's animation copies; saved study stays at60fps.
 actions={ob.animation_data.action for ob in s.objects if ob.animation_data and ob.animation_data.action}
 actions|={ob.data.shape_keys.animation_data.action for ob in s.objects if ob.type=='MESH' and ob.data.shape_keys and ob.data.shape_keys.animation_data and ob.data.shape_keys.animation_data.action}
 for action in actions:
  for layer in action.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for key in fc.keyframe_points:
       key.co.x=(key.co.x-1)*.4+1;key.handle_left.x=(key.handle_left.x-1)*.4+1;key.handle_right.x=(key.handle_right.x-1)*.4+1
      fc.update()
 s.render.resolution_x=640;s.render.resolution_y=640;s.render.fps=24;s.frame_start=1;s.frame_end=385
 s.render.image_settings.media_type='VIDEO';s.render.image_settings.file_format='FFMPEG';s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264';s.render.ffmpeg.constant_rate_factor='HIGH'
 for label,offset in [('Front',Vector((0,-3,.15))),('Back',Vector((0,3,.15)))]:
  cam.animation_data_clear()
  for f in range(1,386):
   s.frame_set(f);bpy.context.view_layer.update()
   chest=(rig.matrix_world@rig.pose.bones['spine_05'].matrix).to_quaternion()@(rig.matrix_world@rig.data.bones['spine_05'].matrix_local).to_quaternion().inverted()
   center=((rig.matrix_world@rig.pose.bones['upperarm_l'].matrix).translation+(rig.matrix_world@rig.pose.bones['upperarm_r'].matrix).translation)*.5
   cam.data.ortho_scale=1.05;cam.location=center+chest@offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.keyframe_insert('location',frame=f);cam.keyframe_insert('rotation_euler',frame=f)
  s.render.filepath=str(D/(('Vexa_Deltoid_' if DELTOID else 'Vexa_ShoulderGirdle_')+label+'.mp4'));bpy.ops.render.render(animation=True)
 print('VEXA_GIRDLE_MOTION_RENDERED',flush=True)
