"""Bounded read-only chair queries near retained actual pelvis/back skin points.

Uses the already proven regional BVH/ray APIs. The caller persists every raw
cast and native hit triangle before interpreting contact. No pose is modified.
"""
import math

from InspectStationOperationsFittedContacts4 import regions, native_api_preflight
from InspectStationOperationsCrewContacts import require

MAX_QUERIES = 96
OFFSET_CM = 2.
MAX_DISTANCE_CM = 8.


def _cast(u, bvhs, point, name, axis, sign, patches):
    mesh, bvh = bvhs[name]
    direction = [0., 0., 0.]; direction[axis] = float(sign)
    origin = list(point); origin[axis] -= sign * OFFSET_CM
    result = u.GeometryScript_MeshSpatial.find_nearest_ray_intersection_with_mesh(
        mesh, bvh, u.Vector(*origin), u.Vector(*direction),
        u.GeometryScriptSpatialQueryOptions(max_distance=MAX_DISTANCE_CM))
    require(isinstance(result, tuple) and len(result) == 3 and result[0] == mesh,
            'Proven near-body ray return schema differs')
    hit, outcome = result[1:]
    record = {'region': name, 'origin_cm': origin, 'direction': direction,
              'maximum_cm': MAX_DISTANCE_CM, 'hit': None}
    if not hit.hit:
        require(outcome == u.GeometryScriptSearchOutcomePins.NOT_FOUND, 'Native near-body miss outcome differs')
        return record
    require(outcome == u.GeometryScriptSearchOutcomePins.FOUND and
            0. <= hit.ray_parameter <= MAX_DISTANCE_CM, 'Native near-body hit outcome/range differs')
    position = list(hit.hit_position.to_tuple())
    require(math.dist(position, [origin[j]+direction[j]*hit.ray_parameter for j in range(3)]) < .003,
            'Native near-body hit position differs from actual ray parameter')
    key = name+':'+str(int(hit.hit_triangle_id))
    if key not in patches:
        triangle = u.GeometryScript_MeshQueries.get_triangle_positions(mesh, int(hit.hit_triangle_id))
        normal = u.GeometryScript_MeshQueries.get_triangle_face_normal(mesh, int(hit.hit_triangle_id))
        require(isinstance(triangle, tuple) and len(triangle) == 4 and triangle[0] is True and
                isinstance(normal, tuple) and len(normal) == 2 and normal[1] is True,
                'Actual near-body triangle/normal return schema differs')
        patches[key] = {'region': name, 'triangle_id': int(hit.hit_triangle_id),
                        'normal': list(normal[0].to_tuple()),
                        'vertices_cm': [list(v.to_tuple()) for v in triangle[1:]]}
    record['hit'] = {'patch': key, 'point_cm': position, 'distance_cm': float(hit.ray_parameter)}
    return record


def classify(anchor, casts, patches):
    axis = 2 if anchor['kind'] == 'Seat' else 1
    facing = .7 if anchor['kind'] == 'Seat' else .15
    candidates = []
    for cast in casts:
        hit = cast['hit']
        if hit is None:
            continue
        normal = patches[hit['patch']]['normal']
        if normal[axis] < facing:
            continue
        point = hit['point_cm']; body = anchor['point_cm']
        candidates.append({'patch': hit['patch'], 'point_cm': point, 'normal': normal,
            'distance_from_skin_cm': math.dist(body, point),
            'axis_gap_cm': body[axis]-point[axis],
            'signed_normal_gap_cm': sum((body[j]-point[j])*normal[j] for j in range(3))})
    chosen = min(candidates, key=lambda r: r['distance_from_skin_cm']) if candidates else None
    return {'anchor': anchor, 'nearest_facing_hit': chosen,
            'status': 'NEARBY_FACING_SURFACE' if chosen else 'NO_FACING_NEARBY_SURFACE_UNKNOWN',
            'cushion_identity_verified': False, 'solid_mesh_intrusion_verified': False}


def collect(plan, u):
    source, bvhs, regions_readback = yield from regions(u)
    rows, patches, queries = [], {}, 0
    require(len(plan['anchors']) == 30 and plan['native_ray_count'] == 80,
            'Frozen near-body point/cast population differs')
    for ordinal, anchor in enumerate(plan['anchors']):
        axis = 2 if anchor['kind'] == 'Seat' else 1
        names = ('SeatAndArms',) if anchor['kind'] == 'Seat' else ('SeatAndArms', 'BackContact')
        casts = []
        for name in names:
            for sign in (-1., 1.):
                require(queries < MAX_QUERIES, 'Strict96 near-body native-query budget exceeded')
                casts.append(_cast(u, bvhs, anchor['point_cm'], name, axis, sign, patches)); queries += 1
        raw = {'anchor': anchor, 'casts': casts,
               'actual_triangle_patches': {cast['hit']['patch']: patches[cast['hit']['patch']]
                                           for cast in casts if cast['hit']}}
        yield {'stage': 'RAW_NEAR_BODY_CASTS', 'artifact_name': 'Anchor'+str(ordinal).zfill(2),
               'artifact_data': raw, 'details': {'anchor': ordinal, 'queries': queries, 'patches': len(patches)}}
        # The caller has persisted every raw cast/triangle before interpreting it.
        rows.append(classify(anchor, casts, patches))
    require(queries == 80 and source.get_triangle_count() == 1382533 and all(
        bvhs[row['name']][0].get_triangle_count() == row['triangles'] for row in regions_readback),
        'Native query population or source geometry changed')
    result = {'success': True, 'read_only': True, 'saved': False, 'rows': rows,
              'queries': queries, 'native_query_cap': MAX_QUERIES, 'source_counts':
              {'vertices': 691725, 'triangles': 1382533}, 'regions': regions_readback,
              'full_skin_export_repeated': False, 'continuous_collision_verified': False,
              'contact_fit_pass': False, 'limits': [
                  'Five native source-key phases reuse actual occupied pelvis/back points from Contact4.',
                  'Short bidirectional casts avoid the distant overhead hardware; misses remain unknown.',
                  'Native facing triangles and skin gaps require physical/visual interpretation before saving.',
                  'Neither all-skin support nor continuous collision is required or established for cosmetic NPCs.']}
    yield {'stage': 'NEAR_BODY_CONTACT_RESULT', 'result': result,
           'details': {'queries': queries, 'patches': len(patches), 'raw_anchors': len(rows)}}
