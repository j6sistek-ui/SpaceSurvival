import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Read-only full-clip range screen on repaired Vexa, without Spiral morph curves.

The clips are unconstrained. This does not certify pole grips or artistic quality.
"""
import bpy, json, math, hashlib
from pathlib import Path
from mathutils import Vector, Matrix
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
O=R/'VexaDistalRepair/GBReuse';O.mkdir(exist_ok=True)
sources=[D/'Vexa_ContinuousDistal_Proof.blend',D/'Refined_ActionLibrary.blend']
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
bpy.ops.wm.open_mainfile(filepath=str(sources[0]),load_ui=False)
s=bpy.context.scene;s.render.fps=60
rig=next(o for o in s.objects if o.type=='ARMATURE')
rig.animation_data_clear()
for ob in s.objects:
 if ob.type=='MESH' and ob.data.shape_keys:
  ob.data.shape_keys.animation_data_clear()
  for key in ob.data.shape_keys.key_blocks:
   if key.name.startswith('REVIEW_'):key.value=0
for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
rest={b.name:(rig.matrix_world@b.matrix_local).copy() for b in rig.data.bones}
with bpy.data.libraries.load(str(sources[1]),link=False) as (a,b):
 b.objects=a.objects;b.actions=['A_F3_Refined_'+k for k in ('g1','g2','b1','b2')]
reference=next(o for o in b.objects if o.type=='ARMATURE')
s.collection.objects.link(reference);bpy.context.view_layer.update()
assert set(rest)==set(x.name for x in reference.data.bones)
rest_error=max(max(abs(rest[n][r][c]-(reference.matrix_world@reference.data.bones[n].matrix_local)[r][c]) for r in range(4) for c in range(4)) for n in rest)
assert rest_error<1e-5,rest_error
bpy.data.objects.remove(reference,do_unlink=True)
actions=b.actions
hinge={}
for side in ('l','r'):
 a,b,c=[rest[n+'_'+side] for n in ('upperarm','lowerarm','hand')]
 hinge[side]=a.to_quaternion().inverted()@(b.translation-a.translation).cross(c.translation-b.translation).normalized()
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='SINGLE'
s.display.shading.single_color=(.55,.55,.55);s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD'
s.world=bpy.data.worlds.new('GBRange');s.world.color=(.035,.045,.055)
s.render.resolution_x=800;s.render.resolution_y=800;s.render.resolution_percentage=100
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO'
report={'sources':hashes,'rest_matrix_error':rest_error,'scope':'Repaired Vexa weights/continuous surfaces; prior Spiral correction curves disabled; no contact solver or new retarget. Range screens are rejection signals, not anatomy acceptance.','clips':[]}
for act in actions:
 rig.animation_data_create();rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 start,end=map(round,act.frame_range);row={'clip':act.name,'frames':end-start+1,'reversed_elbow_frames':0,'rear_reach_frames':0,'max_wrist_rest_angle_deg':0,'max_ankle_rest_angle_deg':0,'max_local_step_deg':0,'worst':[]}
 previous={};pose_by_frame={}
 for f in range(start,end+1):
  s.frame_set(f);p={n:rig.matrix_world@rig.pose.bones[n].matrix for n in rest}
  chest=p['spine_05'].to_quaternion()@rest['spine_05'].to_quaternion().inverted();up=chest@Vector((0,0,1));forward=chest@Vector((0,-1,0))
  flipped=rear=False;score=0.;details=[]
  for side in ('l','r'):
   a,b,c=[p[n+'_'+side] for n in ('upperarm','lowerarm','hand')]
   upper=(b.translation-a.translation).normalized();lower=(c.translation-b.translation).normalized();h=upper.cross(lower)
   flex=math.degrees(upper.angle(lower));alignment=1. if h.length<=.1 else (a.to_quaternion().inverted()@h.normalized()).dot(hinge[side])
   back=math.degrees(math.asin(max(-1,min(1,-upper.dot(forward)))));limit=10 if upper.dot(up)>0 else 0
   flipped|=alignment<0 and flex>10;rear|=back>limit+2
   angles={}
   for prefix,parprefix in [('hand','lowerarm'),('foot','calf')]:
    n=prefix+'_'+side;par=parprefix+'_'+side
    neutral=p[par]@rest[par].inverted()@rest[n]
    q=neutral.to_quaternion().inverted()@p[n].to_quaternion()
    if q.w<0:q.negate()
    angles[prefix]=math.degrees(q.angle)
    field='max_wrist_rest_angle_deg' if prefix=='hand' else 'max_ankle_rest_angle_deg'
    row[field]=max(row[field],angles[prefix])
   details.append({'side':side,'elbow_flex_deg':flex,'hinge_alignment':alignment,'rear_deg':back,'wrist_deg':angles['hand'],'ankle_deg':angles['foot']})
   score=max(score,max(0,back-limit)+max(0,-alignment)*90+angles['hand']*.2+angles['foot']*.1)
  for n in rest:
   q=rig.pose.bones[n].rotation_quaternion.copy()
   if n in previous:
    angle=math.degrees(q.rotation_difference(previous[n]).angle);angle=min(angle,360-angle)
    row['max_local_step_deg']=max(row['max_local_step_deg'],angle)
   previous[n]=q
  row['reversed_elbow_frames']+=int(flipped);row['rear_reach_frames']+=int(rear)
  row['worst'].append({'frame':f,'seconds':(f-start)/60,'score':score,'sides':details})
 row['worst']=sorted(row['worst'],key=lambda v:v['score'],reverse=True)
 chosen=[]
 for candidate in row['worst']:
  if all(abs(candidate['frame']-x['frame'])>=90 for x in chosen):chosen.append(candidate)
  if len(chosen)==3:break
 row['worst']=chosen;row['views']=[]
 for entry in chosen:
  f=entry['frame'];s.frame_set(f)
  pelvis=rig.matrix_world@rig.pose.bones['pelvis'].head
  chest=(rig.matrix_world@rig.pose.bones['spine_05'].matrix).to_quaternion()@rest['spine_05'].to_quaternion().inverted()
  center=(rig.matrix_world@rig.pose.bones['upperarm_l'].head+rig.matrix_world@rig.pose.bones['upperarm_r'].head)*.5
  for view,offset,scale,target in [('front',Vector((0,-3,.2)),1.2,center),('back',Vector((0,3,.2)),1.2,center),('full',Vector((2,-4,1)),2.8,pelvis)]:
   cam.data.ortho_scale=scale;cam.location=target+(chest@offset if view!='full' else offset);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
   path=O/f'{act.name}_{f}_{view}.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
   row['views'].append(str(path))
 report['clips'].append(row)
 print('VEXA_GB_RANGE',json.dumps({k:v for k,v in row.items() if k not in ('worst','views')}),flush=True)
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
(O/'Report.json').write_text(json.dumps(report,indent=2))
print('VEXA_GB_RANGE_DONE',flush=True)
