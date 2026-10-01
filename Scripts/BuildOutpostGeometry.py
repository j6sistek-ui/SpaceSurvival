"""Small original architectural mesh kit, Blender background only, metres -> FBX cm."""
import bpy
import math
import sys
from pathlib import Path

OUT = Path(sys.argv[sys.argv.index('--') + 1])
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def ring(name, inner, outer, height, segments=96):
    vertices = []
    for z in (-height / 2, height / 2):
        for radius in (inner, outer):
            vertices += [(radius * math.cos(i * math.tau / segments), radius * math.sin(i * math.tau / segments), z) for i in range(segments)]
    faces = []
    for i in range(segments):
        j = (i + 1) % segments
        faces += [(i,j,segments+j,segments+i),
                  (2*segments+i,3*segments+i,3*segments+j,2*segments+j),
                  (i,2*segments+i,2*segments+j,j),
                  (segments+i,segments+j,3*segments+j,3*segments+i)]
    mesh = bpy.data.meshes.new(name); mesh.from_pydata(vertices, [], faces); mesh.update()
    ob = bpy.data.objects.new(name, mesh); bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bevel = ob.modifiers.new('Machined edges', 'BEVEL'); bevel.width = .025; bevel.segments = 2
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / (name + '.blend')))
    bpy.ops.export_scene.fbx(filepath=str(OUT / (name + '.fbx')), use_selection=True, object_types={'MESH'}, axis_forward='-Y', axis_up='Z', global_scale=1, apply_unit_scale=True, bake_anim=False, add_leaf_bones=False)
    bpy.data.objects.remove(ob, do_unlink=True)

ring('SM_OutpostHalo', .97, 1, .04)
ring('SM_OutpostRoof', .42, 1, .045)
ring('SM_OutpostCollar', .88, 1, .20)
