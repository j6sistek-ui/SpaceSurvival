"""Private archive hologram: translucent body, curved rim and moving scanlines.

Only the three static archive figures use this material. It has no vertex
displacement, scene-depth override, textures or dependency on world lighting.
The caller owns component assignment and saving the sandbox level.
"""

TARGET = '/Game/OutpostSandbox/L_AsteroidOutpost'
MATERIAL = '/Game/OutpostSandbox/Materials/M_OutpostArchiveHologram'
REVISION = 'archive-rim-height-scan-v2'
METADATA_KEY = 'OutpostArchiveHologramRecipe'
PARAMETERS = {
    'BodyOpacity': .12,
    'RimOpacity': .50,
    'ScanOpacity': .18,
    'BodyEmission': 1.5,
    'RimEmission': 12.,
    'ScanEmission': 3.,
    'RimExponent': 2.4,
    'ScanCyclesPerCm': .10,
    'ScanCyclesPerSecond': .35,
    'ScanSharpness': 18.,
}
COLOR = (1., .27, .035)


def ensure(api):
    """Return (material, recipe receipt), rebuilding this private graph once."""
    import unreal as u
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    package = world.get_path_name().split('.')[0]
    fresh = package.startswith('/Temp/Untitled') and api.get('TARGET') == TARGET
    if package != TARGET and not fresh:
        raise RuntimeError('Archive hologram is restricted to the private outpost')
    lib, edit = u.EditorAssetLibrary, u.MaterialEditingLibrary
    material = lib.load_asset(MATERIAL) if lib.does_asset_exist(MATERIAL) else None
    if material and not isinstance(material, u.Material):
        raise RuntimeError('Archive material path is occupied by another asset type')
    rebuilt = not material or lib.get_metadata_tag(material, METADATA_KEY) != REVISION
    if rebuilt:
        if not material:
            folder, name = MATERIAL.rsplit('/', 1)
            lib.make_directory(folder)
            material = u.AssetToolsHelpers.get_asset_tools().create_asset(
                name, folder, u.Material, u.MaterialFactoryNew())
        if not material:
            raise RuntimeError('Could not create the private archive material')
        edit.delete_all_material_expressions(material)
        material.set_editor_property('blend_mode', u.BlendMode.BLEND_TRANSLUCENT)
        material.set_editor_property('shading_model', u.MaterialShadingModel.MSM_UNLIT)
        # Front surfaces convey the silhouette without accumulating a second
        # bright back-facing shell through the low-opacity body.
        material.set_editor_property('two_sided', False)
        edit.set_base_material_usage(material, u.MaterialUsage.MATUSAGE_SKELETAL_MESH, True)
        created = []

        def node(kind, **properties):
            expression = edit.create_material_expression(material, getattr(u, kind))
            if expression is None:
                raise RuntimeError('Could not create hologram node: ' + kind)
            for key, value in properties.items():
                expression.set_editor_property(key, value)
            created.append(expression)
            return expression

        def link(source, dest, pin, output=''):
            if not edit.connect_material_expressions(source, output, dest, pin):
                raise RuntimeError('Hologram graph connection failed: ' + pin)

        parameters = {name: node('MaterialExpressionScalarParameter',
            parameter_name=name, default_value=value) for name, value in PARAMETERS.items()}

        def multiply(a, b):
            expression = node('MaterialExpressionMultiply')
            link(a, expression, 'A')
            link(b, expression, 'B')
            return expression

        def add(a, b):
            expression = node('MaterialExpressionAdd')
            link(a, expression, 'A')
            link(b, expression, 'B')
            return expression

        fresnel = node('MaterialExpressionFresnel', base_reflect_fraction=0.)
        link(parameters['RimExponent'], fresnel, 'ExponentIn')

        position = node('MaterialExpressionWorldPosition')
        height = node('MaterialExpressionComponentMask', r=False, g=False, b=True, a=False)
        link(position, height, '')
        time = node('MaterialExpressionTime')
        phase = add(multiply(height, parameters['ScanCyclesPerCm']),
                    multiply(time, parameters['ScanCyclesPerSecond']))
        sine = node('MaterialExpressionSine', period=1.)
        link(phase, sine, '')
        half = node('MaterialExpressionMultiply', const_b=.5)
        link(sine, half, 'A')
        positive = node('MaterialExpressionAdd', const_b=.5)
        link(half, positive, 'A')
        stripe = node('MaterialExpressionPower')
        link(positive, stripe, 'Base')
        link(parameters['ScanSharpness'], stripe, 'Exp')

        # Both contributions preserve normal-dependent form. Thin stripes
        # cross the model in world height, rather than moving its geometry.
        opacity = add(parameters['BodyOpacity'], add(
            multiply(fresnel, parameters['RimOpacity']),
            multiply(stripe, parameters['ScanOpacity'])))
        gain = add(parameters['BodyEmission'], add(
            multiply(fresnel, parameters['RimEmission']),
            multiply(stripe, parameters['ScanEmission'])))
        tint = node('MaterialExpressionVectorParameter', parameter_name='HologramAmber',
                    default_value=u.LinearColor(*COLOR, 1.))
        emission = node('MaterialExpressionMultiply')
        link(tint, emission, 'A', 'RGB')
        link(gain, emission, 'B')
        if not edit.connect_material_property(opacity, '', u.MaterialProperty.MP_OPACITY):
            raise RuntimeError('Hologram opacity output could not be connected')
        if not edit.connect_material_property(emission, '', u.MaterialProperty.MP_EMISSIVE_COLOR):
            raise RuntimeError('Hologram emission output could not be connected')
        edit.layout_material_expressions(material)
        edit.recompile_material(material)
        lib.set_metadata_tag(material, METADATA_KEY, REVISION)
        if not lib.save_loaded_asset(material, False):
            raise RuntimeError('Private archive material could not be saved')

    return material, {
        'path': MATERIAL, 'revision': REVISION, 'graph_rebuilt': rebuilt,
        'parameters': dict(PARAMETERS), 'color': list(COLOR),
        'opacity_range': [.12, .80], 'emission_gain_range': [1.5, 16.5],
        'scan_pitch_cm': 10., 'scan_speed_cm_per_second': 3.5,
        'fresnel_base_reflect_fraction': 0., 'two_sided': False,
        'world_position_offset': False, 'interactive_wardrobe_unchanged': True,
        'visual_validation': 'Pending native same-view capture',
    }
