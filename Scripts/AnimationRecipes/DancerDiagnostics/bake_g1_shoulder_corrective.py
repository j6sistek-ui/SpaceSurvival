"""Bake the isolated left-axilla correction for G1, preserving every bone pose.

The mask/target reuse the retained local axilla technique, evaluated on G1's
actual poses. Old Spiral coefficients must never be replayed on this passage.
Private proof only: native replay and owner motion acceptance remain required.
"""
import hashlib
import json
import math
import os
import sys
from pathlib import Path

os.environ.setdefault('OPENBLAS_NUM_THREADS', '4')
import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from g1_palmar_motion_control import G1PalmarControl
from shoulder_support import shoulder_mask

model = G1PalmarControl(False, True, True, True)
scene, rig = model.scene, model.rig
cap_control = '--cap' in sys.argv
output = model.review/('G1ShoulderCapCorrective' if cap_control else 'G1ShoulderCorrective')
output.mkdir(exist_ok=True)
destination = model.source/('Vexa_G1_ShoulderCap_Candidate.blend' if cap_control else 'Vexa_G1_ShoulderLocal_Candidate.blend')
assert not destination.exists(), 'Preserve the existing candidate'
manifest_path = model.source/'G1_PalmarGrip_Knots_Manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
action_path = model.source/manifest['file']
assert hashlib.sha256(action_path.read_bytes()).hexdigest() == manifest['sha256']
with bpy.data.libraries.load(str(action_path), link=False) as (_, loaded):
    loaded.actions = [manifest['action']]
action = loaded.actions[0]
body = bpy.data.objects['Vexa_Continuous_Hands']
mask, boundary = shoulder_mask(body, [model.rest['upperarm_l'].translation])
points = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
def step(a, b, x):
    t = np.clip((x-a)/(b-a), 0, 1)
    return t*t*(3-2*t)
mask *= step(.09, .14, points[:, 0])*step(1.15, 1.24, points[:, 2])
if not cap_control:
    mask *= 1-step(1.44, 1.49, points[:, 2])
group = body.vertex_groups.new(name='REVIEW_G1_LeftAxilla')
for i, value in enumerate(mask):
    if value > 0:
        group.add([i], float(value), 'REPLACE')
corrective = body.modifiers.new('REVIEW_G1_LeftAxilla', 'CORRECTIVE_SMOOTH')
corrective.vertex_group = group.name
corrective.factor, corrective.iterations = .5, 8
corrective.rest_source = 'ORCO'
corrective.use_pin_boundary = True
weights = np.zeros((len(points), len(model.names)))
index = {name: i for i, name in enumerate(model.names)}
for vertex in body.data.vertices:
    for item in vertex.groups:
        name = body.vertex_groups[item.group].name
        if name in index:
            weights[vertex.index, index[name]] = item.weight
weights /= np.maximum(weights.sum(axis=1)[:, None], 1e-12)
left = body.matrix_world.inverted() @ rig.matrix_world
right = rig.matrix_world.inverted() @ body.matrix_world
scale = max(body.matrix_world.to_scale())
active = np.flatnonzero(mask > 0)
outside = np.flatnonzero(mask == 0)
maximum_target = 0.
cache = {}

def positions():
    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    coords = np.empty(len(evaluated.data.vertices)*3)
    evaluated.data.vertices.foreach_get('co', coords)
    return coords.reshape(-1, 3)

def target(seconds):
    global maximum_target
    key = round(seconds, 9)
    if key in cache:
        return cache[key]
    pose, _, _ = model.pose(seconds)
    model.apply(pose)
    corrective.show_viewport = False
    bpy.context.view_layer.update()
    linear = positions()
    corrective.show_viewport = True
    bpy.context.view_layer.update()
    adjusted = positions()
    corrective.show_viewport = False
    bpy.context.view_layer.update()
    assert np.max(np.linalg.norm(adjusted[outside]-linear[outside], axis=1))*scale < 1e-7
    maximum_target = max(maximum_target, float(np.linalg.norm(adjusted-linear, axis=1).max())*scale)
    matrices = np.array([(left @ rig.pose.bones[name].matrix @ rig.data.bones[name].matrix_local.inverted() @ right).to_3x3() for name in model.names])
    skin = np.einsum('vb,bij->vij', weights[active], matrices, optimize=True)
    assert np.abs(np.linalg.det(skin)).min() > .01, 'Singular local skin inverse'
    result = np.linalg.solve(skin, (adjusted-linear)[active, :, None])[..., 0]
    cache[key] = result
    return result

seconds = np.arange(0, 2*(model.manifest['frame_end']-1)+1)/120
if seconds[-1] != model.duration:
    seconds = np.r_[seconds, model.duration]
samples = []
for i, value in enumerate(seconds):
    samples.append(target(float(value)))
    if i % 100 == 0:
        print('G1_SHOULDER_SAMPLE', i, len(seconds), flush=True)
array = np.array(samples).reshape(len(samples), -1)
np.savez_compressed(output/'TargetSamples120.npz', seconds=seconds, active=active, deltas=np.array(samples))
u, singular, v = np.linalg.svd(array, full_matrices=False)
rank = None
rank_trials = []
for trial in (16, 24, 32, 48, 64, 96, 128):
    approximation = (u[:, :trial]*singular[:trial]) @ v[:trial]
    error = float(np.linalg.norm((approximation-array).reshape(len(samples), -1, 3), axis=2).max())*scale
    rank_trials.append({'rank': trial, 'max_rest_target_error_m': error})
    if error < .0001:
        rank = trial
        break
(output/'CompressionTrials.json').write_text(json.dumps(rank_trials, indent=2), encoding='utf-8')
assert rank, error
basis = v[:rank]
coefficients = u[:, :rank]*singular[:rank]
# Quarter-source-frame times were not used to fit the bases or interpolation.
holdout = []
for frame in range(0, model.manifest['frame_end']-1, 4):
    t = (frame+.25)/60
    expected = target(t)
    fitted = np.array([np.interp(t, seconds, coefficients[:, k]) for k in range(rank)]) @ basis
    error = float(np.linalg.norm(fitted.reshape(-1, 3)-expected, axis=1).max())*scale
    holdout.append(error)
(output/'Holdouts120.json').write_text(json.dumps(holdout), encoding='utf-8')
assert max(holdout) < .0003, max(holdout)

body.modifiers.remove(corrective)
body.vertex_groups.remove(group)
base = np.array([tuple(v.co) for v in body.data.shape_keys.key_blocks[0].data])
times = np.interp(seconds, manifest['source_seconds_map'], manifest['destination_seconds_map'])
frames = 1+times*manifest['fps']
keys = []
for k in range(rank):
    amplitude = max(float(np.abs(coefficients[:, k]).max()), 1e-6)
    key = body.shape_key_add(name=f'REVIEW_G1_LeftAxilla_{k:02}', from_mix=False)
    key.slider_min, key.slider_max = -10, 10
    coordinates = base.copy()
    coordinates[active] += basis[k].reshape(-1, 3)*amplitude
    key.data.foreach_set('co', coordinates.ravel())
    keys.append(key)
    for frame, value in zip(frames, coefficients[:, k]/amplitude):
        key.value = float(value)
        key.keyframe_insert('value', frame=float(frame))
shape_action = body.data.shape_keys.animation_data.action
shape_action.name = 'A_F3_G1_LeftAxilla_Correctives'
for layer in shape_action.layers:
    for strip in layer.strips:
        for bag in strip.channelbags:
            for curve in bag.fcurves:
                for point in curve.keyframe_points:
                    point.interpolation = 'LINEAR'

# Test the saved rig plus corrective curves at unrelated fractional times.
rig.animation_data.action = action
rig.animation_data.action_slot = action.slots[0]
scene.render.fps = manifest['fps']
scene.frame_start, scene.frame_end = 1, manifest['frame_end']
check_times = [0., .713, 3., 5.017, 8.4166667, 11.69, 12.27, 13.19, 16.123, model.duration]
replay = []
for t in check_times:
    frame = 1+float(np.interp(t, manifest['source_seconds_map'], manifest['destination_seconds_map']))*manifest['fps']
    scene.frame_set(math.floor(frame), subframe=frame%1)
    bpy.context.view_layer.update()
    live = positions()
    delta = np.zeros_like(base)
    for key in keys:
        coords = np.array([tuple(p.co) for p in key.data])
        delta += key.value*(coords-base)
    assert float(np.linalg.norm(delta[outside], axis=1).max())*scale < 1e-7
    replay.append({'source_seconds': t, 'destination_frame': frame,
                   'outside_mask_delta_m': float(np.linalg.norm(delta[outside], axis=1).max())*scale,
                   'finite_surface': bool(np.isfinite(live).all())})
assert all(x['finite_surface'] for x in replay)
model.assert_guards()
assert hashlib.sha256(action_path.read_bytes()).hexdigest() == manifest['sha256']
used = {action, shape_action}
for ob in scene.objects:
    if ob.type == 'MESH' and ob.data.shape_keys and ob.data.shape_keys.animation_data:
        used.add(ob.data.shape_keys.animation_data.action)
for old in list(bpy.data.actions):
    if old not in used:
        bpy.data.actions.remove(old)
scene.frame_set(round(1+np.interp(3., manifest['source_seconds_map'], manifest['destination_seconds_map'])*manifest['fps']))
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(destination), compress=True)
report = {'status': 'PRIVATE G1 LEFT SHOULDER CANDIDATE; NOT NATIVE OR OWNER ACCEPTED',
          'sources': model.guards, 'rig_action_sha256': manifest['sha256'],
          'file': str(destination), 'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
          'action': action.name, 'shape_action': shape_action.name, 'rank': rank,
          'active_vertices': len(active), 'max_target_surface_delta_m': maximum_target,
          'rank_trials': rank_trials,
          'holdout_samples': len(holdout), 'max_holdout_target_error_m': max(holdout),
          'bone_count': len(model.names), 'weight_changes': 0, 'bone_pose_changes': 0,
          'includes_shoulder_cap': cap_control,
          'fps': manifest['fps'], 'frame_end': manifest['frame_end'], 'seconds': manifest['seconds'],
          'replay': replay}
(output/'Bake.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('G1_SHOULDER_SAVED', report['sha256'], flush=True)
