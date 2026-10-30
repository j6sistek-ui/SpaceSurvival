"""Small authored overlap on the measured G2 holds, preserving primary motion.

This is a Vexa review control, not a universal anatomical solver. It preserves
the right grip, shoulders, spine and original action, including both endpoints.
"""
import hashlib
import json
import math
import os
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector

from g2_glute_follow_control import glute_follow_pose


class FloatingLifeControl:
    def __init__(self, phrase=False):
        self.phrase = phrase
        self.project = Path(os.environ.get('SS_ANIMATION_PROJECT', str(Path.home() / 'SpaceSurvival'))).resolve()
        self.source = self.project / 'SourceAssets/DanceRefinement_20261025'
        self.manifest = json.loads((self.source / 'G2_PalmarGrip_Knots_Manifest.json').read_text(encoding='utf-8'))
        self.guards = {
            str(self.source / 'Vexa_G1_ShoulderCap_Candidate.blend'): '51c25e242a481e7a98aee5281f11aa09094ecfbf0510272401f7868e87a8128e',
            str(self.source / self.manifest['file']): '409a79adfcfd8e9b365310f1d58955f91e6662eac47e613a6fb7314455ecd90d',
        }
        self.assert_guards()
        bpy.ops.wm.open_mainfile(filepath=str(self.source / 'Vexa_G1_ShoulderCap_Candidate.blend'), load_ui=False)
        self.scene = bpy.context.scene
        self.rig = next(o for o in self.scene.objects if o.type == 'ARMATURE')
        self.ordered = sorted(self.rig.pose.bones, key=lambda b: len(b.parent_recursive))
        self.names = [b.name for b in self.ordered]
        assert len(self.names) == 95
        self.rest = {n: self.rig.matrix_world @ self.rig.data.bones[n].matrix_local for n in self.names}
        self.parents = {b.name: b.parent.name if b.parent else None for b in self.ordered}
        self.relative = {n: self.rest[self.parents[n]].inverted() @ self.rest[n] if self.parents[n] else self.rest[n] for n in self.names}
        self.descendants = {n: [b.name for b in self.ordered if b.name == n or n in [p.name for p in b.parent_recursive]] for n in self.names}
        for ob in self.scene.objects:
            if ob.type == 'MESH' and ob.data.shape_keys:
                ob.data.shape_keys.animation_data_clear()
                for key in ob.data.shape_keys.key_blocks:
                    if key.name.startswith('REVIEW_'):
                        key.value = 0
        with bpy.data.libraries.load(str(self.source / self.manifest['file']), link=False) as (_, loaded):
            loaded.actions = [self.manifest['action']]
        self.action = loaded.actions[0]
        self.duration = self.manifest['seconds']
        self.windows = [(0., 6.8), (33.5, 44.), (47., self.duration)]

    def assert_guards(self):
        assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in self.guards.items())

    def base(self, seconds):
        self.rig.animation_data.action = self.action
        self.rig.animation_data.action_slot = self.action.slots[0]
        frame = 1 + seconds * 120
        self.scene.frame_set(math.floor(frame), subframe=frame % 1)
        bpy.context.view_layer.update()
        return {n: (self.rig.matrix_world @ self.rig.pose.bones[n].matrix).copy() for n in self.names}

    @staticmethod
    def smooth(value):
        x = max(0., min(1., value))
        return x*x*x*(x*(x*6-15)+10)

    def envelope(self, seconds):
        for start, end in self.windows:
            if start < seconds < end:
                return self.smooth((seconds-start)/.9)*self.smooth((end-seconds)/.9), seconds-start
        return 0., 0.

    def pose(self, seconds):
        original = self.base(seconds)
        pose = {n: m.copy() for n, m in original.items()}
        amount, t = self.envelope(seconds)
        if amount == 0:
            return pose, original, {}

        body = original['pelvis'].to_quaternion() @ self.rest['pelvis'].to_quaternion().inverted()
        changes = {}

        def rotate(name, axis, degrees):
            pivot = pose[name].translation
            transform = Matrix.Translation(pivot) @ Quaternion(axis.normalized(), math.radians(degrees)).to_matrix().to_4x4() @ Matrix.Translation(-pivot)
            for descendant in self.descendants[name]:
                pose[descendant] = transform @ pose[descendant]

        def hinge(a, b, c):
            axis = (pose[b].translation-pose[a].translation).cross(pose[c].translation-pose[b].translation)
            if axis.length < .0001:
                rest_axis = (self.rest[b].translation-self.rest[a].translation).cross(self.rest[c].translation-self.rest[b].translation).normalized()
                axis = pose[a].to_quaternion() @ self.rest[a].to_quaternion().inverted() @ rest_axis
            assert axis.length > .00001
            return axis.normalized()

        for side, sign, phase in [('l', 1, 0.), ('r', -1, math.pi)]:
            # One knee draws in while the other returns; the ankle follows
            # later. Different phases avoid a symmetrical pumping gesture.
            angle = 2*math.pi*t/6.2 + phase
            lift = .5-.5*math.cos(angle)
            knee = .5-.5*math.cos(angle-.55)
            thigh_flex = amount*(12.0 if self.phrase else 4.0)*lift
            spacing = amount*sign*(3.0 if self.phrase else 1.2)*math.sin(angle+.7)
            rotate('thigh_'+side, body @ Vector((1, 0, 0)), -thigh_flex)
            rotate('thigh_'+side, body @ Vector((0, 1, 0)), spacing)
            knee_axis = hinge('thigh_'+side, 'calf_'+side, 'foot_'+side)
            knee_flex = amount*(1.0+(29.0 if self.phrase else 7.0)*knee)
            rotate('calf_'+side, knee_axis, knee_flex)
            rotate('foot_'+side, knee_axis, -amount*(3.0 if self.phrase else 1.5)*math.sin(angle-1.0))
            changes[side] = {'thigh_flex_deg': thigh_flex, 'spacing_deg': spacing, 'knee_flex_deg': knee_flex}

        # Re-evaluate the established 30% swing-follow helper for these thighs.
        pelvis = pose['pelvis'] @ self.rest['pelvis'].inverted()
        for side in ('l', 'r'):
            pose['glute_'+side] = pelvis @ self.rest['glute_'+side]
        pose = glute_follow_pose(pose, self.rest)

        # The left arm is free in these holds. Keep its shoulder/clavicle exact;
        # a small elbow follow and later wrist response sustain its phrase.
        elbow_axis = hinge('upperarm_l', 'lowerarm_l', 'hand_l')
        rotate('lowerarm_l', elbow_axis, amount*2.5*(.5-.5*math.cos(2*math.pi*t/7.1+.8)))
        rotate('hand_l', elbow_axis, amount*.8*math.sin(2*math.pi*t/7.1-.4))
        return pose, original, changes

    def apply(self, pose):
        self.rig.animation_data.action = None
        inverse = self.rig.matrix_world.inverted()
        local = {n: inverse @ m for n, m in pose.items()}
        for bone in self.ordered:
            base = local[bone.parent.name] @ bone.parent.bone.matrix_local.inverted() @ bone.bone.matrix_local if bone.parent else bone.bone.matrix_local
            bone.matrix_basis = base.inverted() @ local[bone.name]
        bpy.context.view_layer.update()
