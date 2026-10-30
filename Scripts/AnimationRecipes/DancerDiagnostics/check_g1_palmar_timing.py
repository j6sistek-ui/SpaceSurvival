"""Both-arm direction checks and shared pacing for the G1 signed grip.

Targets describe this slow aerial passage, not universal anatomical limits.
The passage endpoints differ; a loop/join must be authored separately.
"""
import hashlib
import json
import math
import sys
from pathlib import Path
import numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from g1_palmar_motion_control import G1PalmarControl

model=G1PalmarControl(False,True,'--continuous-release' in sys.argv,'--pin-orientation' in sys.argv)
hinge={}
for side in ('l','r'):
    a,b,c=[model.rest[n+'_'+side] for n in ('upperarm','lowerarm','hand')]
    hinge[side]=a.to_quaternion().inverted() @ (b.translation-a.translation).cross(c.translation-b.translation).normalized()
previous=None;rates=[];roots=[];peaks=[];arms=[];unchanged=0.;support=0.
for frame in range(model.manifest['frame_end']):
    pose,original,phase=model.pose(frame/60)
    chest=pose['spine_05'].to_quaternion() @ model.rest['spine_05'].to_quaternion().inverted()
    forward=chest @ Vector((0,-1,0));up=chest @ Vector((0,0,1))
    for side in ('l','r'):
        a,b,c=[pose[n+'_'+side] for n in ('upperarm','lowerarm','hand')]
        upper=(b.translation-a.translation).normalized();lower=(c.translation-b.translation).normalized()
        axis=upper.cross(lower);bend=math.degrees(upper.angle(lower))
        alignment=(a.to_quaternion().inverted() @ axis.normalized()).dot(hinge[side]) if axis.length>.01 else 1.
        rear=math.degrees(math.asin(max(-1.,min(1.,-upper.dot(forward)))))
        hand=((pose['index_01_'+side].translation+pose['pinky_01_'+side].translation)*.5-c.translation).normalized()
        arms.append({'seconds':frame/60,'side':side,'bend':bend,'hinge_alignment':alignment,
                     'rear_degrees':rear,'rear_flag':rear>(12 if upper.dot(up)>0 else 2),
                     'wrist_direction_degrees':math.degrees(lower.angle(hand))})
    matrices=[]
    for n in model.names:
        if model.parents[n]:
            local=pose[model.parents[n]].inverted() @ pose[n]
            old=original[model.parents[n]].inverted() @ original[n]
            error=float(np.abs(np.array(local)-np.array(old)).max())
            if n in ('clavicle_r','upperarm_r','lowerarm_r','hand_r'):support=max(support,error)
            if n not in model.closed and n not in ('upperarm_l','lowerarm_l'):unchanged=max(unchanged,error)
        else:local=pose[n]
        matrices.append(local)
    quats=np.array([list(m.to_quaternion().normalized()) for m in matrices],dtype=float)
    if previous is not None:
        dots=np.clip(np.abs((quats*previous[0]).sum(axis=1)),0,1)
        angular=np.degrees(2*np.arccos(dots))*60
        i=int(angular.argmax());rates.append(float(angular[i]))
        roots.append(float((pose['pelvis'].translation-previous[1]).length*60))
        peaks.append({'seconds':frame/60,'bone':model.names[i],'dps':rates[-1],'pelvis_mps':roots[-1]})
    previous=(quats,pose['pelvis'].translation.copy())
    if frame%300==0:print('G1_SIGNED_TIMING',frame,flush=True)
rates=np.array(rates);roots=np.array(roots)
required=np.maximum(1.,np.maximum(rates/90.,roots/.45))
expanded=np.array([required[max(0,i-30):min(len(required),i+31)].max() for i in range(len(required))])
kernel=np.exp(-.5*(np.arange(-24,25)/8.)**2);kernel/=kernel.sum()
slow=np.convolve(np.pad(expanded,(24,24),mode='edge'),kernel,mode='valid')
assert np.all(slow+1e-9>=required)
destination=np.r_[0.,np.cumsum(slow)/60]
report={'sources':model.guards,'control_sha256':hashlib.sha256((Path(__file__).parent/'g1_palmar_motion_control.py').read_bytes()).hexdigest(),
        'samples':model.manifest['frame_end'],'source_seconds':model.duration,'destination_seconds':float(destination[-1]),
        'source_seconds_map':(np.arange(model.manifest['frame_end'])/60).tolist(),'destination_seconds_map':destination.tolist(),
        'maximum_local_dps':float(rates.max()),'maximum_pelvis_mps':float(roots.max()),
        'predicted_max_local_dps':float((rates/slow).max()),'predicted_max_pelvis_mps':float((roots/slow).max()),
        'unchanged_local_matrix_error':unchanged,'support_arm_local_matrix_error':support,
        'rear_flags':sum(r['rear_flag'] for r in arms),'hinge_flags':sum(r['hinge_alignment']<=0 and r['bend']>10 for r in arms),
        'fastest':sorted(peaks,key=lambda r:r['dps'],reverse=True)[:12],
        'fastest_root':sorted(peaks,key=lambda r:r['pelvis_mps'],reverse=True)[:6],'arms':arms,
        'scope':'Both-arm sampled owner reach screen and measured timing, not full anatomy, loop, saved replay or acceptance.'}
(model.output/'Timing.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
model.assert_guards()
print('G1_SIGNED_TIMING_RESULT',{k:v for k,v in report.items() if k not in ('sources','arms','fastest') and not k.endswith('_map')},flush=True)
