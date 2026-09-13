"""Inspect a separate tail-only selection proposal without editing source assets.

Default creates rest-pose selection overlays and connected-island measurements.
No GLB or Unreal asset is changed by this diagnostic step.
"""
import hashlib
import json
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ContentSource/TailCandidatePreview"
SOURCE = ROOT / "model-rigged.glb"
EXPECTED = "c106b51d3463130be49e80f7e738f52be931f80dd73e15f1cfa53b07d99bfc91"


def main():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
    OUT.mkdir(exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(SOURCE))
    scene = bpy.context.scene
    mesh = next(obj for obj in scene.objects if obj.type == "MESH")
    rig = next(obj for obj in scene.objects if obj.type == "ARMATURE")
    rig.data.pose_position = "REST"
    coords = np.array([vertex.co[:] for vertex in mesh.data.vertices], dtype=np.float32)
    previous, proposed, bridge = np.zeros(len(coords), bool), np.zeros(len(coords), bool), np.zeros(len(coords), bool)
    bm = bmesh.new(); bm.from_mesh(mesh.data); bm.verts.ensure_lookup_table()
    islands = []
    for seed in bm.verts:
        if seed.tag:
            continue
        seed.tag = True; stack, island = [seed], []
        while stack:
            vertex = stack.pop(); island.append(vertex.index)
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if not other.tag:
                    other.tag = True; stack.append(other)
        points = coords[island]; minimum, maximum = points.min(axis=0), points.max(axis=0)
        old = minimum[1] > -.04 and maximum[1] > .10 and maximum[2] > -.10
        prior_candidate = old or (minimum[1] > -.04 and maximum[1] > .10 and minimum[2] > -.18)
        root_bridge = minimum[0] > -.09 and maximum[0] < .09 and minimum[1] > .02 and maximum[1] < .11 and minimum[2] > -.135 and maximum[2] < .015
        broad = prior_candidate or root_bridge
        if root_bridge and not prior_candidate: bridge[island] = True
        if old: previous[island] = True
        if broad: proposed[island] = True
        islands.append({"vertices": len(island), "min_m": minimum.tolist(), "max_m": maximum.tolist(), "old": bool(old), "additional": bool(broad and not old), "indices": island if broad and not old else None})
    bm.free()
    assert previous.sum() == 140186
    added = proposed & ~previous
    record = {"status": "TAIL_SELECTION_PROPOSAL_REQUIRES_VISUAL_REVIEW", "source_sha256": EXPECTED,
              "previous_vertices": int(previous.sum()), "additional_vertices": int(added.sum()), "candidate_vertices": int(proposed.sum()), "root_bridge_vertices": int(bridge.sum()),
              "new_criterion": "Preserve old whole-island selection and add rear islands with minY>-.04m,maxY>.10m,minZ>-.18m; spatial gap excludes original foot/lower-leg components; root bridge whole islands within X[-.09,.09],Y[.02,.11],Z[-.135,.015]m additionally reviewed",
              "additional_islands": [island for island in islands if island["additional"]],
              "remaining_islands": [{k:v for k,v in island.items() if k != "indices"} for island in islands if not island["old"] and not island["additional"]],
              "source_assets_modified": False, "palette": {"magenta": "existing selected tail", "cyan": "additional candidate islands", "grey": "preserved remainder", "gold": "additional303 tail-root continuity vertices"}}
    (OUT / "Selection.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    mesh.data.materials.clear()
    for name, color in (("BodyGrey", (.15, .18, .22, 1)), ("ExistingTailMagenta", (.75, .025, .2, 1)), ("AddedTailCyan", (.02, .65, .9, 1)), ("RootBridgeGold", (.9, .6, .025, 1))):
        material = bpy.data.materials.new(name); material.use_nodes = True
        material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = color
        mesh.data.materials.append(material)
    for polygon in mesh.data.polygons:
        polygon.material_index = 3 if any(bridge[index] for index in polygon.vertices) else (2 if any(added[index] for index in polygon.vertices) else (1 if any(previous[index] for index in polygon.vertices) else 0))
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = 1000, 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world = bpy.data.worlds.new("TailSelectionWorld"); scene.world.color = (.065, .065, .065)
    for location, energy in (((2, -2, 3), 400), ((-2, 1, 2), 450), ((1, 3, 2), 350)):
        data = bpy.data.lights.new("SelectionArea", "AREA"); data.energy = energy; data.size = 3
        light = bpy.data.objects.new("SelectionArea", data); scene.collection.objects.link(light); light.location = location
        light.rotation_euler = (Vector((0, 0, 0)) - light.location).to_track_quat("-Z", "Y").to_euler()
    data = bpy.data.cameras.new("SelectionCamera"); camera = bpy.data.objects.new("SelectionCamera", data); scene.collection.objects.link(camera)
    scene.camera = camera; data.type = "ORTHO"; data.ortho_scale = 1.7
    for name, position in (("Front", (1.5, -3, .4)), ("Side", (3, 0, .1)), ("Rear", (1.5, 3, .4)), ("UnderTail", (1.5, 3, -1.5))):
        data.ortho_scale = .75 if name == "UnderTail" else 1.7
        camera.location = position; camera.rotation_euler = (Vector((0, .1, -.06)) - camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(OUT / ("Selection" + name + ".png")); bpy.ops.render.render(write_still=True)
    print(json.dumps({key: record[key] for key in ("previous_vertices", "additional_vertices", "candidate_vertices")}))
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED


if __name__ == "__main__":
    main()