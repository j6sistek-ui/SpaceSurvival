"""Unsaved forward-reach shoulder controls; preserve the held arm and neck.

Compare clavicle protraction separately from weights and volume preservation.
Angles are diagnostic settings, not a claim about universal human limits.
"""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from g1_palmar_motion_control import G1PalmarControl

model = G1PalmarControl(False, True, True, True)
scene = model.scene
cap_control = '--cap-control' in sys.argv
smooth_control = '--smooth-control' in sys.argv or cap_control
output = model.review / ('G1ShoulderCapControl' if cap_control else 'G1ShoulderForwardSmooth' if smooth_control else 'G1ShoulderForward')
output.mkdir(exist_ok=True)
body = bpy.data.objects['Vexa_Continuous_Hands']
top = bpy.data.objects['Vexa_Top']
arm = next(m for m in body.modifiers if m.type == 'ARMATURE')
corrective = None
if smooth_control:
    from shoulder_support import shoulder_mask
    mask, _ = shoulder_mask(body, [model.rest['upperarm_l'].translation])
    points = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
    def step(a, b, x):
        t = np.clip((x-a)/(b-a), 0, 1)
        return t*t*(3-2*t)
    cap_mask = mask*step(.09, .14, points[:, 0])*step(1.15, 1.24, points[:, 2])
    mask = cap_mask*(1-step(1.44, 1.49, points[:, 2]))
    group = body.vertex_groups.new(name='REVIEW_G1_LeftAxilla')
    for i, value in enumerate(mask):
        if value > 0:
            group.add([i], float(value), 'REPLACE')
    corrective = body.modifiers.new('REVIEW_G1_LeftAxilla', 'CORRECTIVE_SMOOTH')
    corrective.vertex_group = group.name
    corrective.factor, corrective.iterations = .5, 8
    corrective.rest_source = 'ORCO'
    corrective.use_pin_boundary = True
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (.55, .55, .55)
scene.display.shading.show_cavity = False
scene.display.shading.background_type = 'WORLD'
scene.world = bpy.data.worlds.new('ForwardShoulderWorld')
scene.world.color = (.035, .045, .055)
scene.render.resolution_x = scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
for ob in scene.objects:
    if ob.type == 'MESH':
        ob.hide_render = ob not in (body, top)
bpy.ops.object.camera_add()
camera = bpy.context.object
scene.camera = camera
camera.data.type = 'ORTHO'
camera.data.ortho_scale = .72
rows = []
for seconds in ((3., 7.254899317387129, 8.4166667) if cap_control else (3., 8.4166667)):
    original, _, phase = model.pose(seconds)
    chest = original['spine_05'] @ model.rest['spine_05'].inverted()
    rotation = chest.to_quaternion()
    rest_axis = model.rest['lowerarm_l'].translation-model.rest['upperarm_l'].translation
    live_axis = original['lowerarm_l'].translation-original['upperarm_l'].translation
    expected = (rotation @ rest_axis).rotation_difference(live_axis) @ rotation @ model.rest['upperarm_l'].to_quaternion()
    roll = expected.rotation_difference(original['upperarm_l'].to_quaternion())
    if roll.w < 0:
        roll.negate()
    axis = rotation.inverted() @ live_axis.normalized()
    forward_angle = math.degrees(math.atan2(-axis.y, axis.x))
    variants = (('baseline', 0, False), ('protract10', 10, False),
                ('protract20', 20, False), ('volume_control', 0, True))
    if smooth_control:
        variants = (('baseline', 0, False), ('local_smooth', 0, False), ('protract10_smooth', 10, False))
    if cap_control:
        variants = (('baseline', 0, False), ('local_smooth', 0, False), ('cap_smooth', 0, False))
    for label, degrees, dq in variants:
        pose = {n: m.copy() for n, m in original.items()}
        if degrees:
            clavicle = pose['clavicle_l']
            pivot = clavicle.translation.copy()
            q = Quaternion(rotation @ Vector((0, 0, -1)), math.radians(degrees))
            pose['clavicle_l'] = Matrix.LocRotScale(pivot, q @ clavicle.to_quaternion(), clavicle.to_scale())
            shift = q @ (pose['upperarm_l'].translation-pivot) + pivot-pose['upperarm_l'].translation
            for name in model.descendants['upperarm_l']:
                pose[name].translation += shift
        else:
            shift = Vector()
        model.apply(pose)
        arm.use_deform_preserve_volume = dq
        if corrective:
            corrective.show_render = corrective.show_viewport = label != 'baseline'
            if cap_control:
                for i, value in enumerate(cap_mask if label == 'cap_smooth' else mask):
                    group.add([i], float(value), 'REPLACE')
        bpy.context.view_layer.update()
        rows.append({'seconds': seconds, 'variant': label, 'clavicle_forward_degrees': degrees,
                     'upper_arm_forward_angle': forward_angle,
                     'chest_relative_arm_direction': list(axis),
                     'upper_arm_axial_residual_degrees': math.degrees(roll.angle),
                     'free_arm_translation_m': shift.length,
                     'held_arm_unchanged': all(pose[n] == original[n] for n in model.descendants['upperarm_r'])})
        center = original['upperarm_l'].translation*.5+original['spine_05'].translation*.5
        for view, delta in (('front', Vector((.9, -3, .35))),
                            ('back', Vector((.9, 3, .35))),
                            ('side', Vector((3, -.7, .25)))):
            camera.location = center+rotation @ delta
            camera.rotation_euler = (rotation @ (-delta).to_track_quat('-Z', 'Y')).to_euler()
            scene.render.filepath = str(output / f't{seconds:.3f}_{label}_{view}.png')
            bpy.ops.render.render(write_still=True)
model.assert_guards()
(output/'Report.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
print('FORWARD_SHOULDER_CONTROLS_DONE', flush=True)
