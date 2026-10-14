"""Scoped existing Joy skin finish; preserve texture, tint, mesh and animation."""
from pathlib import Path
import hashlib, json, shutil

PARTS=('Head','Body','Arm','Leg')
ROOT='/Game/SpaceSurvival/Licensed/StationAssets/JoyLightBlue117'
def apply(u):
    repo=Path(u.Paths.project_dir()).resolve()
    out=repo/'.agent/local/StationRefinement/JoyMetal216'
    assert not out.exists(),'Fresh scoped edit only; inspect any existing receipt before retry.'
    assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    assert not u.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    matlib=u.MaterialEditingLibrary
    mats=[u.load_asset(ROOT+'/Materials/MI_JoyBlue_Skin_'+p) for p in PARTS]
    assert all(mats)
    master=u.load_asset('/Game/SpaceSurvival/Licensed/StationAssets/JoyPurple/Materials/M_JoyOpaque')
    assert str(master.get_editor_property('shading_model'))=='<MaterialShadingModel.MSM_DEFAULT_LIT: 1>'
    assert str(matlib.get_material_property_input_node(master,u.MaterialProperty.MP_METALLIC).get_editor_property('parameter_name'))=='Metallic'
    for mat in mats:
        assert mat.get_editor_property('parent')==master
        assert matlib.get_material_instance_scalar_parameter_value(mat,'Metallic')==0.
    out.mkdir(parents=True)
    report={'status':'PREPARED','materials':[],'metallic':.75,'roughness':.32}
    for mat in mats:
        file=repo/'Content'/(mat.get_path_name().split('.')[0].removeprefix('/Game/')+'.uasset')
        shutil.copy2(file,out/file.name)
        color=matlib.get_material_instance_vector_parameter_value(mat,'Tint')
        row={'path':mat.get_path_name(),'before_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'tint':[color.r,color.g,color.b,color.a],'textures':{str(n):matlib.get_material_instance_texture_parameter_value(mat,n).get_path_name() for n in matlib.get_texture_parameter_names(mat)},'before_metallic':matlib.get_material_instance_scalar_parameter_value(mat,'Metallic'),'before_roughness':matlib.get_material_instance_scalar_parameter_value(mat,'Roughness')}
        report['materials'].append(row)
    (out/'Receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    for mat,row in zip(mats,report['materials']):
        matlib.set_material_instance_scalar_parameter_value(mat,'Metallic',.75)
        matlib.set_material_instance_scalar_parameter_value(mat,'Roughness',.32)
        assert abs(matlib.get_material_instance_scalar_parameter_value(mat,'Metallic')-.75)<1e-5
        assert abs(matlib.get_material_instance_scalar_parameter_value(mat,'Roughness')-.32)<1e-5
        color=matlib.get_material_instance_vector_parameter_value(mat,'Tint')
        assert [color.r,color.g,color.b,color.a]==row['tint']
        assert {str(n):matlib.get_material_instance_texture_parameter_value(mat,n).get_path_name() for n in matlib.get_texture_parameter_names(mat)}==row['textures']
        matlib.update_material_instance(mat)
        assert u.EditorAssetLibrary.save_loaded_asset(mat,False)
        file=repo/'Content'/(mat.get_path_name().split('.')[0].removeprefix('/Game/')+'.uasset')
        row['after_sha256']=hashlib.sha256(file.read_bytes()).hexdigest()
    report['status']='SAVED_NATIVE_VISUAL_REVIEW_PENDING'
    (out/'Receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
