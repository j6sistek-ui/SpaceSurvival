import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Fresh G2 action reload, using the same fixed-joint comparison as G1."""
from pathlib import Path
code = (_recipe_dir/'verify_supported_release_reload.py').read_text(encoding='utf-8')
assert 'GBSupportedRelease' in code
exec(compile(code.replace('GBSupportedRelease', 'G2SupportedPassage'), __file__, 'exec'))
