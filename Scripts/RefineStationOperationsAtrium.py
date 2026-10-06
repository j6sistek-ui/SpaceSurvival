"""Refine the saved T Operations, R archive and central reception in place.

Only apply(ctx) mutates actors. The lead owns map load/save, rollback and native
visual/walking validation. Vendor assets, floors, doors and the apartment remain
unchanged. Surplus complete banks are reversibly hidden, never deleted.
"""
import math

P4 = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Meshes/'
PRIVATE = '/Game/OutpostSandbox/Materials/'
CREW = '/Game/SpaceSurvival/Licensed/StationAssets/AlienCrew/'
GRAPHITE = PRIVATE + 'M_OutpostGraphite'
PEARL = PRIVATE + 'M_OutpostPearl'
CYAN = PRIVATE + 'M_OutpostCyan'
SCREEN = '/Game/BuildingLibrary/Assembled/Screens/P3_CompleteThreePartScreen'
BLUE = (.58, .81, 1.)
BANKS = ('North Navigation', 'North Communications', 'South Logistics',
         'South Science', 'East Tracking', 'East Contracts')
PODS = (
    ('Port South', (7400, -210, 0), (7100, -950, 0), 0, 'Teal'),
    ('Port North', (7400, 210, 0), (7100, 950, 0), 180, 'Amber'),
    ('Starboard South', (8130, -210, 0), (8250, -950, 0), 0, 'Jade'),
    ('Starboard North', (8130, 210, 0), (8250, 950, 0), 180, 'Pale'),
)


def _one(actors, label):
    rows = [a for a in actors if a.get_actor_label() == label]
    if len(rows) != 1:
        raise RuntimeError('Expected one preserved actor: ' + label + ' (' + str(len(rows)) + ')')
    return rows[0]


def _group(actors, prefix, count=None):
    rows = [a for a in actors if a.get_actor_label().startswith(prefix)]
    if not rows or (count is not None and len(rows) != count):
        raise RuntimeError('Saved assembly changed: ' + prefix + ' (' + str(len(rows)) + ')')
    return rows


def _rotate(point, yaw):
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    return (c * point[0] - s * point[1], s * point[0] + c * point[1], point[2])


def _rigid(ctx, actors, source, target, yaw=0):
    for actor in actors:
        p, r = actor.get_actor_location(), actor.get_actor_rotation()
        q = _rotate((p.x - source[0], p.y - source[1], p.z - source[2]), yaw)
        ctx.move(actor, tuple(target[i] + q[i] for i in range(3)),
                 (r.pitch, r.yaw + yaw, r.roll))


def _pose(actor):
    p, r, s = actor.get_actor_location(), actor.get_actor_rotation(), actor.get_actor_scale3d()
    return (p.x, p.y, p.z, r.pitch, r.yaw, r.roll, s.x, s.y, s.z)


def _property(ctx, actor, name, value):
    old = actor.get_editor_property(name)
    ctx.records.append({'kind': 'property', 'actor': actor.get_path_name(),
                        'property': name, 'before': str(old), 'after': str(value)})
    actor.set_editor_property(name, value)


def _panel(ctx, label, center, yaw, dimensions='400X200', variant='Graph1'):
    """Complete native frame/pane, one rigid assembly with native proportions."""
    from OutpostGeometryUtils import mesh_union
    frame = ctx.raw(label + '/Frame', P4 + 'SM_Window' + dimensions + '_V1_Part1',
                    center, (0, yaw, 0), collision=True)
    # Reuse the owner's already balanced native frame slots; do not edit the
    # pack material or replace it with a new generic surface.
    original = _one(ctx.actors, 'Operations/HoloArchive1/Frame').static_mesh_component
    if frame.static_mesh_component.get_num_materials() == original.get_num_materials():
        for slot in range(original.get_num_materials()):
            frame.static_mesh_component.set_material(slot, original.get_material(slot))
    pane = ctx.raw(label + '/Glass', P4 + 'SM_Window' + dimensions + '_V2_Part2_DigitalWindow',
                   center, (0, yaw, 0), collision=False)
    c, e = mesh_union(frame)
    delta = (center[0] - c.x, center[1] - c.y, center[2] - c.z)
    for actor in (frame, pane):
        p = actor.get_actor_location()
        ctx.move(actor, (p.x + delta[0], p.y + delta[1], p.z + delta[2]))
    component = pane.static_mesh_component
    material = ctx.asset(PRIVATE + 'MI_InteriorGraphic_' + variant)
    for slot in range(component.get_num_materials()):
        component.set_material(slot, material)
    return frame, pane


def _service(ctx, actors, label, destination, yaw):
    actor = _one(actors, label)
    group = [a for a in actors if a == actor or a.get_actor_label().startswith(label + '/')]
    p = actor.get_actor_location()
    _rigid(ctx, group, (p.x, p.y, p.z), destination, yaw - actor.get_actor_rotation().yaw)


def _standing(ctx, label, position, yaw, skin):
    import unreal as u
    actor = ctx.raw(label, u.SSOutpostAmbientActor, position, (0, yaw, 0))
    component = actor.character_mesh
    mesh = ctx.asset('/Game/Nyxar/Meshes/SKM_Nyxar')
    component.set_skeletal_mesh_asset(mesh)
    b = mesh.get_bounds()
    scale = 190. / (b.box_extent.z * 2.)
    component.set_relative_scale3d(u.Vector(scale, scale, scale))
    component.set_relative_rotation(u.Rotator(yaw=-90), False, False)
    component.set_relative_location(u.Vector(0, 0, -85 - (b.origin.z - b.box_extent.z) * scale), False, False)
    component.set_material(component.get_num_materials() - 1, ctx.asset(CREW + 'MI_NyxarCrew_' + skin))
    idle = ctx.asset(CREW + 'Anims/A_Alien_Convo_11_Listening_Loop')
    actor.set_editor_property('idle_animation', idle)
    actor.set_editor_property('gesture_animations', [ctx.asset(CREW + 'Anims/A_Alien_Convo_01_Low_Key_Loop')])
    actor.set_editor_property('phase_offset', sum(map(ord, label)) % 11 * .37)
    component.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
    data = component.get_editor_property('animation_data')
    data.anim_to_play, data.saved_looping, data.saved_playing = idle, True, True
    component.set_editor_property('animation_data', data)
    return actor


def _seated(ctx, actor, name, anchor, yaw, skin, clip, evidence):
    import unreal as u
    # Native chair pan at X0/Y10 is Z60.267, measured from the cached source
    # mesh. The higher Z92 surfaces are armrests, not a seat. Preserve the
    # stock chair/desk geometry and place the actual animated pelvis above it.
    component = actor.character_mesh
    mesh = ctx.asset('/Game/Nyxar/Meshes/SKM_Nyxar')
    assert clip.get_editor_property('skeleton') == mesh.skeleton
    component.set_skeletal_mesh_asset(mesh)
    scale = 190. / (mesh.get_bounds().box_extent.z * 2.)
    component.set_relative_scale3d(u.Vector(scale, scale, scale))
    component.set_relative_rotation(u.Rotator(yaw=-90), False, False)
    component.set_relative_location(u.Vector(0, 0, 0), False, False)
    component.set_material(component.get_num_materials() - 1, ctx.asset(CREW + 'MI_NyxarCrew_' + skin))
    local = (.650022, -144.324905 + 10., 60.267 + 15.)
    delta = _rotate(local, yaw)
    pelvis = tuple(anchor[i] + delta[i] for i in range(3))
    bones = evidence['component_bones_cm']
    offset = _rotate(tuple(v * scale for v in bones['pelvis']), yaw)
    origin = tuple(pelvis[i] - offset[i] for i in range(3))
    ctx.move(actor, origin, (0, yaw + 90, 0))
    _property(ctx, actor, 'idle_animation', clip)
    _property(ctx, actor, 'gesture_animations', [])
    _property(ctx, actor, 'route_points', [])
    _property(ctx, actor, 'phase_offset', 0.)
    # The occupied chair supplies physical collision. A standing capsule around
    # a seated presentation actor would protrude through its desk and floor.
    actor.set_actor_enable_collision(False)
    component.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
    data = component.get_editor_property('animation_data')
    data.anim_to_play, data.saved_looping, data.saved_playing = clip, True, True
    data.saved_position = 0.
    component.set_editor_property('animation_data', data)
    points = {}
    for key, point in bones.items():
        q = _rotate(tuple(v * scale for v in point), yaw)
        points[key] = [origin[i] + q[i] for i in range(3)]
    # A visible, grounded footrest supports the pilot-pose feet; do not lower
    # the body into the seat or extend a standing idle through the floor.
    feet = [(points['ball_' + side][i] + points['foot_' + side][i]) / 2
            for side in ('l', 'r') for i in range(3)]
    foot_center = tuple((feet[i] + feet[3 + i]) / 2 for i in range(3))
    top = min(points['ball_l'][2], points['ball_r'][2]) - 3.
    assert top > 1., 'Seated operator would penetrate the floor: ' + name
    rest = ctx.box('Operations/' + name + '/Footrest',
                   (foot_center[0], foot_center[1], top / 2.), (60, 34, top), GRAPHITE, True)
    rest.set_actor_rotation(u.Rotator(yaw=yaw), False)
    return {'operator': actor.get_actor_label(), 'pelvis': list(pelvis), 'scale': scale,
            'bones_world_cm': points, 'footrest_top_cm': top,
            'chair_pan_local_cm': [0, 10, 60.267],
            'evidence': 'Compatible actual seated clip; initial geometric fit. Rendered body, hand and contact QA pending.'}


def _operations(ctx, actors, clip, evidence):
    import unreal as u
    retired = []
    for bank in BANKS:
        group = _group(actors, 'OperationsNative/' + bank + '/')
        for actor in group:
            ctx.hide(actor)
        retired.append({'bank': bank, 'actors': len(group)})
    for actor in actors:
        if actor.get_actor_label().startswith(('Operations/SuspendedTelemetry', 'Operations/HoloArchive',
                                              'Operations/Status band mounting/')):
            ctx.hide(actor)
    ctx.hide(_one(actors, 'Operations/Identity'))
    primary = _group(actors, 'Engineering/Primary workstation/', 29)
    lights = _group(actors, 'Engineering/Workstation light/', 12)
    _rigid(ctx, primary + lights, (4200, -3200, 0), (7800, 0, 0), 90)
    _service(ctx, actors, 'Services/FLIGHT UPGRADES', (7580, 0, 100), 180)
    seated = []
    for index, (name, source, target, yaw, skin) in enumerate(PODS):
        group = _group(actors, 'OperationsNative/Command island ' + name + '/', 17)
        _rigid(ctx, group, source, target)
        for actor in group:
            if '/SM_TitaniumIndustrySeat_' in actor.get_actor_label():
                p = actor.get_actor_location()
                ctx.move(actor, (p.x, p.y, p.z + 4.92005))
        operator = (_one(actors, ('Crew/Engineer', 'Crew/Ops officer')[index]) if index < 2 else
                    ctx.raw('Operations/Operator ' + str(index + 1), u.SSOutpostAmbientActor, (0, 0, 85), collision=False))
        seated.append(_seated(ctx, operator, name, (target[0], target[1], 4.92005), yaw, skin, clip, evidence))
    # Existing transactions remain unchanged and visibly sit at the four desks.
    _service(ctx, actors, 'Services/SHIP & PARTS', (7200, -720, 125), 90)
    _service(ctx, actors, 'Services/PILOT LEADERBOARD', (7000, 720, 125), -90)
    _service(ctx, actors, 'Services/CONTRACT EXCHANGE', (8250, -720, 125), 90)
    _service(ctx, actors, 'Services/TRADE NETWORK', (8150, 720, 125), -90)
    anchors = {'ShipLoadout': (7000, -720, 100), 'Modules': (7200, 720, 100),
               'Systems': (8350, 720, 100)}
    for key, point in anchors.items():
        actor = ctx.raw('Operations/Service anchor ' + key, u.TargetPoint, point, collision=False)
        actor.tags = list(actor.tags) + ['OutpostServiceAnchor:' + key]
    for index, (y, variant) in enumerate(((-650, 'Graph1'), (0, 'DigitalPanel'), (650, 'Graph2'))):
        _panel(ctx, 'Operations/Rear data ' + str(index + 1), (9148, y, 205), 180, variant=variant)
    ctx.text('Operations/Identity', 'OPERATIONS  /  FLIGHT ENGINEERING', (9114, 0, 352), 180, 26)
    ctx.light('Operations/Central task pool', (7800, 0, 315), 1700, 900, (.66, .83, 1.))
    return {'retired_complete_banks': retired, 'central_workstation_parts': len(primary),
            'central_light_parts': len(lights), 'complete_work_desks': 4,
            'seated_operators': seated, 'native_service_anchors': anchors}


def _archive(ctx, actors):
    import unreal as u
    ctx.hide(_one(actors, 'Lounge/Identity'))
    ctx.text('Archive/Identity', 'CREW ARCHIVE  /  WARDROBE', (4200, 4425, 305), -90, 28, (.85, .69, 1.))
    # The apartment branch lies south/east of this room. Its complete namespace,
    # corridor, descending steps, instance and door are protected in apply().
    sign = ctx.box('Archive/Home direction backing', (4985, 2336, 248), (6, 380, 52), GRAPHITE, False)
    sign.set_actor_rotation(u.Rotator(yaw=90), False)
    ctx.text('Archive/Home direction', 'HOME  /  LOWER PASSAGE', (4985, 2340, 248), 90, 20, (.89, .76, 1.))
    _standing(ctx, 'Archive/Conversation guest A', (3210, 3150, 85), 0, 'Violet')
    _standing(ctx, 'Archive/Conversation guest B', (3410, 3150, 85), 180, 'Rose')
    # New pools reinforce existing figures without replacing their hologram material.
    for y in (2800, 3960):
        ctx.light('Archive/Bay pool ' + str(y), (5100, y, 285), 650, 430, (.65, .57, 1.))
    return {'preserved_hologram_bays': 3, 'preserved_conversation_islands': 2,
            'new_conversation_guests': 2, 'apartment_changes': 0}


def _ring(ctx, label, center, diameter, height, material):
    from OutpostGeometryUtils import mesh_union
    path = '/Game/OutpostSandbox/Geometry/SM_OutpostCollar'
    mesh = ctx.asset(path)
    b = mesh.get_bounds()
    actor = ctx.raw(label, mesh, center,
                    scale=(diameter / (2 * b.box_extent.x), diameter / (2 * b.box_extent.y),
                           height / (2 * b.box_extent.z)), collision=False)
    actor.static_mesh_component.set_material(0, ctx.asset(material))
    c, e = mesh_union(actor)
    p = actor.get_actor_location()
    ctx.move(actor, (p.x + center[0] - c.x, p.y + center[1] - c.y, p.z + center[2] - c.z))
    return actor


def _atrium(ctx, actors):
    import unreal as u
    _ring(ctx, 'Reception/Circular body', (4200, 0, 49), 590, 98, GRAPHITE)
    _ring(ctx, 'Reception/Countertop', (4200, 0, 102), 610, 8, PEARL)
    _ring(ctx, 'Reception/Light reveal', (4200, 0, 87), 594, 3, CYAN)
    # Match the annular visible body rather than using a convex hull that fills
    # its open interior. The two standing staff are presentation actors inside.
    for i in range(24):
        angle = i * 15.
        p = _rotate((277, 0, 49), angle)
        actor = ctx.box('Reception/Body segment ' + str(i), (4200 + p[0], p[1], p[2]),
                        (34, 75, 98), GRAPHITE, True)
        actor.set_actor_rotation(u.Rotator(yaw=angle), False)
    # Retain existing people and their standing idle/gesture clips.
    for label, y in (('Crew/Atrium A', -80), ('Crew/Atrium B', 80)):
        actor = _one(actors, label)
        ctx.move(actor, (4010, y, 85), (0, 180, 0))
        _property(ctx, actor, 'route_points', [])
    patrol = _one(actors, 'Crew/Atrium patrol')
    ctx.move(patrol, (4850, 0, 85), (0, 0, 0))
    route = [_rotate((650, 0, 0), angle) for angle in range(0, 360, 45)]
    _property(ctx, patrol, 'route_points', [u.Vector(p[0] - 650, p[1], p[2]) for p in route])
    for y in (-130, 130):
        ctx.grounded('Reception/Welcome console ' + str(y), SCREEN, (3930, y), floor=106,
                     yaw=180, scale=(.6, .6, .6), collision=False)
    ctx.text('Reception/Welcome', 'WAYFARER  /  WELCOME', (3891, 0, 66), 180, 20, BLUE)
    ctx.light('Reception/Staff light', (4100, 0, 355), 1500, 650, (1., .86, .70))
    info = (
        ('WELCOME / WAYFARER', 'WAYFARER', 'Station information. Operations is ahead; social is left; crew archive is right.'),
        ('FLIGHT ENGINEERING', 'SOCIAL  /  LEFT', 'Social lounge: bar, booths and arcade in the left wing.'),
        ('CREW ARCHIVE', 'ARCHIVE  /  RIGHT', 'Crew wardrobe and character archive are in the right wing. Home is through the lower passage.'),
        ('OPERATIONS', 'OPERATIONS  /  AHEAD', 'Flight upgrades, pilot records, contracts and ship services are in Operations, straight ahead.'),
        ('SURVIVAL DEPARTURES', 'PAD  /  DEPARTURES', 'Choose Waves or Free Flight at the flight mode terminal, then enter the Phoenix cockpit and sit to depart.'),
        ('OBSERVATION GALLERY', 'OBSERVATION GALLERY', 'Use the existing observation route to the glass gallery above the station.'),
        ('MARKET / BERTHS', 'MARKET  /  BERTHS', 'The market and ship berths are back along the arrival concourse.'),
    )
    for actor in actors:
        label = actor.get_actor_label()
        if label.startswith('Welcome/') and not isinstance(actor, u.SSOutpostTerminal):
            ctx.hide(actor)
    for i, (old, title, description) in enumerate(info, 1):
        angle = 22.5 + (i - 1) * 45.
        direction = _rotate((1, 0, 0), angle)
        center = (4200 + 1330 * direction[0], 1330 * direction[1], 175)
        # Large supported signs between the cardinal routes keep the centre open.
        _panel(ctx, 'Reception/Direction ' + str(i), center, angle + 180, '200X250', 'Clear')
        for side in (-1, 1):
            offset = _rotate((0, side * 70, 0), angle)
            post = ctx.box('Reception/Direction ' + str(i) + '/Support ' + str(side),
                           (center[0] + offset[0], center[1] + offset[1], 25),
                           (8, 8, 50), GRAPHITE, True)
            post.set_actor_rotation(u.Rotator(yaw=angle), False)
        backing = ctx.box('Reception/Direction ' + str(i) + '/Backing', center,
                          (6, 185, 230), GRAPHITE, False)
        backing.set_actor_rotation(u.Rotator(yaw=angle), False)
        face = (center[0] - direction[0] * 17, center[1] - direction[1] * 17, 200)
        # Short lines fit the native 2 m frame; this is wayfinding, not a new service.
        text = title.replace(' / ', '\n').replace('OBSERVATION GALLERY', 'OBSERVATION\nGALLERY')
        ctx.text('Reception/Direction ' + str(i) + '/Title', text,
                 face, angle + 180, 18, BLUE)
        actor = _one(actors, 'Welcome/' + str(i) + ' / ' + old)
        ctx.move(actor, (center[0] - direction[0] * 35, center[1] - direction[1] * 35, 110))
        _property(ctx, actor, 'display_name', title)
        _property(ctx, actor, 'description', description)
    return {'counter_center': [4200, 0], 'counter_diameter_cm': 610, 'welcome_staff': 2,
            'information_terminals_preserved': 7, 'earth_transform_unchanged': True,
            'counter_collision': '24 visible annular wall segments; central void remains open'}


def apply(ctx):
    """One guarded owner-preview authoring pass; no process launch or map save."""
    from AuthorStationSeatedCrew import CLIP, pose_evidence
    actors = list(ctx.actors)
    if any(a.get_actor_label().startswith(('Refine/Operations/', 'Refine/Archive/', 'Refine/Reception/')) for a in actors):
        raise RuntimeError('Operations/atrium already refined; restore guarded baseline before replay')
    for label, target in (('Operations/Roof structure', (7800, 0)),
                          ('Lounge/Roof structure', (4200, 3400)),
                          ('Atrium/Planetary archive/World', (4200, 0))):
        actor = _one(actors, label)
        p = actor.get_actor_location()
        if math.hypot(p.x - target[0], p.y - target[1]) > .1 or abs(actor.get_actor_rotation().yaw) > .1:
            raise RuntimeError('Owner room moved since inventory; review before furnishing ' + label)
    # The only asset creation is a separate, already validated retarget author pass.
    clip = ctx.asset(CLIP)
    evidence = pose_evidence(clip)
    _group(actors, 'Engineering/Primary workstation/', 29)
    _group(actors, 'Engineering/Workstation light/', 12)
    for name, _, _, _, _ in PODS:
        _group(actors, 'OperationsNative/Command island ' + name + '/', 17)
    for label in ('Crew/Engineer', 'Crew/Ops officer', 'Crew/Atrium A', 'Crew/Atrium B',
                  'Crew/Atrium patrol', 'Operations/Identity', 'Lounge/Identity',
                  'Operations/HoloArchive1/Frame', 'Services/FLIGHT UPGRADES',
                  'Services/SHIP & PARTS', 'Services/PILOT LEADERBOARD',
                  'Services/CONTRACT EXCHANGE', 'Services/TRADE NETWORK'):
        _one(actors, label)
    assert not any(str(tag).startswith('OutpostServiceAnchor:') for a in actors for tag in a.tags), 'Service anchors already exist'
    for path in (GRAPHITE, PEARL, CYAN, SCREEN, '/Game/OutpostSandbox/Geometry/SM_OutpostCollar'):
        ctx.asset(path)
    for dimensions in ('400X200', '200X250'):
        for suffix in ('_V1_Part1', '_V2_Part2_DigitalWindow'):
            ctx.asset(P4 + 'SM_Window' + dimensions + suffix)
    for variant in ('Graph1', 'Graph2', 'DigitalPanel', 'Clear'):
        ctx.asset(PRIVATE + 'MI_InteriorGraphic_' + variant)
    protected = {a: _pose(a) for a in actors if a.get_actor_label().startswith('HomeHub/') or
                 a.get_actor_label() == 'Atrium/Planetary archive/World'}
    operations = _operations(ctx, actors, clip, evidence)
    archive = _archive(ctx, actors)
    atrium = _atrium(ctx, actors)
    assert all(_pose(a) == pose for a, pose in protected.items()), 'Protected home/Earth transform changed'
    return {'module': 'operations_archive_atrium', 'operations': operations,
            'archive': archive, 'atrium': atrium, 'protected_transforms': len(protected),
            'cameras': [
                {'name': 'Operations entry', 'location': [6470, -180, 170], 'look_at': [7950, 0, 130]},
                {'name': 'Operator contact', 'location': [7380, -670, 150], 'look_at': [7100, -1070, 100]},
                {'name': 'Archive entry', 'location': [4100, 2410, 170], 'look_at': [4810, 3660, 150]},
                {'name': 'Reception arrival', 'location': [2900, -230, 170], 'look_at': [4250, 0, 230]}],
            'limits': 'Authored placement and seated-bone evidence only; native appearance, contacts, collision and service range still require lead validation.'}
