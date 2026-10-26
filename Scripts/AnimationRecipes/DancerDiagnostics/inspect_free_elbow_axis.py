import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

from pathlib import Path
exec(compile((_recipe_dir/'audit_supported_contact_motion.py').read_text().split("report={'sources':hashes,'grip_source'")[0],__file__,'exec'))
rig.animation_data_create();rig.animation_data.action=acts['g1'];rig.animation_data.action_slot=acts['g1'].slots[0]
rows=[]
for frame in [934,941,946,954,962]:
 s.frame_set(frame);bpy.context.view_layer.update();p=supported({b.name:(rig.matrix_world@b.matrix).copy() for b in ordered})
 base=p['upperarm_l']@rel['lowerarm_l'];basis=base.inverted()@p['lowerarm_l']
 h,k,a=[p[n].translation for n in ['upperarm_l','lowerarm_l','hand_l']]
 axis=base.to_quaternion()@Vector((0,0,1));bend=(k-h).cross(a-k).normalized()
 rows.append({'frame':frame,'local_quaternion':list(basis.to_quaternion()),'local_euler_degrees':[math.degrees(v) for v in basis.to_euler()], 'hinge_sign':axis.dot(bend)})
print('ELBOW_AXIS_RESULT',json.dumps(rows),flush=True)
