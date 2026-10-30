import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Fresh Blender action reload: compare all saved joints at nine poses."""
import bpy,json,hashlib,numpy as np
from pathlib import Path
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
report=json.loads((R/'GBSupportedRelease/Export.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(D/'Vexa_HandIsolation_Proof.blend'),load_ui=False)
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
with bpy.data.libraries.load(report['file'],link=False) as(a,b):b.actions=[report['action']]
action=b.actions[0];assert action and len(action.slots)==1
rig.animation_data_create();rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
rows=[]
for frame,bones in report['expected_bones'].items():
 bpy.context.scene.frame_set(int(frame));bpy.context.view_layer.update();maximum=0
 for n,expected in bones.items():
  matrix=np.array(rig.matrix_world@rig.pose.bones[n].matrix);maximum=max(maximum,float(np.abs(matrix-np.array(expected)).max()))
 assert maximum<.00005,(frame,maximum)
 rows.append({'frame':int(frame),'max_matrix_element_error':maximum})
result={'sha256':hashlib.sha256(Path(report['file']).read_bytes()).hexdigest(),'bone_count':len(rig.pose.bones),'action':action.name,'frames':list(action.frame_range),'samples':rows,'ok':True}
assert result['sha256']==report['sha256']
(R/'GBSupportedRelease/Reload.json').write_text(json.dumps(result,indent=2));print('RELEASE_RELOAD_OK',json.dumps(result),flush=True)
