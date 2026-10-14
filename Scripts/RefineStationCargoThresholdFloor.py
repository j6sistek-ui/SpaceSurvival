"""One measured Cargo walking Cube; helpers never load/save/create content."""
import copy
import json
import re

import AuthorStationWhiteFloorsMain as main
import AuthorStationWhiteFloorsRemainder4 as retained
import PreviewStationOperationsFloors as measured

require, path = measured.require, measured._path


def world_reference(actor, u):
    value = actor.get_editor_property('world_asset')
    exported = (value.get_path_name() if isinstance(value, u.Object) else
                value.export_text() if callable(getattr(value, 'export_text', None)) else str(value))
    matches = re.findall(r'/Game/[A-Za-z0-9_/]+(?:\.[A-Za-z0-9_]+)?', exported)
    require(len(matches) == 1, 'Require one exact native instance world path: '+exported)
    return {'package': matches[0].split('.')[0], 'export': exported, 'native_type': type(value).__name__}


def scene(actors, world, u):
    """Typed full physical state; only the current package prefix is aliased."""
    return retained.scene(actors, world.get_path_name().split('.')[0], u)


def verify_white(plan, main_receipt, u):
    """Reuse one already saved material; no graph/parameter writes or compilation."""
    source, white = u.load_asset(plan['source']), u.load_asset(plan['white'])
    require(isinstance(source, u.MaterialInstanceConstant) and isinstance(white, u.MaterialInstanceConstant),
            'Exact existing native and white material classes differ')
    native = measured._parameters(source, u)
    actual = measured._parameters(white, u)
    require(native == plan['native_parameters'] and actual == plan['white_parameters'],
            'Existing source or white material effective parameters changed')
    require(path(source.get_editor_property('parent')) == plan['master_source'] and
            path(white.get_editor_property('parent')) == plan['master_private'],
            'Native/white inheritance no longer matches the saved actual source/Main1 masters')
    proof = main_receipt['master_graphs'][plan['master_graph_proof_index']]
    require(proof['source'] == plan['master_source'] and proof['private'] == plan['master_private'] and
            proof['native_normal_ao_uv_preserved'] and proof['only_three_outputs_replaced'],
            'Main1 exact native graph proof differs')
    source_master, private_master = u.load_asset(plan['master_source']), u.load_asset(plan['master_private'])
    require(isinstance(source_master, u.Material) and isinstance(private_master, u.Material) and
            not private_master.get_editor_property('use_material_attributes') and
            not source_master.get_editor_property('use_material_attributes') and
            main.graph(source_master, u) == proof['before'] and main.graph(private_master, u) == proof['after'],
            'Exact saved master graph/Normal/AO/UV wiring changed')
    return white, {'source': plan['source'], 'private': plan['white'], 'native_parameters': native,
                   'actual': actual, 'normal_ao_uv_graphs_unchanged': True, 'material_writes': 0}


def apply_child(world, actors, plan, white, u):
    require(world.get_path_name().split('.')[0] == plan['old_child'] and
            len(actors) == plan['old_actor_count'] == 2074, 'Exact completed Cargo source/population differs')
    before = scene(actors, world, u)
    key = 'WORLD'+plan['floor_actor_suffix']
    matches = [a for a in actors if a.get_path_name().endswith(plan['floor_actor_suffix'])]
    require(len(matches) == 1 and matches[0].get_actor_label() == plan['floor_label'] and
            matches[0].get_class() == u.StaticMeshActor.static_class() and
            before.get(key) == plan['floor_source_state'], 'Exact previously missed walking Cube identity/state changed')
    actor = matches[0]
    components = actor.get_components_by_class(u.StaticMeshComponent)
    require(len(components) == 1 and components[0].get_path_name() == actor.get_path_name()+plan['component_suffix'] and
            components[0].get_num_materials() == 1 and path(components[0].static_mesh) == '/Engine/BasicShapes/Cube.Cube' and
            path(components[0].get_material(0)) == plan['source'], 'Exact single Cube floor slot differs')
    component = components[0]
    expected = copy.deepcopy(before)
    expected[key]['materials'][key+plan['component_suffix']][0] = plan['white']
    component.set_material(0, white)
    require(scene(actors, world, u) == expected, 'Unlisted child actor/pose/collision/light/material change')
    return {'before': before, 'expected': expected, 'material_slot_allowlist': [
        {'actor': actor.get_path_name(), 'component': component.get_path_name(), 'label': plan['floor_label'],
         'mesh': path(component.static_mesh), 'slot': 0, 'before': plan['source'], 'after': plan['white']}]}


def apply_main(world, actors, plan, private_world, u):
    require(world.get_path_name().split('.')[0] == plan['main'], 'Require one latest saved Main world')
    before = scene(actors, world, u)
    spec = plan['main_instance']
    matches = [a for a in actors if a.get_path_name() == spec['actor']]
    require(len(matches) == 1 and isinstance(matches[0], u.LevelInstance) and
            matches[0].get_actor_label() == spec['label'] and
            matches[0].get_class().get_path_name() == plan['main_instance_class'],
            'Exact existing Cargo instance identity changed')
    actor = matches[0]
    original = world_reference(actor, u)
    cdo = u.get_default_object(actor.get_class())
    original_cdo = world_reference(cdo, u)
    require(original == spec['after'] and original_cdo == plan['original_cdo_world'] and
            path(private_world).split('.')[0] == plan['new_child'],
            'Exact completed Cargo world/CDO or new saved child differs')
    # All instance world references are independently guarded; generic physical
    # state deliberately does not stringify UObject values across map reloads.
    refs_before = {a.get_path_name(): world_reference(a, u) for a in actors if isinstance(a, u.LevelInstance)}
    actor.set_editor_property('world_asset', private_world)
    refs_expected = copy.deepcopy(refs_before)
    refs_expected[actor.get_path_name()] = world_reference(actor, u)
    require(refs_expected[actor.get_path_name()]['package'] == plan['new_child'] and
            world_reference(cdo, u) == original_cdo and scene(actors, world, u) == before,
            'Unlisted Main physical field or source Blueprint CDO change')
    refs_after = {a.get_path_name(): world_reference(a, u) for a in actors if isinstance(a, u.LevelInstance)}
    require(refs_after == refs_expected, 'Unlisted LevelInstance world-reference change')
    return {'before': before, 'expected': before, 'level_instance_worlds': refs_expected,
            'original_cdo_world': original_cdo,
            'level_instance_world_allowlist': [
                {'actor': actor.get_path_name(), 'label': spec['label'], 'before': original,
                 'after': refs_expected[actor.get_path_name()], 'private': plan['new_child']}]}
