"""Opposing hidden views of the unsaved palmar-motion control."""
import hashlib
import json
import math
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from g2_palmar_motion_control import PalmarControl, options
import bpy
import numpy as np
from mathutils import Vector
model=PalmarControl(*options());s=model.scene
saved='--saved' in sys.argv
movie='--movie' in sys.argv
if saved:
    knots='--source-knots' in sys.argv
    manifest=json.loads((model.source/('G2_PalmarGrip_Knots_Manifest.json' if knots else 'G2_PalmarGrip_Manifest.json')).read_text())
    assert manifest['sources']==model.guards
    source=model.source/manifest['file']
    assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['sha256']
    with bpy.data.libraries.load(str(source),link=False) as (_,loaded):loaded.actions=[manifest['action']]
    candidate=loaded.actions[0]
    model.output=model.review/('G2PalmarGrip/SavedKnotsReview' if knots else 'G2PalmarGrip/SavedReview')
    model.output.mkdir(exist_ok=True)
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO'
s.display.shading.color_type='OBJECT';s.display.shading.show_cavity=False
s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('PalmarMotionWorld');s.world.color=(.035,.045,.055)
s.render.resolution_x=s.render.resolution_y=800;s.render.resolution_percentage=100
for ob in s.objects:
    if ob.type=='MESH':ob.color=(.55,.55,.55,1)
bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.025,depth=5,location=(0,0,2.5))
pole=bpy.context.object;pole.color=(1,.12,0,1)
bpy.ops.object.camera_add();camera=bpy.context.object;s.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=2.4
times=(0.,1.333333,1.666667,2.,3.666667,10.666667,29.333333,29.666667,30.333333,31.)
if saved:
    times=[float(np.interp(t,manifest['source_seconds_map'],manifest['destination_seconds_map'])) for t in times]
if movie:
    assert saved
    times=np.arange(math.floor(manifest['seconds']*12)+1)/12
    for name in ('front','back'):(model.output/name).mkdir(exist_ok=True)
for index,seconds in enumerate(times):
    if saved:
        model.rig.animation_data.action=candidate;model.rig.animation_data.action_slot=candidate.slots[0]
        frame=1+seconds*manifest['fps'];s.frame_set(math.floor(frame),subframe=frame%1);bpy.context.view_layer.update()
        pose={b.name:model.rig.matrix_world@b.matrix for b in model.ordered}
    else:
        pose,_,_=model.pose(seconds);model.apply(pose)
    center=(pose['pelvis'].translation+pose['spine_05'].translation)*.5
    for view,delta in [('front',Vector((4,-6,2))),('back',Vector((-4,6,2)))]:
        camera.location=center+delta;camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
        s.render.filepath=str(model.output/view/f'{index:05d}.png') if movie else str(model.output/f't{seconds:.3f}_{view}.png')
        bpy.ops.render.render(write_still=True)
model.assert_guards()
if saved:
    assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['sha256']
