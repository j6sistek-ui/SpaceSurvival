"""Reuse exact saved white material; one measured floor slot/world reference.

Main1's historical ``before`` graph is the private clone before its three
output edits, not the original source graph. File digests retain that saved
proof; current typed graphs are guarded exactly within this author session.
"""
import AuthorStationWhiteFloorsMain as main
import PreviewStationOperationsFloors as measured
from RefineStationCargoThresholdFloor import apply_child, apply_main, scene, world_reference

require, path = measured.require, measured._path


def material_state(plan, u):
    source, white = u.load_asset(plan['source']), u.load_asset(plan['white'])
    source_master, private_master = u.load_asset(plan['master_source']), u.load_asset(plan['master_private'])
    require(isinstance(source, u.MaterialInstanceConstant) and isinstance(white, u.MaterialInstanceConstant) and
            isinstance(source_master, u.Material) and isinstance(private_master, u.Material),
            'Exact four existing material classes differ')
    return white, {'source': plan['source'], 'private': plan['white'],
                   'native_parameters': measured._parameters(source, u),
                   'actual': measured._parameters(white, u),
                   'source_parent': path(source.get_editor_property('parent')),
                   'private_parent': path(white.get_editor_property('parent')),
                   'source_use_material_attributes': bool(source_master.get_editor_property('use_material_attributes')),
                   'private_use_material_attributes': bool(private_master.get_editor_property('use_material_attributes')),
                   'current_master_graphs': {'source': main.graph(source_master, u),
                                             'private': main.graph(private_master, u)}}


def verify_white(plan, main_receipt, u, snapshot):
    """Read existing assets only; persist both current graphs before comparison."""
    white, actual = material_state(plan, u)
    snapshot('00_CurrentSourceMasterGraph', actual['current_master_graphs']['source'])
    snapshot('00_CurrentPrivateMasterGraph', actual['current_master_graphs']['private'])
    proof = main_receipt['master_graphs'][plan['master_graph_proof_index']]
    require(proof['source'] == plan['master_source'] and proof['private'] == plan['master_private'] and
            proof['native_normal_ao_uv_preserved'] and proof['only_three_outputs_replaced'] and
            proof['before']['asset'] == plan['master_private'], 'Exact saved Main1 clone provenance differs')
    require(actual['native_parameters'] == plan['native_parameters'] and actual['actual'] == plan['white_parameters'] and
            actual['source_parent'] == plan['master_source'] and actual['private_parent'] == plan['master_private'] and
            not actual['source_use_material_attributes'] and not actual['private_use_material_attributes'],
            'Existing saved material parameters/parents/attributes differ')
    actual['historical_source_vs_private_clone_graph_equality_claimed'] = False
    actual['historical_saved_graph_protected_by_exact_file_sha256'] = True
    actual['material_writes'] = 0
    return white, actual


def verify_unchanged(plan, before, u, snapshot):
    """Exact current-session graph, parameter, parent and class readbacks."""
    _, after = material_state(plan, u)
    snapshot('07_FinalSourceMasterGraph', after['current_master_graphs']['source'])
    snapshot('08_FinalPrivateMasterGraph', after['current_master_graphs']['private'])
    require(all(after[key] == before[key] for key in after),
            'Existing source/private graph, inherited parameter or parent changed during floor transaction')
    return True
