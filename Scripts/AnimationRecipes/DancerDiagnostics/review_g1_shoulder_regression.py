"""Isolate G1 shoulder skin, garment and pose against the preserved shoulder mesh.

Read-only Blender comparison. Never saves a blend or changes source weights.
"""
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from g1_palmar_motion_control import G1PalmarControl

model = G1PalmarControl(False, True, True, True)
scene = model.scene
output = model.review / 'G1ShoulderIsolation'
output.mkdir(exist_ok=True)
source = model.source / 'Vexa_ShoulderBalanced_Proof.blend'
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
assert source_hash.startswith('844aae5f')
body = bpy.data.objects['Vexa_Continuous_Hands']
top = bpy.data.objects['Vexa_Top']
report = {'scope': 'Matched G1 skin and clothing comparison; no source saved.',
          'preserved_shoulder_source': str(source), 'sha256': source_hash,
          'current_sources': model.guards, 'meshes': {}, 'poses': []}
for ob in (body, top):
    report['meshes'][ob.name] = {
        'vertices': len(ob.data.vertices),
        'active_shapes': {k.name: k.value for k in ob.data.shape_keys.key_blocks
                          if abs(k.value) > 1e-7 and not k.mute} if ob.data.shape_keys else {},
        'modifiers': [(m.name, m.type) for m in ob.modifiers]}
with bpy.data.libraries.load(str(source), link=False) as (_, loaded):
    loaded.objects = ['Vexa_Nude_Torso']
approved = loaded.objects[0]
scene.collection.objects.link(approved)
world = approved.matrix_world.copy()
approved.parent = None
approved.matrix_world = world
for modifier in approved.modifiers:
    if modifier.type == 'ARMATURE':
        modifier.object = model.rig
if approved.data.shape_keys:
    approved.data.shape_keys.animation_data_clear()
    for key in approved.data.shape_keys.key_blocks:
        if key.name.startswith('REVIEW_'):
            key.value = 0
            key.mute = True

# Compare only common torso vertices; the current mesh additionally joins hands.
tree = KDTree(len(body.data.vertices))
for vertex in body.data.vertices:
    tree.insert(body.matrix_world @ vertex.co, vertex.index)
tree.balance()
def weights(ob, i):
    return {ob.vertex_groups[g.group].name: g.weight for g in ob.data.vertices[i].groups
            if ob.vertex_groups[g.group].name in model.names}
comparisons = []
for vertex in approved.data.vertices:
    point = approved.matrix_world @ vertex.co
    _, index, distance = tree.find(point)
    if distance < 1e-5:
        a, b = weights(approved, vertex.index), weights(body, index)
        comparisons.append(sum(abs(a.get(n, 0)-b.get(n, 0)) for n in set(a)|set(b)))
report['common_torso'] = {'matched': len(comparisons),
                          'old_vertices': len(approved.data.vertices),
                          'max_weight_L1': max(comparisons, default=None)}

scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (.55, .55, .55)
scene.display.shading.show_cavity = False
scene.display.shading.background_type = 'WORLD'
scene.world = bpy.data.worlds.new('ShoulderIsolationWorld')
scene.world.color = (.035, .045, .055)
scene.render.resolution_x = scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
visible = {ob: ob.hide_render for ob in scene.objects if ob.type == 'MESH'}
bpy.ops.object.camera_add()
camera = bpy.context.object
scene.camera = camera
camera.data.type = 'ORTHO'
camera.data.ortho_scale = .68

for seconds in (3., 8.4166667):
    candidate, baseline, phase = model.pose(seconds)
    # Register the original to the same chest frame for a fair local comparison.
    transform = candidate['spine_05'] @ baseline['spine_05'].inverted()
    baseline = {n: transform @ m for n, m in baseline.items()}
    report['poses'].append({'seconds': seconds, **phase})
    for pose_name, pose in (('original', baseline), ('contact_relief', candidate)):
        model.apply(pose)
        chest = pose['spine_05'] @ model.rest['spine_05'].inverted()
        rotation = chest.to_quaternion()
        center = (pose['upperarm_l'].translation * .6 + pose['spine_05'].translation * .4)
        for version in ('current_clothed', 'current_body', 'preserved_body'):
            for ob in visible:
                ob.hide_render = True
            selected = approved if version == 'preserved_body' else body
            selected.hide_render = False
            if version == 'current_clothed':
                top.hide_render = False
            for view, delta in (('front', Vector((.7, -3, .45))),
                                ('back', Vector((.7, 3, .45)))):
                camera.location = center + rotation @ delta
                camera.rotation_euler = (center-camera.location).to_track_quat('-Z', 'Y').to_euler()
                scene.render.filepath = str(output / f't{seconds:.3f}_{pose_name}_{version}_{view}.png')
                bpy.ops.render.render(write_still=True)

model.assert_guards()
assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
(output / 'Report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('SHOULDER_ISOLATION_DONE', json.dumps(report['common_torso']), flush=True)
