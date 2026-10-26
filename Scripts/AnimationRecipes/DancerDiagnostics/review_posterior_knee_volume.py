import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""A localized posterior-only volume control; preserve the anterior contour.

Compare small blends of the DQ target behind the knee, with a 12mm maximum
target displacement. Prior whole-knee DQ puffed the front; it is not reused.
No weights, rig, topology or source asset are changed or saved.
"""
from pathlib import Path
exec(compile((_recipe_dir/'review_aligned_knee_targets.py').read_text().split("report={'source_sha256'")[0],__file__,'exec'))
O=R/'ZeroGSharedHip/PosteriorKneeVolume';O.mkdir(exist_ok=True)
posterior=np.zeros(len(rest))
for i,side in enumerate(['l','r']):
 foot=rig.matrix_world@rig.data.bones['foot_'+side].head_local;ball=rig.matrix_world@rig.data.bones['ball_'+side].head_local
 direction=np.array((foot-ball).normalized());direction[2]=0;direction/=np.linalg.norm(direction)
 d=(rest-centers[i])@direction
 blend=np.clip((d+.005)/.055,0,1);blend=blend*blend*(3-2*blend)
 posterior[nearest==i]=blend[nearest==i]
weights=mask*posterior
report={'source_sha256':digest,'scope':'posterior evaluated snapshots only; no mesh edit or acceptance','poses':[]}
for suffix,frame in [('01_Drift',563.5),('02_Spiral',481),('03_Butterfly',474)]:
 name='A_F3_Coordinated_ZeroG_'+suffix;act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 for on,an in pairs[name].items():
  keys=bpy.data.objects[on].data.shape_keys;keys.animation_data.action=bpy.data.actions[an];keys.animation_data.action_slot=keys.animation_data.action.slots[0]
 s.frame_set(math.floor(frame),subframe=frame%1);mod.use_deform_preserve_volume=False;linear=evaluate();mod.use_deform_preserve_volume=True;dq=evaluate();mod.use_deform_preserve_volume=False;bpy.context.view_layer.update()
 delta=(dq-linear)*weights[:,None];length=np.linalg.norm(delta,axis=1);delta*=np.minimum(1,.012/np.maximum(length,1e-12))[:,None]
 modes={'baseline':linear,'posterior35':linear+delta*.35,'posterior65':linear+delta*.65}
 h,k,a=[(rig.matrix_world@rig.pose.bones[n+'_r'].matrix).translation for n in ['thigh','calf','foot']]
 up=(h-k).normalized();inside=((a-k)-up*(a-k).dot(up)).normalized();normal=up.cross(inside).normalized()
 row={'action':suffix,'frame':frame,'max_displacement_mm':{n:float(np.linalg.norm(v-linear,axis=1).max()*1000) for n,v in modes.items()}}
 for view,offset in [('posterior',inside),('posterior_oblique',(inside+normal).normalized()),('lateral',normal),('anterior',-inside)]:
  cam.location=k+offset*3;cam.rotation_euler=(k-cam.location).to_track_quat('-Z','Y').to_euler()
  for label,points in modes.items():
   mesh.vertices.foreach_set('co',points.ravel());mesh.update();bpy.context.view_layer.update();s.render.filepath=str(O/f'{suffix}_{view}_{label}.png');bpy.ops.render.render(write_still=True)
 report['poses'].append(row)
(O/'Report.json').write_text(json.dumps(report,indent=2));assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
print('POSTERIOR_KNEE_CONTROL_DONE',flush=True)
