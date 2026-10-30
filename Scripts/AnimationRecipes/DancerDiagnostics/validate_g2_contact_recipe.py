"""Re-run the G2 candidate's technical gates from preserved inputs.

Hidden Blender invocation only. Produces a receipt, never publishes a mesh,
changes the game, or asserts artistic/anatomical acceptance.
"""
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from g2_contact_recipe import G2ContactRecipe


def geometry(model):
    index = {name: i for i, name in enumerate(model.names)}
    meshes = []
    body = np.array([name.startswith(('spine_', 'neck_', 'head', 'pelvis', 'thigh_', 'calf_', 'foot_', 'ball_', 'toe_')) for name in model.names])
    arm = np.array([name.startswith(('lowerarm_', 'hand_', 'thumb_', 'index_', 'middle_', 'ring_', 'pinky_')) for name in model.names])
    for ob in model.scene.objects:
        if ob.type != 'MESH' or ob.hide_render:
            continue
        modifiers = [modifier for modifier in ob.modifiers if modifier.type == 'ARMATURE']
        states = [modifier.show_viewport for modifier in modifiers]
        try:
            for modifier in modifiers:
                modifier.show_viewport = False
            bpy.context.view_layer.update()
            evaluated = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
            evaluated.data.calc_loop_triangles()
            points = np.array([tuple(ob.matrix_world @ vertex.co) + (1,) for vertex in evaluated.data.vertices])
            triangles = np.array([triangle.vertices for triangle in evaluated.data.loop_triangles])
            assert len(points) == len(ob.data.vertices), ob.name
            joints = np.zeros((len(points), 12), dtype=np.int32)
            weights = np.zeros((len(points), 12))
            for vertex in ob.data.vertices:
                influences = [(index[ob.vertex_groups[group.group].name], group.weight) for group in vertex.groups if ob.vertex_groups[group.group].name in index and group.weight > 0]
                total = sum(weight for _, weight in influences)
                assert 0 < total and len(influences) <= 12, (ob.name, vertex.index)
                for slot, (joint, weight) in enumerate(influences):
                    joints[vertex.index, slot] = joint
                    weights[vertex.index, slot] = weight / total
            b = (weights * body[joints]).sum(axis=1) > 0.75
            a = (weights * arm[joints]).sum(axis=1) > 0.75
            meshes.append((ob.name, points, triangles, joints, weights, triangles[np.all(b[triangles], axis=1)], triangles[np.all(a[triangles], axis=1)]))
        finally:
            for modifier, state in zip(modifiers, states):
                modifier.show_viewport = state
    bpy.context.view_layer.update()
    return meshes


def skin(matrices, mesh):
    _, points, _, joints, weights, _, _ = mesh
    result = np.zeros((len(points), 3))
    for slot in range(12):
        result += np.einsum('vij,vj->vi', matrices[joints[:, slot]], points)[:, :3] * weights[:, slot, None]
    return result


def triangle_radii(points, triangles):
    a = points[triangles, :2]
    edge = np.roll(a, -1, axis=1) - a
    alpha = np.clip(-np.sum(a * edge, axis=2) / np.maximum(np.sum(edge * edge, axis=2), 1e-20), 0, 1)
    radius = np.linalg.norm(a + alpha[:, :, None] * edge, axis=2).min(axis=1)
    cross = edge[:, :, 0] * -a[:, :, 1] - edge[:, :, 1] * -a[:, :, 0]
    inside = np.all(cross >= -1e-12, axis=1) | np.all(cross <= 1e-12, axis=1)
    radius[inside] = 0
    return radius


def validate(model, meshes):
    inverse_rest = np.array([model.rest[name].inverted() for name in model.names])
    hinge = {}
    for side in ('l', 'r'):
        a, b, c = [model.rest[name + '_' + side] for name in ('upperarm', 'lowerarm', 'hand')]
        hinge[side] = a.to_quaternion().inverted() @ (b.translation - a.translation).cross(c.translation - b.translation).normalized()
    rows = []
    maximum_grip = maximum_child_local = 0.0
    maximum_radius = 0.0
    previous = None
    maximum_speed = maximum_angular = 0.0
    for frame in range(round(model.duration * model.export_fps) + 1):
        time = frame / model.export_fps
        pose = model.pose(time)
        base = model.base_loop(time)
        for side in ('l', 'r'):
            for parent, child in (('upperarm_', 'lowerarm_'), ('lowerarm_', 'hand_')):
                want = base[parent + side].inverted() @ base[child + side]
                got = pose[parent + side].inverted() @ pose[child + side]
                maximum_child_local = max(maximum_child_local, float(np.abs(np.array(want) - np.array(got)).max()))
        if model.approach_seconds <= time <= model.approach_seconds + model.motion_seconds:
            maximum_grip = max(maximum_grip, float(np.abs(np.array(pose['hand_r']) - np.array(model.target)).max()))
        matrices = np.array([pose[name] for name in model.names]) @ inverse_rest
        body_vertices = []; body_faces = []; arm_vertices = []; arm_faces = []
        pole = {}
        for mesh in meshes:
            name, _, triangles, _, _, body_triangles, arm_triangles = mesh
            points = skin(matrices, mesh)
            maximum_radius = max(maximum_radius, float(np.linalg.norm(points[:, :2], axis=1).max()))
            radius = triangle_radii(points, triangles)
            z = points[triangles, 2]
            bad = (radius < model.pole_radius_m - 0.00001) & (z.max(axis=1) > 0) & (z.min(axis=1) < 5)
            if bad.any():
                pole[name] = {'triangles': int(bad.sum()), 'penetration_mm': float((model.pole_radius_m - radius[bad]).max() * 1000)}
            if len(body_triangles):
                offset = len(body_vertices); body_vertices.extend(points.tolist()); body_faces.extend((body_triangles + offset).tolist())
            if len(arm_triangles):
                offset = len(arm_vertices); arm_vertices.extend(points.tolist()); arm_faces.extend((arm_triangles + offset).tolist())
        contacts = BVHTree.FromPolygons(body_vertices, body_faces, all_triangles=True).overlap(BVHTree.FromPolygons(arm_vertices, arm_faces, all_triangles=True))
        chest = pose['spine_05'].to_quaternion() @ model.rest['spine_05'].to_quaternion().inverted()
        up = chest @ Vector((0, 0, 1)); forward = chest @ Vector((0, -1, 0)); arms = []
        for side in ('l', 'r'):
            a, b, c = [pose[name + '_' + side] for name in ('upperarm', 'lowerarm', 'hand')]
            upper = (b.translation - a.translation).normalized(); lower = (c.translation - b.translation).normalized()
            axis = upper.cross(lower); flex = math.degrees(upper.angle(lower)); alignment = 1.0
            if axis.length > 0.1:
                alignment = (a.to_quaternion().inverted() @ axis.normalized()).dot(hinge[side])
            rear = math.degrees(math.asin(max(-1, min(1, -upper.dot(forward)))))
            limit = 10 if upper.dot(up) > 0 else 0
            arms.append({'side': side, 'reversal': alignment < 0 and flex > 10, 'rear_flag': rear > limit + 2})
        pelvis = pose['pelvis']
        if previous:
            maximum_speed = max(maximum_speed, (pelvis.translation - previous.translation).length * model.export_fps)
            maximum_angular = max(maximum_angular, math.degrees(2 * math.acos(min(1, abs(pelvis.to_quaternion().dot(previous.to_quaternion()))))) * model.export_fps)
        previous = pelvis.copy()
        if pole or contacts or any(arm['reversal'] or arm['rear_flag'] for arm in arms):
            rows.append({'time': time, 'pole': pole, 'body_triangle_pairs': len(contacts), 'arms': arms})
        if frame % 300 == 0:
            print('G2_RECIPE_CHECK', frame, len(rows), flush=True)
    start, end = model.pose(0), model.pose(model.duration)
    loop_error = max(float(np.abs(np.array(start[name]) - np.array(end[name])).max()) for name in model.names)
    summary = {'samples': round(model.duration * model.export_fps) + 1, 'flagged_samples': len(rows), 'maximum_grip_matrix_error': maximum_grip, 'maximum_child_local_matrix_error': maximum_child_local, 'loop_matrix_error': loop_error, 'maximum_radius_m': maximum_radius, 'maximum_speed_mps': maximum_speed, 'maximum_angular_dps': maximum_angular}
    ok = not rows and maximum_grip < 1e-5 and maximum_child_local < 0.001 and loop_error < 1e-6 and maximum_radius < 3.48
    model.assert_inputs_unchanged()
    return {'sources': model.hashes, 'recipe_sha256': hashlib.sha256(Path(__file__).with_name('g2_contact_recipe.py').read_bytes()).hexdigest(), 'summary': summary, 'flags': rows, 'ok': ok, 'limits': 'Technical sampled contact/arm checks only. Excludes adjacent shoulder/within-hand/garment contact and between-sample contacts. Does not establish full original G2, anatomy or artistic acceptance.'}


if __name__ == '__main__':
    project = Path(os.environ.get('SS_ANIMATION_PROJECT', str(Path.home() / 'SpaceSurvival'))).resolve()
    output = project / '.agent/local/AnimationReview_20261025/G2ClearContact'
    output.mkdir(parents=True, exist_ok=True)
    model = G2ContactRecipe(project)
    report = validate(model, geometry(model))
    (output / 'ConsolidatedAudit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('G2_RECIPE_RESULT', report['ok'], report['summary'], flush=True)
    assert report['ok'], report['summary']
