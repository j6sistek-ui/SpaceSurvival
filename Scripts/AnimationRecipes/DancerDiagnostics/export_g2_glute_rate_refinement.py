"""Retain120Hz failure; export only a240Hz animation, reusing the rest FBX."""
import bpy, hashlib, json, os, shutil
from pathlib import Path
P=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()
R=P/'.agent/local/AnimationReview_20261025';O=R/'G2GluteFollowNative240'
old=R/'G2GluteFollowNative';contract=json.loads((old/'Export.json').read_text())
failure=json.loads((old/'NativeParity.json').read_text());assert not failure['ok']
control=json.loads((old/'ResamplingControl.json').read_text())
assert max(r['max_mm'] for r in control if r['hz']==240)<.2
for key in ('source','action','rest'):
 assert hashlib.sha256(Path(contract[key]).read_bytes()).hexdigest()==contract[key+'_sha256']
target=Path(contract['animation']).with_name('G2_GluteFollow_240Hz.fbx')
assert not O.exists() and not target.exists(), 'Preserve previous export'
O.mkdir()
bpy.ops.wm.open_mainfile(filepath=contract['source'],load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');rig.name='root.001'
manifest=json.loads((Path(contract['action']).parent/'G2_GluteFollow_Manifest.json').read_text())
with bpy.data.libraries.load(contract['action'],link=False) as (_,loaded):loaded.actions=[manifest['action']]
rig.animation_data.action=loaded.actions[0];rig.animation_data.action_slot=loaded.actions[0].slots[0]
s.frame_start=1;s.frame_end=manifest['frame_end'];s.render.fps=60;s.frame_set(1)
bpy.ops.object.select_all(action='DESELECT');rig.hide_set(False);rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(target),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,axis_forward='-Y',axis_up='Z',bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,bake_anim_step=.25)
contract.update(animation=str(target),animation_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),fps=240)
(O/'Export.json').write_text(json.dumps(contract,indent=2))
for name in ('SourceControls.json','SourceSurfaces.npz'):shutil.copy2(old/name,O/name)
for key in ('source','action','rest'):
 assert hashlib.sha256(Path(contract[key]).read_bytes()).hexdigest()==contract[key+'_sha256']
print('GLUTE_240_EXPORTED',contract['animation_sha256'],flush=True)
