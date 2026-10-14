"""Correct reviewed lounge graphics and fixture presentation without scene redesign.

The lead owns native execution, saving and matched captures. Private derivatives
preserve the native masks, animation and source assets. Only two agent-authored
headings may change transform; all other existing actors are protected.
"""
import hashlib
import math
from pathlib import Path

from OutpostGeometryUtils import mesh_union
from RefineStationSocialAtmosphereFollowup import MAP, MASTER, _one, _pose
from RefineStationSocialAtmosphere import FIXTURE, GRAPHITE
from AuthorStationPoolReturn import DARK, TRIM


MAP_SHA = '2e64c159a545d45f58386e6f9007c680a6877300952d1e55ba4eb993eeb8b711'
PRIVATE = '/Game/OutpostSandbox/StationRefinement/SocialVisualFinish'
PREFIX = 'Refine/SocialVisualFinish/'
COSMOS = '/Game/OutpostSandbox/StationRefinement/SocialAtmosphereFollowup/Materials/MI_Lounge_CosmoAdvertisment'
LAMP = '/Game/CyberpunkRestaurant/Materials/MI_Lamp_01'
GLASS = '/Game/CyberpunkRestaurant/Materials/MI_Light_Lamp_Glass'
TEXT = '/Game/OutpostSandbox/Materials/M_OutpostReadableTextOneSided'
HEADINGS = (('CosmoAdvertisment', 'Engineering/Bay W1/Glass'),
            ('DigitalPanel', 'Engineering/Bay S1/Glass'))


def _path(asset):
    return asset.get_path_name().split('.')[0] if asset else None


def _digest(root, path, suffix='.uasset'):
    if not path.startswith('/Game/'):
        raise RuntimeError('Expected a project source: ' + path)
    return hashlib.sha256((root / ('Content/' + path[6:] + suffix)).read_bytes()).hexdigest()


def _values(edit, material):
    return {
        'scalars': {str(n): float(edit.get_material_instance_scalar_parameter_value(material, n))
                    for n in edit.get_scalar_parameter_names(material)},
        'vectors': {str(n): tuple(edit.get_material_instance_vector_parameter_value(material, n).to_tuple())
                    for n in edit.get_vector_parameter_names(material)},
        'textures': {str(n): _path(edit.get_material_instance_texture_parameter_value(material, n))
                     for n in edit.get_texture_parameter_names(material)},
        'switches': {str(n): bool(edit.get_material_instance_static_switch_parameter_value(material, n))
                     for n in edit.get_static_switch_parameter_names(material)}}


def _duplicate(source, destination, u, dirty):
    if u.EditorAssetLibrary.does_asset_exist(destination):
        raise RuntimeError('Preserve existing visual finish: ' + destination)
    result = u.EditorAssetLibrary.duplicate_asset(source, destination)
    if not result:
        raise RuntimeError('Could not create private visual derivative: ' + destination)
    dirty.append(result.get_path_name())
    return result


def _inward_cosmos(ctx, u, dirty, guard):
    edit = u.MaterialEditingLibrary
    source = ctx.asset(COSMOS)
    if _path(source.get_editor_property('parent')) != MASTER:
        raise RuntimeError('Reviewed COSMOS parent changed')
    original = ctx.asset(MASTER)
    guard(COSMOS)
    guard(MASTER)
    values = _values(edit, source)
    for texture in values['textures'].values():
        if texture:
            guard(texture)
    # ServiceMaterialProbe records these three native emission-only UV chains.
    # Their scalar tiling affects both axes, so a MIC scalar cannot mirror U
    # alone. Insert (1-U,V) BEFORE native translation/rotation/tiling/scroll.
    chains = (('MaterialExpressionTextureCoordinate_3', 'MaterialExpressionMaterialFunctionCall_0',
               'MaterialExpressionConstant2Vector_0'),
              ('MaterialExpressionTextureCoordinate_9', 'MaterialExpressionMaterialFunctionCall_36',
               'MaterialExpressionConstant2Vector_5'),
              ('MaterialExpressionTextureCoordinate_10', 'MaterialExpressionMaterialFunctionCall_41',
               'MaterialExpressionConstant2Vector_6'))
    master = _duplicate(MASTER, PRIVATE + '/M_CosmosInwardUV', u, dirty)
    nodes = {n.get_name(): n for n in edit.get_material_expressions(master)}
    before = {name: tuple(n.get_name() if n else None for n in
                         edit.get_inputs_for_material_expression(master, node)) for name, node in nodes.items()}

    def node(kind, **properties):
        result = edit.create_material_expression(master, getattr(u, kind))
        if not result:
            raise RuntimeError('Cannot author private inward UV expression: ' + kind)
        for name, value in properties.items():
            result.set_editor_property(name, value)
        return result

    def link(a, b, pin):
        if not edit.connect_material_expressions(a, '', b, pin):
            raise RuntimeError('Cannot connect inward UV expression: ' + pin)

    multiplier = node('MaterialExpressionConstant2Vector', r=-1., g=1.)
    offset = node('MaterialExpressionConstant2Vector', r=1., g=0.)
    changed = {}
    for coordinate, function, center in chains:
        if (coordinate not in nodes or function not in nodes or center not in nodes or
                before[function] != (coordinate, center) or
                _path(nodes[function].get_editor_property('material_function')) !=
                '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Materials/Functions/MF_Translate2D'):
            raise RuntimeError('Inspected native emission UV route changed: ' + function)
        inputs = list(edit.get_material_expression_input_names(nodes[function]))
        if len(inputs) != 2 or not inputs[0]:
            raise RuntimeError('Native translation input interface changed')
        multiply, add = node('MaterialExpressionMultiply'), node('MaterialExpressionAdd')
        link(nodes[coordinate], multiply, 'A')
        link(multiplier, multiply, 'B')
        link(multiply, add, 'A')
        link(offset, add, 'B')
        link(add, nodes[function], inputs[0])
        changed[function] = (add.get_name(), center)
    for name, expected in before.items():
        actual = tuple(n.get_name() if n else None for n in
                       edit.get_inputs_for_material_expression(master, nodes[name]))
        if actual != changed.get(name, expected):
            raise RuntimeError('Unexpected original graph change: ' + name)
    errors = edit.recompile_material(master)
    if errors:
        raise RuntimeError('Private inward graphic compilation failed: ' + repr(list(errors)))
    child = _duplicate(COSMOS, PRIVATE + '/MI_CosmosInward', u, dirty)
    edit.set_material_instance_parent(child, master)
    edit.update_material_instance(child)
    if _values(edit, child) != values:
        raise RuntimeError('Inward graphic lost source masks, colors or animation parameters')
    return child, {'source': COSMOS, 'private_master': master.get_path_name(),
                   'private_instance': child.get_path_name(), 'uv_mapping': '(1-U, V)',
                   'changed_native_links': list(changed), 'other_native_graph_links_preserved': True,
                   'all_effective_instance_parameters_preserved': True}


def apply(ctx):
    """Return only new dirty assets; no map/asset save or native process entry."""
    import unreal as u
    root = Path(u.Paths.project_dir()).resolve()
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name().split('.')[0] != MAP or _digest(root, MAP, '.umap') != MAP_SHA:
        raise RuntimeError('Visual finish requires the exact saved StationPoolMatch1 owner preview')
    actors = list(ctx.eas.get_all_level_actors())
    if any(a.get_actor_label().startswith(PREFIX) for a in actors):
        raise RuntimeError('Visual finish already exists; preserve it')
    _one(actors, 'Refine/OrbitPool/Alternating match sequence')
    before = {a.get_path_name(): _pose(a) for a in actors}
    sources, dirty = {}, []

    def guard(path):
        if path not in sources:
            sources[path] = _digest(root, path)

    for path in (FIXTURE, LAMP, GLASS, TEXT, GRAPHITE, DARK, TRIM):
        ctx.asset(path)
        guard(path)
    report = {'module': 'social_visual_finish', 'dirty_assets': dirty,
              'map_before_sha256': MAP_SHA, 'headings': [], 'fixtures': [], 'return_materials': []}
    edit = u.MaterialEditingLibrary
    cosmos, report['cosmos'] = _inward_cosmos(ctx, u, dirty, guard)
    pane = _one(actors, 'Engineering/Bay W1/Glass').static_mesh_component
    if pane.get_num_materials() != 2 or any(_path(m) != COSMOS for m in pane.get_materials()):
        raise RuntimeError('Reviewed mirrored COSMOS pane has unexpected overrides')
    for slot in range(pane.get_num_materials()):
        pane.set_material(slot, cosmos)
        if pane.get_material(slot) != cosmos:
            raise RuntimeError('Inward COSMOS material assignment failed')

    # The follow-up headings inherited the default lit text material. Reuse the
    # established unlit font/alpha graph and orient only these two private labels.
    allowed_heading_moves = set()
    text_material = ctx.asset(TEXT)
    if (text_material.get_editor_property('shading_model') != u.MaterialShadingModel.MSM_UNLIT or
            text_material.get_editor_property('two_sided')):
        raise RuntimeError('Reviewed readable one-sided text material changed')
    for variant, label in HEADINGS:
        display = _one(actors, label)
        heading = _one(actors, 'Refine/SocialAtmosphereFollowup/Screen ' + variant + '/Heading')
        component = heading.get_component_by_class(u.TextRenderComponent)
        center, extent = mesh_union(display)
        normal = display.get_actor_forward_vector()
        toward_room = u.Vector(4200-center.x, -3400-center.y, 0)
        if normal.x*toward_room.x+normal.y*toward_room.y < 0:
            normal = normal * -1
        depth = abs(normal.x)*extent.x+abs(normal.y)*extent.y
        position = center+normal*(depth+2)+u.Vector(0, 0, extent.z*.73)
        heading.set_actor_location(position, False, False)
        heading.set_actor_rotation(u.Rotator(yaw=math.degrees(math.atan2(normal.y, normal.x))), False)
        component.set_text_material(text_material)
        component.set_text_render_color(u.Color(168, 219, 255, 255))
        component.set_world_size(18.)
        size = component.get_text_local_size()
        width = max(abs(size.x), abs(size.y))
        available = 1.72*(abs(normal.x)*extent.y+abs(normal.y)*extent.x)
        if width > available:
            component.set_world_size(18.*available/width)
        if component.get_editor_property('world_size') < 11.:
            raise RuntimeError('Lounge heading is too small for the measured pane')
        allowed_heading_moves.add(heading.get_path_name())
        report['headings'].append({'actor': heading.get_actor_label(), 'position': list(position.to_tuple()),
            'yaw': heading.get_actor_rotation().yaw, 'text_material': text_material.get_path_name(),
            'world_size': float(component.get_editor_property('world_size')), 'faces_room_interior': True})

    # Native SocialQualityProbe2 identifies the diffuser's actual texture mask;
    # its zero Emmisive Color disabled it. Preserve every other native parameter.
    lamp_source = ctx.asset(LAMP)
    lamp_values = _values(edit, lamp_source)
    if (lamp_values['vectors'].get('Emmisive Color') != (0., 0., 0., 1.) or
            lamp_values['textures'].get('Emmisive Map') != '/Game/CyberpunkRestaurant/Textures/T_Lamp_01_E'):
        raise RuntimeError('Inspected native lamp mask/interface changed')
    for path in lamp_values['textures'].values():
        if path:
            guard(path)
    lamp = _duplicate(LAMP, PRIVATE + '/MI_AisleLampLit', u, dirty)
    emission = (6., 4.9, 3.6, 1.)
    edit.set_material_instance_vector_parameter_value(lamp, 'Emmisive Color', u.LinearColor(*emission))
    edit.update_material_instance(lamp)
    after_lamp = _values(edit, lamp)
    actual_color = after_lamp['vectors'].pop('Emmisive Color')
    expected_lamp = {k: dict(v) for k, v in lamp_values.items()}
    expected_lamp['vectors'].pop('Emmisive Color')
    if after_lamp != expected_lamp or max(abs(a-b) for a, b in zip(actual_color, emission)) > .0001:
        raise RuntimeError('Private lamp changed more than the inspected diffuser emission')
    for index in (1, 2):
        housing = _one(actors, 'Refine/SocialAtmosphereFollowup/Aisle %d/Housing' % index)
        component = housing.static_mesh_component
        if _path(component.static_mesh) != FIXTURE or [_path(m) for m in component.get_materials()] != [LAMP, GLASS]:
            raise RuntimeError('Reviewed central housing/native material slots changed')
        component.set_material(0, lamp)
        if component.get_material(0) != lamp or _path(component.get_material(1)) != GLASS:
            raise RuntimeError('Actual lamp diffuser assignment failed')
        center, extent = mesh_union(housing)
        position = u.Vector(center.x, center.y, center.z+extent.z+1)
        light = ctx.eas.spawn_actor_from_class(u.RectLight, position, u.Rotator(pitch=90))
        ctx.register(light, 'SocialVisualFinish/Aisle %d/Ceiling bounce' % index)
        c = light.get_component_by_class(u.RectLightComponent)
        c.set_mobility(u.ComponentMobility.MOVABLE)
        c.set_intensity_units(u.LightUnits.LUMENS)
        c.set_intensity(110.)
        c.set_attenuation_radius(440.)
        c.set_source_width(120.)
        c.set_source_height(20.)
        c.set_light_color(u.LinearColor(1., 1., 1., 1.))
        c.set_editor_property('use_temperature', True)
        c.set_editor_property('temperature', 4000.)
        c.set_editor_property('specular_scale', .05)
        c.set_editor_property('volumetric_scattering_intensity', 0.)
        c.set_cast_shadows(False)
        if not light.attach_to_component(component, u.Name(''), u.AttachmentRule.KEEP_WORLD,
                u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, False):
            raise RuntimeError('Ceiling bounce could not attach to its actual housing')
        if abs(float(c.intensity)-110.) > .001 or abs(float(c.attenuation_radius)-440.) > .001:
            raise RuntimeError('Ceiling bounce light readback differs')
        report['fixtures'].append({'housing': housing.get_actor_label(), 'emissive_mask': lamp_values['textures']['Emmisive Map'],
            'emissive_color': emission, 'material': lamp.get_path_name(), 'ceiling_bounce_lumens': 110.,
            'ceiling_bounce_radius_cm': 440., 'position': list(position.to_tuple()), 'source_cm': [120., 20.]})

    returns = [a for a in actors if a.get_actor_label().startswith('Refine/OrbitPool/Return/')]
    if len(returns) != 32:
        raise RuntimeError('Expected all 32 reviewed return parts, got ' + str(len(returns)))
    graphite = ctx.asset(GRAPHITE)
    for actor in returns:
        component = actor.get_component_by_class(u.StaticMeshComponent)
        if not component or _path(component.static_mesh) != '/Engine/BasicShapes/Cube':
            raise RuntimeError('Reviewed pool return geometry changed')
        old = [_path(m) for m in component.get_materials()]
        if not old or any(m not in (DARK, TRIM) for m in old):
            raise RuntimeError('Pool return part has an unreviewed material override')
        for slot in range(component.get_num_materials()):
            component.set_material(slot, graphite)
            if component.get_material(slot) != graphite:
                raise RuntimeError('Pool return graphite assignment failed')
        report['return_materials'].append({'actor': actor.get_actor_label(), 'before': old, 'after': GRAPHITE})

    current = {a.get_path_name(): a for a in ctx.eas.get_all_level_actors()}
    changes = [path for path, pose in before.items() if path not in current or _pose(current[path]) != pose]
    if set(changes)-allowed_heading_moves:
        raise RuntimeError('Visual finish moved an unrelated actor: ' + str(changes))
    if any(_digest(root, path) != digest for path, digest in sources.items()) or _digest(root, MAP, '.umap') != MAP_SHA:
        raise RuntimeError('Visual finish changed a source or saved the map')
    report.update(source_sha256_preserved=sources, changed_actor_transforms=changes,
        protected_actor_count=len(before)-len(allowed_heading_moves), protected_transforms_preserved=True,
        previous_lamp_keys_exposure_architecture_sequences_unchanged=True,
        limits='Private authoring only; native shader compilation/readbacks and fresh matched room renders required.')
    return report
