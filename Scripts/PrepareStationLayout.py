"""Prepare the initial station visual layout from inspected owner meshes.
Does not replace an existing owner-edited Blueprint. UE authoring consumes this recipe.
"""
from pathlib import Path
import json
import math


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / '.agent/local/StationVisualPass'
asset_rows = json.loads(
    (DATA / 'OwnerStationAssets.json').read_text(encoding='utf-8')
)['meshes']
meshes = {row['asset'].split('.')[-1]: row for row in asset_rows}
parts = []
lights = []

def place(name, mesh, center, bottom=0, yaw=0, scale=1, dimensions=None, materials=None):
    mesh_data = meshes[mesh]
    extent = mesh_data['extent']
    mesh_origin = mesh_data['origin']
    component_scale = [scale] * 3
    if dimensions:
        component_scale = [
            dimensions[axis] / (2 * extent[axis])
            if dimensions[axis] else component_scale[axis]
            for axis in range(3)
        ]
    yaw_radians = math.radians(yaw)
    yaw_cosine = math.cos(yaw_radians)
    yaw_sine = math.sin(yaw_radians)
    scaled_origin = [mesh_origin[axis] * component_scale[axis] for axis in range(3)]
    rotated_origin = [
        scaled_origin[0] * yaw_cosine - scaled_origin[1] * yaw_sine,
        scaled_origin[0] * yaw_sine + scaled_origin[1] * yaw_cosine,
        scaled_origin[2],
    ]
    midpoint = [center[0], center[1], bottom + extent[2] * component_scale[2]]
    part = {
        'name': name,
        'asset': mesh_data['asset'],
        'location': [round(midpoint[axis] - rotated_origin[axis], 4) for axis in range(3)],
        'rotation': [0, yaw, 0],
        'scale': component_scale,
    }
    if materials:
        part['materials'] = materials
    parts.append(part)
    return part


# Replace the thin, oversized original panels with a regular, physically scaled deck.
for x in range(10):
    for y in range(8):
        floor_mesh = meshes['SM_Floor_A']
        thickness = 2 * floor_mesh['extent'][2]
        place(
            f'Deck_{x:02d}_{y:02d}',
            'SM_Floor_A',
            [-1530 + x * 340, -1225 + y * 350],
            bottom=-7.25 - thickness,
            dimensions=[340, 350, None],
        )

# Full freestanding control desks. UI is a separate fitted surface sharing the terminal pivot.
for name, center, yaw in [
    ('RepairTerminal', [-820, -1120], 90),
    ('UpgradeTerminal', [200, -1120], 90),
    ('RecordTerminal', [-1100, 1040], -90),
    ('SystemsTerminal', [0, 1120], -90),
    ('MicaTerminal', [1010, 1020], -90),
    ('LaunchTerminal', [950, -805], 90),
]:
    terminal = place(name, 'SM_Terminal_A', center, bottom=-8, yaw=yaw, scale=0.85)
    screen = dict(terminal)
    screen['name'] = name + '_Screen'
    screen['asset'] = meshes['SM_Terminal_A_UI']['asset']
    parts.append(screen)

# A maintained workshop along the north wall; the robot works beside its console.
for name, center in [
    ('EngineeringBench', [1220, 1260]),
    ('DiagnosticBench', [-550, 1250]),
    ('RepairBench', [-1100, -1280]),
]:
    yaw = 180 if center[1] > 0 else 0
    place(name, 'SM_Desk_A_v1', center, bottom=-8, yaw=yaw)
    place(
        name + '_Laptop', 'SM_Laptop', [center[0] - 60, center[1]],
        bottom=84, yaw=yaw, scale=0.85,
    )
    place(
        name + '_Lamp', 'SM_TableLamp', [center[0] + 105, center[1]],
        bottom=84, yaw=yaw,
    )
    place(
        name + '_HandScanner', 'SM_HScanner_Open', [center[0] + 30, center[1] - 15],
        bottom=84, yaw=yaw, scale=0.85,
    )
    place(
        name + '_Chair', 'SM_Stool', [center[0], center[1] + (-115 if center[1] > 0 else 110)],
        bottom=-8, yaw=yaw, scale=1.2,
    )

# Storage banks and stocked shelves sit outboard of the landing/foot traffic corridor.
for index, (x, y, yaw) in enumerate([
    (-1380, -1260, 0),
    (-470, -1260, 0),
    (500, 1260, 180),
    (1450, 1020, -90),
]):
    place(f'Storage_{index}', 'SM_Cabinet_A', [x, y], bottom=-8, yaw=yaw, scale=0.85)
    place(f'Storage_{index}_Shelf', 'SM_Shelf_A_v2', [x, y], bottom=61, yaw=yaw, scale=0.9)
    for supply_index, mesh in enumerate(['SM_MedBottle', 'SM_HScanner_Closed', 'SM_CommDevice']):
        place(
            f'Storage_{index}_Supply_{supply_index}', mesh, [x - 50 + supply_index * 50, y],
            bottom=188, yaw=yaw, scale=1.0,
        )

for index, (x, y) in enumerate([(1220, 1260), (-550, 1250), (-1100, -1280)]):
    place(
        f'FirstAid_{index}', 'SM_FirstAidKit', [x + 45, y + 15],
        bottom=84, yaw=180 if y > 0 else 0, scale=0.65,
    )
    place(f'WasteBin_{index}', 'SM_WasteBin', [x + 185, y - 10], bottom=-8, scale=1.1)

# Low-intensity task pools give equipment clusters focus; only two overhead lights cast shadows.
for index, (x, y, color) in enumerate([
    (-1050, -850, [1, 0.69, 0.40]),
    (1050, 850, [0.43, 0.72, 1]),
    (-950, 850, [0.43, 0.72, 1]),
    (950, -850, [1, 0.72, 0.48]),
]):
    lights.append({
        'name': f'OverheadPool_{index}',
        'location': [x, y, 570],
        'color': color,
        'intensity': 36000,
        'attenuation_radius': 1050,
        'cast_shadows': index < 2,
    })

for index, (x, y) in enumerate([
    (1220, 1180), (-550, 1160), (-1100, -1180), (200, -1120), (0, 1120),
]):
    lights.append({
        'name': f'ConsolePool_{index}',
        'location': [x, y, 260],
        'color': [0.30, 0.67, 1] if index % 2 else [1, 0.60, 0.26],
        'intensity': 5500,
        'attenuation_radius': 480,
        'cast_shadows': False,
    })

recipe = {
    'schema_version': 1,
    'purpose': 'Initial editable station workshop composition; asset-only, gameplay anchors remain native.',
    'exclude_harvested': [
        'Shell_SM_Floor_01_*', 'Shell_SM_Monitor_*', 'Shell_SM_MonitorScreen_*', 'BayLight_*',
    ],
    'static_meshes': parts,
    'point_lights': lights,
    'notes': [
        'Main entry corridor and floor collision remain native.',
        'Deck top is Z=-7.25, matching the existing planted sole; collision top remains Z=-10. Decorative props have no collision.',
        'Service terminals align with existing interaction areas; Launch terminal is outboard of the entry corridor.',
        'Do not reset the Blueprint after owner edits; edit its components directly.',
    ],
}
recipe_path = DATA / 'EditableLayout.json'
recipe_path.write_text(json.dumps(recipe, indent=2) + '\n', encoding='utf-8')
print(json.dumps({
    'recipe': str(recipe_path),
    'static_meshes': len(parts),
    'lights': len(lights),
    'floor_tiles': 80,
}))
