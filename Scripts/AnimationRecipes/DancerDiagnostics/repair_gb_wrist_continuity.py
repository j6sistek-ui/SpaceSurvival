import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Repair discontinuities in already-bounded wrist tracks; preserve other keys.

The original limit chose a shortest quaternion branch at pi and jumped between
opposite 40-degree limits. Work inside that small neutral-centered rotation ball
where the logarithm is unique. Local Gaussian averaging is activated only near
high-speed events. Convex averages stay inside the original bound. This is a
contact-free candidate, not an anatomical or pole-grip solution.
"""
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Quaternion,Vector
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
source=D/'Refined_ActionLibrary.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
output=D/'GB_WristContinuous_ActionLibrary.blend';assert not output.exists()
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')

def curves(action):
 return [fc for layer in action.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]

def signature(action):
 return {(fc.data_path,fc.array_index):[(tuple(k.co),k.interpolation,tuple(k.handle_left),tuple(k.handle_right)) for k in fc.keyframe_points] for fc in curves(action) if not (fc.data_path.startswith('pose.bones["hand_') and fc.data_path.endswith('rotation_quaternion'))}

def angle(a,b):
 value=math.degrees(a.rotation_difference(b).angle)
 return min(value,360-value)

report={'source_sha256':digest,'scope':'Only local hand_l/hand_r quaternion curves near high-speed events; other action keys unchanged. Original 40-degree diagnostic bound retained, not declared an anatomical limit. No pole constraint.','clips':[]}
keep=set()
for clip in ('g1','g2','b1','b2'):
 original=bpy.data.actions['A_F3_Refined_'+clip];before=signature(original)
 action=original.copy();action.name='A_F3_WristContinuous_'+clip;action.use_fake_user=True;keep.add(action)
 rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
 start,end=map(round,action.frame_range);frames=list(range(start,end+1));sample={side:[] for side in ('l','r')}
 for f in frames:
  s.frame_set(f)
  for side in sample:
   q=rig.pose.bones['hand_'+side].matrix_basis.to_quaternion().normalized()
   if q.w<0:q.negate()
   sample[side].append(q.copy())
 row={'clip':clip,'frames':len(frames),'sides':[]}
 for side,track in sample.items():
  vectors=[q.axis*q.angle if q.angle>1e-7 else Vector() for q in track]
  steps=[angle(a,b) for a,b in zip(track,track[1:])]
  mask=[0.]*len(track);events=[i+1 for i,v in enumerate(steps) if v>5]
  radius=32;sigma=8.
  for event in events:
   for i in range(max(0,event-radius),min(len(track),event+radius+1)):
    t=abs(i-event)/radius;mask[i]=max(mask[i],.5+.5*math.cos(math.pi*t))
  result=[]
  for i,q in enumerate(track):
   if mask[i]<1e-10:result.append(q.copy());continue
   avg=Vector();total=0.
   for offset in range(-32,33):
    j=max(0,min(len(track)-1,i+offset));weight=math.exp(-.5*(offset/sigma)**2)
    avg+=vectors[j]*weight;total+=weight
   value=vectors[i].lerp(avg/total,mask[i]);a=value.length
   result.append(Quaternion(value/a,a) if a>1e-7 else Quaternion())
  # Re-evaluate blend-window boundary velocities; increase the smooth region
  # locally if a high-speed segment remains. Do not broaden acceptance gates.
  for iteration in range(6):
   bad=[i+1 for i,(a,b) in enumerate(zip(result,result[1:])) if angle(a,b)>5]
   if not bad:break
   for event in bad:
    for i in range(max(0,event-radius),min(len(track),event+radius+1)):
     t=abs(i-event)/radius;mask[i]=max(mask[i],.5+.5*math.cos(math.pi*t))
   result=[]
   for i,q in enumerate(track):
    avg=Vector();total=0.
    for offset in range(-32,33):
     j=max(0,min(len(track)-1,i+offset));weight=math.exp(-.5*(offset/sigma)**2)
     avg+=vectors[j]*weight;total+=weight
    value=vectors[i].lerp(avg/total,mask[i]);a=value.length
    result.append(Quaternion(value/a,a) if a>1e-7 else Quaternion())
  maxstep=max(angle(a,b) for a,b in zip(result,result[1:]));assert maxstep<=5.01,(clip,side,maxstep)
  maxangle=max(math.degrees(q.angle) for q in result);assert maxangle<=40.01,(clip,side,maxangle)
  for fc in curves(action):
   if fc.data_path==f'pose.bones["hand_{side}"].rotation_quaternion':
    fc.keyframe_points.clear();fc.keyframe_points.add(len(frames))
    values=[x for f,q in zip(frames,result) for x in (f,q[fc.array_index])]
    fc.keyframe_points.foreach_set('co',values)
    for key in fc.keyframe_points:key.interpolation='LINEAR'
    fc.update()
  changed=[angle(a,b) for a,b in zip(track,result)]
  row['sides'].append({'side':side,'events':len(events),'max_step_before_deg':max(steps),'max_step_after_deg':maxstep,'max_rest_angle_after_deg':maxangle,'changed_frames_over_0_01deg':sum(v>.01 for v in changed),'max_rotation_change_deg':max(changed)})
 assert before==signature(action),clip+' non-wrist keys changed'
 report['clips'].append(row);print('WRIST_CONTINUITY',json.dumps(row),flush=True)
for action in list(bpy.data.actions):
 if action not in keep:bpy.data.actions.remove(action)
rig.animation_data.action=bpy.data.actions['A_F3_WristContinuous_g1'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(output),compress=True)
report['output_sha256']=hashlib.sha256(output.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(R/'VexaDistalRepair/GBWristContinuity.json').write_text(json.dumps(report,indent=2))
print('WRIST_CONTINUITY_SAVED',report['output_sha256'],flush=True)
