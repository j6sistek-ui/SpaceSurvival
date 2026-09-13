"""Author the original, direction-stable cinematic space material without changing gameplay."""
from pathlib import Path
import hashlib
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
PATH = '/Game/SpaceSurvival/Materials/M_Space'

def author():
    shader = (ROOT / 'ContentSource/Shaders/SpaceBackdrop.hlsl').read_text(encoding='utf-8-sig')
    digest = hashlib.sha256(shader.encode('utf-8')).hexdigest()
    library = u.EditorAssetLibrary
    material = library.load_asset(PATH)
    if not material:
        raise RuntimeError('Base palette must be authored first')
    if library.get_metadata_tag(material, 'SSSpaceShaderHash') == digest:
        return
    edit = u.MaterialEditingLibrary
    edit.delete_all_material_expressions(material)
    material.set_editor_property('shading_model', u.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property('two_sided', True)
    direction = edit.create_material_expression(material, u.MaterialExpressionCameraVectorWS, -650, 0)
    tint = edit.create_material_expression(material, u.MaterialExpressionVectorParameter, -650, 200)
    tint.set_editor_property('parameter_name', 'Tint')
    tint.set_editor_property('default_value', u.LinearColor(.6, .7, 1, 1))
    custom = edit.create_material_expression(material, u.MaterialExpressionCustom, -250, 0)
    custom.set_editor_property('description', 'Four octave direction-space dust and gas')
    custom.set_editor_property('code', shader)
    custom.set_editor_property('output_type', u.CustomMaterialOutputType.CMOT_FLOAT3)
    inputs = []
    for name in ('Direction', 'Tint'):
        item = u.CustomInput()
        item.set_editor_property('input_name', name)
        inputs.append(item)
    custom.set_editor_property('inputs', inputs)
    if not edit.connect_material_expressions(direction, '', custom, 'Direction'):
        raise RuntimeError('Direction input did not connect')
    if not edit.connect_material_expressions(tint, '', custom, 'Tint'):
        raise RuntimeError('Region tint input did not connect')
    edit.connect_material_property(custom, '', u.MaterialProperty.MP_EMISSIVE_COLOR)
    edit.recompile_material(material)
    library.set_metadata_tag(material, 'SSSpaceShaderHash', digest)
    if not library.save_loaded_asset(material, only_if_is_dirty=False):
        raise RuntimeError('Could not save authored space material')
    u.log('SS_SPACE_MATERIAL authored shader ' + digest)

if __name__ == '__main__':
    author()
