"""Read-only comparison of current G2 knee phrasing and original GLB source."""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parent))
from g2_floating_life_control import FloatingLifeControl

model=FloatingLifeControl()
out=model.project/'.agent/local/AnimationReview_20261025/G2FloatingLife/LegPhrase.json'
assert not out.exists(), 'Preserve prior audit'

def knee_angles(pose, names):
    result={}
    for side,bones in names.items():
        hip,knee,ankle=[pose[n].translation for n in bones]
        result[side]=math.degrees((knee-hip).angle(ankle-knee))
    return result

current=[]
for t in np.arange(0,model.duration,1/15):
    pose=model.base(float(t))
    current.append({'seconds':float(t),'knee_degrees':knee_angles(pose,{s:['thigh_'+s,'calf_'+s,'foot_'+s] for s in ('l','r')})})
model.assert_guards()
path=model.project/'SourceAssets/CharacterWorkshop_20261021/MotionSources/g2_default.glb'
source_hash=hashlib.sha256(path.read_bytes()).hexdigest()
assert source_hash=='1069f7e9f4a3db1d8d7688f1c303eaea7f99dd1c303010fcd5bd44a1e5b8a7aa'
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.render.fps=60
bpy.ops.import_scene.gltf(filepath=str(path))
rig=next(o for o in scene.objects if o.type=='ARMATURE')
action=rig.animation_data.action
start,end=map(float,action.frame_range)
raw=[]
for t in np.arange(0,(end-start)/60,1/15):
    f=start+t*60;scene.frame_set(math.floor(f),subframe=f%1);bpy.context.view_layer.update()
    pose={b.name:rig.matrix_world@b.matrix for b in rig.pose.bones}
    raw.append({'seconds':float(t),'knee_degrees':knee_angles(pose,{s:[s+'_upleg_JNT',s+'_leg_JNT',s+'_foot_JNT'] for s in ('l','r')})})

def summary(rows):
    return {'samples':len(rows),'both_below15_deg_fraction':sum(max(r['knee_degrees'].values())<15 for r in rows)/len(rows),
            'either_above45_deg_fraction':sum(max(r['knee_degrees'].values())>45 for r in rows)/len(rows),
            'range_degrees':{s:[min(r['knee_degrees'][s] for r in rows),max(r['knee_degrees'][s] for r in rows)] for s in ('l','r')}}

selected=[r for r in raw if (570-1)/60<=r['seconds']<=(770-1)/60]
report={'current_action_sha256':model.manifest['sha256'],'original_glb_sha256':source_hash,
        'current':summary(current),'raw_full':summary(raw),'raw_selected':summary(selected),
        'current_rows':current,'raw_rows':raw,
        'scope':'Geometric knee flex from hip/knee/ankle joint positions; fractions characterize phrasing, not medical limits or appearance acceptance. Current includes authored approach/release/reset and pacing; original full and selected source durations differ.'}
out.write_text(json.dumps(report,indent=2),encoding='utf-8')
print('LEG_PHRASE',{k:report[k] for k in ('current','raw_full','raw_selected')},flush=True)
assert hashlib.sha256(path.read_bytes()).hexdigest()==source_hash
