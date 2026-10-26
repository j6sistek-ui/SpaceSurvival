import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Complete the isolated support-hand contact, without changing arm pose."""
from pathlib import Path
code=(_recipe_dir/'fit_supported_finger_contact.py').read_text()
exec(compile(code.split('# Validate this local CPU evaluator')[0],__file__,'exec'))
O=R/'GBSupportedThumbFit';O.mkdir(exist_ok=True)
finger_fit=json.loads((R/'GBSupportedFingerFit2/Fit.json').read_text())
fixed=np.array(finger_fit['params']);finger_pose=posed
thumbmask=W[:,[n.startswith('thumb_') and n.endswith('_r') for n in names]].sum(axis=1)>.5
thumbpad=W[:,[n=='thumb_03_r' for n in names]].sum(axis=1)>.5
def thumb_pose(t):
 p=finger_pose(fixed)
 for i in (1,2,3):
  n=f'thumb_{i:02}_r';base=p[parent[n]]@rel[n]
  rotate(p,n,base.to_quaternion()@p[n].to_quaternion().inverted())
 # Opposition at the thumb base, then flex toward the palm from each joint.
 rotate(p,'thumb_01_r',Quaternion(forward,float(t[0])))
 for i in (1,2,3):
  n=f'thumb_{i:02}_r'
  direction=(p[f'thumb_{i+1:02}_r'].translation-p[n].translation).normalized() if i<3 else (p[n].translation-p['thumb_02_r'].translation).normalized()
  palm=forward.cross(width).normalized();axis=direction.cross(palm).normalized()
  rotate(p,n,Quaternion(axis,float(t[i])))
 return p
def loss(t,details=False):
 points=skin(thumb_pose(t),fixed);gap=np.linalg.norm(points[:,:2],axis=1)-.025;pen=np.minimum(gap,0)
 nearest=float(np.mean(np.sort(gap[thumbpad])[:3]));score=2500*float(pen.min())**2+100*float(np.mean(pen**2))+nearest**2+.000002*float(np.sum(t*t))
 if details:return {'loss':score,'max_penetration_mm':float(-pen.min()*1000),'thumb_pad_gap_mm':nearest*1000}
 return score
best=float('inf');t=None
for values in itertools.product([-35,-15,15,35],[0,25,50,70],[0,25,50,70],[0,25,50,70]):
 q=np.radians(values);v=loss(q)
 if v<best:best=v;t=q
low=np.radians([-45,0,0,0]);high=np.radians([45,75,80,80])
for step in [8,4,2,1]:
 for it in range(8):
  changed=False
  for j in range(4):
   winner=t;best=loss(t)
   for sign in (-1,1):
    q=t.copy();q[j]=np.clip(q[j]+math.radians(step)*sign,low[j],high[j]);v=loss(q)
    if v<best-1e-12:winner=q;best=v;changed=True
   t=winner
  if not changed:break
 print('THUMB_SCALE',step,loss(t,True),flush=True)
p=thumb_pose(t);shift=Matrix.Translation(Vector((float(fixed[0]),float(fixed[1]),0)));p={n:shift@m for n,m in p.items()};apply_pose(p)
center=Vector((0,0,3));cam.data.ortho_scale=.32
for view,offset in [('front',Vector((3,-5,.4))),('back',Vector((-3,5,.4))),('side',Vector((4,2,0))),('above',Vector((.2,-.3,3)))]:
 cam.location=center+offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'right_grip_{view}.png');bpy.ops.render.render(write_still=True)
locals_saved={n:[list(row) for row in rig.pose.bones[n].matrix_basis] for n in names if n.endswith('_r') and n.startswith(('thumb_','index_','middle_','ring_','pinky_'))}
(O/'Fit.json').write_text(json.dumps({'sources':hashes,'finger_fit':str(R/'GBSupportedFingerFit2/Fit.json'),'thumb_degrees':np.degrees(t).tolist(),'metrics':loss(t,True),'finger_params':fixed.tolist(),'finger_local_matrices':locals_saved,'hand_world_matrix':[list(row) for row in p[hn]],'limits':'Static right-hand contact candidate; no thumb/index self-contact, triangle intersections or full-motion acceptance.'},indent=2))
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
print('SUPPORTED_THUMB_FIT_DONE',flush=True)
