"""Bounded source skin/chair data for fitting; no actors, assets or maps changed.

The caller advances collect() once per Slate tick and owns receipts/cleanup.
Full candidate skin weights are exported, never guessed from joint positions.
This is contact-authoring input, not a seated/contact or visual acceptance.
"""
import json
import math

MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
MAX_VERTICES = 60000
MAX_TRIANGLES = 200000
WEIGHTS_PER_TICK = 128
MODELS = {
    'Human': '/Game/SciFITrooper_Man_03/SkeletalMesh/SK_SciFITrooper_Man_03',
    'Robot': '/Game/Robot_scout_R_21/Mesh/SK_Robot_scout_R21',
}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def path(obj):
    return obj.get_path_name() if obj else None


def transform(value):
    return {key: list(data.to_tuple()) for key, data in (
        ('location', value.translation), ('rotation', value.rotation), ('scale', value.scale3d))}


def native_api_preflight(u):
    methods = {
        'GeometryScript_AssetUtils': ('copy_mesh_from_skeletal_mesh', 'copy_mesh_from_static_mesh_v2'),
        'GeometryScript_MeshQueries': ('get_vertex_count', 'get_all_vertex_positions', 'get_all_triangle_indices'),
        'GeometryScript_List': ('convert_vector_list_to_array', 'convert_triangle_list_to_array'),
        'GeometryScript_BoneWeights': ('get_all_bones_info', 'get_vertex_bone_weights'),
        'DynamicMesh': ('get_triangle_count',),
        'AnimPoseExtensions': ('get_anim_pose_at_time', 'get_bone_names', 'get_bone_pose'),
        'SkeletalMeshComponent': ('get_skeletal_mesh_asset',),
    }
    checked = {cls + '.' + name: callable(getattr(getattr(u, cls, None), name, None))
               for cls, names in methods.items() for name in names}
    require(all(checked.values()), 'Actual bounded skin export API unavailable')
    empty = u.DynamicMesh()
    require(empty.get_triangle_count() == 0 and u.GeometryScript_MeshQueries.get_vertex_count(empty) == 0,
            'Actual empty mesh count schema differs')
    return {'methods': checked, 'empty_count_readback': True,
            'weight_chunk_vertices': WEIGHTS_PER_TICK, 'full_vertex_limit': MAX_VERTICES,
            'full_triangle_limit': MAX_TRIANGLES}


def geometry(mesh, skeletal, u):
    """Count the native transient copy before exporting Python arrays."""
    dynamic = u.DynamicMesh()
    copy = (u.GeometryScript_AssetUtils.copy_mesh_from_skeletal_mesh if skeletal else
            u.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2)
    result = copy(mesh, dynamic, u.GeometryScriptCopyMeshFromAssetOptions(apply_build_settings=False),
                  u.GeometryScriptMeshReadLOD(lod_type=u.GeometryScriptLODType.SOURCE_MODEL, lod_index=0))
    require(isinstance(result, tuple) and len(result) == 2 and result[0] == dynamic and
            result[1] == u.GeometryScriptOutcomePins.SUCCESS, 'Native source geometry copy schema differs')
    counts = {'vertices': int(u.GeometryScript_MeshQueries.get_vertex_count(dynamic)),
              'triangles': int(dynamic.get_triangle_count())}
    return dynamic, counts


def arrays(dynamic, counts, u, vertex_limit=MAX_VERTICES):
    require(0 < counts['vertices'] <= vertex_limit and 0 < counts['triangles'] <= MAX_TRIANGLES,
            'Full source skin/fixture geometry outside strict export budget: ' + json.dumps(counts))
    _, positions, sparse = u.GeometryScript_MeshQueries.get_all_vertex_positions(dynamic, False)
    _, indices, sparse_triangles = u.GeometryScript_MeshQueries.get_all_triangle_indices(dynamic, False)
    require(not sparse and not sparse_triangles, 'Source geometry has sparse vertex/triangle IDs')
    vertices = list(u.GeometryScript_List.convert_vector_list_to_array(positions))
    triangles = list(u.GeometryScript_List.convert_triangle_list_to_array(indices))
    require(len(vertices) == counts['vertices'] and len(triangles) == counts['triangles'],
            'Source bulk arrays differ from native counts')
    return {'vertices': [list(v.to_tuple()) for v in vertices],
            'triangles': [[int(t.x), int(t.y), int(t.z)] for t in triangles]}


def collect(npc, candidates, u):
    """Yield bounded read-only stages, raw artifacts and one final serializable result."""
    from RefineStationSocialSeatedCrew import _forward
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    eas = u.get_editor_subsystem(u.EditorActorSubsystem)
    world = editor.get_editor_world()
    require(world and world.get_path_name().split('.')[0] == MAP and not editor.get_game_world(),
            'Require exact saved owner editor map outside PIE')
    actors = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
    output = {'scope': 'FULL_TWO_MODEL_SKIN_WEIGHTS_FIVE_NATIVE_POSES_AND_CURRENT_CHAIR_FOOTREST_DATA',
              'read_only': True, 'saved': False, 'models': {}, 'chairs': [], 'footrests': [], 'operators': [],
              'fixtures': {}, 'desk_hardware': [], 'source_packages': [], 'contacts_fitted': False,
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
    # Exactly three reused chair meshes and the real footrest cube; no dense desk export.
    fixture_names = sorted({r['mesh'] for r in output['chairs'] + output['footrests']})
    require(len(fixture_names) == 4, 'Expected three original chair parts plus one cube source')
    for package in fixture_names:
        yield {'stage': 'BEFORE_FIXTURE_COPY', 'details': {'mesh': package}}
        mesh = u.load_asset(package); require(isinstance(mesh, u.StaticMesh), 'Native fixture source missing')
        dynamic, counts = geometry(mesh, False, u)
        yield {'stage': 'FIXTURE_COUNTS', 'details': {'mesh': package, **counts}}
        # Fixture arrays have no skin-weight calls; same200k triangle cap.
        data = arrays(dynamic, counts, u, vertex_limit=200000)
        output['fixtures'][package] = data; output['source_packages'].append(package)
        yield {'stage': 'FIXTURE_GEOMETRY_READY', 'artifact_name': 'Fixture' + str(len(output['fixtures'])),
               'artifact_data': {'mesh': package, 'geometry': data}, 'details': {'mesh': package, **counts}}
    for kind, package in MODELS.items():
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
    output['success'] = True
    yield {'stage': 'CONTACT_AUTHORING_DATA_READY_NO_ACTORS_CHANGED', 'result': output,
           'details': {'models': 2, 'chairs': 12, 'footrests': 4, 'source_packages': len(output['source_packages'])}}
