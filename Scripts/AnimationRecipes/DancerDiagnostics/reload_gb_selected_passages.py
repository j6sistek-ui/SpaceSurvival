import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Fresh process checks for both local-passage candidate dependencies."""
from pathlib import Path
code=(Path(__file__).resolve().parent/'verify_gb_wrist_native_reload.py').read_text().replace('VexaContinuousDistalProof_20261025','VexaHandIsolationProof_20261026').replace('SK_VexaContinuousDistalProof','SK_VexaHandIsolationProof').replace("R/'VexaDistalRepair/GBWristExport.json'","R/'GBFastPassage/SelectedExport.json'").replace("'A_Wrist_'","'A_SelectedPassages_'").replace('len(rows)==8','len(rows)==2').replace("R/'VexaDistalRepair/GBNativeReload.json'","R/'GBFastPassage/SelectedReload.json'")
exec(compile(code,__file__,'exec'))
