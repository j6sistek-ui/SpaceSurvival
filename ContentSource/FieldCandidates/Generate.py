"""Original field geometry candidates. Run in a fresh Blender background process.
No rendering, imports, runtime references, or files outside this directory change.
Centimetre OBJ axes match the existing Unreal FbxFactory/convert_scene=False path.
"""
import hashlib
import json
import math
from pathlib import Path
import random

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
RADIUS = 100.0
VERSION = "FieldCandidate1"
PROTECTED = [
    "ContentSource/GenerateGeometry.py",
    "ContentSource/Meshes/SM_StormRing.obj",
    "ContentSource/Meshes/SM_GravityRing.obj",
    "Content/SpaceSurvival/Meshes/SM_StormRing.uasset",
    "Content/SpaceSurvival/Meshes/SM_GravityRing.uasset",
    "Content/SpaceSurvival/Materials/M_Emissive.uasset",
    "Source/SpaceSurvival/Private/SSWorldActors.cpp",
    "Source/SpaceSurvival/Public/SSContentTypes.h",
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
        self.vertices, self.uvs, self.faces, self.paths = [], [], [], []

    def tube(self, points, width, role, closed=False, boundary=False):
        """Four-sided thin tube: one material pass, no alpha or camera-facing work.
        UV0.x=role*4+longitudinal_fraction, UV0.y=strand*2+circumference_fraction.
        Boundary role0 never disappears; primary role1 and branch role2 share Emission.
        """
        first = len(self.vertices)
        strand = len(self.paths)
        normal = None
        for i, position in enumerate(points):
            before = points[i-1] if i else points[-2] if closed else points[0]
            after = points[i+1] if i+1 < len(points) else points[1] if closed else points[-1]
            tangent = unit(sub(after, before))
            if boundary:
                normal = unit(position)
            elif normal is None:
                normal = unit(cross(tangent, (0, 0, 1) if abs(tangent[2]) < .9 else (0, 1, 0)))
            else:
                normal = unit(sub(normal, mul(tangent, dot(normal, tangent))))
            binormal = unit(cross(tangent, normal))
            t = i / (len(points)-1)
            radius = width if closed else width*(.30 + .70*math.sin(math.pi*t)**.45)
            for side in range(4):
                angle = side*math.tau/4
                offset = add(mul(normal, math.cos(angle)*radius), mul(binormal, math.sin(angle)*radius))
                vertex = add(position, offset)
                # Clamp only the visual envelope; never changes gameplay BodyRadius.
                if length(vertex) > RADIUS:
                    vertex = mul(unit(vertex), RADIUS)
                self.vertices.append(vertex)
                self.uvs.append((role*4+t, strand*2+side/4))
        for i in range(len(points)-1):
            for side in range(4):
                a = first+i*4+side
                b = first+i*4+(side+1)%4
                c = first+(i+1)*4+(side+1)%4
                d = first+(i+1)*4+side
                self.faces.extend([(a,b,c), (a,c,d)])
        if not closed:
            end = first+(len(points)-1)*4
            self.faces.extend([(first,first+2,first+1), (first,first+3,first+2),
                               (end,end+1,end+2), (end,end+2,end+3)])
        self.paths.append({"role": role, "points": len(points), "half_width_cm": width,
                           "closed": closed, "triangles": (len(points)-1)*8+(0 if closed else 4)})

    def boundary(self):
        # Three low-level great-circle filaments give exact +/-100 cm extents
        # along all axes. They remain continuous during every warning/active state.
        for axis in range(3):
            points = []
            for i in range(65):
                angle = math.tau*i/64
                p = [0.0, 0.0, 0.0]
                p[(axis+1)%3], p[(axis+2)%3] = 99.6*math.cos(angle), 99.6*math.sin(angle)
                points.append(tuple(p))
            self.tube(points, .4, role=0, closed=True, boundary=True)

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
        for a,b,c in self.faces:
            n = unit(cross(sub(self.vertices[b],self.vertices[a]),sub(self.vertices[c],self.vertices[a])))
            lines.append("vn "+" ".join(f"{x:.9f}" for x in n))
        for index,face in enumerate(self.faces):
            lines.append("f "+" ".join(f"{i+1}/{i+1}/{index+1}" for i in face))
        (OUT/(self.name+".obj")).write_text("\n".join(lines)+"\n",encoding="utf-8",newline="\n")


def electrical():
    mesh = FieldMesh("SM_ElectricalFieldCandidate", "M_ElectricalFieldCandidate", (.24,.55,1.0))
    mesh.boundary()
    rng = random.Random(73191)
    for strand in range(8):
        angle = strand*math.tau/8
        start = sphere_point(.7*math.sin(angle*1.7),angle,96)
        end = sphere_point(.6*math.cos(angle*1.3),angle+2.2,92)
        centre = sphere_point(rng.uniform(-.65,.65),angle+.8,25)
        points = []
        for i in range(13):
            t = i/12
            p = add(add(mul(start,(1-t)**2),mul(centre,2*t*(1-t))),mul(end,t*t))
            jitter = tuple(rng.uniform(-8,8)*math.sin(math.pi*t) for _ in range(3))
            points.append(add(p,jitter))
        mesh.tube(points,.65,role=1)
        for branch, index in enumerate((4,8)):
            source = points[index]
            tip = sphere_point(rng.uniform(-.9,.9),angle+.7+branch,78+rng.random()*17)
            branch_points = []
            for i in range(7):
                t=i/6
                p=add(mul(source,1-t),mul(tip,t))
                jitter=tuple(rng.uniform(-4,4)*math.sin(math.pi*t) for _ in range(3))
                branch_points.append(add(p,jitter))
            mesh.tube(branch_points,.38,role=2)
    return mesh


def gravity():
    mesh = FieldMesh("SM_GravityFieldCandidate", "M_GravityFieldCandidate", (.6,.18,1.0))
    mesh.boundary()
    for strand in range(9):
        points=[]
        phase=strand*math.tau/9
        for i in range(29):
            t=i/28
            radius=94*(1-t)+24*t
            angle=phase+t*math.tau*.74
            z=.68*math.sin(phase*1.7+t*math.pi*1.25)
            points.append(sphere_point(z,angle,radius))
        mesh.tube(points,.5,role=1)
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
                            "v":"strand_index*2+circumference_fraction; texture coordinates intentionally unwrapped"},
            "material_contract":{"parameters":["Tint","Color","Emission"],"sections_per_mesh":1,
                "blend_mode":"Opaque", "shading_model":"Unlit", "two_sided":False,
                "no_texture_samples":True,"no_WPO":True,"no_opacity_input":True,
                "boundary":"Role0 retains a nonzero brightness floor for all Emission values.",
                "clock":"Electrical flash amplitude only follows supplied Emission; Time only moves bounded low-contrast detail."},
            "meshes":records,"protected_sha256":protected,
            "generator_sha256":sha(Path(__file__)),"palette_sha256":sha(OUT/"FieldPalette.mtl"),
            "shader_sha256":{p.name:sha(p) for p in sorted(OUT.glob("*.hlsl"))},
            "limits":["No Unreal import, shader compile, rendering, gameplay adoption or performance evidence.",
                "Opaque thin tubes have open geometric gaps; no fading opacity conceals the outer boundary.",
                "Three continuous outer filaments suggest spherical extent; sparse wire geometry is not a filled force-volume visualization.",
                "Projected area is an analytic sum, not visibility/pixel coverage or an occlusion test.",
                "Existing field clocks, damage, forces, collision, shared emissive and wormhole assets are untouched."]}
    (OUT/"SourceReport.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8",newline="\n")
    print("FIELD_CANDIDATES_SOURCE",json.dumps([{k:m[k] for k in ("name","vertices","triangles","bounds_cm")} for m in records]))


if __name__=="__main__":
    main()
