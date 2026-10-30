import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Read the actual contact failure before choosing a free-hand route."""
from pathlib import Path
code=(_recipe_dir/'audit_supported_contact_motion.py').read_text()
exec(compile(code.split("report={'sources':hashes,'grip_source'")[0],__file__,'exec'))
rig.animation_data_create();rig.animation_data.action=acts['g1'];rig.animation_data.action_slot=acts['g1'].slots[0]
rows=[]
for frame in [934,938,940,942,944,946,948,950,954,958]:
 s.frame_set(frame);bpy.context.view_layer.update();p=supported({b.name:(rig.matrix_world@b.matrix).copy() for b in ordered})
 rows.append({'frame':frame,'joints':{n:list(p[n].translation) for n in ['clavicle_l','upperarm_l','lowerarm_l','hand_l','middle_03_l','head']}})
(R/'GBSupportedPassage/FreeHandPath.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows),flush=True)
