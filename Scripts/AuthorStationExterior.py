"""Prepare a private exterior derivative; originals and PBR structure are preserved.
Blender --background --factory-startup --python Scripts/AuthorStationExterior.py
"""
from pathlib import Path
import hashlib
import json
import struct
import bpy
from mathutils import Vector, Matrix

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Artifacts/StationExterior'
SOURCE=ROOT/'User downloaded assets/VaultCache/FabLibrary/Space_Station_4-a50ebf13/glb/converted/space_station_4.glb'
OUT.mkdir(parents=True,exist_ok=True)
digest=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
body=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m and m.name!='Emission' for m in o.data.materials)]
assert len(body)==19
points=[o.matrix_world@Vector(c) for o in body for c in o.bound_box]
lo=Vector([min(v[i] for v in points) for i in range(3)])
hi=Vector([max(v[i] for v in points) for i in range(3)])
center=(lo+hi)*.5
scale=100/(hi.x-lo.x)
normalization=Matrix.Scale(scale,4)@Matrix.Translation(-center)
triangles_before=sum(len(p.vertices)-2 for o in body for p in o.data.polygons)
bpy.ops.object.select_all(action='DESELECT')
for obj in body:
    transform=obj.matrix_world.copy()
    obj.parent=None
    obj.matrix_world=normalization@transform
    obj.select_set(True)
bpy.context.view_layer.objects.active=body[0]
bpy.ops.object.join()
mesh=bpy.context.object
mesh.name='SM_StationExterior';mesh.data.name='SM_StationExterior'
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
# Rotated source-object bounding boxes conservatively overestimate the body.
# Recenter actual transformed vertices so runtime offsets refer to true mesh bounds.
actual_center=Vector([(min(v.co[i] for v in mesh.data.vertices)+max(v.co[i] for v in mesh.data.vertices))*.5 for i in range(3)])
for vertex in mesh.data.vertices:
    vertex.co-=actual_center
assert sum(len(p.vertices)-2 for p in mesh.data.polygons)==triangles_before
textures=[]
for image in bpy.data.images:
    original=list(image.size)
    if max(original)>2048:
        image.scale(2048,2048)
        image.pack()
    textures.append(dict(name=image.name,source_size=original,output_size=list(image.size)))
target=OUT/'StationExterior.glb'
bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,
    export_animations=False,export_normals=True,export_tangents=True)
with target.open('rb') as stream:
    header=stream.read(20)
    data=json.loads(stream.read(struct.unpack_from('<I',header,12)[0]))
primitives=[p for m in data['meshes'] for p in m['primitives']]
assert len(primitives)<=3
assert all('normalTexture' in m and 'emissiveTexture' in m for m in data['materials'])
assert sum(data['accessors'][p['indices']]['count']//3 for p in primitives)==triangles_before
bounds=[[min(v.co[i] for v in mesh.data.vertices)*100 for i in range(3)],
        [max(v.co[i] for v in mesh.data.vertices)*100 for i in range(3)]]
report=dict(source_sha256=digest,output_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
    output_bytes=target.stat().st_size,triangles=triangles_before,primitives=len(primitives),
    material_names=[m['name'] for m in data['materials']],textures=textures,bounds_cm=bounds,
    axis='Longitudinal +X; rotate yaw90 at station attachment, no baked yaw',
    proposed_attachment_cm=[7000,0,3500],excluded='Detached Emission-only light-point mesh (13556 triangles)',
    pbr='Body normal, ORM, color and emissive maps retained; textures downsampled 4K to2K; no detail rebake',
    limitation='Exterior backdrop, no validated docking opening/interior or collision')
(OUT/'Derivative.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==digest
print('STATION_EXTERIOR_DERIVATIVE',json.dumps(report))
