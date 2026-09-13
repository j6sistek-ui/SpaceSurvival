"""Separate AcornShip surface/art candidate, authored in installed Blender.

Writes only AcornShipCandidate/*: editable ship-only .blend, ship-only .glb,
five purposeful source renders, and bounds/material/provenance measurements.
Original gameplay meshes and every character source/asset remain unchanged.
Acornaut is imported transiently for fit renders after the .blend/export save.
"""
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ContentSource/AcornShipCandidate"
PROFILE = [(-1.98,.19),(-1.80,.52),(-1.35,.83),(-.85,.925),(-.25,.89),(.40,.755),(1.0,.56),(1.55,.34),(1.95,.11),(2.1,.012)]
SHIP = []
MATERIALS = {}


def material(name, color, metal, rough, coat=.0, emission=0, transmission=0):
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    node = mat.node_tree.nodes.get("Principled BSDF")
    for key,value in {"Base Color": (*color,1), "Metallic":metal,"Roughness":rough,"Coat Weight":coat,"Coat Roughness":.17,"Transmission Weight":transmission,"IOR":1.45,"Emission Color":(*color,1),"Emission Strength":emission}.items():
        if key not in node.inputs:
            raise RuntimeError("Unsupported Principled input: "+key)
        node.inputs[key].default_value=value
    mat.diffuse_color=(*color,1)
    if metal>.4:
        noise=mat.node_tree.nodes.new("ShaderNodeTexNoise");noise.inputs["Scale"].default_value=550;noise.inputs["Detail"].default_value=2
        bump=mat.node_tree.nodes.new("ShaderNodeBump");bump.inputs["Strength"].default_value=.08;bump.inputs["Distance"].default_value=.00015
        mat.node_tree.links.new(noise.outputs["Fac"],bump.inputs["Height"]);mat.node_tree.links.new(bump.outputs["Normal"],node.inputs["Normal"])
    MATERIALS[name]=mat
    return mat


def mesh_object(name, vertices, faces, mat, smooth=True, bevel=0, solidify=0):
    data=bpy.data.meshes.new(name);data.from_pydata(vertices,[],faces);data.update()
    obj=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(obj);data.materials.append(mat)
    for polygon in data.polygons:polygon.use_smooth=smooth
    if solidify:
        mod=obj.modifiers.new("Physical panel thickness","SOLIDIFY");mod.thickness=solidify;mod.offset=-1
    if bevel:
        mod=obj.modifiers.new("Machined edge highlights","BEVEL");mod.width=bevel;mod.segments=3;mod.limit_method="ANGLE";mod.angle_limit=.30;mod.harden_normals=True
    if not smooth or bevel:
        mod=obj.modifiers.new("Face weighted corner normals","WEIGHTED_NORMAL");mod.keep_sharp=True;mod.weight=50
    SHIP.append(obj)
    return obj


def radius(x):
    for i in range(len(PROFILE)-1):
        if x<=PROFILE[i+1][0]:
            x0,r0=PROFILE[i];x1,r1=PROFILE[i+1]
            prior=PROFILE[max(0,i-1)];after=PROFILE[min(len(PROFILE)-1,i+2)]
            slope0=(r1-prior[1])/(x1-prior[0]);slope1=(after[1]-r0)/(after[0]-x0)
            t=max(0,min(1,(x-x0)/(x1-x0)))
            return (2*t**3-3*t*t+1)*r0+(t**3-2*t*t+t)*(x1-x0)*slope0+(-2*t**3+3*t*t)*r1+(t**3-t*t)*(x1-x0)*slope1
    return PROFILE[-1][1]


def loft(name, rings, mat, sides=64, zscale=1, center=(0,0,0), close=True):
    verts=[(x+center[0],r*math.cos(a*math.tau/sides)+center[1],r*math.sin(a*math.tau/sides)*zscale+center[2]) for x,r in rings for a in range(sides)]
    faces=[(row*sides+a,row*sides+(a+1)%sides,(row+1)*sides+(a+1)%sides,(row+1)*sides+a) for row in range(len(rings)-1) for a in range(sides)]
    if close:
        faces.extend([tuple(reversed(range(sides))),tuple(range((len(rings)-1)*sides,len(rings)*sides))])
    return mesh_object(name,verts,faces,mat,True)


def tube(name, points, width, mat, cyclic=False):
    data=bpy.data.curves.new(name,"CURVE");data.dimensions="3D";data.resolution_u=1;data.bevel_depth=width;data.bevel_resolution=3;data.resolution_u=2
    spline=data.splines.new("POLY");spline.points.add(len(points)-1)
    for point,co in zip(spline.points,points):point.co=(*co,1)
    spline.use_cyclic_u=cyclic
    obj=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(obj);data.materials.append(mat);SHIP.append(obj)
    return obj


def ring(name,x,r,width,mat,y=0,z=0,zscale=1):
    return tube(name,[(x,y+r*math.cos(i*math.tau/96),z+r*math.sin(i*math.tau/96)*zscale) for i in range(96)],width,mat,True)


def box(name,position,dimensions,mat,bevel=.012,rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1,location=position,rotation=rotation);obj=bpy.context.object;obj.name=name;obj.scale=dimensions
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons: polygon.use_smooth=True
    if bevel:
        mod=obj.modifiers.new("Machined corner radius","BEVEL");mod.width=bevel;mod.segments=6;mod.harden_normals=True
        mod=obj.modifiers.new("Weighted normals","WEIGHTED_NORMAL");mod.keep_sharp=True;mod.weight=50
    SHIP.append(obj);return obj


def cut_cockpit(obj,cutter):
    bpy.context.view_layer.objects.active=obj;obj.select_set(True)
    mod=obj.modifiers.new("Open pilot well","BOOLEAN");mod.operation="DIFFERENCE";mod.solver="EXACT";mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name);obj.select_set(False)


def shell_panel(name,low,high,a0,a1,mat,cutter=None,offset=.012):
    rows,cols=28,8;verts=[]
    for i in range(rows+1):
        x=low+(high-low)*i/rows
        for j in range(cols+1):
            theta=a0+(a1-a0)*j/cols;r=radius(x)+offset
            verts.append((x,r*math.cos(theta),r*math.sin(theta)*.68))
    faces=[(i*(cols+1)+j,i*(cols+1)+j+1,(i+1)*(cols+1)+j+1,(i+1)*(cols+1)+j) for i in range(rows) for j in range(cols)]
    obj=mesh_object(name,verts,faces,mat,True,bevel=.003,solidify=.016)
    if cutter:
        bpy.context.view_layer.objects.active=obj
        for mod in list(obj.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
        cut_cockpit(obj,cutter)
    return obj


def extruded_outline(name,polygon,top,bottom,mat,bevel=.02):
    n=len(polygon);verts=[(x,y,z) for z in (bottom,top) for x,y in polygon]
    area=sum(polygon[i][0]*polygon[(i+1)%n][1]-polygon[(i+1)%n][0]*polygon[i][1] for i in range(n))
    if area<0:polygon=list(reversed(polygon));verts=[(x,y,z) for z in (bottom,top) for x,y in polygon]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh_object(name,verts,faces,mat,False,bevel)


def make_ship():
    ceramic=material("AC01_WarmCeramic",(.70,.62,.46),.16,.25,.35)
    pearl=material("AC01_IvoryPanels",(.87,.86,.78),.06,.24,.25)
    bronze=material("AC01_BurnishedBronze",(.34,.145,.045),.82,.27,.18)
    gold=material("AC01_ChampagneEdges",(.68,.39,.13),.85,.21,.18)
    dark=material("AC01_GraphiteStructure",(.018,.027,.032),.72,.28,.15)
    rubber=material("AC01_CockpitPadding",(.009,.014,.016),.0,.55)
    metal=material("AC01_MachinedTitanium",(.23,.27,.30),.92,.22)
    cyan=material("AC01_IonAndNav",(.015,.40,.58),.18,.2,emission=3.5)
    glass=material("AC01_Windscreen",(.38,.67,.72),0,.065,coat=.3,transmission=.92)
    # The underlying smooth acorn shell has a real cockpit cutout.
    rings=[(-1.98+(2.1+1.98)*i/100,radius(-1.98+(2.1+1.98)*i/100)) for i in range(101)]
    hull=loft("Pressure hull understructure",rings,dark,96,.68)
    bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=1,depth=1.7,location=(-.15,0,.98));cutter=bpy.context.object;cutter.name="CockpitBooleanTool";cutter.scale=(.64,.40,1)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    cut_cockpit(hull,cutter)
    # Twelve tapered seed shell plates reveal graphite seams rather than painted lines.
    for index in range(12):
        a0=index*math.tau/12+.010;a1=(index+1)*math.tau/12-.010
        chosen=pearl if index in (1,2,3,4,7,8,9,10) else ceramic
        shell_panel("Seed shell plate %02d"%index,-.90,2.076,a0,a1,chosen,cutter)
    bpy.data.objects.remove(cutter,do_unlink=True)
    # Layered aft cap tiles form the acorn's defining cupule.
    for row,(low,high) in enumerate(((-1.88,-1.49),(-1.57,-1.18),(-1.26,-.88))):
        for index in range(14):
            center=(index+.5*(row%2))*math.tau/14
            verts=[];rows,cols=5,8
            for i in range(rows+1):
                for j in range(cols+1):
                    u=j/cols;v=i/rows;theta=center+(u-.5)*(math.tau/14-.026)
                    x=low+(high-low)*v+.045*math.sin(u*math.pi)*v
                    r=radius(x)+.026+.016*(2-row)
                    verts.append((x,r*math.cos(theta),r*math.sin(theta)*.68))
            faces=[(i*(cols+1)+j,i*(cols+1)+j+1,(i+1)*(cols+1)+j+1,(i+1)*(cols+1)+j) for i in range(rows) for j in range(cols)]
            mesh_object("Cap scale %d %02d"%(row,index),verts,faces,bronze,True,.004,.018)
            edge=[verts[rows*(cols+1)+j] for j in range(cols+1)]
            tube("Cap engraved lip %d %02d"%(row,index),edge,.0045,gold)
    ring("Cap compression collar",-.884,radius(-.884)+.023,.011,gold,zscale=.68)
    ring("Aft cap service seal",-1.902,radius(-1.902)+.016,.009,metal,zscale=.68)
    # Swept surfaces retain the original wingtip and collision silhouette.
    for sign in (-1,1):
        outline=[(-2.035,sign*1.08),(-1.07,sign*1.435),(.03,sign*.725),(-1.55,sign*.625)]
        extruded_outline("Swept stabilizer %s"%sign,outline,-.105,-.24,bronze,.035)
        center=Vector((sum(p[0] for p in outline)/4,sum(p[1] for p in outline)/4))
        inset=[tuple(center+(Vector(p)-center)*.84) for p in outline]
        extruded_outline("Stabilizer ceramic inlay %s"%sign,inset,-.09,-.112,pearl,.018)
        tip=[(-1.60,sign*1.17,-.073),(-1.23,sign*1.28,-.073)]
        tube("Stabilizer navigation slit %s"%sign,tip,.008,cyan)
        # Twin short nacelles with an actual recessed rear chamber.
        y=sign*.85;z=-.25
        loft("Thruster ceramic fairing %s"%sign,[(-2.29,.175),(-2.25,.207),(-2.10,.237),(-1.72,.231),(-1.36,.174),(-1.13,.065)],ceramic,64,1,(0,y,z))
        loft("Thruster exposed neck %s"%sign,[(-2.43,.169),(-2.34,.187),(-2.18,.199)],dark,64,1,(0,y,z))
        # Open annular shroud: inward and outward rings share a rear lip.
        verts=[];N=64
        for x,r in [(-2.445,.17),(-2.43,.185),(-2.30,.183),(-2.32,.128),(-2.444,.13)]:
            verts.extend([(x,y+r*math.cos(i*math.tau/N),z+r*math.sin(i*math.tau/N)) for i in range(N)])
        faces=[(k*N+i,k*N+(i+1)%N,((k+1)%5)*N+(i+1)%N,((k+1)%5)*N+i) for k in range(5) for i in range(N)]
        mesh_object("Machined nozzle shroud %s"%sign,verts,faces,metal,True)
        ring("Nozzle retention ring %s"%sign,-2.431,.184,.009,gold,y,z)
        ring("Recessed ion aperture %s"%sign,-2.44,.125,.008,cyan,y,z)
        loft("Nozzle dark recessed center %s"%sign,[(-2.365,.120),(-2.350,.120)],dark,64,1,(0,y,z))
        for i in range(12):
            theta=i*math.tau/12
            box("Nozzle radiator tooth %s %d"%(sign,i),(-2.31,y+.19*math.cos(theta),z+.19*math.sin(theta)),(.20,.026,.037),dark,.004,(theta,0,0))
        # Restrained side markings and navigation apertures.
        x=.49;r=radius(x);theta=.48 if sign>0 else math.pi-.48
        p=(x,r*math.cos(theta),r*math.sin(theta)*.68)
        tube("Forward navigation slit %s"%sign,[(p[0]-.13,p[1]*1.012,p[2]+.013),(p[0]+.13,p[1]*1.012,p[2]+.013)],.009,cyan)
        loft("Forward emitter barrel %s"%sign,[(.91,.031),(1.48,.031),(1.60,.041),(1.67,.040)],dark,40,1,(0,sign*.27,-.10))
        ring("Emitter muzzle trim %s"%sign,1.67,.040,.006,metal,sign*.27,-.10)
        # Flush vent banks read as cooling machinery, not extra weapons.
        for i in range(5):
            x=-.95+i*.10;y=sign*.88;z=.055
            box("Shoulder vent blade %s %d"%(sign,i),(x,y,z),(.045,.045,.16),dark,.006,(sign*.13,0,0))
    # Open oval cockpit ring conforms to the acorn shell rather than a raised box.
    rim=[]
    for i in range(128):
        theta=i*math.tau/128;x=-.15+.646*math.cos(theta);y=.410*math.sin(theta)
        z=.68*math.sqrt(max(0,radius(x)**2-y*y))+.021
        rim.append((x,y,z))
    tube("Cockpit continuous raised coaming",rim,.024,gold,True)
    box("Pilot footwell",(-.04,0,.245),(.95,.58,.055),dark,.06)
    box("Seat plinth",(-.34,0,.47),(.41,.47,.33),dark,.06)
    box("Seat cushion",(-.27,0,.659),(.49,.49,.072),rubber,.055)
    back=box("Seat back",(-.595,0,.779),(.11,.56,.40),rubber,.065,(0,-.10,0))
    for sign in (-1,1):
        tube("Seat structural brace %s"%sign,[(-.57,sign*.285,.51),(-.66,sign*.285,.90)],.016,gold)
        box("Arm console %s"%sign,(.12,sign*.28,.72),(.33,.105,.13),dark,.025)
        tube("Pilot control grip %s"%sign,[(.12,sign*.245,.77),(.135,sign*.235,.90)],.018,rubber)
        ring("Control illumination %s"%sign,.14,.022,.0035,cyan,sign*.235,.89)
    box("Forward instrument deck",(.36,0,.735),(.23,.52,.075),dark,.025,(0,.27,0))
    for y in (-.15,0,.15):
        box("Instrument glass %s"%y,(.32,y,.79),(.14,.115,.01),glass,.012,(0,.27,0))
        tube("Instrument line %s"%y,[(.299,y-.035,.799),(.299,y+.035,.799)],.003,cyan)
    # A low, physically thick windscreen keeps the hero's face and tail unobstructed.
    verts=[];rows,cols=10,24
    for i in range(rows+1):
        v=i/rows
        for j in range(cols+1):
            u=2*j/cols-1
            verts.append((.48+.09*(1-u*u)-v*.105,.40*u,.585+.07*u*u+v*(.28-.05*u*u)))
    faces=[(i*(cols+1)+j,i*(cols+1)+j+1,(i+1)*(cols+1)+j+1,(i+1)*(cols+1)+j) for i in range(rows) for j in range(cols)]
    mesh_object("Curved low windscreen",verts,faces,glass,True,solidify=.007)
    tube("Windscreen top trim",verts[-(cols+1):],.012,gold)
    for edge in (0,cols):tube("Windscreen edge %d"%edge,[verts[i*(cols+1)+edge] for i in range(rows+1)],.011,dark)
    # Small flush service caps and fasteners give readable scale without noisy greebles.
    for sign in (-1,1):
        for x in (.05,.8):
            theta=.35 if sign>0 else math.pi-.35;r=radius(x)+.018
            center=Vector((x,r*math.cos(theta),r*math.sin(theta)*.68))
            normal=Vector((0,math.cos(theta),math.sin(theta)/.68)).normalized()
            tangent=Vector((1,0,0));up=normal.cross(tangent)
            loop=[center+.032*(tangent*math.cos(i*math.tau/24)+up*math.sin(i*math.tau/24)) for i in range(24)]
            tube("Flush access cap %s %s"%(sign,x),loop,.0035,metal,True)
    # Reinforced keel remains inside the existing underside envelope.
    # The pressure shell itself defines the underside; avoid an exposed floating keel rod.
    return MATERIALS


def evaluated_bounds(objects):
    deps=bpy.context.evaluated_depsgraph_get();points=[];triangles=0
    for obj in objects:
        evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh();mesh.calc_loop_triangles();triangles+=len(mesh.loop_triangles)
        points.extend(evaluated.matrix_world@vertex.co for vertex in mesh.vertices);evaluated.to_mesh_clear()
    return [[min(v[i] for v in points)*100 for i in range(3)],[max(v[i] for v in points)*100 for i in range(3)]],triangles


def setup_studio():
    scene=bpy.context.scene;scene.render.engine="CYCLES";scene.cycles.samples=48;scene.cycles.use_denoising=True
    try:
        prefs=bpy.context.preferences.addons["cycles"].preferences;prefs.compute_device_type="OPTIX";prefs.get_devices()
        gpu=[device for device in prefs.devices if device.type=="OPTIX"]
        if gpu:
            for device in prefs.devices:device.use=device.type=="OPTIX"
            scene.cycles.device="GPU"
    except Exception as error:print("Cycles uses existing CPU fallback:",error)
    scene.render.resolution_x,scene.render.resolution_y=1800,1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format="PNG"
    scene.world=bpy.data.worlds.new("Neutral dark studio");scene.world.use_nodes=True;scene.world.node_tree.nodes["Background"].inputs["Color"].default_value=(.075,.10,.15,1);scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value=.27
    floor_mat=bpy.data.materials.new("Preview floor only");floor_mat.use_nodes=True;bsdf=floor_mat.node_tree.nodes["Principled BSDF"];bsdf.inputs["Base Color"].default_value=(.018,.024,.032,1);bsdf.inputs["Roughness"].default_value=.30
    bpy.ops.mesh.primitive_plane_add(size=2000,location=(0,0,-.705));floor=bpy.context.object;floor.name="StudioFloor_NOT_ASSET";floor.data.materials.append(floor_mat)
    for name,position,power,size,color in [("KeySoftbox",(1,-4,6),1500,5,(1,.88,.72)),("ColdRim",(-3,3,4),1900,4,(.55,.73,1)),("TopRibbon",(0,1,6),1100,3,(1,1,1)),("ForwardFill",(4,1,2),600,3,(1,.85,.68))]:
        data=bpy.data.lights.new(name,"AREA");data.energy=power;data.shape="RECTANGLE";data.size=size;data.size_y=size*.45;data.color=color
        obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=position;obj.rotation_euler=(Vector((0,0,.1))-obj.location).to_track_quat("-Z","Y").to_euler()
    data=bpy.data.cameras.new("ReviewCamera");camera=bpy.data.objects.new("ReviewCamera",data);scene.collection.objects.link(camera);scene.camera=camera;data.lens=52;data.clip_end=5000
    return scene,camera


def export_ship():
    # Editable .blend stores all authored parts/modifiers; no character embedded.
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"AcornShipCandidate.blend"),compress=True)
    bpy.ops.object.select_all(action="DESELECT")
    copies=[]
    for obj in SHIP:
        clone=obj.copy();clone.data=obj.data.copy();bpy.context.scene.collection.objects.link(clone);clone.select_set(True);copies.append(clone)
    bpy.context.view_layer.objects.active=copies[0]
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.join();joined=bpy.context.object;joined.name="SM_AcornShipCandidate"
    # Stable common pivot, metres. Blender glTF export supplies coordinate transport.
    bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    bpy.ops.export_scene.gltf(filepath=str(OUT/"AcornShipCandidate.glb"),export_format="GLB",use_selection=True,export_apply=True,export_yup=True,export_normals=True,export_materials="EXPORT",export_animations=False)
    # A single OBJ in project centimetres uses the proven legacy UE importer.
    # Preserve evaluated corner normals and all material groups; no hero/studio.
    mesh=joined.data;mesh.calc_loop_triangles()
    matrix=joined.matrix_world;normal_matrix=matrix.to_3x3().inverted().transposed()
    normal_ids={};normals=[];triangles=[]
    for tri in mesh.loop_triangles:
        corners=[]
        for loop_index in tri.loops:
            normal=(normal_matrix@mesh.corner_normals[loop_index].vector).normalized()
            key=tuple(round(float(value),7) for value in normal)
            if key not in normal_ids:normal_ids[key]=len(normals)+1;normals.append(key)
            corners.append((mesh.loops[loop_index].vertex_index+1,normal_ids[key]))
        triangles.append((tri.material_index,corners))
    def number(value):return f"{0.0 if abs(value)<.00000005 else value:.7f}"
    lines=["# SpaceSurvival AcornShip candidate; centimetres +X forward +Z up", "mtllib AcornShipCandidate.mtl", "o SM_AcornShipV2"]
    for vertex in mesh.vertices:lines.append("v "+" ".join(number(value*100) for value in matrix@vertex.co))
    for normal in normals:lines.append("vn "+" ".join(number(value) for value in normal))
    for index,mat in enumerate(mesh.materials):
        if mat is None:
            assert not any(mat_index==index for mat_index,_ in triangles), "Missing material on an exported triangle"
            continue
        lines.append("usemtl "+mat.name)
        for mat_index,corners in triangles:
            if mat_index==index:lines.append("f "+" ".join(f"{vertex}//{normal}" for vertex,normal in corners))
    (OUT/"AcornShipCandidate.obj").write_text("\n".join(lines)+"\n",encoding="utf-8")
    mtl=[]
    for mat in mesh.materials:
        if mat is None:continue
        bsdf=mat.node_tree.nodes['Principled BSDF'];color=bsdf.inputs['Base Color'].default_value
        mtl.extend(["newmtl "+mat.name,"Kd "+" ".join(number(value) for value in color[:3]),"Pm "+number(bsdf.inputs['Metallic'].default_value),"Pr "+number(bsdf.inputs['Roughness'].default_value),"d 1.0",""])
    (OUT/"AcornShipCandidate.mtl").write_text("\n".join(mtl),encoding="utf-8")
    bpy.data.objects.remove(joined,do_unlink=True)


def transient_pilot():
    sys.path.insert(0,str(ROOT/"ContentSource"));import GenerateDisembark as authoring
    prior=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(ROOT/"ContentSource/Animation/PilotMesh.glb"))
    added=[obj for obj in bpy.context.scene.objects if obj not in prior]
    rig=next(obj for obj in added if obj.type=="ARMATURE");rig.animation_data_clear()
    for bone in rig.pose.bones:bone.rotation_mode="QUATERNION"
    doc,binary=authoring.read_glb(ROOT/"ContentSource/Animation/Pilot.glb");authoring.apply_animation(rig,doc,binary,0)
    rig.rotation_mode="XYZ";rig.rotation_euler=(0,0,math.pi/2);rig.scale=(1.5,1.5,1.5);rig.location=(-.15,0,.72)
    bpy.context.view_layer.update()
    return added


def main():
    OUT.mkdir(exist_ok=True)
    protected_paths=[ROOT/"model-rigged.glb",ROOT/"ContentSource/Animation/Pilot.glb",ROOT/"ContentSource/Animation/PilotMesh.glb",ROOT/"ContentSource/Meshes/SM_AcornShip.obj"]
    protected={path.relative_to(ROOT).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in protected_paths}
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0;bpy.context.scene.unit_settings.system="METRIC";bpy.context.scene.unit_settings.scale_length=1
    make_ship();bpy.context.view_layer.update();bounds,triangles=evaluated_bounds(SHIP)
    scene,camera=setup_studio();export_ship()
    pilot=transient_pilot()
    views=[("Hero",(5.2,-6.5,4.1),(.0,0,.35),52), ("Chase",(-7.6,-4.65,3.2),(-.15,0,.40),50), ("Side",(.1,-9.1,1.5),(-.18,0,.38),52), ("Cockpit",(2.1,-2.2,2.25),(-.15,0,.75),57), ("EngineDetail",(-4.65,-3.8,1.7),(-1.63,-.42,-.18),57)]
    for name,position,target,lens in views:
        camera.location=position;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat("-Z","Y").to_euler();camera.data.lens=lens
        scene.render.filepath=str(OUT/(name+".png"));bpy.ops.render.render(write_still=True)
    for path,digest in protected.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest
    record={"status":"AUTHORED_SHIP_CANDIDATE_SOURCE_REVIEW_NOT_UNREAL_OR_OWNER_ACCEPTANCE","blender":bpy.app.version_string,"bounds_cm":bounds,"reference_bounds_cm":[[-247,-145,-66.516],[210,145,100]],"evaluated_triangles":triangles,"authored_parts":len(SHIP),"pilot_transform":{"position_cm":[-15,0,72],"unreal_yaw_degrees":-90,"blender_z_rotation_degrees":90,"scale":1.5,"source":"Existing PilotMesh.glb plus A_Pilot0s,loaded only for previews"},"cockpit":{"real_open_well":True,"center_xy_cm":[-15,0],"opening_half_dimensions_cm":[64,40],"windscreen_peak_cm":86.5},"materials":[{"name":name,"base_color":list(mat.diffuse_color),"metallic":mat.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value,"roughness":mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value} for name,mat in MATERIALS.items()],"protected_sha256":protected,"limits":["Separate candidate, current runtime and meshes unchanged","Source render uses existing Blender Cycles studio lighting, not gameplay or Unreal materials","Procedural micro-bump is a Blender authoring detail; glTF export retains base PBR values but will need equivalent Unreal shader setup","No collision mesh, LODs, socket integration, shader cost or runtime performance validated","Existing pilot tail defects remain visible and are not modified by this ship source","Commercial Hybrid visual quality requires owner review; no near-alpha acceptance claim"],"outputs":[{"file":path.name,"bytes":path.stat().st_size,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()} for path in sorted(OUT.iterdir()) if path.suffix in ('.blend','.glb','.obj','.mtl','.png')]}
    (OUT/"Report.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    print("ACORN_CANDIDATE_SOURCE_DONE",json.dumps({key:record[key] for key in ['bounds_cm','evaluated_triangles','authored_parts']}))


if __name__=="__main__":
    main()