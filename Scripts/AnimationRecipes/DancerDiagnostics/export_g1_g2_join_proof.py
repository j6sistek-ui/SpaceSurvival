"""Export the saved G1/G2 bridge with paired shapes and local normal mask.

Build only in memory from hash-guarded sources. Eight additional morphs share
the preserved G1 mesh; no duplicate full-character Blender file is written.
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
source = project/'SourceAssets/DanceRefinement_20261025'
review = project/'.agent/local/AnimationReview_20261025'
out, folder = review/'G1G2JoinNative240', source/'G1G2JoinProof'
assert not out.exists() and not folder.exists(), 'Preserve previous native proof'
manifest = json.loads((source/'G1G2_Join_Manifest.json').read_text(encoding='utf-8'))
for receipt in (review/'G1G2JoinBoundary/Boundary.json', review/'G1G2JoinForwardReplay/Replay.json', review/'G1G2JoinForwardReplay/Surface.json'):
    assert json.loads(receipt.read_text(encoding='utf-8'))['passed']
guards = dict(manifest['sources'])
guards[str(source/manifest['file'])] = manifest['sha256']
guards[str(source/manifest['morph_basis'])] = manifest['morph_basis_sha256']
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in guards.items())
out.mkdir(); folder.mkdir()
candidate = source/'Vexa_G1_ShoulderCap_Candidate.blend'
bpy.ops.wm.open_mainfile(filepath=str(candidate), load_ui=False)
scene = bpy.context.scene
rig = next(ob for ob in scene.objects if ob.type == 'ARMATURE')
rig.name = 'root.001'
meshes = [ob for ob in scene.objects if ob.type == 'MESH' and not ob.hide_render]
assert len(rig.data.bones) == 95
body = bpy.data.objects['Vexa_Continuous_Hands']
for ob in meshes:
    if ob.data.shape_keys:
        ob.data.shape_keys.animation_data_clear()
        for key in list(ob.data.shape_keys.key_blocks)[1:]:
            if key.name.startswith('REVIEW_G1_LeftAxilla_'):
                key.value = 0
            elif key.name.startswith('REVIEW_'):
                assert key.mute or abs(key.value) < 1e-8
                ob.shape_key_remove(key)
keys = body.data.shape_keys
base = np.array([tuple(v.co) for v in keys.key_blocks[0].data])
basis = np.load(source/manifest['morph_basis'])
for name, delta in zip(manifest['new_morphs'], basis['deltas']):
    key = body.shape_key_add(name=name, from_mix=False)
    key.slider_min, key.slider_max = -10, 10
    coordinates = base.copy(); coordinates[basis['active']] += delta
    key.data.foreach_set('co', coordinates.ravel())
with bpy.data.libraries.load(str(source/manifest['file']), link=False) as (_, loaded):
    loaded.actions = [manifest['action'], manifest['shape_action']]
action, shape = loaded.actions
rig.animation_data.action = action; rig.animation_data.action_slot = action.slots[0]
keys.animation_data_create(); keys.animation_data.action = shape; keys.animation_data.action_slot = shape.slots[0]
scene.render.fps, scene.frame_start, scene.frame_end = 120, 1, 481
expected = [key.name for key in keys.key_blocks if key.name.startswith('REVIEW_')]
assert len(expected) == 104

mask, _ = shoulder_mask(body, [(rig.matrix_world@rig.data.bones['upperarm_l'].matrix_local).translation])
points = np.array([tuple(body.matrix_world@v.co) for v in body.data.vertices])
def step(a, b, x):
    t = np.clip((x-a)/(b-a), 0, 1)
    return t*t*(3-2*t)
mask *= step(.09, .14, points[:, 0])*step(1.15, 1.24, points[:, 2])
mask = np.clip(mask*4, 0, 1)
assert np.count_nonzero(mask) == 549
for ob in meshes:
    for attribute in list(ob.data.color_attributes):
        ob.data.color_attributes.remove(attribute)
    attribute = ob.data.color_attributes.new(name='G1ShoulderNormalMask', type='FLOAT_COLOR', domain='POINT')
    colors = np.zeros((len(ob.data.vertices), 4), dtype=np.float32); colors[:, 3] = 1
    if ob == body: colors[:, 1] = mask
    attribute.data.foreach_set('color', colors.ravel())
    ob.data.color_attributes.active_color_index = ob.data.color_attributes.render_color_index = 0

rows, surfaces = [], {}
for seconds in (0., .2, .75, 1.5, 2.25, 3., 3.7, 4.):
    frame = 1+seconds*120
    scene.frame_set(math.floor(frame), subframe=frame % 1); bpy.context.view_layer.update()
    label = f't{round(seconds*1000):05d}'
    rows.append({'label': label, 'seconds': seconds, 'bones_m': {b.name: list((rig.matrix_world@b.matrix).translation) for b in rig.pose.bones}})
    for ob in meshes:
        ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
        surfaces[label+'__'+ob.name] = np.array([tuple(ob.matrix_world@v.co) for v in ev.data.vertices])
np.savez_compressed(out/'SourceSurfaces.npz', **surfaces)
(out/'SourceControls.json').write_text(json.dumps({'source_sha256': guards[str(candidate)], 'action_sha256': manifest['sha256'], 'rows': rows}, indent=2), encoding='utf-8')
bpy.ops.object.select_all(action='DESELECT')
for ob in meshes+[rig]: ob.hide_set(False); ob.select_set(True)
bpy.context.view_layer.objects.active = rig
options = dict(use_selection=True, object_types={'MESH', 'ARMATURE'}, add_leaf_bones=False,
               use_mesh_modifiers=False, mesh_smooth_type='FACE', axis_forward='-Y', axis_up='Z', colors_type='LINEAR')
animation = folder/'G1G2_Join_240Hz.fbx'
scene.frame_set(1)
bpy.ops.export_scene.fbx(filepath=str(animation), bake_anim=True, bake_anim_use_all_actions=False,
                        bake_anim_use_nla_strips=False, bake_anim_simplify_factor=0, bake_anim_step=.5, **options)
rig.animation_data_clear()
for bone in rig.pose.bones: bone.matrix_basis = Matrix.Identity(4)
for ob in meshes:
    if ob.data.shape_keys:
        ob.data.shape_keys.animation_data_clear()
        for key in ob.data.shape_keys.key_blocks:
            if key.name.startswith('REVIEW_'): key.value = 0
bpy.context.view_layer.update()
rest = folder/'Vexa_G1G2_Join_Rest.fbx'
bpy.ops.export_scene.fbx(filepath=str(rest), bake_anim=False, **options)
report = {'source': str(candidate), 'source_sha256': guards[str(candidate)],
          'action': str(source/manifest['file']), 'action_sha256': manifest['sha256'],
          'animation': str(animation), 'animation_sha256': hashlib.sha256(animation.read_bytes()).hexdigest(),
          'rest': str(rest), 'rest_sha256': hashlib.sha256(rest.read_bytes()).hexdigest(),
          'expected_morphs': expected, 'duration': 4., 'fps': 240, 'bones': 95, 'sources': guards,
          'scope': 'New private bridge proof with local normal mask; no production or prior-proof overwrite.'}
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in guards.items())
(out/'Export.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('G1G2_JOIN_EXPORTED', report['animation_sha256'], flush=True)
