"""Reload the saved hair derivative; verify body, source guides and materials; CPU preview."""
import bpy,json,hashlib
from array import array
from pathlib import Path
WORK=Path(__file__).resolve().parents[3]/'.agent/local/StationRefinement/JoyHair139';OUT=WORK/'JoyHair140';OUT.mkdir(exist_ok=False)
SOURCE=Path(__file__).resolve().parents[3]/'.agent/local/StationRefinement/CpuJoy121/JoyBlue114/Joy_LightBlue_HairFitted.blend';TARGET=WORK/'JoyHair139/Joy_LightBlue_HairClean.blend'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot():
 geometry=hashlib.sha256();hair={};materials={}
 for o in sorted(bpy.context.scene.objects,key=lambda o:o.name):
  if o.type=='MESH':
   geometry.update(o.name.encode());coords=array('f',[0.])*(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',coords);geometry.update(coords.tobytes())
   geometry.update(str([(m.type,m.object.name if m.type=='ARMATURE' and m.object else None) for m in o.modifiers]).encode())
   if o.data.shape_keys:
    for key in o.data.shape_keys.key_blocks:key.data.foreach_get('co',coords);geometry.update(coords.tobytes())
  elif o.type=='ARMATURE':geometry.update(str([(b.name,[list(v) for v in b.matrix_local]) for b in o.data.bones]).encode())
  elif o.type=='CURVES':hair[o.name]=[[[list(p.position),p.radius] for p in c.points] for c in o.data.curves]
 for m in bpy.data.materials:
  materials[m.name]=[list(m.diffuse_color),[(n.name,n.type,[(s.name,str(s.default_value)) for s in n.inputs if hasattr(s,'default_value')]) for n in m.node_tree.nodes] if m.node_tree else None]
 return geometry.hexdigest(),hair,materials
bpy.ops.wm.open_mainfile(filepath=str(SOURCE),load_ui=False,use_scripts=False);before=snapshot()
bpy.ops.wm.open_mainfile(filepath=str(TARGET),load_ui=False,use_scripts=False);after=snapshot()
assert before==after,'Body/raw guides/material drift'
assert after[0]=='b8425d97025e0fcb2dece841875631f783a077e81f5c894c26ce78148cc7fc5f'
obj=bpy.data.objects['2.side left 2'];assert len(obj.modifiers)==5 and obj.modifiers[0].name=='Joy_StrayGuideCleanup'
bpy.context.view_layer.update();assert len(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.curves)==1020
scene=bpy.context.scene;assert scene.cycles.device=='CPU' and scene.render.threads==4
scene.render.filepath=str(OUT/'Joy-hair-cleanup.png');bpy.ops.render.render(write_still=True)
report={'state':'SAVED_BLENDER_RELOAD_AND_CPU_PREVIEW_PASS','body_shape_keys_armature_sha256':after[0],'all_raw_hair_guides_and_materials_preserved':True,'derivative_sha256':sha(TARGET),'source_sha256':sha(SOURCE),'preview_sha256':sha(Path(scene.render.filepath)),'gpu_rendering':False}
(OUT/'Reload140.json').write_text(json.dumps(report,indent=2)+'\n');print('HAIR140_PASS',flush=True)
