"""Adapt the verified signed G2 grip to the retained G1 supported passage.

Private, unsaved comparison. The old G1 finger calibration is rejected for
dorsal flexion. Keep its body motion as the baseline and test both rigid shift
and arm-only reach correction before saving a replacement. No production edits.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from g2_palmar_motion_control import PalmarControl, audit
from g2_contact_recipe import smooth


def relieve_free_arm(model, pose, reach_degrees, elbow_degrees):
    """Move the free wrist toward the chest front, then open its elbow hinge."""
    a,b,c=[pose[n].translation.copy() for n in ('upperarm_l','lowerarm_l','hand_l')]
    if reach_degrees:
        chest=pose['spine_05'].to_quaternion() @ model.rest['spine_05'].to_quaternion().inverted()
        forward=chest @ Vector((0,-1,0))
        axis=(c-a).normalized().cross(forward)
        assert axis.length>.01, 'Ambiguous free-arm forward swing'
        model.rotate_subtree(pose,'upperarm_l',Quaternion(axis.normalized(),math.radians(reach_degrees)))
    if elbow_degrees:
        a,b,c=[pose[n].translation.copy() for n in ('upperarm_l','lowerarm_l','hand_l')]
        upper=(b-a).normalized();lower=(c-b).normalized()
        axis=upper.cross(lower)
        assert axis.length>.01
        allowed=max(0.,math.degrees(upper.angle(lower))-10.)
        model.rotate_subtree(pose,'lowerarm_l',Quaternion(axis.normalized(),math.radians(-min(allowed,elbow_degrees))))


class G1PalmarControl(PalmarControl):
    def __init__(self, arm_only=True, free_profile=False, continuous_release=False, pin_orientation=False):
        super().__init__(arm_ik=True, staged_release=True, free_wrist=True, index_lead=2.3)
        self.arm_only = arm_only
        self.continuous_release = continuous_release
        self.pin_orientation = pin_orientation
        self.output = self.review / 'G1PalmarGrip' / ('ArmControl' if arm_only else 'RigidControl')
        self.output.mkdir(parents=True, exist_ok=True)
        receipt_path = self.review / 'GBSupportedRelease/Export.json'
        receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
        source = self.source / Path(receipt['file']).name
        self.guards[str(source)] = receipt['sha256']
        assert receipt['sha256'] == '49f8765479a611da20536ca2576879ab845cc9ba16558d5912866e3a8dd72cc2'
        self.assert_guards()
        with bpy.data.libraries.load(str(source), link=False) as (_, loaded):
            loaded.actions = [receipt['action']]
        self.action = loaded.actions[0]
        self.duration = receipt['seconds']
        self.manifest = {'seconds': self.duration, 'frame_end': receipt['frames'][1]}
        self.release_start = (920-780)/12
        self.release_duration = (940-920)/12
        # Neutral fingers come from the original source, never the rejected curl.
        neutral_source = self.source / 'GB_SelectedPassages_ActionLibrary.blend'
        with bpy.data.libraries.load(str(neutral_source), link=False) as (_, loaded):
            loaded.actions = ['A_F3_SelectedPassages_g1']
        self.rig.animation_data.action = loaded.actions[0]
        self.rig.animation_data.action_slot = loaded.actions[0].slots[0]
        self.scene.frame_set(940)
        bpy.context.view_layer.update()
        self.open_fingers = {n:self.rig.pose.bones[n].matrix_basis.copy() for n in self.closed}
        self.free_profile=None
        if free_profile:
            path=self.review/'G1PalmarGrip/FreeArmProfile.json'
            self.free_profile=json.loads(path.read_text(encoding='utf-8'))
            self.guards[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
            self.output=self.output.parent/('FreeArmIKControl' if arm_only else 'FreeArmRigidControl')
            self.output.mkdir(exist_ok=True)
        if continuous_release:
            self.output=self.output.with_name(self.output.name+'Continuous')
            self.output.mkdir(exist_ok=True)
        if pin_orientation:
            assert continuous_release
            self.output=self.output.with_name(self.output.name+'Pinned')
            self.output.mkdir(exist_ok=True)

    def pose(self, seconds):
        self.rig.animation_data.action = self.action
        self.rig.animation_data.action_slot = self.action.slots[0]
        frame = 1+seconds*60
        self.scene.frame_set(math.floor(frame), subframe=frame%1)
        bpy.context.view_layer.update()
        original = {b.name:(self.rig.matrix_world @ b.matrix).copy() for b in self.ordered}
        pose = {n:m.copy() for n,m in original.items()}
        phase = max(0., min(1., (seconds-self.release_start)/self.release_duration))
        opening = smooth(phase)
        # Quintic evaluation can overshoot 1 by a few ulps. Fractional powers
        # below require a closed interval, including fractional-frame sampling.
        u = max(0., min(1., smooth((phase-.15)/.85)))
        thumb_escape = smooth(phase/.2)*(1-smooth(u/.3))
        target = Matrix(self.calibration['hand_world_matrix'])
        desired = original['hand_r'].copy()
        if self.pin_orientation and phase<1:
            # No rotation against the pole while fingers remain closed. Resume
            # the source orientation only after the thumb/fingers start clearing.
            desired=target.lerp(original['hand_r'],smooth((u-.1)/.25))
        # The held calibration is identical to G2. During release, compensate
        # the old 40cm body retreat and route fingers around the pole first.
        desired.translation += Vector(self.calibration['translation'])*(1-opening)
        if phase < 1:
            desired.translation = target.translation + Vector((.016*u+.22*math.sin(math.pi*u)**2, -.505*u+.3*math.sin(math.pi*u), 0))
            if self.continuous_release:
                # G1's old hand already moves relative to its frozen support
                # frame during release. Keep that residual; dropping it then
                # restoring it at phase==1 produces a visible 25cm snap.
                old_target=target.translation-Vector(self.calibration['translation'])
                old_expected=old_target+Vector((0,-.4*opening,0))
                desired.translation+=(original['hand_r'].translation-old_expected)*smooth((u-.1)/.25)
        reach_error = root_adjust = 0.
        if self.arm_only:
            a,b,c = [pose[n].translation.copy() for n in ('upperarm_r','lowerarm_r','hand_r')]
            aim = desired.translation-a
            distance = aim.length
            aim.normalize()
            l1,l2 = (b-a).length,(c-b).length
            maximum = math.sqrt(l1*l1+l2*l2+2*l1*l2*math.cos(math.radians(10)))
            excess = distance-(maximum-.005)
            root_adjust = 0. if excess<=0 else excess*excess/.02 if excess<.01 else excess-.005
            if root_adjust:
                shift = Matrix.Translation(aim*root_adjust)
                pose = {n:shift @ m for n,m in pose.items()}
                a,b,c = [pose[n].translation.copy() for n in ('upperarm_r','lowerarm_r','hand_r')]
                distance = (desired.translation-a).length
            reachable = max(abs(l1-l2)+.001, min(maximum,distance))
            reach_error = abs(reachable-distance)
            hint = b-a-aim*(b-a).dot(aim)
            assert hint.length>1e-5, 'Degenerate elbow plane'
            hint.normalize()
            projection = (l1*l1-l2*l2+reachable*reachable)/(2*reachable)
            elbow = a+aim*projection+hint*math.sqrt(max(0.,l1*l1-projection*projection))
            self.rotate_aim(pose,'upperarm_r',b-a,elbow-a)
            self.rotate_aim(pose,'lowerarm_r',pose['hand_r'].translation-pose['lowerarm_r'].translation,desired.translation-elbow)
            actual = pose['hand_r'].copy()
            desired.translation = actual.translation
            natural = pose['lowerarm_r'] @ original['lowerarm_r'].inverted() @ original['hand_r']
            natural.translation = actual.translation
            desired = desired.lerp(natural,smooth((u-.10)/.25))
            transform = desired @ actual.inverted()
            for n in self.descendants['hand_r']:
                pose[n] = transform @ pose[n]
        else:
            transform = desired @ original['hand_r'].inverted()
            pose = {n:transform @ m for n,m in pose.items()}
        for n in self.names:
            if n in self.closed:
                blend = 1-(1-u)**2.3 if n.startswith('index_') else u
                # Rejoin each moving original local finger after the release.
                neutral = self.open_fingers[n] if phase<1 else (original[self.parents[n]] @ self.relative[n]).inverted() @ original[n]
                pose[n] = pose[self.parents[n]] @ self.relative[n] @ self.closed[n].lerp(neutral,blend)
        if thumb_escape:
            width = (self.rest['index_01_r'].translation-self.rest['pinky_01_r'].translation).normalized()
            axis = (pose['hand_r'] @ self.rest['hand_r'].inverted()).to_3x3() @ width
            self.rotate_subtree(pose,'thumb_01_r',Quaternion(axis.normalized(),math.radians(25)*thumb_escape))
        free_reach=free_elbow=0.
        if self.free_profile:
            free_reach=float(np.interp(seconds,self.free_profile['seconds'],self.free_profile['reach_degrees']))
            free_elbow=float(np.interp(seconds,self.free_profile['seconds'],self.free_profile['elbow_degrees']))
            relieve_free_arm(self,pose,free_reach,free_elbow)
        local_before = original['lowerarm_r'].inverted() @ original['hand_r']
        local_after = pose['lowerarm_r'].inverted() @ pose['hand_r']
        return pose, original, {'source_frame':780+seconds*12,'opening':opening,'finger_opening':u,
            'thumb_escape':thumb_escape,'reach_error_m':reach_error,'root_adjust_m':root_adjust,
            'free_reach_degrees':free_reach,'free_elbow_degrees':free_elbow,
            'wrist_local_delta_degrees':math.degrees(local_before.to_quaternion().rotation_difference(local_after.to_quaternion()).angle)}


if __name__ == '__main__':
    model = G1PalmarControl('--rigid' not in sys.argv,'--free-profile' in sys.argv,'--continuous-release' in sys.argv,'--pin-orientation' in sys.argv)
    report = audit(model,'--dense' in sys.argv)
    report['control_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report['scope'] = 'G1 unsaved supported passage, not a loop. Signed G2 calibration transferred; sampled limits do not establish anatomy or visual acceptance.'
    report['arm_only'] = model.arm_only
    report['options']={'arm_only':model.arm_only,'free_profile':bool(model.free_profile),
                       'continuous_release':model.continuous_release,'pin_orientation':model.pin_orientation}
    report['all_local_delta_including_authored_free_arm']=report.pop('body_local_matrix_error')
    report['endpoint_difference_not_loop_error'] = report.pop('loop_matrix_error')
    (model.output/('DenseAudit.json' if '--dense' in sys.argv else 'CoarseAudit.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
