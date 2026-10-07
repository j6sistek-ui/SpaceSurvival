"""White-only UNSAVED floor test using cached copies of native MIC inheritance.

The lead launches/captures. No saves, source edits, or actor changes in prepare.
Only three private master outputs change; native normals/AO/UV/parameters stay.
An external process watchdog is required: Python cannot interrupt a blocking
native material API. The progress callback runs before and after each stage.
"""
import copy
import hashlib
import json
from pathlib import Path

import PreviewStationOperationsFloors as measured

MAP = measured.MAP
MASTER = measured.MASTER
PROBE_SHA = measured.PROBE_SHA
PRIVATE = '/Game/OutpostSandbox/StationRefinement/OperationsWhiteUnsaved20261007'
MASTER_COPY = PRIVATE+'/M_WhiteFloor1'
COLOR = 'TestFloorColor'
METAL = 'TestFloorMetallic'
ROUGH = 'TestFloorRoughness'
UTILITY_SHA = 'c7ba30d436cae106c191b3d8d436d5dc2cbaa2fdf7f46f5998cdc7af220c8e7c'
_prepared = None
_candidate_files = []

require = measured.require
_path = measured._path


def _files(root, package):
    base = root/('Content/'+package[6:])
    return [base.with_suffix(s) for s in ('.uasset', '.uexp', '.ubulk')]


def unsaved_package_files_absent():
    return measured._absent(_candidate_files)


def verify_original(world, probe):
    return measured.verify_original(world, probe)


def _local_overrides(material, u):
    """Copy preservation, not a flatten/rewrite of inherited overrides.

    These reflected arrays/base struct are used by AuthorMilkyWay.py. Static
    override flags use the exported editor API rather than editor-only structs.
    """
    arrays = {}
    for name in ('scalar_parameter_values', 'vector_parameter_values',
                 'double_vector_parameter_values', 'texture_parameter_values',
                 'texture_collection_parameter_values', 'parameter_collection_parameter_values',
                 'runtime_virtual_texture_parameter_values', 'sparse_volume_texture_parameter_values',
                 'font_parameter_values', 'user_scene_texture_overrides'):
        arrays[name] = [entry.export_text() for entry in material.get_editor_property(name)]
    switches = {str(n): bool(u.MaterialEditingLibrary.is_material_instance_parameter_overridden(
        material, n, u.MaterialParameterAssociation.GLOBAL_PARAMETER))
        for n in u.MaterialEditingLibrary.get_static_switch_parameter_names(material)}
    return {'arrays': arrays, 'base_property_overrides':
            material.get_editor_property('base_property_overrides').export_text(),
            'static_switch_override_flags': switches}


def prepare_white(probe, plan, progress):
    import unreal as u
    global _prepared, _candidate_files
    require(_prepared is None, 'Never reprepare a prior test')
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    require(hashlib.sha256((root/'Scripts/PreviewStationOperationsFloors.py').read_bytes()).hexdigest() == UTILITY_SHA,
            'Frozen read-only utility source changed')
    require(hashlib.sha256((root/'.agent/local/StationRefinement/StationOperationsFloorProbe1.json').read_bytes()).hexdigest()
            == PROBE_SHA == plan['probe_sha256'] and probe['success'] and probe['preservation_pass'] and
            probe['scene_unchanged'] and plan['color'] == [1., 1., 1.] and
            plan['metallic'] == 0. and plan['roughness'] == .6,
            'Require exact native probe and selected low-gloss white recipe')
    edit = u.MaterialEditingLibrary
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    require(not editor.get_game_world(), 'Prepare before PIE')
    world = editor.get_editor_world()
    actors, rows = measured._floor(world, probe, u)
    from RefineStationOperationsDisplays import _state
    before = {a.get_path_name(): _state(a, u) for a in actors}
    source_slots = {}
    for _, _, row in rows:
        for slot, name in enumerate(row['materials']):
            source_slots.setdefault(name, set()).add(slot)
    require(len(source_slots) == 10 and all(len(s) == 1 for s in source_slots.values()),
            'Require ten exact source leaves and unambiguous native roles')
    sources, parents, local, destinations = {}, {}, {}, {}
    progress('inventory_inheritance', 'before')
    for leaf in sorted(source_slots):
        material = u.load_asset(leaf)
        chain = probe['materials'][leaf]['lineage']
        # Probe records every parent explicitly. Read actual objects without
        # assuming that a source leaf is a direct child of the native master.
        actual = []
        while isinstance(material, u.MaterialInstanceConstant):
            name = _path(material)
            require(name not in actual and len(actual) < 12, 'Cyclic/unbounded material inheritance')
            actual.append(name)
            parent = material.get_editor_property('parent')
            if name in sources:
                require(parents[name] == _path(parent), 'Source parent differs between leaves')
            else:
                sources[name] = material; parents[name] = _path(parent)
                local[name] = _local_overrides(material, u)
                destinations[name] = PRIVATE+'/MI_'+hashlib.sha256(name.encode()).hexdigest()[:16]
            material = parent
        require(_path(material) == MASTER, 'Unexpected original master in measured lineage')
        actual.append(MASTER)
        expected = [row['asset'] for row in chain]
        require(actual == expected, 'Native inheritance differs from exact source probe '+leaf)
    require(len(sources) == 25, 'Expected fifteen shared ancestors and ten distinct leaves')
    packages = [MASTER_COPY]+list(destinations.values())
    _candidate_files = [p for package in packages for p in _files(root, package)]
    require(unsaved_package_files_absent() and all(not u.EditorAssetLibrary.does_asset_exist(p) for p in packages),
            'Preserve any previous unsaved white test package')
    progress('inventory_inheritance', 'after', {'mic_count': len(sources), 'leaf_count': len(source_slots)})
    native = u.load_asset(MASTER)
    expected_graph = probe['master_graphs'][MASTER]
    require(measured._graph(native, u) == expected_graph and len(expected_graph['nodes']) == 377,
            'Native master changed from measured probe')
    tools = u.AssetToolsHelpers.get_asset_tools()
    progress('duplicate_master', 'before')
    clone = tools.duplicate_asset(MASTER_COPY.rsplit('/', 1)[1], PRIVATE, native)
    progress('duplicate_master', 'after')
    require(isinstance(clone, u.Material) and unsaved_package_files_absent(), 'Master duplication failed or saved')
    cloned_before = measured._graph(clone, u)
    require(measured._canonical_graph(cloned_before, _path(clone)) ==
            measured._canonical_graph(expected_graph, MASTER), 'Full master clone lost native graph/texture references')
    added = {}
    for name, kind, prop, settings in (
        (COLOR, u.MaterialExpressionVectorParameter, u.MaterialProperty.MP_BASE_COLOR,
         {'default_value': u.LinearColor(1., 1., 1., 1.)}),
        (METAL, u.MaterialExpressionScalarParameter, u.MaterialProperty.MP_METALLIC, {'default_value': 0.}),
        (ROUGH, u.MaterialExpressionScalarParameter, u.MaterialProperty.MP_ROUGHNESS, {'default_value': .6})):
        require(not any(n.get('parameter_name') == name for n in expected_graph['nodes']), 'White parameter name collision')
        node = edit.create_material_expression(clone, kind); require(node, 'Cannot create white parameter')
        node.set_editor_property('parameter_name', name)
        for key, value in settings.items():
            node.set_editor_property(key, value)
        require(edit.connect_material_property(node, '', prop), 'White output connection failed')
        added[name] = _path(node)
    progress('compile_master_once', 'before')
    errors = edit.recompile_material(clone)
    progress('compile_master_once', 'after', {'compile_errors': list(errors)})
    require(not errors, 'Private white shader compile failed '+str(errors))
    after_graph = measured._graph(clone, u)
    require({n['node']: n for n in cloned_before['nodes']} ==
            {n['node']: n for n in after_graph['nodes'] if n['node'] not in added.values()} and
            len(after_graph['nodes']) == 380 and
            all(after_graph['properties'][key] == cloned_before['properties'][key]
                for key in ('MP_NORMAL', 'MP_AMBIENT_OCCLUSION')) and
            after_graph['properties']['MP_BASE_COLOR'] == added[COLOR] and
            after_graph['properties']['MP_METALLIC'] == added[METAL] and
            after_graph['properties']['MP_ROUGHNESS'] == added[ROUGH] and
            after_graph['blend_mode'] == cloned_before['blend_mode'], 'Native Normal/AO/UV/graph changed')
    cache = {MASTER: clone}; ancestry = []

    def duplicate_chain(name):
        if name in cache:
            return cache[name]
        parent = duplicate_chain(parents[name])
        target = destinations[name]
        progress('duplicate_inherited_mic', 'before', {'source': name, 'private': target})
        child = tools.duplicate_asset(target.rsplit('/', 1)[1], PRIVATE, sources[name])
        progress('duplicate_inherited_mic', 'after', {'source': name, 'private': target})
        require(isinstance(child, u.MaterialInstanceConstant) and _local_overrides(child, u) == local[name],
                'Native MIC duplication lost local overrides '+name)
        progress('reparent_private_mic', 'before', {'source': name})
        edit.set_material_instance_parent(child, parent)
        progress('reparent_private_mic', 'after', {'source': name})
        require(child.get_editor_property('parent') == parent and _local_overrides(child, u) == local[name] and
                sources[name].get_editor_property('parent') == u.load_asset(parents[name]) and
                unsaved_package_files_absent(), 'Reparenting changed native/local overrides or saved a package')
        cache[name] = child
        ancestry.append({'source': name, 'source_parent': parents[name], 'private': _path(child),
                         'private_parent': _path(parent), 'local_overrides_preserved': True})
        return child

    leaves, receipts = {}, []
    for name in sorted(source_slots):
        child = duplicate_chain(name)
        original = probe['materials'][name]
        expected = {key: copy.deepcopy(original[key]) for key in ('scalars', 'vectors', 'textures', 'switches')}
        progress('verify_source_leaf', 'before', {'source': name})
        require(measured._same_parameters(measured._parameters(sources[name], u), expected), 'Original effective parameters changed')
        progress('verify_source_leaf', 'after', {'source': name})
        progress('set_three_white_leaf_values', 'before', {'source': name})
        edit.set_material_instance_vector_parameter_value(child, COLOR, u.LinearColor(1., 1., 1., 1.))
        edit.set_material_instance_scalar_parameter_value(child, METAL, 0.)
        edit.set_material_instance_scalar_parameter_value(child, ROUGH, .6)
        edit.update_material_instance(child)
        progress('set_three_white_leaf_values', 'after', {'source': name})
        expected['scalars'].update({METAL: 0., ROUGH: .6}); expected['vectors'][COLOR] = [1., 1., 1., 1.]
        progress('verify_private_leaf_readbacks', 'before', {'source': name})
        actual = measured._parameters(child, u)
        require(measured._same_parameters(actual, expected), 'White copy lost effective native parameters/texture/switch')
        # The three added leaf overrides are intentional; every original local
        # override entry and base override remains byte-for-byte unchanged.
        private_local = _local_overrides(child, u)
        for key, entries in local[name]['arrays'].items():
            require(all(entry in private_local['arrays'][key] for entry in entries), 'Original local override lost')
            require(len(private_local['arrays'][key]) == len(entries)+(2 if key == 'scalar_parameter_values' else
                    1 if key == 'vector_parameter_values' else 0), 'Unexpected private local override added')
        require(private_local['base_property_overrides'] == local[name]['base_property_overrides'] and
                private_local['static_switch_override_flags'] == local[name]['static_switch_override_flags'],
                'Base/static local overrides changed')
        progress('verify_private_leaf_readbacks', 'after', {'source': name})
        leaves[name] = child
        receipts.append({'source': name, 'native_slot': next(iter(source_slots[name])), 'private': _path(child),
                         'actual': actual, 'original_local_overrides_preserved': True,
                         'effective_native_parameters_preserved': True})
    require(len(cache) == 26 and len(leaves) == 10 and unsaved_package_files_absent() and before == {
        a.get_path_name(): _state(a, u) for a in u.GameplayStatics.get_all_actors_of_class(world, u.Actor)},
        'Unexpected counts/disk write/editor actor change')
    _prepared = {'master': clone, 'children': leaves, 'candidate_files': _candidate_files, 'probe': probe}
    progress('prepare_complete', 'after', {'private_masters': 1, 'private_mics': 25, 'white_leaves': 10})
    return {'saved': False, 'unsaved_master': _path(clone), 'private_mic_count': 25,
            'white_leaf_count': 10, 'native_original_nodes_preserved': 377, 'new_parameters': added,
            'native_normal_output': after_graph['properties']['MP_NORMAL'],
            'native_ao_output': after_graph['properties']['MP_AMBIENT_OCCLUSION'],
            'ancestry': ancestry, 'materials': receipts, 'editor_scene_unchanged': True,
            'candidate_package_files': [str(p) for p in _candidate_files],
            'candidate_package_files_absent': True, 'external_watchdog_required': True}


def apply_white(world, probe):
    import unreal as u
    from RefineStationOperationsDisplays import _state
    require(_prepared and unsaved_package_files_absent(), 'Require prepared unsaved white copy')
    actors, rows = measured._floor(world, probe, u)
    before = {a.get_path_name(): _state(a, u) for a in actors}; expected = copy.deepcopy(before)
    undo, changes = [], []
    try:
        for actor, component, row in rows:
            for slot, source in enumerate(row['materials']):
                child = _prepared['children'][source]
                undo.append((component, slot, component.get_material(slot)))
                component.set_material(slot, child)
                expected[actor.get_path_name()]['materials'][component.get_path_name()][slot] = _path(child)
                changes.append({'label': row['label'], 'component': component.get_path_name(),
                                'slot': slot, 'before': source, 'test': _path(child)})
        require(len(changes) == 420 and expected == {
            a.get_path_name(): _state(a, u) for a in u.GameplayStatics.get_all_actors_of_class(world, u.Actor)},
            'Unlisted actor/material/geometry/light/collision change')
    except Exception:
        for component, slot, original in reversed(undo):
            component.set_material(slot, original)
        raise
    return {'undo': undo, 'world': world, 'probe': probe, 'before': before,
            'receipt': {'option': 'SelectedWhite', 'changed_floor_actors': 84, 'changed_floor_slots': 420,
                        'changes': changes, 'native_normal_uv_ao_and_parameters_preserved': True,
                        'lighting_geometry_collision_unchanged': True, 'saved': False}}


def restore(handle):
    import unreal as u
    from RefineStationOperationsDisplays import _state
    actors, _ = measured._floor(handle['world'], handle['probe'], u, original=False)
    before = {a.get_path_name(): _state(a, u) for a in actors}; expected = copy.deepcopy(before)
    for component, slot, original in reversed(handle['undo']):
        component.set_material(slot, original)
        expected[component.get_owner().get_path_name()]['materials'][component.get_path_name()][slot] = _path(original)
    require(expected == {a.get_path_name(): _state(a, u)
                         for a in u.GameplayStatics.get_all_actors_of_class(handle['world'], u.Actor)} and
            verify_original(handle['world'], handle['probe']) and unsaved_package_files_absent(),
            'Original420 slots failed restoration or unlisted state changed')
    handle['undo'].clear()
