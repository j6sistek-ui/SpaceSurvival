import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Test one whole-arm forward rotation, preserving its elbow/wrist locals."""
from pathlib import Path
code=(_recipe_dir/'inspect_g2_self_contact.py').read_text(encoding='utf-8')
exec(compile(code[:code.index('for t in cases:')],__file__,'exec'))
O=R/'G2ArmClearance';O.mkdir(exist_ok=True)
def forward_arm(p,degrees):
 p={n:m.copy() for n,m in p.items()};anchor=p['hand_r'].copy()
 chest=p['spine_05'].to_quaternion()@rest['spine_05'].to_quaternion().inverted()
 rotate(p,'upperarm_r',Quaternion(chest@Vector((-1,0,0)),math.radians(degrees)))
 delta=anchor@p['hand_r'].inverted()
 return {n:delta@m for n,m in p.items()}
results=[]
for t in [0,5,10.6,16,20.1666666667,26.6666666667]:
 original=sample_loop(t)
 for angle in [0,10,20,30]:
  p=forward_arm(original,angle);hits,groups,center=hits_for(p);collision={}
  for mesh in meshes:
   name,_,tri,_,_,grip=mesh;pts=surface(p,mesh);rad=triangle_radii(pts,tri);z=pts[tri,2];bad=(rad<.025-.00001)&(z.max(axis=1)>0)&(z.min(axis=1)<5)
   if bad.any():collision[name]=int(bad.sum())
  # A rigid upper-arm rotation must not change its child elbow or wrist locals.
  error=max(float(np.abs(np.array(original[parent[n]].inverted()@original[n])-np.array(p[parent[n]].inverted()@p[n])).max()) for n in ['lowerarm_r','hand_r'])
  results.append({'time':t,'degrees':angle,'self_pairs':len(hits),'mesh_pairs':groups,'pole_collisions':collision,'child_local_error':error})
  if t in [0,10.6] and angle in [20,30]:
   apply_pose(p);center=p['pelvis'].translation+Vector((0,0,.18));cam.data.ortho_scale=1.25;s.render.resolution_x=s.render.resolution_y=700
   for view,offset in [('front',Vector((3,-5,.6))),('back',Vector((-3,5,.4)))]:
    cam.location=center+offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'{t:05.2f}_{angle}_{view}.png');bpy.ops.render.render(write_still=True)
(O/'Probe.json').write_text(json.dumps(results,indent=2),encoding='utf-8');print('G2_CLEARANCE_PROBE',results,flush=True)
