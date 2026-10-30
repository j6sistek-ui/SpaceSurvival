import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Read the heel's deformation influences before changing them."""
import bpy,json,hashlib,numpy as np
from pathlib import Path
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
src=D/'Vexa_HandIsolation_Proof.blend';digest=hashlib.sha256(src.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');ob=bpy.data.objects['Vexa_Continuous_Feet']
points=np.array([tuple(ob.matrix_world@v.co) for v in ob.data.vertices]);report={'source_sha256':digest,'sides':{}}
for side in ['l','r']:
 j=np.array(rig.matrix_world@rig.data.bones['foot_'+side].head_local);b=np.array(rig.matrix_world@rig.data.bones['ball_'+side].head_local)
 forward=b-j;forward[2]=0;forward/=np.linalg.norm(forward)
 delta=points-j;y=delta@forward;z=delta[:,2];dist=np.linalg.norm(delta,axis=1)
 rows=[]
 for v in ob.data.vertices:
  if dist[v.index]<.12 and y[v.index]<.005:
   rows.append({'index':v.index,'xyz_m':points[v.index].tolist(),'forward_m':float(y[v.index]),'height_m':float(z[v.index]),'weights':{ob.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>.0001}})
 report['sides'][side]={'joint':j.tolist(),'ball':b.tolist(),'heel_vertices':rows}
(R/'AnkleWeights.json').write_text(json.dumps(report,indent=2))
print('ANKLE_WEIGHTS',json.dumps({k:{'joint':v['joint'],'ball':v['ball'],'count':len(v['heel_vertices']),'examples':v['heel_vertices'][::max(1,len(v['heel_vertices'])//6)]} for k,v in report['sides'].items()}),flush=True)
assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
