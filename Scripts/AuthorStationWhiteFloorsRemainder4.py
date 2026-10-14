"""Measured floor coating and mixed-foundation masks. Root owns loads/saves.

Two private streamed child copies and four retained mixed foundations. Each
native graph/parameter chain remains intact. Four mixed foundations retain their
other faces;90 isolated child floors receive whole-surface coating, including
edges/undersides. No geometry/collision edit; rugs/cloth/walls remain excluded.
"""
import copy
import hashlib
import json
from pathlib import Path
import AuthorStationWhiteFloorsMain as main
import PreviewStationOperationsFloors as measured
import PreviewStationOperationsWhiteFloor as white
from StationFloorSurfaceMasks import mask

PRIVATE = '/Game/OutpostSandbox/StationRefinement/StationWhiteFloorsRemainder20261007'
require, path, transform = measured.require, measured._path, main.transform
PROPERTIES = ('MP_BASE_COLOR', 'MP_NORMAL', 'MP_AMBIENT_OCCLUSION', 'MP_ROUGHNESS', 'MP_METALLIC')


def native_api_preflight(u):
    """CDO/export checks before map load or asset writes; no guessed field names."""
    edit = u.MaterialEditingLibrary
    names = ('get_material_property_input_node_output_name', 'get_material_expression_output_names',
             'get_material_property_input_node', 'create_material_expression', 'connect_material_expressions',
             'connect_material_property', 'recompile_material',
             'get_material_default_scalar_parameter_value', 'get_material_default_vector_parameter_value',
             'get_material_default_texture_parameter_value', 'get_material_default_static_switch_parameter_value')
    require(all(callable(getattr(edit, name, None)) for name in names), 'Required material graph export missing')
    report = {'exports': {name: str(getattr(edit, name).__doc__) for name in names}, 'classes': {}}
    for name in ('MaterialExpressionPreSkinnedPosition', 'MaterialExpressionVertexNormalWS',
                 'MaterialExpressionCustom', 'MaterialExpressionLinearInterpolate', 'MaterialExpressionVertexInterpolator',
                 'MaterialExpressionConstant', 'MaterialExpressionConstant3Vector', 'MaterialExpressionTransformPosition'):
        cls = getattr(u, name, None)
        require(cls, 'Required exact UE5.8 graph class missing '+name)
        cdo = u.get_default_object(cls)
        require(cdo and cdo.get_class().get_name() == name, 'Exact native CDO missing '+name)
        report['classes'][name] = {'class': cdo.get_class().get_path_name(),
                                 'outputs': list(edit.get_material_expression_output_names(cdo)),
                                 'inputs': list(edit.get_material_expression_input_names(cdo))}
        if name == 'MaterialExpressionCustom':
            report['classes'][name]['output_type'] = str(cdo.get_editor_property('output_type'))
            report['classes'][name]['inputs_property'] = str(cdo.get_editor_property('inputs'))
            require(u.CustomMaterialOutputType.CMOT_FLOAT1 is not None, 'Exact custom Float1 enum missing')
        if name == 'MaterialExpressionTransformPosition':
            report['classes'][name]['source'] = str(cdo.get_editor_property('transform_source_type'))
            report['classes'][name]['destination'] = str(cdo.get_editor_property('transform_type'))
        if name == 'MaterialExpressionVertexInterpolator':
            require(report['classes'][name]['inputs'] == ['VS'] and
                    len(report['classes'][name]['outputs']) == 1,
                    'Required native vertex-to-pixel interpolator pins differ')
    # This type/property is already exercised by saved cabin/display helpers.
    pin = u.CustomInput()
    require(pin.get_editor_property('input_name') is not None, 'Exact custom input struct property missing')
    report['position_space'] = 'Foundation PreSkinnedPosition and geometric VertexNormalWS pass through explicit VertexInterpolators to pixel mask.'
    report['transform_node_used'] = False
    return report


def _output_wiring(master, u):
    edit = u.MaterialEditingLibrary
    return {key: {'node': path(edit.get_material_property_input_node(master, getattr(u.MaterialProperty, key))),
                  'output': str(edit.get_material_property_input_node_output_name(master, getattr(u.MaterialProperty, key)))}
            for key in PROPERTIES}


def _extended_graph(master, u):
    """Include unpacked texture references/defaults omitted by the older survey."""
    value = main.graph(master, u)
    by_name = {row['node']: row for row in value['nodes']}
    for expression in u.MaterialEditingLibrary.get_material_expressions(master):
        row = by_name[path(expression)]
        if isinstance(expression, u.MaterialExpressionTextureSample):
            row['native_texture'] = path(expression.get_editor_property('texture'))
        if isinstance(expression, u.MaterialExpressionScalarParameter):
            row['native_default_scalar'] = float(expression.get_editor_property('default_value'))
        if isinstance(expression, u.MaterialExpressionVectorParameter):
            color = expression.get_editor_property('default_value')
            row['native_default_vector'] = [float(getattr(color, k)) for k in ('r', 'g', 'b', 'a')]
    return value


def _default_parameters(master, u):
    """Exact native Material defaults, including overlapping scalar/vector names."""
    edit = u.MaterialEditingLibrary
    return {
        'scalars': {str(n): float(edit.get_material_default_scalar_parameter_value(master, n))
                    for n in edit.get_scalar_parameter_names(master)},
        'vectors': {str(n): [float(getattr(value, k)) for k in ('r', 'g', 'b', 'a')]
                    for n in edit.get_vector_parameter_names(master)
                    for value in (edit.get_material_default_vector_parameter_value(master, n),)},
        'textures': {str(n): path(edit.get_material_default_texture_parameter_value(master, n))
                     for n in edit.get_texture_parameter_names(master)},
        'switches': {str(n): bool(edit.get_material_default_static_switch_parameter_value(master, n))
                     for n in edit.get_static_switch_parameter_names(master)}}


def _normalized(value, package):
    return json.loads(json.dumps(value, sort_keys=True).replace(package+'.'+package.rsplit('/', 1)[1], 'WORLD'))


def scene(actors, package, u):
    return _normalized({a.get_path_name(): state(a, u) for a in actors}, package)


def state(actor, u):
    """Preserve full exact state; native Color is typed RGBA, never its address."""
    from RefineStationOperationsPodiumFinish import state as original_state
    result = original_state(actor, u)
    result['light_properties'] = {}
    for component in actor.get_components_by_class(u.LightComponent):
        color = component.get_editor_property('light_color')
        result['light_properties'][component.get_path_name()] = {
            'intensity': float(component.get_editor_property('intensity')),
            'light_color': [int(getattr(color, key)) for key in ('r', 'g', 'b', 'a')],
            'cast_shadows': bool(component.get_editor_property('cast_shadows')),
            'indirect_lighting_intensity': float(component.get_editor_property('indirect_lighting_intensity')),
            'volumetric_scattering_intensity': float(component.get_editor_property('volumetric_scattering_intensity')),
            'specular_scale': float(component.get_editor_property('specular_scale')),
            'affects_world': bool(component.get_editor_property('affects_world'))}
    return result


def verify_loaded(world, actors, source_package, map_plan, u, private_copy=False):
    """Exact placed floor roles plus all scene state; mapped prefix is the only alias."""
    package = world.get_path_name().split('.')[0]
    require(package == (map_plan['target'] if private_copy else source_package) and
            len(actors) == map_plan['expected_actor_count'], 'Exact source/private actor population differs')
    require(map_plan['rows'], 'Empty reviewed floor whitelist')
    components = {c.get_path_name(): c for a in actors for c in a.get_components_by_class(u.StaticMeshComponent)}
    targets = []
    prefix = source_package+'.'+source_package.rsplit('/', 1)[1]
    replacement = package+'.'+package.rsplit('/', 1)[1]
    for row in map_plan['rows']:
        name = row['component'].replace(prefix, replacement)
        c = components.get(name)
        require(c and c.get_owner().get_path_name() == row['actor'].replace(prefix, replacement) and
                c.get_owner().get_actor_label() == row['label'] and c.get_class().get_name() == row['class'] and
                path(c.static_mesh) == row['mesh'] and
                [path(m) for m in c.get_materials()] == row['materials'] and
                transform(c.get_owner().get_actor_transform()) == row['actor_transform'] and
                transform(c.get_world_transform()) == row['world_transform'] and
                transform(c.get_relative_transform()) == row['relative_transform'] and
                str(c.get_collision_enabled()) == row['collision'] and
                str(c.get_collision_profile_name()) == row['collision_profile'] and c.is_visible() and
                not c.get_editor_property('hidden_in_game'), 'Native floor role changed '+row['label'])
        require(row['slots'] == [0] and c.get_num_materials() == 1,
                'Only exact measured single floor material slots are authorized')
        require(not isinstance(c, u.InstancedStaticMeshComponent), 'No unmeasured instanced remainder floors')
        # Child mesh Z must still be station-vertical; this mask cannot secretly
        # whiten an upright wall made from the same asset. Ring retains mirror.
        if source_package != main.measured.MAP:
            require(abs(c.get_up_vector().z) > .999, 'Child floor changed orientation; height mask unsafe')
        targets.append((c, row))
    return targets


def prepare(survey, plan, progress, u):
    """Verify all geometry first, then create bounded private masked material pairs."""
    from RefineStationSocialSeatedCrew import _geometry
    require(plan['private'] == PRIVATE and plan['expected_role_count'] == len(plan['roles']) == 17 and
            plan['expected_material_asset_count'] == 34 and plan['color'] == [1., 1., 1.] and
            plan['metallic'] == 0. and plan['roughness'] == .6, 'Reviewed remainder recipe differs')
    require(sum(len(m['rows']) for p, m in plan['maps'].items() if p != main.measured.MAP) == 90 and
            len(plan['maps'][main.measured.MAP]['rows']) == 4 and
            sum(r['mask_kind'] == 'pure_child_floor_whole_surface' for r in plan['roles'].values()) == 13 and
            all((r['mask_kind'] in ('owner_deck_top', 'owner_ring_upper')) ==
                (r['survey_map'] == main.measured.MAP) for r in plan['roles'].values()),
            'Exact90 isolated child floors/four mixed-foundation scope differs')
    edit, tools = u.MaterialEditingLibrary, u.AssetToolsHelpers.get_asset_tools()
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    destinations = [r[key] for r in plan['roles'].values() for key in ('master_target', 'leaf_target')]
    candidate_files = [root/('Content/'+dest[6:]+ext) for dest in destinations for ext in ('.uasset', '.uexp', '.ubulk')]
    require(len(destinations) == len(set(destinations)) == 34 and all(not p.exists() for p in candidate_files) and
            all(not u.EditorAssetLibrary.does_asset_exist(p) for p in destinations), 'Preserve existing private attempt')
    proofs, native_sources = {}, {}
    for identity, role in sorted(plan['roles'].items()):
        progress('verify_exact_role_geometry', 'before', {'role': identity, 'mesh': role['mesh']})
        inventory = survey['maps'][role['survey_map']]
        expected = inventory['meshes'][role['mesh']]
        mesh = u.load_asset(role['mesh']); require(mesh, 'Exact measured mesh missing')
        require(len(mesh.get_editor_property('static_materials')) == 1, 'Unmeasured mixed mesh slot role')
        _, geometry = _geometry(mesh, False, u)
        actual_sha = hashlib.sha256(json.dumps(geometry, sort_keys=True).encode()).hexdigest()
        require(actual_sha == role['geometry_sha256'] == expected['geometry_sha256'] and
                len(geometry['triangles']) == role['triangle_count'], 'Native floor geometry changed before masking')
        # Retain exact raw data even when a child topology fails the height-only
        # guard. The root can then repair a role offline without another probe.
        progress('exact_role_geometry_ready', 'after', {'role': identity, 'mesh': role['mesh'],
                 'geometry_sha256': actual_sha, 'native_geometry': geometry})
        if role['mask_kind'] == 'pure_child_floor_whole_surface':
            proof = {'kind': role['mask_kind'], 'coating_alpha': 1.,
                     'coated_triangle_count': len(geometry['triangles']),
                     'includes_edges_and_undersides': True, 'geometry_collision_unchanged': True,
                     'original_normal_ao_uv_preserved': True}
        else:
            proof = mask(geometry, role['mask_kind'], role['normal_min'])
        proof.update({'mesh': role['mesh'], 'geometry_sha256': actual_sha, 'role': identity})
        proofs[identity] = proof
        native = u.load_asset(role['material']); master = u.load_asset(role['master'])
        require(native and isinstance(master, u.Material) and not master.get_editor_property('use_material_attributes'),
                'Exact native material/direct-output master missing')
        require(main.graph(master, u) == inventory['master_graphs'][role['master']], 'Original complete graph differs')
        if isinstance(native, u.MaterialInstanceConstant):
            require(role['lineage'] == [{'asset': path(native), 'class': 'MaterialInstanceConstant'},
                                       {'asset': path(master), 'class': 'Material'}] and
                    native.get_editor_property('parent') == master and
                    measured._same_parameters(measured._parameters(native, u), inventory['materials'][path(native)]['parameters']),
                    'Exact direct inherited native leaf/parameters differ')
        else:
            require(native == master and isinstance(native, u.Material) and
                    role['lineage'] == [{'asset': path(master), 'class': 'Material'}],
                    'Exact measured direct Material/lineage differs')
            defaults = _default_parameters(master, u)
            graph = _extended_graph(master, u)
            for row in graph['nodes']:
                if row['class'] == 'MaterialExpressionScalarParameter':
                    require(defaults['scalars'][row['parameter_name']] == row['native_default_scalar'],
                            'Native scalar default getter/graph differs')
                elif row['class'] == 'MaterialExpressionVectorParameter':
                    require(defaults['vectors'][row['parameter_name']] == row['native_default_vector'],
                            'Native vector default getter/graph differs')
            proofs[identity]['direct_material_default_parameters'] = defaults
        native_sources[identity] = (native, master)
        progress('verify_exact_role_geometry', 'after', proof)
    # Every exact role/source is validated before any material/map create.
    dirty, leaves, graphs, parameter_receipts = [], {}, [], []
    for identity, role in sorted(plan['roles'].items()):
        native, master = native_sources[identity]
        progress('duplicate_masked_master', 'before', {'role': identity, 'source': path(master)})
        target = role['master_target']
        clone = tools.duplicate_asset(target.rsplit('/', 1)[1], target.rsplit('/', 1)[0], master)
        require(isinstance(clone, u.Material) and not clone.get_editor_property('use_material_attributes'), 'Master duplicate failed')
        before = _extended_graph(clone, u); source_graph = _extended_graph(master, u)
        require(measured._canonical_graph(before, path(clone)) == measured._canonical_graph(source_graph, path(master)),
                'Master clone lost native nodes/constants/normal/AO/UV')
        wiring = _output_wiring(clone, u)
        require(all(wiring[key]['node'] for key in PROPERTIES), 'Require explicit measured native output connections')
        added = []
        def node(cls):
            obj = edit.create_material_expression(clone, cls)
            require(obj, 'Cannot create exact mask graph class'); added.append(path(obj)); return obj
        def connect(a, output, b, pin):
            require(edit.connect_material_expressions(a, output, b, pin), 'Masked graph connection failed '+pin)
        whole = role['mask_kind'] == 'pure_child_floor_whole_surface'
        if whole:
            shader = node(u.MaterialExpressionConstant)
            shader.set_editor_property('r', 1.)
            require(float(shader.get_editor_property('r')) == 1., 'Whole-floor coating alpha differs')
        else:
            position = node(u.MaterialExpressionPreSkinnedPosition)
            normal = node(u.MaterialExpressionVertexNormalWS)
            interpolated = []
            for source in (position, normal):
                value = node(u.MaterialExpressionVertexInterpolator)
                require(list(edit.get_material_expression_input_names(value)) == ['VS'], 'Actual interpolator input differs')
                outputs = list(edit.get_material_expression_output_names(value))
                require(len(outputs) == 1, 'Actual interpolator output differs')
                connect(source, '', value, 'VS'); interpolated.append((value, outputs[0]))
            shader = node(u.MaterialExpressionCustom)
            shader.set_editor_property('description', 'Measured mixed foundation top; original other faces retained')
            shader.set_editor_property('code', proofs[identity]['code'])
            shader.set_editor_property('output_type', u.CustomMaterialOutputType.CMOT_FLOAT1)
            pins = []
            for name in ('P', 'N'):
                pin = u.CustomInput(); pin.set_editor_property('input_name', name); pins.append(pin)
            shader.set_editor_property('inputs', pins)
            for (source, output), name in zip(interpolated, ('P', 'N')):
                connect(source, output, shader, name)
            require(shader.get_editor_property('code') == proofs[identity]['code'] and
                    shader.get_editor_property('output_type') == u.CustomMaterialOutputType.CMOT_FLOAT1,
                    'Actual foundation mask differs')
        lerps = {}
        for key, kind, value in (('MP_BASE_COLOR', u.MaterialExpressionConstant3Vector, u.LinearColor(1., 1., 1., 1.)),
                                 ('MP_METALLIC', u.MaterialExpressionConstant, 0.),
                                 ('MP_ROUGHNESS', u.MaterialExpressionConstant, .6)):
            constant = node(kind)
            constant.set_editor_property('constant' if key == 'MP_BASE_COLOR' else 'r', value)
            lerp = node(u.MaterialExpressionLinearInterpolate)
            source = edit.get_material_property_input_node(clone, getattr(u.MaterialProperty, key))
            # The exact exported channel name is essential for packed ORM and
            # Cargo's BreakMaterialAttributes. Never assume default output.
            connect(source, wiring[key]['output'], lerp, 'A')
            connect(constant, '', lerp, 'B'); connect(shader, '', lerp, 'Alpha')
            require(edit.connect_material_property(lerp, '', getattr(u.MaterialProperty, key)), 'Masked output failed')
            lerps[key] = path(lerp)
        expected_added = 7 if whole else 11
        require(len(added) == expected_added, 'Actual floor coating/mask node count differs')
        progress('compile_masked_master', 'before', {'role': identity})
        errors = edit.recompile_material(clone); require(not errors, 'Masked shader compile errors '+str(errors))
        after = _extended_graph(clone, u); after_wiring = _output_wiring(clone, u)
        require({n['node']: n for n in before['nodes']} ==
                {n['node']: n for n in after['nodes'] if n['node'] not in added} and
                len(after['nodes']) == len(before['nodes'])+expected_added and before['blend_mode'] == after['blend_mode'] and
                all(after_wiring[k] == wiring[k] for k in ('MP_NORMAL', 'MP_AMBIENT_OCCLUSION')) and
                all(after_wiring[k]['node'] == v for k,v in lerps.items()) and _extended_graph(master, u) == source_graph,
                'Masked graph changed original parameter/normal/AO/UV/source nodes')
        leaf_target = role['leaf_target']
        if isinstance(native, u.MaterialInstanceConstant):
            local = white._local_overrides(native, u); expected_parameters = measured._parameters(native, u)
            leaf = tools.duplicate_asset(leaf_target.rsplit('/', 1)[1], leaf_target.rsplit('/', 1)[0], native)
            require(isinstance(leaf, u.MaterialInstanceConstant) and white._local_overrides(leaf, u) == local, 'Local overrides lost')
            edit.set_material_instance_parent(leaf, clone)
            require(leaf.get_editor_property('parent') == clone and white._local_overrides(leaf, u) == local and
                    measured._same_parameters(measured._parameters(leaf, u), expected_parameters) and
                    native.get_editor_property('parent') == master, 'Inherited native values changed')
        else:
            expected_parameters = proofs[identity]['direct_material_default_parameters']
            require(_default_parameters(master, u) == expected_parameters and
                    _default_parameters(clone, u) == expected_parameters,
                    'Source/private direct Material defaults differ')
            leaf = tools.create_asset(leaf_target.rsplit('/', 1)[1], leaf_target.rsplit('/', 1)[0],
                                      u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
            require(isinstance(leaf, u.MaterialInstanceConstant), 'Private direct trim leaf create failed')
            edit.set_material_instance_parent(leaf, clone)
            require(leaf.get_editor_property('parent') == clone and
                    measured._parameters(leaf, u) == expected_parameters and
                    _default_parameters(master, u) == expected_parameters,
                    'Private MIC did not inherit exact native direct Material defaults')
        leaves[identity] = leaf; dirty.extend((clone, leaf))
        graphs.append({'role': identity, 'source': path(master), 'private': path(clone), 'before': before, 'after': after,
                       'original_output_pins': wiring, 'private_output_pins': after_wiring,
                       'native_normal_ao_uv_preserved': True, 'original_other_faces_outputs_retained': not whole,
                       'added_node_count': expected_added, 'whole_surface_coating': whole,
                       'foundation_vertex_to_pixel_interpolators': 0 if whole else 2})
        parameter_receipts.append({'role': identity, 'source': path(native), 'private': path(leaf),
                                   'native_effective_parameters': expected_parameters, 'no_parameter_values_changed': True})
        progress('compile_masked_master', 'after', {'role': identity})
    require(len(dirty) == 34 and len(leaves) == 17 and all(not p.exists() for p in candidate_files), 'Private count/disk changed')
    return {'dirty_assets': dirty, 'leaves': leaves, 'mask_proofs': proofs, 'master_graphs': graphs,
            'materials': parameter_receipts, 'candidate_package_files': list(map(str, candidate_files))}


def apply_loaded(world, actors, source_package, map_plan, leaves, u, private_copy=False):
    targets = verify_loaded(world, actors, source_package, map_plan, u, private_copy)
    original = {a.get_path_name(): state(a, u) for a in actors}; expected = copy.deepcopy(original)
    changes, undo = [], []
    try:
        for component, row in targets:
            leaf = leaves[row['role']]; undo.append((component, component.get_material(0)))
            component.set_material(0, leaf)
            expected[component.get_owner().get_path_name()]['materials'][path(component)][0] = path(leaf)
            changes.append({'actor': path(component.get_owner()), 'label': row['label'], 'component': path(component),
                            'slot': 0, 'source': row['materials'][0], 'private': path(leaf), 'role': row['role']})
        require(expected == {a.get_path_name(): state(a, u) for a in actors}, 'Unlisted scene change during floor references')
    except Exception:
        for component, material in reversed(undo): component.set_material(0, material)
        raise
    return {'material_slot_allowlist': changes, 'new_actor_count': 0, 'new_light_count': 0,
            'expected_scene': scene(actors, world.get_path_name().split('.')[0], u)}
