"""Copy-only G2 glute control; use only on the hash-guarded aa7da985 source.

No generic rig calibration: a 30% swing follow with its waist border anchored.
The caller must still validate full motion, garments, silhouette and export.
"""
from collections import Counter
import numpy as np
from mathutils import Matrix, Vector, Quaternion


def anchor_waist_weights(ob):
    rest = np.array([tuple(ob.matrix_world @ v.co) for v in ob.data.vertices])
    ob.data.calc_loop_triangles()
    triangles = [t.vertices for t in ob.data.loop_triangles]
    edges = Counter(tuple(sorted((int(a), int(b)))) for face in triangles
                    for a, b in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])))
    border = sorted({v for edge, count in edges.items() if count == 1
                     for v in edge if rest[v, 2] > .90})
    assert len(border) == 48 and min(rest[border, 2]) > 1.0, 'Unexpected waist topology'
    distance = np.linalg.norm(rest[:, None, :] - rest[border][None, :, :], axis=2).min(axis=1)
    x = np.clip(distance / .08, 0, 1)
    mask = x * x * (3 - 2 * x)
    changes = []
    for vertex in ob.data.vertices:
        before = {ob.vertex_groups[g.group].name: g.weight for g in vertex.groups}
        after = dict(before)
        moved = 0.
        for name in ('glute_l', 'glute_r'):
            weight = before.get(name, 0.)
            if weight and mask[vertex.index] < 1:
                after[name] = weight * mask[vertex.index]
                moved += weight - after[name]
        if moved:
            after['pelvis'] = before.get('pelvis', 0.) + moved
            assert abs(sum(before.values()) - sum(after.values())) < 1e-6
            for name in ('glute_l', 'glute_r', 'pelvis'):
                if name in after:
                    ob.vertex_groups[name].add([vertex.index], after[name], 'REPLACE')
            changes.append({'vertex': vertex.index, 'before': before, 'after': after})
    assert len(changes) == 116, 'Unexpected weight patch extent'
    return {'border': border, 'falloff_m': .08, 'changes': changes}


def glute_follow_pose(pose, rest, amount=.30):
    body = pose['pelvis'] @ rest['pelvis'].inverted()
    result = {name: matrix.copy() for name, matrix in pose.items()}
    for side in ('l', 'r'):
        name = 'glute_' + side
        assert np.abs(np.array(pose[name]) - np.array(body @ rest[name])).max() < 1e-5
        q = (body.inverted() @ pose['thigh_' + side] @ rest['thigh_' + side].inverted()).to_quaternion()
        if q.w < 0:
            q.negate()
        axis = (rest['calf_' + side].translation - rest['thigh_' + side].translation).normalized()
        vector = Vector((q.x, q.y, q.z))
        project = axis * vector.dot(axis)
        twist = Quaternion((q.w, *project))
        twist.normalize()
        swing = q @ twist.inverted()
        swing.normalize()
        part = Quaternion().slerp(swing, amount)
        pivot = rest['thigh_' + side].translation
        result[name] = body @ Matrix.Translation(pivot) @ part.to_matrix().to_4x4() @ Matrix.Translation(-pivot) @ rest[name]
    return result
