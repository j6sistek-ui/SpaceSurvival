import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Bake one isolated Vexa Spiral shoulder proof. Original sources untouched.

Clavicle participation is baked into a derivative action; localized volume
corrections become ordinary morph curves rather than an unexported modifier.
This changes hand positions and must not be applied to fixed-contact clips.
"""
import bpy, sys, math, json, numpy as np
from pathlib import Path
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025'
from shoulder_support import support_clavicles, shoulder_mask
O=R/'VexaShoulderProof';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(D/'Vexa_LegPlane_Proof.blend'),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
ordered=sorted(rig.pose.bones,key=lambda b:len(b.parent_recursive))
rest={b.name:(rig.matrix_world@b.bone.matrix_local).copy() for b in ordered}
desc={b.name:[b.name]+[c.name for c in b.children_recursive] for b in ordered};inv=rig.matrix_world.inverted()
source=rig.animation_data.action;end=round(source.frame_range[1]);previous={};buffers={b.name:{'q':[[],[],[],[]],'p':[[],[],[]]} for b in ordered};max_step=0.;rows=[]
for f in range(1,end+1):
 s.frame_set(f);pose={b.name:(rig.matrix_world@b.matrix).copy() for b in ordered}
 row={'frame':f,'support':support_clavicles(pose,rest,desc)};rows.append(row)
 local={n:inv@m for n,m in pose.items()}
 for b in ordered:
  base=local[b.parent.name]@b.parent.bone.matrix_local.inverted()@b.bone.matrix_local if b.parent else b.bone.matrix_local
  basis=base.inverted()@local[b.name];q=basis.to_quaternion().normalized()
  if b.name in previous:
   if q.dot(previous[b.name])<0:q.negate()
   if b.name.startswith(('clavicle_','upperarm_')):
    step=math.degrees(previous[b.name].rotation_difference(q).angle);max_step=max(max_step,step)
    if step>15:raise ValueError(f'Shoulder temporal jump {b.name} frame {f}: {step}')
  previous[b.name]=q.copy()
  for k in range(4):buffers[b.name]['q'][k].extend((f,q[k]))
  for k in range(3):buffers[b.name]['p'][k].extend((f,basis.translation[k]))
act=bpy.data.actions.new('A_F3_Vexa_Shoulder_ZeroG_02_Spiral');rig.animation_data.action=act
for b in ordered:
 b.rotation_mode='QUATERNION';b.keyframe_insert('rotation_quaternion',frame=1,group=b.name);b.keyframe_insert('location',frame=1,group=b.name)
for layer in act.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    name=fc.data_path.split('"')[1];kind='q' if fc.data_path.endswith('rotation_quaternion') else 'p'
    fc.keyframe_points.clear();fc.keyframe_points.add(end);fc.keyframe_points.foreach_set('co',buffers[name][kind][fc.array_index])
    for key in fc.keyframe_points:key.interpolation='LINEAR'
    fc.update()
torso=bpy.data.objects['Vexa_Nude_Torso'];arm=next(m for m in torso.modifiers if m.type=='ARMATURE');arm.use_deform_preserve_volume=False
mask,boundary=shoulder_mask(torso,[rest['upperarm_'+x].translation for x in ('l','r')])
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
 s.frame_set(math.floor(frame),subframe=frame%1);arm.use_deform_preserve_volume=False;bpy.context.view_layer.update();linear=positions()
 arm.use_deform_preserve_volume=True;bpy.context.view_layer.update();volume=positions();arm.use_deform_preserve_volume=False;bpy.context.view_layer.update()
 matrices=np.array([np.array((left@rig.pose.bones[name].matrix@rig.data.bones[name].matrix_local.inverted()@right).to_3x3()) for name in names])
 skin=np.einsum('vb,bij->vij',weights,matrices,optimize=True);valid=np.abs(np.linalg.det(skin))>.01
 invalid.append(int(np.count_nonzero((mask>0)&~valid)))
 if invalid[-1]:raise ValueError(f'Singular shoulder inverse skin at frame {frame}')
 delta=np.zeros_like(linear);delta[valid]=np.linalg.solve(skin[valid],((volume-linear)*mask[:,None])[valid,:,None])[...,0]
 return delta
frames=list(range(1,end+1,4));deltas=[]
for i,f in enumerate(frames):
 deltas.append(target(f).astype(np.float32))
 if i%60==0:print('SHOULDER_SAMPLE',i,len(frames),flush=True)
array=np.stack(deltas).reshape(len(frames),-1);u,singular,v=np.linalg.svd(array,full_matrices=False);rank=min(24,len(singular));basis=v[:rank];coeff=u[:,:rank]*singular[:rank]
compression=float(np.linalg.norm((coeff@basis-array).reshape(len(frames),-1,3),axis=2).max())*scale
keys=[];base=np.array([tuple(v.co) for v in torso.data.shape_keys.key_blocks[0].data])
for i in range(rank):
 amplitude=max(float(np.abs(coeff[:,i]).max()),1e-6);key=torso.shape_key_add(name=f'REVIEW_Vexa_Shoulder_{i:02}',from_mix=False);key.slider_min=-10;key.slider_max=10
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
s.frame_start=1;s.frame_end=end;s.frame_set(481);bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(D/'Vexa_Shoulder_Proof.blend'),compress=True)
report={'status':'PRIVATE VEXA-ONLY CANDIDATE; NOT ADOPTED OR ACCEPTED','action':act.name,'frames':end,'max_shoulder_local_step_deg':max_step,'morph_count':rank,'compression_error_m':compression,'checks':checks,'max_arm_translation_m':max(row['support'][side]['arm_translation_m'] for row in rows for side in ('l','r')),'boundary_vertices':len(boundary),'samples':rows}
(O/'Report.json').write_text(json.dumps(report,indent=2));print('VEXA_SHOULDER_BAKE_DONE',compression,max_step,flush=True)
