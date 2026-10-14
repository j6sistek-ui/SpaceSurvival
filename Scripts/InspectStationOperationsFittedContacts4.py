"""Read-only actual chair contact samples for the reviewed121-key crew fit.

The native dense chair remains intact. Two proven regional copies retain the
existing1M BVH cap. Full weighted skins select occupied12cm contact cells; ray
hits are persisted by the caller BEFORE contact decisions. This is sampled
surface evidence, not continuous mesh-intersection or owner acceptance.
"""
import math

import FitStationOperationsCrew as fitter
from InspectStationOperationsCrewContacts import geometry, path, transform, require
from InspectStationOperationsCrewContacts2 import spatial_api_preflight
from PreviewStationOperationsCrew4 import support

SOURCE = '/Game/P1toP5_Bundle/P3_ComputerStation/Meshes/SM_TitaniumIndustrySeat_V1_Part2.SM_TitaniumIndustrySeat_V1_Part2'
EXPECTED_COUNTS = {'vertices': 691725, 'triangles': 1382533}
MAX_BVH_TRIANGLES = 1000000
MAX_HIT_TRIANGLES = 2000
MAX_QUERIES = 24000
CELL_CM = 12.


def resolve(u, class_name, cpp_name):
    """Require one actual registered Python export, without guessed spelling."""
    cls = getattr(u, class_name, None)
    require(cls is not None, 'Native geometry class unavailable: ' + class_name)
    wanted = cpp_name.replace('_', '').lower()
    names = [name for name in dir(cls) if name.replace('_', '').lower() == wanted
             and callable(getattr(cls, name, None))]
    require(len(names) == 1, 'Require exactly one registered native export: ' + cpp_name)
    method = getattr(cls, names[0])
    return method, {'class': class_name, 'cpp_name': cpp_name,
                    'python_name': names[0], 'doc': str(method.__doc__)}


def native_api_preflight(u):
    select, selected = resolve(u, 'GeometryScript_MeshSelection', 'SelectMeshElementsInBox')
    extract, extracted = resolve(u, 'GeometryScript_MeshDecomposition', 'CopyMeshSelectionToMesh')
    methods = {cls + '.' + name: callable(getattr(getattr(u, cls, None), name, None))
               for cls, names in {
                   'GeometryScript_MeshSelection': ('get_mesh_selection_info',),
                   'GeometryScript_MeshQueries': ('get_mesh_bounding_box',),
                   'AnimPoseExtensions': ('get_anim_pose_at_time', 'get_bone_pose'),
                   'MathLibrary': ('transform_location', 'inverse_transform_location'),
               }.items() for name in names}
    require(all(methods.values()), 'Actual fitted-contact methods unavailable')
    source, target = u.DynamicMesh(), u.DynamicMesh()
    pair = select(source, u.Box(min=u.Vector(-1, -1, -1), max=u.Vector(1, 1, 1)),
                  selection_type=u.GeometryScriptMeshSelectionType.TRIANGLES, min_num_triangle_points=1)
    require(isinstance(pair, tuple) and len(pair) == 2 and pair[0] == source,
            'Actual empty native box selection tuple differs')
    info = u.GeometryScript_MeshSelection.get_mesh_selection_info(pair[1])
    require(info == (u.GeometryScriptMeshSelectionType.TRIANGLES, 0),
            'Actual empty native box-selection info differs')
    copied = extract(source, target, pair[1])
    require(isinstance(copied, tuple) and len(copied) == 3 and copied[0] == source and
            copied[1] == target and copied[2] is None and target.get_triangle_count() == 0,
            'Actual empty native selection copy differs')
    return {'selection': selected, 'extraction': extracted, 'methods': methods,
            'empty_native_selection_copy_pass': True, 'spatial': spatial_api_preflight(u)}


def regions(u):
    yield {'stage': 'BEFORE_NATIVE_CHAIR_CONTACT_COPY', 'details': {'mesh': SOURCE}}
    mesh = u.load_asset(SOURCE)
    require(isinstance(mesh, u.StaticMesh), 'Exact Part2 contact mesh missing')
    source, counts = geometry(mesh, False, u)
    require(counts == EXPECTED_COUNTS, 'Exact measured Part2 source counts differ')
    bounds = u.GeometryScript_MeshQueries.get_mesh_bounding_box(source)
    lo, hi = list(bounds.min.to_tuple()), list(bounds.max.to_tuple())
    require(all(math.isfinite(v) for v in lo + hi) and all(a < b for a, b in zip(lo, hi)),
            'Actual native contact-source bounds invalid')
    yield {'stage': 'ACTUAL_CHAIR_SOURCE_COUNTS', 'details': {**counts, 'bounds_cm': [lo, hi]}}
    select, _ = resolve(u, 'GeometryScript_MeshSelection', 'SelectMeshElementsInBox')
    extract, _ = resolve(u, 'GeometryScript_MeshDecomposition', 'CopyMeshSelectionToMesh')
    result, records = {}, []
    for name, minimum, maximum, expected in (
            ('SeatAndArms', [-45., -25., 40.], [45., 65., 115.], 353314),
            ('BackContact', [-35., -35., 100.], [35., 15., hi[2] + 1.], 298816)):
        pair = select(source, u.Box(min=u.Vector(*minimum), max=u.Vector(*maximum)),
                      selection_type=u.GeometryScriptMeshSelectionType.TRIANGLES, min_num_triangle_points=1)
        require(isinstance(pair, tuple) and len(pair) == 2 and pair[0] == source,
                'Actual contact-region selection tuple differs')
        kind, count = u.GeometryScript_MeshSelection.get_mesh_selection_info(pair[1])
        require(kind == u.GeometryScriptMeshSelectionType.TRIANGLES and
                count == expected and 0 < count <= MAX_BVH_TRIANGLES,
                'Exact measured regional count or unchanged1M native budget differs')
        subset = u.DynamicMesh(); copied = extract(source, subset, pair[1])
        require(isinstance(copied, tuple) and len(copied) == 3 and copied[0] == source and
                copied[1] == subset and (copied[2] is None or copied[2] == subset) and
                subset.get_triangle_count() == count and source.get_triangle_count() == counts['triangles'],
                'Native region copy changed source/count/identity')
        record = {'name': name, 'box_cm': [minimum, maximum], 'triangles': int(count)}
        records.append(record)
        yield {'stage': 'BEFORE_BOUNDED_CONTACT_BVH', 'details': record}
        built = u.GeometryScript_MeshSpatial.build_bvh_for_mesh(subset)
        require(isinstance(built, tuple) and len(built) == 2 and built[0] == subset,
                'Actual native contact BVH tuple differs')
        result[name] = (subset, built[1])
        yield {'stage': 'BOUNDED_CONTACT_BVH_READY', 'details': record}
    return source, result, records


def anchors(skin, prepared, fitted):
    """Lowest occupied XY cells / rearmost occupied XZ cells of actual full skin."""
    cells = {}
    for index, (_, point) in enumerate(skin):
        group = prepared['groups'][index]
        chair = [point[j] + (fitted['actor_origin_z_cm'] if j == 2 else fitted['actor_xy_cm'][j])
                 for j in range(3)]
        if group in ('pelvis', 'thigh_l', 'thigh_r'):
            role, axes, extreme = 'Seat', (0, 1), 2
        elif group in ('spine_01', 'spine_02', 'spine_03'):
            role, axes, extreme = 'Back', (0, 2), 1
        elif group in ('lowerarm_l', 'lowerarm_r', 'hand_l', 'hand_r'):
            role, axes, extreme = 'ArmClearance', (0, 1), 2
        else:
            continue
        key = (role, group, *(math.floor(chair[j] / CELL_CM) for j in axes))
        if key not in cells or chair[extreme] < cells[key]['point_cm'][extreme]:
            cells[key] = {'kind': role, 'body_region': group, 'source_vertex': index,
                          'cell': list(key[2:]), 'point_cm': chair}
    require(all(any(row['kind'] == kind for row in cells.values()) for kind in
                ('Seat', 'Back', 'ArmClearance')), 'Full actual fitted contact anchors unavailable')
    return [cells[key] for key in sorted(cells)]


def ray(u, bvhs, anchor, cache):
    point, kind = anchor['point_cm'], anchor['kind']
    direction = [0., -1., 0.] if kind == 'Back' else [0., 0., -1.]
    origin = [point[j] - direction[j] * 40. for j in range(3)]
    candidates = []
    names = ('SeatAndArms', 'BackContact') if kind == 'Back' else ('SeatAndArms',)
    for name in names:
        mesh, bvh = bvhs[name]
        value = u.GeometryScript_MeshSpatial.find_nearest_ray_intersection_with_mesh(
            mesh, bvh, u.Vector(*origin), u.Vector(*direction),
            u.GeometryScriptSpatialQueryOptions(max_distance=100.))
        require(isinstance(value, tuple) and len(value) == 3 and value[0] == mesh,
                'Actual fitted-contact ray tuple differs')
        hit, outcome = value[1:]
        if not hit.hit:
            require(outcome == u.GeometryScriptSearchOutcomePins.NOT_FOUND, 'Actual ray miss outcome differs')
            continue
        require(outcome == u.GeometryScriptSearchOutcomePins.FOUND and 0. <= hit.ray_parameter <= 100.,
                'Actual fitted-contact native hit distance/outcome differs')
        position = list(hit.hit_position.to_tuple())
        require(math.dist(position, [origin[j] + direction[j] * hit.ray_parameter for j in range(3)]) < .003,
                'Actual native fitted-contact ray point disagrees with parameter')
        key = name + ':' + str(int(hit.hit_triangle_id))
        if key not in cache:
            tri = u.GeometryScript_MeshQueries.get_triangle_positions(mesh, int(hit.hit_triangle_id))
            normal = u.GeometryScript_MeshQueries.get_triangle_face_normal(mesh, int(hit.hit_triangle_id))
            require(isinstance(tri, tuple) and len(tri) == 4 and tri[0] is True and
                    isinstance(normal, tuple) and len(normal) == 2 and normal[1] is True,
                    'Actual contact-hit native triangle or normal invalid')
            cache[key] = {'region': name, 'triangle_id': int(hit.hit_triangle_id),
                          'normal': list(normal[0].to_tuple()),
                          'vertices_cm': [list(v.to_tuple()) for v in tri[1:]]}
        require(len(cache) <= MAX_HIT_TRIANGLES, 'Actual hit patches exceed unchanged2000 budget')
        candidates.append({'patch': key, 'point_cm': position, 'distance_cm': float(hit.ray_parameter)})
    hit = min(candidates, key=lambda row: row['distance_cm']) if candidates else None
    # Decisions are deliberately deferred until this raw sample has been written.
    return {**anchor, 'origin_cm': origin, 'direction': direction, 'maximum_cm': 100., 'hit': hit}


def decisions(samples, patches):
    """No numeric tolerance: retain negative signed gaps, misses and side normals."""
    rows, missing, intrusion = [], [], []
    for row in samples:
        hit = row['hit']; axis = 1 if row['kind'] == 'Back' else 2
        if hit is None:
            missing.append({'kind': row['kind'], 'vertex': row['source_vertex'], 'reason': 'RAY_MISS_UNKNOWN'})
            continue
        normal = patches[hit['patch']]['normal']
        if normal[axis] < .15:
            missing.append({'kind': row['kind'], 'vertex': row['source_vertex'],
                            'reason': 'HIT_NOT_FACING_BODY', 'normal': normal})
            continue
        signed = sum((row['point_cm'][j] - hit['point_cm'][j]) * normal[j] for j in range(3))
        result = {'kind': row['kind'], 'body_region': row['body_region'], 'vertex': row['source_vertex'],
                  'signed_normal_gap_cm': signed, 'axis_gap_cm': row['point_cm'][axis] - hit['point_cm'][axis]}
        rows.append(result)
        if signed < 0.:
            intrusion.append(result)
    seat = [row for row in rows if row['kind'] == 'Seat']
    return {'measured': rows, 'unmeasured': missing, 'negative_signed_gaps': intrusion,
            'seat_min_gap_cm': min((row['axis_gap_cm'] for row in seat), default=None),
            'contact_sample_count': len(samples), 'measured_count': len(rows),
            'sampled_no_intrusion': bool(seat) and not missing and not intrusion,
            'continuous_collision_verified': False}


def collect(data, actors, u):
    source, bvhs, records = yield from regions(u)
    patches, summaries, queries = {}, {}, 0
    for model_name, station in (('Human', 'Port South'), ('Robot', 'Starboard South')):
        model = data['models'][model_name]
        mesh, clip = u.load_asset(model['mesh']), u.load_asset(model['clip'])
        require(isinstance(mesh, u.SkeletalMesh) and isinstance(clip, u.AnimSequence) and
                path(mesh.get_editor_property('skeleton')) == model['skeleton'] ==
                path(clip.get_editor_property('skeleton')), 'Exact source mesh/clip/skeleton differs')
        native = clip.get_editor_property('data_model_interface')
        require(native.get_number_of_keys() == 121 and float(clip.sequence_length) == 4.,
                'Retain actual121-key/four-second source')
        measured = support(data, actors, station, u)
        measured['hand_front_cm'] = 16. if model_name == 'Human' else 20.
        prepared, origin, reports = fitter.setup(model), None, []
        options = u.AnimPoseEvaluationOptions(optional_skeletal_mesh=mesh, evaluation_type=u.AnimDataEvalType.RAW)
        for frame in range(121):
            seconds = 4. * frame / 120.
            pose = u.AnimPoseExtensions.get_anim_pose_at_time(clip, seconds, options)
            sample = {'seconds': seconds, 'bones': {bone['name']: {
                'local': transform(u.AnimPoseExtensions.get_bone_pose(pose, bone['name'], u.AnimPoseSpaces.LOCAL)),
                'world': transform(u.AnimPoseExtensions.get_bone_pose(pose, bone['name'], u.AnimPoseSpaces.WORLD))}
                for bone in model['geometry']['bones']}}
            _, _, skin, fitted = fitter.fit(model, sample, measured, prepared, origin)
            origin = fitted['actor_origin_z_cm']; points = anchors(skin, prepared, fitted)
            require(queries + len(points) <= MAX_QUERIES, 'Strict24000 actual anchor-query budget exceeded')
            rows = [ray(u, bvhs, point, patches) for point in points]; queries += len(rows)
            raw = {'model': model_name, 'frame': frame, 'seconds': seconds, 'fit': fitted,
                   'cell_cm': CELL_CM, 'full_skin_vertices': len(skin), 'anchors': rows,
                   'actual_triangle_patches': {row['hit']['patch']: patches[row['hit']['patch']]
                                              for row in rows if row['hit']}}
            yield {'stage': 'ACTUAL_RAW_CONTACT_' + model_name.upper(),
                   'artifact_name': model_name + '_Frame' + str(frame).zfill(3), 'artifact_data': raw,
                   'details': {'frame': frame, 'queries': queries, 'anchors': len(rows), 'patches': len(patches)}}
            # The caller has now retained all raw points/normals even if this evaluation fails.
            decision = decisions(rows, patches); decision.update(frame=frame, seconds=seconds)
            reports.append(decision)
            yield {'stage': 'CONTACT_DECISION_' + model_name.upper(), 'details': {
                'frame': frame, 'measured': decision['measured_count'],
                'unknown': len(decision['unmeasured']), 'negative_gaps': len(decision['negative_signed_gaps'])}}
        summaries[model_name] = {'keys': 121, 'source_clip': path(clip), 'source_mesh': path(mesh),
                                 'support': measured, 'frames': reports,
                                 'sampled_no_intrusion': all(row['sampled_no_intrusion'] for row in reports)}
    require(source.get_triangle_count() == EXPECTED_COUNTS['triangles'] and all(
        bvhs[row['name']][0].get_triangle_count() == row['triangles'] for row in records),
        'Actual source or regional geometry changed during contact measurement')
    result = {'success': True, 'read_only': True, 'saved': False, 'models': summaries,
              'regions': records, 'source_counts': EXPECTED_COUNTS, 'queries': queries,
              'actual_hit_triangles': len(patches), 'full_source_skin_reused': True,
              'contact_fit_pass': all(row['sampled_no_intrusion'] for row in summaries.values()),
              'continuous_collision_verified': False, 'scene_saved': False,
              'limits': ['Occupied12cm full-skin cells are sampled at every one of121 source keys; unsampled intersections remain unmeasured.',
                         'Ray misses and surfaces not facing the body remain UNKNOWN, never safe clearance.',
                         'Hands remain lap idle; armrests are checked for clearance, not required hand contact.',
                         'Dense desk contact and continuous between-key collision are not proved by this chair-only diagnostic.',
                         'No model, animation, material, actor or map is modified or saved.']}
    yield {'stage': 'FITTED_CHAIR_CONTACT_RESULT', 'result': result, 'details': {
        'queries': queries, 'patches': len(patches), 'contact_fit_pass': result['contact_fit_pass']}}
