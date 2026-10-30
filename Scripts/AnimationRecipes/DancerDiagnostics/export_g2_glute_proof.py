"""Copy-only native transfer and matched garment views of the saved G2 candidate."""
import bpy
import hashlib
import json
import math
import os
import sys
from pathlib import Path
import numpy as np
from mathutils import Matrix, Vector

CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE))
from g2_glute_follow_control import anchor_waist_weights

P = Path(os.environ.get('SS_ANIMATION_PROJECT', str(Path.home() / 'SpaceSurvival'))).resolve()
D = P / 'SourceAssets/DanceRefinement_20261025'
O = P / '.agent/local/AnimationReview_20261025/G2GluteFollowNative'
O.mkdir(exist_ok=True)
source = D / 'Vexa_G2_PosteriorHip_Candidate.blend'
manifest = json.loads((D / 'G2_GluteFollow_Manifest.json').read_text(encoding='utf-8'))
library = D / manifest['file']
reload = json.loads((O.parent / 'G2PosteriorHip/GluteFollowReload.json').read_text())
assert reload['passed'] and reload['action_sha256'] == manifest['sha256']
assert hashlib.sha256(source.read_bytes()).hexdigest() == manifest['mesh_sha256']
assert hashlib.sha256(library.read_bytes()).hexdigest() == manifest['sha256']
assert hashlib.sha256((CODE / 'g2_glute_follow_control.py').read_bytes()).hexdigest() == manifest['control_sha256']
folder = D / 'G2GluteFollowProof'
assert not folder.exists(), 'Preserve prior export'
folder.mkdir()
bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False)
s = bpy.context.scene
rig = next(o for o in s.objects if o.type == 'ARMATURE')
rig.name = 'root.001'
assert anchor_waist_weights(bpy.data.objects['Vexa_Continuous_Feet']) == manifest['weight_patch']
with bpy.data.libraries.load(str(library), link=False) as (_, loaded):
    loaded.actions = [manifest['action']]
action = loaded.actions[0]
assert action
rig.animation_data.action = action
rig.animation_data.action_slot = action.slots[0]
s.frame_start = 1
s.frame_end = manifest['frame_end']
s.render.fps = 60
meshes = [o for o in s.objects if o.type == 'MESH' and not o.hide_render]
removed = []
for ob in meshes:
    keys = ob.data.shape_keys
    if not keys:
        continue
    if keys.animation_data:
        assert not keys.animation_data.drivers and not keys.animation_data.nla_tracks
        a = keys.animation_data.action
        curves = [fc for layer in a.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves] if a else []
        assert all(fc.data_path.startswith('key_blocks["REVIEW_G2_') for fc in curves)
        keys.animation_data_clear()
    for key in list(keys.key_blocks):
        if key.name.startswith(manifest['morph_mute_prefix']):
            removed.append(ob.name + ':' + key.name)
            key.value = 0
            ob.shape_key_remove(key)
    assert all(k.mute or abs(k.value) < 1e-8 for k in keys.key_blocks[1:]), 'Unexpected static shape mix'

pace = json.loads((O.parent / 'G2PosteriorHip/PacedHipAction.json').read_text())
rows = []
surfaces = {}
for t in (0., 7.1, 7.6, 12.4, 13.5, 18., 26., 30.6666666667):
    frame = float(np.interp(1 + 60*t, pace['source_frames'], pace['destination_frames']))
    s.frame_set(math.floor(frame), subframe=frame % 1)
    bpy.context.view_layer.update()
    label = f't{round(t*100):04d}'
    rows.append({'label': label, 'source_seconds': t, 'seconds': (frame-1)/60,
                 'bones_m': {b.name: list((rig.matrix_world @ b.matrix).translation) for b in rig.pose.bones}})
    for ob in meshes:
        ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
        surfaces[label + '__' + ob.name] = np.array([tuple(ob.matrix_world @ v.co) for v in ev.data.vertices])
np.savez_compressed(O / 'SourceSurfaces.npz', **surfaces)
(O / 'SourceControls.json').write_text(json.dumps({'source_sha256': manifest['mesh_sha256'], 'action_sha256': manifest['sha256'], 'rows': rows}, indent=2))

bpy.ops.object.select_all(action='DESELECT')
for ob in meshes + [rig]:
    ob.hide_set(False)
    ob.select_set(True)
bpy.context.view_layer.objects.active = rig
options = dict(use_selection=True, add_leaf_bones=False, use_mesh_modifiers=False,
               mesh_smooth_type='FACE', axis_forward='-Y', axis_up='Z')
animation = folder / 'G2_GluteFollow.fbx'
s.frame_set(1)
bpy.ops.export_scene.fbx(filepath=str(animation), object_types={'ARMATURE'}, bake_anim=True,
                        bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                        bake_anim_simplify_factor=0, bake_anim_step=.5, **options)
rig.animation_data_clear()
for b in rig.pose.bones:
    b.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()
rest = folder / 'Vexa_G2_GluteFollow_Rest.fbx'
bpy.ops.export_scene.fbx(filepath=str(rest), object_types={'MESH', 'ARMATURE'}, bake_anim=False, **options)
report = {'source': str(source), 'source_sha256': manifest['mesh_sha256'],
          'action': str(library), 'action_sha256': manifest['sha256'],
          'animation': str(animation), 'animation_sha256': hashlib.sha256(animation.read_bytes()).hexdigest(),
          'rest': str(rest), 'rest_sha256': hashlib.sha256(rest.read_bytes()).hexdigest(),
          'expected_morphs': [], 'removed_inactive_morphs': removed,
          'duration': manifest['seconds'], 'fps': 120, 'bones': len(rig.data.bones),
          'weight_patch_vertices': len(manifest['weight_patch']['changes']),
          'scope': 'Private saved-action and paired weight-patch transfer; no native or garment acceptance.'}
(O / 'Export.json').write_text(json.dumps(report, indent=2))

# Saved-action closeups, using the same meshes to expose garment follow errors.
rig.animation_data_create()
rig.animation_data.action = action
rig.animation_data.action_slot = action.slots[0]
s.render.engine = 'BLENDER_WORKBENCH'
s.display.shading.light = 'STUDIO'
s.display.shading.color_type = 'OBJECT'
s.display.shading.show_cavity = False
s.display.shading.background_type = 'WORLD'
s.world = bpy.data.worlds.new('GluteFollowGarmentReview')
s.world.color = (.035, .045, .055)
for ob in meshes:
    ob.color = (.55, .55, .55, 1)
s.render.resolution_x = s.render.resolution_y = 900
s.render.resolution_percentage = 100
bpy.ops.object.camera_add()
camera = bpy.context.object
s.camera = camera
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 1.1
views = O / 'GarmentViews'
views.mkdir(exist_ok=True)
rest_pelvis = rig.matrix_world @ rig.data.bones['pelvis'].matrix_local
for row in rows[1:-1]:
    frame = 1 + row['seconds'] * 60
    s.frame_set(math.floor(frame), subframe=frame % 1)
    bpy.context.view_layer.update()
    pelvis = rig.matrix_world @ rig.pose.bones['pelvis'].matrix
    rotation = pelvis.to_quaternion() @ rest_pelvis.to_quaternion().inverted()
    for clothing in (True, False):
        for name in ('Vexa_Top', 'Vexa_Bottom'):
            bpy.data.objects[name].hide_render = not clothing
        for name, direction in [('rear', Vector((0, 5, .25))), ('quarter', Vector((3, 5, .25)))]:
            camera.location = pelvis.translation + rotation @ direction
            camera.rotation_euler = (pelvis.translation-camera.location).to_track_quat('-Z', 'Y').to_euler()
            s.render.filepath = str(views / f'{row["label"]}_{"dressed" if clothing else "body"}_{name}.png')
            bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest() == manifest['mesh_sha256']
assert hashlib.sha256(library.read_bytes()).hexdigest() == manifest['sha256']
print('G2_GLUTE_EXPORTED', json.dumps(report), flush=True)
