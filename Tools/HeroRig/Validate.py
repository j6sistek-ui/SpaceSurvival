import bpy, json, math, hashlib
from pathlib import Path
from mathutils import Vector, Quaternion
OUT=Path(__file__).resolve().parents[2] / ".agent/local/ReplacementHero"
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT/'SquirrelHero_Rigged.blend'))
rig=bpy.data.objects['Armature'];mesh=bpy.data.objects['SquirrelHero_Replacement'];scene=bpy.context.scene
ids=json.loads((OUT/'repair_vertices.json').read_text())
def rotate(name,axis,degrees):
    pb=rig.pose.bones[name];world_rest=rig.matrix_world@pb.bone.matrix_local
    local_axis=world_rest.to_3x3().inverted()@Vector(axis)
    pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion(local_axis,math.radians(degrees))
def reset():
    for pb in rig.pose.bones:pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion();pb.location=(0,0,0);pb.scale=(1,1,1)
def shape_digest():
    return hashlib.sha256(str(([tuple(v.co) for v in mesh.data.vertices],[tuple(p.vertices) for p in mesh.data.polygons],[tuple(v.uv) for v in mesh.data.uv_layers.active.data])).encode()).hexdigest()
baseline=shape_digest();report={'mesh_vertices':len(mesh.data.vertices),'triangles':len(mesh.data.polygons),'poses':[]}
rig.animation_data_create();rig.animation_data.action=None
for action in list(bpy.data.actions):
    if action.name.startswith('Rig_Check_Not_Gameplay'):bpy.data.actions.remove(action)
rig.animation_data.action=bpy.data.actions.new('Rig_Check_Not_Gameplay')
scene.render.fps=24;scene.frame_start=1;scene.frame_end=101
def keypose(frame):
    for pb in rig.pose.bones:pb.keyframe_insert(data_path='rotation_quaternion',frame=frame)
reset();keypose(1)
for label in ['stride','crouch','twist']:
    reset();rotate('upperarm_l',(0,1,0),65);rotate('upperarm_r',(0,1,0),-65)
    if label=='stride':
        rotate('thigh_l',(1,0,0),-35);rotate('thigh_r',(1,0,0),25);rotate('calf_l',(1,0,0),40);rotate('calf_r',(1,0,0),15)
    elif label=='crouch':
        for s in ['l','r']:rotate('thigh_'+s,(1,0,0),-65);rotate('calf_'+s,(1,0,0),90)
        rotate('spine_01',(1,0,0),12)
    else:rotate('spine_02',(0,0,1),25);rotate('head',(0,0,1),35);rotate('spine_01',(1,0,0),15)
    for i in range(1,8):rotate('tail_%02d'%i,(0,0,1),3*math.sin(i*.5))
    bpy.context.view_layer.update()
    keypose({'stride':26,'crouch':51,'twist':76}[label])
    e=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());deformed=e.to_mesh()
    assert all(math.isfinite(c) for v in deformed.vertices for c in v.co)
    # Distance invariance across the rigid pack, against rest-space geometry.
    anchor=ids['backpack'][0];world=mesh.matrix_world.to_3x3();maxerr=max(abs((world@(deformed.vertices[i].co-deformed.vertices[anchor].co)).length-(world@(mesh.data.vertices[i].co-mesh.data.vertices[anchor].co)).length) for i in ids['backpack'])
    report['poses'].append({'name':label,'backpack_max_distance_error_m':maxerr});e.to_mesh_clear()
    print('PACK_DEFORMATION',label,maxerr,'object scale',list(mesh.scale),'bone scale',list(rig.pose.bones['backpack'].matrix.to_scale()),flush=True)
    assert maxerr<1e-5
    for view,loc in [('front',(1,-2,.9)),('back',(-1,2,.9))]:
        scene.camera.location=loc;scene.camera.rotation_euler=(Vector((0,0,.45))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/(label+'-'+view+'.png'));bpy.ops.render.render(write_still=True)
reset();bpy.context.view_layer.update()
keypose(101);scene.frame_set(1)
assert shape_digest()==baseline
report['mesh_and_uv_unchanged_during_poses']=True
report['max_weight_sum_error']=max(abs(sum(g.weight for g in v.groups)-1) for v in mesh.data.vertices)
assert report['max_weight_sum_error']<1e-4
report['tail_has_no_thigh_weights']=all(not any(mesh.vertex_groups[g.group].name.startswith('thigh') and g.weight>0 for g in mesh.data.vertices[i].groups) for i in ids['tail'])
assert report['tail_has_no_thigh_weights']
report['max_influences']=max(sum(g.weight>1e-7 for g in v.groups) for v in mesh.data.vertices)
assert report['max_influences']<=4
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'SquirrelHero_Rigged.blend'))
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);mesh.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(OUT/'SquirrelHero_Rigged.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',use_mesh_modifiers=False)
bpy.ops.export_scene.gltf(filepath=str(OUT/'SquirrelHero_Rigged.glb'),export_format='GLB',use_selection=True,export_animations=False)
(OUT/'validation.json').write_text(json.dumps(report,indent=2))
print('HERO_RIG_VALIDATE_OK')
