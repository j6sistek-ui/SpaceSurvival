"""Fixture-supported, local accent lighting for three berths and the market.

Eight native metal masts carry inward-facing floods. Four existing promenade
crossheads carry downward native lamps. Broad pad point lights stay in place
with their original parameters and visibility off. No environment, exposure,
planet, hologram, material asset or map-save changes. layout()/audit() are pure.
"""
import itertools
import json
import math
import os
from pathlib import Path

TARGET = '/Game/OutpostSandbox/L_AsteroidOutpost'
PREFIX = 'PublicLighting/'
TAG = 'OutpostPublicLighting'
P5 = '/P5_FruitSeller/'
CUBE = '/Engine/BasicShapes/Cube.Cube'
LAMP = 'SM_Props_ConstructionPart118_Light'
MATERIAL_REFERENCE = 'Engineering/Workstation light/Primary/Owned lamp housing'


def _rotate(point, yaw, roll=0):
    """Unreal yaw/roll convention, all mount recipes have zero pitch."""
    a, b = math.radians(yaw), math.radians(roll)
    x, y, z = point
    y, z = math.cos(b) * y + math.sin(b) * z, -math.sin(b) * y + math.cos(b) * z
    return [math.cos(a) * x - math.sin(a) * y, math.sin(a) * x + math.cos(a) * y, z]


def _overlap(a, b, margin=0):
    return all(a[i] < b[i + 3] + margin and a[i + 3] > b[i] - margin for i in range(3))


def layout(catalog):
    import OutpostBerthDetails as berth
    import OutpostPromenadeDetails as promenade
    meshes = catalog['meshes'] if isinstance(catalog, dict) else catalog
    parts, lights, pools = [], [], []
    lookup = {m['name']: m for m in meshes if P5 in m['asset']}
    base, post, arm, lamp = [lookup[n] for n in (
        'SM_Building_StructureBase_V1', 'SM_Building_Structure200x10_V1',
        'SM_Building_StructureLink90x10_V1', LAMP)]

    def put(name, mesh, center, yaw=0, roll=0, pad=None, floor=False, support=None):
        corners = [_rotate([mesh['extent'][i] * signs[i] for i in range(3)], yaw, roll)
                   for signs in itertools.product((-1, 1), repeat=3)]
        offset = _rotate(mesh['origin'], yaw, roll)
        bounds = [center[i] + min(c[i] for c in corners) for i in range(3)]
        bounds += [center[i] + max(c[i] for c in corners) for i in range(3)]
        row = {'name': PREFIX + name, 'asset': mesh['asset'], 'center': list(center),
            'position': [center[i] - offset[i] for i in range(3)],
            'rotation': [0., yaw, roll], 'scale': [1., 1., 1.], 'bounds': bounds,
            'native_origin': list(mesh['origin']), 'native_extent': list(mesh['extent']),
            'pad': pad, 'floor_supported': floor, 'support': support,
            'native_triangles': mesh['triangles']}
        parts.append(row)
        return row

    pad_names = {'Player': 'Player berth', 'Visitor02': 'Visitor berth 02', 'Visitor03': 'Visitor berth 03'}
    for pad in berth.PADS:
        name, (cx, cy), radius = pad['name'], pad['center'], pad['radius']
        if name == 'Player':
            positions = [(cx + 2700 * math.cos(math.radians(a)),
                          cy + 2700 * math.sin(math.radians(a))) for a in (60, 120, 240, 300)]
        else:
            positions = [(cx - 1200, cy), (cx + 1200, cy)]
        pools.append({'name': pad_names[name] + '/Pool', 'position': [cx, cy, 950.],
            'lumens': 16000., 'radius': radius * 1.2, 'ground': 'Ground/' + pad_names[name],
            'center': [cx, cy], 'pad': name})
        for number, (x, y) in enumerate(positions, 1):
            group = name + '/Mast ' + str(number)
            yaw = math.degrees(math.atan2(cy - y, cx - x))
            deck = .5
            put(group + '/Foot', base, [x, y, deck + base['extent'][2]], yaw + 90,
                pad=name, floor=True, support='Existing berth deck')
            height = post['extent'][2] * 2
            for level in range(2):
                put(group + '/Mast ' + str(level + 1), post,
                    [x, y, deck + height * (level + .5)], yaw + 90, pad=name,
                    support=PREFIX + group + ('/Foot' if level == 0 else '/Mast 1'))
            arm_z = deck + height * 2
            crossarm = put(group + '/Crossarm', arm, [x, y, arm_z], yaw + 90,
                pad=name, support=PREFIX + group + '/Mast 2')
            # Local -Z is the real lens-facing normal. Yaw+90/roll tilts that
            # normal inward while retaining the lamp's 100cm horizontal span.
            center_z = arm_z + arm['extent'][2] + lamp['extent'][1]
            # The two visitor hull midpoints are at Z369/369.5cm, above the
            # old Z235 aim; illuminate their sides without lifting the sky.
            target = [cx, cy, 245. if name == 'Player' else 370.]
            for _ in range(3):
                elevation = math.degrees(math.atan2(target[2] - center_z, math.hypot(cx - x, cy - y)))
                roll = 90 + elevation
                extent_z = max(abs(_rotate([lamp['extent'][i] * s[i] for i in range(3)], yaw + 90, roll)[2])
                               for s in itertools.product((-1, 1), repeat=3))
                center_z = crossarm['bounds'][5] + extent_z - .4
            housing = put(group + '/Flood housing', lamp, [x, y, center_z], yaw + 90, roll,
                pad=name, support=crossarm['name'])
            direction = _rotate([0, 0, -1], yaw + 90, roll)
            position = [housing['center'][i] + direction[i] * (lamp['extent'][2] + 1.) for i in range(3)]
            lights.append({'name': PREFIX + group + '/Local flood', 'kind': 'Spot',
                'housing': housing['name'], 'position': position, 'target': target,
                'lumens': 2200. if name == 'Player' else 850.,
                'radius': 3300. if name == 'Player' else 1550.,
                'inner_cone': 22., 'outer_cone': 38., 'specular': .18,
                'color': [.67, .82, 1.] if number % 2 else [1., .82, .64],
                'pad': name, 'lens_forward': direction})
            # Thin exact-mast proxy; no broad invisible furniture box. Native
            # decorative mesh collision is disabled rather than trusted.
            parts.append({'name': PREFIX + group + '/Mast collision', 'asset': CUBE,
                'center': [x, y, deck + height], 'position': [x, y, deck + height],
                'rotation': [0., 0., 0.], 'scale': [.12, .12, 2 * height / 100.],
                'bounds': [x - 6, y - 6, deck, x + 6, y + 6, deck + height * 2],
                'pad': name, 'floor_supported': True, 'support': 'Existing berth deck',
                'hidden_collision': True})

    gantry_rows = {r['name']: r for r in promenade.layout(catalog)}
    anchors = []
    for group, x in (('Exchange gantry', -780.), ('Arrivals gantry', 1650.)):
        for index, y in ((0, -600.), (3, 600.)):
            anchor = gantry_rows['PromenadeKit/' + group + '/Crosshead ' + str(index)]
            bottom = anchor['bounds'][2]
            center = [x, y, bottom - lamp['extent'][2] + .3]
            housing = put('Market/' + group + '/' + str(index) + '/Downlight housing',
                lamp, center, yaw=90., support=anchor['name'])
            anchors.append({'name': anchor['name'], 'asset': anchor['asset'], 'bounds': anchor['bounds']})
            lights.append({'name': PREFIX + 'Market/' + group + '/' + str(index) + '/Local downlight',
                'kind': 'Rect', 'housing': housing['name'],
                'position': [x, y, housing['bounds'][2] - 1.], 'target': [x, y, 25.],
                'lumens': 275., 'radius': 650., 'width': 90., 'height': 20.,
                'specular': .08, 'color': [.70, .84, 1.], 'pad': None,
                'lens_forward': [0., 0., -1.]})
    return {'parts': parts, 'lights': lights, 'pools': pools, 'anchors': anchors}


def audit(plan, catalog):
    """Conservative geometry guards, not a substitute for native render/play."""
    import OutpostBerthDetails as berth
    import OutpostPromenadeDetails as promenade
    failures = []
    pads = {p['name']: p for p in berth.PADS}
    services = [(r['name'], berth.bounds(r)) for r in berth.layout(catalog) if r['role'] == 'Service']
    names = [r['name'] for key in ('parts', 'lights') for r in plan[key]]
    if len(set(names)) != len(names):
        failures.append('Duplicate new actor label')
    for row in plan['parts']:
        b = row['bounds']
        if row['pad']:
            pad = pads[row['pad']]
            if any(math.dist([x, y], pad['center']) > pad['radius'] - 55
                   for x in (b[0], b[3]) for y in (b[1], b[4])):
                failures.append(row['name'] + ': outside safe pad edge')
            for name, r in berth.CLEARWAYS:
                if _overlap(b, [r[0], r[1], -1, r[2], r[3], 1500], 45):
                    failures.append(row['name'] + ': protected ' + name)
            for name, r in services:
                if _overlap(b, r, 45):
                    failures.append(row['name'] + ': too near ' + name)
            if row['floor_supported'] and abs(b[2] - .5) > .01:
                failures.append(row['name'] + ': floor support gap')
        else:
            for name, r in promenade.PROTECTED.items():
                if _overlap(b, r):
                    failures.append(row['name'] + ': protected ' + name)
            if b[2] < 350:
                failures.append(row['name'] + ': market headroom reduced')
        support = next((p for p in plan['parts'] if p['name'] == row['support']), None)
        if row['name'].endswith('/Flood housing') and (not support or abs(b[2] - support['bounds'][5] + .4) > .1):
            failures.append(row['name'] + ': flood housing not seated on crossarm')
    for light in plan['lights']:
        delta = [light['target'][i] - light['position'][i] for i in range(3)]
        length = math.sqrt(sum(v * v for v in delta))
        dot = sum(a * b / length for a, b in zip(delta, light['lens_forward']))
        if length >= light['radius'] or dot < .9999:
            failures.append(light['name'] + ': target outside aimed bounded beam')
    return {'native_parts': sum(not p.get('hidden_collision') for p in plan['parts']),
        'thin_mast_collision_proxies': sum(bool(p.get('hidden_collision')) for p in plan['parts']),
        'local_lights': len(plan['lights']), 'shadow_lights': 0,
        'main_pad_masts': 4, 'visitor_masts': 4, 'market_mounted_fixtures': 4,
        'new_total_lumens': sum(l['lumens'] for l in plan['lights']),
        'broad_pad_pool_lumens_replaced': sum(p['lumens'] for p in plan['pools']),
        'violations': failures}


def _xyz(v):
    return [float(v.x), float(v.y), float(v.z)]


def _bounds(actor):
    from OutpostGeometryUtils import mesh_union
    c, e = mesh_union(actor)
    return [c.x - e.x, c.y - e.y, c.z - e.z, c.x + e.x, c.y + e.y, c.z + e.z]


def _close(a, b, label, tolerance=.25):
    if len(a) != len(b) or max(abs(x - y) for x, y in zip(a, b)) > tolerance:
        raise RuntimeError('Public-light source geometry changed: ' + label +
                           '; observed=' + repr(a) + '; expected=' + repr(b) +
                           '; tolerance_cm=' + str(tolerance))


def _pool_state(component):
    return {name: float(component.get_editor_property(name)) for name in (
        'intensity', 'attenuation_radius', 'specular_scale', 'indirect_lighting_intensity',
        'volumetric_scattering_intensity')} | {
        'visible': bool(component.get_editor_property('visible')),
        'cast_shadows': bool(component.get_editor_property('cast_shadows')),
        'intensity_units': str(component.get_editor_property('intensity_units'))}


def apply(api):
    """After berth/promenade/local-light passes; caller saves and renders."""
    u, eas = api['u'], api['EAS']
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    package = world.get_path_name().split('.')[0]
    if package != TARGET and not (package.startswith('/Temp/Untitled') and api.get('TARGET') == TARGET):
        raise RuntimeError('Public lighting restricted to the private outpost')
    path = Path(os.environ.get('SS_PREFAB_CATALOG', str(Path(api['ROOT']) / 'Artifacts/PrefabLibrary/catalog.json')))
    catalog = json.loads(path.read_text(encoding='utf-8'))
    plan = layout(catalog)
    checks = audit(plan, catalog)
    if checks['violations']:
        raise RuntimeError('; '.join(checks['violations']))
    actors = {}
    for actor in eas.get_all_level_actors():
        actors.setdefault(actor.get_actor_label(), []).append(actor)

    def one(label, tag='OutpostAuthored'):
        group = actors.get(label, [])
        if len(group) != 1 or tag not in map(str, group[0].tags):
            raise RuntimeError('Missing/duplicate/unowned public-light anchor: ' + label)
        return group[0]

    expected = {r['name'] for kind in ('parts', 'lights') for r in plan[kind]}
    existing = [a for values in actors.values() for a in values if TAG in map(str, a.tags)]
    if existing and (len(existing) != len(expected) or {a.get_actor_label() for a in existing} != expected):
        raise RuntimeError('Public-light set is incomplete or duplicated; inspect before reapplying')
    for name in expected:
        group = actors.get(name, [])
        if len(group) > 1 or group and TAG not in map(str, group[0].tags):
            raise RuntimeError('Public-light label occupied by unrelated actor: ' + name)
    # Read everything before creating any actors. Native bounds and the actual
    # supporting crossheads/decks must agree with the reviewed pure recipe.
    assets = {}
    for row in plan['parts']:
        if row['asset'] not in assets:
            assets[row['asset']] = api['load'](row['asset'])
        mesh = assets[row['asset']]
        if not mesh or not isinstance(mesh, u.StaticMesh):
            raise RuntimeError('Missing native public-light mesh: ' + row['asset'])
        if not row.get('hidden_collision'):
            b = mesh.get_bounds()
            _close(_xyz(b.origin), row['native_origin'], row['asset'])
            _close(_xyz(b.box_extent), row['native_extent'], row['asset'])
    reference = one(MATERIAL_REFERENCE).get_component_by_class(u.StaticMeshComponent)
    if not reference or not reference.static_mesh or not reference.static_mesh.get_name() == LAMP:
        raise RuntimeError('Reviewed native lamp finish reference changed')
    lamp_materials = [reference.get_material(i) for i in range(reference.get_num_materials())]
    for anchor in plan['anchors']:
        actor = one(anchor['name'], 'OutpostPromenadeDetails')
        component = actor.get_component_by_class(u.StaticMeshComponent)
        if not component or component.static_mesh.get_path_name() != anchor['asset']:
            raise RuntimeError('Promenade crosshead mesh changed')
        _close(_bounds(actor), anchor['bounds'], anchor['name'])
    pool_data = []
    for pool in plan['pools']:
        actor = one(pool['name'])
        if not isinstance(actor, u.PointLight) or isinstance(actor, u.SpotLight):
            raise RuntimeError('Expected authored broad pad point light')
        component = actor.get_component_by_class(u.PointLightComponent)
        before = _pool_state(component)
        _close(_xyz(actor.get_actor_location()), pool['position'], pool['name'])
        if (component.get_editor_property('intensity_units') != u.LightUnits.LUMENS or
                abs(before['intensity'] - pool['lumens']) > .1 or
                abs(before['attenuation_radius'] - pool['radius']) > .1 or before['cast_shadows']):
            raise RuntimeError('Unreviewed broad pad light parameters')
        if not existing and not before['visible']:
            raise RuntimeError('Broad pad point was hidden by another pass')
        ground = _bounds(one(pool['ground']))
        _close([(ground[0] + ground[3]) / 2, (ground[1] + ground[4]) / 2, ground[5]],
               [*pool['center'], 0.], pool['ground'], 1.)
        pool_data.append((pool, component, before))

    native, mounted = [], {}
    for row in plan['parts']:
        group = actors.get(row['name'], [])
        actor = group[0] if group else eas.spawn_actor_from_class(u.StaticMeshActor, u.Vector(*row['position']))
        if not actor or not isinstance(actor, u.StaticMeshActor):
            raise RuntimeError('Could not create native public-light mounting part')
        component = actor.get_component_by_class(u.StaticMeshComponent)
        component.set_static_mesh(assets[row['asset']])
        component.set_mobility(u.ComponentMobility.MOVABLE)
        hidden = bool(row.get('hidden_collision'))
        component.set_collision_profile_name('BlockAll' if hidden else 'NoCollision')
        component.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS if hidden else u.CollisionEnabled.NO_COLLISION)
        component.set_cast_shadow(False)
        if assets[row['asset']].get_name() == LAMP:
            for slot, material in enumerate(lamp_materials):
                component.set_material(slot, material)
        actor.set_actor_label(row['name'])
        actor.set_folder_path('PublicLighting')
        actor.tags = [u.Name('OutpostAuthored'), u.Name(TAG), u.Name('OutpostRole:PublicFixture')]
        if row['floor_supported']:
            actor.tags = list(actor.tags) + [u.Name('OutpostRole:FloorProp'), u.Name('OutpostSupport:0')]
        # Python Rotator uses native MakeRotator(Roll, Pitch, Yaw), whereas
        # this recipe consistently stores [Pitch, Yaw, Roll]. Never unpack it.
        rotation = u.Rotator(pitch=row['rotation'][0], yaw=row['rotation'][1], roll=row['rotation'][2])
        actor.set_actor_rotation(rotation, False)
        measured_rotation = actor.get_actor_rotation()
        actual_rotation = [float(measured_rotation.pitch), float(measured_rotation.yaw), float(measured_rotation.roll)]
        if any(abs((observed - expected + 180.) % 360. - 180.) > .01
               for observed, expected in zip(actual_rotation, row['rotation'])):
            raise RuntimeError('Public-light rotation readback failed: ' + row['name'] +
                               '; observed_pitch_yaw_roll=' + repr(actual_rotation) +
                               '; expected=' + repr(row['rotation']))
        actor.set_actor_scale3d(u.Vector(*row['scale']))
        actor.set_actor_location(u.Vector(*row['position']), False, False)
        actor.set_actor_hidden_in_game(hidden)
        observed = _bounds(actor)
        _close(observed, row['bounds'], row['name'], .5)
        mounted[row['name']] = component
        native.append(dict(row, actual_bounds=observed, created=not bool(group)))
    lighting = []
    for row in plan['lights']:
        group = actors.get(row['name'], [])
        klass = u.SpotLight if row['kind'] == 'Spot' else u.RectLight
        position = u.Vector(*row['position'])
        rotation = u.MathLibrary.find_look_at_rotation(position, u.Vector(*row['target']))
        actor = group[0] if group else eas.spawn_actor_from_class(klass, position, rotation)
        if not actor or not isinstance(actor, klass):
            raise RuntimeError('Wrong existing public-light actor class')
        actor.set_actor_label(row['name'])
        actor.set_folder_path('PublicLighting')
        actor.tags = [u.Name('OutpostAuthored'), u.Name(TAG)]
        actor.set_actor_location(position, False, False)
        actor.set_actor_rotation(rotation, False)
        c = actor.get_component_by_class(u.SpotLightComponent if row['kind'] == 'Spot' else u.RectLightComponent)
        c.set_mobility(u.ComponentMobility.MOVABLE)
        c.set_intensity_units(u.LightUnits.LUMENS)
        c.set_intensity(row['lumens'])
        c.set_attenuation_radius(row['radius'])
        c.set_light_color(u.LinearColor(*row['color'], 1.))
        c.set_cast_shadows(False)
        c.set_editor_property('specular_scale', row['specular'])
        c.set_editor_property('indirect_lighting_intensity', 0.)
        c.set_editor_property('volumetric_scattering_intensity', 0.)
        c.set_visibility(True, False)
        if row['kind'] == 'Spot':
            c.set_inner_cone_angle(row['inner_cone'])
            c.set_outer_cone_angle(row['outer_cone'])
            c.set_source_radius(8.)
            c.set_source_length(70.)
        else:
            c.set_source_width(row['width'])
            c.set_source_height(row['height'])
            c.set_barn_door_angle(55.)
            c.set_barn_door_length(15.)
        if not actor.attach_to_component(mounted[row['housing']], u.Name(''), u.AttachmentRule.KEEP_WORLD,
                u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, False):
            raise RuntimeError('Failed to attach public light to native fixture')
        actual = _pool_state(c)
        _close(_xyz(actor.get_actor_forward_vector()), row['lens_forward'], row['name'], .001)
        if abs(actual['intensity'] - row['lumens']) > .1 or abs(actual['attenuation_radius'] - row['radius']) > .1 or actual['cast_shadows']:
            raise RuntimeError('Public-light readback failed')
        lighting.append(dict(row, actual=actual, created=not bool(group)))
    pools = []
    for row, c, before in pool_data:
        c.set_visibility(False, False)
        after = _pool_state(c)
        if after != dict(before, visible=False):
            raise RuntimeError('Original broad pad parameters changed')
        pools.append(dict(row, before=before, after=after))
    receipt = {'map': TARGET, 'audit': checks, 'placements': native, 'lights': lighting,
        'hidden_original_pad_pools': pools, 'original_pool_parameters_preserved': True,
        'global_environment_exposure_planet_holograms_changed': False,
        'vendor_or_material_assets_changed': False, 'map_saved': False,
        'validation': 'Pure protected-bounds and native-anchor/parameter checks only. Native dark-space, ship readability and walking acceptance remain separate.'}
    (Path(api['OUT']) / 'public-lighting.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt
