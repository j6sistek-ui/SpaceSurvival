"""Import the separate reviewed AcornShip source candidate, preserving current art.

Run with UnrealEditor-Cmd SpaceSurvival.uproject -unattended
-ExecutePythonScript=Scripts/AuthorAcornShip.py. Validate in a fresh editor using
ValidateAcornShip.py. This does not select the candidate in gameplay.
"""
import hashlib
import json
from pathlib import Path

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'ContentSource/AcornShipCandidate'
BASE = '/Game/SpaceSurvival'
MESH_PATH = BASE + '/Meshes/SM_AcornShipV2'
VERSION = 'AcornShipCandidate1'
LIBRARY = u.EditorAssetLibrary
EDIT = u.MaterialEditingLibrary


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def material_path(source_name):
    return BASE + '/Materials/M_AcornV2_' + source_name.removeprefix('AC01_')


def owned_content(path):
    return path.stem == 'SM_AcornShipV2' or path.stem.startswith('M_AcornV2_')


def source_report():
    report = json.loads((SOURCE / 'Report.json').read_text(encoding='utf-8'))
    for item in report['outputs']:
        assert sha(SOURCE / item['file']) == item['sha256'], 'Changed candidate source: ' + item['file']
    for path, digest in report['protected_sha256'].items():
        assert sha(ROOT / path) == digest, 'Protected source changed: ' + path
    return report


def save(asset, digest):
    LIBRARY.set_metadata_tag(asset, 'SSAuthoringVersion', '1')
    LIBRARY.set_metadata_tag(asset, 'SSAcornCandidateVersion', VERSION)
    LIBRARY.set_metadata_tag(asset, 'SSAcornSourceSHA256', digest)
    if not LIBRARY.save_loaded_asset(asset, only_if_is_dirty=False):
        raise RuntimeError('Could not save ' + asset.get_path_name())


def node(material, cls, x, y):
    return EDIT.create_material_expression(material, cls, x, y)


def scalar(material, name, value, x, y):
    expression = node(material, u.MaterialExpressionScalarParameter, x, y)
    expression.set_editor_property('parameter_name', name)
    expression.set_editor_property('default_value', value)
    return expression


def material(item, digest):
    path = material_path(item['name'])
    result = LIBRARY.load_asset(path)
    if result:
        if LIBRARY.get_metadata_tag(result, 'SSAcornSourceSHA256') != digest:
            raise RuntimeError('Existing candidate needs deliberate reviewed reimport: ' + path)
        return result
    result = u.AssetToolsHelpers.get_asset_tools().create_asset(path.rsplit('/', 1)[1], BASE + '/Materials', u.Material, u.MaterialFactoryNew())
    if not result:
        raise RuntimeError('Could not create ' + path)
    tint = node(result, u.MaterialExpressionVectorParameter, -800, -250)
    tint.set_editor_property('parameter_name', 'Color')
    tint.set_editor_property('default_value', u.LinearColor(*item['base_color']))
    EDIT.connect_material_property(tint, '', u.MaterialProperty.MP_BASE_COLOR)
    metallic = scalar(result, 'Metallic', item['metallic'], -500, -100)
    roughness = scalar(result, 'Roughness', item['roughness'], -800, 150)
    EDIT.connect_material_property(metallic, '', u.MaterialProperty.MP_METALLIC)
    EDIT.connect_material_property(roughness, '', u.MaterialProperty.MP_ROUGHNESS)
    if item['name'] not in ('AC01_Windscreen', 'AC01_IonAndNav', 'AC01_CockpitPadding'):
        # One inexpensive 3D texture noise level, only +/-0.008 roughness.
        # Local position prevents surface detail swimming during flight/rebasing.
        world = node(result, u.MaterialExpressionWorldPosition, -1200, 300)
        local = node(result, u.MaterialExpressionTransformPosition, -1000, 300)
        local.set_editor_property('transform_source_type', u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_WORLD)
        local.set_editor_property('transform_type', u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_LOCAL)
        EDIT.connect_material_expressions(world, '', local, 'Input')
        noise = node(result, u.MaterialExpressionNoise, -750, 300)
        for key, value in {'scale': 2.0, 'quality': 1, 'levels': 1, 'turbulence': False,
                           'output_min': -1.0, 'output_max': 1.0,
                           'noise_function': u.NoiseFunction.NOISEFUNCTION_GRADIENT_TEX3D}.items():
            noise.set_editor_property(key, value)
        EDIT.connect_material_expressions(local, '', noise, 'Position')
        amount = scalar(result, 'MicroRoughness', .008, -750, 500)
        product = node(result, u.MaterialExpressionMultiply, -470, 300)
        EDIT.connect_material_expressions(noise, '', product, 'A')
        EDIT.connect_material_expressions(amount, '', product, 'B')
        total = node(result, u.MaterialExpressionAdd, -220, 150)
        EDIT.connect_material_expressions(roughness, '', total, 'A')
        EDIT.connect_material_expressions(product, '', total, 'B')
        EDIT.connect_material_property(total, '', u.MaterialProperty.MP_ROUGHNESS)
    if item['name'] == 'AC01_IonAndNav':
        emission = scalar(result, 'Emission', 3.5, -500, 400)
        product = node(result, u.MaterialExpressionMultiply, -200, 300)
        EDIT.connect_material_expressions(tint, '', product, 'A')
        EDIT.connect_material_expressions(emission, '', product, 'B')
        EDIT.connect_material_property(product, '', u.MaterialProperty.MP_EMISSIVE_COLOR)
    if item['name'] == 'AC01_Windscreen':
        result.set_editor_property('blend_mode', u.BlendMode.BLEND_TRANSLUCENT)
        result.set_editor_property('translucency_lighting_mode', u.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
        result.set_editor_property('two_sided', True)
        opacity = scalar(result, 'Opacity', .18, -500, 400)
        EDIT.connect_material_property(opacity, '', u.MaterialProperty.MP_OPACITY)
        # No screen-space refraction: preserves pilot/hazard readability.
        LIBRARY.set_metadata_tag(result, 'SSGlassPresentation', 'TranslucentSurface18PercentNoRefraction')
    EDIT.recompile_material(result)
    save(result, digest)
    return result


def import_mesh(report, materials, digest):
    mesh = LIBRARY.load_asset(MESH_PATH)
    if mesh and LIBRARY.get_metadata_tag(mesh, 'SSAcornSourceSHA256') != digest:
        raise RuntimeError('Existing mesh requires deliberate reviewed reimport')
    if not mesh:
        options = u.FbxImportUI()
        for key, value in {'import_mesh': True, 'import_as_skeletal': False, 'import_materials': False,
                           'import_textures': False, 'mesh_type_to_import': u.FBXImportType.FBXIT_STATIC_MESH}.items():
            options.set_editor_property(key, value)
        data = options.get_editor_property('static_mesh_import_data')
        for key, value in {'combine_meshes': True, 'auto_generate_collision': False, 'generate_lightmap_u_vs': False,
                           'import_uniform_scale': 1.0, 'convert_scene': False, 'force_front_x_axis': False,
                           'normal_import_method': u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS}.items():
            data.set_editor_property(key, value)
        task = u.AssetImportTask()
        for key, value in {'filename': str(SOURCE / 'AcornShipCandidate.obj'), 'destination_path': BASE + '/Meshes',
                           'destination_name': 'SM_AcornShipV2', 'automated': True, 'replace_existing': False,
                           'save': False, 'options': options, 'factory': u.FbxFactory()}.items():
            task.set_editor_property(key, value)
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        imported = [LIBRARY.load_asset(path) for path in task.get_editor_property('imported_object_paths')]
        meshes = [asset for asset in imported if isinstance(asset, u.StaticMesh)]
        if len(meshes) != 1:
            raise RuntimeError('Expected one merged mesh, got ' + str(len(meshes)))
        mesh = meshes[0]
        if mesh.get_path_name().split('.')[0] != MESH_PATH:
            if not LIBRARY.rename_asset(mesh.get_path_name(), MESH_PATH):
                raise RuntimeError('Unable to name candidate mesh')
            mesh = LIBRARY.load_asset(MESH_PATH)
    seen = set()
    for index, slot in enumerate(mesh.get_editor_property('static_materials')):
        name = str(slot.get_editor_property('imported_material_slot_name'))
        if name not in materials:
            name = str(slot.get_editor_property('material_slot_name'))
        if name not in materials:
            raise RuntimeError('Unknown imported material group: ' + name)
        mesh.set_material(index, materials[name])
        seen.add(name)
    assert seen == set(materials), 'Material groups lost during import'
    editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    editor.remove_collisions(mesh)
    for lod in range(editor.get_lod_count(mesh)):
        for section in range(mesh.get_num_sections(lod)):
            editor.enable_section_collision(mesh, False, lod, section)
    body = mesh.get_editor_property('body_setup')
    instance = body.get_editor_property('default_instance')
    instance.set_editor_property('collision_profile_name', 'NoCollision')
    instance.set_editor_property('collision_enabled', u.CollisionEnabled.NO_COLLISION)
    body.set_editor_property('default_instance', instance)
    save(mesh, digest)
    return mesh


def main():
    receipt = {'status': 'FAILED', 'errors': [], 'source_render_is_not_gameplay': True,
               'limits': ['Candidate only; owner acceptance remains pending', 'One LOD, nine material sections',
                          'No rendered Unreal appearance or performance acceptance from import',
                          'Pilot palms float somewhat around controls; unchanged supplied character/tail'],
               'engine': u.SystemLibrary.get_engine_version()}
    protected = {p: sha(p) for p in (ROOT / 'Content').rglob('*') if p.suffix in ('.uasset', '.umap') and not owned_content(p)}
    try:
        report = source_report()
        digest = sha(SOURCE / 'AcornShipCandidate.obj')
        materials = {item['name']: material(item, digest) for item in report['materials']}
        mesh = import_mesh(report, materials, digest)
        assert all(sha(path) == original for path, original in protected.items()), 'An existing protected content package changed'
        receipt.update(status='CANDIDATE_IMPORTED_FRESH_RELOAD_PENDING', mesh=mesh.get_path_name(),
                       material_paths=[asset.get_path_name() for asset in materials.values()], obj_sha256=digest,
                       protected_content_packages_unchanged=len(protected), pilot_transform=report['pilot_transform'])
    except Exception as error:
        receipt['errors'].append(str(error))
        u.log_error('ACORN_CANDIDATE_IMPORT_FAILED: ' + str(error))
    folder = ROOT / 'Saved/Validation'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'AcornShipImport.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    if receipt['errors']:
        raise RuntimeError('Acorn candidate import failed; see Saved/Validation/AcornShipImport.json')
    u.log('ACORN_CANDIDATE_IMPORT_OK')


if __name__ == '__main__':
    main()
