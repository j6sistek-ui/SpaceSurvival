"""Versioned pool pickup repair: squat and step, with cue outside the right hip.

Original shot frames and vendor assets stay intact. The integration lead alone
creates/saves/rebinds the new clips and sequence and reviews whole-body renders.
"""
import copy
import math
from contextlib import contextmanager
from pathlib import Path

import AuthorStationPoolMatchAnimation as previous
import AuthorStationPoolMatchSequence as sequence

pool = previous.pool
pm = previous.pose_math
ORIGINAL_FRAME = previous._frame
PRIVATE = {key: value+'_PickupV2' for key, value in previous.PRIVATE.items()}
SEQUENCE_ASSET = sequence.ASSET+'_PickupV2'
SEQUENCE_LABEL = 'Refine/OrbitPool/Alternating match sequence PickupV2'


def _lerp(a, b, start, end, seconds):
    return pool._mix(a, b, pool._smooth(start, end, seconds))


def _step(a, b, start, end, seconds):
    weight = pool._smooth(start, end, seconds)
    point = pool._mix(a, b, weight)
    lift = 5.*math.sin(math.pi*weight) if 0. < weight < 1. else 0.
    return (point[0], point[1], point[2]+lift)


def _foot_offset(side, seconds, grasp, release):
    tray = (25., 3., 0.) if side == 'l' else (8., 0., 0.)
    felt = (-12., 45., 0.)
    # One foot travels at a time; no sliding both feet under a planted torso.
    first = (grasp-3., grasp-2.45) if side == 'l' else (grasp-2.35, grasp-1.8)
    forward = (grasp+1., grasp+1.55) if side == 'l' else (grasp+1.65, grasp+2.2)
    back = (release+.35, release+1.) if side == 'r' else (release+1.1, release+1.75)
    if seconds < forward[0]:
        return _step((0., 0., 0.), tray, *first, seconds)
    if seconds < back[0]:
        return _step(tray, felt, *forward, seconds)
    return _step(felt, (0., 0., 0.), *back, seconds)


def _body(seconds, model, grasp, release):
    down = 37. if model['key'] == 'nyxar' else 54.
    squat = pool._smooth(grasp-3., grasp-.7, seconds)
    rise = pool._smooth(grasp, grasp+1., seconds)
    walk = pool._smooth(grasp+1., grasp+2.2, seconds)
    recover = pool._smooth(release+.35, release+1.75, seconds)
    placing_down = 16. if model['key'] == 'nyxar' else 27.
    hip = (15.*squat*(1.-walk)-12.*walk, 45.*walk,
           -down*squat*(1.-rise)-placing_down*rise)
    hip = pool._mix(hip, (0., 0., 0.), recover)
    hip = (hip[0], hip[1], hip[2]-6.*math.sin(math.pi*recover))
    bend = (12.*squat*(1.-walk)+24.*walk)*(1.-recover)
    return hip, bend


def _frame(model, seconds, contract, skin=False):
    center, pickup, grasp, release = previous._held_path(model['key'], seconds, contract)
    if not pickup:
        return ORIGINAL_FRAME(model, seconds, contract, skin)
    old_local, old_cue, old_held, old_check = ORIGINAL_FRAME(model, seconds, contract, False)
    bones, scale = model['bones'], model['scale']
    location, rotation, yaw = previous._placement(model, contract)
    old_world = pm._forward(old_local, bones)
    override = pool._smooth(grasp-3., grasp-2.4, seconds)*(1.-pool._smooth(release+1.7, release+2., seconds))
    local = previous._blend_pose(old_local, model['rest'], override)
    hip, bend = _body(seconds, model, grasp, release)
    if model['key'] == 'trooper':
        # Native idle has narrower feet than the already-fitted pool stance.
        # Keep its ordinary bent-knee accommodation throughout this window.
        hip = pm._add(hip, (0., -2., -8.))
    custom_pelvis = pm._add(model['rest']['pelvis']['location'], pm._mul(hip, 1./scale))
    local['pelvis']['location'] = pool._mix(old_local['pelvis']['location'], custom_pelvis, override)
    # Sagittal pitch only. No65-degree sideways pelvis roll or full-body twist.
    custom_rotation = pm._qmul(pool._axis((1., 0., 0.), -bend), model['rest_world']['pelvis']['rotation'])
    pm._world_rotation(local, bones, 'pelvis', pool._lerp_quat(old_world['pelvis']['rotation'], custom_rotation, override))
    for bone, fraction in (('neck_01', .25), ('head', .35)):
        current = pm._forward(local, bones)[bone]['rotation']
        pm._world_rotation(local, bones, bone, pm._qmul(pool._axis((1., 0., 0.), bend*fraction), current))

    feet = {}
    for side, original in model['feet'].items():
        offset = _foot_offset(side, seconds, grasp, release)
        target = pm._add(original['location'], pm._mul(offset, 1./scale))
        feet[side] = {'location': target, 'rotation': original['rotation'], 'lift': offset[2]}
        pm._chain(local, bones, 'thigh_'+side, 'calf_'+side, 'foot_'+side, target, (0., 1., .05))
        pm._world_rotation(local, bones, 'foot_'+side, original['rotation'])

    # Retain the proven pickup/carry/release hand path and digit pose. The body
    # now travels beneath that path, rather than twisting to reach from afar.
    left = old_world['hand_l']
    pm._chain(local, bones, 'upperarm_l', 'lowerarm_l', 'hand_l', left['location'], (1., .1, .15))
    pm._world_rotation(local, bones, 'hand_l', left['rotation'])
    for name in local:
        if name.endswith('_l') and name.startswith(('index_', 'middle_', 'ring_', 'pinky_', 'thumb_')):
            local[name] = copy.deepcopy(old_local[name])

    # Cue is carried vertically to the OUTSIDE of the right hip. Its complete
    #156cm shaft remains on this side during the crouch, lift and placement.
    park = pool._smooth(grasp-3., grasp-2.4, seconds)*(1.-pool._smooth(release+1.7, release+2., seconds))
    old_tip = pm._rotate(pm._inverse(rotation), pm._sub(old_cue['location'], (location[0], location[1], 0.)))
    old_pitch = old_cue['rotation'][0]
    old_direction = (0., math.cos(math.radians(old_pitch)), math.sin(math.radians(old_pitch)))
    old_grip = pm._sub(old_tip, pm._mul(old_direction, 108.))
    park_grip = (-48.+hip[0], 8.+hip[1], 110.+hip[2]*.4)
    grip = pool._mix(old_grip, park_grip, park)
    pitch = old_pitch+(90.-old_pitch)*park
    direction = (0., math.cos(math.radians(pitch)), math.sin(math.radians(pitch)))
    tilt = pool._axis((1., 0., 0.), pitch+6.)
    hand_rotation = pm._qmul(tilt, pool._pose_basis((0., 0., 1.), (-1., 0., 0.)))
    right_target = previous._component(pm._add(grip, pm._rotate(tilt, model['grip_offset'])), model)
    pm._chain(local, bones, 'upperarm_r', 'lowerarm_r', 'hand_r', right_target, (-1., -.2, .15))
    pm._world_rotation(local, bones, 'hand_r', hand_rotation)
    for name in local:
        if name.endswith('_r') and name.startswith(('index_', 'middle_', 'ring_', 'pinky_', 'thumb_')):
            local[name] = copy.deepcopy(old_local[name])
    world = pm._forward(local, bones)
    held = None
    if grasp <= seconds <= release:
        hand = world['hand_l']
        held = previous._world(pm._add(hand['location'], pm._rotate(hand['rotation'], model['cup_offset'])),
                               model, location, rotation)
    tip = pm._add(grip, pm._mul(direction, 108.))
    cue_tip = pm._add((location[0], location[1], 0.), pm._rotate(rotation, tip))
    cue = {'time': seconds, 'location': list(cue_tip), 'rotation': [pitch, yaw+90., 0.], 'scale': [1., 1., 1.]}
    summary = {'time': seconds, 'aim': old_check['aim'], 'pickup': pickup,
               'pelvis_sagittal_bend_degrees': bend, 'pelvis_side_bend_degrees': 0.,
               'hip_displacement_cm': hip, 'feet_step_lift_cm': {s:r['lift'] for s,r in feet.items()},
               'cue_butt_z': tip[2]-156.288*direction[2],
               'cue_to_hip_lateral_cm': abs(grip[0]-hip[0]),
               'right_wrist_error_cm': math.dist(world['hand_r']['location'], right_target)*scale,
               'held_ball_error_cm': math.dist(held, center) if held else None,
               'feet_bone_error_cm': {s: math.dist(world['foot_'+s]['location'], r['location'])*scale
                                      for s,r in feet.items()}}
    if skin:
        skinned = pm._skin(world, model['prepared'])
        # Existing validator checks ground contact. Remove the explicitly
        #authored swing-foot lift; retain actual measured soles separately.
        actual = {side: min(p[2]*scale+model['origin_z'] for name,p in skinned
                           if name in ('foot_'+side, 'ball_'+side, 'ankle_bck_'+side)) for side in ('l','r')}
        summary['feet_surface_actual_z'] = actual
        summary['feet_surface_z'] = {s:z-feet[s]['lift'] for s,z in actual.items()}
        if held:
            hand = world['hand_l']
            cup = pm._add(hand['location'], pm._rotate(hand['rotation'], model['cup_offset']))
            summary['ball_digit_clearance_cm'] = {finger: min(math.dist(p,cup)*scale-contract.BALL_RADIUS
                for name,p in skinned if name.startswith(finger+'_') and name.endswith('_l'))
                for finger in ('hand','index','middle','ring','pinky','thumb')}
    return local, cue, held, summary


@contextmanager
def _versioned_author():
    old_frame, old_private = previous._frame, previous.PRIVATE
    try:
        previous._frame, previous.PRIVATE = _frame, PRIVATE
        yield
    finally:
        previous._frame, previous.PRIVATE = old_frame, old_private


def fit(root, output=None):
    with _versioned_author():
        result = previous.fit(Path(root), output)
    return result


def create(ctx):
    with _versioned_author():
        return previous.create(ctx)


def apply_sequence(ctx, players, cue_ball, motion, static_balls):
    old_asset, old_label = sequence.ASSET, sequence.LABEL
    try:
        sequence.ASSET, sequence.LABEL = SEQUENCE_ASSET, SEQUENCE_LABEL
        return sequence.apply(ctx, players, cue_ball, motion, static_balls)
    finally:
        sequence.ASSET, sequence.LABEL = old_asset, old_label
