"""Original field geometry candidates. Run in a fresh Blender background process.
No rendering, imports, runtime references, or files outside this directory change.
Centimetre OBJ axes match the existing Unreal FbxFactory/convert_scene=False path.
"""
import hashlib
import json
import math
from pathlib import Path
import random
import subprocess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
RADIUS = 100.0
VERSION = "FieldCandidate3"
PROTECTED = [
    "model-rigged.glb",
    "ContentSource/FieldCandidates/V2/Generate.py",
    "ContentSource/FieldCandidates/V2/CheckSource.py",
    "ContentSource/FieldCandidates/V2/ElectricalField.hlsl",
    "ContentSource/FieldCandidates/V2/GravityField.hlsl",
    "ContentSource/FieldCandidates/V2/SourceReport.json",
    "ContentSource/FieldCandidates/V2/SourceValidation.json",
    "ContentSource/FieldCandidates/V2/CandidateReceipt.json",
    "ContentSource/FieldCandidates/V2/UnrealImport.json",
    "ContentSource/FieldCandidates/V2/UnrealPersisted.json",
    "ContentSource/FieldCandidates/V2/UnrealPreview.json",
    "Content/SpaceSurvival/Meshes/SM_ElectricalFieldCandidateV2.uasset",
    "Content/SpaceSurvival/Meshes/SM_GravityFieldCandidateV2.uasset",
    "Content/SpaceSurvival/Materials/M_ElectricalFieldCandidateV2.uasset",
    "Content/SpaceSurvival/Materials/M_GravityFieldCandidateV2.uasset",

    "ContentSource/GenerateGeometry.py",
    "ContentSource/Meshes/SM_StormRing.obj",
    "ContentSource/Meshes/SM_GravityRing.obj",
    "Content/SpaceSurvival/Meshes/SM_StormRing.uasset",
    "Content/SpaceSurvival/Meshes/SM_GravityRing.uasset",
    "Content/SpaceSurvival/Materials/M_Emissive.uasset",
    "ContentSource/FieldCandidates/Generate.py",
    "ContentSource/FieldCandidates/ElectricalField.hlsl",
    "ContentSource/FieldCandidates/GravityField.hlsl",
    "ContentSource/FieldCandidates/SourceReport.json",
    "ContentSource/FieldCandidates/CandidateReceipt.json",
    "Content/SpaceSurvival/Meshes/SM_ElectricalFieldCandidate.uasset",
    "Content/SpaceSurvival/Meshes/SM_GravityFieldCandidate.uasset",
    "Content/SpaceSurvival/Materials/M_ElectricalFieldCandidate.uasset",
    "Content/SpaceSurvival/Materials/M_GravityFieldCandidate.uasset",
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def mul(a, value):
    return tuple(x * value for x in a)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2], a[0]*b[1] - a[1]*b[0])


def length(a):
    return math.sqrt(dot(a, a))


def unit(a):
    size = length(a)
    assert size > 1e-10, "Degenerate geometry direction"
    return mul(a, 1.0 / size)


def sphere_point(z, angle, radius):
    side = math.sqrt(max(0, 1-z*z))
    return (radius*side*math.cos(angle), radius*side*math.sin(angle), radius*z)


class FieldMesh:
    def __init__(self, name, material, tint):
        self.name, self.material, self.tint = name, material, tint
        self.vertices, self.uvs, self.normals, self.faces, self.paths = [], [], [], [], []

    def ribbon(self, points, width, role):
        """Two orthogonal soft ribbons share one additive material section.
        UV.x=role*4+longitudinal fraction; UV.y=strand*4+across-width 0..1.
        The middle column captures a narrow filtered core inside broad raster coverage.
        """
        strand=len(self.paths)
        frames=[]
        normal=None
        for i,position in enumerate(points):
            before=points[max(0,i-1)]; after=points[min(len(points)-1,i+1)]
            tangent=unit(sub(after,before))
            if normal is None:
                normal=unit(cross(tangent,(0,0,1) if abs(tangent[2])<.9 else (0,1,0)))
            else:
                normal=unit(sub(normal,mul(tangent,dot(normal,tangent))))
            frames.append((tangent,normal,unit(cross(tangent,normal))))
        for plane in range(2):
            first=len(self.vertices)
            for i,(position,frame) in enumerate(zip(points,frames)):
                tangent=frame[0]; across=frame[plane+1]
                surface_normal=unit(cross(tangent,across))
                t=i/(len(points)-1)
                radius=width*(.65+.35*math.sin(math.pi*t)**.45)
                for side in range(3):
                    vertex=add(position,mul(across,(side-1)*radius))
                    if length(vertex)>RADIUS:vertex=mul(unit(vertex),RADIUS)
                    self.vertices.append(vertex)
                    self.normals.append(surface_normal)
                    self.uvs.append((role*4+t,strand*4+side*.5))
            for i in range(len(points)-1):
                for side in range(2):
                    a=first+i*3+side; b=a+1; c=a+3; d=c+1
                    self.faces.extend([(a,c,b),(b,c,d)])
        self.paths.append({"role":role,"points":len(points),"half_width_cm":width,
                           "closed":False,"cross_ribbon_planes":2,"triangles":(len(points)-1)*8})

    def boundary(self):
        # A soft additive boundary surface, not opaque geometry or a central core.
        # Smooth radial normals drive a broad stable rim, replacing great-circle wires.
        first=len(self.vertices)
        longitude=32; latitude=16
        self.vertices.append((0,0,RADIUS)); self.normals.append((0,0,1)); self.uvs.append((0,0))
        for ring in range(1,latitude):
            theta=math.pi*ring/latitude
            for segment in range(longitude):
                phi=math.tau*segment/longitude
                normal=(math.sin(theta)*math.cos(phi),math.sin(theta)*math.sin(phi),math.cos(theta))
                self.vertices.append(mul(normal,RADIUS)); self.normals.append(normal)
                self.uvs.append((segment/longitude,ring/latitude))
        south=len(self.vertices)
        self.vertices.append((0,0,-RADIUS)); self.normals.append((0,0,-1)); self.uvs.append((0,1))
        for segment in range(longitude):
            next_segment=(segment+1)%longitude
            self.faces.append((first,first+1+segment,first+1+next_segment))
            for ring in range(latitude-2):
                a=first+1+ring*longitude+segment; b=first+1+ring*longitude+next_segment
                c=a+longitude; d=b+longitude
                self.faces.extend([(a,c,b),(b,c,d)])
            a=first+1+(latitude-2)*longitude+segment
            b=first+1+(latitude-2)*longitude+next_segment
            self.faces.append((a,south,b))
        self.paths.append({"role":0,"surface":"additive spherical boundary","longitude":longitude,
                           "latitude":latitude,"vertices":south-first+1,"triangles":2*longitude*(latitude-1)})

    def inspect(self):
        low = [min(v[a] for v in self.vertices) for a in range(3)]
        high = [max(v[a] for v in self.vertices) for a in range(3)]
        areas = [length(cross(sub(self.vertices[b],self.vertices[a]), sub(self.vertices[c],self.vertices[a])))/2
                 for a,b,c in self.faces]
        assert len(self.faces) <= 5000
        assert min(areas) > 1e-8
        assert max(map(length, self.vertices)) <= RADIUS+1e-6
        assert all(abs(low[a]+RADIUS) < .0001 and abs(high[a]-RADIUS) < .0001 for a in range(3))
        assert all(math.isfinite(x) for v in self.vertices+self.uvs for x in v)
        directions = [(1,0,0),(0,1,0),(0,0,1),unit((1,1,1)),unit((1,-1,.5))]
        cover = []
        for direction in directions:
            # Conservative projected triangle-area sum, no occlusion subtraction;
            # not a rendered pixel-coverage or performance measurement.
            projected = sum(abs(dot(cross(sub(self.vertices[b],self.vertices[a]),
                                           sub(self.vertices[c],self.vertices[a])), direction))/2
                            for a,b,c in self.faces)
            cover.append({"direction": list(direction), "summed_area_to_sphere_disk_percent": 100*projected/(math.pi*RADIUS**2)})
        return {"name": self.name, "material": self.material, "tint": list(self.tint),
                "vertices": len(self.vertices), "triangles": len(self.faces), "material_sections": 1,
                "bounds_cm": [low,high], "max_vertex_radius_cm": max(map(length,self.vertices)),
                "minimum_triangle_area_cm2": min(areas), "paths": self.paths,
                "projected_area_upper_bounds": cover}

    def write_obj(self):
        lines = ["# Original field candidate; centimeters +X forward +Z up", "mtllib FieldPalette.mtl",
                 "o "+self.name, "usemtl "+self.material]
        lines += ["v "+" ".join(f"{x:.9f}" for x in v) for v in self.vertices]
        lines += ["vt "+" ".join(f"{x:.9f}" for x in uv) for uv in self.uvs]
        lines += ["vn "+" ".join(f"{x:.9f}" for x in n) for n in self.normals]
        for face in self.faces:
            lines.append("f "+" ".join(f"{i+1}/{i+1}/{i+1}" for i in face))
        (OUT/(self.name+".obj")).write_text("\n".join(lines)+"\n",encoding="utf-8",newline="\n")


def electrical():
    mesh = FieldMesh("SM_ElectricalFieldCandidateV3", "M_ElectricalFieldCandidateV3", (.24,.55,1.0))
    mesh.boundary()
    rng = random.Random(73191)
    for strand in range(6):
        angle = strand*math.tau/6
        start = sphere_point(.7*math.sin(angle*1.7),angle,96)
        end = sphere_point(.6*math.cos(angle*1.3),angle+2.2,92)
        centre = sphere_point(rng.uniform(-.65,.65),angle+.8,25)
        points = []
        for i in range(17):
            t = i/16
            p = add(add(mul(start,(1-t)**2),mul(centre,2*t*(1-t))),mul(end,t*t))
            jitter = tuple(rng.uniform(-8,8)*math.sin(math.pi*t) for _ in range(3))
            points.append(add(p,jitter))
        mesh.ribbon(points,2.3,role=1)
        for branch, index in enumerate((5,11)):
            source = points[index]
            tip = sphere_point(rng.uniform(-.9,.9),angle+.7+branch,78+rng.random()*17)
            branch_points = []
            for i in range(9):
                t=i/8
                p=add(mul(source,1-t),mul(tip,t))
                jitter=tuple(rng.uniform(-4,4)*math.sin(math.pi*t) for _ in range(3))
                branch_points.append(add(p,jitter))
            mesh.ribbon(branch_points,1.5,role=2)
    return mesh


def gravity():
    mesh = FieldMesh("SM_GravityFieldCandidateV3", "M_GravityFieldCandidateV3", (.6,.18,1.0))
    mesh.boundary()
    for strand in range(6):
        points=[]
        phase=strand*math.tau/6
        for i in range(65):
            t=i/64
            radius=94*(1-t)+24*t
            angle=phase+t*math.tau*.74
            z=.68*math.sin(phase*1.7+t*math.pi*1.25)
            points.append(sphere_point(z,angle,radius))
        mesh.ribbon(points,2.6,role=1)
    return mesh


def save_blender(mesh):
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version=0
    bpy.context.scene.unit_settings.system="METRIC"
    bpy.context.scene.unit_settings.scale_length=1.0
    data=bpy.data.meshes.new(mesh.name)
    data.from_pydata([mul(v,.01) for v in mesh.vertices],[],mesh.faces)
    data.update()
    obj=bpy.data.objects.new(mesh.name,data)
    bpy.context.scene.collection.objects.link(obj)
    uv=data.uv_layers.new(name="FieldRoleAndFlow")
    for face in data.polygons:
        face.use_smooth=True
        for loop in face.loop_indices:
            uv.data[loop].uv=mesh.uvs[data.loops[loop].vertex_index]
    material=bpy.data.materials.new(mesh.material)
    material.use_nodes=True
    material.diffuse_color=(*mesh.tint,1)
    nodes=material.node_tree.nodes
    nodes.clear()
    emission=nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value=(*mesh.tint,1)
    emission.inputs["Strength"].default_value=.3
    output=nodes.new("ShaderNodeOutputMaterial")
    material.node_tree.links.new(emission.outputs[0],output.inputs["Surface"])
    data.materials.append(material)
    obj["CandidateOnly"]="Blender material is a static inspection aid, not the Unreal shader."
    obj["AuthoringRadiusCm"]=RADIUS
    obj["RuntimeReferencesChanged"]=False
    bpy.context.view_layer.objects.active=obj
    obj.select_set(True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(mesh.name+".blend")))


def main():
    protected={name:sha(ROOT/name) for name in PROTECTED}
    historical_base=json.loads((OUT.parent/"CandidateReceipt.json").read_text(encoding="utf-8"))["reference_head_at_receipt"]
    old_source=json.loads((OUT.parent/"SourceReport.json").read_text(encoding="utf-8"))
    historical={}
    for path in ("Source/SpaceSurvival/Private/SSWorldActors.cpp","Source/SpaceSurvival/Public/SSContentTypes.h"):
        blob=subprocess.check_output(["git","show",historical_base+":"+path],cwd=ROOT)
        digest=hashlib.sha256(blob).hexdigest()
        assert digest==old_source["protected_sha256"][path],"Historical runtime source no longer matches immutable Git"
        historical[path]=digest
    candidates=[electrical(),gravity()]
    records=[]
    palette=[]
    for mesh in candidates:
        record=mesh.inspect()
        mesh.write_obj()
        save_blender(mesh)
        for extension in (".obj",".blend"):
            path=OUT/(mesh.name+extension)
            record.setdefault("outputs",[]).append({"file":path.name,"bytes":path.stat().st_size,"sha256":sha(path)})
        records.append(record)
        palette.extend(["newmtl "+mesh.material,"Kd "+" ".join(map(str,mesh.tint)),"d 1","illum 0",""])
    (OUT/"FieldPalette.mtl").write_text("\n".join(palette),encoding="utf-8",newline="\n")
    for name,digest in protected.items():
        assert sha(ROOT/name)==digest,"Protected input changed: "+name
    report={"status":"GENERATED_UNRENDERED_CANDIDATE_NOT_ADOPTED", "version":VERSION,
            "coordinate_system":"OBJ centimeters +X forward +Z up; Blender meters with same axes",
            "uv0_contract":{"u":"role*4+longitudinal_fraction; role0=boundary,1=primary,2=branch",
                            "v":"strand_index*4+cross_ribbon_width0to1; role0 is spherical boundary surface"},
            "material_contract":{"parameters":["Tint","Color","Emission"],"extra_inputs":["PixelNormalWS","CameraVectorWS"],"sections_per_mesh":1,
                "blend_mode":"Additive", "shading_model":"Unlit", "two_sided":True,
                "no_texture_samples":True,"no_WPO":True,"no_opacity_input":False,
                "boundary":"Role0 is a low-opacity additive spherical extent with smooth Fresnel rim; no Time modulation.",
                "clock":"Electrical flash amplitude only follows supplied Emission; Time only moves bounded low-contrast detail."},
            "meshes":records,"protected_sha256":protected,
            "historical_runtime_git":{"base":historical_base,"sha256":historical},
            "generator_sha256":sha(Path(__file__)),"palette_sha256":sha(OUT/"FieldPalette.mtl"),
            "shader_sha256":{p.name:sha(p) for p in sorted(OUT.glob("*.hlsl"))},
            "limits":["No Unreal import, shader compile, rendering, gameplay adoption or performance evidence.",
                "Broad additive cross-ribbons use derivative-filtered cores and soft outer coverage; antialiasing still requires native proof.",
                "Spherical boundary shell has additive, low-opacity falloff; interior/rock readability requires native proof.",
                "Projected area is an analytic sum, not visibility/pixel coverage or an occlusion test.",
                "Existing field clocks, damage, forces, collision, shared emissive and wormhole assets are untouched."]}
    (OUT/"SourceReport.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8",newline="\n")
    print("FIELD_CANDIDATES_SOURCE",json.dumps([{k:m[k] for k in ("name","vertices","triangles","bounds_cm")} for m in records]))


if __name__=="__main__":
    main()
