import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Dense test of the 20-degree forward-reach control, not a baked adoption."""
from pathlib import Path
code=(_recipe_dir/'probe_g2_support_clearance.py').read_text(encoding='utf-8')
exec(compile(code[:code.index('results=[]')],__file__,'exec'))
O=R/'G2ArmClearanceDense';O.mkdir(exist_ok=True)
uncorrected_sample=sample_loop
def sample_loop(t):return forward_arm(uncorrected_sample(t),20)
reference=sample_loop(0)
code=(_recipe_dir/'review_g2_return_loop.py').read_text(encoding='utf-8')
code=code[code.index('hinge={}') : ].replace('np.array(initial[n])-np.array(sample_loop(duration)[n])','np.array(reference[n])-np.array(sample_loop(duration)[n])')
exec(compile(code,__file__,'exec'))
code=(_recipe_dir/'audit_g2_loop_self_contact.py').read_text(encoding='utf-8')
exec(compile(code[code.index('rows=[]'):],__file__,'exec'))
