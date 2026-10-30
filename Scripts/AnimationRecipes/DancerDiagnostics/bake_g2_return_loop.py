import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Save the screened G2 phrase with approach, release and floating return."""
from pathlib import Path
code=(_recipe_dir/'review_g2_return_loop.py').read_text(encoding='utf-8')
exec(compile(code[:code.index('hinge={}')],__file__,'exec'))
receipt=json.loads((O/'Audit.json').read_text());summary=receipt['summary']
assert receipt['sources']==hashes and not any(summary[k] for k in ['collision_samples','reversals','rear_flags'])
assert summary['loop_matrix_error']<1e-6 and summary['radial_extent_m']<3.48
count=round(duration*60)+1
action=bpy.data.actions.new('A_F3_G2_ContactLoop_Candidate');action.use_fake_user=True
rig.animation_data_create();rig.animation_data.action=action
s.render.fps=60;s.frame_start=1;s.frame_end=count;previous={};expected={}
for frame in range(1,count+1):
 p=sample_loop((frame-1)/60);apply_pose(p)
 for pb in ordered:
  pb.rotation_mode='QUATERNION';q=pb.rotation_quaternion.copy()
  if pb.name in previous and q.dot(previous[pb.name])<0:q.negate();pb.rotation_quaternion=q
  previous[pb.name]=q.copy()
  for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(prop,frame=frame,group=pb.name)
 if (frame-1)%230==0:expected[str(frame)]={n:[list(row) for row in p[n]] for n in names}
for layer in action.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for curve in bag.fcurves:
    for key in curve.keyframe_points:key.interpolation='LINEAR'
action['source_frames']='G2 570-770; explicit approach/release/return; source original untouched'
action['quality_state']='Private selected-passage loop, not complete original G2 or approved anatomical rig'
destination=D/'G2_ContactLoop_ActionLibrary.blend';assert not destination.exists()
bpy.data.libraries.write(str(destination),{action},fake_user=True,compress=True)
rig.name='root.001';bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
folder=D/'GBSupportedRelease';folder.mkdir(exist_ok=True);fbx=folder/'G2_ContactLoop.fbx';assert not fbx.exists()
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z')
report={'sources':hashes,'source_frames':[570,770],'frames':[1,count],'fps':60,'seconds':duration,'action':action.name,'file':str(destination),'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'fbx':str(fbx),'expected_bones':expected,'scope':action['quality_state']}
(O/'Export.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
print('G2_LOOP_SAVED',report['sha256'],flush=True)
