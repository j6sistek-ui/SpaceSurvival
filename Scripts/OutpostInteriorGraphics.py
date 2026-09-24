"""Assign owned readable graphics to ten exact existing interior glass panes.

Seven diagnostic/data panes retain their native frame geometry. Three wardrobe
BACK panes become clear glass; their west fronts are already open. Six capsule
side panes, native P3 computer screens and all market content remain untouched.
Only private instance parameters and these component material slots may change.
"""
import hashlib
import json
import math
from pathlib import Path

TARGET = '/Game/OutpostSandbox/L_AsteroidOutpost'
PACK = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/'
PRIVATE = '/Game/OutpostSandbox/Materials/'
MASTER = PACK + 'Materials/Masters/MM_MasterMaterial02_Translucent.MM_MasterMaterial02_Translucent'


def _asset(folder, name):
    return PACK + folder + '/' + name + '.' + name


def layout():
    rows = []

    def add(name, dimensions, variant, originals, purpose):
        source_name = 'MI_Glass01_Clean' if variant == 'Clear' else 'MI_DigitalGlass_Window400X200_' + variant
        rows.append({'actor': name,
            'mesh': _asset('Meshes', 'SM_Window' + dimensions + '_V2_Part2_DigitalWindow'),
            'source_material': _asset('Materials/Instances/Translucent', source_name),
            'private_material': PRIVATE + 'MI_InteriorGraphic_' + variant,
            'variant': variant, 'purpose': purpose,
            'allowed_original_materials': [_asset('Materials/Instances/Translucent', n) for n in originals],
            'required_slots': 2})

    for i, variant in enumerate(('Graph1', 'DigitalPanel', 'Graph2'), 1):
        add('Operations/HoloArchive' + str(i) + '/AnimatedGlass', '400X200', variant,
            ['MI_DigitalGlass_Window400X200'], 'Decorative operations archive data')
    for i, variant in enumerate(('Graph1', 'Graph2'), 1):
        add('Operations/SuspendedTelemetry' + str(i) + '/AnimatedGlass', '300X100', variant,
            ['MI_DigitalGlass_Window300X100'], 'Decorative overhead telemetry graphic')
    for i in (1, 2):
        add('Engineering/Diagnostic backing/Diagnostic ' + str(i) + '/Native digital glass',
            '400X200', 'Graph' + str(i),
            ['MI_DigitalGlass_Window400X200_Graph' + str(i)],
            'Retain existing authored diagnostic graphic with common channel gain')
    for i in (1, 2, 3):
        add('LoungeNative/Hologram bay ' + str(i) + '/Back/Animated glass', '200X250', 'Clear',
            ['MI_DigitalGlass_Window200X250'], 'Clear backdrop behind archive character; not a front door')
    return rows


def channel_recipe(values, clear=False):
    """One source-relative gain preserves image/scan/animation channel ratios."""
    if not values or any(not math.isfinite(v) for v in values.values()):
        raise ValueError('Missing or nonfinite native emissive channels')
    peak = max(abs(v) for v in values.values())
    gain = 0. if clear else min(1., 40./peak) if peak else 1.
    return gain, {k: v*gain for k, v in values.items()}


def _pose(actor):
    p, r, s = actor.get_actor_location(), actor.get_actor_rotation(), actor.get_actor_scale3d()
    return [p.x,p.y,p.z,r.pitch,r.yaw,r.roll,s.x,s.y,s.z]


def _native_parent(material, u):
    seen = set()
    while material and material.get_path_name().startswith(PRIVATE):
        path = material.get_path_name()
        if path in seen or not isinstance(material, u.MaterialInstanceConstant):
            raise RuntimeError('Unexpected or cyclic private pane material: ' + path)
        seen.add(path)
        material = material.get_editor_property('parent')
    return material.get_path_name() if material else None


def inspect_shader(api, master):
    """Read the installed native graph; no edits and no broad material export."""
    u, edit = api['u'], api['EDIT']
    expressions = edit.get_material_expressions(master)
    params = []
    for node in expressions:
        try:
            name = str(node.get_editor_property('parameter_name'))
        except Exception:
            continue
        if 'EM1' in name or 'EM2' in name or 'EM3' in name or name.startswith('Activate Emissive'):
            params.append({'name': name, 'type': node.get_class().get_name()})
    root = edit.get_material_property_input_node(master, u.MaterialProperty.MP_EMISSIVE_COLOR)
    queue, visited, route = [root] if root else [], set(), []
    while queue and len(visited) < 384:
        node = queue.pop()
        if not node or node.get_name() in visited:
            continue
        visited.add(node.get_name())
        inputs = edit.get_inputs_for_material_expression(master, node)
        row = {'node': node.get_name(), 'type': node.get_class().get_name(),
               'inputs': [n.get_name() for n in inputs if n]}
        try:
            row['parameter'] = str(node.get_editor_property('parameter_name'))
        except Exception:
            pass
        route.append(row); queue.extend(n for n in inputs if n)
    return {'source_master': master.get_path_name(), 'expression_count': len(expressions),
            'channel_parameters': params, 'emissive_route': route,
            'emissive_output_connected': bool(root), 'route_truncated': bool(queue),
            'source_inspection': 'Native master has separate EM1/EM2/EM3 masks, colors, animation and activation controls. '
                                 'One gain is applied to all intensity values; no per-channel minimum or clamp.'}


def apply(api):
    import unreal as u
    root, out = Path(api['ROOT']), Path(api['OUT'])
    edit, lib = api['EDIT'], api['LIB']
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    package = world.get_path_name().split('.')[0]
    fresh = package.startswith('/Temp/Untitled') and api.get('TARGET') == TARGET
    if package != TARGET and not fresh:
        raise RuntimeError('Interior graphics are restricted to the private outpost map')
    rows = layout()
    actors = {}
    for actor in api['EAS'].get_all_level_actors():
        actors.setdefault(actor.get_actor_label(), []).append(actor)
    prepared, sources, source_hashes = [], {}, {}
    for row in rows:
        found = actors.get(row['actor'], [])
        if len(found) != 1:
            raise RuntimeError('Missing or duplicate exact interior pane: ' + row['actor'])
        actor = found[0]
        components = actor.get_components_by_class(u.StaticMeshComponent)
        if len(components) != 1:
            raise RuntimeError('Unexpected pane component count: ' + row['actor'])
        component = components[0]
        if not component.static_mesh or component.static_mesh.get_path_name() != row['mesh']:
            raise RuntimeError('Refusing to replace materials on a different/native computer mesh: ' + row['actor'])
        if component.get_num_materials() != row['required_slots']:
            raise RuntimeError('Native digital-pane material slots changed')
        before = [component.get_material(i).get_path_name() if component.get_material(i) else None
                  for i in range(component.get_num_materials())]
        allowed = set(row['allowed_original_materials'] + [row['source_material']])
        for i in range(component.get_num_materials()):
            if _native_parent(component.get_material(i), u) not in allowed:
                raise RuntimeError('Pane has an unexpected authored material; no assignment: ' + row['actor'])
        source = api['load'](row['source_material'])
        if not isinstance(source, u.MaterialInstanceConstant):
            raise RuntimeError('Owned graphics must be native material instances')
        master = source
        while isinstance(master, u.MaterialInstanceConstant):
            master = master.get_editor_property('parent')
        if master.get_path_name() != MASTER:
            raise RuntimeError('Graphic no longer uses the inspected Genesis translucent master')
        sources[row['variant']] = source
        prepared.append((row, actor, component, before, _pose(actor), str(component.get_collision_enabled())))
    # Hash only the four source instances and their shared master. This guard
    # covers our actual scope without rescanning the asset library.
    master = api['load'](MASTER)
    for material in [master] + list(sources.values()):
        path = material.get_path_name().split('.')[0]
        filename = root / ('Content/' + path[len('/Game/'):] + '.uasset')
        source_hashes[path] = {'file': filename, 'sha256': hashlib.sha256(filename.read_bytes()).hexdigest()}
    graph = inspect_shader(api, master)
    names = {p['name'] for p in graph['channel_parameters']}
    required = {'Intensity EM1', 'Intensity EM2', 'Intensity EM3'}
    if not required <= names:
        raise RuntimeError('Native graphic channel interface changed; inspect shader before balancing')

    materials, recipes = {}, {}
    for variant, source in sources.items():
        dest = PRIVATE + 'MI_InteriorGraphic_' + variant
        child = api['load'](dest) if lib.does_asset_exist(dest) else api['TOOLS'].create_asset(
            'MI_InteriorGraphic_' + variant, PRIVATE.rstrip('/'),
            u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
        if not isinstance(child, u.MaterialInstanceConstant):
            raise RuntimeError('Private graphic path is not a material instance')
        if child.get_editor_property('parent') != source:
            edit.set_material_instance_parent(child, source)
        channels = {name: float(edit.get_material_instance_scalar_parameter_value(source, name)) for name in sorted(required)}
        gain, adjusted = channel_recipe(channels, clear=variant == 'Clear')
        for name, value in adjusted.items():
            # UE5.8's implementation always returns false even after a write.
            # Verify the resulting values below instead of trusting that flag.
            edit.set_material_instance_scalar_parameter_value(child, name, value)
        # Preserve texture/switch/opacity/animation settings through inheritance.
        # This also records the actual graphic masks, not a generic cyan color.
        textures = {str(name): edit.get_material_instance_texture_parameter_value(source, name)
                    for name in edit.get_texture_parameter_names(source)}
        textures = {name: texture.get_path_name() for name, texture in textures.items() if texture}
        for name, path in textures.items():
            inherited = edit.get_material_instance_texture_parameter_value(child, name)
            if not inherited or inherited.get_path_name() != path:
                raise RuntimeError('Private graphic has a foreign texture override: ' + name)
        preserved_scalars = 0
        for name in edit.get_scalar_parameter_names(source):
            if str(name) in required:
                continue
            native = float(edit.get_material_instance_scalar_parameter_value(source, name))
            inherited = float(edit.get_material_instance_scalar_parameter_value(child, name))
            if not math.isfinite(native) or not math.isfinite(inherited) or abs(native-inherited) > 1e-5:
                raise RuntimeError('Private graphic has a foreign non-emission override: ' + str(name))
            preserved_scalars += 1
        measured = {name: float(edit.get_material_instance_scalar_parameter_value(child, name)) for name in sorted(required)}
        if any(abs(measured[name]-adjusted[name]) > max(1e-5, abs(adjusted[name])*1e-5) for name in required):
            raise RuntimeError('Private graphic failed common-gain verification')
        edit.update_material_instance(child)
        if not lib.save_loaded_asset(child):
            raise RuntimeError('Could not save private graphic instance')
        materials[variant] = child
        recipes[variant] = {'source': source.get_path_name(), 'private': child.get_path_name(),
            'source_channels': channels, 'common_gain': gain, 'private_channels': measured,
            'native_textures': textures,
            'verified_inherited_non_emission_scalars': preserved_scalars,
            'native_texture_bindings_preserved': True,
            'clear_glass': variant == 'Clear'}

    assignments = []
    for row, actor, component, before, pose, collision in prepared:
        child = materials[row['variant']]
        for i in range(component.get_num_materials()):
            component.set_material(i, child)
        if _pose(actor) != pose or str(component.get_collision_enabled()) != collision:
            raise RuntimeError('Pane geometry or collision changed during material-only assignment')
        assignments.append({'actor': row['actor'], 'mesh': row['mesh'], 'before': before,
                            'after': child.get_path_name(), 'slots': row['required_slots'],
                            'purpose': row['purpose'], 'pose_and_collision_unchanged': True})
    for path, record in source_hashes.items():
        if hashlib.sha256(record['file'].read_bytes()).hexdigest() != record['sha256']:
            raise RuntimeError('Native vendor material changed on disk: ' + path)
    receipt = {'assignments': assignments, 'recipes': recipes, 'native_shader': graph,
        'source_hashes': {path: record['sha256'] for path, record in source_hashes.items()},
        'vendor_sources_unchanged': True, 'geometry_changed': False, 'new_lights': 0,
        'decorative_graphics_only': True,
        'untouched': 'Native P3 computer screens, all market content, six wardrobe side panes and every frame.',
        'validation': 'Native source/slot checks; rendered legibility and character visibility still need capture.'}
    (out/'interior-graphics.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt
