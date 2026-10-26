"""Export only the guarded G1 shoulder candidate into a new private proof.

Old time-indexed corrective curves are removed from this in-memory export,
never from the saved source. The rig and new corrective action travel together.
"""
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix
sys.path.insert(0, str(Path(__file__).resolve().parent))
from shoulder_support import shoulder_mask

project = Path(os.environ.get('SS_ANIMATION_PROJECT', str(Path.home()/'SpaceSurvival'))).resolve()
review = project/'.agent/local/AnimationReview_20261025'
source = project/'SourceAssets/DanceRefinement_20261025'
cap_control = '--cap' in sys.argv
gate = json.loads((review/('G1ShoulderCapCorrective' if cap_control else 'G1ShoulderCorrective')/'Bake.json').read_text(encoding='utf-8'))
manifest = json.loads((source/'G1_PalmarGrip_Knots_Manifest.json').read_text(encoding='utf-8'))
candidate = Path(gate['file'])
assert hashlib.sha256(candidate.read_bytes()).hexdigest() == gate['sha256']
assert gate['rig_action_sha256'] == manifest['sha256']
for name in ('SavedReplayKnots.json', 'SavedHandSurfaceKnots.json'):
    check = json.loads((review/'G1PalmarGrip/FreeArmRigidControlContinuousPinned'/name).read_text(encoding='utf-8'))
    assert check['passed'] and check['action_sha256'] == manifest['sha256']
out = review/('G1ShoulderCapNative240' if cap_control else 'G1ShoulderNative240')
folder = source/('G1ShoulderCapProof' if cap_control else 'G1ShoulderProof')
assert not out.exists() and not folder.exists(), 'Preserve prior proof'
out.mkdir()
folder.mkdir()
bpy.ops.wm.open_mainfile(filepath=str(candidate), load_ui=False)
scene = bpy.context.scene
rig = next(ob for ob in scene.objects if ob.type == 'ARMATURE')
rig.name = 'root.001'
meshes = [ob for ob in scene.objects if ob.type == 'MESH' and not ob.hide_render]
assert len(rig.data.bones) == 95
expected = []
for ob in meshes:
    if not ob.data.shape_keys:
        continue
    keys = ob.data.shape_keys
    for key in list(keys.key_blocks)[1:]:
        if key.name.startswith('REVIEW_G1_LeftAxilla_'):
            assert not key.mute
            expected.append(key.name)
        elif key.name.startswith('REVIEW_'):
            assert key.mute or abs(key.value) < 1e-8, key.name
            ob.shape_key_remove(key)
assert len(expected) == gate['rank']
body = bpy.data.objects['Vexa_Continuous_Hands']
new_keys = [key for key in body.data.shape_keys.key_blocks if key.name.startswith('REVIEW_G1_LeftAxilla_')]
mask, _ = shoulder_mask(body, [(rig.matrix_world@rig.data.bones['upperarm_l'].matrix_local).translation])
points = np.array([tuple(body.matrix_world@v.co) for v in body.data.vertices])
def step(a, b, x):
    value = np.clip((x-a)/(b-a), 0, 1)
    return value*value*(3-2*value)
mask *= step(.09, .14, points[:, 0])*step(1.15, 1.24, points[:, 2])
if not cap_control:
    mask *= 1-step(1.44, 1.49, points[:, 2])
group = body.vertex_groups.new(name='REVIEW_TargetCheck')
for i, value in enumerate(mask):
    if value > 0:
        group.add([i], float(value), 'REPLACE')
smooth = body.modifiers.new('REVIEW_TargetCheck', 'CORRECTIVE_SMOOTH')
smooth.vertex_group = group.name
smooth.factor, smooth.iterations, smooth.rest_source, smooth.use_pin_boundary = .5, 8, 'ORCO', True
smooth.show_viewport = False
rows, surfaces = [], {}
target_errors = []
for t in (0., 3., 7.254899317387129, 8.4166667, 11.69, 12.27, 16.123, 18.333333333333332):
    seconds = float(np.interp(t, manifest['source_seconds_map'], manifest['destination_seconds_map']))
    frame = 1+seconds*manifest['fps']
    scene.frame_set(math.floor(frame), subframe=frame % 1)
    bpy.context.view_layer.update()
    label = f't{round(t*1000):05d}'
    rows.append({'label': label, 'source_seconds': t, 'seconds': seconds,
                 'bones_m': {b.name: list((rig.matrix_world@b.matrix).translation) for b in rig.pose.bones}})
    for ob in meshes:
        evaluated = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
        surfaces[label+'__'+ob.name] = np.array([tuple(ob.matrix_world@v.co) for v in evaluated.data.vertices])
    for key in new_keys:
        key.mute = True
    smooth.show_viewport = True
    bpy.context.view_layer.update()
    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    target_points = np.array([tuple(body.matrix_world@v.co) for v in evaluated.data.vertices])
    error = float(np.linalg.norm(surfaces[label+'__'+body.name]-target_points, axis=1).max())
    target_errors.append({'source_seconds': t, 'error_m': error})
    for key in new_keys:
        key.mute = False
    smooth.show_viewport = False
    bpy.context.view_layer.update()
assert max(row['error_m'] for row in target_errors) < .0003, target_errors
body.modifiers.remove(smooth)
body.vertex_groups.remove(group)
(out/'SavedTargetParity.json').write_text(json.dumps({'passed': True, 'source_sha256': gate['sha256'],
    'rows': target_errors, 'scope': 'Eight fresh saved-shape/pose samples versus localized smoothing target; not full motion acceptance.'}, indent=2), encoding='utf-8')
np.savez_compressed(out/'SourceSurfaces.npz', **surfaces)
(out/'SourceControls.json').write_text(json.dumps({'source_sha256': gate['sha256'],
    'action_sha256': manifest['sha256'], 'rows': rows}, indent=2), encoding='utf-8')
bpy.ops.object.select_all(action='DESELECT')
for ob in meshes+[rig]:
    ob.hide_set(False)
    ob.select_set(True)
bpy.context.view_layer.objects.active = rig
options = dict(use_selection=True, object_types={'MESH', 'ARMATURE'}, add_leaf_bones=False,
               use_mesh_modifiers=False, mesh_smooth_type='FACE', axis_forward='-Y', axis_up='Z')
animation = folder/'G1_ShoulderLocal_240Hz.fbx'
scene.frame_set(1)
bpy.ops.export_scene.fbx(filepath=str(animation), bake_anim=True, bake_anim_use_all_actions=False,
                        bake_anim_use_nla_strips=False, bake_anim_simplify_factor=0, bake_anim_step=.5, **options)
rig.animation_data_clear()
for bone in rig.pose.bones:
    bone.matrix_basis = Matrix.Identity(4)
for ob in meshes:
    if ob.data.shape_keys:
        ob.data.shape_keys.animation_data_clear()
        for key in ob.data.shape_keys.key_blocks:
            if key.name.startswith('REVIEW_'):
                key.value = 0
bpy.context.view_layer.update()
rest = folder/'Vexa_G1_ShoulderLocal_Rest.fbx'
bpy.ops.export_scene.fbx(filepath=str(rest), bake_anim=False, **options)
report = {'source': str(candidate), 'source_sha256': gate['sha256'],
          'action': str(source/manifest['file']), 'action_sha256': manifest['sha256'],
          'animation': str(animation), 'animation_sha256': hashlib.sha256(animation.read_bytes()).hexdigest(),
          'rest': str(rest), 'rest_sha256': hashlib.sha256(rest.read_bytes()).hexdigest(),
          'expected_morphs': expected, 'duration': manifest['seconds'], 'fps': 240, 'bones': 95,
          'scope': 'New private G1 mesh and paired animation; no production or prior proof overwrite.'}
assert hashlib.sha256(candidate.read_bytes()).hexdigest() == gate['sha256']
(out/'Export.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('G1_SHOULDER_EXPORTED', report['animation_sha256'], flush=True)
