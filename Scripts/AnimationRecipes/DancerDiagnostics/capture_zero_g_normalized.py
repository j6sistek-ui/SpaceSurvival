import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Normalize the diagnostic ramp's interpolated normals with recomputation off."""
import os
from pathlib import Path
os.environ['SS_REVIEW_NORMALIZE']='1'
code=(Path(__file__).resolve().parent/'capture_zero_g_explicit_skin.py').read_text().replace('NativeExplicitSkin','NativeNormalized').replace(",'r.SkinCache.SceneMemoryLimitInMB'",'').replace("'r.SkinCache.RecomputeTangents 1'","'r.SkinCache.RecomputeTangents 0'")
exec(compile(code,__file__,'exec'))
