"""Measure existing posed glove surfaces directly from immutable glTF skinning data."""
from pathlib import Path
import hashlib,json,struct
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent

def read(path):
 raw=path.read_bytes();size=struct.unpack_from('<I',raw,12)[0]
 return json.loads(raw[20:20+size]),raw[28+size:]

def accessor(doc,binary,index):
 a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
 count={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
 dtype=np.dtype({5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]);offset=v.get('byteOffset',0)+a.get('byteOffset',0)
 data=np.ndarray((a['count'],count),dtype=dtype,buffer=binary,offset=offset,strides=(v.get('byteStride',count*dtype.itemsize),dtype.itemsize)).copy()
 if a.get('normalized'):data=data.astype(float)/np.iinfo(dtype).max
 return data

def matrix(t,q,s):
 x,y,z,w=q;out=np.eye(4);out[:3,:3]=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])@np.diag(s);out[:3,3]=t
 return out

def hierarchy(doc,binary,seconds):
 clip=doc['animations'][0];tracks={}
 for channel in clip['channels']:
  sampler=clip['samplers'][channel['sampler']];times=accessor(doc,binary,sampler['input']).ravel();values=accessor(doc,binary,sampler['output']);i=int(np.argmin(np.abs(times-seconds)));assert abs(times[i]-seconds)<1e-5
  tracks[(channel['target']['node'],channel['target']['path'])]=values[i]
 parents={child:i for i,node in enumerate(doc['nodes'])for child in node.get('children',[])};cache={}
 def world(i):
  if i not in cache:
   node=doc['nodes'][i];local=matrix(*[tracks.get((i,p),node.get(p,default))for p,default in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1])]])
   cache[i]=world(parents[i])@local if i in parents else local
  return cache[i]
 return [world(i)for i in range(len(doc['nodes']))]

CONVERT=np.array([[0,0,1],[1,0,0],[0,1,0]],dtype=float) # glTF -> Blender Rx90 -> ship Z90
ANCHOR=np.array([-15,0,72.])

def data():
 mesh,raw=read(ROOT/'ContentSource/Animation/TailCandidateV2.glb');primitive=mesh['meshes'][0]['primitives'][0];attr=primitive['attributes'];skin=mesh['skins'][0]
 positions=accessor(mesh,raw,attr['POSITION']);joints=accessor(mesh,raw,attr['JOINTS_0']);weights=accessor(mesh,raw,attr['WEIGHTS_0']);faces=accessor(mesh,raw,primitive['indices']).reshape(-1,3)
 inverse=accessor(mesh,raw,skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1);joint_names=[mesh['nodes'][i]['name']for i in skin['joints']]
 selections={}
 for side in ('L','R'):
  hand_joints=np.array([name.startswith(side+'_')and any(part in name for part in ('Wrist','Thumb','Index','Middle','Ring','Pinky'))for name in joint_names])
  influence=(weights*hand_joints[joints]).sum(1);face_mask=(influence[faces].min(1)>.35)&(influence[faces].max(1)>.6);selected_faces=faces[face_mask];ids=np.unique(selected_faces)
  lookup=np.full(len(positions),-1);lookup[ids]=np.arange(len(ids));selections[side]={'source_ids':ids,'faces':lookup[selected_faces],'positions':np.c_[positions[ids],np.ones(len(ids))],'joints':joints[ids],'weights':weights[ids]}
 return mesh,skin,inverse,selections

def pose(skin,inverse,selections,clip,binary,seconds):
 transforms=hierarchy(clip,binary,seconds);palette=np.array([transforms[i]for i in skin['joints']])@inverse;result={}
 for side,s in selections.items():
  matrices=palette[s['joints']];transformed=np.einsum('nkij,nj->nki',matrices,s['positions']);positions=(transformed*s['weights'][:,:,None]).sum(1)[:,:3]@CONVERT.T*150+ANCHOR
  result[side]=positions
 return result

def vertical_hits(vertices,faces,x,y):
 t=vertices[faces];a=t[:,0,:2];e1=t[:,1,:2]-a;e2=t[:,2,:2]-a;q=np.array([x,y])-a;det=e1[:,0]*e2[:,1]-e1[:,1]*e2[:,0];valid=np.abs(det)>1e-10
 u=np.zeros(len(t));v=u.copy();u[valid]=(q[valid,0]*e2[valid,1]-q[valid,1]*e2[valid,0])/det[valid];v[valid]=(e1[valid,0]*q[valid,1]-e1[valid,1]*q[valid,0])/det[valid];valid&=(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)
 ids=np.flatnonzero(valid);z=t[ids,0,2]+u[ids]*(t[ids,1,2]-t[ids,0,2])+v[ids]*(t[ids,2,2]-t[ids,0,2]);order=np.argsort(z)
 return [{'triangle':int(ids[k]),'z_cm':float(z[k]),'barycentric':[float(1-u[ids[k]]-v[ids[k]]),float(u[ids[k]]),float(v[ids[k]])]}for k in order]

def main():
 mesh,skin,inverse,selections=data();clip,binary=read(ROOT/'ContentSource/Animation/Pilot.glb');proxies={'L':[18.360598,21.082233],'R':[14.217013,-20.322160]};poses=pose(skin,inverse,selections,clip,binary,0)
 result={'status':'ACTUAL_SKINNED_GLOVE_SURFACE_MEASURED_SOURCE_ONLY','seconds':4,'sample_count':121,'method':'Original glTF linear-blend skinning of current TailV2 hand vertices; vertical underside rays at recorded palm proxy XY. All triangle indices refer to filtered hand selection; source vertex IDs included.','hands':{},'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [ROOT/'model-rigged.glb',ROOT/'ContentSource/Animation/Pilot.glb',ROOT/'ContentSource/Animation/TailCandidateV2.glb']}}
 for side,xy in proxies.items():
  s=selections[side];hits=vertical_hits(poses[side],s['faces'],*xy);assert hits
  result['hands'][side]={'selected_vertices':len(s['source_ids']),'selected_triangles':len(s['faces']),'ray_xy_cm':xy,'hits_at0':hits,'lowest_surface_source_vertex_ids':s['source_ids'][s['faces'][hits[0]['triangle']]].tolist(),'hand_bounds_at0_cm':[poses[side].min(0).tolist(),poses[side].max(0).tolist()],'underside_z_samples_cm':[]}
 for index in range(121):
  posed=pose(skin,inverse,selections,clip,binary,index/30)
  for side,xy in proxies.items():
   hits=vertical_hits(posed[side],selections[side]['faces'],*xy);assert hits,'Ray left hand surface'
   result['hands'][side]['underside_z_samples_cm'].append(hits[0]['z_cm'])
 for side,row in result['hands'].items():
  values=row['underside_z_samples_cm'];row['underside_z_range_cm']=[min(values),max(values)];row['provisional_tip_cm']=row['ray_xy_cm']+[sum(row['underside_z_range_cm'])/2]
 result['limits']=['Measured source skinning requires Blender/Unreal pose comparison.','Center ray alone does not establish complete radius1.8cm grip rim clearance.','Fixed grip cannot exactly follow breathing; report gap/penetration envelope and exit release separately.']
 (OUT/'ContactMeasurement.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({side:{key:value for key,value in row.items()if key!='underside_z_samples_cm'}for side,row in result['hands'].items()},indent=2))
if __name__=='__main__':main()
