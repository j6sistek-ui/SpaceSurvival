import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Import five paired proofs on a new private skeleton; old proofs untouched."""
import unreal as u,json,hashlib,traceback
from pathlib import Path
contract=json.loads((R/'ZeroGSharedHip/Export.json').read_text())
BASE='/Game/SpaceSurvival/Licensed/VexaZeroGSharedHipProof_20261026';OLD='/Game/SpaceSurvival/Licensed/VexaContinuousDistalProof_20261025'
assert 'WorkbenchNative/CharacterWorkbench' in u.Paths.get_project_file_path().replace('\\','/')
root=Path(u.Paths.project_content_dir())/'SpaceSurvival/Licensed'
protected={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for sub in ('VexaContinuousDistalProof_20261025','VexaHandIsolationProof_20261026') for p in (root/sub).rglob('*') if p.is_file()}
report={'base':BASE,'status':'Private native proof; no production adoption or owner acceptance','assets':[],'errors':[]}
try:
 lib=u.EditorAssetLibrary
 if lib.does_asset_exist(BASE+'/SKEL_VexaZeroGProof'):
  prior=json.loads((R/'ZeroGSharedHip/NativeImport_FirstReloadError.json').read_text())
  assert prior['base']==BASE and prior['mesh']['actual']==160 and 'AttributeError' in prior['errors'][0]
  skeleton=lib.load_asset(BASE+'/SKEL_VexaZeroGProof')
 else:skeleton=lib.duplicate_asset(OLD+'/SK_VexaContinuousDistalProof_Skeleton',BASE+'/SKEL_VexaZeroGProof')
 assert skeleton
 assert lib.save_loaded_asset(skeleton,False)
 u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
 task=u.AssetImportTask();task.filename=contract['rest'];task.destination_path=BASE;task.destination_name='SK_VexaZeroGShared';task.automated=True;task.save=True;task.replace_existing=False
 opt=u.FbxImportUI();opt.automated_import_should_detect_type=False;opt.import_mesh=True;opt.import_as_skeletal=True;opt.import_animations=False;opt.import_materials=False;opt.import_textures=False;opt.create_physics_asset=False;opt.skeleton=skeleton;opt.mesh_type_to_import=u.FBXImportType.FBXIT_SKELETAL_MESH
 opt.skeletal_mesh_import_data.set_editor_property('import_morph_targets',True);opt.skeletal_mesh_import_data.set_editor_property('morph_threshold_position',.00001);task.options=opt
 if not lib.does_asset_exist(BASE+'/'+task.destination_name):u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
 mesh=u.load_asset(BASE+'/'+task.destination_name);assert mesh and mesh.skeleton==skeleton
 editor=u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem);settings=editor.get_lod_build_settings(mesh,0);settings.set_editor_property('bone_influence_limit',12);editor.set_lod_build_settings(mesh,0,settings)
 assert lib.save_loaded_asset(mesh,False)
 expected={n.casefold() for n in contract['expected_morphs']};actual={m.get_name().casefold() for m in mesh.get_editor_property('morph_targets') if m.get_name().casefold().startswith('review_zg_')}
 report['mesh']={'path':mesh.get_path_name(),'expected':len(expected),'actual':len(actual),'missing':sorted(expected-actual),'extra':sorted(actual-expected)};assert actual==expected,report['mesh']
 for row in contract['exports']:
  name='A_ZG_'+Path(row['file']).stem;task=u.AssetImportTask();task.filename=row['file'];task.destination_path=BASE;task.destination_name=name;task.automated=True;task.save=True;task.replace_existing=False
  opt=u.FbxImportUI();opt.automated_import_should_detect_type=False;opt.import_mesh=False;opt.import_animations=True;opt.import_materials=False;opt.import_textures=False;opt.skeleton=skeleton;opt.mesh_type_to_import=u.FBXImportType.FBXIT_ANIMATION
  opt.anim_sequence_import_data.set_editor_property('use_default_sample_rate',False);opt.anim_sequence_import_data.set_editor_property('custom_sample_rate',120);opt.anim_sequence_import_data.set_editor_property('preserve_local_transform',True);opt.anim_sequence_import_data.set_editor_property('delete_existing_morph_target_curves',True);task.options=opt
  if not lib.does_asset_exist(BASE+'/'+name):u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
  clip=u.load_asset(BASE+'/'+name);assert clip and clip.get_editor_property('skeleton')==skeleton
  curves={str(x).casefold() for x in u.AnimationLibrary.get_animation_curve_names(clip,u.RawCurveTrackTypes.RCT_FLOAT) if str(x).casefold().startswith('review_zg_')}
  result={'path':clip.get_path_name(),'duration':clip.sequence_length,'curves':len(curves),'missing':sorted(expected-curves),'extra':sorted(curves-expected)};report['assets'].append(result)
  assert abs(clip.sequence_length-row['duration'])<.0001 and curves==expected,result
  assert lib.save_loaded_asset(clip,False)
 assert lib.save_loaded_asset(skeleton,False)
 report['old_proofs_unchanged']=all(Path(p).is_file() and hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in protected.items());assert report['old_proofs_unchanged']
 report['ok']=True
except Exception:report['errors'].append(traceback.format_exc())
(R/'ZeroGSharedHip/NativeImport.json').write_text(json.dumps(report,indent=2));print('ZERO_G_NATIVE',report.get('ok',False),report['errors'],flush=True)
