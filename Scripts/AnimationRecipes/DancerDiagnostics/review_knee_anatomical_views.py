import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Label anterior/posterior knee views from rest foot direction.

The earlier bend-plane 'front' was inside the flexion, not the patella side.
Capture both sides explicitly before deciding which contour needs repair.
"""
from pathlib import Path
exec(compile((_recipe_dir/'review_knee_weight_distribution.py').read_text().split("report={'source_sha256'")[0],__file__,'exec'))
O=R/'ZeroGSharedHip/KneeAnatomicalViews';O.mkdir(exist_ok=True)
report={'source_sha256':digest,'cases':[],'limitations':'Labelled diagnostic views; no anatomy acceptance or mesh edit.'}
for suffix,frame in [('01_Drift',563.5),('02_Spiral',481),('03_Butterfly',474)]:
 name='A_F3_Coordinated_ZeroG_'+suffix;act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 for on,an in pairs[name].items():
  keys=bpy.data.objects[on].data.shape_keys;keys.animation_data.action=bpy.data.actions[an];keys.animation_data.action_slot=keys.animation_data.action.slots[0]
 s.frame_set(int(frame),subframe=frame%1);bpy.context.view_layer.update()
 ev=legs.evaluated_get(bpy.context.evaluated_depsgraph_get());points=np.array([tuple(legs.matrix_world@v.co) for v in ev.data.vertices]);mesh.vertices.foreach_set('co',points.ravel());mesh.update();bpy.context.view_layer.update()
 for side in ['l','r']:
  h,k,a=[(rig.matrix_world@rig.pose.bones[n+'_'+side].matrix).translation for n in ['thigh','calf','foot']]
  upper=rig.matrix_world@rig.pose.bones['thigh_'+side].matrix
  restupper=rig.matrix_world@rig.data.bones['thigh_'+side].matrix_local
  restfoot=rig.matrix_world@rig.data.bones['foot_'+side].head_local
  restball=rig.matrix_world@rig.data.bones['ball_'+side].head_local
  # Transport the rest toe-facing direction with the thigh, then remove its
  # axial component. This remains valid as the body floats or inverts.
  forward=upper.to_3x3()@restupper.to_3x3().inverted()@(restball-restfoot)
  up=(h-k).normalized();forward=(forward-up*forward.dot(up)).normalized()
  lateral=up.cross(forward).normalized()
  inside=((a-k)-up*(a-k).dot(up)).normalized()
  report['cases'].append({'clip':suffix,'frame':frame,'side':side,'inside_dot_anterior':inside.dot(forward),'anterior':list(forward),'knee':list(k)})
  for view,offset in [('anterior',forward),('posterior',-forward),('anterior_oblique',(forward+lateral).normalized()),('lateral',lateral)]:
   cam.location=k+offset*3;cam.rotation_euler=(k-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'{suffix}_{side}_{view}.png');bpy.ops.render.render(write_still=True)
(O/'Report.json').write_text(json.dumps(report,indent=2))
assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
print('ANATOMICAL_KNEE_VIEWS_DONE',flush=True)
