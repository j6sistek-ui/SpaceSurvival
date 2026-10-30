import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Compare live component bones/curves against the saved Blender proof."""
import bpy,json,numpy as np,os
from mathutils import kdtree
from pathlib import Path
P=R.parents[2]
SKIN=True
live=json.loads((R/('NativeVexaBalancedRuntimeSkin.json' if SKIN else 'NativeVexaRuntimeBones.json')).read_text());assert live['ok'];live['shots']=[x for x in live['shots'] if 'bones' in x]
bpy.ops.wm.open_mainfile(filepath=str(P/'SourceAssets/DanceRefinement_20261025/Vexa_ShoulderBalanced_Proof.blend'),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');expected=[]
for row in live['shots']:
 frame=1+row['seconds']*60;s.frame_set(int(frame),subframe=frame%1);bpy.context.view_layer.update()
 bones={b.name.casefold():np.array((rig.matrix_world@b.matrix).translation) for b in rig.pose.bones};curves={}
 for ob in s.objects:
  if ob.type=='MESH' and ob.data.shape_keys:
   for key in ob.data.shape_keys.key_blocks:
    if key.name.casefold() in {n.casefold() for n in json.loads((R/'VexaBalancedExportContract.json').read_text())['expected_morphs']}:curves[key.name.casefold()]=key.value
 vertices=[]
 if SKIN:
  for ob in s.objects:
   if ob.type!='MESH' or ob.hide_render:continue
   ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
   vertices.extend(tuple(ev.matrix_world@v.co) for v in me.vertices);ev.to_mesh_clear()
 expected.append({'bones':bones,'curves':curves,'vertices':vertices})
names=sorted(expected[0]['bones']);A=np.array([live['shots'][0]['bones'][n]['translation'] for n in names])*.01;B=np.array([expected[0]['bones'][n] for n in names]);ac=A.mean(0);bc=B.mean(0);u,_,vt=np.linalg.svd((A-ac).T@(B-bc));rotation=u@vt;offset=bc-ac@rotation
rows=[]
for actual,wanted in zip(live['shots'],expected):
 points=np.array([actual['bones'][n]['translation'] for n in names])*.01@rotation+offset;delta=np.linalg.norm(points-np.array([wanted['bones'][n] for n in names]),axis=1);order=np.argsort(delta)[-8:][::-1]
 curves={n.casefold():v for n,v in actual['curves'].items()};errors={n:abs(value-curves.get(n,0)) for n,value in wanted['curves'].items()}
 rows.append({'seconds':actual['seconds'],'max_bone_error_m':float(delta.max()),'worst_bones':[(names[i],float(delta[i])) for i in order],'max_curve_error':max(errors.values()),'worst_curve':max(errors,key=errors.get)})
 if SKIN:
  actual_surface=np.array(actual['vertices_cm'])*.01@rotation+offset;expected_surface=np.array(wanted['vertices'])
  distances=[]
  for source,target in ((actual_surface,expected_surface),(expected_surface,actual_surface)):
   tree=kdtree.KDTree(len(target))
   for i,v in enumerate(target):tree.insert(v,i)
   tree.balance();distances.append(np.array([tree.find(v)[2] for v in source]))
  rows[-1]['skin_vertices']=[len(actual_surface),len(expected_surface)]
  rows[-1]['skin_error_m']=[{'max':float(d.max()),'p95':float(np.percentile(d,95)),'mean':float(d.mean())} for d in distances]
  np.savez_compressed(R/f"VexaBalancedRuntimeSkin_{actual['seconds']}.npz",actual=actual_surface,expected=expected_surface)
influences={ob.name:max(sum(g.weight>1e-6 for g in v.groups) for v in ob.data.vertices) for ob in s.objects if ob.type=='MESH'}
report={'alignment_determinant':float(np.linalg.det(rotation)),'rows':rows,'max_vertex_influences':influences}
(R/('VexaBalancedRuntimeSkinParity.json' if SKIN else 'VexaRuntimePoseParity.json')).write_text(json.dumps(report,indent=2));print('VEXA_RUNTIME_POSE',json.dumps(report),flush=True)
