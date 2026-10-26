import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Export only two locally revised actions, with prior source preservation."""
from pathlib import Path
code=(Path(__file__).resolve().parent/'export_gb_wrist_comparison.py').read_text()
code=code.replace("[('before','Refined_ActionLibrary.blend','A_F3_Refined_'),('after','GB_WristContinuous_ActionLibrary.blend','A_F3_WristContinuous_')]","[('selected','GB_SelectedPassages_ActionLibrary.blend','A_F3_SelectedPassages_')]")
code=code.replace("for clip in ('g1','g2','b1','b2'):","for clip in ('g1','g2'):").replace("action=bpy.data.actions[prefix+clip]","action=bpy.data.actions[prefix+clip if clip=='g1' else 'A_F3_TwoPassages_g2']")
code=code.replace("O=D/'GBWristComparison'","O=D/'GBSelectedPassages'").replace("if kind=='after':","if kind=='selected':").replace("R/'VexaDistalRepair/GBWristExport.json'","R/'GBFastPassage/SelectedExport.json'")
exec(compile(code,__file__,'exec'))
