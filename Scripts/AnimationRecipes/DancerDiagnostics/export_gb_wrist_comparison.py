import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Export existing original/derivative actions only, with fresh-load assertions."""
import bpy,json,hashlib,math
from pathlib import Path
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025';O=D/'GBWristComparison';O.mkdir(exist_ok=True)
report={'exports':[],'unchanged_sources':{}}
for kind,file,prefix in [('before','Refined_ActionLibrary.blend','A_F3_Refined_'),('after','GB_WristContinuous_ActionLibrary.blend','A_F3_WristContinuous_')]:
 source=D/file;digest=hashlib.sha256(source.read_bytes()).hexdigest()
 bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False);s=bpy.context.scene;s.render.fps=60
 rig=next(o for o in s.objects if o.type=='ARMATURE')
 # FBX inserts the armature object as an extra root. Match the saved Vexa
 # object name; the 95 deform/rest bones are already compatible and untouched.
 compatibility=json.loads((R/'VexaDistalRepair/ActionReuse.json').read_text())
 assert compatibility['rigs'][0]['rest_max_element_error']<1e-5
 assert max(abs(rig.matrix_world[r][c]-compatibility['target_matrix'][r][c]) for r in range(4) for c in range(4))<1e-5
 rig.name=compatibility['target_object']
 bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
 for clip in ('g1','g2','b1','b2'):
  action=bpy.data.actions[prefix+clip];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
  s.frame_start,s.frame_end=map(round,action.frame_range)
  previous={};step=0.
  for f in range(s.frame_start,s.frame_end+1):
   s.frame_set(f)
   for side in ('l','r'):
    q=rig.pose.bones['hand_'+side].matrix_basis.to_quaternion()
    if side in previous:
     a=math.degrees(q.rotation_difference(previous[side]).angle);step=max(step,min(a,360-a))
    previous[side]=q.copy()
  if kind=='after':assert step<5.01,(clip,step)
  path=O/f'{clip}_{kind}.fbx'
  bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z')
  report['exports'].append({'clip':clip,'kind':kind,'file':str(path),'seconds':(s.frame_end-s.frame_start)/60,'max_wrist_step_deg':step})
 assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
 report['unchanged_sources'][str(source)]=digest
(R/'VexaDistalRepair/GBWristExport.json').write_text(json.dumps(report,indent=2));print('GB_WRIST_EXPORT_DONE',flush=True)
