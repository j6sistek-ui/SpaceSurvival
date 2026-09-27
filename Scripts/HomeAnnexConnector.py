"""Add only the surveyed home-annex connector through lead-owned helpers.

No Unreal imports, map loads, saves, old-actor edits or apartment/door creation.
All dimensions are centimetres. The lead supplies the AuthorOutpostSandbox-style
API and owns native placement, collision, appearance and walking validation.
"""
import math


PREFIX = 'HomeHub/Connector/'
ENTRANCE = [6120.0, 4100.0, -120.0]
ROOF_UNDERSIDE = 300.0
CLEAR_WIDTH = 220.0
DECK_WIDTH = 280.0
LAMP_ASSET = ('/Game/P1toP5_Bundle/P5_FruitSeller/Meshes/'
              'SM_Props_ConstructionPart118_Light.SM_Props_ConstructionPart118_Light')


def layout():
    """Return the fixed surveyed route; feet are not capsule centres."""
    route = [[4400, 1975, 0], [4700, 1975, 0], [4880, 1975, 0]]
    route += [[4925 + i * 50, 1975, -(i + 1) * 20] for i in range(6)]
    route += [[5350, 1975, -120], [5700, 1975, -120], [5900, 1975, -120]]
    route += [[5900, y, -120] for y in (2250, 2600, 3000, 3400, 3800, 4100)]
    route += [[6010, 4100, -120], list(ENTRANCE)]
    return {
        'prefix': PREFIX,
        'entrance_feet': list(ENTRANCE),
        'route_feet': route,
        'return_route_feet': list(reversed(route)),
        'clear_width_cm': CLEAR_WIDTH,
        'step_count': 6,
        'step_rise_cm': 20,
        'step_tread_cm': 50,
        'roof_underside_z': ROOF_UNDERSIDE,
        'roof_top_z': 340,
        'existing_bridge_min_z': 415,
        'deck_rectangles': [
            {'name': 'Upper approach', 'bounds_xy': [4500, 1835, 4900, 2115], 'floor_z': 0},
            {'name': 'Lower approach', 'bounds_xy': [5200, 1835, 6040, 2115], 'floor_z': -120},
            {'name': 'North passage', 'bounds_xy': [5760, 2115, 6040, 4240], 'floor_z': -120},
            {'name': 'Home landing', 'bounds_xy': [6040, 3960, 6140, 4240], 'floor_z': -120},
        ],
        'stairs_bounds_xy': [4900, 1835, 5200, 2115],
        'existing_entry_support_bounds_xy': [3900, 1600, 4500, 2350],
        'validation': 'Authored geometry only; lead must validate live collision and both walking directions.',
    }


def build(api):
    """Create scoped new actors; fail rather than overwrite an earlier build."""
    required = ('EAS', 'load', 'raw', 'place', 'box', 'text', 'light',
                'ASSETS', 'DARK', 'CYAN', 'PEARL')
    for key in required:
        if key not in api:
            raise KeyError('Home connector requires helper: ' + key)
    previous = [a.get_actor_label() for a in api['EAS'].get_all_level_actors()
                if a.get_actor_label().startswith(PREFIX)]
    if previous:
        raise RuntimeError('Home connector already exists; no existing actors were changed: ' + previous[0])

    assets = api['ASSETS']
    roles = ('floor_main', 'wall_main', 'wall_small', 'ceiling_main',
             'window_frame_4m', 'window_glass_4m')
    paths = {key: assets[key]['asset'] for key in roles}
    paths['fixture'] = LAMP_ASSET
    meshes = {key: api['load'](path) for key, path in paths.items()}
    if any(mesh is None for mesh in meshes.values()):
        raise RuntimeError('Home connector asset preflight failed before placement')
    frame_bounds = meshes['window_frame_4m'].get_bounds()
    frame_origin = [frame_bounds.origin.x, frame_bounds.origin.y, frame_bounds.origin.z]
    frame_size = [frame_bounds.box_extent.x * 2, frame_bounds.box_extent.y * 2,
                  frame_bounds.box_extent.z * 2]
    if min(frame_size) <= .001:
        raise RuntimeError('Home connector window frame has invalid bounds')

    result = layout()
    result.update(placements=[], glass_pairs=[], floor_supports=[], wall_blockers=[], lights=[])
    dark, cyan, pearl = api['DARK'], api['CYAN'], api['PEARL']

    def record(kind, name, **data):
        row = dict(kind=kind, name=PREFIX + name, **data)
        result['placements'].append(row)
        return row

    def cube(name, center, size, material=dark, solid=False, yaw=0, hidden=False):
        actor = api['box'](PREFIX + name, center, size, material, solid, yaw)
        if hidden:
            actor.set_actor_hidden_in_game(True)
            actor.static_mesh_component.set_visibility(False)
        record('structural_box', name, center=list(center), size=list(size), yaw=yaw,
               solid=solid, hidden=hidden)
        return actor

    def mesh(name, role, center, size, yaw=0):
        actor = api['place'](PREFIX + name, paths[role], center, size=size, yaw=yaw, solid=False)
        record('kit_mesh', name, asset=paths[role], center=list(center), size=list(size), yaw=yaw)
        return actor

    def deck(name, bounds, z, bottom=None):
        x0, y0, x1, y1 = bounds
        sx, sy = x1 - x0, y1 - y0
        bottom = z - 64 if bottom is None else bottom
        center = [(x0 + x1) / 2, (y0 + y1) / 2]
        cube(name + '/Physical support', center + [(z + bottom) / 2],
             [sx, sy, z - bottom], solid=True, hidden=True)
        result['floor_supports'].append(dict(name=PREFIX + name, bounds_xy=list(bounds),
                                             floor_z=z, bottom_z=bottom))
        nx, ny = max(1, math.ceil(sx / 400)), max(1, math.ceil(sy / 400))
        for ix in range(nx):
            for iy in range(ny):
                mesh(name + '/Deck %d-%d' % (ix, iy), 'floor_main',
                     [x0 + (ix + .5) * sx / nx, y0 + (iy + .5) * sy / ny, z - 9],
                     [sx / nx, sy / ny, 18])
        # A connected structural spine and its kit facing make the undercroft
        # read as a supported station extension, with no invented rock anchors.
        cube(name + '/Spine', center + [z - 100], [sx, sy, 72], dark)
        mesh(name + '/Underside cladding', 'ceiling_main', center + [z - 138], [sx, sy, 14])

    def roof(name, bounds):
        x0, y0, x1, y1 = bounds
        sx, sy = x1 - x0, y1 - y0
        cube(name + '/Roof structure', [(x0 + x1) / 2, (y0 + y1) / 2, 324],
             [sx, sy, 32], dark, True)
        nx, ny = max(1, math.ceil(sx / 400)), max(1, math.ceil(sy / 400))
        for ix in range(nx):
            for iy in range(ny):
                mesh(name + '/Ceiling %d-%d' % (ix, iy), 'ceiling_main',
                     [x0 + (ix + .5) * sx / nx, y0 + (iy + .5) * sy / ny, 304],
                     [sx / nx, sy / ny, 8])

    def glass(name, x, y, width, floor, yaw=0, glass_bottom=None):
        # Fit the FRAME once, then apply its identical transform to the pane.
        # Fitting each asset independently breaks the vendor's shared pivot.
        bottom = floor + 60 if glass_bottom is None else glass_bottom
        top = ROOF_UNDERSIDE
        scale = [1, width / frame_size[1], (top - bottom) / frame_size[2]]
        center = [x, y, (bottom + top) / 2]
        angle = math.radians(yaw)
        local = [frame_origin[i] * scale[i] for i in range(3)]
        offset = [local[0] * math.cos(angle) - local[1] * math.sin(angle),
                  local[0] * math.sin(angle) + local[1] * math.cos(angle), local[2]]
        pivot = [center[i] - offset[i] for i in range(3)]
        for suffix, role in (('Frame', 'window_frame_4m'), ('Glass', 'window_glass_4m')):
            api['raw'](PREFIX + name + '/' + suffix, paths[role], pivot, yaw, scale, False)
            record('paired_window', name + '/' + suffix, asset=paths[role],
                   location=list(pivot), scale=list(scale), yaw=yaw)
        result['glass_pairs'].append(dict(name=PREFIX + name, pivot=pivot, scale=scale,
                                          yaw=yaw, frame_bounds_size=frame_size))
        height = top - floor
        cube(name + '/Collision', [x, y, floor + height / 2], [30, width, height],
             dark, True, yaw, True)
        result['wall_blockers'].append(dict(name=PREFIX + name, center=[x, y, floor + height / 2],
                                            size=[30, width, height], yaw=yaw))
        # Native textured lower skins continue down over the structural spine.
        if bottom > floor:
            mesh(name + '/Lower cladding', 'wall_small', [x, y, (floor - 140 + bottom) / 2],
                 [22, width, bottom - floor + 140], yaw)
        else:
            mesh(name + '/Spine cladding', 'wall_small', [x, y, floor - 70], [22, width, 140], yaw)
        cube(name + '/Sill', [x, y, bottom], [36, width, 10], pearl, False, yaw)
        cube(name + '/Roof rail', [x, y, 294], [36, width, 12], dark, False, yaw)

    def wall_run(name, fixed, start, end, floor, along_x=False, glass_bottom=None):
        count = max(1, math.ceil((end - start) / 400))
        width = (end - start) / count
        for index in range(count):
            middle = start + (index + .5) * width
            glass(name + '/Bay %02d' % index, middle if along_x else fixed,
                  fixed if along_x else middle, width, floor,
                  90 if along_x else 0, glass_bottom)

    for row in result['deck_rectangles']:
        deck(row['name'], row['bounds_xy'], row['floor_z'])
    for index in range(6):
        x0, z = 4900 + index * 50, -(index + 1) * 20
        name = 'Stairs/Tread %02d' % (index + 1)
        deck(name, [x0, 1835, x0 + 50, 2115], z, bottom=-184)
        # Narrow guides sit just above each real nosing, outside the central
        # 160cm walking strip; the lead supplies the approved dim cyan material.
        for side in (-1, 1):
            cube(name + '/Guide ' + str(side), [x0 + 4, 1975 + side * 95, z + .4],
                 [3, 24, .8], cyan)

    # Roof pieces meet edge-to-edge: avoid coplanar panels at either turn.
    roof('East canopy', [4500, 1835, 6040, 2115])
    roof('North canopy', [5760, 2115, 6040, 4240])
    roof('Home canopy', [6040, 3960, 6140, 4240])
    for side, y in (('South', 1850), ('North', 2100)):
        wall_run(side + '/Upper', y, 4500, 4900, 0, True)
        wall_run(side + '/Stair', y, 4900, 5200, -120, True, glass_bottom=-120)
        wall_run(side + '/Lower', y, 5200, 5760 if side == 'North' else 6040, -120, True)
    wall_run('North passage/West', 5775, 2115, 4240, -120)
    wall_run('North passage/East', 6025, 1850, 3960, -120)
    wall_run('Home landing/North', 4225, 5760, 6140, -120, True)
    wall_run('Home landing/South', 3975, 6040, 6140, -120, True)

    # Mounted, modest local lighting. No global exposure or existing lights.
    for index, (x, y) in enumerate(((4730, 1975), (5410, 1975), (5900, 2250),
                                    (5900, 2975), (5900, 3700), (5990, 4100))):
        name = 'Lighting/Fixture %02d' % index
        mesh(name + '/Native housing', 'fixture', [x, y, 282], [90, 30, 18])
        api['light'](PREFIX + name + '/Pool', [x, y, 265], (0.66, 0.82, 1.0),
                     power=2400, radius=720, shadow=False)
        result['lights'].append(dict(name=PREFIX + name, location=[x, y, 265],
                                     lumens=2400, radius_cm=720))

    for name, words, x, y, yaw in (
            ('Arrival', 'HOME  /  PRIVATE QUARTERS', 4620, 1975, 180),
            ('Turn', 'HOME  /  NORTH', 5900, 2190, -90),
            ('Return', 'EXCHANGE  /  RETURN', 5900, 3900, 90)):
        cube('Signs/' + name + '/Board', [x, y, 249], [12, 205, 48], dark, False, yaw)
        rad = math.radians(yaw)
        api['text'](PREFIX + 'Signs/' + name, words,
                    [x + math.cos(rad) * 7, y + math.sin(rad) * 7, 249], yaw, 9)
        record('sign', 'Signs/' + name, words=words, center=[x, y, 249], yaw=yaw)

    result['actor_count'] = len(result['placements']) + len(result['lights'])
    result['source_assets_modified'] = False
    result['existing_actors_modified'] = False
    result['apartment_and_door_authored'] = False
    return result
