"""Keep cloth render geometry intact; expose four sections and export the existing small simulation cages."""
import bpy,json,hashlib,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'.agent/local/HeroIntegration_20261020';P=OUT/'SourceManifest.json';data=json.loads(P.read_text());h=next(h for h in data['heroes'] if h['key']=='Cloth')
bpy.ops.wm.open_mainfile(filepath=h['source_blend'],load_ui=False);s=bpy.context.scene;rig=bpy.data.objects['ClothHero_Rig'];rig['ClothSimulation']=0.
if rig.animation_data:rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
s.frame_set(1);bpy.context.view_layer.update();template=h['materials'][0];h['materials']=[]
physical={'bone_points_cm':{b.name:list((rig.matrix_world@b.head_local)*100) for b in rig.data.bones},'parts':[]}
names=[('Armor','ClothHero_Armor')]+[(n,n+'_Render') for n in ['Cape','FrontTabard','RearTabard','SideTabard']]
for label,name in names:
    obj=bpy.data.objects[name];mat=obj.data.materials[0].copy();mat.name='Cloth_'+label;obj.data.materials[0]=mat
    desc=copy.deepcopy(template);desc['name']=mat.name;h['materials'].append(desc);h['mesh_materials'][name]=[mat.name]
    if 'FollowClothSimulation' in obj.modifiers:obj.modifiers.remove(obj.modifiers['FollowClothSimulation'])
    if label=='Armor':continue
    skin=obj.modifiers['CharacterSkin']
    for prop in ['show_viewport','show_render']:skin.driver_remove(prop);setattr(skin,prop,True)
    cage=bpy.data.objects[label+'_SIM'];cage.data.calc_loop_triangles();verts=[list((cage.matrix_world@v.co)*100) for v in cage.data.vertices]
    length=max(v[2] for v in verts)-min(v[2] for v in verts);pin=[]
    for v in cage.data.vertices:
        try:p=cage.vertex_groups['Cloth_Pin'].weight(v.index)
        except RuntimeError:p=0.
        pin.append(p)
    physical['parts'].append({'name':label,'material_slot':mat.name,'root_bone':'spine_03' if label=='Cape' else 'pelvis','vertices_cm':verts,'triangles':[list(t.vertices) for t in cage.data.loop_triangles],'max_distance_cm':[(1-p)*length for p in pin]})
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for label,name in names:bpy.data.objects[name].select_set(True)
bpy.context.view_layer.objects.active=rig;rig.name='Armature';target=OUT/'Cloth_Unreal.fbx'
bpy.ops.export_scene.fbx(filepath=str(target),use_selection=True,object_types={'ARMATURE','MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',use_mesh_modifiers=True,mesh_smooth_type='FACE',use_triangles=True,add_leaf_bones=False,use_armature_deform_only=True,armature_nodetype='NULL',bake_anim=False,path_mode='RELATIVE',embed_textures=False)
h['source_fbx']=h['fbx'];h['source_fbx_sha256']=h['fbx_sha256'];h['fbx']=str(target);h['fbx_sha256']=hashlib.sha256(target.read_bytes()).hexdigest();h['derivative_note']='Five material sections preserve original render geometry/UV/skin;585 source cage vertices are exported separately for Chaos clothing.'
(OUT/'ClothPhysicalSource.json').write_text(json.dumps(physical,indent=2));P.write_text(json.dumps(data,indent=2));print('CLOTH_SECTIONS_READY',flush=True)
