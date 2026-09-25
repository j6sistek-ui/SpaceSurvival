"""Accessible roof observation gallery, authored through the caller's helpers.

No editor discovery or Unreal imports. Bounds and route elevations are explicit
so the lead can audit the stairs with the actual walker capsule after authoring.
The shared-pivot Genesis glass assemblies retain their matching frame inserts.
"""
from copy import deepcopy


LAYOUT = {
    'name': 'Observation Gallery',
    'floor_z': 520.0,
    'floor_bounds': [2900, -4400, 4300, -2400],
    'ceiling_underside_z': 1040.0,
    'entry': [2900, -3400, 520],
    'entry_clear_width': 220.0,
    'stairs': {
        'center_x': 2640.0, 'clear_width': 220.0,
        'start_y': -1760.0, 'end_y': -3320.0,
        'bottom_z': 0.0, 'top_z': 520.0,
        'step_count': 30, 'tread': 52.0, 'rise': 520.0 / 30,
        'max_supported_gap': 0.0,
        'side_guard_min_height': 110.0,
    },
    'landings': [
        {'name': 'Market landing', 'center': [2510, -1690, 0], 'size_xy': [480, 260]},
        {'name': 'Upper landing', 'center': [2640, -3440, 520], 'size_xy': [280, 240]},
        {'name': 'Entry bridge', 'center': [2890, -3400, 520], 'size_xy': [260, 220]},
    ],
    # Positions describe FEET, not actor centres. Stair audit should lift the
    # capsule by half-height and separately check each forward step transition.
    'route_feet': [[2400, -1600, 0], [2640, -1690, 0]]
                  + [[2640, -1760 - (i + .5) * 52, (i + 1) * 520 / 30]
                     for i in range(30)]
                  + [[2640, -3400, 520], [2890, -3400, 520],
                     [3150, -3400, 520], [3500, -3400, 520]],
    'gallery_route_feet': [[3500, -4000, 520], [3500, -3400, 520],
                           [3500, -2800, 520]],
    'social_positions': [[4000, -3950, 520], [4000, -2850, 520]],
}


def build(api):
    """Author the isolated gallery; return geometric evidence, not a test pass."""
    place, raw, box = api['place'], api['raw'], api['box']
    text, light = api['text'], api['light']
    assets = api['ASSETS']
    dark, cyan, pearl = api['DARK'], api['CYAN'], api['PEARL']
    prefix = 'Observation/'

    def blocker(name, center, size):
        actor = box(prefix + name, center, size, dark, True)
        actor.set_actor_hidden_in_game(True)
        return actor

    def deck(name, x, y, sx, sy, z, nx=1, ny=1):
        # New support sits directly on the engineering slab (roof top Z515).
        box('Ground/Observation ' + name, [x, y, z - 12], [sx, sy, 24], dark, True).set_actor_hidden_in_game(True)
        for ix in range(nx):
            for iy in range(ny):
                place(prefix + name + f'/Panel {ix}-{iy}', assets['floor_main']['asset'],
                      [x - sx / 2 + (ix + .5) * sx / nx,
                       y - sy / 2 + (iy + .5) * sy / ny, z - 9],
                      size=[sx / nx, sy / ny, 18])

    def guard(name, center_xy, length, floor, yaw=0):
        x, y = center_xy
        # Deliberate waist-high parapets, with actual collision all the way up.
        box(prefix + name + '/Parapet', [x, y, floor + 53], [22, length, 106], dark, True, yaw)
        box(prefix + name + '/Handrail', [x, y, floor + 108], [28, length, 8], pearl, True, yaw)

    # Broad supported start / turning landings keep every edge of the 220cm
    # stair connected. The bridge overlaps both upper landing and gallery deck.
    for landing in LAYOUT['landings']:
        x, y, z = landing['center']
        deck(landing['name'], x, y, *landing['size_xy'], z)
    deck('Gallery deck', 3600, -3400, 1400, 2000, 520, nx=4, ny=5)

    # Real colliding steps, never a visual staircase over an inaccessible wall.
    # Every tread's underside extends down to Z-20: no holes, floating steps or
    # thin collision surfaces. UE walker stepping is tested by the caller.
    stairs = LAYOUT['stairs']
    for i in range(stairs['step_count']):
        z = (i + 1) * stairs['rise']
        y = stairs['start_y'] - (i + .5) * stairs['tread']
        box(prefix + f'Stair/Tread {i + 1:02}', [2640, y, (z - 20) / 2],
            [220, 52, z + 20], pearl, True)
        if i % 5 == 4:
            box(prefix + f'Stair/Guidance {i + 1:02}', [2640, y + 23, z + .6],
                [196, 3, 1.2], cyan)

    # Six discrete structural cheek sections each side follow the rise. The
    # visible cheek is low enough to retain the view; an explicit invisible
    # safety wall reaches 110cm above the highest tread in its section, so it
    # cannot be climbed accidentally by the walker's step-up setting.
    for side in (-1, 1):
        x = 2640 + side * 126
        for segment in range(6):
            low = segment * 5 * stairs['rise']
            high = (segment + 1) * 5 * stairs['rise']
            y = -1760 - (segment + .5) * 260
            bottom, top = low - 20, high + 35
            name = f'Stair/Side {side} section {segment}'
            box(prefix + name, [x, y, (bottom + top) / 2],
                [32, 260, top - bottom], dark, True)
            blocker(name + '/Safety', [x, y, (low + high + 110) / 2],
                    [32, 260, high - low + 110])
    guard('Upper landing west guard', (2489, -3440), 260, 520)
    guard('Upper landing south guard', (2640, -3571), 300, 520, 90)
    guard('Bridge south guard', (2850, -3521), 320, 520, 90)
    guard('Bridge north guard', (2850, -3279), 180, 520, 90)

    # A true panoramic west wall: 8.4m of glass either side of the entry slot.
    # Frames and glass remain registered at their original floor pivot.
    def glass_bay(name, x, y, width, yaw=0):
        for suffix, role in [('Frame', 'window_frame_4m'), ('Glass', 'window_glass_4m')]:
            raw(prefix + name + '/' + suffix, assets[role]['asset'],
                [x, y, 520], yaw, [1, width / 400, 1.92])
        block = box(prefix + name + '/Glass collision', [x, y, 760],
                    [20, width, 480], dark, True, yaw)
        block.set_actor_hidden_in_game(True)

    for index, y in enumerate((-4190, -3770, -3030, -2610)):
        glass_bay('West view ' + str(index), 2900, y, 420)
    for y, yaw, side in [(-4400, 90, 'South'), (-2400, -90, 'North')]:
        for index, x in enumerate((3250, 3950)):
            glass_bay(side + ' view ' + str(index), x, y, 700, yaw)
        box(prefix + side + ' lintel', [3600, y, 1020], [1440, 70, 40], dark)
    for index, y in enumerate((-3980, -2820)):
        box(prefix + f'West lintel {index}', [2900, y, 1020], [70, 840, 40], dark)
        box(prefix + f'West sill guidance {index}', [2920, y, 545], [5, 790, 5], cyan)

    # Rear service wall ties the gallery back into the station instead of
    # suggesting a free-floating glass cube. Its kit storage panels stay at
    # authored human scale; the clear centre route remains 4m wide.
    blocker('Rear wall collision', [4300, -3400, 780], [30, 2000, 520])
    box(prefix + 'Rear wall structure', [4320, -3400, 780], [40, 2000, 520], dark)
    for index in range(5):
        y = -4200 + index * 400
        for z in (520, 720):
            raw(prefix + f'Rear wall panel {index}-{z}', assets['wall_main']['asset'],
                [4280, y, z], 180)
    box(prefix + 'Entry header', [2900, -3400, 1020], [70, 320, 40], dark)
    signs = [text(prefix + 'Arrival sign', 'OBSERVATION / 01', [2858, -3400, 955], 180, 24),
             text(prefix + 'Return sign', 'MARKET / DOWN', [2942, -3400, 955], 0, 19)]
    _one_sided_signs(api, signs)

    # Sealed ceiling with authored Genesis panel undersides, clear height 520.
    box(prefix + 'Roof structure', [3600, -3400, 1100], [1500, 2100, 40], dark, True)
    for ix in range(4):
        for iy in range(5):
            place(prefix + f'Ceiling panel {ix}-{iy}', assets['ceiling_main']['asset'],
                  [3075 + ix * 350, -4200 + iy * 400, 1060], size=[350, 400, 40])
    for x in (3100, 4100):
        box(prefix + f'Ceiling guidance {x}', [x, -3400, 1035], [5, 1840, 5], cyan)
    light(prefix + 'Warm social pool', [3900, -3400, 940], (1, .76, .52), 1800, 1400)
    light(prefix + 'View rim', [3060, -3400, 910], (.32, .7, 1), 950, 1200)
    light(prefix + 'Stair wash', [2480, -2640, 780], (.48, .72, 1), 1300, 1500)

    # Complete ComputerStation seat assemblies, not isolated mesh parts. Native
    # +Y-facing seats yaw90 face west toward the pad, with a 4m clear walk lane.
    root = '/Game/P1toP5_Bundle/P3_ComputerStation/Meshes/'
    for index, y in enumerate((-3930, -2870)):
        for part in (1, 2, 3):
            name = 'SM_TitaniumIndustrySeat_V1_Part' + str(part)
            raw(prefix + f'View seat {index}/Part {part}', root + name + '.' + name,
                [4010, y, 520], 90)
        blocker(f'View seat {index}/Collision', [4010, y, 580], [140, 120, 120])

    result = deepcopy(LAYOUT)
    result['validation'] = 'Geometry authored; engine walk, capsule and rendered appearance checks pending.'
    return result


def _one_sided_signs(api, actors):
    """Keep the engine font/mask graph; cull only each sign's backward face."""
    u = api['u']
    lib, edit = u.EditorAssetLibrary, u.MaterialEditingLibrary
    source = '/Engine/EngineMaterials/UnlitText'
    target = '/Game/OutpostSandbox/Materials/M_ObservationTextOneSided'
    material = api['load'](target) if lib.does_asset_exist(target) else lib.duplicate_asset(source, target)
    if not isinstance(material, u.Material):
        raise RuntimeError('Observation text requires a private copy of the engine text material')
    if material.get_editor_property('two_sided'):
        material.set_editor_property('two_sided', False)
        edit.recompile_material(material)
    lib.save_loaded_asset(material)
    for actor in actors:
        component = actor.get_component_by_class(u.TextRenderComponent)
        if component is None:
            raise RuntimeError('Observation sign is missing its text component')
        component.set_text_material(material)
    return material.get_path_name()


def repair_existing(api):
    """Focused saved-map repair; does not rebuild the gallery or save the level.

    Apply before OutpostRoofDetails.build(api), whose absolute recipe reconciles
    the Engineering details to the repaired Z515 support. Other roofs, physical
    gallery floor and signs' positions/text stay unchanged.
    """
    u, eas = api['u'], api['EAS']
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name().split('.')[0] != '/Game/OutpostSandbox/L_AsteroidOutpost':
        raise RuntimeError('Observation repair is restricted to the private outpost map')
    actors = {actor.get_actor_label(): actor for actor in eas.get_all_level_actors()}
    roof = actors['Engineering/Roof structure']
    signs = [actors['Observation/Arrival sign'], actors['Observation/Return sign']]
    mesh = roof.static_mesh_component.static_mesh
    if mesh.get_path_name() != '/Engine/BasicShapes/Cube.Cube':
        raise RuntimeError('Engineering structural roof differs from its authored cube')
    location, scale = roof.get_actor_location(), roof.get_actor_scale3d()
    before = {'center_z': location.z, 'height': mesh.get_bounds().box_extent.z * 2 * scale.z}
    location.z = 477.0
    scale.z = 76.0 / (mesh.get_bounds().box_extent.z * 2)
    roof.set_actor_location(location, False, False)
    roof.set_actor_scale3d(scale)
    text_material = _one_sided_signs(api, signs)
    # Retain truthful placement records if this is used from an authoring batch.
    for row in api.get('RECORDS', []):
        if row['name'] == 'Engineering/Roof structure':
            row['location'] = [location.x, location.y, location.z]
            row['scale'] = [scale.x, scale.y, scale.z]
    return {'roof_before': before, 'roof_bottom_z': 439.0, 'roof_top_z': 515.0,
            'gallery_floor_z': 520.0, 'private_text_material': text_material,
            'engine_text_material_modified': False, 'gallery_geometry_changed': False}
