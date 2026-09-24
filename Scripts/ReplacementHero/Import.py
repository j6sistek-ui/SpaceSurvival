"""Native import staging; original game hero assets are never overwritten."""
import os
import unreal as u,json,hashlib
from pathlib import Path
ROOT=Path(u.Paths.project_dir()).resolve();SRC=Path(os.environ['SS_HERO_SOURCE']);BASE='/Game/SpaceSurvival/Licensed/HeroReplacement/Final';LIB=u.EditorAssetLibrary
manifest=json.loads((SRC/'main_game_import_plan.json').read_text())
assert hashlib.sha256((SRC/'SquirrelHero_SoftFur.fbx').read_bytes()).hexdigest()==manifest['verified_inputs']['SquirrelHero_SoftFur.fbx']
SRC=SRC/'UnrealUnits'
assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
def pipeline(name,animation=False,skeleton=None):
 p=u.new_object(u.InterchangeGenericAssetsPipeline,name=name+'Pipeline')
 for k,v in {'asset_name':name,'use_source_name_for_asset':False,'asset_type_sub_folders':False,'scene_name_sub_folder':False}.items():p.set_editor_property(k,v)
 c=p.get_editor_property('common_skeletal_meshes_and_animations_properties')
 c.set_editor_property('import_only_animations',animation);c.set_editor_property('try_auto_select_skeleton',False)
 if skeleton:c.set_editor_property('skeleton',skeleton)
 m=p.get_editor_property('mesh_pipeline');m.set_editor_property('import_static_meshes',False);m.set_editor_property('import_skeletal_meshes',not animation);m.set_editor_property('create_physics_asset',not animation);m.set_editor_property('update_skeleton_reference_pose',False)
 m.set_editor_property('combine_skeletal_meshes_behavior',u.InterchangeCombineSkeletalMeshesBehavior.BY_SKELETON)
 p.get_editor_property('animation_pipeline').set_editor_property('import_animations',animation)
 p.get_editor_property('material_pipeline').set_editor_property('import_materials',False)
 p.get_editor_property('material_pipeline').get_editor_property('texture_pipeline').set_editor_property('import_textures',False)
 return p
def do_import(name,filename,animation=False,skeleton=None):
 if LIB.does_asset_exist(BASE+'/'+name):return u.load_asset(BASE+'/'+name)
 p=pipeline(name,animation,skeleton);a=u.ImportAssetParameters();a.set_editor_property('is_automated',True);a.set_editor_property('replace_existing',False);a.set_editor_property('override_pipelines',[u.SoftObjectPath(p.get_path_name())])
 mgr=u.InterchangeManager.get_interchange_manager_scripted();objs=mgr.import_asset(BASE,mgr.create_source_data(str(SRC/filename)),a)
 target_type=u.AnimSequence if animation else u.SkeletalMesh
 chosen=[o for o in objs if isinstance(o,target_type)];assert len(chosen)==1,[(o.get_name(),o.get_class().get_name()) for o in objs]
 asset=chosen[0]
 if asset.get_path_name().split('.')[0]!=BASE+'/'+name:assert LIB.rename_asset(asset.get_path_name(),BASE+'/'+name)
 asset=u.load_asset(BASE+'/'+name)
 for o in objs:LIB.save_loaded_asset(o)
 return asset
mesh=do_import('SK_SquirrelHeroReplacement','SquirrelHero_SoftFur.fbx')
print('IMPORTED',mesh.get_path_name(),mesh.get_bounds(),[str(m.material_slot_name) for m in mesh.materials])
print('pose_api',[n for n in dir(u.AnimPoseExtensions) if 'ref' in n or 'bone' in n])
print('skeleton_api',[n for n in dir(mesh.skeleton) if 'bone' in n or 'ref' in n])
for name in ['Idle','Walk','Run','JumpStart','JumpAir','JumpLand']:
 clip=do_import('Tail_'+name,'Tail_'+name+'.fbx',True,mesh.skeleton)
 print('TAIL',clip.get_name(),clip.sequence_length)
print('STAGE_OK')

