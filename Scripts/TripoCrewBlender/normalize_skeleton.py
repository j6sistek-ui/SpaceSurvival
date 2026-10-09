"""Tripo FBX (from UE) -> clean skeleton: unit bone scale, no 'Armature' bone, real height. CPU only."""
import bpy, sys, math, json
from mathutils import Vector
src, out, height = sys.argv[-3], sys.argv[-2], float(sys.argv[-1])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=src, use_anim=False)
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]; meshes=[o for o in bpy.data.objects if o.type=='MESH']
def sel(objs, active):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active=active
# 1 bake current deformation into the meshes and drop them out of the hierarchy
for m in meshes:
    sel([m],m)
    for mod in [x for x in m.modifiers if x.type=='ARMATURE']: bpy.ops.object.modifier_apply(modifier=mod.name)
    mw=m.matrix_world.copy(); m.parent=None; m.matrix_world=mw
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
# 2 rebuild the rest skeleton from where the joints actually are (world space, scale stripped)
from mathutils import Matrix
bpy.context.view_layer.update()
world={}
for pb in arm.pose.bones:
    M=arm.matrix_world@pb.matrix
    loc,rot,_=M.decompose()
    world[pb.name]=(loc.copy(), rot.copy(), (arm.matrix_world@pb.tail-loc).length)
for pb in arm.pose.bones: pb.matrix_basis=Matrix.Identity(4)
arm.parent=None; arm.location=(0,0,0); arm.rotation_mode='XYZ'; arm.rotation_euler=(0,0,0); arm.rotation_quaternion=(1,0,0,0); arm.scale=(1,1,1); bpy.context.view_layer.update(); print('ARMRESET',[round(v,3) for v in arm.matrix_world.to_scale()])
sel([arm],arm); bpy.ops.object.mode_set(mode='EDIT')
eb=arm.data.edit_bones
for b in eb: b.use_connect=False
for name,(loc,rot,ln) in world.items():
    b=eb[name]; m=rot.to_matrix().to_4x4(); m.translation=loc; b.matrix=m; b.length=max(ln,1e-5)
dropped=[]
if 'Armature' in eb:
    b=eb['Armature']
    for c in b.children: c.parent=None
    eb.remove(b); dropped.append('Armature')
bpy.ops.object.mode_set(mode='OBJECT')
# 3b bones and mesh can disagree by a power of ten (the x100 lived on a bone); measure and snap
pts=[m.matrix_world@v.co for m in meshes for v in m.data.vertices]
mh=max(p.z for p in pts)-min(p.z for p in pts)
hb=arm.data.bones.get('head') or arm.data.bones.get('Head')
ratio=mh*0.87/max(hb.head_local.z,1e-9); snap=10**round(math.log10(ratio))
print("RATIO",round(ratio,4),"snap",snap)
if snap!=1:
    arm.scale=(snap,snap,snap); sel([arm],arm); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
# 4 scale everything to the requested height, feet on z=0, centred
pts=[m.matrix_world@v.co for m in meshes for v in m.data.vertices]
mn=Vector([min(p[i] for p in pts) for i in range(3)]); mx=Vector([max(p[i] for p in pts) for i in range(3)])
k=height/(mx.z-mn.z); off=Vector(((mn.x+mx.x)/2,(mn.y+mx.y)/2,mn.z))
for o in [arm]+meshes:
    o.location=(o.location-off)*k; o.scale=o.scale*k
sel([arm]+meshes,arm); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
# 4b every crew skeleton gets a 'root' at the floor, like the mannequin, so movement/root motion has a home
sel([arm],arm); bpy.ops.object.mode_set(mode='EDIT'); eb=arm.data.edit_bones
if 'root' not in eb:
    tops=[b for b in eb if b.parent is None]
    r=eb.new('root'); r.head=(0,0,0); r.tail=(0,0.1,0)
    for b in tops: b.parent=r
    dropped.append('added_root')
bpy.ops.object.mode_set(mode='OBJECT')
# 5 rebind
for m in meshes:
    m.parent=arm; mod=m.modifiers.new("Armature",'ARMATURE'); mod.object=arm
arm.name="Armature"; arm.data.name="Armature"
pts=[m.matrix_world@v.co for m in meshes for v in m.data.vertices]
H=max(p.z for p in pts)-min(p.z for p in pts)
pb=arm.pose.bones; maxscale=max(max(abs(s) for s in b.scale) for b in pb)
head=arm.data.bones['head'].head_local if 'head' in arm.data.bones else arm.data.bones.get('Head').head_local
rootb=[b.name for b in arm.data.bones if b.parent is None]
print("NORM", json.dumps({"height_m":round(H,3),"scale_factor":round(k,2),"dropped":dropped,"roots":rootb,"bones":len(arm.data.bones),"head_z":round(head.z,3),"max_pose_scale":round(maxscale,3)}))
bpy.ops.wm.save_as_mainfile(filepath=out+".blend")
sel([arm]+meshes,arm)
bpy.ops.export_scene.fbx(filepath=out+".fbx", use_selection=True, object_types={'ARMATURE','MESH'}, add_leaf_bones=False,
    apply_scale_options='FBX_SCALE_ALL', mesh_smooth_type='FACE', use_armature_deform_only=False, bake_anim=False, use_tspace=True, primary_bone_axis='Y', secondary_bone_axis='X')
