"""Locally authored modular RIFT SALVAGE prop, informed by owner crane refs.

This is procedural Blender geometry, not a claimed AI-generated reconstruction.
Named articulated parts/pivots are preparation only; there is no gameplay logic.
"""
import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
from finish_cabinets import material,cube,cylinder,tube,panel,front_panel,configure_render,OUT

NAME="RiftSalvage"
GROUPS={}


def group_since(before,name,pivot):
    objects=[o for o in bpy.context.scene.objects if o not in before and o.type in {"MESH","CURVE"}]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects: obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.join()
    obj=bpy.context.object
    obj.name=name
    bpy.context.scene.cursor.location=pivot
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    GROUPS[name]=obj
    return obj


def main():
    if (OUT.parent / "FROZEN_MANIFEST.json").exists():
        raise RuntimeError("Frozen1 is preserved; author a new version instead")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    graphite=material("Rift_Graphite","Graphite",metallic=.7,roughness=.46)
    metal=material("Rift_Titanium","Titanium",metallic=.8,roughness=.30)
    brass=material("Rift_WornBrass","Brass",metallic=.72,roughness=.47)
    violet=material("Rift_VioletPaint","VioletMetal",metallic=.40,roughness=.44)
    black=material("Rift_Rubber",color=(.014,.018,.021,1),metallic=0,roughness=.72)
    lamp=material("Rift_VioletLight",color=(.30,.04,.60,1),metallic=.0,roughness=.25,emission=2.5)
    amber=material("Rift_AmberLight",color=(.9,.32,.04,1),metallic=0,roughness=.3,emission=1.5)
    glass=material("Rift_Glass",color=(.045,.055,.062,1),metallic=.1,roughness=.04)
    shader=glass.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Transmission Weight"].default_value=0
    shader.inputs["Alpha"].default_value=.035
    shader.inputs["IOR"].default_value=1.45
    title=material("Rift_Title","RiftSalvage_Title",metallic=.05,roughness=.4,emission=.45)
    status=material("Rift_Status","RiftSalvage_Status",metallic=0,roughness=.3,emission=.7)
    controls=material("Rift_ControlLegend","RiftSalvage_Controls",metallic=.2,roughness=.45)
    hatch=material("Rift_HatchLegend","RiftSalvage_Hatch",metallic=.2,roughness=.5)
    side=material("Rift_SideGraphic","RiftSalvage_Side",metallic=.15,roughness=.55)
    before=set(bpy.context.scene.objects)
    # Grounded structural frame, closed back and physically recessed prize return.
    cube("BasePlinth",(0,0,.07),(1.16,.98,.14),graphite,.035)
    cube("RearCabinet",(0,.37,.46),(1.04,.14,.67),graphite,.025)
    for sign in (-1,1):
        cube("LowerSide",(sign*.51,0,.46),(.12,.87,.69),graphite,.018)
        for y in (-.40,.40):
            cube("Foot",(sign*.46,y,.045),(.21,.24,.09),black,.02)
            cube("ChamberPillar",(sign*.50,y,1.285),(.065,.075,.99),graphite,.012)
        cube("InnerRim",(sign*.465,0,.845),(.04,.81,.045),brass,.005)
    cube("CabinetLeftFront",(-.29,-.408,.43),(.46,.05,.58),graphite,.015)
    cube("CabinetRightFront",(.462,-.408,.43),(.11,.05,.58),graphite,.012)
    cube("CabinetFrontTop",(.20,-.408,.645),(.44,.05,.15),graphite,.012)
    cube("CabinetFrontBottom",(.20,-.408,.15),(.44,.06,.12),graphite,.012)
    cube("PrizeReturnFloor",(.19,-.205,.227),(.39,.45,.036),metal,.008)
    cube("PrizeReturnBack",(.19,.025,.371),(.39,.02,.29),black,.003)
    for x in (-.014,.394): cube("PrizeReturnSide",(x,-.20,.36),(.022,.45,.27),graphite,.004)
    cube("PrizeShelf",(0,0,.83),(1.00,.86,.065),graphite,.015)
    cube("ChamberRear",(0,.412,1.29),(.98,.035,.88),metal,.01)
    cube("ChamberCeiling",(0,0,1.766),(1.09,.91,.10),graphite,.025)
    cube("MarqueeHousing",(0,-.04,1.956),(1.16,.94,.29),graphite,.03)
    front_panel("Marquee",.478,1.851,2.054,0,-.519,title,brass)
    cube("ControlConsole",(0,-.414,.759),(1.075,.416,.13),graphite,.027)
    panel("ControlInstruction",[(-.34,-.535,.753),(.34,-.535,.753),(.34,-.535,.797),(-.34,-.535,.797)],controls)
    panel("StatusDisplay",[(-.46,-.598,.838),(-.13,-.598,.838),(-.13,-.434,.838),(-.46,-.434,.838)],status)
    front_panel("ReturnLegend",.168,.557,.644,0,-.445,hatch)
    for sign in (-1,1):
        x=sign*.573
        panel("SideGraphic",[(x,-.29,.34),(x,.31,.34),(x,.31,.71),(x,-.29,.71)],side)
        for y in (-.37,.36):
            tube("PurpleFrameInlay",[(sign*.54,y,.9),(sign*.54,y,1.68)],.006,lamp)
    # Fasteners and ventilation remain geometry at player viewing range.
    for x in (-.505,.505):
        for z in (.19,.62,1.0,1.4,1.72,1.87,2.046):
            bolt=cylinder("FrontHexBolt",(x,-.449 if z<1.80 else -.520,z),.012,.008,metal,6)
            bolt.rotation_euler.x=math.pi/2
    for z in (.29,.335,.38,.425,.47):
        cube("VentSlot",(-.295,-.443,z),(.23,.015,.014),black,.004)
    for x in (-.38,.38):
        cube("MarqueeRunningLight",(x,-.519,2.082),(.16,.019,.016),amber,.005)
    for x in (-.345,.345):
        cube("GantryRail",(x,0,1.699),(.035,.76,.038),metal,.007)
    group_since(before,"SM_RiftSalvage_Frame",(0,0,0))
    # Individual glass panels preserve a hollow chamber and remain replaceable.
    for name,loc,dims in [
        ("GlassFront",(0,-.394,1.297),(.934,.008,.875)),
        ("GlassLeft",(-.494,0,1.297),(.008,.737,.875)),
        ("GlassRight",(.494,0,1.297),(.008,.737,.875)),
    ]:
        before=set(bpy.context.scene.objects)
        cube(name,loc,dims,glass,.002)
        group_since(before,"SM_RiftSalvage_"+name,loc)
    before=set(bpy.context.scene.objects)
    cube("GantryBridge",(0,.05,1.665),(.82,.10,.070),graphite,.012)
    for x in (-.34,.34):
        cylinder("GantryWheel",(x,.05,1.681),.046,.06,metal)
    group_since(before,"SM_RiftSalvage_GantryY",(0,.05,1.665))
    before=set(bpy.context.scene.objects)
    cube("CarriageMotor",(.07,.05,1.595),(.18,.16,.095),violet,.016)
    cylinder("HoistSpool",(.07,.05,1.538),.059,.047,metal)
    group_since(before,"SM_RiftSalvage_CarriageX",(.07,.05,1.595))
    before=set(bpy.context.scene.objects)
    cylinder("HoistRod",(.07,.05,1.424),.015,.18,metal)
    coils=[]
    for i in range(161):
        a=i/160*math.tau*13
        coils.append((.07+.030*math.cos(a),.05+.030*math.sin(a),1.34+i/160*.19))
    tube("HoistSpiralCable",coils,.0045,black)
    group_since(before,"SM_RiftSalvage_HoistCable",(.07,.05,1.535))
    before=set(bpy.context.scene.objects)
    cylinder("ClawMotorHousing",(.07,.05,1.295),.072,.118,metal)
    for z in (1.25,1.285,1.335): cylinder("ClawCollar",(.07,.05,z),.078,.013,brass)
    cylinder("ClawVioletIndicator",(.07,.05,1.302),.074,.012,lamp)
    group_since(before,"SM_RiftSalvage_ClawBodyZ",(.07,.05,1.35))
    for finger in range(3):
        before=set(bpy.context.scene.objects)
        angle=finger*math.tau/3
        radial=[(.057,1.265),(.106,1.220),(.149,1.126),(.140,1.045),(.102,1.009),(.106,1.06),(.111,1.124),(.078,1.2)]
        vertices=[]
        for d in (-.012,.012):
            for r,z in radial:
                vertices.append((.07+r*math.cos(angle)-d*math.sin(angle),.05+r*math.sin(angle)+d*math.cos(angle),z))
        n=len(radial)
        faces=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        mesh=bpy.data.meshes.new("ArticulatedClawFinger")
        mesh.from_pydata(vertices,[],faces)
        mesh.update()
        obj=bpy.data.objects.new("ClawFinger",mesh)
        bpy.context.collection.objects.link(obj)
        obj.data.materials.append(metal)
        pivot=(.07+.057*math.cos(angle),.05+.057*math.sin(angle),1.265)
        group_since(before,f"SM_RiftSalvage_ClawFinger{finger+1}",pivot)
    # Static independent prizes. Nothing is physically simulated or awarded.
    rng=random.Random(10062026)
    crystal=material("Rift_RelicCrystal",color=(.19,.035,.37,1),metallic=.36,roughness=.20,emission=.16)
    teal=material("Rift_RelicTeal",color=(.025,.28,.24,1),metallic=.5,roughness=.24,emission=.07)
    for i in range(13):
        before=set(bpy.context.scene.objects)
        loc=(rng.uniform(-.37,.37),rng.uniform(-.27,.29),.91)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=rng.uniform(.058,.10),location=loc)
        obj=bpy.context.object
        obj.name=f"RecoverableRelic{i+1:02}"
        obj.scale=(.75,.8,rng.uniform(1.25,1.85))
        obj.rotation_euler=(rng.uniform(-.2,.2),rng.uniform(-.3,.3),rng.uniform(0,3))
        obj.data.materials.append(crystal if i%3 else teal)
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        minimum=min((obj.matrix_world@v.co).z for v in obj.data.vertices)
        obj.location.z += .865-minimum
        group_since(before,f"SM_RiftSalvage_Prize{i+1:02}",obj.location.copy())
    before=set(bpy.context.scene.objects)
    cylinder("JoystickBase",(.11,-.51,.846),.055,.016,black)
    cylinder("JoystickStem",(.11,-.51,.888),.012,.078,metal)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=.036,location=(.11,-.51,.936))
    bpy.context.object.data.materials.append(violet)
    group_since(before,"SM_RiftSalvage_Joystick",(.11,-.51,.846))
    before=set(bpy.context.scene.objects)
    cylinder("RecoverButtonBezel",(.32,-.51,.844),.05,.017,brass)
    cylinder("RecoverButton",(.32,-.51,.858),.037,.022,lamp)
    group_since(before,"SM_RiftSalvage_RecoverButton",(.32,-.51,.85))
    # UVs only on untextured geometry; authored labels retain deliberate UVs.
    for obj in GROUPS.values():
        if not obj.data.uv_layers:
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            bpy.context.view_layer.objects.active=obj
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.cube_project(cube_size=.25)
            bpy.ops.object.mode_set(mode="OBJECT")
    target=OUT/NAME
    target.mkdir(parents=True,exist_ok=True)
    bpy.context.scene.unit_settings.system="METRIC"
    for image in bpy.data.images:
        if image.source=="FILE": image.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(target/(NAME+".blend")))
    bpy.ops.object.select_all(action="DESELECT")
    for obj in GROUPS.values(): obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(target/(NAME+".glb")),export_format="GLB",use_selection=True)
    bpy.ops.export_scene.fbx(filepath=str(target/(NAME+"_parts.fbx")),use_selection=True,object_types={"MESH"},axis_forward="-Z",axis_up="Y",path_mode="COPY",embed_textures=True)
    parts=[]
    for key,obj in GROUPS.items():
        parts.append({"name":key,"pivot_m":list(obj.location),"triangles":sum(len(p.vertices)-2 for p in obj.data.polygons),"materials":[m.name for m in obj.data.materials]})
    used={m.name:m for obj in GROUPS.values() for m in obj.data.materials}
    materials=[]
    for key,mat in sorted(used.items()):
        node=mat.node_tree.nodes.get("Principled BSDF")
        images=[n.image for n in mat.node_tree.nodes if n.type=="TEX_IMAGE" and n.image]
        materials.append({"slot":key,"base_color_texture":str(Path(bpy.path.abspath(images[0].filepath))) if images else None,"base_color_linear":list(node.inputs["Base Color"].default_value),"metallic":node.inputs["Metallic"].default_value,"roughness":node.inputs["Roughness"].default_value,"emission_strength":node.inputs["Emission Strength"].default_value,"emission_color_linear":list(node.inputs["Emission Color"].default_value),"emission_uses_base_texture":node.inputs["Emission Color"].is_linked,"alpha":.12 if key=="Rift_Glass" else 1.0,"transmission":.96 if key=="Rift_Glass" else 0,"blend_mode":"translucent thin glass" if key=="Rift_Glass" else "opaque"})
    all_vertices=[obj.matrix_world@v.co for obj in GROUPS.values() for v in obj.data.vertices]
    dimensions=[max(v[i] for v in all_vertices)-min(v[i] for v in all_vertices) for i in range(3)]
    report={"name":NAME,"geometry_provenance":"Local procedural Blender authoring informed by owner crane references; no AI mesh claim","dimensions_m":dimensions,"front_axis":"-Y in Blender","origin":"frame at ground center; moving parts have local mechanism pivots","parts":parts,"materials":materials,"triangles":sum(p["triangles"] for p in parts),"collision_recommendation":"single exterior cabinet box for decorative placement; future mechanical collision not implemented","status":"static decorative asset; no rewards, RNG, physics or gameplay"}
    report["bounds_m"]=[[min(v[i] for v in all_vertices) for i in range(3)],[max(v[i] for v in all_vertices) for i in range(3)]]
    report["fbx_parts"]=[]
    # Combined static opaque export and separately retained glass for native imports.
    bpy.ops.object.select_all(action="DESELECT")
    for name,obj in GROUPS.items():
        if "Glass" not in name: obj.select_set(True)
    bpy.context.view_layer.objects.active=GROUPS["SM_RiftSalvage_Frame"]
    bpy.ops.object.join()
    bpy.context.object.name="SM_RiftSalvage_StaticOpaque"
    obj=bpy.context.object
    vv=[obj.matrix_world@v.co for v in obj.data.vertices]
    bb=[[min(v[i] for v in vv) for i in range(3)],[max(v[i] for v in vv) for i in range(3)]]
    report["fbx_parts"].append({"name":"Static","fbx_path":str(target/(NAME+"_static.fbx")),"bounds_m":bb,"dimensions_m":[bb[1][i]-bb[0][i] for i in range(3)]})
    bpy.ops.export_scene.fbx(filepath=str(target/(NAME+"_static.fbx")),use_selection=True,object_types={"MESH"},axis_forward="-Z",axis_up="Y",path_mode="COPY",embed_textures=True)
    bpy.ops.object.select_all(action="DESELECT")
    for name,obj in GROUPS.items():
        if "Glass" in name: obj.select_set(True)
    bpy.context.view_layer.objects.active=GROUPS["SM_RiftSalvage_GlassFront"]
    bpy.ops.object.join()
    bpy.context.object.name="SM_RiftSalvage_Glass"
    bpy.context.scene.cursor.location=(0,0,0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    obj=bpy.context.object
    vv=[obj.matrix_world@v.co for v in obj.data.vertices]
    bb=[[min(v[i] for v in vv) for i in range(3)],[max(v[i] for v in vv) for i in range(3)]]
    report["fbx_parts"].append({"name":"Glass","fbx_path":str(target/(NAME+"_glass.fbx")),"bounds_m":bb,"dimensions_m":[bb[1][i]-bb[0][i] for i in range(3)]})
    bpy.ops.export_scene.fbx(filepath=str(target/(NAME+"_glass.fbx")),use_selection=True,object_types={"MESH"},axis_forward="-Z",axis_up="Y",path_mode="COPY",embed_textures=True)
    (target/"asset.json").write_text(json.dumps(report,indent=2))
    configure_render(bpy.context.scene,NAME,2.11)
    print(json.dumps({"name":NAME,"triangles":report["triangles"],"parts":len(parts),"dimensions":dimensions}))


if __name__=="__main__": main()
