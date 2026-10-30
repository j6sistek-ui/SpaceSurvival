import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

import unreal as u,json,traceback,os
from pathlib import Path
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
LEG_PLANE=os.environ.get('SS_REVIEW_LEG_PLANE')=='1'
SHOULDER=os.environ.get('SS_REVIEW_SHOULDER')=='1'
assert not (SHOULDER and LEG_PLANE), 'Choose one proof'
DEST='/Game/SpaceSurvival/Licensed/'+('VexaShoulderProof_20261025' if SHOULDER else 'LegPlaneProof_20261025' if LEG_PLANE else 'HipCurveProof_Legacy_20261025')
stem='Vexa_Shoulder' if SHOULDER else 'Roxie_LegPlane' if LEG_PLANE else 'Roxie_HipCurve'
asset='SK_VexaShoulderProof' if SHOULDER else 'SK_RoxieHipProof'
report={'status':'PRIVATE TEST ONLY','assets':[],'errors':[]}
try:
 assert 'WorkbenchNative/CharacterWorkbench' in u.Paths.get_project_file_path().replace('\\','/'), 'Private workbench only'
 # Ephemeral setting in this isolated commandlet; no project config edit.
 u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
 task=u.AssetImportTask();task.filename=str(D/(stem+'_Rest.fbx'));task.destination_path=DEST;task.destination_name=asset;task.automated=True;task.save=True;task.replace_existing=True
 opt=u.FbxImportUI();opt.automated_import_should_detect_type=False;opt.import_mesh=True;opt.import_as_skeletal=True;opt.import_animations=True;opt.import_materials=False;opt.import_textures=False;opt.create_physics_asset=False;opt.mesh_type_to_import=u.FBXImportType.FBXIT_SKELETAL_MESH
 opt.import_animations=False;opt.skeletal_mesh_import_data.set_editor_property('import_morph_targets',True)
 opt.skeletal_mesh_import_data.set_editor_property('morph_threshold_position',.00001)
 opt.anim_sequence_import_data.set_editor_property('use_default_sample_rate',False);opt.anim_sequence_import_data.set_editor_property('custom_sample_rate',60);opt.anim_sequence_import_data.set_editor_property('preserve_local_transform',True)
 task.options=opt;u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
 sk=u.load_asset(DEST+'/'+asset);assert sk and sk.skeleton
 # AssetImportTask.save did not persist the newly created skeleton in UE5.8.
 # Save this dependency explicitly before any later process tries to load it.
 assert u.EditorAssetLibrary.save_loaded_asset(sk.skeleton,False)
 assert u.EditorAssetLibrary.save_loaded_asset(sk,False)
 task=u.AssetImportTask();task.filename=str(D/(stem+'_Proof.fbx'));task.destination_path=DEST;task.destination_name=asset+'_Anim';task.automated=True;task.save=True;task.replace_existing=True
 opt=u.FbxImportUI();opt.automated_import_should_detect_type=False;opt.import_mesh=False;opt.import_animations=True;opt.import_materials=False;opt.import_textures=False;opt.skeleton=sk.skeleton;opt.mesh_type_to_import=u.FBXImportType.FBXIT_ANIMATION
 opt.anim_sequence_import_data.set_editor_property('use_default_sample_rate',False);opt.anim_sequence_import_data.set_editor_property('custom_sample_rate',60);opt.anim_sequence_import_data.set_editor_property('preserve_local_transform',True)
 opt.anim_sequence_import_data.set_editor_property('delete_existing_morph_target_curves',True);task.options=opt
 u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
 assert u.EditorAssetLibrary.save_directory(DEST,False,True)
 reg=u.AssetRegistryHelpers.get_asset_registry();reg.scan_paths_synchronous([DEST],True)
 for data in reg.get_assets_by_path(DEST,True):
  obj=data.get_asset();row={'path':obj.get_path_name(),'class':obj.get_class().get_name()}
  if isinstance(obj,u.SkeletalMesh):row['morphs']=[m.get_name() for m in obj.get_editor_property('morph_targets')]
  if isinstance(obj,u.AnimSequence):
   row['seconds']=obj.sequence_length
   row['curve_names']=[str(x) for x in u.AnimationLibrary.get_animation_curve_names(obj,u.RawCurveTrackTypes.RCT_FLOAT)]
  report['assets'].append(row)
 expected={n.casefold() for n in json.loads((R/('VexaShoulderExportContract.json' if SHOULDER else 'LegPlaneExportContract.json' if LEG_PLANE else 'HipExportContract.json')).read_text())['expected_morphs']}
 report['expected_morphs']=len(expected)
 # Unreal FName identity is case-insensitive; fresh loads can display lower case.
 report['ok']=any({n.casefold() for n in r.get('morphs',[]) if n.casefold().startswith('review_')}==expected for r in report['assets']) and any(abs(r.get('seconds',-1)-16)<.05 and {n.casefold() for n in r.get('curve_names',[]) if n.casefold().startswith('review_')}==expected for r in report['assets'])
except Exception:report['errors'].append(traceback.format_exc())
(R/('NativeVexaShoulderProof.json' if SHOULDER else 'NativeLegPlaneProof.json' if LEG_PLANE else 'NativeHipProof.json')).write_text(json.dumps(report,indent=2));print('HIP_NATIVE_IMPORT',report.get('ok'),report['errors'],flush=True)
