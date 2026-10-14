"""Finish local Hunyuan chassis with authored UV materials and clean display parts.

Run only in an isolated Blender --background --factory-startup process.
All final props are static decorative assets; no arcade gameplay is implemented.
"""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / ".agent/local/ArcadeGeneration"
OUT = WORK / "final"
TEXTURES = OUT / "textures"


def material(name, texture=None, color=(.07, .08, .09, 1), metallic=.55, roughness=.42, emission=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    if texture:
        node = mat.node_tree.nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(str(TEXTURES / (texture + ".png")), check_existing=True)
        mat.node_tree.links.new(node.outputs["Color"], shader.inputs["Base Color"])
        if emission:
            mat.node_tree.links.new(node.outputs["Color"], shader.inputs["Emission Color"])
    elif emission:
        shader.inputs["Emission Color"].default_value = color
    shader.inputs["Emission Strength"].default_value = emission
    return mat


def cube(name, position, dimensions, mat, bevel=.015):
    bpy.ops.mesh.primitive_cube_add(size=1, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("Machined edge", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def tube(name, points, radius, mat):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, coord in zip(spline.points, points):
        point.co = (*coord, 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def panel(name, points, mat, frame=None):
    # Lower-left, lower-right, upper-right, upper-left as viewed from the front.
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(points, [], [(0, 1, 2, 3)])
    mesh.update()
    mesh.uv_layers.new(name="UVMap")
    for loop, uv in zip(mesh.uv_layers.active.data, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop.uv = uv
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(mat)
    if frame:
        tube(name + "_frame", points + [points[0]], .018, frame)
    return obj


def front_panel(name, x, z0, z1, slope, offset, mat, frame=None):
    return panel(name, [(-x, slope*z0+offset, z0), (x, slope*z0+offset, z0), (x, slope*z1+offset, z1), (-x, slope*z1+offset, z1)], mat, frame)


def cylinder(name, position, radius, depth, mat, vertices=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new("Rounded lip", "BEVEL")
    bevel.width = min(.008, depth*.2)
    bevel.segments = 2
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def side_skin(name, x, profile, mat):
    thickness = .034
    vertices = [(x+offset,y,z) for offset in (-thickness/2,thickness/2) for y,z in profile]
    count = len(profile)
    faces = [tuple(range(count-1,-1,-1)),tuple(range(count,count*2))]
    faces += [(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    obj = bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bevel = obj.modifiers.new("Panel edge chamfer","BEVEL")
    bevel.width=.008
    bevel.segments=3
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    obj.select_set(False)
    return obj


def configure_render(scene, name, height):
    if (WORK / "FROZEN_MANIFEST.json").exists():
        raise RuntimeError("Frozen1 is preserved; author a new version instead")
    preview_points = [obj.matrix_world @ Vector(c) for obj in scene.objects if obj.type == "MESH" for c in obj.bound_box]
    preview_low=Vector([min(p[i] for p in preview_points) for i in range(3)])
    preview_high=Vector([max(p[i] for p in preview_points) for i in range(3)])
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 16
    scene.cycles.use_denoising = True
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 8
    scene.render.resolution_x = 900
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.world = bpy.data.worlds.new("Local studio")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs[0].default_value = (.11, .13, .16, 1)
    scene.world.node_tree.nodes["Background"].inputs[1].default_value = .45
    floor = material("Studio floor", color=(.06, .07, .085, 1), metallic=0, roughness=.65)
    cube("StudioGround", (0, 0, -.045), (200, 200, .08), floor, bevel=0)
    for label, location, power, size, color in [
        ("Key", (-3, -4, 5), 650, 4, (1, .9, .78)),
        ("Fill", (3, -1, 3), 430, 3, (.70, .80, 1)),
        ("Rim", (1, 3, 4), 750, 2, (.75, .80, 1)),
    ]:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = label
        light.data.energy = power
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        light.rotation_euler = (Vector((0, 0, height*.5))-light.location).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    scene.camera = camera
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = height * 1.30
    target = (preview_low+preview_high)*.5
    for label, location in (("front", (0, -5, height*1.05)), ("quarter", (3, -5, height*1.40)), ("rear", (-3, 5, height*1.25))):
        camera.location = location
        camera.rotation_euler = (target-camera.location).to_track_quat("-Z", "Y").to_euler()
        rot=camera.rotation_euler.to_matrix().transposed()
        projected=[rot@(point-target) for point in preview_points]
        spans=[max(p[i] for p in projected)-min(p[i] for p in projected) for i in (0,1)]
        camera.data.ortho_scale=max(spans[1],spans[0]/.9)*1.18
        scene.render.filepath = str(OUT / name / f"{name}_{label}.png")
        bpy.ops.render.render(write_still=True)


def finish(name, height):
    if (WORK / "FROZEN_MANIFEST.json").exists():
        raise RuntimeError("Frozen1 is preserved; author a new version instead")
    delivery_name = "CreditExchange" if name == "TokensKiosk" else name
    bpy.ops.wm.open_mainfile(filepath=str(WORK / "raw" / name / f"{name}_raw.blend"))
    for obj in list(bpy.context.scene.objects):
        if obj.type != "MESH":
            bpy.data.objects.remove(obj, do_unlink=True)
    body = next(obj for obj in bpy.context.scene.objects if obj.type == "MESH")
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    body.name = "SM_" + name + "_HunyuanChassis"
    before = sum(len(p.vertices)-2 for p in body.data.polygons)
    graphite = material("M_Graphite", "Graphite")
    accent = material("M_" + name + "_Paint", "GreenMetal" if name == "AsteroidArena" else "VioletMetal" if name == "GalaxyPinball" else "Titanium", metallic=.45)
    metal = material("M_Titanium", "Titanium", metallic=.72, roughness=.32)
    brass = material("M_Brass", "Brass", metallic=.72, roughness=.34)
    display = material("M_" + name + "_Display", name + "_Screen", metallic=.08, roughness=.24, emission=.8)
    title = material("M_" + name + "_Marquee", name + "_Title", metallic=.1, roughness=.32, emission=.38)
    purple = material("M_VioletLamp", color=(.42, .065, .8, 1), metallic=.2, roughness=.28, emission=2.2)
    amber = material("M_AmberLamp", color=(1, .29, .035, 1), metallic=.2, roughness=.26, emission=2.0)
    if name != "TokensKiosk":
        for vert in body.data.vertices:
            if vert.co.z > .940:
                vert.co.z = .940
    if name == "AsteroidArena":
        for vert in body.data.vertices:
            x,y,z = vert.co
            if abs(x)<.438 and -.557<y<-.165 and -.225<z<.13:
                vert.co.z = min(z,.31*y-.022)
    if name == "GalaxyPinball":
        # The image model embosses picture details. Replace its shallow field relief
        # with a planar deck; retain the original chassis and perimeter silhouette.
        for vert in body.data.vertices:
            x, y, z = vert.co
            field = .407*y + .085
            if abs(x) < .415 and -.59 < y < .09 and abs(z-field) < .10:
                vert.co.z = field - .015
    body.data.materials.clear()
    for mat in (graphite, accent, metal):
        body.data.materials.append(mat)
    decimate = body.modifiers.new("Game mesh budget", "DECIMATE")
    decimate.ratio = min(1, 22000 / before)
    bpy.ops.object.modifier_apply(modifier=decimate.name)
    for face in body.data.polygons:
        face.material_index = 0
        face.use_smooth = True
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.cube_project(cube_size=.45)
    bpy.ops.object.mode_set(mode="OBJECT")
    # Hard-surface skins follow the actual generated silhouette and hide soft relief.
    if name != "TokensKiosk":
        pinball = name == "GalaxyPinball"
        front_y = -.66 if pinball else -.568
        back_y = .66 if pinball else .572
        top_front = .03 if pinball else -.092
        profile = [(front_y,-.95),(back_y,-.95),(back_y,.945),(top_front,.945),(top_front,.63),(.11 if pinball else .04,.55),(-.12 if pinball else -.16,.08),(front_y,-.17)]
        for sign in (-1,1):
            x=sign*(.60 if pinball else .59)
            side_skin(name+"_MachinedSide",x,profile,graphite)
            tube(name+"_ContinuousPaintedTrim",[(x,front_y,-.87),(x,front_y,-.17),(x,profile[-2][0],.08),(x,profile[-3][0],.55),(x,top_front,.63),(x,top_front,.94)],.020,accent)
        cube(name+"_FrontLip",(0,front_y-.006,-.258),(1.12,.047,.147),accent,.012)
        cube(name+"_RearServicePanel",(0,back_y+.015,-.01),(1.14,.036,1.83),graphite,.015)
        cube(name+"_CanopyTop",(0,(back_y+top_front)/2,.954),(1.245,back_y-top_front,.035),accent,.012)
    if name == "AsteroidArena":
        front_panel(name + "_Title", .411, .681, .935, 0, -.096, title, graphite)
        front_panel(name + "_Screen", .400, .075, .563, .37, -.128, display, graphite)
        badge = material("M_AsteroidBadge", name + "_Badge", metallic=.35, roughness=.4)
        front_panel(name + "_Badge", .155, -.777, -.47, 0, -.501, badge)
        for x in (-.205, .205):
            tube("Front green inlay", [(x, -.49, -.76), (x, -.49, -.49)], .005, accent)
        panel("AsteroidControlDeck",[(-.446,-.548,-.178),(.446,-.548,-.178),(.446,-.13,-.048),(-.446,-.13,-.048)],accent,graphite)
        for x in (-.275,.045):
            y=-.35
            z=.31*y-.003
            cylinder("JoystickGaiter",(x,y,z),.062,.018,graphite)
            cylinder("JoystickShaft",(x,y,z+.039),.013,.071,metal)
            bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=.043,location=(x,y,z+.084))
            bpy.context.object.name="JoystickGrip"
            bpy.context.object.data.materials.append(accent)
            for face in bpy.context.object.data.polygons: face.use_smooth=True
        for x in (.243,.353):
            for y in (-.37,-.265):
                z=.31*y-.008
                cylinder("ArcadeButtonBezel",(x,y,z),.037,.014,graphite)
                cylinder("ArcadeButtonCap",(x,y,z+.012),.028,.018,accent)
    elif name == "GalaxyPinball":
        front_panel(name + "_Title", .416, .68, .927, 0, .020, title, graphite)
        front_panel(name + "_Screen", .398, .155, .558, .38, .002, display, graphite)
        field = material("M_PinballPlayfield", name + "_Playfield", metallic=.2, roughness=.26, emission=.25)
        panel("PinballPlayfield", [(-.407,-.585,-.153), (.407,-.585,-.153), (.407,.07,.119), (-.407,.07,.119)], field)
        rail = []
        for i in range(49):
            angle = math.tau * i / 48
            x = .384 * math.cos(angle)
            y = -.246 + .286 * math.sin(angle)
            rail.append((x, y, .407*y+.107))
        tube("PhysicalPinballRail", rail, .012, brass)
        for sign in (-1, 1):
            flipper = cube("PinballFlipper", (sign*.147, -.449, -.055), (.225,.066,.044), brass, .017)
            flipper.rotation_euler.z = sign * math.radians(17)
            for y in (-.08, -.26):
                z = .407*y+.13
                cylinder("PinballBumperBase", (sign*.22,y,z), .055,.032,brass)
                cylinder("PinballBumperCap", (sign*.22,y,z+.022), .040,.016,purple)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=.018, location=(.09,-.20,.024))
        bpy.context.object.name = "PinballSteelBall"
        bpy.context.object.data.materials.append(metal)
    else:
        front_panel(name + "_Title", .466, .65, .863, 0, -.291, title, graphite)
        front_panel(name + "_Screen", .429, .028, .543, -.265, -.200, display, graphite)
        status = material("M_TokenStatus", "TokensKiosk_Status", metallic=.05, roughness=.25, emission=.7)
        panel("TokenStatusDisplay", [(-.375,-.436,-.172),(-.064,-.436,-.172),(-.064,-.285,-.092),(-.375,-.285,-.092)],status,graphite)
        cube("TokenSlotLamp", (0,-.463,-.568),(.25,.018,.012),amber,.003)
        cube("TokenLowerInlay", (0,-.522,-.883),(.60,.014,.013),purple,.004)
    # Intentional restrained side decoration and rear maintenance detail.
    for sign in (-1, 1):
        x = sign * (.620 if name == "GalaxyPinball" else .610 if name == "AsteroidArena" else .636)
        for z in (-.63, -.50):
            tube(name + "_SideInlay", [(x,-.25,z),(x,.25,z+.22)], .006, accent if name != "TokensKiosk" else purple)
    back_y = max(v.co.y for v in body.data.vertices) + .009
    for z in (-.66, -.59, -.52, -.45):
        cube(name + "_RearVent", (0,back_y,z),(.49,.008,.019),graphite,.003)
    meshes = [obj for obj in bpy.context.scene.objects if obj.type in {"MESH", "CURVE"}]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.convert(target="MESH")
    scale = height / 1.9668
    minimum_z = min((obj.matrix_world @ vertex.co).z for obj in meshes for vertex in obj.data.vertices)
    for obj in meshes:
        for vertex in obj.data.vertices:
            co = obj.matrix_world @ vertex.co
            vertex.co = (co.x*scale*.87, co.y*scale*.85, (co.z-minimum_z)*scale)
        obj.matrix_world.identity()
    target = OUT / delivery_name
    target.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1
    for image in bpy.data.images:
        if image.source == "FILE":
            image.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(target / f"{delivery_name}.blend"))
    dimensions = [max(v.co[i] for obj in meshes for v in obj.data.vertices)-min(v.co[i] for obj in meshes for v in obj.data.vertices) for i in range(3)]
    material_manifest=[]
    used_materials=sorted({m.name:m for obj in meshes for m in obj.data.materials}.values(),key=lambda m:m.name)
    for mat in used_materials:
        shader=mat.node_tree.nodes.get("Principled BSDF")
        images=[n.image for n in mat.node_tree.nodes if n.type=="TEX_IMAGE" and n.image]
        material_manifest.append({"slot":mat.name,"base_color_texture":str(Path(bpy.path.abspath(images[0].filepath))) if images else None,"base_color_linear":list(shader.inputs["Base Color"].default_value),"metallic":shader.inputs["Metallic"].default_value,"roughness":shader.inputs["Roughness"].default_value,"emission_strength":shader.inputs["Emission Strength"].default_value,"emission_color_linear":list(shader.inputs["Emission Color"].default_value),"emission_uses_base_texture":bool(shader.inputs["Emission Color"].is_linked),"alpha":1.0})
    # The editable blend keeps separate parts; the delivery FBX is one static mesh.
    bpy.context.view_layer.objects.active=body
    bpy.ops.object.join()
    meshes=[bpy.context.object]
    meshes[0].name="SM_"+delivery_name
    bpy.ops.export_scene.gltf(filepath=str(target / f"{delivery_name}.glb"), export_format="GLB", use_selection=True, export_yup=True)
    bpy.ops.export_scene.fbx(filepath=str(target / f"{delivery_name}.fbx"), use_selection=True, object_types={"MESH"}, apply_unit_scale=True, axis_forward="-Z", axis_up="Y", path_mode="COPY", embed_textures=True)
    report = {"name": name, "raw_triangles": before, "final_triangles": sum(sum(len(p.vertices)-2 for p in obj.data.polygons) for obj in meshes), "parts": len(meshes), "height_m": height,"dimensions_m":dimensions,"materials":material_manifest,"collision_recommendation":"one box enclosing cabinet; no playable collision inside", "front_axis": "-Y in Blender", "origin": "center XY, ground Z", "geometry_provenance": "Local Hunyuan3D v2 chassis, decimated; authored planar displays, materials, exterior panel skins and controls", "texture_provenance": "Owner references rectified only onto separate display/title plates; procedural local metal/playfield textures", "status": "exported; render review pending"}
    report["name"]=delivery_name
    report["fbx_path"]=str(target/f"{delivery_name}.fbx")
    report["bounds_m"]=[[min(v.co[i] for obj in meshes for v in obj.data.vertices) for i in range(3)],[max(v.co[i] for obj in meshes for v in obj.data.vertices) for i in range(3)]]
    (target / "asset.json").write_text(json.dumps(report, indent=2))
    configure_render(bpy.context.scene, delivery_name, height)
    print(json.dumps(report))


if __name__ == "__main__":
    requested = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    for item, height in (("AsteroidArena",1.90),("GalaxyPinball",1.90),("TokensKiosk",1.75)):
        if not requested or item in requested:
            finish(item, height)
