"""Native Blender regression: proxy meshes exclude bone widgets and retain world bounds.

Run with --background --factory-startup --python-exit-code 1 --python this.py --
  --snapshot scene.json --report report.json
The input snapshot is read only; no working .blend or preferences are loaded/saved.
"""
import argparse
import json
from pathlib import Path
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).parent))
from ss_live_link import core
from ss_live_link.proxy_cache import snapshot_mesh_key
from build_asset_library import imported_data, release_imported


def bounds(points):
    low, high = [float('inf')] * 3, [float('-inf')] * 3
    for point in points:
        for axis in range(3):
            low[axis] = min(low[axis], point[axis])
            high[axis] = max(high[axis], point[axis])
    return [low, high]


def check_proxy(asset, path):
    path = path.resolve()
    before = imported_data()
    bpy.ops.import_scene.gltf(filepath=str(path))
    bpy.context.view_layer.update()
    new = [obj for obj in bpy.data.objects if obj not in before['objects']]
    meshes = [obj for obj in new if obj.type == 'MESH']
    widgets = {bone.custom_shape for obj in new if obj.type == 'ARMATURE'
               for bone in obj.pose.bones if bone.custom_shape is not None}
    linked = [obj for obj in meshes if bpy.context.view_layer.objects.get(obj.name) is obj
              and obj not in widgets]
    assert linked, f'No linked source meshes: {asset}'
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = [obj.evaluated_get(depsgraph) for obj in linked]
    report = {'asset': asset, 'imported_meshes': [
        {'name': obj.name, 'vertices': len(obj.data.vertices), 'bone_widget': obj in widgets,
         'scenes': [scene.name for scene in obj.users_scene],
         'in_view_layer': bpy.context.view_layer.objects.get(obj.name) is obj}
        for obj in meshes], 'legacy_first_mesh': meshes[0].name,
        'linked_meshes': len(linked), 'excluded_meshes': len(meshes) - len(linked),
        'raw_bounds': bounds(obj.matrix_world @ vertex.co
                             for obj in linked for vertex in obj.data.vertices),
        'expected_vertices': sum(len(obj.data.vertices) for obj in evaluated),
        'expected_polygons': sum(len(obj.data.polygons) for obj in evaluated),
        'expected_bounds': bounds(obj.matrix_world @ vertex.co
                                  for obj in evaluated for vertex in obj.data.vertices)}
    print('SS_PROXY_GEOMETRY_SOURCE ' + json.dumps(report), flush=True)
    release_imported(before)
    bpy.context.view_layer.update()
    core.library_dir = lambda: path.parent
    key = snapshot_mesh_key(asset, path)
    # An old cached mesh is kept for existing scenes, but cannot answer a new import.
    old = bpy.data.meshes.new(key)
    old.from_pydata([(123, 456, 789)], [], [])
    old.use_fake_user = True
    try:
        mesh = core.proxy_mesh({'asset': asset, 'proxy': str(path)}, key, True)
        report.update(vertices=len(mesh.vertices), polygons=len(mesh.polygons),
                      bounds=bounds(vertex.co for vertex in mesh.vertices), cache_name=mesh.name)
        assert mesh is not old and len(old.vertices) == 1, 'old cache was reused or changed'
        assert mesh is core.proxy_mesh({'asset': asset, 'proxy': str(path)}, key, True), 'cache missed'
        assert report['vertices'] == report['expected_vertices'], report
        assert report['polygons'] == report['expected_polygons'], report
        error = max(abs(a - b) for first, second in zip(report['bounds'], report['expected_bounds'])
                    for a, b in zip(first, second))
        report['maximum_bounds_error_metres'] = error
        assert error < 0.0001, report
        assert set(bpy.data.objects) == before['objects'], 'imported objects were left behind'
        print('SS_PROXY_GEOMETRY_CASE ' + json.dumps(report), flush=True)
        return report
    finally:
        release_imported(before)
        bpy.context.view_layer.update()


def compound_proxy(path):
    """Two meshes under a transformed parent exercise join and parent transform baking."""
    before = imported_data()
    core.deselect_all(bpy.context)
    parent = bpy.data.objects.new('TransformedParent', None)
    bpy.context.scene.collection.objects.link(parent)
    parent.matrix_world = Matrix.Translation((4, 5, 6)) @ Matrix.Rotation(0.37, 4, 'Z')
    parent.select_set(True)
    for index in range(2):
        mesh = bpy.data.meshes.new('Triangle')
        mesh.from_pydata([(0, 0, 0), (2, 0, 0), (0, 3, 0)], [], [(0, 1, 2)])
        obj = bpy.data.objects.new('Part' + str(index), mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.parent = parent
        obj.location = (index * 5, 0, 0)
        obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True)
    release_imported(before)
    bpy.context.view_layer.update()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    snapshot = json.loads(args.snapshot.read_text(encoding='utf-8'))
    selected = [(asset, Path(path)) for asset, path in snapshot['proxies'].items()
                if asset.endswith('/Stellar_Phoenix.Stellar_Phoenix')
                or asset.endswith('/Stellar_Phoenix_AirBrake.Stellar_Phoenix_AirBrake')
                or asset.endswith('/SKM_Nyxar.SKM_Nyxar')
                or '/SK_NaniteSkeletal_Mech' in asset]
    assert len(selected) == 9, f'Expected nine skeletal proxies, found {len(selected)}'
    selected.sort(key=lambda row: ('Stellar_Phoenix.Stellar_Phoenix' not in row[0], row[0]))
    result = {'blender_version': bpy.app.version_string, 'snapshot': str(args.snapshot), 'cases': []}
    for asset, path in selected:
        result['cases'].append(check_proxy(asset, path))
        args.report.write_text(json.dumps(result, indent=2), encoding='utf-8')
    compound = args.report.parent / 'compound.glb'
    compound_proxy(compound)
    result['cases'].append(check_proxy('/Game/Test/Compound.Compound', compound))
    result['passed'] = True
    args.report.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('SS_PROXY_GEOMETRY_OK ' + json.dumps({'cases': len(result['cases']), 'report': str(args.report)}))


if __name__ == '__main__':
    main()
