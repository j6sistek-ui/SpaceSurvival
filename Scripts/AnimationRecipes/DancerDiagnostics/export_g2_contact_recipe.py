"""Bake a new private action only from the exact recipe that passed its gates."""
import hashlib
import json
import os
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from g2_contact_recipe import G2ContactRecipe

project = Path(os.environ.get('SS_ANIMATION_PROJECT', str(Path.home() / 'SpaceSurvival'))).resolve()
output = project / '.agent/local/AnimationReview_20261025/G2ClearContact'
destination = project / 'SourceAssets/DanceRefinement_20261025/G2_ClearContact_ActionLibrary.blend'
fbx = destination.parent / 'GBSupportedRelease/G2_ClearContact.fbx'
assert not destination.exists() and not fbx.exists(), 'Preserve existing candidate; choose a deliberate new identity before rerunning.'
receipt = json.loads((output / 'ConsolidatedAudit.json').read_text(encoding='utf-8'))
recipe_sha = hashlib.sha256(Path(__file__).with_name('g2_contact_recipe.py').read_bytes()).hexdigest()
assert receipt['ok'] and receipt['recipe_sha256'] == recipe_sha
model = G2ContactRecipe(project)
assert receipt['sources'] == model.hashes
action = bpy.data.actions.new('A_F3_G2_ClearContact_Candidate')
action.use_fake_user = True
model.rig.animation_data_create()
model.rig.animation_data.action = action
count = round(model.duration * model.export_fps) + 1
model.scene.render.fps = model.export_fps
model.scene.frame_start = 1
model.scene.frame_end = count
previous = {}; expected = {}
for frame in range(1, count + 1):
    pose = model.pose((frame - 1) / model.export_fps)
    model.apply(pose)
    for bone in model.ordered:
        bone.rotation_mode = 'QUATERNION'
        rotation = bone.rotation_quaternion.copy()
        if bone.name in previous and rotation.dot(previous[bone.name]) < 0:
            rotation.negate()
            bone.rotation_quaternion = rotation
        previous[bone.name] = rotation.copy()
        for prop in ('location', 'rotation_quaternion', 'scale'):
            bone.keyframe_insert(prop, frame=frame, group=bone.name)
    if (frame - 1) % 230 == 0:
        expected[str(frame)] = {name: [list(row) for row in pose[name]] for name in model.names}
for layer in action.layers:
    for strip in layer.strips:
        for bag in strip.channelbags:
            for curve in bag.fcurves:
                for key in curve.keyframe_points:
                    key.interpolation = 'LINEAR'
action['source_frames'] = 'G2 570-770; source preserved; 20percent playback plus explicit approach, release and return'
action['recipe_sha256'] = recipe_sha
action['quality_state'] = 'Sampled contact/arm gates passed; full original routine, anatomy and artistic acceptance remain open'
bpy.data.libraries.write(str(destination), {action}, fake_user=True, compress=True)
model.rig.name = 'root.001'
bpy.ops.object.select_all(action='DESELECT')
model.rig.select_set(True)
bpy.context.view_layer.objects.active = model.rig
fbx.parent.mkdir(exist_ok=True)
bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, object_types={'ARMATURE'}, add_leaf_bones=False, bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False, bake_anim_simplify_factor=0, axis_forward='-Y', axis_up='Z')
report = {'sources': model.hashes, 'recipe_sha256': recipe_sha, 'source_frames': [570, 770], 'frames': [1, count], 'fps': model.export_fps, 'seconds': model.duration, 'action': action.name, 'file': str(destination), 'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(), 'fbx': str(fbx), 'fbx_sha256': hashlib.sha256(fbx.read_bytes()).hexdigest(), 'expected_bones': expected, 'scope': action['quality_state']}
(output / 'Export.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
model.assert_inputs_unchanged()
print('G2_CONTACT_EXPORTED', report['sha256'], flush=True)
