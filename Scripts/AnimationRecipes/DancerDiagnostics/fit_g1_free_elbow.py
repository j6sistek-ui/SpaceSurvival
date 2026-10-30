"""Measure a minimal free-elbow opening; retain shoulders and held hand.

This probe does not save an action. It rejects missing contact-free solutions
and fits a smooth conservative envelope before a separate dense/visual review.
"""
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Quaternion
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from g1_palmar_motion_control import G1PalmarControl,relieve_free_arm
from validate_g2_contact_recipe import geometry, skin, triangle_radii

model=G1PalmarControl()
meshes=geometry(model)
inverses=np.array([model.rest[n].inverted() for n in model.names])
left=np.array([n.endswith('_l') and n.startswith(('lowerarm_','hand_','thumb_','index_','middle_','ring_','pinky_')) for n in model.names])
regions=[]
for mesh in meshes:
    _,_,faces,joints,weights,body,_=mesh
    mask=(weights*left[joints]).sum(axis=1)>.75
    regions.append((mesh,faces[np.all(mask[faces],axis=1)],body))


def contacts(pose):
    matrices=np.array([pose[n] for n in model.names])@inverses
    arms=[];arm_faces=[];bodies=[];body_faces=[];pole=0
    for mesh,af,bf in regions:
        points=skin(matrices,mesh)
        if len(af):
            radius=triangle_radii(points,af);z=points[af,2]
            pole+=int(((radius<.025-.00001)&(z.max(axis=1)>0)&(z.min(axis=1)<5)).sum())
            offset=len(arms);arms.extend(points.tolist());arm_faces.extend((af+offset).tolist())
        if len(bf):
            offset=len(bodies);bodies.extend(points.tolist());body_faces.extend((bf+offset).tolist())
    a=BVHTree.FromPolygons(arms,arm_faces,all_triangles=True)
    b=BVHTree.FromPolygons(bodies,body_faces,all_triangles=True)
    return len(a.overlap(b)),pole


rows=[]
reach_mode='--reach' in sys.argv
frames=[] if '--profile-only' in sys.argv else sorted(set(range(0,1101,20 if reach_mode else 10))|{1100})
for frame in frames:
    pose,_,_=model.pose(frame/60)
    a,b,c=[pose[n].translation for n in ('upperarm_l','lowerarm_l','hand_l')]
    upper=(b-a).normalized();lower=(c-b).normalized();axis=upper.cross(lower)
    bend=math.degrees(upper.angle(lower))
    trials=[];chosen=None
    candidates=[(0.,float(x)) for x in np.arange(0,min(48.,bend-10)+.001,2.)]
    if reach_mode:
        candidates=sorted([(float(r),float(e)) for r in range(0,28,3) for e in range(0,31,3) if e<=max(0,bend-10)],key=lambda x:x[0]**2*1.5+x[1]**2)
    for reach,angle in candidates:
        candidate={n:m.copy() for n,m in pose.items()}
        relieve_free_arm(model,candidate,reach,angle)
        body,pole=contacts(candidate)
        trials.append({'reach_degrees':reach,'degrees':float(angle),'body_pairs':body,'pole_pairs':pole})
        if not body and not pole:
            chosen=[reach,float(angle)] if reach_mode else float(angle);break
    rows.append({'seconds':frame/60,'elbow_before_degrees':bend,'required_degrees':chosen,'trials':trials})
    if frame%100==0:print('FREE_ELBOW',frame,chosen,flush=True)
result={'sources':model.guards,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'rows':rows,'unresolved':sum(r['required_degrees'] is None for r in rows),'scope':'Measured lower-arm-only opening; not visual acceptance or saved motion.'}
out=model.review/('G1PalmarGrip/FreeArmFit.json' if reach_mode else 'G1PalmarGrip/FreeElbowFit.json')
if '--profile-only' in sys.argv:
    assert reach_mode
    result=json.loads(out.read_text(encoding='utf-8'))
else:
    out.write_text(json.dumps(result,indent=2),encoding='utf-8')
if reach_mode and not result['unresolved']:
    rows=result['rows'];times=np.arange(1101)/60
    keys=np.array([r['seconds'] for r in rows])
    values=np.array([r['required_degrees'] for r in rows])
    profile={'seconds':times.tolist(),'fit_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
             'sources':model.guards,'scope':'Smooth conservative opening profile; must pass dense contacts and opposing visual review.'}
    kernel=np.exp(-.5*(np.arange(-18,19)/6.)**2);kernel/=kernel.sum()
    for column,name in enumerate(('reach_degrees','elbow_degrees')):
        base=np.interp(times,keys,values[:,column])
        padded=np.array([base[max(0,i-24):min(len(base),i+25)].max() for i in range(len(base))])
        padded+=1.5*(padded>0)
        profile[name]=np.convolve(np.pad(padded,(18,18),mode='edge'),kernel,mode='valid').tolist()
    destination=model.review/'G1PalmarGrip/FreeArmProfile.json'
    assert not destination.exists(),'Preserve previous profile'
    destination.write_text(json.dumps(profile,indent=2),encoding='utf-8')
model.assert_guards()
print('FREE_ELBOW_RESULT',result['unresolved'],flush=True)
