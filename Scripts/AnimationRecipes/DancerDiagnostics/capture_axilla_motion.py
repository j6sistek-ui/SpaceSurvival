import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Capture the same local axilla candidate in the private native workbench."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from axilla_native_common import source
exec(compile(source('capture_balanced_motion.py'),__file__,'exec'))
