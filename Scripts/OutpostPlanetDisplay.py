"""Local self-lit archive display using the owned planet texture library.

The purchased planetary material relies on global SkyAtmosphere lighting. A
small interior exhibit must remain readable without installing that environment.
Only a private material is authored; the original mesh and textures are reused.
"""
import unreal as u


def build(api):
    edit, tools, lib, load = (api[k] for k in ('EDIT', 'TOOLS', 'LIB', 'load'))
    name = 'M_ArchivePlanetDisplay'
    path = '/Game/OutpostSandbox/Materials/' + name
    mat = load(path) if lib.does_asset_exist(path) else tools.create_asset(
        name, '/Game/OutpostSandbox/Materials', u.Material, u.MaterialFactoryNew())
    edit.delete_all_material_expressions(mat)
    mat.set_editor_property('shading_model', u.MaterialShadingModel.MSM_UNLIT)

    def node(kind, **props):
        result = edit.create_material_expression(mat, getattr(u, 'MaterialExpression' + kind))
        for key, value in props.items():
            result.set_editor_property(key, value)
        return result

    def link(source, target, pin, output=''):
        assert edit.connect_material_expressions(source, output, target, pin)

    uv = node('TextureCoordinate')
    pan = node('Panner', speed_x=.0015, speed_y=0.)
    link(uv, pan, 'Coordinate')
    earth = node('TextureSample', texture=load(
        '/Game/Planet_Project/Assets/Textures/Earth/T_8k_earth_daymap'))
    clouds = node('TextureSample', texture=load(
        '/Game/Planet_Project/Assets/Textures/Earth/T_8k_earth_clouds'))
    link(pan, earth, 'UVs')
    cloud_pan = node('Panner', speed_x=.0019, speed_y=0.)
    link(uv, cloud_pan, 'Coordinate')
    link(cloud_pan, clouds, 'UVs')
    cloud_mask = node('Multiply', const_b=.48)
    link(clouds, cloud_mask, 'A', 'R')
    blend = node('LinearInterpolate', const_b=1.)
    link(earth, blend, 'A', 'RGB')
    link(cloud_mask, blend, 'Alpha')

    # Gentle local shading gives depth without a completely black hemisphere.
    normal = node('VertexNormalWS')
    direction = node('Constant3Vector', constant=u.LinearColor(-.48, -.64, .60, 1.))
    dot = node('DotProduct')
    link(normal, dot, 'A')
    link(direction, dot, 'B')
    shade_scale = node('Multiply', const_b=.20)
    link(dot, shade_scale, 'A')
    shade = node('Add', const_b=.80)
    link(shade_scale, shade, 'A')
    shaded = node('Multiply')
    link(blend, shaded, 'A')
    link(shade, shaded, 'B')
    gain = node('Multiply', const_b=7.)
    link(shaded, gain, 'A')
    rim = node('Fresnel', exponent=4., base_reflect_fraction=.0)
    blue = node('Constant3Vector', constant=u.LinearColor(.04, .45, 1.3, 1.))
    rim_color = node('Multiply')
    link(rim, rim_color, 'A')
    link(blue, rim_color, 'B')
    emission = node('Add')
    link(gain, emission, 'A')
    link(rim_color, emission, 'B')
    assert edit.connect_material_property(emission, '', u.MaterialProperty.MP_EMISSIVE_COLOR)
    edit.recompile_material(mat)
    assert lib.save_loaded_asset(mat)
    return mat
