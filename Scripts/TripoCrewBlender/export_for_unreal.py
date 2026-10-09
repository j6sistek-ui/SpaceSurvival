import bpy, sys, json
out=sys.argv[-1]
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]; ms=[o for o in bpy.data.objects if o.type=='MESH']
arm.name="Armature"; arm.data.name="Armature"
# work in centimetres like Unreal: unit scale 0.01, geometry x100 applied, so the FBX carries no scale
bpy.context.scene.unit_settings.system='METRIC'; bpy.context.scene.unit_settings.scale_length=0.01
for o in [arm]+ms:
    if o.parent is None: o.scale=(100,100,100); o.location=o.location*100
for o in bpy.data.objects: o.select_set(o in ms or o==arm)
bpy.context.view_layer.objects.active=arm
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.context.view_layer.objects.active=arm
bpy.ops.export_scene.fbx(filepath=out, use_selection=True, object_types={'ARMATURE','MESH'}, add_leaf_bones=False,
    apply_scale_options='FBX_SCALE_ALL', mesh_smooth_type='FACE', use_armature_deform_only=False, bake_anim=False, use_tspace=True,
    primary_bone_axis='Y', secondary_bone_axis='X', path_mode='STRIP')
print("FINAL", out.split('/')[-1], json.dumps([m.name for m in ms[0].data.materials]))
