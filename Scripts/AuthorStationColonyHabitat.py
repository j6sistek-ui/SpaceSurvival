"""Extract the owned Figur station-3 assembly without changing its source file.

Run with installed Blender --background --factory-startup --python this_file.
The default measures and renders a candidate under Artifacts. Add -- --apply to
bake the supplied UV materials and export the separate, uniformly scaled GLB.
No source .blend is saved. Unreal import remains a separate serialized step.
"""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "User downloaded assets/VaultCache/FabLibrary/Sci_Fi_SPACE_STATION_Kitbash___3D_Kitbash_Asset_Pack___Blender-9af3878b/blender/space_station_kit.blend"
if "--source" in sys.argv:
    SOURCE = Path(sys.argv[sys.argv.index("--source") + 1]).resolve()
OUT = ROOT / "Artifacts/StationReset/ColonyHabitat"
NAME = "SM_ColonyHabitat"
TARGET = "/Game/SpaceSurvival/Licensed/StationReset/ColonyHabitat/" + NAME


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def bounds(obj):
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    return [Vector([fn(p[i] for p in points) for i in range(3)]) for fn in (min, max)]


def preview(obj, suffix):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world = bpy.data.worlds.new("ColonyReviewWorld")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes["Background"]
    background.inputs[0].default_value = (.11, .14, .19, 1)
    background.inputs[1].default_value = .7
    low, high = bounds(obj)
    center = (low + high) / 2
    span = max(high - low)
    added = []
    for label, offset, color, watts in (
            ("Key", (1, -1, 1.7), (.82, .9, 1), 100),
            ("Fill", (-1, -.4, .8), (1, .78, .52), 65),
            ("Rim", (.3, 1, 1.3), (.65, .8, 1), 100)):
        data = bpy.data.lights.new(label, "AREA")
        data.energy = watts * span * span
        data.size = span
        data.color = color
        light = bpy.data.objects.new(label, data)
        scene.collection.objects.link(light)
        light.location = center + Vector(offset) * span
        light.rotation_euler = (center - light.location).to_track_quat("-Z", "Y").to_euler()
        added.append(light)
    data = bpy.data.cameras.new("ColonyReviewCamera")
    camera = bpy.data.objects.new("ColonyReviewCamera", data)
    scene.collection.objects.link(camera)
    data.type = "ORTHO"
    data.ortho_scale = span * 1.35
    data.clip_end = span * 10
    scene.camera = camera
    for name, offset in (("quarter", (1.2, -1.8, .9)), ("side", (1.7, -.1, .35))):
        camera.location = center + Vector(offset) * span
        camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(OUT / f"{suffix}-{name}.png")
        bpy.ops.render.render(write_still=True)
    for extra in added + [camera]:
        bpy.data.objects.remove(extra, do_unlink=True)


def main():
    apply = "--apply" in sys.argv
    OUT.mkdir(parents=True, exist_ok=True)
    before = sha(SOURCE)
    output = OUT / (NAME + ".glb")
    receipt_path = OUT / "author.json"
    prior = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.exists() else None
    if apply and output.exists():
        assert prior and prior.get("output_sha256") == sha(output), "Preserving unowned/edited derivative"
        assert prior.get("source_sha256") == before, "Supplied source changed since authoring"
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(str(SOURCE), link=False) as (available, loaded):
        assert "3" in available.objects, "Authored station object3 is missing"
        loaded.objects = ["3"]
    obj = loaded.objects[0]
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.update()
    source_triangles = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    source_materials = [m.name for m in obj.data.materials]
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph), depsgraph=depsgraph)
    obj.modifiers.clear()
    obj.data = evaluated
    obj.animation_data_clear()
    low, high = bounds(obj)
    source_size = high - low
    source_transform = obj.matrix_world.copy()
    for vertex in obj.data.vertices:
        vertex.co = source_transform @ vertex.co
    obj.matrix_world.identity()
    # Measured 60-band audit places the broad, detailed ring body at world Z
    # -12.614..-10.129 m. Trim at its underside to remove the hanging lower mast
    # and form a grounded building assembly, retaining the full ring/upper tower.
    cut_z = -12.65
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    cut = bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                               dist=.00001, plane_co=(0, 0, cut_z), plane_no=(0, 0, 1),
                               clear_inner=True, clear_outer=False)
    boundaries = [edge for edge in cut["geom_cut"] if isinstance(edge, bmesh.types.BMEdge) and edge.is_boundary]
    capped = bmesh.ops.holes_fill(bm, edges=boundaries, sides=0)["faces"] if boundaries else []
    cap_count = len(capped)
    bm.normal_update()
    bm.to_mesh(obj.data)
    bm.free()
    low, high = bounds(obj)
    size = high - low
    # Blender metres remain real metres in GLB; Unreal converts metres to centimetres.
    scale = min(18.0 / size.x, 18.0 / size.y, 45.0 / size.z)
    base = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, low.z))
    transform = obj.matrix_world.copy()
    for vertex in obj.data.vertices:
        vertex.co = (transform @ vertex.co - base) * scale
    obj.matrix_world.identity()
    obj.name = NAME
    obj.data.name = NAME
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    obj.hide_render = False
    obj.hide_viewport = False
    bpy.context.view_layer.update()
    low, high = bounds(obj)
    textures = []
    for material in obj.data.materials:
        for node in material.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image:
                image = node.image
                assert image.packed_file or Path(bpy.path.abspath(image.filepath)).is_file(), image.name
                textures.append({"name": image.name, "size": list(image.size), "packed": bool(image.packed_file)})
    record = {"utc": datetime.now(timezone.utc).isoformat(), "mode": "apply" if apply else "dry-run",
              "source": str(SOURCE), "source_sha256": before, "source_object": "3",
              "source_triangles": source_triangles, "source_materials": source_materials,
              "source_dimensions_m": list(source_size), "uniform_scale": scale,
              "bounds_cm": [list(low * 100), list(high * 100)], "textures": textures,
              "target": TARGET, "geometry": "Supplied station-3 ring and upper towers; hanging lower mast removed at measured ring underside; no walkable interior",
              "cut_plane_source_world_z_m": cut_z, "cap_faces": cap_count,
              "placement": "Pivot centered in XY at base Z0; two terrace instances; presentation only"}
    print("COLONY_CANDIDATE " + json.dumps(record), flush=True)
    if apply:
        # Reuse the existing UV-square shader bake: it retains source UVs and evaluates
        # the vendor graph into portable base-color/roughness/metallic/normal atlases.
        spec = importlib.util.spec_from_file_location("station_material_bake", ROOT / "Scripts/PrepareStationVisualSources.py")
        helper = importlib.util.module_from_spec(spec)
        saved_args = sys.argv
        try:
            sys.argv = [saved_args[0], "--"]  # Import helpers without running their old authoring targets.
            spec.loader.exec_module(helper)
        finally:
            sys.argv = saved_args
        for index, material in enumerate(list(obj.data.materials)):
            material.animation_data_clear()
            obj.data.materials[index] = helper.bake_uv_material(material, f"ColonyHabitat_{index}")
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        triangulate = obj.modifiers.new("ExportTriangulation", "TRIANGULATE")
        bpy.ops.object.modifier_apply(modifier=triangulate.name)
        bpy.ops.export_scene.gltf(filepath=str(output), export_format="GLB", use_selection=True,
                                 export_animations=False, export_normals=True, export_tangents=True)
        record["output_sha256"] = sha(output)
        record["output_bytes"] = output.stat().st_size
        record["triangles"] = len(obj.data.polygons)
        record["materials"] = [m.name for m in obj.data.materials]
        record["material_bake"] = "Existing UV-square bake of supplied shader to 2048x2048 PBR maps; source UVs retained"
    preview(obj, "baked" if apply else "source")
    record["source_preserved"] = sha(SOURCE) == before
    assert record["source_preserved"]
    record["status"] = "complete"
    (receipt_path if apply else OUT / "dry-run.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("COLONY_HABITAT_COMPLETE " + record["mode"], flush=True)


if __name__ == "__main__":
    main()
