import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Reject unsafe fixed-grip passages before baking any new animation.

The whole character follows a rigid hand frame. This preserves arm local
poses but may amplify source motion; explicit speed and body collision
measurements are therefore required. Outputs are private diagnostics.
"""
from pathlib import Path
exec(compile((_recipe_dir/'review_gb_body_supported_contact.py').read_text().split("cases=[('g1',881)]")[0],__file__,'exec'))
O=R/'GBSupportedMotionAudit';O.mkdir(exist_ok=True)
from load_supported_grip import load_supported_grip
fit=load_supported_grip(hashes)
target=Matrix(fit['hand_world_matrix']);finger_basis={n:Matrix(m) for n,m in fit['finger_local_matrices'].items()}
names=[b.name for b in ordered];index={n:i for i,n in enumerate(names)}
inverses=np.array([rest[n].inverted() for n in names])
meshes=[]
for ob in s.objects:
 if ob.type!='MESH' or ob==pole or ob.hide_render:continue
 mods=[m for m in ob.modifiers if m.type=='ARMATURE'];states=[m.show_viewport for m in mods]
 for m in mods:m.show_viewport=False
 bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());ev.data.calc_loop_triangles()
 points=np.array([tuple(ob.matrix_world@v.co)+(1,) for v in ev.data.vertices]);tri=np.array([t.vertices for t in ev.data.loop_triangles])
 assert len(points)==len(ob.data.vertices)
 joints=np.zeros((len(points),12),dtype=np.int32);weights=np.zeros((len(points),12));grip=np.zeros(len(points),dtype=bool)
 for v in ob.data.vertices:
  ws=[(index[ob.vertex_groups[g.group].name],g.weight) for g in v.groups if ob.vertex_groups[g.group].name in index and g.weight>0]
  assert len(ws)<=12
  total=sum(w for _,w in ws)
  for k,(j,w) in enumerate(ws):joints[v.index,k]=j;weights[v.index,k]=w/total
  grip[v.index]=sum(w for j,w in ws if names[j].endswith('_r') and names[j].startswith(('hand_','thumb_','index_','middle_','ring_','pinky_')))>.5
 for m,state in zip(mods,states):m.show_viewport=state
 meshes.append((ob.name,points,tri,joints,weights,grip))
bpy.context.view_layer.update()

def surface(p,mesh):
 _,points,tri,joints,weights,grip=mesh
 mat=np.array([p[n] for n in names])@inverses
 out=np.zeros((len(points),3))
 for k in range(12):
  out+=np.einsum('vij,vj->vi',mat[joints[:,k]],points)[:,:3]*weights[:,k,None]
 return out

def triangle_radii(points,tri):
 q=points[tri,:2];a=q;b=np.roll(q,-1,axis=1);e=b-a
 t=np.clip(-np.sum(a*e,axis=2)/np.maximum(np.sum(e*e,axis=2),1e-20),0,1)
 radius=np.linalg.norm(a+t[:,:,None]*e,axis=2).min(axis=1)
 cross=e[:,:,0]*(-a[:,:,1])-e[:,:,1]*(-a[:,:,0])
 inside=np.all(cross>=-1e-12,axis=1)|np.all(cross<=1e-12,axis=1)
 radius[inside]=0
 return radius

def supported(original):
 delta=target@original[hn].inverted()
 assert max(abs(v-1) for v in delta.to_scale())<.0002
 p={n:delta@m for n,m in original.items()}
 for pb in ordered:
  n=pb.name
  if n in finger_basis:p[n]=p[parent[n]]@rel[n]@finger_basis[n]
 return p

report={'sources':hashes,'grip_source':str(R/'GBSupportedThumbFit/Fit.json'),'clips':{},'limits':'Rigid support feasibility, no choreography or native acceptance. Triangle radial tests are conservative for faces crossing pole end caps.'}
for clip,act in acts.items():
 rig.animation_data_create();rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 frames=range(int(act.frame_range[0]),int(act.frame_range[1])+1);samples=[];motions=[];last=None;previous_velocity=None
 for frame in frames:
  s.frame_set(frame);bpy.context.view_layer.update();original={b.name:(rig.matrix_world@b.matrix).copy() for b in ordered};p=supported(original)
  pelvis=p['pelvis'];position=np.array(pelvis.translation);rotation=pelvis.to_quaternion()
  speed=angular=accel=0
  if last:
   velocity=(position-last[0])*60;speed=float(np.linalg.norm(velocity));angular=math.degrees(2*math.acos(min(1,abs(rotation.dot(last[1])))))*60
   if previous_velocity is not None:accel=float(np.linalg.norm(velocity-previous_velocity)*60)
   previous_velocity=velocity
  last=(position,rotation.copy());motions.append({'frame':frame,'speed_mps':speed,'angular_dps':angular,'accel_mps2':accel,'pelvis':position.tolist()})
  if (frame-frames.start)%6==0 or frame==frames.stop-1:
   collisions={};gripmin=1e9;bounds=[]
   for mesh in meshes:
    name,_,tri,_,_,grip=mesh;pts=surface(p,mesh);bounds.append(pts)
    rad=triangle_radii(pts,tri);z=pts[tri,2];insidez=(z.max(axis=1)>0)&(z.min(axis=1)<5)
    griptri=np.any(grip[tri],axis=1)
    if griptri.any():gripmin=min(gripmin,float(rad[griptri&insidez].min()-.025))
    bad=(rad<.025)&insidez&(~griptri)
    if bad.any():collisions[name]={'triangles':int(bad.sum()),'max_penetration_mm':float((.025-rad[bad]).max()*1000)}
   allpts=np.concatenate(bounds);samples.append({'frame':frame,'body_collisions':collisions,'grip_triangle_gap_mm':gripmin*1000,'bounds_m':[allpts.min(axis=0).tolist(),allpts.max(axis=0).tolist()]})
  if frame%300==0:print('SUPPORT_AUDIT',clip,frame,flush=True)
 report['clips'][clip]={'frame_range':[frames.start,frames.stop-1],'motions':motions,'surface_samples':samples,'max_speed_mps':max(x['speed_mps'] for x in motions),'max_angular_dps':max(x['angular_dps'] for x in motions),'max_accel_mps2':max(x['accel_mps2'] for x in motions),'collision_sample_count':sum(bool(x['body_collisions']) for x in samples),'worst_grip_triangle_gap_mm':min(x['grip_triangle_gap_mm'] for x in samples)}
 (O/'Audit.json').write_text(json.dumps(report,indent=2))
 print('SUPPORT_CLIP_DONE',clip,{k:v for k,v in report['clips'][clip].items() if k not in ('motions','surface_samples')},flush=True)
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
print('SUPPORTED_MOTION_AUDIT_DONE',flush=True)
