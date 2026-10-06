"""Assign reviewed local card derivatives to two existing cabinet screen slots.

No engine launch, actor transforms, original package writes or saves. The lead
owns native execution, explicit saving and the final in-room visual check.
"""
import hashlib
import json
import struct
from pathlib import Path

from RefineStationSocialVisualFinish import _values
from StationRefinementSupport import transform_record


MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
BASE = '/Game/OutpostSandbox/StationRefinement/ArcadeAttract20261006V2'
ORIGINAL = '/Game/OutpostSandbox/StationRefinement/Arcade20261006'
MANIFEST = '.agent/local/ArcadeGeneration/AttractCardsV2/approved_v2/manifest.json'
MANIFEST_SHA = 'ecbf086267083526912da2873142285ac0e3bd428f58fb1fe873b9333f099dd0'
NAMES = ('AcornautArcade', 'AcornautHyperRun')


def _require(condition, message):
    if not condition:
        raise RuntimeError(message)


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _path(asset):
    return asset.get_path_name().split('.')[0] if asset else None


def apply(ctx, expected_map_sha256):
    import unreal as u
    root = Path(u.Paths.project_dir()).resolve()
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    _require(world.get_path_name().split('.')[0] == MAP, 'Wrong owner preview for arcade cards')
    map_file = root / ('Content/' + MAP[6:] + '.umap')
    _require(_sha(map_file) == expected_map_sha256, 'Saved owner preview changed')
    receipt_path = root / MANIFEST
    _require(_sha(receipt_path) == MANIFEST_SHA, 'Reviewed card receipt changed')
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    _require(set(receipt['outputs']) == set(NAMES), 'Only the two reviewed cards may be assigned')
    source_hashes = dict(receipt['source_sha256'])
    source_hashes[str(receipt_path)] = MANIFEST_SHA
    source_hashes[str(root/'ContentSource/LocalArcade20261006/finish_attract_cards.py')] = receipt['recipe_sha256']
    rows = []
    for name in NAMES:
        row = receipt['outputs'][name]
        source = Path(row['path']).resolve()
        _require(source.parent == receipt_path.parent and row['dimensions'] == [1024, 768],
                 'Unexpected reviewed texture path or dimensions')
        raw = source.read_bytes()
        _require(raw[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', raw[16:24]) == (1024, 768),
                 'Reviewed card is not the expected PNG')
        source_hashes[str(source)] = row['sha256']
        label = 'Refine/LocalArcade/' + name + '/Body'
        _require(row['actor_label'] == label and row['material_slot'] == 'M_' + name + '_Screen',
                 'Reviewed card actor/slot changed')
        actors = [a for a in ctx.actors if a.get_actor_label() == label]
        _require(len(actors) == 1, 'Expected exactly one placed cabinet: ' + label)
        component = actors[0].get_component_by_class(u.StaticMeshComponent)
        mesh_path = ORIGINAL + '/' + name + '/Meshes/SM_' + name + '_Body'
        material_path = ORIGINAL + '/' + name + '/Materials/M_' + name + '_' + name + '_Screen'
        _require(component and _path(component.static_mesh) == mesh_path,
                 'Placed cabinet mesh changed: ' + label)
        slots = list(component.static_mesh.get_editor_property('static_materials'))
        _require(len(slots) > 4 and str(slots[4].get_editor_property('material_slot_name')) == row['material_slot']
                 and _path(component.get_material(4)) == material_path,
                 'Placed cabinet slot4 is not the original screen: ' + label)
        parent = component.get_material(4)
        for asset_path in (mesh_path, material_path):
            file = root / ('Content/' + asset_path[6:] + '.uasset')
            source_hashes[str(file)] = _sha(file)
        for kind in ('T_', 'MI_'):
            _require(not u.EditorAssetLibrary.does_asset_exist(BASE + '/' + kind + name + '_AttractV2'),
                     'Preserve an existing card derivative: ' + name)
        rows.append((name, source, label, component, parent))
    _require(all(_sha(Path(path)) == value for path, value in source_hashes.items()),
             'Reviewed artwork/source recipe changed before authoring')
    poses = {a.get_path_name(): transform_record(a) for a in ctx.actors}
    edit, dirty, assignments = u.MaterialEditingLibrary, [], []
    for name, source, label, component, parent in rows:
        before_slots = [_path(m) for m in component.get_materials()]
        task = u.AssetImportTask()
        texture_name = 'T_' + name + '_AttractV2'
        for key, value in {'filename': str(source), 'destination_path': BASE,
                           'destination_name': texture_name, 'automated': True,
                           'replace_existing': False, 'save': False}.items():
            task.set_editor_property(key, value)
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        texture = u.load_asset(BASE + '/' + texture_name)
        _require(isinstance(texture, u.Texture2D), 'Card texture import failed: ' + name)
        texture.set_editor_property('srgb', True)
        texture.set_editor_property('compression_settings', u.TextureCompressionSettings.TC_BC7)
        texture.set_editor_property('lod_group', u.TextureGroup.TEXTUREGROUP_WORLD)
        texture.set_editor_property('mip_gen_settings', u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)
        material = u.AssetToolsHelpers.get_asset_tools().create_asset(
            'MI_' + name + '_AttractV2', BASE, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
        _require(material, 'Card material creation failed: ' + name)
        edit.set_material_instance_parent(material, parent)
        edit.update_material_instance(material)
        _require(material.get_editor_property('parent') == parent, 'Card parent readback mismatch')
        baseline = _values(edit, material)
        _require('BaseColorTexture' in baseline['textures'], 'Original screen texture parameter missing')
        original_texture = baseline['textures']['BaseColorTexture']
        _require(original_texture and original_texture.startswith(ORIGINAL + '/'),
                 'Original screen texture source changed')
        original_file = root / ('Content/' + original_texture[6:] + '.uasset')
        source_hashes[str(original_file)] = _sha(original_file)
        # UE5.8's setter always returns false. Native readback is authoritative.
        edit.set_material_instance_texture_parameter_value(material, 'BaseColorTexture', texture)
        edit.update_material_instance(material)
        expected = {**baseline, 'textures': {**baseline['textures'], 'BaseColorTexture': _path(texture)}}
        _require(_values(edit, material) == expected and
                 edit.get_material_instance_texture_parameter_value(material, 'BaseColorTexture') == texture,
                 'Card changed an unrelated material value or failed texture readback')
        component.set_material(4, material)
        expected_slots = list(before_slots)
        expected_slots[4] = _path(material)
        _require([_path(m) for m in component.get_materials()] == expected_slots,
                 'Card assignment changed more than the intended screen slot')
        dirty.extend((texture, material))
        assignments.append({'label': label, 'slot_index': 4, 'slot_name': 'M_' + name + '_Screen',
                            'source_material': _path(parent), 'material': material.get_path_name(),
                            'texture': texture.get_path_name(), 'source_png': str(source),
                            'sha256': source_hashes[str(source)], 'effective_parameters': expected})
    _require(all(transform_record(a) == poses[a.get_path_name()] for a in ctx.actors),
             'Card authoring changed actor placement')
    _require(all(_sha(Path(path)) == value for path, value in source_hashes.items()),
             'Card authoring changed original source files/packages')
    _require(_sha(map_file) == expected_map_sha256, 'Card helper unexpectedly saved owner map')
    return {'dirty_assets': dirty, 'assignments': assignments, 'source_sha256': source_hashes,
            'protected_actor_count': len(poses), 'map_before_sha256': expected_map_sha256,
            'saved': False, 'gameplay': 'Static decorative graphics only; no game/input wiring',
            'render_acceptance': 'Pending native room capture'}
