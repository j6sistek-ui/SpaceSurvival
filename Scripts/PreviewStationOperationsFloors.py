"""Unsaved finish tests on the exact84 T floor panels; the lead owns capture.

One private UNSAVED copy of the measured native master retains its original
normal, UVs, AO connection, texture references and parameter graph. Only its
BaseColor/Metallic/Roughness outputs change. All per-source parameters are copied
into transient MICs. No asset/map save, source edit, actor, light or collision.
"""
import copy
import hashlib
import json
import math
import re
from pathlib import Path

MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
MASTER = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Materials/Masters/MM_MasterMaterial01_Opaque.MM_MasterMaterial01_Opaque'
PRIVATE = '/Game/OutpostSandbox/StationRefinement/OperationsFloorUnsaved20261007/M_FloorOptions1'
MESH = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Meshes/SM_UniversalPanel400X200_V2.SM_UniversalPanel400X200_V2'
PROBE_SHA = 'e8481055d10aa1f11c896b663f95bfabdb76e8096f98d231c98f6c505b1c604a'
TEST_SCALARS = ('TestFloorMetallic', 'TestFloorRoughness')
TEST_VECTOR = 'TestFloorColor'
_prepared = None


def _package_files(root):
    base = root/('Content/'+PRIVATE[6:])
    return [base.with_suffix(extension) for extension in ('.uasset', '.uexp', '.ubulk')]


def _absent(files):
    return all(not path.exists() for path in files)


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def _path(obj):
    return obj.get_path_name() if obj else None


def _parameters(material, u):
    edit = u.MaterialEditingLibrary
    return {
        'scalars': {str(n): float(edit.get_material_instance_scalar_parameter_value(material, n))
                    for n in edit.get_scalar_parameter_names(material)},
        'vectors': {str(n): [float(getattr(value, k)) for k in ('r', 'g', 'b', 'a')]
                    for n in edit.get_vector_parameter_names(material)
                    for value in (edit.get_material_instance_vector_parameter_value(material, n),)},
        'textures': {str(n): _path(edit.get_material_instance_texture_parameter_value(material, n))
                     for n in edit.get_texture_parameter_names(material)},
        'switches': {str(n): bool(edit.get_material_instance_static_switch_parameter_value(material, n))
                     for n in edit.get_static_switch_parameter_names(material)}}


def _same_parameters(actual, expected):
    return (actual['textures'] == expected['textures'] and actual['switches'] == expected['switches'] and
            actual['scalars'].keys() == expected['scalars'].keys() and
            all(abs(actual['scalars'][k]-v) < .0001 for k, v in expected['scalars'].items()) and
            actual['vectors'].keys() == expected['vectors'].keys() and
            all(len(actual['vectors'][k]) == len(v) and
                all(abs(a-b) < .0001 for a, b in zip(actual['vectors'][k], v)) for k, v in expected['vectors'].items()))


def _graph(master, u):
    """The same installed5.8 read-only graph fields used by FloorProbe1."""
    edit = u.MaterialEditingLibrary
    result = {'asset': _path(master), 'blend_mode': str(master.get_editor_property('blend_mode')),
              'nodes': [], 'properties': {}}
    for name in ('MP_BASE_COLOR', 'MP_NORMAL', 'MP_AMBIENT_OCCLUSION', 'MP_ROUGHNESS', 'MP_METALLIC'):
        result['properties'][name] = _path(edit.get_material_property_input_node(master, getattr(u.MaterialProperty, name)))
    for node in edit.get_material_expressions(master):
        kind = node.get_class().get_name()
        row = {'node': _path(node), 'class': kind,
               'input_names': list(edit.get_material_expression_input_names(node)),
               'inputs': [_path(x) for x in edit.get_inputs_for_material_expression(master, node)]}
        if isinstance(node, u.MaterialExpressionParameter):
            row['parameter_name'] = str(node.get_editor_property('parameter_name'))
        if isinstance(node, u.MaterialExpressionTextureSampleParameter):
            row['parameter_name'] = str(node.get_editor_property('parameter_name'))
            row['texture'] = _path(node.get_editor_property('texture'))
        if isinstance(node, u.MaterialExpressionMaterialFunctionCall):
            row['function'] = _path(node.get_editor_property('material_function'))
        if kind == 'MaterialExpressionLinearInterpolate':
            row['unconnected_constants'] = {p: float(node.get_editor_property(p))
                                            for p in ('const_a', 'const_b', 'const_alpha')}
        result['nodes'].append(row)
    return result


def _canonical_graph(graph, source_path):
    value = copy.deepcopy(graph)
    value['asset'] = 'MASTER'
    value['nodes'] = sorted(value['nodes'], key=lambda n: n['node'])
    # Full duplicate preserves original expression names and all external refs.
    raw = json.dumps(value, sort_keys=True).replace(source_path, 'MASTER')
    return json.loads(raw)


def _floor(world, probe, u, original=True):
    from RefineStationWorkroomComposition import _guard_pose
    package = re.sub(r'UEDPIE_[0-9]+_', '', world.get_path_name().split('.')[0])
    require(package == MAP and len(probe['floor_actors']) == 84, 'Wrong actual T floor world/plan')
    actors = list(u.GameplayStatics.get_all_actors_of_class(world, u.Actor))
    by_label = {}
    for actor in actors:
        by_label.setdefault(actor.get_actor_label(), []).append(actor)
    require(len([a for a in actors if a.get_actor_label().startswith('Operations/Deck ')]) == 84,
            'Unreviewed or missing T deck actor')
    result = []
    for row in probe['floor_actors']:
        found = by_label.get(row['label'], [])
        require(len(found) == 1, 'Exact deck identity missing '+row['label'])
        actor = found[0]; _guard_pose(actor, row['transform'])
        require(actor.get_path_name().split(':PersistentLevel.')[-1] ==
                row['actor'].split(':PersistentLevel.')[-1], 'Original deck actor identity differs')
        components = list(actor.get_components_by_class(u.StaticMeshComponent))
        require(len(components) == 1, 'Unexpected floor assembly')
        component = components[0]
        require(component.static_mesh.get_path_name() == MESH and component.get_num_materials() == 5 and
                component.get_collision_enabled() == u.CollisionEnabled.NO_COLLISION and component.is_visible() and
                not component.get_editor_property('hidden_in_game'), 'Floor mesh/collision/visibility differs')
        if original:
            require([_path(m) for m in component.get_materials()] == row['materials'], 'Original floor slots differ')
        result.append((actor, component, row))
    ground = by_label.get('Ground/Operations', [])
    require(len(ground) == 1, 'Collision authority missing')
    ground_component = ground[0].get_component_by_class(u.StaticMeshComponent)
    require(ground_component and ground_component.static_mesh.get_path_name() == '/Engine/BasicShapes/Cube.Cube' and
            ground_component.get_collision_enabled() == u.CollisionEnabled.QUERY_AND_PHYSICS,
            'Collision authority changed')
    saved_ground = probe['unchanged_collision_authority']['state']
    from RefineStationOperationsDisplays import _state
    # PIE changes package prefixes only; the collision actor's numeric state,
    # mesh, material, collision and primitive poses must match the native probe.
    actual_state = _state(ground[0], u)
    ground_path = ground[0].get_path_name()
    saved_path = probe['unchanged_collision_authority']['actor']
    normalized = json.loads(json.dumps(actual_state).replace(ground_path, saved_path))
    require(normalized == json.loads(json.dumps(saved_ground)), 'Ground collision authority state differs')
    return actors, result


def verify_original(world, probe):
    import unreal as u
    _floor(world, probe, u)
    return True


def prepare_options(probe, plan):
    """Prepare before PIE; no component reference changes and no file writes."""
    import unreal as u
    global _prepared
    require(_prepared is None, 'Do not reprepare or reuse an earlier test')
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    source = root/'.agent/local/StationRefinement/StationOperationsFloorProbe1.json'
    require(hashlib.sha256(source.read_bytes()).hexdigest() == PROBE_SHA == plan['probe_sha256'] and
            probe['success'] and probe['preservation_pass'] and probe['scene_unchanged'], 'Require exact preserved native floor probe')
    require([o['name'] for o in plan['options']] == ['CleanWhite', 'BrushedSilver', 'WhiteSilverTrim'],
            'Require the three bounded owner floor options')
    for option in plan['options']:
        require(len(option['slots']) == 5, 'Every native slot must have an explicit finish')
        for recipe in option['slots']:
            require(len(recipe['color']) == 3 and all(math.isfinite(v) and 0. <= v <= 1. for v in recipe['color']) and
                    math.isfinite(recipe['metallic']) and 0. <= recipe['metallic'] <= 1. and
                    math.isfinite(recipe['roughness']) and .1 <= recipe['roughness'] <= 1.,
                    'Invalid bounded test color/metallic/roughness')
    candidate_files = _package_files(root)
    require(_absent(candidate_files) and not u.EditorAssetLibrary.does_asset_exist(PRIVATE),
            'Preserve any earlier floor test')
    from RefineStationOperationsDisplays import _state
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    require(not editor.get_game_world(), 'Prepare floor shaders before PIE')
    world = editor.get_editor_world()
    actors, rows = _floor(world, probe, u)
    before = {a.get_path_name(): _state(a, u) for a in actors}
    edit = u.MaterialEditingLibrary
    native = u.load_asset(MASTER)
    expected_graph = probe['master_graphs'][MASTER]
    require(_graph(native, u) == expected_graph and len(expected_graph['nodes']) == 377,
            'Native master graph changed from measured probe')
    clone = u.AssetToolsHelpers.get_asset_tools().duplicate_asset(
        PRIVATE.rsplit('/', 1)[1], PRIVATE.rsplit('/', 1)[0], native)
    require(isinstance(clone, u.Material) and _absent(candidate_files), 'Unsaved native master clone failed or wrote a file')
    cloned_before = _graph(clone, u)
    require(_canonical_graph(cloned_before, _path(clone)) == _canonical_graph(expected_graph, MASTER),
            'Private full master copy changed native graph wiring, textures, functions or outputs')
    added = {}
    for name, kind, prop, properties in (
        (TEST_VECTOR, u.MaterialExpressionVectorParameter, u.MaterialProperty.MP_BASE_COLOR,
         {'default_value': u.LinearColor(1., 1., 1., 1.)}),
        (TEST_SCALARS[0], u.MaterialExpressionScalarParameter, u.MaterialProperty.MP_METALLIC, {'default_value': 0.}),
        (TEST_SCALARS[1], u.MaterialExpressionScalarParameter, u.MaterialProperty.MP_ROUGHNESS, {'default_value': .6})):
        require(not any(n.get('parameter_name') == name for n in expected_graph['nodes']), 'Test parameter collides with native name')
        node = edit.create_material_expression(clone, kind); require(node, 'Cannot create temporary test parameter')
        node.set_editor_property('parameter_name', name)
        for key, value in properties.items():
            node.set_editor_property(key, value)
        require(edit.connect_material_property(node, '', prop), 'Cannot connect test output '+name)
        added[name] = _path(node)
    errors = edit.recompile_material(clone)
    require(not errors, 'Temporary floor shader compile failed '+str(errors))
    cloned_after = _graph(clone, u)
    before_nodes = {n['node']: n for n in cloned_before['nodes']}
    after_nodes = {n['node']: n for n in cloned_after['nodes'] if n['node'] not in added.values()}
    require(before_nodes == after_nodes and len(cloned_after['nodes']) == 380 and
            all(cloned_after['properties'][key] == cloned_before['properties'][key]
                for key in ('MP_NORMAL', 'MP_AMBIENT_OCCLUSION')) and
            cloned_after['properties']['MP_BASE_COLOR'] == added[TEST_VECTOR] and
            cloned_after['properties']['MP_METALLIC'] == added[TEST_SCALARS[0]] and
            cloned_after['properties']['MP_ROUGHNESS'] == added[TEST_SCALARS[1]] and
            cloned_after['blend_mode'] == cloned_before['blend_mode'] and _absent(candidate_files),
            'Native normal/AO/UV/original graph changed or shader wrote a file')
    source_slots = {}
    for _, _, row in rows:
        for index, name in enumerate(row['materials']):
            source_slots.setdefault(name, set()).add(index)
    require(len(source_slots) == 10 and all(len(v) == 1 for v in source_slots.values()), 'Native slot-role mapping is ambiguous')
    cache, material_receipts = {}, []
    for option in plan['options']:
        require(len(option['slots']) == 5, 'Every native slot must have an explicit finish')
        for name, slots in source_slots.items():
            slot = next(iter(slots)); recipe = option['slots'][slot]
            source_material = u.load_asset(name); original = probe['materials'][name]
            original_parameters = {key: original[key] for key in ('scalars', 'vectors', 'textures', 'switches')}
            require(_same_parameters(_parameters(source_material, u), original_parameters), 'Source parameters changed '+name)
            child = u.new_object(u.MaterialInstanceConstant)
            require(isinstance(child, u.MaterialInstanceConstant) and _path(child).startswith('/Engine/Transient.'),
                    'Test child must be transient')
            edit.set_material_instance_parent(child, clone)
            for parameter, value in original['scalars'].items():
                edit.set_material_instance_scalar_parameter_value(child, parameter, value)
            for parameter, value in original['vectors'].items():
                edit.set_material_instance_vector_parameter_value(child, parameter, u.LinearColor(*value))
            for parameter, value in original['textures'].items():
                edit.set_material_instance_texture_parameter_value(child, parameter, u.load_asset(value) if value else None)
            for parameter, value in original['switches'].items():
                # Installed5.8 exposes deferred update explicitly; do not compile
                # every switch separately. Exact final native readbacks decide.
                edit.set_material_instance_static_switch_parameter_value(
                    child, parameter, value, u.MaterialParameterAssociation.GLOBAL_PARAMETER, False)
            edit.set_material_instance_vector_parameter_value(child, TEST_VECTOR, u.LinearColor(*recipe['color'], 1.))
            edit.set_material_instance_scalar_parameter_value(child, TEST_SCALARS[0], recipe['metallic'])
            edit.set_material_instance_scalar_parameter_value(child, TEST_SCALARS[1], recipe['roughness'])
            edit.update_material_instance(child)
            expected = copy.deepcopy(original_parameters)
            expected['scalars'].update({TEST_SCALARS[0]: recipe['metallic'], TEST_SCALARS[1]: recipe['roughness']})
            expected['vectors'][TEST_VECTOR] = recipe['color']+[1.]
            actual = _parameters(child, u)
            require(_same_parameters(actual, expected) and child.get_editor_property('parent') == clone,
                    'Temporary finish changed original parameter/texture/switch or failed test value readback')
            cache[(option['name'], name)] = child
            material_receipts.append({'option': option['name'], 'source': name, 'native_slot': slot,
                'transient_child': _path(child), 'native_parameters_preserved': True,
                'native_textures_preserved': True, 'native_switches_preserved': True, 'actual': actual})
    require(len(cache) == 30 and _absent(candidate_files) and before == {
        a.get_path_name(): _state(a, u) for a in u.GameplayStatics.get_all_actors_of_class(world, u.Actor)},
        'Unexpected test material count, disk write or editor scene change')
    _prepared = {'master': clone, 'children': cache, 'candidate_files': candidate_files, 'probe': probe}
    return {'unsaved_master': _path(clone), 'native_master': MASTER, 'original_nodes_preserved': 377,
            'added_test_parameters': added, 'native_normal_output': cloned_after['properties']['MP_NORMAL'],
            'native_ao_output': cloned_after['properties']['MP_AMBIENT_OCCLUSION'],
            'transient_child_count': len(cache), 'materials': material_receipts,
            'candidate_package_files_absent': True, 'candidate_package_files': [str(p) for p in candidate_files],
            'editor_scene_unchanged': True, 'saved': False}


def apply_option(world, probe, plan, option_name):
    import unreal as u
    from RefineStationOperationsDisplays import _state
    require(_prepared and _absent(_prepared['candidate_files']), 'Require unsaved prepared floor shaders')
    actors, rows = _floor(world, probe, u)
    before = {a.get_path_name(): _state(a, u) for a in actors}; expected = copy.deepcopy(before)
    undo, changes = [], []
    try:
        for actor, component, row in rows:
            for slot, name in enumerate(row['materials']):
                child = _prepared['children'][(option_name, name)]
                original = component.get_material(slot); undo.append((component, slot, original))
                component.set_material(slot, child)
                expected[actor.get_path_name()]['materials'][component.get_path_name()][slot] = _path(child)
                changes.append({'label': row['label'], 'component': component.get_path_name(), 'slot': slot,
                                'before': name, 'test': _path(child)})
        require(len(changes) == 420 and expected == {
            a.get_path_name(): _state(a, u) for a in u.GameplayStatics.get_all_actors_of_class(world, u.Actor)},
            'Unlisted actor/geometry/material/light/collision changed during option application')
    except Exception:
        for component, slot, original in reversed(undo):
            component.set_material(slot, original)
        raise
    return {'undo': undo, 'world': world, 'probe': probe, 'before': before,
            'receipt': {'option': option_name, 'changed_floor_actors': 84, 'changed_floor_slots': 420,
                        'changes': changes, 'native_normal_uv_ao_and_parameters_preserved': True,
                        'lighting_geometry_collision_unchanged': True, 'saved': False}}


def restore(handle):
    import unreal as u
    from RefineStationOperationsDisplays import _state
    actors, _ = _floor(handle['world'], handle['probe'], u, original=False)
    before = {a.get_path_name(): _state(a, u) for a in actors}; expected = copy.deepcopy(before)
    for component, slot, original in reversed(handle['undo']):
        component.set_material(slot, original)
        expected[component.get_owner().get_path_name()]['materials'][component.get_path_name()][slot] = _path(original)
    require(expected == {a.get_path_name(): _state(a, u)
                         for a in u.GameplayStatics.get_all_actors_of_class(handle['world'], u.Actor)} and
            verify_original(handle['world'], handle['probe']) and _absent(_prepared['candidate_files']),
            'Original420 floor references did not restore or an unlisted scene property changed')
    handle['undo'].clear()


def unsaved_package_files_absent():
    return bool(_prepared) and _absent(_prepared['candidate_files'])
