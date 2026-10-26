"""Measure actual local joint speeds and plan shared monotone pacing, unsaved.

Use the same PalmarControl arguments. Pacing targets are artistic choices for
this routine, not anatomical limits. No source/mesh/action is overwritten.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parent))
from g2_palmar_motion_control import PalmarControl, options

model=PalmarControl(*options())
previous=None; rates=[]; roots=[]; peaks=[]; locals=[]
for frame in range(model.manifest['frame_end']):
    pose,_,_=model.pose(frame/60)
    matrices=[pose[model.parents[n]].inverted()@pose[n] if model.parents[n] else pose[n] for n in model.names]
    quats=np.array([list(m.to_quaternion().normalized()) for m in matrices],dtype=float)
    if previous is not None:
        dots=np.clip(np.abs((quats*previous[0]).sum(axis=1)),0,1)
        angular=np.degrees(2*np.arccos(dots))*60
        index=int(angular.argmax())
        rates.append(float(angular[index]));roots.append(float((pose['pelvis'].translation-previous[1]).length*60))
        peaks.append({'time':frame/60,'bone':model.names[index],'dps':rates[-1]})
    previous=(quats,pose['pelvis'].translation.copy())
    if frame%600==0: print('PALMAR_TIMING',frame,flush=True)
rates=np.array(rates);roots=np.array(roots)
required=np.maximum(1.,np.maximum(rates/90.,roots/.45))
expanded=np.array([required[max(0,i-30):min(len(required),i+31)].max() for i in range(len(required))])
kernel=np.exp(-.5*(np.arange(-24,25)/8.)**2);kernel/=kernel.sum()
slow=np.convolve(np.pad(expanded,(24,24),mode='edge'),kernel,mode='valid')
assert np.all(slow+1e-9>=required)
destination=np.r_[0.,np.cumsum(slow)/60]
report={'sources':model.guards,'control_sha256':hashlib.sha256((Path(__file__).parent/'g2_palmar_motion_control.py').read_bytes()).hexdigest(),
        'samples':model.manifest['frame_end'],'source_seconds':model.duration,'destination_seconds':float(destination[-1]),
        'source_seconds_map':(np.arange(model.manifest['frame_end'])/60).tolist(),'destination_seconds_map':destination.tolist(),
        'angular_target_dps':90.,'root_target_mps':.45,'maximum_local_dps':float(rates.max()),'maximum_pelvis_mps':float(roots.max()),
        'predicted_max_local_dps':float((rates/slow).max()),'predicted_max_pelvis_mps':float((roots/slow).max()),
        'fastest':sorted(peaks,key=lambda r:r['dps'],reverse=True)[:16],
        'scope':'Measured60Hz local rotations and pelvis path; predicted shared retime only, not saved replay or artistic acceptance.'}
(model.output/'Timing.json').write_text(json.dumps(report,indent=2))
model.assert_guards()
print('PALMAR_TIMING_RESULT',{k:v for k,v in report.items() if not k.endswith('_map') and k!='sources'},flush=True)
