import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Fixed bone-derived coordinate conversion; eight independent native surfaces."""
import json,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
O=R/'G2PosteriorHip'
source=json.loads((O/'SourceControls.json').read_text());native=json.loads((O/'NativeCapture.json').read_text())
assert native['ok'] and source['source_sha256']==native['source_sha256']
rows={r['label']:r for r in source['rows']};captures=[r for r in native['captures'] if r['kind']=='still' and r['view']=='front']
first=captures[0];names=list(first['bones_world_cm']);src=np.array([rows[first['label']]['bones_m'][n] for n in names])*100;dst=np.array([first['bones_world_cm'][n] for n in names])
U,S,V=np.linalg.svd((src-src.mean(axis=0)).T@(dst-dst.mean(axis=0)));rotation=U@V;translation=dst.mean(axis=0)-src.mean(axis=0)@rotation
report={'source_sha256':source['source_sha256'],'basis':rotation.tolist(),'translation_cm':translation.tolist(),'bones':[],'surfaces':[]}
surfaces=np.load(O/'SourceSurfaces.npz')
def distances(query,ref):
    kd=KDTree(len(ref))
    for i,p in enumerate(ref):kd.insert(tuple(p),i)
    kd.balance();return np.array([kd.find(tuple(p))[2] for p in query])
for row in captures:
    expected=np.array([rows[row['label']]['bones_m'][n] for n in names])*100@rotation+translation
    actual=np.array([row['bones_world_cm'][n] for n in names]);error=np.linalg.norm(expected-actual,axis=1)
    report['bones'].append({'label':row['label'],'max_error_cm':float(error.max()),'bone':names[int(error.argmax())]})
    arrays={k:surfaces[k]*100@rotation+translation for k in surfaces.files if k.startswith(row['label']+'__')}
    points=np.concatenate(list(arrays.values()));actual=np.array(json.loads((O/'NativeViews'/(row['label']+'_Surface.json')).read_text())['vertices_world_cm'])
    forward=distances(actual,points);backward=distances(points,actual)
    report['surfaces'].append({'label':row['label'],'native_vertices':len(actual),'source_vertices':len(points),'native_to_source_max_cm':float(forward.max()),'source_to_native_max_cm':float(backward.max()),'parts':[{'name':n,'max_cm':float(distances(a,actual).max())} for n,a in arrays.items()]})
report['max_bone_error_mm']=max(r['max_error_cm'] for r in report['bones'])*10
report['max_surface_error_mm']=max(max(r['native_to_source_max_cm'],r['source_to_native_max_cm']) for r in report['surfaces'])*10
report['ok']=report['max_bone_error_mm']<.5 and report['max_surface_error_mm']<.5
(O/'NativeParity.json').write_text(json.dumps(report,indent=2));print('G2_POSTERIOR_PARITY',report['ok'],report['max_bone_error_mm'],report['max_surface_error_mm'],flush=True)
