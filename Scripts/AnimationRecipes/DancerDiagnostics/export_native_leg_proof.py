import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Read isolated native assets back through FBX for a bounded parity audit."""
import unreal as u,json,traceback,time,os
from pathlib import Path
SHOULDER=os.environ.get('SS_REVIEW_SHOULDER')=='1'
BASE='/Game/SpaceSurvival/Licensed/'+('VexaShoulderProof_20261025' if SHOULDER else 'LegPlaneProof_20261025')
asset='SK_VexaShoulderProof' if SHOULDER else 'SK_RoxieHipProof'
stem='NativeVexaShoulder' if SHOULDER else 'NativeLegPlane'
report={'errors':[],'ok':False};state={'start':time.monotonic(),'done':False}
def export_after_tick(dt):
 if state['done'] or time.monotonic()-state['start']<8:return
 state['done']=True
 try:
  assert 'WorkbenchNative/CharacterWorkbench' in u.Paths.get_project_file_path().replace('\\','/')
  sk=u.load_asset(BASE+'/'+asset);clip=u.load_asset(BASE+'/'+asset+'_Anim')
  assert sk and clip and sk.skeleton
  clip.set_preview_skeletal_mesh(sk) # in-memory export context only, not saved
  report['skin_cache_cvars']={name:u.SystemLibrary.get_console_variable_int_value(name) for name in ('r.SkinCache.CompileShaders','r.SkinCache.Mode','r.SkinCache.DefaultBehavior','r.SkinCache.RecomputeTangents')}
  task=u.AssetExportTask();task.object=clip;task.filename=str(R/(stem+'Roundtrip.fbx'));task.automated=True;task.prompt=False;task.replace_identical=True
  opts=u.FbxExportOption();opts.level_of_detail=False;opts.collision=False;opts.export_preview_mesh=True;opts.export_morph_targets=True;task.options=opts
  assert u.Exporter.run_asset_export_task(task)
  report['ok']=True;report['path']=task.filename
 except Exception:report['errors'].append(traceback.format_exc())
 (R/(stem+'Export.json')).write_text(json.dumps(report,indent=2));print('NATIVE_LEG_EXPORT',report,flush=True)
 u.unregister_slate_post_tick_callback(state['handle']);u.EditorPythonScripting.set_keep_python_script_alive(False);u.SystemLibrary.quit_editor()
u.EditorPythonScripting.set_keep_python_script_alive(True);state['handle']=u.register_slate_post_tick_callback(export_after_tick)
