"""Reproducible Vexa G2 contact candidate, without experimental-script imports.

Run in the installed Blender Python. Required private inputs are the preserved
hand-isolation mesh and selected-passage animation library, plus the versioned
right-hand calibration. No input file is saved or modified by this module.
This selected source passage is not the full original G2 animation.
"""
import hashlib
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

from load_supported_grip import load_supported_grip


def smooth(value):
    value = max(0.0, min(1.0, value))
    return value ** 3 * (10 - 15 * value + 6 * value ** 2)


def window(time, begin, full, leave, end):
    return smooth((time - begin) / (full - begin)) * (1 - smooth((time - leave) / (end - leave)))


class G2ContactRecipe:
    """Forward kinematics with bounded shoulder swings and explicit contact phases."""

    source_begin = 570
    source_end = 770
    source_samples_begin = 525
    source_fps = 60
    playback_rate = 0.2
    export_fps = 60
    approach_seconds = 2.5
    release_seconds = 2.5
    velocity_ramp_seconds = 1.0
    return_seconds = 8.0
    pole_radius_m = 0.025

    def __init__(self, project):
        self.project = Path(project).resolve()
        assert (self.project / 'SpaceSurvival.uproject').is_file()
        source = self.project / 'SourceAssets/DanceRefinement_20261025'
        mesh_file = source / 'Vexa_HandIsolation_Proof.blend'
        action_file = source / 'GB_SelectedPassages_ActionLibrary.blend'
        self.hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (mesh_file, action_file)}
        fit = load_supported_grip(self.hashes)
        self.target = Matrix(fit['hand_world_matrix'])
        self.fingers = {name: Matrix(value) for name, value in fit['finger_local_matrices'].items()}
        bpy.ops.wm.open_mainfile(filepath=str(mesh_file), load_ui=False)
        self.scene = bpy.context.scene
        self.rig = next(ob for ob in self.scene.objects if ob.type == 'ARMATURE')
        for ob in self.scene.objects:
            if ob.type == 'MESH' and ob.data.shape_keys:
                ob.data.shape_keys.animation_data_clear()
                for key in ob.data.shape_keys.key_blocks:
                    if key.name.startswith('REVIEW_'):
                        key.value = 0
        self.ordered = sorted(self.rig.pose.bones, key=lambda bone: len(bone.parent_recursive))
        self.names = [bone.name for bone in self.ordered]
        self.rest = {bone.name: self.rig.matrix_world @ bone.bone.matrix_local for bone in self.ordered}
        self.parent = {bone.name: bone.parent.name if bone.parent else None for bone in self.ordered}
        self.relative = {name: self.rest[self.parent[name]].inverted() @ matrix if self.parent[name] else matrix.copy() for name, matrix in self.rest.items()}
        self.descendants = {bone.name: [bone.name] + [child.name for child in bone.children_recursive] for bone in self.ordered}
        with bpy.data.libraries.load(str(action_file), link=False) as (_, target):
            target.actions = ['A_F3_TwoPassages_g2']
        action = target.actions[0]
        assert action and len(action.slots) == 1
        self.rig.animation_data_create()
        self.rig.animation_data.action = action
        self.rig.animation_data.action_slot = action.slots[0]
        self.local_samples = []
        for frame in range(self.source_samples_begin, self.source_end + 1):
            self.scene.frame_set(frame)
            bpy.context.view_layer.update()
            pose = {bone.name: (self.rig.matrix_world @ bone.matrix).copy() for bone in self.ordered}
            self.local_samples.append(self.locals_of(pose))
        self.rig.animation_data_clear()
        self.motion_seconds = (self.source_end - self.source_begin) / (self.source_fps * self.playback_rate) + self.velocity_ramp_seconds
        self.envelope_seconds = self.approach_seconds + self.motion_seconds + self.release_seconds
        self.duration = self.envelope_seconds + self.return_seconds
        self.initial = self.envelope(0)
        self.final = self.envelope(self.envelope_seconds)
        park = Matrix.Translation((0, -1, 0))
        self.park_start = self.locals_of({name: park @ matrix for name, matrix in self.initial.items()})
        self.park_end = self.locals_of({name: park @ matrix for name, matrix in self.final.items()})

    def locals_of(self, pose):
        return {name: ((pose[self.parent[name]] @ self.relative[name]) if self.parent[name] else self.relative[name]).inverted() @ pose[name] for name in self.names}

    def from_locals(self, start, end, alpha):
        pose = {}
        for name in self.names:
            base = pose[self.parent[name]] @ self.relative[name] if self.parent[name] else self.relative[name]
            pose[name] = base @ start[name].lerp(end[name], alpha)
        return pose

    def source_pose(self, frame):
        lower = min(int(frame) - self.source_samples_begin, self.source_end - self.source_samples_begin)
        upper = min(lower + 1, self.source_end - self.source_samples_begin)
        alpha = frame - self.source_samples_begin - lower
        return self.from_locals(self.local_samples[lower], self.local_samples[upper], alpha)

    def supported(self, original):
        transform = self.target @ original['hand_r'].inverted()
        assert max(abs(value - 1) for value in transform.to_scale()) < 0.0002
        pose = {name: transform @ matrix for name, matrix in original.items()}
        for name in self.names:
            if name in self.fingers:
                pose[name] = pose[self.parent[name]] @ self.relative[name] @ self.fingers[name]
        return pose

    def motion_distance(self, time):
        time = max(0.0, min(self.motion_seconds, time))
        ramp = self.velocity_ramp_seconds
        def integral(value):
            return 2.5 * value ** 4 - 3 * value ** 5 + value ** 6
        if time < ramp:
            return ramp * integral(time / ramp)
        if time > self.motion_seconds - ramp:
            return self.motion_seconds - ramp - ramp * integral((self.motion_seconds - time) / ramp)
        return time - ramp * 0.5

    def envelope(self, time):
        frame = self.source_begin + self.source_fps * self.playback_rate * self.motion_distance(time - self.approach_seconds)
        pose = self.supported(self.source_pose(frame))
        opening = 1 - smooth(time / self.approach_seconds) if time < self.approach_seconds else smooth((time - self.approach_seconds - self.motion_seconds) / self.release_seconds)
        shift = Matrix.Translation(Vector((0, -0.4, 0)) * opening)
        pose = {name: shift @ matrix for name, matrix in pose.items()}
        lower = min(int(frame) - self.source_samples_begin, self.source_end - self.source_samples_begin)
        upper = min(lower + 1, self.source_end - self.source_samples_begin)
        alpha = frame - self.source_samples_begin - lower
        for name in self.names:
            if name in self.fingers:
                neutral = self.local_samples[lower][name].lerp(self.local_samples[upper][name], alpha)
                pose[name] = pose[self.parent[name]] @ self.relative[name] @ self.fingers[name].lerp(neutral, opening)
        return pose

    def base_loop(self, time):
        if time <= self.envelope_seconds:
            return self.envelope(time)
        time -= self.envelope_seconds
        if time < 2:
            shift = Matrix.Translation((0, -smooth(time / 2), 0))
            return {name: shift @ matrix for name, matrix in self.final.items()}
        if time < 6:
            return self.from_locals(self.park_end, self.park_start, smooth((time - 2) / 4))
        shift = Matrix.Translation((0, -(1 - smooth((time - 6) / 2)), 0))
        return {name: shift @ matrix for name, matrix in self.initial.items()}

    def rotate_subtree(self, pose, name, rotation):
        pivot = pose[name].translation.copy()
        transform = Matrix.Translation(pivot) @ rotation.to_matrix().to_4x4() @ Matrix.Translation(-pivot)
        for child in self.descendants[name]:
            pose[child] = transform @ pose[child]

    def swing(self, original, side, degrees, direction, anchored=False):
        pose = {name: matrix.copy() for name, matrix in original.items()}
        anchor = pose['hand_r'].copy()
        chest = pose['spine_05'].to_quaternion() @ self.rest['spine_05'].to_quaternion().inverted()
        upper = (pose['lowerarm_' + side].translation - pose['upperarm_' + side].translation).normalized()
        target = chest @ Vector(direction).normalized()
        axis = upper.cross(target)
        if axis.length > 1e-6:
            angle = min(math.radians(degrees), upper.angle(target))
            self.rotate_subtree(pose, 'upperarm_' + side, Quaternion(axis.normalized(), angle))
        if anchored:
            transform = anchor @ pose['hand_r'].inverted()
            pose = {name: transform @ matrix for name, matrix in pose.items()}
        return pose

    def pose(self, time):
        assert -1e-8 <= time <= self.duration + 1e-8
        pose = self.base_loop(time)
        right = 20 - 10 * window(time, 1.5, 2.5, 6, 7)
        left = 20 * window(time, 13, 14, 15, 16)
        pose = self.swing(pose, 'r', right, (0, -1, 0), anchored=True)
        pose = self.swing(pose, 'l', left, (0, -1, 0))
        outward = 8 * window(time, 6, 6.8, 7.4, 8.2) + 30 * window(time, 10.5, 11.5, 13.2, 14.2)
        sign = 1 if self.rest['upperarm_l'].translation.x > self.rest['spine_05'].translation.x else -1
        return self.swing(pose, 'l', outward, (sign, -0.25, 0))

    def apply(self, pose):
        inverse = self.rig.matrix_world.inverted()
        local_pose = {name: inverse @ matrix for name, matrix in pose.items()}
        for bone in self.ordered:
            base = local_pose[bone.parent.name] @ bone.parent.bone.matrix_local.inverted() @ bone.bone.matrix_local if bone.parent else bone.bone.matrix_local
            bone.matrix_basis = base.inverted() @ local_pose[bone.name]
        bpy.context.view_layer.update()

    def assert_inputs_unchanged(self):
        assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == value for path, value in self.hashes.items())
