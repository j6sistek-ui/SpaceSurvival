import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Private Vexa shoulder diagnosis: clavicle support and twist distribution.

No source writes, no accepted weighting recipe. Freeze evaluated snapshots so
keyed source animation cannot reset a proposed pose during rendering.
"""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=R.parents[2];O=R/'VexaClavicleReview';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'SourceAssets/DanceRefinement_20261025/Vexa_LegPlane_Proof.blend'),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');torso=bpy.data.objects['Vexa_Nude_Torso']
ordered=sorted(rig.pose.bones,key=lambda b:len(b.parent_recursive));rest={b.name:(rig.matrix_world@b.bone.matrix_local).copy() for b in ordered};inv=rig.matrix_world.inverted()
for ob in s.objects:
 if ob.type=='MESH':ob.hide_render=ob!=torso
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('VexaClavicle');s.world.color=(.035,.045,.055)
s.render.resolution_x=850;s.render.resolution_y=850;s.render.resolution_percentage=100
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.68
report=[]
for sec in (8,9.033333,12.2):
 for mode in ('source','clavicle','clavicle_twist','clavicle_volume'):
  s.frame_set(round(1+sec*60));bpy.context.view_layer.update();pose={b.name:(rig.matrix_world@b.matrix).copy() for b in ordered};chest=pose['spine_05'].to_quaternion()@rest['spine_05'].to_quaternion().inverted();up=chest@Vector((0,0,1));row={'seconds':sec,'mode':mode,'arms':{}}
  for side in ('l','r'):
   clav,upper,lower='clavicle_'+side,'upperarm_'+side,'lowerarm_'+side
   direction=(pose[lower].translation-pose[upper].translation).normalized();elevation=math.asin(max(-1,min(1,direction.dot(up))))
   lift=math.radians(25)*max(0,min(1,(elevation+math.radians(10))/math.radians(90)))
   row['arms'][side]={'elevation':math.degrees(elevation),'clavicle_lift':math.degrees(lift)}
   if mode=='source':continue
   pivot=pose[clav].translation.copy();old_shoulder=pose[upper].translation.copy();cvec=(old_shoulder-pivot).normalized();axis=cvec.cross(up).normalized();q=Quaternion(axis,lift)
   pose[clav]=Matrix.LocRotScale(pivot,q@pose[clav].to_quaternion(),pose[clav].to_scale())
   new_shoulder=pivot+q@(old_shoulder-pivot);shift=new_shoulder-old_shoulder
   for b in [rig.pose.bones[upper]]+list(rig.pose.bones[upper].children_recursive):pose[b.name].translation+=shift
   if mode=='clavicle_twist':
    neutral=pose[clav]@rest[clav].inverted()@rest[upper]
    rest_dir=rest[upper].inverted()@rest[lower].translation
    n=(neutral.to_quaternion()@rest_dir).normalized();minimal=(n.rotation_difference(direction)@neutral.to_quaternion()).normalized()
    for i,weight in ((1,.35),(2,.7)):
     name=f'upperarm_twist_{i:02}_{side}'
     if name not in pose:continue
     native=minimal@rest[upper].to_quaternion().inverted()@rest[name].to_quaternion();actual=pose[name].to_quaternion()
     if native.dot(actual)<0:native.negate()
     pose[name]=Matrix.LocRotScale(pose[name].translation,native.slerp(actual,weight),pose[name].to_scale())
  if mode!='source':
   local={n:inv@m for n,m in pose.items()}
   for b in ordered:
    base=local[b.parent.name]@b.parent.bone.matrix_local.inverted()@b.bone.matrix_local if b.parent else b.bone.matrix_local
    b.matrix_basis=base.inverted()@local[b.name]
   bpy.context.view_layer.update()
  mesh=bpy.data.meshes.new_from_object(torso.evaluated_get(bpy.context.evaluated_depsgraph_get()))
  if mode=='clavicle_volume':
   arm=next(m for m in torso.modifiers if m.type=='ARMATURE');arm.use_deform_preserve_volume=True;bpy.context.view_layer.update()
   volume=torso.evaluated_get(bpy.context.evaluated_depsgraph_get());a=np.array([list(v.co) for v in mesh.vertices]);b=np.array([list(v.co) for v in volume.data.vertices])
   centers=[rest['upperarm_'+side].translation for side in ('l','r')]
   dist=np.array([min((torso.matrix_world@v.co-c).length for c in centers) for v in torso.data.vertices]);mask=np.clip((.22-dist)/.14,0,1);mask=mask*mask*(3-2*mask)
   delta=(b-a)*mask[:,None];mesh.vertices.foreach_set('co',(a+delta).ravel());mesh.update();row['max_volume_correction_m']=float(np.linalg.norm(delta,axis=1).max()*max(torso.matrix_world.to_scale()))
   arm.use_deform_preserve_volume=False;bpy.context.view_layer.update()
  snapshot=bpy.data.objects.new('ShoulderSnapshot',mesh);s.collection.objects.link(snapshot);snapshot.matrix_world=torso.matrix_world.copy();torso.hide_render=True
  center=(pose['upperarm_l'].translation+pose['upperarm_r'].translation)*.5
  for view,delta in (('front',Vector((0,-3,.2))),('back',Vector((0,3,.2)))):
   cam.location=center+chest@delta;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'{sec:g}_{view}_{mode}.png');bpy.ops.render.render(write_still=True)
  torso.hide_render=False;bpy.data.objects.remove(snapshot,do_unlink=True);bpy.data.meshes.remove(mesh);report.append(row)
(O/'Report.json').write_text(json.dumps(report,indent=2));print('VEXA_CLAVICLE_REVIEW_DONE',flush=True)
