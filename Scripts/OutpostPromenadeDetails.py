"""Connected native-kit arrival furnishings for the private outpost map.

Two open wayfinding gantries, a sheltered waiting pocket and a cargo service
counter give the broad plaza a human scale. No lights, new features, vendor
asset edits or gameplay changes. layout/audit are pure; build(api) is owned by
the integration lead. Native movement/render acceptance remains separate.
"""
import itertools
import json
import math
import os
from pathlib import Path

PREFIX = 'PromenadeKit/'
OWNER_TAG = 'OutpostPromenadeDetails'
TARGET_MAP = '/Game/OutpostSandbox/L_AsteroidOutpost'
P4 = '/P4_Genesis_Vol1/'
P5 = '/P5_FruitSeller/'
P3 = '/P3_ComputerStation/'
PROTECTED = {
    'Main promenade and ship approach': [-1800, -500, 0, 2600, 500, 350],
    'Courier rectangle with clearance': [-180, 370, 0, 1280, 730, 230],
    'North visitor bridge': [-1130, 1750, 0, -70, 2480, 250],
    'South visitor bridge': [-1130, -2480, 0, -70, -1750, 250],
    'Observation stairs': [2500, -4420, 0, 2900, -1700, 1130],
    'NorthCommerce source assembly': [-522, 805, 0, 1322, 2096, 650],
    'SouthBotany source assembly': [-1195, -2025, 0, -319, -1030, 650],
    'SouthMachinery source assembly': [416, -1942, 0, 1452, -1025, 650],
    'ArrivalProduce source assembly': [-1197, 714, 0, -886, 1015, 600],
    'ArrivalWeighing source assembly': [-210, -1029, 0, 49, -716, 600],
}
VENDOR_ROUTES = [
    ('NorthCommerce', (700, 0), (700, 780)),
    ('SouthBotany', (-650, 0), (-650, -870)),
    ('SouthMachinery', (920, 0), (920, -780)),
    ('ArrivalProduce', (-1050, 0), (-1050, 590)),
    ('ArrivalWeighing', (-80, 0), (-80, -600)),
]
NEW_ROUTES = [
    ('Waiting pocket', (2250, 0), (2250, 1230)),
    ('Waiting frontage', (2250, 1230), (1490, 1230)),
    ('Cargo approach', (2220, 0), (2220, -1300)),
]
NPC_POINTS = [(290, 1535), (790, 1700), (-530, -870), (1040, -780),
              (-1170, 590), (50, -600), (1850, -1100)]


def _rotate(point, yaw, roll=0):
    """UE yaw/roll convention; authored kit parts have zero pitch."""
    a, b = math.radians(yaw), math.radians(roll)
    x, y, z = point
    y, z = math.cos(b) * y + math.sin(b) * z, -math.sin(b) * y + math.cos(b) * z
    return [math.cos(a) * x - math.sin(a) * y, math.sin(a) * x + math.cos(a) * y, z]


def _overlap(a, b, tolerance=.02):
    return all(a[i] < b[i + 3] - tolerance and a[i + 3] > b[i] + tolerance for i in range(3))


def layout(catalog, interior_source=None):
    meshes = catalog['meshes'] if isinstance(catalog, dict) else catalog
    rows = []

    def get(name, pack=P4):
        found = [m for m in meshes if m['name'] == name and pack in m['asset']]
        if len(found) != 1:
            raise ValueError('Missing or ambiguous promenade asset: ' + name)
        return found[0]

    def put(group, name, mesh, center, scale=1., yaw=0., roll=0., solid=False,
            floor=False, support=None):
        rotation = [0., yaw, roll]
        offset = _rotate([v * scale for v in mesh['origin']], yaw, roll)
        corners = [_rotate([mesh['extent'][i] * signs[i] * scale for i in range(3)], yaw, roll)
                   for signs in itertools.product((-1, 1), repeat=3)]
        low = [center[i] + min(c[i] for c in corners) for i in range(3)]
        high = [center[i] + max(c[i] for c in corners) for i in range(3)]
        row = {'name': PREFIX + group + '/' + name, 'group': group, 'asset': mesh['asset'],
               'center': list(center), 'location': [center[i] - offset[i] for i in range(3)],
               'rotation': rotation, 'scale': [scale] * 3, 'bounds': low + high,
               'native_origin_cm': list(mesh['origin']),
               'native_dimensions_cm': [2 * v for v in mesh['extent']],
               'solid': solid, 'floor_supported': floor, 'support': support,
               'catalog_render_lod0_triangles': mesh['triangles']}
        rows.append(row)
        return row

    storage = get('SM_WallPanel200X100_V1_SmartStorageUnit')
    wall = get('SM_WallPanel400X200_V1_SmartStorageUnit')
    beam = get('SM_CeilingWallPanel400X60_V1')
    cable = get('SM_CornerWallFloor400X70_V3_ElectricalCableRouting')
    plinth = get('SM_CornerWallFloor400X70_V10_ElectricalEquipment')
    roof = get('SM_CeilingPanel400X200_V1')
    frame = get('SM_Window300X100_V1_Part1')
    glass = get('SM_Window300X100_V2_Part2_DigitalWindow')

    def sign(group, label, center, yaw, scale=1.):
        row = put(group, label + ' frame', frame, center, yaw=yaw, scale=scale)
        delta = _rotate([(glass['origin'][i] - frame['origin'][i]) * scale for i in range(3)], yaw)
        put(group, label + ' digital pane', glass,
            [center[i] + delta[i] for i in range(3)], yaw=yaw, scale=scale)
        # Same source pivot for frame and pane, never independently grounded.
        row['shared_pivot_assembly'] = label

    for group, x in (('Exchange gantry', -780.), ('Arrivals gantry', 1650.)):
        for side in (-1, 1):
            for level in range(2):
                put(group, 'Upright %s-%s' % (side, level), storage,
                    (x, side * 780, 100 + level * 200), yaw=180, roll=90,
                    solid=True, floor=level == 0)
        for index, y in enumerate((-600, -200, 200, 600)):
            put(group, 'Crosshead ' + str(index), beam, (x, y, 400), yaw=180)
            put(group, 'Connected cable cornice ' + str(index), cable, (x, y, 460), yaw=90)
        sign(group, 'Wayfinding', (x - 30, 0, 430), 180)

    group = 'Waiting pocket'
    for index, x in enumerate((1650, 2050)):
        put(group, 'Equipment base ' + str(index), plinth, (x, 1580, 30),
            solid=True, floor=True)
        put(group, 'Smart-storage back wall ' + str(index), wall, (x, 1580, 160),
            yaw=-90, solid=True, support=60.)
        put(group, 'Connected shelter roof ' + str(index), roof,
            (x, 1500, 260 + roof['extent'][2]), yaw=90, support=260.)
    sign(group, 'Waiting directory', (1900, 1544, 175), -90, .65)
    seat_parts = [get('SM_TitaniumIndustrySeat_V1_Part' + str(i), P3) for i in (1, 2, 3)]
    seat_scale = .70
    seat_bottom = min(m['origin'][2] - m['extent'][2] for m in seat_parts) * seat_scale
    for index, x in enumerate((1540, 1700, 2000, 2160)):
        for part, mesh in enumerate(seat_parts):
            offset = _rotate([v * seat_scale for v in mesh['origin']], 180)
            put(group, 'Complete waiting seat %s part %s' % (index, part + 1), mesh,
                (x + offset[0], 1410 + offset[1], offset[2] - seat_bottom),
                scale=seat_scale, yaw=180, solid=part < 2, floor=part == 0)

    group = 'Cargo service pocket'
    put(group, 'Equipment base', plinth, (2200, -1760, 30), solid=True, floor=True)
    put(group, 'Smart-storage back wall', wall, (2200, -1760, 160),
        yaw=90, solid=True, support=60.)
    put(group, 'Connected service roof', roof, (2200, -1680, 260 + roof['extent'][2]),
        yaw=90, support=260.)
    sign(group, 'Cargo directory', (2200, -1725, 195), 90, .6)

    # Reuse a COMPLETE thirteen-part authored console (including its chair,
    # screen layers, controls and bottle), not the visibly hollow body alone.
    source_path = Path(interior_source) if interior_source else Path(__file__).with_name('OutpostInteriorAssemblies.json')
    source = json.loads(source_path.read_text(encoding='utf-8'))
    selected = [r for r in source['actors'] if r['name'] in source['console_names']]
    bottom = min(r['bounds_min'][2] for r in selected)
    pivot = [source['console_anchor'][0], source['console_anchor'][1], bottom]
    target, yaw = (2170, -1660, 0), 180
    for record in selected:
        delta = _rotate([record['location'][i] - pivot[i] for i in range(3)], yaw)
        corners = [_rotate([p[i] - pivot[i] for i in range(3)], yaw)
                   for p in itertools.product(*zip(record['bounds_min'], record['bounds_max']))]
        low = [min(p[i] for p in corners) + target[i] for i in range(3)]
        high = [max(p[i] for p in corners) + target[i] for i in range(3)]
        rotation = list(record['rotation']); rotation[1] += yaw
        solid = any(n in record['asset'] for n in ('IndustryStation_V1_Part1', 'IndustrySeat_V1_Part1', 'IndustrySeat_V1_Part2'))
        rows.append({'name': PREFIX + group + '/Complete console/' + record['name'],
                     'group': group, 'asset': record['asset'],
                     'location': [target[i] + delta[i] for i in range(3)],
                     'rotation': rotation, 'scale': list(record['scale']),
                     'bounds': low + high, 'materials': list(record['materials']),
                     'solid': solid, 'floor_supported': abs(low[2]) < .02,
                     'authored_assembly': 'P3 complete console with unchanged child transforms'})
    for index, (x, y, name, scale) in enumerate(((2370, -1560, 'SM_Props_Box03', 1.5),
             (2370, -1650, 'SM_Props_Box04', 1.8), (2370, -1820, 'SM_Props_Box03', 1.5))):
        mesh = get(name, P5)
        put(group, 'Delivery case ' + str(index), mesh, (x, y, mesh['extent'][2] * scale),
            scale=scale, solid=True, floor=True)
    return rows


def audit(rows):
    failures = []
    seen = set()
    exclusions = dict(PROTECTED)
    for name, start, end in VENDOR_ROUTES + NEW_ROUTES:
        exclusions[name + ' approach capsule'] = [min(start[0], end[0]) - 50,
            min(start[1], end[1]) - 50, 0, max(start[0], end[0]) + 50,
            max(start[1], end[1]) + 50, 230]
    for i, (x, y) in enumerate(NPC_POINTS):
        exclusions['NPC standing ' + str(i)] = [x - 80, y - 80, 0, x + 80, y + 80, 230]
    for row in rows:
        b = row['bounds']
        if row['name'] in seen:
            failures.append(row['name'] + ': duplicate label')
        seen.add(row['name'])
        if not all(math.isfinite(v) for v in b) or b[2] < -.03:
            failures.append(row['name'] + ': invalid or buried bounds')
        if b[0] < -1450 or b[3] > 2450 or b[1] < -2300 or b[4] > 2300:
            failures.append(row['name'] + ': outside bounded furnishing footprint')
        if row.get('floor_supported') and abs(b[2]) > .03:
            failures.append(row['name'] + ': floor contact missing')
        for name, excluded in exclusions.items():
            if _overlap(b, excluded):
                failures.append(row['name'] + ': enters ' + name)
    # Every group has grounded elements. Then grow a contact graph through the
    # native bounds. Separate chairs and delivery cases are their own anchors.
    # Complete source console retains tiny authored gaps between electronics.
    for group in sorted({r['group'] for r in rows}):
        members = [r for r in rows if r['group'] == group]
        connected = {i for i, r in enumerate(members) if r.get('floor_supported') or r.get('authored_assembly')}
        while True:
            previous = len(connected)
            connected.update(i for i, r in enumerate(members)
                             if any(_overlap(r['bounds'], members[j]['bounds'], -.6) for j in connected))
            if previous == len(connected):
                break
        failures.extend(r['name'] + ': not attached to a grounded group'
                        for i, r in enumerate(members) if i not in connected)
    return {'scope': 'Pure measured mesh bounds and selected protected routes. Not native collision or visual acceptance.',
            'parts': len(rows), 'unique_meshes': len({r['asset'] for r in rows}),
            'groups': {g: sum(r['group'] == g for r in rows) for g in sorted({r['group'] for r in rows})},
            'solid_parts': sum(r['solid'] for r in rows), 'new_lights': 0,
            'minimum_overhead_crossing_z': min(r['bounds'][2] for r in rows
                if r['bounds'][1] < 500 and r['bounds'][4] > -500),
            'protected_bounds': exclusions, 'violations': failures}


def audit_native(api):
    """Optional focused post-author trace checks; leave all physical props active."""
    import unreal as u
    from ValidateOutpostSandbox import _hit
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    package = world.get_path_name().split('.')[0]
    if package != TARGET_MAP and not (package.startswith('/Temp/Untitled') and api.get('TARGET') == TARGET_MAP):
        raise RuntimeError('Promenade trace audit is restricted to ' + TARGET_MAP)
    cls = u.load_class(None, '/Script/SpaceSurvival.SSWalker')
    capsule = u.get_default_object(cls).get_component_by_class(u.CapsuleComponent)
    radius, half = capsule.get_unscaled_capsule_radius(), capsule.get_unscaled_capsule_half_height()
    routes = [('Main ' + str(y), (-1300, y), (2200, y)) for y in (-350, 0, 350)]
    routes += VENDOR_ROUTES + NEW_ROUTES
    evidence = {'capsule_cm': [radius, half], 'routes': [], 'floors': [], 'failures': [],
                'scope': 'Three main lanes, five vendor approaches and three new pocket routes; no props ignored.'}
    for name, start, end in routes:
        hit = _hit(u.SystemLibrary.capsule_trace_single_by_profile(world,
            u.Vector(start[0], start[1], half + 3), u.Vector(end[0], end[1], half + 3),
            radius, half, 'Pawn', False, [], u.DrawDebugTrace.NONE, True))
        evidence['routes'].append({'name': name, 'hit': hit, 'ok': hit is None})
        if hit:
            evidence['failures'].append({'name': name, 'hit': hit})
        for point in (start, end):
            floor = _hit(u.SystemLibrary.line_trace_single_by_profile(world,
                u.Vector(point[0], point[1], 35), u.Vector(point[0], point[1], -65),
                'Pawn', False, [], u.DrawDebugTrace.NONE, True))
            ok = bool(floor and abs(floor['point'][2]) <= 5 and floor['normal'][2] >= .7)
            evidence['floors'].append({'xy': point, 'ok': ok, 'hit': floor})
            if not ok:
                evidence['failures'].append({'name': name + ' floor', 'hit': floor})
    (Path(api['OUT']) / 'promenade-native-audit.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    return evidence


def build(api):
    import unreal as u
    from OutpostGeometryUtils import mesh_union
    root, out = Path(api['ROOT']), Path(api['OUT'])
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    package = world.get_path_name().split('.')[0]
    blank = package.startswith('/Temp/Untitled') and api.get('TARGET') == TARGET_MAP
    if package != TARGET_MAP and not blank:
        raise RuntimeError('Promenade furnishings are restricted to ' + TARGET_MAP)
    catalog_path = os.environ.get('SS_PREFAB_CATALOG', str(root / 'Artifacts/PrefabLibrary/catalog.json'))
    rows = layout(json.loads(Path(catalog_path).read_text(encoding='utf-8')))
    evidence = audit(rows)
    if evidence['violations']:
        raise ValueError('; '.join(evidence['violations']))
    collision = {}
    for row in rows:
        mesh = api['load'](row['asset'])
        if row['solid'] and row['asset'] not in collision:
            body = mesh.get_editor_property('body_setup')
            agg = body.get_editor_property('agg_geom') if body else None
            count = sum(len(agg.get_editor_property(k)) for k in
                        ('box_elems', 'sphere_elems', 'sphyl_elems', 'convex_elems')) if agg else 0
            trace = str(body.get_editor_property('collision_trace_flag')) if body else 'None'
            collision[row['asset']] = {'simple_elements': count, 'trace_flag': trace}
            if not count and 'USE_COMPLEX_AS_SIMPLE' not in trace:
                raise ValueError('Native collidable furniture has no usable collision: ' + row['asset'])
    removed = 0
    for actor in api['EAS'].get_all_level_actors():
        if actor.get_actor_label().startswith(PREFIX) and OWNER_TAG in [str(t) for t in actor.tags]:
            api['EAS'].destroy_actor(actor); removed += 1
    native = []
    for row in rows:
        materials = [api['balanced'](api['load'](p)) if p else None for p in row['materials']] if 'materials' in row else None
        actor = api['raw'](row['name'], row['asset'], row['location'], rotation=row['rotation'],
                           scale=row['scale'], solid=row['solid'], materials=materials)
        api['tag'](actor, OWNER_TAG)
        api['tag'](actor, 'OutpostRole:PromenadeFurnishing')
        if row.get('floor_supported'):
            api['tag'](actor, 'OutpostRole:FloorProp'); api['tag'](actor, 'OutpostSupport:0')
        center, extent = mesh_union(actor)
        observed = [center.x - extent.x, center.y - extent.y, center.z - extent.z,
                    center.x + extent.x, center.y + extent.y, center.z + extent.z]
        error = max(abs(observed[i] - row['bounds'][i]) for i in range(6))
        native.append({'name': row['name'], 'maximum_bound_error_cm': error, 'ok': error <= 1.})
    for name, words, pos, yaw, size in [
        ('Exchange', 'EXCHANGE / MARKET', (-826, 0, 410), 180, 19),
        ('Arrivals', 'ARRIVALS / SERVICES', (1604, 0, 410), 180, 18),
        ('Waiting', 'TRANSIT / WAITING', (1900, 1526, 166), -90, 12),
        ('Cargo', 'CARGO / SERVICE', (2200, -1707, 186), 90, 12),
    ]:
        actor = api['text'](PREFIX + 'Wayfinding/' + name, words, pos, yaw, size=size)
        api['tag'](actor, OWNER_TAG)
    receipt = {'map': TARGET_MAP, 'placements': rows, 'audit': evidence,
               'removed_owned_actors': removed, 'native_bounds': native, 'collision_sources': collision,
               'signs': 4, 'new_lights': 0, 'vendor_assets_modified': False,
               'sources': ['Measured PrefabLibrary/catalog.json native mesh bounds',
                           'OutpostInteriorAssemblies.json complete thirteen-part P3 console'],
               'acceptance': 'Focused native walking, render and performance review still required.'}
    (out / 'promenade-details.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    if any(not r['ok'] for r in native):
        raise ValueError('Promenade native geometry differs from planned bounds; inspect receipt before saving')
    return receipt
