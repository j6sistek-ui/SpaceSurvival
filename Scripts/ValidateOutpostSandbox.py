"""Read-only author-time collision/placement audit of the private outpost map.

Call run(output_path=...) with the sandbox loaded and Play stopped. No map, door,
collision or visibility mutation occurs. Runtime movement still needs Play review.
"""
import datetime
import json
import math
from pathlib import Path

import unreal as u

TARGET = '/Game/OutpostSandbox/L_AsteroidOutpost'
ROOMS = {'Atrium': (4200, 0), 'Engineering': (4200, -3400),
         'Lounge': (4200, 3400), 'Operations': (7800, 0)}
ROUTES = {
    'arrival': [(-1800, 0), (1000, 0), (2200, 0), (2900, 0), (4200, 0)],
    'engineering': [(4200, 0), (4200, -1750), (4200, -2650), (4200, -2770), (4200, -2830)],
    'lounge': [(4200, 0), (4200, 1750), (4200, 2650), (4200, 3400)],
    'operations': [(4200, 0), (5900, 0), (6900, 0), (7800, 0)],
}
# The central Goliath desk intentionally occupies the old room-centre sample.
# Check its public approach and side aisles instead; colliders stay active.
ROOM_FLOOR_SAMPLES = {
    'Engineering': [(4200, -2770), (3900, -2770), (4500, -2770),
                    (3800, -3000), (4600, -3000)],
}
DOORS = {'Entrance': ((2600, 0), (1, 0)), 'Engineering': ((4200, -2300), (0, 1)),
         'Lounge': ((4200, 2300), (0, 1)), 'Operations': ((6400, 0), (1, 0))}


def _tags(actor):
    return {str(t).split(':', 1)[0]: str(t).split(':', 1)[1]
            for t in actor.tags if ':' in str(t)}


def _point(v):
    return [round(float(v.x), 3), round(float(v.y), 3), round(float(v.z), 3)]


def _hit(result):
    if result is None:
        return None
    fields = result.to_tuple()
    if not fields[0]:
        return None
    actor, component = fields[9], fields[10]
    return {'actor': actor.get_actor_label() if actor else None,
            'component': component.get_name() if component else None,
            'point': _point(fields[5]), 'normal': _point(fields[7]),
            'initial_overlap': bool(fields[1]),
            'role': _tags(actor).get('OutpostRole', '') if actor else ''}

def run(output_path=None, routes_path=None, include_expansion=True):
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    world = editor.get_editor_world()
    assert world and world.get_path_name().split('.')[0] == TARGET, 'Wrong map; audit did not run'
    assert not editor.get_game_world(), 'Stop Play before author-time audit'
    # Fresh loads can leave static-mesh/ISM collision compilation pending.
    # The engine barrier flushes asset loads and FinishAllCompilation before
    # the first trace; do not repair flags or retry until a failing probe passes.
    u.AutomationLibrary.finish_loading_before_screenshot()
    actors = list(u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors())
    routes = ROUTES
    if routes_path:
        routes = json.loads(Path(routes_path).read_text(encoding='utf-8'))['routes']
    cls = u.load_class(None, '/Script/SpaceSurvival.SSWalker')
    assert cls, 'Production walker unavailable; capsule dimensions unverified'
    capsule = u.get_default_object(cls).get_component_by_class(u.CapsuleComponent)
    radius, half = capsule.get_unscaled_capsule_radius(), capsule.get_unscaled_capsule_half_height()
    channel = 'Pawn'
    leaves = [a for a in actors if _tags(a).get('OutpostRole') == 'DoorLeaf']
    report = {'map': TARGET, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status': 'INCOMPLETE', 'capsule_cm': {'radius': radius, 'half_height': half},
              'ignored_door_leaves': [a.get_actor_label() for a in leaves],
              'floor_checks': [], 'clearance_checks': [], 'route_checks': [],
              'door_checks': [], 'grounding_checks': [], 'decorative_collision': [],
              'failures': [], 'deferred': [],
              'limits': ['Editor geometry only; no natural walking or physical input claim.',
                         'Door motion, NPC motion and runtime spawned blockers need Play validation.',
                         'Only FloorProp-tagged actors receive grounding checks.',
                         'Support tags check mesh bounds, not internal support geometry.']}

    def line(start, end, ignore=None):
        return _hit(u.SystemLibrary.line_trace_single_by_profile(world, u.Vector(*start), u.Vector(*end),
                    channel, False, ignore or [], u.DrawDebugTrace.NONE, True))

    def sweep(start, end):
        return _hit(u.SystemLibrary.capsule_trace_single_by_profile(world, u.Vector(*start), u.Vector(*end),
                    radius, half, channel, False, leaves, u.DrawDebugTrace.NONE, True))

    def failure(kind, name, evidence):
        report['failures'].append({'kind': kind, 'name': name, 'evidence': evidence})

    # Bounded samples every <=400cm plus five public standing points per room.
    samples = {}
    for name, route in routes.items():
        for a, b in zip(route, route[1:]):
            count = max(1, math.ceil(math.dist(a[:2], b[:2]) / 400))
            for step in range(count + 1):
                x, y = (a[i] + (b[i] - a[i]) * step / count for i in range(2))
                samples[(round(x, 2), round(y, 2))] = name
    for name, (x, y) in ROOMS.items():
        points = ROOM_FLOOR_SAMPLES.get(name, [(x + dx, y + dy) for dx, dy in
                                               ((0, 0), (300, 0), (-300, 0), (0, 300), (0, -300))])
        for point in points:
            samples[point] = name
    for (x, y), name in samples.items():
        hit = line((x, y, 45), (x, y, -80))
        ok = bool(hit and abs(hit['point'][2]) <= 5 and hit['normal'][2] >= .7)
        report['floor_checks'].append({'area': name, 'xy': [x, y], 'ok': ok, 'hit': hit})
        if not ok:
            failure('floor', name, {'xy': [x, y], 'hit': hit})
        roof = line((x, y, 10), (x, y, half * 2 + 8), leaves)
        report['clearance_checks'].append({'area': name, 'xy': [x, y], 'ok': roof is None, 'hit': roof})
        if roof:
            failure('head_clearance', name, {'xy': [x, y], 'hit': roof})

    def passage(name, a, b, bucket):
        start, end = (a[0], a[1], half + 3), (b[0], b[1], half + 3)
        hit = sweep(start, end)
        expected_door = hit and ('door' in hit['role'].lower())
        status = 'CLEAR' if hit is None else ('CLOSED_DOOR_UNVERIFIED' if expected_door else 'BLOCKED')
        report[bucket].append({'name': name, 'start': list(start), 'end': list(end),
                               'status': status, 'hit': hit})
        if expected_door:
            report['deferred'].append({'kind': 'door_open_passage', 'name': name, 'hit': hit})
        elif hit:
            failure('capsule_sweep', name, hit)
    for name, route in routes.items():
        for index, (a, b) in enumerate(zip(route, route[1:])):
            passage(name + ':' + str(index), a, b, 'route_checks')
    for name, ((x, y), (nx, ny)) in DOORS.items():
        passage(name, (x - nx * 170, y - ny * 170), (x + nx * 170, y + ny * 170), 'door_checks')

    for actor in actors:
        tags = _tags(actor)
        role = tags.get('OutpostRole', '')
        if role == 'FloorProp':
            support = tags.get('OutpostSupport')
            meshes = actor.get_components_by_class(u.MeshComponent)
            if support is None or not meshes:
                failure('grounding_metadata', actor.get_actor_label(), 'Missing support tag or mesh')
                continue
            bounds = [u.SystemLibrary.get_component_bounds(c) for c in meshes]
            bottom = min(origin.z - extent.z for origin, extent, _ in bounds)
            delta = bottom - float(support)
            row = {'actor': actor.get_actor_label(), 'bottom_z': round(bottom, 3),
                   'support_z': float(support), 'gap_cm': round(delta, 3), 'ok': abs(delta) <= 2}
            report['grounding_checks'].append(row)
            if not row['ok']:
                failure('floor_prop_grounding', actor.get_actor_label(), row)
        if role.lower() in ('hologram', 'sky', 'decorativehologram'):
            bad = [c.get_name() for c in actor.get_components_by_class(u.PrimitiveComponent)
                   if c.get_collision_enabled() != u.CollisionEnabled.NO_COLLISION]
            row = {'actor': actor.get_actor_label(), 'role': role, 'blocking_components': bad}
            report['decorative_collision'].append(row)
            if bad:
                failure('decorative_collision', actor.get_actor_label(), bad)
    if not report['grounding_checks']:
        report['deferred'].append({'kind': 'grounding', 'reason': 'No tagged floor props available'})
    if include_expansion:
        from ValidateOutpostMarket import audit
        root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
        focused = audit(actors, radius, half, line, sweep, root)
        report['market_globe_gallery'] = focused
        report['failures'].extend(focused['failures'])
        report['deferred'].extend(focused['deferred'])
    if report['failures']:
        report['status'] = 'FAIL'
    elif report['deferred']:
        report['status'] = 'PARTIAL'
    else:
        report['status'] = 'PASS_AUTHOR_TIME_ONLY'
    if output_path is None:
        root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
        output_path = root / 'Artifacts/OutpostSandbox/placement-audit.json'
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'status': report['status'], 'failures': len(report['failures']),
                      'deferred': len(report['deferred']), 'receipt': str(destination)}))
    return report
