import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Fresh G2 native dependency reload; no asset writes."""
from pathlib import Path
code = (_recipe_dir/'reload_supported_release_native.py').read_text(encoding='utf-8')
for old, new in [('VexaPoleReleaseProof_20261026', 'VexaG2SupportProof_20261026'), ('A_G1_SupportedRelease', 'A_G2_SupportedPassage'), ('L_G1SupportedRelease_Review', 'L_G2SupportedPassage_Review'), ('NativeSupportedRelease', 'NativeG2Support'), ('1100/60', '1000/60')]:
    assert old in code, old
    code = code.replace(old, new)
exec(compile(code, __file__, 'exec'))
