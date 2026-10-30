import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Opposing before/after source views of the G1 local arm trial."""
from pathlib import Path
code=(Path(__file__).resolve().parent/'review_remaining_arm_events.py').read_text()
code=code.replace("O=R/'GBArmEventViews'","O=R/'GBFastPassage/G1After'").replace('G2_ArmPassage_ActionLibrary.blend','GB_SelectedPassages_ActionLibrary.blend')
code=code.replace("names=['A_F3_ArmPassage_g2']+['A_F3_ShoulderResponse_'+c for c in ('g1','b1')]","names=['A_F3_SelectedPassages_g1']")
code=code.replace("action=actions['A_F3_ArmPassage_g2' if clip=='g2' else 'A_F3_ShoulderResponse_'+clip]","action=actions['A_F3_SelectedPassages_g1']")
a=code.index('events=[');z=code.index(';rows=[]',a)
code=code[:a]+"events=[('g1',192,207,225),('g1',231,240,255),('g1',260,265,270)]"+code[z:]
exec(compile(code,__file__,'exec'))
