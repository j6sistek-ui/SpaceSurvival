import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Read-only rest-rig and body-part compatibility for the four local dancers."""
import bpy,json,numpy as np,hashlib
from pathlib import Path
P=R.parents[2]
baseline=None;report=[]
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
for name in ('Roxie','Vexa','Jinx','Vesper'):
 path=P/'SourceAssets/CharacterWorkshop_20261021'/(name+'_Character_Options.blend')
 bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False)
 rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
 rest={b.name:np.array(rig.matrix_world@b.matrix_local) for b in rig.data.bones}
 if baseline is None:baseline=rest
 common=set(rest)&set(baseline)
 bodies={}
 for suffix in ('Nude_Torso','Nude_Legs','Bottom'):
  ob=bpy.data.objects[name+'_'+suffix]
  bodies[suffix]={'geometry':digest([list(v.co) for v in ob.data.vertices]),'topology':digest([list(p.vertices) for p in ob.data.polygons]),'weights':digest([sorted((ob.vertex_groups[g.group].name,g.weight) for g in v.groups) for v in ob.data.vertices]),'object_transform':digest([list(row) for row in ob.matrix_world]),'shape_values':{k.name:k.value for k in ob.data.shape_keys.key_blocks} if ob.data.shape_keys else {},'shape_geometry':digest({k.name:[list(v.co) for v in k.data] for k in ob.data.shape_keys.key_blocks}) if ob.data.shape_keys else None}
 row={'character':name,'body_signatures':bodies,'bones':len(rest),'common_bones':len(common),'max_rest_matrix_difference':float(max(np.abs(rest[n]-baseline[n]).max() for n in common)),
      'meshes':[{'name':o.name,'vertices':len(o.data.vertices),'groups':len(o.vertex_groups)} for o in bpy.context.scene.objects if o.type=='MESH'],'same_bone_names':set(rest)==set(baseline)}
 report.append(row)
(R/'DancerLegCompatibility.json').write_text(json.dumps(report,indent=2));print('DANCER_LEG_COMPATIBILITY',json.dumps(report),flush=True)
