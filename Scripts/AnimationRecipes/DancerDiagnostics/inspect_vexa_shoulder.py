import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Read-only Vexa shoulder controls and deformation comparison."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=R.parents[2];O=R/'VexaShoulderReview';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'SourceAssets/DanceRefinement_20261025/Vexa_LegPlane_Proof.blend'),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');torso=bpy.data.objects['Vexa_Nude_Torso'];arm=next(m for m in torso.modifiers if m.type=='ARMATURE')
report={'source':'Vexa_LegPlane_Proof.blend','bones':[],'shoulder_weights':{},'poses':[]}
for b in rig.data.bones:
 if any(x in b.name for x in ('clavicle','upperarm','lowerarm','scapula')):report['bones'].append({'name':b.name,'parent':b.parent.name if b.parent else None,'head_world':list(rig.matrix_world@b.head_local),'tail_world':list(rig.matrix_world@b.tail_local)})
for side in ('l','r'):
 center=rig.matrix_world@rig.data.bones['upperarm_'+side].head_local;groups={};count=0
 for v in torso.data.vertices:
  if (torso.matrix_world@v.co-center).length>.16:continue
  count+=1
  for g in v.groups:
   n=torso.vertex_groups[g.group].name;groups[n]=groups.get(n,0)+g.weight
 report['shoulder_weights'][side]={'vertices':count,'weight_totals':groups}
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('VexaShoulder');s.world.color=(.035,.045,.055)
s.render.resolution_x=800;s.render.resolution_y=800;s.render.resolution_percentage=100
for ob in s.objects:
 if ob.type=='MESH':ob.hide_render=ob!=torso
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.6
def capture(label,side):
 bpy.context.view_layer.update();upper=rig.pose.bones['upperarm_'+side];chest=rig.matrix_world@rig.pose.bones['spine_05'].matrix
 center=(rig.matrix_world@upper.matrix).translation
 # Use chest orientation for comparable front/three-quarter anatomical views.
 q=(chest.to_quaternion()@(rig.matrix_world@rig.data.bones['spine_05'].matrix_local).to_quaternion().inverted())
 for view,offset in [('front',Vector((0,-3,.15))),('oblique',Vector((1.6 if side=='l' else -1.6,-2.6,.2)))]:
  cam.location=center+q@offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/(label+'_'+side+'_'+view+'.png'));bpy.ops.render.render(write_still=True)
for t in (8,9.033333,12.2):
 s.frame_set(round(t*60)+1)
 for mode in ('linear','preserve_volume'):
  arm.use_deform_preserve_volume=mode=='preserve_volume';capture(f'{t:g}_{mode}','l')
arm.use_deform_preserve_volume=False;rig.animation_data_clear()
for ob in s.objects:
 if ob.type=='MESH' and ob.data.shape_keys:
  ob.data.shape_keys.animation_data_clear()
  for key in ob.data.shape_keys.key_blocks:
   if key.name.startswith('REVIEW_'):key.value=0
for elevation in (0,45,80):
 for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
 up=rig.pose.bones['upperarm_l'];low=rig.pose.bones['lowerarm_l'];bpy.context.view_layer.update()
 old=(rig.matrix_world@low.matrix).translation-(rig.matrix_world@up.matrix).translation
 goal=Vector((math.cos(math.radians(elevation)),0,math.sin(math.radians(elevation))))
 q=old.normalized().rotation_difference(goal)
 world=rig.matrix_world@up.matrix;wanted=Matrix.LocRotScale(world.translation,q@world.to_quaternion(),world.to_scale())
 base=up.parent.matrix@up.parent.bone.matrix_local.inverted()@up.bone.matrix_local;up.matrix_basis=base.inverted()@rig.matrix_world.inverted()@wanted
 # Freeze evaluated geometry so a render cannot re-evaluate the old keyed pose.
 bpy.context.view_layer.update();capture('native_'+str(elevation),'l')
(O/'Report.json').write_text(json.dumps(report,indent=2));print('VEXA_SHOULDER_INSPECTION_DONE',flush=True)
