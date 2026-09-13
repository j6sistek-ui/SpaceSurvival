"""Independent stdlib validation of new paired GLB rotation-patch transport."""
from pathlib import Path
import hashlib,json,struct,math
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
 raw=p.read_bytes();size=struct.unpack_from('<I',raw,12)[0];return json.loads(raw[20:20+size]),raw[28+size:]
def values(doc,raw,index):
 a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];assert a['componentType']==5126;start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',4*width);return b''.join(raw[start+i*stride:start+i*stride+4*width]for i in range(a['count']))
def main():
 record={'status':'SOURCE_PAIR_TRANSPORT_VALIDATED_NOT_UNREAL_IMPORTED','errors':[],'clips':[]};pair={}
 for base,name,kind in [('Pilot','PilotGripFit','Pilot'),('Disembark','DisembarkGripFit','Exit')]:
  source=ROOT/('ContentSource/Animation/'+base+'.glb');target=OUT/(name+'.glb');old,oldraw=read(source);new,newraw=read(target);patch=json.loads((OUT/(kind+'Rotations.json')).read_text());allowed=set(patch['rotations']);assert patch['base_sha256']==sha(source);assert newraw[:len(oldraw)]==oldraw
  for key in old:
   if key not in ('buffers','bufferViews','accessors','animations'):assert old[key]==new[key],key
  assert new['accessors'][:len(old['accessors'])]==old['accessors'];assert new['bufferViews'][:len(old['bufferViews'])]==old['bufferViews'];a=old['animations'][0];b=new['animations'][0];assert a['channels']==b['channels'];changed=[];unchanged=0;tracks={}
  for channel in a['channels']:
   index=channel['sampler'];sam=a['samplers'][index];new_sam=b['samplers'][index];bone=old['nodes'][channel['target']['node']].get('name');path=channel['target']['path'];assert sam['input']==new_sam['input']and sam.get('interpolation')==new_sam.get('interpolation');ov=values(old,oldraw,sam['output']);nv=values(new,newraw,new_sam['output']);assert len(ov)==len(nv);tracks[(bone,path)]=nv
   if path=='rotation'and bone in allowed:
    changed.append(bone)
    if kind=='Exit':assert ov[13*16:]==nv[13*16:],'Exit did not converge at sample13'
    quats=list(struct.iter_unpack('<ffff',nv));assert max(abs(sum(v*v for v in q)-1)for q in quats)<1e-4
   else:assert ov==nv,(bone,path);unchanged+=1
  assert set(changed)==allowed;pair[kind]=tracks;record['clips'].append({'kind':kind,'file':target.name,'bytes':target.stat().st_size,'sha256':sha(target),'base_sha256':sha(source),'original_binary_prefix_exact':len(oldraw),'changed_rotation_tracks':sorted(changed),'unchanged_channel_payloads':unchanged,'exact_original_all_tracks_from_seconds':13/30 if kind=='Exit'else None})
 for (bone,path),pv in pair['Pilot'].items():
  ev=pair['Exit'][(bone,path)];width=16 if path=='rotation'else 12
  if bone in json.loads((OUT/'PilotRotations.json').read_text())['rotations']and path=='rotation':assert pv[:width]==ev[:width],bone
 record['candidate_L_rotation_t0_exact_match']=True;record['limits']=['Original mesh, skin, materials, nodes and buffer prefix unchanged; this does not assert native animation import.','Existing root/pelvis trajectory is retained. Unreal root-motion extraction remains disabled by the existing runtime and must also be checked on any new imported sequences.','Source skin/clearance rendering is separately recorded; source transport equality is not visual acceptance.'];(OUT/'SourcePairValidation.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps(record,indent=2))
if __name__=='__main__':main()
