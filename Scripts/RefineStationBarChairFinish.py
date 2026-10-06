"""Private, textured chair recolor; lead alone saves/renders the owner preview.

Actual source ORM B is an exposed-metal/wear mask, not a clean frame mask.
Keep color endpoints close so the old chips do not become bright steel patches.
Normal, AO and metallic links stay native; source G supplies bounded roughness.
"""
import hashlib
import json
import math
import re
from pathlib import Path

from RefineStationBarPresentation import _one, _path, _require
from RefineStationLoungeCeiling import _snapshot
from StationRefinementSupport import transform_record

MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
CHAIR = '/Game/CyberPunkBarAssetSet01/StaticMeshes/SM_CyberChair01'
SOURCE = '/Game/CyberPunkBarAssetSet01/Materials/M_CyberChairMat01'
TEX = '/Game/CyberPunkBarAssetSet01/Textures/T_CyberChairMat01_'
PRIVATE = '/Game/OutpostSandbox/StationRefinement/BarChairFinish20261006'
MATERIAL = PRIVATE+'/M_BarChairGraphiteSatin'
PROBE_SHA = '6b08319a99dc3cb7958aeccbcd1ced93c1c2dbb5f5fe32d6c7ad0d8914d10995'
FURNITURE_SHA = '15de19cdbfb4ddeab9b580c767df4e454fedd58bd13ab663144cde7cddfd0425'
GRAPHITE = (.055, .085, .11, 1.)
SATIN = (.10, .14, .175, 1.)
PROPERTIES = ('MP_BASE_COLOR', 'MP_ROUGHNESS', 'MP_METALLIC', 'MP_NORMAL', 'MP_AMBIENT_OCCLUSION')


def _connections(material, u):
    edit = u.MaterialEditingLibrary
    result = {}
    for name in PROPERTIES:
        prop = getattr(u.MaterialProperty, name)
        node = edit.get_material_property_input_node(material, prop)
        result[name] = {'node': node.get_name() if node else None,
                        'output': edit.get_material_property_input_node_output_name(material, prop) if node else None}
    return result


def _finish(ctx, u):
    edit = u.MaterialEditingLibrary
    original = ctx.asset(SOURCE)
    expected = {'MP_BASE_COLOR': (TEX+'Base', 'RGB'), 'MP_METALLIC': (TEX+'orm', 'B'),
                'MP_NORMAL': (TEX+'Normal', 'RGB'), 'MP_AMBIENT_OCCLUSION': (TEX+'orm', 'R')}
    original_links = _connections(original, u)
    for name, (texture, output) in expected.items():
        node = edit.get_material_property_input_node(original, getattr(u.MaterialProperty, name))
        _require(isinstance(node, u.MaterialExpressionTextureSample) and
                 _path(node.get_editor_property('texture')) == texture and original_links[name]['output'] == output,
                 'Source chair graph differs from actual exported probe: '+name)
    _require(original_links['MP_ROUGHNESS']['node'] is None,
             'Original disconnected roughness state changed; reassess source before authoring')
    _require(not u.EditorAssetLibrary.does_asset_exist(MATERIAL), 'Preserve existing chair finish')
    material = u.EditorAssetLibrary.duplicate_asset(SOURCE, MATERIAL)
    _require(isinstance(material, u.Material), 'Could not duplicate the owned chair material')
    source_base = edit.get_material_property_input_node(material, u.MaterialProperty.MP_BASE_COLOR)
    source_orm = edit.get_material_property_input_node(material, u.MaterialProperty.MP_METALLIC)
    graph = []

    def node(cls, label):
        value = edit.create_material_expression(material, cls)
        _require(value is not None, 'Could not create private chair expression: '+label)
        graph.append({'node': value.get_name(), 'role': label, 'class': cls.__name__})
        return value

    def scalar(value, label):
        result = node(u.MaterialExpressionConstant, label)
        result.set_editor_property('r', value)
        _require(abs(result.get_editor_property('r')-value) < .00001, 'Scalar expression readback failed')
        return result

    def color(value, label):
        result = node(u.MaterialExpressionConstant3Vector, label)
        result.set_editor_property('constant', u.LinearColor(*value))
        _require(max(abs(a-b) for a, b in zip(result.get_editor_property('constant').to_tuple(), value)) < .00001,
                 'Color expression readback failed')
        return result

    def link(source, output, destination, pin):
        _require(edit.connect_material_expressions(source, output, destination, pin),
                 'Private chair expression link failed: '+pin)
        _require(source in edit.get_inputs_for_material_expression(material, destination),
                 'Private chair expression input readback failed: '+pin)

    # Desaturate while retaining texture variation, stitches, rivets and surface
    # detail. The .78 floor prevents original black/white wear becoming new chips.
    luminance = node(u.MaterialExpressionDotProduct, 'Native base texture luminance')
    link(source_base, 'RGB', luminance, 'A')
    link(color((.2126, .7152, .0722, 1.), 'Luminance weights'), '', luminance, 'B')
    variation = node(u.MaterialExpressionMultiply, 'Restrained native color variation')
    link(luminance, '', variation, 'A')
    link(scalar(.22, 'Color variation strength'), '', variation, 'B')
    texture_factor = node(u.MaterialExpressionAdd, 'Preserved detail with clean baseline')
    link(variation, '', texture_factor, 'A')
    link(scalar(.78, 'Clean base floor'), '', texture_factor, 'B')
    palette = node(u.MaterialExpressionLinearInterpolate, 'Close graphite and satin color endpoints')
    link(color(GRAPHITE, 'Graphite paint and upholstery'), '', palette, 'A')
    link(color(SATIN, 'Restrained exposed metal'), '', palette, 'B')
    link(source_orm, 'B', palette, 'Alpha')
    base = node(u.MaterialExpressionMultiply, 'Textured private chair base color')
    link(palette, '', base, 'A')
    link(texture_factor, '', base, 'B')
    _require(edit.connect_material_property(base, '', u.MaterialProperty.MP_BASE_COLOR),
             'Could not connect textured private chair base')

    # The original never connected G. Keep its local roughness detail within a
    # restrained satin-to-upholstery range rather than a polished chrome coating.
    rough_variation = node(u.MaterialExpressionMultiply, 'Native G roughness variation')
    link(source_orm, 'G', rough_variation, 'A')
    link(scalar(.38, 'Roughness variation strength'), '', rough_variation, 'B')
    roughness = node(u.MaterialExpressionAdd, 'Bounded native roughness')
    link(rough_variation, '', roughness, 'A')
    link(scalar(.32, 'Satin roughness floor'), '', roughness, 'B')
    _require(edit.connect_material_property(roughness, '', u.MaterialProperty.MP_ROUGHNESS),
             'Could not connect bounded chair roughness')
    links = _connections(material, u)
    for name in ('MP_NORMAL', 'MP_METALLIC', 'MP_AMBIENT_OCCLUSION'):
        _require(links[name] == original_links[name], 'Private chair lost native detail/mask connection: '+name)
    _require(links['MP_BASE_COLOR']['node'] == base.get_name() and
             links['MP_ROUGHNESS']['node'] == roughness.get_name(), 'Final private chair output readback failed')
    _require(not edit.recompile_material(material), 'Private chair material compilation failed')
    return material, {'source_connections': original_links, 'private_connections': links, 'expressions': graph,
                      'graphite_linear': GRAPHITE, 'satin_linear': SATIN,
                      'color_luminance_modulation': [.78, .22], 'roughness_from_native_G': [.32, .38],
                      'normal_ao_metallic_preserved': True, 'emissive_added': False,
                      'mask_limit': 'Native B is exposed-metal/wear, not whole-frame segmentation; deliberately close color endpoints'}


def apply(ctx, expected_map_sha256):
    """Stage one private material on the four saved chairs; never save."""
    import unreal as u
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    _require(re.fullmatch('[0-9a-f]{64}', expected_map_sha256), 'Require exact latest owner-preview SHA')
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    map_file = root/('Content/'+MAP[6:]+'.umap')
    _require(world.get_path_name().split('.')[0] == MAP and sha(map_file) == expected_map_sha256,
             'Chair finish targets only the guarded saved owner preview')
    folder = root/'.agent/local/StationRefinement'
    probe_file, furniture_file = folder/'StationBarChairFinishProbe2.json', folder/'StationBarFurniture1.json'
    _require(sha(probe_file) == PROBE_SHA and sha(furniture_file) == FURNITURE_SHA, 'Chair evidence identity changed')
    probe = json.loads(probe_file.read_text(encoding='utf-8'))
    furniture = json.loads(furniture_file.read_text(encoding='utf-8'))
    _require(probe['success'] and probe['preservation_pass'] and furniture['success'] and furniture['preservation_pass'],
             'Require successful inspected source and saved chair placement')
    sources = probe['source_sha256_after']
    _require(all(sha(root/('Content/'+p.split('.')[0][6:]+'.uasset')) == h for p, h in sources.items()),
             'Protected original or private source changed')
    for row in probe['exports']:
        _require(sha(Path(row['path'])) == row['sha256'], 'Inspected native source pixels changed')
    actors = list(ctx.eas.get_all_level_actors())
    before = {a.get_path_name(): _snapshot(a, u) for a in actors}
    meshes = {c.get_path_name(): _path(c.static_mesh) for a in actors
              for c in a.get_components_by_class(u.StaticMeshComponent)}
    chairs = [_one(actors, 'Refine/Social/Bar/Stool '+str(i)) for i in range(1, 5)]
    for actor in chairs:
        saved = next(r['after'] for r in furniture['furniture']['replacements'] if r['after']['label'] == actor.get_actor_label())
        actual = transform_record(actor)
        _require(all(math.dist(actual[k], saved[k]) < .005 for k in ('location', 'rotation', 'scale')) and
                 _path(actor.static_mesh_component.static_mesh) == CHAIR and
                 all(_path(actor.static_mesh_component.get_material(i)) == SOURCE for i in range(2)),
                 'Preserve already-changed chair geometry, pose or finish')
    material, recipe = _finish(ctx, u)
    allowed = {a.get_path_name() for a in chairs}
    for actor in chairs:
        for index in range(2):
            actor.static_mesh_component.set_material(index, material)
            _require(actor.static_mesh_component.get_material(index) == material, 'Chair private finish readback failed')
    for actor in actors:
        old, now = before[actor.get_path_name()], _snapshot(actor, u)
        for field in ('location', 'rotation', 'scale', 'hidden', 'lights'):
            _require(now[field] == old[field], 'Protected room state changed: '+actor.get_actor_label()+'/'+field)
        if actor.get_path_name() not in allowed:
            _require(now['materials'] == old['materials'], 'Unrelated room material changed')
        for component in actor.get_components_by_class(u.StaticMeshComponent):
            _require(_path(component.static_mesh) == meshes[component.get_path_name()], 'Existing mesh changed')
    _require(sha(map_file) == expected_map_sha256 and
             all(sha(root/('Content/'+p.split('.')[0][6:]+'.uasset')) == h for p, h in sources.items()),
             'Chair finish helper must not save or change original packages')
    return {'dirty_assets': [material.get_path_name()], 'source_sha256': sources, 'material': _path(material),
            'probe_sha256': PROBE_SHA, 'furniture_receipt_sha256': FURNITURE_SHA,
            'chairs': [transform_record(a) for a in chairs], 'recipe': recipe,
            'protected_existing_actor_count': len(before), 'changed_material_actor_allowlist': sorted(allowed),
            'all_meshes_transforms_counter_ceiling_lights_preserved': True,
            'limits': 'Unsaved private chair finish; actual room pixels and owner acceptance remain pending'}
