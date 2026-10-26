import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Fresh reload review of the compact coordinated Vexa proof, with opposing motion."""
import bpy,json,sys,hashlib
from pathlib import Path
from mathutils import Vector
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025';O=R/'VexaAxillaMotion';O.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(R));import forearm_markers
path=D/'Vexa_AxillaLocal_Proof.blend';expected=hashlib.sha256(path.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');forearm_markers.add(rig)
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('Reload');s.world.color=(.035,.045,.055);s.render.resolution_x=800;s.render.resolution_y=800;s.render.resolution_percentage=100
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.95
def camera(offset):
 chest=(rig.matrix_world@rig.pose.bones['spine_05'].matrix).to_quaternion()@(rig.matrix_world@rig.data.bones['spine_05'].matrix_local).to_quaternion().inverted()
 center=((rig.matrix_world@rig.pose.bones['upperarm_l'].matrix).translation+(rig.matrix_world@rig.pose.bones['upperarm_r'].matrix).translation)*.5
 cam.location=center+chest@offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
rows=[]
for sec in ():
 s.frame_set(round(1+sec*60));bpy.context.view_layer.update()
 for view,offset in [('front',Vector((0,-3,.15))),('back',Vector((0,3,.15))),('side',Vector((3,-1,.15)))]:
  camera(offset);s.render.filepath=str(O/f'{sec:g}_{view}.png');bpy.ops.render.render(write_still=True);rows.append(s.render.filepath)
report={'proof_sha256':expected,'bones':len(rig.data.bones),'captures':rows,'motion':[],'status':'RENDERED, NOT OWNER ACCEPTED; neck/underarm and full quality remain open'}
if True:
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
 for view,offset in [('Front',Vector((0,-3,.15))),('Back',Vector((0,3,.15)))]:
  cam.animation_data_clear()
  for f in range(1,386):
   s.frame_set(f);bpy.context.view_layer.update();camera(offset);cam.keyframe_insert('location',frame=f);cam.keyframe_insert('rotation_euler',frame=f)
  s.render.filepath=str(D/f'Vexa_AxillaLocal_{view}.mp4');bpy.ops.render.render(animation=True);report['motion'].append(s.render.filepath)
assert hashlib.sha256(path.read_bytes()).hexdigest()==expected
(O/'Report.json').write_text(json.dumps(report,indent=2));print('COORDINATED_RELOAD_DONE',flush=True)
