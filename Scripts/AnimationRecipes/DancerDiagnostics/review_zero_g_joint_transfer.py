import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Read-only five-segment transfer probe before any new native asset.

Compare the established chest-relative girdle and knee-plane technique on the
current repaired mesh. Disable all Spiral-only morph curves on every segment.
The rendered snapshots are diagnostic, not evidence of continuous quality.
"""
import bpy,json,math,hashlib,sys
from pathlib import Path
from mathutils import Vector
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025';O=R/'ZeroGJointTransferLocalBasis';O.mkdir(exist_ok=True)
sys.path.insert(0,str(R))
from coordinated_girdle import coordinate
from leg_plane import align_native_leg_plane
mesh=D/'Vexa_HandIsolation_Proof.blend';library=D/'Refined_ActionLibrary.blend';hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (mesh,library)}
bpy.ops.wm.open_mainfile(filepath=str(mesh),load_ui=False);s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
for ob in s.objects:
 if ob.type=='MESH' and ob.data.shape_keys:
  ob.data.shape_keys.animation_data_clear()
  for key in ob.data.shape_keys.key_blocks:
   if key.name.startswith('REVIEW_'):key.value=0
names=['A_F3_Refined_ZeroG_'+n for n in ('01_Drift','02_Spiral','03_Butterfly','04_Inversion','05_LateralArc')]
with bpy.data.libraries.load(str(library),link=False) as(a,b):b.actions=names
actions={a.name:a for a in b.actions};ordered=sorted(rig.pose.bones,key=lambda b:len(b.parent_recursive));rest={b.name:rig.matrix_world@b.bone.matrix_local for b in ordered};parent={b.name:b.parent.name if b.parent else None for b in ordered};desc={b.name:[b.name]+[x.name for x in b.children_recursive] for b in ordered};inv=rig.matrix_world.inverted()
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.55,.55,.55);s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('TransferReview');s.world.color=(.035,.045,.055)
s.render.resolution_x=s.render.resolution_y=640;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=2.2
rows=[];ends={}
for name,action in actions.items():
 rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];first,last=map(round,action.frame_range);state={};samples={};max_drift=0.;errors=[]
 want={first,first+round((last-first)*.25),first+round((last-first)*.5),first+round((last-first)*.75),last}
 for f in range(first,last+1):
  s.frame_set(f);p={b.name:(rig.matrix_world@b.matrix).copy() for b in ordered};before={n:p[n].copy() for n in ('thigh_l','calf_l','foot_l','thigh_r','calf_r','foot_r')}
  try:
   for side in ('l','r'):align_native_leg_plane(p,rest,parent,desc,side,state)
  except ValueError as exc:errors.append({'frame':f,'error':str(exc)});break
  coordinate(p,rest,parent,desc,True)
  max_drift=max(max_drift,max((p[n].translation-m.translation).length for n,m in before.items()))
  if f in want:samples[f]=p
 ends[name]={str(f):{n:list(p[n].translation) for n in ('pelvis','hand_l','hand_r','foot_l','foot_r')} for f,p in samples.items() if f in (first,last)}
 rig.animation_data.action=None
 for f,p in samples.items():
  local={n:inv@m for n,m in p.items()}
  for bone in ordered:
   base=local[bone.parent.name]@bone.parent.bone.matrix_local.inverted()@bone.bone.matrix_local if bone.parent else bone.bone.matrix_local
   bone.matrix_basis=base.inverted()@local[bone.name]
  bpy.context.view_layer.update()
  matrix_error=max(abs((rig.matrix_world@rig.pose.bones[n].matrix)[i][j]-m[i][j]) for n,m in p.items() for i in range(4) for j in range(4))
  assert matrix_error<1e-4,(name,f,matrix_error)
  chest=p['spine_05'].to_quaternion()@rest['spine_05'].to_quaternion().inverted();center=p['pelvis'].translation+chest@Vector((0,0,.15))
  for view,off in [('front',Vector((0,-3,.2))),('back',Vector((0,3,.2)))]:
   cam.location=center+chest@off;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();path=O/f'{name}_{f}_{view}.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
  rows.append({'action':name,'frame':f,'leg_center_drift_m':max_drift,'pose_matrix_error':matrix_error,'errors':errors})
 assert not errors,errors
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
(O/'Report.json').write_text(json.dumps({'sources':hashes,'rows':rows,'endpoints':ends},indent=2));print('ZERO_G_TRANSFER_DONE',flush=True)
