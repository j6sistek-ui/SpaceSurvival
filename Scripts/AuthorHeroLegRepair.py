"""Repair source walk's left shin half-turn, preserving bind mesh and endpoint motion.
Run in Blender background with factory startup. Outputs ignored derivatives only.
"""
from pathlib import Path
import sys,json,struct,hashlib,math
import numpy as np
from mathutils import Quaternion,Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'ContentSource'))
import GeneratePilotMesh as glb
OUT=ROOT/'Artifacts/HeroLegRepair'
def repair(source,stem,ramp=False):
 OUT.mkdir(parents=True,exist_ok=True)
 original=source.read_bytes();d,b=glb.read_glb(source)
 names={n.get('name'):i for i,n in enumerate(d['nodes'])}
 # Twist around the rest shin axis leaves the ankle position unchanged.
 axis=Vector(d['nodes'][names['L_Ankle']]['translation']).normalized()
 correction=Quaternion(axis,math.pi)
 changed={}
 errors=[]
 for channel in d['animations'][0]['channels']:
  name=d['nodes'][channel['target']['node']].get('name')
  if name not in ('L_Knee','L_Ankle') or channel['target']['path']!='rotation':continue
  sampler=d['animations'][0]['samplers'][channel['sampler']]
  a=glb.accessor(d,b,sampler['output']).copy(); out=[]
  times=glb.accessor(d,b,sampler['input']).reshape(-1)
  for t,v in zip(times,a):
   alpha=max(0.0,min(1.0,(float(t)-.42)/.40)) if ramp else 1.0
   alpha=alpha*alpha*(3-2*alpha)
   correction=Quaternion(axis,math.pi*alpha)
   q=Quaternion((float(v[3]),*map(float,v[:3])))
   old=q.copy()
   q=q@correction if name=='L_Knee' else correction.inverted()@q
   if name=='L_Knee': errors.append(((q@axis)-(old@axis)).length)
   out.append((q.x,q.y,q.z,q.w))
  sampler['output']=glb.append_accessor(d,b,np.array(out,dtype='<f4'),5126,'VEC4');changed[name]=len(out)
 assert set(changed)=={'L_Knee','L_Ankle'}
 d['animations'][0]['name']=stem;d['buffers'][0]['byteLength']=len(b)
 j=json.dumps(d,separators=(',',':')).encode();j+=b' '*((-len(j))%4);b+=b'\0'*((-len(b))%4)
 target=OUT/(stem+'.glb');target.write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b)
 report={'source_sha256':hashlib.sha256(original).hexdigest(),'output_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'changed_rotation_tracks':changed,'correction':'180 degree rest shin axis twist on left knee; inverse compensation on left ankle','preserved':'Mesh, weights, bind matrices, skeleton, materials, all other animation channels; ankle/downstream transforms preserved at keys up to floating point; interpolation error measured separately','maximum_shin_direction_error':max(errors),'status':'BLENDER_REVIEW_PENDING_UNREAL'}
 (OUT/(stem+'.json')).write_text(json.dumps(report,indent=2)+'\n');assert source.read_bytes()==original
 print(json.dumps(report))
def main():
 repair(ROOT/'model-rigged.glb','WalkLegRepair')
 repair(ROOT/'ContentSource/PilotGripPoseCandidate/DisembarkGripFit.glb','DisembarkLegRepair',True)
if __name__=='__main__':main()
