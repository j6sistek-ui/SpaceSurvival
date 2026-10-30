import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Fresh-load five paired joint/morph actions and one rest mesh for native proof."""
import bpy,json,hashlib,math,numpy as np
from pathlib import Path
from mathutils import Matrix
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025';O=D/'ZeroGSharedProof';O.mkdir(exist_ok=True)
source=D/'Vexa_ZeroG_SharedHip_Proof.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False);s=bpy.context.scene;s.render.fps=60;rig=next(o for o in s.objects if o.type=='ARMATURE');rig.name='root.001'
pairs=json.loads(s['zero_g_curve_pairs']);assert len(pairs)==5 and all(n in bpy.data.actions for n in pairs)
meshes=[o for o in s.objects if o.type=='MESH' and not o.hide_render];report={'source_sha256':digest,'exports':[],'pruned':[],'expected_morphs':[],'original_bones':len(rig.data.bones),'status':'Private proof only'};assert len(rig.data.bones)==95
def curves(a):return [f for l in a.layers for st in l.strips for b in st.channelbags for f in b.fcurves]
for ob in meshes:
 if not ob.data.shape_keys:continue
 keys=ob.data.shape_keys;base=np.array([tuple(v.co) for v in keys.key_blocks[0].data]);small=[]
 for key in list(keys.key_blocks):
  if not key.name.startswith('REVIEW_ZG_'):continue
  delta=np.array([tuple(v.co) for v in key.data])-base;size=float(np.linalg.norm(delta,axis=1).max()*max(ob.matrix_world.to_scale()))
  if size<=1e-6:
   bound=max([abs(k.co.y) for pa in pairs.values() if ob.name in pa for fc in curves(bpy.data.actions[pa[ob.name]]) if fc.data_path==key.path_from_id('value') for k in fc.keyframe_points]+[0]);small.append((key,size*bound))
  else:report['expected_morphs'].append(key.name)
 assert sum(v for k,v in small)<=1e-5
 for key,bound in small:
  path=key.path_from_id('value')
  for pa in pairs.values():
   if ob.name not in pa:continue
   act=bpy.data.actions[pa[ob.name]]
   for layer in act.layers:
    for strip in layer.strips:
     for bag in strip.channelbags:
      for fc in list(bag.fcurves):
       if fc.data_path==path:bag.fcurves.remove(fc)
  report['pruned'].append({'key':key.name,'posed_displacement_bound_m':bound});ob.shape_key_remove(key)
bpy.ops.object.select_all(action='DESELECT')
for ob in meshes+[rig]:ob.hide_set(False);ob.select_set(True)
bpy.context.view_layer.objects.active=rig
options=dict(use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,use_mesh_modifiers=False,mesh_smooth_type='FACE',axis_forward='-Y',axis_up='Z')
for name,pa in pairs.items():
 action=bpy.data.actions[name];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];s.frame_start,s.frame_end=map(round,action.frame_range)
 for ob in meshes:
  if ob.name in pa:
   keys=ob.data.shape_keys;keys.animation_data_create();act=bpy.data.actions[pa[ob.name]];keys.animation_data.action=act;keys.animation_data.action_slot=act.slots[0]
 s.frame_set(1);path=O/(name.split('ZeroG_')[1]+'.fbx');assert not path.exists()
 bpy.ops.export_scene.fbx(filepath=str(path),bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,bake_anim_step=.5,**options)
 report['exports'].append({'action':name,'file':str(path),'duration':(s.frame_end-s.frame_start)/60,'sample_rate':120,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
rig.animation_data_clear()
for bone in rig.pose.bones:bone.matrix_basis=Matrix.Identity(4)
for ob in meshes:
 if ob.data.shape_keys:
  ob.data.shape_keys.animation_data_clear()
  for key in ob.data.shape_keys.key_blocks:
   if key.name.startswith('REVIEW_ZG_'):key.value=0
bpy.context.view_layer.update();rest=O/'Vexa_ZeroG_Rest.fbx';assert not rest.exists()
bpy.ops.export_scene.fbx(filepath=str(rest),bake_anim=False,**options)
report['rest']=str(rest);report['rest_sha256']=hashlib.sha256(rest.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(R/'ZeroGSharedHip/Export.json').write_text(json.dumps(report,indent=2));print('SHARED_ZERO_G_EXPORT_DONE',len(report['expected_morphs']),flush=True)
