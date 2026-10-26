import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Persist explicit limit on the new private proof through the LOD accessor."""
import unreal as u,json,hashlib
from pathlib import Path
assert 'WorkbenchNative/CharacterWorkbench' in u.Paths.get_project_file_path().replace('\\','/')
old=Path(u.Paths.project_content_dir())/'SpaceSurvival/Licensed/VexaContinuousDistalProof_20261025'
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in old.rglob('*') if p.is_file()}
mesh=u.load_asset('/Game/SpaceSurvival/Licensed/VexaHandIsolationProof_20261026/SK_VexaHandIsolationProof');assert mesh
editor=u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem);settings=editor.get_lod_build_settings(mesh,0);previous=settings.get_editor_property('bone_influence_limit');assert previous in (0,12)
settings.set_editor_property('bone_influence_limit',12);editor.set_lod_build_settings(mesh,0,settings);assert u.EditorAssetLibrary.save_loaded_asset(mesh,False)
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
(R/'GBFingerShape/InfluenceSetting.json').write_text(json.dumps({'before':previous,'after':editor.get_lod_build_settings(mesh,0).get_editor_property('bone_influence_limit'),'old_unchanged':True},indent=2));print('HAND_LOD_SETTING_SAVED',flush=True)
