import bpy, json, collections
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[2] / ".agent/local/ReplacementHero"
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT/'sci-fi_squirrel_3d_model.blend'))
mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH')
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
mat=mesh.data.materials[0]; mat.use_nodes=True
bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(OUT/'sci-fi_squirrel_3d_model_basecolor.tga'));mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.48
normal=mat.node_tree.nodes.new('ShaderNodeTexImage');normal.image=bpy.data.images.load(str(OUT/'sci-fi_squirrel_3d_model_normal.tga'));normal.image.colorspace_settings.name='Non-Color'
n=mat.node_tree.nodes.new('ShaderNodeNormalMap');mat.node_tree.links.new(normal.outputs['Color'],n.inputs['Color']);mat.node_tree.links.new(n.outputs['Normal'],bs.inputs['Normal'])
pts=[mesh.matrix_world@v.co for v in mesh.data.vertices]
parent=list(range(len(pts)))
def find(x):
    while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
    return x
def union(a,b):
    a,b=find(a),find(b)
    if a!=b:parent[b]=a
seen={}
for i,p in enumerate(pts):
    key=tuple(round(v,5) for v in p)
    if key in seen:union(i,seen[key])
    else:seen[key]=i
for e in mesh.data.edges:union(*e.vertices)
groups=collections.defaultdict(list)
for i in range(len(pts)):groups[find(i)].append(i)
comps=sorted(groups.values(),key=len,reverse=True)
rows=[]
for idx,ids in enumerate(comps):
    weights=collections.Counter()
    for i in ids:
        for g in mesh.data.vertices[i].groups:weights[mesh.vertex_groups[g.group].name]+=g.weight
    rows.append({'id':idx,'vertices':len(ids),'min':[min(pts[i][a] for i in ids) for a in range(3)],'max':[max(pts[i][a] for i in ids) for a in range(3)],'weights':weights.most_common(6)})
(OUT/'components.json').write_text(json.dumps({'components':rows,'bones':{b.name:list(rig.matrix_world@b.head_local) for b in rig.data.bones}},indent=2))
(OUT/'component_vertices.json').write_text(json.dumps(comps))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24
scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.15,.19,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.4
for loc,power,size in [((1,-2,2),180,2),((-1,-1,1),100,1.5),((0,2,1.6),220,1.2)]:
    bpy.ops.object.light_add(type='AREA',location=loc);lamp=bpy.context.object;lamp.data.energy=power;lamp.data.shape='DISK';lamp.data.size=size;lamp.rotation_euler=(Vector((0,0,.45))-lamp.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.22
for label,loc in [('front',(1,-2,.9)),('back',(-1,2,.9)),('side',(2,0,.8))]:
    cam.location=loc;cam.rotation_euler=(Vector((0,0,.45))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/(label+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Survey.blend'))
