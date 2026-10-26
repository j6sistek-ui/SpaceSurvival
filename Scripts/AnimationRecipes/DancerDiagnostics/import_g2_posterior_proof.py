import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""New private native G2 hip proof; no production or prior proof overwrite."""
import hashlib
import json
import traceback
from pathlib import Path
import unreal as u


variant = os.environ.get('SS_G2_VARIANT', '')
assert variant in ('', 'glute_follow', 'glute_follow_240'), 'Unknown proof variant'
glute_follow = variant in ('glute_follow', 'glute_follow_240')
refined_rate = variant == 'glute_follow_240'
O = R / ('G2GluteFollowNative240' if refined_rate else 'G2GluteFollowNative' if glute_follow else 'G2PosteriorHip')
contract = json.loads((O / 'Export.json').read_text())
stem = 'G2GluteFollow240' if refined_rate else 'G2GluteFollow' if glute_follow else 'G2PosteriorHip'
BASE = '/Game/SpaceSurvival/Licensed/Vexa' + stem + 'Proof_20261026'
OLD = '/Game/SpaceSurvival/Licensed/VexaContinuousDistalProof_20261025'
assert 'WorkbenchNative/CharacterWorkbench' in u.Paths.get_project_file_path().replace('\\', '/')
for key in (('source', 'action', 'animation', 'rest') if glute_follow else ('source', 'animation', 'rest')):
    assert hashlib.sha256(Path(contract[key]).read_bytes()).hexdigest() == contract[key + '_sha256']
root = Path(u.Paths.project_content_dir()) / 'SpaceSurvival/Licensed'
protected = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for sub in ('VexaContinuousDistalProof_20261025', 'VexaHandIsolationProof_20261026', 'VexaZeroGSharedHipProof_20261026', *(['VexaG2PosteriorHipProof_20261026'] if glute_follow else []), *(['VexaG2GluteFollowProof_20261026'] if refined_rate else []))
             for p in (root / sub).rglob('*') if p.is_file()}
report = {'base': BASE, 'source_sha256': contract['source_sha256'], 'errors': []}
if glute_follow:
    report['action_sha256'] = contract['action_sha256']
try:
    lib = u.EditorAssetLibrary
    assert not lib.does_directory_exist(BASE), 'Preserve previous proof'
    skeleton = lib.duplicate_asset(OLD + '/SK_VexaContinuousDistalProof_Skeleton', BASE + '/SKEL_' + stem)
    assert skeleton and lib.save_loaded_asset(skeleton, False)
    u.SystemLibrary.execute_console_command(None, 'Interchange.FeatureFlags.Import.FBX 0')
    task = u.AssetImportTask()
    task.filename = contract['rest']; task.destination_path = BASE; task.destination_name = 'SK_' + stem
    task.automated = True; task.save = True; task.replace_existing = False
    opt = u.FbxImportUI(); opt.automated_import_should_detect_type = False
    opt.import_mesh = True; opt.import_as_skeletal = True; opt.import_animations = False
    opt.import_materials = False; opt.import_textures = False; opt.create_physics_asset = False
    opt.skeleton = skeleton; opt.mesh_type_to_import = u.FBXImportType.FBXIT_SKELETAL_MESH
    opt.skeletal_mesh_import_data.set_editor_property('import_morph_targets', True)
    opt.skeletal_mesh_import_data.set_editor_property('morph_threshold_position', .00001)
    task.options = opt
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = u.load_asset(BASE + '/' + task.destination_name)
    assert mesh and mesh.skeleton == skeleton
    editor = u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem)
    settings = editor.get_lod_build_settings(mesh, 0)
    settings.set_editor_property('bone_influence_limit', 12)
    editor.set_lod_build_settings(mesh, 0, settings)
    assert lib.save_loaded_asset(mesh, False)
    expected = {n.casefold() for n in contract['expected_morphs']}
    actual = {m.get_name().casefold() for m in mesh.get_editor_property('morph_targets') if m.get_name().casefold().startswith('review_g2_')}
    assert actual == expected, (expected - actual, actual - expected)
    task = u.AssetImportTask()
    task.filename = contract['animation']; task.destination_path = BASE; task.destination_name = 'A_' + stem
    task.automated = True; task.save = True; task.replace_existing = False
    opt = u.FbxImportUI(); opt.automated_import_should_detect_type = False
    opt.import_mesh = False; opt.import_animations = True; opt.import_materials = False; opt.import_textures = False
    opt.skeleton = skeleton; opt.mesh_type_to_import = u.FBXImportType.FBXIT_ANIMATION
    opt.anim_sequence_import_data.set_editor_property('use_default_sample_rate', False)
    opt.anim_sequence_import_data.set_editor_property('custom_sample_rate', contract['fps'])
    opt.anim_sequence_import_data.set_editor_property('preserve_local_transform', True)
    opt.anim_sequence_import_data.set_editor_property('delete_existing_morph_target_curves', True)
    task.options = opt
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    clip = u.load_asset(BASE + '/' + task.destination_name)
    assert clip and clip.get_editor_property('skeleton') == skeleton
    curves = {str(n).casefold() for n in u.AnimationLibrary.get_animation_curve_names(clip, u.RawCurveTrackTypes.RCT_FLOAT) if str(n).casefold().startswith('review_g2_')}
    assert curves == expected and abs(clip.sequence_length - contract['duration']) < .0001
    assert lib.save_loaded_asset(clip, False) and lib.save_loaded_asset(skeleton, False)
    report.update(mesh=mesh.get_path_name(), clip=clip.get_path_name(), curves=len(curves), morphs=len(actual), duration=clip.sequence_length)
    report['old_proofs_unchanged'] = all(Path(p).is_file() and hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in protected.items())
    assert report['old_proofs_unchanged']
    report['ok'] = True
except Exception:
    report['errors'].append(traceback.format_exc())
(O / 'NativeImport.json').write_text(json.dumps(report, indent=2))
print('G2_POSTERIOR_NATIVE_IMPORT', report.get('ok', False), report['errors'], flush=True)
