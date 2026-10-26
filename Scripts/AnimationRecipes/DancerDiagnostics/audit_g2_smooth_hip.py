"""Unsaved soft hip-motion control: dense contact, preserved upper body and continuity."""
import bpy,json,math,numpy as np,hashlib,os
from pathlib import Path
from mathutils import Vector
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from g2_smooth_hip_control import corrected_pose
from mathutils.bvhtree import BVHTree
CODE=Path(__file__).resolve().parent
P=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()
assert (P/'SpaceSurvival.uproject').is_file()
R=P/'.agent/local/AnimationReview_20261025';O=R/'G2PosteriorHip';D=P/'SourceAssets/DanceRefinement_20261025'
O.mkdir(parents=True,exist_ok=True)
p=D/'Vexa_G2_PosteriorHip_Candidate.blend';h=hashlib.sha256(p.read_bytes()).hexdigest()
assert h=='aa7da9855d2a5af57806674988c2d1017411ccb04201d4d0570a7138c0c3bdae'
bpy.ops.wm.open_mainfile(filepath=str(p),load_ui=False);s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');ob=bpy.data.objects['Vexa_Continuous_Feet']
for o in s.objects:
 if o.type=='MESH' and o.data.shape_keys:
  for k in o.data.shape_keys.key_blocks:
   if k.name.startswith('REVIEW_G2_'):k.mute=True
restbones={b.name:rig.matrix_world@b.matrix_local for b in rig.data.bones}
ordered=sorted(rig.pose.bones,key=lambda b:len(b.parent_recursive));desc={b.name:[b.name]+[c.name for c in b.children_recursive] for b in ordered}
changed=set(desc['thigh_l']+desc['thigh_r']);action=rig.animation_data.action;slot=rig.animation_data.action_slot;inv=rig.matrix_world.inverted()
reload_action='--reload-action' in sys.argv
reload_error=0.;candidate=None;candidate_hash=None
if reload_action:
 manifest=json.loads((O/'SmoothHipAction.json').read_text())
 candidate_path=D/'G2_SmoothHip_ActionLibrary.blend'
 candidate_hash=hashlib.sha256(candidate_path.read_bytes()).hexdigest()
 assert manifest['source_sha256']==h and manifest['sha256']==candidate_hash
 assert manifest['control_sha256']==hashlib.sha256((CODE/'g2_smooth_hip_control.py').read_bytes()).hexdigest()
 with bpy.data.libraries.load(str(candidate_path),link=False) as (_,loaded):loaded.actions=[manifest['action']]
 candidate=loaded.actions[0];assert candidate
upper_error=0.;local_error=0.;max_step={};previous={};start=None;end=None;angle_rows=[]
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
# Fixed rest-weight regions; evaluate actual modified mesh surfaces each frame.
from validate_g2_contact_recipe import triangle_radii
mesh_regions=[]
for item in s.objects:
 if item.type!='MESH' or item.hide_render or not any(m.type=='ARMATURE' for m in item.modifiers):continue
 item.data.calc_loop_triangles();faces=np.array([t.vertices for t in item.data.loop_triangles])
 def weighted(prefixes):
  return np.array([sum(g.weight for g in v.groups if item.vertex_groups[g.group].name.startswith(prefixes)) for v in item.data.vertices])>.75
 bodymask=weighted(('spine_','neck_','head','pelvis','thigh_','calf_','foot_','ball_','toe_'))
 armmask=weighted(('lowerarm_','hand_','thumb_','index_','middle_','ring_','pinky_'))
 mesh_regions.append((item,faces,faces[np.all(bodymask[faces],axis=1)],faces[np.all(armmask[faces],axis=1)]))
contact_flags=[];maximum_radius=0.
rows=[]
for frame in range(s.frame_start,s.frame_end+1):
 t=(frame-1)/60
 rig.animation_data.action=action;rig.animation_data.action_slot=slot
 s.frame_set(frame);bpy.context.view_layer.update();original={b.name:rig.matrix_world@b.matrix for b in ordered}
 target,angles=corrected_pose(original,restbones,desc);angle_rows.append({'time':t,'angles':angles})
 if reload_action:
  rig.animation_data.action=candidate;rig.animation_data.action_slot=candidate.slots[0]
  s.frame_set(frame);bpy.context.view_layer.update()
 else:
  rig.animation_data.action=None
 local={n:inv@m for n,m in target.items()}
 for b in ([] if reload_action else ordered):
  base=local[b.parent.name]@b.parent.bone.matrix_local.inverted()@b.bone.matrix_local if b.parent else b.bone.matrix_local
  b.matrix_basis=base.inverted()@local[b.name]
 bpy.context.view_layer.update()
 actual={b.name:rig.matrix_world@b.matrix for b in ordered}
 reload_error=max(reload_error,max(float(np.abs(np.array(actual[n])-np.array(target[n])).max()) for n in target))
 upper_error=max(upper_error,max(float(np.abs(np.array(actual[n])-np.array(original[n])).max()) for n in original if n not in changed))
 for b in ordered:
  if b.name not in changed:continue
  if not b.name.startswith('thigh_') or b.name not in ('thigh_l','thigh_r'):
   before=original[b.parent.name].inverted()@original[b.name];after=actual[b.parent.name].inverted()@actual[b.name]
   local_error=max(local_error,float(np.abs(np.array(before)-np.array(after)).max()))
  q=b.matrix_basis.to_quaternion()
  if b.name in previous:max_step[b.name]=max(max_step.get(b.name,0),math.degrees(q.rotation_difference(previous[b.name]).angle if q.dot(previous[b.name])>=0 else (-q).rotation_difference(previous[b.name]).angle))
  previous[b.name]=q.copy()
 if frame==s.frame_start:start=actual
 if frame==s.frame_end:end=actual
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());pts=[ob.matrix_world@v.co for v in ev.data.vertices]
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
 bodyvertices=[];bodyfaces=[];armvertices=[];armfaces=[];pole={}
 for item,faces,bfaces,afaces in mesh_regions:
  evaluated=item.evaluated_get(bpy.context.evaluated_depsgraph_get())
  points=np.array([tuple(item.matrix_world@v.co) for v in evaluated.data.vertices])
  maximum_radius=max(maximum_radius,float(np.linalg.norm(points[:,:2],axis=1).max()))
  radius=triangle_radii(points,faces);z=points[faces,2]
  bad=(radius<.025-.00001)&(z.max(axis=1)>0)&(z.min(axis=1)<5)
  if bad.any():pole[item.name]={'triangles':int(bad.sum()),'penetration_mm':float((.025-radius[bad]).max()*1000)}
  if len(bfaces):
   offset=len(bodyvertices);bodyvertices.extend(points.tolist());bodyfaces.extend((bfaces+offset).tolist())
  if len(afaces):
   offset=len(armvertices);armvertices.extend(points.tolist());armfaces.extend((afaces+offset).tolist())
 contacts=BVHTree.FromPolygons(bodyvertices,bodyfaces,all_triangles=True).overlap(BVHTree.FromPolygons(armvertices,armfaces,all_triangles=True))
 if pole or contacts:contact_flags.append({'time':t,'pole':pole,'distal_arm_triangle_pairs':len(contacts)})
 if frame%300==1:print('COUPLED_AUDIT_PROGRESS',frame,len(contact_flags),flush=True)
flags=[r for r in rows if r['nonadjacent_intersections']]
loop_error=max(float(np.abs(np.array(start[n])-np.array(end[n])).max()) for n in start)
summary={'screen_passed':not flags and not contact_flags and reload_error<.001,'reload_matrix_error':reload_error,'contact_flagged_samples':len(contact_flags),'maximum_radius_m':maximum_radius,'upper_body_matrix_error':upper_error,'descendant_local_matrix_error':local_error,'loop_matrix_error':loop_error,'max_local_steps_deg':max_step,'samples':len(rows),'flagged_samples':len(flags),'sides':{side:sum(r['side']==side for r in flags) for side in ('l','r')},'worst':max(rows,key=lambda r:r['nonadjacent_intersections'])}
(O/('SmoothHipReloadAudit.json' if reload_action else 'SmoothHipAudit.json')).write_text(json.dumps({'source_sha256':h,'control_sha256':hashlib.sha256((CODE/'g2_smooth_hip_control.py').read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'candidate_action_sha256':candidate_hash,'summary':summary,'rows':rows,'angles':angle_rows,'contact_flags':contact_flags,'scope':'G2-specific thigh envelope (reload_action recorded by candidate_action_sha256), posterior5/10; adduction5/10; axial twist15/20. No narrow activation band; no medical/universal limits. Dense same-side posterior hip/thigh, pole surface and distal-arm versus torso/legs. Original weights and linear skinning, G2 time morphs muted. Excludes other self-contact, garments against body, between-sample events and artistic acceptance.'},indent=2));print('SMOOTH_HIP_AUDIT',json.dumps(summary),flush=True)
assert hashlib.sha256(p.read_bytes()).hexdigest()==h
