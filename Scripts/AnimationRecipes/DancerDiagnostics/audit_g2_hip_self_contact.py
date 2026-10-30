"""Read-only hip self-contact screen for the exact preserved G2 hip candidate.

Exit success means the report was written; use summary.screen_passed for the
limited screen result. Nonadjacent posterior hip versus same-side proximal thigh
only. Source data is read and hash-checked, never saved or repaired."""
import bpy,json,math,numpy as np,hashlib,os
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()
assert (P/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R=P/'.agent/local/AnimationReview_20261025';O=R/'G2PosteriorHip';D=P/'SourceAssets/DanceRefinement_20261025'
O.mkdir(parents=True,exist_ok=True)
p=D/'Vexa_G2_PosteriorHip_Candidate.blend';h=hashlib.sha256(p.read_bytes()).hexdigest()
assert h=='aa7da9855d2a5af57806674988c2d1017411ccb04201d4d0570a7138c0c3bdae', 'Wrong candidate; deliberately update identity for a new review'
bpy.ops.wm.open_mainfile(filepath=str(p),load_ui=False);s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');ob=bpy.data.objects['Vexa_Continuous_Feet']
assert s.render.fps/s.render.fps_base==60 and s.frame_start==1
assert len(ob.data.vertices)==4776
rest=np.array([tuple(ob.matrix_world@v.co) for v in ob.data.vertices]);weights=[{ob.vertex_groups[g.group].name:g.weight for g in v.groups} for v in ob.data.vertices]
ob.data.calc_loop_triangles();tri=np.array([t.vertices for t in ob.data.loop_triangles]);adj=[set([v.index]) for v in ob.data.vertices]
for e in ob.data.edges:
 a,b=e.vertices;adj[a].add(b);adj[b].add(a)
regions={}
for side,sign in [('l',1),('r',-1)]:
 hip=np.array([sum(w for n,w in d.items() if n in ('pelvis','glute_'+side)) for d in weights]);thigh=np.array([sum(w for n,w in d.items() if n in ('thigh_'+side,'thigh_twist_01_'+side)) for d in weights])
 posterior=(rest[:,1]>.015)&(rest[:,2]>.84)&(rest[:,2]<1.07)&(sign*rest[:,0]>-.006)
 ht=tri[np.all((hip>.35)[tri],axis=1)&np.any(posterior[tri],axis=1)]
 tt=tri[np.all((thigh>.65)[tri],axis=1)&np.any((rest[:,2]>.70)[tri],axis=1)]
 regions[side]=(ht,tt)
rows=[]
for frame in range(s.frame_start,s.frame_end+1):
 t=(frame-1)/60
 f=1+t*60;s.frame_set(math.floor(f),subframe=f%1);bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());pts=[ob.matrix_world@v.co for v in ev.data.vertices]
 for side,(ht,tt) in regions.items():
  hb=BVHTree.FromPolygons(pts,ht.tolist(),all_triangles=True);tb=BVHTree.FromPolygons(pts,tt.tolist(),all_triangles=True)
  raw=hb.overlap(tb);pairs=[(a,b) for a,b in raw if not any(j in adj[i] for i in ht[a] for j in tt[b])]
  root=rig.pose.bones['pelvis'].matrix;rr=rig.data.bones['pelvis'].matrix_local
  thigh=rig.pose.bones['thigh_'+side].matrix;tr=rig.data.bones['thigh_'+side].matrix_local
  delta=(root@rr.inverted()).inverted()@thigh@tr.inverted();q=delta.to_quaternion();axis=(rig.data.bones['calf_'+side].head_local-rig.data.bones['thigh_'+side].head_local).normalized()
  vector=Vector((q.x,q.y,q.z));project=axis*vector.dot(axis);twist=__import__('mathutils').Quaternion((q.w,*project));twist.normalize()
  if twist.w<0:twist.negate()
  sign=1 if Vector((twist.x,twist.y,twist.z)).dot(axis)>=0 else -1
  swing=q@twist.inverted()
  rows.append({'time':t,'side':side,'hip_triangles':len(ht),'thigh_triangles':len(tt),'nonadjacent_intersections':len(pairs), 'hip_swing_deg':math.degrees(swing.angle),'hip_twist_deg':sign*math.degrees(twist.angle)})
flags=[r for r in rows if r['nonadjacent_intersections']]
summary={'screen_passed':not flags,'samples':len(rows),'flagged_samples':len(flags),'sides':{side:sum(r['side']==side for r in flags) for side in ('l','r')},'worst':max(rows,key=lambda r:r['nonadjacent_intersections'])}
(O/'HipSelfContactAudit.json').write_text(json.dumps({'source_sha256':h,'summary':summary,'rows':rows,'scope':'Same-side posterior pelvis/glute-dominant versus proximal thigh-dominant triangles; adjacent topology excluded. Bounded survey, not full self-contact or anatomy acceptance.'},indent=2));print('HIP_CONTACT_AUDIT',json.dumps(summary),flush=True)
assert hashlib.sha256(p.read_bytes()).hexdigest()==h
