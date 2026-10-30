import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Same native poses with the previously validated skin-cache tangent path."""
from pathlib import Path
code=(Path(__file__).resolve().parent/'capture_zero_g_shared_controls.py').read_text().replace('NativeControls','NativeRecomputedControls')
code=code.replace("u.SystemLibrary.execute_console_command(world,'t.MaxFPS 30');u.SystemLibrary.execute_console_command(world,'r.EyeAdaptationQuality 0')","assert u.SystemLibrary.get_console_variable_int_value('r.SkinCache.CompileShaders')==1\n   for cmd in ('t.MaxFPS 30','r.EyeAdaptationQuality 0','r.SkinCache.Mode 1','r.SkinCache.RecomputeTangents 1'):u.SystemLibrary.execute_console_command(world,cmd)")
code=code.replace("report['ok']=not report['errors']", "report['skin_cache_cvars']={n:u.SystemLibrary.get_console_variable_int_value(n) for n in ('r.SkinCache.CompileShaders','r.SkinCache.Mode','r.SkinCache.RecomputeTangents')}\n report['ok']=not report['errors']")
exec(compile(code,__file__,'exec'))
