import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Read-only opposing views; source gesture and collision triage."""
from pathlib import Path
code=(Path(__file__).resolve().parent/'review_remaining_arm_events.py').read_text()
code=code.replace("O=R/'GBArmEventViews'","O=R/'G1ArmInterval'")
a=code.index("events=[");z=code.index(';rows=[]',a)
code=code[:a]+"events=[('g1',180,207,225),('g1',231,240,255),('g1',270,285,300)]"+code[z:]
exec(compile(code,__file__,'exec'))
