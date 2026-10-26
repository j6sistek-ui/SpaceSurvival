import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Isolated coupled scapula study; original hierarchy and arm motion preserved."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025';O=R/'VexaGirdleStudy';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(D/'Vexa_Underarm_Proof.blend'),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');torso=bpy.data.objects['Vexa_Nude_Torso'];original={b.name:np.array(b.matrix_local).copy() for b in rig.data.bones}
rig.animation_data.action=rig.animation_data.action.copy();rig.animation_data.action.name='A_F3_Vexa_GirdleStudy_Spiral'
original_action=rig.animation_data.action;inv=rig.matrix_world.inverted();rest={b.name:(rig.matrix_world@b.matrix_local).copy() for b in rig.data.bones}
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for side,sign in [('l',1),('r',-1)]:
 b=rig.data.edit_bones.new('REVIEW_scapula_'+side);shoulder=rest['upperarm_'+side].translation
 b.head=inv@(shoulder+Vector((-sign*.018,.035,-.015)));b.tail=inv@(shoulder+Vector((-sign*.075,.05,-.17)));b.parent=rig.data.edit_bones['spine_05'];b.use_connect=False;b.use_deform=True
bpy.ops.object.mode_set(mode='OBJECT')
assert all(np.max(np.abs(np.array(rig.data.bones[n].matrix_local)-m))<1e-6 for n,m in original.items())
helpers=['REVIEW_scapula_l','REVIEW_scapula_r'];weighted={};mask_all=np.zeros(len(torso.data.vertices));original_sums=[]
# Do not disturb modular neck/wrist/waist boundaries when redistributing weights.
edges={};adjacency=[set() for _ in torso.data.vertices]
for polygon in torso.data.polygons:
 for a,b in polygon.edge_keys:
  edge=tuple(sorted((a,b)));edges[edge]=edges.get(edge,0)+1
  adjacency[a].add(b);adjacency[b].add(a)
boundary={v for edge,count in edges.items() if count==1 for v in edge}
seam_safe=np.ones(len(torso.data.vertices));frontier=boundary.copy();visited=boundary.copy()
for factor in (0.,.25,.65):
 for index in frontier:seam_safe[index]=factor
 frontier={n for index in frontier for n in adjacency[index]}-visited;visited|=frontier
for v in torso.data.vertices:original_sums.append(sum(g.weight for g in v.groups if torso.vertex_groups[g.group].name in original))
for side,sign in [('l',1),('r',-1)]:
 name='REVIEW_scapula_'+side;group=torso.vertex_groups.new(name=name);head=rig.matrix_world@rig.data.bones[name].head_local;tail=rig.matrix_world@rig.data.bones[name].tail_local;center=(head+tail)*.5
 count=0;maximum=0
 for v in torso.data.vertices:
  point=torso.matrix_world@v.co;diff=np.array(point-center)/np.array((.105,.075,.15));rad=float(diff@diff)
  x=max(0.,min(1.,1-rad));fall=x*x*(3-2*x);posterior=max(0.,min(1.,(point.y-.005)/.045));factor=.68*fall*posterior*seam_safe[v.index]
  donors=[(torso.vertex_groups[g.group],g.weight) for g in v.groups if torso.vertex_groups[g.group].name in ('spine_03','spine_04','spine_05','clavicle_'+side)]
  transfer=sum(w for _,w in donors)*factor
  if transfer<1e-7:continue
  for donor,w in donors:donor.add([v.index],w*(1-factor),'REPLACE')
  group.add([v.index],transfer,'REPLACE');count+=1;maximum=max(maximum,transfer);mask_all[v.index]=max(mask_all[v.index],factor)
 weighted[side]={'vertices':count,'max_weight':maximum,'rest_head':list(head),'rest_tail':list(tail)}
weight_error=max(abs(sum(g.weight for g in v.groups if torso.vertex_groups[g.group].name in set(original)|set(helpers))-original_sums[v.index]) for v in torso.data.vertices)
assert weight_error<1e-6,weight_error
rest.update({n:(rig.matrix_world@rig.data.bones[n].matrix_local).copy() for n in helpers});rows=[]
for f in range(1,962):
 s.frame_set(f);bpy.context.view_layer.update();chest=rig.matrix_world@rig.pose.bones['spine_05'].matrix;chest_delta=chest@rest['spine_05'].inverted();cq=chest_delta.to_quaternion();row={'frame':f}
 for side in ('l','r'):
  name='REVIEW_scapula_'+side;pb=rig.pose.bones[name];upper='upperarm_'+side;clav='clavicle_'+side
  shoulder=(rig.matrix_world@rig.pose.bones[upper].matrix).translation;pivot=(rig.matrix_world@rig.pose.bones[clav].matrix).translation
  reference=(rest[upper].translation-rest[clav].translation).normalized();direction=cq.inverted()@(shoulder-pivot).normalized();swing=reference.rotation_difference(direction)
  # Anchored at the shoulder; blade rotates/slides with its clavicle over the chest.
  head=shoulder+cq@(rest[name].translation-rest[upper].translation);q=cq@swing@rest[name].to_quaternion()
  world=Matrix.LocRotScale(head,q,rest[name].to_scale());local=inv@world;basis=pb.parent.matrix@pb.parent.bone.matrix_local.inverted()@pb.bone.matrix_local;pb.matrix_basis=basis.inverted()@local;pb.rotation_mode='QUATERNION'
  if f>1 and pb.rotation_quaternion.dot(previous[name])<0:pb.rotation_quaternion.negate()
  if f==1:previous={} if side=='l' else previous
  previous[name]=pb.rotation_quaternion.copy();pb.keyframe_insert('location',frame=f,group=name);pb.keyframe_insert('rotation_quaternion',frame=f,group=name)
  row[side]={'rotation_deg':math.degrees(swing.angle),'head':list(head)}
 rows.append(row)
for layer in original_action.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    if any(n in fc.data_path for n in helpers):
     for key in fc.keyframe_points:key.interpolation='LINEAR'
s.frame_set(543);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(D/'Vexa_ShoulderGirdle_Study.blend'),compress=True)
report={'scope':'Private anatomy study, not native compatible adoption or quality acceptance','new_bones':helpers,'original_bones_preserved':len(original),'weights':weighted,'max_weight_sum_error':weight_error,'pose_samples':rows,'remaining':'Existing shoulder morphs require recalibration before any adoption; inspect blade sliding, front shoulder and full motion.'}
(O/'Report.json').write_text(json.dumps(report,indent=2));print('VEXA_GIRDLE_STUDY_SAVED',weighted,flush=True)
