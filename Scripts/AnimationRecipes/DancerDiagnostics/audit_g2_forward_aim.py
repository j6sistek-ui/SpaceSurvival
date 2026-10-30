import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Forward reach follows the arm's current direction, not a fixed axis."""
from pathlib import Path
code=(_recipe_dir/'probe_g2_support_clearance.py').read_text(encoding='utf-8')
exec(compile(code[:code.index('results=[]')],__file__,'exec'))
O=R/'G2ForwardAimDense';O.mkdir(exist_ok=True)
uncorrected_sample=sample_loop
def forward_aim(p,degrees):
 p={n:m.copy() for n,m in p.items()};anchor=p['hand_r'].copy()
 chest=p['spine_05'].to_quaternion()@rest['spine_05'].to_quaternion().inverted()
 upper=(p['lowerarm_r'].translation-p['upperarm_r'].translation).normalized()
 forward=chest@Vector((0,-1,0));axis=upper.cross(forward)
 if axis.length>1e-6:
  angle=min(math.radians(degrees),upper.angle(forward))
  rotate(p,'upperarm_r',Quaternion(axis.normalized(),angle))
 delta=anchor@p['hand_r'].inverted()
 return {n:delta@m for n,m in p.items()}
def sample_loop(t):return forward_aim(uncorrected_sample(t),20)
reference=sample_loop(0)
code=(_recipe_dir/'review_g2_return_loop.py').read_text(encoding='utf-8')
code=code[code.index('hinge={}'):].replace('np.array(initial[n])-np.array(sample_loop(duration)[n])','np.array(reference[n])-np.array(sample_loop(duration)[n])')
exec(compile(code,__file__,'exec'))
code=(_recipe_dir/'audit_g2_loop_self_contact.py').read_text(encoding='utf-8')
exec(compile(code[code.index('rows=[]'):],__file__,'exec'))
