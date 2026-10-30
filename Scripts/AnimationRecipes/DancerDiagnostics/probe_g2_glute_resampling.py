"""Distinguish regular export sampling from a changed source pose or skinning."""
import hashlib
import json
import math
import os
from pathlib import Path

import bpy

P = Path(os.environ.get('SS_ANIMATION_PROJECT', str(Path.home() / 'SpaceSurvival'))).resolve()
D = P / 'SourceAssets/DanceRefinement_20261025'
O = P / '.agent/local/AnimationReview_20261025/G2GluteFollowNative'
manifest = json.loads((D / 'G2_GluteFollow_Manifest.json').read_text())
source = D / 'Vexa_G2_PosteriorHip_Candidate.blend'
library = D / manifest['file']
guards = {source: manifest['mesh_sha256'], library: manifest['sha256']}
assert all(hashlib.sha256(p.read_bytes()).hexdigest() == h for p, h in guards.items())
bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False)
s = bpy.context.scene
rig = next(o for o in s.objects if o.type == 'ARMATURE')
with bpy.data.libraries.load(str(library), link=False) as (_, loaded):
    loaded.actions = [manifest['action']]
rig.animation_data.action = loaded.actions[0]
rig.animation_data.action_slot = loaded.actions[0].slots[0]
ordered = sorted(rig.pose.bones, key=lambda b: len(b.parent_recursive))


def pose(seconds):
    frame = 1 + seconds * 60
    s.frame_set(math.floor(frame), subframe=frame % 1)
    bpy.context.view_layer.update()
    return {b.name: (rig.matrix_world @ b.matrix).copy() for b in ordered}


rows = []
for sample in json.loads((O / 'SourceControls.json').read_text())['rows']:
    time = sample['seconds']
    target = pose(time)
    for hz in (120, 240, 480):
        lower = math.floor(time * hz) / hz
        upper = min(manifest['seconds'], lower + 1 / hz)
        alpha = (time - lower) * hz
        a, b, result = pose(lower), pose(upper), {}
        for bone in ordered:
            name = bone.name
            parent = bone.parent.name if bone.parent else None
            ma = a[parent].inverted() @ a[name] if parent else a[name]
            mb = b[parent].inverted() @ b[name] if parent else b[name]
            local = ma.lerp(mb, alpha)
            result[name] = result[parent] @ local if parent else local
        errors = {n: (result[n].translation - target[n].translation).length * 1000 for n in result}
        rows.append({'label': sample['label'], 'hz': hz, 'max_mm': max(errors.values()), 'bone': max(errors, key=errors.get)})
assert all(hashlib.sha256(p.read_bytes()).hexdigest() == h for p, h in guards.items())
(O / 'ResamplingControl.json').write_text(json.dumps(rows, indent=2))
print('RESAMPLING_MAX_MM', {hz: max(r['max_mm'] for r in rows if r['hz'] == hz) for hz in (120, 240, 480)}, flush=True)
