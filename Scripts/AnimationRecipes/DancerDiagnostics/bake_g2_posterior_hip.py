import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Bake localized hip volume into exportable, motion-specific shape curves.

Copies preserved Vexa geometry and the contact-only G2 action. Bone motion,
weights, topology and rest joints remain unchanged. The DQ target is limited
to a smooth rest-space hip mask and is transferred back through the LBS matrix.
No global Preserve Volume switch is relied on for Unreal playback.
"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','4')
import bpy, hashlib, json, math, sys, numpy as np
from pathlib import Path
P=R.parents[2]
sys.path.insert(0,str(_recipe_dir))
from hip_posterior_mask import posterior_mask
D=P/'SourceAssets/DanceRefinement_20261025';O=R/'G2PosteriorHip';O.mkdir(exist_ok=True)
mesh_file=D/'Vexa_LegIsolation_Proof.blend';action_file=D/'G2_ClearContact_ActionLibrary.blend'
destination=D/'Vexa_G2_PosteriorHip_Candidate.blend'
assert not destination.exists(), 'Preserve prior outputs'
expected={str(mesh_file):'8cd382f7f12e3ea75b5e4a325915b31b48eaedf442177dae402ad4bab91f3e3b',
 str(action_file):'e80efde6391f1627f5739c9c9a1b5371589ca6f0e6201549ddbdd674816779e7'}
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in expected.items())
bpy.ops.wm.open_mainfile(filepath=str(mesh_file),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
meshes=[o for o in s.objects if o.type=='MESH' and not o.hide_render and not o.hide_get()]
for ob in list(s.objects):
 if ob not in meshes+[rig]:bpy.data.objects.remove(ob,do_unlink=True)
for ob in meshes:
 if ob.data.shape_keys:
  ob.data.shape_keys.animation_data_clear()
  for key in list(ob.data.shape_keys.key_blocks):
   if key.name.startswith('REVIEW_'):ob.shape_key_remove(key)
with bpy.data.libraries.load(str(action_file),link=False) as(_,target):target.actions=['A_F3_G2_ClearContact_Candidate']
action=target.actions[0];assert action
action.use_fake_user=True;rig.animation_data_create();rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
s.render.fps=60;first,last=map(round,action.frame_range);s.frame_start=first;s.frame_end=last
names=[b.name for b in rig.data.bones if b.use_deform];index={n:i for i,n in enumerate(names)}
centers=np.array([tuple(rig.matrix_world@rig.data.bones['thigh_'+side].head_local) for side in ('l','r')])
data={}
for ob in meshes:
 mod=next((m for m in ob.modifiers if m.type=='ARMATURE'),None)
 if not mod:continue
 points=np.array([tuple(ob.matrix_world@v.co) for v in ob.data.vertices])
 distance=np.linalg.norm(points[:,None,:]-centers[None,:,:],axis=2).min(axis=1)
 mask=posterior_mask(points,centers)
 if mask.max()<1e-7:continue
 weights=np.zeros((len(points),len(names)))
 for v in ob.data.vertices:
  for g in v.groups:
   n=ob.vertex_groups[g.group].name
   if n in index:weights[v.index,index[n]]=g.weight
 weights/=np.maximum(weights.sum(axis=1)[:,None],1e-12)
 data[ob.name]={'ob':ob,'mod':mod,'mask':mask,'weights':weights,'world3':np.array(ob.matrix_world.to_3x3()),'scale':max(ob.matrix_world.to_scale())}
def evaluate(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());points=np.empty(len(ev.data.vertices)*3)
 ev.data.vertices.foreach_get('co',points);return points.reshape(-1,3)
def sample(frame):
 s.frame_set(math.floor(frame),subframe=frame%1)
 for x in data.values():x['mod'].use_deform_preserve_volume=False
 bpy.context.view_layer.update();linear={n:evaluate(x['ob']) for n,x in data.items()}
 for x in data.values():x['mod'].use_deform_preserve_volume=True
 bpy.context.view_layer.update();volume={n:evaluate(x['ob']) for n,x in data.items()}
 for x in data.values():x['mod'].use_deform_preserve_volume=False
 bpy.context.view_layer.update();result={}
 for n,x in data.items():
  ob=x['ob'];left=ob.matrix_world.inverted()@rig.matrix_world;right=rig.matrix_world.inverted()@ob.matrix_world
  transforms=np.array([np.array((left@rig.pose.bones[name].matrix@rig.data.bones[name].matrix_local.inverted()@right).to_3x3()) for name in names])
  A=np.einsum('vb,bij->vij',x['weights'],transforms,optimize=True)
  active=x['mask']>1e-7;assert np.all(np.abs(np.linalg.det(A[active]))>.01),(n,frame,'Singular skinning')
  delta=np.zeros_like(linear[n]);delta[active]=np.linalg.solve(A[active],((volume[n]-linear[n])*x['mask'][:,None])[active,:,None])[...,0]
  result[n]={'delta':delta,'A':A}
 return result
initial=list(range(first,last+1,4))
if initial[-1]!=last:initial.append(last)
samples={n:[] for n in data}
for f in initial:
 for n,x in sample(f).items():samples[n].append(x['delta'].astype(np.float32))
print('G2_HIP_TARGETS',len(initial),flush=True)
report={'sources':expected,'motion':action.name,'frames':[first,last],'fps':60,
 'method':'Localized DQ-minus-LBS target; inverse-LBS shape transfer; same bones, weights and topology.',
 'mask':{'file':'hip_posterior_mask.py','sha256':hashlib.sha256((_recipe_dir/'hip_posterior_mask.py').read_bytes()).hexdigest(),'scope':'Posterior lateral hip; excludes midline and anterior thigh'},'meshes':[],'holdouts':[]}
for n,x in data.items():
 arr=np.stack(samples.pop(n)).reshape(len(initial),-1).astype(np.float64)
 values,U=np.linalg.eigh(arr@arr.T);order=np.argsort(values)[::-1];values=values[order];U=U[:,order]
 available=np.count_nonzero(values>max(values[0]*1e-12,1e-14));limit=min(128,int(available));assert limit>0
 S=np.sqrt(values[:limit]);V=(U[:,:limit].T@arr)/S[:,None];C=U[:,:limit]*S
 for rank in sorted(set(min(k,limit) for k in (8,16,24,32,48,64,96,128))):
  error=float(np.linalg.norm((C[:,:rank]@V[:rank]-arr).reshape(len(initial),-1,3),axis=2).max()*x['scale'])
  if error<.00015:break
 assert error<.00015,(n,rank,error)
 x['basis']=V[:rank];x['coeff']=C[:,:rank];x['keys']=[];x['amplitudes']=[]
 ob=x['ob']
 if not ob.data.shape_keys:ob.shape_key_add(name='Basis')
 base=np.array([tuple(v.co) for v in ob.data.shape_keys.key_blocks[0].data])
 for i in range(rank):
  amp=max(float(np.abs(C[:,i]).max()),1e-6);key=ob.shape_key_add(name=f'REVIEW_G2_Hip_{n}_{i:02}',from_mix=False)
  key.slider_min=-10;key.slider_max=10;key.mute=True
  key.data.foreach_set('co',(base+V[i].reshape(-1,3)*amp).ravel());x['keys'].append(key);x['amplitudes'].append(amp)
 # Fit to float32-stored basis, not the unsaved ideal basis.
 vectors=np.stack([(np.array([tuple(v.co) for v in key.data])-base).ravel() for key in x['keys']])
 x['vectors']=vectors;x['projector']=vectors.T@np.linalg.pinv(vectors@vectors.T,rcond=1e-10)
 report['meshes'].append({'name':n,'rank':rank,'sample_compression_error_m':error,'vertices':len(ob.data.vertices)})
 print('G2_HIP_BASIS',n,rank,error,flush=True)
selected={};cache={}
def coefficients(frame):
 row=sample(frame)
 return {n:x['delta'].ravel()@data[n]['projector'] for n,x in row.items()},row
for f in initial:selected[f]=coefficients(f)[0]
def posed_error(frame,coef):
 _,row=coefficients(frame);maximum=0.
 for n,x in data.items():
  difference=(coef[n]@x['vectors']).reshape(-1,3)-row[n]['delta']
  posed=np.einsum('vij,vj->vi',row[n]['A'],difference)@x['world3'].T
  maximum=max(maximum,float(np.linalg.norm(posed,axis=1).max()))
 return maximum
failures=[]
def refine(a,b,depth=0):
 mid=(a+b)*.5;coef={n:(selected[a][n]+selected[b][n])*.5 for n in data};error=posed_error(mid,coef)
 if error<=.0002:return
 if depth>=4:failures.append({'frame':mid,'error_m':error});return
 selected[mid]=coefficients(mid)[0];refine(a,mid,depth+1);refine(mid,b,depth+1)
for a,b in zip(initial,initial[1:]):refine(a,b)
times=sorted(selected)
for a,b in zip(times,times[1:]):
 for factor in (.25,.75):
  frame=a+(b-a)*factor;coef={n:selected[a][n]*(1-factor)+selected[b][n]*factor for n in data};error=posed_error(frame,coef)
  report['holdouts'].append({'frame':frame,'posed_error_m':error})
  if error>.0005:failures.append({'frame':frame,'error_m':error})
report.update(curve_samples=len(times),failures=failures,max_holdout_error_m=max(r['posed_error_m'] for r in report['holdouts']))
(O/'BakeReport.json').write_text(json.dumps(report,indent=2))
assert not failures,failures[:4]
pairs={};kept={action}
for n,x in data.items():
 keys=x['ob'].data.shape_keys;keys.animation_data_clear()
 for i,key in enumerate(x['keys']):
  key.mute=False
  for f in times:key.value=float(selected[f][n][i]);key.keyframe_insert('value',frame=f)
 curve=keys.animation_data.action;curve.name='G2_HipVolume_'+n;curve.use_fake_user=True;pairs[n]=curve.name;kept.add(curve)
 for layer in curve.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for point in fc.keyframe_points:point.interpolation='LINEAR'
for a in list(bpy.data.actions):
 if a not in kept:bpy.data.actions.remove(a)
s['g2_hip_curve_pairs']=json.dumps(pairs);s['g2_quality_state']='Hip-volume candidate only; lower-limb range, clothing and native review still open.'
s.frame_set(637);bpy.context.preferences.filepaths.save_version=0;bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=str(destination),compress=True)
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in expected.items())
report.update(destination=str(destination),sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),paired_curve_actions=pairs)
(O/'BakeReport.json').write_text(json.dumps(report,indent=2));print('G2_HIP_BAKE_DONE',report['sha256'],report['max_holdout_error_m'],flush=True)
