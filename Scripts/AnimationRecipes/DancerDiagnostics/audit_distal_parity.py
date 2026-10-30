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
code=source('audit_balanced_native.py')
code=code.replace("if ob.type=='MESH' and ob.data.shape_keys:","if ob.type=='MESH' and not ob.hide_render and ob.data.shape_keys:")
exec(compile(code,__file__,'exec'))
