"""Export the verified palmar action; reuse the unchanged glute-follow rest mesh."""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np

CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE))
from g2_palmar_motion_control import PalmarControl

model = PalmarControl(arm_ik=True, staged_release=True, free_wrist=True, index_lead=2.3)
manifest = json.loads((model.source / 'G2_PalmarGrip_Knots_Manifest.json').read_text())
library = model.source / manifest['file']
assert manifest['sources'] == model.guards
assert hashlib.sha256(library.read_bytes()).hexdigest() == manifest['sha256']
for name in ('SavedReplayKnots.json', 'SavedHandSurfaceKnots.json'):
    check = json.loads((model.output / name).read_text())
    assert check['passed'] and check['action_sha256'] == manifest['sha256']
previous = json.loads((model.review / 'G2GluteFollowNative240/Export.json').read_text())
assert previous['source_sha256'] == manifest['sources'][previous['source']]
assert hashlib.sha256(Path(previous['rest']).read_bytes()).hexdigest() == previous['rest_sha256']
assert manifest['weight_patch'] == model.manifest['weight_patch']
out = model.review / 'G2PalmarNative240'
target = model.source / 'G2GluteFollowProof/G2_PalmarGrip_240Hz.fbx'
assert not out.exists() and not target.exists(), 'Preserve previous proof'
out.mkdir()
rig, scene = model.rig, model.scene
rig.name = 'root.001'
with bpy.data.libraries.load(str(library), link=False) as (_, loaded):
    loaded.actions = [manifest['action']]
action = loaded.actions[0]
rig.animation_data.action = action
rig.animation_data.action_slot = action.slots[0]
scene.frame_start, scene.frame_end = 1, manifest['frame_end']
scene.render.fps = manifest['fps']
meshes = [o for o in scene.objects if o.type == 'MESH' and not o.hide_render]
rows, surfaces = [], {}
for t in (0., 1.9, 5., 10.667, 20., 29.5, 30.05, 31.):
    seconds = float(np.interp(t, manifest['source_seconds_map'], manifest['destination_seconds_map']))
    frame = 1 + seconds * manifest['fps']
    scene.frame_set(math.floor(frame), subframe=frame % 1)
    bpy.context.view_layer.update()
    label = f't{round(t*1000):05d}'
    rows.append({'label': label, 'source_seconds': t, 'seconds': seconds,
                 'bones_m': {b.name: list((rig.matrix_world @ b.matrix).translation) for b in rig.pose.bones}})
    for ob in meshes:
        evaluated = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
        surfaces[label + '__' + ob.name] = np.array([tuple(ob.matrix_world @ v.co) for v in evaluated.data.vertices])
np.savez_compressed(out / 'SourceSurfaces.npz', **surfaces)
(out / 'SourceControls.json').write_text(json.dumps({'source_sha256': previous['source_sha256'],
    'action_sha256': manifest['sha256'], 'rows': rows}, indent=2))
bpy.ops.object.select_all(action='DESELECT')
rig.hide_set(False)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
scene.frame_set(1)
bpy.ops.export_scene.fbx(filepath=str(target), use_selection=True, object_types={'ARMATURE'},
    add_leaf_bones=False, axis_forward='-Y', axis_up='Z', bake_anim=True,
    bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
    bake_anim_simplify_factor=0, bake_anim_step=.5)
report = dict(previous)
report.update(action=str(library), action_sha256=manifest['sha256'], animation=str(target),
    animation_sha256=hashlib.sha256(target.read_bytes()).hexdigest(), duration=manifest['seconds'], fps=240,
    scope='Private signed-palmar action only; reuse unchanged paired rest mesh. Native and artistic acceptance separate.')
(out / 'Export.json').write_text(json.dumps(report, indent=2))
model.assert_guards()
assert hashlib.sha256(library.read_bytes()).hexdigest() == manifest['sha256']
print('PALMAR_EXPORTED', report['animation_sha256'], flush=True)
