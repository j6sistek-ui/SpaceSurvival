import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Geometric normal control: finite derivatives bypass imported tangent data."""
import os
from pathlib import Path
os.environ['SS_REVIEW_SURFACE']='1'
code=(Path(__file__).resolve().parent/'capture_zero_g_explicit_skin.py').read_text().replace('NativeExplicitSkin','NativeGeometricNormals').replace(",'r.SkinCache.SceneMemoryLimitInMB'",'')
exec(compile(code,__file__,'exec'))
