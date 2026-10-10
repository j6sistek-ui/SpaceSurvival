"""Measured main-station floor material transaction. Root owns save/process.

Streamed apartment/cargo interiors and mixed owner foundation remain separate.
No actor, mesh, instance, collision, light, wall or ceiling change is permitted.
"""
import copy
import hashlib
import json
from pathlib import Path
import PreviewStationOperationsFloors as measured
import PreviewStationOperationsWhiteFloor as white

PRIVATE = '/Game/OutpostSandbox/StationRefinement/StationWhiteFloorsMain20261007'
COLOR, METAL, ROUGH = 'StationFloorWhiteColor', 'StationFloorWhiteMetallic', 'StationFloorWhiteRoughness'
require = measured.require
path = measured._path


def transform(value):
    return {key: list(part.to_tuple()) for key, part in
            (('location', value.translation), ('rotation', value.rotation), ('scale', value.scale3d))}


def graph(master, u):
    value = measured._graph(master, u)
    for node in u.MaterialEditingLibrary.get_material_expressions(master):
        row = next(r for r in value['nodes'] if r['node'] == path(node))
        kind = node.get_class().get_name()
        if kind == 'MaterialExpressionConstant':
            row['constant'] = float(node.get_editor_property('r'))
        elif kind in ('MaterialExpressionConstant3Vector', 'MaterialExpressionConstant4Vector'):
            color = node.get_editor_property('constant')
            row['constant'] = [float(getattr(color, c)) for c in ('r', 'g', 'b', 'a')]
    return value


def apply(ctx, inventory, plan, progress):
    import unreal as u
    from RefineStationOperationsPodiumFinish import state
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    require(not editor.get_game_world() and inventory['success'] and inventory['read_only'] and
            inventory['scene_unchanged'] and plan['private'] == PRIVATE and
            plan['color'] == [1., 1., 1.] and plan['metallic'] == 0. and plan['roughness'] == .6,
            'Require preserved actual inventory and approved low-gloss white recipe')
    actors = list(ctx.eas.get_all_level_actors())
    original = {a.get_path_name(): state(a, u) for a in actors}
    components = {c.get_path_name(): c for a in actors for c in a.get_components_by_class(u.StaticMeshComponent)}
    targets = []
    for row in plan['rows']:
        c = components.get(row['component'])
        require(c and c.get_owner().get_path_name() == row['actor'] and
                c.get_owner().get_actor_label() == row['label'] and path(c.static_mesh) == row['mesh'] and
                [path(m) for m in c.get_materials()] == row['materials'] and
                str(c.get_collision_enabled()) == row['collision'] and c.is_visible() and
                transform(c.get_owner().get_actor_transform()) == row['actor_transform'] and
                transform(c.get_world_transform()) == row['world_transform'] and
                transform(c.get_relative_transform()) == row['relative_transform'],
                'Measured floor component/material/physical identity differs '+row['label'])
        if isinstance(c, u.InstancedStaticMeshComponent):
            require(c.get_instance_count() == row['instance_count'] and
                    [transform(c.get_instance_transform(index, True)) for index in range(c.get_instance_count())] ==
                    row['instance_world_transforms'], 'Native floor instance transforms differ '+row['label'])
        targets.append((c, row))
    require(len(targets) == plan['expected_component_count'] == 1022 and
            sum(len(r['slots']) for _, r in targets) == plan['expected_slot_count'] == 5017,
            'Floor whitelist count differs')
    leaf_names = sorted({r['materials'][s] for _, r in targets for s in r['slots']})
    require(leaf_names == plan['leaves'] and len(leaf_names) == 44, 'Measured source floor leaves differ')
    edit, tools = u.MaterialEditingLibrary, u.AssetToolsHelpers.get_asset_tools()
    sources, parents, local, destinations = {}, {}, {}, {}
    masters = {}
    for leaf in leaf_names:
        current = u.load_asset(leaf); actual = []
        for entry in inventory['materials'][leaf]['lineage']:
            require(path(current) == entry['asset'] and current.get_class().get_name() == entry['class'],
                    'Actual native inheritance differs '+leaf)
            actual.append(path(current))
            if isinstance(current, u.MaterialInstanceConstant):
                parent = current.get_editor_property('parent')
                if path(current) not in sources:
                    sources[path(current)] = current; parents[path(current)] = path(parent)
                    local[path(current)] = white._local_overrides(current, u)
                    destinations[path(current)] = PRIVATE+'/MI_'+hashlib.sha256(path(current).encode()).hexdigest()[:16]
                current = parent
            else:
                require(isinstance(current, u.Material), 'Invalid native floor master')
                masters[path(current)] = current
        require(len(actual) == len(set(actual)), 'Cyclic inherited floor material')
    require(len(sources) == plan['expected_inherited_mic_count'] == 49 and
            sorted(masters) == plan['masters'] and len(masters) == 4, 'Private inheritance count differs')
    destinations.update({name: PRIVATE+'/M_'+hashlib.sha256(name.encode()).hexdigest()[:16] for name in masters})
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    candidate_files = [root/('Content/'+target[6:]+suffix) for target in destinations.values()
                       for suffix in ('.uasset', '.uexp', '.ubulk')]
    require(len(destinations) == 53 and all(not p.exists() for p in candidate_files) and
            all(not u.EditorAssetLibrary.does_asset_exist(dest) for dest in destinations.values()),
            'Preserve existing private material attempt')
    cache, dirty, graph_receipts, ancestry = {}, [], [], []
    for name, native in sorted(masters.items()):
        progress('duplicate_full_native_master', 'before', {'source': name})
        expected_graph = inventory['master_graphs'][name]
        require(not native.get_editor_property('use_material_attributes') and graph(native, u) == expected_graph,
                'Require actual direct material outputs; source attributes/graph differ')
        target = destinations[name]
        clone = tools.duplicate_asset(target.rsplit('/', 1)[1], PRIVATE, native)
        require(isinstance(clone, u.Material) and not clone.get_editor_property('use_material_attributes'),
                'Native master duplicate failed or material attributes enabled')
        before = graph(clone, u)
        require(measured._canonical_graph(before, path(clone)) == measured._canonical_graph(expected_graph, name),
                'Full master duplicate lost source graph/wiring/texture/constants')
        added = {}
        for parameter, kind, prop, settings in (
            (COLOR, u.MaterialExpressionVectorParameter, u.MaterialProperty.MP_BASE_COLOR,
             {'default_value': u.LinearColor(1., 1., 1., 1.)}),
            (METAL, u.MaterialExpressionScalarParameter, u.MaterialProperty.MP_METALLIC, {'default_value': 0.}),
            (ROUGH, u.MaterialExpressionScalarParameter, u.MaterialProperty.MP_ROUGHNESS, {'default_value': .6})):
            require(not any(n.get('parameter_name') == parameter for n in before['nodes']), 'White parameter collision')
            node = edit.create_material_expression(clone, kind); require(node, 'Cannot add white floor parameter')
            node.set_editor_property('parameter_name', parameter)
            for key, value in settings.items(): node.set_editor_property(key, value)
            require(edit.connect_material_property(node, '', prop), 'White property connection failed')
            added[parameter] = path(node)
        progress('compile_master_once', 'before', {'source': name})
        errors = edit.recompile_material(clone)
        require(not errors, 'Private floor shader compilation failed '+str(errors))
        after = graph(clone, u)
        require({n['node']: n for n in before['nodes']} ==
                {n['node']: n for n in after['nodes'] if n['node'] not in added.values()} and
                len(after['nodes']) == len(before['nodes'])+3 and after['blend_mode'] == before['blend_mode'] and
                all(after['properties'][key] == before['properties'][key] for key in ('MP_NORMAL','MP_AMBIENT_OCCLUSION')) and
                after['properties']['MP_BASE_COLOR'] == added[COLOR] and
                after['properties']['MP_METALLIC'] == added[METAL] and
                after['properties']['MP_ROUGHNESS'] == added[ROUGH], 'Native normal/AO/UV/detail graph changed')
        cache[name] = clone; dirty.append(clone)
        graph_receipts.append({'source': name, 'private': path(clone), 'original_node_count':len(before['nodes']),
                               'native_normal_ao_uv_preserved':True, 'only_three_outputs_replaced':True,
                               'source_use_material_attributes':False, 'private_use_material_attributes':False,
                               'before':before,'after':after})
        progress('compile_master_once', 'after', {'source': name})
    def duplicate_chain(name):
        if name in cache: return cache[name]
        require(name in sources, 'Unmeasured material ancestor '+name)
        parent = duplicate_chain(parents[name]); target = destinations[name]
        progress('duplicate_inherited_mic', 'before', {'source': name})
        child = tools.duplicate_asset(target.rsplit('/', 1)[1], PRIVATE, sources[name])
        require(isinstance(child,u.MaterialInstanceConstant) and white._local_overrides(child,u) == local[name],
                'Duplicated native local overrides differ '+name)
        edit.set_material_instance_parent(child,parent)
        require(child.get_editor_property('parent') == parent and white._local_overrides(child,u) == local[name] and
                path(sources[name].get_editor_property('parent')) == parents[name],
                'Reparented private child changed source/local overrides')
        cache[name]=child; dirty.append(child)
        ancestry.append({'source':name,'source_parent':parents[name],'private':path(child),'private_parent':path(parent),
                         'local_overrides_preserved':True})
        progress('duplicate_inherited_mic','after',{'source':name})
        return child
    leaves, material_receipts = {}, []
    for name in leaf_names:
        child = duplicate_chain(name); expected = copy.deepcopy(inventory['materials'][name]['parameters'])
        require(expected and measured._same_parameters(measured._parameters(sources[name],u),expected),
                'Original source effective parameters differ '+name)
        edit.set_material_instance_vector_parameter_value(child,COLOR,u.LinearColor(1.,1.,1.,1.))
        edit.set_material_instance_scalar_parameter_value(child,METAL,0.)
        edit.set_material_instance_scalar_parameter_value(child,ROUGH,.6)
        edit.update_material_instance(child)
        expected['vectors'][COLOR]=[1.,1.,1.,1.];expected['scalars'].update({METAL:0.,ROUGH:.6})
        actual=measured._parameters(child,u)
        require(measured._same_parameters(actual,expected),'Private floor lost effective native texture/switch/parameter '+name)
        actual_local=white._local_overrides(child,u)
        for key,values in local[name]['arrays'].items():
            require(all(v in actual_local['arrays'][key] for v in values) and
                    len(actual_local['arrays'][key]) == len(values)+(2 if key=='scalar_parameter_values' else
                    1 if key=='vector_parameter_values' else 0),'Unexpected private local override changes')
        require(actual_local['base_property_overrides']==local[name]['base_property_overrides'] and
                actual_local['static_switch_override_flags']==local[name]['static_switch_override_flags'],
                'Native base/static override changed')
        leaves[name]=child; material_receipts.append({'source':name,'private':path(child),'actual':actual,
                                                     'native_parameters_textures_switches_preserved':True})
        progress('verify_white_leaf','after',{'source':name})
    require(len(dirty)==len(cache)==53 and all(not p.exists() for p in candidate_files) and
            original=={a.get_path_name():state(a,u) for a in ctx.eas.get_all_level_actors()},
            'Preparation changed scene, disk or private asset count')
    expected=copy.deepcopy(original);changes=[];undo=[]
    try:
        for component,row in targets:
            for slot in row['slots']:
                source=row['materials'][slot];child=leaves[source]
                undo.append((component,slot,component.get_material(slot)))
                component.set_material(slot,child)
                expected[row['actor']]['materials'][row['component']][slot]=path(child)
                changes.append({'actor':row['actor'],'label':row['label'],'component':row['component'],'slot':slot,
                                'source':source,'private':path(child),'room':row['room']})
        require(len(changes)==5017 and expected=={a.get_path_name():state(a,u) for a in ctx.eas.get_all_level_actors()},
                'Unlisted geometry/mesh/pose/collision/light/material/service change')
    except Exception:
        for component,slot,value in reversed(undo):component.set_material(slot,value)
        raise
    progress('floor_refs_complete','after',{'components':1022,'slots':5017,'private_assets':53})
    return {'dirty_assets':dirty,'material_slot_allowlist':changes,'master_graphs':graph_receipts,'ancestry':ancestry,
            'materials':material_receipts,'new_actor_count':0,'new_light_count':0,'saved':False,
            'coverage_groups':plan['coverage_groups'],'exclusions':plan['exclusions'],
            'candidate_package_files':[str(p) for p in candidate_files]}
