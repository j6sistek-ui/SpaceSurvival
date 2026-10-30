"""New private mesh with local green tangent mask; keep the original import."""
import hashlib
import json
import os
from pathlib import Path
import unreal as u

project = Path(os.environ.get('SS_ANIMATION_PROJECT', str(Path.home()/'SpaceSurvival'))).resolve()
out = project/'.agent/local/AnimationReview_20261025/G1ShoulderCapNative240'
assert 'WorkbenchNative/CharacterWorkbench' in u.Paths.get_project_file_path().replace('\\', '/')
contract = json.loads((out/'LocalNormalsExport.json').read_text())
previous = json.loads((out/'NativeImport.json').read_text())
assert previous['ok'] and contract['source_sha256'] == previous['source_sha256']
assert hashlib.sha256(Path(contract['rest']).read_bytes()).hexdigest() == contract['rest_sha256']
base = previous['base']
name = 'SK_G1ShoulderCap240_LocalNormals'
assert not u.EditorAssetLibrary.does_asset_exist(base+'/'+name)
root = Path(u.Paths.project_content_dir()).resolve()/'SpaceSurvival/Licensed'
protected = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for folder in root.glob('Vexa*Proof*') for p in folder.glob('*.uasset')}
original = u.load_asset(previous['mesh'])
assert original
u.SystemLibrary.execute_console_command(None, 'Interchange.FeatureFlags.Import.FBX 0')
task = u.AssetImportTask()
task.filename = contract['rest']; task.destination_path = base; task.destination_name = name
task.automated = True; task.save = True; task.replace_existing = False
options = u.FbxImportUI(); options.automated_import_should_detect_type = False
options.import_mesh = True; options.import_as_skeletal = True; options.import_animations = False
options.import_materials = False; options.import_textures = False; options.create_physics_asset = False
options.skeleton = original.skeleton; options.mesh_type_to_import = u.FBXImportType.FBXIT_SKELETAL_MESH
data = options.skeletal_mesh_import_data
data.set_editor_property('import_morph_targets', True)
data.set_editor_property('morph_threshold_position', .00001)
data.set_editor_property('vertex_color_import_option', u.VertexColorImportOption.REPLACE)
task.options = options
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
mesh = u.load_asset(base+'/'+name)
assert mesh and mesh.skeleton == original.skeleton
editor = u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem)
settings = editor.get_lod_build_settings(mesh, 0)
settings.set_editor_property('bone_influence_limit', 12)
editor.set_lod_build_settings(mesh, 0, settings)
for section in range(editor.get_num_sections(mesh, 0)):
    assert editor.set_section_recompute_tangent(mesh, 0, section, True)
    assert editor.set_section_recompute_tangents_vertex_mask_channel(mesh, 0, section, 1)
actual = {m.get_name().casefold() for m in mesh.get_editor_property('morph_targets') if m.get_name().casefold().startswith('review_g1_leftaxilla_')}
assert actual == {n.casefold() for n in contract['expected_morphs']}
assert u.EditorAssetLibrary.save_loaded_asset(mesh, False)
dynamic = u.DynamicMesh()
u.GeometryScript_AssetUtils.copy_mesh_from_skeletal_mesh(mesh, dynamic, u.GeometryScriptCopyMeshFromAssetOptions(), u.GeometryScriptMeshReadLOD())
colors = u.GeometryScript_VertexColors.get_mesh_per_vertex_colors(dynamic, True)
assert colors[2]
values = u.GeometryScript_List.convert_color_list_to_array(colors[1])
span = [min(v.g for v in values), max(v.g for v in values)]
assert span[0] < .0001 and span[1] > .999 and 500 <= sum(v.g > .00001 for v in values) <= 800
assert all(Path(p).is_file() and hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in protected.items())
path = Path(u.Paths.project_content_dir()).resolve()/base.replace('/Game/', '')/(name+'.uasset')
report = {'ok': True, 'source_sha256': contract['source_sha256'], 'mesh': mesh.get_path_name(),
          'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'green_range': span,
          'nonzero_green': sum(v.g > .00001 for v in values), 'morphs': len(actual),
          'old_proofs_unchanged': True, 'status': 'Private localized normals proof; motion review pending.'}
(out/'NativeLocalNormals.json').write_text(json.dumps(report, indent=2))
print('G1_LOCAL_NORMALS_IMPORTED', report, flush=True)
