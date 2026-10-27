"""Unsaved two-bone contact correction for released arms only.

Keep the source elbow plane and segment lengths, with explicit world/local
hand-orientation policies. The caller supplies a measured target and audits surfaces and joint motion;
IK alone supplies neither collision avoidance nor anatomical acceptance.
"""
import math

import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from validate_g2_contact_recipe import skin, triangle_radii


class ArmSurfaceScreen:
    """Actual triangle screen, deliberately limited to distal arm versus body."""
    def __init__(self, model, meshes, side):
        self.model = model
        self.inverse = np.array([model.rest[n].inverted() for n in model.names])
        selected = np.array([n.endswith('_' + side) and n.startswith(
            ('lowerarm_', 'hand_', 'thumb_', 'index_', 'middle_', 'ring_', 'pinky_')) for n in model.names])
        self.regions = []
        for mesh in meshes:
            _, _, faces, joints, weights, body, _ = mesh
            mask = (weights * selected[joints]).sum(axis=1) > .75
            self.regions.append((mesh, faces[np.all(mask[faces], axis=1)], body))

    def sample(self, pose):
        matrices = np.array([pose[n] for n in self.model.names]) @ self.inverse
        av, af, bv, bf = [], [], [], []
        for mesh, arms, body in self.regions:
            points = skin(matrices, mesh)
            if len(arms):
                af.extend((arms + len(av)).tolist()); av.extend(points.tolist())
            if len(body):
                bf.extend((body + len(bv)).tolist()); bv.extend(points.tolist())
        av, af = np.array(av), np.array(af)
        tree = BVHTree.FromPolygons(bv, bf, all_triangles=True)
        pairs = BVHTree.FromPolygons(av.tolist(), af.tolist(), all_triangles=True).overlap(tree)
        z = av[af, 2]
        radius = triangle_radii(av, af)
        pole = int(((radius < .02499) & (z.max(axis=1) > 0) & (z.min(axis=1) < 5)).sum())
        return av, af, tree, pairs, pole

    @staticmethod
    def escape(sample, clearance=.003):
        av, af, tree, pairs, _ = sample
        constraints = []
        vertices = np.unique(af[sorted(set(a for a, _ in pairs))])
        for index in vertices:
            point = Vector(av[index])
            near, normal, _, distance = tree.find_nearest(point)
            signed = (point - near).dot(normal)
            if signed < clearance and distance < .08:
                constraints.append((np.array(normal), clearance - signed))
        shift = np.zeros(3)
        for _ in range(20):
            for normal, need in constraints:
                shift += normal * max(0., need - np.dot(normal, shift))
        length = np.linalg.norm(shift)
        if length > .02:
            shift *= .02 / length
        return Vector(shift), len(constraints)


def reachable_free_target(original, side, desired, softness=.02):
    """Route a released hand within reach, without moving/stretching the body.

    The 10/145 degree interval is this review's conservative elbow envelope,
    not a universal human limit. A C1 radial cap avoids a hard distance clamp.
    This changes the requested free target; never use it for a locked grip.
    """
    a, b, c = (original[name + '_' + side].translation for name in ('upperarm', 'lowerarm', 'hand'))
    first, second = (b - a).length, (c - b).length
    low = math.sqrt(first * first + second * second + 2 * first * second * math.cos(math.radians(145)))
    high = math.sqrt(first * first + second * second + 2 * first * second * math.cos(math.radians(10)))
    vector = Vector(desired) - a
    distance = vector.length
    assert distance > 1e-6 and 0 < softness < (high - low) / 2

    def cap(value, maximum):
        if value < maximum - softness:
            return value
        if value > maximum + softness:
            return maximum
        return maximum - (maximum + softness - value) ** 2 / (4 * softness)

    feasible = -cap(-cap(distance, high - 1e-5), -low - 1e-5)
    return a + vector * (feasible / distance), abs(feasible - distance)


def source_return_left_corridor(model, original, seconds, residual, hand_orientation='source_world'):
    """Measured left-hand route for the released G2 return, not a grip solver."""
    if not 48.8 < seconds < 50.1:
        return {n: m.copy() for n, m in original.items()}, {}
    envelope = model.smooth((seconds - 48.8) / .4) * model.smooth((50.1 - seconds) / .4)
    chest = original['spine_05'].to_quaternion() @ model.rest['spine_05'].to_quaternion().inverted()
    target = original['hand_l'].translation + (chest @ Vector((1, 0, 1)).normalized()) * (.18 * envelope)
    target, projection = reachable_free_target(original, 'l', target)
    pulse = model.smooth((seconds - 49.2) / .16) * model.smooth((49.65 - seconds) / .17)
    target += chest @ Vector(residual) * pulse
    target, _ = reachable_free_target(original, 'l', target)
    pose, metrics = place_released_hand(model, original, 'l', target, hand_orientation)
    return pose, dict(metrics, target_projection_m=projection)


def place_released_hand(model, original, side, target, hand_orientation='source_world'):
    assert hand_orientation in ('source_world', 'source_local')
    pose = {name: matrix.copy() for name, matrix in original.items()}
    upper, lower, hand = (name + '_' + side for name in ('upperarm', 'lowerarm', 'hand'))
    a, b, c = (pose[name].translation.copy() for name in (upper, lower, hand))
    target = Vector(target)
    first, second = (b - a).length, (c - b).length
    direction = target - a
    distance = direction.length
    assert distance > 1e-6
    direction.normalize()
    cosine = (distance * distance - first * first - second * second) / (2 * first * second)
    assert -1 <= cosine <= 1, 'Target requires stretching or chain folding'
    bend = math.degrees(math.acos(cosine))
    assert 10 <= bend <= 145, ('Target outside review elbow envelope', bend)
    hint = b - a - direction * (b - a).dot(direction)
    assert hint.length > 1e-5, 'Source elbow plane is degenerate'
    hint.normalize()
    projection = (first * first - second * second + distance * distance) / (2 * distance)
    elbow = a + direction * projection + hint * math.sqrt(max(0., first * first - projection * projection))

    def aim(name, current, desired):
        rotation = current.rotation_difference(desired).to_matrix().to_4x4()
        pivot = pose[name].translation
        transform = Matrix.Translation(pivot) @ rotation @ Matrix.Translation(-pivot)
        for descendant in model.descendants[name]:
            pose[descendant] = transform @ pose[descendant]

    aim(upper, b - a, elbow - a)
    aim(lower, pose[hand].translation - pose[lower].translation, target - elbow)
    # A released hand can follow its forearm with the source wrist/finger pose.
    # Forcing its world orientation after moving the elbow instead transfers
    # that correction into the wrist. Neither policy certifies anatomy.
    if hand_orientation == 'source_world':
        wanted = original[hand].copy()
        wanted.translation = target
        transform = wanted @ pose[hand].inverted()
        for name in model.descendants[hand]:
            pose[name] = transform @ pose[name]
    moving = set(model.descendants[upper])
    protected_error = max(float(np.abs(np.asarray(pose[n]) - np.asarray(original[n])).max())
                          for n in model.names if n not in moving)
    length_error = max(abs((pose[lower].translation - pose[upper].translation).length - first),
                       abs((pose[hand].translation - pose[lower].translation).length - second))
    if hand_orientation == 'source_world':
        orientation_error = float(np.abs(np.asarray(pose[hand].to_3x3()) - np.asarray(original[hand].to_3x3())).max())
        assert orientation_error < 1e-7
    else:
        before = original[lower].inverted() @ original[hand]
        after = pose[lower].inverted() @ pose[hand]
        orientation_error = float(np.abs(np.asarray(after.to_3x3()) - np.asarray(before.to_3x3())).max())
        assert orientation_error < 1e-5
    assert protected_error == 0 and length_error < 1e-6
    return pose, {'elbow_bend_degrees': bend, 'protected_matrix_error': protected_error,
                  'length_error_m': length_error, 'hand_orientation_error': orientation_error,
                  'hand_orientation_space': hand_orientation,
                  'hand_shift_m': list(target - c)}
