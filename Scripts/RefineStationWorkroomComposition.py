"""Complete front-desk relocation and legible physical archive case labels.

The lead calls apply(ctx) on the guarded DisplayWall1 candidate, then owns save,
rollback, rendered review and actual walking. No map/process/asset writes here.
Only two complete desk/service groups move; all other existing poses, native
materials, collision, Home, Earth, room shells and skyline remain unchanged.
"""
import hashlib
import json
import math
from pathlib import Path

from OutpostGeometryUtils import mesh_union
from StationRefinementSupport import transform_record


MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
MAP_SHA = '5f335c3dd662b641354afc0ebd6e2b18f1ab2770c8630d1b636934b0f8ff20e8'
AUDIT_SHA = 'e1a7a187c95603c7a898d3eb23aa2ddd56514b0edabd1b0d2069479257442fb9'
TAG = 'StationWorkroomComposition20261006'
PODS = (
    ('Port South', (7400, -210, 0), (7100, -950, 0), (300, 300, 0),
     'Crew/Engineer', 'SHIP & PARTS', (7200, -720, 125), 'ShipLoadout', (7000, -720, 100)),
    ('Port North', (7400, 210, 0), (7100, 950, 0), (300, -300, 0),
     'Crew/Ops officer', 'PILOT LEADERBOARD', (7000, 720, 125), 'Modules', (7200, 720, 100)),
)
# Feet paths retain the previously checked Goliath circuit and add explicit
# separate approaches to each of the four relocated interaction points.
ROUTES = {
    'Operations entrance': [(6700, 0, 0), (7100, 0, 0), (7400, 0, 0)],
    'Operations Goliath circuit': [(7400, 0, 0), (7400, -460, 0), (8250, -460, 0),
                                  (8520, 0, 0), (8250, 460, 0), (7400, 460, 0), (7400, 0, 0)],
    'ShipLoadout approach': [(7100, 0, 0), (7300, 0, 0), (7300, -320, 0)],
    'Ship parts approach': [(7400, 0, 0), (7500, 0, 0), (7500, -320, 0)],
    'Pilot records approach': [(7100, 0, 0), (7300, 0, 0), (7300, 320, 0)],
    'Modules approach': [(7400, 0, 0), (7500, 0, 0), (7500, 320, 0)],
    'Archive wardrobe': [(4200, 2470, 0), (4400, 2750, 0), (4400, 3200, 0), (4750, 3400, 0)],
    'Archive cases': [(5030, 2700, 0), (5030, 3300, 0), (5030, 4000, 0)],
}


def _one(actors, label):
    rows = [a for a in actors if a.get_actor_label() == label]
    if len(rows) != 1:
        raise RuntimeError('Expected one reviewed actor: ' + label)
    return rows[0]


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pose(actor):
    t = actor.get_actor_transform()
    return (tuple(t.translation.to_tuple()), tuple(t.rotation.to_tuple()), tuple(t.scale3d.to_tuple()))


def _near(actual, expected, tolerance=.05):
    return len(actual) == len(expected) and max(abs(a - b) for a, b in zip(actual, expected)) <= tolerance


def _guard_pose(actor, source, delta=(0, 0, 0)):
    p, q, s = _pose(actor)
    expected = tuple(source['location'][i] + delta[i] for i in range(3))
    if (not _near(p, expected) or not _near(s, source['scale'], .0001) or
            not (_near(q, source['rotation'], .0001) or _near(q, [-v for v in source['rotation']], .0001))):
        raise RuntimeError('Reviewed assembly pose changed: ' + actor.get_actor_label())


def _bounds(actors, u):
    rows = []
    for actor in actors:
        if any(c.static_mesh for c in actor.get_components_by_class(u.StaticMeshComponent)):
            c, e = mesh_union(actor)
            rows.append(([c.x - e.x, c.y - e.y, c.z - e.z], [c.x + e.x, c.y + e.y, c.z + e.z]))
    if not rows:
        raise RuntimeError('Complete assembly has no native static geometry')
    return {'minimum': [min(row[0][i] for row in rows) for i in range(3)],
            'maximum': [max(row[1][i] for row in rows) for i in range(3)]}


def _appearance(actor, u):
    return [(c.get_name(), tuple(c.get_materials()), c.get_collision_enabled())
            for c in actor.get_components_by_class(u.MeshComponent)]


def _operator_state(actor):
    component = actor.character_mesh
    t = component.get_relative_transform()
    return (tuple(t.translation.to_tuple()), tuple(t.rotation.to_tuple()), tuple(t.scale3d.to_tuple()),
            component.get_skeletal_mesh_asset(), actor.get_editor_property('idle_animation'),
            tuple(actor.get_editor_property('gesture_animations')), tuple(actor.get_editor_property('route_points')),
            float(actor.get_editor_property('phase_offset')))


def _attachment_depth(actor):
    depth, seen = 0, {actor}
    parent = actor.get_attach_parent_actor()
    while parent:
        if parent in seen:
            raise RuntimeError('Cyclic attachment in the saved desk assembly')
        seen.add(parent)
        depth += 1
        parent = parent.get_attach_parent_actor()
    return depth


def _hit(result):
    fields = result.to_tuple() if result is not None else None
    if not fields or not fields[0]:
        return None
    actor, component = fields[9], fields[10]
    return {'label': actor.get_actor_label() if actor else None,
            'component': component.get_name() if component else None,
            'point': list(fields[5].to_tuple()), 'normal': list(fields[7].to_tuple()),
            'initial_overlap': bool(fields[1])}


def _routes(world, u):
    """Full ordinary capsule, no ignored actors or collision changes; no walking claim."""
    segments, floors = [], []
    samples = set()
    for name, points in ROUTES.items():
        for a, b in zip(points, points[1:]):
            start, end = u.Vector(a[0], a[1], a[2] + 78), u.Vector(b[0], b[1], b[2] + 78)
            hit = _hit(u.SystemLibrary.capsule_trace_single_by_profile(
                world, start, end, 34., 75., 'Pawn', False, [], u.DrawDebugTrace.NONE, True))
            row = {'route': name, 'feet_a': a, 'feet_b': b, 'hit': hit}
            segments.append(row)
            if hit:
                raise RuntimeError('Moved desk route blocked: ' + json.dumps(row))
            count = max(1, math.ceil(math.dist(a, b) / 100))
            samples.update(tuple(a[i] + (b[i] - a[i]) * t / count for i in range(3))
                           for t in range(count + 1))
    for p in sorted(samples):
        hit = _hit(u.SystemLibrary.line_trace_single_by_profile(world,
            u.Vector(p[0], p[1], p[2] + 35), u.Vector(p[0], p[1], p[2] - 65),
            'Pawn', False, [], u.DrawDebugTrace.NONE, True))
        if not hit or abs(hit['point'][2] - p[2]) > 5 or hit['normal'][2] < .7:
            raise RuntimeError('Route lost actual floor support: ' + json.dumps({'feet': p, 'hit': hit}))
        floors.append({'feet': p, 'hit': hit})
    return {'capsule_radius_cm': 34, 'capsule_half_height_cm': 75, 'floor_gap_cm': 3,
            'profile': 'Pawn', 'ignored_actors': [], 'segments': segments, 'floor_samples': floors,
            'runtime_walking_verified': False}


def _fit_text(component, size, width, height):
    component.set_world_size(size)
    measured = component.get_text_local_size()
    factor = min(1., width / max(abs(measured.x), abs(measured.y), .001), height / max(abs(measured.z), .001))
    component.set_world_size(size * factor)
    measured = component.get_text_local_size()
    if max(abs(measured.x), abs(measured.y)) > width + .01 or abs(measured.z) > height + .01:
        raise RuntimeError('Physical label exceeds its native supporting face')
    return {'world_size_cm': float(component.get_editor_property('world_size')),
            'local_extent_size_cm': list(measured.to_tuple()), 'allowed_width_height_cm': [width, height]}


def apply(ctx):
    import unreal as u
    actors = list(ctx.actors)
    root = Path(u.Paths.project_dir())
    map_file = root / ('Content/' + MAP[6:] + '.umap')
    audit_file = root / '.agent/local/StationRefinement/OwnerAudit/actors.json'
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name().split('.')[0] != MAP or _sha(map_file) != MAP_SHA or _sha(audit_file) != AUDIT_SHA:
        raise RuntimeError('Workroom composition requires the exact reviewed DisplayWall1 map and owner inventory')
    marker = _one(actors, 'Refine/Operations/Identity')
    if 'StationDisplayWall20261006' not in map(str, marker.tags) or TAG in map(str, marker.tags):
        raise RuntimeError('Expected DisplayWall1 once; do not replay this pass')
    audit = {r['label']: r for r in json.loads(audit_file.read_text(encoding='utf-8'))['actors']}
    staged, selected = [], set()
    for name, original, current, delta, operator_label, service_name, service_point, anchor_key, anchor_point in PODS:
        prefix = 'OperationsNative/Command island ' + name + '/'
        pod = [a for a in actors if a.get_actor_label().startswith(prefix)]
        if len(pod) != 17:
            raise RuntimeError('Complete desk assembly membership changed: ' + name)
        for actor in pod:
            shift = [current[i] - original[i] for i in range(3)]
            if '/SM_TitaniumIndustrySeat_' in actor.get_actor_label():
                shift[2] += 4.92005
            _guard_pose(actor, audit[actor.get_actor_label()]['transform'], shift)
        operator = _one(actors, operator_label)
        if operator.get_actor_enable_collision() or not operator.character_mesh.get_skeletal_mesh_asset():
            raise RuntimeError('Expected the reviewed seated presentation operator')
        footrest = _one(actors, 'Refine/Operations/' + name + '/Footrest')
        service_label = 'Services/' + service_name
        service = _one(actors, service_label)
        service_group = [a for a in actors if a == service or a.get_actor_label().startswith(service_label + '/')]
        if len(service_group) != 2 or not _near(service.get_actor_location().to_tuple(), service_point):
            raise RuntimeError('Integrated service root/face changed: ' + service_label)
        anchor = _one(actors, 'Refine/Operations/Service anchor ' + anchor_key)
        if (not _near(anchor.get_actor_location().to_tuple(), anchor_point) or
                'OutpostServiceAnchor:' + anchor_key not in map(str, anchor.tags)):
            raise RuntimeError('Native service anchor changed: ' + anchor_key)
        group = pod + [operator, footrest] + service_group + [anchor]
        if selected.intersection(group):
            raise RuntimeError('An actor belongs to two moving groups')
        selected.update(group)
        staged.append((name, group, delta, _bounds(pod + [footrest], u)))
    cases = []
    for index, y in enumerate((2800, 3360, 3960), 1):
        prefix = 'LoungeNative/Hologram bay %d/' % index
        cap, housing, lamp = [_one(actors, prefix + tail) for tail in ('Top cap', 'Owned light housing', 'Task light')]
        for actor in (cap, housing, lamp):
            _guard_pose(actor, audit[actor.get_actor_label()]['transform'])
        light = lamp.get_component_by_class(u.PointLightComponent)
        if not light or abs(light.get_editor_property('intensity') - 450) > .01 or abs(light.get_editor_property('attenuation_radius') - 310) > .01:
            raise RuntimeError('Inspected mounted archive light changed')
        cases.append((index, y, cap, housing, lamp, light))
    if any(a.get_actor_label().startswith('Refine/WorkroomComposition/') for a in actors):
        raise RuntimeError('Preserve existing composition labels')
    wardrobe_actor = _one(actors, 'Services/CREW WARDROBE/Face')
    wardrobe = wardrobe_actor.get_component_by_class(u.TextRenderComponent)
    if str(wardrobe.get_editor_property('text')) != 'CREW WARDROBE':
        raise RuntimeError('Existing wardrobe label semantics changed')
    label_material = _one(actors, 'Refine/Archive/Identity').get_component_by_class(u.TextRenderComponent).get_editor_property('text_material')
    if not label_material or '/OwnerPreview/Materials/ServicePolish/' not in label_material.get_path_name():
        raise RuntimeError('Expected the reviewed private unlit service font material')
    # Fail the same geometry guard before editing, so an unrelated existing
    # obstruction cannot be misreported as a successful new composition.
    before_routes = _routes(world, u)
    poses = {a: _pose(a) for a in actors}
    operator_states = {_one(actors, row[4]): _operator_state(_one(actors, row[4])) for row in PODS}
    appearances = {a: _appearance(a, u) for a in selected | {a for a in actors if a.get_actor_label().startswith('Lounge/Archive projection')}}
    collision = {a: a.get_actor_enable_collision() for a in selected}
    moved = []
    for name, group, delta, bounds in staged:
        # Snapshot absolute targets first, so attached members never move twice.
        destinations = {a: tuple(poses[a][0][i] + delta[i] for i in range(3)) for a in group}
        for actor in sorted(group, key=_attachment_depth):
            ctx.move(actor, destinations[actor])
        if any(not _near(a.get_actor_location().to_tuple(), destinations[a]) for a in group):
            raise RuntimeError('Complete desk members did not retain their rigid offsets')
        after = _bounds(group, u)
        moved.append({'name': name, 'delta_cm': delta, 'before_static_bounds': bounds,
                      'after_static_bounds': after, 'actors': [transform_record(a) for a in group]})
    aisle = moved[1]['after_static_bounds']['minimum'][1] - moved[0]['after_static_bounds']['maximum'][1]
    if aisle < 200:
        raise RuntimeError('Complete front groups violate the 200 cm central aisle')
    after_routes = _routes(world, u)
    labels, lights = [], []
    for index, y, cap, housing, lamp, light in cases:
        c, e = mesh_union(cap)
        if not _near((c.x, c.y, c.z, e.y, e.z), (5350, y, 290, 120, 20)):
            raise RuntimeError('Archive case cap no longer has its reviewed label envelope')
        position = (c.x - e.x - 1., c.y, c.z)
        actor = ctx.text('WorkroomComposition/Archive case %02d' % index, 'ARCHIVE %02d' % index,
                         position, 180, 24, (.65, .82, 1.))
        component = actor.get_component_by_class(u.TextRenderComponent)
        component.set_text_material(label_material)
        labels.append({'case': index, 'mount': cap.get_actor_label(), 'position_cm': position,
                       'yaw': 180, **_fit_text(component, 24, 210, 30)})
        before = {key: float(light.get_editor_property(key)) for key in
                  ('intensity', 'attenuation_radius', 'specular_scale', 'indirect_lighting_intensity')}
        before.update({'intensity_units': str(light.get_editor_property('intensity_units')),
                       'color': list(light.get_editor_property('light_color').to_tuple())})
        light.set_intensity_units(u.LightUnits.LUMENS)
        light.set_intensity(650.)
        light.set_attenuation_radius(280.)
        light.set_light_color(u.LinearColor(.67, .79, 1., 1.))
        light.set_editor_property('specular_scale', .15)
        light.set_editor_property('indirect_lighting_intensity', .25)
        row = {'actor': lamp.get_actor_label(), 'fixture': housing.get_actor_label(), 'before': before,
               'after': {'lumens': 650, 'radius_cm': 280, 'color': [.67, .79, 1.],
                         'specular_scale': .15, 'indirect_lighting_intensity': .25}}
        ctx.records.append({'kind': 'archive_mounted_task_light', **row})
        lights.append(row)
    before = {'world_size': float(wardrobe.get_editor_property('world_size')),
              'material': wardrobe.get_editor_property('text_material').get_path_name(),
              'color': list(wardrobe.get_editor_property('text_render_color').to_tuple())}
    wardrobe.set_text_material(label_material)
    wardrobe.set_text_render_color(u.Color(166, 210, 255, 255))
    wardrobe_fit = _fit_text(wardrobe, 20, 92, 36)
    ctx.records.append({'kind': 'wardrobe_existing_label', 'actor': wardrobe_actor.get_actor_label(),
                        'before': before, 'after': wardrobe_fit, 'text_unchanged': True})
    for actor, before in poses.items():
        after = _pose(actor)
        if actor not in selected and after != before:
            raise RuntimeError('Unrelated owner transform changed: ' + actor.get_actor_label())
        if actor in selected and (after[1:] != before[1:] or actor.get_actor_enable_collision() != collision[actor]):
            raise RuntimeError('Rigid group move changed orientation, scale or collision')
    for actor, before in appearances.items():
        if _appearance(actor, u) != before:
            raise RuntimeError('Group move changed native geometry materials/collision')
    if any(_operator_state(a) != before for a, before in operator_states.items()):
        raise RuntimeError('Rigid desk move changed a seated operator pose or animation')
    if _sha(map_file) != MAP_SHA:
        raise RuntimeError('This helper must not save the owner map')
    marker.tags = list(marker.tags) + [TAG]
    return {'module': 'workroom_composition', 'dirty_assets': [], 'basis_map_sha256': MAP_SHA,
            'moved_complete_groups': moved, 'central_aisle_static_width_cm': aisle,
            'routes_before': before_routes, 'routes_after': after_routes,
            'archive_case_labels': labels, 'mounted_case_lights': lights,
            'existing_wardrobe_label': wardrobe_fit, 'unrelated_transforms_preserved': len(poses) - len(selected),
            'cameras': [{'name': 'Archive straight-on', 'location': [4200, 2450, 185], 'look_at': [4200, 3650, 185]},
                        {'name': 'Operations entrance matched', 'location': [6620, 0, 185], 'look_at': [8150, 0, 185]}],
            'limits': 'Static all-actor capsule/floor evidence only; actual room renders, operator contact and natural service walking remain required.'}
