"""CPU-only, standalone curved-bench source repair. Never imports into Unreal.

Rebuilds distorted hard surfaces and upholstery to the measured source profile.
The original is retained, hidden, in the editable blend; exported GLB contains
only the repaired assembly. All outputs are private under SourceAssets.
Run with the installed Blender: --background --factory-startup --disable-autoexec
--threads 6 --python RepairBench.py -- --source INPUT.glb --output OUTPUT_FOLDER.
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


def args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    return parser.parse_args(sys.argv[sys.argv.index('--') + 1:])


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert bpy.app.background, 'Hidden background Blender only.'
    opt = args()
    source = opt.source.resolve(strict=True)
    out = opt.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    source_hash = sha(source)
    assert source_hash == '5bc9af8b78567772dfcd7bf99e708f4ad2315e4345823ac5f9f6feddfbdd28d4', \
        'This fitted recipe is only for the inspected curved-sofa download.'
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.0
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 6
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'AgX'
    scene.render.film_transparent = False
    bpy.context.preferences.filepaths.save_version = 0

    original = bpy.data.collections.new('REFERENCE - original source - hidden')
    repaired = bpy.data.collections.new('REPAIRED - editable parts')
    studio = bpy.data.collections.new('STUDIO - CPU preview only')
    for collection in (original, repaired, studio):
        scene.collection.children.link(collection)

    bpy.ops.import_scene.gltf(filepath=str(source))
    reference_objects = list(scene.objects)
    # Source is normalized, not seat-sized. The 0.125 high seat becomes 45 cm.
    scale = 3.6
    center = (-0.3726036985, -0.3703377695)
    start, end = math.radians(-8), math.radians(99)

    def move_to(obj, collection):
        for old in list(obj.users_collection):
            old.objects.unlink(obj)
        collection.objects.link(obj)

    for obj in reference_objects:
        move_to(obj, original)
        obj.scale *= scale
        obj.name = 'REFERENCE_' + obj.name
    original.hide_render = True
    original.hide_viewport = True

    def material(name, color, metal, roughness):
        mat = bpy.data.materials.new(name)
        mat.diffuse_color = (*color, 1)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Base Color'].default_value = (*color, 1)
        bsdf.inputs['Metallic'].default_value = metal
        bsdf.inputs['Roughness'].default_value = roughness
        # Plain PBR values are deliberately portable to GLB; no lost shader nodes.
        return mat

    leather = material('Bench - black leather', (.013, .015, .022), .0, .43)
    upholstery = material('Bench - deep violet upholstery', (.043, .023, .078), .05, .49)
    shell = material('Bench - indigo enamel shell', (.037, .021, .080), .62, .29)
    silver = material('Bench - brushed titanium trim', (.32, .36, .43), .92, .30)
    dark = material('Bench - graphite chassis', (.022, .027, .038), .72, .40)
    rubber = material('Bench - nonmarking feet', (.009, .011, .014), .0, .75)
    seam = material('Bench - leather piping', (.028, .029, .041), .0, .49)
    parts = []

    def arc(name, profile, mat, lo=start, hi=end, segments=88, bevel=0):
        """Closed profile in (radius,height), swept around source-fitted center."""
        n = len(profile)
        vertices = []
        for j in range(segments + 1):
            angle = lo + (hi - lo) * j / segments
            for radius, height in profile:
                vertices.append(((center[0] + radius * math.cos(angle)) * scale,
                                 (center[1] + radius * math.sin(angle)) * scale,
                                 height * scale))
        faces = []
        for j in range(segments):
            for k in range(n):
                faces.append((j*n+k, j*n+(k+1)%n, (j+1)*n+(k+1)%n, (j+1)*n+k))
        faces.extend([tuple(range(n-1, -1, -1)), tuple(segments*n+k for k in range(n))])
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(name, mesh)
        repaired.objects.link(obj)
        mesh.materials.append(mat)
        # UVs follow arc length and profile distance, not AI-generated smears.
        uv = mesh.uv_layers.new(name='BenchUV')
        lengths = [0.0]
        for a, b in zip(profile, profile[1:]):
            lengths.append(lengths[-1] + math.dist(a, b))
        perimeter = lengths[-1] + math.dist(profile[-1], profile[0])
        for poly in mesh.polygons:
            strip = poly.index < segments * n
            last_cross = strip and poly.index % n == n - 1
            for li in poly.loop_indices:
                vi = mesh.loops[li].vertex_index
                ring, cross = divmod(vi, n)
                if strip:
                    v = 1.0 if last_cross and cross == 0 else lengths[cross]/perimeter
                    uv.data[li].uv = (ring/segments, v)
                else:
                    # Project end caps into the profile plane; avoid zero-area UVs.
                    r, z = profile[cross]
                    rmin, rmax = min(p[0] for p in profile), max(p[0] for p in profile)
                    zmin, zmax = min(p[1] for p in profile), max(p[1] for p in profile)
                    uv.data[li].uv = ((r-rmin)/(rmax-rmin), (z-zmin)/(zmax-zmin))
            poly.use_smooth = True
        if bevel:
            mod = obj.modifiers.new('Soft manufactured edges', 'BEVEL')
            mod.width = bevel * scale
            mod.segments = 3
            mod.limit_method = 'ANGLE'
            mod.angle_limit = math.radians(25)
            mod.harden_normals = True
        wn = obj.modifiers.new('Balanced surface normals', 'WEIGHTED_NORMAL')
        wn.keep_sharp = True
        parts.append(obj)
        return obj

    def rect(r1, r2, z1, z2):
        return [(r1,z1),(r2,z1),(r2,z2),(r1,z2)]

    def tube(name, radius, height, thickness, mat, lo=start, hi=end):
        return arc(name, [(radius+thickness*math.cos(k*math.tau/12),
                           height+thickness*math.sin(k*math.tau/12)) for k in range(12)],
                   mat, lo, hi)

    # Same crescent and raised rail; clean closed parts replace the torn source.
    arc('Base - structural deck', rect(.591,.841,.057,.081), dark, bevel=.003)
    arc('Base - front titanium edge', rect(.589,.599,.071,.085), silver, bevel=.002)
    arc('Base - outer indigo skirt', rect(.817,.841,.023,.075), shell, bevel=.003)
    arc('Seat - continuous rounded black cushion',
        [(.597,.085),(.771,.085),(.781,.094),(.777,.113),(.764,.123),
         (.737,.126),(.620,.125),(.600,.119),(.591,.106),(.592,.093)], leather, bevel=.002)
    tube('Seat - front piping', .596,.112,.0014,seam)
    # Reclined profile follows the original; rear panels are now evenly surfaced.
    arc('Back - structural indigo shell',
        [(.817,.078),(.839,.078),(.876,.146),(.880,.186),(.856,.216),
         (.837,.235),(.824,.235),(.843,.211),(.858,.180),(.854,.148)], shell, bevel=.0018)
    back_profile=[(.765,.120),(.777,.119),(.813,.218),(.817,.229),
                  (.805,.236),(.793,.231),(.778,.208),(.765,.171),(.757,.137)]
    boundaries=[start, math.radians(28), math.radians(64), end]
    for i,(lo,hi) in enumerate(zip(boundaries,boundaries[1:]),1):
        arc('Back cushion %02d - violet'%i,back_profile,upholstery,lo+.005,hi-.005,32,.002)
    for i,ang in enumerate(boundaries[1:-1],1):
        arc('Back divider %02d - titanium'%i,
            [(.753,.135),(.760,.131),(.801,.228),(.818,.239),(.823,.232),(.808,.219)],
            silver,ang-.009,ang+.009,2,.0012)
    tube('Back - upper titanium seam',.836,.231,.0024,silver)
    tube('Back - lower titanium seam',.875,.146,.0022,silver)
    tube('Rail - continuous smooth crown',.841,.255,.0042,silver)
    # Regular straight supports beneath the top rail, instead of bent spikes.
    for i,angle in enumerate([-5,12,31,50,69,88,96],1):
        a=math.radians(angle)
        arc('Rail stanchion %02d'%i,rect(.8385,.8435,.231,.253),silver,a-.0028,a+.0028,1,.0007)
    # End arm pads align with the original open ends.
    for i,a in enumerate([start+.006,end-.006],1):
        arc('End arm %02d - graphite frame'%i,
            [(.596,.086),(.775,.086),(.815,.221),(.803,.224),(.759,.127),(.596,.127)],
            dark,a-.012,a+.012,2,.0018)
        arc('End arm %02d - leather pad'%i,rect(.609,.759,.124,.137),leather,a-.013,a+.013,2,.004)
    for i,angle in enumerate([-5,15,35,55,75,96],1):
        a=math.radians(angle)
        arc('Foot %02d - load support'%i,rect(.615,.818,.008,.058),dark,a-.013,a+.013,2,.003)
        arc('Foot %02d - rubber pad'%i,rect(.609,.822,.000,.009),rubber,a-.016,a+.016,2,.0015)
        arc('Foot %02d - shell insert'%i,rect(.817,.845,.015,.058),shell,a-.014,a+.014,2,.002)

    root = bpy.data.objects.new('CURVED BENCH - 3.6 m source scale',None)
    repaired.objects.link(root)
    root['source_file']=source.name
    root['source_sha256']=source_hash
    root['repair']='Source-fitted closed hard surfaces, rail supports and independent PBR parts; no Unreal import.'
    root['seat_height_m']=.45
    for obj in parts:
        obj.parent=root

    corners=[obj.matrix_world@Vector(c) for obj in parts for c in obj.bound_box]
    lo=Vector(tuple(min(p[k] for p in corners) for k in range(3)))
    hi=Vector(tuple(max(p[k] for p in corners) for k in range(3)))
    target=(lo+hi)/2
    extent=max(hi-lo)
    world=bpy.data.worlds.new('Neutral CPU studio');world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(.15,.18,.23,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45
    scene.world=world
    bpy.ops.mesh.primitive_plane_add(size=extent*200,location=(target.x,target.y,-.014))
    ground=bpy.context.object;ground.name='Studio ground';move_to(ground,studio)
    ground.data.materials.append(material('Studio neutral',(.12,.14,.17),0,.65))
    for name,pos,power,size in [('Key',(-2,-3,4),160,3),('Fill',(3,-1,2),90,3),('Rim',(0,3,3),220,2)]:
        data=bpy.data.lights.new(name,'AREA');data.energy=power*extent**2;data.shape='DISK';data.size=size*extent
        obj=bpy.data.objects.new(name,data);studio.objects.link(obj)
        obj.location=target+Vector(pos)*extent;obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()
    data=bpy.data.cameras.new('Review camera');cam=bpy.data.objects.new('Review camera',data);studio.objects.link(cam)
    scene.camera=cam;data.type='ORTHO';data.ortho_scale=extent*1.55
    shots=[('FrontQuarter',(1,-1.4,1.0)),('RearQuarter',(-1,1.4,.9)),('Side',(1,0,.40)),('Top',(0,0,2))]
    cam.location=target+Vector(shots[0][1])*extent*2
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.select_all(action='DESELECT')
    for obj in parts: obj.select_set(True)
    root.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]
    # GLB contains only repaired parts and basic PBR materials, never the reference/studio.
    glb=out/'CurvedBench_Repaired.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,
                              export_apply=True,export_materials='EXPORT',export_cameras=False,
                              export_lights=False,export_extras=True)
    # Keep editable modifiers and hidden original in the blend.
    for image in bpy.data.images:
        if image.source=='FILE' and not image.packed_file: image.pack()
    blend=out/'CurvedBench_Repaired.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
    report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(source),
            'source_sha256':source_hash,'scale_from_normalized_source':scale,'arc_center_source':center,
            'arc_degrees':[-8,99],'dimensions_m':list(hi-lo),'seat_top_m':.45,
            'part_count':len(parts),'render_device':'CPU','threads':6,'renders':[],
            'unreal_launched':False,'source_unchanged':sha(source)==source_hash,
            'files':{'blend':{'path':str(blend),'sha256':sha(blend)},'glb':{'path':str(glb),'sha256':sha(glb)}}}
    for name,direction in shots:
        cam.location=target+Vector(direction)*extent*2
        cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(out/(name+'.png'))
        bpy.ops.render.render(write_still=True)
        report['renders'].append(name+'.png')
        (out/'RepairReport.json').write_text(json.dumps(report,indent=2))
        print('BENCH_VIEW_DONE',name,flush=True)
    assert report['source_unchanged']
    print('BENCH_REPAIR_AUTHORED',flush=True)


if __name__=='__main__':
    main()
