import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Compare one native FBX readback to the private Blender proof.

This audits exported data, not engine GPU skinning or material quality.
"""
import bpy,json,os,numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
SHOULDER=os.environ.get('SS_REVIEW_SHOULDER')=='1'
stem='NativeVexaShoulder' if SHOULDER else 'NativeLegPlane'
times=(0,8,9.033333,9.5,10.066667,12.2,16)
def capture():
 s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');act=rig.animation_data.action
 fps=s.render.fps/s.render.fps_base;start=float(act.frame_range[0]);rows=[]
 for t in times:
  frame=start+t*fps;s.frame_set(int(frame),subframe=frame%1);bpy.context.view_layer.update()
  bone={b.name.casefold():list((rig.matrix_world@b.matrix).translation) for b in rig.pose.bones}
  verts=[];curves=0
  for ob in s.objects:
   if ob.type!='MESH':continue
   e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());verts.extend(tuple(ob.matrix_world@v.co) for v in e.data.vertices)
   if ob.data.shape_keys and ob.data.shape_keys.animation_data:curves+=1
  rows.append({'seconds':t,'bones':bone,'verts':np.array(verts),'animated_shape_meshes':curves})
 return {'fps':fps,'range':list(act.frame_range),'rows':rows}
bpy.ops.wm.open_mainfile(filepath=str(D/('Vexa_Shoulder_Proof.blend' if SHOULDER else 'Roxie_LegPlane_Proof.blend')),load_ui=False);expected=capture()
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=60
bpy.ops.import_scene.fbx(filepath=str(R/(stem+'Roundtrip.fbx')));actual=capture()
common=sorted(set(expected['rows'][0]['bones'])&set(actual['rows'][0]['bones']))
A=np.array([actual['rows'][0]['bones'][n] for n in common]);B=np.array([expected['rows'][0]['bones'][n] for n in common]);ac=A.mean(0);bc=B.mean(0)
U,S,Vt=np.linalg.svd((A-ac).T@(B-bc));rot=U@Vt
if np.linalg.det(rot)<0:U[:,-1]*=-1;rot=U@Vt
offset=bc-ac@rot
def nearest(src,dst):
 kd=kdtree.KDTree(len(dst))
 for i,v in enumerate(dst):kd.insert(Vector(v),i)
 kd.balance();dist=np.array([kd.find(Vector(v))[2] for v in src])
 return {'max_m':float(dist.max()),'p99_m':float(np.percentile(dist,99)),'mean_m':float(dist.mean())}
rows=[]
for e,a in zip(expected['rows'],actual['rows']):
 posA=np.array([a['bones'][n] for n in common])@rot+offset;posB=np.array([e['bones'][n] for n in common]);errors=np.linalg.norm(posA-posB,axis=1);index=int(errors.argmax())
 transformed=a['verts']@rot+offset
 rows.append({'seconds':e['seconds'],'max_bone_error_m':float(errors.max()),'worst_bone':common[index],
              'expected_to_native_export':nearest(e['verts'],transformed),'native_export_to_expected':nearest(transformed,e['verts']),
              'expected_vertices':len(e['verts']),'exported_vertices':len(a['verts']),'exported_animated_shape_meshes':a['animated_shape_meshes']})
report={'scope':'FBX roundtrip only; not GPU skinning proof','common_bones':len(common),'source_fps':expected['fps'],'export_fps':actual['fps'],'export_range':actual['range'],'alignment_determinant':float(np.linalg.det(rot)),'rows':rows}
(R/(stem+'Parity.json')).write_text(json.dumps(report,indent=2));print('NATIVE_LEG_PARITY',json.dumps(report),flush=True)
