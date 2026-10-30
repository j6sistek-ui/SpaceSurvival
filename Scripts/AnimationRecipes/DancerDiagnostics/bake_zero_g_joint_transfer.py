import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Five private zero-G actions with the verified girdle/knee-plane response.

Keep every unrelated local key exact, bake only twelve local bones, and measure
all ordered endpoint poses. This does not provide morphs or contact constraints.
"""
import bpy, hashlib, json, math, sys
from pathlib import Path
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
O=R/'ZeroGJointBake';O.mkdir(exist_ok=True)
sys.path.insert(0,str(R))
from coordinated_girdle import coordinate
from leg_plane import align_native_leg_plane
src=D/'Refined_ActionLibrary.blend';out=D/'ZeroG_Coordinated_ActionLibrary.blend'
assert not out.exists()
digest=hashlib.sha256(src.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
s=bpy.context.scene;s.render.fps=60;rig=next(o for o in s.objects if o.type=='ARMATURE')
ordered=sorted(rig.pose.bones,key=lambda b:len(b.parent_recursive))
rest={b.name:rig.matrix_world@b.bone.matrix_local for b in ordered}
parent={b.name:b.parent.name if b.parent else None for b in ordered}
desc={b.name:[b.name]+[x.name for x in b.children_recursive] for b in ordered};inv=rig.matrix_world.inverted()
changed={'clavicle_l','clavicle_r','upperarm_l','upperarm_r','neck_01','neck_02'}|{n+'_'+side for n in ('thigh','calf','foot') for side in ('l','r')}
def curves(a):return [f for l in a.layers for st in l.strips for b in st.channelbags for f in b.fcurves]
def snapshot(a):return {(f.data_path,f.array_index):[(tuple(k.co),k.interpolation,tuple(k.handle_left),tuple(k.handle_right)) for k in f.keyframe_points] for f in curves(a) if f.data_path.split('"')[1] not in changed}
def deg(a,b):
 q=a.rotation_difference(b);return math.degrees(min(q.angle,2*math.pi-q.angle))
report={'source_sha256':digest,'scope':'Private actions only; original/approved files unchanged, no anatomy/contact acceptance','clips':[]};new_actions=[];ends={}
for suffix in ('01_Drift','02_Spiral','03_Butterfly','04_Inversion','05_LateralArc'):
 old=bpy.data.actions['A_F3_Refined_ZeroG_'+suffix];rig.animation_data.action=old;rig.animation_data.action_slot=old.slots[0]
 first,last=map(round,old.frame_range);state={};buffers={n:{'rotation_quaternion':[[],[],[],[]],'location':[[],[],[]]} for n in changed};previous={};expected={};max_drift=0.;max_step={n:0. for n in changed}
 for frame in range(first,last+1):
  s.frame_set(frame);pose={b.name:(rig.matrix_world@b.matrix).copy() for b in ordered};centers={n:pose[n].translation.copy() for n in changed if n.startswith(('thigh','calf','foot'))}
  for side in ('l','r'):align_native_leg_plane(pose,rest,parent,desc,side,state)
  coordinate(pose,rest,parent,desc,True)
  max_drift=max(max_drift,*[(pose[n].translation-v).length for n,v in centers.items()]);local={n:inv@m for n,m in pose.items()}
  if frame in (first,first+1,last-1,last) or frame%60==1:expected[frame]=pose
  for n in changed:
   b=rig.pose.bones[n];base=local[parent[n]]@b.parent.bone.matrix_local.inverted()@b.bone.matrix_local if b.parent else b.bone.matrix_local
   basis=base.inverted()@local[n];q=basis.to_quaternion().normalized()
   if n in previous:
    if q.dot(previous[n])<0:q.negate()
    max_step[n]=max(max_step[n],deg(q,previous[n]))
   previous[n]=q.copy()
   for i in range(4):buffers[n]['rotation_quaternion'][i].extend((frame,q[i]))
   for i in range(3):buffers[n]['location'][i].extend((frame,basis.translation[i]))
 new=old.copy();new.name='A_F3_Coordinated_ZeroG_'+suffix;new.use_fake_user=True
 for fc in curves(new):
  n=fc.data_path.split('"')[1];kind=fc.data_path.rsplit('.',1)[-1]
  if n not in changed or kind not in buffers[n]:continue
  fc.keyframe_points.clear();fc.keyframe_points.add(last-first+1);fc.keyframe_points.foreach_set('co',buffers[n][kind][fc.array_index])
  for key in fc.keyframe_points:key.interpolation='LINEAR'
  fc.update()
 assert snapshot(new)==snapshot(old)
 rig.animation_data.action=new;rig.animation_data.action_slot=new.slots[0];error=0.;ep={}
 for f,p in expected.items():
  s.frame_set(f)
  error=max(error,*[abs((rig.matrix_world@rig.pose.bones[n].matrix)[i][j]-m[i][j]) for n,m in p.items() for i in range(4) for j in range(4)])
  if f in (first,first+1,last-1,last):ep[f]={n:(rig.matrix_world@rig.pose.bones[n].matrix).copy() for n in rest}
 assert error<1e-4,(suffix,error)
 ends[suffix]=(first,last,ep);new_actions.append(new)
 row={'action':new.name,'frames':last-first+1,'matrix_error':error,'leg_centers_drift_m':max_drift,'max_local_step_deg':max_step,'unrelated_keys_exact':True};report['clips'].append(row);print('ZERO_G_JOINT',json.dumps(row),flush=True)
joins=[]
for a,(af,al,ae) in ends.items():
 for b,(bf,bl,be) in ends.items():
  pos=max((ae[al][n].translation-be[bf][n].translation).length for n in rest)
  rot=max(deg(ae[al][n].to_quaternion(),be[bf][n].to_quaternion()) for n in rest)
  vel=max(((ae[al][n].translation-ae[al-1][n].translation)-(be[bf+1][n].translation-be[bf][n].translation)).length*60 for n in rest)
  joins.append({'from':a,'to':b,'position_m':pos,'rotation_deg':rot,'velocity_discontinuity_m_s':vel})
report['ordered_joins']=joins
for ob in list(bpy.data.objects):
 if ob!=rig:bpy.data.objects.remove(ob,do_unlink=True)
for a in list(bpy.data.actions):
 if a not in new_actions:bpy.data.actions.remove(a)
for im in list(bpy.data.images):bpy.data.images.remove(im)
bpy.data.orphans_purge(do_recursive=True)
s.frame_set(1);bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
report.update(output=str(out),output_sha256=hashlib.sha256(out.read_bytes()).hexdigest())
(O/'Report.json').write_text(json.dumps(report,indent=2));print('ZERO_G_JOINT_BAKE_DONE',flush=True)
