"""Read-only, hash-bound hand-contact review of the saved paced G2 action.

The owner liked the stills; this checks continuous contact/release before any
new hand edit. It does not turn a geometric screen into anatomy acceptance.
Run with -- --render after the audit for two opposing, hand-following views.
"""
import hashlib
import itertools
import json
import math
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE))
from g2_glute_follow_control import anchor_waist_weights
from validate_g2_contact_recipe import geometry, skin, triangle_radii

P = Path(os.environ.get('SS_ANIMATION_PROJECT', str(Path.home() / 'SpaceSurvival'))).resolve()
D = P / 'SourceAssets/DanceRefinement_20261025'
R = P / '.agent/local/AnimationReview_20261025'
O = R / 'G2GripMotion'
O.mkdir(exist_ok=True)
manifest = json.loads((D / 'G2_GluteFollow_Manifest.json').read_text())
source = D / 'Vexa_G2_PosteriorHip_Candidate.blend'
library = D / manifest['file']
guard = {str(source): manifest['mesh_sha256'], str(library): manifest['sha256']}
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in guard.items())
bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False)
s = bpy.context.scene
rig = next(o for o in s.objects if o.type == 'ARMATURE')
assert anchor_waist_weights(bpy.data.objects['Vexa_Continuous_Feet']) == manifest['weight_patch']
with bpy.data.libraries.load(str(library), link=False) as (_, loaded):
    loaded.actions = [manifest['action']]
rig.animation_data.action = loaded.actions[0]
rig.animation_data.action_slot = loaded.actions[0].slots[0]
for ob in s.objects:
    if ob.type == 'MESH' and ob.data.shape_keys:
        ob.data.shape_keys.animation_data_clear()
        for key in ob.data.shape_keys.key_blocks:
            if key.name.startswith(manifest['morph_mute_prefix']):
                key.value = 0
                key.mute = True
names = [b.name for b in sorted(rig.pose.bones, key=lambda b: len(b.parent_recursive))]
rest = {n: rig.matrix_world @ rig.data.bones[n].matrix_local for n in names}
inverse_rest = np.array([rest[n].inverted() for n in names])
hands = bpy.data.objects['Vexa_Continuous_Hands']
mesh = next(m for m in geometry(SimpleNamespace(names=names, scene=s)) if m[0] == hands.name)
_, _, triangles, joints, weights, _, _ = mesh
digits = ('thumb', 'index', 'middle', 'ring', 'pinky')
digit_masks = {f: (weights * np.array([n.startswith(f + '_') and n.endswith('_r') for n in names])[joints]).sum(axis=1) > .65 for f in digits}
faces = {f: triangles[np.all(mask[triangles], axis=1)] for f, mask in digit_masks.items()}
right = (weights * np.array([n.endswith('_r') for n in names])[joints]).sum(axis=1) > .95
right_triangles = triangles[np.all(right[triangles], axis=1)]
hand_core = (weights * np.array([n.endswith('_r') and n.startswith(('hand_', *[f + '_' for f in digits])) for n in names])[joints]).sum(axis=1) > .99999
pace = json.loads((R / 'G2PosteriorHip/PacedHipAction.json').read_text())


def source_time(seconds):
    return float((np.interp(1 + seconds * 60, pace['destination_frames'], pace['source_frames']) - 1) / 60)


def pose_at(seconds):
    frame = 1 + seconds * 60
    s.frame_set(math.floor(frame), subframe=frame % 1)
    bpy.context.view_layer.update()
    return {n: rig.matrix_world @ rig.pose.bones[n].matrix for n in names}


if '--arms' in sys.argv:
    rows = []
    for frame in range(manifest['frame_end']):
        seconds = frame / 60
        pose = pose_at(seconds)
        for side in ('l', 'r'):
            row = {'seconds': seconds, 'source_seconds': source_time(seconds), 'side': side}
            for parent, name, child in (('clavicle_', 'upperarm_', 'lowerarm_'), ('upperarm_', 'lowerarm_', 'hand_'), ('lowerarm_', 'hand_', 'middle_01_')):
                parent, name, child = parent + side, name + side, child + side
                rest_local = rest[parent].inverted() @ rest[name]
                local = pose[parent].inverted() @ pose[name]
                q = (rest_local.inverted() @ local).to_quaternion().normalized()
                if q.w < 0:
                    q.negate()
                axis = (rest[name].inverted().to_3x3() @ (rest[child].translation - rest[name].translation)).normalized()
                projection = axis * Vector((q.x, q.y, q.z)).dot(axis)
                twist = Quaternion((q.w, *projection)).normalized()
                row[name + '_twist_deg'] = math.degrees(2 * math.atan2(Vector((twist.x, twist.y, twist.z)).dot(axis), twist.w))
                row[name + '_swing_deg'] = math.degrees((q @ twist.inverted()).angle)
            a, b, c = [pose[n + side] for n in ('upperarm_', 'lowerarm_', 'hand_')]
            upper = (b.translation - a.translation).normalized()
            lower = (c.translation - b.translation).normalized()
            hand = ((pose['index_01_' + side].translation + pose['pinky_01_' + side].translation) * .5 - c.translation).normalized()
            row['elbow_bend_deg'] = math.degrees(upper.angle(lower))
            row['wrist_direction_deg'] = math.degrees(lower.angle(hand))
            rows.append(row)
    extremes = {}
    for side in ('l', 'r'):
        selected = [r for r in rows if r['side'] == side]
        extremes[side] = {key: {'min': min(selected, key=lambda r: r[key]), 'max': max(selected, key=lambda r: r[key])}
                          for key in selected[0] if key.endswith('_deg')}
    result = {'sources': guard, 'samples_per_side': manifest['frame_end'], 'extremes': extremes, 'rows': rows,
              'scope': 'Rest-relative local swing/twist and geometric elbow/wrist direction only. Not human joint limits or artistic acceptance; identifies poses for visual review.'}
    (O / 'ArmDirections.json').write_text(json.dumps(result, indent=2))
    print('ARM_DIRECTIONS', {side: {key: [round(v['min'][key], 3), round(v['max'][key], 3), round(v['min']['seconds'], 3), round(v['max']['seconds'], 3)] for key, v in data.items()} for side, data in extremes.items()}, flush=True)
elif not any(flag in sys.argv for flag in ('--render', '--labels', '--isolate', '--palm-proof')):
    rows = []
    held_reference = None
    held_drift = cpu_error = 0.
    for frame in range(manifest['frame_end']):
        seconds = frame / 60
        pose = pose_at(seconds)
        points = skin(np.array([pose[n] for n in names]) @ inverse_rest, mesh)
        if frame in (0, 600, 1200, 1800, manifest['frame_end'] - 1):
            ev = hands.evaluated_get(bpy.context.evaluated_depsgraph_get())
            actual = np.array([tuple(hands.matrix_world @ v.co) for v in ev.data.vertices])
            cpu_error = max(cpu_error, float(np.linalg.norm(actual - points, axis=1).max() * 1000))
        radius = triangle_radii(points, right_triangles)
        bvhs = {f: BVHTree.FromPolygons(points.tolist(), face.tolist(), all_triangles=True) for f, face in faces.items()}
        overlaps = {a + '/' + b: len(bvhs[a].overlap(bvhs[b])) for a, b in itertools.combinations(digits, 2)}
        overlaps = {k: v for k, v in overlaps.items() if v}
        st = source_time(seconds)
        held = 2.5 <= st <= 20.1666666667
        if held:
            if held_reference is None:
                held_reference = points[hand_core].copy()
            held_drift = max(held_drift, float(np.linalg.norm(points[hand_core] - held_reference, axis=1).max() * 1000))
        forearm = (pose['hand_r'].translation - pose['lowerarm_r'].translation).normalized()
        hand = ((pose['index_01_r'].translation + pose['pinky_01_r'].translation) * .5 - pose['hand_r'].translation).normalized()
        rows.append({'seconds': seconds, 'source_seconds': st, 'held': held,
                     'pole_gap_mm': float((radius.min() - .025) * 1000),
                     'wrist_direction_angle_degrees': math.degrees(forearm.angle(hand)),
                     'digit_intersections': overlaps})
        if frame % 600 == 0:
            print('G2_GRIP', frame, rows[-1], flush=True)
    report = {'source_sha256': guard, 'samples': len(rows), 'cpu_surface_error_mm': cpu_error,
              'held_hand_core_vertices': int(hand_core.sum()), 'held_surface_drift_mm': held_drift,
              'pole_flag_samples': sum(r['pole_gap_mm'] < -.01 for r in rows),
              'digit_flag_samples': sum(bool(r['digit_intersections']) for r in rows),
              'wrist_peak': max(rows, key=lambda r: r['wrist_direction_angle_degrees']),
              'rows': rows, 'scope': 'Right-hand triangle/pole and cross-digit intersections at60Hz. Direction angle is diagnostic, not a human motion limit. Excludes palm/digit junctions and between-frame intersections. No mesh/action changes.'}
    assert cpu_error < .01, cpu_error
    (O / 'MotionAudit.json').write_text(json.dumps(report, indent=2))
    print('G2_GRIP_RESULT', {k: v for k, v in report.items() if k != 'rows'}, flush=True)
else:
    audit = json.loads((O / 'MotionAudit.json').read_text())
    assert audit['source_sha256'] == guard
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=.025, depth=5, location=(0, 0, 2.5))
    pole = bpy.context.object
    pole.name = 'Diagnostic_OrangePole'
    pole.color = (1, .12, 0, 1)
    for ob in s.objects:
        if ob.type == 'MESH' and ob != pole:
            ob.color = (.55, .55, .55, 1)
    s.render.engine = 'BLENDER_WORKBENCH'
    s.display.shading.light = 'STUDIO'
    s.display.shading.color_type = 'OBJECT'
    s.display.shading.show_cavity = False
    s.display.shading.background_type = 'WORLD'
    s.world = bpy.data.worlds.new('GripMotionWorld')
    s.world.color = (.035, .045, .055)
    s.render.resolution_x = s.render.resolution_y = 512
    s.render.resolution_percentage = 100
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    s.camera = camera
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = .65
    palm_proof = '--palm-proof' in sys.argv
    labels = '--labels' in sys.argv or palm_proof
    isolated = '--isolate' in sys.argv
    if labels or isolated:
        for ob in s.objects:
            if ob.type == 'MESH' and ob not in (hands, pole):
                ob.hide_render = True
        s.display.shading.color_type = 'MATERIAL'
        colors = [('Neutral', (.55, .55, .55, 1)), ('Thumb_Cyan', (.0, .85, 1, 1)), ('Pinky_Violet', (.6, .08, .85, 1))]
        hands.data.materials.clear()
        for name, color in colors:
            material = bpy.data.materials.new(name)
            material.diffuse_color = color
            hands.data.materials.append(material)
        for face in hands.data.polygons:
            face.material_index = 1 if np.mean(digit_masks['thumb'][list(face.vertices)]) > .5 else 2 if np.mean(digit_masks['pinky'][list(face.vertices)]) > .5 else 0
        orange = bpy.data.materials.new('Pole_Orange')
        orange.diffuse_color = pole.color
        pole.data.materials.append(orange)
        if labels:
            s.render.resolution_x = s.render.resolution_y = 800
            camera.data.ortho_scale = .36
        if isolated:
            region = (weights * np.array([n.endswith('_r') and n.startswith(('lowerarm_', 'hand_', *[f + '_' for f in digits])) for n in names])[joints]).sum(axis=1) > .1
            group = hands.vertex_groups.new(name='REVIEW_VisibleForearmOnly')
            group.add(np.flatnonzero(region).tolist(), 1., 'REPLACE')
            mask = hands.modifiers.new('REVIEW_HideOccludingBody', 'MASK')
            mask.vertex_group = group.name
    frames = 1 if labels else round(manifest['seconds'] * 12) + 1
    for i in range(frames):
        time = float((np.interp(1 + 12.4 * 60, pace['source_frames'], pace['destination_frames']) - 1) / 60) if labels else min(i / 12, manifest['seconds'])
        pose = pose_at(time)
        if palm_proof:
            # Right-hand chirality: distal cross (index minus little) is dorsal.
            # Derive from rest landmarks, then carry with the current hand so
            # curled fingers cannot change the meaning of the palm normal.
            along = (rest['middle_01_r'].translation - rest['hand_r'].translation).normalized()
            width = (rest['index_01_r'].translation - rest['pinky_01_r'].translation).normalized()
            transport = (pose['hand_r'] @ rest['hand_r'].inverted()).to_3x3()
            assert transport.determinant() > 0, 'Mirrored hand transform'
            palmar = (transport @ -along.cross(width).normalized()).normalized()
            distal = (transport @ along).normalized()
            center = pose['hand_r'].translation + distal * .035
            folder = O / 'PalmProof'
            folder.mkdir(exist_ok=True)
            hand_matrix = pose['hand_r'].copy()
            basis = {bone.name: bone.matrix_basis.copy() for bone in rig.pose.bones}
            rig.animation_data.action = None
            for bone in rig.pose.bones:
                bone.matrix_basis = basis[bone.name]
            bpy.context.view_layer.update()
            index_closed = (rig.matrix_world @ rig.pose.bones['index_03_r'].matrix).translation.copy()
            for state in ('closed', 'open_reference'):
                if state == 'open_reference':
                    for bone in rig.pose.bones:
                        if bone.name.endswith('_r') and bone.name.startswith(tuple(f + '_' for f in digits)):
                            bone.matrix_basis = Matrix.Identity(4)
                    bpy.context.view_layer.update()
                    pole.hide_render = True
                for view, direction in (('palm', palmar), ('back_of_hand', -palmar)):
                    camera.location = center + direction * 3
                    camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
                    s.render.filepath = str(folder / f'{state}_{view}.png')
                    bpy.ops.render.render(write_still=True)
            current_hand = rig.matrix_world @ rig.pose.bones['hand_r'].matrix
            error = max(abs(current_hand[a][b] - hand_matrix[a][b]) for a in range(4) for b in range(4))
            assert error < 1e-6, error
            index_open = (rig.matrix_world @ rig.pose.bones['index_03_r'].matrix).translation
            finger_open_delta = (index_open - index_closed).length
            assert finger_open_delta > .02, finger_open_delta
            (folder / 'Orientation.json').write_text(json.dumps({
                'sources': guard, 'source_seconds': 12.4, 'paced_seconds': time,
                'palmar_world': list(palmar), 'distal_world': list(distal),
                'colors': {'thumb': 'cyan', 'pinky': 'violet'},
                'hand_matrix_change_open_reference': error,
                'index_distal_movement_open_reference_m': finger_open_delta,
                'scope': 'Right hand. Open reference changes only digit locals, hides pole, and keeps wrist orientation. No asset saved. Camera front/back names in earlier captures were not anatomical labels.'}, indent=2))
            continue
        center = pose['hand_r'].translation.lerp(pose['lowerarm_r'].translation, .25)
        if labels:
            center = Vector((0, 0, 3))
        views = [('front', Vector((3, -5, 1.2))), ('back', Vector((-3, 5, .7)))]
        if labels:
            views.append(('above', Vector((.2, -.3, 3))))
        for view, direction in views:
            folder = O / ('Labelled' if labels else 'Isolated/' + view if isolated else view)
            folder.mkdir(parents=True, exist_ok=True)
            camera.location = center + direction.normalized() * 3
            camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
            s.render.filepath = str(folder / (f'grip_{view}.png' if labels else f'grip_{i:04d}.png'))
            bpy.ops.render.render(write_still=True)
    if labels and not palm_proof:
        (O / 'Labelled/Orientation.json').write_text(json.dumps({'sources': guard, 'source_seconds': 12.4, 'paced_seconds': time, 'colors': {'thumb': 'cyan', 'pinky': 'violet'}, 'world_m': {n: list(pose[n].translation) for n in ('hand_r', 'thumb_01_r', 'thumb_03_r', 'index_01_r', 'pinky_01_r')}, 'index_minus_pinky_height_mm': (pose['index_01_r'].translation.z - pose['pinky_01_r'].translation.z) * 1000}, indent=2))
    elif not palm_proof:
        (O / ('Isolated/Render.json' if isolated else 'Render.json')).write_text(json.dumps({'sources': guard, 'frames_per_view': frames, 'fps': 12, 'views': ['front', 'back'], 'duration': manifest['seconds'], 'isolated_forearm_only': isolated}, indent=2))
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in guard.items())
