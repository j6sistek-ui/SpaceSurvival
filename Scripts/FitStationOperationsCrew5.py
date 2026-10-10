"""Pure measured-skin correction fit. This file never imports Unreal or saves assets.

The caller supplies an ACTUAL native seat support and footrest box. Five source
poses are preparation only; native authoring must check every source key, actual
chair/desk clearance and rendered contact before replacing any operator.
"""
import copy
import math

from RefineStationSocialSeatedCrew import (
    _chain, _dot, _forward, _qmul, _between, _skin, _skin_setup, _sub,
    _world_rotation,
)

TRACKS = tuple(part + '_' + side for side in ('l', 'r')
               for part in ('thigh', 'calf', 'foot', 'upperarm', 'lowerarm', 'hand'))


def require(value, message):
    if not value:
        raise RuntimeError(message)


def body_regions(bones):
    """Follow measured ancestry; trooper muscle/twist bones belong to their limb.

    Looking only for dominant thigh_l would omit all trooper thigh geometry.
    Exact intervening roots prevent torso or calf descendants becoming pelvis.
    """
    by_index = {row['index']: row for row in bones}
    roots = {'root', 'pelvis', 'spine_01', 'spine_02', 'spine_03', 'neck_01', 'head'}
    roots |= {part + '_' + side for side in ('l', 'r') for part in
              ('clavicle', 'upperarm', 'lowerarm', 'hand', 'thigh', 'calf', 'foot', 'ball')}
    result = {}
    for row in bones:
        current = row
        while current['name'] not in roots and current['parent'] >= 0:
            current = by_index[current['parent']]
        name = current['name']
        if name.startswith('ball_'):
            name = 'foot_' + name[-1]
        result[row['name']] = name
    return result


def setup(model):
    geometry = model['geometry']
    require(len(geometry['vertices']) == len(geometry['weights']), 'Full source skin is required')
    prepared = _skin_setup(geometry)
    regions = body_regions(geometry['bones'])
    groups = [regions[name] for name, _ in prepared]
    require(all(groups.count(name) >= 50 for name in
                ('pelvis', 'thigh_l', 'thigh_r', 'foot_l', 'foot_r', 'hand_l', 'hand_r')),
            'Actual full skin lacks required visible contact regions')
    return {'prepared': prepared, 'groups': groups,
            'contact_groups': {name: [i for i, group in enumerate(groups) if group == name]
                               for name in set(groups)}}


def _points(world, prepared, indices):
    return [point for _, point in _skin(world, [prepared[i] for i in indices])]


def _lap_gap(world, prepared, groups, triangles, side):
    """Lowest actual hand-skin gap above actual thigh triangles, in component cm."""
    indices = [i for i, group in enumerate(groups) if group in ('thigh_' + side, 'hand_' + side)]
    points = {i: point for i, (_, point) in zip(indices, _skin(world, [prepared[i] for i in indices]))}
    thigh = {}
    for tri in triangles:
        if all(groups[i] == 'thigh_' + side for i in tri):
            a, b, c = [points[i] for i in tri]
            denominator = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(denominator) > 1.e-7:
                for x in range(math.floor(min(a[0], b[0], c[0]) / 8), math.floor(max(a[0], b[0], c[0]) / 8) + 1):
                    for y in range(math.floor(min(a[1], b[1], c[1]) / 8), math.floor(max(a[1], b[1], c[1]) / 8) + 1):
                        thigh.setdefault((x, y), []).append((a, b, c, denominator))
    gaps = []
    for i in indices:
        if groups[i] != 'hand_' + side:
            continue
        x, y, z = points[i]
        for a, b, c, denominator in thigh.get((math.floor(x / 8), math.floor(y / 8)), []):
            if x < min(a[0], b[0], c[0]) or x > max(a[0], b[0], c[0]) or \
                    y < min(a[1], b[1], c[1]) or y > max(a[1], b[1], c[1]):
                continue
            p = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (y - c[1])) / denominator
            q = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / denominator
            if min(p, q, 1. - p - q) >= -1.e-6:
                gaps.append(z - p * a[2] - q * b[2] - (1. - p - q) * c[2])
    require(len(gaps) >= 30, 'Hand does not substantially overlap its actual skinned thigh')
    return min(gaps), len(gaps)


def fit(model, sample, support, prepared=None, origin_z=None):
    """Rotation-only fit at unit mesh scale; support is expressed in chair cm."""
    prepared = prepared or setup(model)
    geometry = model['geometry']; bones = geometry['bones']
    local = {name: copy.deepcopy(row['local']) for name, row in sample['bones'].items()}
    source = _forward(local, bones)
    require(max(math.dist(source[n]['location'], row['world']['location'])
                for n, row in sample['bones'].items()) < .005, 'Native source pose convention differs')
    hip_points = _points(source, prepared['prepared'], prepared['contact_groups']['pelvis'])
    seat_z = support['seat_z_cm']; actor_xy = support['actor_xy_cm']
    origin_z = seat_z + .5 - min(p[2] for p in hip_points) if origin_z is None else origin_z
    targets = {}
    floor = support['footrest_box_cm']; sole_target = floor[1][2] + .6
    for side, sign in (('l', 1.), ('r', -1.)):
        foot = 'foot_' + side
        current = source[foot]['location']
        indices = prepared['contact_groups'][foot]
        points = _points(source, prepared['prepared'], indices)
        # Fit the complete visible boot footprint inside the measured footrest.
        forward = max(0., floor[0][1] + .6 - actor_xy[1] - min(p[1] for p in points))
        target = [current[0], current[1] + forward,
                  current[2] + sole_target - origin_z - min(p[2] for p in points)]
        for _ in range(3):
            _chain(local, bones, 'thigh_' + side, 'calf_' + side, foot, target, (0., 1., .15))
            _world_rotation(local, bones, foot, source[foot]['rotation'])
            world = _forward(local, bones)
            actual = min(p[2] for p in _points(world, prepared['prepared'], indices)) + origin_z
            if abs(actual - sole_target) < .025:
                break
            target[2] += sole_target - actual
        pelvis = source['pelvis']['location']
        hand = 'hand_' + side
        hand_target = [sign * 15., pelvis[1] + support['hand_front_cm'] +
                       (1.5 if side == 'r' else 0.), pelvis[2] + 14.]
        fingers = _sub(source['middle_03_' + side]['location'], source[hand]['location'])
        rotation = _qmul(_between(fingers, (fingers[0], fingers[1], 0.)), source[hand]['rotation'])
        for _ in range(5):
            _chain(local, bones, 'upperarm_' + side, 'lowerarm_' + side, hand,
                   hand_target, (sign, -.2, -.25))
            _world_rotation(local, bones, hand, rotation)
            world = _forward(local, bones)
            gap, overlap = _lap_gap(world, prepared['prepared'], prepared['groups'], geometry['triangles'], side)
            if .4 <= gap <= .8:
                break
            hand_target[2] += .6 - gap
        targets[side] = {'foot_component_cm': target, 'hand_component_cm': hand_target,
                         'hand_thigh_min_cm': gap, 'hand_thigh_samples': overlap}
    world = _forward(local, bones)
    skin = _skin(world, prepared['prepared'])
    report = {'seat_z_cm': seat_z, 'actor_xy_cm': actor_xy, 'actor_origin_z_cm': origin_z,
              'targets': targets, 'contact_surface_coverage': 'NATIVE_FULL_PHASE_CHECK_PENDING',
              'actual_pixels_reviewed': False, 'rotation_tracks': list(TRACKS)}
    for side in ('l', 'r'):
        points = [skin[i][1] for i in prepared['contact_groups']['foot_' + side]]
        lo = [min(p[j] for p in points) + (origin_z if j == 2 else actor_xy[j]) for j in range(3)]
        hi = [max(p[j] for p in points) + (origin_z if j == 2 else actor_xy[j]) for j in range(3)]
        report['boot_' + side + '_bounds_chair_cm'] = [lo, hi]
        require(abs(lo[2] - sole_target) < .05 and all(
            floor[0][j] <= lo[j] <= hi[j] <= floor[1][j] for j in (0, 1)),
            'Actual visible boot does not fit measured footrest')
        require(.2 <= targets[side]['hand_thigh_min_cm'] <= 1.2, 'Actual hand/lap skin clearance failed')
    report['pelvis_skin_lowest_chair_z'] = min(skin[i][1][2] for i in prepared['contact_groups']['pelvis']) + origin_z
    report['historical_reference_gap_cm'] = report['pelvis_skin_lowest_chair_z'] - seat_z
    report['historical_height_is_contact_gate'] = False
    require(math.isfinite(report['pelvis_skin_lowest_chair_z']), 'Visible hip position is nonfinite')
    for name in TRACKS:
        require(local[name]['location'] == sample['bones'][name]['local']['location'] and
                local[name]['scale'] == sample['bones'][name]['local']['scale'], 'Limb translations or scales changed')
    return local, world, skin, report
