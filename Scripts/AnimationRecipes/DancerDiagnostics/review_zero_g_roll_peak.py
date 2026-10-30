import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Bounded hip-target views around the two fastest zero-G leg passages."""
from pathlib import Path
hip=(Path(__file__).resolve().parent/'review_zero_g_hip_transfer.py').read_text()
base=(Path(__file__).resolve().parent/'review_zero_g_joint_transfer.py').read_text()
base=base.replace("('01_Drift','02_Spiral','03_Butterfly','04_Inversion','05_LateralArc')","('01_Drift','03_Butterfly')")
base=base.replace("O=R/'ZeroGJointTransferLocalBasis'","O=R/'ZeroGRollPeak'")
base=base.replace("want={first,first+round((last-first)*.25),first+round((last-first)*.5),first+round((last-first)*.75),last}","want={605,625,645,656,665,685} if 'Drift' in name else {421,441,461,481,501}")
hip=hip.replace("code=(Path(__file__).resolve().parent/'review_zero_g_joint_transfer.py').read_text()","code="+repr(base))
exec(compile(hip,__file__,'exec'))
