"""Grounded alternating ambient pool match; the lead owns saves and playback.

The 60-second clock is shared with AuthorStationPoolMatchAnimation. Only the
cue ball rolls, drops into native pockets, and is carried by fitted hands. The
two object balls remain stationary. This is authored ambience, not a minigame.
All offline geometry/motion helpers remain importable without Unreal.
"""
import hashlib
import json
import math
import struct
from pathlib import Path


FPS = 30
DURATION = 60.0
END_FRAME = 1800
ASSET = '/Game/OutpostSandbox/StationRefinement/Sequences/LS_StationPoolMatch_20261006'
LABEL = 'Refine/OrbitPool/Alternating match sequence'
MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
BASE_MESH = '/Game/Rocket/MLR_PoolTable/SM_MLR_PoolTable_Base_c1_Nanite'
BASE_SHA = '885a12c049c7c0f948aa2d74e60ed48d2f3d7c7f962ac0763c937a01efc04327'
BASE_PROBE_SHA = 'a2598e76407b35ec7f4dab50ebfbb78f97b0baaaa87f6bac006e97336fb10e72'
BALL_RADIUS = 2.837515373645715
FELT_Z = 80.06
BALL_Z = FELT_Z + BALL_RADIUS
RAIL_Z = 85.2583999633789
FELT_BOUNDS = (4739.59, 4860.41, -3266.466, -3033.534)
POCKET_RADIUS = 5.695695989106621
POCKET_NW = (4742.226803148387, -3036.433966135041, 62.04670931149504)
POCKET_SE = (4857.773196851613, -3263.566033864959, 62.04670930907022)
PICKUP_NW = (4706.871464, -3001.078627, 55.)
PICKUP_SE = (4893.128536, -3298.921373, 55.)
RETURN_NW, RETURN_SE = PICKUP_NW, PICKUP_SE
RESET_SOUTH = (4800., -3225., BALL_Z)
RESET_NORTH = (4800., -3075., BALL_Z)
SHOT_YAW = 17.03411002137301
CONTACT_TIMES = (7., 30.5)
HELD_INTERVALS = ((17., 21.), (43., 47.))
STATIC_BALL_CENTERS = ((4802.837515373646, -3170., BALL_Z),
                       (4832.837515373646, -3144.0192378864667, BALL_Z))
EVENTS = {
    'alien_contact': 7., 'north_pocket_entry': 9.5, 'north_pocket_settle': 9.9,
    'north_return_tray_settle': 12., 'south_return_tray_settle': 36.,
    'trooper_grasp': 17., 'trooper_release': 21., 'trooper_contact': 30.5,
    'south_pocket_entry': 33.3, 'south_pocket_settle': 33.7,
    'alien_grasp': 43., 'alien_release': 47., 'loop_end': DURATION,
    'conversation_intervals': ((10., 14.), (23., 25.), (34., 40.), (49., 60.)),
}
CHANNELS = ('Location.X', 'Location.Y', 'Location.Z', 'Rotation.X', 'Rotation.Y',
            'Rotation.Z', 'Scale.X', 'Scale.Y', 'Scale.Z')


def _triplet(value, name):
    values = tuple(float(v) for v in value)
    if len(values) != 3 or not all(math.isfinite(v) for v in values):
        raise ValueError(name + ' requires three finite numbers')
    return values


def _frame(seconds):
    frame = round(float(seconds) * FPS)
    if not math.isfinite(seconds) or abs(seconds * FPS - frame) > 1e-5:
        raise ValueError('All match keys must lie on the shared 30 Hz clock')
    return frame


def _mix(a, b, t):
    t = max(0., min(1., t))
    return tuple(x + (y-x)*t for x, y in zip(a, b))


def _qmul(a, b):
    x, y, z, w = a
    X, Y, Z, W = b
    return (w*X+x*W+y*Z-z*Y, w*Y-x*Z+y*W+z*X,
            w*Z+x*Y-y*X+z*W, w*W-x*X-y*Y-z*Z)


def _held_rows(rows, start, end, pocket, reset):
    result = {}
    for row in rows:
        frame = _frame(float(row['time']))
        if frame in result:
            raise ValueError('Duplicate fitted hand frame')
        result[frame] = _triplet(row['center'], 'Fitted held-ball center')
    expected = set(range(_frame(start), _frame(end)+1))
    if set(result) != expected:
        raise ValueError('Fitted hand centers must cover every held frame, including both endpoints')
    if math.dist(result[_frame(start)], pocket) > .05 or math.dist(result[_frame(end)], reset) > .05:
        raise ValueError('Fitted hand pickup/release does not meet the actual pocket/reset anchor')
    return result


def geometry_guard(root):
    root = Path(root)
    receipt = root / '.agent/local/StationRefinement/StationPoolBaseProbe1.json'
    if hashlib.sha256(receipt.read_bytes()).hexdigest() != BASE_PROBE_SHA:
        raise RuntimeError('Actual Base pocket evidence changed; review before authoring')
    native = json.loads(receipt.read_text(encoding='utf-8'))
    if not native['success'] or not native['original_preserved'] or native['source_sha256'] != BASE_SHA:
        raise RuntimeError('Actual Base mesh probe did not preserve the verified source')
    asset = root / ('Content/' + BASE_MESH[6:] + '.uasset')
    if hashlib.sha256(asset.read_bytes()).hexdigest() != BASE_SHA:
        raise RuntimeError('Native pool table source differs from measured pockets')
    return {'base_asset_sha256': BASE_SHA, 'native_probe_sha256': BASE_PROBE_SHA,
            'pocket_circle_fit_max_error_cm': .03100705702367179,
            'felt_z_cm': FELT_Z, 'ball_radius_cm': BALL_RADIUS,
            'pocket_mouth_radius_cm': POCKET_RADIUS,
            'pocket_nw': POCKET_NW, 'pocket_se': POCKET_SE,
            'pickup_nw': PICKUP_NW, 'pickup_se': PICKUP_SE,
            'return_transfer': 'Authored inside opaque service hardware; vendor bag remains unchanged'}


def _return_guard(ctx):
    actors = {a.get_path_name(): a for a in ctx.actors+ctx.created}.values()
    hardware = [a for a in actors if a.get_actor_label().startswith('Refine/OrbitPool/Return/')]
    if len(hardware) != 32:
        raise RuntimeError('Expected both complete enclosed return modules before sequence authoring')
    records = []
    for name, pickup in (('NW', PICKUP_NW), ('SE', PICKUP_SE)):
        matches = [a for a in hardware if a.get_actor_label() == 'Refine/OrbitPool/Return/'+name+'/Tray floor']
        if len(matches) != 1:
            raise RuntimeError('Missing physical pickup tray: '+name)
        floor = matches[0]
        expected = (pickup[0], pickup[1], pickup[2]-BALL_RADIUS-.6)
        if (math.dist(floor.get_actor_location().to_tuple(), expected) > .002 or
                math.dist(floor.get_actor_scale3d().to_tuple(), (.34, .28, .012)) > 1e-6 or
                floor.get_editor_property('hidden')):
            raise RuntimeError('Pickup tray does not match the fitted hand anchor: '+name)
        records.append({'label': floor.get_actor_label(), 'pickup': pickup,
                        'floor_top_z': pickup[2]-BALL_RADIUS})
    return {'actors': len(hardware), 'trays': records, 'visible_hardware_required': True}


def build_motion(held_ball_centers):
    """Join native pocket motion to actual fitted hand centers, continuously.

    held_ball_centers contains 'trooper' and 'nyxar' lists of {time, center};
    the pose author supplies world ball centers from the solved hand transform.
    No synthesized carry path, visible teleport, scale or hidden reset is used.
    """
    north_hold = _held_rows(held_ball_centers['trooper'], 17., 21., PICKUP_NW, RESET_NORTH)
    south_hold = _held_rows(held_ball_centers['nyxar'], 43., 47., PICKUP_SE, RESET_SOUTH)
    result = []
    rotation = (0., 0., 0., 1.)
    max_step = 0.
    minimum_object_clearance = float('inf')
    minimum_rail_clearance = float('inf')
    lifted_clear = {'held_trooper': False, 'held_nyxar': False}

    def roll(start, pocket, t, t0, t1):
        # Modest friction: speed decreases continuously but remains nonzero at
        # the pocket mouth. Endpoint displacement is the measured scratch line.
        x = max(0., min(1., (t-t0)/(t1-t0)))
        progress = 1.25*x-.25*x*x
        return _mix(start, (pocket[0], pocket[1], BALL_Z), progress)

    def returned(pocket, pickup, t, start, settled):
        elapsed = max(0., t-start)
        gravity_center = BALL_Z - .5*981.*elapsed*elapsed
        # The opaque housing encloses the original decorative bag and transfer.
        # Follow one continuous descending path; no visibility/scale teleport.
        if elapsed <= .3:
            return pocket[:2] + (max(55.8, gravity_center),)
        progress = max(0., min(1., (t-start-.3)/(settled-start-.3)))
        return _mix(pocket[:2]+(55.8,), pickup, progress)

    for frame in range(END_FRAME+1):
        t = frame/FPS
        if t <= 7.:
            center, mode = RESET_SOUTH, 'felt_rest'
        elif t <= 9.5:
            center, mode = roll(RESET_SOUTH, POCKET_NW, t, 7., 9.5), 'rolling'
        elif t < 17.:
            center, mode = returned(POCKET_NW, PICKUP_NW, t, 9.5, 12.), 'return_nw'
        elif t <= 21.:
            center, mode = north_hold[frame], 'held_trooper'
        elif t <= 30.5:
            center, mode = RESET_NORTH, 'felt_rest'
        elif t <= 33.3:
            center, mode = roll(RESET_NORTH, POCKET_SE, t, 30.5, 33.3), 'rolling'
        elif t < 43.:
            center, mode = returned(POCKET_SE, PICKUP_SE, t, 33.3, 36.), 'return_se'
        elif t <= 47.:
            center, mode = south_hold[frame], 'held_nyxar'
        else:
            center, mode = RESET_SOUTH, 'felt_rest'
        if result:
            previous = result[-1]['center']
            step = math.dist(center, previous)
            max_step = max(max_step, step)
            if step > 7.5:
                raise ValueError('Cue ball discontinuity or implausible hand speed at frame %d' % frame)
            if mode == 'rolling':
                dx, dy = center[0]-previous[0], center[1]-previous[1]
                travel = math.hypot(dx, dy)
                if travel > 1e-8:
                    half = travel/BALL_RADIUS*.5
                    increment = (-dy/travel*math.sin(half), dx/travel*math.sin(half), 0., math.cos(half))
                    rotation = _qmul(increment, rotation)
                    length = math.sqrt(sum(v*v for v in rotation))
                    rotation = tuple(v/length for v in rotation)
            for other in STATIC_BALL_CENTERS:
                delta = tuple(b-a for a, b in zip(previous, center))
                denom = sum(v*v for v in delta)
                ratio = max(0., min(1., sum((p-a)*v for p, a, v in zip(other, previous, delta))/denom)) if denom else 0.
                distance = math.dist(_mix(previous, center, ratio), other) - 2*BALL_RADIUS
                minimum_object_clearance = min(minimum_object_clearance, distance)
                if distance < -.02:
                    raise ValueError('Cue path would strike a supposedly static object ball at frame %d' % frame)
        if mode.startswith('held_'):
            inside_felt = (FELT_BOUNDS[0]+BALL_RADIUS <= center[0] <= FELT_BOUNDS[1]-BALL_RADIUS and
                           FELT_BOUNDS[2]+BALL_RADIUS <= center[1] <= FELT_BOUNDS[3]-BALL_RADIUS)
            pocket = POCKET_NW if mode == 'held_trooper' else POCKET_SE
            pickup = PICKUP_NW if mode == 'held_trooper' else PICKUP_SE
            pocket_distance = math.dist(center[:2], pocket[:2])
            pickup_distance = math.dist(center[:2], pickup[:2])
            clearance = center[2]-BALL_RADIUS-RAIL_Z
            if clearance >= .3:
                lifted_clear[mode] = True
            if not lifted_clear[mode] and pickup_distance > .15:
                raise ValueError('Held ball exits catch tray sideways before being lifted clear at frame %d' % frame)
            if .15 < pocket_distance < POCKET_RADIUS+BALL_RADIUS+.3:
                minimum_rail_clearance = min(minimum_rail_clearance, clearance)
                if clearance < .3:
                    raise ValueError('Held ball crosses the pocket rim below clearance at frame %d' % frame)
            inside_pocket = pocket_distance <= POCKET_RADIUS-BALL_RADIUS-.05
            inside_tray = pickup_distance < .15
            if not inside_felt and not inside_pocket and not inside_tray:
                minimum_rail_clearance = min(minimum_rail_clearance, clearance)
                if clearance < .3:
                    raise ValueError('Held ball crosses native cushion before being lifted clear at frame %d' % frame)
        result.append({'time': t, 'center': list(center), 'quaternion': list(rotation), 'mode': mode})
    if math.dist(result[0]['center'], result[-1]['center']) > .05:
        raise ValueError('Cue ball loop position would jump')
    if 1.-abs(sum(a*b for a, b in zip(result[0]['quaternion'], result[-1]['quaternion']))) > 1e-7:
        raise ValueError('Opposed rolling paths did not naturally close ball orientation')
    return {'frames': result, 'events': EVENTS, 'duration_seconds': DURATION,
            'ball_radius_cm': BALL_RADIUS, 'maximum_frame_displacement_cm': max_step,
            'minimum_swept_object_clearance_cm': minimum_object_clearance,
            'minimum_cushion_clearance_when_crossing_cm': minimum_rail_clearance if math.isfinite(minimum_rail_clearance) else None,
            'static_ball_centers': STATIC_BALL_CENTERS,
            'held_frames_from_fitted_hand_transforms': True,
            'enclosed_return_transfer': True,
            'floating_reset': False, 'hidden_or_scale_reset': False}


def native_ball_samples(motion):
    """Convert sphere centers into the owned mesh's rotating bottom pivot."""
    import unreal as u
    samples, previous_angles = [], None
    for row in motion['frames']:
        quaternion = u.Quat(*row['quaternion'])
        rotator = quaternion.rotator()
        angles = [rotator.pitch, rotator.yaw, rotator.roll]
        if previous_angles is not None:
            angles = [old+(new-old+180)%360-180 for old, new in zip(previous_angles, angles)]
        previous_angles = angles
        offset = quaternion.rotate_vector(u.Vector(0, 0, BALL_RADIUS))
        center = row['center']
        samples.append({'time': row['time'],
                        'location': [center[0]-offset.x, center[1]-offset.y, center[2]-offset.z],
                        'rotation': angles, 'scale': [1., 1., 1.]})
    return samples


def _samples(rows, name):
    result = []
    previous = -1
    for row in rows:
        seconds = float(row['time'])
        frame = round(seconds * FPS)
        if not math.isfinite(seconds) or abs(seconds * FPS - frame) > .0001:
            raise ValueError(name + ' keys must lie on the shared 30 Hz animation clock')
        if frame <= previous or not 0 <= frame <= END_FRAME:
            raise ValueError(name + ' keys must increase within [0, 60] seconds')
        location = _triplet(row['location'], name + ' location')
        pitch, yaw, roll = _triplet(row['rotation'], name + ' rotation')
        scale = _triplet(row['scale'], name + ' scale')
        if min(scale) <= 0:
            raise ValueError(name + ' has non-positive scale')
        # Native transform channels are XYZ rotation = roll, pitch, yaw.
        result.append((frame, location + (roll, pitch, yaw) + scale))
        previous = frame
    if len(result) < 2 or result[0][0] != 0 or result[-1][0] != END_FRAME:
        raise ValueError(name + ' must include the complete 0/60 second loop')
    first, last = result[0][1], result[-1][1]
    for index, (a, b) in enumerate(zip(first, last)):
        error = abs((b-a+180) % 360-180) if 3 <= index < 6 else abs(b-a)
        if error > (.05 if index < 6 else 1e-6):
            raise ValueError(name + ' loop endpoint would visibly jump')
    return result


def _prop_preflight(actor, rows):
    import unreal as u
    if not isinstance(actor, u.Actor) or actor.get_attach_parent_actor():
        raise ValueError('World-space pool tracks require an unattached Actor')
    if not actor.get_actor_label().startswith('Refine/'):
        raise ValueError('Refusing to animate an unowned placed prop')
    root = actor.get_editor_property('root_component')
    if not isinstance(root, u.SceneComponent):
        raise ValueError('Pool prop has no scene root')
    for component in actor.get_components_by_class(u.PrimitiveComponent):
        if component.is_simulating_physics():
            raise ValueError('Pool sequence must not compete with a physics body')
    sampled = _samples(rows, actor.get_actor_label())
    position = actor.get_actor_location()
    if (position-u.Vector(*sampled[0][1][:3])).length() > .1:
        raise ValueError(actor.get_actor_label() + ' does not start at its authored first key')
    return sampled


def _transform_track(sequence, actor, rows):
    import unreal as u
    actor.get_editor_property('root_component').set_mobility(u.ComponentMobility.MOVABLE)
    binding = u.MovieSceneSequenceExtensions.add_possessable(sequence, actor)
    u.MovieSceneBindingExtensions.set_name(binding, actor.get_actor_label())
    track = u.MovieSceneBindingExtensions.add_track(binding, u.MovieScene3DTransformTrack)
    section = track.add_section()
    u.MovieSceneSectionExtensions.set_range(section, 0, END_FRAME)
    section.set_completion_mode(u.MovieSceneCompletionMode.RESTORE_STATE)
    section.set_blend_type(u.MovieSceneBlendType.ABSOLUTE)
    section.set_editor_property('use_quaternion_interpolation', True)
    channels = {str(channel.get_editor_property('channel_name')): channel
                for channel in u.MovieSceneSectionExtensions.get_all_channels(section)}
    if not set(CHANNELS) <= set(channels):
        raise RuntimeError('Native transform channel schema differs: ' + repr(sorted(channels)))
    precision = {}
    for index, name in enumerate(CHANNELS):
        channel = channels[name]
        if not isinstance(channel, u.MovieSceneScriptingDoubleChannel):
            raise RuntimeError('Native transform channel is not double precision: ' + name)
        channel.set_default(rows[0][1][index])
        maximum_add_error = maximum_final_error = 0.
        for frame, values in rows:
            expected = values[index]
            key = channel.add_key(u.FrameNumber(frame), expected, 0.0,
                                  u.MovieSceneTimeUnit.DISPLAY_RATE, u.MovieSceneKeyInterpolation.LINEAR)
            if not key:
                raise RuntimeError('Native transform key creation failed: %s frame=%d expected=%.17g' %
                                   (name, frame, expected))
            initial = float(key.get_value())
            rounded = struct.unpack('f', struct.pack('f', expected))[0]
            tolerance = 4. * math.ulp(expected)
            if min(abs(initial-expected), abs(initial-rounded)) > tolerance:
                raise RuntimeError('Unexpected native AddKey value: %s frame=%d expected=%.17g '
                                   'float32=%.17g actual=%.17g error=%.17g' %
                                   (name, frame, expected, rounded, initial, abs(initial-expected)))
            # UE5.8's public DoubleChannel AddKey reaches CurveChannelImpl's
            # float InValue parameter. DoubleKey.SetValue writes directly into
            # FMovieSceneDoubleValue, preserving our native world coordinates.
            key.set_value(expected)
            actual = float(key.get_value())
            error = abs(actual-expected)
            if not math.isfinite(actual) or error > tolerance:
                raise RuntimeError('Native double-key readback failed: %s frame=%d expected=%.17g '
                                   'actual=%.17g error=%.17g tolerance=%.17g' %
                                   (name, frame, expected, actual, error, tolerance))
            maximum_add_error = max(maximum_add_error, abs(initial-expected))
            maximum_final_error = max(maximum_final_error, error)
        if len(channel.get_keys()) != len(rows):
            raise RuntimeError('Native transform key count differs: ' + name)
        precision[name] = {'maximum_add_key_float32_error': maximum_add_error,
                           'maximum_final_double_error': maximum_final_error}
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    bound = u.MovieSceneSequenceExtensions.locate_bound_objects(sequence, binding, world)
    if actor not in bound:
        raise RuntimeError('Pool prop binding cannot resolve in the owner level')
    return {'actor': actor.get_path_name(), 'samples': len(rows), 'channels': list(CHANNELS),
            'interpolation': 'LINEAR', 'space': 'Unattached actor world transform',
            'native_key_precision': precision}


def position_balls(ctx, balls, motion):
    """One-time starting arrangement; never called by ambient playback."""
    import unreal as u
    expected = ('Ivory', 'IonBlue', 'SolarAmber')
    if len(balls) != 3 or any(actor.get_actor_label() != 'Refine/OrbitPool/Ball '+name
                             for actor, name in zip(balls, expected)):
        raise ValueError('Expected the three existing, ordered ambient pool balls')
    rows = [native_ball_samples(motion)[0]]
    rows.extend({'location': (c[0], c[1], c[2]-BALL_RADIUS),
                 'rotation': (0., 0., 0.), 'scale': (1., 1., 1.)} for c in STATIC_BALL_CENTERS)
    report = []
    for actor, row in zip(balls, rows):
        before = list(actor.get_actor_location().to_tuple())
        actor.get_editor_property('root_component').set_mobility(u.ComponentMobility.MOVABLE)
        actor.set_actor_location(u.Vector(*row['location']), False, False)
        pitch, yaw, roll = row['rotation']
        actor.set_actor_rotation(u.Rotator(pitch=pitch, yaw=yaw, roll=roll), False)
        actor.set_actor_scale3d(u.Vector(*row['scale']))
        report.append({'actor': actor.get_path_name(), 'before_location': before,
                       'starting_sample': row, 'animated_in_match': actor == balls[0]})
    return {'balls': report, 'scope': 'Initial saved staging only; no playback resets or teleports'}


def _skeletal_track(sequence, player):
    import unreal as u
    actor, clip = player['actor'], player['clip']
    component = actor.get_component_by_class(u.SkeletalMeshComponent)
    mesh = component.get_skeletal_mesh_asset() if component else None
    if not actor.get_actor_label().startswith('Refine/OrbitPool/') or not mesh:
        raise ValueError('Pool player must be an owned placed skeletal actor')
    if not isinstance(clip, u.AnimSequence) or clip.get_editor_property('skeleton') != mesh.skeleton:
        raise ValueError('Pool animation must match this player native skeleton')
    if abs(float(clip.sequence_length)-DURATION) > .001:
        raise ValueError('Both pool clips must span the shared 60-second clock')
    owner_binding = u.MovieSceneSequenceExtensions.add_possessable(sequence, actor)
    binding = u.MovieSceneSequenceExtensions.add_possessable(sequence, component)
    u.MovieSceneBindingExtensions.set_parent(binding, owner_binding)
    u.MovieSceneBindingExtensions.set_name(binding, actor.get_actor_label() + ' fitted match pose')
    track = u.MovieSceneBindingExtensions.add_track(binding, u.MovieSceneSkeletalAnimationTrack)
    section = track.add_section()
    params = u.MovieSceneSkeletalAnimationParams()
    params.set_editor_property('animation', clip)
    params.set_editor_property('force_custom_mode', True)
    params.set_editor_property('skip_anim_notifiers', True)
    section.set_editor_property('params', params)
    actual = section.get_editor_property('params')
    if actual.get_editor_property('animation') != clip or not actual.get_editor_property('force_custom_mode'):
        raise RuntimeError('Native match animation settings did not persist')
    section.set_completion_mode(u.MovieSceneCompletionMode.RESTORE_STATE)
    u.MovieSceneSectionExtensions.set_range(section, 0, END_FRAME)
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if component not in u.MovieSceneSequenceExtensions.locate_bound_objects(sequence, binding, world):
        raise RuntimeError('Pool player binding cannot resolve in the owner level')
    return {'actor': actor.get_path_name(), 'component': component.get_path_name(),
            'clip': clip.get_path_name(), 'cue': player['cue'].get_path_name(),
            'skeleton': mesh.skeleton.get_path_name()}


def apply(ctx, players, cue_ball, motion, static_balls):
    """Author a new unsaved ambient sequence; root explicitly saves reviewed work."""
    import unreal as u
    import AuthorOrbitPoolSequence as previous
    geometry = geometry_guard(Path(u.Paths.project_dir()).resolve())
    return_hardware = _return_guard(ctx)
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name().split('.')[0] != MAP:
        raise RuntimeError('The alternating match belongs only to the separate owner preview')
    api = previous.probe()
    if not api['success']:
        raise RuntimeError('Native sequence API differs: ' + repr(api['missing']))
    if len(players) != 2 or len({p['actor'].get_path_name() for p in players}) != 2:
        raise ValueError('Alternating pool requires exactly two distinct players')
    if len({p['cue'].get_path_name() for p in players}) != 2:
        raise ValueError('Each player must retain a distinct cue')
    if len(static_balls) != 2 or cue_ball in static_balls or static_balls[0] == static_balls[1]:
        raise ValueError('One animated cue ball and two separate stationary object balls are required')
    if len(motion['frames']) != END_FRAME+1 or motion.get('floating_reset') is not False:
        raise ValueError('Expected the fully sampled grounded match motion')
    if not motion.get('held_frames_from_fitted_hand_transforms'):
        raise ValueError('Held ball centers must originate from the fitted hand poses')
    if u.EditorAssetLibrary.does_asset_exist(ASSET):
        raise RuntimeError('Private match sequence already exists; preserve it before authoring a revision')
    for actor in ctx.eas.get_all_level_actors():
        label = actor.get_actor_label()
        if label == LABEL:
            raise RuntimeError('Alternating match sequence already placed')
        if isinstance(actor, u.LevelSequenceActor) and label == previous.LABEL:
            settings = actor.get_editor_property('playback_settings')
            if settings.get_editor_property('auto_play'):
                raise RuntimeError('Old pool playback still active; integration must retire it first')
        if label.startswith('Refine/OrbitPool/Return spill '):
            component = actor.get_component_by_class(u.LocalLightComponent)
            if component and component.is_visible() and float(component.intensity) > 0:
                raise RuntimeError('Magnetic return light remains active')
    # Validate all props and stationary object positions before asset creation.
    prop_rows = [(p['cue'], _prop_preflight(p['cue'], p['cue_samples'])) for p in players]
    prop_rows.append((cue_ball, _prop_preflight(cue_ball, native_ball_samples(motion))))
    static_report = []
    for actor, center in zip(static_balls, STATIC_BALL_CENTERS):
        expected = u.Vector(center[0], center[1], center[2]-BALL_RADIUS)
        if (actor.get_actor_location()-expected).length() > .05:
            raise ValueError('Stationary ball is not at the verified clear starting point')
        for component in actor.get_components_by_class(u.PrimitiveComponent):
            if component.is_simulating_physics():
                raise ValueError('Stationary object ball must not simulate physics')
        static_report.append({'actor': actor.get_path_name(), 'center': center,
                              'location': list(actor.get_actor_location().to_tuple()),
                              'rotation': list(actor.get_actor_rotation().to_tuple()),
                              'scale': list(actor.get_actor_scale3d().to_tuple())})
    package, name = ASSET.rsplit('/', 1)
    sequence = u.AssetToolsHelpers.get_asset_tools().create_asset(
        name, package, u.LevelSequence, u.LevelSequenceFactoryNew())
    if not sequence:
        raise RuntimeError('Private alternating match sequence creation failed')
    u.MovieSceneSequenceExtensions.set_display_rate(sequence, u.FrameRate(FPS, 1))
    u.MovieSceneSequenceExtensions.set_tick_resolution_directly(sequence, u.FrameRate(24000, 1))
    u.MovieSceneSequenceExtensions.set_playback_start(sequence, 0)
    u.MovieSceneSequenceExtensions.set_playback_end(sequence, END_FRAME)
    player_reports = [_skeletal_track(sequence, player) for player in players]
    transforms = [_transform_track(sequence, actor, rows) for actor, rows in prop_rows]
    placed = ctx.eas.spawn_actor_from_class(u.LevelSequenceActor, u.Vector(0, 0, 0))
    if not placed:
        raise RuntimeError('Persistent match sequence player could not be placed')
    ctx.register(placed, LABEL)
    settings = u.MovieSceneSequencePlaybackSettings()
    settings.set_editor_property('auto_play', True)
    settings.set_editor_property('loop_count', u.MovieSceneSequenceLoopCount(value=-1))
    settings.set_editor_property('disable_camera_cuts', True)
    for field in ('disable_movement_input', 'disable_look_at_input', 'hide_player', 'hide_hud'):
        settings.set_editor_property(field, False)
    placed.set_editor_property('playback_settings', settings)
    placed.set_sequence(sequence)
    actual = placed.get_editor_property('playback_settings')
    if (not actual.get_editor_property('auto_play') or
            actual.get_editor_property('loop_count').get_editor_property('value') != -1 or
            not actual.get_editor_property('disable_camera_cuts') or
            any(actual.get_editor_property(field) for field in
                ('disable_movement_input', 'disable_look_at_input', 'hide_player', 'hide_hud'))):
        raise RuntimeError('Native ambient-only playback settings failed readback')
    geometry_guard(Path(u.Paths.project_dir()).resolve())
    return {'module': 'station_pool_match_sequence', 'dirty_assets': [sequence.get_path_name()],
            'sequence_actor': placed.get_path_name(), 'players': player_reports,
            'cue_ball': cue_ball.get_path_name(), 'duration_seconds': DURATION, 'display_rate': FPS,
            'loop_count': -1, 'auto_play': True, 'camera_or_input_tracks': False,
            'transform_tracks': transforms, 'events': EVENTS, 'geometry': geometry,
            'return_hardware': return_hardware,
            'static_ball_anchors': static_report,
            'motion': {k: v for k, v in motion.items() if k != 'frames'},
            'limits': 'Unsaved ambient choreography; inspect actual hands/pockets, both turns and loop seam in PIE'}
