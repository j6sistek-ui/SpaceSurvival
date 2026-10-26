import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Fresh-process dependency and duration check of four shoulder derivatives."""
from pathlib import Path
code=(Path(__file__).resolve().parent/'verify_gb_wrist_native_reload.py').read_text()
code=code.replace("R/'VexaDistalRepair/GBWristExport.json'","R/'GBShoulderResponse/Export.json'")
code=code.replace("'A_Wrist_'","'A_ShoulderResponse_'").replace("len(rows)==8","len(rows)==4")
code=code.replace("R/'VexaDistalRepair/GBNativeReload.json'","R/'GBShoulderResponse/NativeReload.json'")
exec(compile(code,__file__,'exec'))
