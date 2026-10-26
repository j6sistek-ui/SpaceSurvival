import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Region-limited hand/forearm versus torso/head overlap screen."""
from pathlib import Path
code=(_recipe_dir/'review_g2_return_loop.py').read_text(encoding='utf-8')
exec(compile(code[:code.index('hinge={}')],__file__,'exec'))
from mathutils.bvhtree import BVHTree
body=np.array([n.startswith(('spine_','neck_','head','pelvis')) for n in names])
arm=np.array([n.startswith(('lowerarm_','hand_','thumb_','index_','middle_','ring_','pinky_')) for n in names])
regions=[]
for mesh in meshes:
 _,_,tri,joints,weights,_=mesh
 b=(weights*body[joints]).sum(axis=1)>.75;a=(weights*arm[joints]).sum(axis=1)>.75
 regions.append((tri[np.all(b[tri],axis=1)],tri[np.all(a[tri],axis=1)]))
rows=[]
for i in range(round(duration*15)+1):
 p=sample_loop(i/15);body_vertices=[];body_faces=[];arm_vertices=[];arm_faces=[]
 for mesh,(bt,at) in zip(meshes,regions):
  pts=surface(p,mesh)
  if len(bt):
   offset=len(body_vertices);body_vertices.extend(pts.tolist());body_faces.extend((bt+offset).tolist())
  if len(at):
   offset=len(arm_vertices);arm_vertices.extend(pts.tolist());arm_faces.extend((at+offset).tolist())
 bvh=BVHTree.FromPolygons(body_vertices,body_faces,all_triangles=True)
 other=BVHTree.FromPolygons(arm_vertices,arm_faces,all_triangles=True)
 hits=bvh.overlap(other)
 if hits:rows.append({'time':i/15,'overlapping_triangle_pairs':len(hits)})
report={'sources':hashes,'samples':round(duration*15)+1,'flagged_samples':len(rows),'flags':rows,'scope':'Only triangles strongly weighted to hands/forearms versus torso/head. Excludes adjacent shoulder, other limbs, garments as separate interfaces, and between-sample contacts.'}
(O/'SelfContact.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('G2_LOOP_SELF_CONTACT',report['samples'],len(rows),rows[:6],flush=True)
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
