"""Assemble private Havolk derivatives using the owner's existing Blender.

Source FBXs are exported read-only by InspectShipVisualSources.py. This script
never writes vendor files or the original player hulls. --inspect makes a CPU
clay contact sheet; the normal mode builds normalized modules and two enemies.
"""
import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Euler, Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Artifacts/ShipVisualPass"
SOURCE = OUT / "Source"
LIBRARY = {}
MATERIAL_PATHS = {}
ASSEMBLIES = []


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_source(row):
    path = SOURCE / row["fbx"]
    assert sha(path) == row["fbx_sha256"], path
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(path), use_custom_normals=True)
    meshes = [obj for obj in set(bpy.data.objects) - before if obj.type == "MESH"]
    assert meshes, path
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.object
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.name = row["name"]
    return obj


def bounds(obj):
    return (Vector([min(v.co[i] for v in obj.data.vertices) for i in range(3)]),
            Vector([max(v.co[i] for v in obj.data.vertices) for i in range(3)]))


def studio(width, height):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 12
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.world = bpy.data.worlds.new("ShipVisualStudio")
    scene.world.color = (.15, .15, .15)
    scene.view_settings.view_transform = "AgX"
    for loc, power, size in [((-8, -6, 18), 2500, 10), ((4, 5, 13), 2000, 8)]:
        data = bpy.data.lights.new("Softbox", "AREA")
        data.energy = power
        data.shape = "DISK"
        data.size = size
        obj = bpy.data.objects.new("Softbox", data)
        scene.collection.objects.link(obj)
        obj.location = loc
        obj.rotation_euler = (-obj.location).to_track_quat("-Z", "Y").to_euler()
    data = bpy.data.cameras.new("ReviewCamera")
    camera = bpy.data.objects.new("ReviewCamera", data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    data.type = "ORTHO"
    return camera


def inspect(inventory):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    clay = bpy.data.materials.new("InspectionClay")
    clay.diffuse_color = (.38, .47, .54, 1)
    clay.use_nodes = True
    bsdf = clay.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = clay.diffuse_color
    bsdf.inputs["Metallic"].default_value = .45
    bsdf.inputs["Roughness"].default_value = .32
    rows = []
    for index, row in enumerate(inventory["assets"]):
        obj = load_source(row)
        lo, hi = bounds(obj)
        extent = hi - lo
        rows.append({"name": row["name"], "blender_bounds_m": [list(lo), list(hi)],
                     "triangles": sum(len(p.vertices) - 2 for p in obj.data.polygons),
                     "material_slots": [m.name for m in obj.data.materials]})
        for vertex in obj.data.vertices:
            vertex.co = (vertex.co - (lo + hi) / 2) * (1.6 / max(extent))
        obj.data.materials.clear()
        obj.data.materials.append(clay)
        for face in obj.data.polygons:
            face.material_index = 0
        column, line = index % 6, index // 6
        obj.location = (column * 2.2 - 5.5, line * 2.25 - 6.75, 0)
        text = bpy.data.curves.new("Label", "FONT")
        text.body = row["name"].removeprefix("SM_")
        text.align_x = "CENTER"
        text.size = .13
        label = bpy.data.objects.new("Label", text)
        bpy.context.scene.collection.objects.link(label)
        label.location = (obj.location.x, obj.location.y - .94, .3)
    camera = studio(1400, 1650)
    camera.location = (0, -6, 30)
    camera.rotation_euler = (Vector((0, 0, 0)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.ortho_scale = 16.2
    bpy.context.scene.render.filepath = str(OUT / "SourceContactSheet.png")
    bpy.ops.render.render(write_still=True)
    (OUT / "SourceGeometry.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")


def part(name, dimensions, location, rotation=(0, 0, 0), palette="White"):
    """Fit a measured source part to metre dimensions without editing its source."""
    source = LIBRARY[name]
    obj = source.copy()
    obj.data = source.data.copy()
    bpy.context.scene.collection.objects.link(obj)
    obj.hide_render = False
    obj.hide_viewport = False
    lo, hi = bounds(obj)
    center = (lo + hi) / 2
    scale = Vector(dimensions)
    extent = hi - lo
    rotation_matrix = Euler(tuple(math.radians(v) for v in rotation)).to_matrix()
    transform = rotation_matrix @ Matrix.Diagonal(Vector([scale[i] / extent[i] for i in range(3)]))
    normal_transform = transform.inverted().transposed()
    normals = [(normal_transform @ n.vector).normalized() for n in obj.data.corner_normals]
    for vertex in obj.data.vertices:
        p = vertex.co - center
        vertex.co = transform @ p + Vector(location)
    obj.data.normals_split_custom_set(normals)
    for i, mat in enumerate(obj.data.materials):
        old_path = MATERIAL_PATHS[mat.name]
        path = old_path.replace("White_Material", palette + "_Material").replace("MI_White_", "MI_" + palette + "_")
        material_name = path.rsplit(".", 1)[1]
        material = bpy.data.materials.get(material_name)
        if not material:
            material = mat.copy()
            material.name = material_name
            material.use_nodes = True
            bsdf = material.node_tree.nodes.get("Principled BSDF")
            color = {"Red": (.35, .035, .018, 1), "Blue": (.06, .17, .32, 1),
                     "Yellow": (.52, .30, .10, 1), "White": (.58, .63, .67, 1)}[palette]
            bsdf.inputs["Base Color"].default_value = color
            bsdf.inputs["Metallic"].default_value = .65
            bsdf.inputs["Roughness"].default_value = .33
        MATERIAL_PATHS[material.name] = path
        obj.data.materials[i] = material
    return obj


def export_assembly(name, parts, description):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in parts:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    if len(parts) > 1:
        bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = name
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    mesh = obj.data
    mesh.calc_loop_triangles()
    assert mesh.uv_layers.active, name
    uv = mesh.uv_layers.active.data
    positions = [obj.matrix_world @ vertex.co for vertex in mesh.vertices]
    normal_matrix = obj.matrix_world.to_3x3().inverted().transposed()
    normal_ids, normals, uv_ids, uvs, triangles = {}, [], {}, [], []
    for tri in mesh.loop_triangles:
        corners = []
        for loop in tri.loops:
            normal = (normal_matrix @ mesh.corner_normals[loop].vector).normalized()
            normal_key = tuple(round(float(v), 7) for v in normal)
            uv_key = tuple(round(float(v), 7) for v in uv[loop].uv)
            assert all(math.isfinite(v) for v in normal_key + uv_key)
            if normal_key not in normal_ids:
                normal_ids[normal_key] = len(normals) + 1
                normals.append(normal_key)
            if uv_key not in uv_ids:
                uv_ids[uv_key] = len(uvs) + 1
                uvs.append(uv_key)
            corners.append((mesh.loops[loop].vertex_index + 1, uv_ids[uv_key], normal_ids[normal_key]))
        triangles.append((tri.material_index, corners))
    used = {index for index, corners in triangles}
    material_paths = {mat.name: MATERIAL_PATHS[mat.name] for index, mat in enumerate(mesh.materials) if index in used}
    def number(value):
        return f"{value:.7f}"
    lines = ["# Owner-licensed Havolk derivative. Private; +X forward, +Z up, centimetres.",
             "mtllib " + name + ".mtl", "o " + name]
    lines += ["v " + " ".join(number(v * 100) for v in point) for point in positions]
    lines += ["vt " + " ".join(number(v) for v in coord) for coord in uvs]
    lines += ["vn " + " ".join(number(v) for v in normal) for normal in normals]
    for index, mat in enumerate(mesh.materials):
        if index not in used:
            continue
        lines.append("usemtl " + mat.name)
        lines += ["f " + " ".join("/".join(str(v) for v in corner) for corner in corners)
                  for material_index, corners in triangles if material_index == index]
    destination = OUT / "Assembly"
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / (name + ".obj")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (destination / (name + ".mtl")).write_text("\n".join("newmtl " + mat + "\nKd .6 .6 .6\nd 1\n" for mat in material_paths),
                                               encoding="utf-8")
    lo = [min(point[i] for point in positions) * 100 for i in range(3)]
    hi = [max(point[i] for point in positions) * 100 for i in range(3)]
    assert len(triangles) < 80000, (name, len(triangles))
    ASSEMBLIES.append({"name": name, "description": description, "triangles": len(triangles),
                       "bounds_cm": [lo, hi], "materials": material_paths, "obj_sha256": sha(target)})
    obj.hide_render = True
    return obj


def modules():
    def profile_radius(x, swift):
        script = ROOT / ("ContentSource/SwiftCandidate/Generate.py" if swift else "ContentSource/GenerateAcornShipCandidate.py")
        tree = ast.parse(script.read_text(encoding="utf-8-sig"))
        profile = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                       and any(isinstance(target, ast.Name) and target.id == "PROFILE" for target in node.targets))
        for i in range(len(profile) - 1):
            if x <= profile[i + 1][0]:
                a, ra = profile[i]
                b, rb = profile[i + 1]
                prior, after = profile[max(0, i - 1)], profile[min(len(profile) - 1, i + 2)]
                ma, mb = (rb - prior[1]) / (b - prior[0]), (after[1] - ra) / (after[0] - a)
                t = max(0, min(1, (x - a) / (b - a)))
                return (2*t**3 - 3*t*t + 1)*ra + (t**3 - 2*t*t + t)*(b-a)*ma + (-2*t**3 + 3*t*t)*rb + (t**3 - t*t)*(b-a)*mb
        raise ValueError("Module outside authored hull profile")
    for tier in range(2, 6):
        level = tier - 1
        for swift in (False, True):
            plates, emitters = [], []
            suffix = "Swift" if swift else ""
            zscale = .84 if swift else .68
            for side, hand in [(-1, "L"), (1, "R")]:
                for index in range(level):
                    x = .75 - index * .42
                    radius = profile_radius(x, swift)
                    plate_y = math.sqrt(radius**2 - (.15 / zscale)**2) + .015
                    shield_y = math.sqrt(radius**2 - (.22 / zscale)**2) + .02
                    plates.append(part("SM_" + hand + "_Wing_3", (.40, .18, .12), (x, side * plate_y, -.15),
                                       rotation=(side * 14, 0, 0), palette="Yellow"))
                    emitters.append(part("SM_Beam_Engine", (.21, .16, .17), (x, side * shield_y, .22), palette="Blue"))
            export_assembly("SM_UpgradeHull" + suffix + str(tier), plates,
                            "Paired lower flank armor tiles fitted to " + ("Swift" if swift else "Starter") + " profile; II-V.")
            export_assembly("SM_UpgradeShield" + suffix + str(tier), emitters,
                            "Paired blue shield projector arches fitted to " + ("Swift" if swift else "Starter") + " profile; cockpit unchanged.")
        engines, thrusters = [], []
        for side, hand in [(-1, "L"), (1, "R")]:
            engines.append(part("SM_" + hand + "_Engine_1", (.54 + level * .07, .24 + level * .015, .24 + level * .015),
                                (-1.98, side * .54, -.32), rotation=(0, 0, 180), palette="Yellow"))
            thrusters.append(part("SM_" + hand + "_Engine_6", (.38 + level * .035, .18, .21),
                                  (-.90, side * 1.18, -.24), rotation=(0, 0, -side * 90), palette="White"))
            if tier >= 4:
                engines.append(part("SM_" + hand + "_Engine_5", (.32 + level * .03, .10, .12),
                                    (-1.92, side * .83, -.40), rotation=(0, 0, 180), palette="Yellow"))
                thrusters.append(part("SM_" + hand + "_Engine_6", (.27 + level * .03, .15, .16),
                                      (.70, side * .66, -.17), rotation=(0, 0, -side * 90), palette="White"))
        export_assembly("SM_UpgradeEngine" + str(tier), engines, "Progressive paired aft booster cassettes; auxiliary stages at IV-V.")
        export_assembly("SM_UpgradeThrusters" + str(tier), thrusters, "Lateral maneuver pods; additional fore pair at IV-V.")
        for weapon, source in [("Laser", "SM_Weapon_5"), ("Cannon", "SM_Weapon")]:
            barrel = [part(source, (.68 + .045 * level, .16 if weapon == "Laser" else .24,
                                    .16 if weapon == "Laser" else .26), (1.48, 0, -.28))]
            # Structural sleeves make tiers legible without suggesting extra active weapons.
            for index in range(level - 1):
                barrel.append(part("SM_Rocket_4", (.12, .23 if weapon == "Laser" else .31, .14),
                                   (1.18 + index * .15, 0, -.18)))
            export_assembly("SM_Upgrade" + weapon + str(tier), barrel,
                            "Single " + weapon + " housing with progressive structural sleeves; active slot unchanged.")
    fins = [part("SM_" + hand + "_Wing_2", (.42, .31, .29), (-1.46, side * .85, .04),
                 rotation=(side * 45, 0, 0), palette="Blue") for side, hand in [(-1, "L"), (1, "R")]]
    export_assembly("SM_UtilityVector", fins, "Paired vector-control vanes for the existing equipped Vector Thrusters utility.")
    cooler = [part("SM_Beam_Engine", (.54, .66, .24), (-1.25, 0, -.51), palette="Blue")]
    export_assembly("SM_UtilityCooling", cooler, "Underslung radiator loop for the existing equipped Overdrive Cooling utility.")


def enemies():
    for kind, palette in [("Pursuer", "Red"), ("Flanker", "Blue")]:
        flanker = kind == "Flanker"
        pieces = [part("SM_Spacecraft_2", (2.82, 1.20, 1.26), (.15, 0, .04), palette=palette)]
        for side, hand in [(-1, "L"), (1, "R")]:
            wing = "6" if flanker else "1"
            pieces.append(part("SM_" + hand + "_Wing_" + wing, (1.48 if flanker else 1.25,
                               1.32 if flanker else .52, .27 if flanker else .12),
                               (-.22 if flanker else -.43, side * (1.09 if flanker else .77), -.18), palette=palette))
            pieces.append(part("SM_" + hand + "_Engine_" + ("6" if flanker else "3"),
                               (.95, .33, .40), (-.80, side * (1.54 if flanker else .76), -.20),
                               rotation=(0, 0, 180), palette=palette))
            pieces.append(part("SM_" + hand + "_Wing_4", (.48, 1.25 if flanker else .64, .18),
                               (-.80, side * (1.05 if flanker else .60), -.20), palette=palette))
            pieces.append(part("SM_Weapon_" + ("1" if flanker else "4"), (.85, .10, .11),
                               (.61, side * (.82 if flanker else .64), -.22)))
        export_assembly("SM_" + kind + "Havolk", pieces,
                        ("Broad swept-wing flanking silhouette" if flanker else "Compact narrow direct-pressure silhouette") +
                        "; existing enemy kind, movement, health, weapons and collision radius unchanged.")


def assembly(inventory, render):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    for row in inventory["assets"]:
        obj = load_source(row)
        # Exported FBX is right-handed. Inspection establishes nose/barrels -Y;
        # rotate rigidly to the project's +X-forward, +Z-up centimetre export.
        rotation = Matrix.Rotation(math.pi / 2, 3, "Z")
        normals = [(rotation @ n.vector).normalized() for n in obj.data.corner_normals]
        for vertex in obj.data.vertices:
            x, y, z = vertex.co
            vertex.co = (-y, x, z)
        obj.data.normals_split_custom_set(normals)
        assert len(obj.data.materials) == len(row["materials"]) == 1
        path = row["materials"][0]
        old = obj.data.materials[0]
        name = path.rsplit(".", 1)[1]
        material = bpy.data.materials.get(name) or old
        material.name = name
        material.use_nodes = True
        # Source FBX contains the artist's external texture filenames. Clay fit
        # previews deliberately omit these; Unreal assigns the intact vendor MI.
        for node in list(material.node_tree.nodes):
            if node.type == "TEX_IMAGE":
                material.node_tree.nodes.remove(node)
        bsdf = material.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (.52, .57, .60, 1)
        bsdf.inputs["Metallic"].default_value = .65
        bsdf.inputs["Roughness"].default_value = .33
        MATERIAL_PATHS[material.name] = path
        obj.data.materials[0] = material
        obj.hide_render = True
        LIBRARY[row["name"]] = obj
    modules()
    enemies()
    report = {"generator_sha256": sha(__file__), "source_inventory_sha256": sha(SOURCE / "Inventory.json"),
              "source_fbx_sha256": {row["fbx"]: row["fbx_sha256"] for row in inventory["assets"]},
              "assets": ASSEMBLIES, "units": "centimetres", "forward": "+X", "up": "+Z",
              "limits": ["Source assembly and CPU geometry previews; native material, fit and performance review remains required.",
                         "Original acorn/Swift hull and pilot unchanged. Six visual components derive from existing purchases only."]}
    (OUT / "Assembly/Assembly.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if render:
        preview_assemblies()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "Assembly/ShipVisualPass.blend"))
    print("SHIP_VISUAL_ASSEMBLY_OK", len(ASSEMBLIES))


def preview_assemblies():
    camera = studio(1400, 850)
    camera.data.ortho_scale = 7.8
    for name in ("SM_PursuerHavolk", "SM_FlankerHavolk"):
        obj = bpy.data.objects[name]
        obj.hide_render = False
        camera.location = (5.0, -6.3, 4.7)
        camera.rotation_euler = (-camera.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.scene.render.filepath = str(OUT / (name + ".png"))
        bpy.ops.render.render(write_still=True)
        obj.hide_render = True
    # Existing authored hulls are loaded only for fit renders, never exported.
    for hull, file in [("Starter", ROOT / "ContentSource/AcornShipGripFit/AcornShipGripFit.glb"),
                       ("Swift", ROOT / "ContentSource/SwiftCandidate/SwiftCandidate.glb")]:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(file))
        added = set(bpy.data.objects) - before
        for obj in added:
            if obj.type == "MESH":
                obj.hide_render = False
        active = [bpy.data.objects["SM_Upgrade" + track + ("Swift" if hull == "Swift" and track in ("Hull", "Shield") else "") + "5"]
                  for track in ("Hull", "Shield", "Engine", "Thrusters", "Laser")]
        active.append(bpy.data.objects["SM_UtilityVector"])
        for obj in active:
            obj.hide_render = False
        for view, loc in [("Chase", (-6.5, -4.8, 3.8)), ("Side", (1.0, -7.8, 2.2))]:
            camera.location = loc
            camera.rotation_euler = (Vector((0, 0, .25)) - camera.location).to_track_quat("-Z", "Y").to_euler()
            camera.data.ortho_scale = 6.5
            bpy.context.scene.render.filepath = str(OUT / (hull + "TierV" + view + ".png"))
            bpy.ops.render.render(write_still=True)
        for obj in active:
            obj.hide_render = True
        cannon = bpy.data.objects["SM_UpgradeCannon5"]
        cooling = bpy.data.objects["SM_UtilityCooling"]
        cannon.hide_render = cooling.hide_render = False
        camera.location = (-3.7, -6.0, -2.6)
        camera.rotation_euler = (Vector((0, 0, -.15)) - camera.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.scene.render.filepath = str(OUT / (hull + "CannonCooling.png"))
        bpy.ops.render.render(write_still=True)
        cannon.hide_render = cooling.hide_render = True
        for obj in added:
            bpy.data.objects.remove(obj, do_unlink=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    inventory = json.loads((SOURCE / "Inventory.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    if args.inspect:
        inspect(inventory)
    else:
        assembly(inventory, args.render)


if __name__ == "__main__":
    main()
