"""Replace broken Tripo skin weights with Blender automatic (bone heat) weights on the normalized rig."""
import bpy, sys
out=sys.argv[-1]
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
m=[o for o in bpy.data.objects if o.type=='MESH'][0]
for mod in list(m.modifiers): m.modifiers.remove(mod)
m.vertex_groups.clear(); m.parent=None
bpy.ops.object.select_all(action='DESELECT'); m.select_set(True); bpy.context.view_layer.objects.active=m
nv=len(m.data.vertices)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=0.0008); bpy.ops.object.mode_set(mode='OBJECT')
print("WELD",nv,"->",len(m.data.vertices))
# deform bones only: twist/finger bones included; ik/virtual none in Tripo rigs. NOT the floor root: bone heat
# hands the feet and anything near the floor to it, and those vertices then stay behind and stretch whenever the
# body leaves the root (sitting, crouching, root-motion floats). See strip_root_weights.py.
for b in arm.data.bones:
    if b.name in ("root", "Armature"):
        b.use_deform = False
bpy.ops.object.select_all(action='DESELECT'); m.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active=arm
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
from mathutils import kdtree
weighted=[v for v in m.data.vertices if v.groups]; lonely=[v for v in m.data.vertices if not v.groups]
if lonely:
    kd=kdtree.KDTree(len(weighted))
    for i,v in enumerate(weighted): kd.insert(v.co,i)
    kd.balance()
    for v in lonely:
        _,i,_=kd.find(v.co); src=weighted[i]
        for g in src.groups: m.vertex_groups[g.group].add([v.index],g.weight,'REPLACE')
print("FILLED",len(lonely))
empty=sum(1 for v in m.data.vertices if not v.groups)
print("AUTO groups",len(m.vertex_groups),"unweighted verts",empty,"of",len(m.data.vertices))
bpy.ops.wm.save_as_mainfile(filepath=out+".blend")
