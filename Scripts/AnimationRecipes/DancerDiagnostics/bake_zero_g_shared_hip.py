import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""One private Vexa mesh, shared localized hip bases, five paired curve actions.

Recompute per-motion targets; never reuse the old Spiral's time-indexed curves.
Basis compression and hold-outs measure transfer fidelity, not anatomy approval.
"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','4')
import bpy,hashlib,json,math,numpy as np
from pathlib import Path
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025';O=R/'ZeroGSharedHip';O.mkdir(exist_ok=True)
source=D/'Vexa_HandIsolation_Proof.blend';library=D/'ZeroG_Coordinated_ActionLibrary.blend';output=D/'Vexa_ZeroG_SharedHip_Proof.blend'
assert not output.exists()
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (source,library)}
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False);s=bpy.context.scene;s.render.fps=60
rig=next(o for o in s.objects if o.type=='ARMATURE')
meshes=[o for o in s.objects if o.type=='MESH' and not o.hide_render and not o.hide_get()]
for ob in list(s.objects):
 if ob not in meshes+[rig]:bpy.data.objects.remove(ob,do_unlink=True)
removed={}
for ob in meshes:
 if not ob.data.shape_keys:continue
 keys=ob.data.shape_keys;keys.animation_data_clear();removed[ob.name]=[]
 for key in list(keys.key_blocks):
  if key.name.startswith('REVIEW_'):
   removed[ob.name].append(key.name);ob.shape_key_remove(key)
with bpy.data.libraries.load(str(library),link=False) as(a,b):b.actions=[n for n in a.actions if n.startswith('A_F3_Coordinated_ZeroG_')]
actions=sorted(b.actions,key=lambda a:a.name);assert len(actions)==5
for action in actions:action.use_fake_user=True
names=[b.name for b in rig.data.bones if b.use_deform];index={n:i for i,n in enumerate(names)}
centers=np.array([tuple(rig.matrix_world@rig.data.bones['thigh_'+x].head_local) for x in ('l','r')]);data={}
for ob in meshes:
 mod=next((m for m in ob.modifiers if m.type=='ARMATURE'),None)
 if not mod:continue
 points=np.array([tuple(ob.matrix_world@v.co) for v in ob.data.vertices]);dist=np.linalg.norm(points[:,None,:]-centers[None,:,:],axis=2).min(axis=1)
 mask=np.clip((.42-dist)/.22,0,1);mask=mask*mask*(3-2*mask)
 if mask.max()<1e-7:continue
 weights=np.zeros((len(ob.data.vertices),len(names)))
 for v in ob.data.vertices:
  for g in v.groups:
   n=ob.vertex_groups[g.group].name
   if n in index:weights[v.index,index[n]]=g.weight
 weights/=np.maximum(weights.sum(axis=1)[:,None],1e-12)
 data[ob.name]={'ob':ob,'mod':mod,'mask':mask,'weights':weights,'samples':[],'scale':max(ob.matrix_world.to_scale())}
assert data
def evaluate(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());x=np.empty(len(ev.data.vertices)*3);ev.data.vertices.foreach_get('co',x);return x.reshape(-1,3)
def target(frame):
 s.frame_set(math.floor(frame),subframe=frame%1)
 for x in data.values():x['mod'].use_deform_preserve_volume=False
 bpy.context.view_layer.update();lin={n:evaluate(x['ob']) for n,x in data.items()}
 for x in data.values():x['mod'].use_deform_preserve_volume=True
 bpy.context.view_layer.update();vol={n:evaluate(x['ob']) for n,x in data.items()}
 for x in data.values():x['mod'].use_deform_preserve_volume=False
 bpy.context.view_layer.update();out={}
 for n,x in data.items():
  ob=x['ob'];left=ob.matrix_world.inverted()@rig.matrix_world;right=rig.matrix_world.inverted()@ob.matrix_world
  matrices=np.array([np.array((left@rig.pose.bones[b].matrix@rig.data.bones[b].matrix_local.inverted()@right).to_3x3()) for b in names])
  A=np.einsum('vb,bij->vij',x['weights'],matrices,optimize=True);active=x['mask']>1e-7;valid=np.abs(np.linalg.det(A))>.01
  assert np.all(valid[active]),(n,frame,'Near-singular active hip skinning')
  delta=np.zeros_like(lin[n]);delta[active]=np.linalg.solve(A[active],((vol[n]-lin[n])*x['mask'][:,None])[active,:,None])[...,0]
  out[n]=delta
 return out
segments=[];sample_rows=[];cursor=0
for action in actions:
 rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
 first,last=map(round,action.frame_range);frames=list(range(first,last+1,4))
 if frames[-1]!=last:frames.append(last)
 start=cursor
 for f in frames:
  values=target(f)
  for n,v in values.items():data[n]['samples'].append(v.astype(np.float32))
  sample_rows.append((action.name,f));cursor+=1
 segments.append({'action':action.name,'start':start,'stop':cursor,'frames':frames})
 print('HIP_SEGMENT_SAMPLED',action.name,len(frames),flush=True)
report={'sources':hashes,'removed_old_review_keys_on_copy':removed,'scope':'Shared pose-sampled hip targets; private and unaccepted','meshes':[],'segments':segments,'holdouts':[]};paired={a.name:{} for a in actions};kept=set(actions)
for n,x in data.items():
 arr=np.stack(x.pop('samples')).reshape(cursor,-1).astype(np.float64)
 # Gram decomposition avoids a large full right-singular matrix on long clips.
 values,U=np.linalg.eigh(arr@arr.T);order=np.argsort(values)[::-1];values=values[order];U=U[:,order]
 available=int(np.count_nonzero(values>max(values[0]*1e-12,1e-14)));limit=min(96,available)
 if limit==0:continue
 S=np.sqrt(np.maximum(values[:limit],0));V=(U[:,:limit].T@arr)/S[:,None];C=U[:,:limit]*S
 rank=limit;error=0
 for candidate in sorted(set([min(k,limit) for k in (8,16,24,32,48,64,96)])):
  error=float(np.linalg.norm((C[:,:candidate]@V[:candidate]-arr).reshape(cursor,-1,3),axis=2).max()*x['scale'])
  if error<.0002:rank=candidate;break
 assert error<.0002,(n,'Basis transfer error',error,rank)
 basis=V[:rank];coef=C[:,:rank];ob=x['ob']
 if not ob.data.shape_keys:ob.shape_key_add(name='Basis')
 base=np.array([tuple(v.co) for v in ob.data.shape_keys.key_blocks[0].data]);created=[]
 for i in range(rank):
  amplitude=max(float(np.abs(coef[:,i]).max()),1e-6);key=ob.shape_key_add(name=f'REVIEW_ZG_Hip_{n}_{i:02}',from_mix=False);key.slider_min=-10;key.slider_max=10
  key.data.foreach_set('co',(base+basis[i].reshape(-1,3)*amplitude).ravel());created.append((key,amplitude))
 for segment in segments:
  keys=ob.data.shape_keys;keys.animation_data_clear()
  for i,(key,amp) in enumerate(created):
   for f,v in zip(segment['frames'],coef[segment['start']:segment['stop'],i]/amp):key.value=float(v);key.keyframe_insert('value',frame=f)
  act=keys.animation_data.action;act.name='ZG_Hip_'+segment['action'].split('ZeroG_')[1]+'_'+n;act.use_fake_user=True;kept.add(act)
  for layer in act.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for key in fc.keyframe_points:key.interpolation='LINEAR'
  paired[segment['action']][n]=act.name
 x.update(basis=basis,coeff=coef,created=created)
 report['meshes'].append({'mesh':n,'rank':rank,'compression_error_m':error,'sample_count':cursor,'vertices':len(ob.data.vertices)})
 print('HIP_SHARED_BASES',json.dumps(report['meshes'][-1]),flush=True)
def assign(action):
 rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
 for n,x in data.items():
  if n not in paired[action.name]:continue
  keys=x['ob'].data.shape_keys;keys.animation_data_create();a=bpy.data.actions[paired[action.name][n]];keys.animation_data.action=a;keys.animation_data.action_slot=a.slots[0]
for action in actions:
 assign(action);last=round(action.frame_range[1])
 for frame in sorted(set([1,last]+[min(last,1+(last-1)*i/12+1.5) for i in range(1,12)])):
  for x in data.values():
   for key,amp in x.get('created',[]):key.mute=True
  expected=target(frame)
  for x in data.values():
   for key,amp in x.get('created',[]):key.mute=False
  s.frame_set(math.floor(frame),subframe=frame%1);bpy.context.view_layer.update()
  for n,x in data.items():
   if 'created' not in x:continue
   actual=sum(key.value*amp*x['basis'][i].reshape(-1,3) for i,(key,amp) in enumerate(x['created']))
   error=float(np.linalg.norm(actual-expected[n],axis=1).max()*x['scale'])
   projected=(expected[n].ravel()@x['basis'].T)@x['basis'];projection_error=float(np.linalg.norm(projected.reshape(-1,3)-expected[n],axis=1).max()*x['scale'])
   report['holdouts'].append({'action':action.name,'mesh':n,'frame':frame,'rest_error_m':error,'projection_error_m':projection_error})
report['paired_curve_actions']=paired
(O/'Report.json').write_text(json.dumps(report,indent=2))
print('HIP_HOLDOUT_MAX',max(x['rest_error_m'] for x in report['holdouts']),max(x['projection_error_m'] for x in report['holdouts']),flush=True)
if max(x['rest_error_m'] for x in report['holdouts'])>=.0005:
 s['zero_g_curve_pairs']=json.dumps(paired)
 bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(O/'REJECTED_Interpolation.blend'),compress=True)
 raise ValueError('Hold-out interpolation above 0.5mm; draft retained for diagnosis only')
report['paired_curve_actions']=paired
s['zero_g_curve_pairs']=json.dumps(paired);assign(actions[1]);s.frame_start=1;s.frame_end=961;s.frame_set(481)
for a in list(bpy.data.actions):
 if a not in kept:bpy.data.actions.remove(a)
bpy.data.orphans_purge(do_recursive=True);bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(output),compress=True)
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
report.update(output=str(output),output_sha256=hashlib.sha256(output.read_bytes()).hexdigest())
(O/'Report.json').write_text(json.dumps(report,indent=2));print('ZERO_G_SHARED_HIP_DONE',flush=True)
