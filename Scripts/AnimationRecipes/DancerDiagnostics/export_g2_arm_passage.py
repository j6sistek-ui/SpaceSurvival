import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Export the single bounded G2 candidate, leaving all source files intact."""
from pathlib import Path
code=(Path(__file__).resolve().parent/'export_gb_wrist_comparison.py').read_text()
code=code.replace("[('before','Refined_ActionLibrary.blend','A_F3_Refined_'),('after','GB_WristContinuous_ActionLibrary.blend','A_F3_WristContinuous_')]","[('passage','G2_ArmPassage_ActionLibrary.blend','A_F3_ArmPassage_')]")
code=code.replace("for clip in ('g1','g2','b1','b2'):","for clip in ('g2',):").replace("O=D/'GBWristComparison'","O=D/'G2ArmPassage'").replace("if kind=='after':","if kind=='passage':").replace("R/'VexaDistalRepair/GBWristExport.json'","R/'GBFastPassage/Export.json'")
exec(compile(code,__file__,'exec'))
