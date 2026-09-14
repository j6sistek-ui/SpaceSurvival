"""New-only private station exterior import; lead schedules hidden Unreal authoring."""
from pathlib import Path
import hashlib
import json
import unreal as u

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Artifacts/StationExterior'
BASE='/Game/SpaceSurvival/Licensed/StationExterior'
LIB=u.EditorAssetLibrary

def main():
    report=json.loads((OUT/'Derivative.json').read_text(encoding='utf-8'))
    source=OUT/'StationExterior.glb'
    assert hashlib.sha256(source.read_bytes()).hexdigest()==report['output_sha256']
    assert not LIB.does_directory_exist(BASE),'Candidate directory exists; inspect before replacement'
    pipeline=u.new_object(u.InterchangeGenericAssetsPipeline,name='SSStationExteriorImport')
    for k,v in {'asset_name':'SM_StationExterior','use_source_name_for_asset':False,
                'asset_type_sub_folders':False,'scene_name_sub_folder':False}.items():
        pipeline.set_editor_property(k,v)
    mesh_pipeline=pipeline.get_editor_property('mesh_pipeline')
    mesh_pipeline.set_editor_property('import_static_meshes',True)
    mesh_pipeline.set_editor_property('import_skeletal_meshes',False)
    pipeline.get_editor_property('animation_pipeline').set_editor_property('import_animations',False)
    materials=pipeline.get_editor_property('material_pipeline')
    materials.set_editor_property('import_materials',True)
    materials.get_editor_property('texture_pipeline').set_editor_property('import_textures',True)
    params=u.ImportAssetParameters()
    params.set_editor_property('is_automated',True)
    params.set_editor_property('replace_existing',False)
    params.set_editor_property('override_pipelines',[u.SoftObjectPath(pipeline.get_path_name())])
    manager=u.InterchangeManager.get_interchange_manager_scripted()
    assets=manager.import_asset(BASE,manager.create_source_data(str(source)),params)
    meshes=[a for a in assets if isinstance(a,u.StaticMesh)]
    assert len(meshes)==1
    target=BASE+'/SM_StationExterior'
    mesh=meshes[0]
    if mesh.get_path_name().split('.')[0]!=target:
        assert LIB.rename_asset(mesh.get_path_name(),target)
    mesh=u.load_asset(target)
    assert len(mesh.static_materials)==report['primitives']
    assert all(slot.material_interface for slot in mesh.static_materials)
    bounds=mesh.get_bounds()
    assert abs(bounds.box_extent.x*2-10000)<10,'Unexpected GLB scale/axis; do not adopt'
    u.get_editor_subsystem(u.StaticMeshEditorSubsystem).remove_collisions(mesh)
    for asset in assets:
        assert LIB.save_loaded_asset(asset,only_if_is_dirty=False)
    assert LIB.save_loaded_asset(mesh,only_if_is_dirty=False)
    result=dict(mesh=mesh.get_path_name(),source_sha256=report['output_sha256'],
                assets=[a.get_path_name() for a in assets],
                materials=[s.material_interface.get_path_name() for s in mesh.static_materials],
                status='IMPORTED_NOT_RUNTIME_VALIDATED',engine=u.SystemLibrary.get_engine_version())
    (OUT/'Import.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    u.log('STATION_EXTERIOR_IMPORTED '+json.dumps(result))

if __name__=='__main__':
    main()
