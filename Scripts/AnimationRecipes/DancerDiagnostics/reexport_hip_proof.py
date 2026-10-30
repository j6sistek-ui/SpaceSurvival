import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

import bpy,json,numpy as np
from pathlib import Path
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
bpy.ops.wm.open_mainfile(filepath=str(D/'Roxie_HipCurve_Proof.blend'),load_ui=False)
s=bpy.context.scene;s.frame_start=1;s.frame_end=961;s.render.fps=60;bpy.context.preferences.filepaths.save_version=0
# The importer prunes sub-micron shapes. Remove those known negligible bases
# explicitly and their curves, so the exported morph/curve contract is exact.
audit=json.loads((R/'HipMorphPruning.json').read_text())
assert max(row['max_combined_rest_error_m'] for row in audit['meshes'])<.00001
pruned=[];expected=[]
for ob in s.objects:
 if ob.type!='MESH' or not ob.data.shape_keys:continue
 keys=ob.data.shape_keys;basis=np.array([tuple(v.co) for v in keys.key_blocks[0].data])
 for key in list(keys.key_blocks):
  if not key.name.startswith('REVIEW_'):continue
  delta=np.array([tuple(v.co) for v in key.data])-basis
  if float(np.linalg.norm(delta,axis=1).max()*max(ob.matrix_world.to_scale()))>1e-6:
   expected.append(key.name);continue
  path=key.path_from_id('value');pruned.append(key.name)
  if keys.animation_data and keys.animation_data.action:
   for layer in keys.animation_data.action.layers:
    for strip in layer.strips:
     for bag in strip.channelbags:
      for fc in list(bag.fcurves):
       if fc.data_path==path:bag.fcurves.remove(fc)
  ob.shape_key_remove(key)
(R/'HipExportContract.json').write_text(json.dumps({'expected_morphs':sorted(expected),'pruned':pruned,'pruning_audit':audit},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(D/'Roxie_HipCurve_Proof.blend'),compress=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.fbx(filepath=str(D/'Roxie_HipCurve_Proof.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,use_mesh_modifiers=False,mesh_smooth_type='FACE',bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z')
from mathutils import Matrix
for ob in s.objects:
 if ob.type=='ARMATURE':
  ob.animation_data_clear()
  for bone in ob.pose.bones:bone.matrix_basis=Matrix.Identity(4)
 if ob.type=='MESH' and ob.data.shape_keys:
  ob.data.shape_keys.animation_data_clear()
  for key in ob.data.shape_keys.key_blocks:
   if key.name.startswith('REVIEW_'):key.value=0
bpy.context.view_layer.update()
bpy.ops.export_scene.fbx(filepath=str(D/'Roxie_HipCurve_Rest.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,use_mesh_modifiers=False,mesh_smooth_type='FACE',bake_anim=False,axis_forward='-Y',axis_up='Z')
print('HIP_EXPORT_DONE',flush=True)
