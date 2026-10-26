import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Export the approved-by-technical-gates private hip candidate for comparison."""
import bpy,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Matrix
O=R/'G2PosteriorHip';D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
source=D/'Vexa_G2_PosteriorHip_Candidate.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
gate=json.loads((O/'GeometryAudit.json').read_text());assert gate['ok'] and gate['candidate_sha256']==digest
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False);s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');rig.name='root.001'
meshes=[o for o in s.objects if o.type=='MESH' and not o.hide_render];pairs=json.loads(s['g2_hip_curve_pairs'])
report={'source':str(source),'source_sha256':digest,'expected_morphs':[],'pruned':[],'duration':(s.frame_end-s.frame_start)/60,'fps':120,'bones':len(rig.data.bones)}
for ob in meshes:
 if not ob.data.shape_keys:continue
 keys=ob.data.shape_keys;base=np.array([tuple(v.co) for v in keys.key_blocks[0].data]);curve=keys.animation_data.action if keys.animation_data else None
 fcurves=[fc for layer in curve.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves] if curve else []
 for key in list(keys.key_blocks):
  if not key.name.startswith('REVIEW_G2_'):continue
  size=float(np.linalg.norm(np.array([tuple(v.co) for v in key.data])-base,axis=1).max()*max(ob.matrix_world.to_scale()))
  if size<=1e-6:
   path=key.path_from_id('value');bound=size*max([abs(p.co.y) for fc in fcurves if fc.data_path==path for p in fc.keyframe_points]+[0])
   report['pruned'].append({'key':key.name,'bound_m':bound});key.value=0;key.mute=True
   for layer in curve.layers:
    for strip in layer.strips:
     for bag in strip.channelbags:
      for fc in list(bag.fcurves):
       if fc.data_path==path:bag.fcurves.remove(fc)
   ob.shape_key_remove(key)
  else:report['expected_morphs'].append(key.name)
assert sum(x['bound_m'] for x in report['pruned'])<1e-5
bpy.ops.object.select_all(action='DESELECT')
for ob in meshes+[rig]:ob.hide_set(False);ob.select_set(True)
bpy.context.view_layer.objects.active=rig
folder=D/'G2PosteriorHipProof';folder.mkdir(exist_ok=True)
options=dict(use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,use_mesh_modifiers=False,mesh_smooth_type='FACE',axis_forward='-Y',axis_up='Z')
path=folder/'G2_HipVolume.fbx';assert not path.exists()
s.frame_set(1);bpy.ops.export_scene.fbx(filepath=str(path),bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,bake_anim_step=.5,**options)
report.update(animation=str(path),animation_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
rig.animation_data_clear()
for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
for ob in meshes:
 if ob.data.shape_keys:
  ob.data.shape_keys.animation_data_clear()
  for key in ob.data.shape_keys.key_blocks:
   if key.name.startswith('REVIEW_G2_'):key.value=0
bpy.context.view_layer.update();path=folder/'Vexa_G2_Hip_Rest.fbx';assert not path.exists()
bpy.ops.export_scene.fbx(filepath=str(path),bake_anim=False,**options)
report.update(rest=str(path),rest_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(O/'Export.json').write_text(json.dumps(report,indent=2));print('G2_HIP_EXPORTED',len(report['expected_morphs']),flush=True)
