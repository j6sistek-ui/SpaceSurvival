"""Read-only Blender inventory of local station packs; outputs ignored review data.

Run with the existing Blender --background --factory-startup --python script.
Original paid files are never saved or modified.
"""
import json
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "User downloaded assets/VaultCache/FabLibrary"
OUT = ROOT / ".agent/local/StationVisualPass"
OUT.mkdir(parents=True, exist_ok=True)


def inspect(key, source):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if source.suffix == ".blend":
        # Read datablocks instead of running any embedded file startup handlers.
        with bpy.data.libraries.load(str(source), link=False) as (data_from, data_to):
            data_to.objects = data_from.objects
        for obj in data_to.objects:
            if obj is not None:
                bpy.context.scene.collection.objects.link(obj)
    else:
        bpy.ops.import_scene.gltf(filepath=str(source))
    records = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        pts = [obj.matrix_world @ Vector(p) for p in obj.bound_box]
        low = [min(p[i] for p in pts) for i in range(3)]
        high = [max(p[i] for p in pts) for i in range(3)]
        records.append(dict(name=obj.name, data=obj.data.name,
                            triangles=sum(len(p.vertices)-2 for p in obj.data.polygons),
                            low=low, high=high, dimensions=[high[i]-low[i] for i in range(3)],
                            materials=[m.name if m else None for m in obj.data.materials],
                            modifiers=[m.type for m in obj.modifiers],
                            asset=bool(obj.asset_data)))
    materials = []
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            materials.append(dict(name=mat.name, nodes=False))
            continue
        materials.append(dict(name=mat.name, nodes=[dict(type=n.type, name=n.name,
            image=n.image.name if n.type == "TEX_IMAGE" and n.image else None)
            for n in mat.node_tree.nodes]))
    report = dict(source=str(source.relative_to(ROOT)), meshes=records, materials=materials,
                  images=[dict(name=i.name, size=list(i.size), packed=bool(i.packed_file)) for i in bpy.data.images])
    (OUT / f"{key}-inventory.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("STATION_SOURCE", key, "meshes", len(records), "triangles", sum(r["triangles"] for r in records),
          "materials", len(materials), "images", len(report["images"]))


inspect("figur", BASE / "Sci_Fi_SPACE_STATION_Kitbash___3D_Kitbash_Asset_Pack___Blender-9af3878b/blender/space_station_kit.blend")
inspect("station3", BASE / "Space_Station_3-192bc415/glb/converted/space_station_3.glb")
inspect("corner", BASE / "The_Corner-9bbf59e4/glb/converted/the_corner.glb")
