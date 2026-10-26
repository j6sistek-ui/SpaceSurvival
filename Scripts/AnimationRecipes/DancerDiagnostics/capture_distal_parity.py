import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from distal_native_common import source
code=source('capture_balanced_clean.py').replace('SURFACE_READBACK=False','SURFACE_READBACK=True')
code=code.replace("shots=[(9.033333,a) for a in ('front','back','side')]+[(12.2,'side')]", "shots=[(t,'front') for t in (0,4,8)]+[(t,a) for t in (9.033333,12.2) for a in ('front','back','side')]")
exec(compile(code,__file__,'exec'))
