import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Explicit release before the free arm's obstructed pole crossing.

Preserve source local arm poses. Open the supporting fingers, move the body
away from the pole, and smoothly stop constraining its hand frame. This is a
separate authored passage, not proof that the original full G1 is repaired.
"""
from pathlib import Path
exec(compile((_recipe_dir/'audit_supported_contact_motion.py').read_text().split("report={'sources':hashes,'grip_source'")[0],__file__,'exec'))
O=R/'GBSupportedRelease';O.mkdir(exist_ok=True)
act=acts['g1'];rig.animation_data_create();rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
originals=[];start,end=780,1000;rate=.2;fps=60
for frame in range(start,end+1):
 s.frame_set(frame);bpy.context.view_layer.update();originals.append({b.name:(rig.matrix_world@b.matrix).copy() for b in ordered})
rig.animation_data_clear()
local_frames=[]
for p in originals:
 local_frames.append({n:((p[parent[n]]@rel[n]) if parent[n] else rel[n]).inverted()@p[n] for n in names})
release_start,release_end=920,940
frozen=target@originals[release_start-start][hn].inverted()
rows=[];saved=[]
def sample_release(source):
 lo=min(int(source)-start,end-start);hi=min(lo+1,end-start);fraction=source-start-lo
 # Interpolate local rotations and rebuild the hierarchy. Interpolating
 # world-space joint matrices independently can shorten the limb between keys.
 original={}
 for n in names:
  base=original[parent[n]]@rel[n] if parent[n] else rel[n]
  original[n]=base@local_frames[lo][n].lerp(local_frames[hi][n],fraction)
 t=max(0,min(1,(source-release_start)/(release_end-release_start)));blend=t*t*t*(10-15*t+6*t*t)
 delta=(target@original[hn].inverted()).lerp(frozen,blend)
 shift=Matrix.Translation(Vector((0,-.40,0))*blend)
 p={n:shift@delta@m for n,m in original.items()}
 for pb in ordered:
  n=pb.name
  if n in finger_basis:
   neutral=(original[parent[n]]@rel[n]).inverted()@original[n]
   p[n]=p[parent[n]]@rel[n]@finger_basis[n].lerp(neutral,blend)
 return p,blend
for i in range(round((end-start)/60/rate*fps)+1):
 source=start+i/fps*60*rate;p,blend=sample_release(source)
 collisions={};minimum=1e3
 for mesh in meshes:
  name,_,tri,_,_,grip=mesh;pts=surface(p,mesh);rad=triangle_radii(pts,tri);z=pts[tri,2];active=(z.max(axis=1)>0)&(z.min(axis=1)<5)
  minimum=min(minimum,float((rad[active]-.025).min()))
  bad=(rad<.025-.00001)&active
  if bad.any():collisions[name]={'triangles':int(bad.sum()),'penetration_mm':float((.025-rad[bad]).max()*1000)}
 rows.append({'time':i/fps,'source_frame':source,'release':blend,'pole_collisions':collisions,'minimum_pole_clearance_mm':minimum*1000})
 if i%5==0:saved.append((i,p))
summary={'samples':len(rows),'collision_sample_count':sum(bool(x['pole_collisions']) for x in rows),'failures':[x for x in rows if x['pole_collisions']],'minimum_pole_clearance_mm':min(x['minimum_pole_clearance_mm'] for x in rows)}
(O/'Audit.json').write_text(json.dumps({'sources':hashes,'source_frames':[start,end],'rate':rate,'fps':fps,'release_source_frames':[release_start,release_end],'summary':summary,'samples':rows,'scope':'Separate release candidate; complete routine and anatomy remain open.'},indent=2))
print('RELEASE_SUMMARY',json.dumps({k:v if k!='failures' else v[:3] for k,v in summary.items()}),flush=True)
if os.environ.get('SS_RELEASE_RENDER'):
 center=Vector((.45,-.20,2.9));cam.data.ortho_scale=3.2;s.render.resolution_x=s.render.resolution_y=640
 for i,p in saved:
  apply_pose(p)
  for view,offset in [('front',Vector((3,-5,.6))),('back',Vector((-3,5,.4)))]:
   dest=O/view;dest.mkdir(exist_ok=True);cam.location=center+offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(dest/f'{i//5:05}.png');bpy.ops.render.render(write_still=True)
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
print('SUPPORTED_RELEASE_DONE',flush=True)
