import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Check whether the stubborn knee crease is an actual mesh/weight boundary."""
import bpy,json,hashlib,math,numpy as np
from pathlib import Path
from mathutils import kdtree
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025';O=R/'ZeroGSharedHip/KneeTopology';O.mkdir(exist_ok=True)
src=D/'Vexa_ZeroG_SharedHip_Proof.blend';digest=hashlib.sha256(src.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False);s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');ob=bpy.data.objects['Vexa_Continuous_Feet'];pairs=json.loads(s['zero_g_curve_pairs'])
rest=np.array([tuple(ob.matrix_world@v.co) for v in ob.data.vertices]);centers=np.array([tuple(rig.matrix_world@rig.data.bones['calf_'+side].head_local) for side in ['l','r']]);mask=np.min(np.linalg.norm(rest[:,None,:]-centers[None,:,:],axis=2),axis=1)<.16
tree=kdtree.KDTree(len(rest))
for i,p in enumerate(rest):tree.insert(p,i)
tree.balance();duplicates=[]
for i in np.flatnonzero(mask):
 for _,j,d in tree.find_range(rest[i],.00001):
  if j>i:duplicates.append((int(i),int(j),d))
counts={}
for p in ob.data.polygons:
 for edge in p.edge_keys:counts[edge]=counts.get(edge,0)+1
boundary=[e for e,c in counts.items() if c!=2 and (mask[e[0]] or mask[e[1]])]
ob.data.calc_loop_triangles();tri=np.array([t.vertices for t in ob.data.loop_triangles]);selected=np.any(mask[tri],axis=1);tri=tri[selected]
def area(points):
 q=points[tri];return np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)/2
basearea=area(rest);rows=[]
for suffix,frame in [('01_Drift',563.5),('02_Spiral',481),('03_Butterfly',474)]:
 name='A_F3_Coordinated_ZeroG_'+suffix;act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 for on,an in pairs[name].items():
  keys=bpy.data.objects[on].data.shape_keys;keys.animation_data.action=bpy.data.actions[an];keys.animation_data.action_slot=keys.animation_data.action.slots[0]
 s.frame_set(int(frame),subframe=frame%1);bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());points=np.array([tuple(ob.matrix_world@v.co) for v in ev.data.vertices]);ratio=area(points)/np.maximum(basearea,1e-15)
 rows.append({'clip':suffix,'frame':frame,'minimum_area_ratio':float(ratio.min()),'area_ratio_percentiles':np.percentile(ratio,[1,5,50,95,99]).tolist(),'collapsed_below_10_percent':int((ratio<.1).sum()),'seam_max_mm':max([np.linalg.norm(points[i]-points[j])*1000 for i,j,_ in duplicates] or [0]),'worst_triangle_ids':tri[np.argsort(ratio)[:10]].tolist()})
report={'source_sha256':digest,'knee_vertices':int(mask.sum()),'coincident_pairs':duplicates,'boundary_edges':boundary,'triangles_checked':len(tri),'poses':rows}
(O/'Report.json').write_text(json.dumps(report,indent=2));assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
print(json.dumps({k:v for k,v in report.items() if k not in ['coincident_pairs','boundary_edges']}));print('COINCIDENT',len(duplicates),'BOUNDARY',len(boundary),flush=True)
