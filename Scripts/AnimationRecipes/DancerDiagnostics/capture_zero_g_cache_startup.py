import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Set recomputation before registering components; same white-mask pose control."""
import unreal as u
from pathlib import Path
for cmd in ('r.SkinCache.Mode 1','r.SkinCache.RecomputeTangents 1'):
 u.SystemLibrary.execute_console_command(None,cmd)
code=(Path(__file__).resolve().parent/'capture_zero_g_white_mask.py').read_text().replace('NativeWhiteMask','NativeCacheStartup')
exec(compile(code,__file__,'exec'))
