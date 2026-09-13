"""Fresh-editor persisted AcornShip candidate validation; no edits to assets."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ss_acorn_author', ROOT / 'Scripts/AuthorAcornShip.py')
author = importlib.util.module_from_spec(spec)
spec.loader.exec_module(author)


def main():
    result = {'status': 'FAILED', 'engine': u.SystemLibrary.get_engine_version(), 'errors': [], 'materials': [],
              'limits': ['Persisted asset checks, not gameplay or art acceptance', 'LOD and actual draw/shader cost need runtime measurement',
                         'Pilot control contact and existing tail artifacts remain unresolved']}
    try:
        report = author.source_report()
        digest = author.sha(author.SOURCE / 'AcornShipCandidate.obj')
        library = u.EditorAssetLibrary
        editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
        mesh = library.load_asset(author.MESH_PATH)
        assert isinstance(mesh, u.StaticMesh), 'Missing candidate mesh'
        assert library.get_metadata_tag(mesh, 'SSAcornCandidateVersion') == author.VERSION
        assert library.get_metadata_tag(mesh, 'SSAcornSourceSHA256') == digest
        bounds = mesh.get_bounds()
        imported_bounds = [[getattr(bounds.origin, axis) - getattr(bounds.box_extent, axis) for axis in ('x', 'y', 'z')],
                           [getattr(bounds.origin, axis) + getattr(bounds.box_extent, axis) for axis in ('x', 'y', 'z')]]
        for edge in range(2):
            assert all(abs(imported_bounds[edge][axis] - report['bounds_cm'][edge][axis]) < .03 for axis in range(3)), 'Axis/scale/bounds mismatch'
        assert all(report['reference_bounds_cm'][0][axis] - .03 <= imported_bounds[0][axis] and
                   imported_bounds[1][axis] <= report['reference_bounds_cm'][1][axis] + .03 for axis in range(3)), 'Outside reference envelope'
        lods = editor.get_lod_count(mesh)
        assert lods == 1
        assert editor.get_number_verts(mesh, 0) > 0
        assert editor.get_simple_collision_count(mesh) == 0, 'Generated blocking collision'
        assert all(not editor.is_section_collision_enabled(mesh, 0, section) for section in range(mesh.get_num_sections(0)))
        instance = mesh.get_editor_property('body_setup').get_editor_property('default_instance')
        assert instance.get_editor_property('collision_enabled') == u.CollisionEnabled.NO_COLLISION
        assert str(instance.get_editor_property('collision_profile_name')) == 'NoCollision'
        slots = list(mesh.get_editor_property('static_materials'))
        assert len(slots) == 9 and mesh.get_num_sections(0) == 9, 'Expected nine sections and materials'
        expected = {author.material_path(item['name']): item for item in report['materials']}
        seen = set()
        for slot in slots:
            material = slot.get_editor_property('material_interface')
            assert isinstance(material, u.Material), 'Missing material'
            path = material.get_path_name().split('.')[0]
            assert path in expected, 'Unexpected material ' + path
            item = expected[path]
            assert library.get_metadata_tag(material, 'SSAcornSourceSHA256') == digest
            color = u.MaterialEditingLibrary.get_material_default_vector_parameter_value(material, 'Color')
            rgb = [color.r, color.g, color.b, color.a]
            assert all(abs(a-b) < 1e-5 for a, b in zip(rgb, item['base_color'])), 'PBR color changed'
            for name, key in (('Metallic', 'metallic'), ('Roughness', 'roughness')):
                actual = u.MaterialEditingLibrary.get_material_default_scalar_parameter_value(material, name)
                assert abs(actual - item[key]) < 1e-5, 'PBR scalar changed'
            glass = item['name'] == 'AC01_Windscreen'
            assert material.get_editor_property('blend_mode') == (u.BlendMode.BLEND_TRANSLUCENT if glass else u.BlendMode.BLEND_OPAQUE)
            if glass:
                assert material.get_editor_property('two_sided')
                assert abs(u.MaterialEditingLibrary.get_material_default_scalar_parameter_value(material, 'Opacity') - .18) < 1e-5
            if item['name'] == 'AC01_IonAndNav':
                assert abs(u.MaterialEditingLibrary.get_material_default_scalar_parameter_value(material, 'Emission') - 3.5) < 1e-5
            seen.add(path)
            result['materials'].append({'path': path, 'base_color': rgb, 'metallic': item['metallic'], 'roughness': item['roughness'], 'translucent': glass})
        assert seen == set(expected)
        result.update(status='CANDIDATE_PERSISTED_ASSETS_VERIFIED_NOT_VISUAL_ACCEPTANCE', mesh=mesh.get_path_name(),
                      bounds_cm=imported_bounds, lod_count=lods, material_sections=mesh.get_num_sections(0),
                      lod0_vertices=editor.get_number_verts(mesh, 0), lod0_triangles=mesh.get_num_triangles(0),
                      simple_collision_count=0, all_section_collision_disabled=True, collision_profile='NoCollision',
                      obj_sha256=digest, pilot_transform=report['pilot_transform'])
        result['content_packages'] = [{'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size,
                                       'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                                      for path in sorted((ROOT / 'Content').rglob('*.uasset')) if author.owned_content(path)]
    except Exception as error:
        result['errors'].append(str(error))
        u.log_error('ACORN_CANDIDATE_VALIDATE_FAILED: ' + str(error))
    folder = ROOT / 'Saved/Validation'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'AcornShipPersisted.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    if result['errors']:
        raise RuntimeError('Acorn candidate validation failed; see Saved/Validation/AcornShipPersisted.json')
    u.log('ACORN_CANDIDATE_PERSISTED_OK')


if __name__ == '__main__':
    main()
