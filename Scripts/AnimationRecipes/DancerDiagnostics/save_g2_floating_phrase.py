"""Save/replay a private G2 leg phrase while retaining untouched source curves.

The ten edited bones are sampled at120Hz plus every original fractional knot.
No mesh, original action, shoulder corrective or production asset is rewritten.
"""
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
out = model.project / '.agent/local/AnimationReview_20261025/G2FloatingLife/PhraseControl'
audit = json.loads((out / 'Audit.json').read_text())
control_hash = hashlib.sha256(Path(__file__).with_name('g2_floating_life_control.py').read_bytes()).hexdigest()
assert audit['passed'] and audit['control_sha256'] == control_hash and audit['recipe_variant'] == 'phrase'
target = model.source / 'G2_FloatingLegPhrase_ActionLibrary.blend'
record = model.source / 'G2_FloatingLegPhrase_Manifest.json'
changed = {'thigh_l', 'thigh_r', 'calf_l', 'calf_r', 'foot_l', 'foot_r',
           'glute_l', 'glute_r', 'lowerarm_l', 'hand_l'}
fps = 120
verify = '--verify-only' in sys.argv


def curves(action):
    return [c for layer in action.layers for strip in layer.strips
            for bag in strip.channelbags for c in bag.fcurves]


def curve_digest(curve):
    values = np.empty(len(curve.keyframe_points) * 2, dtype=np.float32)
    curve.keyframe_points.foreach_get('co', values)
    return hashlib.sha256(values.tobytes()).hexdigest()


def protected(action):
    return {(c.data_path, c.array_index): curve_digest(c) for c in curves(action)
            if c.data_path.split('"')[1] not in changed}


original_protected = protected(model.action)
if verify:
    manifest = json.loads(record.read_text())
    assert manifest['sources'] == model.guards and manifest['control_sha256'] == control_hash
    assert hashlib.sha256(target.read_bytes()).hexdigest() == manifest['sha256']
    with bpy.data.libraries.load(str(target), link=False) as (_, loaded):
        loaded.actions = [manifest['action']]
    candidate = loaded.actions[0]
    assert protected(candidate) == original_protected
    count = round(model.duration * fps * 2) + 1
    expected = np.empty((count, len(model.names), 4, 4), dtype=np.float32)
    for i in range(count):
        pose = model.pose(i / (fps * 2))[0]
        expected[i] = np.array([pose[n] for n in model.names])
        if i % 2400 == 0:
            print('PHRASE_EXPECTED', i, flush=True)
    model.rig.animation_data.action = candidate
    model.rig.animation_data.action_slot = candidate.slots[0]
    max_position = max_matrix = max_speed = 0.
    first = previous = last = None
    for i in range(count):
        frame = 1 + i / 2
        model.scene.frame_set(math.floor(frame), subframe=frame % 1)
        bpy.context.view_layer.update()
        pose = {n: model.rig.matrix_world @ model.rig.pose.bones[n].matrix for n in model.names}
        actual = np.array([pose[n] for n in model.names])
        max_position = max(max_position, float(np.linalg.norm(actual[:, :3, 3] - expected[i, :, :3, 3], axis=1).max()))
        max_matrix = max(max_matrix, float(np.abs(actual - expected[i]).max()))
        quats = np.array([list((pose[model.parents[n]].inverted() @ pose[n] if model.parents[n] else pose[n]).to_quaternion()) for n in model.names])
        quats /= np.linalg.norm(quats, axis=1)[:, None]
        if previous is not None:
            max_speed = max(max_speed, float(np.degrees(2 * np.arccos(np.clip(np.abs((quats * previous).sum(axis=1)), 0, 1))).max() * fps * 2))
        previous = quats
        if first is None:
            first = actual.copy()
        last = actual
    loop = float(np.abs(first - last).max())
    report = {'passed': max_position < .00015 and max_matrix < .001 and loop < .0001 and max_speed < 95,
              'samples': count, 'maximum_bone_position_error_mm': max_position * 1000,
              'maximum_matrix_error': max_matrix, 'maximum_local_dps': max_speed,
              'loop_matrix_error': loop, 'protected_curves_exact': True,
              'action_sha256': manifest['sha256'], 'control_sha256': control_hash,
              'scope': 'Fresh saved action versus control at240Hz; unchanged curves and loop. Contact/native/artistic checks separate.'}
    assert not (out / 'SavedReplay.json').exists(), 'Preserve prior replay evidence'
    (out / 'SavedReplay.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('PHRASE_REPLAY', report, flush=True)
    assert report['passed']
else:
    assert not target.exists() and not record.exists(), 'Preserve previous candidate'
    frames = set((1 + np.arange(round(model.duration * fps) + 1)).tolist())
    for c in curves(model.action):
        coords = np.empty(len(c.keyframe_points) * 2, dtype=np.float32)
        c.keyframe_points.foreach_get('co', coords)
        frames.update(coords[::2].tolist())
    frames = np.array(sorted(f for f in frames if 1 <= f <= 1 + model.duration * fps))
    names = sorted(changed)
    values = np.empty((len(frames), len(names), 10), dtype=np.float64)
    previous = None
    for i, frame in enumerate(frames):
        pose = model.pose((frame - 1) / fps)[0]
        for j, name in enumerate(names):
            parent = pose[model.parents[name]] @ model.relative[name]
            location, rotation, scale = (parent.inverted() @ pose[name]).decompose()
            rotation.normalize()
            if previous is not None and np.dot(np.array(rotation), previous[j, 3:7]) < 0:
                rotation.negate()
            values[i, j] = [*location, *rotation, *scale]
        previous = values[i]
        if i % 2400 == 0:
            print('PHRASE_BAKE', i, len(frames), flush=True)
    candidate = model.action.copy()
    candidate.name = 'A_F3_G2_FloatingLegPhrase_Review'
    candidate.use_fake_user = True
    offsets = {'location': 0, 'rotation_quaternion': 3, 'scale': 7}
    edited = 0
    for curve in curves(candidate):
        name = curve.data_path.split('"')[1]
        if name not in changed:
            continue
        kind = curve.data_path.rsplit('.', 1)[1]
        column = values[:, names.index(name), offsets[kind] + curve.array_index]
        times = frames
        if np.ptp(column) < 1e-8:
            times, column = frames[[0, -1]], column[[0, -1]]
        curve.keyframe_points.clear()
        curve.keyframe_points.add(len(times))
        curve.keyframe_points.foreach_set('co', np.column_stack((times, column)).ravel())
        for key in curve.keyframe_points:
            key.interpolation = 'LINEAR'
        curve.update()
        edited += 1
    assert edited == len(changed) * 10
    assert protected(candidate) == original_protected
    candidate['quality_state'] = 'Private G2 leg phrasing; full contact, native and artistic review still required.'
    model.assert_guards()
    bpy.data.libraries.write(str(target), {candidate}, fake_user=True, compress=True)
    manifest = {'file': target.name, 'action': candidate.name, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                'sources': model.guards, 'control_sha256': control_hash, 'seconds': model.duration,
                'fps': fps, 'frame_end': round(model.duration * fps) + 1, 'bake_knots': len(frames),
                'edited_bones': names, 'protected_curve_count': len(original_protected),
                'source_knots_preserved': True, 'source_manifest': 'G2_PalmarGrip_Knots_Manifest.json',
                'windows_seconds': model.windows, 'scope': candidate['quality_state']}
    record.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('PHRASE_SAVED', manifest['sha256'], target.stat().st_size, flush=True)
model.assert_guards()
