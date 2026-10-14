"""Small enclosed ambient ball-return hardware; no mesh authoring or saves.

The original purchased table remains intact. Opaque service housings enclose
the original decorative leather bags and the internal authored ball transfer.
The visible ball emerges through a sloped chute into an open hand-access tray.
This is scenic choreography, not a physically simulated playable pool table.
"""
import math


PREFIX = 'Refine/OrbitPool/Return/'
DARK = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Materials/Instances/Opaque/MI_Metal12_PaintAnodizedAluminium_Dark'
TRIM = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Materials/Instances/Opaque/MI_Metal02_AnodizedAluminium'
TRAY_FLOOR_Z = 55.-2.837515373645715


def _box(ctx, label, center, size, material, yaw=0., pitch=0.):
    import unreal as u
    actor = ctx.box(label, center, size, material, collision=False)
    actor.set_actor_rotation(u.Rotator(pitch=pitch, yaw=yaw, roll=0.), False)
    return actor


def _part(ctx, prefix, name, origin, direction, distance, side, z, size, material, pitch=0.):
    dx, dy = direction
    center = (origin[0]+distance*dx-side*dy, origin[1]+distance*dy+side*dx, z)
    yaw = math.degrees(math.atan2(dy, dx))
    return _box(ctx, prefix+name, center, size, material, yaw, pitch)


def apply(ctx):
    """Place attached return modules; integration lead owns the map save."""
    import unreal as u
    import AuthorStationPoolMatchSequence as match
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name().split('.')[0] != match.MAP:
        raise RuntimeError('Pool returns belong only in the owner preview')
    if any(a.get_actor_label().startswith(PREFIX) for a in ctx.actors+ctx.created):
        raise RuntimeError('Preserve existing pool return hardware; do not duplicate')
    tables = [a for a in ctx.actors if a.get_actor_label() == 'Refine/OrbitPool/Table']
    if len(tables) != 1 or tables[0].static_mesh_component.static_mesh.get_path_name().split('.')[0] != match.BASE_MESH:
        raise RuntimeError('Return modules require the unchanged original native table')
    table = tables[0]
    if math.dist(table.get_actor_location().to_tuple(), (4800., -3150., 0.)) > .05:
        raise RuntimeError('Pool table moved; return module coordinates need review')
    # Native textured anodized surfaces already used by the room's owned kit.
    ctx.asset(DARK)
    ctx.asset(TRIM)
    created_before = len(ctx.created)
    modules = []
    for name, pocket, tray in (('NW', match.POCKET_NW, match.PICKUP_NW),
                               ('SE', match.POCKET_SE, match.PICKUP_SE)):
        prefix = PREFIX+name+'/'
        dx, dy = tray[0]-pocket[0], tray[1]-pocket[1]
        length = math.hypot(dx, dy)
        direction = (dx/length, dy/length)
        if abs(length-50.) > .002 or tray[2] != 55.:
            raise RuntimeError('Return geometry and pickup anchor disagree')
        # The below-felt receiver fully masks the decorative bag and transfer.
        # Its top is open under the original hole; the table's wood is intact.
        for side in (-1, 1):
            _part(ctx, prefix, 'Receiver side '+str(side), pocket, direction,
                  0, side*10., 64., (21., 1., 30.), DARK)
            _part(ctx, prefix, 'Receiver end '+str(side), pocket, direction,
                  side*10., 0, 64., (1., 19., 30.), DARK)
        _part(ctx, prefix, 'Receiver base', pocket, direction, 0, 0, 49., (21.,21.,1.), DARK)
        # Closed channel has enough internal space for the real 5.675cm ball.
        # The receiver hides its first section; an open tray receives the end.
        channel_length = 40.
        slope = -.8/50.
        pitch = math.degrees(math.atan(slope))
        middle_z = 55.8+slope*channel_length*.5
        for side in (-1, 1):
            _part(ctx, prefix, 'Chute side '+str(side), pocket, direction,
                  channel_length*.5, side*4.5, middle_z, (channel_length,1.,8.), DARK, pitch)
            _part(ctx, prefix, 'Chute seam '+str(side), pocket, direction,
                  channel_length*.5, side*4.6, middle_z+4., (channel_length,.25,.25), TRIM, pitch)
        _part(ctx, prefix, 'Chute floor', pocket, direction, channel_length*.5, 0,
              middle_z-match.BALL_RADIUS-.5, (channel_length,10.,1.), DARK, pitch)
        _part(ctx, prefix, 'Chute lid', pocket, direction, channel_length*.5, 0,
              middle_z+match.BALL_RADIUS+1., (channel_length,10.,1.), DARK, pitch)
        # Low lips stay below the ball center and leave 26cm of clear hand width.
        _part(ctx, prefix, 'Tray floor', pocket, direction, length, 0,
              TRAY_FLOOR_Z-.6, (34.,28.,1.2), DARK)
        for side in (-1, 1):
            _part(ctx, prefix, 'Tray lip '+str(side), pocket, direction, length,
                  side*13.5, TRAY_FLOOR_Z+.7, (34.,1.,1.4), TRIM)
        _part(ctx, prefix, 'Tray end stop', pocket, direction, length+16.5, 0,
              TRAY_FLOOR_Z+.7, (1.,28.,1.4), TRIM)
        # A visible underside brace attaches each cantilevered tray to receiver.
        _part(ctx, prefix, 'Support rib', pocket, direction, 29., 0, 49.8,
              (42.,3.,3.), DARK, math.degrees(math.atan2(1.6,42.)))
        modules.append({'name': name, 'pocket': pocket, 'pickup': tray,
                        'tray_floor_z': TRAY_FLOOR_Z, 'tray_clear_width_cm': 26.,
                        'enclosed_channel_length_cm': channel_length, 'enclosed_transfer': True})
    return {'module': 'pool_return_hardware', 'dirty_assets': [],
            'created': [a.get_actor_label() for a in ctx.created[created_before:]],
            'modules': modules, 'original_table_mesh_unchanged': True,
            'materials': [DARK, TRIM], 'new_lights': 0,
            'limits': 'Authored scenic ball transfer inside opaque housing; not simulated table physics'}


stage = apply
