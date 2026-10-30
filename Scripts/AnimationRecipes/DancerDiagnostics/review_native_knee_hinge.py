import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Isolate mesh/weights from transferred motion with simple native-axis bends."""
import bpy,json,math
from pathlib import Path
from mathutils import Matrix,Quaternion,Vector
P=R.parents[2];O=R/'NativeKneeHinge';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'SourceAssets/CharacterWorkshop_20261021/Roxie_Character_Options.blend'),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');rig.animation_data_clear()
for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
for ob in s.objects:
 if ob.type=='MESH' and ob.data.shape_keys:ob.data.shape_keys.animation_data_clear()
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('HingeStudy');s.world.color=(.035,.045,.055);s.render.resolution_x=700;s.render.resolution_y=700;s.render.resolution_percentage=100
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.8
report=[]
for angle in (0,30,60,90,120):
 for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
 b=rig.pose.bones['calf_l'];b.rotation_mode='QUATERNION';b.rotation_quaternion=Quaternion((0,0,1),math.radians(-angle));bpy.context.view_layer.update()
 center=(rig.matrix_world@b.matrix).translation
 for view,delta in [('outer',Vector((4,0,0))),('inner',Vector((-4,0,0)))]:
  cam.location=center+delta;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'{angle}_{view}.png');bpy.ops.render.render(write_still=True)
 report.append({'knee_local_z_degrees':-angle,'center':list(center)})
(O/'Report.json').write_text(json.dumps(report,indent=2));print('HINGE_STUDY_DONE',flush=True)
