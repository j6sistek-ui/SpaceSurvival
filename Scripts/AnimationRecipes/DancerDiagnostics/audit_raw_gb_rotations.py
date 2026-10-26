import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Read supplied GLB quaternion keys directly, before import/retarget filters."""
import json,struct,math,hashlib
from pathlib import Path
import numpy as np
P=R.parents[2];report=[]
for clip in ('g1','g2','b1','b2'):
 file=P/'SourceAssets/CharacterWorkshop_20261021/MotionSources'/f'{clip}_default.glb';data=file.read_bytes();at=12;doc=None;binary=None
 while at<len(data):
  size,kind=struct.unpack_from('<II',data,at);chunk=data[at+8:at+8+size];at+=8+size
  if kind==0x4e4f534a:doc=json.loads(chunk)
  elif kind==0x004e4942:binary=chunk
 def values(index):
  a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];dtype={5126:'<f4',5123:'<u2',5125:'<u4'}[a['componentType']];components={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']];offset=v.get('byteOffset',0)+a.get('byteOffset',0);item=np.dtype(dtype).itemsize
  return np.ndarray((a['count'],components),dtype=dtype,buffer=binary,offset=offset,strides=(v.get('byteStride',item*components),item)).copy().astype(float)
 tracks=[]
 for animation in doc.get('animations',[]):
  for channel in animation['channels']:
   if channel['target']['path']!='rotation':continue
   sampler=animation['samplers'][channel['sampler']];name=doc['nodes'][channel['target']['node']].get('name','');q=values(sampler['output']);t=values(sampler['input']).flatten()
   assert sampler.get('interpolation','LINEAR')=='LINEAR'
   q/=np.linalg.norm(q,axis=1)[:,None];step=2*np.degrees(np.arccos(np.clip(abs(np.sum(q[1:]*q[:-1],axis=1)),0,1)));dt=np.diff(t);speed=step/dt
   if any(k in name.lower() for k in ('arm','leg','neck','spine')):
    order=np.argsort(speed)[-5:][::-1];tracks.append({'bone':name,'keys':len(t),'seconds':float(t[-1]-t[0]),'worst':[{'key':int(i+1),'time':float(t[i+1]),'step_deg':float(step[i]),'dt':float(dt[i]),'deg_per_second':float(speed[i])} for i in order]})
 report.append({'clip':clip,'sha256':hashlib.sha256(data).hexdigest(),'tracks':tracks})
 print(clip,[(r['bone'],round(r['worst'][0]['deg_per_second'],2),round(r['worst'][0]['time'],3)) for r in tracks])
(R/'GBFingerShape/RawRotationAudit.json').write_text(json.dumps(report,indent=2))
