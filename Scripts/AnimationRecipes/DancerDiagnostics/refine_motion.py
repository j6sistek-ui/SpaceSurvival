import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Reversible source-first cleanup. Writes derivative actions only, never source art."""
import bpy,json,math,sys,os
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=R.parents[2];OUT=P/'SourceAssets/DanceRefinement_20261025'
OUT.mkdir(exist_ok=True);(OUT/'FBX').mkdir(exist_ok=True)
FPS=60
REVIEW_CALF_ROLL=os.environ.get('SS_REVIEW_CALF_ROLL')=='1'
from joint_cleanup import remove_calf_axial_roll
def matrix(p,q):return Matrix.LocRotScale(p,q,Vector((1,1,1)))
def rotate(p,n,q):
 pivot=p[n].translation
 for b in DESC[n]:p[b]=matrix(pivot+q@(p[b].translation-pivot),q@p[b].to_quaternion())
def soft_limit(x,limit,width=math.radians(2)):
 # C1 transition prevents hard-limit chatter; exact source below transition.
 if x<=limit-width:return x
 if x>=limit+width:return limit
 t=(x-limit+width)/(2*width)
 return (limit-width)+width*(2*t-t*t)
def clean_arm(p,side):
 chest=p['spine_05'].to_quaternion()@REST['spine_05'].to_quaternion().inverted()
 forward=chest@Vector((0,-1,0));up=chest@Vector((0,0,1))
 upper,lower,hand=[x+'_'+side for x in ('upperarm','lowerarm','hand')]
 v=(p[lower].translation-p[upper].translation).normalized()
 rear=math.asin(max(-1,min(1,-v.dot(forward))))
 # Smoothly permit the owner's 10 degree overhead allowance.
 lift=max(0,min(1,v.dot(up)/.35));lift=lift*lift*(3-2*lift)
 limit=math.radians(10)*lift
 allowed=soft_limit(rear,limit)
 correction=rear-allowed
 if correction>1e-7:
  tangent=v-forward*v.dot(forward)
  if tangent.length<1e-5:tangent=up.copy()
  tangent.normalize();goal=tangent*math.cos(allowed)-forward*math.sin(allowed)
  rotate(p,upper,v.rotation_difference(goal))
 # On raised arms, turn the entire arm about its humerus axis only when the
 # forearm points behind the chest. Elbow flex and native hinge are preserved.
 v=(p[lower].translation-p[upper].translation).normalized()
 fore=(p[hand].translation-p[lower].translation).normalized()
 turn=0.0
 if v.dot(up)>.2 and fore.dot(forward)<0:
  a=fore-v*fore.dot(v);b=forward-v*forward.dot(v)
  if a.length>.02 and b.length>.02:
   a.normalize();b.normalize()
   signed=math.atan2(v.dot(a.cross(b)),a.dot(b))
   # Bring the forearm toward the front, with a gradual activation on ascent.
   weight=max(0,min(1,(v.dot(up)-.2)/.3));weight=weight*weight*(3-2*weight)
   # Report this unresolved orientation demand; do not introduce a new axial
   # twist to satisfy it. A large automatic roll repeats the rejected defect.
   turn=signed*weight
 return math.degrees(correction),math.degrees(abs(turn))
def floating_arms(p,phase,segment):
 # Authored, slow arm phrasing over the preserved acrobatic torso/leg motion.
 # All five segments share the same endpoint and zero endpoint velocity.
 chest=p['spine_05'].to_quaternion()@REST['spine_05'].to_quaternion().inverted()
 forward=chest@Vector((0,-1,0));up=chest@Vector((0,0,1));right=chest@Vector((1,0,0))
 envelope=math.sin(math.pi*phase)**2
 values={'01_Drift':(30,-20,20,-20),'02_Spiral':(85,40,10,-10),
         '03_Butterfly':(75,40,-25,-40),'04_Inversion':(65,50,35,15),
         '05_LateralArc':(60,-15,-10,20)}[segment]
 for side,base_elevation,base_flex,de,df in [('l',-20,55,values[0],values[2]),('r',15,75,values[1],values[3])]:
  upper,lower,hand=[x+'_'+side for x in ('upperarm','lowerarm','hand')]
  elev=math.radians(base_elevation+de*envelope);flex=math.radians(base_flex+df*envelope)
  u=((right if side=='l' else -right)*math.cos(elev)+up*math.sin(elev)+forward*.34).normalized()
  phrase=forward*.65+up*.8
  bend=(phrase-u*phrase.dot(u)).normalized();v=u*math.cos(flex)+bend*math.sin(flex)
  a0,b0,c0=[REST[n].translation for n in (upper,lower,hand)]
  h0=(b0-a0).cross(c0-b0).normalized();h=u.cross(v).normalized()
  def orientation(old_dir,new_dir,n):
   x0=old_dir.normalized();x=new_dir.normalized()
   return (Matrix((x,h.cross(x),h)).transposed()@Matrix((x0,h0.cross(x0),h0)).transposed().inverted()).to_quaternion()@REST[n].to_quaternion()
  a=p[upper].translation.copy();b=a+u*(b0-a0).length;c=b+v*(c0-b0).length
  p[upper]=matrix(a,orientation(b0-a0,u,upper));p[lower]=matrix(b,orientation(c0-b0,v,lower))
  for n in ORDER:
   if n in (upper,lower):continue
   if n in DESC[upper]:p[n]=p[PARENT[n]]@REL[n]
  p[hand].translation=c
  # Subtle relaxed hands retain native wrist alignment instead of forced grips.
  for finger in ('index','middle','ring','pinky'):
   for digit in (1,2,3):
    n=f'{finger}_{digit:02}_{side}'
    if n in p:rotate(p,n,Quaternion(h,math.radians(8+digit*3)))
def get_actions():
 for key in ('g1','g2','b1','b2'):
  bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=FPS
  bpy.ops.import_scene.fbx(filepath=str(R/'SourceBaseline'/f'A_F3_Baseline_{key}_Source_Anim.fbx'))
  rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
  yield key,rig,rig.animation_data.action
 bpy.ops.wm.open_mainfile(filepath=str(P/'SourceAssets/ZeroGChoreography_20261025/ZeroG_and_Contact_ActionLibrary.blend'),load_ui=False)
 rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
 for key in ('01_Drift','02_Spiral','03_Butterfly','04_Inversion','05_LateralArc'):
  action=bpy.data.actions['A_F3_ZeroG_'+key];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
  yield 'ZeroG_'+key,rig,action
all_poses={};metrics=[];target_rig=None
for key,rig,action in get_actions():
 scene=bpy.context.scene;scene.render.fps=FPS
 REST={b.name:matrix((rig.matrix_world@b.matrix_local).translation,(rig.matrix_world@b.matrix_local).to_quaternion()) for b in rig.data.bones}
 ORDER=list(REST);PARENT={b.name:b.parent.name if b.parent else None for b in rig.data.bones}
 REL={n:REST[PARENT[n]].inverted()@REST[n] if PARENT[n] else REST[n] for n in ORDER}
 DESC={n:[n]+[b.name for b in rig.data.bones[n].children_recursive] for n in ORDER}
 local=[];root=[]
 for f in range(round(action.frame_range[0]),round(action.frame_range[1])+1):
  scene.frame_set(f);m={n:rig.matrix_world@rig.pose.bones[n].matrix for n in ORDER}
  local.append({n:(m[PARENT[n]].to_quaternion().inverted()@m[n].to_quaternion() if PARENT[n] else m[n].to_quaternion()) for n in ORDER})
  root.append(m['pelvis'].translation.copy())
 poses=[];changes=[]
 for i in range(len(local)):
  # Filter local rotations, not global limbs, to preserve lengths and hierarchy.
  p={};root_pos=Vector();total=0
  neighborhood=[(max(0,min(len(local)-1,i+j)),math.exp(-.5*(j/2.0)**2)) for j in range(-5,6)]
  for ix,w in neighborhood:root_pos+=root[ix]*w;total+=w
  root_pos/=total
  for n in ORDER:
   anchor=local[i][n];qv=[0.0]*4
   for ix,w in neighborhood:
    q=local[ix][n];sign=1 if anchor.dot(q)>=0 else -1
    for k in range(4):qv[k]+=q[k]*w*sign
   q=Quaternion(qv).normalized();par=PARENT[n]
   base=p[par]@REL[n] if par else REST[n]
   p[n]=matrix(root_pos if n=='pelvis' else base.translation,p[par].to_quaternion()@q if par else q)
  if key.startswith('ZeroG_'):
   floating_arms(p,i/(len(local)-1),key[6:]);changes.append([(0,0),(0,0)])
  else:changes.append([clean_arm(p,s) for s in ('l','r')])
  # Floor clips retain lateral travel; fit the soles, without editing leg poses.
  if key.startswith('b'):
   z=min(*[p['foot_'+s].translation.z-.065 for s in ('l','r')],*[p['ball_'+s].translation.z-.025 for s in ('l','r')])
   for n in p:p[n].translation.z-=z
  poses.append(p)
 if not key.startswith('ZeroG_'):
  # Corrected shoulder paths can pass near a projection singularity. Filter
  # those local joint paths over time, then re-check reach; preserve untouched
  # arms instead of smoothing both sides to hide the defect.
  for iteration in range(2):
   local_arms=[{n:p[PARENT[n]].to_quaternion().inverted()@p[n].to_quaternion() for n in ORDER if n.startswith(('upperarm_','lowerarm_')) and len(n.split('_'))==2} for p in poses]
   for i,p in enumerate(poses):
    for si,side in enumerate(('l','r')):
     strength=min(1,max(changes[j][si][0] for j in range(max(0,i-10),min(len(poses),i+11)))/20)
     if strength<=0:continue
     for n in ('upperarm_'+side,'lowerarm_'+side):
      anchor=local_arms[i][n];qv=[0.0]*4
      for offset in range(-10,11):
       j=max(0,min(len(poses)-1,i+offset));q=local_arms[j][n];w=math.exp(-.5*(offset/4.0)**2)*(1 if anchor.dot(q)>=0 else -1)
       for k in range(4):qv[k]+=q[k]*w
      q=anchor.slerp(Quaternion(qv).normalized(),strength)
      goal=p[PARENT[n]].to_quaternion()@q
      rotate(p,n,goal@p[n].to_quaternion().inverted())
     clean_arm(p,side)
  # Keep wrists near their supplied neutral alignment; do not bend a wrist
  # sharply just because motion capture supplied that rotation.
  for p in poses:
   for side in ('l','r'):
    n='hand_'+side;neutral=(p[PARENT[n]]@REL[n]).to_quaternion();delta=neutral.inverted()@p[n].to_quaternion()
    if delta.w<0:delta.negate()
    limit=math.radians(40)
    if delta.angle>limit:
     goal=neutral@Quaternion().slerp(delta,limit/delta.angle)
     rotate(p,n,goal@p[n].to_quaternion().inverted())
 knee=[]
 if REVIEW_CALF_ROLL and key.startswith('ZeroG_'):
  for p in poses:
   for side in ('l','r'):knee.append(remove_calf_axial_roll(p,REST,PARENT,DESC,side))
 all_poses[key]=poses
 metrics.append({'clip':key,'frames':len(poses),'max_rear_correction_degrees':max(x[0] for row in changes for x in row),'unapplied_raised_arm_turn_demand_degrees':max(x[1] for row in changes for x in row),'knee_roll_cleanup':{'max_removed_degrees':max((r['removed_roll_degrees'] for r in knee),default=0),'max_ankle_shift_m':max((r['ankle_shift_m'] for r in knee),default=0),'samples':len(knee)}})
 print('REFINED',key,metrics[-1],flush=True)
 # Store rig reference once, without copying packed artwork.
 if target_rig is None:
  bpy.data.libraries.write(str(OUT/'RigReference.blend'),{rig},compress=True);target_rig=True
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(str(OUT/'RigReference.blend'),link=False) as (a,b):b.objects=a.objects
rig=next(o for o in b.objects if o.type=='ARMATURE');bpy.context.scene.collection.objects.link(rig)
ORDER=[b.name for b in rig.data.bones];PARENT={b.name:b.parent.name if b.parent else None for b in rig.data.bones}
im=rig.matrix_world.inverted();iq=rig.matrix_world.to_quaternion().inverted()
def bake(name,poses):
 act=bpy.data.actions.new(name);act.use_fake_user=True;rig.animation_data_create();rig.animation_data.action=act
 buffers={n:{'q':[[],[],[],[]],'p':[[],[],[]]} for n in ORDER}
 for frame,p in enumerate(poses,1):
  rm={n:matrix(im@p[n].translation,iq@p[n].to_quaternion()) for n in ORDER}
  for n in ORDER:
   bone=rig.pose.bones[n];par=PARENT[n]
   base=rm[par]@bone.parent.bone.matrix_local.inverted()@bone.bone.matrix_local if par else bone.bone.matrix_local
   basis=base.inverted()@rm[n];q=basis.to_quaternion()
   if frame>1 and sum(q[k]*buffers[n]['q'][k][-1] for k in range(4))<0:q.negate()
   for k in range(4):buffers[n]['q'][k].extend((frame,q[k]))
   for k in range(3):buffers[n]['p'][k].extend((frame,basis.translation[k]))
 for n in ORDER:
  bone=rig.pose.bones[n];bone.rotation_mode='QUATERNION';bone.keyframe_insert('rotation_quaternion',frame=1,group=n)
  if n=='pelvis':bone.keyframe_insert('location',frame=1,group=n)
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     n=fc.data_path.split('"')[1];kind='q' if fc.data_path.endswith('rotation_quaternion') else 'p'
     fc.keyframe_points.clear();fc.keyframe_points.add(len(poses));fc.keyframe_points.foreach_set('co',buffers[n][kind][fc.array_index])
     for pt in fc.keyframe_points:pt.interpolation='LINEAR'
     fc.update()
 scene=bpy.context.scene;scene.render.fps=FPS;scene.frame_start=1;scene.frame_end=len(poses);scene.frame_set(1)
 bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
 bpy.ops.export_scene.fbx(filepath=str(OUT/'FBX'/(name+'.fbx')),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z')
 return act
for key,poses in all_poses.items():bake('A_F3_Refined_'+key,poses)
for action in list(bpy.data.actions):
 if not action.name.startswith('A_F3_Refined_'):bpy.data.actions.remove(action)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Refined_ActionLibrary.blend'),compress=True)
(OUT/'Manifest.json').write_text(json.dumps({'fps':FPS,'status':'INTERNAL REVIEW ONLY; not adopted','method':'Source/native FK baseline, short temporal filter, torso-relative arm-direction cleanup; no fixed-hand or invented body orbit','clips':metrics},indent=2))
(R/'RefinedLandmarks.json').write_text(json.dumps({k:[{n:list(m.translation) for n,m in p.items() if n in ['pelvis','spine_05','head','upperarm_l','upperarm_r','lowerarm_l','lowerarm_r','hand_l','hand_r','foot_l','foot_r','ball_l','ball_r']} for p in v] for k,v in all_poses.items()},separators=(',',':')))
print('REFINEMENT_DONE',flush=True)
