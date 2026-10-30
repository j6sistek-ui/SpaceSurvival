import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Portable, clip-driven localized hip volume correction; private proof only.

Sample DQ-vs-linear differences, inverse skin them, compress into morph bases,
and bake their coefficients. Original mesh, rig, clips and artwork are untouched.
"""
import bpy,json,math,os,numpy as np
from pathlib import Path
from mathutils import Vector
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025'
LEG_PLANE=os.environ.get('SS_REVIEW_LEG_PLANE')=='1'
CHARACTER=os.environ.get('SS_REVIEW_CHARACTER','Roxie')
assert CHARACTER in ('Roxie','Vexa','Jinx','Vesper')
assert CHARACTER=='Roxie' or LEG_PLANE, 'Other-character candidates must remain separate from the approved hip proof'
suffix='' if CHARACTER=='Roxie' else '_'+CHARACTER
O=R/(('LegPlaneHipProof' if LEG_PLANE else 'HipCurveProof')+suffix);O.mkdir(exist_ok=True)
stem=CHARACTER+('_LegPlane_Proof' if LEG_PLANE else '_HipCurve_Proof')
if CHARACTER!='Roxie':
 compatibility=json.loads((R/'DancerLegCompatibility.json').read_text())
 row=next(x for x in compatibility if x['character']==CHARACTER)
 assert row['same_bone_names'] and row['max_rest_matrix_difference']<1e-6
bpy.ops.wm.open_mainfile(filepath=str(P/'SourceAssets/CharacterWorkshop_20261021'/(CHARACTER+'_Character_Options.blend')),load_ui=False)
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
library='Roxie_LegPlane_Actions.blend' if LEG_PLANE else 'Refined_ActionLibrary.blend'
action_name='A_F3_LegPlane_ZeroG_02_Spiral' if LEG_PLANE else 'A_F3_Refined_ZeroG_02_Spiral'
with bpy.data.libraries.load(str(D/library),link=False) as (a,b):b.actions=[action_name]
act=b.actions[0];rig.animation_data_create();rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
s=bpy.context.scene;s.render.fps=60;end=round(act.frame_range[1]);s.frame_set(1)
meshes=[o for o in s.objects if o.name in tuple(CHARACTER+x for x in ('_Nude_Legs','_Bottom','_Nude_Torso'))]
assert len(meshes)==3
names=[b.name for b in rig.data.bones if b.use_deform];data={};report={'status':'PRIVATE PROOF; no native adoption','character':CHARACTER,'clip':act.name,'meshes':[],'samples':[]}
for o in meshes:
 arm=next(m for m in o.modifiers if m.type=='ARMATURE');arm.use_deform_preserve_volume=False
 weights=np.zeros((len(o.data.vertices),len(names)),np.float64)
 for v in o.data.vertices:
  for g in v.groups:
   n=o.vertex_groups[g.group].name
   if n in names:weights[v.index,names.index(n)]=g.weight
 sums=weights.sum(axis=1);weights/=np.maximum(sums[:,None],1e-12)
 coords=np.array([tuple(o.matrix_world@v.co) for v in o.data.vertices]);centers=np.array([tuple(rig.matrix_world@rig.data.bones['thigh_'+x].head_local) for x in ('l','r')])
 dist=np.linalg.norm(coords[:,None,:]-centers[None,:,:],axis=2).min(axis=1)
 mask=np.clip((.42-dist)/.22,0,1);mask=mask*mask*(3-2*mask)
 data[o.name]={'ob':o,'mod':arm,'weights':weights,'mask':mask,'deltas':[],'scale':max(o.matrix_world.to_scale())}
def eval_mesh(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());a=np.empty(len(e.data.vertices)*3);e.data.vertices.foreach_get('co',a);return a.reshape(-1,3)
def target_deltas(frame):
 s.frame_set(math.floor(frame),subframe=frame%1)
 for x in data.values():x['mod'].use_deform_preserve_volume=False
 bpy.context.view_layer.update();linear={n:eval_mesh(x['ob']) for n,x in data.items()}
 for x in data.values():x['mod'].use_deform_preserve_volume=True
 bpy.context.view_layer.update();volume={n:eval_mesh(x['ob']) for n,x in data.items()}
 for x in data.values():x['mod'].use_deform_preserve_volume=False
 bpy.context.view_layer.update();out={}
 for n,x in data.items():
  o=x['ob'];left=o.matrix_world.inverted()@rig.matrix_world;right=rig.matrix_world.inverted()@o.matrix_world
  mats=np.array([np.array((left@rig.pose.bones[b].matrix@rig.data.bones[b].matrix_local.inverted()@right).to_3x3()) for b in names])
  A=np.einsum('vb,bij->vij',x['weights'],mats,optimize=True);valid=np.abs(np.linalg.det(A))>.01
  delta=np.zeros_like(linear[n]);delta[valid]=np.linalg.solve(A[valid],((volume[n]-linear[n])*x['mask'][:,None])[valid,:,None])[...,0]
  out[n]=delta
 return out
frames=list(range(1,end+1,4))
if frames[-1]!=end:frames.append(end)
for index,f in enumerate(frames):
 for n,d in target_deltas(f).items():data[n]['deltas'].append(d.astype(np.float32))
 if index%40==0:print('HIP_SAMPLE',index,len(frames),flush=True)
for n,x in data.items():
 arr=np.stack(x['deltas']).reshape(len(frames),-1);U,S,V=np.linalg.svd(arr,full_matrices=False)
 rank=min(24,len(S));basis=V[:rank];coeff=U[:,:rank]*S[:rank]
 error=np.linalg.norm((coeff@basis-arr).reshape(len(frames),-1,3),axis=2).max()*x['scale']
 x.update(basis=basis,coeff=coeff);o=x['ob']
 if not o.data.shape_keys:o.shape_key_add(name='Basis')
 base=np.array([tuple(v.co) for v in o.data.shape_keys.key_blocks[0].data]);x['keys']=[]
 for i in range(rank):
  key=o.shape_key_add(name=f'REVIEW_{n}_Hip_{i:02}',from_mix=False);key.slider_min=-10;key.slider_max=10
  # Scale each basis so its coefficient is in [-1,1], safe for FBX curves.
  amplitude=max(float(np.abs(coeff[:,i]).max()),1e-6);key.data.foreach_set('co',(base+basis[i].reshape(-1,3)*amplitude).ravel());x['keys'].append((key,amplitude))
  for f,v in zip(frames,coeff[:,i]/amplitude):key.value=float(v);key.keyframe_insert('value',frame=f)
 for layer in o.data.shape_keys.animation_data.action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for pt in fc.keyframe_points:pt.interpolation='LINEAR'
 report['meshes'].append({'name':n,'morphs':rank,'compression_error_m':float(error),'samples':len(frames)})
print('HIP_BASES',report['meshes'],flush=True)
# Fresh coefficient interpolation at hold-out times, including the complained-of pose.
for t in (0,2.025,4.025,6.025,8,10.025,12.025,14.025,16):
 frame=1+t*60;s.frame_set(math.floor(frame),subframe=frame%1)
 for x in data.values():
  for k,amp in x['keys']:k.mute=True
 expected=target_deltas(frame)
 for x in data.values():
  for k,amp in x['keys']:k.mute=False
 s.frame_set(math.floor(frame),subframe=frame%1)
 for n,x in data.items():
  actual=sum(k.value*amp*x['basis'][i].reshape(-1,3) for i,(k,amp) in enumerate(x['keys']))
  error=np.linalg.norm(actual-expected[n],axis=1).max()*x['scale']
  report['samples'].append({'seconds':t,'mesh':n,'rest_error_m':float(error)})
# A compact rig/mesh/curve proof, without another packed texture library.
for o in meshes:o.data.materials.clear()
keep=set(meshes+[rig])
for o in list(s.objects):
 if o not in keep:bpy.data.objects.remove(o,do_unlink=True)
used_actions={act}|{o.data.shape_keys.animation_data.action for o in meshes if o.data.shape_keys and o.data.shape_keys.animation_data}
for a in list(bpy.data.actions):
 if a not in used_actions:bpy.data.actions.remove(a)
for mat in list(bpy.data.materials):bpy.data.materials.remove(mat,do_unlink=True)
for img in list(bpy.data.images):bpy.data.images.remove(img,do_unlink=True)
bpy.data.orphans_purge(do_recursive=True)
s.frame_start=1;s.frame_end=end;s.frame_set(481);bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(D/(stem+'.blend')),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for o in keep:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(D/(stem+'.fbx')),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,use_mesh_modifiers=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z')
(O/'Report.json').write_text(json.dumps(report,indent=2));print('HIP_CURVE_PROOF_DONE',flush=True)
