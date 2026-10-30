"""Fresh G1 shoulder proof: matched renders and a decoded-motion source set.

No source edits. The before/after toggle changes only the new corrective keys.
"""
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

project = Path(os.environ.get('SS_ANIMATION_PROJECT', str(Path.home()/'SpaceSurvival'))).resolve()
review = project/'.agent/local/AnimationReview_20261025'/('G1ShoulderCapCorrective' if '--cap' in sys.argv else 'G1ShoulderCorrective')
record = json.loads((review/'Bake.json').read_text(encoding='utf-8'))
path = Path(record['file'])
assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256']
manifest = json.loads((project/'SourceAssets/DanceRefinement_20261025/G1_PalmarGrip_Knots_Manifest.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)
scene = bpy.context.scene
rig = next(ob for ob in scene.objects if ob.type == 'ARMATURE')
body = bpy.data.objects['Vexa_Continuous_Hands']
keys = [k for k in body.data.shape_keys.key_blocks if k.name.startswith('REVIEW_G1_LeftAxilla_')]
assert len(keys) == record['rank']
assert rig.animation_data.action.name == record['action']
assert body.data.shape_keys.animation_data.action.name == record['shape_action']
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (.55, .55, .55)
scene.display.shading.show_cavity = False
scene.display.shading.background_type = 'WORLD'
scene.world = bpy.data.worlds.new('SavedG1ShoulderReview')
scene.world.color = (.035, .045, .055)
scene.render.resolution_x = scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
bpy.ops.object.camera_add()
camera = bpy.context.object
scene.camera = camera
camera.data.type = 'ORTHO'
camera.data.ortho_scale = .95
rest_chest = rig.matrix_world @ rig.data.bones['spine_05'].matrix_local

def seek(seconds):
    frame = 1+seconds*manifest['fps']
    scene.frame_set(math.floor(frame), subframe=frame%1)
    bpy.context.view_layer.update()

def aim(view):
    chest = rig.matrix_world @ rig.pose.bones['spine_05'].matrix
    rotation = (chest @ rest_chest.inverted()).to_quaternion()
    shoulder = (rig.matrix_world @ rig.pose.bones['upperarm_l'].matrix).translation
    center = chest.translation*.65+shoulder*.35
    delta = {'front': Vector((.9, -3, .35)), 'back': Vector((.9, 3, .35)),
             'side': Vector((3, -.7, .25))}[view]
    camera.location = center+rotation @ delta
    camera.rotation_euler = (rotation @ (-delta).to_track_quat('-Z', 'Y')).to_euler()

if '--lighting-control' in sys.argv:
    destination = float(np.interp(7.254899317387129, manifest['source_seconds_map'], manifest['destination_seconds_map']))
    seek(destination)
    for variant in ('current', 'no_shadows', 'body_only', 'geometric_normals'):
        scene.display.shading.show_shadows = variant != 'no_shadows'
        if variant == 'body_only':
            for ob in scene.objects:
                if ob.type == 'MESH':
                    ob.hide_render = ob != body
        if variant == 'geometric_normals':
            evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
            data = bpy.data.meshes.new('REVIEW_GeometricNormals')
            data.from_pydata([tuple(v.co) for v in evaluated.data.vertices], [],
                             [tuple(p.vertices) for p in evaluated.data.polygons])
            for polygon in data.polygons:
                polygon.use_smooth = True
            data.update()
            copy = bpy.data.objects.new('REVIEW_GeometricNormals', data)
            scene.collection.objects.link(copy)
            copy.matrix_world = body.matrix_world.copy()
            body.hide_render = True
        aim('front')
        scene.render.filepath = str(review/f'lighting_{variant}.png')
        bpy.ops.render.render(write_still=True)
    print('SHOULDER_NORMAL_STATE', body.data.has_custom_normals, flush=True)
elif '--video' in sys.argv:
    scene.render.resolution_x = scene.render.resolution_y = 640
    count = math.ceil(manifest['seconds']*24)+1
    for view in ('front', 'back'):
        folder = review/('motion_'+view)
        folder.mkdir(exist_ok=True)
        for i in range(count):
            seek(min(manifest['seconds'], i/24))
            aim(view)
            scene.render.filepath = str(folder/f'{i:04d}.png')
            bpy.ops.render.render(write_still=True)
else:
    for seconds in (0., 3., 7.254899317387129, 8.4166667, 11.69, 12.27, 16.123):
        destination = float(np.interp(seconds, manifest['source_seconds_map'], manifest['destination_seconds_map']))
        seek(destination)
        for variant in ('before', 'after'):
            for key in keys:
                key.mute = variant == 'before'
            bpy.context.view_layer.update()
            for view in ('front', 'side', 'back'):
                aim(view)
                scene.render.filepath = str(review/f't{seconds:.3f}_{variant}_{view}.png')
                bpy.ops.render.render(write_still=True)
assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256']
print('SAVED_G1_SHOULDER_REVIEW_DONE', flush=True)
