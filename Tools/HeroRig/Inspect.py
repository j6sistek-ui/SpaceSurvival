import bpy, json
from pathlib import Path
OUT = Path(__file__).resolve().parents[2] / ".agent/local/ReplacementHero"
OUT.mkdir(parents=True, exist_ok=True)
results = []
for path in [OUT / (name + '.fbx') for name in ('sci-fi_squirrel_3d_model', 'space-suited_squirrel_3d_model')]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(path))
    row = {'file': path.name, 'objects': []}
    for obj in bpy.context.scene.objects:
        item = {'name': obj.name, 'type': obj.type, 'dimensions': list(obj.dimensions)}
        if obj.type == 'ARMATURE':
            item['bones'] = [{'name': b.name, 'parent': b.parent.name if b.parent else None, 'head': list(b.head_local), 'tail': list(b.tail_local)} for b in obj.data.bones]
        elif obj.type == 'MESH':
            obj.data.calc_loop_triangles()
            item.update(vertices=len(obj.data.vertices), triangles=len(obj.data.loop_triangles), materials=[m.name for m in obj.data.materials], groups=[g.name for g in obj.vertex_groups])
        row['objects'].append(item)
    bpy.ops.wm.save_as_mainfile(filepath=str(path.with_suffix('.blend')))
    results.append(row)
(OUT / 'inspection.json').write_text(json.dumps(results, indent=2))
print('HERO_INSPECTION_OK')
