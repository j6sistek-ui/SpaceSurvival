import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""PRIVATE diagnostic: align native knee hinge to source joint plane.

No source/production writes. This does not assert anatomical quality.
"""
import bpy, json, math
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion

P=R.parents[2]
O=R/'LegPlaneReview'; O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'SourceAssets/DanceRefinement_20261025/Roxie_HipCurve_Proof.blend'),load_ui=False)
s=bpy.context.scene; rig=next(o for o in s.objects if o.type=='ARMATURE')
s.render.engine='BLENDER_WORKBENCH'; s.display.shading.light='STUDIO'
s.display.shading.color_type='MATERIAL'; s.display.shading.show_cavity=True
s.display.shading.background_type='WORLD'; s.world=bpy.data.worlds.new('LegPlaneReview'); s.world.color=(.035,.045,.055)
s.render.resolution_x=800; s.render.resolution_y=800; s.render.resolution_percentage=100
bpy.ops.object.camera_add(); cam=bpy.context.object; s.camera=cam; cam.data.type='ORTHO'
ordered=sorted(rig.pose.bones,key=lambda b:len(b.parent_recursive))
rest={b.name:b.bone.matrix_local.copy() for b in ordered}
report=[]
for t in (8,9.033333,9.5,10.066667):
 for mode in ('source','native_plane'):
  s.frame_set(round(t*60)+1); bpy.context.view_layer.update()
  pose={b.name:b.matrix.copy() for b in ordered}; before={k:m.copy() for k,m in pose.items()}
  row={'seconds':t,'mode':mode,'legs':{}}
  if mode=='native_plane':
   for side in ('l','r'):
    th,ca,fo='thigh_'+side,'calf_'+side,'foot_'+side
    h,k,a=[pose[n].translation.copy() for n in (th,ca,fo)]
    upper=(k-h).normalized(); lower=(a-k).normalized()
    bend=upper.cross(lower)
    if bend.length<.05: raise ValueError('Near straight singularity requires temporal continuity')
    bend.normalize()
    base=pose[th]@rest[th].inverted()@rest[ca]
    axis=base.to_quaternion()@Vector((0,0,-1))
    axis=(axis-upper*axis.dot(upper)).normalized()
    angle=math.atan2(upper.dot(axis.cross(bend)),axis.dot(bend))
    q=Quaternion(upper,angle)
    calf_names={ca}|{b.name for b in rig.pose.bones[ca].children_recursive}
    for b in [rig.pose.bones[th]]+list(rig.pose.bones[th].children_recursive):
     if b.name in calf_names: continue
     m=pose[b.name]; pose[b.name]=Matrix.LocRotScale(h+q@(m.translation-h),q@m.to_quaternion(),m.to_scale())
    base=pose[th]@rest[th].inverted()@rest[ca]
    endpoint=rest[ca].inverted()@rest[fo].translation
    neutral=(base.to_quaternion()@endpoint).normalized()
    goal=(neutral.rotation_difference(lower)@base.to_quaternion()).normalized()
    cq=goal@pose[ca].to_quaternion().inverted()
    foot_names={fo}|{b.name for b in rig.pose.bones[fo].children_recursive}
    for n in calf_names:
     if n in foot_names: continue
     m=pose[n];pose[n]=Matrix.LocRotScale(k+cq@(m.translation-k),cq@m.to_quaternion(),m.to_scale())
    row['legs'][side]={'thigh_roll_degrees':math.degrees(angle),'flexion_degrees':math.degrees(upper.angle(lower))}
   for b in ordered:
    base=pose[b.parent.name]@rest[b.parent.name].inverted()@rest[b.name] if b.parent else rest[b.name]
    b.matrix_basis=base.inverted()@pose[b.name]
   bpy.context.view_layer.update()
  row['max_joint_shift_m']=max(((rig.matrix_world@rig.pose.bones[n].matrix).translation-(rig.matrix_world@before[n]).translation).length for n in ('thigh_l','calf_l','foot_l','thigh_r','calf_r','foot_r'))
  if row['max_joint_shift_m']>.0001:raise ValueError(f'Unintended joint displacement: {row}')
  snapshots=[]; originals=[]
  for ob in list(s.objects):
   if ob.type!='MESH' or ob.hide_render: continue
   data=bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
   snap=bpy.data.objects.new('Frozen_'+ob.name,data);s.collection.objects.link(snap);snap.matrix_world=ob.matrix_world.copy();snapshots.append((snap,data));originals.append(ob);ob.hide_render=True
  h,k,a=[(rig.matrix_world@before[n]).translation for n in ('thigh_l','calf_l','foot_l')]
  normal=(k-h).cross(a-k).normalized()
  for view,center,scale,direction in [('knee_outer',k,.72,normal),('knee_inner',k,.72,-normal),('whole_leg',(h+k)*.5,1.25,normal)]:
   cam.data.ortho_scale=scale;cam.location=center+direction*3;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'{t:g}_{view}_{mode}.png');bpy.ops.render.render(write_still=True)
  for ob in originals: ob.hide_render=False
  for ob,data in snapshots:bpy.data.objects.remove(ob,do_unlink=True);bpy.data.meshes.remove(data)
  report.append(row)
(O/'Report.json').write_text(json.dumps(report,indent=2));print('LEG_PLANE_REVIEW_DONE',json.dumps(report),flush=True)
