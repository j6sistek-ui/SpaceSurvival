import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Read-only count and pose comparison of body faces embedded in garments."""
import bpy,json,hashlib,numpy as np
from pathlib import Path
from mathutils import kdtree
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025';O=R/'ZeroGSharedHip/MaterialReview'
source=D/'Vexa_ZeroG_MaterialReview.blend';h=hashlib.sha256(source.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
report={'source_sha256':h,'meshes':[],'materials':{}}
for name in ('Vexa_Top','Vexa_Bottom','Vexa_Continuous_Hands','Vexa_Continuous_Feet','Eden_Pink_CharacterMesh0.001'):
 ob=bpy.data.objects[name];row={'name':name,'slots':[]}
 for i,mat in enumerate(ob.data.materials):
  faces=[p for p in ob.data.polygons if p.material_index==i];ids=sorted({v for p in faces for v in p.vertices});co=np.array([tuple(ob.matrix_world@ob.data.vertices[j].co) for j in ids])
  row['slots'].append({'index':i,'material':mat.name,'faces':len(faces),'vertices':len(ids),'rest_min':co.min(axis=0).tolist() if len(co) else None,'rest_max':co.max(axis=0).tolist() if len(co) else None})
 report['meshes'].append(row)
for name in ('Vexa_Torso_Skin','Vexa_Legs_Skin','MID_MI_Skin_F_Body_A_0_Eden_Pink_Feet'):
 mat=bpy.data.materials[name];report['materials'][name]=[]
 for node in mat.node_tree.nodes:
  inputs={}
  for item in node.inputs:
   if item.is_linked:inputs[item.name]={'links':[(l.from_node.name,l.from_socket.name) for l in item.links]}
   elif hasattr(item,'default_value'):
    value=item.default_value
    if isinstance(value,(str,int,float,bool)):inputs[item.name]=value
    else:
     try:inputs[item.name]=list(value)
     except TypeError:pass
  report['materials'][name].append({'name':node.name,'type':node.type,'inputs':inputs,'image':node.image.name if node.type=='TEX_IMAGE' and node.image else None})
(O/'GarmentSkinAudit.json').write_text(json.dumps(report,indent=2));assert hashlib.sha256(source.read_bytes()).hexdigest()==h
print(json.dumps(report,indent=2),flush=True)
