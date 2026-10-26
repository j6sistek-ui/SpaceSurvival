"""Build a monotone, pose-preserving pace map; no source asset is overwritten."""
import bpy, hashlib, json, math, os, numpy as np
from pathlib import Path
P=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()
assert (P/'SpaceSurvival.uproject').is_file()
R=P/'.agent/local/AnimationReview_20261025';O=R/'G2PosteriorHip';D=P/'SourceAssets/DanceRefinement_20261025'
manifest=json.loads((O/'SmoothHipAction.json').read_text())
source=D/'Vexa_G2_PosteriorHip_Candidate.blend';library=Path(manifest['file'])
assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['source_sha256']
assert hashlib.sha256(library.read_bytes()).hexdigest()==manifest['sha256']
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
with bpy.data.libraries.load(str(library),link=False) as (_,loaded):loaded.actions=[manifest['action']]
action=loaded.actions[0];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
ordered=list(rig.pose.bones);previous=None;speed=[];root_speed=[]
first,last=map(round,action.frame_range)
for frame in range(first,last+1):
 s.frame_set(frame);bpy.context.view_layer.update()
 q=[b.rotation_quaternion.copy() for b in ordered]
 point=(rig.matrix_world@rig.pose.bones['pelvis'].matrix).translation.copy()
 if previous:
  row=[math.degrees(2*math.acos(min(1.,abs(a.dot(b))))) *60 for a,b in zip(q,previous[0])]
  speed.append(max(row));root_speed.append((point-previous[1]).length*60)
 previous=(q,point)
speed=np.array(speed);root_speed=np.array(root_speed)
# This pacing target is authored for this routine, not an anatomical limit.
angular_target=90.;root_target=.45
needed=np.maximum(1.,np.maximum(speed/angular_target,root_speed/root_target))
# Wide maximum followed by a narrower positive Gaussian keeps the result
# smooth and >= every local required slowdown without per-frame hard switching.
expanded=np.array([needed[max(0,i-30):min(len(needed),i+31)].max() for i in range(len(needed))])
kernel=np.exp(-.5*(np.arange(-24,25)/8.)**2);kernel/=kernel.sum()
slow=np.convolve(np.pad(expanded,(24,24),mode='edge'),kernel,mode='valid')
assert np.all(slow+1e-9>=needed)
source_frames=np.arange(first,last+1,dtype=float)
destination_frames=np.r_[1.,1+np.cumsum(slow)]
report={'mesh_sha256':manifest['source_sha256'],'action_sha256':manifest['sha256'],'source_frames':source_frames.tolist(),'destination_frames':destination_frames.tolist(),'source_seconds':(last-first)/60,'destination_seconds':float((destination_frames[-1]-1)/60),'minimum_speed_factor':float((1/slow).min()),'maximum_speed_factor':float((1/slow).max()),'angular_target_dps':angular_target,'root_target_mps':root_target,'before_max_local_dps':float(speed.max()),'before_max_root_mps':float(root_speed.max()),'predicted_max_local_dps':float((speed/slow).max()),'predicted_max_root_mps':float((root_speed/slow).max()),'scope':'Authored pacing-only proposal; monotonic shared time transform preserves the sampled pose path. Not a skin repair or artistic acceptance.'}
(O/'SmoothHipPacing.json').write_text(json.dumps(report,indent=2))
print('PACING',json.dumps({k:v for k,v in report.items() if not k.endswith('_frames')}),flush=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['source_sha256']
assert hashlib.sha256(library.read_bytes()).hexdigest()==manifest['sha256']
