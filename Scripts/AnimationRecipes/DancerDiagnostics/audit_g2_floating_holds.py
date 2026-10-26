"""Measure held limb poses in the saved G2 passage, without changing it."""
import hashlib
import json
import math
import os
from pathlib import Path

import bpy
import numpy as np

project=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()
source=project/'SourceAssets/DanceRefinement_20261025'
out=project/'.agent/local/AnimationReview_20261025/G2FloatingLife'
out.mkdir(exist_ok=True)
manifest=json.loads((source/'G2_PalmarGrip_Knots_Manifest.json').read_text(encoding='utf-8'))
assert hashlib.sha256((source/manifest['file']).read_bytes()).hexdigest()==manifest['sha256']
assert not (out/'Baseline.json').exists(), 'Preserve prior audit'
bpy.ops.wm.open_mainfile(filepath=str(source/'Vexa_G1_ShoulderCap_Candidate.blend'),load_ui=False)
scene=bpy.context.scene
rig=next(o for o in scene.objects if o.type=='ARMATURE')
with bpy.data.libraries.load(str(source/manifest['file']),link=False) as (_,loaded):loaded.actions=[manifest['action']]
rig.animation_data.action=loaded.actions[0];rig.animation_data.action_slot=loaded.actions[0].slots[0]
names=[part+'_'+side for side in ('l','r') for part in ('thigh','calf','foot','upperarm','lowerarm','hand')]
times=np.unique(np.r_[np.arange(0,manifest['seconds'],1/15),manifest['seconds']])
quats=[];positions=[]
for seconds in times:
    frame=1+seconds*120;scene.frame_set(math.floor(frame),subframe=frame%1);bpy.context.view_layer.update()
    quats.append([tuple(rig.pose.bones[n].matrix_basis.to_quaternion().normalized()) for n in names])
    positions.append([tuple((rig.matrix_world@rig.pose.bones[n].matrix).translation) for n in names])
quats=np.array(quats,dtype=float);quats/=np.linalg.norm(quats,axis=2)[:,:,None]
positions=np.array(positions)
rows=[]
for seconds in np.arange(0,manifest['seconds']-2,2):
    indices=np.flatnonzero((times>=seconds)&(times<=seconds+2))
    angles=np.degrees(2*np.arccos(np.clip(np.abs((quats[indices]*quats[indices[0]]).sum(axis=2)),0,1)))
    drift=np.linalg.norm(positions[indices]-positions[indices[0]],axis=2)*1000
    rows.append({'start':float(seconds),'end':float(seconds+2),
        'local_range_degrees':dict(zip(names,angles.max(axis=0).tolist())),
        'world_drift_mm':dict(zip(names,drift.max(axis=0).tolist()))})
report={'action_sha256':manifest['sha256'],'samples':len(times),'rows':rows,
        'scope':'Two-second saved limb movement windows; not anatomical or appearance acceptance.'}
(out/'Baseline.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('QUIET_LEG_WINDOWS',[(r['start'],round(max(r['local_range_degrees'][n] for n in names if n.startswith(('thigh','calf'))),2)) for r in rows],flush=True)
