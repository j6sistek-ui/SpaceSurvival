import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""One isolated mesh-only control with an explicit white recompute mask."""
import unreal as u,json,hashlib
from pathlib import Path
B='/Game/SpaceSurvival/Licensed/VexaZeroGSharedHipProof_20261026'
assert 'WorkbenchNative/CharacterWorkbench' in u.Paths.get_project_file_path().replace('\\','/')
contract=json.loads((R/'ZeroGSharedHip/Export.json').read_text());name='SK_VexaZeroGWhiteMask'
assert not u.EditorAssetLibrary.does_asset_exist(B+'/'+name)
u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
skeleton=u.load_asset(B+'/SKEL_VexaZeroGProof');assert skeleton
task=u.AssetImportTask();task.filename=contract['rest'];task.destination_path=B;task.destination_name=name;task.automated=True;task.save=True;task.replace_existing=False
opt=u.FbxImportUI();opt.automated_import_should_detect_type=False;opt.import_mesh=True;opt.import_as_skeletal=True;opt.import_animations=False;opt.import_materials=False;opt.import_textures=False;opt.create_physics_asset=False;opt.skeleton=skeleton;opt.mesh_type_to_import=u.FBXImportType.FBXIT_SKELETAL_MESH
data=opt.skeletal_mesh_import_data;data.set_editor_property('import_morph_targets',True);data.set_editor_property('morph_threshold_position',.00001)
data.set_editor_property('vertex_color_import_option',u.VertexColorImportOption.OVERRIDE);data.set_editor_property('vertex_override_color',u.Color(255,255,255,255));task.options=opt
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);mesh=u.load_asset(B+'/'+name);assert mesh and mesh.skeleton==skeleton
editor=u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem);settings=editor.get_lod_build_settings(mesh,0);settings.set_editor_property('bone_influence_limit',12);editor.set_lod_build_settings(mesh,0,settings)
for i in range(editor.get_num_sections(mesh,0)):
 assert editor.set_section_recompute_tangent(mesh,0,i,True)
 assert editor.set_section_recompute_tangents_vertex_mask_channel(mesh,0,i,1)
assert len([m for m in mesh.get_editor_property('morph_targets') if m.get_name().casefold().startswith('review_zg_')])==160
assert u.EditorAssetLibrary.save_loaded_asset(mesh,False)
dyn=u.DynamicMesh();u.GeometryScript_AssetUtils.copy_mesh_from_skeletal_mesh(mesh,dyn,u.GeometryScriptCopyMeshFromAssetOptions(),u.GeometryScriptMeshReadLOD());colors=u.GeometryScript_VertexColors.get_mesh_per_vertex_colors(dyn,True)
assert colors[2];values=u.GeometryScript_List.convert_color_list_to_array(colors[1]);span=[min(x.g for x in values),max(x.g for x in values)];assert min(x.g for x in values)>.999
path=Path(u.Paths.project_content_dir())/'SpaceSurvival/Licensed/VexaZeroGSharedHipProof_20261026'/f'{name}.uasset'
report={'ok':True,'mesh':mesh.get_path_name(),'green_mask_range':span,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'status':'Private normal control only; not adopted'}
(R/'ZeroGSharedHip/WhiteMaskImport.json').write_text(json.dumps(report,indent=2));print('WHITE_MASK_IMPORTED',report,flush=True)
