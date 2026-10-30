"""Export the saved leg phrase against the unchanged private G2 rest mesh."""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from g2_floating_life_control import FloatingLifeControl

model = FloatingLifeControl(phrase=True)
manifest = json.loads((model.source / 'G2_FloatingLegPhrase_Manifest.json').read_text())
library = model.source / manifest['file']
assert hashlib.sha256(library.read_bytes()).hexdigest() == manifest['sha256']
review = model.project / '.agent/local/AnimationReview_20261025'
replay = json.loads((review / 'G2FloatingLife/PhraseControl/SavedReplay.json').read_text())
assert replay['passed'] and replay['action_sha256'] == manifest['sha256']
contract = json.loads((review / 'G2GluteFollowNative240/Export.json').read_text())
assert hashlib.sha256(Path(contract['rest']).read_bytes()).hexdigest() == contract['rest_sha256']
out = review / 'G2FloatingPhraseNative240'
target = model.source / 'G2GluteFollowProof/G2_FloatingLegPhrase_240Hz.fbx'
assert not out.exists() and not target.exists(), 'Preserve previous native proof'
out.mkdir()
rig, scene = model.rig, model.scene
rig.name = 'root.001'
with bpy.data.libraries.load(str(library), link=False) as (_, loaded):
    loaded.actions = [manifest['action']]
rig.animation_data.action = loaded.actions[0]
rig.animation_data.action_slot = loaded.actions[0].slots[0]
scene.frame_start, scene.frame_end = 1, manifest['frame_end']
scene.render.fps = manifest['fps']
rows, surfaces = [], {}
for seconds in (0., 1.9, 3.1, 5.5, 34.5, 37.2, 41.5, 49.5):
    frame = 1 + seconds * manifest['fps']
    scene.frame_set(math.floor(frame), subframe=frame % 1)
    bpy.context.view_layer.update()
    label = f't{round(seconds * 1000):05d}'
    rows.append({'label': label, 'source_seconds': seconds, 'seconds': seconds,
                 'bones_m': {b.name: list((rig.matrix_world @ b.matrix).translation) for b in rig.pose.bones}})
    for ob in scene.objects:
        if ob.type == 'MESH' and not ob.hide_render:
            evaluated = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
            surfaces[label + '__' + ob.name] = np.array([tuple(ob.matrix_world @ v.co) for v in evaluated.data.vertices])
source = model.source / 'Vexa_G1_ShoulderCap_Candidate.blend'
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
np.savez_compressed(out / 'SourceSurfaces.npz', **surfaces)
(out / 'SourceControls.json').write_text(json.dumps({'source_sha256': source_hash,
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
contract.update(source=str(source), source_sha256=source_hash, action=str(library),
    action_sha256=manifest['sha256'], animation=str(target),
    animation_sha256=hashlib.sha256(target.read_bytes()).hexdigest(), duration=manifest['seconds'], fps=240,
    scope='Private leg phrase animation; unchanged shared G2 rest mesh. No production adoption or full anatomy acceptance.')
(out / 'Export.json').write_text(json.dumps(contract, indent=2))
model.assert_guards()
assert hashlib.sha256(library.read_bytes()).hexdigest() == manifest['sha256']
print('FLOATING_EXPORTED', contract['animation_sha256'], flush=True)
