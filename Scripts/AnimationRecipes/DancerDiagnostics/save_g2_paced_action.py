"""Time-only derivative; all linear channels share the same monotone mapping."""
import bpy, json, hashlib, math, os, numpy as np
from pathlib import Path
P=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()
assert (P/'SpaceSurvival.uproject').is_file()
R=P/'.agent/local/AnimationReview_20261025';O=R/'G2PosteriorHip';D=P/'SourceAssets/DanceRefinement_20261025'
manifest=json.loads((O/'SmoothHipAction.json').read_text());pace=json.loads((O/'SmoothHipPacing.json').read_text())
source=D/'Vexa_G2_PosteriorHip_Candidate.blend';library=Path(manifest['file']);destination=D/'G2_PacedHip_ActionLibrary.blend'
assert not destination.exists()
assert hashlib.sha256(library.read_bytes()).hexdigest()==pace['action_sha256']==manifest['sha256']
assert hashlib.sha256(source.read_bytes()).hexdigest()==pace['mesh_sha256']==manifest['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
with bpy.data.libraries.load(str(library),link=False) as (_,loaded):loaded.actions=[manifest['action']]
original=loaded.actions[0];candidate=original.copy();candidate.name='A_F3_G2_PacedHip_Review';candidate.use_fake_user=True
src=np.array(pace['source_frames']);dest=np.array(pace['destination_frames'])
stretch=math.ceil(dest[-1]-1)/(dest[-1]-1);dest=1+(dest-1)*stretch
count=0
for layer in candidate.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for curve in bag.fcurves:
    assert not curve.modifiers
    for key in curve.keyframe_points:
     assert key.interpolation=='LINEAR'
     assert src[0]-.001<=key.co.x<=src[-1]+.001
     key.co.x=float(np.interp(key.co.x,src,dest));count+=1
    curve.update()
candidate['source_action_sha256']=manifest['sha256']
candidate['quality_state']='Pacing-only review: complete pose-path and contact equality still requires fresh validation; not accepted anatomy.'
candidate['required_morph_mute_prefix']='REVIEW_G2_'
bpy.data.libraries.write(str(destination),{candidate},fake_user=True,compress=True)
report={'mesh_sha256':manifest['source_sha256'],'source_action_sha256':manifest['sha256'],'action':candidate.name,'file':str(destination),'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'source_frames':src.tolist(),'destination_frames':dest.tolist(),'fps':60,'seconds':float((dest[-1]-1)/60),'integer_end_frame':round(dest[-1]),'key_count':count,'time_scale_for_integer_end':stretch,'scope':candidate['quality_state']}
(O/'PacedHipAction.json').write_text(json.dumps(report,indent=2))
print('PACED_ACTION',report['sha256'],report['seconds'],count,flush=True)
assert hashlib.sha256(library.read_bytes()).hexdigest()==manifest['sha256']
assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['source_sha256']
