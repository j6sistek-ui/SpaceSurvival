import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Same-mesh, same-camera controls isolate finger pose from skin weights."""
import bpy, json, math, hashlib
from pathlib import Path
from mathutils import Vector, Matrix
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025'
mesh=D/'Vexa_ContinuousDistal_Proof.blend';library=D/'GB_ShoulderResponse_ActionLibrary.blend'
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (mesh,library)}
O=R/'GBFingerShape';O.mkdir(exist_ok=True);report={'sources':hashes,'cases':[]}
for clip,frame in [('g1',881),('g1',220)]:
 for mode in ('animated','neutral_fingers'):
  bpy.ops.wm.open_mainfile(filepath=str(mesh),load_ui=False)
  s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
  for ob in s.objects:
   if ob.type=='MESH' and ob.data.shape_keys:
    ob.data.shape_keys.animation_data_clear()
    for key in ob.data.shape_keys.key_blocks:
     if key.name.startswith('REVIEW_'):key.value=0
  with bpy.data.libraries.load(str(library),link=False) as(a,b):b.actions=['A_F3_ShoulderResponse_'+clip]
  rig.animation_data_create();rig.animation_data.action=b.actions[0];rig.animation_data.action_slot=b.actions[0].slots[0]
  s.frame_set(frame);bpy.context.view_layer.update()
  bases={b.name:b.matrix_basis.copy() for b in rig.pose.bones};rig.animation_data_clear()
  for pb in rig.pose.bones:pb.matrix_basis=bases[pb.name]
  fingers=[b.name for b in rig.pose.bones if b.name.startswith(('thumb_','index_','middle_','ring_','pinky_'))]
  if mode=='neutral_fingers':
   for n in fingers:rig.pose.bones[n].matrix_basis=Matrix.Identity(4)
  bpy.context.view_layer.update()
  s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.55,.55,.55);s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD'
  s.world=bpy.data.worlds.new('FingerProbe');s.world.color=(.035,.045,.055)
  s.render.resolution_x=s.render.resolution_y=600;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
  bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.25
  for side in ('l','r'):
   hand=rig.pose.bones['hand_'+side];rest=rig.matrix_world@hand.bone.matrix_local;current=rig.matrix_world@hand.matrix
   rotation=current.to_quaternion()@rest.to_quaternion().inverted()
   pos=lambda n:rig.matrix_world@rig.data.bones[n].head_local
   along=(pos('middle_01_'+side)-pos('hand_'+side)).normalized()
   across=(pos('index_01_'+side)-pos('pinky_01_'+side)).normalized();normal=along.cross(across).normalized()
   center=current.translation+rotation@along*.075
   row={'clip':clip,'frame':frame,'mode':mode,'side':side,'finger_local_deg':{n:math.degrees(rig.pose.bones[n].matrix_basis.to_quaternion().angle) for n in fingers if n.endswith('_'+side)},'views':[]}
   for view,direction in [('palm',normal),('oblique',(-normal+across*.7).normalized())]:
    cam.location=center+rotation@direction*2;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();file=O/f'{clip}_{frame}_{side}_{mode}_{view}.png';s.render.filepath=str(file);bpy.ops.render.render(write_still=True);row['views'].append(str(file))
   report['cases'].append(row)
  print('FINGER_PROBE',clip,frame,mode,flush=True)
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
(O/'Report.json').write_text(json.dumps(report,indent=2));print('FINGER_PROBE_DONE',flush=True)
