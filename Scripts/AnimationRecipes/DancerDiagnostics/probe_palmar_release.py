"""Check finger opening at the fixed corrected wrist before adding a path."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from mathutils import Matrix

sys.path.insert(0,str(Path(__file__).resolve().parent))
from g2_palmar_motion_control import PalmarControl
from validate_g2_contact_recipe import geometry, skin, triangle_radii

model=PalmarControl(arm_ik=True)
mesh=next(m for m in geometry(SimpleNamespace(names=model.names,scene=model.scene)) if m[0]=='Vexa_Continuous_Hands')
_,_,tris,joints,weights,_,_=mesh
right=(weights*np.array([n.endswith('_r') for n in model.names])[joints]).sum(axis=1)>.5
tris=tris[np.all(right[tris],axis=1)]
inverse=np.array([model.rest[n].inverted() for n in model.names])
base,_,_=model.pose(5.)
base['hand_r']=Matrix(model.calibration['hand_world_matrix'])
rows=[]
neutral_options=model.neutral
if '--rest-neutral' in sys.argv:
    neutral_options=[{n:Matrix.Identity(4) for n in model.closed}]
for endpoint,neutral in enumerate(neutral_options):
    for step in range(101):
        opening=step/100
        pose={n:m.copy() for n,m in base.items()}
        for n in model.names:
            if n in model.closed:
                pose[n]=pose[model.parents[n]]@model.relative[n]@model.closed[n].lerp(neutral[n],opening)
        points=skin(np.array([pose[n] for n in model.names])@inverse,mesh)
        minimum=float(triangle_radii(points,tris).min())
        regions={}
        for region in ('thumb','index','middle','ring','pinky','hand'):
            mask=(weights*np.array([n.startswith(region+'_') and n.endswith('_r') for n in model.names])[joints]).sum(axis=1)>.5
            selected=tris[np.all(mask[tris],axis=1)]
            if len(selected):regions[region]=float(triangle_radii(points,selected).min())
        row={'endpoint':endpoint,'opening':opening,'minimum_radius_m':minimum,'regions':regions}
        if step in (0,50,100):
            row['joint_positions']={n:list(pose[n].translation) for n in model.closed if n.startswith(('pinky_','thumb_'))}
        rows.append(row)
report={'sources':model.guards,'rows':rows,'flagged':sum(r['minimum_radius_m']<.02499 for r in rows)}
(model.review/('G2PalmarGrip/RestNeutralOpening.json' if '--rest-neutral' in sys.argv else 'G2PalmarGrip/FixedWristOpening.json')).write_text(json.dumps(report,indent=2))
print('FIXED_WRIST_OPENING',report['flagged'],min(r['minimum_radius_m'] for r in rows),flush=True)
model.assert_guards()
