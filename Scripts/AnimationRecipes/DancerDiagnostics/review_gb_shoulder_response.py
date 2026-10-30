import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Matched G1 shoulder controls using the preserved successful coordination.

Never save or alter the source. Spiral time-indexed morphs are deliberately off.
"""
import bpy, json, sys, hashlib, math
from pathlib import Path
from mathutils import Matrix, Vector
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025'
sys.path.insert(0,str(R))
from coordinated_girdle import coordinate
O=R/'GBShoulderResponse';O.mkdir(exist_ok=True)
sources=[D/'Vexa_ContinuousDistal_Proof.blend',D/'GB_WristContinuous_ActionLibrary.blend']
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
report={'sources':hashes,'scope':'Matched private shoulder diagnosis. No pole contact or production adoption.','cases':[]}
for clip,frame in [('g1',881),('g1',84),('g2',1)]:
 for mode in ('source','coordinated'):
  bpy.ops.wm.open_mainfile(filepath=str(sources[0]),load_ui=False)
  s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
  rig.animation_data_clear()
  for ob in s.objects:
   if ob.type=='MESH' and ob.data.shape_keys:
    ob.data.shape_keys.animation_data_clear()
    for key in ob.data.shape_keys.key_blocks:
     if key.name.startswith('REVIEW_'):key.value=0
  with bpy.data.libraries.load(str(sources[1]),link=False) as (a,b):b.actions=['A_F3_WristContinuous_'+clip]
  rig.animation_data_create();rig.animation_data.action=b.actions[0];rig.animation_data.action_slot=b.actions[0].slots[0]
  s.frame_set(frame);bpy.context.view_layer.update()
  ordered=sorted(rig.pose.bones,key=lambda b:len(b.parent_recursive))
  rest={b.name:rig.matrix_world@b.bone.matrix_local for b in ordered}
  pose={b.name:(rig.matrix_world@b.matrix).copy() for b in ordered};original={n:m.copy() for n,m in pose.items()}
  parent={b.name:b.parent.name if b.parent else None for b in ordered};desc={b.name:[b.name]+[x.name for x in b.children_recursive] for b in ordered}
  rig.animation_data_clear()
  row={'clip':clip,'frame':frame,'mode':mode,'views':[]}
  if mode=='coordinated':row['coordination']=coordinate(pose,rest,parent,desc,True)
  inv=rig.matrix_world.inverted();local={n:inv@m for n,m in pose.items()}
  for pb in ordered:
   base=local[pb.parent.name]@pb.parent.bone.matrix_local.inverted()@pb.bone.matrix_local if pb.parent else pb.bone.matrix_local
   pb.matrix_basis=base.inverted()@local[pb.name]
  bpy.context.view_layer.update()
  row['arm_orientations_unchanged']=max(math.degrees(original[n].to_quaternion().rotation_difference(pose[n].to_quaternion()).angle) for n in pose if n.startswith(('upperarm','lowerarm','hand')))<.1
  row['max_arm_shift_cm']=max((pose[n].translation-original[n].translation).length*100 for n in pose if n.startswith(('upperarm','lowerarm','hand')))
  s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.55,.55,.55);s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD'
  s.world=bpy.data.worlds.new('GBShoulder');s.world.color=(.035,.045,.055)
  s.render.resolution_x=900;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
  bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.05
  # Camera is identical for both controls; preserve the original chest frame.
  chest=original['spine_05'].to_quaternion()@rest['spine_05'].to_quaternion().inverted()
  center=(original['upperarm_l'].translation+original['upperarm_r'].translation)*.5
  for view,off in [('front',Vector((0,-3,.2))),('back',Vector((0,3,.2))),('quarter',Vector((-2,-2,.2)))]:
   cam.location=center+chest@off;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
   file=O/f'{clip}_{frame}_{mode}_{view}.png';s.render.filepath=str(file);bpy.ops.render.render(write_still=True)
   error=max(abs((rig.matrix_world@rig.pose.bones[n].matrix)[i][j]-pose[n][i][j]) for n in pose for i in range(4) for j in range(4));assert error<.0001,error
   row['views'].append(str(file))
  report['cases'].append(row)
  print('SHOULDER_CASE',clip,frame,mode,flush=True)
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
(O/'Report.json').write_text(json.dumps(report,indent=2));print('GB_SHOULDER_RESPONSE_DONE',flush=True)
