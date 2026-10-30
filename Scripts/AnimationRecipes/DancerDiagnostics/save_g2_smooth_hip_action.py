"""Save an isolated action-only review candidate after dense geometry checks."""
import bpy, hashlib, json, math, sys, os
import numpy as np
from pathlib import Path
CODE=Path(__file__).resolve().parent
sys.path.insert(0,str(CODE))
from g2_smooth_hip_control import corrected_pose
P=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()
assert (P/'SpaceSurvival.uproject').is_file()
R=P/'.agent/local/AnimationReview_20261025';D=P/'SourceAssets/DanceRefinement_20261025';O=R/'G2PosteriorHip'
source=D/'Vexa_G2_PosteriorHip_Candidate.blend'
destination=D/'G2_SmoothHip_ActionLibrary.blend'
assert not destination.exists(), 'Preserve existing output'
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
assert source_hash=='aa7da9855d2a5af57806674988c2d1017411ccb04201d4d0570a7138c0c3bdae'
receipt=json.loads((O/'SmoothHipAudit.json').read_text())
assert receipt['source_sha256']==source_hash
assert receipt['control_sha256']==hashlib.sha256((CODE/'g2_smooth_hip_control.py').read_bytes()).hexdigest()
summary=receipt['summary']
assert summary['flagged_samples']==summary['contact_flagged_samples']==0
assert summary['samples']==3682 and summary['loop_matrix_error']<1e-6
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
original_action=rig.animation_data.action;original_slot=rig.animation_data.action_slot
candidate=original_action.copy();candidate.name='A_F3_G2_SmoothHip_Review'
candidate.use_fake_user=True
rest={b.name:rig.matrix_world@b.matrix_local for b in rig.data.bones}
ordered=sorted(rig.pose.bones,key=lambda b:len(b.parent_recursive))
desc={b.name:[b.name]+[c.name for c in b.children_recursive] for b in ordered}
inv=rig.matrix_world.inverted();previous={};expected={}
for frame in range(s.frame_start,s.frame_end+1):
 rig.animation_data.action=original_action;rig.animation_data.action_slot=original_slot
 s.frame_set(frame);bpy.context.view_layer.update()
 original={b.name:rig.matrix_world@b.matrix for b in ordered}
 pose,angles=corrected_pose(original,rest,desc)
 rig.animation_data.action=candidate;rig.animation_data.action_slot=candidate.slots[0]
 local={n:inv@m for n,m in pose.items()}
 for name in ('thigh_l','thigh_r'):
  b=rig.pose.bones[name]
  base=local[b.parent.name]@b.parent.bone.matrix_local.inverted()@b.bone.matrix_local
  b.rotation_mode='QUATERNION';b.matrix_basis=base.inverted()@local[name]
  if name in previous and b.rotation_quaternion.dot(previous[name])<0:b.rotation_quaternion.negate()
  previous[name]=b.rotation_quaternion.copy()
  for prop in ('location','rotation_quaternion','scale'):b.keyframe_insert(prop,frame=frame,group=name)
 if (frame-1)%120==0 or frame==s.frame_end:
  expected[str(frame)]={n:[list(row) for row in m] for n,m in pose.items()}
for layer in candidate.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for curve in bag.fcurves:
    if curve.data_path.startswith(('pose.bones["thigh_l"]','pose.bones["thigh_r"]')):
     for key in curve.keyframe_points:key.interpolation='LINEAR'
candidate['quality_state']='Review only: limited 60Hz hip/pole/distal-arm screens clear. Not anatomy/artistic or native acceptance.'
candidate['source_mesh_sha256']=source_hash
candidate['control_sha256']=hashlib.sha256((CODE/'g2_smooth_hip_control.py').read_bytes()).hexdigest()
candidate['required_morph_mute_prefix']='REVIEW_G2_'
bpy.data.libraries.write(str(destination),{candidate},fake_user=True,compress=True)
report={'source_sha256':source_hash,'control_sha256':candidate['control_sha256'],'file':str(destination),'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'action':candidate.name,'fps':60,'frames':[s.frame_start,s.frame_end],'expected_bones':expected,'scope':candidate['quality_state'],'morph_mute_prefix':'REVIEW_G2_'}
(O/'SmoothHipAction.json').write_text(json.dumps(report,indent=2))
assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash
print('SMOOTH_HIP_ACTION',report['sha256'],destination.stat().st_size,flush=True)
