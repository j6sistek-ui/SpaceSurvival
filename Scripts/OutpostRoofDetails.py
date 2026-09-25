"""Native Genesis roof decking and connected service runs for the private outpost.

Call build(globals()) AFTER the OutpostSkyline placements. The existing solid
roof slabs stay unchanged; native26cm deck relief remains entirely above them.
Engineering uses its repaired515cm slab below the520cm observation floor;
Lounge and Operations keep their526cm slab tops.
The atrium's existingZ750 annulus carries16 pairs of radial service plates,
leaving the central oculus and the globe unobstructed.
Only the existing15 roof heat-exchanger/service components are repositioned,
absolutely from their source recipe. Gallery, fascia and rear district
are untouched. layout()/audit() require no Unreal process.
"""
import json
import math
import os
from pathlib import Path

PREFIX = 'RoofDetail/'
OWNER_TAG = 'OutpostRoofDetails'
TARGET_MAP = '/Game/OutpostSandbox/L_AsteroidOutpost'
ROOF_Z = 526.
ROOF_TOPS = {'Engineering': 515., 'Lounge': ROOF_Z, 'Operations': ROOF_Z, 'Atrium': 750.}
ROOFS = {
    'Engineering': [2850., -4550., 5550., -2250.],
    'Lounge': [2850., 2250., 5550., 4550.],
    'Operations': [6350., -1350., 9250., 1350.],
    'Atrium': [2530., -1670., 5870., 1670.],
}
EXCLUSIONS = {
    'Observation gallery including walls and ceiling': [2850., -4450., 520., 4350., -2350., 1120.],
    'Observation bridge and stairs': [2500., -4420., 0., 2900., -1700., 1130.],
    'Atrium planet and oculus': [3350., -850., 0., 5050., 850., 1800.],
}


def rotate(point, yaw):
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    return [point[0] * c - point[1] * s, point[0] * s + point[1] * c, point[2]]


def bounds(row):
    c, s = abs(math.cos(math.radians(row['yaw']))), abs(math.sin(math.radians(row['yaw'])))
    x, y, z = row['size']
    ext = [(x * c + y * s) / 2, (x * s + y * c) / 2, z / 2]
    return [row['center'][i] - ext[i] for i in range(3)] + [row['center'][i] + ext[i] for i in range(3)]


def overlap(a, b, tolerance=.001):
    return all(a[i] < b[i + 3] - tolerance and a[i + 3] > b[i] + tolerance for i in range(3))


def annulus_interval(row):
    """Exact XY distance interval of a yawed rectangle from the oculus centre."""
    offset = rotate([4200 - row['center'][0], -row['center'][1], 0], -row['yaw'])
    hx, hy = row['size'][0] / 2, row['size'][1] / 2
    closest = [max(abs(offset[0]) - hx, 0), max(abs(offset[1]) - hy, 0)]
    farthest = [abs(offset[0]) + hx, abs(offset[1]) + hy]
    return [math.hypot(*closest), math.hypot(*farthest)]


def layout(catalog):
    import OutpostSkyline
    meshes = catalog['meshes'] if isinstance(catalog, dict) else catalog
    by_asset = {m['asset']: m for m in meshes}
    rows = []

    def get(name):
        found = [m for m in meshes if m['name'] == name and '/P4_Genesis_Vol1/' in m['asset']]
        if len(found) != 1:
            raise ValueError('Missing or ambiguous native roof asset: ' + name)
        return found[0]

    deck = get('SM_UniversalPanel400X200_V1')
    deck_top = ROOF_Z + deck['extent'][2] * 2
    deck_tops = {wing: top + deck['extent'][2] * 2 for wing, top in ROOF_TOPS.items()}
    cable = get('SM_CornerWallFloor400X70_V3_ElectricalCableRouting')
    junction = get('SM_CornerWallFloor100X70_V4_ElectricalEquipment')
    crossbar = get('SM_CornerWallFloor200X70_V4_ElectricalEquipment')
    vent_parts = [get('SM_FloorVentilation_V1_Part1'), get('SM_FloorVentilation_V1_Part2')]

    def put(wing, label, mesh, x, y, support, role, scale=1., yaw=0., center_z=None):
        center = [x, y, support + mesh['extent'][2] * scale if center_z is None else center_z]
        row = {'name': PREFIX + wing + '/' + label, 'wing': wing, 'asset': mesh['asset'],
               'center': center, 'size': [v * 2 * scale for v in mesh['extent']],
               'yaw': yaw, 'scale': [scale] * 3, 'solid': False, 'role': role,
               'support_z': support, 'native_origin_cm': list(mesh['origin']),
               'native_dimensions_cm': [v * 2 for v in mesh['extent']],
               'catalog_render_lod0_triangles': mesh['triangles']}
        row['bounds'] = bounds(row)
        rows.append(row)
        return row

    # Native400x200 plates preserve the authored bolted border and recessed
    # relief. Engineering's complete west gallery footprint is excluded, not
    # covered with a second roof. Margins terminate inside the existing fascia.
    grids = [('Engineering', 3, 11, 4350., -4500.),
             ('Lounge', 6, 11, 3000., 2300.),
             ('Operations', 7, 13, 6400., -1300.)]
    for wing, nx, ny, x0, y0 in grids:
        for ix in range(nx):
            for iy in range(ny):
                put(wing, 'Deck %02d %02d' % (ix, iy), deck,
                    x0 + 200 + ix * 400, y0 + 100 + iy * 200, ROOF_TOPS[wing], 'Deck')

    # Radial native plates articulate the formerly blank annulus. Both tiers
    # are uniformly scaled; their gaps expose deliberate structural ribs.
    # The inner plates start atR800, giving70cm beyond the required730cm void.
    # The outer tier's farthest corners stay insideR1670. There are no
    # rectangular sheets crossing the oculus, nor intersections between bays.
    for index in range(16):
        yaw = index * 22.5
        for tier, radius, scale, turn in [('Inner', 1075., 1.375, 0),
                                          ('Outer', 1490., 1.2, 90)]:
            offset = rotate([radius, 0, 0], yaw)
            put('Atrium', '%s service plate %02d' % (tier, index), deck,
                4200 + offset[0], offset[1], 750., 'Deck', scale=scale, yaw=yaw + turn)

    # Existing roof machinery remains the main silhouette. These native cable
    # housings connect it as maintained mechanical equipment, rather than
    # adding detached boxes. Small end overlaps are purposeful service joints.
    cables = {
        'Engineering': [(5008, y, 90) for y in (-3820, -3420, -3020)],
        'Lounge': [(5008, y, 90) for y in (2900, 3300, 3700, 4100)]
                  + [(4600, 4100, 0)],
        'Operations': [(x, 800, 0) for x in (8200, 8600)]
                      + [(8620, y, 90) for y in (-610, -210, 190, 590)],
    }
    # The final Lounge connector is a short crossbar; use a native200cm part
    # instead of stretching a400cm housing through the adjoining service spine.
    for wing, route in cables.items():
        for index, (x, y, yaw) in enumerate(route):
            put(wing, 'Main utility housing %02d' % index, cable,
                x, y, deck_tops[wing], 'Utility', yaw=yaw)
    put('Lounge', 'Utility manifold junction', crossbar, 4900, 4100,
        deck_top, 'Utility')

    # Two secondary complete exchanger assemblies create distinct service bays
    # on the otherwise broad front roofs. Housing and fan retain the source
    # shared pivot at uniform2.4 scale. Low feed runs physically reach the main
    # exchanger row; no disconnected pipe ends or randomly scattered props.
    for wing, x, y, xs in [('Lounge', 3500, 2850, (3700, 4100, 4500)),
                           ('Operations', 6900, -650, (7100, 7500, 7900, 8300))]:
        scale = 2.4
        bottom = min(m['origin'][2] - m['extent'][2] for m in vent_parts)
        for index, part in enumerate(vent_parts):
            center = [x + part['origin'][0] * scale, y + part['origin'][1] * scale,
                      deck_tops[wing] + (part['origin'][2] - bottom) * scale]
            row = put(wing, 'Auxiliary exchanger part ' + str(index + 1), part,
                      center[0], center[1], deck_tops[wing], 'Assembly', scale=scale, center_z=center[2])
            row['assembly'] = wing + '/Auxiliary exchanger'
        for index, cx in enumerate(xs):
            put(wing, 'Auxiliary feed %02d' % index, cable, cx, y, deck_tops[wing], 'Utility')
        if wing == 'Lounge':
            put(wing, 'Auxiliary feed end joint', junction, 4750, y, deck_top, 'Utility')

    # Absolute targets come from the unchanged source recipe, never the current
    # world location. A second call cannot raise equipment by another37cm.
    shifted = []
    architecture = OutpostSkyline.build(catalog)
    for source in architecture:
        if not source['name'].startswith('Roof_'):
            continue
        if '_HeatExchanger_' not in source['name'] and not source['name'].endswith('_ServiceSpine'):
            continue
        mesh = by_asset[source['asset']]
        row = dict(source)
        row['wing'] = source['name'].split('_')[1]
        row['source_center'] = list(source['center'])
        row['center'] = list(source['center'])
        row['center'][2] += deck_tops[row['wing']] - 515.
        row['native_dimensions_cm'] = [v * 2 for v in mesh['extent']]
        row['native_origin_cm'] = list(mesh['origin'])
        row['scale'] = [row['size'][i] / row['native_dimensions_cm'][i] for i in range(3)]
        offset = rotate([mesh['origin'][i] * row['scale'][i] for i in range(3)], row['yaw'])
        row['target_actor_location'] = [row['center'][i] - offset[i] for i in range(3)]
        row['bounds'] = bounds(row)
        shifted.append(row)
    return {'placements': rows, 'existing_equipment': shifted, 'deck_top_z': deck_top,
            'deck_top_z_by_wing': {w: z for w, z in deck_tops.items() if w != 'Atrium'},
            'source_roof_top_z_by_wing': ROOF_TOPS,
            'source_roof_top_z': ROOF_Z, 'atrium_roof_top_z': 750.,
            'atrium_radial_limits_cm': [730., 1670.],
            'roof_bounds_xy': ROOFS, 'exclusions': EXCLUSIONS}


def audit(plan):
    rows, shifted = plan['placements'], plan['existing_equipment']
    violations, names, signatures = [], set(), set()
    for row in rows + shifted:
        b = bounds(row)
        roof = ROOFS[row['wing']]
        if b[0] < roof[0] - .01 or b[1] < roof[1] - .01 or b[3] > roof[2] + .01 or b[4] > roof[3] + .01:
            violations.append(row['name'] + ': outside supporting roof')
        for name, exclusion in EXCLUSIONS.items():
            if row['wing'] == 'Atrium' and name == 'Atrium planet and oculus':
                continue  # Use the exact radial test rather than its enclosing square.
            if overlap(b, exclusion):
                violations.append(row['name'] + ': overlaps ' + name)
        if row['wing'] == 'Atrium':
            near, far = annulus_interval(row)
            if near < 730 or far > 1670:
                violations.append(row['name'] + ': outside solid annular roof or inside oculus')
        if row['solid'] or max(row['scale']) - min(row['scale']) > .00001:
            violations.append(row['name'] + ': must be noncolliding with uniform native proportions')
        if row['name'] in names:
            violations.append(row['name'] + ': duplicate label')
        names.add(row['name'])
        signature = (row['asset'], tuple(round(v, 4) for v in row['center']), row['yaw'])
        if signature in signatures:
            violations.append(row['name'] + ': duplicate mesh placement')
        signatures.add(signature)
        if not all(math.isfinite(v) for v in b):
            violations.append(row['name'] + ': invalid bounds')
    decks = [r for r in rows if r['role'] == 'Deck']
    for row in rows:
        b = bounds(row)
        if row['role'] in ('Deck', 'Utility') and abs(b[2] - row['support_z']) > .001:
            violations.append(row['name'] + ': does not touch declared support')
        if row['role'] == 'Assembly':
            continue  # Fans are intentionally contained by their paired housing.
        if row['role'] != 'Deck':
            for x in (b[0], row['center'][0], b[3]):
                for y in (b[1], row['center'][1], b[4]):
                    if not any(d['wing'] == row['wing']
                               and d['bounds'][0] - .05 <= x <= d['bounds'][3] + .05
                               and d['bounds'][1] - .05 <= y <= d['bounds'][4] + .05 for d in decks):
                        violations.append(row['name'] + ': service footprint lacks deck support')
                        break
    # Services must connect to existing source machinery via a chain of actual
    # touching bounds. Deck plates are deliberately excluded from this graph:
    # being on the same roof alone does not establish a connected service run.
    services = [r for r in rows if r['role'] != 'Deck'] + shifted
    linked = set(range(len(services) - len(shifted), len(services)))
    def touching(a, b):
        return all(a[i] <= b[i + 3] + .05 and a[i + 3] >= b[i] - .05 for i in range(3))
    while True:
        previous = len(linked)
        linked.update(i for i, row in enumerate(services)
                      if any(touching(bounds(row), bounds(services[j])) for j in linked))
        if len(linked) == previous:
            break
    violations.extend(services[i]['name'] + ': disconnected from source service machinery'
                      for i in range(len(services)) if i not in linked)
    if len(shifted) != 15:
        violations.append('Expected exactly15 existing roof equipment components; source changed')
    return {'geometry_only': True, 'new_parts': len(rows), 'deck_panels': len(decks),
            'atrium_panels': sum(r['wing'] == 'Atrium' for r in rows),
            'atrium_actual_radial_bounds_cm': [min(annulus_interval(r)[0] for r in rows if r['wing'] == 'Atrium'),
                                               max(annulus_interval(r)[1] for r in rows if r['wing'] == 'Atrium')],
            'existing_equipment_rebased': len(shifted),
            'unique_new_meshes': len({r['asset'] for r in rows}),
            'catalog_render_lod0_triangle_instances': sum(r['catalog_render_lod0_triangles'] for r in rows),
            'all_new_actors_noncolliding': all(not r['solid'] for r in rows),
            'violations': violations,
            'limits': 'Native AABB placement checks; rendered materials, source Nanite cost and owner acceptance remain unverified.'}


def build(api):
    """Idempotently add own details and rebase only the15 known roof machines."""
    u, eas = api['u'], api['EAS']
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    package = world.get_path_name().split('.')[0]
    blank = package.startswith('/Temp/Untitled') and api.get('TARGET') == TARGET_MAP
    if package != TARGET_MAP and not blank:
        raise RuntimeError('Roof details are restricted to ' + TARGET_MAP)
    root, out = Path(api['ROOT']), Path(api['OUT'])
    path = os.environ.get('SS_PREFAB_CATALOG', str(root / 'Artifacts/PrefabLibrary/catalog.json'))
    plan = layout(json.loads(Path(path).read_text(encoding='utf-8')))
    evidence = audit(plan)
    if evidence['violations']:
        raise ValueError('; '.join(evidence['violations']))
    actors = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
    for wing in ('Engineering', 'Lounge', 'Operations'):
        slab = actors.get(wing + '/Roof structure')
        if slab is None:
            raise ValueError('Missing supporting roof slab: ' + wing)
        center, extent = slab.get_actor_bounds(False)
        if abs(center.z + extent.z - ROOF_TOPS[wing]) > .05:
            raise ValueError('Repair ' + wing + ' roof top to ' + str(ROOF_TOPS[wing])
                             + ' before roof-detail placement')
    # Fail before mutation if called before the authoritative Skyline recipe.
    for row in plan['existing_equipment']:
        if row['name'] not in actors:
            raise ValueError('Place OutpostSkyline before roof details: ' + row['name'])
        actual = actors[row['name']].static_mesh_component.static_mesh.get_path_name()
        if actual != row['asset']:
            raise ValueError('Roof equipment asset differs from source: ' + row['name'])
    for asset in {r['asset'] for r in plan['placements']}:
        api['load'](asset)
    removed = 0
    for actor in eas.get_all_level_actors():
        if actor.get_actor_label().startswith(PREFIX) and OWNER_TAG in [str(t) for t in actor.tags]:
            eas.destroy_actor(actor)
            removed += 1
    for row in plan['existing_equipment']:
        actors[row['name']].set_actor_location(u.Vector(*row['target_actor_location']), False, False)
        for record in api.get('RECORDS', []):
            if record.get('name') == row['name']:
                record['location'] = list(row['target_actor_location'])
    for row in plan['placements']:
        actor = api['place'](row['name'], row['asset'], row['center'], size=row['size'],
                             yaw=row['yaw'], solid=False)
        api['tag'](actor, OWNER_TAG)
        api['tag'](actor, 'OutpostRole:RoofDecoration')
    receipt = dict(plan, map=TARGET_MAP, audit=evidence, removed_previous_owned_actors=removed,
                   vendor_assets_modified=False, validation='Native placement/render review pending.')
    (out / 'roof-details.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt
