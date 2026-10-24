"""Create isolated v3 console geometry from the four existing v2 Blender files.

Script authoring only: the lead runs the installed Blender with this file and
-- --apply. No original .blend, GLB, OBJ, texture or assembly.json is overwritten.
Native Unreal owns Time-driven HUD animation; this export supplies its depth,
glass, transparent artwork and physical frame. No render is requested here.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import sys


WORK = Path(__file__).resolve().parent
OUT = WORK.parent / "outputs/Cryo_Comparison"
OLD_MANIFEST = OUT / "assembly.json"
NEW_MANIFEST = OUT / "assembly_holo_consoles.json"
HUD_TEXTURE = OUT / "shared/T_Cryo_ConsoleHolo.png"
GLASS_OFFSET_M = 0.04
HUD_OFFSET_M = 0.0425
FRAME_WIDTH_M = 0.006
FRAME_DEPTH_M = 0.04


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def inputs_and_plan(manifest):
    protected = {OLD_MANIFEST.resolve()}
    rows = []
    for model in manifest["models"]:
        components = model["components"]
        require(len(components) == 13, "Expected unchanged 13-component v2 assembly: " + model["id"])
        consoles = [row for row in components if row["role"] == "console"]
        require({row["name"] for row in consoles} == {"Console_1", "Console_2"}, "Expected two original console quads")
        folder = Path(next(row["file"] for row in components if row["role"] == "body")).resolve().parent.parent
        name = folder.name
        blend = folder / (name + "_Editable.blend")
        glb = folder / (name + "_Finished.glb")
        require(blend.is_file() and glb.is_file(), "Existing v2 Blender/GLB source missing: " + name)
        protected.update((blend, glb, Path(model["source"]).resolve()))
        protected.update(Path(row["file"]).resolve() for row in components)
        protected.update(Path(path).resolve() for path in model["textures"].values())
        rows.append({"id": model["id"], "name": name, "source_blend": blend,
                     "source_glb": glb, "folder": folder / "v3_holo_console"})
    protected.update(Path(path).resolve() for path in manifest["shared"].values())
    require(len(rows) == 4 and {row["id"] for row in rows} == set("ABCD"), "Expected all four models A-D")
    require(all(path.is_file() for path in protected), "A protected v2/source file is missing")
    return protected, rows


def mesh_signature(ob):
    """Snapshot geometry/UV/custom normals/transforms without touching mesh data."""
    m = ob.data
    h = hashlib.sha256()
    def add(values):
        h.update(struct.pack("<" + "d" * len(values), *values))
    for row in ob.matrix_world:
        add(tuple(row))
    for vertex in m.vertices:
        add(tuple(vertex.co))
    for polygon in m.polygons:
        h.update(struct.pack("<II?", len(polygon.vertices), polygon.material_index, polygon.use_smooth))
        h.update(struct.pack("<" + "I" * len(polygon.vertices), *polygon.vertices))
    for normal in m.corner_normals:
        add(tuple(normal.vector))
    for layer in m.uv_layers:
        h.update(layer.name.encode("utf-8"))
        for corner in layer.data:
            add(tuple(corner.uv))
    return h.hexdigest()


def simple_material(bpy, name, color, metallic, roughness, alpha=1.0, emission=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    for socket, value in {"Base Color": (*color, 1.0), "Metallic": metallic,
                          "Roughness": roughness, "Alpha": alpha,
                          "Emission Color": (*color, 1.0), "Emission Strength": emission}.items():
        bsdf.inputs[socket].default_value = value
    mat.diffuse_color = (*color, alpha)
    if alpha < 1.0:
        mat.surface_render_method = "DITHERED"
    mat.use_backface_culling = False
    return mat


def materials(bpy):
    result = {
        "console_backing": simple_material(bpy, "M_ConsoleBacking_v3", (0.006, 0.012, 0.018), 0.2, 0.45),
        "console_glass": simple_material(bpy, "M_ConsoleGlass_v3", (0.30, 0.55, 0.70), 0.0, 0.09, alpha=0.08),
        "console_frame": simple_material(bpy, "M_ConsoleFrame_v3", (0.015, 0.16, 0.23), 0.4, 0.28, emission=0.6),
    }
    mat = simple_material(bpy, "M_ConsoleHUD_v3", (0.20, 0.65, 1.0), 0.0, 0.35, alpha=0.90, emission=1.8)
    tree = mat.node_tree
    bsdf = tree.nodes.get("Principled BSDF")
    tex = tree.nodes.new("ShaderNodeTexImage")
    tex.name = "TransparentConsoleArtwork"
    tex.image = bpy.data.images.load(str(HUD_TEXTURE), check_existing=True)
    tex.image.alpha_mode = "STRAIGHT"
    require(tex.image.channels == 4, "Console HUD image must have an alpha channel")
    # Inspect alpha values; do not synthesize/edit texture pixels in Python.
    from array import array
    pixels = array("f", [0.0]) * len(tex.image.pixels)
    tex.image.pixels.foreach_get(pixels)
    alpha = pixels[3::4]
    require(min(alpha) < 0.05 and max(alpha) > 0.5, "Console HUD must contain real transparent and visible pixels")
    alpha_info = {"min": float(min(alpha)), "max": float(max(alpha)),
                  "fraction_below_0_05": sum(value < 0.05 for value in alpha) / len(alpha)}
    del pixels, alpha
    tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    tree.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
    multiply = tree.nodes.new("ShaderNodeMath")
    multiply.operation = "MULTIPLY"
    multiply.inputs[1].default_value = 0.90
    tree.links.new(tex.outputs["Alpha"], multiply.inputs[0])
    tree.links.new(multiply.outputs[0], bsdf.inputs["Alpha"])
    tex.image.pack()
    result["console"] = mat
    return result, alpha_info


def offset_copy(bpy, original, name, normal_world, offset, material):
    ob = original.copy()
    ob.data = original.data.copy()
    ob.animation_data_clear()
    ob.name = name
    ob.data.name = name + "Mesh"
    for collection in original.users_collection:
        collection.objects.link(ob)
    matrix = ob.matrix_world.copy()
    matrix.translation += normal_world * offset
    ob.matrix_world = matrix
    ob.data.materials.clear()
    ob.data.materials.append(material)
    return ob


def make_frame(bpy, name, corners, normal, material):
    """Four narrow rectangular rails join backing to glass, leaving center open."""
    vertices, faces = [], []
    for i, first in enumerate(corners):
        second = corners[(i + 1) % len(corners)]
        edge = (second - first).normalized()
        side = normal.cross(edge).normalized() * (FRAME_WIDTH_M * 0.5)
        rear = normal * -0.001
        front = normal * (FRAME_DEPTH_M - 0.001)
        points = [first - side + rear, second - side + rear, second + side + rear, first + side + rear,
                  first - side + front, second - side + front, second + side + front, first + side + front]
        start = len(vertices)
        vertices.extend(tuple(point) for point in points)
        faces.extend(tuple(start + j for j in face) for face in (
            (3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4),
            (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    mesh.materials.append(material)
    uv = mesh.uv_layers.new(name="UVMap")
    for face in mesh.polygons:
        for li, coord in zip(face.loop_indices, ((0, 0), (1, 0), (1, 1), (0, 1))):
            uv.data[li].uv = coord
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(ob)
    return ob


def export_obj(bpy, ob, path):
    """Same cm/Z-up/per-corner-normal format as v2; no importer mirroring here."""
    deps = bpy.context.evaluated_depsgraph_get()
    evaluated = ob.evaluated_get(deps)
    mesh = evaluated.to_mesh()
    try:
        mesh.calc_loop_triangles()
        world = evaluated.matrix_world
        normal_matrix = world.to_3x3().inverted().transposed()
        uv = mesh.uv_layers.active
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write("# Cryo console v3; centimeters; Z up; front -Y\no " + ob.name + "\n")
            for vertex in mesh.vertices:
                point = (world @ vertex.co) * 100
                handle.write(f"v {point.x:.8f} {point.y:.8f} {point.z:.8f}\n")
            for li in range(len(mesh.loops)):
                coord = uv.data[li].uv if uv else (0.0, 0.0)
                handle.write(f"vt {coord[0]:.8f} {coord[1]:.8f}\n")
            for li in range(len(mesh.loops)):
                n = (normal_matrix @ mesh.corner_normals[li].vector).normalized()
                handle.write(f"vn {n.x:.8f} {n.y:.8f} {n.z:.8f}\n")
            handle.write("usemtl " + ob.data.materials[0].name + "\ns 1\n")
            for tri in mesh.loop_triangles:
                handle.write("f " + " ".join(f"{mesh.loops[li].vertex_index + 1}/{li + 1}/{li + 1}" for li in tri.loops) + "\n")
        return len(mesh.loop_triangles)
    finally:
        evaluated.to_mesh_clear()


def inspect_glb(path):
    raw = path.read_bytes()
    magic, version, size = struct.unpack_from("<4sII", raw)
    require(magic == b"glTF" and version == 2 and size == len(raw), "Invalid new GLB")
    length, kind = struct.unpack_from("<I4s", raw, 12)
    require(kind == b"JSON", "New GLB JSON chunk missing")
    doc = json.loads(raw[20:20 + length])
    require(len(doc.get("meshes", [])) == 19, "New GLB must contain exactly 19 selected component meshes")
    require(all("bufferView" in im and "uri" not in im for im in doc.get("images", [])), "New GLB must embed all images")
    result = {}
    for suffix in ("HUD", "Glass", "Backing", "Frame"):
        name = "M_Console" + suffix + "_v3"
        matches = [mat for mat in doc.get("materials", []) if mat.get("name") == name]
        require(len(matches) == 1, "Missing console material in new GLB: " + name)
        mat = matches[0]
        result[name] = {"alphaMode": mat.get("alphaMode", "OPAQUE"),
                        "baseColorFactor": mat.get("pbrMetallicRoughness", {}).get("baseColorFactor", [1, 1, 1, 1]),
                        "emissiveFactor": mat.get("emissiveFactor", [0, 0, 0]),
                        "extensions": mat.get("extensions", {})}
        if suffix in ("HUD", "Glass"):
            require(mat.get("alphaMode") == "BLEND", "Console transparency did not export: " + name)
    return {"bytes": len(raw), "sha256": sha(path), "embedded_images": len(doc.get("images", [])),
            "meshes": len(doc.get("meshes", [])), "console_materials": result,
            "animation_note": "Standard glTF material export is static. Native Unreal Time material supplies console animation."}


def main(apply=False):
    manifest = json.loads(OLD_MANIFEST.read_text(encoding="utf-8-sig"))
    protected, plan = inputs_and_plan(manifest)
    if not apply:
        print(json.dumps({"status": "DRY_RUN_NO_FILES_WRITTEN", "console_texture_exists": HUD_TEXTURE.is_file(),
            "new_manifest": str(NEW_MANIFEST), "plan": [{key: str(value) for key, value in row.items()} for row in plan],
            "components_per_assembly": 19, "new_console_objs_per_assembly": 8}, indent=2), flush=True)
        return
    import bpy
    from mathutils import Vector
    require(HUD_TEXTURE.is_file(), "Await generated transparent console HUD: " + str(HUD_TEXTURE))
    require(not NEW_MANIFEST.exists(), "Refusing to overwrite existing v3 manifest")
    require(all(not row["folder"].exists() for row in plan), "Refusing to overwrite an existing v3 model folder")
    protected.add(HUD_TEXTURE.resolve())
    before = {str(path): sha(path) for path in protected}
    upgraded = deepcopy(manifest)
    upgraded["shared"]["console"] = str(HUD_TEXTURE.resolve())
    upgraded["version"] = "v3_holo_consoles"
    upgraded["source_manifest"] = str(OLD_MANIFEST.resolve())
    upgraded["source_manifest_sha256"] = before[str(OLD_MANIFEST.resolve())]
    upgraded["console_upgrade"] = {"scope": "Only the two bottom consoles on each chamber", "instances": 8,
        "glass_offset_cm": 4.0, "hud_offset_cm": 4.25, "frame_width_cm": 0.6, "frame_depth_cm": 4.0,
        "hud_opacity_multiplier": 0.90, "hud_emission_strength": 1.8, "glass_alpha": 0.08,
        "animation_owner": "Native Unreal Time-driven console material; GLB appearance is static",
        "native_import_note": "FbxFactory converts Blender -Y to Unreal +Y. Preserve current root-approved Unreal front +Y convention; do not add another mirror."}
    upgraded["same_finish"] = "Preserved v2 chamber finish; both bottom consoles use identical backing, raised glass, transparent HUD and narrow support frames. Native Unreal supplies animated HUD and cryogenic VFX."
    receipt = {"utc": datetime.now(timezone.utc).isoformat(), "models": []}
    for model, item in zip(upgraded["models"], plan):
        bpy.ops.wm.open_mainfile(filepath=str(item["source_blend"]), load_ui=False)
        bpy.context.view_layer.update()
        components = [(row, bpy.data.objects.get(row["name"])) for row in model["components"]]
        require(all(ob and ob.type == "MESH" for row, ob in components), "Missing v2 component object")
        unchanged = [(row, ob, mesh_signature(ob), tuple(mat.name for mat in ob.data.materials))
                     for row, ob in components if row["role"] != "console"]
        mats, alpha_info = materials(bpy)
        item["folder"].mkdir()
        mesh_folder = item["folder"] / "meshes"
        mesh_folder.mkdir()
        rows, objects, details = [], [], []
        for old_row, ob in components:
            if old_row["role"] != "console":
                rows.append({**old_row, "file": str(Path(old_row["file"]).resolve())})
                objects.append(ob)
                continue
            require(len(ob.data.vertices) == 4 and len(ob.data.polygons) == 1, "Console must remain one original fitted quad")
            require(not ob.modifiers and ob.parent is None, "Unexpected console parent/modifier needs explicit handling")
            normal = (ob.matrix_world.to_3x3().inverted().transposed() @ ob.data.polygons[0].normal).normalized()
            require(normal.y < -0.1, "Original console winding is not outward toward Blender -Y")
            corners = [ob.matrix_world @ ob.data.vertices[index].co for index in ob.data.polygons[0].vertices]
            original_signature = mesh_signature(ob)
            original_name = old_row["name"]
            ob.name = original_name + "_Backing"
            ob.data.materials.clear()
            ob.data.materials.append(mats["console_backing"])
            glass = offset_copy(bpy, ob, original_name + "_Glass", normal, GLASS_OFFSET_M, mats["console_glass"])
            hud = offset_copy(bpy, ob, original_name + "_HUD", normal, HUD_OFFSET_M, mats["console"])
            frame = make_frame(bpy, original_name + "_Frame", corners, normal, mats["console_frame"])
            bpy.context.view_layer.update()
            require(mesh_signature(ob) == original_signature, "Backing quad geometry changed")
            for current, role in ((ob, "console_backing"), (glass, "console_glass"), (hud, "console"), (frame, "console_frame")):
                current["CryoRole"] = role
                current["CryoModelID"] = model["id"]
                current["CryoConsoleRevision"] = "v3"
                path = mesh_folder / ("SM_" + item["name"] + "_" + current.name + ".obj")
                count = export_obj(bpy, current, path)
                rows.append({"name": current.name, "role": role, "file": str(path), "triangles": count})
                objects.append(current)
            details.append({"console": original_name, "outward_normal_blender": list(normal),
                            "glass_world_translation_m": list(glass.matrix_world.translation),
                            "hud_world_translation_m": list(hud.matrix_world.translation),
                            "original_quad_geometry_sha256": original_signature})
        require(len(rows) == len(objects) == 19, "Upgrade must produce exactly 19 components")
        for row, ob, signature, material_names in unchanged:
            require(mesh_signature(ob) == signature, "Preserved geometry changed: " + row["name"])
            require(tuple(mat.name for mat in ob.data.materials) == material_names, "Preserved material assignment changed")
        bpy.ops.object.select_all(action="DESELECT")
        for ob in objects:
            ob.select_set(True)
        bpy.context.view_layer.objects.active = next(ob for row, ob in components if row["role"] == "body")
        glb = item["folder"] / (item["name"] + "_HoloConsoles_v3.glb")
        bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", use_selection=True,
                                 export_animations=True, export_frame_range=True,
                                 export_keep_originals=False, export_image_format="AUTO")
        glb_info = inspect_glb(glb)
        blend = item["folder"] / (item["name"] + "_HoloConsoles_v3_Editable.blend")
        # Existing v2 maps are already packed; only the new HUD was packed above.
        bpy.ops.wm.save_as_mainfile(filepath=str(blend), copy=True)
        for row, ob, signature, material_names in unchanged:
            require(mesh_signature(ob) == signature, "Export changed preserved geometry: " + row["name"])
        model["components"] = rows
        model["editable_blend"] = str(blend)
        model["finished_glb"] = str(glb)
        model["console_geometry"] = details
        receipt["models"].append({"id": model["id"], "source_blend": str(item["source_blend"]),
            "source_blend_sha256": before[str(item["source_blend"])], "blend": str(blend), "blend_sha256": sha(blend),
            "glb": str(glb), "glb_validation": glb_info, "unchanged_component_geometry_count": len(unchanged),
            "new_console_components": 8, "total_components": len(rows), "hud_source_alpha": alpha_info,
            "console_geometry": details})
        print("CRYO_CONSOLE_V3_SAVED " + model["id"] + " " + str(blend), flush=True)
    changed = [path for path, value in before.items() if sha(path) != value]
    require(not changed, "Protected source/v2 files changed: " + str(changed))
    receipt["protected_hash_count"] = len(before)
    receipt["protected_inputs_unchanged"] = True
    receipt["status"] = "GEOMETRY_EXPORT_COMPLETE_NATIVE_ANIMATION_AND_VISUAL_REVIEW_PENDING"
    upgraded["console_upgrade_receipt"] = receipt
    with NEW_MANIFEST.open("x", encoding="utf-8") as handle:
        json.dump(upgraded, handle, indent=2)
        handle.write("\n")
    print("CRYO_CONSOLE_V3_MANIFEST " + str(NEW_MANIFEST), flush=True)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parsed, _ = parser.parse_known_args(args)
    main(parsed.apply)
