"""Measured Nyxar ambient pool animation authoring.

The lead owns serialized Unreal execution, placement and asset saves. The initial
probe only reads native source assets; cue, stance and table contacts must be fit
from that receipt before creating a private animation. No pool minigame is added.
"""
import hashlib
import json
import math
import copy
from pathlib import Path

import RefineStationSocialSeatedCrew as pose_math


MESH = '/Game/Nyxar/Meshes/SKM_Nyxar'
SOURCE_CLIP = '/Game/SpaceSurvival/Licensed/StationAssets/AlienCrew/Anims/A_Alien_Convo_11_Listening_Loop'
PRIVATE_CLIP = '/Game/OutpostSandbox/StationRefinement/SocialCrew/A_Nyxar_OrbitPool_GripV3'
POOL_ROOT = '/Game/Rocket/MLR_PoolTable/'
POOL_MESHES = tuple(POOL_ROOT + 'SM_MLR_PoolTable' + suffix + '_c1_Nanite'
                    for suffix in ('', '_Base', '_CueStick', '_CueRack', '_Triangle', '_Ball01'))
SKIN_RECEIPT = '.agent/local/StationRefinement/SocialSeatedProbe.json'
TABLE_POSITION = (4800., -3150., 0.)
SHOOTER_POSITION = (4810., -3330., 0.)
DURATION = 14.
RATE = 30
CONTACT_TIME = 7.
BRIDGE_HAND_X = 11.
BRIDGE_HAND_Y = -9.
BRIDGE_HAND_Z = 5.2
GRIP_HAND_X = 5.6
REAR_CURL = {'index': (55., 55., 45.), 'middle': (55., 55., 45.),
             'ring': (55., 55., 45.), 'pinky': (10., 45., 30.)}


def _smooth(a, b, t):
    x = max(0., min(1., (t-a)/(b-a)))
    return x*x*(3.-2.*x)


def _axis(axis, degrees):
    half = math.radians(degrees)*.5
    return (*pose_math._mul(pose_math._unit(axis), math.sin(half)), math.cos(half))


def _mix(a, b, amount):
    return tuple(x+(y-x)*amount for x, y in zip(a, b))


def _lerp_quat(a, b, amount):
    if pose_math._dot(a, b) < 0:
        b = pose_math._mul(b, -1.)
    return pose_math._unit(_mix(a, b, amount))


def _pose_basis(x, y):
    """Rotation mapping the local X/Y axes onto measured unit world vectors."""
    first = pose_math._between((1., 0., 0.), x)
    actual_y = pose_math._rotate(first, (0., 1., 0.))
    return pose_math._qmul(pose_math._between(actual_y, y), first)


def _motion(t):
    aim = _smooth(1.5, 3.5, t)*(1.-_smooth(8.2, 10.2, t))
    draw = -4.*aim
    peak = 21.*_smooth(6.8, 7.15, CONTACT_TIME)
    if 3.5 <= t < 6.2:
        draw = -4.-6.*(.5-.5*math.cos((t-3.5)*math.tau/1.35))
    elif 6.2 <= t < 6.8:
        draw = -4.-(peak-4.)*_smooth(6.2, 6.8, t)
    elif 6.8 <= t <= 7.15:
        # Tip reaches the cue ball's south tangent exactly at frame210/7s.
        draw = -peak+21.*_smooth(6.8, 7.15, t)
    elif 7.15 < t < 8.2:
        draw = 21.-peak
    elif t >= 8.2:
        draw = (21.-peak)*aim
    return aim, draw


def _load_proof(root):
    root = Path(root)
    path = root / '.agent/local/StationRefinement/OrbitPoolProbe1.json'
    proof = json.loads(path.read_text(encoding='utf-8'))
    skin_path = root / proof['skin_receipt']
    if (not proof['success'] or not all(proof['originals_preserved'].values()) or
            hashlib.sha256(skin_path.read_bytes()).hexdigest() != proof['skin_receipt_sha256']):
        raise RuntimeError('Pool fit requires successful exact native source receipts')
    skin = json.loads(skin_path.read_text(encoding='utf-8'))
    return proof, skin


def _surface(proof):
    """Find the broad actual cloth plane by summed horizontal triangle area."""
    data = proof['props'][POOL_MESHES[0]]
    vertices, planes = data['vertices'], {}
    for face in data['triangles']:
        a, b, c = [vertices[i] for i in face]
        area = abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))*.5
        if max(a[2], b[2], c[2])-min(a[2], b[2], c[2]) < .015 and area > .001:
            z = round((a[2]+b[2]+c[2])/3., 2)
            row = planes.setdefault(z, {'area': 0., 'lo': [1e9, 1e9], 'hi': [-1e9, -1e9]})
            row['area'] += area
            for point in (a, b, c):
                for axis in range(2):
                    row['lo'][axis] = min(row['lo'][axis], point[axis])
                    row['hi'][axis] = max(row['hi'][axis], point[axis])
    z, row = max(planes.items(), key=lambda item: item[1]['area'])
    if row['area'] < 20000. or not 75. < z < 85.:
        raise RuntimeError('Native cloth plane is not the inspected broad table surface')
    return {'z': z, 'native_xy_min': row['lo'], 'native_xy_max': row['hi'], 'horizontal_area_cm2': row['area']}


def _fit_frame(proof, skin, surface, t, prepared, fixed_origin_z=None):
    pm = pose_math
    bones = skin['nyxar']['bones']
    scale = proof['fit_scale']
    local = {name: copy.deepcopy(row['local']) for name, row in proof['animation']['samples'][0]['bones'].items()}
    local['root']['rotation'] = [0., 0., 0., 1.]
    source = pm._forward(local, bones)
    original_skin = pm._skin(source, prepared)
    origin_z = (.6-min(p[2] for n, p in original_skin if n.startswith(('foot_', 'ball_', 'ankle_')))*scale
                if fixed_origin_z is None else fixed_origin_z)
    aim, draw = _motion(t)
    local['pelvis']['location'][2] -= 5.+9.*aim
    local['pelvis']['location'][1] -= 2.+5.*aim
    pm._world_rotation(local, bones, 'pelvis', pm._qmul(_axis((1., 0., 0.), -8.-56.*aim), source['pelvis']['rotation']))
    # Both feet use fixed native ankle orientation and separate planted targets.
    for side, x, y in (('l', 15., 17.), ('r', -17., -13.)):
        target = (x, y, source['foot_'+side]['location'][2]-(.92/scale if side == 'r' else 0.))
        pm._chain(local, bones, 'thigh_'+side, 'calf_'+side, 'foot_'+side, target, (0., 1., .05))
        pm._world_rotation(local, bones, 'foot_'+side, source['foot_'+side]['rotation'])
    posed = pm._forward(local, bones)
    radius = proof['props'][POOL_MESHES[-1]]['summary']['size'][2]*.5
    ball = (4800., -3225., surface['z']+radius)
    pitch = 32.*(1.-aim)-6.*aim
    direction = (0., math.cos(math.radians(pitch)), math.sin(math.radians(pitch)))
    contact_tip = (ball[0], ball[1]-radius, ball[2])
    aiming_tip = pm._add(contact_tip, pm._mul(direction, draw))
    grip_idle = (SHOOTER_POSITION[0]-22., SHOOTER_POSITION[1]+5., 107.)
    idle_tip = pm._add(grip_idle, pm._mul(direction, 87.))
    tip = _mix(idle_tip, aiming_tip, aim)
    grip = pm._sub(tip, pm._mul(direction, 87.))
    bridge = pm._sub(contact_tip, pm._mul((0., math.cos(math.radians(-6)), math.sin(math.radians(-6))), 23.))
    def component(point):
        return ((point[0]-SHOOTER_POSITION[0])/scale, (point[1]-SHOOTER_POSITION[1])/scale,
                (point[2]-origin_z)/scale)
    # Right hand grips the cue below its wrist. Left hand spreads into a flat bridge.
    grip_tilt = _axis((1., 0., 0.), pitch+6.)
    right_rotation = pm._qmul(grip_tilt, _pose_basis((0., 0., 1.), (-1., 0., 0.)))
    right_target = component(pm._add(grip, pm._rotate(grip_tilt, (GRIP_HAND_X, 0., 8.))))
    pm._chain(local, bones, 'upperarm_r', 'lowerarm_r', 'hand_r', right_target, (-1., -.2, .25))
    pm._world_rotation(local, bones, 'hand_r', right_rotation)
    # Nyxar's left palm faces local -Y (the native fingers curl toward -Y).
    # Mapping local +Y upward puts the palm on the felt, not up toward the viewer.
    bridge_rotation = _pose_basis((0., 1., 0.), (0., 0., 1.))
    left_idle = posed['hand_l']['location']
    left_target = _mix(left_idle, component((bridge[0]+BRIDGE_HAND_X, bridge[1]+BRIDGE_HAND_Y, surface['z']+BRIDGE_HAND_Z)), aim)
    pm._chain(local, bones, 'upperarm_l', 'lowerarm_l', 'hand_l', left_target, (1., .1, .25))
    pm._world_rotation(local, bones, 'hand_l', _lerp_quat(source['hand_l']['rotation'], bridge_rotation, aim))
    for finger in ('index', 'middle'):
        for joint in (1, 2, 3):
            name = '%s_%02d_l' % (finger, joint)
            local[name]['rotation'] = _lerp_quat(local[name]['rotation'], _axis((0., 0., 1.), -5.), aim)
    # All four native rear fingers must participate. The listening animation's
    # untouched ring/pinky chains visibly hung open beside the first grip pass.
    # The shorter pinky needs a shallower first bend to clear the cue's envelope.
    for finger, angles in REAR_CURL.items():
        for joint, angle in enumerate(angles, 1):
            local['%s_%02d_r' % (finger, joint)]['rotation'] = _axis((0., 0., 1.), -angle)
    hand_world = pm._forward(local, bones)
    for side, target_local, pole_local in (
            ('l', (5.5, -1.3, -8.), (0., -1., -1.)),
            ('r', (-5.1, 3.8, 4.8), (-1., -1., 1.))):
        hand = hand_world['hand_'+side]
        target = pm._add(hand['location'], pm._rotate(hand['rotation'], target_local))
        original_thumb = hand_world['thumb_03_'+side]['location']
        amount = aim if side == 'l' else 1.
        pm._chain(local, bones, 'thumb_01_'+side, 'thumb_02_'+side, 'thumb_03_'+side,
                  _mix(original_thumb, target, amount), pm._rotate(hand['rotation'], pole_local))
        current = pm._forward(local, bones)['thumb_03_'+side]['rotation']
        axis = (1., 0., 0.) if side == 'l' else (-1., 0., 0.)
        tangent = (1., 0., 0.) if side == 'l' else (-1., -2., 0.)
        desired = pm._qmul(pm._between(pm._rotate(current, axis),
                                     pm._rotate(hand['rotation'], tangent)), current)
        pm._world_rotation(local, bones, 'thumb_03_'+side, _lerp_quat(current, desired, amount))
    # A bowed torso must not carry the gaze straight into the floor. Distribute
    # the extension over Nyxar's actual two neck joints and head, retaining a
    # slight downward sight line toward the cue rather than craning one joint.
    for name, extension in (('neck_01', 12.), ('neck_02', 10.), ('head', 8.)):
        current = pm._forward(local, bones)
        pm._world_rotation(local, bones, name,
                           pm._qmul(_axis((1., 0., 0.), extension*aim), current[name]['rotation']))
    world = pm._forward(local, bones)
    skinned = pm._skin(world, prepared)
    foot_min = {side: min(p[2]*scale+origin_z for n, p in skinned
                         if n in ('foot_'+side, 'ball_'+side, 'ankle_bck_'+side)) for side in ('l', 'r')}
    summary = {'time': t, 'aim_weight': aim, 'actor_origin_z': origin_z, 'feet_lowest_z': foot_min,
               'hand_r_target_error_cm': math.dist(world['hand_r']['location'], right_target)*scale,
               'hand_l_target_error_cm': math.dist(world['hand_l']['location'], left_target)*scale,
               'cue_tip_world': tip, 'cue_grip_world': grip, 'bridge_world': bridge,
               'cue_ball_center': ball, 'ball_radius_cm': radius}
    # Native left palm is -Y. A proximity-only check accepted the old palm-up
    # pose, so verify orientation as well as the actual skinned surface below.
    summary['bridge_palm_up_dot'] = pm._rotate(world['hand_l']['rotation'], (0., -1., 0.))[2]
    summary['rear_finger_to_wrist_cm'] = {
        finger: math.dist(world[finger+'_03_r']['location'], world['hand_r']['location'])*scale
        for finger in (*REAR_CURL, 'thumb')}
    shaft_radius = max(proof['props'][POOL_MESHES[2]]['summary']['size'][1:])*.5
    for side in ('l', 'r'):
        hand_points = [(p[0]*scale+SHOOTER_POSITION[0], p[1]*scale+SHOOTER_POSITION[1], p[2]*scale+origin_z)
                       for name, p in skinned if name.endswith('_'+side) and
                       name.startswith(('hand_', 'index_', 'middle_', 'thumb_', 'ring_', 'pinky_'))]
        distances = []
        for point in hand_points:
            delta = pm._sub(point, tip)
            along = pm._dot(delta, direction)
            if -156.288 <= along <= 0.:
                distances.append(math.dist(delta, pm._mul(direction, along)))
        summary['hand_'+side+'_shaft_clearance_cm'] = min(distances)-shaft_radius if distances else None
        summary['hand_'+side+'_lowest_z'] = min(p[2] for p in hand_points)
    # Evaluate separate skinned digits around the actual pitched shaft. A single
    # nearby vertex cannot establish a closed, opposing grip.
    radial_up = (0., -direction[2], direction[1])
    digit_contacts = {}
    for finger in (*REAR_CURL, 'thumb'):
        rows = []
        for name, point in skinned:
            if not (name.startswith(finger+'_') and name.endswith('_r')):
                continue
            point = (point[0]*scale+SHOOTER_POSITION[0], point[1]*scale+SHOOTER_POSITION[1],
                     point[2]*scale+origin_z)
            delta = pm._sub(point, tip)
            along = pm._dot(delta, direction)
            if -156.288 <= along <= 0.:
                rows.append((math.dist(delta, pm._mul(direction, along))-shaft_radius,
                             math.degrees(math.atan2(pm._dot(delta, radial_up), delta[0]))))
        clearance, angle = min(rows)
        digit_contacts[finger] = {'clearance_cm': clearance, 'angle_degrees': angle}
    angles = sorted(row['angle_degrees'] % 360. for row in digit_contacts.values())
    gaps = [b-a for a, b in zip(angles, angles[1:]+[angles[0]+360.])]
    summary['rear_digit_contacts'] = digit_contacts
    summary['rear_contact_arc_degrees'] = 360.-max(gaps)
    cue = {'time': t, 'location': list(tip), 'rotation': [pitch, 90., 0.], 'scale': [1., 1., 1.]}
    return local, world, skinned, cue, summary


def fit(root, output=None):
    """Offline fit with the captured native bones/vertices; creates no Unreal assets."""
    root = Path(root)
    proof, skin = _load_proof(root)
    surface = _surface(proof)
    # Only contact-relevant vertices need skinning at every sampled frame.
    full = pose_math._skin_setup(skin['nyxar'])
    prepared = [(name, weights) for name, weights in full
                if name.startswith(('foot_', 'ball_', 'ankle_', 'hand_', 'index_', 'middle_', 'thumb_')) or
                (name.endswith('_r') and name.startswith(('ring_', 'pinky_')))]
    tracks, cues, contacts, origin_z = {}, [], [], None
    for frame in range(int(DURATION*RATE)+1):
        local, world, skinned, cue, summary = _fit_frame(proof, skin, surface, frame/RATE, prepared, origin_z)
        origin_z = summary['actor_origin_z']
        for name, transform in local.items():
            keys = tracks.setdefault(name, [])
            if keys and pose_math._dot(keys[-1]['rotation'], transform['rotation']) < 0:
                transform['rotation'] = pose_math._mul(transform['rotation'], -1.)
            keys.append(transform)
        cues.append(cue)
        contacts.append(summary)
        if (any(not 0. <= z <= 1.2 for z in summary['feet_lowest_z'].values()) or
                summary['hand_r_target_error_cm'] > .01 or summary['hand_l_target_error_cm'] > .01):
            raise RuntimeError('Measured pool stance/contact failed: ' + json.dumps(summary))
        if not 0. <= summary['hand_r_shaft_clearance_cm'] <= .75:
            raise RuntimeError('Pool grip is disconnected or clips the cue: ' + json.dumps(summary))
        digit_clearances = [row['clearance_cm'] for row in summary['rear_digit_contacts'].values()]
        if (any(not 0. <= clearance <= 1.25 for clearance in digit_clearances) or
                sum(clearance <= .75 for clearance in digit_clearances) < 4 or
                summary['rear_contact_arc_degrees'] < 180.):
            raise RuntimeError('Pool rear digits do not enclose the cue: ' + json.dumps(summary))
        if summary['aim_weight'] >= .999:
            if (not 0. <= summary['hand_l_shaft_clearance_cm'] <= .75 or
                    not 0. <= summary['hand_l_lowest_z']-surface['z'] <= 1.2 or
                    summary['bridge_palm_up_dot'] > -.95):
                raise RuntimeError('Pool bridge contact failed: ' + json.dumps(summary))
    for name, keys in tracks.items():
        if math.dist(keys[0]['location'], keys[-1]['location']) > .001 or abs(
                pose_math._dot(keys[0]['rotation'], keys[-1]['rotation'])) < .999999:
            raise RuntimeError('Pool animation has an open loop seam: ' + name)
    result = {'success': True, 'duration': DURATION, 'rate': RATE, 'surface': surface,
              'shooter': {'location': [SHOOTER_POSITION[0], SHOOTER_POSITION[1], origin_z],
                          'rotation': [0., 0., 0.], 'scale': [proof['fit_scale']]*3},
              'table': {'location': list(TABLE_POSITION), 'rotation': [0., 90., 0.], 'scale': [1., 1., 1.]},
              'cue_samples': cues, 'contact_time': CONTACT_TIME,
              'contacts': contacts, 'tracks': tracks}
    if output:
        Path(output).write_text(json.dumps(result, separators=(',', ':')), encoding='utf-8')
    return result


def create(ctx):
    """Create one unsaved private clip after offline contacts pass; lead saves it."""
    import unreal as u
    root = Path(u.Paths.project_dir()).resolve()
    proof, skin = _load_proof(root)
    before = {path: _sha(root, path) for path in proof['source_sha256']}
    if before != proof['source_sha256']:
        raise RuntimeError('Pool source changed after the native standing/table probe')
    if u.EditorAssetLibrary.does_asset_exist(PRIVATE_CLIP):
        raise RuntimeError('Preserve existing private pool clip; inspect before replacement')
    result = fit(root)
    mesh = ctx.asset(MESH)
    factory = u.AnimSequenceFactory()
    factory.target_skeleton = mesh.skeleton
    factory.preview_skeletal_mesh = mesh
    folder, name = PRIVATE_CLIP.rsplit('/', 1)
    clip = u.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, u.AnimSequence, factory)
    if not clip:
        raise RuntimeError('Private pool animation creation failed')
    controller = clip.get_editor_property('controller')
    controller.open_bracket('Measured pool stance, bridge and cue stroke', False)
    try:
        controller.set_frame_rate(u.FrameRate(RATE, 1), False)
        controller.set_number_of_frames(u.FrameNumber(int(DURATION*RATE)), False)
        for bone, keys in result['tracks'].items():
            controller.add_bone_curve(bone, False)
            if not controller.set_bone_track_keys(bone,
                    [u.Vector(*key['location']) for key in keys], [u.Quat(*key['rotation']) for key in keys],
                    [u.Vector(*key['scale']) for key in keys], False):
                raise RuntimeError('Private pool bone track write failed: ' + bone)
    finally:
        controller.close_bracket(False)
    api = u.AnimPoseExtensions
    options = u.AnimPoseEvaluationOptions(optional_skeletal_mesh=mesh, evaluation_type=u.AnimDataEvalType.RAW)
    checked = [0, 75, 105, 204, 210, 215, 285, 420]
    max_error = 0.
    for frame in checked:
        pose = api.get_anim_pose_at_time(clip, frame/RATE, options)
        local = {bone: keys[frame] for bone, keys in result['tracks'].items()}
        expected = pose_math._forward(local, skin['nyxar']['bones'])
        for bone, transform in expected.items():
            actual = api.get_bone_pose(pose, bone, u.AnimPoseSpaces.WORLD)
            max_error = max(max_error, math.dist(actual.translation.to_tuple(), transform['location']))
            if abs(pose_math._dot(actual.rotation.to_tuple(), transform['rotation'])) < .99999:
                raise RuntimeError('Private pool native rotation readback failed: ' + bone)
    if max_error > .015 or abs(float(clip.sequence_length)-DURATION) > .0001:
        raise RuntimeError('Private pool native pose/duration readback differs')
    if any(_sha(root, path) != digest for path, digest in before.items()):
        raise RuntimeError('Private pool author changed a source asset')
    report = {key: value for key, value in result.items() if key != 'tracks'}
    report.update({'private_clip': PRIVATE_CLIP, 'actor_location': result['shooter']['location'],
                   'actor_rotation': result['shooter']['rotation'], 'mesh_scale': result['shooter']['scale'],
                   'ball_center': result['contacts'][210]['cue_ball_center'],
                   'ball_radius_cm': result['contacts'][210]['ball_radius_cm'],
                   'native_readback_frames': checked, 'native_readback_max_cm': max_error,
                   'source_originals_preserved': True, 'dirty_assets': [PRIVATE_CLIP]})
    return clip, report


def _sha(root, asset):
    package = asset.split('.')[0]
    if not package.startswith('/Game/'):
        raise RuntimeError('Pool source must belong to the project content: ' + package)
    return hashlib.sha256((root / ('Content/' + package[6:] + '.uasset')).read_bytes()).hexdigest()


def _shape_summary(data):
    points = data['vertices']
    low = [min(p[axis] for p in points) for axis in range(3)]
    high = [max(p[axis] for p in points) for axis in range(3)]
    return {'min': low, 'max': high, 'size': [b-a for a, b in zip(low, high)],
            'vertex_count': len(points), 'triangle_count': len(data['triangles'])}


def _upper_surface(data, depth=35.):
    """Keep the table's upper 35 cm, including cloth and cushion bevels."""
    points = data['vertices']
    cutoff = max(p[2] for p in points) - depth
    faces = [tri for tri in data['triangles'] if min(points[i][2] for i in tri) >= cutoff]
    used = sorted({i for tri in faces for i in tri})
    remap = {old: new for new, old in enumerate(used)}
    if not faces:
        raise RuntimeError('No table upper surface in native geometry')
    return {'vertices': [points[i] for i in used],
            'triangles': [[remap[i] for i in tri] for tri in faces],
            'surface_filter': {'native_min_z': cutoff, 'depth_from_native_top_cm': depth}}


def probe(ctx, output=None):
    """Export native standing pose and prop geometry without scene/asset writes.

    Run in the lead's Entry-world probe wrapper. The separate skin receipt is
    reused only after verifying its original mesh hash and bone-pose agreement.
    Returned JSON stores native component centimetres and XYZW quaternions.
    """
    import unreal as u
    root = Path(u.Paths.project_dir()).resolve()
    output = Path(output) if output else root / '.agent/local/StationRefinement/OrbitPoolProbe1.json'
    if output.exists():
        raise RuntimeError('Preserve existing pool probe evidence: ' + str(output))
    skin_path = root / SKIN_RECEIPT
    skin = json.loads(skin_path.read_text(encoding='utf-8'))
    if (not skin['success'] or not all(skin['originals_preserved'].values()) or
            _sha(root, MESH) != skin['source_sha256'][MESH]):
        raise RuntimeError('Pool fit requires the verified unchanged Nyxar skin receipt')
    assets = {path: ctx.asset(path) for path in (MESH, SOURCE_CLIP, *POOL_MESHES)}
    before = {path: _sha(root, path) for path in assets}
    report = {'success': False, 'source_sha256': before,
              'skin_receipt': SKIN_RECEIPT,
              'skin_receipt_sha256': hashlib.sha256(skin_path.read_bytes()).hexdigest(),
              'fit_scale': skin['fit_scale'],
              'evidence': 'Read-only raw standing bones and native pool triangles; no animation/contact acceptance',
              'scene_mutations': False, 'props': {}}
    try:
        for path in POOL_MESHES:
            mesh = assets[path]
            _, data = pose_math._geometry(mesh, False, u)
            summary = _shape_summary(data)
            compact = _upper_surface(data) if path == POOL_MESHES[0] else {}
            compact['summary'] = summary
            compact['materials'] = [slot.material_interface.get_path_name() if slot.material_interface else None
                                    for slot in mesh.get_editor_property('static_materials')]
            report['props'][path] = compact
        mesh, clip = assets[MESH], assets[SOURCE_CLIP]
        if clip.get_editor_property('skeleton') != mesh.skeleton:
            raise RuntimeError('Standing pool source is incompatible with Nyxar')
        model = clip.get_editor_property('data_model_interface')
        rate = model.get_frame_rate()
        report['animation'] = {
            'clip': clip.get_path_name(), 'skeleton': mesh.skeleton.get_path_name(),
            'key_count': model.get_number_of_keys(), 'frame_rate': [rate.numerator, rate.denominator],
            'length_seconds': float(clip.sequence_length), 'samples': []}
        api = u.AnimPoseExtensions
        options = u.AnimPoseEvaluationOptions(optional_skeletal_mesh=mesh, evaluation_type=u.AnimDataEvalType.RAW)
        expected = {b['name'] for b in skin['nyxar']['bones']}
        for step in range(9):
            seconds = float(clip.sequence_length) * step / 8.
            pose = api.get_anim_pose_at_time(clip, seconds, options)
            if not expected <= set(map(str, api.get_bone_names(pose))):
                raise RuntimeError('Standing source bone set differs from the verified skin')
            sample = {'seconds': seconds, 'bones': {
                name: {'world': pose_math._transform(api.get_bone_pose(pose, name, u.AnimPoseSpaces.WORLD)),
                       'local': pose_math._transform(api.get_bone_pose(pose, name, u.AnimPoseSpaces.LOCAL))}
                for name in sorted(expected)}}
            local = {name: value['local'] for name, value in sample['bones'].items()}
            rebuilt = pose_math._forward(local, skin['nyxar']['bones'])
            error = max(sum((a-b)**2 for a, b in zip(rebuilt[name]['location'], value['world']['location']))**.5
                        for name, value in sample['bones'].items())
            if error > .005:
                raise RuntimeError('Standing native/offline transform disagreement: %.6f cm' % error)
            sample['native_reconstruction_max_cm'] = error
            report['animation']['samples'].append(sample)
        report['success'] = True
    finally:
        report['originals_preserved'] = {path: _sha(root, path) == value for path, value in before.items()}
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, separators=(',', ':')), encoding='utf-8')
        if not all(report['originals_preserved'].values()):
            raise RuntimeError('Read-only pool probe unexpectedly changed a source asset')
    return {'success': report['success'], 'output': str(output), 'source_sha256': before,
            'raw_pose_samples': len(report['animation']['samples']),
            'props': {path: data['summary'] for path, data in report['props'].items()},
            'dirty_assets': []}
