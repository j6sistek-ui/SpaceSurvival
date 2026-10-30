import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Fresh saved-proof CPU-only inspection; owner original files are read-only."""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025';O=R/'VexaNape/Reload';O.mkdir(parents=True,exist_ok=True)
path=D/'Vexa_ShoulderBalanced_Proof.blend';before=hashlib.sha256(path.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False);s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=32;s.cycles.use_denoising=False;s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_x=800;s.render.resolution_y=800;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.95
lights=[]
for energy,size in ((110,1.4),(65,1.8)):
 bpy.ops.object.light_add(type='AREA');li=bpy.context.object;li.data.energy=energy;li.data.shape='DISK';li.data.size=size;lights.append(li)
def camera(offset):
 chest=(rig.matrix_world@rig.pose.bones['spine_05'].matrix).to_quaternion()@(rig.matrix_world@rig.data.bones['spine_05'].matrix_local).to_quaternion().inverted();center=((rig.matrix_world@rig.pose.bones['upperarm_l'].matrix).translation+(rig.matrix_world@rig.pose.bones['upperarm_r'].matrix).translation)*.5
 cam.location=center+chest@offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
 for li,off in zip(lights,(Vector((-1,1.5,1.7)),Vector((1,-1,1)))):
  li.location=center+chest@off;li.rotation_euler=(center-li.location).to_track_quat('-Z','Y').to_euler()
report={'proof_sha256':before,'engine':'Cycles CPU, four threads','views':[],'status':'PRIVATE; visual review and native validation remain open'}
for sec in (0,4,9.033333,12.2,16):
 s.frame_set(round(1+sec*60));bpy.context.view_layer.update()
 for view,off in [('front',Vector((0,-3,.15))),('back',Vector((0,3,.15)))]:
  camera(off);s.render.filepath=str(O/f'{sec:g}_{view}.png');bpy.ops.render.render(write_still=True);report['views'].append(s.render.filepath)
if '--video' in sys.argv:
 # Low-resource 12fps preview. Not evidence of final frame pacing.
 actions={o.animation_data.action for o in s.objects if o.animation_data and o.animation_data.action}
 actions|={o.data.shape_keys.animation_data.action for o in s.objects if o.type=='MESH' and o.data.shape_keys and o.data.shape_keys.animation_data and o.data.shape_keys.animation_data.action}
 for a in actions:
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for k in fc.keyframe_points:k.co.x=(k.co.x-1)*.2+1;k.handle_left.x=(k.handle_left.x-1)*.2+1;k.handle_right.x=(k.handle_right.x-1)*.2+1
      fc.update()
 for f in range(1,194):
  s.frame_set(f);bpy.context.view_layer.update();camera(Vector((0,3,.15)))
  for o in (cam,*lights):o.keyframe_insert('location',frame=f);o.keyframe_insert('rotation_euler',frame=f)
 s.render.resolution_x=480;s.render.resolution_y=480;s.cycles.samples=8;s.render.fps=12;s.frame_start=1;s.frame_end=193;s.render.image_settings.media_type='VIDEO';s.render.image_settings.file_format='FFMPEG';s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264';s.render.ffmpeg.constant_rate_factor='HIGH';s.render.filepath=str(D/'Vexa_ShoulderBalanced_Back_CPU.mp4');bpy.ops.render.render(animation=True);report['motion']=s.render.filepath;report['motion_fps']=12
assert hashlib.sha256(path.read_bytes()).hexdigest()==before
(O/'Report.json').write_text(json.dumps(report,indent=2));print('BALANCED_CPU_RELOAD_DONE',flush=True)
