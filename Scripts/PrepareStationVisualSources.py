"""Prepare private station presentation derivatives with existing Blender.

Only derivative output under .agent/local/StationVisualPass is written. Originals
remain untouched. Run with Blender --background --factory-startup --python.
"""
from pathlib import Path
import hashlib
import json
import math
import sys

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "User downloaded assets/VaultCache/FabLibrary"
OUT = ROOT / ".agent/local/StationVisualPass"
OUT.mkdir(parents=True, exist_ok=True)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def mesh_bounds(mesh):
    points = [mesh.matrix_world @ v.co for v in mesh.data.vertices]
    return (Vector([min(v[i] for v in points) for i in range(3)]),
            Vector([max(v[i] for v in points) for i in range(3)]))


def join_and_normalize(objects, name, max_size):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        transform = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = transform
        obj.animation_data_clear()
        obj.hide_viewport = False
        obj.hide_render = False
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    if len(objects) > 1:
        bpy.ops.object.join()
    mesh = bpy.context.object
    mesh.name = name
    mesh.data.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    low, high = mesh_bounds(mesh)
    scale = min(max_size[i] / (high[i] - low[i]) for i in range(3))
    center = (low + high) * 0.5
    for vertex in mesh.data.vertices:
        vertex.co = (vertex.co - center) * scale
    return mesh


def export(mesh, source, key, source_sha, notes):
    used = {m for m in mesh.data.materials if m}
    textures = set()
    for mat in used:
        for node in mat.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image:
                textures.add(node.image)
    image_rows = []
    for img in textures:
        original = list(img.size)
        if max(original) > 2048:
            ratio = 2048 / max(original)
            img.scale(max(1, round(original[0] * ratio)), max(1, round(original[1] * ratio)))
            img.pack()
        image_rows.append(dict(name=img.name, original=original, derivative=list(img.size)))
    target = OUT / f"{key}.glb"
    bpy.ops.export_scene.gltf(filepath=str(target), export_format="GLB", use_selection=True,
                             export_animations=False, export_normals=True, export_tangents=True)
    low, high = mesh_bounds(mesh)
    report = dict(source=str(source.relative_to(ROOT)), source_sha256=source_sha,
                  output_sha256=digest(target), output_bytes=target.stat().st_size,
                  triangles=sum(len(p.vertices) - 2 for p in mesh.data.polygons),
                  materials=[m.name for m in used], textures=image_rows,
                  bounds_cm=[list(low*100), list(high*100)], notes=notes)
    assert digest(source) == source_sha
    (OUT / f"{key}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("STATION_VISUAL_DERIVATIVE", key, json.dumps(report))
    return mesh


def render_preview(mesh, key):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world = bpy.data.worlds.new("ReviewWorld")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.15, 0.18, 0.23, 1)
    scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.65
    low, high = mesh_bounds(mesh)
    size = max(high-low)
    for name, pos, energy, color in [
        ("Key", (1, -1, 1.5), 60, (0.7, 0.84, 1.0)),
        ("Fill", (-1, -0.2, 0.7), 40, (1.0, 0.70, 0.4)),
        ("Rim", (0, 1, 1), 85, (0.5, 0.7, 1.0)),
    ]:
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy * size * size
        data.shape = "DISK"
        data.size = size
        data.color = color
        light = bpy.data.objects.new(name, data)
        scene.collection.objects.link(light)
        light.location = Vector(pos) * size
        light.rotation_euler = (-light.location).to_track_quat("-Z", "Y").to_euler()
    data = bpy.data.cameras.new("ReviewCamera")
    cam = bpy.data.objects.new("ReviewCamera", data)
    scene.collection.objects.link(cam)
    cam.location = Vector((1.2, -1.8, 0.9)) * size
    cam.rotation_euler = (-cam.location).to_track_quat("-Z", "Y").to_euler()
    data.type = "ORTHO"
    data.ortho_scale = size * 1.65
    data.clip_end = size * 10
    scene.camera = cam
    scene.render.filepath = str(OUT / f"{key}-preview.png")
    bpy.ops.render.render(write_still=True)


def prepare_corner():
    source = BASE / "The_Corner-9bbf59e4/glb/converted/the_corner.glb"
    source_sha = digest(source)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    bpy.context.scene.frame_set(0)
    objects = [o for o in bpy.context.scene.objects if o.type == "MESH" and
               all(m and m.name != "Studio_floor_material" for m in o.data.materials)]
    floor = [o for o in bpy.context.scene.objects if o.type == "MESH" and o not in objects]
    for obj in floor:
        bpy.data.objects.remove(obj, do_unlink=True)
    mesh = join_and_normalize(objects, "SM_ServiceCargo", (1.0, 1.0, 1.0))
    mesh = export(mesh, source, "ServiceCargo", source_sha,
                  "Static closed rest-pose cargo, studio floor excluded, source PBR retained; no gameplay/collision.")
    render_preview(mesh, "ServiceCargo")


def prepare_figur():
    source = BASE / "Sci_Fi_SPACE_STATION_Kitbash___3D_Kitbash_Asset_Pack___Blender-9af3878b/blender/space_station_kit.blend"
    source_sha = digest(source)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(str(source), link=False) as (data_from, data_to):
        data_to.objects = ["5"]
    mesh = data_to.objects[0]
    bpy.context.scene.collection.objects.link(mesh)
    mesh.animation_data_clear()
    # Evaluate the source's geometry nodes before deriving anything. Raw mesh
    # datablocks can omit details added by the vendor's node modifier.
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = bpy.data.meshes.new_from_object(mesh.evaluated_get(depsgraph), depsgraph=depsgraph)
    mesh.modifiers.clear()
    mesh.data = evaluated
    # All material inputs here derive from UVs, so evaluate the original shader
    # on a UV-square into a portable PBR atlas without changing the model UVs.
    graph = []
    for index, mat in enumerate(list(mesh.data.materials)):
        mat.animation_data_clear()
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
        graph.append(dict(material=mat.name, links=[f"{l.from_node.name}.{l.from_socket.name} -> {l.to_node.name}.{l.to_socket.name}" for l in links]))
        mesh.data.materials[index] = bake_uv_material(mat, f"Figur_{index}")
    (OUT / "Figur-material-graph.json").write_text(json.dumps(graph, indent=2), encoding="utf-8")
    # Existing runtime exterior yaw90 envelope is 71.42m x100m x76.62m.
    # Native derivative stays INSIDE that same envelope; no collision change.
    mesh = join_and_normalize([mesh], "SM_FigurStationExterior", (100.0, 71.42, 76.62))
    # Explicit triangulation supplies deterministic tangents for the original
    # ngons; the exported silhouette and source UVs are retained.
    modifier = mesh.modifiers.new("ExportTriangulation", "TRIANGULATE")
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    mesh = export(mesh, source, "FigurStationExterior", source_sha,
        "Assembled station5; evaluated geometry nodes and UVs retained; original UV-driven Blender shader baked to 2K base/roughness/metallic/normal atlases. Uniformly fits existing collision envelope. No source save.")
    render_preview(mesh, "FigurStationExterior")


def bake_uv_material(source, name):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 1
    scene.render.bake.margin = 0
    scene.render.bake.use_clear = True
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.mesh.primitive_plane_add(size=2)
    plane = bpy.context.object
    plane.data.materials.append(source)
    nodes, links = source.node_tree.nodes, source.node_tree.links
    output = next(n for n in nodes if n.type == "OUTPUT_MATERIAL")
    bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
    emitter = nodes.new("ShaderNodeEmission")
    images = {}
    for channel, socket in [("Color", "Base Color"), ("Roughness", "Roughness"), ("Metallic", "Metallic"), ("Normal", "Normal")]:
        img = bpy.data.images.new(f"T_{name}_{channel}", width=2048, height=2048, alpha=False)
        img.colorspace_settings.name = "sRGB" if channel == "Color" else "Non-Color"
        target = nodes.new("ShaderNodeTexImage")
        target.image = img
        nodes.active = target
        if channel == "Normal":
            links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
            bpy.ops.object.bake(type="NORMAL")
        else:
            value = bsdf.inputs[socket]
            for link in list(emitter.inputs["Color"].links):
                links.remove(link)
            if value.is_linked:
                links.new(value.links[0].from_socket, emitter.inputs["Color"])
            else:
                default = value.default_value
                emitter.inputs["Color"].default_value = tuple(default) if channel == "Color" else (default, default, default, 1)
            links.new(emitter.outputs["Emission"], output.inputs["Surface"])
            bpy.ops.object.bake(type="EMIT")
        img.pack()
        images[channel] = img
        nodes.remove(target)
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    nodes.remove(emitter)
    bpy.data.objects.remove(plane, do_unlink=True)
    material = bpy.data.materials.new(f"M_{name}")
    material.use_nodes = True
    n, l = material.node_tree.nodes, material.node_tree.links
    shader = n.get("Principled BSDF")
    for channel, socket in [("Color", "Base Color"), ("Roughness", "Roughness"), ("Metallic", "Metallic"), ("Normal", "Normal")]:
        sample = n.new("ShaderNodeTexImage")
        sample.image = images[channel]
        if channel == "Normal":
            normal = n.new("ShaderNodeNormalMap")
            l.new(sample.outputs["Color"], normal.inputs["Color"])
            l.new(normal.outputs["Normal"], shader.inputs["Normal"])
        else:
            l.new(sample.outputs["Color"], shader.inputs[socket])
    return material


def prepare_station3():
    source = BASE / "Space_Station_3-192bc415/glb/converted/space_station_3.glb"
    source_sha = digest(source)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    objects = [o for o in bpy.context.scene.objects if o.type == "MESH" and
               not any(m and m.name == "spacestation_smalllights" for m in o.data.materials)]
    for obj in list(bpy.context.scene.objects):
        if obj.type == "MESH" and obj not in objects:
            bpy.data.objects.remove(obj, do_unlink=True)
    mesh = join_and_normalize(objects, "SM_Station3Exterior", (100.0, 71.42, 76.62))
    mesh = export(mesh, source, "Station3Exterior", source_sha,
                  "Paired ring station; detached surrounding light points excluded. Source PBR retained at2K. Fits unchanged exterior envelope.")
    render_preview(mesh, "Station3Exterior")


selection = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else ["corner", "figur", "station3"]
for key in selection:
    {"corner": prepare_corner, "figur": prepare_figur, "station3": prepare_station3}[key]()
