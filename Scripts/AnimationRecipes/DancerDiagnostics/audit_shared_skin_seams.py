import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Read actual packed base colour at coincident body-part seam loops."""
import bpy,json,hashlib,numpy as np
from pathlib import Path
from mathutils import kdtree
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025';O=R/'ZeroGSharedHip/MaterialReview';src=D/'Vexa_ZeroG_MaterialReview.blend'
h=hashlib.sha256(src.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
cache={}
def sample(ob,loop,mat):
 n=mat.node_tree.nodes;imgnode=n.get('Image Texture');mapping=imgnode.inputs['Vector'].links[0].from_node;uvnode=mapping.inputs['Vector'].links[0].from_node
 layer=ob.data.uv_layers.get(uvnode.uv_map) if uvnode.uv_map else ob.data.uv_layers.active
 assert layer is not None,(ob.name,uvnode.uv_map,[x.name for x in ob.data.uv_layers])
 uv=np.array(layer.data[loop].uv);uv=uv*np.array(mapping.inputs['Scale'].default_value)[:2]+np.array(mapping.inputs['Location'].default_value)[:2]
 im=imgnode.image
 if im.name not in cache:
  pixels=np.empty(im.size[0]*im.size[1]*4,np.float32);im.pixels.foreach_get(pixels);cache[im.name]=pixels.reshape(im.size[1],im.size[0],4)
 a=cache[im.name];uv=uv%1.;x=uv[0]*(a.shape[1]-1);y=uv[1]*(a.shape[0]-1);ix=int(x);iy=int(y);fx=x-ix;fy=y-iy
 col=((a[iy,ix]*(1-fx)+a[iy,min(ix+1,a.shape[1]-1)]*fx)*(1-fy)+(a[min(iy+1,a.shape[0]-1),ix]*(1-fx)+a[min(iy+1,a.shape[0]-1),min(ix+1,a.shape[1]-1)]*fx)*fy)[:3]
 for name in ('Editable_Skin_Match','Boundary_Skin_Match'):
  node=n.get(name)
  if node:
   assert node.blend_type=='MULTIPLY',node.blend_type
   col*=np.array(node.inputs[2].default_value)[:3]
 return col
body=bpy.data.objects['Vexa_Continuous_Hands'];legs=bpy.data.objects['Vexa_Continuous_Feet']
tree=kdtree.KDTree(len(body.data.vertices))
for v in body.data.vertices:tree.insert(body.matrix_world@v.co,v.index)
tree.balance();pairs=[]
for v in legs.data.vertices:
 _,i,d=tree.find(legs.matrix_world@v.co)
 if d<1e-5:pairs.append((i,v.index,d))
def colors(ob,vertex):
 result=[]
 for poly in ob.data.polygons:
  for loop in poly.loop_indices:
   if ob.data.loops[loop].vertex_index==vertex:result.append(sample(ob,loop,ob.data.materials[poly.material_index]))
 return np.mean(result,axis=0)
rows=[{'torso':i,'leg':j,'distance_m':d,'torso_rgb':colors(body,i).tolist(),'leg_rgb':colors(legs,j).tolist()} for i,j,d in pairs]
report={'source_sha256':h,'waist_pairs':rows,'uv_layers':{o.name:[x.name for x in o.data.uv_layers] for o in (body,legs)}}
if rows:
 a=np.array([r['torso_rgb'] for r in rows]);b=np.array([r['leg_rgb'] for r in rows]);report['max_rgb_difference']=abs(a-b).max(axis=0).tolist();report['mean_torso']=a.mean(axis=0).tolist();report['mean_legs']=b.mean(axis=0).tolist()
(O/'SkinSeamColors.json').write_text(json.dumps(report,indent=2));assert hashlib.sha256(src.read_bytes()).hexdigest()==h
print('SEAM_COLORS',json.dumps({k:v for k,v in report.items() if k!='waist_pairs'}),len(rows),flush=True)
