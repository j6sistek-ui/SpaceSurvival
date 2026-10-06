"""Private cosmetic Director-rock arrival material; default is an asset read-only dry run.

Apply explicitly with -SSAuthorDirectorArrival. Existing private targets are backed
up before editing; the original photographic material is never saved or modified.
"""
import hashlib
import json
import shutil
import uuid
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
SOURCE = '/Game/SpaceSurvival/Materials/M_RockPhotographic'
BASE = '/Game/SpaceSurvival/Licensed/DirectorArrival'
MASTER = BASE + '/M_DirectorRockArrival'
INSTANCE = BASE + '/MI_DirectorRockArrival'
LIB = u.EditorAssetLibrary
EDIT = u.MaterialEditingLibrary


def disk_path(asset):
    return ROOT / 'Content' / (asset.removeprefix('/Game/') + '.uasset')


def main():
    apply = 'SSAuthorDirectorArrival' in u.SystemLibrary.get_command_line()
    source = u.load_asset(SOURCE)
    assert isinstance(source, u.Material), 'Photographic source material is missing'
    assert source.get_editor_property('blend_mode') == u.BlendMode.BLEND_OPAQUE
    assert not source.get_editor_property('use_material_attributes')
    source_file = disk_path(SOURCE)
    source_hash = hashlib.sha256(source_file.read_bytes()).hexdigest()
    out = ROOT / 'Artifacts/SurvivalQuality/DirectorArrival' / uuid.uuid4().hex
    out.mkdir(parents=True)
    backups = {}
    report = {'status': 'DRY_RUN_NO_ASSET_WRITES', 'source': SOURCE, 'source_sha256': source_hash,
              'master': MASTER, 'instance': INSTANCE, 'parameter': 'SpawnVisibility',
              'initial_coverage': 0.15, 'final_coverage': 1.0, 'arrival_seconds': 0.30,
              'native_dither_opacity_mask': True, 'opacity_mask_clip': 0.5,
              'required_saved_usage': ['Nanite'],
              'mask_expression': '0.17 + 0.83 * saturate(SpawnVisibility)',
              'backups': backups, 'source_unchanged': False, 'collision_or_gameplay_changes': False}
    if apply:
        for target in (MASTER, INSTANCE):
            path = disk_path(target)
            if path.exists():
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                shutil.copy2(path, out / (digest[:12] + '-' + path.name))
                backups[target] = digest
        master = LIB.load_asset(MASTER) if LIB.does_asset_exist(MASTER) else LIB.duplicate_asset(SOURCE, MASTER)
        assert isinstance(master, u.Material)
        master.set_editor_property('blend_mode', u.BlendMode.BLEND_MASKED)
        master.set_editor_property('dither_opacity_mask', True)
        master.set_editor_property('opacity_mask_clip_value', 0.5)
        nodes = EDIT.get_material_expressions(master)
        mask = next((node for node in nodes if str(node.get_editor_property('desc')) == 'SS Director arrival'), None)
        if mask is None:
            visibility = EDIT.create_material_expression(master, u.MaterialExpressionScalarParameter, 1900, 800)
            visibility.set_editor_property('parameter_name', 'SpawnVisibility')
            visibility.set_editor_property('default_value', 1.0)
            mask = EDIT.create_material_expression(master, u.MaterialExpressionCustom, 2200, 800)
            mask.set_editor_property('desc', 'SS Director arrival')
            mask.set_editor_property('description', 'SS Director arrival')
            mask.set_editor_property('output_type', u.CustomMaterialOutputType.CMOT_FLOAT1)
            pin = u.CustomInput()
            pin.set_editor_property('input_name', 'Visibility')
            mask.set_editor_property('inputs', [pin])
            assert EDIT.connect_material_expressions(visibility, '', mask, 'Visibility')
        # UE5.8 BlueNoiseCommon computes (mask - clip) + .83 * noise - .5.
        # This encoding gives linear coverage, including fully solid at visibility=1.
        mask.set_editor_property('code', 'return 0.17 + 0.83 * saturate(Visibility);')
        assert EDIT.connect_material_property(mask, '', u.MaterialProperty.MP_OPACITY_MASK)
        EDIT.set_base_material_usage(master, u.MaterialUsage.MATUSAGE_NANITE, True)
        assert EDIT.has_material_usage(master, u.MaterialUsage.MATUSAGE_NANITE)
        errors = EDIT.recompile_material(master)
        assert not errors, 'Private Director material compilation failed: ' + repr(errors)
        assert LIB.save_loaded_asset(master, False)
        instance = LIB.load_asset(INSTANCE) if LIB.does_asset_exist(INSTANCE) else u.AssetToolsHelpers.get_asset_tools().create_asset(
            INSTANCE.rsplit('/', 1)[1], BASE, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
        assert isinstance(instance, u.MaterialInstanceConstant)
        EDIT.set_material_instance_parent(instance, master)
        overrides = instance.get_editor_property('base_property_overrides')
        overrides.set_editor_property('override_blend_mode', True)
        overrides.set_editor_property('blend_mode', u.BlendMode.BLEND_MASKED)
        overrides.set_editor_property('override_opacity_mask_clip_value', True)
        overrides.set_editor_property('opacity_mask_clip_value', 0.5)
        instance.set_editor_property('base_property_overrides', overrides)
        EDIT.set_material_instance_scalar_parameter_value(instance, 'SpawnVisibility', 1.0)
        EDIT.set_material_usage_override(instance, u.MaterialUsage.MATUSAGE_NANITE, True, True)
        EDIT.update_material_instance(instance)
        assert EDIT.has_material_usage(instance, u.MaterialUsage.MATUSAGE_NANITE)
        assert LIB.save_loaded_asset(instance, False)
        report['status'] = 'AUTHORED_REQUIRES_NATIVE_TEST_AND_RENDER'
        report['target_sha256'] = {target: hashlib.sha256(disk_path(target).read_bytes()).hexdigest()
                                   for target in (MASTER, INSTANCE)}
    report['source_unchanged'] = hashlib.sha256(source_file.read_bytes()).hexdigest() == source_hash
    assert report['source_unchanged'], 'Original photographic material changed'
    (out / 'report.json').write_text(json.dumps(report, indent=2))
    u.log('DIRECTOR_ARRIVAL_REPORT ' + str(out))


if __name__ == '__main__':
    main()
