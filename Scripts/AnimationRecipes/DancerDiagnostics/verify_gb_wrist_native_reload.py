import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Read-only dependency/duration reload of the eight native comparison clips."""
import unreal as u,json
from pathlib import Path

assert 'WorkbenchNative/CharacterWorkbench' in u.Paths.get_project_file_path().replace('\\','/')
base='/Game/SpaceSurvival/Licensed/VexaContinuousDistalProof_20261025'
sk=u.load_asset(base+'/SK_VexaContinuousDistalProof');assert sk and sk.skeleton
rows=[]
for entry in json.loads((R/'VexaDistalRepair/GBWristExport.json').read_text())['exports']:
 name='A_Wrist_'+entry['clip']+'_'+entry['kind'];clip=u.load_asset(base+'/'+name)
 assert clip and clip.get_editor_property('skeleton')==sk.skeleton
 assert abs(clip.sequence_length-entry['seconds'])<.02
 rows.append({'asset':clip.get_path_name(),'seconds':clip.sequence_length,'skeleton':sk.skeleton.get_path_name()})
(R/'VexaDistalRepair/GBNativeReload.json').write_text(json.dumps({'ok':len(rows)==8,'scope':'Fresh-process dependency/duration reload only, no visual acceptance','clips':rows},indent=2))
print('GB_WRIST_NATIVE_RELOAD',len(rows),flush=True)
