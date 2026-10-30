import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Unlit packed colours isolate colour seams from lighting/geometry."""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025';O=R/'ZeroGSharedHip/AlbedoControl';O.mkdir(exist_ok=True)
src=D/'Vexa_ZeroG_MaterialReview.blend';h=hashlib.sha256(src.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');pairs=json.loads(s['zero_g_curve_pairs']);cam=s.camera
for mat in {m for o in s.objects if o.type=='MESH' for m in o.data.materials if m}:
 n=mat.node_tree.nodes;bs=next((x for x in n if x.type=='BSDF_PRINCIPLED'),None)
 if not bs:continue
 out=next(x for x in n if x.type=='OUTPUT_MATERIAL');em=n.new('ShaderNodeEmission');color=bs.inputs['Base Color']
 if color.is_linked:mat.node_tree.links.new(color.links[0].from_socket,em.inputs['Color'])
 else:em.inputs['Color'].default_value=color.default_value
 mat.node_tree.links.new(em.outputs[0],out.inputs['Surface'])
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=8;s.cycles.use_denoising=False;s.render.resolution_x=s.render.resolution_y=800;s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0
for suffix,f in [('01_Drift',563.5),('02_Spiral',481)]:
 name='A_F3_Coordinated_ZeroG_'+suffix;a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for on,an in pairs[name].items():
  keys=bpy.data.objects[on].data.shape_keys;keys.animation_data.action=bpy.data.actions[an];keys.animation_data.action_slot=keys.animation_data.action.slots[0]
 s.frame_set(math.floor(f),subframe=f%1);bpy.context.view_layer.update()
 up=((rig.matrix_world@rig.pose.bones['neck_01'].matrix).translation-(rig.matrix_world@rig.pose.bones['spine_03'].matrix).translation).normalized();side=((rig.matrix_world@rig.pose.bones['upperarm_l'].matrix).translation-(rig.matrix_world@rig.pose.bones['upperarm_r'].matrix).translation).normalized();front=side.cross(up).normalized();center=(rig.matrix_world@rig.pose.bones['pelvis'].matrix).translation+up*.1
 for view,delta in [('front',front*4),('rear',-front*4)]:
  cam.location=center+delta+up*.1;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'{suffix}_{view}.png');bpy.ops.render.render(write_still=True)
assert hashlib.sha256(src.read_bytes()).hexdigest()==h
print('ALBEDO_CONTROL_DONE',flush=True)
