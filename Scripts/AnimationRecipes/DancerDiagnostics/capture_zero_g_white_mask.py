import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Compare identical poses using the new explicit-white mask mesh."""
from pathlib import Path
code=(Path(__file__).resolve().parent/'capture_zero_g_explicit_skin.py').read_text().replace('NativeExplicitSkin','NativeWhiteMask').replace(",'r.SkinCache.SceneMemoryLimitInMB'",'')
code=code.replace("(Path(__file__).resolve().parent/'capture_zero_g_shared_controls.py').read_text()", "(Path(__file__).resolve().parent/'capture_zero_g_shared_controls.py').read_text().replace('SK_VexaZeroGShared','SK_VexaZeroGWhiteMask')")
exec(compile(code,__file__,'exec'))
