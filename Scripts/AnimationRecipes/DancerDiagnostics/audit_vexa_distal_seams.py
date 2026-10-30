import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Inspect modular hand/foot joins without changing source geometry or weights."""
import bpy,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import kdtree
P=R.parents[2]
path=P/'SourceAssets/DanceRefinement_20261025/Vexa_AxillaLocal_Proof.blend'
before=hashlib.sha256(path.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
objects=[o for o in s.objects if o.type=='MESH' and not o.hide_render]
report={'proof_sha256':before,'objects':[{'name':o.name,'vertices':len(o.data.vertices),'modifiers':[(m.name,m.type) for m in o.modifiers]} for o in objects],'pairs':{}}
def coords(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 values=np.array([tuple(ev.matrix_world@v.co) for v in me.vertices]);ev.to_mesh_clear();return values
def weights(ob,index):return {ob.vertex_groups[g.group].name:g.weight for g in ob.data.vertices[index].groups if g.weight>1e-7}
s.frame_set(1);rig.data.pose_position='REST';bpy.context.view_layer.update()
rest={o.name:coords(o) for o in objects}
for distal,proximal in [('Feet','Nude_Legs'),('Hands','Nude_Torso')]:
 a=next(o for o in objects if distal.lower() in o.name.lower());b=next(o for o in objects if proximal.lower() in o.name.lower())
 tree=kdtree.KDTree(len(rest[b.name]))
 for i,v in enumerate(rest[b.name]):tree.insert(v,i)
 tree.balance();pairs=[]
 for i,v in enumerate(rest[a.name]):
  _,j,d=tree.find(v)
  if d<.0001:pairs.append((i,j,float(d)))
 report['pairs'][distal]={'distal':a.name,'proximal':b.name,'rest_coincident_count':len(pairs),'pairs':pairs,'weight_examples':[{'indices':[i,j],'distal':weights(a,i),'proximal':weights(b,j)} for i,j,_ in pairs[::max(1,len(pairs)//5)]],'posed':[]}
rig.data.pose_position='POSE'
for sec in (0,4,8,9.033333,11.966667,12.2,16):
 f=1+sec*60;s.frame_set(int(f),subframe=f%1);bpy.context.view_layer.update()
 for entry in report['pairs'].values():
  a=coords(bpy.data.objects[entry['distal']]);b=coords(bpy.data.objects[entry['proximal']])
  errors=[float(np.linalg.norm(a[i]-b[j])) for i,j,_ in entry['pairs']]
  entry['posed'].append({'seconds':sec,'max_gap_mm':max(errors,default=-1)*1000,'p95_gap_mm':float(np.percentile(errors,95))*1000 if errors else None})
assert hashlib.sha256(path.read_bytes()).hexdigest()==before
(R/'VexaEndJoints/Seams.json').write_text(json.dumps(report,indent=2))
print('DISTAL_SEAMS',json.dumps({k:{'pairs':v['rest_coincident_count'],'samples':v['posed']} for k,v in report['pairs'].items()}),flush=True)
