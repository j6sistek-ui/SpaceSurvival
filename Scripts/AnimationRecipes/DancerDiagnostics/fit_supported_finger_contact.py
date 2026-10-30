import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Constrained local finger/pole fit; all arm local transforms stay unchanged.

CPU skinning evaluates only the hand neighborhood. Bounds are editable pose
design limits, not medical anatomy rules. No production files are written.
"""
import os, itertools
os.environ.pop('SS_CONTACT_CLOSEUP',None)
from pathlib import Path
code=(_recipe_dir/'review_gb_body_supported_contact.py').read_text()
exec(compile(code.split("cases=[('g1',881)]")[0],__file__,'exec'))
O=R/'GBSupportedFingerFit2';O.mkdir(exist_ok=True)
rig.animation_data_create();rig.animation_data.action=acts['g1'];rig.animation_data.action_slot=acts['g1'].slots[0]
s.frame_set(881);bpy.context.view_layer.update()
original={b.name:(rig.matrix_world@b.matrix).copy() for b in ordered}
original_local={b.name:b.matrix_basis.copy() for b in ordered}
root_delta=target@original[hn].inverted(); p0={n:root_delta@m for n,m in original.items()}
rig.animation_data_clear()
hands=bpy.data.objects['Vexa_Continuous_Hands']; arm=next(m for m in hands.modifiers if m.type=='ARMATURE')
arm.show_viewport=False;bpy.context.view_layer.update();ev=hands.evaluated_get(bpy.context.evaluated_depsgraph_get())
restpoints=np.array([tuple(hands.matrix_world@v.co)+(1,) for v in ev.data.vertices]);arm.show_viewport=True
names=[b.name for b in ordered];indices={n:i for i,n in enumerate(names)}
weights=np.zeros((len(hands.data.vertices),len(names)))
for v in hands.data.vertices:
 for g in v.groups:
  name=hands.vertex_groups[g.group].name
  if name in indices:weights[v.index,indices[name]]=g.weight
fingers=['index','middle','ring','pinky']
own=np.array([n.endswith('_r') and n.startswith(('hand_','thumb_','index_','middle_','ring_','pinky_')) for n in names])
ids=np.flatnonzero(weights[:,own].sum(axis=1)>.5)
W=weights[ids];rp=restpoints[ids];W/=W.sum(axis=1)[:,None]
inverses=np.array([rest[n].inverted() for n in names])
group_masks={f:W[:,[n.startswith(f+'_') and n.endswith('_r') for n in names]].sum(axis=1)>.5 for f in fingers}
pad_masks={f:W[:,[n.startswith((f+'_02_',f+'_03_')) and n.endswith('_r') for n in names]].sum(axis=1)>.5 for f in fingers}
def posed(params):
 p={n:m.copy() for n,m in p0.items()}
 for fi,finger in enumerate(fingers):
  for i in (1,2,3):
   n=f'{finger}_{i:02}_r';base=p[parent[n]]@rel[n]
   rotate(p,n,base.to_quaternion()@p[n].to_quaternion().inverted())
   rotate(p,n,Quaternion(-width,float(params[2+fi*3+i-1])))
 return p
def skin(p,params):
 matrices=np.array([p[n] for n in names])@inverses
 blend=np.einsum('vb,bij->vij',W,matrices,optimize=True)
 points=np.einsum('vij,vj->vi',blend,rp)[:,:3]
 points[:,:2]+=params[:2]
 return points
seed=np.array([-.019,-.013]+[.35,1.05,1.05]*4)
def metric(params,details=False):
 points=skin(posed(params),params);gap=np.linalg.norm(points[:,:2],axis=1)-.025
 penetration=np.minimum(gap,0)
 # Penalize worst intersection heavily; softly prefer near contact at pads.
 nearest={f:float(np.mean(np.sort(gap[pad_masks[f]])[:3])) for f in fingers}
 score=2500*float(penetration.min())**2+100*float(np.mean(penetration**2))+sum(v*v for v in nearest.values())
 score+=.000005*float(np.sum((params[2:]-seed[2:])**2))
 score+=.004*float(np.sum(np.maximum(math.radians(145)-params[2:].reshape(4,3).sum(axis=1),0)**2))
 if details:return {'loss':score,'max_penetration_mm':float(-penetration.min()*1000),'pad_gap_mm':{k:v*1000 for k,v in nearest.items()}}
 return score
# Validate this local CPU evaluator against the actual Blender armature first.
pp=posed(seed);apply_pose(pp);ev=hands.evaluated_get(bpy.context.evaluated_depsgraph_get())
actual=np.array([tuple(hands.matrix_world@ev.data.vertices[int(i)].co) for i in ids]);pred=skin(pp,seed);pred[:,:2]-=seed[:2]
error=float(np.linalg.norm(actual-pred,axis=1).max()*1000);assert error<.005,error
x=seed.copy();before=metric(x,True);history=[]
lower=np.array([-.04,-.05]+[.10,math.radians(40),.10]*4);upper=np.array([.04,.04]+[1.3,1.8,1.35]*4)
# A small coarse initialization avoids settling on a straight middle finger
# merely because the nearest local descent step crosses the pole.
for fi in range(4):
 best=metric(x); winner=x.copy()
 for angles in itertools.product([20,35,50,65],[45,60,75,90],[20,35,50,65]):
  candidate=x.copy();candidate[2+fi*3:5+fi*3]=np.radians(angles);value=metric(candidate)
  if value<best:best=value;winner=candidate
 x=winner
for step in [1,.5,.25,.125]:
 increments=np.array([.004,.004]+[math.radians(8)]*12)*step
 for iteration in range(10):
  changed=False
  for j in range(len(x)):
   current=metric(x);best=current;winner=None
   for direction in (-1,1):
    candidate=x.copy();candidate[j]=np.clip(candidate[j]+direction*increments[j],lower[j],upper[j]);value=metric(candidate)
    if value<best-1e-12:best=value;winner=candidate
   if winner is not None:x=winner;changed=True
  history.append({'scale':step,'iteration':iteration,'loss':metric(x)})
  if not changed:break
 print('FINGER_FIT_SCALE',step,metric(x,True),flush=True)
p=posed(x);shift=Matrix.Translation(Vector((float(x[0]),float(x[1]),0)));p={n:shift@m for n,m in p.items()};apply_pose(p)
arm_names=['clavicle_r','upperarm_r','lowerarm_r','hand_r','clavicle_l','upperarm_l','lowerarm_l','hand_l']
localerr=max(abs(rig.pose.bones[n].matrix_basis[i][j]-original_local[n][i][j]) for n in arm_names for i in range(4) for j in range(4));assert localerr<.0001
center=Vector((0,0,3));cam.data.ortho_scale=.32
for view,offset in [('front',Vector((3,-5,.4))),('back',Vector((-3,5,.4))),('side',Vector((4,2,0)))]:
 cam.location=center+offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'right_grip_{view}.png');bpy.ops.render.render(write_still=True)
(O/'Fit.json').write_text(json.dumps({'sources':hashes,'before':before,'after':metric(x,True),'params':x.tolist(),'angles_degrees':np.degrees(x[2:]).reshape(4,3).tolist(),'fingers':fingers,'cpu_skin_error_mm':error,'arm_local_error':localerr,'history':history,'limits':'No thumb fit yet. Vertex/pad tests do not prove triangle collision, contact under animation, or other character fit.'},indent=2))
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
print('SUPPORTED_FINGER_FIT_DONE',flush=True)
