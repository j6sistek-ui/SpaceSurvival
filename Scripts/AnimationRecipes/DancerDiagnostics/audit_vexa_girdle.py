import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Compare the private girdle study against its preserved source motion."""
import bpy,json,numpy as np,os
from pathlib import Path
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025'
DELTOID=os.environ.get('SS_REVIEW_DELTOID')=='1'
O=R/('VexaDeltoidStudy' if DELTOID else 'VexaGirdleStudy');O.mkdir(exist_ok=True)
frames=list(range(1,962))
def sample(path,names=None):
 bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False)
 rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
 if names is None:names=[b.name for b in rig.data.bones]
 rows=[]
 for frame in frames:
  bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
  rows.append([np.array(rig.matrix_world@rig.pose.bones[n].matrix) for n in names])
 return names,np.array(rows),{n:np.array(rig.data.bones[n].matrix_local) for n in names}
names,reference,rest=sample(D/('Vexa_ShoulderGirdle_Study.blend' if DELTOID else 'Vexa_Underarm_Proof.blend'))
regions=[]
if DELTOID:
 torso=bpy.data.objects['Vexa_Nude_Torso'];world=np.array([tuple(torso.matrix_world@v.co) for v in torso.data.vertices]);protected=np.where(world[:,0]<.065)[0]
 for frame in (1,241,481,543,733,961):
  bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();ev=torso.evaluated_get(bpy.context.evaluated_depsgraph_get())
  regions.append((frame,np.array([tuple(ev.matrix_world@ev.data.vertices[int(i)].co) for i in protected])))
_,candidate,candidate_rest=sample(D/('Vexa_Deltoid_Study.blend' if DELTOID else 'Vexa_ShoulderGirdle_Study.blend'),names)
pose_error=float(np.max(np.abs(candidate-reference)))
rest_error=max(float(np.max(np.abs(rest[n]-candidate_rest[n]))) for n in names)
assert pose_error<1e-6 and rest_error<1e-6,(pose_error,rest_error)
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
torso=bpy.data.objects['Vexa_Nude_Torso'];bone_names={b.name for b in rig.data.bones if b.use_deform}
weights=[]
for v in torso.data.vertices:
 weights.append(sum(g.weight for g in v.groups if torso.vertex_groups[g.group].name in bone_names))
maximum_normalization_error=float(np.max(np.abs(np.array(weights)-1.)))
assert maximum_normalization_error<1e-5
helper_motion={}
for side in ('l','r'):
 pb=rig.pose.bones['REVIEW_scapula_'+side];locations=[];rotations=[]
 for frame in frames:
  bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
  chest=rig.pose.bones['spine_05'].matrix
  relative=chest.inverted()@pb.matrix
  locations.append(list(relative.translation*.01));rotations.append(relative.to_quaternion())
 steps=[rotations[i-1].rotation_difference(rotations[i]).angle for i in range(1,len(rotations))]
 helper_motion[side]={'max_local_step_deg':float(np.degrees(max(steps))),
                      'chest_relative_travel_m':np.ptp(np.array(locations),axis=0).tolist()}
 assert helper_motion[side]['max_local_step_deg']<5,helper_motion[side]
report={'status':'DATA PARITY ONLY; anatomy and native playback still unaccepted',
        'frames':len(frames),'original_bones':len(names),'original_pose_matrix_max_delta':pose_error,
        'original_rest_matrix_max_delta':rest_error,'max_weight_normalization_error':maximum_normalization_error,
        'helpers':helper_motion}
if DELTOID:
 errors=[]
 for frame,expected in regions:
  bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();ev=torso.evaluated_get(bpy.context.evaluated_depsgraph_get())
  actual=np.array([tuple(ev.matrix_world@ev.data.vertices[int(i)].co) for i in protected])
  errors.append({'frame':frame,'max_neck_and_other_side_delta_m':float(np.linalg.norm(actual-expected,axis=1).max())})
 report['protected_region']=errors
 assert max(x['max_neck_and_other_side_delta_m'] for x in errors)<1e-5,errors
(O/'MotionAudit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report),flush=True)
