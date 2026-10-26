import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Adaptively sample shared hip coefficients by posed interpolation error.

The shared mesh/bases stay exact. Only private curve actions gain keys. The
rest-space inverse can amplify an error; decisions use posed metric distances.
"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','4')
import bpy,json,math,hashlib,numpy as np
from pathlib import Path
O=R/'ZeroGSharedHip';D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
draft=O/'REJECTED_Interpolation.blend';output=D/'Vexa_ZeroG_SharedHip_Proof.blend';assert not output.exists()
report=json.loads((O/'Report.json').read_text());pairs=report['paired_curve_actions'];draft_hash=hashlib.sha256(draft.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(draft),load_ui=False);s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');meshes=[o for o in s.objects if o.type=='MESH']
with bpy.data.libraries.load(str(D/'ZeroG_Coordinated_ActionLibrary.blend'),link=False) as(a,b):b.actions=[n for n in a.actions if n.startswith('A_F3_Coordinated_ZeroG_') and n not in bpy.data.actions]
for action in bpy.data.actions:
 if action.name in pairs:action.use_fake_user=True
code=(Path(__file__).resolve().parent/'bake_zero_g_shared_hip.py').read_text();a=code.index('names=[b.name');b=code.index('segments=[]',a)
code=code[a:b].replace("out[n]=delta","x['pose_A']=A\n  out[n]=delta")
exec(compile(code,__file__,'exec'))
for n,x in data.items():
 keys=x['ob'].data.shape_keys;base=np.array([tuple(v.co) for v in keys.key_blocks[0].data]);correctives=[k for k in keys.key_blocks if k.name.startswith('REVIEW_ZG_')]
 vectors=np.stack([(np.array([tuple(v.co) for v in k.data])-base).ravel() for k in correctives]);x['keys']=correctives;x['vectors']=vectors
 # A small pseudo-inverse accommodates saved float32 mesh coordinates.
 x['projector']=vectors.T@np.linalg.pinv(vectors@vectors.T,rcond=1e-10)
 for key in correctives:key.mute=True
result={'draft_sha256':draft_hash,'scope':'Adaptive posed-distance interpolation on shared bases; no native/anatomy acceptance','actions':[],'holdouts':[],'paired_curve_actions':pairs};kept={bpy.data.actions[n] for n in pairs}|{bpy.data.actions[a] for p in pairs.values() for a in p.values()}
for action_name,part_actions in pairs.items():
 action=bpy.data.actions[action_name];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];first,last=map(round,action.frame_range)
 cache={};selected={};failures=[];max_projection=0.
 def sample(frame):
  nonlocal_dummy=None
  if frame in cache:return cache[frame]
  values=target(frame);row={}
  for n,delta in values.items():
   x=data[n];coeff=delta.ravel()@x['projector'];row[n]={'coeff':coeff,'expected':delta,'A':x['pose_A'].copy()}
  cache[frame]=row;return row
 def error(frame,coeffs):
  row=sample(frame);maximum=0.
  for n,c in coeffs.items():
   x=data[n];diff=(c@x['vectors']).reshape(-1,3)-row[n]['expected'];posed=np.einsum('vij,vj->vi',row[n]['A'],diff)@np.array(x['ob'].matrix_world.to_3x3()).T
   maximum=max(maximum,float(np.linalg.norm(posed,axis=1).max()))
  return maximum
 initial=list(range(first,last+1,4))
 if initial[-1]!=last:initial.append(last)
 for f in initial:selected[f]={n:x['coeff'] for n,x in sample(float(f)).items()}
 def refine(left,right,depth=0):
  mid=(left+right)*.5;mix={n:(selected[left][n]+selected[right][n])*.5 for n in data};err=error(mid,mix)
  if err<=.0002:return
  if depth>=4:failures.append({'frame':mid,'error_m':err});return
  selected[mid]={n:x['coeff'] for n,x in sample(mid).items()};refine(left,mid,depth+1);refine(mid,right,depth+1)
 for left,right in zip(initial,initial[1:]):refine(left,right)
 times=sorted(selected)
 # Quarter interval hold-outs were not used to select midpoint keys.
 for left,right in zip(times,times[1:]):
  for fraction in (.25,.75):
   frame=left+(right-left)*fraction;mix={n:selected[left][n]*(1-fraction)+selected[right][n]*fraction for n in data};err=error(frame,mix)
   if err>.0005:failures.append({'frame':frame,'error_m':err,'holdout':True})
   result['holdouts'].append({'action':action_name,'frame':frame,'posed_error_m':err})
 for n,curve_name in part_actions.items():
  x=data[n];keys=x['ob'].data.shape_keys;keys.animation_data_create();curve=bpy.data.actions[curve_name];keys.animation_data.action=curve;keys.animation_data.action_slot=curve.slots[0]
  by_path={k.path_from_id('value'):i for i,k in enumerate(x['keys'])}
  for layer in curve.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      if fc.data_path not in by_path:continue
      i=by_path[fc.data_path];fc.keyframe_points.clear();fc.keyframe_points.add(len(times));fc.keyframe_points.foreach_set('co',[v for f in times for v in (f,float(selected[f][n][i]))])
      for k in fc.keyframe_points:k.interpolation='LINEAR'
      fc.update()
 row={'action':action_name,'original_sample_count':len(initial),'refined_sample_count':len(times),'failures':failures,'max_holdout_posed_error_m':max(x['posed_error_m'] for x in result['holdouts'] if x['action']==action_name)}
 result['actions'].append(row);print('ADAPTIVE_HIP',json.dumps(row),flush=True)
 (O/'AdaptiveCurves.json').write_text(json.dumps(result,indent=2))
 assert not failures,(action_name,failures[:4])
 del cache
for n,x in data.items():
 for key in x['keys']:key.mute=False
for a in list(bpy.data.actions):
 if a not in kept:bpy.data.actions.remove(a)
select='A_F3_Coordinated_ZeroG_02_Spiral';rig.animation_data.action=bpy.data.actions[select];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
for n,a in pairs[select].items():keys=data[n]['ob'].data.shape_keys;keys.animation_data.action=bpy.data.actions[a];keys.animation_data.action_slot=keys.animation_data.action.slots[0]
s['zero_g_curve_pairs']=json.dumps(pairs);s.frame_start=1;s.frame_end=961;s.frame_set(481);bpy.data.orphans_purge(do_recursive=True);bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(output),compress=True)
assert hashlib.sha256(draft.read_bytes()).hexdigest()==draft_hash
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in report['sources'].items())
result.update(output=str(output),output_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),mesh_bases_unchanged=True)
(O/'AdaptiveCurves.json').write_text(json.dumps(result,indent=2));print('ADAPTIVE_HIP_DONE',flush=True)
