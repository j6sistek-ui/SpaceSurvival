import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Isolate inherited clavicle/neck motion at the rejected pose; no persistent edits."""
import bpy,json,math
from pathlib import Path
from mathutils import Matrix,Vector
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025';O=R/'VexaGirdleAuthority';O.mkdir(exist_ok=True)
report=[]
for mode in ('baseline','neutral_clavicle','neutral_neck','neutral_both'):
 bpy.ops.wm.open_mainfile(filepath=str(P/'SourceAssets/CharacterWorkshop_20261021/Vexa_Character_Options.blend'),load_ui=False)
 s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');rig.animation_data_clear()
 with bpy.data.libraries.load(str(D/'Vexa_LegPlane_Proof.blend'),link=False) as (a,b):b.actions=['A_F3_LegPlane_ZeroG_02_Spiral']
 rig.animation_data_create();rig.animation_data.action=b.actions[0];rig.animation_data.action_slot=b.actions[0].slots[0]
 s.frame_set(733);bpy.context.view_layer.update()
 rest={b.name:b.matrix_local.copy() for b in rig.data.bones};pose={pb.name:pb.matrix.copy() for pb in rig.pose.bones};original={n:m.copy() for n,m in pose.items()};ordered=sorted(rig.pose.bones,key=lambda b:len(b.parent_recursive))
 rig.animation_data_clear()  # Rendering evaluates actions again; hold the sampled pose explicitly.
 row={'mode':mode,'bones':{}}
 for n in ('spine_03','spine_04','spine_05','neck_01','neck_02','head','clavicle_l','clavicle_r','upperarm_l','upperarm_r'):
  pb=rig.pose.bones[n];base=original[pb.parent.name]@rest[pb.parent.name].inverted()@rest[n] if pb.parent else rest[n]
  d=base.inverted()@original[n]
  row['bones'][n]={'local_angle_deg':math.degrees(d.to_quaternion().angle),'local_euler_deg':[math.degrees(v) for v in d.to_euler()],'local_translation':list(d.translation)}
 if mode in ('neutral_clavicle','neutral_both'):
  for side in ('l','r'):
   n='clavicle_'+side;pb=rig.pose.bones[n];new=pose[pb.parent.name]@rest[pb.parent.name].inverted()@rest[n]
   # Neutral clavicle only; retain arm world orientation and shift its root as one chain.
   upper='upperarm_'+side;shoulder=(new@rest[n].inverted()@rest[upper]).translation;shift=shoulder-pose[upper].translation;pose[n]=new
   for b in [rig.pose.bones[upper]]+list(rig.pose.bones[upper].children_recursive):pose[b.name].translation+=shift
 if mode in ('neutral_neck','neutral_both'):
  for n in ('neck_01','neck_02','head'):
   pb=rig.pose.bones[n];new=pose[pb.parent.name]@rest[pb.parent.name].inverted()@rest[n];delta=new@pose[n].inverted()
   for b in [pb]+list(pb.children_recursive):pose[b.name]=delta@pose[b.name]
 for pb in ordered:
  base=pose[pb.parent.name]@rest[pb.parent.name].inverted()@rest[pb.name] if pb.parent else rest[pb.name]
  pb.matrix_basis=base.inverted()@pose[pb.name]
 bpy.context.view_layer.update()
 for o in s.objects:
  if o.type=='MESH' and 'hair' in o.name.lower():o.hide_render=True
 s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.65,.65,.65);s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('Authority');s.world.color=(.035,.045,.055)
 s.render.resolution_x=800;s.render.resolution_y=800;s.render.resolution_percentage=100
 bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.9
 world={n:rig.matrix_world@m for n,m in pose.items()};chest=world['spine_05'].to_quaternion()@(rig.matrix_world@rest['spine_05']).to_quaternion().inverted();center=(world['upperarm_l'].translation+world['upperarm_r'].translation)*.5
 for view,offset in [('front',Vector((0,-3,.15))),('back',Vector((0,3,.15)))]:
  cam.location=center+chest@offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'{mode}_{view}.png');bpy.ops.render.render(write_still=True)
  row['render_pose_matrix_error']=max(abs(rig.pose.bones[n].matrix[i][j]-m[i][j]) for n,m in pose.items() for i in range(4) for j in range(4))
  assert row['render_pose_matrix_error']<.001,row['render_pose_matrix_error']
 report.append(row)
(O/'Report.json').write_text(json.dumps(report,indent=2));print('GIRDLE_AUTHORITY_DONE',flush=True)
