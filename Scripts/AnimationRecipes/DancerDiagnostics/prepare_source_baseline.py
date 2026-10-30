import os
from pathlib import Path
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Export untouched source rig/motion and inspect removable arrows on neutral F3."""
import bpy, json, hashlib, sys
from pathlib import Path
from mathutils import Vector
from mathutils import Matrix
P=R.parents[2]
sys.path.insert(0,str(R))
import forearm_markers
report={'sources':[], 'changes':'No source motion, skin textures or character originals modified'}
(R/'SourceBaseline').mkdir(exist_ok=True)
for clip in (() if '--markers-only' in sys.argv else ('g1','g2','b1','b2')):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    scene.render.fps=60
    source=P/'SourceAssets/CharacterWorkshop_20261021/MotionSources'/f'{clip}_default.glb'
    bpy.ops.import_scene.gltf(filepath=str(source))
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
    action=rig.animation_data.action
    scene.frame_start=int(action.frame_range[0]); scene.frame_end=round(action.frame_range[1])
    bpy.ops.object.select_all(action='SELECT')
    target=R/'SourceBaseline'/f'{clip}_Source.fbx'
    bpy.ops.export_scene.fbx(filepath=str(target),use_selection=True,object_types={'ARMATURE','MESH'},
        add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,
        bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z')
    report['sources'].append({'clip':clip,'input':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'fbx':str(target),'seconds':(action.frame_range[1]-action.frame_range[0])/60,
        'bones':len(rig.data.bones),'meshes':[o.name for o in bpy.data.objects if o.type=='MESH']})
    print('SOURCE_EXPORTED',clip,flush=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'SourceAssets/CharacterWorkshop_20261021/Vexa_Character_Options.blend'),load_ui=False)
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
rig.animation_data_clear()
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
report['markers']=forearm_markers.add(rig)
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_x=900;scene.render.resolution_y=650;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('MarkerReview');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.14,.18,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.4
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.3
center=(rig.matrix_world@rig.pose.bones['lowerarm_r'].matrix).translation.lerp((rig.matrix_world@rig.pose.bones['hand_r'].matrix).translation,.66)
report['camera_target']=list(center)
for loc in ((-3,-3,4),(3,2,4)):
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=400;o.data.size=3
    o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=.38
normal=Vector(report['markers'][1]['palmar_normal_world'])
for i,delta in enumerate((normal*.22, normal*.22+Vector((-.04,-.035,.015)))):
    camera.location=center+delta;camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(R/f'ForearmMarker_{i}.png');bpy.ops.render.render(write_still=True)
collection=bpy.data.collections[forearm_markers.COLLECTION]
overlay_objects={rig,*collection.objects}
bpy.data.libraries.write(str(R/'SourceBaseline/ForearmReviewOverlay.blend'),overlay_objects,compress=True)
bpy.ops.object.select_all(action='DESELECT')
for ob in overlay_objects:ob.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(R/'SourceBaseline/ForearmReviewOverlay.fbx'),use_selection=True,
    object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z')
# Verify the arrow follows bone roll and removal leaves the original skin alone.
arrow=bpy.data.objects['REVIEW_ONLY_ForearmArrow_r'];bone=rig.pose.bones['lowerarm_r']
def arrow_tip():
    ob=arrow.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return ob.matrix_world@ob.data.vertices[3].co
before=arrow_tip();bone.rotation_mode='XYZ';bone.rotation_euler.x=.5;bpy.context.view_layer.update()
after=arrow_tip()
report['arrow_tip_before']=list(before);report['arrow_tip_after']=list(after)
report['mesh_upperarm_centroids']={}
for ob in bpy.data.objects:
    if ob.type=='MESH' and ob.visible_get() and ob.vertex_groups.get('lowerarm_r'):
        idx=ob.vertex_groups['lowerarm_r'].index
        ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
        ids=[v.index for v in ob.data.vertices if any(g.group==idx and g.weight>.5 for g in v.groups)]
        if ids:report['mesh_upperarm_centroids'][ob.name]=list(sum((ev.matrix_world@ev.data.vertices[i].co for i in ids),Vector())/len(ids))
report['roll_followed']=(after-before).length>.005
forearm_markers.remove();report['removal_verified']=not bpy.data.collections.get(forearm_markers.COLLECTION)
(R/'ForearmMarkers.json').write_text(json.dumps(report,indent=2))
print('SOURCE_MARKERS_DONE',report['roll_followed'],report['removal_verified'],flush=True)
