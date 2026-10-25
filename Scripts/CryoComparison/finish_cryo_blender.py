"""Non-destructive, shared finish for four source GLBs; native UE VFX authored separately."""
import bpy, json, math, struct, hashlib, sys
from pathlib import Path
from mathutils import Vector, Matrix

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs'/'Cryo_Comparison'
SRC=Path(r'C:\Users\j6sis\Downloads\CRYO')
SHARED={k:str(OUT/'shared'/f'T_Cryo_{v}.png') for k,v in [('status','Status'),('console','Console'),('holo','Holo'),('frost','Frost'),('mist','Mist')]}
NAMES=['Cybernetic_Cat','Futuristic_Cat','Futuristic_Fox','Meshy_Raccoon']
GLASS=[(1.42,.77,2.88,-.87,-.43),(1.52,.60,2.83,-.88,-.22),(1.28,.80,2.86,-.91,-.72),(1.56,.64,2.84,-1.07,-.47)]
SCREENS=[
 [[(127,611),(238,611),(226,674),(119,674)],[(404,611),(495,612),(508,673),(417,674)]],
 [[(70,651),(160,651),(145,707),(59,705)],[(472,655),(556,654),(571,711),(481,709)]],
 [[(151,605),(223,607),(211,671),(138,669)],[(390,604),(477,602),(487,665),(400,667)]],
 [[(68,647),(158,650),(145,708),(57,704)],[(476,650),(558,648),(575,709),(485,711)]]]

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def extract_maps(path,dest):
    raw=path.read_bytes(); offset=12; js=None; binary=None
    while offset<len(raw):
        size,kind=struct.unpack_from('<II',raw,offset);chunk=raw[offset+8:offset+8+size];offset+=8+size
        if kind==0x4e4f534a: js=json.loads(chunk)
        elif kind==0x004e4942: binary=chunk
    mat=js['materials'][0];pbr=mat['pbrMetallicRoughness'];result={}
    for key,info in [('base_color',pbr['baseColorTexture']),('normal',mat.get('normalTexture')),('orm',pbr.get('metallicRoughnessTexture'))]:
        if info is None:continue
        im=js['images'][js['textures'][info['index']]['source']];bv=js['bufferViews'][im['bufferView']]
        ext='.png' if im.get('mimeType')=='image/png' else '.jpg'
        p=dest/f'T_{key}{ext}';start=bv.get('byteOffset',0);p.write_bytes(binary[start:start+bv['byteLength']]);result[key]=str(p)
    return result

def mesh_object(name,verts,faces,uvs,material):
    m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update()
    o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o)
    layer=m.uv_layers.new(name='UVMap')
    for f in m.polygons:
        for li in f.loop_indices:layer.data[li].uv=uvs[m.loops[li].vertex_index]
    m.materials.append(material)
    for f in m.polygons:f.use_smooth=True
    return o

def image_mat(name,path,alpha=1,emission=0):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.38
    im=m.node_tree.nodes.new('ShaderNodeTexImage');im.image=bpy.data.images.load(str(path),check_existing=True)
    m.node_tree.links.new(im.outputs['Color'],p.inputs['Base Color'])
    if emission:
        m.node_tree.links.new(im.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=emission
    if alpha<1:
        mult=m.node_tree.nodes.new('ShaderNodeMath');mult.operation='MULTIPLY';mult.inputs[1].default_value=alpha
        m.node_tree.links.new(im.outputs['Alpha'],mult.inputs[0]);m.node_tree.links.new(mult.outputs[0],p.inputs['Alpha'])
        m.surface_render_method='DITHERED'
    return m

def simple_mat(name,color,metal=0,rough=.4,emission=0,alpha=1):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF')
    for n,val in [('Base Color',(*color,1)),('Metallic',metal),('Roughness',rough),('Alpha',alpha),('Emission Color',(*color,1)),('Emission Strength',emission)]:p.inputs[n].default_value=val
    if alpha<1:m.surface_render_method='DITHERED'
    return m

def panel(name,center,w,h,mat):
    x,y,z=center
    return mesh_object(name,[(x-w/2,y,z-h/2),(x+w/2,y,z-h/2),(x+w/2,y,z+h/2),(x-w/2,y,z+h/2)],[(0,1,2,3)],[(0,0),(1,0),(1,1),(0,1)],mat)

def curved(name,fit,mat,offset=0):
    w,b,t,front,edge=fit; nu,nv=32,40;r=.16;verts=[];uv=[];faces=[]
    for j in range(nv+1):
        v=j/nv;z=b+(t-b)*v;dz=min(z-b,t-z)
        half=w/2 if dz>=r else w/2-r+math.sqrt(max(0,r*r-(r-dz)**2))
        for i in range(nu+1):
            u=i/nu;x=(u-.5)*2*half;y=front+(edge-front)*(x/(w/2))**2+offset
            verts.append((x,y,z));uv.append((u,v))
    for j in range(nv):
        for i in range(nu):
            a=j*(nu+1)+i;faces.append((a,a+1,a+nu+2,a+nu+1))
    return mesh_object(name,verts,faces,uv,mat)

def curved_holo(fit,mat):
    w,b,t,front,edge=fit;verts=[];uv=[];faces=[];n=24
    for j in range(n+1):
        for i in range(n+1):
            u=i/n;v=j/n;x=-.12+(u-.5)*.8;z=.68+v*1.2
            y=front+(edge-front)*(x/(w/2))**2-.021
            verts.append((x,y,z));uv.append((u,v))
    for j in range(n):
        for i in range(n):
            a=j*(n+1)+i;faces.append((a,a+1,a+n+2,a+n+1))
    return mesh_object('Holo',verts,faces,uv,mat)

def export_obj(o,path):
    # Explicit cm/Z-up coordinates and per-corner UV/normals avoid importer axis guesses.
    deps=bpy.context.evaluated_depsgraph_get();eo=o.evaluated_get(deps);m=eo.to_mesh();m.calc_loop_triangles()
    world=eo.matrix_world;normal=world.to_3x3().inverted().transposed();layer=m.uv_layers.active
    with path.open('w',encoding='utf-8',newline='\n') as f:
        f.write(f'# Cryo comparison; centimeters; Z up; front -Y\no {o.name}\n')
        for v in m.vertices:
            p=world@v.co*100;f.write(f'v {p.x:.8f} {p.y:.8f} {p.z:.8f}\n')
        for li in range(len(m.loops)):
            uv=layer.data[li].uv if layer else (0,0);f.write(f'vt {uv[0]:.8f} {uv[1]:.8f}\n')
        for li in range(len(m.loops)):
            n=(normal@m.corner_normals[li].vector).normalized();f.write(f'vn {n.x:.8f} {n.y:.8f} {n.z:.8f}\n')
        f.write(f'usemtl {o.data.materials[0].name}\ns 1\n')
        for tri in m.loop_triangles:f.write('f '+' '.join(f'{m.loops[li].vertex_index+1}/{li+1}/{li+1}' for li in tri.loops)+'\n')
    eo.to_mesh_clear()

def lights_and_camera():
    sc=bpy.context.scene;world=bpy.data.worlds.new('ComparisonWorld');sc.world=world;world.use_nodes=True
    world.node_tree.nodes['Background'].inputs[0].default_value=(.008,.014,.022,1);world.node_tree.nodes['Background'].inputs[1].default_value=.32
    for name,loc,power,size,color in [('Key',(2,-4,4),500,3,(.7,.83,1)),('Fill',(-3,-3,2),340,3,(.25,.55,1)),('Rim',(1,2,4),700,2,(.25,.65,1))]:
        d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color
        ob=bpy.data.objects.new(name,d);sc.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,0,1.6))-ob.location).to_track_quat('-Z','Y').to_euler()
    for z in [1,2.7]:
        d=bpy.data.lights.new('CryoInterior','POINT');d.energy=12;d.color=(.12,.6,1);d.shadow_soft_size=.25
        ob=bpy.data.objects.new('CryoInterior',d);sc.collection.objects.link(ob);ob.location=(0,.10,z)
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.025));floor=bpy.context.object;floor.name='StudioFloor';floor.data.materials.append(simple_mat('StudioFloor',(.018,.025,.034),.4,.3))
    camd=bpy.data.cameras.new('PreviewCamera');cam=bpy.data.objects.new('PreviewCamera',camd);sc.collection.objects.link(cam);sc.camera=cam;camd.type='ORTHO';camd.ortho_scale=3.9
    sc.render.engine='CYCLES';sc.cycles.samples=48;sc.cycles.use_denoising=True
    sc.render.resolution_x=960;sc.render.resolution_y=1200;sc.render.resolution_percentage=100;sc.view_settings.view_transform='AgX'
    return cam,floor

manifest={'shared':SHARED,'models':[],'same_finish':'Glass, frosted edges, two replacement consoles, status panel, hologram, four mist cards, trim. Native Unreal adds localized volumetric fog and Niagara.','units':'OBJ cm; Blender/GLB meters; front -Y, up Z'}
for idx,source in enumerate(sorted(SRC.glob('*.glb'))):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source));bpy.context.view_layer.update()
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(objects)==1
    body=objects[0];body.name='Body';pts=[body.matrix_world@Vector(c) for c in body.bound_box]
    lo=Vector(tuple(min(v[a] for v in pts) for a in range(3)));hi=Vector(tuple(max(v[a] for v in pts) for a in range(3)));scale=3.2/(hi.z-lo.z)
    c=(lo+hi)/2;c.z=lo.z;rot=Matrix.Rotation(math.radians(-30 if idx==0 else 0),4,'Z')
    old=body.matrix_world.copy();normal_transform=rot.to_3x3()@old.to_3x3().inverted().transposed()
    normals=[(normal_transform@n.vector).normalized() for n in body.data.corner_normals]
    for v in body.data.vertices:v.co=rot@((old@v.co-c)*scale)
    body.parent=None;body.matrix_world=Matrix.Identity(4);body.data.update();body.data.normals_split_custom_set(normals);bpy.context.view_layer.update()
    folder=OUT/NAMES[idx];folder.mkdir(parents=True,exist_ok=True);(folder/'meshes').mkdir(exist_ok=True)
    maps=extract_maps(source,folder)
    m=body.data.materials[0];m.name=f'M_Source_{idx}';bs=m.node_tree.nodes.get('Principled BSDF')
    if bs:
        for input_name,operation,value in [('Metallic','MULTIPLY',.7),('Roughness','MAXIMUM',.25)]:
            sock=bs.inputs[input_name]
            if sock.is_linked:
                oldsocket=sock.links[0].from_socket;n=m.node_tree.nodes.new('ShaderNodeMath');n.operation=operation;n.inputs[1].default_value=value
                m.node_tree.links.new(oldsocket,n.inputs[0]);m.node_tree.links.new(n.outputs[0],sock)
            elif operation=='MULTIPLY':sock.default_value*=value
            else:sock.default_value=max(sock.default_value,value)
    mats={k:image_mat('M_'+k,p,{'frost':.40,'holo':.60,'mist':.13}.get(k,1),{'console':.65,'status':.65,'holo':2,'mist':.22}.get(k,0)) for k,p in SHARED.items()}
    glassmat=simple_mat('M_Glass',(.3,.55,.7),0,.12,0,.055);trim=simple_mat('M_Trim',(.05,.55,1),.25,.25,2.5)
    components=[(body,'body')];fit=GLASS[idx]
    # Screen corners are projected back onto the untouched source surface.
    q=(Vector((0,0,1.6))-Vector((0,-6,1.75))).to_track_quat('-Z','Y');direction=q@Vector((0,0,-1))
    for j,corners in enumerate(SCREENS[idx]):
        verts=[]
        for px,py in corners:
            origin=Vector((0,-6,1.75))+q@Vector(((px/640-.5)*3.8*.8,(.5-py/800)*3.8,0))
            hit,loc,normal,*_=bpy.context.scene.ray_cast(bpy.context.evaluated_depsgraph_get(),origin,direction)
            if not hit:raise RuntimeError(f'Screen miss {idx} {j} {px} {py}')
            verts.append(loc-direction*.012)
        ob=mesh_object('Console_'+str(j+1),verts,[(3,2,1,0)],[(0,1),(1,1),(1,0),(0,0)],mats['console']);components.append((ob,'console'))
    glass=curved('Glass',fit,glassmat);components.append((glass,'glass'))
    frost=curved('Frost',fit,mats['frost'],-.008);components.append((frost,'frost'))
    w,b,t,front,edge=fit
    holo=curved_holo(fit,mats['holo']);components.append((holo,'holo'))
    status=panel('Status',(-w/2-.09,front+.06,1.98),.28,.42,mats['status']);components.append((status,'status'))
    housingmat=simple_mat('M_Housing',(.012,.022,.035),.6,.32);housing=[]
    for loc,dims in [((-w/2-.09,front+.084,1.98),(.31,.035,.45)),((-w/2-.09,front+.19,1.98),(.055,.23,.08))]:
        bpy.ops.mesh.primitive_cube_add(size=1,location=loc);ob=bpy.context.object;ob.dimensions=dims
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);ob.data.materials.append(housingmat)
        bevel=ob.modifiers.new('MachinedEdges','BEVEL');bevel.width=.008;bevel.segments=2
        bpy.ops.object.modifier_apply(modifier=bevel.name);housing.append(ob)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in housing:ob.select_set(True)
    bpy.context.view_layer.objects.active=housing[0];bpy.ops.object.join();housing[0].name='Housing';components.append((housing[0],'housing'))
    for j,(x,z,h) in enumerate([(-.18,.98,.85),(.22,1.18,.8),(-.20,2.53,.65),(.20,2.68,.7)]):
        ob=panel('Mist_'+str(j+1),(x,front+.12+j*.025,z),w*.84,h,mats['mist']);components.append((ob,'mist'))
        start=ob.location.copy()
        for frame,offset in [(1,0),(121,.035),(241,0)]:
            ob.location=start+Vector((offset if j%2 else -offset,0,offset));ob.keyframe_insert('location',frame=frame)
        ob.location=start
    # Two narrow blue emitters across the lid/floor; same construction and material for all variants.
    trimobs=[]
    for z in [b+.035,t-.035]:trimobs.append(panel('TrimPart',(0,front-.012,z),w*.55,.009,trim))
    bpy.ops.object.select_all(action='DESELECT')
    for ob in trimobs:ob.select_set(True)
    bpy.context.view_layer.objects.active=trimobs[0];bpy.ops.object.join();trimobs[0].name='Trim';components.append((trimobs[0],'trim'))
    bpy.context.scene.frame_set(1);rows=[]
    for ob,role in components:
        path=folder/'meshes'/f'SM_{NAMES[idx]}_{ob.name}.obj';export_obj(ob,path)
        rows.append({'name':ob.name,'role':role,'file':str(path),'triangles':sum(len(f.vertices)-2 for f in ob.data.polygons)})
    bpy.ops.object.select_all(action='DESELECT')
    for ob,_ in components:ob.select_set(True)
    bpy.context.view_layer.objects.active=body
    bpy.ops.export_scene.gltf(filepath=str(folder/f'{NAMES[idx]}_Finished.glb'),export_format='GLB',use_selection=True,export_animations=True,export_frame_range=True,export_keep_originals=True)
    cam,floor=lights_and_camera()
    for label,location in [('front',(0,-6,1.75)),('threequarter',(2.8,-5.5,2.1))]:
        cam.location=location;cam.rotation_euler=(Vector((0,0,1.6))-cam.location).to_track_quat('-Z','Y').to_euler()
        bpy.context.scene.render.filepath=str(OUT/'previews'/f'{chr(65+idx)}_{label}_blender.png');bpy.ops.render.render(write_still=True)
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(folder/f'{NAMES[idx]}_Editable.blend'))
    manifest['models'].append({'id':chr(65+idx),'label':NAMES[idx].replace('_',' '),'source':str(source),'source_sha256':sha(source),'components':rows,'textures':maps,'height_cm':320,'glass_fit_m':fit,'yaw_alignment_deg':-30 if idx==0 else 0})
    (OUT/'assembly.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('FINISHED_PREVIEW',NAMES[idx],flush=True)
