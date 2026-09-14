"""Original, separate Phase 1 enemy candidates; Blender 5.1, no external assets.
Build: blender --background --threads 8 --python Generate.py
Render: blender --background --threads 8 --python Generate.py -- --render
Only writes this EnemyCandidates directory. No Unreal import or gameplay edits.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
PARTS = []
MATS = {}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1
    PARTS.clear()
    MATS.clear()
    for name, color, metal, rough, emission in [
        ("EN_Titanium", (.035, .049, .063), .83, .34, 0),
        ("EN_Ceramic", (.24, .28, .26), .12, .37, 0),
        ("EN_Recess", (.009, .014, .020), .40, .42, 0),
        ("EN_Amber", (.95, .115, .012), .10, .27, 2.6),
    ]:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        node = mat.node_tree.nodes["Principled BSDF"]
        for key, value in {
            "Base Color": (*color, 1), "Metallic": metal, "Roughness": rough,
            "Emission Color": (*color, 1), "Emission Strength": emission,
            "Coat Weight": .18 if name == "EN_Ceramic" else .04,
            "Coat Roughness": .25,
        }.items():
            node.inputs[key].default_value = value
        mat.diffuse_color = (*color, 1)
        MATS[name] = mat


def body(name, verts, faces, material="EN_Titanium", bevel=.01, smooth=False):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.materials.append(MATS[material])
    for p in mesh.polygons:
        p.use_smooth = smooth
    if smooth:
        mesh.set_sharp_from_angle(angle=math.radians(42))
    if bevel:
        mod = obj.modifiers.new("Manufactured edge radii", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = "ANGLE"
        mod.angle_limit = .35
        mod.harden_normals = True
    mod = obj.modifiers.new("Planar weighted highlights", "WEIGHTED_NORMAL")
    mod.keep_sharp = True
    mod.weight = 50
    PARTS.append(obj)
    return obj


def prism(name, polygon, low, high, material="EN_Titanium", bevel=.012):
    if sum(polygon[i][0] * polygon[(i + 1) % len(polygon)][1] -
           polygon[(i + 1) % len(polygon)][0] * polygon[i][1]
           for i in range(len(polygon))) < 0:
        polygon = list(reversed(polygon))
    n = len(polygon)
    verts = [(x, y, z) for z in (low, high) for x, y in polygon]
    faces = [tuple(reversed(range(n))), tuple(range(n, n * 2))]
    faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    return body(name, verts, faces, material, min(bevel, (high - low) * .30))


def box(name, at, size, material="EN_Titanium", bevel=.008, rotation=0):
    x, y, z = at
    a, b, c = [v / 2 for v in size]
    obj = body(name, [(x + u * a, y + v * b, z + w * c)
                     for w in (-1, 1) for v in (-1, 1) for u in (-1, 1)],
               [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4),
                (1, 3, 7, 5), (3, 2, 6, 7), (2, 0, 4, 6)],
               material, min(bevel, min(size) * .30))
    if rotation:
        for vertex in obj.data.vertices:
            dx, dy = vertex.co.x - x, vertex.co.y - y
            vertex.co.x = x + dx * math.cos(rotation) - dy * math.sin(rotation)
            vertex.co.y = y + dx * math.sin(rotation) + dy * math.cos(rotation)
    return obj


def loft(name, rings, material="EN_Titanium", sides=32, center=(0, 0, 0), zscale=1, bevel=0):
    # Cross sections run around the X axis; radius is never zero.
    verts = [(center[0] + x, center[1] + radius * math.cos(a * math.tau / sides),
              center[2] + radius * math.sin(a * math.tau / sides) * zscale)
             for x, radius in rings for a in range(sides)]
    faces = [(i * sides + a, i * sides + (a + 1) % sides,
              (i + 1) * sides + (a + 1) % sides, (i + 1) * sides + a)
             for i in range(len(rings) - 1) for a in range(sides)]
    faces += [tuple(reversed(range(sides))),
              tuple(range((len(rings) - 1) * sides, len(rings) * sides))]
    return body(name, verts, faces, material, bevel, True)


def annulus(name, rings, center=(0, 0, 0), material="EN_Titanium", sides=40):
    # Closed annular cross section: visible mouth, inner wall, rear return.
    verts = [(x + center[0], radius * math.cos(a * math.tau / sides) + center[1],
              radius * math.sin(a * math.tau / sides) + center[2])
             for x, radius in rings for a in range(sides)]
    n = len(rings)
    faces = [(i * sides + a, i * sides + (a + 1) % sides,
              ((i + 1) % n) * sides + (a + 1) % sides, ((i + 1) % n) * sides + a)
             for i in range(n) for a in range(sides)]
    return body(name, verts, faces, material, 0, True)


def fastener(name, x, y, z, radius=.014):
    sides = 8
    verts = [(x + radius * math.cos(a * math.tau / sides),
              y + radius * math.sin(a * math.tau / sides), height)
             for height in (z - .007, z + .002) for a in range(sides)]
    faces = [tuple(reversed(range(sides))), tuple(range(sides, sides * 2))]
    faces += [(i, (i + 1) % sides, (i + 1) % sides + sides, i + sides) for i in range(sides)]
    return body(name, verts, faces, "EN_Recess", .0018)


def engine(name, x, y, z, radius=.21):
    loft(name + " pressure fairing", [(-.32, radius * .92), (-.26, radius * 1.06),
         (.12, radius), (.29, radius * .70), (.39, radius * .18)],
         center=(x, y, z), sides=32, bevel=.006)
    annulus(name + " deep machined exhaust", [(-.51, radius * .93), (-.49, radius * 1.01),
         (-.27, radius * 1.02), (-.24, radius * .68), (-.40, radius * .65),
         (-.48, radius * .78)], (x, y, z))
    annulus(name + " ceramic retention lip", [(-.484, radius * 1.015), (-.465, radius * 1.025),
         (-.444, radius * 1.02), (-.45, radius * .97)], (x, y, z), "EN_Ceramic", 40)
    loft(name + " recessed exhaust glow", [(-.404, radius * .635), (-.399, radius * .635)],
         "EN_Amber", 40, (x, y, z))
    loft(name + " injector center", [(-.417, radius * .21), (-.410, radius * .24),
         (-.398, radius * .24)], "EN_Recess", 24, (x, y, z))
    for i in range(10):
        angle = i * math.tau / 10
        yy, zz = y + radius * .96 * math.cos(angle), z + radius * .96 * math.sin(angle)
        obj = box(name + " cooling rib %02d" % i, (x - .36, yy, zz),
                  (.18, .026, .018), "EN_Recess", .003)
        # Rotate each narrow rib about its local X center.
        for v in obj.data.vertices:
            dy, dz = v.co.y - yy, v.co.z - zz
            v.co.y, v.co.z = yy + dy * math.cos(angle) - dz * math.sin(angle), zz + dy * math.sin(angle) + dz * math.cos(angle)


def weapon_and_sensor(front):
    # One existing central projectile emitter; no extra weapon mounts.
    loft("Single central emitter housing", [(front - .34, .105), (front - .19, .113),
         (front - .045, .070)], "EN_Recess", 32, zscale=.78)
    annulus("Single emitter recessed muzzle", [(front - .10, .073), (front, .063),
         (front, .044), (front - .09, .043)], material="EN_Titanium", sides=40)
    loft("Single emitter amber aperture", [(front - .058, .040), (front - .052, .040)],
         "EN_Amber", 32)
    box("Autonomous sensor recessed mask", (front - .36, 0, .153), (.23, .30, .052), "EN_Recess", .018)
    for y in (-.077, .077):
        box("Small passive sensor lens %.3f" % y, (front - .232, y, .158),
            (.009, .055, .020), "EN_Amber", .003)


def build_pursuer():
    loft("Armored pressure spine", [(-1.13, .19), (-1.03, .31), (-.69, .42),
         (-.18, .38), (.42, .27), (.94, .13), (1.10, .068)],
         "EN_Recess", 24, zscale=.68, bevel=.009)
    # Broad clipped shoulders converge into a strong single forward wedge.
    prism("Port and starboard armor bed", [(-1.12, -.36), (-.66, -.72), (.18, -.54),
          (.94, -.18), (1.10, 0), (.94, .18), (.18, .54), (-.66, .72), (-1.12, .36)],
          -.09, .07, bevel=.024)
    for sign in (-1, 1):
        outline = [(-1.04, sign * .33), (-.61, sign * .675), (.13, sign * .50),
                   (.72, sign * .23), (.29, sign * .21), (-.58, sign * .31)]
        prism("Shoulder ceramic armor %d" % sign, outline, .075, .132, "EN_Ceramic", .015)
        prism("Forward cheek armor %d" % sign, [(.25, sign * .20), (.39, sign * .34),
              (1.03, sign * .107), (.95, sign * .068)], -.025, .15, bevel=.015)
        prism("Short swept stabilizer %d" % sign, [(-.97, sign * .45), (-.57, sign * .46),
              (-.67, sign * .96), (-1.10, sign * .80)], -.115, -.05, bevel=.016)
        prism("Stabilizer inset %d" % sign, [(-.967, sign * .55), (-.63, sign * .525),
              (-.715, sign * .876), (-1.015, sign * .765)], -.043, -.026, "EN_Ceramic", .009)
        engine("Pursuer drive %d" % sign, -.87, sign * .43, -.105, .20)
        # Dark panel wells and separated ribs give real depth.
        box("Shoulder radiator well %d" % sign, (-.35, sign * .395, .152), (.44, .14, .028), "EN_Recess", .012, sign * -.19)
        for i in range(7):
            box("Shoulder radiator fin %d %d" % (sign, i), (-.54 + i * .060, sign * .395, .175),
                (.022, .112, .032), "EN_Titanium", .003, sign * -.19)
        box("Aft narrow identification slit %d" % sign, (-.86, sign * .49, .147), (.12, .018, .008), "EN_Amber", .003)
        for i, (x, y) in enumerate([(-.84, .41), (-.53, .56), (-.11, .46), (.33, .32), (-.80, .76)]):
            fastener("Shoulder captive fastener %d %d" % (sign, i), x, sign * y, .140 if i < 4 else -.020)
        box("Side seam %d" % sign, (.015, sign * .29, .204), (.63, .021, .021), "EN_Recess", .004)
    prism("Central forward armor", [(-.72, -.23), (.30, -.205), (.83, -.086),
          (1.03, 0), (.83, .086), (.30, .205), (-.72, .23)], .175, .258, bevel=.023)
    prism("Recessed dorsal service well", [(-.83, -.185), (-.24, -.16), (.06, 0),
          (-.24, .16), (-.83, .185)], .249, .270, "EN_Recess", .012)
    prism("Dorsal ceramic hatch", [(-.76, -.145), (-.31, -.126), (-.04, 0),
          (-.31, .126), (-.76, .145)], .272, .299, "EN_Ceramic", .009)
    for i in range(5):
        box("Dorsal heat exchanger %d" % i, (-.97 + i * .045, 0, .288),
            (.015, .25, .033), "EN_Titanium", .003)
    weapon_and_sensor(1.33)


def build_flanker():
    loft("Thin central pressure hull", [(-1.05, .11), (-.84, .28), (-.36, .32),
         (.22, .25), (.70, .16), (1.01, .07)], "EN_Recess", 24, zscale=.54, bevel=.008)
    for sign in (-1, 1):
        # Broad swept wings have connected spars, stepped plate edges and open aft notches.
        outline = [(.76, sign * .20), (.33, sign * .66), (-.38, sign * 1.61),
                   (-.68, sign * 1.73), (-.82, sign * 1.51), (-.58, sign * .89),
                   (-.97, sign * .36), (-.83, sign * .19)]
        prism("Swept wing structural shell %d" % sign, outline, -.065, .012, bevel=.021)
        inset = [(.55, sign * .27), (.22, sign * .64), (-.40, sign * 1.48),
                 (-.62, sign * 1.56), (-.67, sign * 1.45), (-.46, sign * .88),
                 (-.71, sign * .38)]
        # Separate spanwise plates with actual dark seams; ceramic is an accent.
        def span_clip(poly, limit, greater):
            clipped = []
            for a, b in zip(poly, poly[1:] + poly[:1]):
                av, bv = a[1] * sign, b[1] * sign
                ai = av >= limit if greater else av <= limit
                bi = bv >= limit if greater else bv <= limit
                if ai:
                    clipped.append(a)
                if ai != bi:
                    t = (limit - av) / (bv - av)
                    clipped.append((a[0] + t * (b[0] - a[0]), sign * limit))
            return clipped
        for plate, (low, high, material) in enumerate([
            (.27, .725, "EN_Titanium"), (.740, 1.055, "EN_Ceramic"),
            (1.070, 1.70, "EN_Titanium")]):
            poly = span_clip(span_clip(inset, low, True), high, False)
            if len(poly) >= 3:
                prism("Swept separated wing plate %d %d" % (sign, plate), poly,
                      .016, .058, material, .008)
        prism("Outer wing titanium leading cap %d" % sign, [(.30, sign * .63), (-.38, sign * 1.61),
              (-.67, sign * 1.73), (-.62, sign * 1.58), (-.43, sign * 1.49), (.18, sign * .66)],
              .004, .056, bevel=.009)
        prism("Wing trailing machinery bay %d" % sign, [(-.65, sign * .46), (-.43, sign * .76),
              (-.60, sign * .97), (-.91, sign * .55)], .055, .085, "EN_Recess", .014)
        for i in range(8):
            x, y = -.77 + i * .037, sign * (.53 + i * .046)
            box("Angled radiator bank %d %d" % (sign, i), (x, y, .090), (.028, .18, .026),
                "EN_Titanium", .003, sign * -.65)
        engine("Flanker drive %d" % sign, -.66, sign * .345, -.10, .175)
        # Slender canted stabilizers are part of silhouette, without moving surfaces.
        fin = prism("Canted aft stabilizer %d" % sign, [(-1.02, sign * .41), (-.55, sign * .39),
              (-.82, sign * .53), (-1.09, sign * .52)], .012, .052, "EN_Titanium", .01)
        for v in fin.data.vertices:
            v.co.z += max(0, (-v.co.x - .53)) * .30
        box("Wingtip identification slit %d" % sign, (-.59, sign * 1.57, .066),
            (.13, .018, .007), "EN_Amber", .002, sign * -.32)
        for i, (x, y) in enumerate([(.17, .61), (-.21, 1.11), (-.52, 1.45), (-.56, .44), (-.57, .83)]):
            fastener("Wing captive fastener %d %d" % (sign, i), x, sign * y, .066)
        # Narrow void between central dorsal rail and wing is deliberate relief.
        prism("Inner shoulder rail %d" % sign, [(-.75, sign * .19), (.25, sign * .22),
              (.61, sign * .15), (.53, sign * .095), (-.75, sign * .105)],
              .13, .192, bevel=.016)
    prism("Central tapered ceramic plate", [(-.73, -.18), (.19, -.16), (.76, -.045),
          (.86, 0), (.76, .045), (.19, .16), (-.73, .18)], .194, .231, "EN_Ceramic", .012)
    box("Recessed central avionics access", (-.38, 0, .237), (.43, .22, .021), "EN_Recess", .012)
    for i in range(5):
        box("Central avionics service ribs %d" % i, (-.53 + i * .071, 0, .252),
            (.026, .17, .022), "EN_Titanium", .004)
    weapon_and_sensor(1.20)


def bake_export(name):
    bpy.context.view_layer.update()
    # Save editable individual parts and modifiers before evaluated export.
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / (name + ".blend")), compress=True)
    bpy.ops.object.select_all(action="DESELECT")
    clones = []
    for obj in sorted(PARTS, key=lambda o: o.name):
        clone = obj.copy()
        clone.data = obj.data.copy()
        bpy.context.scene.collection.objects.link(clone)
        clone.select_set(True)
        clones.append(clone)
    bpy.context.view_layer.objects.active = clones[0]
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = "SM_" + name + "Candidate"
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    # Non-overlapping smart-projected islands, suitable for texture authoring.
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=.014)
    bpy.ops.object.mode_set(mode="OBJECT")
    mesh = obj.data
    mesh.calc_loop_triangles()
    uv = mesh.uv_layers.active
    assert uv is not None
    vertices = [obj.matrix_world @ v.co for v in mesh.vertices]
    low = [min(v[i] for v in vertices) for i in range(3)]
    high = [max(v[i] for v in vertices) for i in range(3)]
    # Pivot at the bounds center, explicitly reflected in every exported vertex.
    center = Vector([(low[i] + high[i]) * .5 for i in range(3)])
    for v in mesh.vertices:
        v.co -= center
    for original in PARTS:
        original.location -= center
    vertices = [obj.matrix_world @ v.co for v in mesh.vertices]
    extent = max((high[i] - low[i]) * .5 for i in range(3))
    normal_matrix = obj.matrix_world.to_3x3().inverted().transposed()
    normal_values, uv_values, faces = [], [], []
    assert 8000 <= len(mesh.loop_triangles) <= 20000, "Candidate triangle budget exceeded"
    area_min = min(t.area for t in mesh.loop_triangles)
    assert area_min > 1e-12, (name, area_min)
    for t in mesh.loop_triangles:
        corners = []
        for idx in t.loops:
            n = (normal_matrix @ mesh.corner_normals[idx].vector).normalized()
            u = uv.data[idx].uv
            assert all(math.isfinite(x) for x in (*n, *u)) and abs(n.length - 1) < 1e-5
            normal_values.append(tuple(n))
            uv_values.append(tuple(u))
            corners.append((mesh.loops[idx].vertex_index + 1, len(uv_values), len(normal_values)))
        faces.append((t.material_index, corners))
    def number(x):return "%.7f" % (0 if abs(x) < .00000005 else x)
    lines = ["# Original SpaceSurvival enemy candidate; cm; +X forward; +Z up", "mtllib EnemyPalette.mtl", "o " + obj.name]
    lines += ["v " + " ".join(number(x * 100) for x in v) for v in vertices]
    lines += ["vt " + " ".join(number(x) for x in v) for v in uv_values]
    lines += ["vn " + " ".join(number(x) for x in v) for v in normal_values]
    for matid, mat in enumerate(mesh.materials):
        lines.append("usemtl " + mat.name)
        lines += ["f " + " ".join("%d/%d/%d" % c for c in corners) for idx, corners in faces if idx == matid]
    (OUT / (name + ".obj")).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    bpy.ops.export_scene.gltf(filepath=str(OUT / (name + ".glb")), export_format="GLB",
        use_selection=True, export_apply=True, export_yup=True, export_normals=True,
        export_materials="EXPORT", export_animations=False)
    matlist = [mat.name for mat in mesh.materials]
    assert len(matlist) == 4
    record = {"name": name, "parts": len(PARTS), "triangles": len(mesh.loop_triangles), "vertices": len(vertices),
              "materials": matlist, "uv_layers": len(mesh.uv_layers), "min_triangle_area_m2": area_min,
              "bounds_cm": [[round(min(v[i] for v in vertices) * 100, 5) for i in range(3)],
                            [round(max(v[i] for v in vertices) * 100, 5) for i in range(3)]],
              "max_box_extent_cm": extent * 100,
              "runtime_uniform_scale_at_radius150": 1.5 / extent,
              "farthest_vertex_at_runtime_radius150_cm": max(v.length for v in vertices) * 150 / extent,
              "source_center_adjustment_cm": [x * 100 for x in center],
              "obj_sha256": sha(OUT / (name + ".obj")), "glb_sha256": sha(OUT / (name + ".glb"))}
    bpy.data.objects.remove(obj, do_unlink=True)
    # Editable saved source and exports now share exactly the same centered pivot.
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / (name + ".blend")), compress=True)
    return record


def studio(name):
    bpy.ops.wm.open_mainfile(filepath=str(OUT / (name + ".blend")))
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 8
    scene.render.resolution_x, scene.render.resolution_y = 1440, 1050
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX"
    scene.world = bpy.data.worlds.new("Preview studio environment")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (.09, .115, .16, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = .35
    for label, position, energy, size, color in [
        ("Key softbox", (3, -4, 6), 1200, 4, (1, .88, .72)),
        ("Rim softbox", (-3, 3, 4), 1600, 3, (.64, .79, 1)),
        ("Forward fill", (4, 3, 1.5), 500, 3, (.85, .91, 1)),
        ("Top strip", (-.5, 0, 5), 700, 2.5, (1, 1, 1)),
    ]:
        data = bpy.data.lights.new(label, "AREA")
        data.energy, data.shape, data.size, data.size_y, data.color = energy, "RECTANGLE", size, size * .45, color
        obj = bpy.data.objects.new(label, data)
        scene.collection.objects.link(obj)
        obj.location = position
        obj.rotation_euler = (-obj.location).to_track_quat("-Z", "Y").to_euler()
    data = bpy.data.cameras.new("Candidate review camera")
    camera = bpy.data.objects.new("Candidate review camera", data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    data.type = "ORTHO"
    base_scale = 4.3 if name == "Flanker" else 3.6
    data.ortho_scale = base_scale
    views = [("ForwardQuarter", (4.4, -5.3, 4.3)),
             ("RearQuarter", (-4.8, -5.4, 3.0)),
             ("TopSilhouette", (.01, 0, 8))]
    output = []
    for label, position in views:
        data.ortho_scale = max(base_scale, 4.5) if label == "TopSilhouette" else base_scale
        camera.location = position
        camera.rotation_euler = (-camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(OUT / (name + "-" + label + ".png"))
        bpy.ops.render.render(write_still=True)
        output.append({"file": Path(scene.render.filepath).name, "sha256": sha(scene.render.filepath)})
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    protected_paths = [ROOT / "ContentSource/Meshes" / (n + ".obj") for n in ("SM_Pursuer", "SM_Flanker")]
    protected_paths += [ROOT / "Content/SpaceSurvival/Meshes" / (n + ".uasset") for n in ("SM_Pursuer", "SM_Flanker")]
    protected_paths += [ROOT / "ContentSource/GenerateGeometry.py", ROOT / "model-rigged.glb"]
    protected = {str(p.relative_to(ROOT)): sha(p) for p in protected_paths}
    if args.render:
        outputs = [entry for name in ("Pursuer", "Flanker") for entry in studio(name)]
        record = {"status": "BLENDER_STUDIO_RENDERS_NOT_UNREAL_OR_OWNER_ACCEPTANCE", "renderer": "Cycles CPU / 8 threads / 32 samples",
                  "blender": bpy.app.version_string, "generator_sha256": sha(__file__), "images": outputs, "protected_sha256": protected}
        (OUT / "RenderReport.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    else:
        records = []
        for name, generate in [("Pursuer", build_pursuer), ("Flanker", build_flanker)]:
            reset()
            generate()
            records.append(bake_export(name))
        palette = []
        for mat in MATS.values():
            node = mat.node_tree.nodes["Principled BSDF"]
            color = node.inputs["Base Color"].default_value
            palette += ["newmtl " + mat.name, "Kd " + " ".join(str(v) for v in color[:3]),
                        "Pm " + str(node.inputs["Metallic"].default_value),
                        "Pr " + str(node.inputs["Roughness"].default_value),
                        "Ke " + " ".join(str(v * node.inputs["Emission Strength"].default_value) for v in color[:3]), ""]
        (OUT / "EnemyPalette.mtl").write_text("\n".join(palette), encoding="utf-8", newline="\n")
        record = {"status": "SEPARATE_ORIGINAL_SOURCE_CANDIDATES_NOT_ADOPTED", "blender": bpy.app.version_string,
                  "generator_sha256": sha(__file__), "coordinate_system": "OBJ centimetres +X forward +Z up; GLB metres with glTF axis transport",
                  "source_origin": "Original deterministic geometry authored for SpaceSurvival in this generator; no downloaded model, image or texture source.",
                  "assets": records,
                  "materials": [{"name": mat.name, "base_color": list(mat.diffuse_color),
                      "metallic": mat.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value,
                      "roughness": mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value,
                      "emission": mat.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value}
                      for mat in MATS.values()],
                  "protected_sha256": protected,
                  "collision": "No collision mesh or physics change. Existing runtime uses a separate Radius150 sphere and max-box-extent visual scaling; candidate fit is measured above.",
                  "limits": ["Candidate files only, no Unreal import or production reference change.",
                             "Four PBR materials with no texture dependency; needs faithful Unreal materials and game lighting review.",
                             "Studio appearance, runtime LODs, shader cost and gameplay silhouette acceptance remain separate checks.",
                             "Owner rejected prior graphics; these candidates are not owner art acceptance."]}
        (OUT / "SourceReport.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
        print("ENEMY_CANDIDATES_SOURCE", json.dumps(records))
    for path, digest in protected.items():
        assert sha(ROOT / path) == digest, path


if __name__ == "__main__":
    main()
