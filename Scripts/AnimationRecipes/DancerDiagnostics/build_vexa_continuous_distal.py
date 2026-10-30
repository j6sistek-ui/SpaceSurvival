import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Private continuous-surface control: stitch only audited hand/foot boundaries.

Source parts remain hidden and intact. No skeleton or rest-point changes. The
candidate is rejected if shape animation no longer reproduces the source.
"""
import bpy,bmesh,json,hashlib,sys
import numpy as np
from pathlib import Path
from mathutils import kdtree
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025'
source=D/'Vexa_HandWeights_Proof.blend'
digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
seams=json.loads((R/'VexaEndJoints/Seams.json').read_text())
report={'source_sha256':digest,'pairs':[],'status':'PRIVATE CONTINUOUS SURFACE CONTROL; not adopted'}
def coords(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 values=np.array([list(ev.matrix_world@v.co) for v in me.vertices]);ev.to_mesh_clear();return values
for label in ('Hands','Feet'):
 entry=seams['pairs'][label];prox=bpy.data.objects[entry['proximal']];dist=bpy.data.objects[entry['distal']]
 original=(prox,dist); times=(0,4,8,9.033333,11.966667,12.2,16);expected={}
 for t in times:
  f=1+t*60;s.frame_set(int(f),subframe=f%1);bpy.context.view_layer.update()
  expected[t]=np.concatenate([coords(o) for o in original])
 s.frame_set(1);bpy.context.view_layer.update()
 clones=[]
 for ob in original:
  cp=ob.copy();cp.data=ob.data.copy();s.collection.objects.link(cp)
  if cp.data.shape_keys and cp.data.shape_keys.animation_data and cp.data.shape_keys.animation_data.action:
   cp.data.shape_keys.animation_data.action=cp.data.shape_keys.animation_data.action.copy()
  cp.hide_render=False;cp.hide_set(False);clones.append(cp)
 first=clones[0];n0=len(first.data.vertices);n1=len(clones[1].data.vertices)
 expected_rest=np.concatenate([np.array([list(first.matrix_world.inverted()@o.matrix_world@v.co) for v in o.data.vertices]) for o in clones])
 bpy.ops.object.select_all(action='DESELECT')
 for ob in clones:ob.select_set(True)
 bpy.context.view_layer.objects.active=first
 bpy.ops.object.join()
 assert len(first.data.vertices)==n0+n1
 assert np.max(abs(np.array([tuple(v.co) for v in first.data.vertices])-expected_rest))<1e-5, 'Unexpected join ordering'
 # Keep every source face/UV/material. Only the exact paired boundary vertices
 # merge; no broad proximity merge that could join fingers or unrelated parts.
 if first.data.has_custom_normals:bpy.ops.mesh.customdata_custom_splitnormals_clear()
 bm=bmesh.new();bm.from_mesh(first.data);bm.verts.ensure_lookup_table()
 targets={bm.verts[n0+int(i)]:bm.verts[int(j)] for i,j,_ in entry['pairs']}
 max_rest=max((a.co-b.co).length for a,b in targets.items())
 assert max_rest<1e-5,max_rest
 bmesh.ops.weld_verts(bm,targetmap=targets)
 bm.to_mesh(first.data);bm.free();first.data.update()
 assert len(first.data.vertices)==n0+n1-len(targets)
 first.name='Vexa_Continuous_'+label
 # Match preserved rest vertices after bmesh index compaction, then verify the
 # complete source-derived shape animation at seven different times.
 tree=kdtree.KDTree(len(first.data.vertices))
 for v in first.data.vertices:tree.insert(v.co,v.index)
 tree.balance();mapping=[]
 for p in expected_rest:
  _,i,d=tree.find(p);assert d<1e-5,d;mapping.append(i)
 for ob in original:ob.hide_render=True;ob.hide_set(True)
 checks=[]
 for t in times:
  f=1+t*60;s.frame_set(int(f),subframe=f%1);bpy.context.view_layer.update()
  actual=coords(first)[mapping];error=np.linalg.norm(actual-expected[t],axis=1)
  checks.append({'seconds':t,'max_position_error_mm':float(error.max()*1000)})
 assert max(v['max_position_error_mm'] for v in checks)<.02,checks
 report['pairs'].append({'kind':label,'original_objects':[o.name for o in original],'output_object':first.name,'original_vertices':n0+n1,'vertices':len(first.data.vertices),'welded':len(targets),'max_rest_pair_distance_m':max_rest,'checks':checks,'materials':[m.name if m else None for m in first.data.materials]})
s.frame_set(1);bpy.context.preferences.filepaths.save_version=0
output=D/'Vexa_ContinuousDistal_Proof.blend';assert not output.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(output),compress=True)
report['output_sha256']=hashlib.sha256(output.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(R/'VexaDistalRepair/ContinuousSurface.json').write_text(json.dumps(report,indent=2))
print('CONTINUOUS_DISTAL_SAVED',report['output_sha256'],flush=True)
code=(Path(__file__).resolve().parent/'stress_vexa_distal_joints.py').read_text().replace('Vexa_AxillaLocal_Proof.blend','Vexa_ContinuousDistal_Proof.blend').replace("out=R/'VexaJointStress'","out=R/'VexaDistalRepair/ContinuousStress'")
exec(compile(code,str(R/'stress_vexa_distal_joints.py'),'exec'),{'__file__':str(R/'stress_vexa_distal_joints.py'),'__name__':'__main__'})
