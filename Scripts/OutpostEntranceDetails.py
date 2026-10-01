"""Native P4/P5 cladding for the existing outpost entrance, not a new facade.

The two structural piers remain centred at (2460,+/-430,360), and the crown
at (2460,0,740). All additions are noncolliding; existing doorway, structural
collision, canopy, name sign and light blades remain authoritative.
layout()/audit() are pure Python. build(api) is called by the integration lead.
"""
import itertools
import json
import math
import os
from pathlib import Path

PREFIX = 'EntranceKit/'
OWNER_TAG = 'OutpostEntranceDetails'
TARGET_MAP = '/Game/OutpostSandbox/L_AsteroidOutpost'
P4 = '/P4_Genesis_Vol1/'
P5 = '/P5_FruitSeller/'
THRESHOLD_LIGHT_POSITION = (2455., 0., 410.5)


def _rotate(point, rotation):
    """UE Rotator yaw/roll convention; every authored pitch is zero.

Matches RotationTranslationMatrix.h: positive roll maps local Y toward -Z.
"""
    pitch, yaw, roll = rotation
    if pitch != 0:
        raise ValueError('Entrance detail layout supports zero pitch only')
    a, b = math.radians(yaw), math.radians(roll)
    x, y, z = point
    y, z = math.cos(b) * y + math.sin(b) * z, -math.sin(b) * y + math.cos(b) * z
    return [math.cos(a) * x - math.sin(a) * y,
            math.sin(a) * x + math.cos(a) * y, z]


def layout(catalog):
    meshes = catalog['meshes'] if isinstance(catalog, dict) else catalog
    rows = []

    def get(name, pack=P4):
        found = [m for m in meshes if m['name'] == name and pack in m['asset']]
        if len(found) != 1:
            raise ValueError('Missing or ambiguous entrance asset: ' + name)
        return found[0]

    def put(name, mesh, center, scale=1., yaw=0., roll=0., anchor='Portal pier'):
        rotation = [0., yaw, roll]
        offset = _rotate([v * scale for v in mesh['origin']], rotation)
        location = [center[i] - offset[i] for i in range(3)]
        corners = [_rotate([mesh['extent'][i] * sign[i] * scale for i in range(3)], rotation)
                   for sign in itertools.product((-1, 1), repeat=3)]
        row = {'name': PREFIX + name, 'asset': mesh['asset'], 'center': list(center),
               'location': location, 'rotation': rotation, 'scale': [scale] * 3,
               'native_origin_cm': list(mesh['origin']),
               'native_dimensions_cm': [v * 2 for v in mesh['extent']],
               'bounds_min': [center[i] + min(c[i] for c in corners) for i in range(3)],
               'bounds_max': [center[i] + max(c[i] for c in corners) for i in range(3)],
               'mount': anchor, 'solid': False}
        rows.append(row)
        return row

    storage = get('SM_WallPanel200X100_V1_SmartStorageUnit')
    foot = get('SM_CornerWallFloor100X70_V4_ElectricalEquipment')
    cap = get('SM_CornerWallCeiling200X70_V4_ElectricalEquipment')
    edge = get('SM_OutCornerWall10X10_V1')
    cornice = get('SM_CeilingWallPanel400X20_V1')
    conduit = get('SM_CornerWallCeiling400X70_V2_ElectricalCableRouting')
    strut = get('SM_Building_Structure200x10_V1', P5)
    strut_base = get('SM_Building_StructureBase_V1', P5)
    bracket = get('SM_Building_AngleStructureLink_V1', P5)
    holo_frame = get('SM_Window200X100_V1_Part1')
    holo_glass = get('SM_Window200X100_V2_Part2_DigitalWindow')
    header = get('SM_WallPanel400X100_V1_SmartStorageUnit')
    upper_wall = get('SM_WallPanel400X200_V1_SmartStorageUnit')

    for side, name in ((-1, 'South'), (1, 'North')):
        y = side * 430
        # A 90-degree roll turns the native 200x100 panel into a 100x200
        # vertical inset. Its back overlaps the pier, leaving the original cyan
        # blade at X2310 in front. No flattened or stretched storage geometry.
        for index, z in enumerate((170, 370, 570)):
            put(name + '/Front inset ' + str(index), storage, (2360, y, z),
                yaw=180, roll=90)
        for index, z in enumerate((140, 360, 580)):
            put(name + '/Outer equipment bay ' + str(index), storage,
                (2460, side * 493, z), yaw=side * 90)
        put(name + '/Grounded equipment plinth', foot, (2325, y, 39),
            scale=1.3, yaw=90, anchor='Floor and portal pier')
        put(name + '/Pier capital', cap, (2325, y, 700.5), scale=.65, yaw=90)
        # Four native edge pieces per corner make continuous 0..800cm ribs.
        # The top section joins the pier to the crown rather than ending in air.
        for edge_y in (y - 56, y + 56):
            for index, z in enumerate((100, 300, 500, 700)):
                put(name + '/Front edge ' + str(int(edge_y)) + '/' + str(index),
                    edge, (2347, edge_y, z), yaw=180)

        # Matched frame/digital-glass layers preserve the source shared pivot.
        # Mounted on the outer equipment bay, away from the central lane and
        # existing WAYFARER name sign. Native animated screen materials remain.
        center, scale, yaw = (2460, side * 524, 348), .65, side * 90
        put(name + '/Holo directory frame', holo_frame, center,
            scale=scale, yaw=yaw, anchor='Outer equipment bay')
        local_delta = [(holo_glass['origin'][i] - holo_frame['origin'][i]) * scale for i in range(3)]
        delta = _rotate(local_delta, [0, yaw, 0])
        glass_center = [center[i] + delta[i] for i in range(3)]
        put(name + '/Holo directory glass', holo_glass, glass_center,
            scale=scale, yaw=yaw, anchor='Matched directory frame')

        # Two short utility bridges enter the atrium roof. Pipes overlap the
        # crown at X2560..2600 and sit on braced feet at the rear, never floating.
        put(name + '/Crown to atrium conduit', conduit, (2680, y, 792),
            scale=.6, anchor='Crown and atrium roof strut')
        put(name + '/Atrium roof strut', strut, (2790, y, 750),
            scale=.6, anchor='Atrium roof Z750')
        put(name + '/Atrium roof foot', strut_base, (2790, y, 757.5),
            scale=.35, anchor='Atrium roof Z750')
        put(name + '/Utility bridge bracket', bracket, (2758, y, 775),
            scale=.9, yaw=180, anchor='Conduit and roof strut')

    # Four authored-width crown insets plus thin upper/lower cornices retain
    # the existing1050cm silhouette. The kit carries the surface richness.
    for index, y in enumerate((-390, -130, 130, 390)):
        put('Crown/Equipment fascia ' + str(index), storage, (2330, y, 740),
            scale=1.3, yaw=180, anchor='Existing crown')
    for name, z in (('Upper', 811), ('Lower', 668)):
        for index, y in enumerate((-350, 0, 350)):
            put('Crown/' + name + ' cornice ' + str(index), cornice, (2325, y, z),
                scale=.875, yaw=180, anchor='Existing crown edge')

    # Capture8 showed a small native door stranded in a blank black surround.
    # Clad the EXISTING100cm header and120cm side infills. Their collision is
    # unchanged; the central320cm-wide/302cm-high passage remains untouched.
    put('Door surround/Header', header, (2554, 0, 352), yaw=180,
        anchor='Existing door header')
    for side in (-1, 1):
        for index, z in enumerate((100, 300)):
            put('Door surround/Infill %d %d' % (side, index), storage,
                (2554, side * 260, z), yaw=180, roll=90,
                anchor='Existing door infill')

    # Capture10 exposed the atrium's plain collar and open dark band above the
    # smaller native doorway. Build a continuous800x300cm upper facade from
    # full-size kit panels: bottom touches the existing400cm-high surround,
    # outer edges join the portal piers and top overlaps the crown at670cm.
    # No panel extends belowZ400; the actual320x302cm door stays untouched.
    for side in (-1, 1):
        put('Upper facade/Storage infill ' + str(side), upper_wall,
            (2554, side * 200, 500), yaw=180, anchor='Upper facade band')
        put('Upper facade/Crown transition ' + str(side), header,
            (2554, side * 200, 650), yaw=180, anchor='Upper facade band')
        for index, z in enumerate((500, 700)):
            put('Upper facade/Outer seam %s %s' % (side, index), edge,
                (2522, side * 400, z), yaw=180, anchor='Upper facade band')
        put('Upper facade/Service rail ' + str(side), cornice,
            (2510, side * 200, 600), yaw=180, anchor='Upper facade band')
    # A short central mullion starts above the complete inspection fixture.
    # Its native200cm length ties both facade panels to the service rail.
    put('Upper facade/Central seam', edge, (2522, 0, 550), yaw=180,
        anchor='Upper facade band')

    # Complete three-part native fixture, shared source pivot. The housing's
    # Y=-40cm back plane becomesX2530 after scale/yaw and touches the cladding.
    # A restrained local wash makes the actual doorway the visual destination.
    pivot, scale, yaw = (2500., 0., 415.), .75, 90
    for index, mesh_name in enumerate(('SM_CornerWallCeiling400X70_V6_Lights_Part1',
                                      'SM_CornerWallCeiling400X70_V6V7V8_Lights_Part2',
                                      'SM_CornerWallCeiling400X70_V6V7V8_Lights_Part3')):
        mesh = get(mesh_name)
        offset = _rotate([v * scale for v in mesh['origin']], [0, yaw, 0])
        row = put('Door surround/Inspection fixture part ' + str(index + 1), mesh,
                  [pivot[i] + offset[i] for i in range(3)], scale=scale, yaw=yaw,
                  anchor='Native inspection fixture on existing header')
        if index == 2:
            row['inspection_lens'] = True
    return rows


def audit(rows):
    violations = []
    names = set()
    for row in rows:
        if row['name'] in names:
            violations.append(row['name'] + ': duplicate label')
        names.add(row['name'])
        lo, hi = row['bounds_min'], row['bounds_max']
        door_infill = row['mount'] in ('Existing door header', 'Existing door infill')
        if door_infill:
            if lo[1] < 160 and hi[1] > -160 and lo[2] < 301.95 and hi[2] > 0:
                violations.append(row['name'] + ': intrudes into actual320cm main door passage')
        elif (lo[0] < 2800 and hi[0] > 1800 and lo[1] < 330 and hi[1] > -330
              and lo[2] < 350 and hi[2] > 0):
            violations.append(row['name'] + ': intrudes into660cm-wide protected entrance lane')
        if row['solid'] or len(set(row['scale'])) != 1:
            violations.append(row['name'] + ': must remain decorative and uniformly scaled')
        if lo[2] < -.01:
            violations.append(row['name'] + ': below floor')
        if not all(math.isfinite(v) for v in lo + hi):
            violations.append(row['name'] + ': invalid bounds')
        if row['mount'] == 'Upper facade band':
            if lo[2] < 399.95 or row['rotation'] != [0., 180, 0.]:
                violations.append(row['name'] + ': upper facade lost upright/front-facing placement')
    # Bounded attachment check against existing supports. The roof patch sits
    # inside SM_OutpostRoof's native annulus (.42..1 radii) at world Z670..750.
    anchors = [[2345, -495, 0, 2575, -365, 720], [2345, 365, 0, 2575, 495, 720],
               [2320, -525, 670, 2600, 525, 810], [2670, -490, 670, 2860, 490, 750],
               [2562.5, -200, 302, 2637.5, 200, 402],
               [2565, -320, 0, 2635, -200, 400], [2565, 200, 0, 2635, 320, 400]]
    boxes = [r['bounds_min'] + r['bounds_max'] for r in rows]

    def intersects(a, b):
        return all(a[i] <= b[i + 3] + .05 and a[i + 3] >= b[i] - .05 for i in range(3))

    connected = {i for i, box in enumerate(boxes) if any(intersects(box, a) for a in anchors)}
    while True:
        previous = len(connected)
        connected.update(i for i, box in enumerate(boxes)
                         if any(intersects(box, boxes[j]) for j in connected))
        if len(connected) == previous:
            break
    violations.extend(rows[i]['name'] + ': disconnected from entrance support bounds'
                      for i in range(len(rows)) if i not in connected)
    # Explicitly check the opening seen in the native image is now covered by
    # the four broad infill panels, rather than accepting a few decorative ribs.
    infill = [r for r in rows if '/Upper facade/Storage infill ' in r['name']
              or '/Upper facade/Crown transition ' in r['name']]
    coverage_samples = 0
    for y in range(-390, 391, 20):
        for z in (410, 450, 550, 610, 650, 690):
            coverage_samples += 1
            if not any(r['bounds_min'][1] - .01 <= y <= r['bounds_max'][1] + .01
                       and r['bounds_min'][2] - .01 <= z <= r['bounds_max'][2] + .01
                       for r in infill):
                violations.append('Upper facade: uncovered sample y%s z%s' % (y, z))
    return {'scope': 'Pure native-bounds placement; does not establish rendered quality or collision acceptance.',
            'parts': len(rows), 'unique_meshes': len({r['asset'] for r in rows}),
            'protected_lane': {'x': [1800, 2800], 'y': [-330, 330], 'z': [0, 350]},
            'existing_door_passage': {'y': [-160, 160], 'z': [0, 302]},
            'upper_facade_coverage': {'y': [-400, 400], 'z': [400, 700],
                                      'sample_count': coverage_samples, 'native_infill_panels': len(infill)},
            'local_nonshadow_lights': 1,
            'existing_support_bounds': anchors,
            'all_decorative': all(not r['solid'] for r in rows), 'violations': violations}


def build(api):
    """Idempotent only for this helper's tagged actors in the private map."""
    root, out = Path(api['ROOT']), Path(api['OUT'])
    import unreal as u
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    package = world.get_path_name().split('.')[0]
    # Full authoring starts from a blank world and saves TARGET only at the end.
    # Existing maps must match; the lead's explicit TARGET permits that blank
    # authoring stage without permitting an unrelated loaded gameplay map.
    blank_authoring = package.startswith('/Temp/Untitled') and api.get('TARGET') == TARGET_MAP
    if package != TARGET_MAP and not blank_authoring:
        raise RuntimeError('Entrance details are restricted to ' + TARGET_MAP)
    catalog_path = os.environ.get('SS_PREFAB_CATALOG', str(root / 'Artifacts/PrefabLibrary/catalog.json'))
    rows = layout(json.loads(Path(catalog_path).read_text(encoding='utf-8')))
    evidence = audit(rows)
    if evidence['violations']:
        raise ValueError('; '.join(evidence['violations']))
    for asset in {r['asset'] for r in rows}:
        api['load'](asset)
    lens = api['material']('M_OutpostEntranceInspectionLens', (.55, .82, 1.0), emission=1.3)
    removed = 0
    for actor in api['EAS'].get_all_level_actors():
        if actor.get_actor_label().startswith(PREFIX) and OWNER_TAG in [str(t) for t in actor.tags]:
            api['EAS'].destroy_actor(actor)
            removed += 1
    for row in rows:
        actor = api['raw'](row['name'], row['asset'], row['location'],
                           scale=row['scale'], rotation=row['rotation'], solid=False,
                           materials=[lens] if row.get('inspection_lens') else None)
        api['tag'](actor, OWNER_TAG)
        api['tag'](actor, 'OutpostRole:EntranceDecoration')
    light = api['light'](PREFIX + 'Door surround/Inspection wash', THRESHOLD_LIGHT_POSITION,
                         (.65, .85, 1.0), power=800, radius=600, shadow=False)
    api['tag'](light, OWNER_TAG)
    receipt = {'map': TARGET_MAP, 'audit': evidence, 'removed_previous_owned_actors': removed,
               'placements': rows, 'vendor_assets_modified': False,
               'local_lights': [{'position': THRESHOLD_LIGHT_POSITION, 'lumens': 800,
                                 'radius_cm': 600, 'casts_shadows': False}],
               'validation': 'Native placement/render review pending.'}
    (out / 'entrance-details.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt
