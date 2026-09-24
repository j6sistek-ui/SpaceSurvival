"""Focused export and skin checks for the optional tail-only fur derivative."""
import bpy,json,math
from pathlib import Path
OUT=Path(__file__).resolve().parents[2] / ".agent/local/ReplacementHero"
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT/'SquirrelHero_SoftFur.blend'))
meshes=[bpy.data.objects[n] for n in ['SquirrelHero_Replacement','Tail_FurCards']]
report={'max_weight_error':max(abs(sum(g.weight for g in v.groups)-1) for m in meshes for v in m.data.vertices),'max_influences':max(len(v.groups) for m in meshes for v in m.data.vertices)}
assert report['max_weight_error']<1e-4 and report['max_influences']<=4
rig=bpy.data.objects['Armature']
for clip,last in [('JumpStart',10),('JumpAir',25),('JumpLand',27)]:
    rig.animation_data.action=bpy.data.actions['Tail_'+clip]
    for frame in range(1,last+1):
        bpy.context.scene.frame_set(frame)
        for m in meshes:
            evaluated=m.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
            assert all(math.isfinite(c) for v in mesh.vertices for c in v.co)
            evaluated.to_mesh_clear()
report['all_jump_frames_finite']=True
for ext in ['fbx','glb']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if ext=='fbx':bpy.ops.import_scene.fbx(filepath=str(OUT/('SquirrelHero_SoftFur.'+ext)))
    else:bpy.ops.import_scene.gltf(filepath=str(OUT/('SquirrelHero_SoftFur.'+ext)))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
    bones=[b.name for o in bpy.context.scene.objects if o.type=='ARMATURE' for b in o.data.bones]
    count=0
    for mesh in meshes:mesh.data.calc_loop_triangles();count+=len(mesh.data.loop_triangles)
    assert count==76623 and len(bones)==69
    report[ext]={'triangles':count,'bones':len(bones)}
(OUT/'fur_validation.json').write_text(json.dumps(report,indent=2))
print('FUR_VALIDATION_OK',json.dumps(report))
