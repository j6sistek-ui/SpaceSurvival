"""Dense native computer-room banks and framed crew presentation bays.

Only the source actors belonging to complete equipment assemblies are reused.
Original relative placement, all three rotation axes, scale and per-slot native
materials remain intact. The source floor offset is removed once per assembly.
The helper starts no engine and edits no vendor assets or gameplay behavior.
"""
import itertools
import json
import math
from pathlib import Path

P1 = '/Game/P1toP5_Bundle/P1_WorkStation/Meshes/'
P3 = '/Game/P1toP5_Bundle/P3_ComputerStation/Meshes/'
P4 = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Meshes/'
P5 = '/Game/P1toP5_Bundle/P5_FruitSeller/Meshes/'

# North/south banks face the room. The east pair faces the west entrance.
# Native widths are about10m, so six dense sections fit around the28x26m room.
BANKS = [('North Navigation', (7000, 1170, 0), 0),
         ('North Communications', (8170, 1170, 0), 0),
         ('South Logistics', (7000, -1170, 0), 180),
         ('South Science', (8170, -1170, 0), 180),
         ('East Tracking', (9160, -560, 0), -90),
         ('East Contracts', (9160, 560, 0), -90)]
COMMAND_PODS = [('Port North', (7400, 210, 0), 180),
                ('Port South', (7400, -210, 0), 0),
                ('Starboard North', (8130, 210, 0), 180),
                ('Starboard South', (8130, -210, 0), 0)]
HOLOGRAM_BAYS = [(5350, 2800, 20), (5350, 3360, 20), (5350, 3960, 20)]
CONVERSATION_CENTERS = [(3440, 2870, 0), (3440, 3710, 0)]
REPLACED_DRESSING_PREFIXES = ('Ops_', 'Lounge_Chair_', 'Lounge_LowTable_',
    'Lounge_GameProjector_', 'Lounge_GameHologram_')


def _rotate(point, yaw):
    angle = math.radians(yaw)
    c, s = math.cos(angle), math.sin(angle)
    return [point[0] * c - point[1] * s, point[0] * s + point[1] * c, point[2]]


def _object(prefix, name):
    return prefix + name + '.' + name


def _transformed(record, pivot, target, yaw, group):
    offset = _rotate([record['location'][i] - pivot[i] for i in range(3)], yaw)
    rotation = list(record['rotation'])
    rotation[1] += yaw
    corners = [_rotate([p[i] - pivot[i] for i in range(3)], yaw)
               for p in itertools.product(*zip(record['bounds_min'], record['bounds_max']))]
    return {'name': group + '/' + record['name'], 'asset': record['asset'],
            'location': [target[i] + offset[i] for i in range(3)],
            'rotation': rotation, 'scale': list(record['scale']),
            'materials': list(record['materials']),
            'bounds_min': [min(p[i] for p in corners) + target[i] for i in range(3)],
            'bounds_max': [max(p[i] for p in corners) + target[i] for i in range(3)],
            'solid': ('IndustryStation_V1_Part1' in record['asset'] or
                      'IndustrySeat_V1_Part1' in record['asset'] or
                      'IndustrySeat_V1_Part2' in record['asset'] or
                      ('Storage3000Series' in record['asset'] and '_Part1.' in record['asset']))}


def source_layout(data=None):
    """Pure native source geometry, useful before invoking Unreal."""
    data = data or json.loads(Path(__file__).with_suffix('.json').read_text(encoding='utf-8'))
    records = data['actors']
    rows = []
    for name, target, yaw in BANKS:
        rows.extend(_transformed(r, data['bank_anchor'], target, yaw,
                    'OperationsNative/' + name) for r in records)
    console_names = set(data['console_names'])
    for name, target, yaw in COMMAND_PODS:
        rows.extend(_transformed(r, data['console_anchor'], target, yaw,
                    'OperationsNative/Command island ' + name)
                    for r in records if r['name'] in console_names)
    chair_names = set(data['chair_names'])
    for index, center in enumerate(CONVERSATION_CENTERS):
        for side, offset, yaw in [('South', (0, -210, 0), 0),
                                  ('North', (0, 210, 0), 180),
                                  ('West', (-270, 0, 0), -90)]:
            target = [center[i] + offset[i] for i in range(3)]
            rows.extend(_transformed(r, data['chair_anchor'], target, yaw,
                'LoungeNative/Conversation ' + str(index + 1) + '/' + side)
                for r in records if r['name'] in chair_names)
    return rows


def build(api):
    """Compose actual native assets, returning provenance and owner-view points."""
    import unreal as u
    rows = source_layout()
    receipt = {'source_map': '/Game/P1toP5_Bundle/P3_ComputerStation/Map/Demonstration_ComputerStation',
               'banks': [], 'native_actor_count': len(rows), 'decorations': [],
               'hologram_character_feet': [[p[0], p[1], p[2] + 10] for p in HOLOGRAM_BAYS],
               'hologram_facing_yaw': 180,
               'conversation_centers': [list(p) for p in CONVERSATION_CENTERS],
               'replace_dressing_prefixes': list(REPLACED_DRESSING_PREFIXES),
               'validation': 'Source composition only; final render, collision and walking are pending.'}
    for row in rows:
        materials = [api['balanced'](api['load'](p)) if p else None for p in row['materials']]
        actor = api['raw'](row['name'], row['asset'], row['location'],
            scale=row['scale'], rotation=row['rotation'], materials=materials,
            solid=row['solid'])
        actor.static_mesh_component.set_simulate_physics(False)
        actor.tags = list(actor.tags) + [u.Name('OutpostRole:NativeInteriorAssembly')]
    for name, target, yaw in BANKS:
        group = [r for r in rows if r['name'].startswith('OperationsNative/' + name + '/')]
        receipt['banks'].append({'name': name, 'source_parts': len(group),
            'target': list(target), 'yaw': yaw,
            'bounds_min': [min(r['bounds_min'][i] for r in group) for i in range(3)],
            'bounds_max': [max(r['bounds_max'][i] for r in group) for i in range(3)]})

    def placed(name, asset, center, size=None, height=None, yaw=0, solid=False, mounting='Floor'):
        actor = api['place'](name, asset, center, size=size, height=height,
                             yaw=yaw, solid=solid)
        actor.tags = list(actor.tags) + [u.Name('OutpostRole:InteriorDetail'),
                                       u.Name('OutpostMount:' + mounting)]
        receipt['decorations'].append({'name': name, 'center': list(center),
            'size': size, 'height': height, 'yaw': yaw, 'mounting': mounting})
        return actor

    # Native overhead service panels and electrical trays visually connect each
    # dense console bank to the ceiling. No unsupported giant featureless desk.
    ceiling = _object(P4, 'SM_CeilingPanel400X200_V1')
    cable_tray = _object(P4, 'SM_CornerWallCeiling400X70_V2_ElectricalCableRouting')
    for name, target, yaw in BANKS:
        for side in (-1, 1):
            delta = _rotate((side * 210, -130, 360), yaw)
            center = [target[i] + delta[i] for i in range(3)]
            placed('OperationsNative/' + name + '/Ceiling service panel' + str(side),
                ceiling, center, size=[200, 400, 40], yaw=yaw + 90, mounting='Ceiling')
            placed('OperationsNative/' + name + '/Ceiling suspension' + str(side),
                _object(P5, 'SM_Props_ConstructionPart119'),
                (center[0], center[1], 407.5), size=[7, 7, 55], mounting='Ceiling')
        delta = _rotate((0, -35, 350), yaw)
        placed('OperationsNative/' + name + '/Overhead cable trunk', cable_tray,
            [target[i] + delta[i] for i in range(3)], yaw=yaw, mounting='Ceiling')

    # Complete conversation islands: three native multipart seats around a
    # low game table and an animated hologram, with a broad eastern throughway.
    for index, (x, y, _) in enumerate(CONVERSATION_CENTERS):
        name = 'LoungeNative/Conversation ' + str(index + 1)
        placed(name + '/Low game table', _object(P1, 'SM_GoliathTable02'),
               (x, y, 32), height=64, solid=True)
        placed(name + '/Projector', _object(P5, 'SM_Props_ConstructionPart114'),
               (x, y, 70), height=12)
        placed(name + '/Animated game', _object(P5, 'SM_Props_ConstructionPart115'),
               (x, y, 96), height=40)

    # Actual owned fixture meshes anchor local task lighting; these lights
    # serve their furniture islands rather than changing room exposure/ambient.
    lamp = _object(P5, 'SM_Props_ConstructionPart118_Light')
    warm_lens = api['material']('M_OutpostCapsuleWarmLens', (1.0, .34, .055), emission=1.5)
    cool_lens = api['material']('M_OutpostTaskCoolLens', (.45, .75, 1.0), emission=1.5)
    silver = api['balanced'](api['load']('/Game/P1toP5_Bundle/P3_ComputerStation/Materials/Instances/Base/MI_Metal09_Silver.MI_Metal09_Silver'))
    receipt['local_lights'] = []

    def fixture_light(name, fixture_center, fixture_size, light_position, power, radius, color=(1.0, .66, .36)):
        actor = placed(name + '/Owned light housing', lamp, fixture_center,
                       size=fixture_size, mounting='Ceiling')
        # Only the native lamp lens becomes warm. Housing texture slots remain.
        actor.static_mesh_component.set_material(2, warm_lens if color[0] > .9 else cool_lens)
        api['light'](name + '/Task light', light_position, color,
                     power=power, radius=radius, shadow=False)
        receipt['local_lights'].append({'name': name, 'location': list(light_position),
            'lumens': power, 'radius_cm': radius, 'fixture': lamp, 'casts_shadows': False,
            'color': list(color)})

    # Small, motivated lights sit below each computer bank's suspended panels.
    # Their finite ranges illuminate controls/people without a global fill change.
    for index, (name, target, yaw) in enumerate(BANKS):
        color = (1.0, .76, .52) if index % 2 == 0 else (.58, .78, 1.0)
        for side in (-1, 1):
            delta = _rotate((side * 210, -130, 333), yaw)
            center = [target[i] + delta[i] for i in range(3)]
            fixture_light('OperationsNative/' + name + '/Local task ' + str(side),
                          center, [135, 32, 14], (center[0], center[1], 319),
                          850, 550, color=color)
    for name, target, yaw in COMMAND_PODS:
        delta = _rotate((0, -80, 0), yaw)
        x, y = target[0] + delta[0], target[1] + delta[1]
        group = 'OperationsNative/Command island ' + name
        fixture_light(group, (x, y, 390), [135, 32, 14], (x, y, 367),
                      950, 550, color=(.68, .85, 1.0))
        placed(group + '/Fixture suspension', _object(P5, 'SM_Props_ConstructionPart119'),
               (x, y, 416), size=[6, 6, 38], mounting='Ceiling')

    for index, (x, y, _) in enumerate(CONVERSATION_CENTERS):
        fixture_light('LoungeNative/Conversation ' + str(index + 1),
                      (x, y, 390), [130, 34, 14], (x, y, 367), 850, 650)
        placed('LoungeNative/Conversation ' + str(index + 1) + '/Fixture suspension',
               _object(P5, 'SM_Props_ConstructionPart119'),
               (x, y, 416), size=[6, 6, 38], mounting='Ceiling')

    # Three human-scale wardrobe archive capsules built from matched native
    # window frame and digital glass layers. Their source pivots stay shared.
    # Open fronts face west. Character previews can be added at the feet anchors;
    # the existing interactive wardrobe projection remains in its original spot.
    frame = _object(P4, 'SM_Window200X250_V1_Part1')
    glass = _object(P4, 'SM_Window200X250_V2_Part2_DigitalWindow')
    deck = _object(P3, 'SM_SciFiFloor200_100_V1')
    for index, (x, y, z) in enumerate(HOLOGRAM_BAYS):
        name = 'LoungeNative/Hologram bay ' + str(index + 1)
        placed(name + '/Foot deck', deck, (x, y, 10), size=[220, 240, 20], solid=True)
        placed(name + '/Top cap', ceiling, (x, y, 290), size=[220, 240, 40], mounting='Capsule')
        for side, location, yaw in [('Back', (x + 90, y, z), 0),
                                    ('North', (x - 10, y + 110, z), 90),
                                    ('South', (x - 10, y - 110, z), -90)]:
            for part, asset in [('Frame', frame), ('Animated glass', glass)]:
                actor = api['raw'](name + '/' + side + '/' + part, asset,
                                   location, yaw=yaw, solid=part == 'Frame')
                actor.tags = list(actor.tags) + [u.Name('OutpostRole:HologramCapsule')]
        emitter = placed(name + '/Emitter', _object(P5, 'SM_Props_ConstructionPart114'),
                         (x, y, 25), height=10)
        # Keep the copper/steel/projector detail; warm only its two glass slots.
        for slot in (4, 5):
            emitter.static_mesh_component.set_material(slot, warm_lens)
        for side in (-1, 1):
            for tier in (0, 1):
                upright = placed(name + '/Front chrome upright ' + str(side) + ':' + str(tier),
                    _object(P5, 'SM_Props_ConstructionPart119'),
                    (x - 90, y + side * 92, 80 + tier * 120),
                    size=[13, 13, 120], solid=True, mounting='Capsule')
                # Native copper brackets remain; silver tubing ties the bay to
                # the reference's readable illuminated metal capsule silhouette.
                component = upright.static_mesh_component
                for slot in range(component.get_num_materials()):
                    if slot != 1:
                        component.set_material(slot, silver)
        fixture_light(name, (x - 15, y, 265), [135, 32, 14],
                      (x - 20, y, 247), 450, 310)
    return receipt
