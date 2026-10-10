"""V3 changes only the free arm/held ball during the middle of the carry.

V2's grounded squat, steps, torso and parked cue remain identical. Tray pickup,
felt placement, original shots and all timing retain their existing samples.
"""
import math
from contextlib import contextmanager
from pathlib import Path

import RefineStationPoolPickupPose as v2

previous, sequence, pool, pm = v2.previous, v2.sequence, v2.pool, v2.pm
PRIVATE = {key: value + '_PickupV3' for key, value in previous.PRIVATE.items()}
SEQUENCE_ASSET = sequence.ASSET + '_PickupV3'
SEQUENCE_LABEL = 'Refine/OrbitPool/Alternating match sequence PickupV3'


def _frame(model, seconds, contract, skin=False):
    local, cue, held, check = v2._frame(model, seconds, contract, skin)
    _, _, grasp, release = previous._held_path(model['key'], seconds, contract)
    weight = (pool._smooth(grasp+.7, grasp+1.5, seconds)
              * (1.-pool._smooth(release-1.65, release-.65, seconds)))
    if not held or weight <= 0.:
        return local, cue, held, check
    bones, scale = model['bones'], model['scale']
    world = pm._forward(local, bones)
    hand = world['hand_l']
    shoulder = world['upperarm_l']['location']
    # A relaxed bent arm carries in front of the moving shoulder. The existing
    # wrist height and top/side grip keep the ball above the physical cushion.
    forward = (shoulder[0]+8./scale, shoulder[1]+22./scale, hand['location'][2])
    target = pool._mix(hand['location'], forward, weight)
    # Blend the swivel angle around the reach axis, not raw pole vectors.
    # A vector lerp can pass through the axis and abruptly flip the elbow.
    axis = pm._unit(pm._sub(target, shoulder))
    old_elbow = pm._sub(world['lowerarm_l']['location'], shoulder)
    start = pm._unit(pm._sub(old_elbow, pm._mul(axis, pm._dot(old_elbow, axis))))
    preference = (1., 0., -1.)
    end = pm._unit(pm._sub(preference, pm._mul(axis, pm._dot(preference, axis))))
    cross = (start[1]*end[2]-start[2]*end[1], start[2]*end[0]-start[0]*end[2],
             start[0]*end[1]-start[1]*end[0])
    angle = math.atan2(pm._dot(axis, cross), pm._dot(start, end))
    pole = pm._rotate(pool._axis(axis, math.degrees(angle*weight)), start)
    pm._chain(local, bones, 'upperarm_l', 'lowerarm_l', 'hand_l', target, pole)
    pm._world_rotation(local, bones, 'hand_l', hand['rotation'])
    world = pm._forward(local, bones)
    hand = world['hand_l']
    local_center = pm._add(hand['location'], pm._rotate(hand['rotation'], model['cup_offset']))
    expected_center = pm._add(target, pm._rotate(hand['rotation'], model['cup_offset']))
    location, rotation, _ = previous._placement(model, contract)
    held = previous._world(local_center, model, location, rotation)
    check.update(carry_forward_blend=weight,
                 held_ball_error_cm=math.dist(local_center, expected_center)*scale,
                 hand_ahead_of_shoulder_cm=(hand['location'][1]-shoulder[1])*scale,
                 elbow_below_shoulder_cm=(shoulder[2]-world['lowerarm_l']['location'][2])*scale,
                 elbow_ahead_of_shoulder_cm=(world['lowerarm_l']['location'][1]-shoulder[1])*scale,
                 carry_scope='Only free arm rotations and held ball; V2 body/feet/cue untouched')
    if weight > .999:
        if check['hand_ahead_of_shoulder_cm'] < 21.9 or check['elbow_below_shoulder_cm'] < 10.:
            raise RuntimeError('V3 carry lost its forward hand/lowered elbow silhouette')
    if skin:
        skinned = pm._skin(world, model['prepared'])
        check['ball_digit_clearance_cm'] = {finger: min(math.dist(p, local_center)*scale-contract.BALL_RADIUS
            for name, p in skinned if name.startswith(finger+'_') and name.endswith('_l'))
            for finger in ('hand', 'index', 'middle', 'ring', 'pinky', 'thumb')}
    return local, cue, held, check


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
        return previous.fit(Path(root), output)


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
