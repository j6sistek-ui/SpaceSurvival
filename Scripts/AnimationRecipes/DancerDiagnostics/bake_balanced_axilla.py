import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Bake a local bilateral axilla trial; preserve the balanced rig, neck and source."""
import bpy,sys,math,json,hashlib,numpy as np
from pathlib import Path
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025'
sys.path.insert(0,str(R))
from shoulder_support import shoulder_mask
O=R/'VexaAxillaProof';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(D/'Vexa_ShoulderBalanced_Proof.blend'),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');act=rig.animation_data.action;end=round(act.frame_range[1])
torso=bpy.data.objects['Vexa_Nude_Torso'];arm=next(m for m in torso.modifiers if m.type=='ARMATURE');arm.use_deform_preserve_volume=False
source_path=D/'Vexa_ShoulderBalanced_Proof.blend';before=hashlib.sha256(source_path.read_bytes()).hexdigest()
mask,boundary=shoulder_mask(torso,[rig.matrix_world@rig.data.bones['upperarm_'+side].head_local for side in ('l','r')])
positions=np.array([list(torso.matrix_world@v.co) for v in torso.data.vertices])
def step(a,b,value):
 t=np.clip((value-a)/(b-a),0,1);return t*t*(3-2*t)
mask*=step(.09,.14,np.abs(positions[:,0]))*(1-step(1.44,1.49,positions[:,2]))*step(1.15,1.24,positions[:,2])
mask_group=torso.vertex_groups.new(name='REVIEW_BilateralAxillaOnly')
for i,w in enumerate(mask):
 if w>0:mask_group.add([i],float(w),'REPLACE')
corrective=torso.modifiers.new('REVIEW_BilateralAxillaCorrective','CORRECTIVE_SMOOTH');corrective.vertex_group=mask_group.name;corrective.factor=.5;corrective.iterations=8;corrective.rest_source='ORCO';corrective.use_pin_boundary=True
names=[b.name for b in rig.data.bones if b.use_deform];weights=np.zeros((len(torso.data.vertices),len(names)))
for v in torso.data.vertices:
 for group in v.groups:
  name=torso.vertex_groups[group.group].name
  if name in names:weights[v.index,names.index(name)]=group.weight
weights/=np.maximum(weights.sum(axis=1)[:,None],1e-12)
left=torso.matrix_world.inverted()@rig.matrix_world;right=rig.matrix_world.inverted()@torso.matrix_world
scale=max(torso.matrix_world.to_scale());invalid=[]
def positions():
 evaluated=torso.evaluated_get(bpy.context.evaluated_depsgraph_get());coords=np.empty(len(evaluated.data.vertices)*3);evaluated.data.vertices.foreach_get('co',coords);return coords.reshape(-1,3)
def target(frame):
 s.frame_set(math.floor(frame),subframe=frame%1);corrective.show_viewport=False;bpy.context.view_layer.update();linear=positions()
 corrective.show_viewport=True;bpy.context.view_layer.update();volume=positions();corrective.show_viewport=False;bpy.context.view_layer.update()
 matrices=np.array([np.array((left@rig.pose.bones[name].matrix@rig.data.bones[name].matrix_local.inverted()@right).to_3x3()) for name in names])
 skin=np.einsum('vb,bij->vij',weights,matrices,optimize=True);valid=np.abs(np.linalg.det(skin))>.01
 invalid.append(int(np.count_nonzero((mask>0)&~valid)))
 if invalid[-1]:raise ValueError(f'Singular shoulder inverse skin at frame {frame}')
 delta=np.zeros_like(linear);delta[valid]=np.linalg.solve(skin[valid],(volume-linear)[valid,:,None])[...,0]
 return delta
frames=list(range(1,end+1,4));deltas=[]
for i,f in enumerate(frames):
 deltas.append(target(f).astype(np.float32))
 if i%60==0:print('UNDERARM_SAMPLE',i,len(frames),flush=True)
array=np.stack(deltas).reshape(len(frames),-1);u,singular,v=np.linalg.svd(array,full_matrices=False);rank=min(24,len(singular));basis=v[:rank];coeff=u[:,:rank]*singular[:rank]
compression=float(np.linalg.norm((coeff@basis-array).reshape(len(frames),-1,3),axis=2).max())*scale
keys=[];base=np.array([tuple(v.co) for v in torso.data.shape_keys.key_blocks[0].data])
for i in range(rank):
 amplitude=max(float(np.abs(coeff[:,i]).max()),1e-6);key=torso.shape_key_add(name=f'REVIEW_Vexa_Axilla_{i:02}',from_mix=False);key.slider_min=-10;key.slider_max=10
 key.data.foreach_set('co',(base+basis[i].reshape(-1,3)*amplitude).ravel());keys.append((key,amplitude))
 for f,value in zip(frames,coeff[:,i]/amplitude):key.value=float(value);key.keyframe_insert('value',frame=f)
for layer in torso.data.shape_keys.animation_data.action.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for key in fc.keyframe_points:key.interpolation='LINEAR'
checks=[]
for sec in (0,4.025,8,9.033333,9.5,12.2,14.025,16):
 for key,amplitude in keys:key.mute=True
 expected=target(1+sec*60)
 for key,amplitude in keys:key.mute=False
 s.frame_set(math.floor(1+sec*60),subframe=(1+sec*60)%1);bpy.context.view_layer.update()
 actual=sum(key.value*amplitude*basis[i].reshape(-1,3) for i,(key,amplitude) in enumerate(keys))
 checks.append({'seconds':sec,'max_rest_target_error_m':float(np.linalg.norm(actual-expected,axis=1).max())*scale,'boundary_delta_m':float(np.linalg.norm(actual[list(boundary)],axis=1).max())*scale})
used={act}|{ob.data.shape_keys.animation_data.action for ob in s.objects if ob.type=='MESH' and ob.data.shape_keys and ob.data.shape_keys.animation_data}
for action in list(bpy.data.actions):
 if action not in used:bpy.data.actions.remove(action)
assert compression<.0002,compression
assert max(x['max_rest_target_error_m'] for x in checks)<.0005,checks
assert max(x['boundary_delta_m'] for x in checks)<1e-7,checks
assert all((key.data[int(i)].co-key.relative_key.data[int(i)].co).length<1e-6 for key,amplitude in keys for i in np.where(mask==0)[0])
assert hashlib.sha256(source_path.read_bytes()).hexdigest()==before
s.frame_start=1;s.frame_end=end;s.frame_set(481);bpy.context.preferences.filepaths.save_version=0
torso.modifiers.remove(corrective);torso.vertex_groups.remove(mask_group)
bpy.ops.wm.save_as_mainfile(filepath=str(D/'Vexa_AxillaLocal_Proof.blend'),compress=True)
report={'source_sha256':before,'status':'PRIVATE VEXA BILATERAL AXILLA CANDIDATE; NOT ADOPTED OR ACCEPTED','action':act.name,'frames':end,'morph_count':rank,'compression_error_m':compression,'checks':checks,'boundary_vertices':len(boundary),'unchanged_region':'outside local bilateral axilla mask; original action, neck, central chest and bones unchanged'}
(O/'Report.json').write_text(json.dumps(report,indent=2));print('VEXA_UNDERARM_BAKE_DONE',compression,flush=True)
