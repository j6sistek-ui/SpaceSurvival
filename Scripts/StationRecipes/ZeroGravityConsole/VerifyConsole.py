"""Fresh reload, solid mesh and texture checks, then a CPU GLB render.

Run in hidden Blender with -- --output <delivery>. Does not resave delivery files.
"""
import argparse
import datetime
import hashlib
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(parts):
    deps = bpy.context.evaluated_depsgraph_get()
    corners = []
    meshes = []
    for obj in parts:
        evaluated = obj.evaluated_get(deps)
        mesh = evaluated.to_mesh()
        mesh.calc_loop_triangles()
        corners.extend(evaluated.matrix_world @ Vector(c) for c in evaluated.bound_box)
        bm = bmesh.new()
        bm.from_mesh(mesh)
        # Only the disposable audit mesh is welded; glTF separates UV/normal seams.
        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=.000001)
        meshes.append({
            'name': obj.name, 'triangles': len(mesh.loop_triangles),
            'nonmanifold_after_audit_weld': sum(not e.is_manifold for e in bm.edges),
            'zero_area_faces': sum(f.calc_area() < 1e-12 for f in bm.faces),
            'signed_volume': bm.calc_volume(signed=True),
            'finite': all(math.isfinite(c) for v in bm.verts for c in v.co),
            'uv_layers': len(mesh.uv_layers),
        })
        bm.free()
        evaluated.to_mesh_clear()
    images = set()
    for obj in parts:
        for mat in obj.data.materials:
            if mat and mat.node_tree:
                images.update(n.image for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image)
    return {'part_count': len(parts), 'meshes': meshes,
            'triangles': sum(m['triangles'] for m in meshes),
            'dimensions_m': [max(p[i] for p in corners)-min(p[i] for p in corners) for i in range(3)],
            'floor_m': min(p.z for p in corners),
            'materials': sorted({m.name for o in parts for m in o.data.materials if m}),
            'images': [{'name': i.name, 'size': list(i.size), 'packed': bool(i.packed_file)} for i in images]}


def main():
    assert bpy.app.background
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    out = args.output.resolve(strict=True)
    report = json.loads((out/'RepairReport.json').read_text())
    blend = out/'ZeroGravityConsole_Repaired.blend'
    glb = out/'ZeroGravityConsole_Repaired.glb'
    source = Path(report['source'])
    before = {str(p): sha(p) for p in [blend, glb, source]}
    bpy.ops.wm.open_mainfile(filepath=str(blend), load_ui=False)
    original = bpy.data.collections['REFERENCE - original source - hidden']
    collection = bpy.data.collections['REPAIRED - editable parts']
    result = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'original_hidden': original.hide_render and original.hide_viewport,
              'blend_render_device': bpy.context.scene.cycles.device,
              'packed_images_in_blend': sum(bool(i.packed_file) for i in bpy.data.images)}
    result['blend'] = inspect([o for o in collection.objects if o.type == 'MESH'])
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.import_scene.gltf(filepath=str(glb))
    parts = [o for o in bpy.context.selected_objects if o.type == 'MESH']
    bpy.context.view_layer.update()
    result['glb'] = inspect(parts)
    result['geometry_checks_pass'] = all(
        m['nonmanifold_after_audit_weld'] == 0 and m['zero_area_faces'] == 0
        and m['finite'] and m['signed_volume'] > 0 and m['uv_layers'] > 0
        for group in [result['blend'], result['glb']] for m in group['meshes'])
    scene = bpy.context.scene
    scene.cycles.device = 'CPU'
    scene.render.filepath = str(out/'GLBRoundTrip.png')
    bpy.ops.render.render(write_still=True)
    result['files_unchanged'] = all(sha(Path(p)) == h for p,h in before.items())
    result['source_matches_original'] = sha(source) == report['source_sha256']
    (out/'Verification.json').write_text(json.dumps(result, indent=2))
    assert result['geometry_checks_pass'], 'Inspect Verification.json for failed parts'
    assert result['original_hidden'] and result['packed_images_in_blend'] == 7
    assert result['blend_render_device'] == 'CPU'
    assert result['blend']['part_count'] == result['glb']['part_count'] == report['part_count']
    assert result['blend']['triangles'] == result['glb']['triangles']
    assert max(abs(a-b) for a,b in zip(result['blend']['dimensions_m'],result['glb']['dimensions_m'])) < .00001
    assert abs(result['glb']['floor_m']) < .00001
    assert len(result['blend']['images']) == len(result['glb']['images']) == 4
    assert all(i['packed'] and min(i['size']) > 0 for i in result['glb']['images'])
    assert result['files_unchanged'] and result['source_matches_original']
    print('CONSOLE_ROUNDTRIP_PASS', flush=True)


if __name__ == '__main__':
    main()
