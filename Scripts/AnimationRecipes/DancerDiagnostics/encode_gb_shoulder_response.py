import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Encode only the two complete native G1 views; preserve twelve stills."""
from pathlib import Path
code=(Path(__file__).resolve().parent/'encode_gb_wrist_comparison.py').read_text()
code=code.replace("R/'NativeGBWristComparison.json'","R/'NativeGBShoulderResponse.json'")
code=code.replace("for seg in source['segments']:","for seg in source['segments']:\n if seg['frames']==1:continue")
code=code.replace("R/'NativeGBWristComparison'","R/'NativeGBShoulderResponse'").replace("'Vexa_Wrist_'","'Vexa_ShoulderResponse_'")
code=code.replace("R/'VexaDistalRepair/NativeGBWristVideos.json'","R/'GBShoulderResponse/Videos.json'")
exec(compile(code,__file__,'exec'))
