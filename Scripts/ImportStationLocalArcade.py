"""Import frozen local arcade exports into new private packages, without saving.

The lead owns the native process, map placement, explicit saves and visual review.
This module deliberately has no executable entry point or reimport/delete path.
"""
from contextlib import contextmanager
import hashlib
import json
import math
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / '.agent/local/ArcadeGeneration/final'
BASE = '/Game/OutpostSandbox/StationRefinement/Arcade20261006'


def _require(condition, message):
    if not condition:
        raise RuntimeError(message)


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source(value):
    path = Path(value).resolve(strict=True)
    _require(path.is_relative_to(SOURCE.resolve()) and path.is_file(),
             'Arcade source outside the final export folder: ' + str(path))
    return path


def _name(value):
    _require(isinstance(value, str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', value),
             'Unsafe arcade asset/slot name: ' + str(value))
    return value


def _numbers(values, count, label):
    _require(len(values) == count and all(math.isfinite(float(v)) for v in values),
             'Invalid finite numeric data: ' + label)
    return [float(v) for v in values]


def inspect_sources(sources):
    """Filesystem-only manifest preflight; also usable before Unreal starts."""
    result, hashes, names = [], {}, set()
    for source in sources:
        path = _source(source)
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        name = _name(data['name'])
        _require(name not in names, 'Duplicate arcade manifest: ' + name)
        names.add(name)
        _require(data.get('frozen') is True, 'Export is not frozen: ' + name)
        declared = {str(_source(p)): digest.lower() for p, digest in data['source_sha256'].items()}
        _require(declared and all(re.fullmatch('[a-f0-9]{64}', h) for h in declared.values()),
                 'Missing frozen source hashes: ' + name)
        used = set()
        parts = data.get('fbx_parts') or [{
            'name': 'Body', 'fbx_path': data['fbx_path'],
            'dimensions_m': data['dimensions_m'], 'bounds_m': data['bounds_m'],
            'collision': 'box'}]
        part_names = set()
        for part in parts:
            part_name = _name(part['name'])
            _require(part_name not in part_names, 'Duplicate mesh part: ' + part_name)
            part_names.add(part_name)
            fbx = _source(part['fbx_path'])
            _require(fbx.suffix.lower() == '.fbx', 'Expected FBX: ' + str(fbx))
            part['fbx_path'] = str(fbx)
            used.add(str(fbx))
            size = _numbers(part['dimensions_m'], 3, name + ' dimensions')
            bounds = [_numbers(v, 3, name + ' bounds') for v in part['bounds_m']]
            _require(len(bounds) == 2 and all(v > 0 for v in size), 'Invalid mesh extent: ' + name)
            _require(all(abs(bounds[1][i]-bounds[0][i]-size[i]) < .002 for i in range(3)),
                     'Source bounds/dimensions disagree: ' + name)
            _require(part.get('collision', 'box') in ('box', 'none'), 'Unknown collision policy')
        _require(abs(min(p['bounds_m'][0][2] for p in parts)) < .005,
                 'Assembled arcade export must be grounded at Z=0: ' + name)
        slots = set()
        for material in data['materials']:
            slot = _name(material['slot'])
            _require(slot not in slots, 'Duplicate source material slot: ' + slot)
            slots.add(slot)
            for key in ('base_color_texture', 'emission_texture'):
                if material.get(key):
                    texture = _source(material[key])
                    _require(texture.suffix.lower() in ('.png', '.jpg', '.jpeg', '.tga', '.exr'),
                             'Unsupported arcade texture: ' + str(texture))
                    material[key] = str(texture)
                    used.add(str(texture))
            _numbers(material['base_color_linear'], 4, slot + ' color')
            _numbers(material.get('emission_color_linear', [1, 1, 1, 1]), 4, slot + ' emission')
            for key, default in (('metallic', 0), ('roughness', .5), ('alpha', 1)):
                value = float(material.get(key, default))
                _require(math.isfinite(value) and 0 <= value <= 1, slot + ': invalid ' + key)
            strength = float(material.get('emission_strength', 0))
            _require(math.isfinite(strength) and strength >= 0, slot + ': invalid emission')
        _require(used <= declared.keys(), 'Frozen hashes omit import sources: ' + name)
        for filename, digest in declared.items():
            _require(_sha(Path(filename)) == digest, 'Frozen source changed: ' + filename)
            _require(filename not in hashes or hashes[filename] == digest, 'Conflicting frozen hashes')
            hashes[filename] = digest
        hashes[str(path)] = _sha(path)
        result.append({'name': name, 'manifest': str(path), 'parts': parts,
                       'materials': data['materials'], 'source': data})
    _require(result, 'No frozen arcade exports supplied')
    return result, hashes


@contextmanager
def _legacy_fbx(u):
    key = 'Interchange.FeatureFlags.Import.FBX'
    previous = u.SystemLibrary.get_console_variable_int_value(key)
    try:
        u.SystemLibrary.execute_console_command(None, key + ' 0')
        _require(u.SystemLibrary.get_console_variable_int_value(key) == 0, 'Legacy FBX routing failed')
        yield
    finally:
        u.SystemLibrary.execute_console_command(None, key + ' ' + str(previous))
        _require(u.SystemLibrary.get_console_variable_int_value(key) == previous, 'FBX routing restore failed')


def _fresh(path, u):
    _require(path.startswith(BASE + '/') and not u.EditorAssetLibrary.does_asset_exist(path),
             'Refusing to replace an existing arcade asset: ' + path)


def _texture(path, cache, dirty, u):
    if path in cache:
        return cache[path]
    source = Path(path)
    name = 'T_' + re.sub(r'[^A-Za-z0-9_]', '_', source.stem) + '_' + _sha(source)[:10]
    target = BASE + '/Textures/' + name
    _fresh(target, u)
    task = u.AssetImportTask()
    for key, value in {'filename': path, 'destination_path': BASE + '/Textures',
                       'destination_name': name, 'automated': True, 'replace_existing': False,
                       'save': False}.items():
        task.set_editor_property(key, value)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = u.load_asset(target)
    _require(isinstance(texture, u.Texture2D), 'Texture import failed: ' + path)
    texture.set_editor_property('srgb', True)
    texture.set_editor_property('compression_settings', u.TextureCompressionSettings.TC_BC7)
    texture.set_editor_property('lod_group', u.TextureGroup.TEXTUREGROUP_WORLD)
    texture.set_editor_property('mip_gen_settings', u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)
    cache[path] = texture
    dirty.append(texture)
    return texture


def _material(asset_name, row, textures, dirty, u):
    edit = u.MaterialEditingLibrary
    name = 'M_' + asset_name + '_' + row['slot'].removeprefix('M_')
    folder = BASE + '/' + asset_name + '/Materials'
    _fresh(folder + '/' + name, u)
    material = u.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, u.Material, u.MaterialFactoryNew())
    _require(material, 'Material creation failed: ' + name)
    material.set_editor_property('shading_model', u.MaterialShadingModel.MSM_DEFAULT_LIT)
    alpha = float(row.get('alpha', 1))
    glass = alpha < .999
    material.set_editor_property('blend_mode', u.BlendMode.BLEND_TRANSLUCENT if glass else u.BlendMode.BLEND_OPAQUE)
    if glass:
        material.set_editor_property('translucency_lighting_mode', u.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
        material.set_editor_property('two_sided', True)

    def node(cls, x, y):
        return edit.create_material_expression(material, cls, x, y)

    def scalar(label, value, y):
        n = node(u.MaterialExpressionScalarParameter, -500, y)
        n.set_editor_property('parameter_name', label)
        n.set_editor_property('default_value', float(value))
        return n

    def color(label, values, y):
        n = node(u.MaterialExpressionVectorParameter, -700, y)
        n.set_editor_property('parameter_name', label)
        n.set_editor_property('default_value', u.LinearColor(*values))
        return n

    def sample(label, path, y):
        n = node(u.MaterialExpressionTextureSampleParameter2D, -900, y)
        n.set_editor_property('parameter_name', label)
        n.set_editor_property('texture', _texture(path, textures, dirty, u))
        n.set_editor_property('sampler_type', u.MaterialSamplerType.SAMPLERTYPE_COLOR)
        return n

    def connect(n, output, prop):
        _require(edit.connect_material_property(n, output, prop), 'Material property connection failed: ' + name)

    if row.get('base_color_texture'):
        base = sample('BaseColorTexture', row['base_color_texture'], 0)
        base_output = 'RGB'
    else:
        base = color('BaseColor', row['base_color_linear'], 0)
        base_output = ''
    connect(base, base_output, u.MaterialProperty.MP_BASE_COLOR)
    connect(scalar('Metallic', row.get('metallic', 0), 180), '', u.MaterialProperty.MP_METALLIC)
    connect(scalar('Roughness', row.get('roughness', .5), 300), '', u.MaterialProperty.MP_ROUGHNESS)
    if glass:
        connect(scalar('Opacity', alpha, 430), '', u.MaterialProperty.MP_OPACITY)
    if float(row.get('emission_strength', 0)) > 0:
        if row.get('emission_texture'):
            emission, output = sample('EmissionTexture', row['emission_texture'], 600), 'RGB'
        elif row.get('emission_uses_base_texture') and row.get('base_color_texture'):
            emission, output = base, base_output
        else:
            emission, output = color('EmissionColor', row.get('emission_color_linear', [1, 1, 1, 1]), 600), ''
        product = node(u.MaterialExpressionMultiply, -150, 600)
        strength = scalar('EmissionStrength', row['emission_strength'], 780)
        _require(edit.connect_material_expressions(emission, output, product, 'A') and
                 edit.connect_material_expressions(strength, '', product, 'B'), 'Emission connection failed')
        connect(product, '', u.MaterialProperty.MP_EMISSIVE_COLOR)
    edit.recompile_material(material)
    dirty.append(material)
    return material


def _mesh(asset_name, part, materials, dirty, u):
    folder, name = BASE + '/' + asset_name + '/Meshes', 'SM_' + asset_name + '_' + part['name']
    _fresh(folder + '/' + name, u)
    options = u.FbxImportUI()
    for key, value in {'import_mesh': True, 'import_as_skeletal': False, 'import_materials': False,
                       'import_textures': False, 'mesh_type_to_import': u.FBXImportType.FBXIT_STATIC_MESH}.items():
        options.set_editor_property(key, value)
    data = options.get_editor_property('static_mesh_import_data')
    for key, value in {'combine_meshes': True, 'auto_generate_collision': False,
                       'generate_lightmap_u_vs': False, 'import_uniform_scale': 1.,
                       'convert_scene': True, 'convert_scene_unit': True, 'force_front_x_axis': False,
                       'transform_vertex_to_absolute': True, 'bake_pivot_in_vertex': False,
                       'normal_import_method': u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS,
                       'normal_generation_method': u.FBXNormalGenerationMethod.MIKK_T_SPACE,
                       'import_translation': u.Vector(0, 0, 0), 'import_rotation': u.Rotator(0, 0, 0)}.items():
        data.set_editor_property(key, value)
    task = u.AssetImportTask()
    for key, value in {'filename': part['fbx_path'], 'destination_path': folder, 'destination_name': name,
                       'automated': True, 'replace_existing': False, 'save': False,
                       'factory': u.FbxFactory(), 'options': options}.items():
        task.set_editor_property(key, value)
    with _legacy_fbx(u):
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = [u.load_asset(p) for p in task.get_editor_property('imported_object_paths')]
    meshes = [m for m in imported if isinstance(m, u.StaticMesh)]
    _require(len(imported) == len(meshes) == 1, 'Expected one combined static mesh: ' + name)
    mesh = meshes[0]
    _require(mesh.get_path_name().split('.')[0] == folder + '/' + name, 'Unexpected FBX asset path')
    slots = mesh.get_editor_property('static_materials')
    slot_names = [str(s.get_editor_property('material_slot_name')) for s in slots]
    _require(slots and len(slots) == len(set(slot_names)) and set(slot_names) <= materials.keys(),
             'Unexpected native material slots: ' + repr(slot_names))
    for index, slot_name in enumerate(slot_names):
        mesh.set_material(index, materials[slot_name])
    editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    _require(mesh.get_num_triangles(0) > 0 and editor.get_num_uv_channels(mesh, 0) >= 1,
             'Imported arcade geometry/UVs are empty: ' + name)
    build = editor.get_lod_build_settings(mesh, 0)
    for key, value in {'recompute_normals': False, 'recompute_tangents': True,
                       'use_mikk_t_space': True, 'use_full_precision_u_vs': True}.items():
        build.set_editor_property(key, value)
    editor.set_lod_build_settings(mesh, 0, build)
    editor.remove_collisions(mesh)
    solid = part.get('collision', 'box') == 'box'
    if solid:
        editor.add_simple_collisions(mesh, u.ScriptCollisionShapeType.BOX)
    body = mesh.get_editor_property('body_setup')
    instance = body.get_editor_property('default_instance')
    instance.set_editor_property('collision_profile_name', 'BlockAll' if solid else 'NoCollision')
    instance.set_editor_property('collision_enabled', u.CollisionEnabled.QUERY_AND_PHYSICS if solid else u.CollisionEnabled.NO_COLLISION)
    body.set_editor_property('default_instance', instance)
    u.AutomationLibrary.finish_loading_before_screenshot()
    bounds = mesh.get_bounds()
    actual = [[getattr(bounds.origin, a)+sign*getattr(bounds.box_extent, a) for a in ('x', 'y', 'z')]
              for sign in (-1, 1)]
    size = [actual[1][i]-actual[0][i] for i in range(3)]
    expected = [v*100 for v in part['dimensions_m']]
    # UE legacy FBX uses Z up and mirrors Y handedness with force_front_x_axis=False.
    lo, hi = part['bounds_m']
    expected_bounds = [[lo[0]*100, -hi[1]*100, lo[2]*100], [hi[0]*100, -lo[1]*100, hi[2]*100]]
    tolerance = .5  # half a centimetre accommodates FBX float geometry, not an axis/unit correction
    _require(all(abs(size[i]-expected[i]) <= tolerance for i in range(3)),
             'FBX unit/up-axis mismatch: ' + name + ' actual=' + repr(size) + ' expected=' + repr(expected))
    _require(all(abs(actual[e][i]-expected_bounds[e][i]) <= tolerance for e in range(2) for i in range(3)),
             'FBX pivot/bounds mismatch: ' + name + ' actual=' + repr(actual) + ' expected=' + repr(expected_bounds))
    _require(editor.get_simple_collision_count(mesh) == int(solid), 'Cabinet collision did not match policy')
    dirty.append(mesh)
    return {'name': asset_name, 'part': part['name'], 'mesh': mesh.get_path_name(),
            'bounds_cm': actual, 'dimensions_cm': size, 'triangles': mesh.get_num_triangles(0),
            'material_slots': [{'slot': n, 'material': materials[n].get_path_name()} for n in slot_names],
            'collision': 'box' if solid else 'none', 'native_front_axis': '+Y',
            'source_fbx': part['fbx_path']}


def create(ctx, sources):
    """Create new, unsaved private assets; return serializable evidence and dirty objects."""
    import unreal as u
    rows, hashes = inspect_sources(sources)
    _require(Path(u.Paths.project_dir()).resolve() == ROOT, 'Unexpected Unreal project')
    for row in rows:
        _require(not u.EditorAssetLibrary.list_assets(BASE + '/' + row['name'], recursive=True),
                 'Arcade destination is not empty: ' + row['name'])
    textures, dirty, meshes, materials = {}, [], [], []
    for row in rows:
        made = {m['slot']: _material(row['name'], m, textures, dirty, u) for m in row['materials']}
        materials.extend({'name': row['name'], 'slot': k, 'material': v.get_path_name()} for k, v in made.items())
        meshes.extend(_mesh(row['name'], part, made, dirty, u) for part in row['parts'])
    _require(all(_sha(Path(p)) == h for p, h in hashes.items()), 'Frozen arcade files changed during import')
    return {'meshes': meshes, 'materials': materials,
            'textures': {p: t.get_path_name() for p, t in textures.items()}, 'dirty_assets': dirty,
            'source_sha256': hashes, 'manifests': [r['manifest'] for r in rows],
            'glass_note': 'Explicit surface translucency/opacity; Blender transmission is not a 1:1 shader transfer.',
            'saved': False, 'placed': False}
