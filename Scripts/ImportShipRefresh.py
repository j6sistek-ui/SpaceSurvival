"""Import fitted Ludo ship new-only, preserving its PBR material/textures."""
from pathlib import Path
import hashlib,json
import unreal as u
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Artifacts/ShipRefresh';BASE='/Game/SpaceSurvival/ShipRefresh';LIB=u.EditorAssetLibrary

def main():
 report=json.loads((OUT/'Report.json').read_text());source=OUT/'LudoStarter.glb'
 assert hashlib.sha256(source.read_bytes()).hexdigest()==report['output_sha256']
 assert not LIB.does_directory_exist(BASE),'Candidate directory exists; inspect before replacement'
 pipeline=u.new_object(u.InterchangeGenericAssetsPipeline,name='SSLudoShipImport')
 for k,v in {'asset_name':'SM_LudoStarter','use_source_name_for_asset':False,'asset_type_sub_folders':False,'scene_name_sub_folder':False}.items():pipeline.set_editor_property(k,v)
 mesh=pipeline.get_editor_property('mesh_pipeline')
 for k,v in {'import_static_meshes':True,'import_skeletal_meshes':False}.items():mesh.set_editor_property(k,v)
 pipeline.get_editor_property('animation_pipeline').set_editor_property('import_animations',False)
 mat=pipeline.get_editor_property('material_pipeline');mat.set_editor_property('import_materials',True);mat.get_editor_property('texture_pipeline').set_editor_property('import_textures',True)
 params=u.ImportAssetParameters();params.set_editor_property('is_automated',True);params.set_editor_property('replace_existing',False);params.set_editor_property('override_pipelines',[u.SoftObjectPath(pipeline.get_path_name())])
 mgr=u.InterchangeManager.get_interchange_manager_scripted();assets=mgr.import_asset(BASE,mgr.create_source_data(str(source)),params)
 meshes=[a for a in assets if isinstance(a,u.StaticMesh)];assert len(meshes)==1
 target=BASE+'/SM_LudoStarter';m=meshes[0]
 if m.get_path_name().split('.')[0]!=target:assert LIB.rename_asset(m.get_path_name(),target)
 m=u.load_asset(target);assert len(m.get_editor_property('static_materials'))==1
 for slot in m.get_editor_property('static_materials'):assert slot.get_editor_property('material_interface')
 for asset in assets:LIB.save_loaded_asset(asset,only_if_is_dirty=False)
 LIB.save_loaded_asset(m,only_if_is_dirty=False)
 record={'mesh':m.get_path_name(),'assets':[a.get_path_name()for a in assets],'source_sha256':report['output_sha256'],'status':'IMPORTED_REQUIRES_GAMEPLAY_VISUAL_FIT','engine':u.SystemLibrary.get_engine_version()}
 (OUT/'Import.json').write_text(json.dumps(record,indent=2));u.log(json.dumps(record))
if __name__=='__main__':main()
