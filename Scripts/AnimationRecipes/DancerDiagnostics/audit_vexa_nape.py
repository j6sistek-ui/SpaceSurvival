import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""CPU-only localization of the nape fold; never saves the source scene."""
import bpy, json, math, hashlib
from pathlib import Path
import numpy as np
P=R.parents[2]
O=R/'VexaNape';O.mkdir(exist_ok=True)
src=P/'SourceAssets/DanceRefinement_20261025/Vexa_CoordinatedSymmetry_Proof.blend'
before=hashlib.sha256(src.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');ob=bpy.data.objects['Vexa_Nude_Torso']
rest=np.array([list(ob.matrix_world@v.co) for v in ob.data.vertices])
edges={}
for f in ob.data.polygons:
 for a,b in f.edge_keys:edges.setdefault(tuple(sorted((a,b))),[]).append(f.index)
polys=[list(f.vertices) for f in ob.data.polygons]
def normals(points):
 result=[]
 for face in polys:
  a,b,c=points[face[:3]];n=np.cross(b-a,c-a);result.append(n/max(1e-12,np.linalg.norm(n)))
 return np.array(result)
rn=normals(rest);rows=[]
for frame in (241,543,733):
 s.frame_set(frame);bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());points=np.array([list(ev.matrix_world@v.co) for v in ev.data.vertices]);pn=normals(points)
 flags=[]
 for (a,b),faces in edges.items():
  mid=(rest[a]+rest[b])*.5
  if len(faces)!=2 or abs(mid[0])>.105 or not 1.37<mid[2]<1.54 or mid[1]<0:continue
  i,j=faces;ra=math.degrees(math.acos(np.clip(rn[i]@rn[j],-1,1)));pa=math.degrees(math.acos(np.clip(pn[i]@pn[j],-1,1)))
  flags.append({'edge':[a,b],'rest_mid_m':mid.tolist(),'rest_dihedral_deg':ra,'posed_dihedral_deg':pa,'angle_change_deg':pa-ra,'length_ratio':float(np.linalg.norm(points[b]-points[a])/np.linalg.norm(rest[b]-rest[a]))})
 flags.sort(key=lambda x:x['angle_change_deg'],reverse=True);rows.append({'frame':frame,'worst_edges':flags[:20]})
ids=sorted(set(i for row in rows for edge in row['worst_edges'] for i in edge['edge']))
vertices=[{'id':i,'rest_m':rest[i].tolist(),'weights':{ob.vertex_groups[g.group].name:g.weight for g in ob.data.vertices[i].groups if g.weight>1e-5}} for i in ids]
rest_bones={b.name:list((rig.matrix_world@b.matrix_local).translation) for b in rig.data.bones if b.name.startswith(('spine','neck','head','clavicle'))}
report={'source_sha256':before,'bone_heads_m':rest_bones,'rows':rows,'vertices':vertices,'status':'GEOMETRY LOCALIZATION ONLY; NOT A QUALITY PASS'}
assert hashlib.sha256(src.read_bytes()).hexdigest()==before
(O/'Audit.json').write_text(json.dumps(report,indent=2));print('NAPE_AUDIT_DONE',json.dumps({'bone_heads_m':rest_bones,'worst':rows[1]['worst_edges'][:6],'vertices':vertices[:5]}),flush=True)
