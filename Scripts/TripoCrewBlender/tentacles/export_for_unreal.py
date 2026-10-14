"""Export a tentacle character for Scripts/ImportTripoCrew.py: the rest-pose mesh plus ONE FBX PER CLIP.

  blender -b <animated>.blend -P export_for_unreal.py -- <outdir> <Name>

Writes <outdir>/<Name>.fbx (mesh + skeleton, no animation, true rest pose) and <Name>_Crawl.fbx, _Idle.fbx,
_TurnL.fbx, _TurnR.fbx - the layout ImportTripoCrew.py's import_clips reads. Clips shipped inside the mesh FBX are
rejected there: Interchange rebinds the skin to frame 0 of the first take.

Centimetre export (the crew-wide trap): scale_length 0.01, x100 on the root objects, applied, FBX_SCALE_ALL. Applying
the scale rescales the bone rest positions but NOT pose-bone location F-curves, so the Pelvis bob that
animate_tentacles.py keys in metres is multiplied by 100 here; without that it arrives 100x too small (invisible),
which is how the clips imported on 2026-10-08 went out.
"""
import os
import sys

import bpy

outdir, short = sys.argv[-2], sys.argv[-1]
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
ms = [o for o in bpy.data.objects if o.type == 'MESH']
arm.name = "Armature"; arm.data.name = "Armature"
sc = bpy.context.scene
sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 0.01; sc.render.fps = 30
for o in [arm] + ms:
    if o.parent is None:
        o.scale = (100, 100, 100); o.location = o.location * 100
for o in bpy.data.objects:
    o.select_set(o in ms or o == arm)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
def fcurves(a):
    if hasattr(a, "fcurves"):                          # Blender < 4.4
        return list(a.fcurves)
    return [fc for layer in a.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]


acts = [a for a in bpy.data.actions if a.name.startswith('Tent')]
for a in acts:
    a.use_fake_user = True
    for fc in fcurves(a):
        if fc.data_path.endswith('.location'):        # only Pelvis has location keys (the bob), authored in metres
            for k in fc.keyframe_points:
                k.co.y *= 100; k.handle_left.y *= 100; k.handle_right.y *= 100
common = dict(use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
              apply_scale_options='FBX_SCALE_ALL', use_armature_deform_only=False, mesh_smooth_type='FACE',
              primary_bone_axis='Y', secondary_bone_axis='X', path_mode='STRIP')
arm.animation_data.action = None
for pb in arm.pose.bones:                              # the skin binds to the true rest pose, not a take's frame 0
    pb.location = (0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
bpy.context.view_layer.update()
bpy.ops.export_scene.fbx(filepath=os.path.join(outdir, short + ".fbx"), use_tspace=True, bake_anim=False, **common)
for a in acts:
    arm.animation_data.action = a
    sc.frame_start, sc.frame_end = int(a.frame_range[0]), int(a.frame_range[1])
    bpy.ops.export_scene.fbx(filepath=os.path.join(outdir, "%s_%s.fbx" % (short, a.name[len('Tent'):])),
                             bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                             bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0, **common)
print("TENTEXPORT", short, [a.name for a in acts])
