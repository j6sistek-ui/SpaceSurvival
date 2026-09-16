"""Derive broken ring silhouettes from owned Station3; originals never saved.

Run using the installed Blender --background --factory-startup --python.
Only private derivatives/previews under .agent/local/OrbitalWreck are written.
"""
import hashlib
import json
import math
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / '.agent/local/StationVisualPass/Station3Exterior.glb'
OUT = ROOT / '.agent/local/OrbitalWreck'
OUT.mkdir(parents=True, exist_ok=True)
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
original = digest(SOURCE)
reports = []
for name, start, end in [('BrokenArc', -70, 80), ('RingFragment', 110, 158)]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(SOURCE))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bm = bmesh.new(); bm.from_mesh(obj.data)
    # Keep a jagged angular sector; triangles retain original material and UV data.
    discard = []
    for f in bm.faces:
        c = f.calc_center_median()
        angle = math.degrees(math.atan2(c.y, c.x))
        if not start <= angle <= end:
            discard.append(f)
    bmesh.ops.delete(bm, geom=discard, context='FACES')
    bm.to_mesh(obj.data); bm.free()
    low = Vector([min(v.co[i] for v in obj.data.vertices) for i in range(3)])
    high = Vector([max(v.co[i] for v in obj.data.vertices) for i in range(3)])
    middle = (low + high) * .5
    for v in obj.data.vertices:
        v.co -= middle
    obj.name = 'SM_' + name
    path = OUT / (name + '.glb')
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True,
                              export_animations=False, export_normals=True, export_tangents=True)
    reports.append(dict(name=name, triangles=sum(len(p.vertices)-2 for p in obj.data.polygons),
                        source_sha256=original, output_sha256=digest(path)))
assert digest(SOURCE) == original
# Use an actual structural member from the owned Figur kit. Reuse its privately
# baked metal atlas; do not export Blender-only procedural shaders as blank PBR.
bpy.ops.wm.read_factory_settings(use_empty=True)
baked = ROOT/'.agent/local/StationVisualPass/FigurStationExterior.glb'
bpy.ops.import_scene.gltf(filepath=str(baked))
metal = next(m for m in bpy.data.materials if 'M_Figur_0' in m.name)
for obj in list(bpy.context.scene.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
kit = ROOT/'User downloaded assets/VaultCache/FabLibrary/Sci_Fi_SPACE_STATION_Kitbash___3D_Kitbash_Asset_Pack___Blender-9af3878b/blender/space_station_kit.blend'
kit_hash = digest(kit)
with bpy.data.libraries.load(str(kit), link=False) as (src, dst):
    dst.objects = ['Cube_RLExtr.098']
beam = dst.objects[0]; assert beam
bpy.context.scene.collection.objects.link(beam)
world = beam.matrix_world.copy(); beam.parent = None; beam.matrix_world = world
beam.animation_data_clear()
beam.data.materials.clear(); beam.data.materials.append(metal)
bpy.context.view_layer.objects.active = beam; beam.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
middle = sum((v.co for v in beam.data.vertices), Vector()) / len(beam.data.vertices)
for v in beam.data.vertices:
    v.co -= middle
beam.name = 'SM_KitBeam'
path = OUT/'KitBeam.glb'
bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True,
                          export_animations=False, export_normals=True, export_tangents=True)
assert digest(kit) == kit_hash
reports.append(dict(name='KitBeam', source_object='Cube_RLExtr.098', source_sha256=kit_hash,
                    triangles=sum(len(p.vertices)-2 for p in beam.data.polygons),
                    material='Existing private Figur metal atlas', output_sha256=digest(path)))
(OUT/'derivatives.json').write_text(json.dumps(reports, indent=2), encoding='utf-8')
print('ORBITAL_WRECK_DERIVED', json.dumps(reports))
