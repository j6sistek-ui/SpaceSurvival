"""Source-only L hand pose diagnostic; protected rig, meshes and clips remain unchanged."""
from pathlib import Path
import sys,hashlib,json,math
import bpy
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'ContentSource'));import GenerateDisembark as anim
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protected_paths=[ROOT/'model-rigged.glb',ROOT/'ContentSource/Animation/Pilot.glb',ROOT/'ContentSource/Animation/Disembark.glb',ROOT/'ContentSource/Animation/TailCandidateV2.glb',ROOT/'ContentSource/AcornShipGripFit/AcornShipGripFit.blend']
protected={str(p.relative_to(ROOT)):sha(p)for p in protected_paths}
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'ContentSource/AcornShipGripFit/AcornShipGripFit.blend'))
before=set(bpy.context.scene.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'ContentSource/Animation/TailCandidateV2.glb'));added=[o for o in bpy.context.scene.objects if o not in before];rig=next(o for o in added if o.type=='ARMATURE');rig.animation_data_clear()
for bone in rig.pose.bones:bone.rotation_mode='QUATERNION'
clip,binary=anim.read_glb(ROOT/'ContentSource/Animation/Pilot.glb');anim.apply_animation(rig,clip,binary,0);rig.rotation_mode='XYZ';rig.rotation_euler=(0,0,math.pi/2);rig.scale=(1.5,)*3;rig.location=(-.15,0,.72);bpy.context.view_layer.update()
base=anim.capture(rig);wrist=rig.pose.bones['L_Wrist'];forward=(rig.pose.bones['L_Middle1'].head-wrist.head).normalized();palm=forward.cross(rig.pose.bones['L_Index1'].head-rig.pose.bones['L_Pinky1'].head).normalized()
record={'status':'L_WRIST_DIAGNOSTIC_NO_CLIP_ADOPTION','protected_sha256':protected,'base_wrist_head_rig_m':list(wrist.head),'forward_rig':list(forward),'forward_in_blender_pose_bone_local':list(wrist.matrix.to_3x3().inverted()@forward),'palm_normal_proxy_rig':list(palm),'base_bones':{},'poses':[]}
for bone in rig.pose.bones:
 if bone.name.startswith('L_')and any(part in bone.name for part in ('Wrist','Thumb','Index','Middle','Ring','Pinky')):
  record['base_bones'][bone.name]={'head_ship_cm':list((rig.matrix_world@bone.head)*100),'rest_matrix':[[float(v)for v in row]for row in bone.bone.matrix_local],'pose_matrix':[[float(v)for v in row]for row in bone.matrix]}
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.render.threads_mode='FIXED';scene.render.threads=8;scene.cycles.samples=20;scene.cycles.use_denoising=True;scene.render.resolution_x=1120;scene.render.resolution_y=840;scene.render.resolution_percentage=100
camera=scene.camera;camera.location=(.90,1.04,1.36);target=Vector((.18,.21,.95));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=72
for name,degrees in [('Original',0),('ObliqueRoll',-120),('PalmDownRoll',-170.25305053927806)]:
 anim.restore(rig,base);bone=rig.pose.bones['L_Wrist'];head=bone.head.copy();matrix=Quaternion(forward,math.radians(degrees)).to_matrix().to_4x4()@bone.matrix;matrix.translation=head;bone.matrix=matrix;bpy.context.view_layer.update()
 assert (bone.head-head).length<1e-6
 changed=[b.name for b in rig.pose.bones if b.rotation_quaternion.rotation_difference(base[b.name][1]).angle>1e-4];assert set(changed)<= {'L_Wrist'},changed
 assert all((b.location-base[b.name][0]).length<1e-6 and (b.scale-base[b.name][2]).length<1e-6 for b in rig.pose.bones)
 pose={'name':name,'roll_degrees':degrees,'changed_rotation_bones':changed,'heads_ship_cm':{b.name:list((rig.matrix_world@b.head)*100)for b in rig.pose.bones if b.name in record['base_bones']}}
 scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True);pose['image_sha256']=sha(OUT/(name+'.png'));record['poses'].append(pose)
assert all(sha(ROOT/p)==h for p,h in protected.items())
(OUT/'Diagnostic.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print('L_WRIST_SOURCE_DIAGNOSTIC_FINISHED')
