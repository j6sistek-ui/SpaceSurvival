import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Slow support passage candidate with opposing views and every-frame surfaces.

The source interval and 20-percent playback are explicit artistic edits. This
is a candidate passage, not a replacement for the complete G1/G2 routine.
"""
from pathlib import Path
code=(_recipe_dir/'audit_supported_contact_motion.py').read_text()
exec(compile(code.split("report={'sources':hashes,'grip_source'")[0],__file__,'exec'))
O=R/'GBSupportedPassage';O.mkdir(exist_ok=True)
start,end=780,1000;rate=.2;fps=24;duration=(end-start)/60/rate
act=acts['g1'];rig.animation_data_create();rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
originals=[]
for frame in range(start,end+1):
 s.frame_set(frame);bpy.context.view_layer.update();originals.append({b.name:(rig.matrix_world@b.matrix).copy() for b in ordered})
rig.animation_data_clear();rows=[]
for i in range(round(duration*fps)+1):
 source=start+i/fps*60*rate;lo=min(int(source)-start,end-start);hi=min(lo+1,end-start);frac=source-start-lo
 p0={n:originals[lo][n].lerp(originals[hi][n],frac) for n in names}
 p=supported(p0);apply_pose(p);collisions={};parts=[]
 for mesh in meshes:
  name,_,tri,_,_,grip=mesh;pts=surface(p,mesh);parts.append(pts)
  rad=triangle_radii(pts,tri);z=pts[tri,2];body=(~np.any(grip[tri],axis=1))&(z.max(axis=1)>0)&(z.min(axis=1)<5)
  bad=(rad<.025)&body
  if bad.any():collisions[name]={'triangles':int(bad.sum()),'max_penetration_mm':float((.025-rad[bad]).max()*1000)}
 # Independent evaluated Blender positions verify skinning remains comparable.
 parity=0
 if i%120==0:
  deps=bpy.context.evaluated_depsgraph_get()
  for mesh,expected in zip(meshes,parts):
   ob=bpy.data.objects[mesh[0]];ev=ob.evaluated_get(deps);actual=np.array([tuple(ob.matrix_world@v.co) for v in ev.data.vertices])
   parity=max(parity,float(np.linalg.norm(actual-expected,axis=1).max()*1000))
  assert parity<.03,parity
 rows.append({'sample':i,'time':i/fps,'source_frame':source,'body_collisions':collisions,'evaluated_parity_mm':parity})
 center=Vector((.45,0,2.9));cam.data.ortho_scale=3.2
 s.render.resolution_x=s.render.resolution_y=640
 for view,offset in [('front',Vector((3,-5,.6))),('back',Vector((-3,5,.4)))]:
  out=O/view;out.mkdir(exist_ok=True)
  cam.location=center+offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(out/f'{i:05}.png');bpy.ops.render.render(write_still=True)
 if i%100==0:print('PASSAGE',i,flush=True)
(O/'Review.json').write_text(json.dumps({'sources':hashes,'source_clip':'g1','source_frames':[start,end],'playback_rate':rate,'duration':duration,'fps':fps,'samples':rows,'limits':'No release/regrip yet; source local arms preserved; this grip trajectory is not the original motion. Human visual fluidity and whole routine remain open.'},indent=2))
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
print('SUPPORTED_PASSAGE_DONE',flush=True)
