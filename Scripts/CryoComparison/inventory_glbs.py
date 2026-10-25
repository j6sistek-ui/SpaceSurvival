"""Read-only source GLB structural inventory using Python's standard library."""
import collections
import hashlib
import json
from pathlib import Path
import struct

SOURCE = Path(r'C:/Users/j6sis/Downloads/CRYO')
TARGET = Path(__file__).with_name('glb-baseline.json')


def dimensions(data):
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        w, h = struct.unpack_from('>II', data, 16)
        return {'format': 'PNG', 'width': w, 'height': h}
    if data.startswith(b'\xff\xd8'):
        i = 2
        while i + 3 < len(data):
            if data[i] != 255:
                i += 1
                continue
            while i < len(data) and data[i] == 255:
                i += 1
            marker = data[i]
            i += 1
            if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
                continue
            length = struct.unpack_from('>H', data, i)[0]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack_from('>HH', data, i + 3)
                return {'format': 'JPEG', 'width': w, 'height': h}
            i += length
    return {'format': 'UNKNOWN'}


def inspect(path):
    raw = path.read_bytes()
    magic, version, total = struct.unpack_from('<4sII', raw)
    assert magic == b'glTF' and total == len(raw)
    offset = 12
    chunks = []
    doc = None
    binary = None
    while offset < total:
        size, tag = struct.unpack_from('<I4s', raw, offset)
        content = raw[offset + 8:offset + 8 + size]
        chunks.append({'type': tag.decode('ascii').rstrip('\0'), 'bytes': size})
        if tag == b'JSON':
            doc = json.loads(content)
        elif tag == b'BIN\0':
            binary = content
        offset += 8 + size
    accessors = doc.get('accessors', [])
    meshes = []
    total_vertices = total_triangles = 0
    modes = {0: 'POINTS', 1: 'LINES', 2: 'LINE_LOOP', 3: 'LINE_STRIP', 4: 'TRIANGLES', 5: 'TRIANGLE_STRIP', 6: 'TRIANGLE_FAN'}
    for mi, mesh in enumerate(doc.get('meshes', [])):
        primitives = []
        for pi, prim in enumerate(mesh.get('primitives', [])):
            attributes = prim.get('attributes', {})
            pos = accessors[attributes['POSITION']] if 'POSITION' in attributes else {}
            vertices = pos.get('count', 0)
            index_count = accessors[prim['indices']]['count'] if 'indices' in prim else vertices
            mode = prim.get('mode', 4)
            triangles = index_count // 3 if mode == 4 else max(0, index_count - 2) if mode in (5, 6) else 0
            total_vertices += vertices
            total_triangles += triangles
            material_index = prim.get('material')
            material_name = doc.get('materials', [])[material_index].get('name') if material_index is not None else None
            primitives.append({'index': pi, 'vertices': vertices, 'index_count': index_count, 'triangles': triangles, 'mode': modes.get(mode, mode), 'material_index': material_index, 'material_name': material_name, 'attributes': attributes, 'position_accessor_bounds': {'min': pos.get('min'), 'max': pos.get('max')}, 'morph_targets': len(prim.get('targets', [])), 'extensions': prim.get('extensions', {})})
        meshes.append({'index': mi, 'name': mesh.get('name'), 'primitives': primitives, 'weights': mesh.get('weights')})
    materials = []
    for mi, mat in enumerate(doc.get('materials', [])):
        materials.append({'index': mi, 'name': mat.get('name'), 'alphaMode': mat.get('alphaMode', 'OPAQUE'), 'alphaCutoff': mat.get('alphaCutoff', 0.5), 'doubleSided': mat.get('doubleSided', False), 'pbrMetallicRoughness': mat.get('pbrMetallicRoughness', {}), 'normalTexture': mat.get('normalTexture'), 'occlusionTexture': mat.get('occlusionTexture'), 'emissiveTexture': mat.get('emissiveTexture'), 'emissiveFactor': mat.get('emissiveFactor', [0, 0, 0]), 'extensions': mat.get('extensions', {})})
    images = []
    for ii, im in enumerate(doc.get('images', [])):
        item = {'index': ii, 'name': im.get('name'), 'mimeType': im.get('mimeType'), 'bufferView': im.get('bufferView'), 'uri': im.get('uri')}
        if 'bufferView' in im:
            bv = doc['bufferViews'][im['bufferView']]
            assert bv.get('buffer', 0) == 0
            start = bv.get('byteOffset', 0)
            data = binary[start:start + bv['byteLength']]
            item.update({'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), **dimensions(data)})
        images.append(item)
    return {'file': str(path), 'filename': path.name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'glb_version': version, 'asset': doc.get('asset'), 'chunks': chunks, 'counts': {'meshes': len(meshes), 'primitives': sum(len(m['primitives']) for m in meshes), 'nodes': len(doc.get('nodes', [])), 'vertices_primitive_sum': total_vertices, 'triangles_primitive_sum': total_triangles, 'materials': len(materials), 'textures': len(doc.get('textures', [])), 'images': len(images), 'embedded_image_bytes': sum(i.get('bytes', 0) for i in images), 'animations': len(doc.get('animations', [])), 'skins': len(doc.get('skins', []))}, 'meshes': meshes, 'materials': materials, 'images': images, 'textures': doc.get('textures', []), 'nodes': doc.get('nodes', []), 'scenes': doc.get('scenes', []), 'default_scene': doc.get('scene'), 'animations': doc.get('animations', []), 'skins': doc.get('skins', []), 'accessor_bounds': [{'index': i, 'type': a.get('type'), 'count': a.get('count'), 'min': a.get('min'), 'max': a.get('max')} for i, a in enumerate(accessors) if 'min' in a or 'max' in a], 'extensionsUsed': doc.get('extensionsUsed', []), 'extensionsRequired': doc.get('extensionsRequired', [])}


results = [inspect(p) for p in sorted(SOURCE.glob('*.glb'))]
TARGET.write_text(json.dumps({'scope': 'Read-only source structural inventory; no post-finishing evaluation or runtime claim.', 'assets': results}, indent=2), encoding='utf-8')
for result in results:
    print(json.dumps({'filename': result['filename'], 'sha256': result['sha256'], 'counts': result['counts'], 'meshes': [m['name'] for m in result['meshes']], 'materials': [m['name'] for m in result['materials']], 'images': [{'width': i.get('width'), 'height': i.get('height'), 'format': i.get('format')} for i in result['images']], 'extensionsUsed': result['extensionsUsed']}))
print('Written:', TARGET)
