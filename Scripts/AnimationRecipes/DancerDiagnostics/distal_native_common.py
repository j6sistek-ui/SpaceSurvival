import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Established native harness, isolated destination for the continuous distal copy."""
from pathlib import Path
def source(script):
    text=(Path(__file__).resolve().parent/script).read_text()
    text=text.replace('Vexa_ShoulderBalanced','Vexa_ContinuousDistal').replace('VexaBalanced','VexaContinuousDistal')
    return text
