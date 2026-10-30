"""Review measured G2 hold overlap with unchanged grip and bounded contacts."""
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from g2_floating_life_control import FloatingLifeControl
from validate_g2_contact_recipe import geometry, skin, triangle_radii

phrase = '--phrase' in sys.argv
source_legs = '--source-legs' in sys.argv
source_phrase = '--source-phrase' in sys.argv
assert not (source_legs and source_phrase)
if source_phrase:
    from g2_source_phrase_control import SourcePhraseControl
    model = SourcePhraseControl()
    variant = 'SourcePhraseCurrentLeg'
    control_file = 'g2_source_phrase_control.py'
elif source_legs:
    from g2_source_leg_control import SourceLegControl
    model = SourceLegControl()
    variant = 'SourceLegControl'
    control_file = 'g2_source_leg_control.py'
else:
    model = FloatingLifeControl(phrase=phrase)
    variant = 'PhraseControl' if phrase else 'OverlapControl'
    control_file = 'g2_floating_life_control.py'
out = model.project / '.agent/local/AnimationReview_20261025/G2FloatingLife' / variant
out.mkdir(parents=True, exist_ok=True)
render = '--render' in sys.argv
diagnostic = '--diagnostic' in sys.argv
assert not diagnostic or render, 'Diagnostic mode only renders retained failures'
audit_root = out
framed = '--framed' in sys.argv
if framed:
    assert render and (phrase or source_legs or source_phrase)
    out = out / ('DiagnosticFramed' if diagnostic else 'Framed')
    out.mkdir(exist_ok=True)
receipt = out / ('Motion.json' if render else 'Audit.json')
assert not receipt.exists(), 'Preserve prior evidence'
control_hash = hashlib.sha256(Path(__file__).with_name(control_file).read_bytes()).hexdigest()

if not render:
    meshes = geometry(model)
    inverse = np.array([model.rest[n].inverted() for n in model.names])
    lower = bpy.data.objects['Vexa_Continuous_Feet']
    rest = np.array([tuple(lower.matrix_world @ v.co) for v in lower.data.vertices])
    weights = [{lower.vertex_groups[g.group].name: g.weight for g in v.groups} for v in lower.data.vertices]
    lower.data.calc_loop_triangles()
    tri = np.array([t.vertices for t in lower.data.loop_triangles])
    adjacent = [set([v.index]) for v in lower.data.vertices]
    for edge in lower.data.edges:
        a, b = edge.vertices; adjacent[a].add(b); adjacent[b].add(a)
    regions = {}
    for side, sign in [('l', 1), ('r', -1)]:
        hip = np.array([sum(w for n, w in d.items() if n in ('pelvis', 'glute_'+side)) for d in weights])
        thigh = np.array([sum(w for n, w in d.items() if n in ('thigh_'+side, 'thigh_twist_01_'+side)) for d in weights])
        posterior = (rest[:, 1]>.015)&(rest[:, 2]>.84)&(rest[:, 2]<1.07)&(sign*rest[:, 0]>-.006)
        regions[side] = (tri[np.all((hip>.35)[tri], axis=1)&np.any(posterior[tri], axis=1)],
                         tri[np.all((thigh>.65)[tri], axis=1)&np.any((rest[:, 2]>.70)[tri], axis=1)])
    rows = []; flags = []; preserved_error = 0.; endpoint_error = 0.
    times = np.unique(np.r_[np.arange(0, model.duration, 1/15), model.duration])
    moving = set(sum([model.descendants[n] for n in ('thigh_l', 'thigh_r', 'lowerarm_l')], [])) | {'glute_l', 'glute_r'}
    if source_phrase:
        moving = model.moving
    for index, seconds in enumerate(times):
        pose, base, offsets = model.pose(float(seconds))
        preserved_error = max(preserved_error, max(float(np.abs(np.array(pose[n])-np.array(base[n])).max()) for n in model.names if n not in moving))
        if not offsets:
            endpoint_error = max(endpoint_error, max(float(np.abs(np.array(pose[n])-np.array(base[n])).max()) for n in model.names))
        matrices = np.array([pose[n] for n in model.names]) @ inverse
        body_v = []; body_f = []; arm_v = []; arm_f = []; pole = {}; hips = {}
        for mesh in meshes:
            name, _, faces, _, _, body, arms = mesh
            points = skin(matrices, mesh)
            radius = triangle_radii(points, faces); z = points[faces, 2]
            bad = (radius < .025-.00001)&(z.max(axis=1)>0)&(z.min(axis=1)<5)
            if bad.any(): pole[name] = {'count': int(bad.sum()), 'depth_mm': float((.025-radius[bad]).max()*1000)}
            if len(body):
                offset = len(body_v); body_v.extend(points.tolist()); body_f.extend((body+offset).tolist())
            if len(arms):
                offset = len(arm_v); arm_v.extend(points.tolist()); arm_f.extend((arms+offset).tolist())
            if name == lower.name:
                for side, (ht, tt) in regions.items():
                    overlaps = BVHTree.FromPolygons(points.tolist(), ht.tolist(), all_triangles=True).overlap(BVHTree.FromPolygons(points.tolist(), tt.tolist(), all_triangles=True))
                    hips[side] = sum(not any(j in adjacent[i] for i in ht[a] for j in tt[b]) for a, b in overlaps)
        contacts = BVHTree.FromPolygons(body_v, body_f, all_triangles=True).overlap(BVHTree.FromPolygons(arm_v, arm_f, all_triangles=True))
        local = {n: pose[model.parents[n]].inverted()@pose[n] if model.parents[n] else pose[n] for n in model.names}
        knees = {side: math.degrees((pose['calf_'+side].translation-pose['thigh_'+side].translation).angle(pose['foot_'+side].translation-pose['calf_'+side].translation)) for side in ('l','r')}
        row = {'seconds': float(seconds), 'offsets': offsets, 'pole': pole, 'arm_body_pairs': len(contacts), 'hip_pairs': hips, 'knees': knees,
               'local_quaternions': {n: list(local[n].to_quaternion().normalized()) for n in ('thigh_l','calf_l','foot_l','thigh_r','calf_r','foot_r','lowerarm_l','hand_l')}}
        rows.append(row)
        if pole or contacts or any(hips.values()): flags.append({k: v for k, v in row.items() if k != 'local_quaternions'})
        if index % 150 == 0: print('FLOATING_CHECK', index, len(flags), flush=True)
    windows = []
    for start in range(0, 50, 2):
        selected = [r for r in rows if start <= r['seconds'] <= start+2]
        q = np.array([list(r['local_quaternions'].values()) for r in selected]); q /= np.linalg.norm(q, axis=2)[:, :, None]
        angles = np.degrees(2*np.arccos(np.clip(np.abs((q*q[0]).sum(axis=2)), 0, 1)))
        windows.append({'start': start, 'ranges_degrees': dict(zip(selected[0]['local_quaternions'], angles.max(axis=0).tolist()))})
    report = {'passed': not flags and preserved_error < 1e-7 and endpoint_error < 1e-7, 'samples': len(rows),
              'sources': model.guards, 'control_sha256': control_hash, 'preserved_bone_matrix_error': preserved_error,
              'outside_window_matrix_error': endpoint_error, 'flags': flags, 'movement_windows': windows,
              'both_knees_below15_fraction': sum(max(r['knees'].values())<15 for r in rows)/len(rows),
              'recipe_variant': variant,
              'scope': ('15Hz pole, distal arm/body and bounded posterior hip screens. Existing released return only; original root/outside-window poses exact. Pelvis route preserved, body rotations changed. No complete anatomy, native or artistic acceptance.' if source_phrase else
                        '15Hz pole, distal arm/body and bounded posterior hip contact screens. Original grip, shoulders, spine and outside-window poses exact. Not complete anatomy, native or artistic acceptance.')}
    receipt.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('FLOATING_RESULT', {k:v for k,v in report.items() if k not in ('sources','movement_windows','flags')}, 'flags', len(flags), flush=True)
    model.assert_guards()
    assert report['passed'], flags[:3]
else:
    audit = json.loads((audit_root/'Audit.json').read_text(encoding='utf-8'))
    assert (audit['passed'] or diagnostic) and audit['control_sha256'] == control_hash
    scene = model.scene
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'; scene.display.shading.color_type = 'OBJECT'
    scene.display.shading.show_cavity = False; scene.display.shading.background_type = 'WORLD'
    scene.world = bpy.data.worlds.new('FloatingOverlapReview'); scene.world.color = (.035,.045,.055)
    scene.render.resolution_x = scene.render.resolution_y = 700; scene.render.resolution_percentage = 100
    for ob in scene.objects:
        if ob.type == 'MESH': ob.color = (.55,.55,.55,1)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=.025, depth=5, location=(0,0,2.5))
    pole = bpy.context.object; pole.color = (1,.12,0,1)
    bpy.ops.object.camera_add(); camera = bpy.context.object; scene.camera = camera
    camera.data.type = 'ORTHO'; camera.data.ortho_scale = 3.3
    center = Vector((.5,-.65,3.1))
    clips = [('opening',0.,6.8),('swing',34.,42.5)]
    if source_legs:
        clips.append(('return',47.,model.duration))
    if source_phrase:
        clips = [('return',46.5,model.duration)]
    for view, direction in [('front',Vector((4,-6,2))),('back',Vector((-4,6,2)))]:
        camera.location = center+direction; camera.rotation_euler = (center-camera.location).to_track_quat('-Z','Y').to_euler()
        for label, start, end in clips:
            if framed:
                # Fit a fixed camera to the whole passage, including its exit.
                # Joint bounds get a margin for skinned surfaces/clothing.
                rotation = (-direction).to_track_quat('-Z','Y')
                right, up = rotation @ Vector((1,0,0)), rotation @ Vector((0,1,0))
                forward = direction.normalized()
                points = [m.translation for t in np.r_[np.arange(start,end,1/12),end]
                          for m in model.pose(float(t))[0].values()]
                projected = np.array([[p.dot(right),p.dot(up),p.dot(forward)] for p in points])
                low, high = projected.min(axis=0), projected.max(axis=0)
                middle = (low+high)/2
                focus = right*middle[0]+up*middle[1]+forward*middle[2]
                camera.location = focus+forward*8
                camera.rotation_euler = rotation.to_euler()
                camera.data.ortho_scale = float(max(high[:2]-low[:2])+.5)
            folder = out/(view+'_'+label); folder.mkdir(exist_ok=False)
            for i in range(round((end-start)*24)+1):
                model.apply(model.pose(start+i/24)[0])
                scene.render.filepath = str(folder/f'{i:04d}.png'); bpy.ops.render.render(write_still=True)
    receipt.write_text(json.dumps({'sources':model.guards,'control_sha256':control_hash,'fps':24,'clips':clips,
        'audit_passed':audit['passed'],'diagnostic_only':diagnostic,
        'views':['front','back'],'scope':'Unsaved control motion; Blender source renderer, not native/runtime acceptance.'},indent=2), encoding='utf-8')
    model.assert_guards()
