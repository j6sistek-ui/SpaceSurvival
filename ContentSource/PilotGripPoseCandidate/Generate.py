"""Separate L-only pilot hand pose proposal. No original animation/mesh/rig writes."""
from pathlib import Path
import sys,hashlib,json,math
import bpy
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'ContentSource'));import GenerateDisembark as anim
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ROLL=-170.25305053927806
# Ship-space finger flex directions; each increment is clamped to avoid a forced IK snap.
FLEX={'Middle':[(-.2,0,-1),(-1,0,-.15),(-.6,0,.6)],'Ring':[(-.2,-.12,-1),(-1,-.12,-.15),(-.6,-.1,.6)],'Pinky':[(0,-.5,-1),(-.7,-.7,-.25),(-.5,-.5,.1)],'Thumb':[(-.55,.3,-.1),(-.8,.5,.1),(.2,.1,1)],'Index':[(.5,.2,-.8),(1,.1,.3),(.5,.2,.9)]}
LIMITS={'Middle':(20,35,20),'Ring':(20,35,20),'Pinky':(20,30,20),'Thumb':(15,20,10),'Index':(15,20,10)}

def rotate(bone,delta):
 head=bone.head.copy();location=bone.location.copy();scale=bone.scale.copy();matrix=delta.to_matrix().to_4x4()@bone.matrix;matrix.translation=head;bone.matrix=matrix;bone.location=location;bone.scale=scale;bpy.context.view_layer.update()

def pose(rig,clip,binary,seconds,amount=1):
 anim.apply_animation(rig,clip,binary,seconds);baseline=anim.capture(rig);wrist=rig.pose.bones['L_Wrist'];forward=(rig.pose.bones['L_Middle1'].head-wrist.head).normalized();rotate(wrist,Quaternion(forward,math.radians(ROLL)))
 for finger in FLEX:
  for index in range(1,4):
   bone=rig.pose.bones['L_'+finger+str(index)];child=rig.pose.bones.get('L_'+finger+str(index+1));direction=(child.head-bone.head)if child else(bone.head-rig.pose.bones['L_'+finger+str(index-1)].head);desired=rig.matrix_world.to_3x3().inverted()@Vector(FLEX[finger][index-1]);delta=direction.normalized().rotation_difference(desired.normalized());axis,angle=delta.to_axis_angle();rotate(bone,Quaternion(axis,min(angle,math.radians(LIMITS[finger][index-1]))*amount))
 for bone in rig.pose.bones:
  assert (bone.location-baseline[bone.name][0]).length<1e-6 and (bone.scale-baseline[bone.name][2]).length<1e-6,bone.name
  if not bone.name.startswith('L_')or not any(n in bone.name for n in ('Wrist','Thumb','Index','Middle','Ring','Pinky')):assert bone.rotation_quaternion.rotation_difference(baseline[bone.name][1]).angle<1e-4,bone.name
 return baseline

def world_bvh(obj):
 evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh();mesh.calc_loop_triangles();vertices=[obj.matrix_world@v.co for v in mesh.vertices];triangles=[tuple(t.vertices)for t in mesh.loop_triangles];tree=BVHTree.FromPolygons(vertices,triangles,all_triangles=True);evaluated.to_mesh_clear();return tree,vertices,triangles

def main():
 protected_paths=[ROOT/'model-rigged.glb',ROOT/'ContentSource/Animation/Pilot.glb',ROOT/'ContentSource/Animation/Disembark.glb',ROOT/'ContentSource/Animation/TailCandidateV2.glb',ROOT/'ContentSource/AcornShipGripFit/AcornShipGripFit.blend'];protected={str(p.relative_to(ROOT)):sha(p)for p in protected_paths}
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/'ContentSource/AcornShipGripFit/AcornShipGripFit.blend'));before=set(bpy.context.scene.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'ContentSource/Animation/TailCandidateV2.glb'));added=[o for o in bpy.context.scene.objects if o not in before];rig=next(o for o in added if o.type=='ARMATURE');hero=next(o for o in added if o.type=='MESH');rig.animation_data_clear()
 for bone in rig.pose.bones:bone.rotation_mode='QUATERNION'
 clip,binary=anim.read_glb(ROOT/'ContentSource/Animation/Pilot.glb');rig.rotation_mode='XYZ';rig.rotation_euler=(0,0,math.pi/2);rig.scale=(1.5,)*3;rig.location=(-.15,0,.72);bpy.context.view_layer.update()
 record={'status':'L_HAND_SOURCE_POSE_CANDIDATE_NOT_CLIP_OR_RUNTIME_ADOPTION','roll_degrees':ROLL,'flex_limits_degrees':LIMITS,'flex_directions_ship':FLEX,'protected_sha256':protected,'samples':[],'limits':['Hand contact is source geometry only, no UE animation imported.','All base translations/scales and non-L-hand local rotations remain unchanged.','BVH triangle-overlap count is a diagnostic, not owner quality acceptance.','Existing Disembark needs an L-hand-specific release that converges to old tracks before the unchanged rise/contact phases.']}
 for seconds in (0,1,2,3,4):
  baseline=pose(rig,clip,binary,seconds);tree,vertices,triangles=world_bvh(hero);grip=bpy.data.objects['Pilot control grip 1'];other,grip_vertices,grip_triangles=world_bvh(grip);overlap=tree.overlap(other);distances=[tree.find_nearest(v)[3]*100 for v in grip_vertices];record['samples'].append({'seconds':seconds,'left_grip_overlapping_triangle_pairs':len(overlap),'minimum_grip_vertex_to_skin_cm':min(distances),'left_local_rotations_wxyz':{b.name:list(b.rotation_quaternion)for b in rig.pose.bones if b.name.startswith('L_')and any(n in b.name for n in ('Wrist','Thumb','Index','Middle','Ring','Pinky'))}})
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.render.threads_mode='FIXED';scene.render.threads=8;scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.resolution_x=1120;scene.render.resolution_y=840;scene.render.resolution_percentage=100;camera=scene.camera
 views=[('ClosureNear',(.90,1.04,1.36),(.18,.21,.95),72,0),('ClosureFar',(.64,-.60,1.28),(.19,.21,.93),80,0),('ClosureOverview',(1.65,-1.65,1.85),(.12,0,.94),57,0)]
 for name,position,target,lens,seconds in views:
  pose(rig,clip,binary,seconds);camera.location=position;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=lens;scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
 assert all(sha(ROOT/p)==h for p,h in protected.items());record['images']=[{'file':v[0]+'.png','sha256':sha(OUT/(v[0]+'.png'))}for v in views];(OUT/'PoseCandidate.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print('L_HAND_POSE_CANDIDATE_FINISHED')
if __name__=='__main__':main()
