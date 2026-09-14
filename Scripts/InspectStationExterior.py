"""Read-only Blender inspection of the locally licensed Space Station 4 GLB.
Run with Blender --background --factory-startup --python Scripts/InspectStationExterior.py.
Only Artifacts/StationExterior is written; the source GLB remains unchanged.
"""
import hashlib
import json
import math
from pathlib import Path
import bpy
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'User downloaded assets/VaultCache/FabLibrary/Space_Station_4-a50ebf13/glb/converted/space_station_4.glb'
OUT = ROOT/'Artifacts/StationExterior'
OUT.mkdir(parents=True,exist_ok=True)
source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
meshes = [o for o in bpy.context.scene.objects if o.type=='MESH']
body_meshes = [o for o in meshes if any(m and m.name != 'Emission' for m in o.data.materials)]
points = [o.matrix_world @ Vector(c) for o in body_meshes for c in o.bound_box]
low = Vector([min(v[i] for v in points) for i in range(3)])
high = Vector([max(v[i] for v in points) for i in range(3)])
center = (low+high)*.5
size = high-low
triangles = 0
for o in meshes:
    o.data.calc_loop_triangles()
    triangles += len(o.data.loop_triangles)
report = dict(source=str(SOURCE.relative_to(ROOT)),sha256=source_hash,bytes=SOURCE.stat().st_size,
    mesh_objects=len(meshes),triangles=triangles,body_mesh_objects=len(body_meshes),bounds_exclude='Isolated Emission-only geometry surrounding main station',bounds_min=list(low),bounds_max=list(high),size=list(size),
    materials=[m.name for m in bpy.data.materials],
    images=[dict(name=i.name,size=list(i.size),channels=i.channels) for i in bpy.data.images],
    note='Blender source-unit dimensions; normalized only in inspection scene. No Unreal fit/import validated.')
# Detach each mesh while preserving its evaluated imported transform. Normalize preview only.
normalization = Matrix.Scale(20/max(size),4) @ Matrix.Translation(-center)
for obj in meshes:
    if obj not in body_meshes:
        obj.hide_render = True
    transform = obj.matrix_world.copy()
    obj.parent = None
    obj.matrix_world = normalization @ transform
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.device='CPU'
scene.cycles.samples=12
scene.cycles.use_denoising=True
scene.render.resolution_x=960
scene.render.resolution_y=720
scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('InspectionWorld')
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.055,.07,.10,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
for name,loc,power,color,size_l in [('Key',(5,-12,15),2300,(.85,.92,1),12),('Fill',(-10,5,8),1800,(1,.72,.4),10),('Rim',(0,12,2),2000,(.5,.7,1),8)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.shape='DISK';data.size=size_l
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=loc
    obj.rotation_euler=(-obj.location).to_track_quat('-Z','Y').to_euler()
camera_data=bpy.data.cameras.new('InspectionCamera');camera=bpy.data.objects.new('InspectionCamera',camera_data)
scene.collection.objects.link(camera);scene.camera=camera;camera_data.type='ORTHO';camera_data.ortho_scale=25
for name,loc in [('diagonal',(22,-28,18)),('axis_x',(30,0,5)),('axis_y',(0,-30,5))]:
    camera.location=loc;camera.rotation_euler=(-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(OUT/(name+'.png'))
    bpy.ops.render.render(write_still=True)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash
(OUT/'inspection.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('STATION_EXTERIOR_INSPECTED',json.dumps(report))
