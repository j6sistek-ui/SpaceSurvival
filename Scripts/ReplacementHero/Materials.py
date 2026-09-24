import os
import unreal as u,json
from pathlib import Path
BASE='/Game/SpaceSurvival/Licensed/HeroReplacement/Final';SRC=Path(os.environ['SS_HERO_SOURCE']);L=u.EditorAssetLibrary;E=u.MaterialEditingLibrary;T=u.AssetToolsHelpers.get_asset_tools()
def tex(name,file):
 if not L.does_asset_exist(BASE+'/'+name):
  t=u.AssetImportTask();t.filename=str(SRC/file);t.destination_path=BASE;t.destination_name=name;t.automated=True;t.save=True;t.replace_existing=False;T.import_asset_tasks([t])
 return u.load_asset(BASE+'/'+name)
color=tex('T_TailSoftCore','Tail_SoftCore_Color.png');fur=tex('T_TailFibers','Tail_FineFibers_RGBA.png')
body=u.load_asset('/Game/TripoModels/sci-fi_squirrel_3d_model/sci-fi_squirrel_3d_model_Mat')
soft=u.load_asset(BASE+'/MI_TailSoftCore') or T.create_asset('MI_TailSoftCore',BASE,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew());E.set_material_instance_parent(soft,body);E.set_material_instance_texture_parameter_value(soft,'BaseColorTex',color);L.save_loaded_asset(soft)
m=u.load_asset(BASE+'/M_TailFur') or T.create_asset('M_TailFur',BASE,u.Material,u.MaterialFactoryNew());E.delete_all_material_expressions(m);m.set_editor_property('two_sided',True);m.set_editor_property('blend_mode',u.BlendMode.BLEND_MASKED);m.set_editor_property('opacity_mask_clip_value',.3)
f=E.create_material_expression(m,u.MaterialExpressionTextureSample);f.texture=fur;E.connect_material_property(f,'RGB',u.MaterialProperty.MP_BASE_COLOR);E.connect_material_property(f,'A',u.MaterialProperty.MP_OPACITY_MASK)
v=E.create_material_expression(m,u.MaterialExpressionConstant);v.r=.9;E.connect_material_property(v,'',u.MaterialProperty.MP_ROUGHNESS);E.set_base_material_usage(m,u.MaterialUsage.MATUSAGE_SKELETAL_MESH,True);E.recompile_material(m);L.save_loaded_asset(m,False)
mesh=u.load_asset(BASE+'/SK_SquirrelHeroReplacement');materials=mesh.materials
for i,slot in enumerate(materials):slot.material_interface=[body,soft,m][i];materials[i]=slot
mesh.set_editor_property('materials',materials);L.save_loaded_asset(mesh,False)
print('MATERIALS_READY',[s.material_interface.get_path_name() for s in mesh.materials])


