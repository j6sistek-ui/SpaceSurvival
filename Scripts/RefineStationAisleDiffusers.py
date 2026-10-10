"""Light the two existing native glass diffusers; no global lighting changes.

Import1 measured black emission on slot1 despite an emissive housing in slot0.
The lead owns explicit saves and matched rendered review of this new child MIC.
"""
import hashlib
from pathlib import Path

from RefineStationSocialVisualFinish import _values
from StationRefinementSupport import transform_record


MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
SOURCE = '/Game/CyberpunkRestaurant/Materials/MI_Light_Lamp_Glass'
TARGET = '/Game/OutpostSandbox/StationRefinement/SocialVisualFinish/MI_AisleLampGlassLit'
FIXTURE = '/Game/CyberpunkRestaurant/Meshes/SM_Fluorescent_Light_01'
HOUSING = '/Game/OutpostSandbox/StationRefinement/SocialVisualFinish/MI_AisleLampLit'


def _path(asset):
    return asset.get_path_name().split('.')[0] if asset else None


def _require(condition, message):
    if not condition:
        raise RuntimeError(message)


def apply(ctx, expected_map_sha256):
    import unreal as u
    root = Path(u.Paths.project_dir()).resolve()
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    _require(world.get_path_name().split('.')[0] == MAP, 'Wrong map for the bounded diffuser correction')
    map_file = root / ('Content/' + MAP[6:] + '.umap')
    _require(hashlib.sha256(map_file.read_bytes()).hexdigest() == expected_map_sha256, 'Owner preview changed')
    _require(not u.EditorAssetLibrary.does_asset_exist(TARGET), 'Preserve existing diffuser candidate')
    source = ctx.asset(SOURCE)
    edit = u.MaterialEditingLibrary
    baseline = _values(edit, source)
    _require(baseline['vectors']['Emmisive Color'] == (0., 0., 0., 1.) and
             abs(baseline['scalars']['Emmisive Intensity']-5.) < 1.e-5,
             'Native lamp glass no longer matches Import1 evidence')
    _require(baseline['textures']['Emmisive Map'] == '/Game/CyberpunkRestaurant/Textures/T_Fill_Emissive',
             'Preserve the verified native diffuser emission texture')
    protected_paths = [SOURCE, FIXTURE, HOUSING] + [p for p in baseline['textures'].values() if p]
    files = {p: root / ('Content/' + p[6:] + '.uasset') for p in protected_paths}
    hashes = {p: hashlib.sha256(f.read_bytes()).hexdigest() for p, f in files.items()}
    poses = {a.get_path_name(): transform_record(a) for a in ctx.actors}
    folder, name = TARGET.rsplit('/', 1)
    material = u.AssetToolsHelpers.get_asset_tools().create_asset(
        name, folder, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
    _require(material, 'Private diffuser material creation failed')
    edit.set_material_instance_parent(material, source)
    color, intensity = (1.2, 1., .78, 1.), 2.
    # UE5.8 MaterialEditingLibrary.cpp setters return their unchanged false
    # local even after Set*ParameterValueEditorOnly and UpdateMaterialInstance.
    # Validate actual values below instead of treating that return as success.
    edit.set_material_instance_vector_parameter_value(material, 'Emmisive Color', u.LinearColor(*color))
    edit.set_material_instance_scalar_parameter_value(material, 'Emmisive Intensity', intensity)
    edit.update_material_instance(material)
    actual = _values(edit, material)
    actual_color = actual['vectors'].pop('Emmisive Color')
    actual_intensity = actual['scalars'].pop('Emmisive Intensity')
    expected = _values(edit, source)
    expected['vectors'].pop('Emmisive Color')
    expected['scalars'].pop('Emmisive Intensity')
    _require(actual == expected and max(abs(a-b) for a, b in zip(actual_color, color)) < 1.e-5 and
             abs(actual_intensity-intensity) < 1.e-5, 'Private diffuser changed unrelated native settings')
    fixtures = []
    for index in (1, 2):
        label = 'Refine/SocialAtmosphereFollowup/Aisle %d/Housing' % index
        actors = [a for a in ctx.actors if a.get_actor_label() == label]
        _require(len(actors) == 1, 'Missing reviewed central fixture: ' + label)
        component = actors[0].get_component_by_class(u.StaticMeshComponent)
        _require(_path(component.static_mesh) == FIXTURE and
                 [_path(m) for m in component.get_materials()] == [HOUSING, SOURCE],
                 'Fixture mesh or material slots changed: ' + label)
        component.set_material(1, material)
        _require(component.get_material(1) == material and _path(component.get_material(0)) == HOUSING,
                 'Diffuser slot assignment failed')
        fixtures.append({'label': label, 'slot': 1, 'material': material.get_path_name()})
    _require(all(transform_record(a) == poses[a.get_path_name()] for a in ctx.actors),
             'Diffuser correction changed actor placement')
    _require(all(hashlib.sha256(files[p].read_bytes()).hexdigest() == h for p, h in hashes.items()),
             'Original fixture material/texture/mesh changed')
    _require(hashlib.sha256(map_file.read_bytes()).hexdigest() == expected_map_sha256, 'Unexpected map save')
    return {'dirty_assets': [material], 'fixtures': fixtures, 'emissive_color_linear': color,
            'emissive_intensity': intensity, 'emissive_texture': baseline['textures']['Emmisive Map'],
            'source_sha256': hashes, 'protected_actor_count': len(poses),
            'light_component_changes': [], 'saved': False, 'render_acceptance': 'Pending matched capture'}
