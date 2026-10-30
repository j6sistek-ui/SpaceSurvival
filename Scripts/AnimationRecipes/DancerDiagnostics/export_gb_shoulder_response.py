import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Export only the four saved shoulder derivatives, retaining source files."""
from pathlib import Path
code=(Path(__file__).resolve().parent/'export_gb_wrist_comparison.py').read_text()
old="[('before','Refined_ActionLibrary.blend','A_F3_Refined_'),('after','GB_WristContinuous_ActionLibrary.blend','A_F3_WristContinuous_')]"
assert old in code
code=code.replace(old,"[('shoulder','GB_ShoulderResponse_ActionLibrary.blend','A_F3_ShoulderResponse_')]")
code=code.replace("O=D/'GBWristComparison'","O=D/'GBShoulderResponse'")
code=code.replace("if kind=='after':","if kind=='shoulder':")
code=code.replace("R/'VexaDistalRepair/GBWristExport.json'","R/'GBShoulderResponse/Export.json'")
exec(compile(code,__file__,'exec'))
