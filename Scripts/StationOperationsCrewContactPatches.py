"""Pure finite-triangle readbacks of immutable native Contact5 surfaces.

This does not import Unreal, load/export geometry, infer closed-mesh intrusion,
or turn absent cached triangles into support. Both face windings are retained.
"""
import math


def prepare(raw_rows):
    patches, indices = {}, {}
    for raw in raw_rows:
        anchor = raw['anchor']
        indices.setdefault(anchor['model'], {}).setdefault(anchor['kind'], set()).add(anchor['source_vertex'])
        for name, patch in raw['actual_triangle_patches'].items():
            if name in patches and patches[name] != patch:
                raise RuntimeError('Retained actual native triangle identity differs')
            patches[name] = patch
    if len(raw_rows) != 30 or set(indices) != {'Human', 'Robot'} or len(patches) > 80:
        raise RuntimeError('Bounded actual Contact5 samples differ')
    return {'patches': patches, 'indices': {model: {kind: sorted(values) for kind, values in kinds.items()}
                                          for model, kinds in indices.items()}}


def project(point, patch, axis):
    """Intersect an axis line with the actual FINITE triangle, or return None."""
    vertices, normal = patch['vertices_cm'], patch['normal']
    if abs(normal[axis]) < 1.e-12:
        return None
    delta = sum(normal[i] * (vertices[0][i] - point[i]) for i in range(3)) / normal[axis]
    hit = list(point)
    hit[axis] += delta
    ab = [vertices[1][i] - vertices[0][i] for i in range(3)]
    ac = [vertices[2][i] - vertices[0][i] for i in range(3)]
    ah = [hit[i] - vertices[0][i] for i in range(3)]
    dot = lambda a, b: sum(x * y for x, y in zip(a, b))
    bb, cc, bc = dot(ab, ab), dot(ac, ac), dot(ab, ac)
    denominator = bb * cc - bc * bc
    if denominator <= 0.:
        return None
    p = (cc * dot(ab, ah) - bc * dot(ac, ah)) / denominator
    q = (bb * dot(ac, ah) - bc * dot(ab, ah)) / denominator
    if min(p, q, 1. - p - q) < 0. or abs(delta) > 8.:
        return None
    return {'point_cm': hit, 'normal': normal, 'barycentric': [1.-p-q, p, q],
            'axis_gap_cm': -delta, 'signed_normal_gap_cm': -delta * normal[axis],
            'distance_cm': abs(delta)}


def sample_skin(model, skin, origin, actor_xy, prepared):
    rows = []
    for kind, indices in prepared['indices'][model].items():
        axis = 2 if kind == 'Seat' else 1
        for vertex in indices:
            component_point = skin[vertex][1]
            point = [component_point[i] + (origin if i == 2 else actor_xy[i]) for i in range(3)]
            hits = []
            for name, patch in prepared['patches'].items():
                if kind == 'Seat' and patch['region'] != 'SeatAndArms':
                    continue
                projection = project(point, patch, axis)
                if projection is not None:
                    projection.update(patch=name, triangle_id=patch['triangle_id'], region=patch['region'])
                    hits.append(projection)
            hits.sort(key=lambda row: (row['distance_cm'], row['patch']))
            facing = [row for row in hits if row['normal'][axis] >= (.7 if kind == 'Seat' else .15)]
            rows.append({'kind': kind, 'source_vertex': vertex, 'point_cm': point,
                         'nearest_finite_hit': hits[0] if hits else None,
                         'nearest_facing_hit': facing[0] if facing else None,
                         'finite_hits': hits,
                         'status': 'LIMITED_NATIVE_PATCH_READBACK' if hits else 'NO_FINITE_CACHED_SURFACE_UNKNOWN',
                         'solid_intrusion_verified': False, 'continuous_collision_verified': False})
    return rows


def summarize(reports):
    result = {'all_keys': len(reports), 'coverage': 'FINITE_RETAINED_CONTACT5_TRIANGLES_ONLY',
              'continuous_collision_verified': False, 'solid_intrusion_verified': False,
              'unknown_is_not_a_clearance_pass': True, 'kinds': {}}
    for kind in ('Seat', 'Back'):
        rows = [row for report in reports for row in report['actual_cached_surface_samples'] if row['kind'] == kind]
        known = [row['nearest_facing_hit'] for row in rows if row['nearest_facing_hit']]
        result['kinds'][kind] = {'samples': len(rows), 'facing_measured': len(known),
                                'facing_unknown': len(rows) - len(known),
                                'axis_gap_cm': [min(row['axis_gap_cm'] for row in known),
                                                max(row['axis_gap_cm'] for row in known)] if known else None,
                                'negative_axis_gap_samples': sum(row['axis_gap_cm'] < 0. for row in known)}
    return result
