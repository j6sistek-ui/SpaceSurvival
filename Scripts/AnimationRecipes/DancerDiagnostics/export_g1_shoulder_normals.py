"""Export a separate rest mesh with a localized tangent-recompute mask.

No skin, geometry, morph or saved source edits. Green is the native blend mask;
all other mesh parts stay black so their original tangent treatment survives.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shoulder_support import shoulder_mask

project = Path(os.environ.get('SS_ANIMATION_PROJECT', str(Path.home()/'SpaceSurvival'))).resolve()
out = project/'.agent/local/AnimationReview_20261025/G1ShoulderCapNative240'
contract = json.loads((out/'Export.json').read_text())
source = Path(contract['source'])
assert hashlib.sha256(source.read_bytes()).hexdigest() == contract['source_sha256']
destination = Path(contract['rest']).with_name('Vexa_G1_Shoulder_LocalNormals_Rest.fbx')
assert not destination.exists(), 'Preserve previous masked export'
bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False)
rig = next(ob for ob in bpy.context.scene.objects if ob.type == 'ARMATURE')
rig.name = 'root.001'
rig.animation_data_clear()
for bone in rig.pose.bones:
    bone.matrix_basis = Matrix.Identity(4)
meshes = [ob for ob in bpy.context.scene.objects if ob.type == 'MESH' and not ob.hide_render]
body = bpy.data.objects['Vexa_Continuous_Hands']
mask, _ = shoulder_mask(body, [(rig.matrix_world@rig.data.bones['upperarm_l'].matrix_local).translation])
points = np.array([tuple(body.matrix_world@v.co) for v in body.data.vertices])

def step(a, b, x):
    v = np.clip((x-a)/(b-a), 0, 1)
    return v*v*(3-2*v)

mask *= step(.09, .14, points[:, 0])*step(1.15, 1.24, points[:, 2])
mask = np.clip(mask*4, 0, 1)
assert int(np.count_nonzero(mask)) == 549
expected = []
for ob in meshes:
    if ob.data.shape_keys:
        ob.data.shape_keys.animation_data_clear()
        for key in list(ob.data.shape_keys.key_blocks)[1:]:
            if key.name.startswith('REVIEW_G1_LeftAxilla_'):
                expected.append(key.name)
                key.value = 0
            elif key.name.startswith('REVIEW_'):
                assert key.mute or abs(key.value) < 1e-8
                ob.shape_key_remove(key)
    for attribute in list(ob.data.color_attributes):
        ob.data.color_attributes.remove(attribute)
    colors = ob.data.color_attributes.new(name='G1ShoulderNormalMask', type='FLOAT_COLOR', domain='POINT')
    values = np.zeros((len(ob.data.vertices), 4), dtype=np.float32)
    values[:, 3] = 1
    if ob == body:
        values[:, 1] = mask
    colors.data.foreach_set('color', values.ravel())
    ob.data.color_attributes.active_color_index = 0
    ob.data.color_attributes.render_color_index = 0
assert set(expected) == set(contract['expected_morphs'])
bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
for ob in meshes+[rig]:
    ob.hide_set(False)
    ob.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.fbx(filepath=str(destination), use_selection=True, object_types={'MESH', 'ARMATURE'},
    add_leaf_bones=False, use_mesh_modifiers=False, mesh_smooth_type='FACE', axis_forward='-Y', axis_up='Z',
    bake_anim=False, colors_type='LINEAR')
report = {'source_sha256': contract['source_sha256'], 'rest': str(destination),
          'rest_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
          'body_vertices': len(mask), 'masked_vertices': int(np.count_nonzero(mask)),
          'expected_morphs': expected, 'scope': 'Green shoulder mask only; geometry, skin and source unchanged.'}
assert hashlib.sha256(source.read_bytes()).hexdigest() == contract['source_sha256']
(out/'LocalNormalsExport.json').write_text(json.dumps(report, indent=2))
print('G1_LOCAL_NORMALS_EXPORT', report['rest_sha256'], flush=True)
