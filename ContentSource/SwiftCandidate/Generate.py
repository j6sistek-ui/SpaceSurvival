"""Original Swift body candidate around an exact preserved authored cockpit.
Only writes ContentSource/SwiftCandidate. No Unreal or gameplay selection.
Build with installed Blender --background --factory-startup --threads 8.
Pass -- --render for a source-only CPU studio review with transient Acornaut.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys

import bpy
import bmesh
from mathutils import Vector

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
BASE = ROOT / "ContentSource/AcornShipCandidate"
PARTS = []
MATS = {}
PRESERVED_PREFIXES = (
    "Cockpit continuous raised coaming", "Pilot footwell", "Seat plinth",
    "Seat cushion", "Seat back", "Seat structural brace", "Arm console",
    "Pilot control grip", "Control illumination", "Forward instrument deck",
    "Instrument glass", "Instrument line", "Curved low windscreen",
    "Windscreen top trim", "Windscreen edge")
PROFILE = [(-2.26,.12),(-2.08,.29),(-1.64,.45),(-1.02,.58),
           (-.60,.665),(-.15,.67),(.38,.59),(.93,.44),(1.48,.29),
           (1.98,.13),(2.39,.015)]
TITANIUM = "AC01_MachinedTitanium"
DARK = "AC01_GraphiteStructure"
PEARL = "AC01_IvoryPanels"
GOLD = "AC01_ChampagneEdges"
GLOW = "AC01_IonAndNav"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_module():
    spec = importlib.util.spec_from_file_location("ss_acorn_helpers", ROOT / "ContentSource/GenerateAcornShipCandidate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fingerprint(obj):
    deps = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(deps)
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    digest = hashlib.sha256()
    def pack(values, code):
        digest.update(struct.pack("<" + code * len(values), *values))
    pack([v for row in obj.matrix_world for v in row], "f")
    for v in mesh.vertices:
        pack(tuple(v.co), "f")
    for t in mesh.loop_triangles:
        pack(tuple(t.vertices) + (t.material_index,), "I")
    for n in mesh.corner_normals:
        pack(tuple(n.vector), "f")
    digest.update("|".join(m.name if m else "" for m in mesh.materials).encode())
    result = {"sha256": digest.hexdigest(), "triangles": len(mesh.loop_triangles),
              "vertices": len(mesh.vertices), "materials": [m.name for m in mesh.materials if m]}
    evaluated.to_mesh_clear()
    return result


def load_cockpit():
    bpy.ops.wm.open_mainfile(filepath=str(BASE / "AcornShipCandidate.blend"))
    bpy.context.preferences.filepaths.save_version = 0
    retained = [o for o in bpy.context.scene.objects if o.type in ("MESH", "CURVE") and o.name.startswith(PRESERVED_PREFIXES)]
    assert len(retained) == 24, [o.name for o in retained]
    before = {o.name: fingerprint(o) for o in retained}
    for obj in list(bpy.context.scene.objects):
        if obj not in retained:
            bpy.data.objects.remove(obj, do_unlink=True)
    PARTS.extend(sorted(retained, key=lambda o:o.name))
    for name in (TITANIUM, DARK, PEARL, GOLD, GLOW, "AC01_CockpitPadding", "AC01_Windscreen"):
        MATS[name] = bpy.data.materials[name]
    return before


def radius(x):
    for i in range(len(PROFILE)-1):
        if x <= PROFILE[i+1][0]:
            a,ra=PROFILE[i]; b,rb=PROFILE[i+1]
            t=max(0,min(1,(x-a)/(b-a)))
            prior=PROFILE[max(0,i-1)];after=PROFILE[min(len(PROFILE)-1,i+2)]
            ma=(rb-prior[1])/(b-prior[0]);mb=(after[1]-ra)/(after[0]-a)
            return (2*t**3-3*t*t+1)*ra+(t**3-2*t*t+t)*(b-a)*ma+(-2*t**3+3*t*t)*rb+(t**3-t*t)*(b-a)*mb
    return PROFILE[-1][1]


def body(name, vertices, faces, material, bevel=0, smooth=False):
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.materials.append(MATS[material])
    for p in mesh.polygons:p.use_smooth=smooth
    if smooth:mesh.set_sharp_from_angle(angle=math.radians(42))
    if bevel:
        mod=obj.modifiers.new("Machined edge radius","BEVEL")
        mod.width=bevel; mod.segments=3; mod.limit_method="ANGLE"; mod.angle_limit=.35; mod.harden_normals=True
    if bevel or not smooth:
        mod=obj.modifiers.new("Face weighted highlights","WEIGHTED_NORMAL");mod.keep_sharp=True
    PARTS.append(obj)
    return obj


def prism(name, polygon, low, high, material, bevel=.012):
    area=sum(polygon[i][0]*polygon[(i+1)%len(polygon)][1]-polygon[(i+1)%len(polygon)][0]*polygon[i][1] for i in range(len(polygon)))
    if area<0:polygon=list(reversed(polygon))
    n=len(polygon)
    verts=[(x,y,z) for z in (low,high) for x,y in polygon]
    faces=[tuple(reversed(range(n))),tuple(range(n,n*2))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return body(name,verts,faces,material,min(bevel,(high-low)*.25))


def loft(name,rings,material,center=(0,0,0),zscale=1,sides=48,closed=True):
    verts=[(center[0]+x,center[1]+r*math.cos(i*math.tau/sides),center[2]+r*math.sin(i*math.tau/sides)*zscale) for x,r in rings for i in range(sides)]
    faces=[(j*sides+i,j*sides+(i+1)%sides,(j+1)*sides+(i+1)%sides,(j+1)*sides+i) for j in range(len(rings)-1) for i in range(sides)]
    if closed:faces += [tuple(reversed(range(sides))),tuple(range((len(rings)-1)*sides,len(rings)*sides))]
    return body(name,verts,faces,material,smooth=True)


def annulus(name,rings,material,center=(0,0,0),sides=48,zscale=1):
    verts=[(center[0]+x,center[1]+r*math.cos(i*math.tau/sides),center[2]+r*math.sin(i*math.tau/sides)*zscale) for x,r in rings for i in range(sides)]
    faces=[(j*sides+i,j*sides+(i+1)%sides,((j+1)%len(rings))*sides+(i+1)%sides,((j+1)%len(rings))*sides+i) for j in range(len(rings)) for i in range(sides)]
    return body(name,verts,faces,material,smooth=True)


def box(name,at,size,material,bevel=.008):
    x,y,z=at;a,b,c=[v/2 for v in size]
    return body(name,[(x+u*a,y+v*b,z+w*c) for w in (-1,1) for v in (-1,1) for u in (-1,1)],
                [(0,2,3,1),(4,5,7,6),(0,1,5,4),(1,3,7,5),(3,2,6,7),(2,0,4,6)],
                material,min(bevel,min(size)*.25))


def tube(name,points,width,material,cyclic=False):
    data=bpy.data.curves.new(name,"CURVE");data.dimensions="3D";data.bevel_depth=width;data.bevel_resolution=2
    s=data.splines.new("POLY");s.points.add(len(points)-1)
    for p,co in zip(s.points,points):p.co=(*co,1)
    s.use_cyclic_u=cyclic
    obj=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(obj);data.materials.append(MATS[material]);PARTS.append(obj);return obj


def hull_and_deck():
    rings=[(-2.26+(2.39+2.26)*i/100,radius(-2.26+(2.39+2.26)*i/100)) for i in range(101)]
    hull=loft("Swift narrow continuous pressure hull",rings,TITANIUM,zscale=.84,sides=72)
    # Same original clear pilot well: no fill across the retained seat/footwell.
    bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=1,depth=1.8,location=(-.15,0,1.0))
    cutter=bpy.context.object;cutter.scale=(.64,.40,1);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    helper=source_module();helper.cut_cockpit(hull,cutter);bpy.data.objects.remove(cutter,do_unlink=True)
    # Only the new hull receives submicron boolean cleanup. Retained cockpit is untouched.
    bm=bmesh.new();bm.from_mesh(hull.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-8)
    bm.to_mesh(hull.data);bm.free();hull.data.update()
    # A new transition collar connects the exact old coaming to the slimmer skin.
    verts=[];N=128
    coaming=bpy.data.objects["Cockpit continuous raised coaming"].data.splines[0]
    assert len(coaming.points)==N
    for row in range(5):
        t=row/4
        for i in range(N):
            a=i*math.tau/N;inner=Vector(coaming.points[i].co[:3])
            x=-.15+.75*math.cos(a);y=.525*math.sin(a)
            outer_z=.84*math.sqrt(max(.001,radius(x)**2-y*y))+.008
            outer=Vector((x,y,outer_z))
            p=inner.lerp(outer,t);p.z-=.017*(1-t)
            verts.append(tuple(p))
    faces=[(j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i) for j in range(4) for i in range(N)]
    collar=body("Swift cockpit transition collar",verts,faces,DARK,smooth=True)
    mod=collar.modifiers.new("Collar thickness","SOLIDIFY");mod.thickness=.012;mod.offset=-1
    # Sample the actual skin in both axes; long n-gons would cut through the hull.
    def surface_panel(name,positions,rows,cols):
        faces=[(j*(cols+1)+i,j*(cols+1)+i+1,(j+1)*(cols+1)+i+1,(j+1)*(cols+1)+i) for j in range(rows) for i in range(cols)]
        obj=body(name,positions,faces,PEARL,smooth=True)
        thickness=obj.modifiers.new("Ceramic physical thickness","SOLIDIFY");thickness.thickness=.012;thickness.offset=-1
        bevel=obj.modifiers.new("Ceramic edge highlight","BEVEL");bevel.width=.003;bevel.segments=2;bevel.limit_method="ANGLE";bevel.angle_limit=.25
        return obj
    positions=[];rows,cols=48,8
    for j in range(rows+1):
        t=j/rows;x=.59+(2.345-.59)*t
        width=(.275*(1-t)+.009*t)*(1-.12*math.sin(t*math.pi))
        for i in range(cols+1):
            y=width*(2*i/cols-1)
            z=.84*math.sqrt(max(.0001,radius(x)**2-y*y))+.021
            positions.append((x,y,z))
    surface_panel("Swift continuous dorsal nose plate",positions,rows,cols)
    for side in (-1,1):
        positions=[];rows,cols=32,6
        for j in range(rows+1):
            t=j/rows;x=-2.09+1.22*t
            for i in range(cols+1):
                angle=side*(.16+(.65-.16)*i/cols)
                r=radius(x)+.02
                positions.append((x,r*math.sin(angle),r*math.cos(angle)*.84))
        surface_panel("Swift aft curved service rail %d"%side,positions,rows,cols)
    for i in range(8):
        x=-1.90+i*.09
        z=radius(x)*.84+.008
        box("Swift recessed dorsal radiator %02d"%i,(x,0,z),(.038,.24,.022),DARK,.004)


def wings_and_drives():
    for side in (-1,1):
        # Cranked swept planform: inboard neck, diagonal spar, tapered tip.
        wing=[(-1.95,side*.39),(-1.84,side*.88),(-1.12,side*1.285),
              (-.78,side*1.23),(-.31,side*.55),(.42,side*.49),(.59,side*.34)]
        prism("Swift swept spar %d"%side,wing,-.19,-.105,DARK,.022)
        panels=[
            [(-1.80,side*.48),(-1.67,side*.84),(-1.22,side*1.11),(-.80,side*.55),(-.44,side*.47)],
            [(-1.21,side*1.135),(-1.105,side*1.245),(-.83,side*1.197),(-.42,side*.602),(-.71,side*.588)]]
        for j,polygon in enumerate(panels):
            prism("Swift swept ceramic surface %d %d"%(side,j),polygon,-.097,-.062,PEARL,.008)
        tube("Swift wing leading metal edge %d"%side,[(-1.90,side*.47,-.084),(-1.76,side*.90,-.084),(-1.12,side*1.253,-.084)],.008,GOLD)
        tube("Swift narrow navigation slit %d"%side,[(-1.13,side*1.253,-.047),(-.86,side*1.205,-.047)],.006,GLOW)
        # Narrower, longer thrust pods, no added thruster gameplay.
        y=side*.71;z=-.24
        loft("Swift long engine nacelle %d"%side,[(-2.31,.145),(-2.20,.18),(-1.66,.176),(-1.14,.122),(-.78,.035)],PEARL,(0,y,z),sides=48)
        annulus("Swift machined exhaust chamber %d"%side,[(-2.435,.141),(-2.405,.167),(-2.18,.167),(-2.15,.115),(-2.37,.113)],TITANIUM,(0,y,z))
        annulus("Swift nozzle retention band %d"%side,[(-2.405,.170),(-2.370,.170),(-2.370,.161),(-2.405,.161)],GOLD,(0,y,z))
        loft("Swift recessed cyan ion face %d"%side,[(-2.36,.108),(-2.355,.108)],GLOW,(0,y,z),sides=48)
        loft("Swift nozzle injector %d"%side,[(-2.395,.030),(-2.35,.041)],DARK,(0,y,z),sides=32)
        for i in range(8):
            a=i*math.tau/8
            tube("Swift engine cooling channel %d %d"%(side,i),[(-2.13,y+.181*math.cos(a),z+.181*math.sin(a)),(-1.87,y+.181*math.cos(a),z+.181*math.sin(a))],.008,DARK)
        # Original class uses two frontal visual emitters; one weapon policy stays native.
        loft("Swift emitter fairing %d"%side,[(1.16,.031),(1.69,.036),(1.78,.025)],DARK,(0,side*.27,-.10),sides=32)
        annulus("Swift emitter muzzle %d"%side,[(1.77,.03),(1.805,.03),(1.805,.018),(1.775,.018)],TITANIUM,(0,side*.27,-.10),sides=32)
        for i,x in enumerate((-.88,-.63,-.37)):
            box("Swift shoulder service port %d %d"%(side,i),(x,side*.591,.10),(.095,.018,.048),DARK,.008)
        # Deliberately low dorsal strakes behind the pilot, below the old seatback.
        poly=[(-2.07,.08),(-1.49,.44),(-1.17,.46),(-1.48,.11)]
        verts=[(x,side*.34+v,z) for v in (-.017,.017) for x,z in poly];n=len(poly)
        faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)]
        body("Swift aft directional strake %d"%side,verts,faces,TITANIUM,.006)


def export(before):
    bpy.context.view_layer.update()
    assert all(fingerprint(bpy.data.objects[name])==value for name,value in before.items()),"Preserved cockpit changed"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"SwiftCandidate.blend"),compress=True)
    bpy.ops.object.select_all(action="DESELECT")
    clones=[]
    for original in sorted(PARTS,key=lambda o:o.name):
        obj=original.copy();obj.data=original.data.copy();bpy.context.scene.collection.objects.link(obj);obj.select_set(True);obj["swift_original_name"]=original.name;clones.append(obj)
    bpy.context.view_layer.objects.active=clones[0];bpy.ops.object.convert(target="MESH")
    # Freeze each evaluated tessellation before joining dissimilar part transforms.
    export_parts=[]
    for part_index,clone in enumerate(clones):
        bpy.context.view_layer.objects.active=clone
        mod=clone.modifiers.new("Export triangle topology","TRIANGULATE");mod.quad_method="BEAUTY";mod.ngon_method="BEAUTY"
        bpy.ops.object.modifier_apply(modifier=mod.name)
        clone.data.calc_loop_triangles()
        identity=clone.data.attributes.new(name="swift_part_id",type="INT",domain="FACE")
        identity.data.foreach_set("value",[part_index]*len(clone.data.polygons))
        export_parts.append({"name":clone["swift_original_name"],"triangles":len(clone.data.loop_triangles),
                             "degenerate":sum(t.area<=1e-12 for t in clone.data.loop_triangles)})
    bpy.context.view_layer.objects.active=clones[0];bpy.ops.object.join()
    joined=bpy.context.object;joined.name="SM_SwiftCandidate"
    bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    bpy.ops.object.mode_set(mode="EDIT");bpy.ops.mesh.select_all(action="SELECT");bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.008);bpy.ops.object.mode_set(mode="OBJECT")
    mesh=joined.data;mesh.calc_loop_triangles();uv=mesh.uv_layers.active
    vertices=[joined.matrix_world@v.co for v in mesh.vertices]
    normal_matrix=joined.matrix_world.to_3x3().inverted().transposed()
    normals=[];uvs=[];triangles=[];degenerate=0;joined_degenerate_by_part={}
    identities=mesh.attributes["swift_part_id"]
    for t in mesh.loop_triangles:
        if t.area<=1e-12:
            degenerate+=1
            part=export_parts[identities.data[t.polygon_index].value]["name"]
            joined_degenerate_by_part[part]=joined_degenerate_by_part.get(part,0)+1
        corners=[]
        for loop in t.loops:
            n=(normal_matrix@mesh.corner_normals[loop].vector).normalized();coord=uv.data[loop].uv
            assert all(math.isfinite(x)for x in (*n,*coord)) and abs(n.length-1)<.00001
            normals.append(tuple(n));uvs.append(tuple(coord));corners.append((mesh.loops[loop].vertex_index+1,len(uvs),len(normals)))
        triangles.append((t.material_index,corners))
    def number(v):return "%.7f"%(0 if abs(v)<.00000005 else v)
    lines=["# SpaceSurvival Swift candidate; cm; +X forward; +Z up; pilot pivot preserved","mtllib SwiftCandidate.mtl","o SM_SwiftCandidate"]
    lines+=["v "+" ".join(number(x*100)for x in v)for v in vertices]
    lines+=["vt "+" ".join(number(x)for x in v)for v in uvs]
    lines+=["vn "+" ".join(number(x)for x in v)for v in normals]
    materials=[]
    for index,mat in enumerate(mesh.materials):
        if not any(i==index for i,_ in triangles):continue
        lines.append("usemtl "+mat.name)
        lines+=["f "+" ".join("%d/%d/%d"%c for c in corners)for i,corners in triangles if i==index]
        node=mat.node_tree.nodes["Principled BSDF"]
        materials.append({"name":mat.name,"base_color":list(node.inputs["Base Color"].default_value),"metallic":node.inputs["Metallic"].default_value,"roughness":node.inputs["Roughness"].default_value,"emission":node.inputs["Emission Strength"].default_value,"transmission":node.inputs["Transmission Weight"].default_value})
    (OUT/"SwiftCandidate.obj").write_text("\n".join(lines)+"\n",encoding="utf-8",newline="\n")
    mtl=[]
    for m in materials:mtl+=["newmtl "+m["name"],"Kd "+" ".join(number(x)for x in m["base_color"][:3]),"Pm "+number(m["metallic"]),"Pr "+number(m["roughness"]),"d 1.0",""]
    (OUT/"SwiftCandidate.mtl").write_text("\n".join(mtl),encoding="utf-8",newline="\n")
    bpy.ops.export_scene.gltf(filepath=str(OUT/"SwiftCandidate.glb"),export_format="GLB",use_selection=True,export_apply=True,export_yup=True,export_normals=True,export_materials="EXPORT",export_animations=False)
    record={"parts":len(PARTS),"triangles":len(triangles),"vertices":len(vertices),"degenerate_triangles":degenerate,"materials":materials,"bounds_cm":[[min(v[i]for v in vertices)*100 for i in range(3)],[max(v[i]for v in vertices)*100 for i in range(3)]],"pivot_cm":[0,0,0],"uv_channels":len(mesh.uv_layers),"preserved_cockpit":before,"export_part_topology":export_parts,"joined_degenerate_by_part":joined_degenerate_by_part}
    assert len(materials)==7,len(materials)
    assert not any(name.startswith("Swift ") for name in joined_degenerate_by_part), "New body has degenerate exported triangles"
    assert all(r["degenerate"]==0 for r in export_parts if r["name"].startswith("Swift "))
    assert all(record["bounds_cm"][0][i] >= (-247,-185,-66.6)[i]-.02 for i in range(3))
    assert all(record["bounds_cm"][1][i] <= (241.5,185,100)[i]+.02 for i in range(3))
    bpy.data.objects.remove(joined,do_unlink=True)
    return record


def studio():
    bpy.ops.wm.open_mainfile(filepath=str(OUT/"SwiftCandidate.blend"))
    # Source-only fit reference; supplied hero/animation are never saved in candidate.
    sys.path.insert(0,str(ROOT/"ContentSource"));import GenerateDisembark as animation
    prior=set(bpy.context.scene.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/"ContentSource/Animation/TailCandidateV2.glb"))
    added=[o for o in bpy.context.scene.objects if o not in prior];rig=next(o for o in added if o.type=="ARMATURE");rig.animation_data_clear()
    for bone in rig.pose.bones:bone.rotation_mode="QUATERNION"
    clip,binary=animation.read_glb(ROOT/"ContentSource/Animation/Pilot.glb");animation.apply_animation(rig,clip,binary,0)
    rig.rotation_mode="XYZ";rig.rotation_euler=(0,0,math.pi/2);rig.scale=(1.5,)*3;rig.location=(-.15,0,.72)
    helper=source_module();scene,camera=helper.setup_studio()
    scene.cycles.device="CPU";scene.cycles.samples=32;scene.render.threads_mode="FIXED";scene.render.threads=8
    scene.render.resolution_x,scene.render.resolution_y=1440,1050
    scene.view_settings.view_transform="AgX"
    views=[("Hero",(5.8,-7.4,4.5),(0,0,.30),52),
           ("Chase",(-7.5,-4.9,3.4),(-.15,0,.32),50),
           ("Top",(.01,0,11.5),(-.15,0,0),52),
           ("Cockpit",(2.1,-2.2,2.25),(-.15,0,.75),57)]
    output=[]
    for name,position,target,lens in views:
        camera.location=position;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat("-Z","Y").to_euler();camera.data.lens=lens
        scene.render.filepath=str(OUT/(name+".png"));bpy.ops.render.render(write_still=True)
        output.append({"file":name+".png","sha256":sha(OUT/(name+".png"))})
    return output


def main():
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    protected_paths=[ROOT/"model-rigged.glb",ROOT/"ContentSource/Animation/Pilot.glb",ROOT/"ContentSource/Animation/TailCandidateV2.glb",ROOT/"ContentSource/Animation/Disembark.glb",BASE/"AcornShipCandidate.blend",BASE/"AcornShipCandidate.obj",BASE/"AcornShipCandidate.glb",ROOT/"ContentSource/Meshes/SM_AgileShip.obj",ROOT/"Content/SpaceSurvival/Meshes/SM_AgileShip.uasset"]
    protected={p.relative_to(ROOT).as_posix():sha(p) for p in protected_paths}
    if "--render" in args:
        record={"status":"BLENDER_SOURCE_SWIFT_REVIEW_NOT_UNREAL","images":studio(),"generator_sha256":sha(__file__),"renderer":"Cycles CPU8 / 32 samples / 1440x1050 / AgX","protected_sha256":protected}
        (OUT/"RenderReport.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8",newline="\n")
    else:
        before=load_cockpit();hull_and_deck();wings_and_drives();record=export(before)
        record.update(status="SWIFT_SOURCE_CANDIDATE_NOT_ADOPTED",blender=bpy.app.version_string,generator_sha256=sha(__file__),
                      original_helper_sha256=sha(ROOT/"ContentSource/GenerateAcornShipCandidate.py"),protected_sha256=protected,
                      pilot_transform={"position_cm":[-15,0,72],"unreal_yaw_degrees":-90,"blender_z_rotation_degrees":90,"scale":1.5},
                      source_origin="Original replacement body around 24 exactly preserved authored Acorn cockpit components. No downloaded source. Existing Acornaut is transient only in source render.",
                      outputs=[{"file":p.name,"bytes":p.stat().st_size,"sha256":sha(p)}for p in sorted(OUT.iterdir())if p.suffix in (".blend",".obj",".glb",".mtl")],
                      limits=["Only separate source candidate; no Unreal import or runtime selection.","Exact existing cockpit does not resolve its known open-palm/grip animation fit.","New body keeps original Swift envelope and origin; no collision, stats or gameplay change.","Shared existing seven-material palette; native appearance, full animation clearance, LOD/performance and owner quality acceptance remain open."])
        (OUT/"Report.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8",newline="\n")
        print("SWIFT_SOURCE_FINISHED",json.dumps({k:record[k] for k in ("parts","triangles","vertices","degenerate_triangles","bounds_cm")}))
    for p,digest in protected.items():assert sha(ROOT/p)==digest,"Protected source changed: "+p


if __name__=="__main__":main()
