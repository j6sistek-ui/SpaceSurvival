import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Export private native proof, with explicit negligible morph pruning."""
import bpy,json,os,numpy as np
from pathlib import Path
from mathutils import Matrix
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
SHOULDER=os.environ.get('SS_REVIEW_SHOULDER')=='1'
stem='Vexa_Shoulder' if SHOULDER else 'Roxie_LegPlane'
contract='VexaShoulderExportContract.json' if SHOULDER else 'LegPlaneExportContract.json'
bpy.ops.wm.open_mainfile(filepath=str(D/(stem+'_Proof.blend')),load_ui=False)
s=bpy.context.scene;s.frame_start=1;s.frame_end=961;s.render.fps=60
expected=[];pruned=[];audit=[]
for ob in s.objects:
 if ob.type!='MESH' or not ob.data.shape_keys:continue
 keys=ob.data.shape_keys;basis=np.array([tuple(v.co) for v in keys.key_blocks[0].data]);small=[]
 for key in list(keys.key_blocks):
  if not key.name.startswith('REVIEW_'):continue
  delta=np.array([tuple(v.co) for v in key.data])-basis
  if float(np.linalg.norm(delta,axis=1).max()*max(ob.matrix_world.to_scale()))<=1e-6:small.append((key,delta))
  else:expected.append(key.name)
 worst=0.
 for f in range(1,962):
  s.frame_set(f)
  if small:worst=max(worst,float(np.linalg.norm(sum(key.value*delta for key,delta in small),axis=1).max()*max(ob.matrix_world.to_scale())))
 if worst>.00001:raise ValueError('Cumulative pruning exceeds 0.01mm')
 audit.append({'mesh':ob.name,'pruned':len(small),'max_combined_rest_error_m':worst})
 for key,_ in small:
  path=key.path_from_id('value');pruned.append(key.name)
  if keys.animation_data and keys.animation_data.action:
   for layer in keys.animation_data.action.layers:
    for strip in layer.strips:
     for bag in strip.channelbags:
      for fc in list(bag.fcurves):
       if fc.data_path==path:bag.fcurves.remove(fc)
  ob.shape_key_remove(key)
(R/contract).write_text(json.dumps({'expected_morphs':expected,'pruned':pruned,'audit':audit},indent=2))
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(D/(stem+'_Proof.blend')),compress=True)
bpy.ops.object.select_all(action='SELECT')
options=dict(use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,use_mesh_modifiers=False,mesh_smooth_type='FACE',axis_forward='-Y',axis_up='Z')
bpy.ops.export_scene.fbx(filepath=str(D/(stem+'_Proof.fbx')),bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,**options)
for ob in s.objects:
 if ob.type=='ARMATURE':
  ob.animation_data_clear()
  for bone in ob.pose.bones:bone.matrix_basis=Matrix.Identity(4)
 if ob.type=='MESH' and ob.data.shape_keys:
  ob.data.shape_keys.animation_data_clear()
  for key in ob.data.shape_keys.key_blocks:
   if key.name.startswith('REVIEW_'):key.value=0
bpy.context.view_layer.update()
bpy.ops.export_scene.fbx(filepath=str(D/(stem+'_Rest.fbx')),bake_anim=False,**options)
print('LEG_PLANE_EXPORT_DONE',len(expected),audit,flush=True)
