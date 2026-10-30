"""Unsaved right-hand control: curl toward verified palm, never toward nails.

The retained radial-only calibration allowed dorsal finger flexion. This probe
keeps the saved candidate intact and distinguishes bend direction from contact.
Run hidden Blender. --fit performs the bounded static fitting control.
"""
import hashlib
import itertools
import json
import math
import os
import sys
from pathlib import Path

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
O = R / 'G2PalmarGrip'
O.mkdir(exist_ok=True)
if '--coarse' in sys.argv:
    O = O / 'IndependentFingerControl'
    O.mkdir(exist_ok=True)
if '--thumb-axis' in sys.argv:
    O = R / 'G2PalmarGrip/ThumbHingeControl'
    O.mkdir(exist_ok=True)
if '--surface' in sys.argv:
    assert '--thumb-axis' in sys.argv
    O = R / 'G2PalmarGrip/SurfaceContactControl'
    O.mkdir(exist_ok=True)
if '--cmc' in sys.argv:
    assert '--surface' in sys.argv
    O = R / 'G2PalmarGrip/ThumbCMCControl'
    O.mkdir(exist_ok=True)
if '--opposition' in sys.argv:
    assert '--cmc' in sys.argv
    O = R / 'G2PalmarGrip/ThumbOppositionControl'
    O.mkdir(exist_ok=True)
manifest = json.loads((D / 'G2_GluteFollow_Manifest.json').read_text())
source, library = D / 'Vexa_G2_PosteriorHip_Candidate.blend', D / manifest['file']
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
                key.value, key.mute = 0, True
ordered = sorted(rig.pose.bones, key=lambda b: len(b.parent_recursive))
names = [b.name for b in ordered]
rest = {n: rig.matrix_world @ rig.data.bones[n].matrix_local for n in names}
parent = {b.name: b.parent.name if b.parent else None for b in ordered}
relative = {n: rest[parent[n]].inverted() @ rest[n] if parent[n] else rest[n] for n in names}
descendants = {b.name: [b.name] + [c.name for c in b.children_recursive] for b in ordered}
pace = json.loads((R / 'G2PosteriorHip/PacedHipAction.json').read_text())
frame = float(np.interp(1 + 12.4 * 60, pace['source_frames'], pace['destination_frames']))
s.frame_set(math.floor(frame), subframe=frame % 1)
bpy.context.view_layer.update()
before = {n: (rig.matrix_world @ rig.pose.bones[n].matrix).copy() for n in names}
rig.animation_data_clear()
hands = bpy.data.objects['Vexa_Continuous_Hands']
meshes = geometry(type('Model', (), {'names': names, 'scene': s})())
mesh = next(m for m in meshes if m[0] == hands.name)
_, points, triangles, joints, weights, _, _ = mesh
inverse_rest = np.array([rest[n].inverted() for n in names])
digits = ('index', 'middle', 'ring', 'pinky')
rest_along = (rest['middle_01_r'].translation - rest['hand_r'].translation).normalized()
rest_width = (rest['index_01_r'].translation - rest['pinky_01_r'].translation).normalized()
rest_palm = -rest_along.cross(rest_width).normalized()
transport = (before['hand_r'] @ rest['hand_r'].inverted()).to_3x3()
along, width, palm = [(transport @ v).normalized() for v in (rest_along, rest_width, rest_palm)]
assert palm.dot(Vector((0, -1, 0))) > .999
right = (weights * np.array([n.endswith('_r') and n.startswith(('hand_', 'thumb_', *[d + '_' for d in digits])) for n in names])[joints]).sum(axis=1) > .5
ids = np.flatnonzero(right)
local_mesh = (mesh[0], points[ids], None, joints[ids], weights[ids], None, None)
digit_masks = {d: (weights * np.array([n.startswith(d + '_') and n.endswith('_r') for n in names])[joints]).sum(axis=1) > .65 for d in (*digits, 'thumb')}
pad_masks = {}
for digit in (*digits, 'thumb'):
    pad = np.zeros(len(points), dtype=bool)
    for segment in (2, 3):
        n = f'{digit}_{segment:02}_r'
        own = (weights * (joints == names.index(n))).sum(axis=1) > .5
        side = (points[:, :3] - np.array(rest[n].translation)) @ np.array(rest_palm)
        pad |= own & (side > .001)
    pad_masks[digit] = pad[ids]
    assert pad_masks[digit].sum() >= 3, (digit, pad_masks[digit].sum())
if '--surface' in sys.argv:
    # Thumb pad is on its own flexion side, not the four fingers' shared plane.
    direction = (rest['thumb_03_r'].translation - rest['thumb_02_r'].translation).normalized()
    thumb_pad_normal = (rest_along - direction * rest_along.dot(direction)).normalized()
    own = (weights * (joints == names.index('thumb_03_r'))).sum(axis=1) > .5
    side = (points[:, :3] - np.array(rest['thumb_03_r'].translation)) @ np.array(thumb_pad_normal)
    pad_masks['thumb'] = (own & (side > .001))[ids]
    assert pad_masks['thumb'].sum() >= 3
    remap = np.full(len(points), -1); remap[ids] = np.arange(len(ids))
    compact_faces = remap[triangles[np.all(right[triangles], axis=1)]]
    compact_digit_faces = {d:remap[triangles[np.all(mask[triangles], axis=1)]] for d,mask in digit_masks.items()}

def rotate(pose, name, rotation):
    pivot = pose[name].translation
    change = Matrix.Translation(pivot) @ rotation.to_matrix().to_4x4() @ Matrix.Translation(-pivot)
    for child in descendants[name]:
        pose[child] = change @ pose[child]

def apply(pose):
    inv = rig.matrix_world.inverted()
    local = {n: inv @ m for n, m in pose.items()}
    for b in ordered:
        base = local[b.parent.name] @ b.parent.bone.matrix_local.inverted() @ b.bone.matrix_local if b.parent else b.bone.matrix_local
        b.matrix_basis = base.inverted() @ local[b.name]
    bpy.context.view_layer.update()

def bend_directions(pose):
    return {d: {'proximal_palmar_mm': (pose[d + '_02_r'].translation - pose[d + '_01_r'].translation).dot(palm) * 1000,
                'middle_palmar_mm': (pose[d + '_03_r'].translation - pose[d + '_02_r'].translation).dot(palm) * 1000}
            for d in digits}

def posed(params):
    p = {n: m.copy() for n, m in before.items()}
    for fi, digit in enumerate(digits):
        for segment in (1, 2, 3):
            n = f'{digit}_{segment:02}_r'
            base = p[parent[n]] @ relative[n]
            rotate(p, n, base.to_quaternion() @ p[n].to_quaternion().inverted())
            # Positive curl is toward the right palm, opposite old -width.
            rotate(p, n, Quaternion(width, float(params[2 + fi * 3 + segment - 1])))
    for segment in (1, 2, 3):
        n = f'thumb_{segment:02}_r'
        base = p[parent[n]] @ relative[n]
        rotate(p, n, base.to_quaternion() @ p[n].to_quaternion().inverted())
    if '--cmc' in sys.argv:
        rotate(p, 'thumb_01_r', Quaternion(width, float(params[18])))
    rotate(p, 'thumb_01_r', Quaternion(along, float(params[14])))
    if '--opposition' in sys.argv:
        axis = (p['thumb_02_r'].translation - p['thumb_01_r'].translation).normalized()
        rotate(p, 'thumb_01_r', Quaternion(axis, float(params[19])))
    if '--thumb-axis' in sys.argv:
        # Thumb flexes across the palm toward the finger bases; it does not
        # share the four fingers' palmar flexion plane. Transport its rest
        # hinge with opposition rather than continually aiming at world -Y.
        thumb_direction = (rest['thumb_03_r'].translation - rest['thumb_02_r'].translation).normalized()
        hinge_rest = thumb_direction.cross(rest_along).normalized()
        hinge = (p['thumb_01_r'] @ rest['thumb_01_r'].inverted()).to_3x3() @ hinge_rest
        for segment in (1, 2, 3):
            rotate(p, f'thumb_{segment:02}_r', Quaternion(hinge, float(params[14 + segment])))
        shift = Matrix.Translation((float(params[0]), float(params[1]), 0))
        return {n: shift @ m for n, m in p.items()}
    for segment in (1, 2, 3):
        n = f'thumb_{segment:02}_r'
        direction = (p[f'thumb_{segment+1:02}_r'].translation - p[n].translation).normalized() if segment < 3 else (p[n].translation - p['thumb_02_r'].translation).normalized()
        rotate(p, n, Quaternion(direction.cross(palm).normalized(), float(params[14 + segment])))
    shift = Matrix.Translation((float(params[0]), float(params[1]), 0))
    return {n: shift @ m for n, m in p.items()}

def metric(params, details=False, digit=None):
    p = posed(params)
    pts = skin(np.array([p[n] for n in names]) @ inverse_rest, local_mesh)
    gap = np.linalg.norm(pts[:, :2], axis=1) - .025
    extra = 0.; surface_gap = None; contact_pairs = None
    if '--surface' in sys.argv:
        surface_gap = float(triangle_radii(pts, compact_faces).min() - .025)
        extra = 2500 * min(surface_gap - .00005, 0) ** 2
        index_tree = BVHTree.FromPolygons(pts.tolist(), compact_digit_faces['index'].tolist(), all_triangles=True)
        thumb_tree = BVHTree.FromPolygons(pts.tolist(), compact_digit_faces['thumb'].tolist(), all_triangles=True)
        contact_pairs = len(index_tree.overlap(thumb_tree))
        extra += contact_pairs * .01
    if '--opposition' in sys.argv:
        # A contact-only minimum lifted the thumb into a stretched hook. Keep
        # its distal joint by the index, and penalize excess CMC rotation.
        desired_height = p['index_01_r'].translation.z + .012
        extra += 2 * (p['thumb_03_r'].translation.z - desired_height) ** 2
        base = p['hand_r'] @ relative['thumb_01_r']
        angle = base.to_quaternion().rotation_difference(p['thumb_01_r'].to_quaternion()).angle
        extra += .00005 * max(angle - math.radians(45), 0) ** 2
    if digit is not None:
        own = digit_masks[digit][ids]
        pen = np.minimum(gap[own], 0)
        near = float(np.mean(np.sort(gap[pad_masks[digit]])[:3]))
        return extra + 2500 * float(pen.min()) ** 2 + 100 * float(np.mean(pen ** 2)) + near * near
    penetration = np.minimum(gap, 0)
    near = {d: float(np.mean(np.sort(gap[mask])[:3])) for d, mask in pad_masks.items()}
    score = extra + 2500 * float(penetration.min()) ** 2 + 100 * float(np.mean(penetration ** 2)) + sum(v*v for v in near.values())
    score += .000002 * float(np.sum((params[2:] - seed[2:]) ** 2))
    if details:
        return {'loss': score, 'max_vertex_penetration_mm': float(-penetration.min() * 1000), 'palmar_pad_gap_mm': {d:v*1000 for d,v in near.items()}, 'surface_gap_mm':None if surface_gap is None else surface_gap*1000, 'thumb_index_pairs':contact_pairs}
    return score

seed = np.array([0., .084] + list(np.radians([35, 85, 50])) * 4 + list(np.radians([-16, 0, 50, 52])))
params = seed.copy()
low = np.array([-.04, .035] + list(np.radians([5, 30, 5])) * 4 + list(np.radians([-55, 0, 0, 0])))
high = np.array([.04, .12] + list(np.radians([75, 105, 85])) * 4 + list(np.radians([55, 75, 85, 85])))
if '--cmc' in sys.argv:
    seed = np.append(seed, math.radians(40))
    low = np.append(low, math.radians(-15)); high = np.append(high, math.radians(75))
if '--opposition' in sys.argv:
    seed = np.append(seed, 0.)
    low = np.append(low, math.radians(-80)); high = np.append(high, math.radians(80))
    high[15:18] = np.radians((45,65,65))
    high[18] = math.radians(60)
history = []
if '--thumb-axis' in sys.argv and '--reuse' not in sys.argv:
    old = json.loads((R / 'G2PalmarGrip/IndependentFingerControl/StaticControl.json').read_text())
    params = np.array(old['params'])
    if '--cmc' in sys.argv:
        params = np.append(params, math.radians(40))
    if '--opposition' in sys.argv:
        params = np.append(params, 0.)
    best = float('inf'); winner = None
    cmc_angles = (0, 20, 40, 60, 75) if '--cmc' in sys.argv else (0,)
    grid = itertools.product((-40,0,40),(0,20,40),(0,30,60),(0,30,60),(0,30,60),(-70,-35,0,35,70)) if '--opposition' in sys.argv else itertools.product((-50, -25, 0, 25, 50), (0, 20, 40, 60), (0, 25, 50, 75), (0, 25, 50, 75), cmc_angles)
    for angles in grid:
        q = params.copy(); q[14:18] = np.radians(angles[:4])
        if '--cmc' in sys.argv:
            q[18] = math.radians(angles[4])
        if '--opposition' in sys.argv:
            q[19] = math.radians(angles[5])
        score = metric(q, digit='thumb')
        if score < best:
            best, winner = score, q
    params = winner
    print('THUMB_COARSE_RESULT',metric(params,True),flush=True)
if '--coarse' in sys.argv:
    # The max penetration of an unrelated digit made the joint fit flat. Fit
    # each digit independently for each wrist offset, then judge the whole hand.
    candidates = []
    for x, y in itertools.product((-.012, 0., .012), (.07, .085, .10)):
        trial = seed.copy(); trial[:2] = (x, y)
        for fi, digit in enumerate(digits):
            best = float('inf'); winner = None
            for angles in itertools.product((10, 30, 50, 70), (35, 60, 85, 105), (10, 35, 60, 85)):
                q = trial.copy(); q[2+fi*3:5+fi*3] = np.radians(angles)
                score = metric(q, digit=digit)
                if score < best:
                    best, winner = score, q
            trial = winner
        best = float('inf'); winner = None
        for angles in itertools.product((-50, -25, 0, 25, 50), (0, 30, 60), (0, 35, 70), (0, 35, 70)):
            q = trial.copy(); q[14:] = np.radians(angles)
            score = metric(q, digit='thumb')
            if score < best:
                best, winner = score, q
        trial = winner
        candidates.append((metric(trial), trial))
        print('PALMAR_COARSE', x, y, metric(trial, True), flush=True)
    params = min(candidates, key=lambda c:c[0])[1]
if '--reuse' in sys.argv:
    params = np.array(json.loads((O / 'StaticControl.json').read_text())['params'])
if '--fit' in sys.argv and '--reuse' not in sys.argv:
    for scale in (1, .5, .25, .125):
        increments = np.array([.004, .004] + [math.radians(8)] * (len(params)-2)) * scale
        for iteration in range(20):
            changed = False
            for j in range(len(params)):
                best, winner = metric(params), None
                for sign in (-1, 1):
                    trial = params.copy()
                    trial[j] = np.clip(trial[j] + sign * increments[j], low[j], high[j])
                    score = metric(trial)
                    if score < best - 1e-12:
                        best, winner = score, trial
                if winner is not None:
                    params, changed = winner, True
            history.append({'scale':scale, 'iteration':iteration, 'metric':metric(params, True)})
            if not changed:
                break
        print('PALMAR_FIT', scale, metric(params, True), flush=True)
after = posed(params)
apply(after)
evaluated = hands.evaluated_get(bpy.context.evaluated_depsgraph_get())
actual = np.array([tuple(hands.matrix_world @ evaluated.data.vertices[int(i)].co) for i in ids])
predicted = skin(np.array([after[n] for n in names]) @ inverse_rest, local_mesh)
cpu_error_mm = float(np.linalg.norm(actual - predicted, axis=1).max() * 1000)
assert cpu_error_mm < .01, cpu_error_mm
all_points = skin(np.array([after[n] for n in names]) @ inverse_rest, mesh)
right_tri = triangles[np.all(right[triangles], axis=1)]
radius = triangle_radii(all_points, right_tri)
trees = {d: BVHTree.FromPolygons(all_points.tolist(), triangles[np.all(mask[triangles], axis=1)].tolist(), all_triangles=True) for d, mask in digit_masks.items()}
from itertools import combinations
overlaps = {a+'/'+b:len(trees[a].overlap(trees[b])) for a,b in combinations(trees,2)}
report = {'sources': guard, 'cpu_skin_error_mm':cpu_error_mm, 'seed_metric':metric(seed, True), 'after':metric(params, True), 'params':params.tolist(), 'history':history,
          'before_bend':bend_directions(before), 'after_bend':bend_directions(after),
          'thumb_bones':{n:{'rest':list(rest[n].translation),'before':list(before[n].translation),'after':list(after[n].translation)} for n in names if n.startswith('thumb_') and n.endswith('_r')},
          'palmar_world':list(palm), 'pole_offset_from_hand_palmar_mm':(-after['hand_r'].translation).dot(palm)*1000,
          'triangle_pole_min_gap_mm':float((radius.min()-.025)*1000), 'cross_digit_pairs':overlaps,
          'scope':'Unsaved static control. Correct signed finger curl and palm-side target. No full-motion or artistic acceptance.'}
if '--reuse' in sys.argv:
    assert '--opposition' in sys.argv
    finger_names = [n for n in names if n.endswith('_r') and n.startswith((*[d+'_' for d in digits], 'thumb_'))]
    calibration = {'sources':guard, 'hand_world_matrix':[list(row) for row in after['hand_r']],
                   'translation':list(params[:2]) + [0.],
                   'finger_local_matrices':{n:[list(row) for row in (after[parent[n]] @ relative[n]).inverted() @ after[n]] for n in finger_names},
                   'static_control':report, 'scope':'Private candidate only. Full motion, release and artistic acceptance pending.'}
    destination = O / 'ControlCalibration.json'
    assert not destination.exists(), 'Preserve recorded control'
    destination.write_text(json.dumps(calibration,indent=2))
    print('PALMAR_CALIBRATION', destination, flush=True)
    sys.exit(0)
s.render.engine = 'BLENDER_WORKBENCH'
s.display.shading.light = 'STUDIO'
s.display.shading.color_type = 'MATERIAL'
s.display.shading.show_cavity = False
s.display.shading.background_type = 'WORLD'
s.world = bpy.data.worlds.new('PalmarGripWorld')
s.world.color = (.035,.045,.055)
s.render.resolution_x = s.render.resolution_y = 800
s.render.resolution_percentage = 100
for ob in s.objects:
    if ob.type == 'MESH':
        ob.hide_render = ob != hands
hands.data.materials.clear()
for name, color in [('Grey',(.55,.55,.55,1)),('Thumb_Cyan',(0,.85,1,1)),('Pinky_Violet',(.6,.08,.85,1))]:
    mat=bpy.data.materials.new(name);mat.diffuse_color=color;hands.data.materials.append(mat)
for face in hands.data.polygons:
    face.material_index = 1 if np.mean(digit_masks['thumb'][list(face.vertices)])>.5 else 2 if np.mean(digit_masks['pinky'][list(face.vertices)])>.5 else 0
bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.025,depth=5,location=(0,0,2.5))
pole=bpy.context.object;mat=bpy.data.materials.new('OrangePole');mat.diffuse_color=(1,.12,0,1);pole.data.materials.append(mat)
bpy.ops.object.camera_add();camera=bpy.context.object;s.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=.36
for state, p in [('before',before),('palmar_control',after)]:
    apply(p)
    for view, direction in [('palm',Vector((.3,-1,.15))),('back',Vector((-.3,1,.15))),('above',Vector((.1,-.2,1)))]:
        center=Vector((0,0,3));camera.location=center+direction.normalized()*3;camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
        s.render.filepath=str(O/f'{state}_{view}.png');bpy.ops.render.render(write_still=True)
(O/'StaticControl.json').write_text(json.dumps(report,indent=2))
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in guard.items())
print('PALMAR_RESULT', {k:v for k,v in report.items() if k!='history'}, flush=True)
