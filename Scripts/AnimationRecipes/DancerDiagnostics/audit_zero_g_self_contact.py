import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Sample evaluated forearm/hand triangles against torso/head; no source edits.

Adjacent shoulder interfaces and clothing-vs-skin pairs are not a watertight
whole-body collision model. Flags select poses for visual review.
"""
import bpy,json,hashlib,numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
src=D/'Vexa_ZeroG_SharedHip_Proof.blend';digest=hashlib.sha256(src.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False);s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');pairs=json.loads(s['zero_g_curve_pairs'])
objects=[]
for ob in s.objects:
 if ob.type!='MESH' or ob.hide_render:continue
 ob.data.calc_loop_triangles();tri=np.array([t.vertices for t in ob.data.loop_triangles],dtype=np.int32)
 names={g.index:g.name for g in ob.vertex_groups};regions={}
 for label in ['body','l','r']:
  def relevant(n):
   return n.startswith(('spine','neck','head','pelvis')) if label=='body' else n.endswith('_'+label) and n.startswith(('lowerarm','hand','thumb','index','middle','ring','pinky'))
  weight=np.array([sum(g.weight for g in v.groups if relevant(names[g.group])) for v in ob.data.vertices])
  chosen=tri[np.all(weight[tri]>.75,axis=1)]
  if not len(chosen):continue
  used,inverse=np.unique(chosen,return_inverse=True);regions[label]=(used,inverse.reshape(-1,3))
 if regions:objects.append((ob,regions))
rows=[];summary=[]
for name,pa in pairs.items():
 action=bpy.data.actions[name];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
 for n,a in pa.items():
  keys=bpy.data.objects[n].data.shape_keys;keys.animation_data_create();keys.animation_data.action=bpy.data.actions[a];keys.animation_data.action_slot=keys.animation_data.action.slots[0]
 first,last=map(round,action.frame_range);cliprows=[]
 for frame in sorted(set(range(first,last+1,4))|{last}):
  s.frame_set(frame);bpy.context.view_layer.update();regionpoints={k:[] for k in ['body','l','r']};regionfaces={k:[] for k in regionpoints};sizes={k:0 for k in regionpoints}
  for ob,regions in objects:
   ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());coords=np.empty(len(ev.data.vertices)*3);ev.data.vertices.foreach_get('co',coords);coords=coords.reshape(-1,3);m=np.array(ob.matrix_world);coords=coords@m[:3,:3].T+m[:3,3]
   for label,(used,tri) in regions.items():
    regionpoints[label].append(coords[used]);regionfaces[label].append(tri+sizes[label]);sizes[label]+=len(used)
  points={k:np.concatenate(v) for k,v in regionpoints.items() if v};faces={k:np.concatenate(regionfaces[k]) for k in points};counts={}
  body=points['body'];bodytree=None
  for side in ['l','r']:
   arm=points[side]
   if np.any(arm.max(axis=0)<body.min(axis=0)) or np.any(arm.min(axis=0)>body.max(axis=0)):counts[side]=0;continue
   if bodytree is None:bodytree=BVHTree.FromPolygons(body.tolist(),faces['body'].tolist(),all_triangles=True)
   armtree=BVHTree.FromPolygons(arm.tolist(),faces[side].tolist(),all_triangles=True);counts[side]=len(armtree.overlap(bodytree))
  row={'clip':name,'frame':frame,'triangle_overlaps':counts};rows.append(row);cliprows.append(row)
 summary.append({'clip':name,'samples':len(cliprows),'flagged_samples':sum(any(x['triangle_overlaps'].values()) for x in cliprows),'worst':sorted(cliprows,key=lambda x:sum(x['triangle_overlaps'].values()),reverse=True)[:5]});print('ZERO_G_SELF_CONTACT',json.dumps(summary[-1]),flush=True)
(R/'ZeroGSharedHip/SelfContactScreen.json').write_text(json.dumps({'source_sha256':digest,'sample_rate':15,'summary':summary,'samples':rows,'limitations':'Surface-overlap flags, not complete collision certification; inspect candidates and resample flagged intervals.'},indent=2))
assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
