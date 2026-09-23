"""Private, repeatable repair of the owner-selected 75,183-triangle Tripo hero."""
import bpy, json, math, hashlib
from pathlib import Path
from mathutils import Vector, Quaternion
OUT=Path(__file__).resolve().parents[2] / ".agent/local/ReplacementHero"
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT/'Survey.blend'))
mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH')
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
assert len(mesh.data.polygons) == 75183, 'This recipe is only for the selected Tripo source'
assert not any(b.name.startswith('tail_') for b in rig.data.bones), 'Use the unchanged Survey input'
pts=[mesh.matrix_world@v.co for v in mesh.data.vertices]
tail=[];pack=[];pack_blend={}
def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
for i,p in enumerate(pts):
    x,y,z=p
    if (y>-.10 and z<.445) or y>.015:tail.append(i)
    else:
        w=smooth(-.16,-.125,y)*smooth(.425,.46,z)*(1-smooth(.745,.785,z))*(1-smooth(.112,.137,abs(x)))
        if w>1e-6:pack_blend[i]=w
        if w>.99999:pack.append(i)
report={'tail_vertices':len(tail),'backpack_vertices':len(pack)}
# Derive the tail centerline from its cross-sections; start at the pelvis attachment.
centers=[Vector((0,-.14,.397))]
for y in [-.075,.0,.075,.15,.225,.30]:
    sample=[pts[i] for i in tail if abs(pts[i].y-y)<.018]
    centers.append(Vector((sum(p.x for p in sample)/len(sample),y,sum(p.z for p in sample)/len(sample))))
centers.append(Vector((centers[-1].x,.345,centers[-1].z-.04)))
report['tail_centerline']=[list(p) for p in centers]
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
root=rig.data.edit_bones.new('root');root.head=rig.matrix_world.inverted()@Vector((0,-.213,0));root.tail=root.head+Vector((0,.06,0))
rig.data.edit_bones['pelvis'].parent=root
tail_names=[]
for i in range(len(centers)-1):
    b=rig.data.edit_bones.new('tail_%02d'%(i+1));b.head=rig.matrix_world.inverted()@centers[i];b.tail=rig.matrix_world.inverted()@centers[i+1];b.parent=rig.data.edit_bones[tail_names[-1]] if tail_names else rig.data.edit_bones['pelvis'];b.use_connect=bool(tail_names);tail_names.append(b.name)
b=rig.data.edit_bones.new('backpack');b.head=rig.matrix_world.inverted()@Vector((0,-.10,.55));b.tail=rig.matrix_world.inverted()@Vector((0,-.10,.68));b.parent=rig.data.edit_bones['spine_03']
bpy.ops.object.mode_set(mode='OBJECT')
for name in tail_names+['backpack']:mesh.vertex_groups.new(name=name)
def assign(i,weights):
    for g in list(mesh.data.vertices[i].groups):mesh.vertex_groups[g.group].remove([i])
    weights=dict(sorted(weights.items(),key=lambda p:p[1],reverse=True)[:4])
    total=sum(weights.values())
    for name,w in weights.items():
        w/=total
        if w>1e-7:mesh.vertex_groups[name].add([i],w,'REPLACE')
# Smooth interpolation along the curved chain; no leg influence can reach the tail.
for i in tail:
    p=pts[i];nearest=None
    for j in range(len(centers)-1):
        a,b=centers[j:j+2];delta=b-a;t=max(0,min(1,(p-a).dot(delta)/delta.length_squared));dist=(p-a-t*delta).length_squared
        if nearest is None or dist<nearest[0]:nearest=(dist,j,t)
    _,j,t=nearest
    # Bone influence centers are at segment midpoints.
    q=max(0,min(len(tail_names)-1,j+t-.5));a=int(q);f=q-a
    weights={tail_names[a]:1-f}
    if f:weights[tail_names[a+1]]=f
    if p.y<-.07:
        blend=max(0,min(1,(p.y+.10)/.03));weights={k:v*blend for k,v in weights.items()};weights['pelvis']=1-blend
    assign(i,weights)
for i,w in pack_blend.items():
    weights={mesh.vertex_groups[g.group].name:g.weight*(1-w) for g in mesh.data.vertices[i].groups}
    weights['backpack']=w
    assign(i,weights)
report['rig_bones']=len(rig.data.bones)
rig.name='Armature';mesh.name='SquirrelHero_Replacement'
rig.show_in_front=True;rig.display_type='WIRE'
# Save a portable, textured rig with the original mesh topology/UVs.
for img in bpy.data.images:
    if img.source=='FILE' and Path(bpy.path.abspath(img.filepath)).is_file():img.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'SquirrelHero_Rigged.blend'))
(OUT/'repair.json').write_text(json.dumps(report,indent=2))
(OUT/'repair_vertices.json').write_text(json.dumps({'tail':tail,'backpack':pack}))
# Diagnostic selection render: red tail, cyan rigid backpack, grey untouched body.
mask=mesh.data.color_attributes.new(name='RepairMask',type='FLOAT_COLOR',domain='POINT');ts=set(tail);ps=set(pack)
for i,c in enumerate(mask.data):c.color=(.8,.03,.02,1) if i in ts else ((.02,.7,.8,1) if i in ps else (.22,.22,.22,1))
mat=bpy.data.materials.new('DiagnosticOnly');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');attr=mat.node_tree.nodes.new('ShaderNodeVertexColor');attr.layer_name='RepairMask';mat.node_tree.links.new(attr.outputs['Color'],bs.inputs['Base Color']);mesh.data.materials[0]=mat
scene=bpy.context.scene
for label,loc in [('mask-side',(2,0,.8)),('mask-back',(-1,2,.9))]:
    scene.camera.location=loc;scene.camera.rotation_euler=(Vector((0,0,.45))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/(label+'.png'));bpy.ops.render.render(write_still=True)
