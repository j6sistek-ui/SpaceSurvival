import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Fresh saved-proof CPU-only inspection; owner original files are read-only."""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025';O=R/'VexaShoulderGarmentControl';O.mkdir(parents=True,exist_ok=True)
path=D/'Vexa_ShoulderBalanced_Proof.blend';before=hashlib.sha256(path.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False);s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
s.render.engine='CYCLES';s.cycles.device='GPU';s.cycles.samples=96;s.cycles.use_denoising=True;s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_x=1000;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
assert any(d.type=='OPTIX' for d in prefs.devices), 'OptiX unavailable'
for d in prefs.devices:d.use=d.type=='OPTIX'
print('GPU_DEVICES',[(d.name,d.type,d.use) for d in prefs.devices],flush=True)
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.95
lights=[]
for energy,size in ((110,1.4),(65,1.8)):
 bpy.ops.object.light_add(type='AREA');li=bpy.context.object;li.data.energy=energy;li.data.shape='DISK';li.data.size=size;lights.append(li)
def camera(offset):
 chest=(rig.matrix_world@rig.pose.bones['spine_05'].matrix).to_quaternion()@(rig.matrix_world@rig.data.bones['spine_05'].matrix_local).to_quaternion().inverted();center=((rig.matrix_world@rig.pose.bones['upperarm_l'].matrix).translation+(rig.matrix_world@rig.pose.bones['upperarm_r'].matrix).translation)*.5
 cam.location=center+chest@offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
 for li,off in zip(lights,(Vector((-1,1.5,1.7)),Vector((1,-1,1)))):
  li.location=center+chest@off;li.rotation_euler=(center-li.location).to_track_quat('-Z','Y').to_euler()
report={'proof_sha256':before,'engine':'Cycles OptiX, 96 samples, denoised','views':[],'status':'PRIVATE; visual review and native validation remain open'}
bpy.data.objects['Vexa_Top'].hide_render=True
for sec in (4,9.033333):
 s.frame_set(round(1+sec*60));bpy.context.view_layer.update()
 for view,off in [('left_quarter',Vector((2,-2,.15))),('right_quarter',Vector((-2,-2,.15)))]:
  camera(off);s.render.filepath=str(O/f'{sec:g}_{view}.png');bpy.ops.render.render(write_still=True);report['views'].append(s.render.filepath)
assert hashlib.sha256(path.read_bytes()).hexdigest()==before
(O/'Report.json').write_text(json.dumps(report,indent=2));print('BALANCED_GPU_VIEWS_DONE',flush=True)
