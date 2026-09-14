"""Run in Unreal by lead, import isolated A_WalkLegRepair only. No original replacement."""
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1];BASE='/Game/SpaceSurvival/Character'
lib=u.EditorAssetLibrary
for stem in ['WalkLegRepair','DisembarkLegRepair']:
 TARGET=BASE+'/A_'+stem
 assert not lib.does_asset_exist(TARGET),'Inspect existing derivative before replacing'
 original=u.load_asset(BASE+'/SK_Acornaut');skeleton=original.get_editor_property('skeleton')
 p=u.new_object(u.InterchangeGenericAssetsPipeline,name='SS'+stem+'Import')
 for k,v in {'asset_name':'A_'+stem,'use_source_name_for_asset':False,'asset_type_sub_folders':False,'scene_name_sub_folder':False}.items():p.set_editor_property(k,v)
 c=p.get_editor_property('common_skeletal_meshes_and_animations_properties')
 for k,v in {'import_only_animations':True,'skeleton':skeleton,'try_auto_select_skeleton':False}.items():c.set_editor_property(k,v)
 m=p.get_editor_property('mesh_pipeline')
 for k in ['import_skeletal_meshes','import_static_meshes','create_physics_asset','update_skeleton_reference_pose']:m.set_editor_property(k,False)
 p.get_editor_property('animation_pipeline').set_editor_property('import_animations',True)
 p.get_editor_property('material_pipeline').set_editor_property('import_materials',False)
 p.get_editor_property('material_pipeline').get_editor_property('texture_pipeline').set_editor_property('import_textures',False)
 a=u.ImportAssetParameters();a.set_editor_property('is_automated',True);a.set_editor_property('replace_existing',False);a.set_editor_property('override_pipelines',[u.SoftObjectPath(p.get_path_name())])
 mgr=u.InterchangeManager.get_interchange_manager_scripted();objects=mgr.import_asset(BASE,mgr.create_source_data(str(ROOT/'Artifacts/HeroLegRepair'/(stem+'.glb'))),a)
 assert len(objects)==1 and isinstance(objects[0],u.AnimSequence)
 clip=objects[0]
 if clip.get_path_name().split('.')[0]!=TARGET:assert lib.rename_asset(clip.get_path_name(),TARGET)
 clip=u.load_asset(TARGET);assert clip.get_editor_property('skeleton')==skeleton
 assert lib.save_loaded_asset(clip,only_if_is_dirty=False)
 u.log('Hero leg repair imported isolated derivative '+TARGET)
