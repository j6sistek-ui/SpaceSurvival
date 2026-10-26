import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Read-only native dependency reload after the capture process has exited."""
import unreal as u,json
from pathlib import Path
assert 'WorkbenchNative/CharacterWorkbench' in u.Paths.get_project_file_path().replace('\\','/')
base='/Game/SpaceSurvival/Licensed/VexaPoleReleaseProof_20261026'
clip=u.load_asset(base+'/A_G1_SupportedRelease');mesh=u.load_asset('/Game/SpaceSurvival/Licensed/VexaHandIsolationProof_20261026/SK_VexaHandIsolationProof');world=u.load_asset(base+'/L_G1SupportedRelease_Review')
assert clip and mesh and world and mesh.skeleton==clip.get_editor_property('skeleton')
assert abs(clip.sequence_length-1100/60)<.02
result={'ok':True,'clip':clip.get_path_name(),'mesh':mesh.get_path_name(),'skeleton':mesh.skeleton.get_path_name(),'map':world.get_path_name(),'seconds':clip.sequence_length,'scope':'Dependencies only; not anatomical acceptance.'}
(R/'NativeSupportedRelease/Reload.json').write_text(json.dumps(result,indent=2));print('RELEASE_NATIVE_RELOAD',json.dumps(result),flush=True)
