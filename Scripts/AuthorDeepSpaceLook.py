"""Author the owned Asteroid Library look as private, editable presentation data.
Run in Unreal after the Editor target is built. Vendor assets and example maps are never saved.
"""
import unreal as u
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
BASE='/Game/SpaceSurvival/Licensed/Atmosphere'
SKY='/Game/Asteroid_Library/Space_Skybox_Library_16k_Sample'
lib=u.EditorAssetLibrary; edit=u.MaterialEditingLibrary

def duplicate(source,target):
    existing=lib.load_asset(target) if lib.does_asset_exist(target) else None
    return existing or lib.duplicate_asset(source,target)

def main():
    lib.make_directory(BASE)
    (ROOT/'Artifacts/EnvironmentRefresh').mkdir(parents=True,exist_ok=True)
    master=duplicate(SKY+'/Materials/M_Skybox_16k',BASE+'/M_DeepSpaceSky')
    assert master
    if lib.get_metadata_tag(master,'SSRegionTint')!='1':
        previous=edit.get_material_property_input_node(master,u.MaterialProperty.MP_EMISSIVE_COLOR)
        assert previous
        tint=edit.create_material_expression(master,u.MaterialExpressionVectorParameter,1000,400)
        tint.set_editor_property('parameter_name','Tint')
        tint.set_editor_property('default_value',u.LinearColor(1,1,1,1))
        white=edit.create_material_expression(master,u.MaterialExpressionConstant3Vector,1000,600)
        white.set_editor_property('constant',u.LinearColor(1,1,1,1))
        blend=edit.create_material_expression(master,u.MaterialExpressionLinearInterpolate,1200,400)
        blend.set_editor_property('const_alpha',.25)
        mult=edit.create_material_expression(master,u.MaterialExpressionMultiply,1400,100)
        assert edit.connect_material_expressions(white,'',blend,'A')
        assert edit.connect_material_expressions(tint,'',blend,'B')
        assert edit.connect_material_expressions(previous,'',mult,'A')
        assert edit.connect_material_expressions(blend,'',mult,'B')
        assert edit.connect_material_property(mult,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
        lib.set_metadata_tag(master,'SSRegionTint','1')
        edit.recompile_material(master)
    sky=duplicate(SKY+'/Material_Instances/MI_Skybox_024',BASE+'/MI_DeepSpaceSky')
    edit.set_material_instance_parent(sky,master)
    # Match the verified LV_1 cool sky, including explicit inherited texture overrides.
    source_sky=u.load_asset(SKY+'/Material_Instances/MI_Skybox_024')
    for kind in ['scalar','vector','texture']:
        for name in getattr(edit,'get_'+kind+'_parameter_names')(source_sky):
            value=getattr(edit,'get_material_instance_'+kind+'_parameter_value')(source_sky,name)
            if value is not None:
                getattr(edit,'set_material_instance_'+kind+'_parameter_value')(sky,name,value)
    edit.set_material_instance_scalar_parameter_value(sky,'Brightness',.35)
    cloud=duplicate('/Game/Asteroid_Library/Material_Instances/MI_Volume_CloudSimple_1',BASE+'/MI_DeepSpaceCloud')
    edit.set_material_instance_scalar_parameter_value(cloud,'Density',.000025)
    edit.set_material_instance_vector_parameter_value(cloud,'Color',u.LinearColor(.12,.19,.26,1))
    path=BASE+'/DA_DeepSpaceLook'
    look=lib.load_asset(path) if lib.does_asset_exist(path) else None
    if not look:
        cls=u.load_class(None,'/Script/SpaceSurvival.SSSpaceLookData')
        assert cls
        factory=u.DataAssetFactory();factory.set_editor_property('data_asset_class',cls)
        look=u.AssetToolsHelpers.get_asset_tools().create_asset('DA_DeepSpaceLook',BASE,cls,factory)
    assert look
    look.set_editor_property('SkyMaterial',sky)
    look.set_editor_property('CloudMaterial',cloud)
    look.set_editor_property('AmbientCubemap',u.load_asset(SKY+'/Textures/Skybox_Color_Textures/T_CUBE_Skybox_24'))
    look.set_editor_property('AmbientIntensity',40.)
    for asset in [master,sky,cloud,look]:
        assert lib.save_loaded_asset(asset,only_if_is_dirty=False)
    (ROOT/'Artifacts/EnvironmentRefresh/DeepSpaceAuthor.json').write_text(json.dumps({'status':'authored_requires_render','data':path,'sky':sky.get_path_name(),'cloud':cloud.get_path_name(),'intended_write_scope':'private derivatives only; vendor hashes not measured by this script'},indent=2))
    u.log('DEEP_SPACE_LOOK_AUTHORED')
if __name__=='__main__':main()
