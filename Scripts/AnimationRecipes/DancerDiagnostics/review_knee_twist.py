import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Compare supplied calf axial roll with a minimal-swing counterpart.
Joint positions and the approved hip correction stay fixed. No source writes.
"""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
P=R.parents[2];O=R/'KneeTwistReview';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'SourceAssets/DanceRefinement_20261025/Roxie_HipCurve_Proof.blend'),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('KneeTwist');s.world.color=(.035,.045,.055);s.render.resolution_x=700;s.render.resolution_y=700;s.render.resolution_percentage=100
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.6;report=[]
for t in (8,9.033333,9.5,10.066667):
 for mode in ('original','minimal_roll'):
  s.frame_set(round(t*60)+1);row={'seconds':t,'mode':mode,'roll':{}};positions={n:(rig.matrix_world@rig.pose.bones[n].matrix).translation.copy() for n in ('calf_l','calf_r','foot_l','foot_r')}
  for side in ('l','r'):
   b=rig.pose.bones['calf_'+side];foot=rig.pose.bones['foot_'+side];base=b.parent.matrix@b.parent.bone.matrix_local.inverted()@b.bone.matrix_local
   endpoint=b.bone.matrix_local.inverted()@foot.bone.matrix_local.translation
   current=(foot.matrix.translation-b.matrix.translation).normalized();neutral=(base.to_quaternion()@endpoint).normalized();q=neutral.rotation_difference(current)@base.to_quaternion();delta=q@b.matrix.to_quaternion().inverted()
   row['roll'][side]=math.degrees(delta.angle)
   if mode=='minimal_roll':b.matrix=Matrix.LocRotScale(b.matrix.translation,q,b.matrix.to_scale())
  bpy.context.view_layer.update();row['max_joint_shift_m']=max(((rig.matrix_world@rig.pose.bones[n].matrix).translation-p).length for n,p in positions.items());report.append(row)
  # Rendering re-evaluates keyed animation. Freeze evaluated geometry so this
  # diagnostic compares the assigned pose rather than reloading the source key.
  legs=bpy.data.objects['Roxie_Nude_Legs'];data=bpy.data.meshes.new_from_object(legs.evaluated_get(bpy.context.evaluated_depsgraph_get()));snapshot=bpy.data.objects.new('KneePoseSnapshot',data);s.collection.objects.link(snapshot);snapshot.matrix_world=legs.matrix_world.copy();legs.hide_render=True
  p=[(rig.matrix_world@rig.pose.bones[n].matrix).translation for n in ('thigh_l','calf_l','foot_l')];center=p[1];normal=(p[0]-p[1]).cross(p[2]-p[1]).normalized()
  for side in (-1,1):
   cam.location=center+normal*(3*side);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'{t:g}_{side}_{mode}.png');bpy.ops.render.render(write_still=True)
  legs.hide_render=False;bpy.data.objects.remove(snapshot,do_unlink=True);bpy.data.meshes.remove(data)
(O/'Report.json').write_text(json.dumps(report,indent=2));print('KNEE_TWIST_DONE',report,flush=True)
