"""Ground a NEW Type02 female bartender clip without changing her upper body.

Only six leg rotation tracks change. The lead runs author() in an isolated
native process, saves the returned private clip, and separately reviews it in
the actual room. Original imported clips, skeletons and meshes stay unchanged.
"""
import copy
import hashlib
import json
import math
from pathlib import Path

import RefineStationSocialSeatedCrew as rig

SOURCE = '/Game/OutpostSandbox/StationRefinement/BartenderCandidates20261006_V2/Preview/A_FemaleBartender_Type02'
TARGET = '/Game/SpaceSurvival/Licensed/AlienFemalePresentation/SK_AlienFemalePresentation'
PRIVATE = '/Game/OutpostSandbox/StationRefinement/BartenderGrounded20261006_V1/A_FemaleBartender_Type02_Grounded'
CHANGED = tuple(part+'_'+side for side in ('l', 'r') for part in ('thigh', 'calf', 'foot'))
ORIGINAL_RECEIPT = 'StationBartenderCandidates2.json'
ORIGINAL_SHA = 'd0ff06dc38154e8c0df297e4e4c6a1bc66a66ee424831a65361105f0b059d191'


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _require(value, message):
    if not value:
        raise RuntimeError(message)


def _feet(mesh, u):
    dynamic, geometry = rig._geometry(mesh, True, u)
    _, rows = u.GeometryScript_BoneWeights.get_all_bones_info(dynamic)
    bones = [{'index': b.index, 'parent': b.parent_index, 'name': str(b.name),
              'reference_world': rig._transform(b.world_transform)} for b in rows]
    names = {b['index']: b['name'] for b in bones}
    data = {'bones': bones, 'vertices': [], 'weights': []}
    source_ids = []
    # Complete foot/toe skin in the measured source foot region, not the sparse
    # viewport diagnostic sample. No upper-body vertices participate in fitting.
    for index, point in enumerate(geometry['vertices']):
        if point[2] >= 17.:
            continue
        _, weights, valid = u.GeometryScript_BoneWeights.get_vertex_bone_weights(dynamic, index)
        total = sum(w.weight for w in weights)
        _require(valid and abs(total-1.) < .002, 'Native foot skin weights are invalid')
        dominant = names[max(weights, key=lambda w: w.weight).bone_index]
        if dominant not in ('foot_l', 'ball_l', 'foot_r', 'ball_r'):
            continue
        data['vertices'].append(point)
        data['weights'].append([[w.bone_index, float(w.weight/total)] for w in weights])
        source_ids.append(index)
    prepared = rig._skin_setup(data)
    grouped = {side: [row for row in prepared if row[0].endswith('_'+side)] for side in ('l', 'r')}
    _require(all(len(rows) > 50 for rows in grouped.values()), 'Native foot region is incomplete')
    return bones, grouped, {'source_vertices': len(geometry['vertices']),
                            'foot_vertices': {s: len(v) for s, v in grouped.items()},
                            'original_vertex_ids': source_ids, 'filter_reference_z_less_than_cm': 17.}


def _sole(world, prepared, scale, offset):
    return min(point[2]*scale+offset for _, point in rig._skin(world, prepared))


def _fit(local, bones, feet, scale, offset):
    """Preserve ankle XY/orientation; bend measured legs to lift buried soles."""
    original = rig._forward(local, bones)
    corrected = copy.deepcopy(local)
    before = {s: _sole(original, feet[s], scale, offset) for s in ('l', 'r')}
    moved = {}
    for side in ('l', 'r'):
        thigh, calf, foot = (part+'_'+side for part in ('thigh', 'calf', 'foot'))
        hip, knee, ankle = (original[name]['location'] for name in (thigh, calf, foot))
        pole = rig._sub(knee, hip)
        axis = rig._unit(rig._sub(ankle, hip))
        perpendicular = rig._sub(pole, rig._mul(axis, rig._dot(pole, axis)))
        if math.sqrt(rig._dot(perpendicular, perpendicular)) < .02:
            pole = (0., 1., 0.)
        lift = max(0., .04-before[side])
        _require(lift < 9., 'Foot defect exceeds the bounded 9 cm leg-only correction')
        target = list(ankle)
        target[2] += lift/scale
        if lift > .00001:
            rig._chain(corrected, bones, thigh, calf, foot, target, pole)
            rig._world_rotation(corrected, bones, foot, original[foot]['rotation'])
        # Blended ankle weights may differ slightly from a rigid foot. At most
        # two small measured refinements retain the same original ankle XY.
        for _ in range(2):
            world = rig._forward(corrected, bones)
            actual = _sole(world, feet[side], scale, offset)
            if actual >= -.03:
                break
            target[2] += (.04-actual)/scale
            rig._chain(corrected, bones, thigh, calf, foot, target, pole)
            rig._world_rotation(corrected, bones, foot, original[foot]['rotation'])
        moved[side] = (target[2]-ankle[2])*scale
    world = rig._forward(corrected, bones)
    after = {s: _sole(world, feet[s], scale, offset) for s in ('l', 'r')}
    _require(min(after.values()) >= -.05 and max(after.values()) < 1.,
             'Grounded standing soles are buried or floating: '+str(after))
    for name in corrected:
        if name not in CHANGED:
            _require(corrected[name] == local[name], 'Grounding changed a non-leg track')
        else:
            _require(corrected[name]['location'] == local[name]['location'] and
                     corrected[name]['scale'] == local[name]['scale'], 'Grounding changed leg length or scale')
    for side in ('l', 'r'):
        foot = 'foot_'+side
        _require(math.dist(world[foot]['location'][:2], original[foot]['location'][:2]) < .003,
                 'Grounding shifted ankle horizontally')
        _require(abs(rig._dot(world[foot]['rotation'], original[foot]['rotation'])) > .99999,
                 'Grounding changed source foot orientation')
    return corrected, world, {'source_sole_z_cm': before, 'grounded_sole_z_cm': after, 'ankle_lift_cm': moved}


def author(ctx):
    """Return the one new unsaved clip; no map loads, saves or actor changes."""
    import unreal as u
    import ImportStationBartenderMocap as mocap
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    receipt_path = root/'.agent/local/StationRefinement'/ORIGINAL_RECEIPT
    _require(_sha(receipt_path) == ORIGINAL_SHA, 'Frozen original mocap receipt changed')
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    _require(receipt['success'] and receipt['preservation_pass'], 'Require successful original mocap candidates')
    _require(not u.EditorAssetLibrary.does_asset_exist(PRIVATE), 'Preserve existing grounded candidate')
    source, mesh = ctx.asset(SOURCE), ctx.asset(TARGET)
    _require(source.get_editor_property('skeleton') == mesh.skeleton, 'Candidate skeleton mismatch')
    source_file = root/('Content/'+SOURCE[6:]+'.uasset')
    source_sha = _sha(source_file)
    _require(source_sha == receipt['saved_asset_sha256'][source.get_path_name()], 'Frozen Type02 source changed')
    presentation = receipt['candidate']['target_presentation']
    scale, offset = presentation['uniform_scale'], presentation['sole_offset_cm']
    bones, feet, selection = _feet(mesh, u)
    model = source.get_editor_property('data_model_interface')
    keys, duration = model.get_number_of_keys(), float(source.sequence_length)
    rate = model.get_frame_rate()
    _require(abs(duration-33.) < .001 and 2 <= keys <= 10000 and rate.numerator > 0 and
             abs((keys-1)*rate.denominator/rate.numerator-duration) < .001,
             'Type02 native duration, rate and key count disagree')
    options = u.AnimPoseEvaluationOptions(optional_skeletal_mesh=mesh, evaluation_type=u.AnimDataEvalType.RAW)
    api = u.AnimPoseExtensions
    tracks = {name: [] for name in CHANGED}
    frames, readback = [], {}
    maximum_step, maximum_delta = 0., 0.
    for frame in range(keys):
        seconds = duration*frame/(keys-1)
        pose = api.get_anim_pose_at_time(source, seconds, options)
        local = {b['name']: rig._transform(api.get_bone_pose(pose, b['name'], u.AnimPoseSpaces.LOCAL)) for b in bones}
        try:
            fitted, world, measurement = _fit(local, bones, feet, scale, offset)
        except RuntimeError as error:
            raise RuntimeError('Type02 frame %d at %.6fs: %s' % (frame, seconds, error)) from error
        for name in CHANGED:
            rotation = fitted[name]['rotation']
            maximum_delta = max(maximum_delta, math.degrees(2.*math.acos(min(1., abs(rig._dot(rotation, local[name]['rotation']))))))
            if tracks[name]:
                if rig._dot(tracks[name][-1]['rotation'], rotation) < 0:
                    fitted[name]['rotation'] = rig._mul(rotation, -1.)
                step = math.degrees(2.*math.acos(min(1., abs(rig._dot(tracks[name][-1]['rotation'], fitted[name]['rotation'])))))
                maximum_step = max(maximum_step, step)
                _require(step < 12., 'Leg IK swivel jumps between adjacent source keys: '+name)
            tracks[name].append(fitted[name])
        frames.append({'frame': frame, **measurement})
        if frame % 30 == 0 or frame == keys-1:
            readback[frame] = world
            u.log('BARTENDER_GROUND frame=%d/%d soles=%.3f/%.3f cm' %
                  (frame, keys, measurement['grounded_sole_z_cm']['l'], measurement['grounded_sole_z_cm']['r']))
    _require(maximum_delta < 70., 'Leg-only grounding requires an excessive joint correction')
    for name, rows in tracks.items():
        _require(abs(rig._dot(rows[0]['rotation'], rows[-1]['rotation'])) > .99999,
                 'Grounding breaks the source loop boundary')
    clip = u.EditorAssetLibrary.duplicate_asset(SOURCE, PRIVATE)
    _require(clip and clip.get_editor_property('skeleton') == mesh.skeleton, 'Cannot duplicate compatible private candidate')
    controller = clip.get_editor_property('controller')
    controller.open_bracket('Native measured female bartender foot contacts', False)
    try:
        for name, rows in tracks.items():
            _require(controller.set_bone_track_keys(name, [u.Vector(*t['location']) for t in rows],
                     [u.Quat(*t['rotation']) for t in rows], [u.Vector(*t['scale']) for t in rows], False),
                     'Private grounded leg track write failed: '+name)
    finally:
        controller.close_bracket(False)
    native = []
    for frame, expected in readback.items():
        pose = api.get_anim_pose_at_time(clip, duration*frame/(keys-1), options)
        world = {b['name']: rig._transform(api.get_bone_pose(pose, b['name'], u.AnimPoseSpaces.WORLD)) for b in bones}
        error = max(math.dist(world[n]['location'], expected[n]['location']) for n in world)
        _require(error < .015 and all(abs(rig._dot(world[n]['rotation'], expected[n]['rotation'])) > .99999 for n in world),
                 'Native grounded readback differs from the fitted tracks')
        soles = {s: _sole(world, feet[s], scale, offset) for s in ('l', 'r')}
        _require(min(soles.values()) >= -.05 and max(soles.values()) < 1., 'Native grounded foot readback failed')
        native.append({'frame': frame, 'maximum_pose_error_cm': error, 'soles_cm': soles})
    # Native interpolation checks between source keys, evenly across the cycle.
    midpoint_checks = []
    for frame in range(0, keys-1, 15):
        seconds = duration*(frame+.5)/(keys-1)
        pose = api.get_anim_pose_at_time(clip, seconds, options)
        world = {b['name']: rig._transform(api.get_bone_pose(pose, b['name'], u.AnimPoseSpaces.WORLD)) for b in bones}
        soles = {s: _sole(world, feet[s], scale, offset) for s in ('l', 'r')}
        _require(min(soles.values()) >= -.1 and max(soles.values()) < 1., 'Native interpolated foot contact failed')
        midpoint_checks.append({'seconds': seconds, 'soles_cm': soles})
    _require(_sha(source_file) == source_sha, 'Grounding modified imported Type02 source')
    return {'success': True, 'target_presentation': presentation,
        'clips': [mocap._clip_probe(clip, u, presentation)], 'dirty_assets': [clip],
        'source_clip': SOURCE, 'source_sha256': source_sha, 'private_clip': PRIVATE,
        'changed_rotation_tracks': list(CHANGED), 'bone_translations_scales_and_nonleg_tracks_preserved': True,
        'root_pelvis_hands_head_motion_preserved': True, 'source_loop_preserved': True,
        'actor_height_cm': 178., 'actor_vertical_lift_cm': 0., 'counter_lift_cm': 0.,
        'frame_rate': [rate.numerator, rate.denominator], 'source_keys': keys, 'duration_seconds': duration,
        'foot_selection': selection, 'per_frame_contacts': frames,
        'maximum_adjacent_leg_rotation_step_degrees': maximum_step,
        'maximum_leg_rotation_adjustment_degrees': maximum_delta,
        'native_key_readbacks': native, 'native_between_key_contacts': midpoint_checks,
        'limits': 'One conversational Type02 candidate; no props, no serving routine, no map placement or visual acceptance.'}
