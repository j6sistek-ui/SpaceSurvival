import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Use the established native harness in a distinct, private axilla destination."""
from pathlib import Path
def source(script):
    root=Path(__file__).resolve().parent
    text=(root/script).read_text()
    return text.replace('Vexa_ShoulderBalanced','Vexa_AxillaLocal').replace('VexaBalanced','VexaAxilla')
