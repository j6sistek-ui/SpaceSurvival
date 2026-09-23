import bpy, json, hashlib, math
from pathlib import Path
OUT=Path(__file__).resolve().parents[2] / ".agent/local/ReplacementHero"
OUT.mkdir(parents=True, exist_ok=True)
def geom(mesh):
    return hashlib.sha256(str(([tuple(v.co) for v in mesh.data.vertices],[tuple(p.vertices) for p in mesh.data.polygons],[tuple(v.uv) for v in mesh.data.uv_layers.active.data])).encode()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(OUT/'sci-fi_squirrel_3d_model.blend'));source=geom(next(o for o in bpy.context.scene.objects if o.type=='MESH'))
bpy.ops.wm.open_mainfile(filepath=str(OUT/'SquirrelHero_Rigged.blend'));mesh=bpy.data.objects['SquirrelHero_Replacement'];rig=bpy.data.objects['Armature']
assert geom(mesh)==source
report={'source_geometry_and_uv_sha256':source,'source_geometry_and_uv_preserved':True,'clips':{}}
def pose(kind,frame):
    rig.animation_data.action=bpy.data.actions['Tail_'+kind];bpy.context.scene.frame_set(frame)
    return [rig.pose.bones['tail_%02d'%i].rotation_quaternion.copy() for i in range(1,8)]
for kind,last in [('Idle',361),('Walk',31),('Run',19),('JumpAir',25)]:
    a,b=pose(kind,1),pose(kind,last);err=max(min(sum((x-y)**2 for x,y in zip(q,r)),sum((x+y)**2 for x,y in zip(q,r)))**.5 for q,r in zip(a,b));assert err<1e-5;report['clips'][kind]={'loop_endpoint_quaternion_error':err}
for left,frame,right in [('JumpStart',10,'JumpAir'),('JumpAir',25,'JumpLand')]:
    a,b=pose(left,frame),pose(right,1);err=max(sum((x-y)**2 for x,y in zip(q,r))**.5 for q,r in zip(a,b));print('TRANSITION',left,right,err,flush=True);assert err<1e-5;report['clips'][left+'_to_'+right]={'transition_quaternion_error':err}
for ext in ['fbx','glb']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if ext=='fbx':bpy.ops.import_scene.fbx(filepath=str(OUT/('SquirrelHero_Rigged.'+ext)))
    else:bpy.ops.import_scene.gltf(filepath=str(OUT/('SquirrelHero_Rigged.'+ext)))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)];bones=[b.name for o in bpy.context.scene.objects if o.type=='ARMATURE' for b in o.data.bones]
    tris=0
    for m in meshes:m.data.calc_loop_triangles();tris+=len(m.data.loop_triangles)
    print('EXPORT',ext,tris,len(bones),flush=True)
    assert tris==75183 and all('tail_%02d'%i in bones for i in range(1,8)) and 'backpack' in bones
    report[ext]={'triangles':tris,'bones':len(bones),'root_present':'root' in bones,'tail_and_backpack_present':True}
(OUT/'roundtrip.json').write_text(json.dumps(report,indent=2));print('ROUNDTRIP_OK')
