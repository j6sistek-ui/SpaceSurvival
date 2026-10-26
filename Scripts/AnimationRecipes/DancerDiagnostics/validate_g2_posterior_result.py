import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Fresh-load the baked hip copy and check its actual deformed geometry."""
import bpy, hashlib, json, math, sys, numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(_recipe_dir))
from validate_g2_contact_recipe import triangle_radii
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025';O=R/'G2PosteriorHip'
source=D/'Vexa_LegIsolation_Proof.blend';candidate=D/'Vexa_G2_PosteriorHip_Candidate.blend'
bake=json.loads((O/'BakeReport.json').read_text());assert hashlib.sha256(candidate.read_bytes()).hexdigest()==bake['sha256']
def fingerprint():
 out={}
 for ob in bpy.context.scene.objects:
  if ob.type!='MESH' or ob.hide_render or ob.hide_get():continue
  data={'vertices':[tuple(v.co) for v in ob.data.vertices],'faces':[tuple(p.vertices) for p in ob.data.polygons],
    'weights':[[(ob.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in ob.data.vertices]}
  out[ob.name]=hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
 return out
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False);original=fingerprint()
original_rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
rest={b.name:np.array(b.matrix_local) for b in original_rig.data.bones}
bpy.ops.wm.open_mainfile(filepath=str(candidate),load_ui=False);assert fingerprint()==original,'Base geometry/topology/weights changed'
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
assert set(rest)=={b.name for b in rig.data.bones}
assert max(float(np.abs(rest[b.name]-np.array(b.matrix_local)).max()) for b in rig.data.bones)==0
assert all(not m.use_deform_preserve_volume for ob in s.objects for m in ob.modifiers if m.type=='ARMATURE')
pairs=json.loads(s['g2_hip_curve_pairs']);assert pairs==bake['paired_curve_actions']
meshes=[]
for ob in s.objects:
 if ob.type!='MESH' or ob.hide_render:continue
 ob.data.calc_loop_triangles();tri=np.array([t.vertices for t in ob.data.loop_triangles]);body=np.zeros(len(ob.data.vertices));arm=body.copy()
 for v in ob.data.vertices:
  for g in v.groups:
   name=ob.vertex_groups[g.group].name
   if name.startswith(('spine_','neck_','head','pelvis','thigh_','glute_','calf_','foot_','ball_','toe_')):body[v.index]+=g.weight
   if name.startswith(('lowerarm_','hand_','thumb_','index_','middle_','ring_','pinky_')):arm[v.index]+=g.weight
 meshes.append((ob,tri,tri[np.all(body[tri]>.75,axis=1)],tri[np.all(arm[tri]>.75,axis=1)]))
start={};end={};flags=[];max_radius=0.;bound=float('-inf');expected=json.loads((R/'G2ClearContact/Export.json').read_text())['expected_bones'];bone_error=0.
for frame in range(s.frame_start,s.frame_end+1):
 s.frame_set(frame);bpy.context.view_layer.update();bv=[];bf=[];av=[];af=[];pole={}
 if str(frame) in expected:
  for name,want in expected[str(frame)].items():bone_error=max(bone_error,float(np.abs(np.array(rig.matrix_world@rig.pose.bones[name].matrix)-want).max()))
 for ob,tri,btri,atri in meshes:
  ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());points=np.array([tuple(ob.matrix_world@v.co) for v in ev.data.vertices])
  assert len(points)==len(ob.data.vertices)
  if frame==s.frame_start:start[ob.name]=points.copy()
  if frame==s.frame_end:end[ob.name]=points.copy()
  max_radius=max(max_radius,float(np.linalg.norm(points[:,:2],axis=1).max()))
  r=triangle_radii(points,tri);z=points[tri,2];bad=(r<.025-.00001)&(z.max(axis=1)>0)&(z.min(axis=1)<5)
  if bad.any():pole[ob.name]={'triangles':int(bad.sum()),'penetration_mm':float((.025-r[bad]).max()*1000)}
  if len(btri):offset=len(bv);bv.extend(points.tolist());bf.extend((btri+offset).tolist())
  if len(atri):offset=len(av);av.extend(points.tolist());af.extend((atri+offset).tolist())
 contact=BVHTree.FromPolygons(bv,bf,all_triangles=True).overlap(BVHTree.FromPolygons(av,af,all_triangles=True))
 if pole or contact:flags.append({'frame':frame,'time':(frame-1)/60,'pole':pole,'arm_body_pairs':len(contact)})
 if (frame-1)%300==0:print('HIP_GEOMETRY_AUDIT',frame,len(flags),flush=True)
loop_error=max(float(np.linalg.norm(end[n]-start[n],axis=1).max()) for n in start)
report={'candidate_sha256':bake['sha256'],'source_fingerprints':original,'base_geometry_weights_rest_unchanged':True,
 'frames':s.frame_end-s.frame_start+1,'fps':60,'bone_matrix_error':bone_error,'loop_surface_error_m':loop_error,
 'maximum_radius_m':max_radius,'flags':flags,'ok':not flags and bone_error<.0001 and loop_error<.00001 and max_radius<3.48,
 'scope':'Actual baked surfaces at60Hz; pole and distal arm versus torso/legs only. Does not validate hip range, garments, between-frame contact or artistic quality.'}
(O/'GeometryAudit.json').write_text(json.dumps(report,indent=2));print('HIP_GEOMETRY_RESULT',report['ok'],len(flags),bone_error,loop_error,flush=True)
assert hashlib.sha256(candidate.read_bytes()).hexdigest()==bake['sha256']
