import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Carry the approved G1 clavicle/neck response across private G/B derivatives.

Only six local bone channels change. Hand world paths move, so this is not a
pole-contact solution. Preserve immutable source actions and the Spiral proof.
"""
import bpy,json,hashlib,math,sys
from pathlib import Path
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025'
sys.path.insert(0,str(R));from coordinated_girdle import coordinate
source=D/'GB_WristContinuous_ActionLibrary.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
output=D/'GB_ShoulderResponse_ActionLibrary.blend';assert not output.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');s.render.fps=60
ordered=sorted(rig.pose.bones,key=lambda b:len(b.parent_recursive));rest={b.name:rig.matrix_world@b.bone.matrix_local for b in ordered}
parent={b.name:b.parent.name if b.parent else None for b in ordered};desc={b.name:[b.name]+[x.name for x in b.children_recursive] for b in ordered};inv=rig.matrix_world.inverted()
changed={'clavicle_l','clavicle_r','upperarm_l','upperarm_r','neck_01','neck_02'}
def curves(action):
 return [fc for layer in action.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
def snapshot(action,exclude):
 return {(fc.data_path,fc.array_index):[(tuple(k.co),k.interpolation,tuple(k.handle_left),tuple(k.handle_right)) for k in fc.keyframe_points] for fc in curves(action) if fc.data_path.split('"')[1] not in exclude}
report={'source_sha256':digest,'scope':'Private six-bone shoulder response derived from the owner-approved G1 frame881 control; no fixed contact or full-motion acceptance','clips':[]}
for clip in ('g1','g2','b1','b2'):
 old=bpy.data.actions['A_F3_WristContinuous_'+clip];rig.animation_data.action=old;rig.animation_data.action_slot=old.slots[0]
 first,last=map(round,old.frame_range);buffers={n:{'rotation_quaternion':[[],[],[],[]],'location':[[],[],[]]} for n in changed};previous={};max_step=0.;max_shift=0.;max_head=0.;expected={};rows=[]
 for f in range(first,last+1):
  s.frame_set(f);p={b.name:(rig.matrix_world@b.matrix).copy() for b in ordered}
  change=coordinate(p,rest,parent,desc,True);max_shift=max(max_shift,*(change[x]['arm_root_shift_m'] for x in ('l','r')));max_head=max(max_head,change['neck']['head_translation_m'])
  local={n:inv@m for n,m in p.items()}
  if f in {first,last,84,220,543,881} or f%120==0:expected[f]={n:m.copy() for n,m in p.items()}
  for n in changed:
   pb=rig.pose.bones[n];base=local[parent[n]]@pb.parent.bone.matrix_local.inverted()@pb.bone.matrix_local if parent[n] else pb.bone.matrix_local
   basis=base.inverted()@local[n];q=basis.to_quaternion().normalized()
   if n in previous:
    if q.dot(previous[n])<0:q.negate()
    a=math.degrees(q.rotation_difference(previous[n]).angle);max_step=max(max_step,min(a,360-a))
   previous[n]=q.copy()
   for i in range(4):buffers[n]['rotation_quaternion'][i].extend((f,q[i]))
   for i in range(3):buffers[n]['location'][i].extend((f,basis.translation[i]))
 new=old.copy();new.name='A_F3_ShoulderResponse_'+clip;new.use_fake_user=True
 for fc in curves(new):
  n=fc.data_path.split('"')[1];kind=fc.data_path.rsplit('.',1)[-1]
  if n not in changed or kind not in buffers[n]:continue
  fc.keyframe_points.clear();fc.keyframe_points.add(last-first+1);fc.keyframe_points.foreach_set('co',buffers[n][kind][fc.array_index])
  for key in fc.keyframe_points:key.interpolation='LINEAR'
  fc.update()
 assert snapshot(old,changed)==snapshot(new,changed),'Unrelated keys changed'
 rig.animation_data.action=new;rig.animation_data.action_slot=new.slots[0]
 max_matrix=0.;wrist_step=0.;previous={}
 for f in range(first,last+1):
  s.frame_set(f)
  if f in expected:
   for n,m in expected[f].items():max_matrix=max(max_matrix,max(abs((rig.matrix_world@rig.pose.bones[n].matrix)[i][j]-m[i][j]) for i in range(4) for j in range(4)))
  for side in ('l','r'):
   q=rig.pose.bones['hand_'+side].matrix_basis.to_quaternion()
   if side in previous:
    a=math.degrees(q.rotation_difference(previous[side]).angle);wrist_step=max(wrist_step,min(a,360-a))
   previous[side]=q.copy()
 assert max_matrix<.0001,(clip,max_matrix)
 assert wrist_step<5.01,(clip,wrist_step)
 row={'clip':clip,'frames':last-first+1,'max_six_bone_step_deg':max_step,'max_wrist_step_deg':wrist_step,'max_arm_shift_cm':max_shift*100,'max_head_shift_cm':max_head*100,'pose_matrix_error':max_matrix,'other_keys_identical':True,'sampled_frames':list(expected)}
 report['clips'].append(row);print('SHOULDER_BAKE',json.dumps(row),flush=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
s.frame_set(881);s.frame_start=1;s.frame_end=1012;bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(output),compress=True)
report['output']=str(output);report['output_sha256']=hashlib.sha256(output.read_bytes()).hexdigest()
(R/'GBShoulderResponse/BakeReport.json').write_text(json.dumps(report,indent=2));print('GB_SHOULDER_BAKE_DONE',flush=True)
