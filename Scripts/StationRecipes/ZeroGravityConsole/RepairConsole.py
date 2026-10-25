"""Rebuild the inspected console's hard surfaces; preserve projected source artwork.

Hidden CPU Blender only. Original download is never overwritten. Source payloads
and generated deliverables remain private; this recipe contains no licensed art.
"""
import argparse
import datetime
import hashlib
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

EXPECTED_SOURCE = '250ae437566a4347540fa978ca0e984dac6997a5488118243935b85437dd4aa6'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert bpy.app.background, 'Use hidden background Blender.'
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--bake-only', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    source = args.source.resolve(strict=True)
    assert sha(source) == EXPECTED_SOURCE, 'Recipe is fitted only to the inspected source.'
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out/'Review.html').write_text(Path(__file__).with_name('ReviewTemplate.html').read_text(), encoding='utf-8')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 6
    scene.render.image_settings.file_format = 'PNG'
    scene.render.resolution_percentage = 100
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.import_scene.gltf(filepath=str(source))
    originals = list(scene.objects)
    original = bpy.data.collections.new('REFERENCE - original source - hidden')
    repaired = bpy.data.collections.new('REPAIRED - editable parts')
    studio = bpy.data.collections.new('STUDIO - CPU preview only')
    for col in [original, repaired, studio]:
        scene.collection.children.link(col)

    def move(obj, col):
        for old in list(obj.users_collection):
            old.objects.unlink(obj)
        col.objects.link(obj)

    def look(obj, point):
        obj.rotation_euler = (Vector(point)-obj.location).to_track_quat('-Z', 'Y').to_euler()

    for obj in originals:
        move(obj, original)
        obj.name = 'REFERENCE_' + obj.name
    # Orthographic emission projections preserve the supplied artwork. The source
    # nodes are restored before saving the hidden reference, including normal maps.
    original_links = []
    for mat in {m for obj in originals if obj.type == 'MESH' for m in obj.data.materials}:
        tree = mat.node_tree
        output = next(n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL')
        bsdf = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
        old_socket = output.inputs['Surface'].links[0].from_socket
        emit = tree.nodes.new('ShaderNodeEmission')
        base = bsdf.inputs['Base Color']
        if base.is_linked:
            tree.links.new(base.links[0].from_socket, emit.inputs['Color'])
        else:
            emit.inputs['Color'].default_value = base.default_value
        tree.links.new(emit.outputs[0], output.inputs['Surface'])
        original_links.append((tree, output, old_socket, emit))
    camera_data = bpy.data.cameras.new('Review camera')
    camera = bpy.data.objects.new('Review camera', camera_data)
    studio.objects.link(camera)
    scene.camera = camera
    camera_data.type = 'ORTHO'
    scene.view_settings.view_transform = 'Standard'
    scene.cycles.samples = 1
    scene.cycles.use_denoising = False
    # width/height are measured in the normalized input coordinates.
    captures = [
        ('SignArtwork', (0, .18, .755), (0, -1, 0), .740, .430, 1536),
        ('MonitorArtwork', (-.085, -.032, .451), (0, -.72, .69), .400, .164, 1536),
        ('ControlsArtwork', (-.030, -.198, .360), (0, -.25, .968), .640, .160, 1536),
        ('CautionArtwork', (0, -.34, .329), (0, -1, 0), .610, .044, 1536),
    ]
    for name, target, direction, width, height, resolution in captures:
        camera.location = Vector(target)+Vector(direction)*3
        look(camera, target)
        camera_data.ortho_scale = width
        scene.render.resolution_x = resolution
        scene.render.resolution_y = round(resolution*height/width)
        scene.render.filepath = str(out/(name+'.png'))
        bpy.ops.render.render(write_still=True)
    for tree, output, old_socket, emit in original_links:
        tree.links.new(old_socket, output.inputs['Surface'])
        tree.nodes.remove(emit)
    if args.bake_only:
        print('CONSOLE_ARTWORK_BAKED', flush=True)
        return
    scale = 2.1
    for obj in originals:
        obj.scale *= scale
    original.hide_render = True
    original.hide_viewport = True
    parts = []

    def material(name, color, metal=0, rough=.45):
        mat = bpy.data.materials.new(name)
        mat.diffuse_color = (*color, 1)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Base Color'].default_value = (*color, 1)
        bsdf.inputs['Metallic'].default_value = metal
        bsdf.inputs['Roughness'].default_value = rough
        return mat

    steel = material('Console - satin titanium', (.28, .30, .34), .8, .34)
    graphite = material('Console - graphite chassis', (.035, .043, .055), .65, .4)
    panel_mat = material('Console - steel blue panels', (.13, .16, .20), .65, .37)
    rubber = material('Console - rubber seals and feet', (.012, .016, .022), 0, .72)
    amber = material('Console - caution amber', (.75, .22, .025), .15, .38)
    violet = material('Console - violet indicators', (.25, .055, .56), .1, .3)
    violet.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value = (.25, .055, .56, 1)
    violet.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = .6

    def finish(obj, name, mat, bevel=0):
        obj.name = name
        move(obj, repaired)
        obj.data.materials.append(mat)
        if not obj.data.uv_layers:
            obj.data.uv_layers.new(name='ConsoleUV')
        if bevel:
            mod = obj.modifiers.new('Manufactured edge radius', 'BEVEL')
            mod.width = bevel
            mod.segments = 3
            mod.limit_method = 'ANGLE'
            mod.harden_normals = True
        mod = obj.modifiers.new('Surface normals', 'WEIGHTED_NORMAL')
        mod.keep_sharp = True
        parts.append(obj)
        return obj

    def box(name, center, dimensions, mat, bevel=.004, rotation=0):
        bpy.ops.mesh.primitive_cube_add(size=1, location=center)
        obj = bpy.context.object
        obj.dimensions = dimensions
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        obj.rotation_euler.x = rotation
        return finish(obj, name, mat, bevel)

    def rod(name, a, b, radius=.012, mat=steel, vertices=12):
        delta = Vector(b)-Vector(a)
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=delta.length,
                                          location=(Vector(a)+Vector(b))/2)
        obj = bpy.context.object
        obj.rotation_euler = delta.to_track_quat('Z', 'Y').to_euler()
        return finish(obj, name, mat, .002)

    def rail(name, x):
        # Rounded rectangular side loop, 8 samples per corner; swept closed mesh.
        y0, y1, z0, z1, radius = -.65, .55, .07, .79, .085
        path = []
        for cy, cz, start in [(y1-radius, z1-radius, 0), (y0+radius,z1-radius,90),
                              (y0+radius,z0+radius,180), (y1-radius,z0+radius,270)]:
            for k in range(9):
                angle = math.radians(start+k*90/8)
                path.append(Vector((x, cy+radius*math.cos(angle), cz+radius*math.sin(angle))))
        verts = []
        for i, p in enumerate(path):
            tangent = (path[(i+1)%len(path)]-path[i-1]).normalized()
            other = tangent.cross(Vector((1,0,0))).normalized()
            for k in range(12):
                angle = k*math.tau/12
                verts.append(p+Vector((1,0,0))*.017*math.cos(angle)+other*.017*math.sin(angle))
        faces = [(i*12+j, i*12+(j+1)%12, ((i+1)%len(path))*12+(j+1)%12,
                  ((i+1)%len(path))*12+j) for i in range(len(path)) for j in range(12)]
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
        uv=mesh.uv_layers.new(name='RailUV')
        for poly in mesh.polygons:
            ring=poly.index//12;cross=poly.index%12
            for li in poly.loop_indices:
                vi=mesh.loops[li].vertex_index;u,v=divmod(vi,12)
                uv.data[li].uv=((u if u else len(path) if ring==len(path)-1 else 0)/len(path),
                               (v if v else 12 if cross==11 else 0)/12)
        obj=bpy.data.objects.new(name,mesh);repaired.objects.link(obj)
        for poly in mesh.polygons:poly.use_smooth=True
        return finish(obj,name,steel)

    def artwork(name, center, width, height, rotation, filename, emissive):
        # Thin closed box; only the upper (+Z) face receives the baked image.
        mat = material(name+' - preserved artwork', (1,1,1), .05, .42)
        tree=mat.node_tree;bsdf=tree.nodes['Principled BSDF']
        tex=tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(out/filename));tex.image.pack()
        tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
        if emissive:
            tree.links.new(tex.outputs['Color'],bsdf.inputs['Emission Color'])
            bsdf.inputs['Emission Strength'].default_value=emissive
        obj=box(name,center,(width,height,.003),graphite,0,rotation)
        obj.data.materials.append(mat)
        for poly in obj.data.polygons:
            if poly.normal.z>.9:poly.material_index=1
            for li in poly.loop_indices:
                v=obj.data.vertices[obj.data.loops[li].vertex_index].co
                obj.data.uv_layers.active.data[li].uv=(v.x/width+.5,v.y/height+.5)
        return obj

    # Preserve the source's freestanding kiosk, knee recess, side loops and tall sign.
    box('Chassis - rear service spine',(0,.435,.43),(1.65,.20,.78),graphite,.018)
    for side in [-1,1]:
        tag='L' if side<0 else 'R'
        box('Cabinet '+tag+' - closed side',(.81*side,-.06,.43),(.21,1.02,.78),panel_mat,.025)
        box('Cabinet '+tag+' - outer access panel',(.923*side,-.06,.44),(.016,.78,.56),graphite,.01)
        box('Foot '+tag+' - floor pad',(.81*side,-.06,.025),(.25,1.07,.05),rubber,.012)
        rail('Rail '+tag+' - straight protective loop',.965*side)
        for y in [-.48,.41]:
            rod('Rail '+tag+' - standoff',(.88*side,y,.28),(.965*side,y,.28),.025,graphite)
        for z in [.34,.40,.46,.52]:
            box('Vent '+tag+' %.2f'%z,(.938*side,.08,z),(.012,.38,.022),steel,.005)
    rod('Lower rear crossbar',(-.82,.39,.13),(.82,.39,.13),.026,steel)
    box('Deck - sealed structural tray',(0,-.04,.815),(1.84,1.16,.11),graphite,.018)
    box('Deck - lower controls surround',(-.065,-.445,.88),(1.43,.39,.075),steel,.012,math.radians(8))
    artwork('Controls - source button artwork',(-.065,-.451,.922),1.344,.336,math.radians(8),'ControlsArtwork.png',.04)
    box('Deck - left wing',(-.837,-.18,.884),(.16,.78,.045),steel,.009)
    box('Deck - right service wing',(.77,-.14,.884),(.30,.86,.045),steel,.009)
    tilt=math.radians(46)
    box('Monitor - closed angled housing',(-.105,.01,1.01),(1.14,.52,.11),graphite,.022,tilt)
    box('Monitor - titanium bezel',(-.105,-.034,1.052),(1.02,.406,.042),steel,.01,tilt)
    artwork('Monitor - original purple display',(-.105,-.052,1.070),.840,.344,tilt,'MonitorArtwork.png',.18)
    for side in [-1,1]:
        box('Monitor support '+str(side),(-.105+side*.40,.13,.947),(.055,.26,.24),steel,.009)
    box('Right module - service pedestal',(.66,.07,.956),(.27,.30,.14),graphite,.014)
    box('Right module - access lid',(.66,.07,1.033),(.23,.25,.022),panel_mat,.008)
    rod('Service cable',(.72,.08,1.048),(.72,.26,1.048),.012,rubber)
    box('Right module - violet status',(.66,-.084,.97),(.12,.009,.018),violet,.003)
    # Symmetric load-bearing sign posts, a sealed rear box and a replaceable face.
    for x in [-.49,.49]:
        box('Sign post %.2f'%x,(x,.37,1.215),(.075,.085,.68),steel,.008)
        box('Sign foot %.2f'%x,(x,.37,.91),(.20,.17,.055),graphite,.008)
    box('Sign - straight outer frame',(0,.37,1.657),(1.65,.105,.940),steel,.016)
    box('Sign - rear service cover',(0,.438,1.65),(.54,.045,.22),panel_mat,.009)
    box('Sign - dark face gasket',(0,.309,1.66),(1.58,.018,.90),rubber,.008)
    artwork('Sign - original ZERO G artwork',(0,.297,1.66),1.554,.903,math.pi/2,'SignArtwork.png',.03)
    for x in [-.775,.775]:
        for z in [1.30,2.02]:
            rod('Sign frame fastener %.2f %.2f'%(x,z),(x,.307,z),(x,.294,z),.013,graphite,6)
    for z in [.26,.59]:
        box('Rear service door %.2f'%z,(0,.548,z),(1.29,.027,.28),panel_mat,.01)
        box('Rear service latch %.2f'%z,(.46,.565,z),(.10,.018,.035),steel,.004)
    box('Front fascia',(0,-.639,.80),(1.36,.035,.11),steel,.008)
    artwork('Fascia - original caution label',(0,-.660,.80),1.281,.0924,math.pi/2,'CautionArtwork.png',0)
    for side in [-1,1]:
        for k in range(3):
            box('Caution mark '+str(side)+' '+str(k),(.61*side+side*k*.04,-.660,.80),(.018,.006,.062),amber,.002)
    root=bpy.data.objects.new('ZeroGravityConsole - move whole assembly',None);repaired.objects.link(root)
    for obj in parts:obj.parent=root
    bpy.context.view_layer.update()
    deps=bpy.context.evaluated_depsgraph_get()
    corners=[o.evaluated_get(deps).matrix_world@Vector(c) for o in parts for c in o.evaluated_get(deps).bound_box]
    lo=Vector([min(p[i] for p in corners) for i in range(3)]);hi=Vector([max(p[i] for p in corners) for i in range(3)])
    target=(lo+hi)/2;extent=max(hi-lo)
    scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.view_settings.view_transform='AgX'
    scene.render.resolution_x=1100;scene.render.resolution_y=1100
    world=bpy.data.worlds.new('Neutral CPU studio');world.use_nodes=True
    world.node_tree.nodes['Background'].inputs[0].default_value=(.15,.18,.23,1)
    world.node_tree.nodes['Background'].inputs[1].default_value=.45
    scene.world=world
    ground=box('Studio floor',(0,0,-.04),(extent*200,extent*200,.08),material('Studio gray',(.11,.13,.16),0,.7),0)
    parts.remove(ground);move(ground,studio)
    for name,delta,power in [('Key',(-2,-3,4),170),('Fill',(3,-1,2),90),('Rim',(0,3,3),210)]:
        data=bpy.data.lights.new(name,'AREA');data.energy=power*extent**2;data.shape='DISK';data.size=extent*2.5
        obj=bpy.data.objects.new(name,data);studio.objects.link(obj);obj.location=target+Vector(delta)*extent;look(obj,target)
    shots=[('FrontQuarter',(1.4,-2,1.1)),('RearQuarter',(-1.4,2,1.05)),('Side',(2,.05,.40)),('Top',(0,-.01,3))]
    camera_data.ortho_scale=extent*1.43
    camera.location=target+Vector(shots[0][1])*extent;look(camera,target)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in parts:obj.select_set(True)
    root.select_set(True);bpy.context.view_layer.objects.active=parts[0]
    glb=out/'ZeroGravityConsole_Repaired.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_apply=True,
                             export_materials='EXPORT',export_cameras=False,export_lights=False,export_extras=True)
    for im in bpy.data.images:
        if im.source=='FILE' and not im.packed_file:im.pack()
    blend=out/'ZeroGravityConsole_Repaired.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
    report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(source),'source_sha256':sha(source),
            'source_scale':scale,'part_count':len(parts),'dimensions_m':list(hi-lo),'bounds_m':[list(lo),list(hi)],
            'render_device':'CPU','threads':6,'unreal_launched':False,'artwork_projections':[c[0]+'.png' for c in captures],
            'files':{'blend':{'sha256':sha(blend),'bytes':blend.stat().st_size},'glb':{'sha256':sha(glb),'bytes':glb.stat().st_size}},'renders':[]}
    for name,direction in shots:
        camera.location=target+Vector(direction)*extent;look(camera,target)
        scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
        report['renders'].append(name+'.png');(out/'RepairReport.json').write_text(json.dumps(report,indent=2))
        print('CONSOLE_VIEW_DONE',name,flush=True)
    assert sha(source)==EXPECTED_SOURCE
    print('CONSOLE_REPAIR_AUTHORED',flush=True)


if __name__=='__main__':
    main()
