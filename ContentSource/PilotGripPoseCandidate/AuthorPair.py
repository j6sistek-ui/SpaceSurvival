"""Author L pilot-hand and bounded exit-arm rotation patches for a candidate pair.
Original complete glTF clips are immutable; --export optionally reconstructs separate GLBs.
"""
from pathlib import Path
import sys,json,hashlib,math,struct
import bpy
import numpy as np
from mathutils import Quaternion,Vector,Matrix
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(OUT));import Generate as hand
anim=hand.anim;sha=hand.sha;NAMES=['L_Wrist']+['L_'+f+str(i)for f in ('Thumb','Index','Middle','Ring','Pinky')for i in range(1,4)]
EXIT_NAMES=NAMES+['L_Shoulder','L_Elbow','R_Shoulder','R_Elbow','R_Wrist']
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def exact_intersect(a,b):
 def edges_hit(p,t):
  e1=t[1]-t[0];e2=t[2]-t[0]
  for i in range(3):
   origin=p[i];direction=p[(i+1)%3]-origin;h=np.cross(direction,e2);det=e1@h
   if abs(det)<1e-12:continue
   q=origin-t[0];u=(q@h)/det
   if not -1e-8<=u<=1+1e-8:continue
   cross=np.cross(q,e1);v=(direction@cross)/det;along=(e2@cross)/det
   if v>=-1e-8 and u+v<=1+1e-8 and -1e-8<=along<=1+1e-8:return True
  return False
 return edges_hit(a,b)or edges_hit(b,a)
def overlap_evidence(hero,grips):
 tree,verts,triangles=hand.world_bvh(hero);vertices=np.array([tuple(v)for v in verts]);tri=np.array(triangles);result={}
 for side,(other,ov,ot)in grips.items():
  pairs=tree.overlap(other);ov=np.array([tuple(v)for v in ov]);ot=np.array(ot);exact=[(a,b)for a,b in pairs if exact_intersect(vertices[tri[a]],ov[ot[b]])]
  centers=[((vertices[tri[a]].mean(0))*100).tolist()for a,b in exact]
  result[side]={'bvh_pairs':len(pairs),'confirmed_triangle_crossings':len(exact),'crossing_skin_triangle_ids':sorted(set(a for a,b in exact)),'crossing_centroid_bounds_cm':[np.min(centers,axis=0).tolist(),np.max(centers,axis=0).tolist()]if centers else None}
 return result

def two_bone(rig,side,target_ship):
 root=rig.pose.bones[side+'_Shoulder'];middle=rig.pose.bones[side+'_Elbow'];end=rig.pose.bones[side+'_Wrist'];origin=root.head.copy();a=(middle.head-origin).length;b=(end.head-middle.head).length;target=rig.matrix_world.inverted()@(Vector(target_ship)/100);v=target-origin;distance=max(abs(a-b)+1e-6,min(v.length,(a+b)*.998));direction=v.normalized();pole=rig.matrix_world.to_3x3().inverted()@Vector((.15,1 if side=='L'else-1,-.5));bend=pole-direction*pole.dot(direction);bend.normalize();along=(a*a+distance*distance-b*b)/(2*distance);elbow=origin+direction*along+bend*math.sqrt(max(0,a*a-along*along))
 hand.rotate(root,(middle.head-root.head).normalized().rotation_difference((elbow-origin).normalized()));hand.rotate(middle,(end.head-middle.head).normalized().rotation_difference((origin+direction*distance-middle.head).normalized()))
 return (rig.matrix_world@end.head-Vector(target_ship)/100).length*100

def sample_exit(rig,doc,raw,seconds,deltas):
 anim.apply_animation(rig,doc,raw,seconds);original=anim.capture(rig);original_world={side:rig.pose.bones[side+'_Wrist'].matrix.to_quaternion()for side in ('L','R')}
 if seconds>=13/30:return original
 arm_gain=smooth(seconds/.06)*(1-smooth((seconds-.33)/(13/30-.33)))
 for side in ('L','R'):
  sign=1 if side=='L'else-1;start=[12.942420,21.082233,94.249429]if side=='L'else[9.137310,-20.322157,95.602653]
  keys=[(0,start),(.10,[10,sign*28,105]),(.20,[-12,sign*31,106]),(.28,[-19,sign*29,96]),(.34,[-19,sign*28,91]),(13/30,[-14.01,sign*24.01,81.73])]
  for (ta,pa),(tb,pb)in zip(keys,keys[1:]):
   if ta<=seconds<=tb:
    alpha=smooth((seconds-ta)/(tb-ta));target=[a+(b-a)*alpha for a,b in zip(pa,pb)];break
  two_bone(rig,side,target)
  for name in (side+'_Shoulder',side+'_Elbow'):
   b=rig.pose.bones[name];b.rotation_quaternion=original[name][1].slerp(b.rotation_quaternion,arm_gain)
  bpy.context.view_layer.update()
 wrist_gain=1-smooth((seconds-.33)/(13/30-.33));finger_gain=1-smooth((seconds-.05)/.15)
 for name in NAMES:
  amount=wrist_gain if name=='L_Wrist'else finger_gain
  rig.pose.bones[name].rotation_quaternion=original[name][1]@Quaternion().slerp(deltas[name],amount)
 bpy.context.view_layer.update()
 hold_gain=1-smooth((seconds-.30)/(13/30-.30))
 for side in ('L','R'):
  bone=rig.pose.bones[side+'_Wrist'];bone.rotation_quaternion=original[bone.name][1].slerp(deltas['_local_'+side],hold_gain)
 bpy.context.view_layer.update()

 for b in rig.pose.bones:
  assert (b.location-original[b.name][0]).length<1e-6 and (b.scale-original[b.name][2]).length<1e-6,b.name
  if b.name not in EXIT_NAMES:assert b.rotation_quaternion.rotation_difference(original[b.name][1]).angle<1e-4,b.name
 return original

def gltf_rotations(rig,names=NAMES):
 joints={b.name:b.matrix@b.bone.matrix_local.inverted()@Matrix.Translation(b.bone.head_local)for b in rig.pose.bones};inverse=anim.CONVERSION.inverted();result={}
 for name in names:
  b=rig.pose.bones[name];local=joints[b.parent.name].inverted()@joints[name]if b.parent else joints[name];q=(inverse@local@anim.CONVERSION).to_quaternion();result[name]=[q.x,q.y,q.z,q.w]
 return result

def export_patch(base_path,patch,name):
 doc,raw=anim.read_glb(base_path);names={n.get('name'):i for i,n in enumerate(doc['nodes'])};clip=doc['animations'][0];changed=[]
 for channel in clip['channels']:
  bone=doc['nodes'][channel['target']['node']].get('name')
  if channel['target']['path']!='rotation'or bone not in patch['rotations']:continue
  sampler=clip['samplers'][channel['sampler']];values=patch['rotations'][bone];old=anim.accessor(doc,raw,sampler['output']);assert len(values)==len(old)
  if patch['kind']=='Exit':
   values=[q if frame<13 and (frame>0 or bone in NAMES) else list(old[frame])for frame,q in enumerate(values)]
   if bone in NAMES:values[0]=json.loads((OUT/'PilotRotations.json').read_text())['rotations'][bone][0]
  while len(raw)%4:raw.append(0)
  offset=len(raw);raw.extend(struct.pack('<'+'f'*(len(values)*4),*[v for q in values for v in q]));view=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(values)*16});accessor=len(doc['accessors']);doc['accessors'].append({'bufferView':view,'componentType':5126,'count':len(values),'type':'VEC4'});sampler['output']=accessor;changed.append(bone)
 assert set(changed)==set(patch['rotations']);clip['name']=name;doc['buffers'][0]['byteLength']=len(raw);encoded=json.dumps(doc,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4);raw.extend(b'\0'*((-len(raw))%4));path=OUT/(name.removeprefix('A_')+'.glb');path.write_bytes(struct.pack('<III',0x46546C67,2,12+8+len(encoded)+8+len(raw))+struct.pack('<II',len(encoded),0x4E4F534A)+encoded+struct.pack('<II',len(raw),0x004E4942)+raw);return {'file':path.name,'sha256':sha(path)}

def main():
 if '--export-only'in sys.argv:
  results=[]
  for kind,base,name in [('Pilot','Pilot','A_PilotGripFit'),('Exit','Disembark','A_DisembarkGripFit')]:
   patch=json.loads((OUT/(kind+'Rotations.json')).read_text());assert patch['base_sha256']==sha(ROOT/('ContentSource/Animation/'+base+'.glb'))
   if kind=='Exit':
    pilot_patch=json.loads((OUT/'PilotRotations.json').read_text())
    for bone in NAMES:patch['rotations'][bone][0]=pilot_patch['rotations'][bone][0]
   results.append(export_patch(ROOT/('ContentSource/Animation/'+base+'.glb'),patch,name))
  (OUT/'ExportedClips.json').write_text(json.dumps({'status':'SOURCE_PAIR_EXPORTED_REQUIRES_INDEPENDENT_VALIDATION','exports':results},indent=2)+'\n',encoding='utf-8');print('PAIRED_SOURCE_EXPORT_FINISHED');return
 protected_paths=[ROOT/'model-rigged.glb',ROOT/'ContentSource/Animation/Pilot.glb',ROOT/'ContentSource/Animation/Disembark.glb',ROOT/'ContentSource/Animation/TailCandidateV2.glb',ROOT/'ContentSource/AcornShipGripFit/AcornShipGripFit.blend'];protected={str(p.relative_to(ROOT)):sha(p)for p in protected_paths}
 bpy.ops.wm.open_mainfile(filepath=str(protected_paths[-1]));before=set(bpy.context.scene.objects);bpy.ops.import_scene.gltf(filepath=str(protected_paths[3]));added=[o for o in bpy.context.scene.objects if o not in before];rig=next(o for o in added if o.type=='ARMATURE');hero=next(o for o in added if o.type=='MESH');rig.animation_data_clear()
 for bone in rig.pose.bones:bone.rotation_mode='QUATERNION'
 rig.rotation_mode='XYZ';rig.rotation_euler=(0,0,math.pi/2);rig.scale=(1.5,)*3;rig.location=(-.15,0,.72);bpy.context.view_layer.update();pilot,pilot_raw=anim.read_glb(protected_paths[1]);exit_doc,exit_raw=anim.read_glb(protected_paths[2]);baseline=hand.pose(rig,pilot,pilot_raw,0);candidate=anim.capture(rig);deltas={name:baseline[name][1].inverted()@candidate[name][1]for name in NAMES};deltas.update({'_local_'+side:rig.pose.bones[side+'_Wrist'].rotation_quaternion.copy()for side in ('L','R')})
 record={'status':'PAIRED_GRIP_ROTATION_SOURCE_NOT_IMPORTED','protected_sha256':protected,'changed_rotation_tracks':{'Pilot':NAMES,'Exit':EXIT_NAMES},'unchanged_track_contract':'All translations/scales and rotations outside the declared per-clip track list copied byte-for-byte on export; all Exit outputs from sample13 (0.433333s) onward use exact old rotation values.','release':'Begin at candidatePilot0. Lift wrists to105cm by0.10s with seated wrist-local orientation, retract behind grips by0.20s, lower behind controls; wrist/finger release follows. L/R shoulder/elbow/wrist rotations may differ untilsample13; no R finger edits. Original lower body and actor path unchanged. Exact original local pose resumes at0.433333s.','live_phase_handoff':'Lead owns captured-pose proxy; source pair alone does not remove live Pilot phase mismatch.','release_samples':[],'patches':[]}
 for kind,frames,doc,raw,path in [('Pilot',121,pilot,pilot_raw,protected_paths[1]),('Exit',73,exit_doc,exit_raw,protected_paths[2])]:
  if kind=='Pilot'and '--exit-only'in sys.argv:continue
  patch={'kind':kind,'base_sha256':sha(path),'fps':30,'samples':frames,'rotations':{n:[]for n in (NAMES if kind=='Pilot'else EXIT_NAMES)}}
  for frame in range(frames):
   if kind=='Pilot':hand.pose(rig,doc,raw,frame/30)
   else:sample_exit(rig,doc,raw,frame/30,deltas)
   for name,q in gltf_rotations(rig,NAMES if kind=='Pilot'else EXIT_NAMES).items():patch['rotations'][name].append(q)
  file=OUT/(kind+'Rotations.json');file.write_text(json.dumps(patch,separators=(',',':'))+'\n',encoding='utf-8');record['patches'].append({'file':file.name,'sha256':sha(file)})
  if '--export'in sys.argv:record.setdefault('exports',[]).append(export_patch(path,patch,'A_PilotGripFit'if kind=='Pilot'else'A_DisembarkGripFit'))
 playback=anim.read_glb(OUT/'DisembarkGripFit.glb')if '--export'in sys.argv else None;record['clearance_sampling']='Exact exported glTF playback at60Hz'if playback else'Analytic authoring path only'
 grips={side:hand.world_bvh(bpy.data.objects['Pilot control grip '+sign])for side,sign in [('L','1'),('R','-1')]}
 for frame in range(27):
  seconds=frame/60;anim.apply_animation(rig,exit_doc,exit_raw,seconds);old=overlap_evidence(hero,grips);anim.apply_animation(rig,*playback,seconds)if playback else sample_exit(rig,exit_doc,exit_raw,seconds,deltas);new=overlap_evidence(hero,grips);record['release_samples'].append({'seconds':seconds,'original':old,'candidate':new})
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.render.threads_mode='FIXED';scene.render.threads=8;scene.cycles.samples=20;scene.cycles.use_denoising=True;scene.render.resolution_x=1120;scene.render.resolution_y=840;scene.render.resolution_percentage=100;camera=scene.camera;camera.location=(.90,1.04,1.36);camera.rotation_euler=(Vector((.18,.21,.95))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=72
 views=[('ArmNaturalRetract',8/30,True),('ArmNaturalOverview',.2,True)]
 for name,seconds,new in views:
  if name=='ArmNaturalOverview':camera.location=(1.65,-1.65,1.85);camera.rotation_euler=(Vector((.12,0,.94))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=57
  if new:anim.apply_animation(rig,*playback,seconds)if playback else sample_exit(rig,exit_doc,exit_raw,seconds,deltas)
  else:anim.apply_animation(rig,exit_doc,exit_raw,seconds)
  scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
 record['images']=[{'file':name+'.png','sha256':sha(OUT/(name+'.png'))}for name,_,_ in views];assert all(sha(ROOT/p)==h for p,h in protected.items());(OUT/'PairedRelease.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print('PAIRED_L_HAND_SOURCE_FINISHED')
if __name__=='__main__':main()
