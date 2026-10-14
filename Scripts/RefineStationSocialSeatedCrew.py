"""Measured private lounge pose and two reused social conversation actors.

The lead owns serialized native execution and all asset/map saves. probe(ctx)
only exports owned source geometry and raw animation data for fitting; it does
not spawn actors or mutate any mesh, animation or level.
"""
import hashlib
import json
import math
import copy
from pathlib import Path


SOFA = '/Game/CyberpunkRestaurant/Meshes/SM_Sofa_01'
TABLE = '/Game/CyberpunkRestaurant/Meshes/SM_Table_01'
MESH = '/Game/Nyxar/Meshes/SKM_Nyxar'
SOURCE_CLIP = '/Game/OutpostSandbox/StationRefinement/OperationsCrew/A_Nyxar_SeatedOperations'
PRIVATE_CLIP = '/Game/OutpostSandbox/StationRefinement/SocialCrew/A_Nyxar_SeatedLounge'
MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
MAP_SHA = 'c176006ae0e09327c24234c9a046577d3386308634bf06ab6d182469072cc542'
PROBE_SHA = '17e5fdff6680aaf3127e14083b105eb02ae708dcfb88269a5399184745d4f898'
CHANGED_BONES = tuple(part+'_'+side for side in ('l', 'r')
                      for part in ('thigh', 'calf', 'foot', 'upperarm', 'lowerarm', 'hand'))
TAG = 'StationSocialSeated20261006'


def _sha(root, asset):
    package = asset.split('.')[0]
    return hashlib.sha256((root / ('Content/' + package[6:] + '.uasset')).read_bytes()).hexdigest()


def _transform(t):
    return {'location': list(t.translation.to_tuple()), 'rotation': list(t.rotation.to_tuple()),
            'scale': list(t.scale3d.to_tuple())}


def _one(actors, label):
    rows = [a for a in actors if a.get_actor_label() == label]
    if len(rows) != 1:
        raise RuntimeError('Expected one existing social actor: ' + label)
    return rows[0]


def _geometry(mesh, skeletal, u):
    dynamic = u.DynamicMesh()
    args = (mesh, dynamic, u.GeometryScriptCopyMeshFromAssetOptions(apply_build_settings=False),
            u.GeometryScriptMeshReadLOD(lod_type=u.GeometryScriptLODType.SOURCE_MODEL, lod_index=0))
    copy = (u.GeometryScript_AssetUtils.copy_mesh_from_skeletal_mesh if skeletal else
            u.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2)
    _, outcome = copy(*args)
    if outcome != u.GeometryScriptOutcomePins.SUCCESS:
        raise RuntimeError('Cannot inspect native geometry: ' + mesh.get_path_name())
    _, vertices, gaps = u.GeometryScript_MeshQueries.get_all_vertex_positions(dynamic, False)
    _, triangles, triangle_gaps = u.GeometryScript_MeshQueries.get_all_triangle_indices(dynamic, False)
    if gaps or triangle_gaps:
        raise RuntimeError('Unexpected sparse native source mesh IDs')
    points = u.GeometryScript_List.convert_vector_list_to_array(vertices)
    faces = u.GeometryScript_List.convert_triangle_list_to_array(triangles)
    return dynamic, {'vertices': [list(p.to_tuple()) for p in points],
                     'triangles': [[int(t.x), int(t.y), int(t.z)] for t in faces]}


def probe(ctx, output=None):
    """Read-only, no scene changes; output belongs to the lead's ignored receipts."""
    import unreal as u
    root = Path(u.Paths.project_dir()).resolve()
    output = Path(output) if output else root / '.agent/local/StationRefinement/SocialSeatedProbe.json'
    actors = list(ctx.actors)
    assets = {name: ctx.asset(name) for name in (SOFA, TABLE, MESH, SOURCE_CLIP)}
    hashes = {name: _sha(root, name) for name in assets}
    report = {'success': False, 'source_sha256': hashes,
              'evidence': 'Native source triangles, raw compatible pose and skin weights; not a seated visual/contact acceptance'}
    try:
        report['furniture'] = {}
        for name in (SOFA, TABLE):
            _, data = _geometry(assets[name], False, u)
            report['furniture'][name] = data
        report['actors'] = []
        labels = ['Refine/Social/Conversation %d/%s' % (index, part)
                  for index in (1, 2) for part in ('Sofa south', 'Sofa north', 'Low table')]
        labels += ['Crew/Lounge conversation A', 'Crew/Lounge conversation B']
        for label in labels:
            actor = _one(actors, label)
            row = {'label': label, 'transform': _transform(actor.get_actor_transform()), 'meshes': []}
            for component in actor.get_components_by_class(u.MeshComponent):
                mesh = (component.get_skeletal_mesh_asset() if isinstance(component, u.SkeletalMeshComponent)
                        else component.static_mesh if isinstance(component, u.StaticMeshComponent) else None)
                row['meshes'].append({'component': component.get_name(), 'asset': mesh.get_path_name() if mesh else None,
                    'world_transform': _transform(component.get_world_transform()),
                    'relative_transform': _transform(component.get_relative_transform()),
                    'materials': [m.get_path_name() if m else None for m in component.get_materials()]})
            report['actors'].append(row)
        mesh, clip = assets[MESH], assets[SOURCE_CLIP]
        if clip.get_editor_property('skeleton') != mesh.skeleton:
            raise RuntimeError('Inspected seated source is not compatible with Nyxar')
        dynamic, data = _geometry(mesh, True, u)
        _, bones = u.GeometryScript_BoneWeights.get_all_bones_info(dynamic)
        data['bones'] = [{'index': b.index, 'parent': b.parent_index, 'name': str(b.name),
                          'reference_world': _transform(b.world_transform)} for b in bones]
        data['weights'] = []
        for index in range(len(data['vertices'])):
            _, weights, valid = u.GeometryScript_BoneWeights.get_vertex_bone_weights(dynamic, index)
            total = sum(w.weight for w in weights)
            if not valid or abs(total - 1.) > .002:
                raise RuntimeError('Missing/non-normalized source skin weights: ' + str(index))
            data['weights'].append([[w.bone_index, float(w.weight / total)] for w in weights])
        report['nyxar'] = data
        report['fit_scale'] = 190. / (mesh.get_bounds().box_extent.z * 2.)
        model = clip.get_editor_property('data_model_interface')
        count, rate = model.get_number_of_keys(), model.get_frame_rate()
        report['animation'] = {'clip': clip.get_path_name(), 'key_count': count,
            'frame_rate': [rate.numerator, rate.denominator], 'length_seconds': float(clip.sequence_length), 'samples': []}
        api = u.AnimPoseExtensions
        options = u.AnimPoseEvaluationOptions(optional_skeletal_mesh=mesh, evaluation_type=u.AnimDataEvalType.RAW)
        for fraction in (0., .25, .5, .75, 1.):
            seconds = float(clip.sequence_length) * fraction
            pose = api.get_anim_pose_at_time(clip, seconds, options)
            names = set(map(str, api.get_bone_names(pose)))
            if not {str(b.name) for b in bones} <= names:
                raise RuntimeError('Mesh source bone names differ from evaluated seated pose')
            report['animation']['samples'].append({'seconds': seconds, 'bones': {
                str(b.name): {'world': _transform(api.get_bone_pose(pose, b.name, u.AnimPoseSpaces.WORLD)),
                              'local': _transform(api.get_bone_pose(pose, b.name, u.AnimPoseSpaces.LOCAL))}
                for b in bones}})
        report['success'] = True
    finally:
        report['originals_preserved'] = {name: _sha(root, name) == value for name, value in hashes.items()}
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, separators=(',', ':')), encoding='utf-8')
        if not all(report['originals_preserved'].values()):
            raise RuntimeError('Read-only source geometry probe changed an asset')
    return {'success': report['success'], 'output': str(output), 'source_sha256': hashes,
            'sofa_triangles': len(report['furniture'][SOFA]['triangles']),
            'nyxar_vertices': len(report['nyxar']['vertices']), 'raw_pose_samples': 5}


def _add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _mul(a, scale):
    return tuple(x * scale for x in a)


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _unit(a):
    length = math.sqrt(_dot(a, a))
    if length < .00001:
        raise RuntimeError('Degenerate measured pose vector')
    return _mul(a, 1. / length)


def _qmul(a, b):
    x, y, z, w = a
    X, Y, Z, W = b
    return (w*X+x*W+y*Z-z*Y, w*Y-x*Z+y*W+z*X, w*Z+x*Y-y*X+z*W, w*W-x*X-y*Y-z*Z)


def _inverse(q):
    return (-q[0], -q[1], -q[2], q[3])


def _rotate(q, point):
    return _qmul(_qmul(q, (*point, 0.)), _inverse(q))[:3]


def _between(a, b):
    a, b = _unit(a), _unit(b)
    cross = (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
    return _unit((*cross, 1. + _dot(a, b)))


def _forward(local, bones):
    world = {}
    names = {b['index']: b['name'] for b in bones}
    for bone in bones:
        name = bone['name']
        t = local[name]
        if not all(abs(x - 1.) < .0001 for x in t['scale']):
            raise RuntimeError('Measured lounge solver requires the inspected unit-scale bone rig')
        if bone['parent'] < 0:
            world[name] = copy.deepcopy(t)
        else:
            parent = world[names[bone['parent']]]
            world[name] = {'location': _add(parent['location'], _rotate(parent['rotation'], t['location'])),
                           'rotation': _unit(_qmul(parent['rotation'], t['rotation'])), 'scale': [1., 1., 1.]}
    return world


def _world_rotation(local, bones, name, rotation):
    world = _forward(local, bones)
    bone = next(b for b in bones if b['name'] == name)
    parent = next((b['name'] for b in bones if b['index'] == bone['parent']), None)
    local[name]['rotation'] = _unit(_qmul(_inverse(world[parent]['rotation']), rotation)) if parent else rotation


def _chain(local, bones, root, joint, tip, target, pole):
    """Exact two-link rotation-only solve: all bone translations/scales survive."""
    world = _forward(local, bones)
    a, b, c = [world[n]['location'] for n in (root, joint, tip)]
    first, second, distance = math.dist(a, b), math.dist(b, c), math.dist(a, target)
    if not abs(first-second)+.1 < distance < first+second-.1:
        raise RuntimeError('Lounge contact target exceeds the measured limb reach')
    axis = _unit(_sub(target, a))
    perpendicular = _unit(_sub(pole, _mul(axis, _dot(pole, axis))))
    along = (first*first-second*second+distance*distance)/(2.*distance)
    height = math.sqrt(max(0., first*first-along*along))
    elbow = _add(a, _add(_mul(axis, along), _mul(perpendicular, height)))
    _world_rotation(local, bones, root, _qmul(_between(_sub(b, a), _sub(elbow, a)), world[root]['rotation']))
    world = _forward(local, bones)
    b, c = world[joint]['location'], world[tip]['location']
    _world_rotation(local, bones, joint, _qmul(_between(_sub(c, b), _sub(target, b)), world[joint]['rotation']))
    actual = _forward(local, bones)[tip]['location']
    if math.dist(actual, target) > .002:
        raise RuntimeError('Measured two-link pose did not reach its contact target')


def _skin_setup(data):
    bones = {b['index']: b for b in data['bones']}
    result = []
    for point, weights in zip(data['vertices'], data['weights']):
        dominant = bones[max(weights, key=lambda w: w[1])[0]]['name']
        values = []
        for index, weight in weights:
            bone = bones[index]
            reference = bone['reference_world']
            position = _rotate(_inverse(reference['rotation']), _sub(point, reference['location']))
            position = tuple(position[i]/reference['scale'][i] for i in range(3))
            values.append((bone['name'], weight, position))
        result.append((dominant, values))
    return result


def _skin(world, prepared):
    result = []
    for name, weights in prepared:
        point = (0., 0., 0.)
        for bone, weight, local in weights:
            t = world[bone]
            point = _add(point, _mul(_add(t['location'], _rotate(t['rotation'], local)), weight))
        result.append((name, point))
    return result


def _seat_height(data, x, y):
    """Highest native triangle intersection under the selected seat contact."""
    hits = []
    for tri in data['triangles']:
        a, b, c = [data['vertices'][i] for i in tri]
        denominator = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(denominator) < .000001:
            continue
        p = ((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/denominator
        q = ((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/denominator
        if min(p, q, 1.-p-q) >= -.000001:
            hits.append(p*a[2]+q*b[2]+(1.-p-q)*c[2])
    if not hits:
        raise RuntimeError('No actual sofa surface under seated contact')
    return max(hits)


def _lap_clearance(skin, triangles):
    """Vertical hand-vertex clearance over actual posed thigh triangles."""
    grid = {}
    for indices in triangles:
        if not all(skin[i][0].startswith('thigh_') for i in indices):
            continue
        points = [skin[i][1] for i in indices]
        for x in range(math.floor(min(p[0] for p in points)/8), math.floor(max(p[0] for p in points)/8)+1):
            for y in range(math.floor(min(p[1] for p in points)/8), math.floor(max(p[1] for p in points)/8)+1):
                grid.setdefault((x, y), []).append(points)
    gaps = []
    for name, (x, y, z) in skin:
        if not name.startswith(('hand_', 'thumb_', 'index_', 'middle_', 'ring_', 'pinky_')):
            continue
        for a, b, c in grid.get((math.floor(x/8), math.floor(y/8)), []):
            denominator = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(denominator) < .000001:
                continue
            p = ((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/denominator
            q = ((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/denominator
            if min(p, q, 1-p-q) >= -.000001:
                gaps.append(z-p*a[2]-q*b[2]-(1-p-q)*c[2])
    if len(gaps) < 50:
        raise RuntimeError('Relaxed hands do not overlap the actual lap surface')
    return min(gaps)


def fit_sample(proof, sample, prepared=None, fixed_origin_z=None):
    """Offline/native shared deterministic fit; no UObjects or writes."""
    bones, scale = proof['nyxar']['bones'], proof['fit_scale']
    prepared = prepared or _skin_setup(proof['nyxar'])
    local = {name: copy.deepcopy(t['local']) for name, t in sample['bones'].items()}
    source = _forward(local, bones)
    if max(math.dist(source[n]['location'], t['world']['location']) for n, t in sample['bones'].items()) > .005:
        raise RuntimeError('Offline/native raw pose transform conventions differ')
    # The original pelvis skin is the actual seated contact, not its joint pivot.
    # Selected centre is 91cm along the native sofa and 30cm from its front.
    seat = _seat_height(proof['furniture'][SOFA], 91., -30.)
    source_skin = _skin(source, prepared)
    pelvis_skin = [p for name, p in source_skin if name == 'pelvis']
    origin_z = (seat + .5 - min(p[2] for p in pelvis_skin)*scale
                if fixed_origin_z is None else fixed_origin_z)
    targets = {}
    for side, sign in (('l', 1.), ('r', -1.)):
        root, knee, foot = 'thigh_'+side, 'calf_'+side, 'foot_'+side
        current = source[foot]['location']
        foot_points = [p for name, p in source_skin
                       if name in ('foot_'+side, 'ball_'+side, 'ankle_bck_'+side)]
        lift = (.6-origin_z)/scale - min(p[2] for p in foot_points)
        target = (current[0], current[1], current[2]+lift)
        _chain(local, bones, root, knee, foot, target, (0., 1., .15))
        _world_rotation(local, bones, foot, source[foot]['rotation'])
        # Arms stay near the torso with both hands above the thighs rather than
        # spread at the pilot controls. Slight asymmetry avoids a mirrored statue.
        pelvis = source['pelvis']['location']
        hand_target = (sign*15., pelvis[1]+20.+(1.5 if side == 'r' else 0.), pelvis[2]+14.)
        _chain(local, bones, 'upperarm_'+side, 'lowerarm_'+side, 'hand_'+side,
               hand_target, (sign, -.2, -.25))
        fingers = _sub(source['middle_03_'+side]['location'], source['hand_'+side]['location'])
        hand_rotation = _qmul(_between(fingers, (fingers[0], fingers[1], 0.)), source['hand_'+side]['rotation'])
        _world_rotation(local, bones, 'hand_'+side, hand_rotation)
        targets[side] = {'foot': target, 'hand': hand_target}
    world = _forward(local, bones)
    skin = _skin(world, prepared)
    summary = {'seat_native_xy': [91., -30.], 'seat_surface_z': seat, 'actor_origin_z': origin_z,
               'pelvis_world_z': origin_z+world['pelvis']['location'][2]*scale, 'targets_component_cm': targets}
    for side in ('l', 'r'):
        points = [p for name, p in skin if name in ('foot_'+side, 'ball_'+side, 'ankle_bck_'+side)]
        summary['foot_'+side+'_lowest_z'] = min(p[2] for p in points)*scale+origin_z
    summary['body_lowest_z'] = min(p[2] for _, p in skin)*scale+origin_z
    summary['pelvis_skin_lowest_z'] = min(p[2] for name, p in skin if name == 'pelvis')*scale+origin_z
    summary['hand_over_thigh_min_cm'] = _lap_clearance(skin, proof['nyxar']['triangles'])*scale
    return local, world, skin, summary


def _checked_contacts(summary):
    if (not -.05 <= summary['body_lowest_z'] <= 1.2 or
            not all(0. <= summary['foot_'+side+'_lowest_z'] <= 1.2 for side in ('l', 'r')) or
            not 0. <= summary['pelvis_skin_lowest_z']-summary['seat_surface_z'] <= 2. or
            not .2 <= summary['hand_over_thigh_min_cm'] <= 2.):
        raise RuntimeError('Measured lounge contact failed: ' + json.dumps(summary))


def _guard_transform(actual, expected):
    if (max(abs(a-b) for a, b in zip(actual['location'], expected['location'])) > .05 or
            max(abs(a-b) for a, b in zip(actual['scale'], expected['scale'])) > .0001 or
            min(max(abs(a-b) for a, b in zip(actual['rotation'], expected['rotation'])),
                max(abs(a+b) for a, b in zip(actual['rotation'], expected['rotation']))) > .0001):
        raise RuntimeError('Measured sofa or conversation actor moved since the native probe')


def _author_clip(ctx, proof, u):
    if u.EditorAssetLibrary.does_asset_exist(PRIVATE_CLIP):
        raise RuntimeError('Preserve existing private lounge animation; inspect before any replacement')
    source, mesh = ctx.asset(SOURCE_CLIP), ctx.asset(MESH)
    model = source.get_editor_property('data_model_interface')
    count, duration = model.get_number_of_keys(), float(source.sequence_length)
    if count != 121 or abs(duration-4.) > .0001:
        raise RuntimeError('Verified seated source cadence changed')
    prepared = _skin_setup(proof['nyxar'])
    api = u.AnimPoseExtensions
    options = u.AnimPoseEvaluationOptions(optional_skeletal_mesh=mesh, evaluation_type=u.AnimDataEvalType.RAW)
    tracks = {name: [] for name in CHANGED_BONES}
    evidence, readback, origin_z, bounds = [], {}, None, [[1e9]*3, [-1e9]*3]
    for frame in range(count):
        seconds = duration*frame/(count-1)
        pose = api.get_anim_pose_at_time(source, seconds, options)
        sample = {'bones': {b['name']: {
            'local': _transform(api.get_bone_pose(pose, b['name'], u.AnimPoseSpaces.LOCAL)),
            'world': _transform(api.get_bone_pose(pose, b['name'], u.AnimPoseSpaces.WORLD))}
            for b in proof['nyxar']['bones']}}
        local, world, skin, summary = fit_sample(proof, sample, prepared, origin_z)
        origin_z = summary['actor_origin_z']
        _checked_contacts(summary)
        for name in CHANGED_BONES:
            if (local[name]['location'] != sample['bones'][name]['local']['location'] or
                    local[name]['scale'] != sample['bones'][name]['local']['scale']):
                raise RuntimeError('Lounge solver changed limb length or bone scale')
            if tracks[name] and _dot(tracks[name][-1]['rotation'], local[name]['rotation']) < 0:
                local[name]['rotation'] = _mul(local[name]['rotation'], -1)
            tracks[name].append(local[name])
        for _, point in skin:
            for axis in range(3):
                value = point[axis]*proof['fit_scale']+(origin_z if axis == 2 else 0.)
                bounds[0][axis] = min(bounds[0][axis], value)
                bounds[1][axis] = max(bounds[1][axis], value)
        evidence.append({'frame': frame, **summary})
        if frame % 30 == 0:
            readback[frame] = {'local': local, 'world': world}
            u.log('SOCIAL_SEATED_FIT frame=%d foot=%.3f/%.3f hip=%.3f lap=%.3f' %
                  (frame, summary['foot_l_lowest_z'], summary['foot_r_lowest_z'],
                   summary['pelvis_skin_lowest_z'], summary['hand_over_thigh_min_cm']))
    for name in CHANGED_BONES:
        if abs(_dot(tracks[name][0]['rotation'], tracks[name][-1]['rotation'])) < .99999:
            raise RuntimeError('Private lounge pose would break the original closed loop')
    # All measurements pass before creating any persistent private asset.
    clip = u.EditorAssetLibrary.duplicate_asset(SOURCE_CLIP, PRIVATE_CLIP)
    if not clip or clip.get_editor_property('skeleton') != mesh.skeleton:
        raise RuntimeError('Could not create the separate compatible lounge animation')
    controller = clip.get_editor_property('controller')
    controller.open_bracket('Measured social seated lap and floor contacts', False)
    try:
        for name, keys in tracks.items():
            if not controller.set_bone_track_keys(name,
                    [u.Vector(*t['location']) for t in keys], [u.Quat(*t['rotation']) for t in keys],
                    [u.Vector(*t['scale']) for t in keys], False):
                raise RuntimeError('Private lounge bone track write failed: ' + name)
    finally:
        controller.close_bracket(False)
    for frame, expected in readback.items():
        pose = api.get_anim_pose_at_time(clip, duration*frame/(count-1), options)
        for name in expected['local']:
            actual = api.get_bone_pose(pose, name, u.AnimPoseSpaces.WORLD)
            if math.dist(actual.translation.to_tuple(), expected['world'][name]['location']) > .015:
                raise RuntimeError('Native lounge pose readback differs: ' + name)
            local = api.get_bone_pose(pose, name, u.AnimPoseSpaces.LOCAL)
            if abs(_dot(local.rotation.to_tuple(), expected['local'][name]['rotation'])) < .99999:
                raise RuntimeError('Native lounge local rotation readback differs: ' + name)
    return clip, {'source': SOURCE_CLIP, 'private': PRIVATE_CLIP, 'keys': count, 'duration_seconds': duration,
                  'changed_rotation_tracks': list(CHANGED_BONES), 'bone_translations_and_scales_preserved': True,
                  'native_readback_frames': list(readback), 'fixed_actor_origin_z': origin_z,
                  'posed_scaled_bounds': bounds, 'per_frame_contacts': evidence}


def apply(ctx):
    """One guarded author pass. The lead saves returned dirty_assets and the map."""
    import unreal as u
    from StationRefinementSupport import transform_record
    root = Path(u.Paths.project_dir()).resolve()
    path = root / '.agent/local/StationRefinement/SocialSeatedProbe.json'
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    map_file = root / ('Content/'+MAP[6:]+'.umap')
    if world.get_path_name().split('.')[0] != MAP or hashlib.sha256(map_file.read_bytes()).hexdigest() != MAP_SHA:
        raise RuntimeError('Seated lounge requires the reviewed CargoConnection1 candidate')
    if hashlib.sha256(path.read_bytes()).hexdigest() != PROBE_SHA:
        raise RuntimeError('Measured sofa/crew source receipt changed')
    proof = json.loads(path.read_text(encoding='utf-8'))
    if not proof['success'] or not all(proof['originals_preserved'].values()):
        raise RuntimeError('Source contact probe was not successful')
    for asset, digest in proof['source_sha256'].items():
        if _sha(root, asset) != digest:
            raise RuntimeError('Inspected source changed: ' + asset)
    actors = list(ctx.actors)
    for row in proof['actors']:
        actor = _one(actors, row['label'])
        _guard_transform(_transform(actor.get_actor_transform()), row['transform'])
    crew = [_one(actors, 'Crew/Lounge conversation '+letter) for letter in ('A', 'B')]
    sofas = [_one(actors, 'Refine/Social/Conversation %d/Sofa south' % index) for index in (1, 2)]
    for actor in crew:
        if TAG in map(str, actor.tags) or actor.character_mesh.get_skeletal_mesh_asset() != ctx.asset(MESH):
            raise RuntimeError('Expected the two unchanged Nyxar conversation actors')
        actual_scale = actor.character_mesh.get_relative_transform().scale3d
        if max(abs(v-proof['fit_scale']) for v in actual_scale.to_tuple()) > .00001:
            raise RuntimeError('Preserve the current crew scale; measured fit no longer applies')
    protected = {a: _transform(a.get_actor_transform()) for a in actors if a not in crew}
    materials = {a: tuple(a.character_mesh.get_materials()) for a in crew}
    clip, animation = _author_clip(ctx, proof, u)
    rows = []
    for index, (actor, sofa) in enumerate(zip(crew, sofas)):
        transform = sofa.static_mesh_component.get_world_transform()
        if not all(abs(v-w) < .0001 for v, w in zip(transform.rotation.to_tuple(), (0, 0, 0, 1))):
            raise RuntimeError('Selected sofa no longer faces its measured +Y direction')
        position = u.MathLibrary.transform_location(transform, u.Vector(91, -30, animation['fixed_actor_origin_z']))
        lo, hi = animation['posed_scaled_bounds']
        if position.x+hi[0] > 4000 and position.x+lo[0] < 4400:
            raise RuntimeError('Seated body intrudes on the central 4000..4400 cm aisle')
        before = transform_record(actor)
        before.update({'mesh_relative': _transform(actor.character_mesh.get_relative_transform()),
                       'collision': actor.get_actor_enable_collision(),
                       'idle_animation': str(actor.get_editor_property('idle_animation')),
                       'gesture_animations': list(map(str, actor.get_editor_property('gesture_animations'))),
                       'route_points': [list(p.to_tuple()) for p in actor.get_editor_property('route_points')],
                       'phase_offset': float(actor.get_editor_property('phase_offset'))})
        ctx.move(actor, position, (0, 90, 0))
        component = actor.character_mesh
        component.set_relative_location(u.Vector(0, 0, 0), False, False)
        component.set_relative_rotation(u.Rotator(yaw=-90), False, False)
        actor.set_editor_property('idle_animation', clip)
        actor.set_editor_property('gesture_animations', [])
        actor.set_editor_property('route_points', [])
        actor.set_editor_property('phase_offset', index*2.)
        actor.set_actor_enable_collision(False)  # Actual occupied sofa retains its collision.
        component.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
        data = component.get_editor_property('animation_data')
        data.anim_to_play, data.saved_looping, data.saved_playing = clip, True, True
        data.saved_position = index*2.
        component.set_editor_property('animation_data', data)
        actor.tags = list(actor.tags)+[TAG]
        row = {'actor': actor.get_actor_label(), 'sofa': sofa.get_actor_label(), 'before': before,
               'after': transform_record(actor), 'phase_seconds': index*2.,
               'body_bounds_world_cm': [[position.x+lo[0], position.y+lo[1], lo[2]],
                                        [position.x+hi[0], position.y+hi[1], hi[2]]]}
        ctx.records.append({'kind': 'measured_seated_lounge', **row})
        rows.append(row)
    for x in (4000, 4200, 4400):
        hit = u.SystemLibrary.capsule_trace_single_by_profile(world, u.Vector(x, -2400, 78),
            u.Vector(x, -3750, 78), 34., 75., 'Pawn', False, [], u.DrawDebugTrace.NONE, True)
        if hit and hit.to_tuple()[0]:
            raise RuntimeError('Actual player capsule cannot traverse retained central social aisle')
    if any(_transform(a.get_actor_transform()) != before for a, before in protected.items()):
        raise RuntimeError('Lounge seating moved an unrelated owner actor')
    if any(tuple(a.character_mesh.get_materials()) != before for a, before in materials.items()):
        raise RuntimeError('Seating changed an existing crew material')
    if any(_sha(root, asset) != value for asset, value in proof['source_sha256'].items()):
        raise RuntimeError('Seating changed an original furniture, mesh or animation asset')
    return {'module': 'social_seated_crew', 'dirty_assets': [clip.get_path_name()],
            'basis_map_sha256': MAP_SHA, 'source_probe_sha256': PROBE_SHA,
            'source_hashes_preserved': proof['source_sha256'], 'animation': animation, 'seated_actors': rows,
            'central_aisle_x_cm': [4000, 4400], 'all_actor_capsule_sweeps': 3,
            'protected_actor_transforms': len(protected),
            'cameras': [{'name': 'Lounge seated contact', 'location': [3890, -2830, 125],
                         'look_at': [3650, -3010, 75]},
                        {'name': 'Lounge second pocket', 'location': [4500, -2810, 135],
                         'look_at': [4740, -3010, 75]}],
            'limits': 'Source-skin contact and native pose readback are authoring evidence; actual rendered sofa contact, relaxed hands and looping appearance require review.'}
