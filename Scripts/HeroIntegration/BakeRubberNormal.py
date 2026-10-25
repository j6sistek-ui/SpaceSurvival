"""Bake procedural seals on new UVs in a separate Unreal FBX; never save the source blend."""
import bpy,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'.agent/local/HeroIntegration_20261020';P=OUT/'SourceManifest.json';data=json.loads(P.read_text())
h=data['heroes'][0];bpy.ops.wm.open_mainfile(filepath=h['source_blend'],load_ui=False)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=1;s.render.bake.use_clear=True;s.render.bake.margin=16;s.render.bake.normal_space='TANGENT'
template=next(m for m in h['materials'] if m['name']=='Technical_Rubber_Procedural');h['materials'].remove(template)
import copy
for name in ['Wrist_Seal_L','Wrist_Seal_R','Knee_Seal_L','Knee_Seal_R','Neck_Seal']:
    o=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    if not o.data.uv_layers:
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT')
    m=o.data.materials[0].copy();m.name='Technical_Rubber_'+name;o.data.materials[0]=m
    im=bpy.data.images.new('RubberNormal_'+name,4096,4096,alpha=False);im.colorspace_settings.name='Non-Color'
    n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=im;m.node_tree.nodes.active=n
    bpy.ops.object.bake(type='NORMAL');path=OUT/'SourceTextures'/('RubberNormal_'+name+'.png');im.filepath_raw=str(path);im.file_format='PNG';im.save()
    digest=hashlib.sha256(path.read_bytes()).hexdigest();h['images'][digest]={'file':str(path),'size':[4096,4096],'color_space':'Non-Color','name':im.name,'sha256':digest}
    mat=copy.deepcopy(template);mat['name']=m.name;mat['portable_normal']=digest
    mat['portable_normal_note']='Exact source procedural grain baked onto new UVs for this seal only; original native blend unchanged.'
    h['materials'].append(mat);h['mesh_materials'][name]=[m.name];print('RUBBER_NORMAL_BAKED',name,flush=True)
rig=next(o for o in s.objects if o.type=='ARMATURE');bpy.ops.object.select_all(action='DESELECT')
for o in s.objects:
    if o==rig or o.name in h['mesh_materials']:o.select_set(True)
bpy.context.view_layer.objects.active=rig;old=rig.name;rig.name='Armature';target=OUT/'EX7_Unreal.fbx'
bpy.ops.export_scene.fbx(filepath=str(target),use_selection=True,object_types={'ARMATURE','MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',use_mesh_modifiers=True,mesh_smooth_type='FACE',use_triangles=True,add_leaf_bones=False,use_armature_deform_only=True,armature_nodetype='NULL',bake_anim=False,path_mode='RELATIVE',embed_textures=False)
h['source_fbx']=h['fbx'];h['source_fbx_sha256']=h['fbx_sha256'];h['fbx']=str(target);h['fbx_sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
h['derivative_note']='Only five previously UV-less procedural seals receive UVs and per-seal4K normal bakes. Native original and existing mapped surfaces unchanged.'
P.write_text(json.dumps(data,indent=2));print('PORTABLE_EX7_READY',str(target),flush=True)
