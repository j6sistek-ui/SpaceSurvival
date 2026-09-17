"""Plated hull materials for the pit stop exterior, authored in the editor and applied by the importer.

The composition comes in with flat colours, and a 180 m hull with one flat colour reads as clay. The kitbash
has no usable UVs at this scale, so the plating is computed from the mesh's own local position: two grids of
plates (9 m and 2.25 m), a groove between them, and a little value and roughness change per plate. It is
local space on purpose: the station actor is rotated per run, and world-aligned plating would run diagonally
across it. No textures, so nothing to license and nothing to stream.

ImportStationPitStop.py calls apply(mesh) after every import, because the import clears its folder. Light
materials (the lane, frame, strips, windows) are left as imported: they only carry emission.
"""
import unreal as u

EDIT = u.MaterialEditingLibrary
LIB = u.EditorAssetLibrary
FOLDER = '/Game/SpaceSurvival/Licensed/StationPitStop/Materials'
MASTER = 'M_StationPitStopHull'
VERSION = '2'
# slot material name fragment -> (instance name, base colour, metallic)
FINISHES = {
    # Dark on purpose: the level's key light is warm and strong, and a mid grey came out as sandstone.
    'PitStop_Hull': ('MI_StationPitStop_Hull', (0.075, 0.088, 0.110), 0.55),
    'PitStop_Panel': ('MI_StationPitStop_Panel', (0.038, 0.048, 0.068), 0.45),
    'PitStop_Accent': ('MI_StationPitStop_Accent', (0.40, 0.19, 0.04), 0.30),
}
# P and N are local-space position (cm) and normal. Returns (value factor, groove mask, roughness, unused).
SHADER = """
float3 a = abs(N);
float2 uv = (a.x > a.y && a.x > a.z) ? P.yz : ((a.y > a.z) ? P.xz : P.xy);
const float Big = 900.0, Small = 225.0, GrooveBig = 16.0, GrooveSmall = 5.0;
float2 g1 = abs(frac(uv / Big) - 0.5) * 2.0;
float2 g2 = abs(frac(uv / Small) - 0.5) * 2.0;
float w1 = 2.0 * GrooveBig / Big, w2 = 2.0 * GrooveSmall / Small;
float e1 = max(smoothstep(1.0 - w1, 1.0, g1.x), smoothstep(1.0 - w1, 1.0, g1.y));
float e2 = max(smoothstep(1.0 - w2, 1.0, g2.x), smoothstep(1.0 - w2, 1.0, g2.y));
float groove = saturate(max(e1, e2 * 0.55));
float h1 = frac(sin(dot(floor(uv / Big), float2(12.9898, 78.233))) * 43758.5453);
float h2 = frac(sin(dot(floor(uv / Small), float2(39.3468, 11.1351))) * 24634.6345);
float value = lerp(0.72 + 0.40 * h1, 1.0, 0.35) * (0.90 + 0.20 * h2);
float rough = lerp(0.42 + 0.28 * h2, 0.9, groove);
return float4(lerp(value, 0.10, groove), groove, rough, 0.0);
"""


def _node(material, cls, x, y):
    return EDIT.create_material_expression(material, cls, x, y)


def _mask(material, source, channel, x, y):
    mask = _node(material, u.MaterialExpressionComponentMask, x, y)
    for name in ('r', 'g', 'b', 'a'):
        mask.set_editor_property(name, name == channel)
    assert EDIT.connect_material_expressions(source, '', mask, '')
    return mask


def master():
    path = f'{FOLDER}/{MASTER}'
    material = LIB.load_asset(path) if LIB.does_asset_exist(path) else None
    if material and LIB.get_metadata_tag(material, 'SSPitStopHullVersion') == VERSION:
        return material
    if material:
        assert LIB.delete_asset(path), 'could not replace the hull material'
    material = u.AssetToolsHelpers.get_asset_tools().create_asset(MASTER, FOLDER, u.Material, u.MaterialFactoryNew())
    assert material
    material.set_editor_property('blend_mode', u.BlendMode.BLEND_OPAQUE)
    material.set_editor_property('shading_model', u.MaterialShadingModel.MSM_DEFAULT_LIT)
    material.set_editor_property('used_with_nanite', True)
    world = _node(material, u.MaterialExpressionWorldPosition, -1100, 0)
    local = _node(material, u.MaterialExpressionTransformPosition, -900, 0)
    local.set_editor_property('transform_source_type', u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_WORLD)
    local.set_editor_property('transform_type', u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_LOCAL)
    # UE 5.8: TransformPosition's first pin is unnamed; an empty target name is the first input.
    assert EDIT.connect_material_expressions(world, '', local, '')
    normal_ws = _node(material, u.MaterialExpressionVertexNormalWS, -1100, 200)
    normal = _node(material, u.MaterialExpressionTransform, -900, 200)
    normal.set_editor_property('transform_source_type', u.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_WORLD)
    normal.set_editor_property('transform_type', u.MaterialVectorCoordTransform.TRANSFORM_LOCAL)
    assert EDIT.connect_material_expressions(normal_ws, '', normal, '')
    custom = _node(material, u.MaterialExpressionCustom, -650, 80)
    custom.set_editor_property('code', SHADER)
    custom.set_editor_property('description', 'Pit stop hull plating from local position; no UVs, no textures')
    custom.set_editor_property('output_type', u.CustomMaterialOutputType.CMOT_FLOAT4)
    pins = []
    for name in ('P', 'N'):
        pin = u.CustomInput()
        pin.set_editor_property('input_name', name)
        pins.append(pin)
    custom.set_editor_property('inputs', pins)
    assert EDIT.connect_material_expressions(local, '', custom, 'P')
    assert EDIT.connect_material_expressions(normal, '', custom, 'N')
    colour = _node(material, u.MaterialExpressionVectorParameter, -650, -200)
    colour.set_editor_property('parameter_name', 'Color')
    colour.set_editor_property('default_value', u.LinearColor(0.23, 0.25, 0.28, 1))
    value = _mask(material, custom, 'r', -400, 0)
    tinted = _node(material, u.MaterialExpressionMultiply, -200, -100)
    assert EDIT.connect_material_expressions(colour, '', tinted, 'A')
    assert EDIT.connect_material_expressions(value, '', tinted, 'B')
    assert EDIT.connect_material_property(tinted, '', u.MaterialProperty.MP_BASE_COLOR)
    rough = _mask(material, custom, 'b', -400, 200)
    assert EDIT.connect_material_property(rough, '', u.MaterialProperty.MP_ROUGHNESS)
    metallic = _node(material, u.MaterialExpressionScalarParameter, -400, 400)
    metallic.set_editor_property('parameter_name', 'Metallic')
    metallic.set_editor_property('default_value', 0.35)
    assert EDIT.connect_material_property(metallic, '', u.MaterialProperty.MP_METALLIC)
    EDIT.recompile_material(material)
    LIB.set_metadata_tag(material, 'SSPitStopHullVersion', VERSION)
    assert LIB.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def instance(parent, name, colour, metallic):
    path = f'{FOLDER}/{name}'
    if LIB.does_asset_exist(path):
        assert LIB.delete_asset(path)
    mi = u.AssetToolsHelpers.get_asset_tools().create_asset(name, FOLDER, u.MaterialInstanceConstant,
                                                            u.MaterialInstanceConstantFactoryNew())
    assert mi
    EDIT.set_material_instance_parent(mi, parent)
    EDIT.set_material_instance_vector_parameter_value(mi, 'Color', u.LinearColor(*colour, 1))
    EDIT.set_material_instance_scalar_parameter_value(mi, 'Metallic', metallic)
    EDIT.update_material_instance(mi)
    assert LIB.save_loaded_asset(mi, only_if_is_dirty=False)
    return mi


def apply(mesh):
    """Swap the imported flat hull materials for the plated instances, slot by slot; returns {slot: material}."""
    parent = master()
    finishes = {key: instance(parent, *row) for key, row in FINISHES.items()}
    assigned = {}
    for index, slot in enumerate(mesh.static_materials):
        current = slot.material_interface.get_name() if slot.material_interface else ''
        label = f'{slot.material_slot_name} {current}'
        for key, material in finishes.items():
            if key in label:
                mesh.set_material(index, material)
                assigned[str(slot.material_slot_name)] = material.get_path_name()
                break
    assert len(assigned) >= 2, f'expected the hull and panel slots, found {assigned}'
    return assigned
