import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Fixed coordinate conversion from bones, then all-pose bone/surface parity."""
import json,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
O=R/'ZeroGSharedHip';source=json.loads((O/'Controls/Report.json').read_text());native=json.loads((O/'NativeControls.json').read_text());lookup={r['label']:r for r in source['rows']}
first=native['captures'][0];names=list(first['bones_world_cm']);src=np.array([lookup[first['label']]['bones_m'][n] for n in names])*100;dst=np.array([first['bones_world_cm'][n] for n in names]);A=src-src.mean(axis=0);B=dst-dst.mean(axis=0);U,S,V=np.linalg.svd(A.T@B);rotation=U@V;translation=dst.mean(axis=0)-src.mean(axis=0)@rotation
report={'basis_determinant':float(np.linalg.det(rotation)),'basis':rotation.tolist(),'translation_cm':translation.tolist(),'bone_samples':[],'surface_samples':[]}
for row in native['captures']:
 expected=np.array([lookup[row['label']]['bones_m'][n] for n in names])*100@rotation+translation;actual=np.array([row['bones_world_cm'][n] for n in names]);errors=np.linalg.norm(expected-actual,axis=1);i=int(errors.argmax());report['bone_samples'].append({'label':row['label'],'max_error_cm':float(errors[i]),'bone':names[i]})
surfaces=np.load(O/'Controls/PosedSurfaces.npz')
for path in sorted((O/'NativeControls').glob('*_Surface.json')):
 name=path.stem.replace('_Surface','');arrays={k:surfaces[k]*100@rotation+translation for k in surfaces.files if k.startswith(name+'_')};points=np.concatenate(list(arrays.values()));actual=np.array(json.loads(path.read_text())['vertices_world_cm'])
 def distances(queries,reference):
  kd=KDTree(len(reference))
  for i,p in enumerate(reference):kd.insert(tuple(p),i)
  kd.balance();return np.array([kd.find(tuple(p))[2] for p in queries])
 forward=distances(actual,points);backward=distances(points,actual)
 report['surface_samples'].append({'action':name,'source_vertices':len(points),'native_vertices':len(actual),'native_to_source_max_cm':float(forward.max()),'source_to_native_max_cm':float(backward.max()),'native_to_source_p95_cm':float(np.percentile(forward,95)),'parts':[{'name':n,'max_cm':float(distances(a,actual).max())} for n,a in arrays.items()]})
(O/'NativeParity.json').write_text(json.dumps(report,indent=2));print('BONE_MAX_CM',max(x['max_error_cm'] for x in report['bone_samples']),flush=True);print(json.dumps(report['surface_samples']),flush=True)
