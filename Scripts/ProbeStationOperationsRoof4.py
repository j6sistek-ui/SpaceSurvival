"""Read actual roof contacts after DensityProbe3 rejects the support band.

This diagnostic performs no authoring and makes no canopy height decision.
Compare raw source triangles with triangles using mesh build settings and the
rendered native bounds. Keep the failed physical guard and all old receipts.
"""
import json

import RefineStationOperationsDensity as D

MAP = D.MAP


def _geometry(mesh, apply_settings, u):
    # Same verified GeometryScript calls as the earlier native geometry probes;
    # only the explicit apply_build_settings option differs for the comparison.
    dynamic = u.DynamicMesh()
    _, outcome = u.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(
        mesh, dynamic, u.GeometryScriptCopyMeshFromAssetOptions(apply_build_settings=apply_settings),
        u.GeometryScriptMeshReadLOD(lod_type=u.GeometryScriptLODType.SOURCE_MODEL, lod_index=0))
    D._require(outcome == u.GeometryScriptOutcomePins.SUCCESS, 'Cannot inspect actual roof source '+mesh.get_path_name())
    _, vectors, gaps = u.GeometryScript_MeshQueries.get_all_vertex_positions(dynamic, False)
    _, triples, triangle_gaps = u.GeometryScript_MeshQueries.get_all_triangle_indices(dynamic, False)
    D._require(not gaps and not triangle_gaps, 'Unexpected sparse actual roof source geometry')
    points = u.GeometryScript_List.convert_vector_list_to_array(vectors)
    triangles = u.GeometryScript_List.convert_triangle_list_to_array(triples)
    data = {'vertices': [list(v.to_tuple()) for v in points],
            'triangles': [[int(t.x), int(t.y), int(t.z)] for t in triangles]}
    data['local_bounds_cm'] = [[min(v[i] for v in data['vertices']) for i in range(3)],
                               [max(v[i] for v in data['vertices']) for i in range(3)]]
    data['apply_build_settings'] = apply_settings
    return data


def probe(ctx):
    import unreal as u
    from RefineStationOperationsDisplays import _state
    from RefineStationWorkroomComposition import _guard_pose
    _, sources, native = D._inputs(ctx, u)
    actors = list(ctx.eas.get_all_level_actors())
    before = {a.get_path_name(): _state(a, u) for a in actors}
    expected = {row['label']: row for row in native if row['label'].startswith('QuietCeiling/Operations/Panel ')}
    selected = [a for a in actors if a.get_actor_label() in expected]
    D._require(len(selected) == len(expected) == 28, 'Complete unchanged native quiet roof required')
    meshes, surfaces, rows = {}, {'raw': [], 'build_applied': []}, []
    baseline_sources = json.loads(D.BASELINE.read_text())['operations']['source_sha256']
    for actor in selected:
        baseline = expected[actor.get_actor_label()]
        _guard_pose(actor, baseline['transform'])
        component = actor.get_component_by_class(u.StaticMeshComponent)
        D._require(component and component.static_mesh, 'Roof has no actual native component')
        package = component.static_mesh.get_path_name().split('.')[0]
        original = next(r for r in baseline['components'] if r['name'] == component.get_name())
        D._require(package == original['mesh'].split('.')[0] and
                   D._sha(D._asset_file(package)) == baseline_sources[package], 'Original native roof source changed')
        sources[package] = baseline_sources[package]
        if package not in meshes:
            bounds = component.static_mesh.get_bounds()
            meshes[package] = {'native_origin_cm': list(bounds.origin.to_tuple()),
                               'native_extent_cm': list(bounds.box_extent.to_tuple()),
                               'raw': _geometry(component.static_mesh, False, u),
                               'build_applied': _geometry(component.static_mesh, True, u)}
        transform = component.get_world_transform()
        for kind in surfaces:
            geometry = meshes[package][kind]
            vertices = [transform.transform_location(u.Vector(*point)).to_tuple() for point in geometry['vertices']]
            surfaces[kind].append((actor, component, package, vertices, geometry['triangles']))
        rows.append({'label': actor.get_actor_label(), 'actor': actor.get_path_name(),
                     'component': component.get_name(), 'mesh': package,
                     'baseline_rendered_world_bounds_cm': baseline['bounds'],
                     'current_transform': {'location': list(transform.translation.to_tuple()),
                                           'rotation': list(transform.rotation.to_tuple()),
                                           'scale': list(transform.scale3d.to_tuple())}})
    contacts = []
    for y in (-500., 0., 500.):
        comparisons = {}
        for kind, blocks in surfaces.items():
            candidates = []
            for actor, component, package, vertices, triangles in blocks:
                for index, face in enumerate(triangles):
                    polygon = [vertices[i] for i in face]
                    for axis, limit, greater in ((0, 7000., True), (0, 8600., False),
                                                 (1, y-5., True), (1, y+5., False)):
                        polygon = D._clip(polygon, axis, limit, greater)
                        if not polygon:
                            break
                    if polygon:
                        low = min(polygon, key=lambda value: value[2])
                        high = max(polygon, key=lambda value: value[2])
                        candidates.append({'minimum_z_cm': low[2], 'maximum_z_cm': high[2],
                            'minimum_point_cm': list(low), 'maximum_point_cm': list(high),
                            'actor': actor.get_path_name(), 'label': actor.get_actor_label(),
                            'component': component.get_name(), 'source_mesh': package, 'triangle': index,
                            'clipped_world_polygon_cm': [list(v) for v in polygon]})
            comparisons[kind] = {'candidate_count': len(candidates),
                'minimum': min(candidates, key=lambda r: r['minimum_z_cm']) if candidates else None,
                'maximum': max(candidates, key=lambda r: r['maximum_z_cm']) if candidates else None,
                'all_contact_candidates': candidates}
        contacts.append({'y_cm': y, 'footprint_cm': [[7000., y-5.], [8600., y+5.]], 'comparisons': comparisons})
    D._require(all(_state(a, u) == before[a.get_path_name()] for a in actors), 'Read-only roof survey changed actor state')
    return {'source_sha256': sources, 'native_roof_actors': rows, 'source_geometry': meshes,
            'actual_contact_surveys': contacts, 'existing_actors_preserved': len(actors),
            'height_assertion_or_authoring': False,
            'scope': 'READ_ONLY RAW_VS_BUILD_APPLIED_ROOF_TRIANGLE_SURVEY',
            'limits': 'Diagnostic only. No canopy placement, lowered guard or saved-room visual acceptance.'}
