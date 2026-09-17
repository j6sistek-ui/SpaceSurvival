"""Generate the pit stop hangar recipe: the interior half of the station target.

Plain Python, no Unreal. Reads measured mesh bounds and writes a recipe for
AuthorStationEditableLayout.py. Keeps the existing deck, terminals and benches, then adds the
target's dressing: amber overhead, mezzanine walkways along both long walls with stairs and
railings, a gantry over the parked ship, container stacks in the corners, wall pipes, banners,
a paint bay, and warm light spilling out of the mouth.

Frame: station-local cm. Deck top Z=-7.25. The flight lane, X -1900..1715, |Y|<=700, Z -10..967.5,
is kept empty of geometry: everything below the bay beams sits at |Y|>700, and anything that
crosses the lane sits above Z 975. The script asserts this rather than trusting it.
"""
from pathlib import Path
import json
import math

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / '.agent/local/StationVisualPass'
OUT = DATA / 'PitStopLayout.json'
DECK = -7.25
LANE = dict(x=(-1900.0, 1715.0), y=(-700.0, 700.0), z=(-10.0, 967.5))

meshes = {}
for row in json.loads((DATA / 'OwnerStationAssets.json').read_text(encoding='utf-8-sig'))['meshes']:
    meshes[row['asset'].split('/')[-1].split('.')[0]] = row
for row in json.loads((ROOT / 'Artifacts/Refresh/vendor-meshes.json').read_text(encoding='utf-8-sig')):
    name = row['path'].split('/')[-1].split('.')[0]
    meshes.setdefault(name, {'asset': row['path'], 'origin': row['origin'], 'extent': row['extent']})

base = json.loads((DATA / 'EditableLayout.json').read_text(encoding='utf-8-sig'))
parts = list(base['static_meshes'])
lights = []
names = {p['name'] for p in parts}
M = '/Game/SpaceSurvival/Materials/'


def place(name, mesh, center, bottom=None, yaw=0.0, scale=1.0, dimensions=None, materials=None, pitch=0.0, roll=0.0,
          shadows=True):
    """Place a mesh by the world-space centre of its bounds. `bottom` seats its lowest point at that Z."""
    assert name not in names, f'duplicate part name {name}'
    row = meshes[mesh]
    ext, org = row['extent'], row['origin']
    s = [scale] * 3
    if dimensions:
        s = [dimensions[i] / (2 * ext[i]) if dimensions[i] else s[i] for i in range(3)]
    a = math.radians(yaw)
    so = [org[i] * s[i] for i in range(3)]
    ro = [so[0] * math.cos(a) - so[1] * math.sin(a), so[0] * math.sin(a) + so[1] * math.cos(a), so[2]]
    z = bottom + ext[2] * s[2] if bottom is not None else center[2]
    mid = [center[0], center[1], z]
    part = {'name': name, 'asset': row['asset'], 'location': [round(mid[i] - ro[i], 3) for i in range(3)],
            'rotation': [pitch, yaw, roll], 'scale': [round(v, 5) for v in s]}
    if materials:
        part['materials'] = materials
    if not shadows:
        part['cast_shadows'] = False
    # world half-extents, yaw only
    ex = [abs(math.cos(a)) * ext[0] * s[0] + abs(math.sin(a)) * ext[1] * s[1],
          abs(math.sin(a)) * ext[0] * s[0] + abs(math.cos(a)) * ext[1] * s[1], ext[2] * s[2]]
    part['_box'] = [[mid[i] - ex[i] for i in range(3)], [mid[i] + ex[i] for i in range(3)]]
    parts.append(part)
    names.add(name)
    return part


def light(name, loc, color, intensity, radius, shadows=False):
    lights.append({'name': name, 'location': [round(v) for v in loc], 'color': color, 'intensity': intensity,
                   'attenuation_radius': radius, 'cast_shadows': shadows})


# ---------------------------------------------------------------- mezzanine walkways, both long walls
WALK_Z = 352.0          # walkway surface height: two stair flights, human scale
WALK_DEPTH = 260.0      # Y depth of the walkway
for side in (-1, 1):
    ycen = side * (1400 - WALK_DEPTH / 2)
    ext = meshes['SM_Floor_A']['extent']
    tile_w = 2 * ext[0]
    x = -1450.0
    i = 0
    while x < 1500:
        place(f'Walk_{"P" if side > 0 else "S"}_{i:02d}', 'SM_Floor_A', [x, ycen, 0], bottom=WALK_Z - 2 * ext[2],
              dimensions=[None, WALK_DEPTH, None])
        x += tile_w
        i += 1
    # railing along the inner edge, at |Y| = 1400 - depth, facing the bay
    # The railing's long axis is Y in its own frame; yaw 90 runs it along the bay.
    rext = meshes['SM_Railing_Center']['extent']
    rail_len = 2 * rext[1]
    x = -1450.0 + rail_len / 2
    i = 0
    while x < 1450:
        place(f'Rail_{"P" if side > 0 else "S"}_{i:02d}', 'SM_Railing_Center', [x, side * (1400 - WALK_DEPTH) + side * 40, 0],
              bottom=WALK_Z, yaw=90 if side > 0 else -90)
        x += rail_len
        i += 1
    # pillars under the walkway edge
    for j, px in enumerate(range(-1400, 1500, 480)):
        place(f'Pillar_{"P" if side > 0 else "S"}_{j}', 'SM_Pilar', [px, side * (1400 - WALK_DEPTH + 30), 0], bottom=DECK,
              dimensions=[None, None, WALK_Z - DECK - 4])
    # stairs down to the deck at the mouth end, running along X so they stay outside the lane
    # Two flights end to end along X at the mouth end, outside the lane, doubling the native rise.
    place(f'Stairs_{"P" if side > 0 else "S"}', 'SM_Stairs_A_Straight', [-1560, side * 980, 0], bottom=DECK,
          yaw=90 if side > 0 else -90, dimensions=[None, None, WALK_Z - DECK])
    # wall pipes above the walkway
    for j, px in enumerate(range(-1300, 1500, 700)):
        place(f'WallPipe_{"P" if side > 0 else "S"}_{j}', ['SM_Wall_Pipe_A', 'SM_Wall_Pipe_C', 'SM_Wall_Pipe_E', 'SM_Wall_Pipe_G'][j % 4],
              [px, side * 1385, 0], bottom=WALK_Z + 160 + (j % 2) * 90, yaw=0 if side > 0 else 180)
    # banners hanging from the walkway edge
    for j, px in enumerate((-900, 300, 1200)):
        place(f'Banner_{"P" if side > 0 else "S"}_{j}', ['SM_Flag_01', 'SM_Flag_02', 'SM_Flag_03'][j % 3],
              [px, side * (1400 - WALK_DEPTH - 30), 0], bottom=12, yaw=0 if side > 0 else 180)

# ---------------------------------------------------------------- gantry over the parked ship
# Hung from the bay beams, no legs: the first capture showed a leg standing between the services camera and
# ENGINEER MICA and another in front of the overview, and a floor this busy does not need two more columns.
fx = meshes['SM_Floor_A']['extent']
place('Gantry_Beam', 'SM_Floor_A', [850, 0, 0], bottom=985, dimensions=[220, 2 * 880 + 2 * fx[1] * .0 + 120, 22])
# Service tubes dropping from the beam to the wings' level, outside the lane.
for side in (-1, 1):
    place(f'Gantry_Drop_{"P" if side > 0 else "S"}', 'SM_Tube', [850, side * 760, 0], bottom=985 - 300,
          dimensions=[24, 24, 300])

# ---------------------------------------------------------------- container stacks in the corners
def stack(tag, cx, cy, yaw, count, mesh='SM_Crate'):
    z = DECK
    for k in range(count):
        p = place(f'{tag}_{k}', mesh, [cx + (k % 2) * 18, cy - (k % 2) * 14, 0], bottom=z, yaw=yaw + (k % 3) * 7, scale=1.0)
        z = p['_box'][1][2]
stack('Crates_A', -1480, -1180, 12, 3)
stack('Crates_B', -1300, -1250, -8, 2)
stack('Crates_C', 1500, 1180, 95, 3)
stack('Crates_D', 1560, 900, 80, 2)
stack('Cases_A', 1520, -1150, 0, 2, 'SM_ArmoryBox')
stack('Cases_B', -1500, 1100, 90, 2, 'SM_ArmoryBox')
for j, (cx, cy, yaw) in enumerate(((-1100, 1290, 0), (700, -1300, 180), (1250, -1300, 180))):
    place(f'Locker_{j}', 'SM_Cabinet_B', [cx, cy, 0], bottom=DECK, yaw=yaw, scale=1.3)

# ---------------------------------------------------------------- paint bay, a new service on the starboard wall
place('PaintBay_Platform', 'SM_Floor_A', [-1400, -1000, 0], bottom=DECK, dimensions=[420, 420, 16],
      materials=[M + 'M_Cyan.M_Cyan'])
place('PaintBay_Arch', 'SM_Portal', [-1400, -1000, 0], bottom=DECK + 16, yaw=0)
place('PaintBay_Screen', 'SM_Monitor', [-1400, -1330, 0], bottom=130, yaw=0, scale=1.3)
# SM_MonitorScreen ships with an empty material slot, which the layout library refuses; give it the bay's cyan.
place('PaintBay_ScreenFace', 'SM_MonitorScreen', [-1400, -1322, 0], bottom=142, yaw=0, scale=1.3,
      materials=[M + 'M_Cyan.M_Cyan'])

# ---------------------------------------------------------------- overhead fixtures and the warm light
for j, lx in enumerate(range(-1400, 1600, 350)):
    for side in (-1, 1):
        place(f'Fixture_{j}_{"P" if side > 0 else "S"}', 'SM_CeilingLight', [lx, side * 900, 0], bottom=976, scale=1.5,
              shadows=False)
        if j % 2 == 0:
            light(f'Amber_{j}_{"P" if side > 0 else "S"}', (lx, side * 700, 900), [1.0, 0.62, 0.30], 26000, 1500)
# 80000 burned the inside of the mouth frame white at this range; the spill should glow, not glare.
light('MouthSpill', (-1150, 0, 760), [1.0, 0.68, 0.38], 14000, 3000)
light('BayCore', (850, 0, 880), [1.0, 0.72, 0.45], 42000, 1900)
for side in (-1, 1):
    light(f'WalkUnder_{"P" if side > 0 else "S"}', (0, side * 1250, WALK_Z - 60), [0.25, 0.75, 1.0], 9000, 1400)
    light(f'WalkUnder2_{"P" if side > 0 else "S"}', (-1000, side * 1250, WALK_Z - 60), [0.25, 0.75, 1.0], 9000, 1400)
    light(f'WalkUnder3_{"P" if side > 0 else "S"}', (1000, side * 1250, WALK_Z - 60), [0.25, 0.75, 1.0], 9000, 1400)

# ---------------------------------------------------------------- the lane stays empty; prove it
def overlaps(box):
    (x0, y0, z0), (x1, y1, z1) = box
    return (x0 < LANE['x'][1] and x1 > LANE['x'][0] and y0 < LANE['y'][1] and y1 > LANE['y'][0]
            and z0 < LANE['z'][1] and z1 > LANE['z'][0])
intrusions = [p['name'] for p in parts if '_box' in p and overlaps(p['_box'])]
assert not intrusions, f'parts intrude on the flight lane: {intrusions}'

recipe = {
    'schema_version': 1,
    'purpose': 'Pit stop hangar: amber, dense, industrial. Gameplay anchors, deck collision and the docking lane remain native.',
    'exclude_harvested': base['exclude_harvested'] + ['StationDockEntryFrame_*'],
    'static_meshes': [{k: v for k, v in p.items() if k != '_box'} for p in parts],
    'point_lights': lights,
    'notes': base['notes'] + [
        'Mezzanine walkways at Z 470 along both long walls; stairs at the mouth end; lane stays empty below the bay beams.',
        'The old dock entry frame is excluded: the exterior body carries the mouth at exactly the admission gap.',
        'Paint bay platform and arch at (-1400, -1000); its service anchor is added natively by ASSStation.',
    ],
}
OUT.write_text(json.dumps(recipe, indent=2), encoding='utf-8')
print(json.dumps({'parts': len(parts), 'added': len(parts) - len(base['static_meshes']), 'lights': len(lights),
                  'recipe': str(OUT)}))
