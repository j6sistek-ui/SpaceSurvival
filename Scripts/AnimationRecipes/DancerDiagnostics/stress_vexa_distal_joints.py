import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Dedicated Vexa wrist/ankle/forearm deformation probes, no source writes.

Probe angles select inspection poses, not approved anatomical limits. This is
one mesh/rig in isolation, not evidence for another animation or character.
"""
import bpy,json,hashlib,math,sys
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
P=R.parents[2]
proof=P/'SourceAssets/DanceRefinement_20261025/Vexa_AxillaLocal_Proof.blend'
before=hashlib.sha256(proof.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(proof),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
rig.animation_data_clear()
for ob in s.objects:
 if ob.type=='MESH' and ob.data.shape_keys:
  ob.data.shape_keys.animation_data_clear()
  for key in ob.data.shape_keys.key_blocks:
   if key.name.startswith('REVIEW_'):key.value=0
for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
rest={b.name:b.matrix.copy() for b in rig.pose.bones}
out=R/'VexaJointStress';out.mkdir(exist_ok=True)
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO'
s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.55,.55,.55)
s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD'
s.world=bpy.data.worlds.new('DistalStress');s.world.color=(.035,.045,.055)
s.render.resolution_x=640;s.render.resolution_y=640;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO'
report={'proof_sha256':before,'scope':'ONE VEXA PROOF, isolated diagnostic poses; not anatomical, animation, pole-contact or multi-character acceptance','cases':[]}
cases=[]
for side in ('l','r'):
 hand='hand_'+side;foot='foot_'+side;forearm='lowerarm_'+side
 across=(rest['index_01_'+side].translation-rest['pinky_01_'+side].translation).normalized()
 along=(rest['middle_01_'+side].translation-rest[hand].translation).normalized()
 normal=along.cross(across).normalized()
 footforward=(rest['ball_'+side].translation-rest[foot].translation).normalized()
 lateral=(rest['foot_l'].translation-rest['foot_r'].translation).normalized()
 for bone,axis,label,angles in [(hand,across,'flex',(-30,0,30)),(hand,normal,'deviation',(-15,15)),(foot,lateral,'pitch',(-30,0,30)),(foot,footforward,'roll',(-15,15)),(forearm,(rest[hand].translation-rest[forearm].translation).normalized(),'twist',(-45,45))]:
  for angle in angles:cases.append((bone,axis,label,angle,hand if bone==forearm else bone))
for bone,axis,label,angle,focus in cases:
 for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update()
 origin=rest[bone].translation
 delta=Matrix.Translation(origin)@Quaternion(axis,math.radians(angle)).to_matrix().to_4x4()@Matrix.Translation(-origin)
 expected=delta@rest[bone]
 rig.pose.bones[bone].matrix=expected
 bpy.context.view_layer.update()
 matrix_error=max(abs(rig.pose.bones[bone].matrix[r][c]-expected[r][c]) for r in range(4) for c in range(4))
 assert matrix_error<1e-4,(bone,label,angle,matrix_error)
 pb=rig.pose.bones[focus];center=rig.matrix_world@pb.head
 orientation=(rig.matrix_world@rest[pb.parent.name]).to_quaternion()
 cam.data.ortho_scale=.42 if focus.startswith('hand') else .5
 row={'bone':bone,'test':label,'degrees':angle,'axis_armature_space':tuple(axis),'applied_transform_max_error':matrix_error,'views':[]}
 for view,direction in [('front',Vector((0,-2,.8))),('side',Vector((2,0,.8)))]:
  cam.location=center+orientation@direction;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
  file=out/f'{bone}_{label}_{angle:+d}_{view}.png'
  if '--scan-only' not in sys.argv:
   s.render.filepath=str(file);bpy.ops.render.render(write_still=True);row['views'].append(str(file))
 report['cases'].append(row)
assert len(report['cases'])==24
assert hashlib.sha256(proof.read_bytes()).hexdigest()==before
(out/('Transforms.json' if '--scan-only' in sys.argv else 'Report.json')).write_text(json.dumps(report,indent=2))
print('DISTAL_STRESS_DONE',len(report['cases']),flush=True)
