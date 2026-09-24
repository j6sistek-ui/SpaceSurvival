"""Reveal the native vendor frontage without dismantling the market assembly.

Run build(api) after OutpostTechDisplays.build and OutpostLocalLights.apply.
The complete NorthCommerce valance rises to its EXISTING overhead deck edge;
its internal component/instance poses, cloth roofs, counters and wares remain
unchanged. Six existing downward RectLights receive explicit local task levels.
No actors/light components are added, no vendor assets are modified, no save
or Unreal launch is performed. plan()/audit_plan() are ordinary Python.
"""
import itertools
import json
import math
from pathlib import Path

TARGET_MAP = '/Game/OutpostSandbox/L_AsteroidOutpost'
TASK_TAG = 'OutpostMarketTask'
PRESENTATION_TAG = 'OutpostMarketPresentation'
FASCIA_LABEL = 'MarketNative/NorthCommerce/BP_ISM_Structure_V2'
DECK_LABEL = 'MarketNative/NorthCommerce/BP_ISM_Floor400x192'
FIXTURE_MESH = '/Game/P1toP5_Bundle/P5_FruitSeller/Meshes/SM_Props_ConstructionPart118_Light.SM_Props_ConstructionPart118_Light'
TASK_LUMENS = 600.
TASK_RADIUS = 650.
FIXTURES = (
    ('NorthCommerce', 'BP_ISM_Light_V13'),
    ('NorthCommerce', 'BP_ISM_Light_V15'),
    ('NorthCommerce', 'BP_ISM_Light_V11'),
    ('SouthMachinery', 'BP_ISM_Light_V1'),
    ('SouthMachinery', 'BP_ISM_Light_V11'),
    ('SouthBotany', 'BP_ISM_Light_V15'),
)


def plan(data=None):
    from OutpostTechDisplays import placement
    if data is None:
        data = json.loads(Path(__file__).with_name('OutpostMarketAssemblies.json').read_text(encoding='utf-8'))
    by_block = {b['name']: b for b in data['blocks']}
    rows = []

    def record(block_name, name):
        block = by_block[block_name]
        source = [r for r in block['actors'] if r['name'] == name]
        if len(source) != 1:
            raise ValueError('Missing or ambiguous source market actor: ' + block_name + '/' + name)
        row = source[0]
        location, rotation, scale = placement(row, block, data['source_pivot'])
        return row, {'label': 'MarketNative/' + block_name + '/' + name,
                     'class': row['class'], 'source_location': location,
                     'source_rotation': rotation, 'source_scale': scale}

    for block, name in FIXTURES:
        source, item = record(block, name)
        geometry = [c for c in source['components'] if c['mesh'] == FIXTURE_MESH]
        if len(geometry) != 1 or len(geometry[0]['instances']) != 1:
            raise ValueError('Task light requires the known single native fixture instance: ' + item['label'])
        item.update({'fixture_component': geometry[0]['name'], 'mesh': FIXTURE_MESH,
                     'lumens': TASK_LUMENS, 'radius_cm': TASK_RADIUS, 'casts_shadows': False})
        rows.append(item)
    _, fascia = record('NorthCommerce', 'BP_ISM_Structure_V2')
    _, deck = record('NorthCommerce', 'BP_ISM_Floor400x192')
    return {'source_map': data['source_map'], 'valance': fascia, 'overhead_deck': deck,
            'fixtures': rows, 'no_new_lights': True,
            'preserved': ['cloth poses', 'structural columns', 'counter poses', 'fruit trays',
                          'native fixture poses and colors', 'centre promenade', 'all vendor assets']}


def audit_plan(recipe):
    errors = []
    labels = [r['label'] for r in recipe['fixtures']]
    if len(labels) != 6 or len(set(labels)) != 6:
        errors.append('Exactly six distinct existing fixtures are required')
    for row in recipe['fixtures']:
        if abs(row['source_location'][1]) < 500:
            errors.append(row['label'] + ': source fixture intrudes into central promenade')
        if row['mesh'] != FIXTURE_MESH or row['casts_shadows']:
            errors.append(row['label'] + ': must reuse native task fixture without new shadows')
        if not 500 <= row['lumens'] <= 800 or row['radius_cm'] > 650:
            errors.append(row['label'] + ': exceeds authorized local task-light range')
    return {'source_plan_only': True, 'existing_fixtures': len(labels), 'new_lights': 0,
            'existing_valance_assemblies_to_move': 1, 'violations': errors}


def _values(vector):
    return [float(vector.x), float(vector.y), float(vector.z)]


def _bounds(u, component, transform):
    native = component.static_mesh.get_bounds()
    points = []
    for signs in itertools.product((-1, 1), repeat=3):
        local = native.origin + u.Vector(native.box_extent.x * signs[0],
                                         native.box_extent.y * signs[1],
                                         native.box_extent.z * signs[2])
        points.append(_values(u.MathLibrary.transform_location(transform, local)))
    return [min(p[i] for p in points) for i in range(3)] + [max(p[i] for p in points) for i in range(3)]


def _mesh_boxes(u, actor):
    result = []
    for component in actor.get_components_by_class(u.StaticMeshComponent):
        if not component.static_mesh:
            continue
        if isinstance(component, u.InstancedStaticMeshComponent):
            transforms = [component.get_instance_transform(i, world_space=True)
                          for i in range(component.get_instance_count())]
        else:
            transforms = [component.get_world_transform()]
        result.extend(_bounds(u, component, transform) for transform in transforms)
    if not result:
        raise ValueError('No rendered market geometry: ' + actor.get_actor_label())
    return result


def _union(boxes):
    return [min(b[i] for b in boxes) for i in range(3)] + [max(b[i + 3] for b in boxes) for i in range(3)]


def _touches(a, b):
    return all(a[i] <= b[i + 3] + .25 and a[i + 3] >= b[i] - .25 for i in range(3))


def support_audit(valance_boxes, deck_boxes):
    """Check real instance AABBs, not an inflated whole-building bounding box."""
    linked = {i for i, b in enumerate(valance_boxes) if any(_touches(b, d) for d in deck_boxes)}
    direct = sorted(linked)
    while True:
        count = len(linked)
        linked.update(i for i, box in enumerate(valance_boxes)
                      if any(_touches(box, valance_boxes[j]) for j in linked))
        if len(linked) == count:
            break
    return {'native_valance_instances': len(valance_boxes), 'native_deck_instances': len(deck_boxes),
            'direct_deck_contacts': direct, 'unsupported_instances': sorted(set(range(len(valance_boxes))) - linked),
            'method': 'Transformed native mesh AABBs plus touching-frame connectivity, not triangle collision.'}


def _local_pose(u, actor):
    """Capture child/instance poses while excluding the deliberately moved root."""
    def values(transform):
        rot = transform.rotation.rotator()
        return _values(transform.translation) + [rot.pitch, rot.yaw, rot.roll] + _values(transform.scale3d)
    rows = {}
    for component in actor.get_components_by_class(u.SceneComponent):
        if component.get_attach_parent() is not None:
            rows[component.get_name()] = [values(component.get_relative_transform())]
        if isinstance(component, u.InstancedStaticMeshComponent):
            rows[component.get_name() + '/Instances'] = [values(component.get_instance_transform(i, world_space=False))
                                                        for i in range(component.get_instance_count())]
    return rows


def _pose_error(before, after):
    if before.keys() != after.keys():
        return float('inf')
    maximum = 0.
    for key in before:
        if len(before[key]) != len(after[key]):
            return float('inf')
        for a, b in zip(before[key], after[key]):
            maximum = max(maximum, *(abs(x - y) for x, y in zip(a, b)))
    return maximum


def _light_state(component):
    return {'location': _values(component.get_world_location()),
            'intensity': float(component.get_editor_property('intensity')),
            'units': str(component.get_editor_property('intensity_units')),
            'radius_cm': float(component.get_editor_property('attenuation_radius')),
            'casts_shadows': bool(component.get_editor_property('cast_shadows'))}


def build(api):
    u, eas = api['u'], api['EAS']
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    package = world.get_path_name().split('.')[0]
    blank = package.startswith('/Temp/Untitled') and api.get('TARGET') == TARGET_MAP
    if package != TARGET_MAP and not blank:
        raise RuntimeError('Market presentation is restricted to ' + TARGET_MAP)
    recipe = plan()
    source_audit = audit_plan(recipe)
    if source_audit['violations']:
        raise ValueError('; '.join(source_audit['violations']))
    actors = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
    for row in [recipe['valance'], recipe['overhead_deck']] + recipe['fixtures']:
        if row['label'] not in actors or actors[row['label']].get_class().get_path_name() != row['class']:
            raise ValueError('Author the unchanged native market first: ' + row['label'])
    prepared_lights = []
    for row in recipe['fixtures']:
        actor = actors[row['label']]
        lights = list(actor.get_components_by_class(u.RectLightComponent))
        if len(lights) != 1:
            raise ValueError('Expected one existing RectLight; no duplicate will be created: ' + row['label'])
        components = {c.get_name(): c for c in actor.get_components_by_class(u.StaticMeshComponent)}
        fixture = components.get(row['fixture_component'])
        if fixture is None or fixture.static_mesh.get_path_name() != FIXTURE_MESH:
            raise ValueError('Task-light hardware changed: ' + row['label'])
        if not isinstance(fixture, u.InstancedStaticMeshComponent) or fixture.get_instance_count() != 1:
            raise ValueError('Expected the single native fixture instance: ' + row['label'])
        lens_bounds = _bounds(u, fixture, fixture.get_instance_transform(0, world_space=True))
        light_position = _values(lights[0].get_world_location())
        if any(light_position[i] < lens_bounds[i] - 10 or light_position[i] > lens_bounds[i + 3] + 10 for i in range(3)):
            raise ValueError('Existing light is not at the native fixture lens: ' + row['label'])
        prepared_lights.append((row, actor, lights[0], lens_bounds))

    fascia, deck = actors[FASCIA_LABEL], actors[DECK_LABEL]
    before = _values(fascia.get_actor_location())
    original = recipe['valance']['source_location']
    if max(abs(before[i] - original[i]) for i in (0, 1)) > .5:
        raise ValueError('Valance XY was independently edited; preserve it rather than overwrite')
    boxes_before = _mesh_boxes(u, fascia)
    deck_boxes = _mesh_boxes(u, deck)
    bounds_before, deck_bounds = _union(boxes_before), _union(deck_boxes)
    top_offset = bounds_before[5] - before[2]
    target = [before[0], before[1], deck_bounds[5] - top_offset]
    total_raise = target[2] - original[2]
    if not 35 <= total_raise <= 80:
        raise ValueError('Native valance/deck separation differs from reviewed~55cm arrangement')
    local_before = _local_pose(u, fascia)
    fascia.set_actor_location(u.Vector(*target), False, False)
    boxes_after = _mesh_boxes(u, fascia)
    bounds_after = _union(boxes_after)
    support = support_audit(boxes_after, deck_boxes)
    pose_error = _pose_error(local_before, _local_pose(u, fascia))
    if (support['unsupported_instances'] or pose_error > .001 or bounds_after[2] < 235
            or abs(bounds_after[5] - deck_bounds[5]) > .05):
        fascia.set_actor_location(u.Vector(*before), False, False)
        raise RuntimeError('Valance support/pose check failed; original position restored: '
                           + json.dumps({'support': support, 'pose_error': pose_error, 'bounds': bounds_after}))
    api['tag'](fascia, PRESENTATION_TAG)
    for row in api.get('RECORDS', []):
        if row.get('name') == FASCIA_LABEL:
            row['location'] = list(target)

    light_changes = []
    for row, actor, component, lens_bounds in prepared_lights:
        previous = _light_state(component)
        component.set_intensity_units(u.LightUnits.LUMENS)
        component.set_intensity(row['lumens'])
        component.set_attenuation_radius(row['radius_cm'])
        component.set_cast_shadows(False)
        tags = list(component.component_tags)
        if TASK_TAG not in [str(t) for t in tags]:
            component.component_tags = tags + [u.Name(TASK_TAG)]
        api['tag'](actor, TASK_TAG)
        after = _light_state(component)
        if max(abs(a - b) for a, b in zip(previous['location'], after['location'])) > .001:
            raise RuntimeError('A task-light pose changed unexpectedly: ' + row['label'])
        light_changes.append({'actor': row['label'], 'component': component.get_name(),
                              'before': previous, 'after': after, 'native_lens_bounds': lens_bounds})
    receipt = {'map': TARGET_MAP, 'source_plan': recipe, 'source_audit': source_audit,
               'valance': {'name': FASCIA_LABEL, 'position_before': before, 'position_after': target,
                           'absolute_raise_from_source_cm': total_raise, 'bounds_before': bounds_before,
                           'bounds_after': bounds_after, 'mounting_deck_bounds': deck_bounds,
                           'support': support, 'internal_pose_max_error': pose_error},
               'existing_lights_modified': light_changes, 'new_light_components': 0,
               'vendor_assets_modified': False, 'validation': 'Native appearance and owner acceptance pending.'}
    (Path(api['OUT']) / 'market-presentation.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt
