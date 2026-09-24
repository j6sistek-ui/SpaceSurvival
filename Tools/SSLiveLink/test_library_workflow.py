"""Focused Blender checks for pop-out data, offline transfer, and surface isolation.
Run with --background --factory-startup --python-exit-code 1 --python this.py.
"""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import zipfile

import bpy

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import ss_live_link as sl


def module(name):
    spec = importlib.util.spec_from_file_location(name, TOOLS / (name + '.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


root = Path(tempfile.mkdtemp(prefix='ss-library-test-'))
lib = root / 'Artifacts/PrefabLibrary'
lib.mkdir(parents=True)
(root / 'SSPortableLibrary.json').write_text('{"schema_version":1}')
sl.core.project_root = lambda: root
sl.register()
sl.unregister()
sl.register()
bpy.ops.mesh.primitive_cube_add()
cube = bpy.context.object
cube.name = 'SourceCube'
proxy = lib / 'cube.glb'
bpy.ops.export_scene.gltf(filepath=str(proxy), export_format='GLB', use_selection=True)
row = {'asset': '/Game/Test/Wall.Wall', 'name': 'Wall', 'pack': 'Test', 'group': 'Building',
       'category': 'Walls', 'proxy': 'cube.glb', 'materials': ['/Game/Test/Original.Original'],
       'origin': [0, 0, 0], 'extent': [100, 100, 100], 'triangles': 12}
(lib / 'catalog.json').write_text(json.dumps({'meshes': [row]}))
sl.core.load_catalog(force=True)
first = sl.core.add_part(row['asset'], name='A_Wall')
second = sl.core.add_part(row['asset'], name='B_Wall')
values = {'base_color': [0.2, 0.5, 0.8], 'metallic': 1.0, 'roughness': 0.02,
          'opacity': 1.0, 'transmission': 0.0, 'ior': 1.45}
mat = sl.surfaces.assign(first, 0, values)
assert second.active_material != mat, 'surface changed a shared mesh instance'
payload = sl.link_payload([first, second])
assert 'surface_overrides' in payload[0] and 'surface_overrides' not in payload[1]
before = sl.signature(payload[0])
shader = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
shader.inputs['Roughness'].default_value = 0.35
assert sl.signature(sl.link_payload([first])[0]) != before, 'material-only edit was invisible to Live'
duplicate = first.copy()
bpy.context.scene.collection.objects.link(duplicate)
assert len({r['link'] for r in sl.link_payload([first, duplicate])}) == 2, 'duplicated placements share a live ID'
path = sl.save_prefab([first, second], 'Test', 'Pair')
loaded = sl.load_prefab(path)
assert sl.surfaces.describe(loaded[0]) == sl.surfaces.describe(first)
assert sl.surfaces.describe(loaded[1]) == {}
texture = mat.node_tree.nodes.new('ShaderNodeTexNoise')
try:
    sl.surfaces.describe(first)
    raise AssertionError('unsupported shader was silently exported')
except RuntimeError:
    pass
mat.node_tree.nodes.remove(texture)
native = lib / 'BlenderAssets'
module('build_asset_library').build(root, native)
built = json.loads((native / 'build.json').read_text())
assert sl.popout.attach_library().import_method == 'APPEND'
native_file = native / next(iter(built['entries'].values()))['file']
with bpy.data.libraries.load(str(native_file), assets_only=True) as (source, target):
    assert len(source.objects) == 1
    target.objects = source.objects
assert target.objects[0].get(sl.PROP_ASSET) == row['asset']
assert not target.objects[0].get(sl.PROP_LINK), 'library asset must not carry a reusable placement ID'
module('build_asset_library').build(root, native)
assert json.loads((native / 'build.json').read_text())['rebuilt'] == 0, 'unchanged library was rebuilt'
archive = root / 'library.zip'
module('package_portable').package(root, TOOLS.parents[1], native, archive)
relocated = sl.transfer.import_archive(archive, root / 'another-device')
assert (relocated / 'Artifacts/PrefabLibrary/cube.glb').read_bytes() == proxy.read_bytes()
assert (relocated / 'SSPortableLibrary.json').is_file()
# Both traversal and tampering must fail before extracting any library.
malicious = root / 'bad.zip'
with zipfile.ZipFile(malicious, 'w') as z:
    z.writestr('SpaceSurvivalLibrary/../../escape', 'bad')
try:
    sl.transfer.import_archive(malicious, root / 'rejected')
    raise AssertionError('unsafe path was accepted')
except ValueError:
    pass
assert not (root / 'rejected').exists()
tampered = root / 'tampered.zip'
with zipfile.ZipFile(archive) as source, zipfile.ZipFile(tampered, 'w') as target:
    for item in source.infolist():
        data = source.read(item.filename)
        if item.filename.endswith('/cube.glb'):
            data += b'changed'
        target.writestr(item, data)
try:
    sl.transfer.import_archive(tampered, root / 'rejected')
    raise AssertionError('checksum mismatch was accepted')
except ValueError:
    pass
assert not (root / 'rejected').exists()
(lib / 'catalog.json').write_text(json.dumps({'meshes': [row], 'new': True}))
try:
    module('package_portable').package(root, TOOLS.parents[1], native, root / 'stale.zip')
    raise AssertionError('stale prepared library was exported')
except RuntimeError:
    pass
assert not (root / 'stale.zip').exists()
sl.unregister()
print('SS_LIBRARY_WORKFLOW_OK: registration, per-object surfaces, material-only changes, duplicate IDs, prefab roundtrip, native assets, portable relocation, unsafe archive rejection')
