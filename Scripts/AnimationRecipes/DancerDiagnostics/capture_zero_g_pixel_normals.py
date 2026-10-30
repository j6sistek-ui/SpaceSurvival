import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Same explicit-cache control, changing only the diagnostic normal expression."""
from pathlib import Path
code=(Path(__file__).resolve().parent/'capture_zero_g_explicit_skin.py').read_text()
code=code.replace("code=code.replace(\"exec(compile(code,__file__,'exec'))\"", "code=code.replace(\"exec(compile(code,__file__,'exec'))\"")
# The nested setup must use pixel normals; save neither a mesh nor owner settings.
code=code.replace("exec(compile(code,__file__,'exec'))\n", "code=code.replace('NativeExplicitSkin','NativePixelNormals').replace(\"exec(compile(code,__file__,'exec'))\",\"code=code.replace('u.MaterialExpressionVertexNormalWS','u.MaterialExpressionPixelNormalWS')\\nexec(compile(code,__file__,'exec'))\")\nexec(compile(code,__file__,'exec'))\n")
code=code.replace(",'r.SkinCache.SceneMemoryLimitInMB'",'')
exec(compile(code,__file__,'exec'))
