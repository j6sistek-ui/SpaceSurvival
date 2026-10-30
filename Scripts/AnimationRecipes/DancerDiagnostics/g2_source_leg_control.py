"""Restore source G1 leg phrases on current G2 without replacing its upper body.

Unsaved review only. Preserve the source mapping and any failed contact result.
"""
import hashlib
import math

import bpy

from g2_floating_life_control import FloatingLifeControl
from g2_glute_follow_control import glute_follow_pose


class SourceLegControl(FloatingLifeControl):
    # Owner-highlighted raw G1 poses, paced into existing held passages.
    passages = [(0., 6.8, .5, 3.), (33.5, 44., 4.5, 6.5), (47., 51.1666666667, 7.5, 9.)]

    def __init__(self):
        super().__init__(phrase=True)
        library = self.source/'GB_SelectedPassages_ActionLibrary.blend'
        self.guards[str(library)] = hashlib.sha256(library.read_bytes()).hexdigest()
        with bpy.data.libraries.load(str(library), link=False) as (_, loaded):
            loaded.actions = ['A_F3_SelectedPassages_g1']
        self.source_action = loaded.actions[0]
        assert self.source_action is not None
        self.leg_names = set(self.descendants['thigh_l']+self.descendants['thigh_r'])

    def pose(self, seconds):
        original = self.base(seconds)
        pose = {n: m.copy() for n, m in original.items()}
        section = next((s for s in self.passages if s[0] < seconds < s[1]), None)
        if section is None:
            return pose, original, {}
        start, end, source_start, source_end = section
        u = (seconds-start)/(end-start)
        source_time = source_start+(source_end-source_start)*u
        self.rig.animation_data.action = self.source_action
        self.rig.animation_data.action_slot = self.source_action.slots[0]
        # The retained retargeted library uses the original 60Hz frame domain.
        frame = 1+60*source_time
        self.scene.frame_set(math.floor(frame), subframe=frame % 1)
        bpy.context.view_layer.update()
        source_pose = {n: (self.rig.matrix_world @ self.rig.pose.bones[n].matrix).copy() for n in self.names}
        weight = self.smooth((seconds-start)/1.15)*self.smooth((end-seconds)/1.15)
        for n in self.names:
            if n not in self.leg_names:
                continue
            parent = self.parents[n]
            source_local = (source_pose[parent] @ self.relative[n]).inverted() @ source_pose[n]
            base_local = (original[parent] @ self.relative[n]).inverted() @ original[n]
            # Retain rest lengths; only transfer relative rotations.
            q = base_local.to_quaternion().slerp(source_local.to_quaternion(), weight)
            local = q.to_matrix().to_4x4()
            local.translation = base_local.translation
            pose[n] = pose[parent] @ self.relative[n] @ local
        pelvis = pose['pelvis'] @ self.rest['pelvis'].inverted()
        for side in ('l', 'r'):
            pose['glute_'+side] = pelvis @ self.rest['glute_'+side]
        return glute_follow_pose(pose, self.rest), original, {'source_seconds': source_time, 'weight': weight}
