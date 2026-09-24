"""Bounded post-authoring probes for the market, globe and upper gallery.

Called by ValidateOutpostSandbox with its existing Pawn-profile trace wrappers.
Tests selected approaches and components, not every member of the vendor kit.
"""
import hashlib
import json
import math
from pathlib import Path

import unreal as u


def audit(actors, radius, half, line, sweep, root):
    report = {'floor_checks': [], 'clearance_checks': [], 'route_checks': [],
              'tangible_probes': [], 'globe_bounds': [], 'failures': [], 'deferred': [],
              'scope': 'Three promenade lanes, five vendor approaches, three tangible components, '
                       'globe standing space and upper gallery. Not an audit of all market actors.'}
    by_name = {actor.get_actor_label(): actor for actor in actors}

    def failure(kind, name, evidence):
        report['failures'].append({'kind': kind, 'name': name, 'evidence': evidence})

    def stand(name, feet):
        x, y, z = feet
        hit = line((x, y, z + 35), (x, y, z - 65))
        ok = bool(hit and abs(hit['point'][2] - z) <= 5 and hit['normal'][2] >= .7)
        row = {'name': name, 'feet': list(feet), 'ok': ok, 'hit': hit}
        report['floor_checks'].append(row)
        if not ok:
            failure('expansion_floor', name, row)
        hit = sweep((x, y, z + half + 3), (x, y, z + half + 4))
        report['clearance_checks'].append({'name': name, 'feet': list(feet), 'hit': hit, 'ok': hit is None})
        if hit:
            failure('expansion_standing_capsule', name, hit)

    def route(name, start, end):
        assert abs(start[2] - end[2]) < .01, 'This audit only sweeps level approaches'
        hit = sweep((start[0], start[1], start[2] + half + 3),
                    (end[0], end[1], end[2] + half + 3))
        report['route_checks'].append({'name': name, 'start_feet': start, 'end_feet': end,
                                       'ok': hit is None, 'hit': hit})
        if hit:
            failure('expansion_capsule_route', name, hit)
        count = max(1, math.ceil(math.dist(start, end) / 400))
        for i in range(count + 1):
            stand(name + ':' + str(i), [start[j] + (end[j] - start[j]) * i / count for j in range(3)])

    for y in (-350, 0, 350):
        route('Market promenade ' + str(y), [-1300, y, 0], [2200, y, 0])
    route('NorthCommerce approach', [700, 0, 0], [700, 780, 0])
    route('SouthBotany approach', [-650, 0, 0], [-650, -870, 0])
    route('SouthMachinery approach', [920, 0, 0], [920, -780, 0])
    route('ArrivalProduce approach', [-1050, 0, 0], [-1050, 590, 0])
    route('ArrivalWeighing approach', [-80, 0, 0], [-80, -600, 0])
    for x, y in ((4200, 0), (3900, 0), (4500, 0), (4200, -300), (4200, 300)):
        stand('Globe standing area', [x, y, 0])
    for x in (3150, 3500, 3850):
        for y in (-4050, -3400, -2750):
            stand('Observation gallery', [x, y, 520])
    route('Observation bridge', [2640, -3400, 520], [3500, -3400, 520])
    route('Observation viewing lane', [3500, -4050, 520], [3500, -2750, 520])

    # BEGIN bounded native interior expansion audit. No collision exclusions:
    # the supplied sweep retains all room fixtures, capsules and native furniture.
    # These samples cover intended public circulation, not decorative pod decks.
    from OutpostGeometryUtils import mesh_union
    from OutpostInteriorAssemblies import BANKS, HOLOGRAM_BAYS, source_layout
    report['scope'] += ' Native Operations banks and public interior circulation.'
    report['interior_bounds_checks'] = []
    source_rows = source_layout()
    for bank, _, _ in BANKS:
        prefix = 'OperationsNative/' + bank + '/'
        expected = [r for r in source_rows if r['name'].startswith(prefix)]
        expected_low = [min(r['bounds_min'][i] for r in expected) for i in range(3)]
        expected_high = [max(r['bounds_max'][i] for r in expected) for i in range(3)]
        low, high, missing = [float('inf')] * 3, [float('-inf')] * 3, []
        for row in expected:
            actor = by_name.get(row['name'])
            if actor is None:
                missing.append(row['name'])
                continue
            center, extent = mesh_union(actor)
            values, radii = (center.x, center.y, center.z), (extent.x, extent.y, extent.z)
            low = [min(low[i], values[i] - radii[i]) for i in range(3)]
            high = [max(high[i], values[i] + radii[i]) for i in range(3)]
        finite = all(math.isfinite(v) for v in low + high)
        error = max([abs(low[i] - expected_low[i]) for i in range(3)] +
                    [abs(high[i] - expected_high[i]) for i in range(3)]) if finite else None
        row = {'name': bank, 'missing_actors': missing,
               'expected_bounds': [expected_low, expected_high],
               'actual_geometry_bounds': [low, high] if finite else None,
               'maximum_bound_error_cm': error,
               'ok': not missing and error is not None and error <= 1.0,
               'meaning': 'Native transformed geometry only; visibility and appearance need captures.'}
        report['interior_bounds_checks'].append(row)
        if not row['ok']:
            failure('interior_native_transform', bank, row)

    interior_routes = [
        ('Operations central aisle', [6600, 0, 0], [8590, 0, 0]),
        ('Operations north crossover', [6860, 0, 0], [6860, 560, 0]),
        ('Operations south crossover', [6860, 0, 0], [6860, -560, 0]),
        ('Operations north equipment frontage', [6860, 560, 0], [8590, 560, 0]),
        ('Operations south equipment frontage', [6860, -620, 0], [8490, -620, 0]),
        ('Operations east service aisle', [8510, -620, 0], [8510, 560, 0]),
        ('Operations contract approach', [8510, -620, 0], [8460, -560, 0]),
        ('Operations trade approach', [8510, 560, 0], [8460, 560, 0]),
        ('Operations leaderboard approach', [7700, 460, 0], [7700, 525, 0]),
        ('Lounge entry promenade', [4200, 2550, 0], [4200, 3380, 0]),
        ('Lounge south conversation approach', [4200, 2800, 0], [3710, 2800, 0]),
        ('Lounge conversation circulation', [3710, 2800, 0], [3710, 3970, 0]),
        ('Lounge capsule gallery approach', [4200, 3360, 0], [5100, 3360, 0]),
        ('Lounge capsule gallery lane', [5100, 2750, 0], [5100, 4080, 0]),
        ('Lounge wardrobe approach', [4750, 3300, 0], [4750, 3430, 0]),
    ]
    for name, start, end in interior_routes:
        route(name, start, end)
    for index, (_, y, _) in enumerate(HOLOGRAM_BAYS):
        stand('Lounge capsule front ' + str(index + 1), [5100, y, 0])
    # END bounded native interior expansion audit.

    # Check the actual rendered globe bounds, not only its recipe diameter.
    globes = [a for a in actors if a.get_actor_label().startswith('Atrium/Planetary archive/')]
    if len(globes) != 1:
        failure('globe_presence', 'Planetary archive', {'expected_layers': 1, 'observed': len(globes)})
    for actor in globes:
        components = actor.get_components_by_class(u.StaticMeshComponent)
        for component in components:
            origin, extent, _ = u.SystemLibrary.get_component_bounds(component)
            bottom = origin.z - extent.z
            ok = bottom >= 2 * half + 20
            row = {'actor': actor.get_actor_label(), 'bottom_z': bottom,
                   'standing_height': 2 * half, 'ok': ok}
            report['globe_bounds'].append(row)
            if not ok:
                failure('globe_visual_headroom', actor.get_actor_label(), row)

    # Each ray isolates the target actor so another prop, the station floor or
    # an invisible wall cannot masquerade as collision on the selected kit part.
    targets = [('NorthCommerce', 'BP_ISM_Storage12', 'InstancedStaticMesh5'),
               ('SouthBotany', 'BP_ISM_Storage12', 'InstancedStaticMesh5'),
               ('NorthCommerce', 'BP_ISM_Structure_V4', 'ISM_Building_StructureBase_V1')]
    for block, suffix, component_name in targets:
        name = 'MarketNative/' + block + '/' + suffix
        actor = by_name.get(name)
        if actor is None:
            failure('tangible_actor_missing', name, component_name)
            continue
        components = {c.get_name(): c for c in actor.get_components_by_class(u.StaticMeshComponent)}
        component = components.get(component_name)
        if component is None or component.static_mesh is None:
            failure('tangible_component_missing', name, component_name)
            continue
        if not isinstance(component, u.InstancedStaticMeshComponent) or component.get_instance_count() < 1:
            failure('tangible_instance_missing', name, component_name)
            continue
        transform = component.get_instance_transform(0, world_space=True)
        bounds = component.static_mesh.get_bounds()
        isolated = [other for other in actors if other != actor]
        rays = []
        for axis in range(3):
            origin = [bounds.origin.x, bounds.origin.y, bounds.origin.z]
            extent = [bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z]
            start, end = list(origin), list(origin)
            start[axis] -= extent[axis] + 10
            end[axis] += extent[axis] + 10
            start = u.MathLibrary.transform_location(transform, u.Vector(*start))
            end = u.MathLibrary.transform_location(transform, u.Vector(*end))
            hit = line((start.x, start.y, start.z), (end.x, end.y, end.z), isolated)
            rays.append({'local_axis': axis, 'hit': hit})
        component_hits = [r for r in rays if r['hit'] and r['hit']['actor'] == name
                          and r['hit']['component'] == component_name]
        row = {'actor': name, 'component': component_name, 'instance': 0,
               'asset': component.static_mesh.get_path_name(), 'rays': rays,
               'ok': bool(component_hits)}
        report['tangible_probes'].append(row)
        if not row['ok']:
            failure('selected_tangible_component_unproven', name, row)

    receipt = Path(root) / 'Artifacts/Outpost/market.json'
    if receipt.exists():
        encoded = receipt.read_bytes()
        data = json.loads(encoded)
        collision = data.get('structural_collision', {})
        report['market_receipt'] = {
            'path': str(receipt), 'sha256': hashlib.sha256(encoded).hexdigest(),
            'authored_actors': sum(len(b['actors']) for b in data.get('blocks', [])),
            'observed_market_actors': sum(n.startswith('MarketNative/') for n in by_name),
            'structural_meshes': len(collision),
            'collision_attention': data.get('collision_attention', []),
            'meaning': 'Native collision metadata supports the focused probes; it does not prove every placement.'}
        if data.get('collision_attention'):
            report['deferred'].append({'kind': 'native_market_collision_review',
                                       'assets': data['collision_attention']})
    else:
        report['deferred'].append({'kind': 'market_receipt_missing', 'path': str(receipt)})
    report['status'] = 'FAIL' if report['failures'] else 'PARTIAL' if report['deferred'] else 'PASS_FOCUSED_EDITOR_ONLY'
    return report
