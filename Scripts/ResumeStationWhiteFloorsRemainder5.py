"""Reuse exact saved attempt4 floor assets; no asset creation or source writes.

Only Cargo cross-load comparison aliases measured generated actor identities
and the 120 exact procedural cable quaternion pairs observed in attempt4.
Same-loaded floor edits remain the unchanged exact attempt4 transaction.
"""
import copy
import json
import re
from collections import Counter
import AuthorStationWhiteFloorsRemainder4 as original

PRIVATE = original.PRIVATE
require, path = original.require, original.path
native_api_preflight, scene, state = original.native_api_preflight, original.scene, original.state
verify_loaded, apply_loaded = original.verify_loaded, original.apply_loaded
CARGO = '/Game/OutpostSandbox/StationRefinement/Cargo/L_DockedCargo'


def canonical_crossload(value, rules):
    """Exact measured representations only; no rounding, tolerance or omissions."""
    result = copy.deepcopy(value)
    require(len(rules['quaternion_pairs']) == 120 and len(rules['generated_stems']) == 28,
            'Exact observed Cargo representation scope differs')
    for row in rules['quaternion_pairs']:
        keys = row['path']
        require(len(keys) == 5 and keys[1] == 'components' and keys[3] == 'rotation' and
                keys[4] in (0, 1, 2) and keys[0] in rules['rope_actors'] and
                keys[2].startswith(keys[0]+'.PCGSplineMeshComponent_SM_Cable_'),
                'Unreviewed procedural representation field')
        current = result
        for key in keys[:-1]:
            current = current[key]
        require(current[keys[-1]] in (row['before'], row['after']),
                'Unobserved procedural quaternion value '+str(keys))
        current[keys[-1]] = row['before']
    generated = {}
    for actor in list(result):
        stem = re.sub(r'_CAT_[0-9]+$', '_CAT', actor)
        if stem not in rules['generated_stems']:
            continue
        require(stem != actor, 'Generated actor identity lacks measured numeric suffix')
        # Every physical property remains in the fingerprint. Only this actor's
        # own object/component path is aliased; each original family stays distinct.
        fingerprint = json.dumps(result.pop(actor), sort_keys=True, allow_nan=False).replace(actor, 'ACTOR')
        generated.setdefault(stem, Counter())[fingerprint] += 1
    require(set(generated) == set(rules['generated_stems']) and
            all(sum(values.values()) == rules['generated_stems'][stem] for stem, values in generated.items()),
            'Measured generated actor family/count changed')
    result['MEASURED_GENERATED_ACTOR_FAMILIES'] = {
        stem: sorted(values.items()) for stem, values in generated.items()}
    return result


def coated_scene(source_scene, source, spec, leaves):
    """Add only the exact isolated floor slot references to the source snapshot."""
    expected = copy.deepcopy(source_scene)
    prefix = source+'.'+source.rsplit('/', 1)[1]
    changes = []
    for row in spec['rows']:
        actor = row['actor'].replace(prefix, 'WORLD')
        component = row['component'].replace(prefix, 'WORLD')
        private = path(leaves[row['role']])
        require(expected[actor]['materials'][component] == row['materials'] and row['slots'] == [0],
                'Exact copied floor slot/source differs')
        expected[actor]['materials'][component][0] = private
        target_prefix = spec['target']+'.'+spec['target'].rsplit('/', 1)[1]
        changes.append({'actor': row['actor'].replace(prefix, target_prefix), 'label': row['label'],
                        'component': row['component'].replace(prefix, target_prefix), 'slot': 0,
                        'source': row['materials'][0], 'private': private, 'role': row['role']})
    return expected, changes


def verify_finished_child(world, actors, source, spec, leaves, u):
    adjusted = copy.deepcopy(spec)
    for row in adjusted['rows']:
        row['materials'] = [path(leaves[row['role']])]
    return verify_loaded(world, actors, source, adjusted, u, True)


def reuse_materials(plan, failed, progress, u):
    """Validate exact saved bytes externally and full live graphs/parameters here."""
    require(failed['success'] is False and len(failed['saved_asset_sha256']) == 34 and
            len(failed['master_graphs']) == len(failed['materials']) == len(plan['roles']) == 17 and
            plan['private'] == PRIVATE and plan['color'] == [1., 1., 1.] and
            plan['metallic'] == 0. and plan['roughness'] == .6,
            'Require exact retained partial save/approved coating recipe')
    graphs = {row['role']: row for row in failed['master_graphs']}
    parameters = {row['role']: row for row in failed['materials']}
    leaves, verified = {}, []
    for identity, role in sorted(plan['roles'].items()):
        progress('verify_saved_material_pair', 'before', {'role': identity})
        graph, parameter = graphs[identity], parameters[identity]
        native, master = u.load_asset(role['material']), u.load_asset(role['master'])
        clone, leaf = u.load_asset(role['master_target']), u.load_asset(role['leaf_target'])
        require(native and isinstance(master, u.Material) and isinstance(clone, u.Material) and
                isinstance(leaf, u.MaterialInstanceConstant) and leaf.get_editor_property('parent') == clone and
                not master.get_editor_property('use_material_attributes') and
                not clone.get_editor_property('use_material_attributes') and
                path(master) == graph['source'] and path(clone) == graph['private'] and
                path(native) == parameter['source'] and path(leaf) == parameter['private'],
                'Exact saved material identity/class/parent differs')
        actual_source = original._extended_graph(master, u)
        require(original.measured._canonical_graph(actual_source, path(master)) ==
                original.measured._canonical_graph(graph['before'], path(clone)),
                'Original complete graph/defaults/textures/normal/AO/UV changed')
        require(original._extended_graph(clone, u) == graph['after'] and
                original._output_wiring(clone, u) == graph['private_output_pins'],
                'Saved private complete coating graph/output pins changed')
        if isinstance(native, u.MaterialInstanceConstant):
            require(native.get_editor_property('parent') == master and
                    original.white._local_overrides(native, u) == original.white._local_overrides(leaf, u),
                    'Original direct parent/private local override arrays changed')
            expected = original.measured._parameters(native, u)
        else:
            require(native == master and role['lineage'] == [{'asset': path(master), 'class': 'Material'}],
                    'Original direct Material lineage changed')
            expected = original._default_parameters(master, u)
            require(original._default_parameters(clone, u) == expected,
                    'Saved direct Material copied defaults changed')
        require(expected == parameter['native_effective_parameters'] == original.measured._parameters(leaf, u),
                'Exact source/private effective parameters changed')
        expressions = list(u.MaterialEditingLibrary.get_material_expressions(clone))
        customs = [node for node in expressions if isinstance(node, u.MaterialExpressionCustom)]
        whole = role['mask_kind'] == 'pure_child_floor_whole_surface'
        require(graph['added_node_count'] == (7 if whole else 11) and
                graph['whole_surface_coating'] == whole and
                graph['foundation_vertex_to_pixel_interpolators'] == (0 if whole else 2),
                'Saved whole-floor/foundation node role changed')
        if not whole:
            require(len(customs) == 1 and
                    customs[0].get_editor_property('code') == failed['mask_proofs'][identity]['code'] and
                    customs[0].get_editor_property('output_type') == u.CustomMaterialOutputType.CMOT_FLOAT1 and
                    [str(pin.get_editor_property('input_name')) for pin in customs[0].get_editor_property('inputs')] == ['P', 'N'],
                    'Saved exact foundation pixel mask code/type/input identity changed')
        leaves[identity] = leaf
        verified.append({'role': identity, 'master': path(clone), 'leaf': path(leaf),
                         'complete_graph_parameters_verified': True, 'created': False, 'resaved': False})
        progress('verify_saved_material_pair', 'after', {'role': identity})
    return leaves, verified
