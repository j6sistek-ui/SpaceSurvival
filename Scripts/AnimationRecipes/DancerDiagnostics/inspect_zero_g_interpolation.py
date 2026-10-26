import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Separate sparse curve interpolation from discontinuities in the DQ target."""
import bpy,json,math,numpy as np
from pathlib import Path
O=R/'ZeroGSharedHip';D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
bpy.ops.wm.open_mainfile(filepath=str(O/'REJECTED_Interpolation.blend'),load_ui=False);s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');meshes=[o for o in s.objects if o.type=='MESH']
with bpy.data.libraries.load(str(D/'ZeroG_Coordinated_ActionLibrary.blend'),link=False) as(a,b):b.actions=[n for n in a.actions if n.startswith('A_F3_Coordinated_ZeroG_') and n not in bpy.data.actions]
for action in b.actions:action.use_fake_user=True
for ob in meshes:
 if ob.data.shape_keys:
  for key in ob.data.shape_keys.key_blocks:
   if key.name.startswith('REVIEW_ZG_'):key.mute=True
code=(Path(__file__).resolve().parent/'bake_zero_g_shared_hip.py').read_text();a=code.index('names=[b.name');b=code.index('segments=[]',a);exec(compile(code[a:b],__file__,'exec'))
action=bpy.data.actions['A_F3_Coordinated_ZeroG_01_Drift'];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
rows=[];prev=None;positions={};deltas={}
for frame in np.arange(549.,576.01,.5):
 values=target(float(frame));deltas[frame]=values
 target_pos={n:evaluate(x['ob']) for n,x in data.items()}
 if prev is not None:
  row={'frame':float(frame),'delta_step_m':{n:float(np.linalg.norm(v-deltas[prev][n],axis=1).max()*data[n]['scale']) for n,v in values.items()}};rows.append(row)
 prev=frame
(O/'InterpolationDiagnostic.json').write_text(json.dumps(rows,indent=2));print(json.dumps(sorted(rows,key=lambda r:max(r['delta_step_m'].values()),reverse=True)[:8]),flush=True)
