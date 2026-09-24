"""Non-destructive source derivative: local smoothing plus 180 skinned fur cards."""
import bpy,json,math,random,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[2] / ".agent/local/ReplacementHero"
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT/'SquirrelHero_Rigged.blend'))
rig=bpy.data.objects['Armature'];body=bpy.data.objects['SquirrelHero_Replacement'];scene=bpy.context.scene
rig.animation_data.action=None
for b in rig.pose.bones:b.rotation_quaternion=(1,0,0,0)
bpy.context.view_layer.update()
tail=set(json.loads((OUT/'repair_vertices.json').read_text())['tail'])
original=[v.co.copy() for v in body.data.vertices]
world=[body.matrix_world@v.co for v in body.data.vertices]
# Weld only the smoothing calculation, keeping original UV seams and topology intact.
lookup={};groups=[];index=[]
for i,p in enumerate(world):
    key=tuple(round(v,5) for v in p)
    if key not in lookup:lookup[key]=len(groups);groups.append([])
    k=lookup[key];groups[k].append(i);index.append(k)
positions=[world[g[0]].copy() for g in groups];adj=[set() for g in groups]
for e in body.data.edges:
    a,b=[index[v] for v in e.vertices]
    if a!=b:adj[a].add(b);adj[b].add(a)
for iteration in range(5):
    new=[p.copy() for p in positions]
    for k,group in enumerate(groups):
        if not all(i in tail for i in group) or not adj[k]:continue
        feather=max(0,min(1,(world[group[0]].y+.065)/.09))
        mean=sum((positions[j] for j in adj[k]),Vector())/len(adj[k])
        new[k]=positions[k]+(mean-positions[k])*.38*feather
    positions=new
inverse=body.matrix_world.inverted()
for k,group in enumerate(groups):
    if all(i in tail for i in group):
        delta=positions[k]-world[group[0]]
        if delta.length>.003:delta=delta.normalized()*.003
        for i in group:body.data.vertices[i].co=inverse@(world[i]+delta)
body.data.update()
assert all((body.data.vertices[i].co-original[i]).length==0 for i in range(len(original)) if i not in tail)
base=body.data.materials[0];soft=base.copy();soft.name='Tail_SoftCore'
for node in soft.node_tree.nodes:
    if node.type=='BSDF_PRINCIPLED':node.inputs['Roughness'].default_value=.86;node.inputs['Metallic'].default_value=0
    if node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=.25
body.data.materials.append(soft)
bs=next(n for n in soft.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
source=bs.inputs['Base Color'].links[0].from_node.image
# Bake a private diffuse tint so Blender and glTF use the identical simple material.
color=source.copy();color.name='Tail_SoftCore_Color'
rgba=np.empty(len(color.pixels),dtype=np.float32);color.pixels.foreach_get(rgba)
rgba=rgba.reshape((-1,4));rgba[:,:3]*=np.array([.22,.12,.06])
color.pixels.foreach_set(rgba.ravel());color.filepath_raw=str(OUT/'Tail_SoftCore_Color.png');color.file_format='PNG';color.save();color.pack()
tex=soft.node_tree.nodes.new('ShaderNodeTexImage');tex.image=color
soft.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
bs.inputs['Specular IOR Level'].default_value=.12
bs.inputs['Roughness'].default_value=.72
for p in body.data.polygons:
    if all(i in tail for i in p.vertices):p.material_index=1
# Procedural strand atlas: individual tapered fibers, not broad opaque leaf shapes.
rng=random.Random(75203);width,height=256,512
x=np.linspace(0,1,width)[None,:];y=np.linspace(0,1,height)[:,None]
alpha=np.zeros((height,width),dtype=np.float32);rgb=np.zeros((height,width,3),dtype=np.float32)
for i in range(24):
    root=(i+.5)/24;phase=rng.random()*6.28;end=rng.uniform(.73,1.0)
    center=.5+(root-.5)*(1-.8*y)+.025*np.sin(y*5+phase)*y
    thickness=rng.uniform(.0014,.0030)*(1-.85*y)
    strand=np.exp(-((x-center)/thickness)**2)*np.clip((end-y)*30,0,1)*np.clip(y*18,0,1)
    color=np.array(rng.choice([(.16,.075,.032),(.30,.16,.07),(.09,.038,.015),(.43,.29,.15)]))
    total=alpha+strand;rgb=(rgb*alpha[:,:,None]+strand[:,:,None]*color)/np.maximum(total[:,:,None],1e-8);alpha=np.maximum(alpha,strand)
pixels=np.dstack((rgb,alpha)).astype(np.float32)
atlas=bpy.data.images.new('Tail_FineFibers_RGBA',width,height,alpha=True);atlas.pixels.foreach_set(pixels.ravel());atlas.filepath_raw=str(OUT/'Tail_FineFibers_RGBA.png');atlas.file_format='PNG';atlas.save();atlas.pack()
mat=bpy.data.materials.new('Tail_FineFurCards');mat.use_nodes=True
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.9;bs.inputs['Metallic'].default_value=0
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=atlas;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);mat.node_tree.links.new(tex.outputs['Alpha'],bs.inputs['Alpha'])
centers=[Vector(p) for p in json.loads((OUT/'tail_weight_revision.json').read_text())['tail_centerline']]
candidates=[i for i in tail if world[i].y>-.035]
rng.shuffle(candidates);chosen=[]
for i in candidates:
    p=body.matrix_world@body.data.vertices[i].co
    if all((p-q).length>.018 for q,j in chosen):chosen.append((p,i))
    if len(chosen)==180:break
verts=[];faces=[];uvs=[];weights=[]
normal_matrix=body.matrix_world.to_3x3().inverted().transposed()
for p,source_i in chosen:
    distances=[(p-(a+b)*.5).length for a,b in zip(centers,centers[1:])];j=min(range(len(distances)),key=distances.__getitem__)
    direction=(centers[j+1]-centers[j]).normalized();normal=(normal_matrix@body.data.vertices[source_i].normal).normalized()
    tangent=direction-normal*direction.dot(normal)
    if tangent.length<.1:tangent=direction
    tangent.normalize();side=tangent.cross(normal).normalized()
    length=rng.uniform(.025,.045);halfwidth=rng.uniform(.005,.010);offset=len(verts)
    skin={body.vertex_groups[g.group].name:g.weight for g in body.data.vertices[source_i].groups}
    for s in range(5):
        t=s/4;center=p+tangent*(length*t)+normal*(.001+.009*math.sin(t*math.pi*.75))
        for sign in [-1,1]:verts.append(tuple(center+side*halfwidth*sign));uvs.append((0 if sign<0 else 1,t));weights.append(skin)
    for s in range(4):
        a=offset+2*s;faces.extend([(a,a+1,a+3),(a,a+3,a+2)])
data=bpy.data.meshes.new('Tail_FurCards');data.from_pydata(verts,[],faces);data.update();cards=bpy.data.objects.new('Tail_FurCards',data);scene.collection.objects.link(cards);cards.data.materials.append(mat)
uv=data.uv_layers.new(name='UVMap')
for poly in data.polygons:
    for li in poly.loop_indices:uv.data[li].uv=uvs[data.loops[li].vertex_index]
for name in body.vertex_groups:cards.vertex_groups.new(name=name.name)
for i,skin in enumerate(weights):
    for name,w in skin.items():cards.vertex_groups[name].add([i],w,'REPLACE')
modifier=cards.modifiers.new('Follow repaired tail','ARMATURE');modifier.object=rig
for poly in data.polygons:poly.use_smooth=True
total=len(body.data.polygons)+len(faces);assert total<80000
report={'base_triangles':len(body.data.polygons),'cards':len(chosen),'card_triangles':len(faces),'total_triangles':total,'body_vertices_outside_tail_unchanged':True,'maximum_tail_vertex_shift_m':max((body.matrix_world.to_3x3()@(v.co-original[i])).length for i,v in enumerate(body.data.vertices)),'material_slots':3,'source_rig_unchanged':True,'native_Unreal_fur_material_not_yet_created':True}
(OUT/'fur_revision.json').write_text(json.dumps(report,indent=2))
# Exports in reference pose; a separate file makes the appearance comparison reversible.
bpy.ops.object.select_all(action='DESELECT')
for ob in [body,cards,rig]:ob.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(OUT/'SquirrelHero_SoftFur.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',use_mesh_modifiers=False,path_mode='RELATIVE')
bpy.ops.export_scene.gltf(filepath=str(OUT/'SquirrelHero_SoftFur.glb'),export_format='GLB',use_selection=True,export_animations=False)
rig.animation_data.action=bpy.data.actions['Tail_Idle'];scene.frame_set(1)
from mathutils import Quaternion
for name,deg in [('upperarm_l',65),('upperarm_r',-65)]:
    pb=rig.pose.bones[name];axis=(rig.matrix_world@pb.bone.matrix_local).to_3x3().inverted()@Vector((0,1,0));pb.rotation_quaternion=Quaternion(axis,math.radians(deg))
scene.render.resolution_x=700;scene.render.resolution_y=700;scene.cycles.samples=24;scene.camera.location=(-1,2,.85);scene.camera.data.ortho_scale=1.22;scene.camera.rotation_euler=(Vector((0,0,.45))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/'SoftFur_Back.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'SquirrelHero_SoftFur.blend'),compress=True)
print('SOFT_FUR_OK',json.dumps(report))
