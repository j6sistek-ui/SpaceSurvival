import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Compare the bounded candidate through the same camera recipe."""
from pathlib import Path
code=(Path(__file__).resolve().parent/'review_gb_fast_passage.py').read_text().replace("O=R/'GBFastPassage'","O=R/'GBFastPassage/After'").replace('GB_ShoulderResponse_ActionLibrary.blend','G2_ArmPassage_ActionLibrary.blend').replace('A_F3_ShoulderResponse_g2','A_F3_ArmPassage_g2')
exec(compile(code,__file__,'exec'))
