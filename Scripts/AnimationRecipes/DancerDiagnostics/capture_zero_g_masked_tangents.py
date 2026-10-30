import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Diagnostic masked-tangent control for the documented no-mask regression."""
from pathlib import Path
code=(Path(__file__).resolve().parent/'capture_zero_g_explicit_skin.py').read_text().replace('NativeExplicitSkin','NativeMaskedTangents').replace(",'r.SkinCache.SceneMemoryLimitInMB'",'')
code=code.replace("assert editor.set_section_recompute_tangent(sk,0,i,True)","assert editor.set_section_recompute_tangent(sk,0,i,True)\\n assert editor.set_section_recompute_tangents_vertex_mask_channel(sk,0,i,1)")
exec(compile(code,__file__,'exec'))
