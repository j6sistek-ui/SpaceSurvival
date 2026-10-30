"""Save/verify an action plus a tiny weight patch, never another full mesh copy."""
import bpy, hashlib, json, os, sys, math
import numpy as np
from pathlib import Path
CODE=Path(__file__).resolve().parent
sys.path.insert(0,str(CODE))
from g2_glute_follow_control import anchor_waist_weights, glute_follow_pose
P=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()
D=P/'SourceAssets/DanceRefinement_20261025';O=P/'.agent/local/AnimationReview_20261025/G2PosteriorHip'
source=D/'Vexa_G2_PosteriorHip_Candidate.blend'
pace=json.loads((O/'PacedHipAction.json').read_text(encoding='utf-8'))
audit=json.loads((O/'GluteFollowDenseAudit.json').read_text(encoding='utf-8'))
control_hash=hashlib.sha256((CODE/'g2_glute_follow_control.py').read_bytes()).hexdigest()
assert audit['summary']['screen_passed'] and audit['summary']['samples']==5190
assert audit['glute_control_sha256']==control_hash
assert hashlib.sha256(source.read_bytes()).hexdigest()==audit['source_sha256']==pace['mesh_sha256']
assert hashlib.sha256(Path(pace['file']).read_bytes()).hexdigest()==audit['candidate_action_sha256']==pace['sha256']
output=D/'G2_GluteFollow_ActionLibrary.blend';record=D/'G2_GluteFollow_Manifest.json'
verify='--verify-only' in sys.argv
assert verify or (not output.exists() and not record.exists()), 'Preserve existing candidate'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False);s=bpy.context.scene
rig=next(o for o in s.objects if o.type=='ARMATURE')
patch=anchor_waist_weights(bpy.data.objects['Vexa_Continuous_Feet'])
assert patch==audit['glute_patch']
with bpy.data.libraries.load(pace['file'],link=False) as (_,loaded):loaded.actions=[pace['action']]
original=loaded.actions[0];assert original
if verify:
 manifest=json.loads(record.read_text(encoding='utf-8'))
 assert manifest['mesh_sha256']==pace['mesh_sha256'] and manifest['source_action_sha256']==pace['sha256']
 assert manifest['control_sha256']==control_hash and manifest['weight_patch']==patch
 assert hashlib.sha256(output.read_bytes()).hexdigest()==manifest['sha256']
 with bpy.data.libraries.load(str(output),link=False) as (_,loaded):loaded.actions=[manifest['action']]
 candidate=loaded.actions[0];assert candidate
else:
 candidate=original.copy();candidate.name='A_F3_G2_GluteFollow_Review';candidate.use_fake_user=True
 # The paced source has fractional key times. Clear these two channels before
 # rebaking, or old rest keys would remain between the new sampled keys.
 for layer in candidate.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for curve in list(bag.fcurves):
     if curve.data_path.startswith(('pose.bones["glute_l"]','pose.bones["glute_r"]')):
      bag.fcurves.remove(curve)
rest={b.name:rig.matrix_world@b.matrix_local for b in rig.data.bones}
ordered=sorted(rig.pose.bones,key=lambda b:len(b.parent_recursive));inv=rig.matrix_world.inverted()
maximum=0.;previous={};start=None;last=None
frames=(1+sample/2 for sample in range(2*pace['integer_end_frame']-1)) if verify else range(1,pace['integer_end_frame']+1)
for frame in frames:
 rig.animation_data.action=original;rig.animation_data.action_slot=original.slots[0]
 s.frame_set(math.floor(frame),subframe=frame%1);bpy.context.view_layer.update()
 expected=glute_follow_pose({b.name:rig.matrix_world@b.matrix for b in ordered},rest)
 rig.animation_data.action=candidate;rig.animation_data.action_slot=candidate.slots[0]
 if verify:
  s.frame_set(math.floor(frame),subframe=frame%1);bpy.context.view_layer.update()
  actual={b.name:rig.matrix_world@b.matrix for b in ordered}
  maximum=max(maximum,max(float(np.abs(np.array(actual[n])-np.array(expected[n])).max()) for n in expected))
  if start is None:start=actual
  last=actual
 else:
  for name in ('glute_l','glute_r'):
   bone=rig.pose.bones[name];local=inv@expected[name]
   base=(inv@expected[bone.parent.name])@bone.parent.bone.matrix_local.inverted()@bone.bone.matrix_local
   bone.rotation_mode='QUATERNION';bone.matrix_basis=base.inverted()@local
   if name in previous and bone.rotation_quaternion.dot(previous[name])<0:bone.rotation_quaternion.negate()
   previous[name]=bone.rotation_quaternion.copy()
   for prop in ('location','rotation_quaternion','scale'):bone.keyframe_insert(prop,frame=frame,group=name)
 if frame%600==1:print('GLUTE_SAVE_VERIFY',verify,frame,maximum,flush=True)
if verify:
 loop=max(float(np.abs(np.array(start[n])-np.array(last[n])).max()) for n in start)
 report={'passed':maximum<.0001 and loop<1e-5,'samples':2*pace['integer_end_frame']-1,'maximum_matrix_error':maximum,'loop_matrix_error':loop,'action_sha256':manifest['sha256'],'mesh_sha256':pace['mesh_sha256'],'control_sha256':control_hash,'weight_patch_vertices':len(patch['changes']),'scope':'Fresh saved95-bone replay versus the audited control at5189 integer/half times; exact source/patch guards. Not native, garment or artistic acceptance.'}
 (O/'GluteFollowReload.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print('GLUTE_RELOAD',json.dumps(report),flush=True)
 assert report['passed']
else:
 for layer in candidate.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for curve in bag.fcurves:
     if curve.data_path.startswith(('pose.bones["glute_l"]','pose.bones["glute_r"]')):
      for key in curve.keyframe_points:key.interpolation='LINEAR'
 candidate['required_weight_patch']='G2_GluteFollow_Manifest.json'
 candidate['required_morph_mute_prefix']='REVIEW_G2_'
 candidate['quality_state']='Private source review only; limited screens pass; not a production rig.'
 bpy.data.libraries.write(str(output),{candidate},fake_user=True,compress=True)
 manifest={'mesh_sha256':pace['mesh_sha256'],'source_action_sha256':pace['sha256'],'control_sha256':control_hash,'file':output.name,'action':candidate.name,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'weight_patch':patch,'fps':60,'frame_end':pace['integer_end_frame'],'seconds':pace['seconds'],'morph_mute_prefix':'REVIEW_G2_','scope':candidate['quality_state']}
 record.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 print('GLUTE_SAVED',manifest['sha256'],output.stat().st_size,flush=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==pace['mesh_sha256']
assert hashlib.sha256(Path(pace['file']).read_bytes()).hexdigest()==pace['sha256']
