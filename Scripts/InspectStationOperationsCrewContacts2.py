"""Read-only full candidate skin first, then bounded native chair support queries.

Dense chair geometry remains native. Only actual ray hit triangles are exported.
Support samples are fitting input, not continuous chair/body clearance or pixels.
The caller advances collect once per tick and preserves independent artifacts.
"""
import math
import traceback
import InspectStationOperationsCrewContacts as base
from RefineStationSocialSeatedCrew import _forward

require, path, transform = base.require, base.path, base.transform
geometry, arrays = base.geometry, base.arrays
MODELS, MAP = base.MODELS, base.MAP
WEIGHTS_PER_TICK = base.WEIGHTS_PER_TICK
RAYS_PER_TICK = 24
MAX_HIT_TRIANGLES = 2000
# Native source stays in its BVH; this never raises the200k Python array budget.
MAX_BVH_TRIANGLES = 1000000


def spatial_api_preflight(u):
    methods = {
        'GeometryScript_MeshSpatial': ('build_bvh_for_mesh', 'find_nearest_ray_intersection_with_mesh'),
        'GeometryScript_MeshQueries': ('get_triangle_positions', 'get_triangle_face_normal'),
    }
    checks = {cls + '.' + name: callable(getattr(getattr(u, cls, None), name, None))
              for cls, names in methods.items() for name in names}
    result = {'methods': checks, 'docs': {key: str(getattr(getattr(u, key.split('.')[0]),
             key.split('.')[1]).__doc__) if ok else None for key, ok in checks.items()}}
    require(all(checks.values()), 'Native BVH/ray/triangle API unavailable')
    empty = u.DynamicMesh()
    built = u.GeometryScript_MeshSpatial.build_bvh_for_mesh(empty)
    require(isinstance(built, tuple) and len(built) == 2 and built[0] == empty,
            'Native empty BVH tuple schema differs')
    ray = u.GeometryScript_MeshSpatial.find_nearest_ray_intersection_with_mesh(
        empty, built[1], u.Vector(0, 0, 1), u.Vector(0, 0, -1), u.GeometryScriptSpatialQueryOptions(max_distance=2.))
    require(isinstance(ray, tuple) and len(ray) == 3 and ray[0] == empty and not ray[1].hit and
            ray[2] == u.GeometryScriptSearchOutcomePins.NOT_FOUND, 'Native empty ray tuple/outcome differs')
    tri = u.GeometryScript_MeshQueries.get_triangle_positions(empty, -1)
    normal = u.GeometryScript_MeshQueries.get_triangle_face_normal(empty, -1)
    require(isinstance(tri, tuple) and len(tri) == 4 and tri[0] is False and
            all(isinstance(v, u.Vector) for v in tri[1:]) and
            isinstance(normal, tuple) and len(normal) == 2 and isinstance(normal[0], u.Vector) and normal[1] is False,
            'Native empty triangle/normal tuple schema differs')
    require(isinstance(ray[1].hit_position, u.Vector) and isinstance(ray[1].hit_triangle_id, int) and
            math.isfinite(float(ray[1].ray_parameter)), 'Native ray-hit field schema differs')
    result.update(empty_bvh=True, empty_ray=True, empty_triangle=True, empty_normal=True)
    return result


def native_api_preflight(u):
    result = {'skin': base.native_api_preflight(u)}
    try:
        result['spatial'] = spatial_api_preflight(u)
    except Exception:
        # An unrelated new spatial contract may not suppress model skin evidence.
        result['spatial_error'] = traceback.format_exc()
    return result


def _model(kind, package, npc, candidates, output, u):
    expected = next(r for r in candidates['candidate_evidence'] if r['kind'] == kind)
    native = next(r for r in npc['candidates'] if r['mesh'].split('.')[0] == package)
    yield {'stage': 'BEFORE_' + kind.upper() + '_SOURCE_COPY', 'details': {'mesh': package}}
    mesh, clip = u.load_asset(package), u.load_asset(expected['clip'])
    require(isinstance(mesh, u.SkeletalMesh) and isinstance(clip, u.AnimSequence) and
            path(mesh) == expected['mesh'] and path(mesh.skeleton) == native['skeleton'] == expected['skeleton'] and
            clip.get_editor_property('skeleton') == mesh.skeleton and
            float(clip.sequence_length) == expected['duration_seconds'] == 4., 'Exact private seated candidate changed')
    output['source_packages'].extend((path(mesh), path(mesh.skeleton), path(clip)))
    dynamic, counts = geometry(mesh, True, u)
    yield {'stage': kind.upper() + '_NATIVE_COUNTS', 'details': {'mesh': path(mesh), **counts}}
    data = arrays(dynamic, counts, u)
    _, bones = u.GeometryScript_BoneWeights.get_all_bones_info(dynamic)
    data['bones'] = [{'index': int(b.index), 'parent': int(b.parent_index), 'name': str(b.name),
                      'reference_world': transform(b.world_transform)} for b in bones]
    require(0 < len(bones) < 500 and len({b['index'] for b in data['bones']}) == len(bones),
            'Source weighted bone inventory differs')
    valid_bones = {b['index'] for b in data['bones']}; data['weights'] = []
    yield {'stage': kind.upper() + '_RAW_GEOMETRY_READY', 'artifact_name': kind + 'RawGeometry',
           'artifact_data': data, 'details': {'mesh': path(mesh), **counts, 'bones': len(bones)}}
    for first in range(0, counts['vertices'], WEIGHTS_PER_TICK):
        for index in range(first, min(first + WEIGHTS_PER_TICK, counts['vertices'])):
            _, weights, valid = u.GeometryScript_BoneWeights.get_vertex_bone_weights(dynamic, index)
            total = sum(float(w.weight) for w in weights)
            require(valid and weights and math.isfinite(total) and abs(total - 1.) < .002 and
                    all(w.bone_index in valid_bones and math.isfinite(w.weight) and w.weight >= 0. for w in weights),
                    'Native full skin weight is invalid at vertex ' + str(index))
            data['weights'].append([[int(w.bone_index), float(w.weight / total)] for w in weights])
        yield {'stage': kind.upper() + '_FULL_SKIN_WEIGHT_CHUNK',
               'details': {'vertices_complete': len(data['weights']), 'vertices_total': counts['vertices']}}
    require(len(data['weights']) == len(data['vertices']), 'No source skin vertices may be omitted')
    options = u.AnimPoseEvaluationOptions(optional_skeletal_mesh=mesh, evaluation_type=u.AnimDataEvalType.RAW)
    api = u.AnimPoseExtensions; samples = []
    for fraction in (0., .25, .5, .75, 1.):
        seconds = float(clip.sequence_length) * fraction
        pose = api.get_anim_pose_at_time(clip, seconds, options)
        names = {b['name'] for b in data['bones']}
        require(names <= set(map(str, api.get_bone_names(pose))), 'Seated native pose lacks source weighted bones')
        sample = {'seconds': seconds, 'bones': {name: {
            'local': transform(api.get_bone_pose(pose, name, u.AnimPoseSpaces.LOCAL)),
            'world': transform(api.get_bone_pose(pose, name, u.AnimPoseSpaces.WORLD))} for name in sorted(names)}}
        rebuilt = _forward({name: row['local'] for name, row in sample['bones'].items()}, data['bones'])
        error = max(math.dist(rebuilt[name]['location'], row['world']['location'])
                    for name, row in sample['bones'].items())
        require(error < .005, 'Native/offline raw pose transform convention differs')
        sample['native_reconstruction_max_cm'] = error; samples.append(sample)
        yield {'stage': kind.upper() + '_RAW_NATIVE_POSE_READY', 'details': {'seconds': seconds, 'error_cm': error}}
    output['models'][kind] = {'mesh': path(mesh), 'skeleton': path(mesh.skeleton), 'clip': path(clip),
        'native_height_cm': float(mesh.get_bounds().box_extent.z) * 2., 'geometry': data,
        'animation': {'duration_seconds': float(clip.sequence_length), 'samples': samples}}
    yield {'stage': kind.upper() + '_FULL_SKIN_AND_POSES_READY', 'artifact_name': kind + 'FullContactSource',
           'artifact_data': output['models'][kind], 'details': {'vertices': counts['vertices'], 'samples': 5}}


def _chair(package, output, u):
    yield {'stage': 'BEFORE_CHAIR_NATIVE_BVH_SOURCE_COPY', 'details': {'mesh': package}}
    mesh = u.load_asset(package)
    require(isinstance(mesh, u.StaticMesh), 'Exact current chair source missing')
    dynamic, counts = geometry(mesh, False, u)
    yield {'stage': 'CHAIR_NATIVE_COUNTS', 'details': {'mesh': package, **counts}}
    require(0 < counts['triangles'] <= MAX_BVH_TRIANGLES, 'Native BVH source exceeds bounded query budget')
    built = u.GeometryScript_MeshSpatial.build_bvh_for_mesh(dynamic)
    require(isinstance(built, tuple) and len(built) == 2 and built[0] == dynamic, 'Actual chair BVH tuple differs')
    bvh = built[1]
    yield {'stage': 'CHAIR_NATIVE_BVH_READY', 'details': {'mesh': package, **counts}}
    # Common native chair coordinates: retained seat centre(0,10), front+Y.
    # This357-ray grid surveys support; unqueried space stays UNKNOWN.
    queries = [(float(x), float(y)) for x in range(-40, 41, 5) for y in range(-30, 71, 5)]
    samples, hits = [], {}
    options = u.GeometryScriptSpatialQueryOptions(max_distance=250.)
    for first in range(0, len(queries), RAYS_PER_TICK):
        for x, y in queries[first:first + RAYS_PER_TICK]:
            origin = u.Vector(x, y, 170.)
            result = u.GeometryScript_MeshSpatial.find_nearest_ray_intersection_with_mesh(
                dynamic, bvh, origin, u.Vector(0, 0, -1), options)
            require(isinstance(result, tuple) and len(result) == 3 and result[0] == dynamic,
                    'Actual chair native ray tuple differs')
            hit, outcome = result[1:]
            sample = {'origin_cm': [x, y, 170.], 'direction': [0., 0., -1.], 'hit': bool(hit.hit)}
            if hit.hit:
                require(outcome == u.GeometryScriptSearchOutcomePins.FOUND and
                        math.isfinite(float(hit.ray_parameter)) and 0. <= hit.ray_parameter <= 250.,
                        'Actual chair ray outcome/distance differs')
                identity = int(hit.hit_triangle_id)
                require(identity >= 0, 'Chair hit triangle is invalid')
                point = list(hit.hit_position.to_tuple())
                require(math.dist(point, [x, y, 170. - float(hit.ray_parameter)]) < .003,
                        'Native chair hit position/distance differs')
                if identity not in hits:
                    tri = u.GeometryScript_MeshQueries.get_triangle_positions(dynamic, identity)
                    normal = u.GeometryScript_MeshQueries.get_triangle_face_normal(dynamic, identity)
                    require(isinstance(tri, tuple) and len(tri) == 4 and tri[0] is True and
                            isinstance(normal, tuple) and len(normal) == 2 and normal[1] is True,
                            'Actual native chair hit triangle/normal is invalid')
                    hits[identity] = {'triangle_id': identity, 'vertices': [list(v.to_tuple()) for v in tri[1:]],
                                      'normal': list(normal[0].to_tuple())}
                sample.update(point_cm=point, distance_cm=float(hit.ray_parameter), triangle_id=identity)
            else:
                require(outcome == u.GeometryScriptSearchOutcomePins.NOT_FOUND, 'Native chair miss outcome differs')
            samples.append(sample)
        require(len(hits) <= MAX_HIT_TRIANGLES, 'Actual hit-triangle export exceeds bounded patch budget')
        yield {'stage': 'CHAIR_SUPPORT_RAY_CHUNK', 'details': {'mesh': package, 'queries_complete': len(samples),
                                                            'queries_total': len(queries), 'hit_triangles': len(hits)}}
    require(dynamic.get_triangle_count() == counts['triangles'], 'Chair source transient geometry changed during queries')
    data = {'mesh': package, 'native_source_counts': counts, 'source_model_unchanged': True,
            'samples': samples, 'actual_hit_triangles': list(hits.values()),
            'continuous_contact_coverage': False, 'all_chair_triangles_exported': False,
            'limits': ['Only357 actual vertical rays and their hit triangles are measured.',
                       'Native per-frame visible skin/support/desk contact and actual pixels remain mandatory.']}
    output['fixtures'][package] = data; output['source_packages'].append(package)
    yield {'stage': 'CHAIR_SAMPLED_SUPPORT_READY', 'artifact_name': 'Chair' + str(len(output['fixtures'])),
           'artifact_data': data, 'details': {'mesh': package, 'samples': len(samples), 'hit_triangles': len(hits)}}


def collect(npc, candidates, u):
    """Yield bounded read-only stages, raw artifacts and one final serializable result."""
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    eas = u.get_editor_subsystem(u.EditorActorSubsystem)
    world = editor.get_editor_world()
    require(world and world.get_path_name().split('.')[0] == MAP and not editor.get_game_world(),
            'Require exact saved owner editor map outside PIE')
    actors = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
    output = {'scope': 'FULL_TWO_MODEL_SKIN_WEIGHTS_FIVE_NATIVE_POSES_AND_SAMPLED_NATIVE_CHAIR_SUPPORT',
              'read_only': True, 'saved': False, 'models': {}, 'chairs': [], 'footrests': [], 'operators': [],
              'fixtures': {}, 'desk_hardware': [], 'source_packages': [], 'contacts_fitted': False, 'section_errors': [],
              'limits': ['Full source skin weights and native pose reconstruction are authoring inputs only.',
                         'No actor replacement, pose write, material change, fitting or level save occurs.',
                         'Actual seated skin contact and rendered desk/body silhouette remain unverified.']}
    for expected in npc['current_crew']:
        actor = actors.get(expected['label'])
        component = actor.get_component_by_class(u.SkeletalMeshComponent) if actor else None
        require(actor and path(actor) == expected['actor'] and transform(actor.get_actor_transform()) == expected['pose'] and
                component and path(component.get_skeletal_mesh_asset()) == expected['mesh'] and
                transform(component.get_relative_transform()) == expected['mesh_relative_transform'] and
                path(actor.get_editor_property('idle_animation')) == expected['idle']['asset'] and
                not actor.get_editor_property('route_points') and not actor.get_editor_property('gesture_animations'),
                'Unchanged actual seated operator differs: ' + expected['label'])
        output['operators'].append({'label': expected['label'], 'actor': path(actor),
                                   'actor_transform': transform(actor.get_actor_transform()),
                                   'mesh_transform': transform(component.get_world_transform())})
    for expected in npc['seat_hardware']:
        actor = actors.get(expected['label'])
        component = actor.get_component_by_class(u.StaticMeshComponent) if actor else None
        require(actor and path(actor) == expected['actor'] and transform(actor.get_actor_transform()) == expected['pose'] and
                component and path(component.static_mesh) == expected['mesh'], 'Native chair/source identity differs')
        output['chairs'].append({'label': expected['label'], 'actor': path(actor), 'mesh': path(component.static_mesh),
            'world_transform': transform(component.get_world_transform()),
            'collision': str(component.get_collision_enabled()), 'materials': [path(m) for m in component.get_materials()]})
    require(len(output['chairs']) == 12, 'All four actual three-part chairs are required')
    for name in ('Port North', 'Port South', 'Starboard North', 'Starboard South'):
        label = 'Refine/Operations/' + name + '/Footrest'
        actor = actors.get(label); component = actor.get_component_by_class(u.StaticMeshComponent) if actor else None
        require(actor and component and path(component.static_mesh) == '/Engine/BasicShapes/Cube.Cube',
                'Existing actual footrest source missing: ' + label)
        output['footrests'].append({'label': label, 'actor': path(actor), 'mesh': path(component.static_mesh),
            'world_transform': transform(component.get_world_transform()),
            'collision': str(component.get_collision_enabled())})
    yield {'stage': 'CURRENT_FOUR_CHAIRS_OPERATORS_AND_FOOTRESTS_MEASURED',
           'details': {'chairs': 12, 'operators': 4, 'footrests': 4}}
    for name in ('Port North', 'Port South', 'Starboard North', 'Starboard South'):
        label = 'OperationsNative/Command island ' + name + '/SM_TitaniumIndustryStation_V1_Part1'
        actor = actors.get(label); component = actor.get_component_by_class(u.StaticMeshComponent) if actor else None
        require(actor and component and path(component.static_mesh) ==
                '/Game/P1toP5_Bundle/P3_ComputerStation/Meshes/SM_TitaniumIndustryStation_V1_Part1.SM_TitaniumIndustryStation_V1_Part1',
                'Existing four complete native desk bodies differ')
        output['desk_hardware'].append({'label': label, 'actor': path(actor), 'mesh': path(component.static_mesh),
            'world_transform': transform(component.get_world_transform()),
            'collision': str(component.get_collision_enabled()), 'materials': [path(m) for m in component.get_materials()],
            'triangle_contact_status': 'NOT_EXPORTED_OR_FITTED'})
    # Human and robot are independent and FIRST. A dense fixture cannot discard them.
    for kind, package in MODELS.items():
        try:
            yield from _model(kind, package, npc, candidates, output, u)
        except Exception:
            error = {'section': kind, 'error': traceback.format_exc()}
            output['section_errors'].append(error)
            yield {'stage': kind.upper() + '_SECTION_FAILED', 'details': error}
    try:
        output['spatial_api_preflight'] = spatial_api_preflight(u)
        yield {'stage': 'ACTUAL_SPATIAL_API_PREFLIGHT_PASS', 'details': output['spatial_api_preflight']}
    except Exception:
        error = {'section': 'spatial_preflight', 'error': traceback.format_exc()}
        output['section_errors'].append(error)
        yield {'stage': 'SPATIAL_API_PREFLIGHT_FAILED', 'details': error}
    # The exact native Cube is small and remains a complete26/48 export.
    cube = '/Engine/BasicShapes/Cube.Cube'
    try:
        yield {'stage': 'BEFORE_FOOTREST_CUBE_COPY', 'details': {'mesh': cube}}
        dynamic, counts = geometry(u.load_asset(cube), False, u)
        data = arrays(dynamic, counts, u, vertex_limit=200000)
        output['fixtures'][cube] = data; output['source_packages'].append(cube)
        yield {'stage': 'FOOTREST_CUBE_COMPLETE', 'artifact_name': 'FootrestCube',
               'artifact_data': {'mesh': cube, 'geometry': data}, 'details': counts}
    except Exception:
        error = {'section': 'footrest_cube', 'error': traceback.format_exc()}
        output['section_errors'].append(error)
        yield {'stage': 'FOOTREST_CUBE_FAILED', 'details': error}
    if 'spatial_api_preflight' in output:
        for package in sorted({row['mesh'] for row in output['chairs']}):
            try:
                yield from _chair(package, output, u)
            except Exception:
                error = {'section': package, 'error': traceback.format_exc()}
                output['section_errors'].append(error)
                yield {'stage': 'CHAIR_SECTION_FAILED', 'details': error}
    output['success'] = (not output['section_errors'] and len(output['models']) == 2 and len(output['fixtures']) == 4)
    yield {'stage': 'CONTACT_AUTHORING_DATA_READY_NO_ACTORS_CHANGED', 'result': output,
           'details': {'models': len(output['models']), 'chairs': 12, 'footrests': 4,
                       'section_errors': len(output['section_errors']), 'source_packages': len(output['source_packages'])}}
