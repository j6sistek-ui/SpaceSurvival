"""Fresh native import only; no level placement, reimport, rig or gameplay changes.
Set SS_BAR_HOLOGRAM_SOURCE to ExportAssets.py's output directory. Execute in an
isolated Unreal editor, outside PIE; see docs/production/BAR_HOLOGRAM.md.
"""
import json,os
from pathlib import Path
import unreal as u
D=Path(os.environ['SS_BAR_HOLOGRAM_SOURCE']).resolve()
assert not u.EditorLevelLibrary.get_pie_worlds(False)
assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
L=u.EditorAssetLibrary;E=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools()
DEST='/Game/SpaceSurvival/Licensed/StationAssets/BarHologram_20261016'
assert not L.does_directory_exist(DEST),'Fresh import only'
u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
exports=json.loads((D/'Export.json').read_text());receipt=[]
def save(asset):
    assert L.save_loaded_asset(asset,False),asset.get_path_name()
    return asset
for row in exports:
    folder=DEST+'/'+row['name'];L.make_directory(folder)
    opt=u.FbxImportUI()
    for k,v in dict(automated_import_should_detect_type=False,mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH,import_as_skeletal=False,import_mesh=True,import_animations=False,import_materials=False,import_textures=False).items():opt.set_editor_property(k,v)
    data=opt.get_editor_property('static_mesh_import_data')
    for k,v in dict(combine_meshes=True,auto_generate_collision=False,convert_scene=True,convert_scene_unit=True,force_front_x_axis=False,normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS).items():data.set_editor_property(k,v)
    task=u.AssetImportTask();task.filename=row['fbx'];task.destination_path=folder;task.destination_name='SM_'+row['name'];task.automated=True;task.replace_existing=False;task.save=False;task.options=opt;task.factory=u.FbxFactory()
    AT.import_asset_tasks([task]);mesh=next((u.load_asset(p) for p in task.imported_object_paths if isinstance(u.load_asset(p),u.StaticMesh)),None);assert mesh
    textures={}
    for tr in row['textures']:
        task=u.AssetImportTask();task.filename=tr['path'];task.destination_path=folder;task.destination_name='T_'+row['name']+'_'+tr['name'];task.automated=True;task.replace_existing=False;task.save=False
        AT.import_asset_tasks([task]);tex=next(u.load_asset(p) for p in task.imported_object_paths if isinstance(u.load_asset(p),u.Texture2D))
        if tr['name']!='BaseColor':tex.set_editor_property('srgb',False)
        if tr['name']=='Normal':
            tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP);tex.set_editor_property('flip_green_channel',True)
        elif tr['name']=='MetallicRoughness':tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_MASKS)
        tex.set_editor_property('max_texture_size',2048);textures[tr['name']]=save(tex)
    material=AT.create_asset('M_'+row['name'],folder,u.Material,u.MaterialFactoryNew());assert material
    def node(kind,**props):
        n=E.create_material_expression(material,getattr(u,kind));assert n
        for k,v in props.items():n.set_editor_property(k,v)
        return n
    def link(a,b,pin,out=''):assert E.connect_material_expressions(a,out,b,pin),(a,b,pin)
    def op(kind,a,b):
        n=node(kind);link(a,n,'A');link(b,n,'B');return n
    def mul(a,b):return op('MaterialExpressionMultiply',a,b)
    def add(a,b):return op('MaterialExpressionAdd',a,b)
    def scalar(name,value):return node('MaterialExpressionScalarParameter',parameter_name=name,default_value=value)
    base=node('MaterialExpressionTextureSampleParameter2D',parameter_name='BaseColorTexture',texture=textures['BaseColor'],sampler_type=u.MaterialSamplerType.SAMPLERTYPE_COLOR)
    if row['name']=='WaitressHologram':
        material.set_editor_property('blend_mode',u.BlendMode.BLEND_TRANSLUCENT);material.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT);material.set_editor_property('two_sided',False)
        f=node('MaterialExpressionFresnel',base_reflect_fraction=0.);link(scalar('RimExponent',2.3),f,'ExponentIn')
        pos=node('MaterialExpressionWorldPosition');mask=node('MaterialExpressionComponentMask',r=False,g=False,b=True,a=False);link(pos,mask,'')
        phase=add(mul(mask,scalar('ScanCyclesPerCm',.3)),mul(node('MaterialExpressionTime'),scalar('ScanCyclesPerSecond',.25)))
        sine=node('MaterialExpressionSine',period=1.);link(phase,sine,'');half=node('MaterialExpressionMultiply',const_b=.5);link(sine,half,'A');positive=node('MaterialExpressionAdd',const_b=.5);link(half,positive,'A')
        stripe=node('MaterialExpressionPower');link(positive,stripe,'Base');link(scalar('ScanSharpness',12.),stripe,'Exp')
        opacity=add(scalar('BodyOpacity',.28),add(mul(f,scalar('RimOpacity',.42)),mul(stripe,scalar('ScanOpacity',.13))))
        gain=add(scalar('BodyGlow',7.),add(mul(f,scalar('RimGlow',14.)),mul(stripe,scalar('ScanGlow',6.))))
        tint=node('MaterialExpressionVectorParameter',parameter_name='Tint',default_value=u.LinearColor(.025,.8,.62,1.))
        grey=node('MaterialExpressionDesaturation');link(base,grey,'','RGB');detail=node('MaterialExpressionMultiply',const_b=.6);link(grey,detail,'A');lift=node('MaterialExpressionAdd',const_b=.4);link(detail,lift,'A')
        emission=mul(mul(tint,lift),gain)
        assert E.connect_material_property(opacity,'',u.MaterialProperty.MP_OPACITY);assert E.connect_material_property(emission,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
    else:
        assert E.connect_material_property(base,'RGB',u.MaterialProperty.MP_BASE_COLOR)
        normal=node('MaterialExpressionTextureSampleParameter2D',parameter_name='NormalTexture',texture=textures['Normal'],sampler_type=u.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        rm=node('MaterialExpressionTextureSampleParameter2D',parameter_name='MetallicRoughnessTexture',texture=textures['MetallicRoughness'],sampler_type=u.MaterialSamplerType.SAMPLERTYPE_MASKS)
        assert E.connect_material_property(normal,'RGB',u.MaterialProperty.MP_NORMAL)
        assert E.connect_material_property(rm,'G',u.MaterialProperty.MP_ROUGHNESS);assert E.connect_material_property(rm,'B',u.MaterialProperty.MP_METALLIC)
    E.layout_material_expressions(material);E.recompile_material(material);save(material)
    instance=AT.create_asset('MI_'+row['name'],folder,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew());E.set_material_instance_parent(instance,material);save(instance)
    mesh.set_material(0,instance);save(mesh);bounds=mesh.get_bounds()
    receipt.append({'name':row['name'],'mesh':mesh.get_path_name(),'material':instance.get_path_name(),'textures':{k:v.get_path_name() for k,v in textures.items()},'bounds_cm':{'origin':list(bounds.origin.to_tuple()),'extent':list(bounds.box_extent.to_tuple())},'triangles_source':row['triangles']})
(D/'Imported.json').write_text(json.dumps(receipt,indent=2))
