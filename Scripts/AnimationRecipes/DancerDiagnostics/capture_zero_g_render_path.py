import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Inspect the installed renderer path, retaining the normal diagnostic control."""
from pathlib import Path
code=(Path(__file__).resolve().parent/'capture_zero_g_explicit_skin.py').read_text().replace('NativeExplicitSkin','NativeRenderPath').replace(",'r.SkinCache.SceneMemoryLimitInMB'",'')
code=code.replace("settings_before={'component'", "print('ZERO_G_NANITE',sk.get_editor_property('nanite_settings'),flush=True)\\nsettings_before={'component'")
code=code.replace("'r.SkinCache.RecomputeTangents 1'", "'r.SkinCache.RecomputeTangents 1','DumpConsoleCommands r.SkinCache','r.SkinCache.PrintMemorySummary 2','rhi.dumpresourcememory summary name=SkinCache'")
exec(compile(code,__file__,'exec'))
