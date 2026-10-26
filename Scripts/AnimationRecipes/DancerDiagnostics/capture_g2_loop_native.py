import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Isolated native transfer and opposing views for the saved G2 loop."""
from pathlib import Path
code=(_recipe_dir/'capture_supported_release_native.py').read_text(encoding='utf-8')
for old,new in [
 ('VexaPoleReleaseProof_20261026','VexaG2LoopProof_20261026'),
 ("OUT=R/'NativeSupportedRelease'","OUT=R/'NativeG2Loop'"),
 ("R/'GBSupportedRelease/Export.json'","R/'G2ReturnLoop/Export.json'"),
 ('A_G1_SupportedRelease','A_G2_ContactLoop'),
 ('L_G1SupportedRelease_Review','L_G2ContactLoop_Review'),
 ('640,640','800,800'),
 ('u.Vector(25,0,1380)','u.Vector(0,-55,1380)'),
 ("u.Vector(240,-360,45) if view=='front' else u.Vector(-240,360,45)","u.Vector(390,-585,70) if view=='front' else u.Vector(-390,585,70)"),
 ('mesh.override_animation_data(clip,False,False,0,0)','mesh.override_animation_data(clip,True,True,0,1)'),
 ]:
 assert old in code,old;code=code.replace(old,new)
exec(compile(code,__file__,'exec'))
