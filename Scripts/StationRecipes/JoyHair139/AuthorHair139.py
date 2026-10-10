"""CPU trial: suppress three malformed side guides without changing original sources."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[3]/'.agent/local/StationRefinement/JoyHair139/JoyHair139';OUT.mkdir(exist_ok=False)
SRC=Path(__file__).resolve().parents[3]/'.agent/local/StationRefinement/CpuJoy121/JoyBlue114/Joy_LightBlue_HairFitted.blend'
assert hashlib.sha256(SRC.read_bytes()).hexdigest()=='38a31ab08e9e5362d1c60c88ee24f6d7a32be1ba0bb397f58892ea7643508f9b'
bpy.ops.wm.open_mainfile(filepath=str(SRC),load_ui=False,use_scripts=False)
original_hair={o.name:[list(p.position) for p in o.data.points] for o in bpy.context.scene.objects if o.type=='CURVES'}
obj=bpy.data.objects['2.side left 2'];assert len(obj.data.curves)==23
group=bpy.data.node_groups.new('Joy_RemoveStrayGuides','GeometryNodeTree')
group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
entry=group.nodes.new('NodeGroupInput');out=group.nodes.new('NodeGroupOutput')
index=group.nodes.new('GeometryNodeInputIndex');cmp=group.nodes.new('ShaderNodeMath');cmp.operation='COMPARE'
cmp.inputs[1].default_value=15;cmp.inputs[2].default_value=.1
delete=group.nodes.new('GeometryNodeDeleteGeometry');delete.domain='CURVE'
cmp.inputs[1].default_value=10
group.links.new(index.outputs['Index'],cmp.inputs[0]);selection=cmp.outputs[0]
for value in (12,13):
 extra=group.nodes.new('ShaderNodeMath');extra.operation='COMPARE';extra.inputs[1].default_value=value;extra.inputs[2].default_value=.1;group.links.new(index.outputs['Index'],extra.inputs[0])
 add=group.nodes.new('ShaderNodeMath');add.operation='MAXIMUM';group.links.new(selection,add.inputs[0]);group.links.new(extra.outputs[0],add.inputs[1]);selection=add.outputs[0]
group.links.new(selection,delete.inputs['Selection'])
group.links.new(entry.outputs['Geometry'],delete.inputs['Geometry']);group.links.new(delete.outputs['Geometry'],out.inputs['Geometry'])
mod=obj.modifiers.new('Joy_StrayGuideCleanup','NODES');mod.node_group=group
obj.modifiers.move(len(obj.modifiers)-1,0)
scene=bpy.context.scene;rig=bpy.data.objects['Armature']
target=rig.matrix_world@rig.pose.bones['CC_Base_Head'].head+Vector((0,0,.075))
data=bpy.data.cameras.new('JoyHairCamera');camera=bpy.data.objects.new('JoyHairCamera',data);scene.collection.objects.link(camera)
camera.location=target+Vector((0,-2.5,0));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
data.type='ORTHO';data.ortho_scale=.40;scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=48;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_x=768;scene.render.resolution_y=960;scene.render.resolution_percentage=100

# Save the reviewed derivative before temporary rest-space export transforms.
bpy.context.view_layer.update()
evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
assert len(evaluated.data.curves)==1020,len(evaluated.data.curves)
assert original_hair=={o.name:[list(p.position) for p in o.data.points] for o in bpy.context.scene.objects if o.type=='CURVES'}
target=OUT/'Joy_LightBlue_HairClean.blend'
scene.render.filepath=str(OUT/'Joy-hair-cleanup.png')
bpy.ops.wm.save_as_mainfile(filepath=str(target),check_existing=False)
report={'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'derivative_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'raw_guides_preserved':True,'removed_evaluated_guides':[10,12,13],'curve_object':obj.name,'source_guide_count':23,'retained_evaluated_strands':1020,'original_evaluated_strands':1173,'geometry_change':'Non-destructive first modifier removes only three malformed guide bundles. All raw curves remain recoverable.','gpu_rendering':False}
scene.frame_set(1)
rig=bpy.data.objects['Armature'];head=rig.pose.bones['CC_Base_Head']
pose_to_rest=(rig.matrix_world@head.bone.matrix_local)@(rig.matrix_world@head.matrix).inverted()
scalp=bpy.data.objects['[pomiya]node_hair_Flower Collection_rose'];scalp.matrix_world=pose_to_rest@scalp.matrix_world
rig.animation_data_clear();rig.data.pose_position='REST';bpy.context.view_layer.update()
curves=[o for o in scene.objects if o.type=='CURVES' and not o.hide_render and any(m and m.name=='Joy_Purple_Hair_base' for m in o.data.materials)]
assert len(curves)==8
sample_group=bpy.data.node_groups.new('JoyExport_PolylineStrands','GeometryNodeTree')
sample_group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');sample_group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
entry=sample_group.nodes.new('NodeGroupInput');out=sample_group.nodes.new('NodeGroupOutput');sample=sample_group.nodes.new('GeometryNodeResampleCurve');sample.inputs['Mode'].default_value='Count';sample.inputs['Count'].default_value=64
sample_group.links.new(entry.outputs['Geometry'],sample.inputs['Curve']);sample_group.links.new(sample.outputs['Curve'],out.inputs['Geometry'])
bpy.ops.object.select_all(action='DESELECT')
for o in curves:
 mod=o.modifiers.new('JoyExport_LinearFormat','NODES');mod.node_group=sample_group;o.select_set(True)
bpy.context.view_layer.objects.active=curves[0]
abc=OUT/'G_JoyHair_base_Clean.abc'
bpy.ops.wm.alembic_export(filepath=str(abc),start=1,end=1,selected=True,flatten=True,export_hair=True,export_particles=False,global_scale=1.,evaluation_mode='RENDER')
report.update({'abc_sha256':hashlib.sha256(abc.read_bytes()).hexdigest(),'abc_bytes':abc.stat().st_size,'hair_pose_to_rest':[list(r) for r in pose_to_rest],'base_objects':[o.name for o in curves]})
assert report['source_sha256']=='38a31ab08e9e5362d1c60c88ee24f6d7a32be1ba0bb397f58892ea7643508f9b'
(OUT/'Author139.json').write_text(json.dumps(report,indent=2)+'\n')
print('HAIR139_SAVED_EXPORTED',flush=True)
