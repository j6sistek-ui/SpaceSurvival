"""New-only candidate Pilot/Exit import using the immutable existing skeleton."""
from pathlib import Path
import hashlib
import json
import sys
import traceback
import unreal as u


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'ContentSource/PilotGripPoseCandidate'
BASE = '/Game/SpaceSurvival/Character'
LIB = u.EditorAssetLibrary
VERSION = 'GripPoseRelease1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_rows():
    report = json.loads((SOURCE / 'SourcePairValidation.json').read_text(encoding='utf-8'))
    assert report['status'] == 'SOURCE_PAIR_TRANSPORT_VALIDATED_NOT_UNREAL_IMPORTED' and (not report['errors'])
    review = json.loads((SOURCE / 'Review.json').read_text(encoding='utf-8'))
    assert report['clips'] == review['clips'], 'Source review has stale clip identities'
    for row in report['clips']:
        assert sha(SOURCE / row['file']) == row['sha256']
    for path, digest in json.loads((SOURCE / 'PairedRelease.json').read_text(encoding='utf-8'))['protected_sha256'].items():
        assert sha(ROOT / path) == digest, path
    return report['clips']


def validate(clip, row, skeleton):
    name = Path(row['file']).stem
    seconds = 4.0 if row['kind'] == 'Pilot' else 2.4
    assert isinstance(clip, u.AnimSequence)
    assert clip.get_path_name().split('.')[0] == BASE + '/A_' + name
    assert clip.get_editor_property('skeleton') == skeleton
    assert abs(clip.get_editor_property('sequence_length') - seconds) < 0.001
    assert not clip.get_editor_property('enable_root_motion') and (not clip.get_editor_property('force_root_lock'))
    assert LIB.get_metadata_tag(clip, 'SSGripPairVersion') == VERSION
    assert LIB.get_metadata_tag(clip, 'SSGripPairSourceSHA256') == row['sha256']
    path = ROOT / ('Content/SpaceSurvival/Character/A_' + name + '.uasset')
    assert path.exists()
    return {
        'path': clip.get_path_name(),
        'seconds': float(clip.get_editor_property('sequence_length')),
        'skeleton': skeleton.get_path_name(),
        'root_motion': False,
        'force_root_lock': False,
        'source_sha256': row['sha256'],
        'package_sha256': sha(path),
        'package_bytes': path.stat().st_size,
    }


def main(validate_only=False):
    (ROOT / 'Saved/Validation').mkdir(parents=True, exist_ok=True)
    protected = {p: sha(p) for folder in ('Source', 'Config', 'Content') for p in (ROOT / folder).rglob('*') if p.is_file()}
    record = {
        'status': 'FAILED',
        'engine': u.SystemLibrary.get_engine_version(),
        'errors': [],
        'clips': [],
        'limits': [
            'New candidate clips only; runtime selection unchanged',
            'Native rendered combined pose review is separate',
            'Initial seated skin/grip intersections and existing fur/claw limitations remain',
        ],
    }
    try:
        skeleton = LIB.load_asset(BASE + '/SK_Acornaut').get_editor_property('skeleton')
        for row in source_rows():
            name = Path(row['file']).stem
            path = BASE + '/A_' + name
            clip = LIB.load_asset(path)
            if not clip:
                assert not validate_only, 'Candidate missing from fresh persisted reload'
                pipeline = u.new_object(u.InterchangeGenericAssetsPipeline, name='SS' + name + 'OnlyImport')
                for key, value in {
                    'asset_name': 'A_' + name,
                    'use_source_name_for_asset': False,
                    'asset_type_sub_folders': False,
                    'scene_name_sub_folder': False,
                }.items():
                    pipeline.set_editor_property(key, value)
                common = pipeline.get_editor_property('common_skeletal_meshes_and_animations_properties')
                for key, value in {
                    'import_only_animations': True,
                    'skeleton': skeleton,
                    'try_auto_select_skeleton': False,
                    'use_t0_as_ref_pose': False,
                }.items():
                    common.set_editor_property(key, value)
                settings = pipeline.get_editor_property('mesh_pipeline')
                for key, value in {
                    'import_skeletal_meshes': False,
                    'import_static_meshes': False,
                    'create_physics_asset': False,
                    'update_skeleton_reference_pose': False,
                }.items():
                    settings.set_editor_property(key, value)
                animation = pipeline.get_editor_property('animation_pipeline')
                animation.set_editor_property('import_animations', True)
                animation.set_editor_property('import_bone_tracks', True)
                animation.set_editor_property('use30_hz_to_bake_bone_animation', True)
                material = pipeline.get_editor_property('material_pipeline')
                material.set_editor_property('import_materials', False)
                material.get_editor_property('texture_pipeline').set_editor_property('import_textures', False)
                params = u.ImportAssetParameters()
                params.set_editor_property('is_automated', True)
                params.set_editor_property('replace_existing', False)
                params.set_editor_property('override_pipelines', [u.SoftObjectPath(pipeline.get_path_name())])
                manager = u.InterchangeManager.get_interchange_manager_scripted()
                imported = manager.import_asset(BASE, manager.create_source_data(str(SOURCE / row['file'])), params)
                assert len(imported) == 1 and isinstance(imported[0], u.AnimSequence), 'Expected one animation only'
                clip = imported[0]
                if clip.get_path_name().split('.')[0] != path:
                    assert not LIB.does_asset_exist(path)
                    assert LIB.rename_asset(clip.get_path_name(), path)
                    clip = LIB.load_asset(path)
                clip.set_editor_property('enable_root_motion', False)
                clip.set_editor_property('force_root_lock', False)
                LIB.set_metadata_tag(clip, 'SSGripPairVersion', VERSION)
                LIB.set_metadata_tag(clip, 'SSGripPairSourceSHA256', row['sha256'])
                assert LIB.save_loaded_asset(clip, only_if_is_dirty=False)
            record['clips'].append(validate(clip, row, skeleton))
        assert all((sha(p) == h for p, h in protected.items())), 'Existing Source/Config/Content modified'
        record['protected_existing_files_unchanged'] = len(protected)
        record['status'] = 'GRIP_PAIR_FRESH_PERSISTED_VALIDATED_NOT_ADOPTED' if validate_only else 'GRIP_PAIR_IMPORTED_SAVED_NOT_ADOPTED'
    except Exception as error:
        record['errors'].append(str(error))
        u.log_error(traceback.format_exc())
    receipt_name = 'PilotGripFitPersisted.json' if validate_only else 'PilotGripFitImport.json'
    (ROOT / 'Saved/Validation' / receipt_name).write_text(
        json.dumps(record, indent=2) + '\n',
        encoding='utf-8',
        newline='\n',
    )
    if record['errors']:
        raise RuntimeError('Grip pair import/validation failed')
    u.log('GRIP_PAIR_VALIDATION_FINISHED')
    return record


if __name__ == '__main__':
    main('--validate-only' in sys.argv)
