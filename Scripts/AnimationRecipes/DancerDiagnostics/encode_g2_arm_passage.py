import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Encode and decode-count the completed native matching passage captures."""
from pathlib import Path
code=(Path(__file__).resolve().parent/'encode_gb_wrist_comparison.py').read_text().replace('NativeGBWristComparison','NativeG2ArmPassage').replace('Vexa_Wrist_','Vexa_G2Passage_').replace("R/'VexaDistalRepair/NativeGBWristVideos.json'","R/'GBFastPassage/Videos.json'").replace('Native private Vexa, unconstrained clips; matched wrist events and full G1. No pole contact, anatomical or artistic acceptance.','Native private Vexa, local G2 arm passage before/after. No pole contact or whole-routine acceptance.')
exec(compile(code,__file__,'exec'))
