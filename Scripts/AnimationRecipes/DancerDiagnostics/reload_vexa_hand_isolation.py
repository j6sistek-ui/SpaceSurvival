import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

import unreal as u,json,traceback
from pathlib import Path
report={'errors':[],'ok':False}
try:
 assert 'WorkbenchNative/CharacterWorkbench' in u.Paths.get_project_file_path().replace('\\','/')
 base='/Game/SpaceSurvival/Licensed/';old=u.load_asset(base+'VexaContinuousDistalProof_20261025/SK_VexaContinuousDistalProof');new=u.load_asset(base+'VexaHandIsolationProof_20261026/SK_VexaHandIsolationProof')
 assert old and new and new.skeleton==old.skeleton
 a={m.get_name().casefold() for m in old.get_editor_property('morph_targets')};b={m.get_name().casefold() for m in new.get_editor_property('morph_targets')};assert a==b
 report.update(morphs=len(b),skeleton=new.skeleton.get_path_name(),clips=[])
 for clip in ('g1','g2','b1','b2'):
  anim=u.load_asset(base+'VexaContinuousDistalProof_20261025/A_ShoulderResponse_'+clip+'_shoulder');assert anim and anim.get_editor_property('skeleton')==new.skeleton
  report['clips'].append({'name':clip,'seconds':anim.sequence_length})
 limits=[lod.get_editor_property('build_settings').get_editor_property('bone_influence_limit') for lod in new.get_editor_property('source_models')]
 actual=u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem).get_lod_build_settings(new,0).get_editor_property('bone_influence_limit')
 report.update(source_model_initialization_limits=limits,actual_lod_influence_limit=actual)
 assert actual==12
 assert u.SystemLibrary.get_console_variable_int_value('r.GPUSkin.UnlimitedBoneInfluences')==1
 report['ok']=True
except Exception:report['errors'].append(traceback.format_exc())
(R/'GBFingerShape/NativeReload.json').write_text(json.dumps(report,indent=2));print('HAND_RELOAD',report,flush=True)
