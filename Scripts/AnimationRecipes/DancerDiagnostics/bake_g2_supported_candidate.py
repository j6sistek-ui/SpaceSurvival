import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Save only the densely clear G2 subpassage, retaining the wider failure."""
from pathlib import Path
code=(_recipe_dir/'review_g2_supported_passage.py').read_text()
exec(compile(code[:code.index('hinge={}')],__file__,'exec'))
receipt=json.loads((O/'Audit.json').read_text());assert receipt['sources']==hashes
a,b=570,770;chosen=[x for x in receipt['samples'] if a<=x['source_frame']<=b]
assert len(chosen)==1001 and not any(x['collisions'] or any(z['reversal'] or z['rear_flag'] for z in x['arms']) for x in chosen)
action=bpy.data.actions.new('A_F3_G2_SupportedPassage_Candidate');action.use_fake_user=True
rig.animation_data_create();rig.animation_data.action=action
s.render.fps=60;s.frame_start=1;s.frame_end=1001;previous={};expected={}
for frame in range(1,1002):
 p=sample_passage(a+(frame-1)*.2);apply_pose(p)
 for pb in ordered:
  pb.rotation_mode='QUATERNION';q=pb.rotation_quaternion.copy()
  if pb.name in previous and q.dot(previous[pb.name])<0:q.negate();pb.rotation_quaternion=q
  previous[pb.name]=q.copy()
  for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(prop,frame=frame,group=pb.name)
 if frame in [1,126,251,376,501,626,751,876,1001]:expected[str(frame)]={n:[list(row) for row in p[n]] for n in names}
for layer in action.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for curve in bag.fcurves:
    for key in curve.keyframe_points:key.interpolation='LINEAR'
action['source_sha256']=hashes[str(D/'GB_SelectedPassages_ActionLibrary.blend')]
action['source_frames']='G2 570-770, 0.2 playback; preceding525-770 trial rejected for27 collision samples'
action['quality_state']='Private subpassage; entrance/exit/loop/anatomy not accepted'
destination=D/'G2_SupportedPassage_ActionLibrary.blend';assert not destination.exists()
bpy.data.libraries.write(str(destination),{action},fake_user=True,compress=True)
rig.name='root.001';bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
folder=D/'GBSupportedRelease';folder.mkdir(exist_ok=True);fbx=folder/'G2_SupportedPassage.fbx';assert not fbx.exists()
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z')
report={'sources':hashes,'source_frames':[a,b],'rate':.2,'frames':[1,1001],'fps':60,'seconds':1000/60,'action':action.name,'file':str(destination),'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'fbx':str(fbx),'expected_bones':expected,'scope':'Clear sampled subpassage, no entrance/exit/loop/native/full-anatomy acceptance'}
(O/'Export.json').write_text(json.dumps(report,indent=2));assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
print('G2_CANDIDATE_SAVED',report['sha256'],flush=True)
