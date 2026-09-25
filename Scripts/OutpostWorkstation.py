"""A complete human-scale Goliath hub and two assembled diagnostic stations.

The primary desk moves into the room's visual foreground. Source child pivots,
rotations and scales remain intact; alternative demo screen variants are NOT
stacked on the same faces. Native clean technology materials replace three
accidentally damaged material assignments. Three native pendant fixtures add
local working pools; global lighting and exposure remain unchanged.
"""
from math import cos, radians, sin

ROOT = '/Game/P1toP5_Bundle/'
PRIMARY_PIVOT = (4200, -3200, 0)
UPGRADE_ACCESS = (4200, -2980, 100)
ENGINEER_FEET = (4400, -3000, 0)
TASK_LIGHT_POSITION = (4200, -2900, 290)


def _rotate(point, yaw):
    a = radians(yaw)
    return [point[0] * cos(a) - point[1] * sin(a),
            point[0] * sin(a) + point[1] * cos(a), point[2]]


def layout(workstation):
    """Pure source records, reusable for a bounded geometry/asset-path audit."""
    rows = []
    materials_root = ROOT + 'P1_WorkStation/Materials/Instances/'
    clean = {
        'MI_WorkPlan01_Damaged_slot2_4': 'MI_WorkPlan01_Cleaned_slot2_3',
        'MI_MediumScreen01_Damaged_slot1': 'MI_MediumScreen01_Cleaned_slot1',
        'MI_MediumScreen01_Damaged_slot2_Technology03': 'MI_MediumScreen01_Cleaned_slot2_Technology03',
    }
    for part in workstation['parts']:
        materials = []
        for path in part.get('default_materials', []):
            name = path.split('.')[-1]
            if name in clean:
                name = clean[name]
                path = materials_root + name + '.' + name
            materials.append(path)
        name = part['name']
        rows.append({'name': 'Engineering/Primary workstation/' + name,
            'asset': part['asset'],
            'location': [PRIMARY_PIVOT[i] + part['location_cm'][i] for i in range(3)],
            'rotation': [part.get('pitch_deg', 0), part['yaw_deg'], part.get('roll_deg', 0)],
            'scale': part.get('scale_xyz', [1, 1, 1]), 'materials': materials,
            'solid': not any(token in name for token in ('Screen', 'Cable', 'Light', 'WorkPlan'))})

    # Complete P3 console assemblies use their shared source offsets. These
    # are satellite diagnostics, each with its own chair facing the controls.
    parts = [('SM_TitaniumIndustryStation_V1_Part1', (0, 0, 0), 180),
             ('SM_TitaniumIndustryStation_V1_Part2', (0, -60, 120), 180),
             ('SM_SciFiScreen_V1_Part1', (0, 20, 150), 180),
             ('SM_SciFiScreen_V1_Part2', (0, 20, 150), 180),
             ('SM_SciFiScreen_V1_Part3', (0, 20, 150), 180)]
    for side, pivot, yaw in [('Port', (3600, -3550, 0), 135),
                             ('Starboard', (4800, -3550, 0), 225)]:
        for name, offset, child_yaw in parts:
            delta = _rotate(offset, yaw)
            asset = ROOT + 'P3_ComputerStation/Meshes/' + name
            rows.append({'name': 'Engineering/Work bay ' + side + '/' + name,
                'asset': asset + '.' + name,
                'location': [pivot[i] + delta[i] for i in range(3)],
                'rotation': [0, yaw + child_yaw, 0], 'scale': [1, 1, 1],
                'materials': [], 'solid': name == 'SM_TitaniumIndustryStation_V1_Part1'})
        delta = _rotate((0, -225, 0), yaw)
        for index in (1, 2, 3):
            name = 'SM_TitaniumIndustrySeat_V1_Part' + str(index)
            asset = ROOT + 'P3_ComputerStation/Meshes/' + name
            rows.append({'name': 'Engineering/Work bay ' + side + '/Chair' + str(index),
                'asset': asset + '.' + name,
                'location': [pivot[i] + delta[i] for i in range(3)],
                'rotation': [0, yaw, 0], 'scale': [.9, .9, .9],
                'materials': [], 'solid': index in (1, 2)})
    return rows


def add_task_lights(api):
    """Three owned pendant fixtures illuminate the central working furniture."""
    root = ROOT + 'P5_FruitSeller/Meshes/'
    lamp = root + 'SM_Props_ConstructionPart118_Light.SM_Props_ConstructionPart118_Light'
    stem = root + 'SM_Props_ConstructionPart119.SM_Props_ConstructionPart119'
    warm = api['material']('M_OutpostWorkstationWarmLens', (1.0, .46, .16), emission=1.5)
    cool = api['material']('M_OutpostWorkstationCoolLens', (.45, .76, 1.0), emission=1.5)
    fixtures = [('Primary', (4200, -3150), (1.0, .76, .52), 1100, 650, warm),
                ('Port diagnostics', (3685, -3465), (.58, .78, 1.0), 950, 550, cool),
                ('Starboard diagnostics', (4715, -3465), (.58, .78, 1.0), 950, 550, cool)]
    receipt = []
    for label, (x, y), color, power, radius, lens in fixtures:
        name = 'Engineering/Workstation light/' + label
        housing = api['place'](name + '/Owned lamp housing', lamp, (x, y, 328),
                                size=[135, 32, 14], solid=False)
        housing.static_mesh_component.set_material(2, lens)
        api['place'](name + '/Native pendant support', stem, (x, y, 385),
                     size=[6, 6, 100], solid=False)
        api['light'](name + '/Working pool', (x, y, 304), color,
                     power=power, radius=radius, shadow=False)
        receipt.append({'name': name, 'fixture_center': [x, y, 328],
                        'light_center': [x, y, 304], 'lumens': power,
                        'radius_cm': radius, 'casts_shadows': False})
    return receipt


def build(api):
    """Replace the lead's old workstation placement loop with this function."""
    rows = layout(api['PLAN']['workstation'])
    for record in rows:
        materials = [api['balanced'](api['load'](path)) for path in record['materials']]
        actor = api['raw'](record['name'], record['asset'], record['location'],
                           scale=record['scale'], rotation=record['rotation'],
                           materials=materials or None, solid=record['solid'])
        actor.static_mesh_component.set_simulate_physics(False)
    return {'primary_pivot': list(PRIMARY_PIVOT), 'upgrade_access': list(UPGRADE_ACCESS),
            'engineer_feet': list(ENGINEER_FEET), 'task_light_position': list(TASK_LIGHT_POSITION),
            'placements': rows, 'local_task_lights': add_task_lights(api), 'validation': 'Authored source only; rendered appearance and native collision require engine checks.'}