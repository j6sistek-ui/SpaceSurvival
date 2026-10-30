import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Private bounded rephrasing of the inspected G2 right-arm excursion.

This deliberately changes choreography within frames59-109 only. It is not a
general anatomical repair or pole solver. Preserve all other keys exactly.
"""
import bpy,json,math,hashlib,sys
from pathlib import Path
from mathutils import Matrix,Vector
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025';O=R/'GBFastPassage'
sys.path.insert(0,str(R));from coordinated_girdle import coordinate
source=D/'GB_ShoulderResponse_ActionLibrary.blend';output=D/'G2_ArmPassage_ActionLibrary.blend';assert not output.exists()
digest=hashlib.sha256(source.read_bytes()).hexdigest();assert digest=='4d72c70e5410b55847c81943c4ab7c6a3e4d2baa5b151611673dbec6216f4679'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False);s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
old=bpy.data.actions['A_F3_ShoulderResponse_g2'];rig.animation_data.action=old;rig.animation_data.action_slot=old.slots[0]
ordered=sorted(rig.pose.bones,key=lambda b:len(b.parent_recursive));rest={b.name:rig.matrix_world@b.bone.matrix_local for b in ordered};parent={b.name:b.parent.name if b.parent else None for b in ordered};desc={b.name:[b.name]+[x.name for x in b.children_recursive] for b in ordered};inv=rig.matrix_world.inverted()
names={n for n in rest if n.endswith('_r') and n.startswith(('upperarm','lowerarm'))};changed=names|{'clavicle_r'};a,z=59,109
def curves(action):return [fc for l in action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
def snap(action):return {(fc.data_path,fc.array_index):[(tuple(k.co),k.interpolation,tuple(k.handle_left),tuple(k.handle_right)) for k in fc.keyframe_points] for fc in curves(action)}
original=snap(old);local={};world={}
for f in range(a,z+1):
 s.frame_set(f);local[f]={b.name:b.matrix_basis.copy() for b in ordered};world[f]={b.name:(rig.matrix_world@b.matrix).copy() for b in ordered}
buffers={};expected={};deltas=[]
smooth=lambda t:t*t*(3-2*t)
for f in range(a,z+1):
 t=(f-a)/(z-a);blend=smooth(min(1,(f-a)/8))*smooth(min(1,(z-f)/8));pose={}
 for b in ordered:
  n=b.name;m=local[f][n].copy()
  if n in names:
   qa=local[a][n].to_quaternion();qz=local[z][n].to_quaternion();target=qa.slerp(qz,smooth(t));q=m.to_quaternion().slerp(target,blend);m=Matrix.LocRotScale(m.translation,q,m.to_scale())
  base=pose[parent[n]]@rest[parent[n]].inverted()@rest[n] if parent[n] else rest[n];pose[n]=base@m
 coordinate(pose,rest,parent,desc,False)
 loc={n:inv@m for n,m in pose.items()};row={}
 for n in changed:
  b=rig.pose.bones[n];base=loc[parent[n]]@b.parent.bone.matrix_local.inverted()@b.bone.matrix_local if parent[n] else b.bone.matrix_local;m=base.inverted()@loc[n];row[n]=m
 buffers[f]=row;expected[f]=pose
 deltas.append({'frame':f,'hand_shift_cm':100*(pose['hand_r'].translation-world[f]['hand_r'].translation).length})
new=old.copy();new.name='A_F3_ArmPassage_g2';new.use_fake_user=True
for fc in curves(new):
 n=fc.data_path.split('"')[1];kind=fc.data_path.rsplit('.',1)[-1]
 if n not in changed or kind not in ('rotation_quaternion','location'):continue
 previous=None
 for k in fc.keyframe_points:
  f=round(k.co.x)
  if a<f<z:
   m=buffers[f][n];value=m.to_quaternion().normalized() if kind=='rotation_quaternion' else m.translation
   # Align quaternion sign with original local rotation to retain neighboring
   # key hemisphere. Endpoints and all exterior keys are untouched.
   if kind=='rotation_quaternion' and value.dot(local[f][n].to_quaternion())<0:value.negate()
   k.co.y=value[fc.array_index];k.interpolation='LINEAR'
 fc.update()
current=snap(new)
for key,vals in original.items():
 n=key[0].split('"')[1]
 for oldkey,newkey in zip(vals,current[key]):
  if n not in changed:assert oldkey==newkey,(key,oldkey,newkey)
  elif not a<oldkey[0][0]<z:
   # update() recomputes unused automatic Bezier handles by tiny roundoff.
   # LINEAR evaluation uses only the unchanged coordinate/interpolation.
   assert oldkey[:2]==newkey[:2] and oldkey[1]=='LINEAR',(key,oldkey,newkey)
rig.animation_data.action=new;rig.animation_data.action_slot=new.slots[0];max_step={n:0 for n in changed};prev={};error=0
for f in range(a-1,z+2):
 s.frame_set(f)
 for n in changed:
  q=rig.pose.bones[n].matrix_basis.to_quaternion()
  if n in prev:
   angle=math.degrees(q.rotation_difference(prev[n]).angle);max_step[n]=max(max_step[n],min(angle,360-angle))
  prev[n]=q.copy()
 if a<f<z:
  for n in changed:error=max(error,max(abs((rig.matrix_world@rig.pose.bones[n].matrix)[i][j]-expected[f][n][i][j]) for i in range(4) for j in range(4)))
assert error<1e-5,error
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(output),compress=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
report={'source_sha256':digest,'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'window':[a,z],'changed_bones':sorted(changed),'max_step_deg':max_step,'matrix_error':error,'other_keys_exact':True,'max_hand_shift_cm':max(r['hand_shift_cm'] for r in deltas),'acceptance':'Private candidate; actual poses, contact and native continuity require review'}
(O/'Repair.json').write_text(json.dumps(report,indent=2));print('ARM_PASSAGE',json.dumps(report),flush=True)
