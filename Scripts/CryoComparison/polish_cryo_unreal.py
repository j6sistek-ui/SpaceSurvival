"""Owned-stage display sharpness and contained cold-vapor refinement."""
from pathlib import Path
import unreal as u
import json,traceback
WORK=Path(__file__).resolve().parent
BASE='/Game/SpaceSurvival/CryoComparison'
r={'status':'FAILED','textures':[],'effects':[]}
try:
    assert Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==(WORK/'CryoStage').resolve()
    world=u.EditorLoadingAndSavingUtils.load_map(BASE+'/Maps/L_CryoComparison')
    assert world
    label_mat=u.EditorAssetLibrary.load_asset(BASE+'/Materials/M_ReviewLabel') if u.EditorAssetLibrary.does_asset_exist(BASE+'/Materials/M_ReviewLabel') else u.EditorAssetLibrary.duplicate_asset('/Engine/EngineMaterials/DefaultTextMaterialOpaque',BASE+'/Materials/M_ReviewLabel')
    edit=u.MaterialEditingLibrary
    base=edit.get_material_property_input_node(label_mat,u.MaterialProperty.MP_BASE_COLOR)
    base_output=edit.get_material_property_input_node_output_name(label_mat,u.MaterialProperty.MP_BASE_COLOR)
    assert base
    label_mat.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
    assert edit.connect_material_property(base,base_output,u.MaterialProperty.MP_EMISSIVE_COLOR)
    assert not edit.recompile_material(label_mat)
    assert u.EditorAssetLibrary.save_loaded_asset(label_mat,False)
    for name in ('Status','Console','Holo'):
        tex=u.EditorAssetLibrary.load_asset(BASE+'/Textures/T_Cryo_'+name)
        tex.set_editor_property('mip_gen_settings',u.TextureMipGenSettings.TMGS_SHARPEN4)
        assert u.EditorAssetLibrary.save_loaded_asset(tex,False)
        r['textures'].append({'name':name,'build_size':[tex.blueprint_get_size_x(),tex.blueprint_get_size_y()],
            'power_of_two_mode':str(tex.get_editor_property('power_of_two_mode'))})
    for actor in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        if isinstance(actor,u.NiagaraActor):
            comp=actor.get_component_by_class(u.NiagaraComponent)
            comp.set_variable_linear_color('Smoke Color',u.LinearColor(.6,.8,1,.45))
            p=actor.get_actor_location()
            actor.set_actor_location(u.Vector(p.x,30,p.z),False,False)
            r['effects'].append(actor.get_actor_label())
        elif isinstance(actor,u.TextRenderActor):
            comp=actor.get_component_by_class(u.TextRenderComponent)
            comp.set_text_material(label_mat)
    assert len(r['effects'])==4
    assert u.EditorLoadingAndSavingUtils.save_map(world,BASE+'/Maps/L_CryoComparison')
    r['status']='POLISH_SAVED_PENDING_FINAL_CAPTURE'
except Exception:
    r['error']=traceback.format_exc()
    u.log_error(r['error'])
finally:
    (WORK/'CryoNativePolish.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
    u.SystemLibrary.quit_editor()
