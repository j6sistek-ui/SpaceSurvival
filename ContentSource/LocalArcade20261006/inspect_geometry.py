"""Headless Blender inspection of locally generated geometry (no user scene)."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / ".agent/local/ArcadeGeneration"


def main():
    if (WORK / "FROZEN_MANIFEST.json").exists():
        raise RuntimeError("Frozen1 is preserved; author a new version instead")
    reports = []
    for name in ("AsteroidArena", "GalaxyPinball", "TokensKiosk"):
        sources = list((WORK / "raw" / name).glob("*.glb"))
        if not sources:
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(sources[0]))
        meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
        bpy.ops.object.select_all(action="DESELECT")
        for obj in meshes:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        bpy.ops.object.join()
        obj = bpy.context.object
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        bounds = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        lo = Vector(tuple(min(v[i] for v in bounds) for i in range(3)))
        hi = Vector(tuple(max(v[i] for v in bounds) for i in range(3)))
        obj.location -= (lo + hi) * 0.5
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        obj.name = name + "_LocalHunyuanRaw"
        reports.append({"name": name, "bounds_before": [list(lo), list(hi)], "vertices": len(obj.data.vertices), "triangles": sum(len(p.vertices) - 2 for p in obj.data.polygons)})
        scene = bpy.context.scene
        scene.render.engine = "BLENDER_WORKBENCH"
        scene.display.shading.light = "STUDIO"
        scene.display.shading.show_cavity = True
        scene.display.shading.cavity_type = "BOTH"
        scene.display.shading.color_type = "SINGLE"
        scene.display.shading.single_color = (0.38, 0.42, 0.48)
        scene.display.shading.background_type = "WORLD"
        scene.world = bpy.data.worlds.new("InspectionWorld")
        scene.world.color = (0.055, 0.065, 0.075)
        scene.render.resolution_x = 768
        scene.render.resolution_y = 768
        scene.render.resolution_percentage = 100
        bpy.ops.object.camera_add()
        camera = bpy.context.object
        scene.camera = camera
        camera.data.type = "ORTHO"
        camera.data.ortho_scale = max(hi - lo) * 1.35
        for label, position in (
            ("front", (0, -5, 1.7)), ("right", (5, 0, 1.7)),
            ("back", (0, 5, 1.7)), ("left", (-5, 0, 1.7)),
        ):
            camera.location = position
            camera.rotation_euler = (-camera.location).to_track_quat("-Z", "Y").to_euler()
            scene.render.filepath = str(WORK / "preview" / f"{name}_raw_{label}.png")
            bpy.ops.render.render(write_still=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(WORK / "raw" / name / f"{name}_raw.blend"))
    (WORK / "receipts" / "raw_geometry.json").write_text(json.dumps(reports, indent=2))
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
