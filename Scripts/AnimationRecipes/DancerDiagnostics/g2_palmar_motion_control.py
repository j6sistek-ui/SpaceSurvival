"""Private motion control for signed palmar grip; does not save assets.

Compares rejected whole-body shifts with arm-only IK and staged release.
The arm-only control keeps other body-local motion and allows a bounded smooth
root adjustment at full reach. Audit before exporting any candidate; --dense
samples every60Hz source frame. No control is a complete anatomy certification.
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
from g2_contact_recipe import smooth
from g2_glute_follow_control import anchor_waist_weights
from validate_g2_contact_recipe import geometry, skin, triangle_radii


class PalmarControl:
    def __init__(self, swing_degrees=0., radial_retreat=False, arm_ik=False, staged_release=False, free_wrist=False, index_lead=2.):
        self.project = Path(os.environ.get('SS_ANIMATION_PROJECT', str(Path.home() / 'SpaceSurvival'))).resolve()
        self.source = self.project / 'SourceAssets/DanceRefinement_20261025'
        self.review = self.project / '.agent/local/AnimationReview_20261025'
        self.output = self.review / 'G2PalmarGrip/MotionControl'
        self.swing_degrees = swing_degrees
        self.radial_retreat = radial_retreat
        self.arm_ik = arm_ik
        self.staged_release = staged_release
        self.free_wrist = free_wrist
        self.index_lead = index_lead
        assert 1. <= index_lead <= 3.
        assert not staged_release or arm_ik
        assert not free_wrist or staged_release
        if radial_retreat or swing_degrees:
            self.output = self.output.parent / f'MotionRadial{int(radial_retreat)}Swing{swing_degrees:g}'
        if arm_ik:
            self.output = self.output.parent / 'MotionArmIKV2'
        if staged_release:
            self.output = self.output.parent / 'MotionArmIKStaged'
        if free_wrist:
            self.output = self.output.parent / 'MotionArmIKFreeWrist'
            if index_lead != 2.:
                self.output = self.output.with_name(self.output.name+f'Index{index_lead:g}')
        self.output.mkdir(exist_ok=True)
        self.manifest = json.loads((self.source / 'G2_GluteFollow_Manifest.json').read_text())
        calibration_file = self.review / 'G2PalmarGrip/ThumbOppositionControl/ControlCalibration.json'
        self.calibration = json.loads(calibration_file.read_text())
        self.guards = dict(self.calibration['sources'])
        self.guards[str(calibration_file)] = hashlib.sha256(calibration_file.read_bytes()).hexdigest()
        assert self.guards[str(calibration_file)] == '3deea08d0acc9af732dbe6417d501b494762134b8488abc44ac5d1cbd1130af7'
        self.assert_guards()
        bpy.ops.wm.open_mainfile(filepath=str(self.source / 'Vexa_G2_PosteriorHip_Candidate.blend'), load_ui=False)
        self.scene = bpy.context.scene
        self.rig = next(o for o in self.scene.objects if o.type == 'ARMATURE')
        assert anchor_waist_weights(bpy.data.objects['Vexa_Continuous_Feet']) == self.manifest['weight_patch']
        for ob in self.scene.objects:
            if ob.type == 'MESH' and ob.data.shape_keys:
                ob.data.shape_keys.animation_data_clear()
                for key in ob.data.shape_keys.key_blocks:
                    if key.name.startswith('REVIEW_G2_'):
                        key.value, key.mute = 0, True
        self.ordered = sorted(self.rig.pose.bones, key=lambda b:len(b.parent_recursive))
        self.names = [b.name for b in self.ordered]
        self.descendants = {b.name:[b.name]+[c.name for c in b.children_recursive] for b in self.ordered}
        self.rest = {b.name:self.rig.matrix_world @ b.bone.matrix_local for b in self.ordered}
        self.parents = {b.name:b.parent.name if b.parent else None for b in self.ordered}
        self.relative = {n:self.rest[self.parents[n]].inverted() @ self.rest[n] if self.parents[n] else self.rest[n] for n in self.names}
        self.closed = {n:Matrix(v) for n,v in self.calibration['finger_local_matrices'].items()}
        neutral_file = self.source / 'GB_SelectedPassages_ActionLibrary.blend'
        self.guards[str(neutral_file)] = hashlib.sha256(neutral_file.read_bytes()).hexdigest()
        assert self.guards[str(neutral_file)].startswith('0a38e12a')
        with bpy.data.libraries.load(str(neutral_file), link=False) as (_,loaded):
            loaded.actions = ['A_F3_TwoPassages_g2']
        self.neutral = []
        self.rig.animation_data.action = loaded.actions[0]
        self.rig.animation_data.action_slot = loaded.actions[0].slots[0]
        for frame in (570,770):
            self.scene.frame_set(frame); bpy.context.view_layer.update()
            self.neutral.append({n:self.rig.pose.bones[n].matrix_basis.copy() for n in self.closed})
        with bpy.data.libraries.load(str(self.source / self.manifest['file']), link=False) as (_,loaded):
            loaded.actions = [self.manifest['action']]
        self.action = loaded.actions[0]
        self.rig.animation_data.action = self.action
        self.rig.animation_data.action_slot = self.action.slots[0]
        self.pace = json.loads((self.review / 'G2PosteriorHip/PacedHipAction.json').read_text())
        self.duration = self.manifest['seconds']
        self.hold_end = 2.5 + (770-570)/12 + 1
        self.envelope_end = self.hold_end + 2.5

    def assert_guards(self):
        assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p,h in self.guards.items())

    def source_time(self, seconds):
        return (float(np.interp(1+seconds*60, self.pace['destination_frames'], self.pace['source_frames']))-1)/60

    def pose(self, seconds):
        self.rig.animation_data.action = self.action
        self.rig.animation_data.action_slot = self.action.slots[0]
        frame = 1+seconds*60
        self.scene.frame_set(math.floor(frame), subframe=frame%1); bpy.context.view_layer.update()
        original = {b.name:(self.rig.matrix_world @ b.matrix).copy() for b in self.ordered}
        st = self.source_time(seconds)
        if st <= self.envelope_end:
            opening = 1-smooth(st/2.5) if st<2.5 else smooth((st-self.hold_end)/2.5)
            neutral = self.neutral[0 if st<2.5 else 1]
            retreat = .4*opening
        else:
            t = st-self.envelope_end
            retreat = .4 + (smooth(t/2) if t<2 else 1 if t<6 else 1-smooth((t-6)/2))
            opening, neutral = 1., None
        away = Vector((0,1,0))
        if self.radial_retreat:
            away = Matrix(self.calibration['hand_world_matrix']).translation
            away.z = 0
            away.normalize()
        # Cancel the saved negative-Y retreat, then apply the new outward path.
        shift = Vector(self.calibration['translation']) + (Vector((0,1,0))+away)*retreat
        transform = Matrix.Translation(shift)
        pose = {n:transform @ m for n,m in original.items()}
        finger_opening = opening
        thumb_escape = 0.
        if self.staged_release and neutral is not None:
            phase = max(0.,min(1.,1-st/2.5 if st<2.5 else (st-self.hold_end)/2.5))
            finger_opening = smooth((phase-.15)/.85)
            thumb_escape = smooth(phase/.2)*(1-smooth(finger_opening/.3))
        if neutral is not None:
            for n in self.names:
                if n in self.closed:
                    mix = 1-(1-finger_opening)**self.index_lead if self.free_wrist and n.startswith('index_') else finger_opening
                    pose[n] = pose[self.parents[n]] @ self.relative[n] @ self.closed[n].lerp(neutral[n], mix)
        reach_error = 0.
        root_adjust = 0.
        if self.arm_ik:
            desired_hand = original['hand_r'].copy()
            if neutral is not None:
                # Rejoin the preserved free-flight pose when the hand is open.
                # The lateral arc routes the open fingers around the pole.
                desired_hand.translation += Vector(self.calibration['translation'])*(1-opening) + Vector((.22*math.sin(math.pi*opening),0,0))
                if self.staged_release:
                    u = finger_opening
                    desired_hand.translation = Matrix(self.calibration['hand_world_matrix']).translation + Vector((.016*u+.22*math.sin(math.pi*u)**2,-.505*u+.3*math.sin(math.pi*u),0))
            pose = {n:m.copy() for n,m in original.items()}
            a,b,c = [pose[n].translation.copy() for n in ('upperarm_r','lowerarm_r','hand_r')]
            target = desired_hand.translation
            l1,l2 = (b-a).length,(c-b).length
            aim = target-a
            distance = aim.length
            aim.normalize()
            maximum = math.sqrt(l1*l1+l2*l2+2*l1*l2*math.cos(math.radians(10)))
            excess = distance-(maximum-.005)
            root_adjust = 0. if excess <= 0 else excess*excess/.02 if excess<.01 else excess-.005
            if root_adjust:
                transform = Matrix.Translation(aim*root_adjust)
                pose = {n:transform @ m for n,m in pose.items()}
                a,b,c = [pose[n].translation.copy() for n in ('upperarm_r','lowerarm_r','hand_r')]
                distance = (target-a).length
            reachable = max(abs(l1-l2)+.001,min(maximum,distance))
            reach_error = abs(reachable-distance)
            hint = b-a-aim*(b-a).dot(aim)
            assert hint.length > 1e-5, 'Degenerate elbow plane'
            hint.normalize()
            projection = (l1*l1-l2*l2+reachable*reachable)/(2*reachable)
            height = math.sqrt(max(0.,l1*l1-projection*projection))
            elbow = a+aim*projection+hint*height
            self.rotate_aim(pose,'upperarm_r',b-a,elbow-a)
            self.rotate_aim(pose,'lowerarm_r',pose['hand_r'].translation-pose['lowerarm_r'].translation,target-elbow)
            actual_hand = pose['hand_r'].copy()
            desired_hand.translation = actual_hand.translation
            if self.free_wrist and neutral is not None:
                natural = pose['lowerarm_r'] @ original['lowerarm_r'].inverted() @ original['hand_r']
                natural.translation = actual_hand.translation
                desired_hand = desired_hand.lerp(natural,smooth((finger_opening-.10)/.25))
            transform = desired_hand @ actual_hand.inverted()
            for n in self.descendants['hand_r']:
                pose[n] = transform @ pose[n]
            if neutral is not None:
                for n in self.names:
                    if n in self.closed:
                        mix = 1-(1-finger_opening)**self.index_lead if self.free_wrist and n.startswith('index_') else finger_opening
                        pose[n] = pose[self.parents[n]] @ self.relative[n] @ self.closed[n].lerp(neutral[n], mix)
            if thumb_escape:
                width = (self.rest['index_01_r'].translation-self.rest['pinky_01_r'].translation).normalized()
                axis = (pose['hand_r'] @ self.rest['hand_r'].inverted()).to_3x3() @ width
                self.rotate_subtree(pose,'thumb_01_r',Quaternion(axis.normalized(),math.radians(25)*thumb_escape))
        elif self.swing_degrees:
            anchor = pose['hand_r'].copy()
            chest = pose['spine_05'].to_quaternion() @ self.rest['spine_05'].to_quaternion().inverted()
            upper = (pose['lowerarm_r'].translation-pose['upperarm_r'].translation).normalized()
            target = chest @ Vector((0,-1,0))
            axis = upper.cross(target)
            if axis.length > 1e-6:
                pivot = pose['upperarm_r'].translation
                angle = min(math.radians(self.swing_degrees),upper.angle(target))
                rotation = Quaternion(axis.normalized(),angle).to_matrix().to_4x4()
                transform = Matrix.Translation(pivot) @ rotation @ Matrix.Translation(-pivot)
                for n in self.descendants['upperarm_r']:
                    pose[n] = transform @ pose[n]
                transform = anchor @ pose['hand_r'].inverted()
                pose = {n:transform @ m for n,m in pose.items()}
        original_local = original['lowerarm_r'].inverted() @ original['hand_r']
        new_local = pose['lowerarm_r'].inverted() @ pose['hand_r']
        wrist_change = math.degrees(original_local.to_quaternion().rotation_difference(new_local.to_quaternion()).angle)
        return pose, original, {'source_seconds':st,'opening':opening,'finger_opening':finger_opening,'thumb_escape':thumb_escape,'retreat':retreat,'translation_control_shift':list(shift),'translation_control_applied':not self.arm_ik,'shoulder_swing_degrees':self.swing_degrees,'reach_error_m':reach_error,'root_adjust_m':root_adjust,'wrist_local_delta_degrees':wrist_change}

    def rotate_aim(self, pose, name, before, after):
        rotation = before.normalized().rotation_difference(after.normalized())
        self.rotate_subtree(pose,name,rotation)

    def rotate_subtree(self, pose, name, rotation):
        pivot = pose[name].translation.copy()
        transform = Matrix.Translation(pivot) @ rotation.to_matrix().to_4x4() @ Matrix.Translation(-pivot)
        for n in self.descendants[name]:
            pose[n] = transform @ pose[n]

    def apply(self, pose):
        self.rig.animation_data.action = None
        inv = self.rig.matrix_world.inverted()
        local = {n:inv @ m for n,m in pose.items()}
        for b in self.ordered:
            base = local[b.parent.name] @ b.parent.bone.matrix_local.inverted() @ b.bone.matrix_local if b.parent else b.bone.matrix_local
            b.matrix_basis = base.inverted() @ local[b.name]
        bpy.context.view_layer.update()


def audit(model, dense=False):
    meshes = geometry(SimpleNamespace(names=model.names, scene=model.scene))
    inverses = np.array([model.rest[n].inverted() for n in model.names])
    rows = []; max_radius = local_error = 0.; first = last = None
    ar,br,cr=[model.rest[n] for n in ('upperarm_r','lowerarm_r','hand_r')]
    hinge_rest=ar.to_quaternion().inverted()@(br.translation-ar.translation).cross(cr.translation-br.translation).normalized()
    step = 1 if dense else 20
    for frame in sorted(set(range(0,model.manifest['frame_end'],step)) | {model.manifest['frame_end']-1}):
        seconds = frame/60
        pose,original,phase = model.pose(seconds)
        if first is None: first=pose
        last=pose
        for n in model.names:
            if n not in model.closed and n not in ('upperarm_r','lowerarm_r','hand_r') and model.parents[n]:
                parent=model.parents[n]
                local_error=max(local_error,float(np.abs(np.array(pose[parent].inverted()@pose[n])-np.array(original[parent].inverted()@original[n])).max()))
        matrices=np.array([pose[n] for n in model.names])@inverses
        a,b,c=[pose[n] for n in ('upperarm_r','lowerarm_r','hand_r')]
        upper=(b.translation-a.translation).normalized();lower=(c.translation-b.translation).normalized()
        hand=((pose['index_01_r'].translation+pose['pinky_01_r'].translation)*.5-c.translation).normalized()
        axis=upper.cross(lower)
        hinge_alignment=(a.to_quaternion().inverted()@axis.normalized()).dot(hinge_rest) if axis.length>.01 else 1.
        chest=pose['spine_05'].to_quaternion()@model.rest['spine_05'].to_quaternion().inverted()
        forward=chest@Vector((0,-1,0));up=chest@Vector((0,0,1))
        rear=math.degrees(math.asin(max(-1.,min(1.,-upper.dot(forward)))))
        phase.update({'elbow_bend_degrees':math.degrees(upper.angle(lower)), 'hinge_alignment':hinge_alignment,
                      'rear_reach_degrees':rear, 'rear_flag':rear>(12 if upper.dot(up)>0 else 2),
                      'wrist_direction_degrees':math.degrees(lower.angle(hand))})
        pole={}; bodies=[]; body_faces=[]; arms=[]; arm_faces=[]; digit_pairs={}
        for mesh in meshes:
            name,_,triangles,joints,weights,body_tri,arm_tri=mesh
            pts=skin(matrices,mesh)
            max_radius=max(max_radius,float(np.linalg.norm(pts[:,:2],axis=1).max()))
            radius=triangle_radii(pts,triangles); z=pts[triangles,2]
            bad=(radius<.025-.00001)&(z.max(axis=1)>0)&(z.min(axis=1)<5)
            if bad.any():pole[name]={'count':int(bad.sum()),'penetration_mm':float((.025-radius[bad]).max()*1000)}
            if len(body_tri):
                offset=len(bodies);bodies.extend(pts.tolist());body_faces.extend((body_tri+offset).tolist())
            if len(arm_tri):
                offset=len(arms);arms.extend(pts.tolist());arm_faces.extend((arm_tri+offset).tolist())
            if name=='Vexa_Continuous_Hands':
                trees={}
                for digit in ('thumb','index','middle','ring','pinky'):
                    mask=(weights*np.array([n.startswith(digit+'_') and n.endswith('_r') for n in model.names])[joints]).sum(axis=1)>.65
                    selected=triangles[np.all(mask[triangles],axis=1)]
                    trees[digit]=BVHTree.FromPolygons(pts.tolist(),selected.tolist(),all_triangles=True)
                    if name in pole:
                        pole[name].setdefault('digit_radius_mm',{})[digit]=float(triangle_radii(pts,selected).min()*1000)
                digit_pairs={a+'/'+b:len(trees[a].overlap(trees[b])) for a,b in itertools.combinations(trees,2)}
                digit_pairs={k:v for k,v in digit_pairs.items() if v}
        contact=BVHTree.FromPolygons(bodies,body_faces,all_triangles=True).overlap(BVHTree.FromPolygons(arms,arm_faces,all_triangles=True))
        rows.append({'seconds':seconds,**phase,'pole':pole,'arm_body_pairs':len(contact),'digit_pairs':digit_pairs})
        if frame%600==0:print('PALMAR_MOTION',frame,rows[-1],flush=True)
    loop=max(float(np.abs(np.array(first[n])-np.array(last[n])).max()) for n in model.names)
    report={'sources':model.guards,'control_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'options':{'swing_degrees':model.swing_degrees,'radial_retreat':model.radial_retreat,'arm_ik':model.arm_ik,'staged_release':model.staged_release,'free_wrist':model.free_wrist,'index_lead':model.index_lead},'samples':len(rows),'dense':dense,'pole_flags':sum(bool(r['pole']) for r in rows),'arm_body_flags':sum(r['arm_body_pairs']>0 for r in rows),'digit_flags':sum(bool(r['digit_pairs']) for r in rows),'body_local_matrix_error':local_error,'loop_matrix_error':loop,'maximum_radius_m':max_radius,'rows':rows,'scope':'Private unsaved control. Limited sampled contacts; not owner/artistic/native acceptance.'}
    (model.output/('DenseAudit.json' if dense else 'CoarseAudit.json')).write_text(json.dumps(report,indent=2))
    model.assert_guards()
    print('PALMAR_MOTION_RESULT',{k:v for k,v in report.items() if k!='rows'},flush=True)
    return report


def options():
    swing = float(sys.argv[sys.argv.index('--swing')+1]) if '--swing' in sys.argv else 0.
    lead = float(sys.argv[sys.argv.index('--index-lead')+1]) if '--index-lead' in sys.argv else 2.
    return swing, '--radial-retreat' in sys.argv, '--arm-ik' in sys.argv, '--staged-release' in sys.argv, '--free-wrist' in sys.argv, lead


if __name__=='__main__':
    audit(PalmarControl(*options()), '--dense' in sys.argv)
