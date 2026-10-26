import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""All 24 native distal cases, with the tested foot viewed from outside."""
from pathlib import Path
code=(Path(__file__).resolve().parent/'capture_vexa_distal_native.py').read_text()
code=code.replace('diagnostic poses plus preserved shoulder','diagnostic poses only')
code=code.replace("code=source('capture_balanced_clean.py')","code=source('capture_balanced_clean.py').replace('NativeVexaContinuousDistalCleanViews','NativeVexaContinuousDistalFullRangeViews').replace('NativeVexaContinuousDistalCleanCapture.json','NativeVexaContinuousDistalFullRange.json')")
code=code.replace(" if x['test'] in ('flex','pitch')",'')
code=code.replace("across=unit(cross(up,along));center=center+along*5","across=unit(cross(up,along))\n   other=c.get_socket_location('foot_'+('r' if side=='l' else 'l'))\n   outward=center-other\n   if across.x*outward.x+across.y*outward.y+across.z*outward.z<0:across=across*-1\n   center=center+along*5")
code=code.replace("exec(compile(code,__file__,'exec'))", "code=code.replace(\"'hip':center.to_tuple()\",\"'camera_target':center.to_tuple(),'bone':bone,'bone_transform':str(c.get_socket_transform(bone,u.RelativeTransformSpace.RTS_COMPONENT))\")\nexec(compile(code,__file__,'exec'))")
exec(compile(code,__file__,'exec'))
