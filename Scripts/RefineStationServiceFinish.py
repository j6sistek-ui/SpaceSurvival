"""Small native furnishing/signage pass on the guarded owner-preview candidate.

The lead owns loading, saving, rollback and rendered review. This helper changes
only five existing service face labels, the Archive identity and one reception
lamp; service roots/anchors, crew poses, geometry assets and materials stay intact.
"""
import hashlib
import json
import math
from pathlib import Path

from OutpostGeometryUtils import mesh_union
from RefineStationWorkroomComposition import _appearance, _fit_text, _hit, _one, _pose, ROUTES
from StationRefinementSupport import transform_record


MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
TAG = 'StationServiceFinish20261006'
PLANT = '/Game/P1toP5_Bundle/P5_FruitSeller/Blueprints/BP_ISM_PlantBox_V1'
GRAPHITE = '/Game/OutpostSandbox/Materials/M_OutpostGraphite'
PEARL = '/Game/OutpostSandbox/Materials/M_OutpostPearl'
RECEPTION = [(2780, 0, 0), (3400, 0, 0), (3700, -500, 0), (4200, -620, 0),
             (4780, -300, 0), (5050, 0, 0), (4780, 300, 0), (4200, 620, 0),
             (3700, 500, 0), (3400, 0, 0), (2780, 0, 0)]
PLANTS = [('Operations south', (7820, -820)), ('Operations north', (7820, 820)),
          ('Archive west', (3970, 4260)), ('Archive east', (4430, 4260))]
DESKS = [('SHIP & PARTS', 'Port South', 1), ('PILOT LEADERBOARD', 'Port North', -1),
         ('CONTRACT EXCHANGE', 'Starboard South', 1), ('TRADE NETWORK', 'Starboard North', -1)]


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _routes(world, u):
    routes = {**ROUTES, 'Reception verified ring': RECEPTION}
    segments, floors, samples = [], [], set()
    for name, points in routes.items():
        for a, b in zip(points, points[1:]):
            hit = _hit(u.SystemLibrary.capsule_trace_single_by_profile(
                world, u.Vector(a[0], a[1], a[2] + 78), u.Vector(b[0], b[1], b[2] + 78),
                34., 75., 'Pawn', False, [], u.DrawDebugTrace.NONE, True))
            row = {'route': name, 'feet_a': a, 'feet_b': b, 'hit': hit}
            if hit:
                raise RuntimeError('Service finish route blocked: ' + json.dumps(row))
            segments.append(row)
            count = max(1, math.ceil(math.dist(a, b) / 100))
            samples.update(tuple(a[i] + (b[i] - a[i]) * t / count for i in range(3))
                           for t in range(count + 1))
    for p in sorted(samples):
        hit = _hit(u.SystemLibrary.line_trace_single_by_profile(world,
            u.Vector(p[0], p[1], p[2] + 35), u.Vector(p[0], p[1], p[2] - 65),
            'Pawn', False, [], u.DrawDebugTrace.NONE, True))
        if not hit or abs(hit['point'][2] - p[2]) > 5 or hit['normal'][2] < .7:
            raise RuntimeError('Service finish route lost support: ' + json.dumps({'feet': p, 'hit': hit}))
        floors.append({'feet': p, 'hit': hit})
    return {'segments': segments, 'floor_samples': floors, 'radius_cm': 34, 'half_height_cm': 75,
            'ignored_actors': [], 'runtime_walking_verified': False}


def _mount(ctx, actor, center, normal, width, height, u):
    """A shallow backed plaque physically meets the inspected desk/wall face."""
    yaw = math.degrees(math.atan2(normal[1], normal[0]))
    backing = ctx.box('ServiceFinish/' + actor.get_actor_label() + '/Plaque', center,
                      (4, width, height), GRAPHITE, False)
    backing.set_actor_rotation(u.Rotator(pitch=0, yaw=yaw, roll=0), False)
    component = actor.get_component_by_class(u.TextRenderComponent)
    before = {'actor': transform_record(actor), 'world_size': float(component.get_editor_property('world_size')),
              'text': str(component.get_editor_property('text'))}
    position = (center[0] + normal[0] * 2.5, center[1] + normal[1] * 2.5, center[2])
    ctx.move(actor, position, (0, yaw, 0))
    fit = _fit_text(component, 18 if height < 40 else 22, width - 12, height - 10)
    if str(component.get_editor_property('text')) != before['text']:
        raise RuntimeError('Mounted label changed existing service semantics')
    row = {'label': actor.get_actor_label(), 'before': before, 'position_cm': position,
           'plaque': backing.get_actor_label(), **fit}
    ctx.records.append({'kind': 'mounted_service_label', **row})
    return row


def apply(ctx):
    import unreal as u
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    command = u.SystemLibrary.get_command_line().lower()
    if (world.get_path_name().split('.')[0] != MAP or
            u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world() or
            not any(flag in command for flag in ('-renderoffscreen', '-nullrhi'))):
        raise RuntimeError('Service finish requires the isolated owner-preview editor')
    map_file = root / ('Content/' + MAP[6:] + '.umap')
    map_sha = _sha(map_file)
    basis = None
    for name in ('SocialFinish1', 'Compatibility1'):
        path = root / ('.agent/local/StationRefinement/' + name + '.json')
        if path.exists():
            receipt = json.loads(path.read_text(encoding='utf-8-sig'))
            if receipt.get('success') is True and receipt.get('after_sha256') == map_sha:
                basis = {'receipt': name, 'sha256': _sha(path), 'map_sha256': map_sha}
                break
    if basis is None:
        raise RuntimeError('Expected exact successful SocialFinish1 or Compatibility1 saved map')
    actors = list(ctx.actors)
    if any(a.get_actor_label().startswith('Refine/ServiceFinish/') for a in actors):
        raise RuntimeError('Preserve existing ServiceFinish; do not replay')
    marker = _one(actors, 'Refine/Operations/Identity')
    if TAG in map(str, marker.tags):
        raise RuntimeError('ServiceFinish marker already applied')
    faces = [_one(actors, 'Services/' + name + '/Face') for name in
             ('SHIP & PARTS', 'PILOT LEADERBOARD', 'CONTRACT EXCHANGE', 'TRADE NETWORK', 'FLIGHT UPGRADES')]
    archive = _one(actors, 'Refine/Archive/Identity')
    staff_light = _one(actors, 'Refine/Reception/Staff light')
    light = staff_light.get_component_by_class(u.PointLightComponent)
    if not light or math.dist(staff_light.get_actor_location().to_tuple(), (4100, 0, 355)) > .1:
        raise RuntimeError('Inspected reception lamp changed; review before moving')
    for a in faces + [archive]:
        if not a.get_component_by_class(u.TextRenderComponent):
            raise RuntimeError('Existing label is no longer native text: ' + a.get_actor_label())
    poses = {a: _pose(a) for a in actors}
    appearances = {a: _appearance(a, u) for a in actors}
    # No source asset is authored. Hash the exact native planter assembly and
    # its resident mesh/material packages before any furnishing is placed.
    source_paths = {PLANT, GRAPHITE, PEARL}
    original_plant = _one(actors, 'Refine/Social/Planter 0')
    for c in original_plant.get_components_by_class(u.StaticMeshComponent):
        if c.static_mesh:
            source_paths.add(c.static_mesh.get_path_name().split('.')[0])
        source_paths.update(m.get_path_name().split('.')[0] for m in c.get_materials() if m)
    files = {p: root / ('Content/' + p[6:] + '.uasset') for p in source_paths if p.startswith('/Game/')}
    hashes = {p: _sha(f) for p, f in files.items()}
    before_routes = _routes(world, u)
    for name, (x, y) in PLANTS:
        floor = _hit(u.SystemLibrary.line_trace_single_by_profile(world, u.Vector(x, y, 35),
            u.Vector(x, y, -65), 'Pawn', False, [], u.DrawDebugTrace.NONE, True))
        obstruction = _hit(u.SystemLibrary.capsule_trace_single_by_profile(world,
            u.Vector(x, y, 78), u.Vector(x, y, 78.1), 60., 75., 'Pawn', False, [], u.DrawDebugTrace.NONE, True))
        if not floor or abs(floor['point'][2]) > 5 or floor['normal'][2] < .7 or obstruction:
            raise RuntimeError('Planter is not on clear existing floor: ' + name)

    mounted = []
    for name, pod, sign in DESKS:
        base = _one(actors, 'OperationsNative/Command island ' + pod + '/SM_TitaniumIndustryStation_V1_Part1')
        c, e = mesh_union(base)
        # The native desk's 137cm top has an inner front face at this Y bound.
        center = (c.x, c.y + sign * (e.y + 2), 116)
        mounted.append(_mount(ctx, _one(actors, 'Services/' + name + '/Face'), center,
                              (0, sign), min(200, 2 * e.x - 12), 30, u))
    base = _one(actors, 'Engineering/Primary workstation/SM_GoliathTable02_Clean')
    c, e = mesh_union(base)
    mounted.append(_mount(ctx, _one(actors, 'Services/FLIGHT UPGRADES/Face'),
                          (c.x - e.x - 2, c.y, 98), (-1, 0), min(186, 2 * e.y - 10), 26, u))
    wall = _one(actors, 'Lounge/Bay N3/Panel 200')
    c, e = mesh_union(wall)
    archive_text = archive.get_component_by_class(u.TextRenderComponent)
    archive_before = str(archive_text.get_editor_property('text'))
    if archive_before != 'CREW ARCHIVE  /  WARDROBE':
        raise RuntimeError('Archive heading semantics changed since the reviewed view')
    archive_text.set_text('CREW ARCHIVE<br>WARDROBE')
    ctx.records.append({'kind': 'archive_heading_line_wrap', 'before': archive_before,
                        'after': 'CREW ARCHIVE<br>WARDROBE', 'words_preserved': True})
    mounted.append(_mount(ctx, archive, (c.x, c.y - e.y - 2, 350), (0, -1), 340, 75, u))

    plants = []
    for name, xy in PLANTS:
        actor = ctx.grounded('ServiceFinish/Planter ' + name, PLANT, xy,
                             scale=(2.765208, 2.765208, 2.765208), collision=True)
        c, e = mesh_union(actor)
        if abs(2 * e.z - 120) > .1 or math.hypot(e.x, e.y) > 60:
            raise RuntimeError('Native planter proportions exceed the inspected clear footprint')
        plants.append({'actor': actor.get_actor_label(), 'center': list(c.to_tuple()), 'extent': list(e.to_tuple())})
    # Sub-centimetre, non-colliding inlays define the Goliath work cell while
    # leaving the measured service approaches and both circuit lanes untouched.
    for y in (-300, 300):
        ctx.box('ServiceFinish/Operations workcell edge ' + str(y), (7890, y, .35),
                (520, 4, .7), PEARL, False)
        for x in (7630, 8150):
            ctx.box('ServiceFinish/Operations workcell return %s %s' % (x, y), (x, y * .8, .35),
                    (4, 120, .7), PEARL, False)
    before_light = {k: str(light.get_editor_property(k)) for k in
                    ('intensity', 'attenuation_radius', 'light_color', 'specular_scale', 'volumetric_scattering_intensity')}
    ctx.move(staff_light, (3840, 0, 235))
    light.set_intensity_units(u.LightUnits.LUMENS)
    light.set_intensity(1100.)
    light.set_attenuation_radius(450.)
    light.set_light_color(u.LinearColor(1., .88, .74, 1.))
    light.set_editor_property('specular_scale', .15)
    light.set_volumetric_scattering_intensity(0.)
    ctx.records.append({'kind': 'reception_front_counter_light', 'before': before_light,
                        'after': {'position': [3840, 0, 235], 'lumens': 1100, 'radius_cm': 450,
                                  'specular_scale': .15, 'volumetric': 0, 'new_shadow_casters': 0}})
    after_routes = _routes(world, u)
    changed = set(faces + [archive, staff_light])
    for actor, before in poses.items():
        if actor not in changed and _pose(actor) != before:
            raise RuntimeError('Unrelated owner pose changed: ' + actor.get_actor_label())
        if _appearance(actor, u) != appearances[actor]:
            raise RuntimeError('Existing geometry/material/collision changed: ' + actor.get_actor_label())
    if _sha(map_file) != map_sha or any(_sha(files[p]) != digest for p, digest in hashes.items()):
        raise RuntimeError('Service finish must not save or change source packages')
    marker.tags = list(marker.tags) + [TAG]
    return {'module': 'service_finish', 'basis': basis, 'dirty_assets': [], 'mounted_labels': mounted,
            'native_planters': plants, 'floor_inlays': 6, 'reception_lamp_new_casters': 0,
            'unrelated_actor_poses_preserved': len(poses) - len(changed), 'source_hashes_preserved': hashes,
            'routes_before': before_routes, 'routes_after': after_routes,
            'limits': 'Native placement/static route preservation only; final actual room views and owner approval remain required.'}
