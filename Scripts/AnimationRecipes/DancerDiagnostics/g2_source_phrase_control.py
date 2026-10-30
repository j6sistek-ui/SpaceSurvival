"""Restore one repaired source-derived whole-body phrase in G2's free return.

Unsaved diagnostic only. This is existing-routine repair, not implementation
of a new conceptual block. Preserve the established world route and endpoints;
transfer coordinated body rotations rather than isolated legs. Contact and
deformation failures remain evidence, not permission to save this control.
"""
import hashlib
import json
import math

from g2_floating_life_control import FloatingLifeControl
from g2_glute_follow_control import glute_follow_pose

import bpy


class SourcePhraseControl(FloatingLifeControl):
    passage = (47., 51.1666666667, 7., 9.5)

    def __init__(self):
        super().__init__(phrase=True)
        self.manifest = json.loads((self.source / 'G2_FloatingLegPhrase_Manifest.json').read_text())
        current = self.source / self.manifest['file']
        expected_current = '173a62234bcc7572ba3c9a7070018557f3e845f6be8749ded6dab8f1c475205e'
        assert self.manifest['sha256'] == expected_current and self.manifest['fps'] == 120
        assert hashlib.sha256(current.read_bytes()).hexdigest() == expected_current
        self.guards[str(current)] = expected_current
        with bpy.data.libraries.load(str(current), link=False) as (_, loaded):
            loaded.actions = [self.manifest['action']]
        self.action = loaded.actions[0]
        assert self.action is not None and self.duration == self.manifest['seconds']
        library = self.source / 'GB_SelectedPassages_ActionLibrary.blend'
        expected = '0a38e12a774436fd08a44508f32820573cdc0dab4a56658737ecc1b7d4060b8e'
        assert hashlib.sha256(library.read_bytes()).hexdigest() == expected
        self.guards[str(library)] = expected
        with bpy.data.libraries.load(str(library), link=False) as (_, loaded):
            loaded.actions = ['A_F3_SelectedPassages_g1']
        self.source_action = loaded.actions[0]
        assert self.source_action is not None
        self.reference = self.donor(self.passage[2])
        self.moving = set(self.descendants['pelvis'])

    def donor(self, seconds):
        self.rig.animation_data.action = self.source_action
        self.rig.animation_data.action_slot = self.source_action.slots[0]
        frame = 1. + 60. * seconds
        self.scene.frame_set(math.floor(frame), subframe=frame % 1)
        bpy.context.view_layer.update()
        return {n: (self.rig.matrix_world @ self.rig.pose.bones[n].matrix).copy() for n in self.names}

    def pose(self, seconds):
        original = self.base(seconds)
        pose = {n: m.copy() for n, m in original.items()}
        start, end, source_start, source_end = self.passage
        if not start < seconds < end:
            return pose, original, {}
        source_seconds = source_start + (source_end - source_start) * (seconds - start) / (end - start)
        donor = self.donor(source_seconds)
        weight = self.smooth((seconds - start) / .65) * self.smooth((end - seconds) / .65)

        # Pelvis follows the source's changing orientation in the current
        # floating frame; its translation remains on the established route.
        q_base = original['pelvis'].to_quaternion()
        q_delta = self.reference['pelvis'].to_quaternion().inverted() @ donor['pelvis'].to_quaternion()
        q = q_base.slerp(q_base @ q_delta, weight)
        # Retain the imported 0.01 world scale. Replacing this matrix with a
        # unit quaternion matrix would enlarge the body by 100x and invalidate
        # every resulting surface/contact observation.
        rotation_delta = (q @ q_base.inverted()).to_matrix().to_4x4()
        pose['pelvis'] = rotation_delta @ original['pelvis']
        pose['pelvis'].translation = original['pelvis'].translation
        for name in self.names:
            if name == 'pelvis' or name not in self.moving:
                continue
            parent = self.parents[name]
            donor_local = (donor[parent] @ self.relative[name]).inverted() @ donor[name]
            base_local = (original[parent] @ self.relative[name]).inverted() @ original[name]
            q = base_local.to_quaternion().slerp(donor_local.to_quaternion(), weight)
            rotation_delta = (q @ base_local.to_quaternion().inverted()).to_matrix().to_4x4()
            local = rotation_delta @ base_local
            local.translation = base_local.translation
            pose[name] = pose[parent] @ self.relative[name] @ local
        pelvis_transform = pose['pelvis'] @ self.rest['pelvis'].inverted()
        for side in ('l', 'r'):
            pose['glute_' + side] = pelvis_transform @ self.rest['glute_' + side]
        pose = glute_follow_pose(pose, self.rest)
        scale_error = max((pose[n].to_scale() - original[n].to_scale()).length for n in self.names)
        assert scale_error < 1e-5, ('Source phrase must preserve imported world scale', scale_error)
        assert (pose['pelvis'].translation - original['pelvis'].translation).length < 1e-7
        return pose, original, {'source_seconds': source_seconds, 'weight': weight,
                                'hand_state': 'released', 'world_route': 'preserved',
                                'scale_error': scale_error}
