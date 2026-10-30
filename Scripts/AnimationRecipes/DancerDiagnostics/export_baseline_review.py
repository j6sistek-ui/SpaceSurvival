import os
from pathlib import Path
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

import unreal as u,json,traceback
from pathlib import Path
report={'exports':[],'errors':[]}
try:
 assert 'CharacterWorkbench' in u.Paths.get_project_file_path()
 source=json.loads((R/'NativeSourceBaseline.json').read_text())
 for path in source['retargeted']:
  a=u.load_asset(path);target=R/'SourceBaseline'/(a.get_name()+'.fbx')
  task=u.AssetExportTask();task.object=a;task.filename=str(target);task.automated=True;task.prompt=False;task.replace_identical=True
  opts=u.FbxExportOption();opts.level_of_detail=False;opts.collision=False;task.options=opts
  assert u.Exporter.run_asset_export_task(task)
  report['exports'].append(str(target));print('BASELINE_EXPORT',target,flush=True)
 report['ok']=True
except Exception:report['errors'].append(traceback.format_exc())
(R/'BaselineExports.json').write_text(json.dumps(report,indent=2));print('BASELINE_EXPORT_RESULT',report,flush=True)
