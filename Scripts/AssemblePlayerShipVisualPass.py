"""Build a private closed Havolk player hull and fitted modules in Blender.

Uses the existing audited FBX export only. Does not recopy or rewrite source
assets, prior assemblies, the artist's original hull, or any avatar/animation.
Run with the installed Blender in background mode; the lead owns Unreal import.
"""
import importlib.util
import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Artifacts/PlayerShipVisualPass"
HELPER = ROOT / "Scripts/AssembleShipVisualPass.py"
ENCODER = ROOT / "Scripts/EncodeUnrealObj.py"
spec = importlib.util.spec_from_file_location("ship_parts", HELPER)
parts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parts)
parts.OUT = OUT
encoder_spec = importlib.util.spec_from_file_location("unreal_obj", ENCODER)
unreal_obj = importlib.util.module_from_spec(encoder_spec)
encoder_spec.loader.exec_module(unreal_obj)
CONTACTS = []
HULL_BVH = None


def hull_contact(origin, direction):
    """Use the assembled hull's actual triangles for attachment contact."""
    point, normal, _, _ = HULL_BVH.ray_cast(Vector(origin), Vector(direction), 6.)
    assert point is not None, (origin, direction)
    CONTACTS.append({"origin_m": origin, "surface_m": list(point), "normal": list(normal)})
    return point


def top_contact(x, side):
    # Narrow to the actual closed fuselage cross-section, never place a
    # projector over an empty gap merely because it is inside the AABB.
    for width in (.32, .24, .16, .12):
        origin = (x, side * width, 3.)
        point, _, _, _ = HULL_BVH.ray_cast(Vector(origin), Vector((0, 0, -1)), 6.)
        if point is not None:
            return hull_contact(origin, (0, 0, -1))
    raise ValueError(f"No paired shield mounting surface at {x}, {side}")


def load_library(inventory):
    for row in inventory["assets"]:
        obj = parts.load_source(row)
        rotation = Matrix.Rotation(math.pi / 2, 3, "Z")
        normals = [(rotation @ n.vector).normalized() for n in obj.data.corner_normals]
        for vertex in obj.data.vertices:
            x, y, z = vertex.co
            vertex.co = (-y, x, z)
        obj.data.normals_split_custom_set(normals)
        assert len(obj.data.materials) == len(row["materials"]) == 1
        path = row["materials"][0]
        material = obj.data.materials[0]
        material.name = path.rsplit(".", 1)[1]
        material.use_nodes = True
        for node in list(material.node_tree.nodes):
            if node.type == "TEX_IMAGE":
                material.node_tree.nodes.remove(node)
        bsdf = material.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (.60, .66, .71, 1)
        bsdf.inputs["Metallic"].default_value = .65
        bsdf.inputs["Roughness"].default_value = .3
        parts.MATERIAL_PATHS[material.name] = path
        obj.hide_render = True
        parts.LIBRARY[row["name"]] = obj


def hull():
    global HULL_BVH
    part = parts.part
    craft = [part("SM_Spacecraft_2", (4.6, 1.25, 1.15), (.0, 0, .0))]
    for side, hand in [(-1, "L"), (1, "R")]:
        craft.append(part("SM_" + hand + "_Wing_5", (1.75, 1.45, .25),
                          (-.40, side * 1.13, -.18)))
        craft.append(part("SM_" + hand + "_Engine_1", (1.35, .45, .45),
                          (-1.62, side * 1.02, .10), rotation=(0, 0, 180)))
        craft.append(part("SM_" + hand + "_Wing_2", (.72, .40, .26),
                          (-1.28, side * .76, .25), rotation=(side * 32, 0, 0), palette="Blue"))
    craft.append(part("SM_Rocket_4", (.46, .40, .18), (1.35, 0, -.36)))
    body = parts.export_assembly("SM_PlayerHavolkStarter", craft,
                                 "Provisional closed player craft: slender real fuselage, angular paired wings, "
                                 "twin engine nacelles and blue aft stabilizers. Original starter remains fallback.")
    # Build from final vertices directly; do not use a stale evaluated-object
    # ray cache immediately after joining edited copies of the source meshes.
    HULL_BVH = BVHTree.FromPolygons([body.matrix_world @ vertex.co for vertex in body.data.vertices],
                                   [tuple(face.vertices) for face in body.data.polygons])


def modules():
    part = parts.part
    export = parts.export_assembly
    for tier in range(2, 6):
        level = tier - 1
        armor, shield, engines, thrusters = [], [], [], []
        for side, hand in [(-1, "L"), (1, "R")]:
            for index in range(level):
                x = .70 - index * .42
                flank = hull_contact((x, side * 3., .10), (0, -side, 0))
                top = top_contact(x, side)
                armor.append(part("SM_" + hand + "_Wing_3", (.34, .19, .12),
                                  (x, flank.y + side * .015, .10), palette="Yellow"))
                shield.append(part("SM_Beam_Engine", (.20, .17, .15),
                                   (x, top.y, top.z + .015), palette="Blue"))
            # The scaled matching engine casing encloses its base casing; it
            # changes presentation without adding a new active engine/weapon.
            engines.append(part("SM_" + hand + "_Engine_1",
                                (1.39 + level * .02, .49 + level * .015, .49 + level * .015),
                                (-1.62, side * 1.02, .10), rotation=(0, 0, 180), palette="Blue"))
            thrusters.append(part("SM_" + hand + "_Engine_6", (.34 + level * .035, .19, .21),
                                  (-.64, side * 1.60, -.15), rotation=(0, 0, -side * 90)))
            if tier >= 4:
                thrusters.append(part("SM_" + hand + "_Engine_6", (.26, .14, .17),
                                      (.14, side * 1.05, -.18), rotation=(0, 0, -side * 90)))
        for track, objects in [("Hull", armor), ("Shield", shield), ("Engine", engines), ("Thrusters", thrusters)]:
            export("SM_UpgradeHavolk" + track + str(tier), objects,
                   "Fitted " + track + " presentation for the private closed player hull; existing tier unchanged.")
        for weapon, source in [("Laser", "SM_Weapon_5"), ("Cannon", "SM_Weapon")]:
            barrel = [part(source, (.80 + .02 * level, .16 if weapon == "Laser" else .24,
                                    .16 if weapon == "Laser" else .25), (2.0, 0, -.25))]
            for index in range(level - 1):
                barrel.append(part("SM_Rocket_4", (.10, .24 if weapon == "Laser" else .31, .13),
                                   (1.78 + index * .13, 0, -.22)))
            export("SM_UpgradeHavolk" + weapon + str(tier), barrel,
                   "Single ventral " + weapon + " housing with tier sleeves; real muzzle and damage unchanged.")
    fins = [part("SM_" + hand + "_Wing_2", (.42, .31, .22), (-1.40, side * .97, .42),
                 rotation=(side * 48, 0, 0), palette="Blue") for side, hand in [(-1, "L"), (1, "R")]]
    export("SM_UtilityHavolkVector", fins, "Two fitted vector-control vanes for the existing utility slot.")
    radiator = hull_contact((-.86, 0, 3.), (0, 0, -1))
    export("SM_UtilityHavolkCooling", [part("SM_Beam_Engine", (.48, .55, .17),
                                         (-.86, 0, radiator.z + .02), palette="Blue")],
           "Dorsal radiator frame fitted to the existing utility slot.")


def preview():
    camera = parts.studio(1440, 960)
    camera.data.ortho_scale = 6.8
    body = bpy.data.objects["SM_PlayerHavolkStarter"]
    body.hide_render = False
    views = [("Front", (6.2, -7.4, 4.2)), ("Chase", (-7.3, -5.8, 3.9)),
             ("Side", (.1, -8.5, 1.35)), ("Top", (0, 0, 10))]
    selected = [bpy.data.objects["SM_UpgradeHavolk" + track + "5"]
                for track in ("Hull", "Shield", "Engine", "Thrusters", "Laser")]
    selected.append(bpy.data.objects["SM_UtilityHavolkVector"])
    for tier in ("Base", "TierV"):
        for obj in selected:
            obj.hide_render = tier != "TierV"
        for view, location in views:
            camera.location = location
            camera.rotation_euler = (Vector((0, 0, .05)) - camera.location).to_track_quat("-Z", "Y").to_euler()
            bpy.context.scene.render.filepath = str(OUT / (tier + view + ".png"))
            bpy.ops.render.render(write_still=True)
    for obj in selected:
        obj.hide_render = True
    for name in ("SM_UpgradeHavolkCannon5", "SM_UtilityHavolkCooling"):
        bpy.data.objects[name].hide_render = False
    camera.location = (4.8, -6.2, 3.4)
    camera.rotation_euler = (-camera.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.render.filepath = str(OUT / "CannonCooling.png")
    bpy.ops.render.render(write_still=True)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    inventory_path = parts.SOURCE / "Inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    load_library(inventory)
    hull()
    modules()
    for row in parts.ASSEMBLIES:
        encoded = unreal_obj.encode(OUT / "Assembly" / (row["name"] + ".obj"))
        row["obj_sha256"] = encoded["encoded_sha256"]
        row["obj_encoding"] = encoded
    report = {"generator_sha256": parts.sha(__file__), "helper_sha256": parts.sha(HELPER),
              "coordinate_encoder_sha256": parts.sha(ENCODER), "obj_space": unreal_obj.SPACE,
              "source_inventory_sha256": parts.sha(inventory_path),
              "source_fbx_sha256": {r["fbx"]: r["fbx_sha256"] for r in inventory["assets"]},
              "assets": parts.ASSEMBLIES, "measured_hull_contacts": CONTACTS,
              "units": "centimetres", "forward": "+X", "up": "+Z",
              "limits": ["CPU material-fit preview; actual vendor materials assigned by Unreal import.",
                         "New provisional player appearance only; original hulls, rigs and all gameplay preserved."]}
    (OUT / "Assembly/Assembly.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    preview()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "Assembly/PlayerShipVisualPass.blend"))
    print("PLAYER_SHIP_VISUAL_ASSEMBLY_OK", len(parts.ASSEMBLIES))


if __name__ == "__main__":
    main()
