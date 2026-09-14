"""Read-only OBJ/image/source-identity check for the separate station candidate.

Writes only Validation.json alongside this script when explicitly run.
Uses the existing bundled Python with numpy and Pillow; no Unreal or Blender.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import numpy as np
from PIL import Image

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'SpaceSurvival.uproject').is_file())
OUT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report = json.loads((OUT/'Report.json').read_text(encoding='utf-8'))
    vertices, normals, faces, face_normals, materials = [], [], [], [], []
    uvs, face_uvs = [], []
    material = None
    for line in (OUT/'StationShellCandidate.obj').read_text(encoding='utf-8').splitlines():
        words = line.split()
        if not words:
            continue
        if words[0] == 'v':
            vertices.append([float(x) for x in words[1:]])
        elif words[0] == 'vn':
            normals.append([float(x) for x in words[1:]])
        elif words[0] == 'vt':
            uvs.append([float(x) for x in words[1:]])
        elif words[0] == 'usemtl':
            material = words[1]
        elif words[0] == 'f':
            assert len(words) == 4
            pairs = [word.split('/') for word in words[1:]]
            assert all(len(pair) == 3 and pair[1] for pair in pairs)
            face_uvs.append([int(p[1])-1 for p in pairs])
            faces.append([int(p[0])-1 for p in pairs])
            face_normals.append([int(p[2])-1 for p in pairs])
            materials.append(material)
    vertices, normals, faces, face_normals = map(np.array, (vertices,normals,faces,face_normals))
    assert np.isfinite(vertices).all() and np.isfinite(normals).all()
    assert len(faces) == report['evaluated_triangles']
    assert dict(Counter(materials)) == report['material_triangles']
    normal_error = float(np.max(np.abs(np.linalg.norm(normals,axis=1)-1)))
    assert normal_error < 1e-5
    bounds = np.array([vertices.min(0),vertices.max(0)])
    assert np.max(np.abs(bounds-report['bounds_cm'])) < 1e-5
    uv_array = np.array(uvs, dtype=np.float32)
    uv_indices = np.array(face_uvs)
    assert len(uvs) == len(faces)*3 and np.isfinite(uv_array).all()
    uv_triangles = uv_array[uv_indices]
    du = uv_triangles[:,1]-uv_triangles[:,0]
    dv = uv_triangles[:,2]-uv_triangles[:,0]
    determinants = du[:,0]*dv[:,1]-du[:,1]*dv[:,0]
    assert np.min(np.abs(determinants)) > 1e-12, 'Degenerate float32 UV triangle'
    uv_revision = json.loads((OUT/'UVRevision.json').read_text(encoding='utf-8'))
    assert report['uv_revision_sha256'] == sha(OUT/'UVRevision.json')
    assert uv_revision['obj_sha256'] == sha(OUT/'StationShellCandidate.obj')
    geometry_records = []
    for line in (OUT/'StationShellCandidate.obj').read_text(encoding='utf-8').splitlines():
        words = line.split()
        if words and words[0] == 'f':
            pairs = [word.split('/') for word in words[1:]]
            geometry_records.append('f '+' '.join(f'{pair[0]}//{pair[2]}' for pair in pairs))
        elif words and words[0] in ('v','vn','usemtl'):
            geometry_records.append(line)
    geometry_digest = hashlib.sha256(('\n'.join(geometry_records)+'\n').encode()).hexdigest()
    assert geometry_digest == uv_revision['exact_geometry_normal_material_record_sha256']
    triangles = vertices[faces]
    low, high = triangles.min(1), triangles.max(1)
    inbound = (low[:,0]<-1675)&(high[:,1]>-700)&(low[:,1]<700)&(high[:,2]>-10)
    assert not inbound.any(), 'A triangle AABB obstructs the open inbound approach'
    mica = (high[:,0]>1020)&(low[:,0]<1200)&(high[:,1]>1040)&(low[:,1]<1220)&(high[:,2]>-10)&(low[:,2]<270)
    assert not mica.any(), 'A triangle AABB overlaps the unchanged Mica service corner'
    areas = np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]),axis=1)/2
    for row in report['outputs']:
        path = OUT/row['file']
        assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256']
    for row in report['views']:
        with Image.open(OUT/row['file']) as image:
            assert image.format == 'PNG' and list(image.size) == row['dimensions'] == [1600,1000]
            image.verify()
    for path,digest in report['protected_sources'].items():
        if not path.startswith('Source/'):
            assert sha(ROOT/path) == digest, path
    revision = json.loads((OUT/'SourceRevision.json').read_text(encoding='utf-8'))
    generator = revision['source_scripts']['Generate.py']
    assert sha(OUT/'Generate.py') in (report['source_sha256'], generator['promoted_sha256'])
    if sha(OUT/'Generate.py') != report['source_sha256']:
        assert report['source_sha256'] == generator['historical_executed_sha256']
    record = {
        'status':'CANDIDATE_SOURCE_GEOMETRY_CHECKED_NOT_RUNTIME_ACCEPTANCE',
        'utc':datetime.now(timezone.utc).isoformat(),
        'vertices':len(vertices), 'triangles':len(faces), 'materials':dict(Counter(materials)),
        'exported_normals':len(normals), 'maximum_normal_unit_error':normal_error,
        'triangle_area_below_one_millionth_square_cm':int(np.count_nonzero(areas<1e-6)),
        'bounds_cm':bounds.tolist(), 'corridor_triangle_aabb_conflicts':0,
        'uv_corner_records':len(uvs), 'uv_float32_minimum_absolute_determinant':float(np.min(np.abs(determinants))),
        'uv_float32_degenerate_triangles':0, 'geometry_normal_material_record_sha256':geometry_digest,
        'uv_revision_sha256':sha(OUT/'UVRevision.json'),
        'inbound_domain_cm':{'x_below':-1675,'y_open':[-700,700],'z_above':-10},
        'mica_corner_triangle_aabb_conflicts':0,
        'mica_envelope_cm':[[1020,1040,-10],[1200,1220,270]],
        'source_report_sha256':sha(OUT/'Report.json'),
        'hash_verified_outputs':len(report['outputs']),
        'hash_verified_protected_content_sources':sum(not p.startswith('Source/') for p in report['protected_sources']),
        'historical_runtime_source_hashes':{p:h for p,h in report['protected_sources'].items() if p.startswith('Source/')},
        'promoted_validator_sha256':sha(Path(__file__)),
        'source_revision_sha256':sha(OUT/'SourceRevision.json'),
        'images':report['views'],
        'limitations':['No native import, material, collision, draw/LOD or gameplay validation.',
                      'Corridor/Mica checks conservatively use triangle AABBs; seven service envelopes use the generator separating-axis triangle check.',
                      'The exact deck is render context and excluded from exported shell; exterior housings extend outside its playable footprint.']
    }
    (OUT/'Validation.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(record,indent=2))


if __name__ == '__main__':
    main()
