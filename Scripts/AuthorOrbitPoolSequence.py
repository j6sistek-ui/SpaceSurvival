"""Author the ambient pool match; integration lead owns map and asset saves.

UE 5.8 source contracts: MovieSceneSequence/Binding/SectionExtensions,
MovieSceneScriptingDouble, MovieSceneSkeletalAnimationSection and
MovieSceneSequencePlaybackSettings. There are no camera, input or game-state tracks.

apply(ctx, shooter, clip, cue, cue_samples, balls): cue_samples and every ball's
samples are rows with time (seconds), location (world cm), rotation (pitch, yaw,
roll degrees), scale (xyz). Include both 0 and 14 seconds with matching poses.
balls is [{actor: placed_actor, samples: rows}, ...], exactly three balls.
All animated prop actors must be unattached. The shooter may be a skeletal actor
or its skeletal component. Source assets are never saved or altered here.
"""
import math
import struct

import unreal as u


FPS = 30
DURATION = 14.0
END_FRAME = 420
ASSET = '/Game/OutpostSandbox/StationRefinement/Sequences/LS_OrbitPool_20261006'
LABEL = 'Refine/OrbitPool/Ambient match sequence'
CHANNELS = ('Location.X', 'Location.Y', 'Location.Z', 'Rotation.X', 'Rotation.Y',
            'Rotation.Z', 'Scale.X', 'Scale.Y', 'Scale.Z')


def probe():
    """Read-only reflected-API probe for the lead's existing editor process."""
    required = {
        'LevelSequence': (), 'LevelSequenceFactoryNew': (),
        'LevelSequenceActor': ('set_sequence',),
        'UnrealEditorSubsystem': ('get_editor_world',),
        'SkeletalMeshComponent': ('get_skeletal_mesh_asset',),
        'PrimitiveComponent': ('is_simulating_physics',),
        'MovieSceneSequenceExtensions': ('add_possessable', 'set_display_rate',
            'set_tick_resolution_directly', 'set_playback_start', 'set_playback_end',
            'locate_bound_objects'),
        'MovieSceneBindingExtensions': ('add_track', 'set_parent', 'set_name'),
        'MovieSceneSectionExtensions': ('set_range', 'get_all_channels'),
        'MovieSceneSkeletalAnimationTrack': ('add_section',),
        'MovieScene3DTransformTrack': ('add_section',),
        'MovieSceneScriptingDoubleChannel': ('add_key', 'set_default', 'get_keys'),
        'MovieSceneScriptingDoubleKey': ('get_value', 'set_value', 'get_interpolation_mode'),
    }
    missing = [name + ('.' + method if method else '')
               for name, methods in required.items()
               for method in (methods or ('',))
               if not hasattr(u, name) or (method and not hasattr(getattr(u, name), method))]
    fields = {}
    if not missing:
        for struct, names in (
            (u.MovieSceneSkeletalAnimationParams(), ('animation', 'force_custom_mode', 'skip_anim_notifiers')),
            (u.MovieSceneSequencePlaybackSettings(), ('auto_play', 'loop_count', 'disable_camera_cuts',
                'disable_movement_input', 'disable_look_at_input', 'hide_player', 'hide_hud')),
            (u.MovieSceneSequenceLoopCount(), ('value',))):
            for name in names:
                try:
                    fields[type(struct).__name__ + '.' + name] = str(struct.get_editor_property(name))
                except Exception as exc:
                    missing.append(type(struct).__name__ + '.' + name + ': ' + str(exc))
    return {'success': not missing, 'missing': missing, 'fields': fields,
            'scope': 'Reflected API only; no asset creation, save or playback'}


def _triplet(value, name):
    values = tuple(float(v) for v in value)
    if len(values) != 3 or not all(math.isfinite(v) for v in values):
        raise ValueError(name + ' requires three finite numbers')
    return values


def _samples(rows, name):
    result = []
    previous = -1
    for row in rows:
        seconds = float(row['time'])
        frame = round(seconds * FPS)
        if not math.isfinite(seconds) or abs(seconds * FPS - frame) > .0001:
            raise ValueError(name + ' keys must lie on the shared 30 Hz animation clock')
        if frame <= previous or not 0 <= frame <= END_FRAME:
            raise ValueError(name + ' keys must increase within [0, 14] seconds')
        location = _triplet(row['location'], name + ' location')
        pitch, yaw, roll = _triplet(row['rotation'], name + ' rotation')
        scale = _triplet(row['scale'], name + ' scale')
        if min(scale) <= 0:
            raise ValueError(name + ' has non-positive scale')
        # Native transform channels are XYZ rotation = roll, pitch, yaw.
        result.append((frame, location + (roll, pitch, yaw) + scale))
        previous = frame
    if len(result) < 2 or result[0][0] != 0 or result[-1][0] != END_FRAME:
        raise ValueError(name + ' must include the complete 0/14 second loop')
    first, last = result[0][1], result[-1][1]
    for index, (a, b) in enumerate(zip(first, last)):
        error = abs((b-a+180) % 360-180) if 3 <= index < 6 else abs(b-a)
        if error > (.05 if index < 6 else 1e-6):
            raise ValueError(name + ' loop endpoint would visibly jump')
    return result


def _prop_preflight(actor, rows):
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


def carom_samples(cue_ball_center, shot_direction, felt_bounds, ball_radius,
                  contact_time=7.0, ball_scale=(1, 1, 1)):
    """Measured-frame carom, then visible magnetic return; no scene mutations.

    Inputs are world-space cue-ball center, horizontal strike direction, native
    felt bounds [min_x, max_x, min_y, max_y], actual radius and uniform native
    ball scale. Output sample locations compensate the ball's bottom pivot.
    Lead positions the three new balls at samples[0] before calling apply.
    This is ambient keyframed choreography, not a physics simulation/minigame.
    """
    origin = _triplet(cue_ball_center, 'cue ball center')
    direction = _triplet(shot_direction, 'shot direction')
    if abs(direction[2]) > .02:
        raise ValueError('Ball roll requires the measured horizontal projection of the cue direction')
    norm = math.hypot(direction[0], direction[1])
    if norm < .9:
        raise ValueError('Strike direction must be a nonzero unit-scale vector')
    direction = (direction[0]/norm, direction[1]/norm, 0.)
    side = (direction[1], -direction[0], 0.)
    radius = float(ball_radius)
    scale = _triplet(ball_scale, 'native ball scale')
    if radius <= 0 or max(scale)-min(scale) > .000001:
        raise ValueError('Pool balls need positive radius and uniform scale')
    bounds = tuple(float(x) for x in felt_bounds)
    if len(bounds) != 4 or not all(math.isfinite(v) for v in bounds):
        raise ValueError('Measured felt rectangle requires four finite bounds')
    contact_time = float(contact_time)
    if not 0 < contact_time <= 7.0 or abs(contact_time*FPS-round(contact_time*FPS)) > .0001:
        raise ValueError('Cue contact must lie on 30Hz clock and allow settlement before 10 seconds')

    def add(a, b, amount=1):
        return tuple(x+amount*y for x, y in zip(a, b))

    def lerp(a, b, t):
        t = max(0., min(1., t))
        return tuple(x+(y-x)*t for x, y in zip(a, b))

    def smooth(t):
        t = max(0., min(1., t))
        return t*t*(3-2*t)

    def out(t):
        t = max(0., min(1., t))
        return 1-(1-t)**2

    # Half-radius lateral offset creates a clear glancing collision. The second
    # object is placed on that ball's actual outward normal, not a separate lane.
    normal = add(tuple(v*math.sqrt(.75) for v in direction), side, .5)
    tangent = add(tuple(v*.5 for v in direction), side, -math.sqrt(.75))
    object_one = add(add(origin, direction, 55.), side, radius)
    first_contact = add(object_one, normal, -2*radius)
    object_two = add(object_one, normal, 30.)
    second_contact = add(object_two, normal, -2*radius)
    starts = (origin, object_one, object_two)
    stops = (add(first_contact, tangent, 30.), second_contact, add(object_two, normal, 30.))
    first_time, second_time, settled_time = contact_time+.7, contact_time+1.2, 9.75
    paths = [[], [], []]
    for frame in range(END_FRAME+1):
        t = frame/FPS
        positions = [origin, object_one, object_two]
        if t > contact_time:
            positions[0] = (lerp(origin, first_contact, (t-contact_time)/(first_time-contact_time))
                            if t <= first_time else
                            lerp(first_contact, stops[0], out((t-first_time)/(settled_time-first_time))))
        if t > first_time:
            positions[1] = lerp(object_one, second_contact, (t-first_time)/(second_time-first_time))
        if t > second_time:
            positions[2] = lerp(object_two, stops[2], out((t-second_time)/(settled_time-second_time)))
        if t >= 10:
            for index, lift in enumerate((12., 15., 18.)):
                if t <= 10.6:
                    positions[index] = add(stops[index], (0, 0, 1), lift*smooth((t-10)/.6))
                elif t <= 13:
                    positions[index] = add(lerp(stops[index], starts[index], smooth((t-10.6)/2.4)),
                                           (0, 0, 1), lift)
                else:
                    positions[index] = add(starts[index], (0, 0, 1), lift*(1-smooth((t-13)/.8)))
        for index, center in enumerate(positions):
            if not (bounds[0]+radius <= center[0] <= bounds[1]-radius and
                    bounds[2]+radius <= center[1] <= bounds[3]-radius):
                raise ValueError('Carom exceeds measured felt at frame %d, ball %d' % (frame, index))
            for other in positions[:index]:
                distance = math.dist(center, other)
                if distance < 2*radius-.02:
                    raise ValueError('Carom balls overlap by %.4f cm at frame %d' % (2*radius-distance, frame))
            paths[index].append(center)

    def multiply(a, b):
        x, y, z, w = a
        X, Y, Z, W = b
        return (w*X+x*W+y*Z-z*Y, w*Y-x*Z+y*W+z*X, w*Z+x*Y-y*X+z*W, w*W-x*X-y*Y-z*Z)

    rows = []
    for index, path in enumerate(paths):
        rotation = (0., 0., 0., 1.)
        held_rotation = rotation
        samples = []
        previous_angles = None
        for frame, center in enumerate(path):
            t = frame/FPS
            if frame and t < 10:
                delta = tuple(b-a for a, b in zip(path[frame-1], center))
                travel = math.hypot(delta[0], delta[1])
                if travel > .000001:
                    half_angle = travel/radius*.5
                    axis = (-delta[1]/travel, delta[0]/travel, 0.)
                    increment = tuple(v*math.sin(half_angle) for v in axis)+(math.cos(half_angle),)
                    rotation = multiply(increment, rotation)
                held_rotation = rotation
            elif t >= 10.6:
                # Normalize/shortest-path nlerp back to the display pose while
                # suspended; the translational return remains visibly continuous.
                blend = smooth((t-10.6)/2.4)
                q = held_rotation if held_rotation[3] >= 0 else tuple(-x for x in held_rotation)
                q = tuple(v*(1-blend)+(blend if axis == 3 else 0.) for axis, v in enumerate(q))
                length = math.sqrt(sum(v*v for v in q))
                rotation = tuple(v/length for v in q)
            quaternion = u.Quat(*rotation)
            rotator = quaternion.rotator()
            angles = [rotator.pitch, rotator.yaw, rotator.roll]
            if previous_angles is not None:
                angles = [old+(new-old+180)%360-180 for old, new in zip(previous_angles, angles)]
            previous_angles = angles
            # Native Ball01 origin is its bottom. Rotate the center offset too,
            # otherwise a nominal rolling sphere would bob through the felt.
            offset = quaternion.rotate_vector(u.Vector(0, 0, radius))
            samples.append({'time': t,
                            'location': [center[0]-offset.x, center[1]-offset.y, center[2]-offset.z],
                            'rotation': angles, 'scale': list(scale)})
        _samples(samples, 'ball %d' % index)
        rows.append(samples)
    return {'samples': rows, 'centers': paths, 'contact_seconds': [contact_time, first_time, second_time],
            'settled_seconds': settled_time, 'return_seconds': [10., 10.6, 13., 13.8],
            'magnetic_lifts_cm': [12., 15., 18.], 'ball_radius_cm': radius,
            'native_felt_bounds': bounds, 'center_clearance_checked_frames': END_FRAME+1,
            'scope': 'Ambient sampled carom and magnetic return, not player billiards physics'}


def apply(ctx, shooter, clip, cue, cue_samples, balls):
    """Create only a new private sequence and placed player; caller explicitly saves."""
    api = probe()
    if not api['success']:
        raise RuntimeError('Sequence API probe failed: ' + repr(api['missing']))
    component = (shooter if isinstance(shooter, u.SkeletalMeshComponent)
                 else shooter.get_component_by_class(u.SkeletalMeshComponent))
    actor = component.get_owner() if component else None
    mesh = component.get_skeletal_mesh_asset() if component else None
    if not actor or not actor.get_actor_label().startswith('Refine/') or not mesh:
        raise ValueError('Pool shooter must be a placed refinement skeletal actor')
    if not isinstance(clip, u.AnimSequence) or clip.get_editor_property('skeleton') != mesh.skeleton:
        raise ValueError('Pool clip must use the actual shooter skeleton')
    if abs(float(clip.sequence_length)-DURATION) > .001:
        raise ValueError('Pool clip must span the same exact 14 second clock')
    if len(balls) != 3 or len({ball['actor'].get_path_name() for ball in balls}) != 3:
        raise ValueError('Orbit pool uses exactly one cue ball and two distinct object balls')
    prop_rows = [(cue, _prop_preflight(cue, cue_samples))]
    prop_rows.extend((ball['actor'], _prop_preflight(ball['actor'], ball['samples'])) for ball in balls)
    if u.EditorAssetLibrary.does_asset_exist(ASSET):
        raise RuntimeError('Sequence already exists: back up/review the private target before a new revision')
    if any(a.get_actor_label() == LABEL for a in ctx.eas.get_all_level_actors()):
        raise RuntimeError('Pool sequence actor already exists; refusing duplicate playback')

    package, name = ASSET.rsplit('/', 1)
    sequence = u.AssetToolsHelpers.get_asset_tools().create_asset(
        name, package, u.LevelSequence, u.LevelSequenceFactoryNew())
    if not sequence:
        raise RuntimeError('Private pool sequence creation failed')
    u.MovieSceneSequenceExtensions.set_display_rate(sequence, u.FrameRate(FPS, 1))
    u.MovieSceneSequenceExtensions.set_tick_resolution_directly(sequence, u.FrameRate(24000, 1))
    u.MovieSceneSequenceExtensions.set_playback_start(sequence, 0)
    u.MovieSceneSequenceExtensions.set_playback_end(sequence, END_FRAME)
    owner_binding = u.MovieSceneSequenceExtensions.add_possessable(sequence, actor)
    binding = u.MovieSceneSequenceExtensions.add_possessable(sequence, component)
    u.MovieSceneBindingExtensions.set_parent(binding, owner_binding)
    u.MovieSceneBindingExtensions.set_name(binding, 'Measured shooter pose')
    track = u.MovieSceneBindingExtensions.add_track(binding, u.MovieSceneSkeletalAnimationTrack)
    section = track.add_section()
    params = u.MovieSceneSkeletalAnimationParams()
    params.set_editor_property('animation', clip)
    params.set_editor_property('force_custom_mode', True)
    params.set_editor_property('skip_anim_notifiers', True)
    section.set_editor_property('params', params)
    actual_params = section.get_editor_property('params')
    if (actual_params.get_editor_property('animation') != clip or
            not actual_params.get_editor_property('force_custom_mode')):
        raise RuntimeError('Native shooter animation settings did not persist in the section')
    section.set_completion_mode(u.MovieSceneCompletionMode.RESTORE_STATE)
    u.MovieSceneSectionExtensions.set_range(section, 0, END_FRAME)
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if component not in u.MovieSceneSequenceExtensions.locate_bound_objects(sequence, binding, world):
        raise RuntimeError('Shooter component binding cannot resolve in owner level')
    transforms = [_transform_track(sequence, prop, rows) for prop, rows in prop_rows]

    placed = ctx.eas.spawn_actor_from_class(u.LevelSequenceActor, u.Vector(0, 0, 0))
    if not placed:
        raise RuntimeError('Persistent pool playback actor could not be placed')
    ctx.register(placed, LABEL)
    settings = u.MovieSceneSequencePlaybackSettings()
    settings.set_editor_property('auto_play', True)
    settings.set_editor_property('loop_count', u.MovieSceneSequenceLoopCount(value=-1))
    settings.set_editor_property('disable_camera_cuts', True)
    for field in ('disable_movement_input', 'disable_look_at_input', 'hide_player', 'hide_hud'):
        settings.set_editor_property(field, False)
    placed.set_editor_property('playback_settings', settings)
    placed.set_sequence(sequence)
    actual_settings = placed.get_editor_property('playback_settings')
    if (not actual_settings.get_editor_property('auto_play') or
            actual_settings.get_editor_property('loop_count').get_editor_property('value') != -1 or
            not actual_settings.get_editor_property('disable_camera_cuts') or
            any(actual_settings.get_editor_property(field) for field in
                ('disable_movement_input', 'disable_look_at_input', 'hide_player', 'hide_hud'))):
        raise RuntimeError('Native ambient-only sequence playback settings differ from requested values')
    return {'module': 'orbit_pool_sequence', 'dirty_assets': [sequence.get_path_name()],
            'sequence_actor': placed.get_path_name(), 'clip': clip.get_path_name(),
            'duration_seconds': DURATION, 'display_rate': FPS, 'loop_count': -1,
            'auto_play': True, 'camera_or_input_tracks': False, 'transform_tracks': transforms,
            'limits': 'Unsaved ambient choreography; verify reload, PIE synchronization and loop seam before acceptance'}
