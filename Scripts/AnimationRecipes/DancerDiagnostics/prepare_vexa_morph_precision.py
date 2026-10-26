import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Test render-time morph precision on a private duplicate, preserving baseline."""
import unreal as u,json,traceback
from pathlib import Path
BASE='/Game/SpaceSurvival/Licensed/VexaShoulderProof_20261025'
report={'ok':False,'errors':[]}
try:
 assert 'WorkbenchNative/CharacterWorkbench' in u.Paths.get_project_file_path().replace('\\','/')
 source=u.load_asset(BASE+'/SK_VexaShoulderProof');assert source
 destination=BASE+'/SK_VexaShoulderPrecise'
 if u.EditorAssetLibrary.does_asset_exist(destination):
  previous=json.loads((R/'VexaMorphPrecision.json').read_text())
  property_failure=not previous['ok'] and any("'lod_info'" in x for x in previous['errors'])
  copy_failure=previous.get('after_precision_microns')==[20.0]
  assert property_failure or copy_failure, 'Do not overwrite a completed precision experiment'
  (R/('VexaMorphPrecision_PropertyFailure.json' if property_failure else 'VexaMorphPrecision_StructCopyFailure.json')).write_text(json.dumps(previous,indent=2))
  mesh=u.load_asset(destination)
 else:mesh=u.EditorAssetLibrary.duplicate_asset(source.get_path_name(),destination)
 assert mesh
 # UE5.8 stores FSkeletalMeshLODInfo fields on FSkeletalMeshSourceModel.
 lods=mesh.get_editor_property('source_models');report['before']=[]
 updated=[]
 for lod in lods:
  build=lod.get_editor_property('build_settings')
  report['before'].append({'morph_precision_microns':lod.get_editor_property('morph_target_position_error_tolerance'),'morph_delta_threshold_cm':build.get_editor_property('morph_threshold_position'),'bone_influence_limit':build.get_editor_property('bone_influence_limit'),'skin_cache_usage':str(lod.get_editor_property('skin_cache_usage'))})
  lod.set_editor_property('morph_target_position_error_tolerance',.01)
  updated.append(lod)
 mesh.set_editor_property('source_models',updated)
 assert u.EditorAssetLibrary.save_loaded_asset(mesh,False)
 report['after_precision_microns']=[lod.get_editor_property('morph_target_position_error_tolerance') for lod in mesh.get_editor_property('source_models')]
 assert all(abs(value-.01)<1e-6 for value in report['after_precision_microns']), 'Precision update did not persist'
 report['ok']=True
except Exception:report['errors'].append(traceback.format_exc())
(R/'VexaMorphPrecision.json').write_text(json.dumps(report,indent=2));print('VEXA_MORPH_PRECISION',report,flush=True)
