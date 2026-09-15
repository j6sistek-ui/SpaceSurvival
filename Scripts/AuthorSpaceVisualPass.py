"""Author private NebulaFantasy regions, retaining vendor assets unchanged.
Run after compiling Editor. Only selected cubemaps are copied/cooked; maps remain examples.
"""
import json
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1]
BASE='/Game/SpaceSurvival/Licensed/Atmosphere'
LIB=u.EditorAssetLibrary
EDIT=u.MaterialEditingLibrary

def duplicate(src,name):
    path=BASE+'/'+name
    a=LIB.load_asset(path) if LIB.does_asset_exist(path) else LIB.duplicate_asset(src,path)
    assert a, src
    return a

def main():
    LIB.make_directory(BASE)
    cubes=[]
    for folder,name in [('Skybox_8','T_Nebula_Turquoise_Dark_8'),('Skybox_6','T_Nebula_Orange_6'),('Skybox_1','T_Nebula_Blue_1')]:
        a=duplicate('/Game/SpaceNebulaFantasy/Textures/'+folder+'/'+name,'T_Region_'+folder)
        a.set_editor_property('max_texture_size',2048)
        cubes.append(a)
    stars=duplicate('/Game/SpaceNebulaFantasy/Textures/Starfields/T_Stars_Far_White','T_RegionStars')
    stars.set_editor_property('max_texture_size',1024)
    path=BASE+'/M_RegionSky'
    m=LIB.load_asset(path) if LIB.does_asset_exist(path) else u.AssetToolsHelpers.get_asset_tools().create_asset('M_RegionSky',BASE,u.Material,u.MaterialFactoryNew())
    EDIT.delete_all_material_expressions(m)
    m.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property('two_sided',True)
    # Match the working vendor material: this project's capture was black with
    # is_sky=True and rendered the same graph/cubemaps with False. The deeper
    # renderer interaction is not diagnosed by that bounded comparison.
    m.set_editor_property('is_sky',False)
    def node(cls,**props):
        n=EDIT.create_material_expression(m,getattr(u,cls),0,0)
        for k,v in props.items(): n.set_editor_property(k,v)
        return n
    def link(a,b,pin,output=''):
        assert EDIT.connect_material_expressions(a,output,b,pin), (str(b.get_class()), pin, EDIT.get_material_expression_input_names(b))
    view=node('MaterialExpressionCameraVectorWS')
    direction=node('MaterialExpressionMultiply',const_b=-1.)
    link(view,direction,'A')
    def sample(name,tex):
        n=node('MaterialExpressionTextureSampleParameterCube',parameter_name=name,texture=tex)
        link(direction,n,'UVs')
        return n
    a=sample('RegionA',cubes[0]);b=sample('RegionB',cubes[1]);star=sample('Stars',stars)
    alpha=node('MaterialExpressionScalarParameter',parameter_name='RegionBlend',default_value=0.)
    blend=node('MaterialExpressionLinearInterpolate')
    link(a,blend,'A','RGB');link(b,blend,'B','RGB');link(alpha,blend,'Alpha')
    desat=node('MaterialExpressionDesaturation')
    saturation=node('MaterialExpressionConstant',r=.3)
    link(saturation,desat,'Fraction')
    link(blend,desat,'')
    power=node('MaterialExpressionScalarParameter',parameter_name='SkyBrightness',default_value=.3)
    mult=node('MaterialExpressionMultiply');link(desat,mult,'A');link(power,mult,'B')
    # Stars have their own exposure and a fixed directional brightness distribution.
    # Most points recede; the noise is anchored to the cubemap direction, never time.
    star_contrast=node('MaterialExpressionPower',const_exponent=1.45)
    link(star,star_contrast,'Base','RGB')
    star_brightness=node('MaterialExpressionScalarParameter',parameter_name='StarBrightness',default_value=.30)
    noise_function=next(getattr(u.NoiseFunction,name) for name in dir(u.NoiseFunction)
                        if 'GRADIENTTEX3D' in name.upper().replace('_',''))
    variation=node('MaterialExpressionNoise',scale=35.,quality=1,levels=1,
                   output_min=.18,output_max=1.,noise_function=noise_function)
    # UE 5.8 names this pin by its world-position origin; query the reflected name.
    link(direction,variation,str(EDIT.get_material_expression_input_names(variation)[0]))
    star_varied=node('MaterialExpressionMultiply');link(star_contrast,star_varied,'A');link(variation,star_varied,'B')
    stars_gain=node('MaterialExpressionMultiply');link(star_varied,stars_gain,'A');link(star_brightness,stars_gain,'B')
    add=node('MaterialExpressionAdd');link(mult,add,'A');link(stars_gain,add,'B')
    assert EDIT.connect_material_property(add,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
    EDIT.layout_material_expressions(m);EDIT.recompile_material(m)
    look=LIB.load_asset(BASE+'/DA_DeepSpaceLook');assert look
    look.set_editor_property('sky_material',m)
    look.set_editor_property('region_skies',cubes)
    look.set_editor_property('region_stars',stars)
    look.set_editor_property('region_seconds',180.)
    look.set_editor_property('ambient_intensity',8.)
    look.set_editor_property('key_color',u.LinearColor(.95,.87,.73,1))
    look.set_editor_property('key_intensity',4.)
    meshes=[]
    for path in ['/Game/SpaceSurvival/Licensed/StationVisualPass/Meshes/SM_Station3Exterior','/Game/SpaceSurvival/Licensed/StationExterior/SM_StationExterior']:
        if LIB.does_asset_exist(path): meshes.append(LIB.load_asset(path))
    look.set_editor_property('structure_meshes',meshes)
    cloud=look.get_editor_property('cloud_material')
    if cloud:
        EDIT.set_material_instance_scalar_parameter_value(cloud,'Density',.000012)
        EDIT.set_material_instance_vector_parameter_value(cloud,'Color',u.LinearColor(.12,.16,.2,1))
    for asset in cubes+[stars,m,look]+([cloud] if cloud else []):
        assert LIB.save_loaded_asset(asset,only_if_is_dirty=False)
    out=ROOT/'Artifacts/VisualPass';out.mkdir(parents=True,exist_ok=True)
    (out/'SpaceAuthor.json').write_text(json.dumps({'status':'AUTHORED_REQUIRES_RENDER','regions':[x.get_path_name() for x in cubes],'structures':[x.get_path_name() for x in meshes],'vendor_saved':False,'stars':{'brightness':.30,'contrast_exponent':1.45,'directional_gain_min':.18,'directional_gain_max':1.,'noise_scale':35.,'temporal_animation':False}},indent=2))
    u.log('SPACE_VISUAL_PASS_AUTHORED')
if __name__=='__main__':main()
