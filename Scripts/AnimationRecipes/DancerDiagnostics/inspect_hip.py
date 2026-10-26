import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

import bpy,json
from pathlib import Path
P=R.parents[2]
bpy.ops.wm.open_mainfile(filepath=str(P/'SourceAssets/CharacterWorkshop_20261021/Roxie_Character_Options.blend'),load_ui=False)
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
report={'bones':[],'meshes':[]}
for bone in rig.data.bones:
 if any(s in bone.name.lower() for s in ['thigh','butt','hip','pelvis','glute','twist','correct']):
  report['bones'].append({'name':bone.name,'parent':bone.parent.name if bone.parent else None,'head':list(bone.head_local),'tail':list(bone.tail_local)})
for ob in bpy.data.objects:
 if ob.type=='MESH' and ob.visible_get() and not ob.hide_render:
  groups={g.index:g.name for g in ob.vertex_groups};sums={}
  for vertex in ob.data.vertices:
   for g in vertex.groups:
    name=groups[g.group]
    if any(s in name for s in ['thigh','pelvis','hip','butt']):sums[name]=sums.get(name,0)+g.weight
  report['meshes'].append({'name':ob.name,'vertices':len(ob.data.vertices),'modifiers':[(m.name,m.type,getattr(m,'use_deform_preserve_volume',None)) for m in ob.modifiers],'weights':sums})
(R/'HipInspection.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
