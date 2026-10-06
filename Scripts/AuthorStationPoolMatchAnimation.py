"""Grounded, alternating ambient pool poses; integration lead owns native saves.

The existing Orbit Pool assets remain intact. This helper first measures the
opponent's own skin and compatible idle animation; no cross-skeleton animation
assignment, physical minigame or floating ball reset is introduced.
"""
import hashlib
import json
import math
import copy
from pathlib import Path

import AuthorOrbitPoolAnimation as pool
import RefineStationSocialSeatedCrew as pose_math


TROOPER_MESH = '/Game/Heavy_space_trooper/character/mesh/Heavy_space_trooper_A_Pose'
TROOPER_IDLE = '/Game/Heavy_space_trooper/Demo/animations/ThirdPersonIdle'
PROBE = '.agent/local/StationRefinement/StationPoolMatchProbe1.json'
FPS = 30
PRIVATE = {
    'nyxar': '/Game/OutpostSandbox/StationRefinement/SocialCrew/A_Nyxar_GroundedPoolMatch',
    'trooper': '/Game/OutpostSandbox/StationRefinement/SocialCrew/A_Trooper_GroundedPoolMatch',
}


def _blend_pose(a, b, weight):
    return {name: {'location': pool._mix(row['location'], b[name]['location'], weight),
                   'rotation': pool._lerp_quat(row['rotation'], b[name]['rotation'], weight),
                   'scale': row['scale']} for name, row in a.items()}


def _models(root):
    """Load hash-bound native rigs; never assign one character's clip to another."""
    root = Path(root)
    native, nyxar = pool._load_proof(root)
    heavy = json.loads((root/PROBE).read_text(encoding='utf-8'))
    if not heavy['success'] or not all(heavy['originals_preserved'].values()):
        raise RuntimeError('Grounded pool requires a successful unchanged trooper probe')
    for relative, digest in heavy['existing_receipts'].items():
        if hashlib.sha256((root/relative).read_bytes()).hexdigest() != digest:
            raise RuntimeError('Shared native pool receipt changed: '+relative)
    existing = json.loads((root/'.agent/local/StationRefinement/OrbitPoolGripV3Fit1.json').read_text(encoding='utf-8'))
    models = {}
    for key, data, source, scale in (
            ('nyxar', nyxar['nyxar'], native['animation']['samples'][0], native['fit_scale']),
            ('trooper', heavy['trooper'], heavy['animation']['samples'][0], heavy['fit_scale'])):
        local = {name: copy.deepcopy(row['local']) for name, row in source['bones'].items()}
        local['root']['rotation'] = [0., 0., 0., 1.]
        bones = data['bones']
        prepared = [row for row in pose_math._skin_setup(data)
                    if row[0].startswith(('hand_', 'index_', 'middle_', 'ring_', 'pinky_', 'thumb_',
                                          'foot_', 'ball_', 'ankle_'))]
        model = {'key': key, 'data': data, 'bones': bones, 'scale': scale,
                 'source': local, 'prepared': prepared,
                 'mesh': pool.MESH if key == 'nyxar' else TROOPER_MESH}
        if key == 'nyxar':
            model['old_tracks'] = existing['tracks']
            model['rest'] = {name: rows[0] for name, rows in existing['tracks'].items()}
            model['aim_pose'] = {name: rows[210] for name, rows in existing['tracks'].items()}
            model['origin_z'] = existing['shooter']['location'][2]
            model['cup_offset'] = (8., -5., 0.)
            model['cup_thumb'] = (5.5, -6., -3.5)
            model['cup_angles'] = (45., 45., 35.)
            model['grip_offset'] = (5.6, 0., 8.)
        else:
            model['rest'] = local
            model['origin_z'] = 0.
            model['cup_offset'] = (12., -5., 1.5)
            model['cup_thumb'] = (8.5, -7., -1.5)
            model['cup_angles'] = (35., 45., 35.)
            model['grip_offset'] = (8.*scale, 0., 10.*scale)
        model['rest_world'] = pose_math._forward(model['rest'], bones)
        initial_skin = pose_math._skin(model['rest_world'], prepared)
        model['feet'] = {}
        for side in ('l', 'r'):
            foot = model['rest_world']['foot_'+side]
            target = tuple(foot['location'])
            if key == 'trooper':
                minimum = min(point[2] for name, point in initial_skin
                              if name in ('foot_'+side, 'ball_'+side))
                target = ((18. if side == 'l' else -17.), (17. if side == 'l' else -13.),
                          target[2]-minimum+.6/scale)
            model['feet'][side] = {'location': target, 'rotation': foot['rotation']}
        models[key] = model
    return models, native, heavy


def _shot_clock(key, seconds):
    start = 0. if key == 'nyxar' else 23.5
    return seconds-start if start <= seconds <= start+14. else 0.


def _placement(model, contract):
    yaw = contract.SHOT_YAW + (0. if model['key'] == 'nyxar' else 180.)
    rotation = pool._axis((0., 0., 1.), yaw)
    ball = contract.RESET_SOUTH if model['key'] == 'nyxar' else contract.RESET_NORTH
    offset = pose_math._rotate(rotation, (10., -105., 0.))
    return (ball[0]+offset[0], ball[1]+offset[1], model['origin_z']), rotation, yaw


def _held_path(key, seconds, contract):
    """Centers stay on the physical return tray until grasp, then lift clear."""
    start, end = contract.HELD_INTERVALS[0 if key == 'trooper' else 1]
    pocket = contract.PICKUP_NW if key == 'trooper' else contract.PICKUP_SE
    reset = contract.RESET_NORTH if key == 'trooper' else contract.RESET_SOUTH
    high = (pocket[0], pocket[1], 104.)
    above = (reset[0], reset[1], 104.)
    if seconds <= start:
        center = pocket
    elif seconds < start+1.:
        center = pool._mix(pocket, high, pool._smooth(start, start+1., seconds))
    elif seconds < end-.65:
        center = pool._mix(high, above, pool._smooth(start+1., end-.65, seconds))
    else:
        center = pool._mix(above, reset, pool._smooth(end-.65, end, seconds))
    reach = pool._smooth(start-3., start, seconds)*(1.-pool._smooth(end, end+2., seconds))
    return center, reach, start, end


def _component(point, model):
    scale = model['scale']
    return (point[0]/scale, point[1]/scale, (point[2]-model['origin_z'])/scale)


def _world(point, model, location, rotation):
    value = pose_math._rotate(rotation, pose_math._mul(point, model['scale']))
    return pose_math._add(location, value)


def _feet(local, model):
    for side, target in model['feet'].items():
        pose_math._chain(local, model['bones'], 'thigh_'+side, 'calf_'+side, 'foot_'+side,
                         target['location'], (0., 1., .05))
        pose_math._world_rotation(local, model['bones'], 'foot_'+side, target['rotation'])


def _cup(local, model, amount):
    """Measured five-digit sphere cradle, not an unvalidated wrist attachment."""
    if amount <= 0.:
        return
    bones = model['bones']
    for finger in ('index', 'middle', 'ring', 'pinky'):
        angles = ((25., 25., 25.) if model['key'] == 'nyxar' and finger == 'pinky' else model['cup_angles'])
        for joint, angle in enumerate(angles, 1):
            name = '%s_%02d_l' % (finger, joint)
            local[name]['rotation'] = pool._lerp_quat(local[name]['rotation'], pool._axis((0., 0., 1.), -angle), amount)
    world = pose_math._forward(local, bones)
    hand = world['hand_l']
    target = pose_math._add(hand['location'], pose_math._rotate(hand['rotation'], model['cup_thumb']))
    original = world['thumb_03_l']['location']
    pose_math._chain(local, bones, 'thumb_01_l', 'thumb_02_l', 'thumb_03_l',
                     pool._mix(original, target, amount), pose_math._rotate(hand['rotation'], (0., -1., -1.)))
    current = pose_math._forward(local, bones)['thumb_03_l']['rotation']
    desired = pose_math._qmul(pose_math._between(pose_math._rotate(current, (1., 0., 0.)),
                                               pose_math._rotate(hand['rotation'], (1., 0., 0.))), current)
    pose_math._world_rotation(local, bones, 'thumb_03_l', pool._lerp_quat(current, desired, amount))


def _frame(model, seconds, contract, skin=False):
    pm = pose_math
    bones, scale = model['bones'], model['scale']
    clock = _shot_clock(model['key'], seconds)
    aim, draw = pool._motion(clock)
    center, pickup, grasp, release = _held_path(model['key'], seconds, contract)
    location, rotation, yaw = _placement(model, contract)
    carry_turn = pool._smooth(grasp+1., grasp+3., seconds)
    tray_pose = pickup*(1.-carry_turn)
    hip_shift = (12.*(1.-carry_turn)+(-20. if model['key'] == 'nyxar' else -15.)*carry_turn)*pickup
    hip_forward = 20.*pickup*carry_turn
    hip_down = -8.*pickup-17.*tray_pose
    pickup_lean = pickup*(1.-.45*pool._smooth(grasp, grasp+1., seconds)
                         +.45*pool._smooth(grasp+1.3, grasp+3., seconds))
    if model['key'] == 'nyxar':
        key = min(420, max(0, round(clock*30)))
        local = {name: copy.deepcopy(rows[key]) for name, rows in model['old_tracks'].items()}
        if pickup:
            local = _blend_pose(model['rest'], model['aim_pose'], pickup_lean)
    else:
        local = copy.deepcopy(model['source'])
        source = model['rest_world']
        bend = max(aim, pickup_lean)
        local['pelvis']['location'][2] -= 5.+9.*bend
        local['pelvis']['location'][1] -= 2.+5.*bend
        pm._world_rotation(local, bones, 'pelvis', pm._qmul(pool._axis((1., 0., 0.), -8.-56.*bend),
                                                          source['pelvis']['rotation']))
        for name, extension in (('neck_01', 12.), ('head', 18.)):
            current = pm._forward(local, bones)
            pm._world_rotation(local, bones, name,
                               pm._qmul(pool._axis((1., 0., 0.), extension*bend), current[name]['rotation']))
    if pickup:
        world = pm._forward(local, bones)
        side_bend = pm._qmul(pool._axis((0., 1., 0.), 65.), model['rest_world']['pelvis']['rotation'])
        pm._world_rotation(local, bones, 'pelvis', pool._lerp_quat(
            world['pelvis']['rotation'], side_bend, pickup*(1.-carry_turn)))
        # Bend toward the low return tray within the planted stance, then turn
        # toward the ball-in-hand placement. Never stretch a measured limb.
        local['pelvis']['location'] = pm._add(local['pelvis']['location'],
                                             (hip_shift/scale, hip_forward/scale, hip_down/scale))
    _feet(local, model)
    pitch = 60.*(1.-aim)-6.*aim
    direction = (0., math.cos(math.radians(pitch)), math.sin(math.radians(pitch)))
    contact = (-10., 105.-contract.BALL_RADIUS, contract.BALL_Z)
    idle_grip = (-22., 5., 107.)
    shot_direction = (0., math.cos(math.radians(-6.)), math.sin(math.radians(-6.)))
    aiming_grip = pm._sub(contact, pm._mul(shot_direction, 87.-draw))
    # Lower the cue around the held grip. Interpolating its far tip while
    # changing pitch pulled the glove down beyond the trooper's real reach.
    grip = pm._add(pool._mix(idle_grip, aiming_grip, aim),
                  (hip_shift+20.*tray_pose, hip_forward, hip_down+35.*(pickup-pickup_lean)))
    tip = pm._add(grip, pm._mul(direction, 108.-21.*aim))
    tilt = pool._axis((1., 0., 0.), pitch+6.)
    right_rotation = pm._qmul(tilt, pool._pose_basis((0., 0., 1.), (-1., 0., 0.)))
    right_target = _component(pm._add(grip, pm._rotate(tilt, model['grip_offset'])), model)
    pm._chain(local, bones, 'upperarm_r', 'lowerarm_r', 'hand_r', right_target, (-1., -.2, .25))
    pm._world_rotation(local, bones, 'hand_r', right_rotation)
    if model['key'] == 'trooper':
        for finger in ('index', 'middle', 'ring', 'pinky'):
            for joint, angle in enumerate((55., 55., 45.), 1):
                local['%s_%02d_r' % (finger, joint)]['rotation'] = pool._axis((0., 0., 1.), -angle)
        bridge = pm._sub(contact, pm._mul((0., math.cos(math.radians(-6.)), math.sin(math.radians(-6.))), 23.))
        target = _component((bridge[0]+8., bridge[1]-12., contract.FELT_Z+5.991777032847343), model)
        target = pool._mix(model['rest_world']['hand_l']['location'], target, aim)
        if not pickup:
            pm._chain(local, bones, 'upperarm_l', 'lowerarm_l', 'hand_l', target, (1., .1, .25))
            pm._world_rotation(local, bones, 'hand_l', pool._lerp_quat(model['rest_world']['hand_l']['rotation'],
                                 pool._pose_basis((0., 1., 0.), (0., 0., 1.)), aim))
        for finger in ('index', 'middle', 'ring', 'pinky', 'thumb'):
            for joint in (1, 2, 3):
                name = '%s_%02d_l' % (finger, joint)
                local[name]['rotation'] = pool._lerp_quat(local[name]['rotation'],
                    pool._axis((0., 0., 1.), 0. if finger == 'thumb' else -5.), aim)
    held = None
    if pickup:
        # A measured top/side grip keeps the palm above the physical tray and
        # felt. The same sphere contact survives the whole carry; the other
        # hand retains the cue throughout the bend and recovery.
        placement_up = ((.4275717884, .8447994013, -.3217084663) if model['key'] == 'nyxar'
                        else (.3143200817, .8612537517, -.3993054738))
        top_grip = pm._qmul(pool._axis((0., 0., 1.), 90.), pm._between(placement_up, (0., 0., 1.)))
        hand_rotation = top_grip
        approach = pool._smooth(grasp-3., grasp-1.1, seconds)
        desired_center = center
        if seconds < grasp:
            # Approach above the return tray before lowering to the ball.
            desired_center = pool._mix((center[0], center[1], 118.), center,
                                      pool._smooth(grasp-1.1, grasp, seconds))
        elif seconds > release:
            # Open and lift the empty hand above the felt before retracting it.
            # Turning directly toward idle swings the extended fingertips down.
            desired_center = pm._add(center, (0., 0., 20.*pool._smooth(release, release+.3, seconds)))
        local_center = pm._rotate(pm._inverse(rotation), pm._sub(desired_center, (location[0], location[1], 0.)))
        desired = pm._sub(_component(local_center, model), pm._rotate(hand_rotation, model['cup_offset']))
        reach = approach if seconds < grasp else pickup
        if seconds > release:
            reach = 1.-pool._smooth(release+.3, release+2., seconds)
        target = pool._mix(model['rest_world']['hand_l']['location'], desired, reach)
        rotation_reach = reach
        if seconds > release:
            # Keep the open hand high while it crosses back over the cushion.
            # Only lower/turn it after it has retracted outside the table.
            lower = pool._smooth(release+1.6, release+2., seconds)
            target = (target[0], target[1], desired[2]*(1.-lower)
                      +model['rest_world']['hand_l']['location'][2]*lower)
            rotation_reach = 1.-lower
        pm._chain(local, bones, 'upperarm_l', 'lowerarm_l', 'hand_l', target, (0., 0., 1.))
        pm._world_rotation(local, bones, 'hand_l', pool._lerp_quat(model['rest_world']['hand_l']['rotation'],
                                                                hand_rotation, rotation_reach))
        release_curl = 1.-pool._smooth(release, release+.25, seconds)
        _cup(local, model, pickup*release_curl)
        if grasp <= seconds <= release:
            actual_hand = pm._forward(local, bones)['hand_l']
            held = _world(pm._add(actual_hand['location'], pm._rotate(actual_hand['rotation'], model['cup_offset'])),
                          model, location, rotation)
    # Small, unequal head turns during actual conversational pauses; return to
    # the sight line before the next cue stroke. No lip-sync/audio claim.
    conversation = 0.
    for start, end in contract.EVENTS['conversation_intervals']:
        if start <= seconds <= end:
            conversation = math.sin(math.pi*(seconds-start)/(end-start))**2
    if conversation and not pickup:
        world = pm._forward(local, bones)
        degrees = (-contract.SHOT_YAW+4.*math.sin(seconds*.7))*conversation
        pm._world_rotation(local, bones, 'head', pm._qmul(pool._axis((0., 0., 1.), degrees), world['head']['rotation']))
    world = pm._forward(local, bones)
    cue_tip = pm._add((location[0], location[1], 0.), pm._rotate(rotation, tip))
    cue = {'time': seconds, 'location': list(cue_tip), 'rotation': [pitch, yaw+90., 0.], 'scale': [1., 1., 1.]}
    summary = {'time': seconds, 'aim': aim, 'pickup': pickup,
               'cue_butt_z': tip[2]-156.288*direction[2],
               'right_wrist_error_cm': math.dist(world['hand_r']['location'], right_target)*scale,
               'held_ball_error_cm': math.dist(held, center) if held else None,
               'feet_bone_error_cm': {side: math.dist(world['foot_'+side]['location'], row['location'])*scale
                                      for side, row in model['feet'].items()}}
    if skin:
        skinned = pm._skin(world, model['prepared'])
        summary['feet_surface_z'] = {side: min(point[2]*scale+model['origin_z'] for name, point in skinned
                                             if name in ('foot_'+side, 'ball_'+side, 'ankle_bck_'+side))
                                     for side in ('l', 'r')}
        if held:
            cup_center = pm._add(world['hand_l']['location'], pm._rotate(world['hand_l']['rotation'], model['cup_offset']))
            summary['ball_digit_clearance_cm'] = {finger: min(math.dist(point, cup_center)*scale-contract.BALL_RADIUS
                for name, point in skinned if name.startswith(finger+'_') and name.endswith('_l'))
                for finger in ('hand', 'index', 'middle', 'ring', 'pinky', 'thumb')}
    return local, cue, held, summary


def fit(root, output=None):
    """Generate native-compatible keys and measured ball attachments offline."""
    import AuthorStationPoolMatchSequence as contract
    root = Path(root)
    models, native, heavy = _models(root)
    result = {'success': False, 'duration': contract.DURATION, 'rate': contract.FPS,
              'players': {}, 'held_ball_centers': {}, 'source_sha256': {**native['source_sha256'], **heavy['source_sha256']},
              'evidence': 'Measured baked skeletal/prop motion; requires native visual playback acceptance'}
    for key, model in models.items():
        tracks, cues, held_rows, checks = {}, [], [], []
        for frame in range(contract.END_FRAME+1):
            seconds = frame/contract.FPS
            skin = frame % 15 == 0 or frame in (210, 510, 630, 915, 1290, 1410)
            try:
                local, cue, held, check = _frame(model, seconds, contract, skin)
            except Exception as exc:
                raise RuntimeError('%s pool pose at %.4fs: %s' % (key, seconds, exc)) from exc
            if (check['right_wrist_error_cm'] > .01 or max(check['feet_bone_error_cm'].values()) > .01 or
                    check['cue_butt_z'] < 2. or (held and check['held_ball_error_cm'] > .01)):
                raise RuntimeError('Grounded pool contact failed: '+json.dumps(check))
            if skin and any(not 0. <= value <= 1.2 for value in check['feet_surface_z'].values()):
                raise RuntimeError('Grounded pool sole contact failed: '+json.dumps(check))
            if 'ball_digit_clearance_cm' in check:
                clearances = list(check['ball_digit_clearance_cm'].values())
                if min(clearances) < 0. or sum(value <= .8 for value in clearances) < 3:
                    raise RuntimeError('Grounded pool sphere cradle failed: '+json.dumps(check))
            for name, transform in local.items():
                keys = tracks.setdefault(name, [])
                if keys and pose_math._dot(keys[-1]['rotation'], transform['rotation']) < 0.:
                    transform['rotation'] = pose_math._mul(transform['rotation'], -1.)
                keys.append(transform)
            cues.append(cue)
            if held:
                held_rows.append({'time': seconds, 'center': list(held)})
            if skin:
                checks.append(check)
        for name, keys in tracks.items():
            if math.dist(keys[0]['location'], keys[-1]['location']) > .001 or abs(
                    pose_math._dot(keys[0]['rotation'], keys[-1]['rotation'])) < .999999:
                raise RuntimeError('Grounded pool skeletal loop seam: '+key+'/'+name)
        location, rotation, yaw = _placement(model, contract)
        result['players'][key] = {'mesh': model['mesh'], 'private_clip': PRIVATE[key],
            'actor_location': list(location), 'actor_rotation': [0., yaw, 0.], 'mesh_scale': [model['scale']]*3,
            'held_ball_local_offset': list(model['cup_offset']),
            'cue_samples': cues, 'tracks': tracks, 'contact_validation': checks}
        result['held_ball_centers'][key] = held_rows
    # The choreography owner verifies actual pocket walls, cushion traversal,
    # phase joins and physical rolling using these solved hand-center streams.
    motion = contract.build_motion(result['held_ball_centers'])
    result['ball_motion_verified'] = True
    result['success'] = True
    if output:
        Path(output).write_text(json.dumps(result, separators=(',', ':')), encoding='utf-8')
    return result


def create(ctx):
    """Create two private clips unsaved; caller alone owns transaction/save/rebind."""
    import unreal as u
    root = Path(u.Paths.project_dir()).resolve()
    result = fit(root)
    before = {path: pool._sha(root, path) for path in result['source_sha256']}
    if before != result['source_sha256']:
        raise RuntimeError('Grounded pool source changed after the native probe')
    clips = {}
    for key, player in result['players'].items():
        path = player['private_clip']
        if u.EditorAssetLibrary.does_asset_exist(path):
            raise RuntimeError('Preserve existing grounded pool clip: '+path)
        mesh = ctx.asset(player['mesh'])
        factory = u.AnimSequenceFactory()
        factory.target_skeleton = mesh.skeleton
        factory.preview_skeletal_mesh = mesh
        folder, name = path.rsplit('/', 1)
        clip = u.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, u.AnimSequence, factory)
        if not clip:
            raise RuntimeError('Could not create grounded pool clip: '+path)
        controller = clip.get_editor_property('controller')
        controller.open_bracket('Grounded alternating pool stance and physical ball pickup', False)
        try:
            controller.set_frame_rate(u.FrameRate(FPS, 1), False)
            controller.set_number_of_frames(u.FrameNumber(round(result['duration']*FPS)), False)
            for bone, keys in player['tracks'].items():
                controller.add_bone_curve(bone, False)
                if not controller.set_bone_track_keys(bone, [u.Vector(*row['location']) for row in keys],
                        [u.Quat(*row['rotation']) for row in keys], [u.Vector(*row['scale']) for row in keys], False):
                    raise RuntimeError('Grounded pool track write failed: '+key+'/'+bone)
        finally:
            controller.close_bracket(False)
        clips[key] = clip
    models, _, _ = _models(root)
    frames = (0, 210, 510, 555, 630, 915, 1290, 1335, 1410, 1800)
    for key, clip in clips.items():
        mesh = ctx.asset(result['players'][key]['mesh'])
        options = u.AnimPoseEvaluationOptions(optional_skeletal_mesh=mesh, evaluation_type=u.AnimDataEvalType.RAW)
        maximum = 0.
        for frame in frames:
            actual = u.AnimPoseExtensions.get_anim_pose_at_time(clip, frame/FPS, options)
            local = {name: keys[frame] for name, keys in result['players'][key]['tracks'].items()}
            expected = pose_math._forward(local, models[key]['bones'])
            for name, value in expected.items():
                transform = u.AnimPoseExtensions.get_bone_pose(actual, name, u.AnimPoseSpaces.WORLD)
                maximum = max(maximum, math.dist(transform.translation.to_tuple(), value['location']))
                if abs(pose_math._dot(transform.rotation.to_tuple(), value['rotation'])) < .99999:
                    raise RuntimeError('Grounded pool native rotation differs: '+key+'/'+name)
        if maximum > .015 or abs(float(clip.sequence_length)-result['duration']) > .0001:
            raise RuntimeError('Grounded pool native pose/duration readback differs: '+key)
        del result['players'][key]['tracks']
        result['players'][key]['native_readback_frames'] = list(frames)
        result['players'][key]['native_readback_max_cm'] = maximum
    if any(pool._sha(root, path) != digest for path, digest in before.items()):
        raise RuntimeError('Grounded pool author changed a source asset')
    result['dirty_assets'] = list(PRIVATE.values())
    result['source_originals_preserved'] = True
    return clips, result


def probe(ctx, output=None):
    """Read-only native contact skin and standing poses, without loading a map.

    Nyxar and table measurements are reused through hashes of existing receipts.
    The trooper export retains all bones but only skin near hands and feet. Its
    original vertex IDs and filtering bounds are recorded explicitly.
    """
    import unreal as u
    root = Path(u.Paths.project_dir()).resolve()
    output = Path(output) if output else root / PROBE
    if output.exists():
        raise RuntimeError('Preserve existing match probe evidence: '+str(output))
    previous, _ = pool._load_proof(root)
    source_paths = (TROOPER_MESH, TROOPER_IDLE)
    hashes = {path: pool._sha(root, path) for path in source_paths}
    report = {'success': False, 'source_sha256': hashes,
              'scope': 'Read-only native rig/contact skin; no scene edits, animation authoring or acceptance',
              'existing_receipts': {str(path): hashlib.sha256((root/path).read_bytes()).hexdigest()
                  for path in (pool.SKIN_RECEIPT, '.agent/local/StationRefinement/OrbitPoolProbe1.json')}}
    try:
        mesh, clip = [ctx.asset(path) for path in source_paths]
        if mesh.skeleton != clip.get_editor_property('skeleton'):
            raise RuntimeError('Heavy trooper idle must match its native skeleton')
        dynamic, data = pose_math._geometry(mesh, True, u)
        _, bones = u.GeometryScript_BoneWeights.get_all_bones_info(dynamic)
        data['bones'] = [{'index': b.index, 'parent': b.parent_index, 'name': str(b.name),
                          'reference_world': pose_math._transform(b.world_transform)} for b in bones]
        bone_names = {b['name'] for b in data['bones']}
        required = {'root', 'pelvis', 'hand_l', 'hand_r', 'foot_l', 'foot_r',
                    'upperarm_l', 'lowerarm_l', 'upperarm_r', 'lowerarm_r',
                    'thigh_l', 'calf_l', 'thigh_r', 'calf_r'}
        required |= {f'{finger}_{joint:02d}_{side}' for side in ('l', 'r')
                     for finger in ('thumb', 'index', 'middle', 'ring', 'pinky') for joint in (1, 2, 3)}
        if not required <= bone_names:
            raise RuntimeError('Trooper requires measured native limb/digit chains: '+str(sorted(required-bone_names)))
        centers = [(b['reference_world']['location'], 40. if b['name'].startswith('hand_') else 28.)
                   for b in data['bones'] if b['name'] in ('hand_l', 'hand_r', 'foot_l', 'foot_r')]
        used = [index for index, point in enumerate(data['vertices'])
                if any(math.dist(point, center) <= radius for center, radius in centers)]
        remap = {old: new for new, old in enumerate(used)}
        weights = []
        for index in used:
            _, rows, valid = u.GeometryScript_BoneWeights.get_vertex_bone_weights(dynamic, index)
            total = sum(row.weight for row in rows)
            if not valid or abs(total-1.) > .002:
                raise RuntimeError('Trooper contact skin weight invalid: '+str(index))
            weights.append([[row.bone_index, float(row.weight/total)] for row in rows])
        data['contact_filter'] = {'source_vertex_count': len(data['vertices']),
                                  'source_triangle_count': len(data['triangles']),
                                  'reference_centers_and_radii_cm': centers, 'original_vertex_ids': used}
        data['triangles'] = [[remap[index] for index in face] for face in data['triangles']
                             if all(index in remap for index in face)]
        data['vertices'] = [data['vertices'][index] for index in used]
        data['weights'] = weights
        report['trooper'] = data
        bounds = mesh.get_bounds()
        report['fit_scale'] = 205. / (bounds.box_extent.z*2.)
        report['native_bounds'] = {'origin': list(bounds.origin.to_tuple()),
                                   'extent': list(bounds.box_extent.to_tuple())}
        report['skeleton'] = mesh.skeleton.get_path_name()
        report['table_surface'] = pool._surface(previous)
        model = clip.get_editor_property('data_model_interface')
        rate = model.get_frame_rate()
        report['animation'] = {'clip': clip.get_path_name(), 'length_seconds': float(clip.sequence_length),
                               'frame_rate': [rate.numerator, rate.denominator],
                               'key_count': model.get_number_of_keys(), 'samples': []}
        options = u.AnimPoseEvaluationOptions(optional_skeletal_mesh=mesh, evaluation_type=u.AnimDataEvalType.RAW)
        api = u.AnimPoseExtensions
        for step in range(9):
            seconds = float(clip.sequence_length)*step/8.
            pose = api.get_anim_pose_at_time(clip, seconds, options)
            if not bone_names <= set(map(str, api.get_bone_names(pose))):
                raise RuntimeError('Native trooper idle pose omits measured mesh bones')
            sample = {'seconds': seconds, 'bones': {
                name: {'world': pose_math._transform(api.get_bone_pose(pose, name, u.AnimPoseSpaces.WORLD)),
                       'local': pose_math._transform(api.get_bone_pose(pose, name, u.AnimPoseSpaces.LOCAL))}
                for name in sorted(bone_names)}}
            local = {name: row['local'] for name, row in sample['bones'].items()}
            rebuilt = pose_math._forward(local, data['bones'])
            error = max(math.dist(rebuilt[name]['location'], row['world']['location'])
                        for name, row in sample['bones'].items())
            if error > .005:
                raise RuntimeError('Trooper native/offline pose reconstruction mismatch: %.6f cm'%error)
            sample['native_reconstruction_max_cm'] = error
            report['animation']['samples'].append(sample)
        report['success'] = True
    finally:
        report['originals_preserved'] = {path: pool._sha(root, path) == digest for path, digest in hashes.items()}
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, separators=(',', ':')), encoding='utf-8')
        if not all(report['originals_preserved'].values()):
            raise RuntimeError('Read-only trooper probe changed a source asset')
    return {'success': report['success'], 'output': str(output),
            'contact_vertices': len(report['trooper']['vertices']),
            'bones': len(report['trooper']['bones']), 'raw_pose_samples': len(report['animation']['samples']),
            'source_sha256': hashes, 'dirty_assets': []}
