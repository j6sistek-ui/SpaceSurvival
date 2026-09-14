"""Author a separate station perimeter shell; no runtime/content writes.

The shell uses metres in Blender and exports centimetres with unchanged XYZ axes.
Deck, ship and station services are transient render context, excluded from exports.
Run with installed Blender --background --factory-startup --threads 8 --python ...
"""
from pathlib import Path
import hashlib
import json
import math

import bpy
from mathutils import Vector

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'SpaceSurvival.uproject').is_file())
OUT = Path(__file__).resolve().parent
SHELL = []
MATERIALS = {}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pbr(name, color, metal, roughness, emission=0.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = (*color, 1.0)
    bsdf = material.node_tree.nodes['Principled BSDF']
    for key, value in {'Base Color': (*color, 1), 'Metallic': metal,
                       'Roughness': roughness, 'Emission Color': (*color, 1),
                       'Emission Strength': emission}.items():
        bsdf.inputs[key].default_value = value
    MATERIALS[name] = material
    return material


def projected_uv(points, normal):
    """One-metre object-local box projection; axis seams are intentional."""
    axis = max(range(3), key=lambda i: abs(normal[i]))
    sign = 1.0 if normal[axis] >= 0 else -1.0
    if axis == 0:
        return [(point.y*sign, point.z) for point in points]
    if axis == 1:
        return [(-point.x*sign, point.z) for point in points]
    return [(point.x*sign, point.y) for point in points]


def assign_base_uv(mesh):
    layer = mesh.uv_layers.get('StationBox1m') or mesh.uv_layers.new(name='StationBox1m')
    for polygon in mesh.polygons:
        points = [mesh.vertices[mesh.loops[i].vertex_index].co for i in polygon.loop_indices]
        for loop_index, uv in zip(polygon.loop_indices, projected_uv(points, polygon.normal)):
            layer.data[loop_index].uv = uv


def mesh_object(name, vertices, faces, material, bevel=0.025, shell=True):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    assign_base_uv(mesh)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    for face in mesh.polygons:
        face.use_smooth = True
    if bevel:
        modifier = obj.modifiers.new('Machined edge radius', 'BEVEL')
        modifier.width = bevel
        modifier.segments = 3
        modifier.harden_normals = True
        modifier = obj.modifiers.new('Face weighted normals', 'WEIGHTED_NORMAL')
        modifier.keep_sharp = True
    if shell:
        SHELL.append(obj)
    return obj


def box(name, center, size, material, bevel=0.025, shell=True):
    x, y, z = center
    a, b, c = (v / 2 for v in size)
    vertices = [(x+i*a, y+j*b, z+k*c) for i, j, k in
                [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
                 (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    faces = [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    return mesh_object(name, vertices, faces, material, min(bevel, .35*min(size)), shell)


def profile_x(name, x0, x1, polygon_yz, material, bevel=0.025):
    n = len(polygon_yz)
    # Orient the perimeter consistently in its local YZ plane.
    area = sum(polygon_yz[i][0]*polygon_yz[(i+1)%n][1] -
               polygon_yz[(i+1)%n][0]*polygon_yz[i][1] for i in range(n))
    if area < 0:
        polygon_yz = list(reversed(polygon_yz))
    vertices = [(x, y, z) for x in (x0, x1) for y, z in polygon_yz]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2*n))]
    faces.extend((i, (i+1)%n, (i+1)%n+n, i+n) for i in range(n))
    return mesh_object(name, vertices, faces, material, bevel)


def cylinder(name, center, radius, depth, material, axis='Z', sides=12, shell=True):
    vertices = []
    for h in (-depth/2, depth/2):
        for i in range(sides):
            a = i*math.tau/sides
            local = (radius*math.cos(a), radius*math.sin(a), h)
            if axis == 'X':
                local = (h, local[0], local[1])
            elif axis == 'Y':
                local = (local[0], h, local[1])
            vertices.append(tuple(c+v for c, v in zip(center, local)))
    faces = [tuple(reversed(range(sides))), tuple(range(sides, sides*2))]
    faces.extend((i, (i+1)%sides, (i+1)%sides+sides, i+sides) for i in range(sides))
    return mesh_object(name, vertices, faces, material, .008, shell)


def build_shell():
    structure = pbr('SSS_GraphiteAlloy', (.048, .068, .083), .72, .31)
    panel = pbr('SSS_BlueGreyPanels', (.18, .235, .265), .42, .37)
    trim = pbr('SSS_MachinedEdges', (.36, .40, .42), .84, .25)
    amber = pbr('SSS_SafetyOchre', (.70, .32, .055), .15, .41)
    dark = pbr('SSS_RecessAndRadiator', (.012, .023, .028), .65, .43)
    guide = pbr('SSS_GuideLight', (.075, .48, .63), .05, .25, 2.8)
    warm = pbr('SSS_WorkLight', (1.0, .61, .27), .0, .24, 2.2)

    # Ribs occupy the original side-column stations, with an open central roof.
    for side in (-1, 1):
        yz = [(side*y, z) for y, z in [(13.75,-.10),(14.25,-.10),(14.25,7.95),
              (11.73,10.00),(8.90,10.00),(8.90,9.55),(11.56,9.55),(13.75,7.69)]]
        for x in (-12., -6., 0., 6., 12.):
            profile_x(f'Portal rib {x:+.0f} {side}', x-.25, x+.25, yz, structure, .055)
            box(f'Rib foot shoe {x} {side}', (x, side*14.08, .15), (.88,.68,.50), trim, .045)
            box(f'Rib safety inset {x} {side}', (x-.266, side*13.99, 2.15), (.035,.40,2.5), amber, .012)
            box(f'Rib knee plate {x} {side}', (x-.275, side*13.95, 6.7), (.06,.44,.83), panel, .035)
            for z in (1.0, 3.30, 6.42, 6.98):
                cylinder(f'Rib fastener {x} {side} {z}', (x-.319,side*13.98,z), .036,.026, trim, 'X', 8)

        # Low walls retain the current inner face, open deck, and collision silhouette.
        box(f'Perimeter wall spine {side}', (0,side*14.035,1.70), (34.,.37,4.50), structure, .045)
        box(f'Perimeter top rail {side}', (0,side*13.91,3.85), (33.96,.27,.24), trim, .035)
        for index in range(6):
            x = -13.75 + index*5.5
            # Nested frames form real shadowed recesses, not a flat painted rectangle.
            box(f'Recess backing {side} {index}', (x,side*13.829,2.0), (5.17,.08,2.55), dark, .065)
            box(f'Inset cladding {side} {index}', (x,side*13.783,2.0), (4.78,.06,2.20), panel, .065)
            for edge in (-1, 1):
                box(f'Panel edge bead {side} {index} {edge}', (x+edge*2.47,side*13.731,2.0), (.045,.08,2.32), trim, .012)
            box(f'Panel service stripe {side} {index}', (x+.90,side*13.743,3.02), (1.15,.023,.075), amber, .008)
            for j in range(5):
                box(f'Panel ventilation slot {side} {index} {j}', (x-1.7+j*.22,side*13.739,1.39), (.07,.016,.65), dark, .008)
            box(f'Canopy shell {side} {index}', (x,side*11.20,9.60), (5.35,4.60,.12), panel, .038)
            box(f'Canopy edge rail {side} {index}', (x,side*8.945,9.62), (5.35,.16,.30), structure, .025)
            box(f'Canopy lamp housing {side} {index}', (x,side*11.50,9.44), (3.75,.20,.13), dark, .022)
            box(f'Canopy guide slit {side} {index}', (x,side*11.50,9.365), (3.58,.055,.025), guide, .007)
            box(f'Perimeter foot guide {side} {index}', (x,side*13.40,.08), (5.15,.12,.08), guide, .012)

        # Outside-only maintenance housings do not consume the service floor.
        for x in (-8.5, 8.5):
            box(f'Radiator housing {x} {side}', (x,side*14.69,5.85), (4.35,1.20,2.55), structure, .13)
            box(f'Radiator bed {x} {side}', (x,side*15.306,5.85), (3.93,.05,2.09), dark, .045)
            for j in range(13):
                box(f'Radiator fin {x} {side} {j}', (x-1.76+j*.293,side*15.385,5.85), (.055,.15,1.88), trim, .012)
            for edge in (-1, 1):
                box(f'Radiator corner marker {x} {side} {edge}', (x+edge*1.83,side*15.422,6.86), (.23,.024,.12), amber, .010)
            box(f'Utility conduit {x} {side}', (x,side*14.32,4.20), (4.40,.15,.21), trim, .030)
        box(f'External upper longitudinal beam {side}', (0,side*14.22,7.65), (33.90,.32,.48), structure, .060)
        box(f'Exterior lower rub strip {side}', (0,side*14.265,.10), (33.80,.12,.21), amber, .030)

    # Inbound wings occupy the original split wall: exact inner edge |Y|=7 m.
    for side in (-1, 1):
        yz = [(side*y,z) for y,z in [(7.,-.50),(14.,-.50),(14.,6.95),
                                     (13.5,7.5),(7.5,7.5),(7.,6.95)]]
        profile_x(f'Inbound wing {side}', -17.25, -16.75, yz, structure, .045)
        box(f'Inbound recessed plate {side}', (-17.275,side*10.50,3.58), (.10,5.98,5.80), panel, .085)
        box(f'Portal jamb safety {side}', (-17.35,side*7.24,3.20), (.13,.34,5.85), amber, .035)
        box(f'Portal inner light recess {side}', (-17.36,side*7.48,3.20), (.15,.12,4.45), dark, .020)
        box(f'Portal approach guide {side}', (-17.448,side*7.48,3.20), (.026,.045,4.19), guide, .009)
        for j in range(3):
            box(f'Portal broad plate recess {side} {j}', (-17.339,side*10.7,2.1+j*1.35), (.030,4.85,.77), dark, .060)
            box(f'Portal inset face {side} {j}', (-17.36,side*10.7,2.1+j*1.35), (.035,4.63,.61), panel, .045)
        box(f'Portal worklight housing {side}', (-17.37,side*10.5,6.84), (.20,2.0,.25), dark, .040)
        box(f'Portal warm guide {side}', (-17.482,side*10.5,6.84), (.028,1.77,.080), warm, .012)

    # Preserve existing low aft barrier and overhead beam underside (9.675 m).
    box('Aft low barrier', (17.,0,1.), (.30,28.,2.), structure, .040)
    box('Aft barrier cap', (17.,0,1.98), (.32,27.96,.12), trim, .025)
    for i in range(-3,4):
        x = i*4.5
        box(f'Existing overhead crossbeam {i}', (x,0,9.80), (.18,28.,.25), structure, .027)
        for side in (-1,1):
            box(f'Crossbeam support pad {i} {side}', (x,side*11.9,9.93), (.62,.65,.12), trim, .030)
    # Exterior deck edge is below the exact walking collision surface.
    for side in (-1,1):
        box(f'Underside edge girder {side}', (0,side*13.75,-.84), (33.95,.38,.54), structure, .055)
        for i in range(-2,3):
            box(f'Underside fitting {side} {i}', (i*6,side*13.95,-.83), (.95,.70,.65), panel, .070)


def evaluated_geometry(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    return evaluated, mesh


def triangle_box_overlap(vertices, center, half):
    """Separating-axis triangle/AABB test; resolves concave-rib broad-phase hits."""
    points = [vertex-Vector(center) for vertex in vertices]
    edges = [points[(i+1)%3]-points[i] for i in range(3)]
    basis = [Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))]
    axes = basis+[edges[0].cross(edges[1])]
    axes.extend(edge.cross(axis) for edge in edges for axis in basis)
    for axis in axes:
        if axis.length_squared < 1e-16:
            continue
        projected = [point.dot(axis) for point in points]
        radius = sum(abs(axis[i])*half[i] for i in range(3))
        if min(projected) > radius+1e-7 or max(projected) < -radius-1e-7:
            return False
    return True


def measure_and_export():
    bpy.context.view_layer.update()
    report = {'authored_parts':len(SHELL), 'evaluated_triangles':0, 'material_triangles':{},
              'bounds_cm':[[float('inf')]*3,[-float('inf')]*3], 'corridor_conflicting_parts':[],
              'service_envelope_conflicting_parts':[]}
    lines = ['# Station shell candidate; centimetres, +X inbound, +Z up.',
             'mtllib StationShellCandidate.mtl', 'o SM_StationShellCandidate']
    vertex_offset=0; normal_offset=0; uv_offset=0
    services=[(2,-10),(-8,-10),(-11,8.5),(0,10),(9.5,-4.5),(10,10),(-14,0)]
    for obj in SHELL:
        evaluated, mesh = evaluated_geometry(obj)
        vertices=[obj.matrix_world@v.co for v in mesh.vertices]
        lo=[min(v[a] for v in vertices) for a in range(3)]
        hi=[max(v[a] for v in vertices) for a in range(3)]
        for a in range(3):
            report['bounds_cm'][0][a]=min(report['bounds_cm'][0][a],lo[a]*100)
            report['bounds_cm'][1][a]=max(report['bounds_cm'][1][a],hi[a]*100)
        # Conservative part AABB: no shell at the open inbound wall slab above deck.
        if hi[0]>-17.25 and lo[0]<-16.75 and hi[1]>-7 and lo[1]<7 and hi[2]>-.1:
            report['corridor_conflicting_parts'].append(obj.name)
        for x,y in services:
            if hi[0]>x-.9 and lo[0]<x+.9 and hi[1]>y-.9 and lo[1]<y+.9 and hi[2]>-.1 and lo[2]<2.7:
                if any(triangle_box_overlap([vertices[i] for i in triangle.vertices], (x,y,1.30), (.9,.9,1.40)) for triangle in mesh.loop_triangles):
                    report['service_envelope_conflicting_parts'].append(obj.name)
        material=obj.data.materials[0]
        report['evaluated_triangles']+=len(mesh.loop_triangles)
        report['material_triangles'][material.name]=report['material_triangles'].get(material.name,0)+len(mesh.loop_triangles)
        lines.extend('v '+' '.join(f'{float(v[a])*100:.7f}' for a in range(3)) for v in vertices)
        normals=[]; faces=[]; uvs=[]
        normal_matrix=obj.matrix_world.to_3x3().inverted().transposed()
        for triangle in mesh.loop_triangles:
            face=[]
            points = [vertices[i] for i in triangle.vertices]
            projection = projected_uv(points, (points[1]-points[0]).cross(points[2]-points[0]))
            for loop_index, uv in zip(triangle.loops, projection):
                normal=(normal_matrix@mesh.corner_normals[loop_index].vector).normalized()
                assert normal.length > .999, (obj.name, loop_index, "Invalid exported corner normal")
                normals.append(normal)
                uvs.append(uv)
                face.append(f'{vertex_offset+mesh.loops[loop_index].vertex_index+1}/{uv_offset+len(uvs)}/{normal_offset+len(normals)}')
            faces.append('f '+' '.join(face))
        lines.extend('vn '+' '.join(f'{float(v):.7f}' for v in normal) for normal in normals)
        lines.extend('vt '+f'{uv[0]:.9f} {uv[1]:.9f}' for uv in uvs)
        lines.append('usemtl '+material.name);lines.extend(faces)
        vertex_offset+=len(vertices);normal_offset+=len(normals);uv_offset+=len(uvs)
        evaluated.to_mesh_clear()
    assert not report['corridor_conflicting_parts'],report['corridor_conflicting_parts']
    assert not report['service_envelope_conflicting_parts'],report['service_envelope_conflicting_parts']
    (OUT/'StationShellCandidate.obj').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    mtl=[]; report['materials']=[]
    for name, material in MATERIALS.items():
        node=material.node_tree.nodes['Principled BSDF']; color=list(node.inputs['Base Color'].default_value[:3]);metal=node.inputs['Metallic'].default_value;rough=node.inputs['Roughness'].default_value;emission=node.inputs['Emission Strength'].default_value
        mtl.extend(['newmtl '+name,'Kd '+' '.join(f'{v:.6f}' for v in color),f'Pm {metal:.6f}',f'Pr {rough:.6f}','Ke '+' '.join(f'{v*emission:.6f}' for v in color),'d 1.0',''])
        report['materials'].append({'name':name,'base_color':color,'metallic':metal,'roughness':rough,'emission_strength':emission})
    (OUT/'StationShellCandidate.mtl').write_text('\n'.join(mtl),encoding='utf-8',newline='\n')
    # Only authored shell and material nodes; no ship, hero, floor, services, lights or camera.
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'StationShellCandidate.blend'),compress=True)
    return report


def add_context():
    structure=MATERIALS['SSS_GraphiteAlloy'];panel=MATERIALS['SSS_BlueGreyPanels'];amber=MATERIALS['SSS_SafetyOchre'];guide=MATERIALS['SSS_GuideLight']
    box('CONTEXT exact original collision deck', (0,0,-.60), (34,28,1), structure, 0,False)
    floor=bpy.data.materials.new('CONTEXT existing deck texture');floor.use_nodes=True
    nodes=floor.node_tree.nodes;links=floor.node_tree.links;bsdf=nodes['Principled BSDF'];bsdf.inputs['Metallic'].default_value=.5;bsdf.inputs['Roughness'].default_value=.59
    image=nodes.new('ShaderNodeTexImage');image.image=bpy.data.images.load(str(ROOT/'ContentSource/ThirdParty/PolyHaven/MetalPlate/metal_plate_diff_2k.png'))
    tex=nodes.new('ShaderNodeTexCoord');scale=nodes.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs[3].default_value=2.0;links.new(tex.outputs['Object'],scale.inputs[0]);links.new(scale.outputs['Vector'],image.inputs['Vector'])
    hue=nodes.new('ShaderNodeHueSaturation');hue.inputs['Saturation'].default_value=.15;hue.inputs['Value'].default_value=.42;links.new(image.outputs['Color'],hue.inputs['Color']);links.new(hue.outputs['Color'],bsdf.inputs['Base Color'])
    for x in range(6):
        for y in range(6):
            box(f'CONTEXT floor plate {x} {y}',(-13.75+x*5.5,-11.25+y*4.5,-.08),(5.35,4.35,.015),floor,0,False)
    for i in range(-3,4):
        for side in (-1,1):
            box(f'CONTEXT existing approach strip {i} {side}',(i*3.5,side*6.5,-.05),(2.4,.12,.04),guide,.01,False)
    service_positions=[(2,-10),(-8,-10),(-11,8.5),(0,10),(9.5,-4.5),(10,10),(-14,0)]
    for i,(x,y) in enumerate(service_positions):
        # Exact source console box sizes/offsets, with neutral contextual materials.
        for j,(offset,size,mat) in enumerate([((0,0,.10),(.90,.60,.20),structure),((-.12,0,.50),(.42,.42,.80),structure),((0,0,.98),(.86,.62,.15),amber),((.04,0,1.07),(.67,.44,.03),guide)]):
            box(f'CONTEXT service {i} part {j}',(x+offset[0],y+offset[1],offset[2]),size,mat,0,False)
    for side in (-1,1):
        box(f'CONTEXT bay stripe {side}',(8.5,side*3.9,-.04),(7.7,.09,.015),amber,0,False)
        box(f'CONTEXT bay border {side}',(4.6 if side<0 else 12.4,0,-.04),(.09,7.9,.015),amber,0,False)
    # Append existing hull only as transient scale context; no model/animation editing.
    with bpy.data.libraries.load(str(ROOT/'ContentSource/AcornShipGripFit/AcornShipGripFit.blend'),link=False) as (source,target):
        target.objects=list(source.objects)
    for obj in target.objects:
        if obj is not None and obj.type in {'MESH','CURVE'} and not obj.name.startswith(('Studio','Key','Cold','Top','Forward')):
            bpy.context.scene.collection.objects.link(obj)
            obj.location.x+=8.5;obj.location.z+=2.2
    box('CONTEXT ship cradle',(8.5,0,1.38),(3.7,1.35,.16),structure,.02,False)
    for x in (7.2,9.7):
        for y in (-.55,.55):box(f'CONTEXT cradle leg {x} {y}',(x,y,.75),(.22,.22,1.1),structure,.01,False)


def render_views(report):
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=36;scene.cycles.use_denoising=True
    scene.render.threads_mode='FIXED';scene.render.threads=8
    scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
    scene.world=bpy.data.worlds.new('Preview dark space');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.055,.083,.12,1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.40
    for name,position,energy,size,color,target in [
        ('Exterior key',(-25,-20,25),38000,20,(1,.82,.66),(0,0,3)),
        ('Exterior rim',(10,20,22),44000,16,(.59,.75,1),(0,0,4)),
        ('Inbound fill',(-32,6,9),22000,14,(.72,.85,1),(-7,0,4)),
        ('Interior work',(-4,-7,8.3),9500,7,(1,.72,.44),(0,0,0)),
        ('Interior fill',(7,8,8.3),11000,8,(.63,.83,1),(4,0,0))]:
        data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size;data.color=color
        light=bpy.data.objects.new(name,data);scene.collection.objects.link(light);light.location=position;light.rotation_euler=(Vector(target)-light.location).to_track_quat('-Z','Y').to_euler()
    camera_data=bpy.data.cameras.new('Candidate review camera');camera=bpy.data.objects.new('Candidate review camera',camera_data);scene.collection.objects.link(camera);scene.camera=camera;camera_data.clip_end=300
    views=[('Approach',(-47,-7,9),(0,0,3.3),38),('Interior',(-14,-5,2.1),(8,4.5,3.8),24),('Wide',(-37,-39,26),(0,0,3.3),43)]
    report['views']=[]
    for name,position,target,lens in views:
        camera.location=position;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera_data.lens=lens
        scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
        report['views'].append({'file':name+'.png','camera_m':position,'target_m':target,'lens_mm':lens,'dimensions':[1600,1000],'sha256':sha(OUT/(name+'.png'))})


def main():
    protected_paths=[ROOT/'Source/SpaceSurvival/Private/SSStation.cpp',ROOT/'Source/SpaceSurvival/Public/SSStation.h',ROOT/'model-rigged.glb',ROOT/'ContentSource/AcornShipGripFit/AcornShipGripFit.blend',ROOT/'ContentSource/ThirdParty/PolyHaven/MetalPlate/metal_plate_diff_2k.png']
    protected={p:sha(p) for p in protected_paths}
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0
    bpy.context.scene.unit_settings.system='METRIC'
    build_shell();report=measure_and_export();add_context();render_views(report)
    assert all(sha(p)==h for p,h in protected.items()),'A referenced source changed during candidate generation'
    report.update({'status':'SOURCE_ONLY_STATION_SHELL_CANDIDATE_NOT_IMPORTED_OR_ACCEPTED','blender':bpy.app.version_string,'render_device':'Cycles CPU / 8 threads / 36 samples','source_sha256':sha(Path(__file__)),'protected_sources':{p.relative_to(ROOT).as_posix():h for p,h in protected.items()},'deck_contract_cm':{'size':[3400,2800,100],'center':[0,0,-60],'collision_top_z':-10,'exported':False},'corridor_contract_cm':{'x_slab':[-1725,-1675],'y_open':[-700,700],'z_open_above':-10,'upper_limit':None,'test':'Conservative evaluated part AABB rejection in the open inbound slab above deck; no lintel added.'},'service_envelope_test':'No evaluated shell triangle overlaps a 180x180x280 cm envelope (AABB broad phase, triangle/AABB separating-axis narrow phase) around any of the seven unchanged service anchors. Mica/props remain context-owned, unchanged.','collision':'Candidate exports no collision mesh. Runtime would retain existing blocking components and use this as NoCollision presentation only. No runtime integration occurred.','limits':['Authored shell only; no room, service, mechanic, landing path, Mica or character change.','Reference ship and exact-sized console boxes are transient context and excluded from .blend and OBJ; no pilot is embedded.','Deck texture appears only in transient context, with approximate Blender tint; existing Unreal shader and runtime lighting are not reproduced exactly.','Material bevels/PBR values are source-authoring evidence; no native lighting, shadows, LOD, draw cost, collision or first-person/interact visibility verification.','No owner acceptance or near-alpha-quality claim.'], 'outputs':[{'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(OUT.iterdir()) if p.suffix in {'.blend','.obj','.mtl','.png'}]})
    (OUT/'Report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('STATION_SHELL_SOURCE_DONE',json.dumps({k:report[k]for k in ['authored_parts','evaluated_triangles','bounds_cm','corridor_conflicting_parts','service_envelope_conflicting_parts']}))


if __name__=='__main__':
    main()
