"""Private blue-white ribbon derivative; retains Epic's spawn, lifetime and alpha behavior."""
import unreal as u
from pathlib import Path
import json
BASE='/Game/SpaceSurvival/Licensed/Atmosphere'

def main():
    lib=u.EditorAssetLibrary;edit=u.MaterialEditingLibrary
    lib.make_directory(BASE)
    Path(u.Paths.project_dir(),'Artifacts/EnvironmentRefresh').mkdir(parents=True,exist_ok=True)
    target=BASE+'/NS_DeepSpaceExhaust'
    system=lib.load_asset(target) if lib.does_asset_exist(target) else lib.duplicate_asset('/Game/NiagaraExamples/FX_Weapons/Trails/NS_SimpleRibbonTrail',target)
    assert system
    renderers=[]
    for obj in u.ObjectIterator(u.Object):
        # Native iterator also exposes class wrappers with static Python methods.
        try:
            if obj.get_path_name().startswith(system.get_path_name()+':') and obj.get_class().get_name()=='NiagaraRibbonRendererProperties':
                renderers.append(obj)
        except TypeError:
            continue
    assert renderers,'No exclusively owned ribbon renderers found; do not modify shared emitter assets'
    target_mat=BASE+'/M_DeepSpaceExhaust'
    source=renderers[0].get_editor_property('Material')
    material=lib.load_asset(target_mat) if lib.does_asset_exist(target_mat) else lib.duplicate_asset(source.get_path_name(),target_mat)
    assert material
    if lib.get_metadata_tag(material,'SSExhaustVersion')!='1':
        previous=edit.get_material_property_input_node(material,u.MaterialProperty.MP_EMISSIVE_COLOR)
        assert previous
        desat=edit.create_material_expression(material,u.MaterialExpressionDesaturation,1200,0)
        color=edit.create_material_expression(material,u.MaterialExpressionVectorParameter,1200,240)
        color.set_editor_property('parameter_name','ExhaustColor')
        color.set_editor_property('default_value',u.LinearColor(.16,1.4,3.2,1))
        mult=edit.create_material_expression(material,u.MaterialExpressionMultiply,1500,0)
        assert edit.connect_material_expressions(previous,'',desat,edit.get_material_expression_input_names(desat)[0])
        assert edit.connect_material_expressions(desat,'',mult,'A')
        assert edit.connect_material_expressions(color,'',mult,'B')
        assert edit.connect_material_property(mult,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
        lib.set_metadata_tag(material,'SSExhaustVersion','1')
        edit.recompile_material(material)
    for renderer in renderers:
        renderer.set_editor_property('Material',material)
    for asset in [material,system]:assert lib.save_loaded_asset(asset,only_if_is_dirty=False)
    Path(u.Paths.project_dir(),'Artifacts/EnvironmentRefresh/ExhaustAuthor.json').write_text(json.dumps({'system':system.get_path_name(),'material':material.get_path_name(),'renderers':[r.get_path_name() for r in renderers],'spawn_lifetime_alpha':'unchanged','requires':'integrated rendered review'},indent=2))
    u.log('DEEP_SPACE_EXHAUST_AUTHORED')
if __name__=='__main__':main()
