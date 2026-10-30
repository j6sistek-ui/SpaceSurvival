"""Fit a continuous wrist escape path against the actual opening hand surface.

No Blender asset writes. The two endpoint controls retain source finger poses.
Each accepted point must clear the pole; a penalty minimum alone is insufficient.
"""
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from mathutils import Matrix

sys.path.insert(0,str(Path(__file__).resolve().parent))
from g2_contact_recipe import smooth
from g2_palmar_motion_control import PalmarControl
from validate_g2_contact_recipe import geometry, skin, triangle_radii

model=PalmarControl(arm_ik=True)
mesh=next(m for m in geometry(SimpleNamespace(names=model.names,scene=model.scene)) if m[0]=='Vexa_Continuous_Hands')
_,_,triangles,joints,weights,_,_=mesh
mask=(weights*np.array([n.endswith('_r') and n.startswith(('hand_','thumb_','index_','middle_','ring_','pinky_')) for n in model.names])[joints]).sum(axis=1)>.5
triangles=triangles[np.all(mask[triangles],axis=1)]
inverse=np.array([model.rest[n].inverted() for n in model.names])
base,_,_=model.pose(5.)
base['hand_r']=Matrix(model.calibration['hand_world_matrix'])
paths=[]
for endpoint,neutral in enumerate(model.neutral):
    previous=np.zeros(2);rows=[]
    for step in range(101):
        u=step/100
        pose={n:m.copy() for n,m in base.items()}
        for n in model.names:
            if n in model.closed:
                pose[n]=pose[model.parents[n]]@model.relative[n]@model.closed[n].lerp(neutral[n],u)
        points=skin(np.array([pose[n] for n in model.names])@inverse,mesh)
        low=points[triangles,:2].min(axis=1);high=points[triangles,:2].max(axis=1)
        clearance=.00002+.001*smooth(u/.15)
        goal=np.array((.016*u+.22*math.sin(math.pi*u)**2,-.505*u+.3*math.sin(math.pi*u)))
        def radius(shift):
            center=-shift
            near=np.all((low<center+.028)&(high>center-.028),axis=1)
            if not near.any():return .028
            translated=points.copy();translated[:,:2]+=shift
            return float(triangle_radii(translated,triangles[near]).min())
        def loss(shift):
            penetration=max(0.,.025+clearance-radius(shift))
            return 10000*penetration*penetration+float(np.sum((shift-goal)**2))+.15*float(np.sum((shift-previous)**2))
        candidates=[]
        for start in (previous,goal,goal+np.array((.035,.035))):
            q=start.copy()
            for size in (.016,.008,.004,.002,.001,.0005,.00025):
                for _ in range(12):
                    options=[q+np.array((x,y))*size for x,y in ((0,0),(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1))]
                    winner=min(options,key=loss)
                    if np.array_equal(winner,q):break
                    q=winner
            candidates.append((loss(q),q,radius(q)))
        _,winner,minimum=min(candidates,key=lambda x:x[0])
        if step==0:
            winner=np.zeros(2);minimum=radius(winner)
        rows.append({'opening':u,'offset_xy_m':winner.tolist(),'minimum_radius_m':minimum,'goal_xy_m':goal.tolist()})
        previous=winner
        if step%20==0:print('PALMAR_PATH',endpoint,step,winner.tolist(),minimum,flush=True)
    paths.append(rows)
report={'sources':model.guards,'paths':paths,'flags':sum(r['minimum_radius_m']<.02499 for path in paths for r in path),'max_offset_step_m':max(float(np.linalg.norm(np.subtract(b['offset_xy_m'],a['offset_xy_m']))) for path in paths for a,b in zip(path,path[1:])), 'scope':'Private hand-only path. Full-body IK, between-sample contact, speed and visual checks required.'}
(model.review/'G2PalmarGrip/ReleasePaths.json').write_text(json.dumps(report,indent=2))
model.assert_guards()
print('PALMAR_PATH_RESULT',report['flags'],report['max_offset_step_m'],flush=True)
