"""Fresh Blender/GLB round-trip checks and CPU render; no Unreal access."""
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


def inspect_mesh(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    # glTF splits vertices at UV/normal seams. Weld only this disposable audit.
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.000001)
    result = {
        'name': obj.name,
        'triangles': len(mesh.loop_triangles),
        'boundary_edges_after_audit_weld': sum(e.is_boundary for e in bm.edges),
        'nonmanifold_edges_after_audit_weld': sum(not e.is_manifold for e in bm.edges),
        'zero_area_faces': sum(f.calc_area() < 1e-12 for f in bm.faces),
        'finite_vertices': all(math.isfinite(c) for v in bm.verts for c in v.co),
        'signed_volume': bm.calc_volume(signed=True),
        'uv_layers': len(mesh.uv_layers),
    }
    bm.free()
    evaluated.to_mesh_clear()
    return result


def main():
    assert bpy.app.background
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    opt = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    out = opt.output.resolve(strict=True)
    authored = json.loads((out / 'RepairReport.json').read_text())
    blend = out / 'CurvedBench_Repaired.blend'
    glb = out / 'CurvedBench_Repaired.glb'
    before = {str(p): sha(p) for p in [blend, glb, Path(authored['source'])]}
    bpy.ops.wm.open_mainfile(filepath=str(blend), load_ui=False)
    collection = bpy.data.collections['REPAIRED - editable parts']
    parts = [o for o in collection.objects if o.type == 'MESH']
    deps = bpy.context.evaluated_depsgraph_get()
    corners = [o.evaluated_get(deps).matrix_world @ Vector(c)
               for o in parts for c in o.evaluated_get(deps).bound_box]
    blend_dimensions = [max(p[k] for p in corners)-min(p[k] for p in corners) for k in range(3)]
    original = bpy.data.collections['REFERENCE - original source - hidden']
    result = {
        'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'blend_part_count': len(parts),
        'blend_evaluated_dimensions_m': blend_dimensions,
        'blend_meshes': [inspect_mesh(o, deps) for o in parts],
        'original_hidden': original.hide_render and original.hide_viewport,
        'original_packed_images': sum(bool(i.packed_file) for i in bpy.data.images),
        'blend_render_device': bpy.context.scene.cycles.device,
    }
    # Keep the exact CPU studio, replace only the disposable repaired assembly.
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.import_scene.gltf(filepath=str(glb))
    imported = list(bpy.context.selected_objects)
    imported_meshes = [o for o in imported if o.type == 'MESH']
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    result['glb_part_count'] = len(imported_meshes)
    result['glb_meshes'] = [inspect_mesh(o, deps) for o in imported_meshes]
    result['glb_materials'] = sorted({m.name for o in imported_meshes for m in o.data.materials})
    corners = [o.matrix_world @ Vector(c) for o in imported_meshes for c in o.bound_box]
    result['glb_dimensions_m'] = [max(p[k] for p in corners)-min(p[k] for p in corners) for k in range(3)]
    result['glb_floor_m'] = min(p.z for p in corners)
    result['glb_triangles'] = sum(m['triangles'] for m in result['glb_meshes'])
    result['geometry_checks_pass'] = all(
        m['nonmanifold_edges_after_audit_weld'] == 0 and m['zero_area_faces'] == 0
        and m['finite_vertices'] and m['signed_volume'] > 0 and m['uv_layers'] > 0
        for m in result['blend_meshes'] + result['glb_meshes'])
    scene = bpy.context.scene
    scene.cycles.device = 'CPU'
    scene.render.filepath = str(out / 'GLBRoundTrip.png')
    bpy.ops.render.render(write_still=True)
    result['files_unchanged'] = all(sha(Path(p)) == h for p, h in before.items())
    result['source_matches_original'] = before[authored['source']] == authored['source_sha256']
    (out / 'Verification.json').write_text(json.dumps(result, indent=2))
    assert result['geometry_checks_pass'], 'Mesh checks failed; inspect Verification.json'
    assert result['blend_part_count'] == result['glb_part_count'] == 43
    assert result['original_hidden'] and result['original_packed_images'] == 3
    assert result['files_unchanged'] and result['source_matches_original']
    # Compare evaluated geometry: bevels legitimately trim the editable cage bounds.
    assert max(abs(a-b) for a, b in zip(result['glb_dimensions_m'], blend_dimensions)) < .00001
    assert result['glb_triangles'] == sum(m['triangles'] for m in result['blend_meshes'])
    print('BENCH_ROUNDTRIP_PASS', flush=True)


if __name__ == '__main__':
    main()
