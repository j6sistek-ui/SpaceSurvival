import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Read-only arm-roll evidence at the reported shoulder folds."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025'
bpy.ops.wm.open_mainfile(filepath=str(D/'Vexa_ShoulderGirdle_Study.blend'),load_ui=False)
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');rows=[]
for sec in (0,4,8,9.033333,12.2,16):
 bpy.context.scene.frame_set(round(1+sec*60));bpy.context.view_layer.update()
 row={'seconds':sec}
 for side in ('l','r'):
  upper,lower,hand=['upperarm_'+side,'lowerarm_'+side,'hand_'+side]
  rest=[rig.matrix_world@rig.data.bones[n].matrix_local for n in (upper,lower,hand)]
  pose=[rig.matrix_world@rig.pose.bones[n].matrix for n in (upper,lower,hand)]
  u=(pose[1].translation-pose[0].translation).normalized();v=(pose[2].translation-pose[1].translation).normalized();bend=u.cross(v).normalized()
  rest_u=(rest[1].translation-rest[0].translation).normalized();rest_bend=rest_u.cross(Vector((0,-1,0))).normalized()
  delta=pose[0].to_quaternion()@rest[0].to_quaternion().inverted();expected=delta@rest_bend
  row[side]={'elbow_flex_deg':math.degrees(u.angle(v)),
             'front_flex_plane_error_deg':math.degrees(expected.angle(bend)),
             'upperarm_world_dir':list(u),'forearm_world_dir':list(v),
             'native_hinge_local':list(rest[0].to_quaternion().inverted()@rest_bend)}
 rows.append(row)
(R/'VexaGirdleStudy/ArmPlaneInspection.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows),flush=True)
