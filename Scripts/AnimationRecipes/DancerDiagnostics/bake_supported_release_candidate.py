import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Keep one collision-screened action-only source and FBX, not another body copy."""
from pathlib import Path
exec(compile((_recipe_dir/'review_supported_release.py').read_text().split('for i in range(round((end-start)/60/rate*fps)+1):')[0],__file__,'exec'))
receipt=json.loads((O/'Audit.json').read_text())
assert receipt['summary']['collision_sample_count']==0
assert receipt['sources']==hashes
action=bpy.data.actions.new('A_F3_G1_SupportedRelease_Candidate');action.use_fake_user=True
rig.animation_data_create();rig.animation_data.action=action
for pb in ordered:pb.rotation_mode='QUATERNION'
s.render.fps=60;s.frame_start=1;s.frame_end=round((end-start)/60/rate*60)+1
previous={};expected={};max_local_translation_drift=0;max_step={n:0. for n in ['root','pelvis','upperarm_l','lowerarm_l','upperarm_r','lowerarm_r','hand_l','hand_r'] if n in names}
for frame in range(1,s.frame_end+1):
 source=start+(frame-1)/60*60*rate;p,blend=sample_release(source);apply_pose(p)
 for pb in ordered:
  pb.rotation_mode='QUATERNION';q=pb.rotation_quaternion.copy()
  if pb.name in previous:
   if q.dot(previous[pb.name])<0:q.negate();pb.rotation_quaternion=q
   if pb.name in max_step:max_step[pb.name]=max(max_step[pb.name],math.degrees(2*math.acos(min(1,abs(q.dot(previous[pb.name]))))))
  previous[pb.name]=q.copy()
  for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(prop,frame=frame,group=pb.name)
 if frame in [1,506,701,726,751,776,801,901,1101]:expected[str(frame)]={n:[list(row) for row in p[n]] for n in names}
 if frame%250==0:print('RELEASE_BAKE',frame,flush=True)
for layer in action.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for curve in bag.fcurves:
    for key in curve.keyframe_points:key.interpolation='LINEAR'
action['source_sha256']=hashes[str(D/'GB_SelectedPassages_ActionLibrary.blend')]
action['source_frames']='G1 780-1000; 0.2 playback; release920-940'
action['quality_state']='Private candidate; not a loop or complete G1/G2 repair; no owner/native acceptance.'
destination=D/'GB_SupportedRelease_ActionLibrary.blend'
assert not destination.exists(),'Do not overwrite an existing candidate'
bpy.data.libraries.write(str(destination),{action},fake_user=True,compress=True)
# Same extra armature root as the existing native Vexa proof.
rig.name='root.001';bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
fbx=D/'GBSupportedRelease';fbx.mkdir(exist_ok=True);path=fbx/'G1_SupportedRelease.fbx'
bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z')
report={'sources':hashes,'action':action.name,'file':str(destination),'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'fbx':str(path),'frames':[1,s.frame_end],'fps':60,'seconds':(s.frame_end-1)/60,'expected_bones':expected,'max_local_step_degrees':max_step,'limitations':'No loop closure, source G2 integration, chamber placement or full anatomy acceptance.'}
(O/'Export.json').write_text(json.dumps(report,indent=2))
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
print('RELEASE_CANDIDATE_SAVED',report['sha256'],flush=True)
