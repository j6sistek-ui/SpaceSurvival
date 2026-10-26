import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Full Vexa assembly check before baking a shoulder corrective. No source save."""
import bpy, sys, json, numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025'
from shoulder_support import support_clavicles, shoulder_mask
O=R/'VexaFullShoulderReview';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'SourceAssets/CharacterWorkshop_20261021/Vexa_Character_Options.blend'),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');rig.animation_data_clear()
replacement=('Vexa_Nude_Legs','Vexa_Nude_Torso','Vexa_Bottom')
for name in replacement:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
with bpy.data.libraries.load(str(D/'Vexa_LegPlane_Proof.blend'),link=False) as (a,b):
 b.objects=list(replacement);b.actions=['A_F3_LegPlane_ZeroG_02_Spiral']
for ob in b.objects:
 s.collection.objects.link(ob);world=ob.matrix_world.copy();ob.parent=rig;ob.matrix_world=world
 for mod in ob.modifiers:
  if mod.type=='ARMATURE':mod.object=rig;mod.use_deform_preserve_volume=False
act=b.actions[0];rig.animation_data_create();rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
ordered=sorted(rig.pose.bones,key=lambda b:len(b.parent_recursive));rest={b.name:(rig.matrix_world@b.bone.matrix_local).copy() for b in ordered}
desc={b.name:[b.name]+[c.name for c in b.children_recursive] for b in ordered};inv=rig.matrix_world.inverted()
torso=bpy.data.objects['Vexa_Nude_Torso'];arm=next(m for m in torso.modifiers if m.type=='ARMATURE')
mask,boundary=shoulder_mask(torso,[rest['upperarm_'+x].translation for x in ('l','r')])
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('VexaFullShoulder');s.world.color=(.035,.045,.055)
s.render.resolution_x=960;s.render.resolution_y=960;s.render.resolution_percentage=100
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';rows=[]
for sec in (8,9.033333):
 for mode in ('source','supported'):
  s.frame_set(round(1+sec*60));bpy.context.view_layer.update();pose={b.name:(rig.matrix_world@b.matrix).copy() for b in ordered}
  row={'seconds':sec,'mode':mode}
  if mode=='supported':
   row['support']=support_clavicles(pose,rest,desc);local={n:inv@m for n,m in pose.items()}
   for pb in ordered:
    base=local[pb.parent.name]@pb.parent.bone.matrix_local.inverted()@pb.bone.matrix_local if pb.parent else pb.bone.matrix_local
    pb.matrix_basis=base.inverted()@local[pb.name]
   bpy.context.view_layer.update()
  visible=[ob for ob in s.objects if ob.type=='MESH' and not ob.hide_render and not ob.hide_get()]
  snapshots=[]
  for ob in visible:
   mesh=bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
   if ob==torso and mode=='supported':
    linear=np.array([tuple(v.co) for v in mesh.vertices]);arm.use_deform_preserve_volume=True;bpy.context.view_layer.update()
    volume=np.array([tuple(v.co) for v in torso.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices]);delta=(volume-linear)*mask[:,None]
    mesh.vertices.foreach_set('co',(linear+delta).ravel());mesh.update();arm.use_deform_preserve_volume=False;bpy.context.view_layer.update()
    row['boundary_correction_m']=float(max(np.linalg.norm(delta[list(boundary)],axis=1)))*max(torso.matrix_world.to_scale())
   snapshot=bpy.data.objects.new('ProofSnapshot',mesh);s.collection.objects.link(snapshot);snapshot.matrix_world=ob.matrix_world.copy();snapshots.append((snapshot,mesh));ob.hide_render=True
  chest=pose['spine_05'].to_quaternion()@rest['spine_05'].to_quaternion().inverted();center=(pose['upperarm_l'].translation+pose['upperarm_r'].translation)*.5
  for view,delta,scale,target in [('front',Vector((0,-3,.2)),.85,center),('back',Vector((0,3,.2)),.85,center),('oblique',Vector((2,-3,.5)),1.1,center),('full',Vector((2,-6,1)),2.4,pose['pelvis'].translation)]:
   cam.data.ortho_scale=scale;cam.location=target+(chest@delta if view!='full' else delta);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'{sec:g}_{view}_{mode}.png');bpy.ops.render.render(write_still=True)
  for ob in visible:ob.hide_render=False
  for ob,mesh in snapshots:bpy.data.objects.remove(ob,do_unlink=True);bpy.data.meshes.remove(mesh)
  rows.append(row)
(O/'Report.json').write_text(json.dumps(rows,indent=2));print('VEXA_FULL_SHOULDER_REVIEW_DONE',flush=True)
