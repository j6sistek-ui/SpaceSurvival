"""Blender-only contact sheet of the private derivatives; not gameplay evidence."""
import math
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'Artifacts/OrbitalWreck'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1200
scene.render.resolution_y = 600
scene.render.resolution_percentage = 100
scene.world = bpy.data.worlds.new('AssetReview')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.08,.10,.13,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .5
for index, name in enumerate(('BrokenArc','RingFragment','KitBeam')):
    bpy.ops.import_scene.gltf(filepath=str(ROOT/'.agent/local/OrbitalWreck'/(name+'.glb')))
    obj = next(o for o in bpy.context.selected_objects if o.type == 'MESH')
    scale = 4/max(obj.dimensions)
    obj.scale *= scale
    obj.location = ((index-1)*5,0,0)
    obj.rotation_euler = (math.radians(55),0,math.radians(-20))
    font = bpy.data.curves.new(name,'FONT'); font.body = name; font.size = .4; font.align_x = 'CENTER'
    label = bpy.data.objects.new(name+'_label',font);scene.collection.objects.link(label)
    label.location = ((index-1)*5,-.2,-2.8);label.rotation_euler = (math.pi/2,0,0)
for pos,power,color in [((0,-7,9),2500,(.75,.85,1)),((6,3,6),1800,(1,.65,.3))]:
    data=bpy.data.lights.new('ReviewLight','AREA');data.energy=power;data.shape='DISK';data.size=8;data.color=color
    light=bpy.data.objects.new('ReviewLight',data);scene.collection.objects.link(light);light.location=pos
    light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
camera=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'))
scene.collection.objects.link(camera);camera.location=(0,-19,7)
camera.rotation_euler=(-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=16
scene.camera=camera;scene.render.filepath=str(OUT/'DerivativeContact.png')
bpy.ops.render.render(write_still=True)
