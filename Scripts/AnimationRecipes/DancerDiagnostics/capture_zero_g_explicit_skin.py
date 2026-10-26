import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Bounded same-pose control with explicit per-mesh skin-cache participation."""
import json
from pathlib import Path
code=(Path(__file__).resolve().parent/'capture_zero_g_shared_controls.py').read_text().replace('NativeControls','NativeExplicitSkin')
code=code.replace("events=[(row,view) for row in controls['rows'] for view in ('front','back')]", "events=[(row,view) for row in controls['rows'] if row['label'] in ('01_Drift_563p5','02_Spiral_481p0','01_Drift_1') for view in ('front','back')]")
code=code.replace("exec(compile(code,__file__,'exec'))", "exec(compile(code,__file__,'exec'))\nmesh.set_editor_property('skin_cache_usage',[u.SkinCacheUsage.ENABLED])\neditor=u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem)\nsettings_before={'component':str(mesh.get_editor_property('skin_cache_usage')),'sections':[]}\nfor i in range(editor.get_num_sections(sk,0)):\n settings_before['sections'].append({'section':i,'recompute':str(editor.get_section_recompute_tangent(sk,0,i)),'mask':str(editor.get_section_recompute_tangents_vertex_mask_channel(sk,0,i))})\n assert editor.set_section_recompute_tangent(sk,0,i,True)\n# Changes remain transient: no mesh save.\n")
code=code.replace("u.SystemLibrary.execute_console_command(world,'t.MaxFPS 30');u.SystemLibrary.execute_console_command(world,'r.EyeAdaptationQuality 0')", "c.set_editor_property('skin_cache_usage',[u.SkinCacheUsage.ENABLED])\n   for cmd in ('t.MaxFPS 30','r.EyeAdaptationQuality 0','r.SkinCache.Mode 1','r.SkinCache.RecomputeTangents 1'):u.SystemLibrary.execute_console_command(world,cmd)")
code=code.replace("report['ok']=not report['errors']", "report['cache_settings']=settings_before\n report['cache_cvars']={n:u.SystemLibrary.get_console_variable_int_value(n) for n in ('r.SkinCache.CompileShaders','r.SkinCache.Mode','r.SkinCache.RecomputeTangents','r.SkinCache.DefaultBehavior','r.SkinCache.SceneMemoryLimitInMB')}\n report['ok']=not report['errors']")
exec(compile(code,__file__,'exec'))
