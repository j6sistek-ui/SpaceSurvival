import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""One fixed basis/scale conversion across nine native pose samples."""
from pathlib import Path
import json,numpy as np
source=json.loads((R/'GBSupportedRelease/Export.json').read_text())
native=json.loads((R/'NativeSupportedRelease/Capture.json').read_text())
assert native['ok'] and native['old_proof_unchanged']
first=next(iter(source['expected_bones']))
names=list(source['expected_bones'][first])
a=np.array([np.array(source['expected_bones'][first][n])[:3,3] for n in names])*100
b=np.array([native['bone_samples'][first][n] for n in names])
# The actor origin is explicitly subtracted in the native capture. Do not
# fit a new translation, scale or basis per frame and hide root-path errors.
u,_,vt=np.linalg.svd(a.T@b);basis=u@vt
rows=[]
for frame,bones in source['expected_bones'].items():
 a=np.array([np.array(bones[n])[:3,3] for n in names])*100
 b=np.array([native['bone_samples'][frame][n] for n in names])
 error=np.linalg.norm(a@basis-b,axis=1)*10
 rows.append({'frame':int(frame),'maximum_mm':float(error.max()),'rms_mm':float(np.sqrt(np.mean(error**2))),'worst_bone':names[int(error.argmax())]})
result={'source_sha256':source['sha256'],'basis':basis.tolist(),'basis_determinant':float(np.linalg.det(basis)),'bone_count':len(names),'samples':rows,'maximum_mm':max(x['maximum_mm'] for x in rows),'scope':'Bone transfer only, no anatomical or full motion acceptance.'}
assert result['maximum_mm']<.5,result
(R/'NativeSupportedRelease/BoneParity.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
