import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Opposing views of the late local G2 trial; no production changes."""
from pathlib import Path
code=(Path(__file__).resolve().parent/'review_remaining_arm_events.py').read_text()
code=code.replace("O=R/'GBArmEventViews'","O=R/'GBFastPassage/LateAfter'").replace('G2_ArmPassage_ActionLibrary.blend','G2_TwoPassages_ActionLibrary.blend').replace('A_F3_ArmPassage_g2','A_F3_TwoPassages_g2')
a=code.index('events=[');z=code.index(';rows=[]',a)
code=code[:a]+"events=[('g2',787,800,810),('g2',815,825,830)]"+code[z:]
exec(compile(code,__file__,'exec'))
