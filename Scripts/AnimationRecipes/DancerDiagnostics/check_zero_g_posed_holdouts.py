import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Measure visible posed error, separately from inverse-skin rest-space error."""
import bpy,json,math,numpy as np,hashlib
from pathlib import Path
O=R/'ZeroGSharedHip';D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
draft=O/'REJECTED_Interpolation.blend';report=json.loads((O/'Report.json').read_text());pairs=report['paired_curve_actions']
bpy.ops.wm.open_mainfile(filepath=str(draft),load_ui=False);s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');meshes=[o for o in s.objects if o.type=='MESH']
with bpy.data.libraries.load(str(D/'ZeroG_Coordinated_ActionLibrary.blend'),link=False) as(a,b):b.actions=[n for n in a.actions if n.startswith('A_F3_Coordinated_ZeroG_') and n not in bpy.data.actions]
for action in bpy.data.actions:
 if action.name in pairs:action.use_fake_user=True
code=(Path(__file__).resolve().parent/'bake_zero_g_shared_hip.py').read_text();a=code.index('names=[b.name');b=code.index('segments=[]',a);exec(compile(code[a:b],__file__,'exec'))
rows=[]
for name,pa in pairs.items():
 action=bpy.data.actions[name];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
 for n,action_name in pa.items():
  keys=data[n]['ob'].data.shape_keys;keys.animation_data_create();ka=bpy.data.actions[action_name];keys.animation_data.action=ka;keys.animation_data.action_slot=ka.slots[0]
 frames=sorted({x['frame'] for x in report['holdouts'] if x['action']==name}|({555,557,558,561,562,562.5,563,565} if 'Drift' in name else set()))
 for frame in frames:
  for x in data.values():
   for key in x['ob'].data.shape_keys.key_blocks:
    if key.name.startswith('REVIEW_ZG_'):key.mute=True
   x['mod'].use_deform_preserve_volume=False
  s.frame_set(math.floor(frame),subframe=frame%1);bpy.context.view_layer.update();lin={n:evaluate(x['ob']) for n,x in data.items()}
  for x in data.values():x['mod'].use_deform_preserve_volume=True
  bpy.context.view_layer.update();targets={n:lin[n]+(evaluate(x['ob'])-lin[n])*x['mask'][:,None] for n,x in data.items()}
  for x in data.values():
   x['mod'].use_deform_preserve_volume=False
   for key in x['ob'].data.shape_keys.key_blocks:
    if key.name.startswith('REVIEW_ZG_'):key.mute=False
  bpy.context.view_layer.update()
  for n,x in data.items():
   diff=(evaluate(x['ob'])-targets[n])@np.array(x['ob'].matrix_world.to_3x3()).T
   rows.append({'action':name,'frame':frame,'mesh':n,'posed_error_m':float(np.linalg.norm(diff,axis=1).max())})
result={'draft_sha256':hashlib.sha256(draft.read_bytes()).hexdigest(),'max_posed_error_m':max(x['posed_error_m'] for x in rows),'rows':rows}
(O/'PosedHoldouts.json').write_text(json.dumps(result,indent=2));print(json.dumps(sorted(rows,key=lambda x:x['posed_error_m'],reverse=True)[:8]),flush=True)
