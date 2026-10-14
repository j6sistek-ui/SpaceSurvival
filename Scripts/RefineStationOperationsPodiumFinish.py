"""Private podium metals only; the lead owns the joint transaction and save.

Preserve every actor, source asset, dimension, light, glass, hologram and sequence.
Two opaque materials replace exactly 44 existing hardware slots on 36 actors.
"""
import copy
import hashlib
import json
import math
import re
from pathlib import Path

from RefineStationOperationsComposition5 import MAP, PREFIX, PANEL, POST, DARK, TRIM
from RefineStationOperationsDisplays import _state as _original_state

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / '.agent/local/StationRefinement'
BASE = '/Game/OutpostSandbox/StationRefinement/OperationsPodiumMetals20261007'
COMPOSITION_SHA = '2944f5f19ed180afcb7f8511933bc4e04135b3053ddebe76eb092f8cf39ac8ce'
CAPTURE_SHA = '0af2c3670848fa499f5a256b027ac177147a0c49985d5fbc0d53b5bb17edb174'
PROBE_SHA = '594247794f1048db936dbc1beaba5284f5cfd5a80377c0ea68b1a56158b9fa39'
PLATE = '/Game/OutpostSandbox/StationRefinement/OperationsComposition20261007/SM_OctagonalPodiumUnit'
METALS = {
    'Graphite': {'color': (.045, .060, .078), 'metallic': .80, 'roughness': .42, 'specular': .35},
    'Titanium': {'color': (.22, .26, .31), 'metallic': .90, 'roughness': .31, 'specular': .40},
}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def path(asset):
    return asset.get_path_name() if asset else None


def object_path(package):
    return package if '.' in package else package + '.' + package.rsplit('/', 1)[-1]


def whitelist():
    rows = [{'label': PREFIX + name, 'mesh': object_path(PLATE), 'slots': (0,),
             'source': object_path(DARK), 'metal': 'Graphite'} for name in
            ('Grounded plinth', 'Recessed body', 'Projection deck')]
    rows.append({'label': PREFIX + 'Upper rim', 'mesh': object_path(PLATE),
                 'slots': (0,), 'source': object_path(TRIM), 'metal': 'Titanium'})
    for index in range(8):
        rows.append({'label': PREFIX + 'Owned service panel %02d' % index,
                     'mesh': object_path(PANEL), 'slots': (0, 4), 'metal': 'Graphite'})
        for name in ('Glass shoe', 'Crown rail'):
            rows.append({'label': PREFIX + name + ' %02d' % index,
                         'mesh': '/Engine/BasicShapes/Cube.Cube', 'slots': (0,),
                         'source': object_path(TRIM), 'metal': 'Titanium'})
        rows.append({'label': PREFIX + 'Owned post %02d' % index, 'mesh': object_path(POST),
                     'slots': (0,), 'source': object_path(TRIM), 'metal': 'Titanium'})
    require(len(rows) == 36 and sum(len(row['slots']) for row in rows) == 44,
            'Podium material-only whitelist count changed')
    return rows


def state(actor, u):
    """The joint wrapper uses the same numeric light/mesh guard for all actors."""
    result = _original_state(actor, u)
    result['light_properties'] = {component.get_path_name(): {
        key: str(component.get_editor_property(key)) for key in
        ('intensity', 'light_color', 'cast_shadows', 'indirect_lighting_intensity',
         'volumetric_scattering_intensity', 'specular_scale', 'affects_world')}
        for component in actor.get_components_by_class(u.LightComponent)}
    result['mesh_assets'] = {component.get_path_name(): path(
        component.get_skeletal_mesh_asset() if isinstance(component, u.SkeletalMeshComponent)
        else component.static_mesh if isinstance(component, u.StaticMeshComponent) else None)
        for component in actor.get_components_by_class(u.MeshComponent)}
    return result


def _metals(u):
    """Sane opaque metal responses; fine world grain avoids legacy UV/dirt layers."""
    tools, edit = u.AssetToolsHelpers.get_asset_tools(), u.MaterialEditingLibrary
    values = {}
    for name, settings in METALS.items():
        require(not u.EditorAssetLibrary.does_asset_exist(BASE + '/M_' + name),
                'Preserve any previous private podium metal')
        material = tools.create_asset('M_' + name, BASE, u.Material, u.MaterialFactoryNew())
        require(isinstance(material, u.Material), 'Private podium metal creation failed')
        material.set_editor_property('blend_mode', u.BlendMode.BLEND_OPAQUE)
        material.set_editor_property('shading_model', u.MaterialShadingModel.MSM_DEFAULT_LIT)
        material.set_editor_property('two_sided', False)

        def node(cls, **properties):
            value = edit.create_material_expression(material, getattr(u, cls))
            require(value, 'Cannot create private metal node: ' + cls)
            for key, value_property in properties.items():
                value.set_editor_property(key, value_property)
            return value

        def link(a, b, pin):
            require(edit.connect_material_expressions(a, '', b, pin), 'Metal graph connection failed')

        def output(value, prop):
            require(edit.connect_material_property(value, '', prop), 'Metal output connection failed')

        output(node('MaterialExpressionConstant3Vector',
                    constant=u.LinearColor(*settings['color'], 1.)), u.MaterialProperty.MP_BASE_COLOR)
        for key, prop in (('metallic', u.MaterialProperty.MP_METALLIC),
                          ('specular', u.MaterialProperty.MP_SPECULAR)):
            output(node('MaterialExpressionConstant', r=settings[key]), prop)
        # Fine directional grain changes roughness by only +/-0.02.
        # No coarse albedo noise, damage layer, normal-map relief or emissive output.
        position = node('MaterialExpressionWorldPosition')
        direction = node('MaterialExpressionConstant3Vector', constant=u.LinearColor(2.7, 1.9, .6, 1.))
        dot = node('MaterialExpressionDotProduct')
        link(position, dot, 'A'); link(direction, dot, 'B')
        sine = node('MaterialExpressionSine', period=1.)
        link(dot, sine, '')
        grain = node('MaterialExpressionMultiply', const_b=.02)
        link(sine, grain, 'A')
        roughness = node('MaterialExpressionAdd', const_b=settings['roughness'])
        link(grain, roughness, 'A')
        output(roughness, u.MaterialProperty.MP_ROUGHNESS)
        edit.layout_material_expressions(material)
        errors = edit.recompile_material(material)
        require(not errors, 'Private podium metal native shader compile failed: ' + str(errors))
        values[name] = material
    return values


def apply(ctx, expected_map_sha256):
    import unreal as u
    map_file = ROOT / ('Content/' + MAP[6:] + '.umap')
    require(re.fullmatch('[0-9a-f]{64}', expected_map_sha256) and
            sha(map_file) == expected_map_sha256 and
            u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world().get_path_name().split('.')[0] == MAP,
            'Require exact latest saved owner preview')
    composition_file = LOCAL / 'StationOperationsComposition5.json'
    capture_file = LOCAL / 'StationOperationsCompositionCapture6/manifest.json'
    probe_file = LOCAL / 'StationOperationsCompositionProbe1.json'
    require(sha(composition_file) == COMPOSITION_SHA and sha(capture_file) == CAPTURE_SHA and
            sha(probe_file) == PROBE_SHA, 'Preserve reviewed native podium proofs')
    composition = json.loads(composition_file.read_text())
    capture = json.loads(capture_file.read_text())
    probe = json.loads(probe_file.read_text())
    require(composition['success'] and composition['preservation_pass'] and capture['success'] and
            capture['natural_rotation']['passed'] and len(capture['images']) == 6 and
            capture['files_unchanged'] and capture['saves_unchanged'] and capture['ships_unchanged'] and
            capture['pie_stopped'] and capture['map_sha256'] == composition['after_sha256'],
            'Require actual original podium save, pixels and natural rotation evidence')
    sources = dict(composition['saved_asset_sha256'])
    sources.update(probe['probe']['source_sha256'])
    require(all(sha(ROOT / ('Content/' + package.split('.')[0][6:] + '.uasset')) == digest
                for package, digest in sources.items()), 'Original podium geometry/material/sequence sources changed')
    actors = list(ctx.eas.get_all_level_actors())
    before = {actor.get_path_name(): state(actor, u) for actor in actors}
    expected = copy.deepcopy(before)

    def one(label):
        found = [actor for actor in actors if actor.get_actor_label() == label]
        require(len(found) == 1, 'Require one exact podium actor: ' + label)
        return found[0]

    # Density may add hardware elsewhere, but every original podium part and pose
    # must still be present before any material asset is created.
    for row in composition['changes']['created']:
        actor = one(row['label'])
        transform = actor.get_actor_transform()
        rotation = transform.rotation.to_tuple()
        # q and -q represent the same orientation after native serialization.
        rotation_error = min(math.dist(rotation, row['rotation']),
                             math.dist(rotation, [-value for value in row['rotation']]))
        require(math.dist(transform.translation.to_tuple(), row['location']) < .05 and
                rotation_error < .00001 and
                math.dist(transform.scale3d.to_tuple(), row['scale']) < .00001,
                'An original podium/Phoenix/sequence pose changed: ' + row['label'])
    panel_slots = [row['asset'] for row in probe['probe']['meshes'][PANEL]['materials']]
    targets, current = [], []
    for row in whitelist():
        actor = one(row['label'])
        components = actor.get_components_by_class(u.StaticMeshComponent)
        require(len(components) == 1 and path(components[0].static_mesh) == row['mesh'],
                'Podium finish mesh identity changed: ' + row['label'])
        component = components[0]
        material_paths = [path(value) for value in component.get_materials()]
        require(material_paths == (panel_slots if row['mesh'] == object_path(PANEL) else [row['source']]),
                'Current native podium slots differ from reviewed original: ' + row['label'])
        targets.append((actor, component, row))
        current.append({'label': row['label'], 'component': component.get_path_name(),
                        'mesh': row['mesh'], 'materials': material_paths})
        for material in component.get_materials():
            package = material.get_path_name().split('.')[0]
            sources[package] = sha(ROOT / ('Content/' + package[6:] + '.uasset'))
    materials = _metals(u)
    changes = []
    for actor, component, row in targets:
        value = materials[row['metal']]
        for slot in row['slots']:
            old = path(component.get_material(slot))
            component.set_material(slot, value)
            require(component.get_material(slot) == value, 'Podium material slot readback failed')
            expected[actor.get_path_name()]['materials'][component.get_path_name()][slot] = value.get_path_name()
            changes.append({'label': actor.get_actor_label(), 'actor': actor.get_path_name(),
                            'component': component.get_path_name(), 'slot': slot, 'source': old,
                            'private': value.get_path_name(), 'metal': row['metal']})
    require(len(changes) == 44 and not ctx.created and
            {actor.get_path_name(): state(actor, u) for actor in ctx.eas.get_all_level_actors()} == expected,
            'Finish changed actor, geometry, light, glass, hologram, sequence or an unlisted material slot')
    require(sha(map_file) == expected_map_sha256 and all(
            sha(ROOT / ('Content/' + package.split('.')[0][6:] + '.uasset')) == digest
            for package, digest in sources.items()), 'Helper saved map or changed an original source')
    return {'dirty_assets': [value.get_path_name() for value in materials.values()], 'changes': changes,
            'current_native_material_readbacks': current, 'source_sha256': sources,
            'material_settings': METALS, 'new_actor_count': 0, 'new_light_count': 0,
            'original_geometry_glass_hologram_sequence_services_lounge_preserved': True,
            'proof_sha256': {'composition5': COMPOSITION_SHA, 'capture6': CAPTURE_SHA, 'native_kit': PROBE_SHA},
            'limits': 'Private metal candidate; actual native saved-room pixels and owner quality approval remain open.'}
