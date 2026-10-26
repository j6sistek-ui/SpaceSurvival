import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Opposing views of the nominated Butterfly ankle; keep originals unchanged."""
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025';O=R/'ZeroGSharedHip/AnklePeak';O.mkdir(exist_ok=True)
source=D/'Vexa_ZeroG_SharedHip_Proof.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False);s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
name='A_F3_Coordinated_ZeroG_03_Butterfly';a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
for n,act in json.loads(s['zero_g_curve_pairs'])[name].items():
 keys=bpy.data.objects[n].data.shape_keys;keys.animation_data.action=bpy.data.actions[act];keys.animation_data.action_slot=keys.animation_data.action.slots[0]
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.55,.55,.55);s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('AnkleInspection');s.world.color=(.035,.045,.055)
s.render.resolution_x=s.render.resolution_y=640;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.65
rows=[]
for f in (440,461,474,492,510):
 s.frame_set(f);bpy.context.view_layer.update();bone=rig.pose.bones['foot_l'];center=rig.matrix_world@bone.head;basis=(rig.matrix_world@bone.parent.matrix).to_quaternion()
 for label,d in [('front',(0,-2,.6)),('side',(2,0,.6))]:
  cam.location=center+basis@Vector(d);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'{f}_{label}.png');bpy.ops.render.render(write_still=True)
 rows.append({'frame':f,'foot_local_quaternion':list(bone.matrix_basis.to_quaternion()),'foot_world':list(center),'calf_world':list(rig.matrix_world@bone.parent.head),'ball_world':list(rig.matrix_world@rig.pose.bones['ball_l'].head)})
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(O/'Report.json').write_text(json.dumps({'source_sha256':digest,'poses':rows},indent=2));print('ANKLE_PEAK_DONE',flush=True)
