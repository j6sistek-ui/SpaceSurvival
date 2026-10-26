import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Bake one isolated Spiral candidate; refuse large temporal jumps."""
import bpy, json, math, sys
from pathlib import Path
P=R.parents[2]; D=P/'SourceAssets/DanceRefinement_20261025'
from leg_plane import align_native_leg_plane
bpy.ops.wm.open_mainfile(filepath=str(D/'Roxie_HipCurve_Proof.blend'),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
ordered=sorted(rig.pose.bones,key=lambda b:len(b.parent_recursive))
rest={b.name:b.bone.matrix_local.copy() for b in ordered}
parent={b.name:b.parent.name if b.parent else None for b in ordered}
desc={b.name:[b.name]+[x.name for x in b.children_recursive] for b in ordered}
original=rig.animation_data.action;end=round(original.frame_range[1])
buffers={b.name:{'q':[[],[],[],[]],'p':[[],[],[]]} for b in ordered}
previous={};metrics=[];max_step=0.;max_drift=0.;continuity={}
for f in range(1,end+1):
 s.frame_set(f);pose={b.name:b.matrix.copy() for b in ordered}
 centers={n:(rig.matrix_world@pose[n]).translation.copy() for n in ('thigh_l','calf_l','foot_l','thigh_r','calf_r','foot_r')}
 try: row={'frame':f,'legs':{side:align_native_leg_plane(pose,rest,parent,desc,side,continuity) for side in ('l','r')}}
 except ValueError as exc:
  (R/'LegPlaneReview/BakeFailure.json').write_text(json.dumps({'frame':f,'error':str(exc),'previous_samples':metrics[-20:]},indent=2))
  raise ValueError(f'Frame {f}: {exc}') from exc
 max_drift=max(max_drift,max(((rig.matrix_world@pose[n]).translation-p).length for n,p in centers.items()))
 for b in ordered:
  n=b.name;par=parent[n];base=pose[par]@rest[par].inverted()@rest[n] if par else rest[n]
  basis=base.inverted()@pose[n];q=basis.to_quaternion().normalized()
  if n in previous:
   if q.dot(previous[n])<0:q.negate()
   if n in ('thigh_l','thigh_r','calf_l','calf_r'):
    step=math.degrees(previous[n].rotation_difference(q).angle);max_step=max(max_step,step)
    if step>25:raise ValueError(f'Unacceptable temporal jump {n} frame {f}: {step:.3f} degrees')
  previous[n]=q.copy()
  for k in range(4):buffers[n]['q'][k].extend((f,q[k]))
  for k in range(3):buffers[n]['p'][k].extend((f,basis.translation[k]))
 metrics.append(row)
 if f%240==0:print('LEG_PLANE_SAMPLE',f,flush=True)
if max_drift>.0001:raise ValueError(f'Joint center drift {max_drift}')
act=bpy.data.actions.new('A_F3_LegPlane_ZeroG_02_Spiral');act.use_fake_user=True
rig.animation_data.action=act
for b in ordered:
 b.rotation_mode='QUATERNION';b.keyframe_insert('rotation_quaternion',frame=1,group=b.name);b.keyframe_insert('location',frame=1,group=b.name)
for layer in act.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    n=fc.data_path.split('"')[1];kind='q' if fc.data_path.endswith('rotation_quaternion') else 'p'
    fc.keyframe_points.clear();fc.keyframe_points.add(end);fc.keyframe_points.foreach_set('co',buffers[n][kind][fc.array_index])
    for pt in fc.keyframe_points:pt.interpolation='LINEAR'
    fc.update()
# Save an action-only library. Never rebind old hip correctives to a new pose.
bpy.data.libraries.write(str(D/'Roxie_LegPlane_Actions.blend'),{act},compress=True)
report={'status':'EXPERIMENTAL; source and game untouched','frames':end,'max_joint_center_drift_m':max_drift,'max_leg_local_rotation_step_deg':max_step,'samples':metrics}
(R/'LegPlaneReview/BakeReport.json').write_text(json.dumps(report,indent=2));print('LEG_PLANE_BAKE_DONE',max_drift,max_step,flush=True)
