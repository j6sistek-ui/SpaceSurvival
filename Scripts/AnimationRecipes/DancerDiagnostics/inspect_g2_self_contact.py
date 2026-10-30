import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Locate region-screen hits and compare fitted versus source fingers."""
from pathlib import Path
code=(_recipe_dir/'audit_g2_loop_self_contact.py').read_text(encoding='utf-8')
exec(compile(code[:code.index('rows=[]')],__file__,'exec'))
report=json.loads((O/'SelfContact.json').read_text());worst=max(report['flags'],key=lambda x:x['overlapping_triangle_pairs'])['time'];cases=[0.,worst,26.6666666667];findings=[]
def hits_for(p):
 bv=[];bf=[];av=[];af=[];bm=[];am=[]
 for mesh,(bt,at) in zip(meshes,regions):
  name=mesh[0];pts=surface(p,mesh)
  if len(bt):
   offset=len(bv);bv.extend(pts.tolist());bf.extend((bt+offset).tolist());bm.extend((name,list(t)) for t in bt)
  if len(at):
   offset=len(av);av.extend(pts.tolist());af.extend((at+offset).tolist());am.extend((name,list(t)) for t in at)
 hits=BVHTree.FromPolygons(bv,bf,all_triangles=True).overlap(BVHTree.FromPolygons(av,af,all_triangles=True))
 groups={};center=[]
 for b,a in hits:
  key=bm[b][0]+' / '+am[a][0];groups[key]=groups.get(key,0)+1;center.extend(np.array(bv)[bf[b]].tolist());center.extend(np.array(av)[af[a]].tolist())
 return hits,groups,np.mean(center,axis=0).tolist() if center else None
for t in cases:
 for mode in ['fitted','source_fingers']:
  p=sample_loop(t)
  if mode=='source_fingers' and t<=envelope_seconds:
   source=570+12*distance(t-approach);lo=min(int(source)-start,end-start);hi=min(lo+1,end-start);f=source-start-lo
   for pb in ordered:
    n=pb.name
    if n in finger_basis:p[n]=p[parent[n]]@rel[n]@local_frames[lo][n].lerp(local_frames[hi][n],f)
  hits,groups,center=hits_for(p);findings.append({'time':t,'mode':mode,'pairs':len(hits),'mesh_pairs':groups,'center':center})
  if mode=='fitted' and center:
   apply_pose(p);center=Vector(center);cam.data.ortho_scale=.65;s.render.resolution_x=s.render.resolution_y=700
   for view,offset in [('front',Vector((3,-5,.6))),('back',Vector((-3,5,.4))),('side',Vector((5,2,.3)))]:
    cam.location=center+offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'contact_{t:06.2f}_{view}.png');bpy.ops.render.render(write_still=True)
(O/'SelfContactInspection.json').write_text(json.dumps(findings,indent=2),encoding='utf-8');print('SELF_CONTACT_DETAILS',findings,flush=True)
