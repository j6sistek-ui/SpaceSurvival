import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Dense geometry and joint-continuity screen of the one routed passage.

This is a diagnostic, not a clinical range-of-motion or choreography approval.
No native or source assets are overwritten.
"""
from pathlib import Path
exec(compile((_recipe_dir/'audit_supported_contact_motion.py').read_text().split("report={'sources':hashes,'grip_source'")[0],__file__,'exec'))
import sys
import os
sys.path.insert(0,str(_recipe_dir))
from route_supported_free_arm import route_free_arm
from align_supported_elbow import align_elbow
from mathutils.bvhtree import BVHTree
hinge=bool(os.environ.get('SS_ROUTE_HINGE'))
keypose=bool(os.environ.get('SS_ROUTE_KEYPOSE'))
if keypose:from route_supported_free_arm_keypose import route_free_arm
O=R/('GBSupportedPassageKeypose' if keypose else 'GBSupportedPassageHinge' if hinge else 'GBSupportedPassageRouted2');O.mkdir(exist_ok=True)
start,end=780,1000;rate=.2;fps=120
act=acts['g1'];rig.animation_data_create();rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
originals=[]
for frame in range(start,end+1):
 s.frame_set(frame);bpy.context.view_layer.update();originals.append({b.name:(rig.matrix_world@b.matrix).copy() for b in ordered})
rig.animation_data_clear()
if keypose:
 reference=originals[881-start]
 route_free_arm.rig_data=(parent,rel,names,{n:(reference[parent[n]]@rel[n]).inverted()@reference[n] for n in ['clavicle_l','upperarm_l','lowerarm_l','hand_l']})
 route_free_arm.branch=set(desc['clavicle_l'])
route_free_arm.controls=[]
for frame,goal in [(934,None),(941,(.28,-.20,3.75)),(946,(.30,.15,3.85)),(954,(.05,.25,3.45)),(962,None)]:
 original=supported(originals[frame-start])['hand_l'].translation
 route_free_arm.controls.append((frame,Vector(goal)-original if goal else Vector((0,0,0))))
def local(p,n):
 base=p[parent[n]]@rel[n] if parent[n] else rel[n]
 return base.inverted()@p[n]
def angle(a,b):return math.degrees(2*math.acos(min(1,abs(a.to_quaternion().dot(b.to_quaternion())))))
def hinge_offaxis(m):
 q=m.to_quaternion();z=Quaternion((q.w,0,0,q.z));z.normalize()
 return math.degrees(2*math.acos(min(1,abs(q.dot(z)))))
# Separate free forearm/hand faces from head and torso faces. Interfaces
# with the same shoulder are excluded, not tested as self-collision.
regions=[]
for mesh in meshes:
 name,_,tri,joints,weights,_=mesh
 arm=np.array([n.endswith('_l') and n.startswith(('lowerarm','calf_DO_NOT_MATCH','hand','thumb','index','middle','ring','pinky')) for n in names])
 body=np.array([n.startswith(('spine','neck','head','pelvis')) for n in names])
 aw=(arm[joints]*weights).sum(axis=1);bw=(body[joints]*weights).sum(axis=1)
 regions.append((tri[np.all(aw[tri]>.75,axis=1)],tri[np.all(bw[tri]>.75,axis=1)]))
rows=[];last=None;previous_velocity=None
total=round((end-start)/60/rate*fps)
for i in range(total+1):
 source=start+i/fps*60*rate;lo=min(int(source)-start,end-start);hi=min(lo+1,end-start);frac=source-start-lo
 original={n:originals[lo][n].lerp(originals[hi][n],frac) for n in names}
 baseline=supported(original);p={n:m.copy() for n,m in baseline.items()};route=route_free_arm(p,source,rotate)
 correction=align_elbow(p,rest,rel,desc,source) if hinge else {'active':False}
 row={'sample':i,'time':i/fps,'source_frame':source,'route':route,'elbow_plane':correction}
 # Explicitly protect the supporting arm's local shape and finger contact.
 protected=[n for n in names if n.endswith('_r') and n.startswith(('clavicle','upperarm','lowerarm','hand','thumb','index','middle','ring','pinky'))]
 row['support_local_error']=max(max(abs(local(p,n)[x][y]-local(baseline,n)[x][y]) for x in range(4) for y in range(4)) for n in protected)
 assert row['support_local_error']<.0001
 row['elbow_source_offaxis_deg']=hinge_offaxis(local(baseline,'lowerarm_l'))
 row['elbow_routed_offaxis_deg']=hinge_offaxis(local(p,'lowerarm_l'))
 row['local_step_deg']={}
 row['hand_speed_mps']=0;row['hand_acceleration_mps2']=0
 if last:
  row['local_step_deg']={n:angle(local(p,n),local(last,n)) for n in ['upperarm_l','lowerarm_l','hand_l']}
  velocity=(p['hand_l'].translation-last['hand_l'].translation)*fps
  row['hand_speed_mps']=velocity.length
  if previous_velocity is not None:row['hand_acceleration_mps2']=(velocity-previous_velocity).length*fps
  previous_velocity=velocity.copy()
 last={n:m.copy() for n,m in p.items()}
 # Dense all-surface check only around the altered interval; untouched
 # passage has the existing 24fps screen. This is not continuous collision.
 if 932<=source<=976:
  collisions={};armpts=[];armfaces=[];bodypts=[];bodyfaces=[]
  for mesh,(at,bt) in zip(meshes,regions):
   name,_,tri,_,_,grip=mesh;pts=surface(p,mesh);rad=triangle_radii(pts,tri);z=pts[tri,2]
   bad=(rad<.025)&(~np.any(grip[tri],axis=1))&(z.max(axis=1)>0)&(z.min(axis=1)<5)
   if bad.any():collisions[name]={'triangles':int(bad.sum()),'penetration_mm':float((.025-rad[bad]).max()*1000)}
   offset=len(armpts);armpts.extend(pts.tolist());armfaces.extend((at+offset).tolist())
   offset=len(bodypts);bodypts.extend(pts.tolist());bodyfaces.extend((bt+offset).tolist())
  row['body_pole_collisions']=collisions
  # Every half source frame is sufficient to flag obvious body penetration
  # for visual review; it is not a watertight garment collision certificate.
  if i%5==0 and armfaces and bodyfaces:
   ta=BVHTree.FromPolygons(armpts,armfaces,all_triangles=True)
   tb=BVHTree.FromPolygons(bodypts,bodyfaces,all_triangles=True)
   row['free_arm_body_triangle_overlaps']=len(ta.overlap(tb))
 rows.append(row)
 if i%500==0:print('DENSE_ROUTE',i,flush=True)
summary={'samples':len(rows),'dense_surface_samples':sum('body_pole_collisions' in x for x in rows),
 'pole_collision_samples':[{'frame':x['source_frame'],'parts':x['body_pole_collisions']} for x in rows if x.get('body_pole_collisions')],
 'body_overlap_samples':[{'frame':x['source_frame'],'pairs':x['free_arm_body_triangle_overlaps']} for x in rows if x.get('free_arm_body_triangle_overlaps',0)],
 'max_elbow_source_offaxis_deg':max(x['elbow_source_offaxis_deg'] for x in rows),
 'max_elbow_routed_offaxis_deg':max(x['elbow_routed_offaxis_deg'] for x in rows),
 'max_local_step_deg':{n:max(x['local_step_deg'].get(n,0) for x in rows) for n in ['upperarm_l','lowerarm_l','hand_l']},
 'max_hand_speed_mps':max(x['hand_speed_mps'] for x in rows),'max_hand_acceleration_mps2':max(x['hand_acceleration_mps2'] for x in rows)}
(O/'DenseAudit.json').write_text(json.dumps({'sources':hashes,'summary':summary,'samples':rows,'limitations':'No ground-truth anatomical limit, no complete release/regrip, no continuous collision certificate.'},indent=2))
print(json.dumps(summary),flush=True)
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
