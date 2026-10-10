"""Read-only native reload of Joy121 and corrected Central planter assets."""
import unreal as u
import hashlib
import json
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / '.agent/local/StationRefinement/CpuJoy121'
OUT = WORK / 'JoyBlue114/Reload124.json'
DEST = '/Game/SpaceSurvival/Licensed/StationAssets/JoyLightBlue117'
REPORT = {'state': 'IN_PROGRESS', 'errors': [], 'checks': []}

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def file_for(asset):
    return ROOT / 'Content' / (asset.removeprefix('/Game/').split('.')[0] + '.uasset')

def checkpoint():
    OUT.write_text(json.dumps(REPORT, indent=2) + '\n')

def main():
    assert not OUT.exists(), 'Retain previous evidence; use a new receipt for another read.'
    complete = json.loads((WORK / 'JoyBlue114/Complete121.json').read_text())
    pilot = json.loads((WORK / 'JoyBlue114/Author117.json').read_text())
    planters = json.loads((WORK / 'CentralPlanter119/Receipt.json').read_text())
    assert not complete['errors'] and not planters['errors']
    all_hashes = dict(pilot['protected'])
    for row in complete['native_packages']:
        all_hashes[str(file_for(row['asset']))] = row['sha256']
        asset = u.load_asset(row['asset'])
        assert asset, row['asset']
    assert len(complete['native_packages']) == 147
    REPORT['checks'].append('147 Joy packages loaded')
    mesh = u.load_asset(DEST + '/Mesh/SK_JoyLightBlue')
    original = u.load_asset('/Game/SpaceSurvival/Licensed/StationAssets/JoyPurple/Mesh/SK_JoyPurple')
    assert mesh.skeleton == original.skeleton
    assert len(mesh.materials) == len(original.materials) == 18
    skin = []
    for slot in mesh.materials:
        if str(slot.material_slot_name).startswith('Joy_Purple_Std_Skin_'):
            color = u.MaterialEditingLibrary.get_material_instance_vector_parameter_value(slot.material_interface, 'Tint')
            assert all(abs(a-b) < 1e-6 for a,b in zip((color.r,color.g,color.b),(.46,.66,.84)))
            skin.append(str(slot.material_slot_name))
    assert len(skin) == 4
    REPORT['checks'].append('Original skeleton and 18 material slots; four light-blue skin overrides')
    for row in complete['clips']:
        anim = u.load_asset(row['target'])
        assert anim.get_editor_property('skeleton') == mesh.skeleton
        assert u.AnimationLibrary.get_num_frames(anim) == row['frames']
        assert abs(anim.get_editor_property('sequence_length') - row['duration']) < 0.0001
    REPORT['checks'].append('135 clips retain saved target skeleton, frame counts and durations')
    REPORT['grooms'] = []
    for row in complete['bindings']:
        binding = u.load_asset(row['binding'])
        assert binding.get_editor_property('target_skeletal_mesh') == mesh
        assert binding.get_editor_property('groom').get_path_name() == row['groom']
        groups = binding.get_editor_property('group_infos')
        REPORT['grooms'].append({'family': row['family'], 'groups': [str(g) for g in groups]})
        assert len(groups) > 0
    bp = u.load_asset(complete['blueprint'])
    assert bp.generated_class()
    sub = u.get_engine_subsystem(u.SubobjectDataSubsystem)
    api = u.SubobjectDataBlueprintFunctionLibrary
    components = {}
    for handle in sub.k2_gather_subobject_data_for_blueprint(bp):
        obj = api.get_object_for_blueprint(api.get_data(handle), bp)
        if isinstance(obj, (u.SkeletalMeshComponent, u.GroomComponent)):
            components[obj.get_path_name()] = obj
    bodies = [c for c in components.values() if isinstance(c, u.SkeletalMeshComponent)]
    hairs = [c for c in components.values() if isinstance(c, u.GroomComponent)]
    assert len(bodies) == 1 and len(hairs) == 2
    body = bodies[0]
    assert body.get_editor_property('skeletal_mesh_asset') == mesh
    assert body.get_editor_property('animation_mode') == u.AnimationMode.ANIMATION_SINGLE_NODE
    data = body.get_editor_property('animation_data')
    assert data.get_editor_property('anim_to_play').get_path_name().split('.')[0] == DEST + '/Animations/A_Joy_Idle'
    assert data.get_editor_property('saved_looping') and data.get_editor_property('saved_playing')
    REPORT['components'] = []
    for hair in hairs:
        binding = hair.get_editor_property('binding_asset')
        assert binding and binding.get_editor_property('target_skeletal_mesh') == mesh
        parent = hair.get_attach_parent()
        REPORT['components'].append({'name':hair.get_name(), 'binding':binding.get_path_name(), 'parent':parent.get_path_name() if parent else None})
    REPORT['checks'].append('Compiled preview Blueprint retains idle loop and two groom bindings')
    for row in planters['meshes']:
        mesh = u.load_asset(row['asset'])
        bounds = mesh.get_bounds()
        values = list(bounds.origin.to_tuple()) + list(bounds.box_extent.to_tuple())
        assert all(abs(a-b) < 1e-4 for a,b in zip(values,row['after_bounds']))
        assert [m.material_interface.get_path_name() if m.material_interface else None for m in mesh.static_materials] == row['materials_after']
        all_hashes[str(file_for(row['asset']))] = row['after_sha256']
    REPORT['checks'].append('Three repaired planter meshes reload with unchanged bounds and material slots')
    all_hashes[str(ROOT/'Content/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime.umap')] = planters['map_sha256']
    for path, expected in all_hashes.items():
        assert sha(Path(path)) == expected, path
    REPORT['protected_file_count'] = len(all_hashes)
    REPORT['map_sha256'] = planters['map_sha256']
    REPORT['dirty_maps'] = [p.get_path_name() for p in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
    REPORT['dirty_content'] = [p.get_path_name() for p in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
    REPORT['state'] = 'CPU_ASSET_RELOAD_PASS_RENDERED_REVIEW_PENDING'
    checkpoint()

try:
    main()
except Exception:
    REPORT['errors'].append(traceback.format_exc())
    REPORT['state'] = 'FAILED_READ_ONLY_CHECK'
    checkpoint()
    raise
print('RELOAD124_RESULT', REPORT['state'])
