"""Original low-cost machined berth perimeter. Blender background export only.

Usage: blender.exe --background --python Scripts/BuildOutpostPadTrim.py -- OUTPUT
Builds one30m-radius player and one14m-radius visitor FBX in metres. No purchased
geometry is changed. Pure geometry() and audit() work without importing Blender.
"""
import hashlib
import json
import math
from pathlib import Path
import sys

SEGMENTS = 256
SLOTS = ('PadMetal', 'PadBezel', 'PadCyanLens', 'PadWarmGuide')
SPECS = (('SM_OutpostPadTrim_Player',3000.,500.,64,32),
         ('SM_OutpostPadTrim_Visitor',1400.,500.,32,16))


def geometry(name, radius, width, lamps, guides):
    vertices, faces, materials, smooth = [], [], [], []
    inner = radius-width

    def sector(profile, start, end, steps, slots, caps=True):
        # Separate surface strips preserve hard profile edges; only angular
        # normals are smoothed. Deck faces remain flat with planar tiled UVs.
        area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(profile,profile[1:]+profile[:1]))
        if area>0:
            if isinstance(slots,(tuple,list)):
                slots=[slots[(len(profile)-2-j)%len(profile)] for j in range(len(profile))]
            profile=list(reversed(profile))
        for edge in range(len(profile)):
            ra,za = profile[edge]
            rb,zb = profile[(edge+1)%len(profile)]
            base = len(vertices)
            for step in range(steps+1):
                angle = start+(end-start)*step/steps
                vertices.extend([(ra*math.cos(angle),ra*math.sin(angle),za),
                                 (rb*math.cos(angle),rb*math.sin(angle),zb)])
            for step in range(steps):
                i=base+2*step
                faces.append((i,i+1,i+3,i+2))
                materials.append(slots[edge] if isinstance(slots,(tuple,list)) else slots)
                smooth.append(abs(za-zb)>.00001)
        if caps:
            for angle,reverse in ((start,True),(end,False)):
                ids=[]
                for r,z in profile:
                    ids.append(len(vertices))
                    vertices.append((r*math.cos(angle),r*math.sin(angle),z))
                faces.append(tuple(reversed(ids)) if reverse else tuple(ids))
                materials.append(1);smooth.append(False)

    profile=[(inner,-8),(inner,.65),(radius-80,.65),(radius-75,-5),
             (radius-45,-5),(radius-40,.65),(radius-2,.65),(radius,-1.35),
             (radius,-40),(radius-20,-40),(radius-20,-8)]
    slots=(1,0,1,1,1,0,0,1,1,1,1)
    panel_count=32
    seam_angle=1./radius  # 1cm physical expansion joint at the outer rim.
    for i in range(panel_count):
        a,b=i*math.tau/panel_count,(i+1)*math.tau/panel_count
        sector(profile,a+seam_angle/2,b-seam_angle/2,SEGMENTS//panel_count,slots)
        # Shallow dark gasket lies above underlying deckZ.5 but below trimZ.65.
        sector([(inner,.55),(radius-82,.55),(radius-82,.57),(inner,.57)],
               a-seam_angle/2,a+seam_angle/2,1,1)

    # Ten-centimetre lens inside a31cm physical dark channel. Lens topZ-2.5
    # is recessed3.15cm below deck, wholly outside retained tiles(maxR-85).
    lens=[(radius-65,-3),(radius-55,-3),(radius-55,-2.5),(radius-65,-2.5)]
    for i in range(lamps):
        mid=(i+.5)*math.tau/lamps
        half=(math.tau/lamps-8./radius)/2
        sector(lens,mid-half,mid+half,SEGMENTS//lamps,2)

    # Short, fine warm guide inserts along the inner band. Dark raised bezel
    # topsZ.85; recessed2cm-wide lensZ.75. No new walking obstruction.
    guide_radius=inner+28
    for i in range(guides):
        mid=(i+.5)*math.tau/guides
        half=45./guide_radius
        sector([(guide_radius-4,.65),(guide_radius-4,.85),
                (guide_radius-1.5,.85),(guide_radius-1.5,.68),
                (guide_radius+1.5,.68),(guide_radius+1.5,.85),
                (guide_radius+4,.85),(guide_radius+4,.65)],mid-half,mid+half,2,1)
        sector([(guide_radius-1,.70),(guide_radius+1,.70),
                (guide_radius+1,.75),(guide_radius-1,.75)],mid-half+.001,mid+half-.001,2,3)
    return {'name':name,'radius_cm':radius,'width_cm':width,'segments':SEGMENTS,
            'vertices_cm':vertices,'faces':faces,'material_indices':materials,
            'smooth_faces':smooth,'material_slots':SLOTS,'lamp_count':lamps,'guide_count':guides}


def audit(data):
    vertices=data['vertices_cm']
    triangles=sum(len(f)-2 for f in data['faces'])
    r=data['radius_cm'];inner=r-data['width_cm']
    radii=[math.hypot(p[0],p[1]) for p in vertices]
    failures=[]
    if min(radii)<inner-.001 or max(radii)>r+.001:failures.append('Mesh escapes annular footprint')
    if max(p[2] for p in vertices)>.87 or min(p[2] for p in vertices)<-40.001:failures.append('Height envelope changed')
    if triangles>11000:failures.append('Triangle budget exceeded')
    for indices in data['faces']:
        if len(set(indices))!=len(indices):failures.append('Degenerate face indices')
    return {'mesh':data['name'],'vertices':len(vertices),'triangles':triangles,
            'radius_cm':r,'inner_radius_cm':inner,'width_cm':data['width_cm'],
            'segments':SEGMENTS,'maximum_circle_chord_error_cm':r*(1-math.cos(math.pi/SEGMENTS)),
            'min_z_cm':min(p[2] for p in vertices),'max_z_cm':max(p[2] for p in vertices),
            'main_deck_z_cm':.65,'outer_lens_width_cm':10.,'outer_lens_top_z_cm':-2.5,
            'material_slots':SLOTS,'failures':failures}


def build(output):
    import bpy
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene
    scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1.
    result=[]
    for spec in SPECS:
        data=geometry(*spec);proof=audit(data)
        if proof['failures']:raise RuntimeError('; '.join(proof['failures']))
        mesh=bpy.data.meshes.new(data['name'])
        mesh.from_pydata([(x/100,y/100,z/100) for x,y,z in data['vertices_cm']],[],data['faces'])
        mesh.update()
        for name in SLOTS:
            material=bpy.data.materials.get(name) or bpy.data.materials.new(name)
            mesh.materials.append(material)
        for polygon,slot,smooth in zip(mesh.polygons,data['material_indices'],data['smooth_faces']):
            polygon.material_index=slot;polygon.use_smooth=smooth
        uv=mesh.uv_layers.new(name='UVMap')
        for polygon in mesh.polygons:
            zz=[mesh.vertices[i].co.z for i in polygon.vertices]
            flat=max(zz)-min(zz)<1e-6
            angles=[math.atan2(mesh.vertices[i].co.y,mesh.vertices[i].co.x) for i in polygon.vertices]
            wraps=max(angles)-min(angles)>math.pi
            for index in polygon.loop_indices:
                p=mesh.vertices[mesh.loops[index].vertex_index].co
                angle=math.atan2(p.y,p.x)
                if wraps and angle<0:angle+=math.tau
                uv.data[index].uv=(p.x/4,p.y/4) if flat else (angle*data['radius_cm']/400,p.z)
        color=mesh.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
        for value in color.data:value.color=(1.,1.,1.,1.)
        ob=bpy.data.objects.new(data['name'],mesh);bpy.context.collection.objects.link(ob)
        bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
        fbx=output/(data['name']+'.fbx')
        bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'MESH'},
            axis_forward='-Y',axis_up='Z',global_scale=1.,apply_unit_scale=True,
            bake_anim=False,add_leaf_bones=False,mesh_smooth_type='FACE',use_triangles=True)
        mesh.calc_loop_triangles()
        proof.update(fbx=fbx.name,fbx_sha256=hashlib.sha256(fbx.read_bytes()).hexdigest(),
                     exported_triangles=len(mesh.loop_triangles))
        result.append(proof)
        bpy.data.objects.remove(ob,do_unlink=True)
    report={'generator':'BuildOutpostPadTrim.py','source':'Original machined geometry; no vendor mesh derivation',
            'units':'Blender metres, FBX centimetres','meshes':result}
    (output/'pad-trim-geometry.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('OUTPOST_PAD_TRIM_EXPORTED '+json.dumps(result))


if __name__=='__main__':
    build(sys.argv[sys.argv.index('--')+1])
