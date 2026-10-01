"""Wall-mounted diagnostics behind the existing Engineering workstation.

Native P4 frame and digital-glass pivots stay shared; Graph1/Graph2 are the
vendor's diagnostic graphics. Equipment housings, uprights and cable headers
form one mounted composition. No changes to Goliath, actors, services or lights.
All geometry stays in the rear wall band and above floor level.
"""
P4 = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/'
P5 = '/Game/P1toP5_Bundle/P5_FruitSeller/'
PREFIX = 'Engineering/Diagnostic backing/'
WALL_BAND_MIN = (3769, -4501, 29)
WALL_BAND_MAX = (4631, -4359, 396)
PROTECTED_APPROACH_MIN_Y = -4180


def _asset(root, name):
    return root + 'Meshes/' + name + '.' + name


def layout():
    """Pure placement recipe; sizes are local axes before yaw, in cm."""
    frame = _asset(P4, 'SM_Window400X200_V1_Part1')
    pane = _asset(P4, 'SM_Window400X200_V2_Part2_DigitalWindow')
    rows = []
    for index, x in enumerate((3995, 4405), 1):
        group = PREFIX + 'Diagnostic ' + str(index)
        # P4 walls have local X normal, Y width and Z up. +90 yaw faces north
        # into Engineering; shared floor pivot keeps the inset glass attached.
        for part, asset in [('Frame', frame), ('Native digital glass', pane)]:
            material = None
            if part == 'Native digital glass':
                name = 'MI_DigitalGlass_Window400X200_Graph' + str(index)
                material = P4 + 'Materials/Instances/Translucent/' + name + '.' + name
            rows.append({'name': group + '/' + part, 'asset': asset,
                'location': (x, -4410, 90), 'yaw': 90,
                'material': material, 'solid': part == 'Frame',
                'mounting': 'Shared native wall-frame pivot'})
    for side, x in [('Port', 3785), ('Starboard', 4615)]:
        rows.append({'name': PREFIX + side + ' wall upright',
            'asset': _asset(P5, 'SM_Props_ConstructionPart119'),
            'center': (x, -4440, 212.5), 'size': (30, 100, 365),
            'solid': True, 'mounting': 'Rear wall: back face y=-4490'})
    for index, x in enumerate((4000, 4400), 1):
        rows.append({'name': PREFIX + 'Overhead cable header ' + str(index),
            'asset': _asset(P4, 'SM_CornerWallCeiling400X70_V2_ElectricalCableRouting'),
            'center': (x, -4440, 380), 'size': (400, 100, 30),
            'solid': True, 'mounting': 'Joined upright tops; top z=395 below native ceiling z=398'})
    for index, x in enumerate((3995, 4405), 1):
        rows.append({'name': PREFIX + 'Electrical distribution ' + str(index),
            'asset': _asset(P4, 'SM_CornerWallCeiling400X70_V1_ElectricalEquipment'),
            'center': (x, -4450, 60), 'size': (350, 100, 60),
            'solid': True, 'mounting': 'Rear-wall housing; top z=90 supports frame bottom'})
    for side, x in [('Port', 3890), ('Starboard', 4510)]:
        rows.append({'name': PREFIX + side + ' integral lamp',
            'asset': _asset(P5, 'SM_Props_ConstructionPart118_Light'),
            'center': (x, -4380, 360), 'size': (100, 26, 10),
            'solid': False, 'mounting': 'Lamp top z=365 meets cable header underside'})
    return rows


def build(api):
    """Author only this mounted group, with actual transformed-bounds checks.

    Caller owns map save and final rendered review. This helper creates no
    gameplay systems, no light actors and no private material assets itself.
    """
    import unreal as u
    from OutpostGeometryUtils import mesh_union
    target = '/Game/OutpostSandbox/L_AsteroidOutpost'
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    package = world.get_path_name().split('.')[0]
    fresh = package.startswith('/Temp/Untitled') and api.get('TARGET') == target
    if package != target and not fresh:
        raise RuntimeError('Engineering backing is restricted to the private outpost')
    rows = layout()
    # Preflight all assets before removing a previous copy of this group.
    for row in rows:
        mesh = api['load'](row['asset'])
        if not isinstance(mesh, u.StaticMesh):
            raise RuntimeError('Backing requires an owned static mesh: ' + row['asset'])
        bounds = mesh.get_bounds()
        if min(bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z) <= 0:
            raise RuntimeError('Invalid native mesh bounds: ' + row['asset'])
        if row.get('material'):
            api['load'](row['material'])
    for actor in api['EAS'].get_all_level_actors():
        if actor.get_actor_label().startswith(PREFIX):
            api['EAS'].destroy_actor(actor)
    receipt = {'group': PREFIX, 'placements': [],
        'graphics': 'Native animated P4 Graph1 and Graph2; decorative diagnostic imagery',
        'scope': 'Back-wall band only; no Goliath, NPC, terminal, floor, exposure or light changes',
        'validation': 'Native bounds assertions; rendered quality and walking pending'}
    bounds_by_suffix = {}
    for row in rows:
        if 'location' in row:
            actor = api['raw'](row['name'], row['asset'], row['location'],
                               yaw=row['yaw'], solid=row['solid'])
        else:
            actor = api['place'](row['name'], row['asset'], row['center'],
                                 size=row['size'], solid=row['solid'])
        component = actor.static_mesh_component
        component.set_simulate_physics(False)
        if row.get('material'):
            material = api['balanced'](api['load'](row['material']))
            for slot in range(component.get_num_materials()):
                component.set_material(slot, material)
        actor.tags = list(actor.tags) + [u.Name('OutpostRole:EngineeringDiagnosticBacking'),
                                       u.Name('OutpostMount:RearWall')]
        center, extent = mesh_union(actor)
        low = [getattr(center, a) - getattr(extent, a) for a in ('x', 'y', 'z')]
        high = [getattr(center, a) + getattr(extent, a) for a in ('x', 'y', 'z')]
        for i in range(3):
            if low[i] < WALL_BAND_MIN[i] or high[i] > WALL_BAND_MAX[i]:
                raise RuntimeError('Diagnostic backing escaped mounted band: ' + row['name'])
        if high[1] >= PROTECTED_APPROACH_MIN_Y:
            raise RuntimeError('Diagnostic backing entered workstation approach')
        suffix = row['name'][len(PREFIX):]
        bounds_by_suffix[suffix] = (low, high)
        receipt['placements'].append({'name': row['name'], 'asset': row['asset'],
            'bounds_min': low, 'bounds_max': high, 'mounting': row['mounting'],
            'material': row.get('material'), 'solid': row['solid']})
    # Floor remains continuous: the lowest new part starts at z30; all parts
    # occupy only the wall band, >700cm behind the current Goliath approach.
    for index in (1, 2):
        frame_low, frame_high = bounds_by_suffix['Diagnostic ' + str(index) + '/Frame']
        pane_low, pane_high = bounds_by_suffix['Diagnostic ' + str(index) + '/Native digital glass']
        for axis in (0, 2):
            if pane_low[axis] < frame_low[axis] or pane_high[axis] > frame_high[axis]:
                raise RuntimeError('Native glass no longer sits inside its matching frame')
        _, housing_high = bounds_by_suffix['Electrical distribution ' + str(index)]
        if abs(housing_high[2] - frame_low[2]) > .1:
            raise RuntimeError('Diagnostic frame detached from distribution housing')
    receipt['mounted_bounds'] = {'minimum': list(WALL_BAND_MIN), 'maximum': list(WALL_BAND_MAX)}
    receipt['protected_approach_min_y'] = PROTECTED_APPROACH_MIN_Y
    return receipt
