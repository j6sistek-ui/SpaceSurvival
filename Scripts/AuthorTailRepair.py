"""Import the separately reviewed tail-only v2 repair; original content untouched."""
import hashlib,json
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1]
BASE='/Game/SpaceSurvival/Character'
TARGET=BASE+'/SK_AcornautTailV2'
LIB=u.EditorAssetLibrary
VERSION='ScreenRayTailV2'


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_source():
    source=ROOT/'ContentSource/Animation/TailCandidateV2.glb';manifest=json.loads(source.with_suffix('.json').read_text(encoding='utf-8'))
    assert digest(source)==manifest['sha256'],'Tail source differs from reviewed manifest'
    for name,expected in manifest['protected_sources'].items():assert digest(ROOT/name)==expected,'Protected character source changed: '+name
    assert digest(ROOT/'ContentSource/TailCandidateV2Preview/RaySelection.json')==manifest['ray_selection_sha256']
    assert digest(ROOT/'ContentSource/TailCandidateV2Preview/RaySelectionResidual.json')==manifest['residual_selection_sha256']
    return source,manifest


def main():
    receipt={'status':'FAILED','engine':u.SystemLibrary.get_engine_version(),'errors':[],
             'limits':['Provisional art selection; thin residual fragments remain','No gameplay or native deformation validation from import alone']}
    protected={path:digest(path) for path in (ROOT/'Content').rglob('*.uasset') if path.stem!='SK_AcornautTailV2'}
    try:
        source,manifest=verify_source();original=LIB.load_asset(BASE+'/SK_Acornaut');assert isinstance(original,u.SkeletalMesh)
        skeleton=original.get_editor_property('skeleton');assert skeleton
        mesh=LIB.load_asset(TARGET)
        if mesh:
            assert LIB.get_metadata_tag(mesh,'SSTailRepairVersion')==VERSION and LIB.get_metadata_tag(mesh,'SSTailRepairSourceSHA256')==manifest['sha256'],'Tail candidate requires deliberate reviewed reimport'
        else:
            pipeline=u.new_object(u.InterchangeGenericAssetsPipeline,name='SSTailV2OnlyImport')
            for key,value in {'asset_name':'SK_AcornautTailV2','use_source_name_for_asset':False,'asset_type_sub_folders':False,'scene_name_sub_folder':False}.items():pipeline.set_editor_property(key,value)
            common=pipeline.get_editor_property('common_skeletal_meshes_and_animations_properties')
            for key,value in {'import_only_animations':False,'skeleton':skeleton,'try_auto_select_skeleton':False,'use_t0_as_ref_pose':False}.items():common.set_editor_property(key,value)
            settings=pipeline.get_editor_property('mesh_pipeline')
            for key,value in {'import_skeletal_meshes':True,'import_static_meshes':False,'create_physics_asset':False,'update_skeleton_reference_pose':False}.items():settings.set_editor_property(key,value)
            settings.set_editor_property('combine_skeletal_meshes_behavior',u.InterchangeCombineSkeletalMeshesBehavior.BY_SKELETON)
            pipeline.get_editor_property('animation_pipeline').set_editor_property('import_animations',False)
            material=pipeline.get_editor_property('material_pipeline');material.set_editor_property('import_materials',False);material.get_editor_property('texture_pipeline').set_editor_property('import_textures',False)
            params=u.ImportAssetParameters();params.set_editor_property('is_automated',True);params.set_editor_property('replace_existing',False);params.set_editor_property('override_pipelines',[u.SoftObjectPath(pipeline.get_path_name())])
            manager=u.InterchangeManager.get_interchange_manager_scripted();imported=manager.import_asset(BASE,manager.create_source_data(str(source)),params)
            assert len(imported)==1 and isinstance(imported[0],u.SkeletalMesh),'Expected one skeletal mesh only'
            mesh=imported[0];assert mesh.get_path_name().split('.')[0]==TARGET
            assert mesh.get_editor_property('skeleton')==skeleton
            mesh.set_editor_property('materials',original.get_editor_property('materials'))
            LIB.set_metadata_tag(mesh,'SSAuthoringVersion','1');LIB.set_metadata_tag(mesh,'SSTailRepairVersion',VERSION);LIB.set_metadata_tag(mesh,'SSTailRepairSourceSHA256',manifest['sha256'])
            LIB.set_metadata_tag(mesh,'SSTailRepairScope','TailOnly2631AdditionalVerticesOriginalSkeletonMaterials')
            assert LIB.save_loaded_asset(mesh,only_if_is_dirty=False),'Candidate save failed'
        assert all(digest(path)==expected for path,expected in protected.items()),'Protected content package changed'
        receipt.update(status='TAIL_V2_IMPORTED_FRESH_RELOAD_AND_RENDER_PENDING',mesh=mesh.get_path_name(),skeleton=skeleton.get_path_name(),
                       materials=[s.get_editor_property('material_interface').get_path_name() for s in mesh.get_editor_property('materials')],
                       source_sha256=manifest['sha256'],protected_content_packages_unchanged=len(protected),imported_asset_count=1)
    except Exception as error:receipt['errors'].append(str(error));u.log_error('TAIL_V2_IMPORT_FAILED: '+str(error))
    output=ROOT/'Saved/Validation/TailRepairImport.json';output.parent.mkdir(exist_ok=True,parents=True);output.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    if receipt['errors']:raise RuntimeError('Tail repair import failed; inspect fresh receipt')
    u.log('TAIL_V2_IMPORT_OK')


if __name__=='__main__':main()
