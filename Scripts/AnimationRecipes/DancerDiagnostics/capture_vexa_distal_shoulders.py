import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Check that the continuous distal surface retains the shoulder appearance."""
from pathlib import Path
import sys
sys.path.insert(0,str(R))
from distal_native_common import source
code=source('capture_balanced_clean.py')
code=code.replace('NativeVexaContinuousDistalCleanViews','NativeVexaContinuousShoulderViews').replace('NativeVexaContinuousDistalCleanCapture.json','NativeVexaContinuousShoulderCapture.json')
code=code.replace("if RECOMPUTE:\n    u.SystemLibrary.execute_console_command(world,'r.SkinCache.Mode 1',pc)","if True:\n    u.SystemLibrary.execute_console_command(world,'r.SkinCache.Mode 1',pc)")
exec(compile(code,__file__,'exec'))
