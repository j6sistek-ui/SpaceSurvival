"""Stage eight private satin Goliath children, without saving or changing lights.

The lead combines this helper with the separate podium finish in one guarded
native transaction. Earlier finish candidates remain frozen and unrun. Native
texture, mask, switch and untouched parameter values remain inherited exactly;
the accepted lounge and every other actor/component stay unchanged.
"""
import copy
import hashlib
import json
import re
from pathlib import Path

from RefineStationOperationsDisplays import _state as _original_state

MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
PRIVATE = '/Game/OutpostSandbox/StationRefinement/OperationsFinishMaterial20261007'
TABLE = 'Engineering/Primary workstation/SM_GoliathTable02_Clean'
PROBE_SHA = '363188f0e330eb053c0038b2933c4349b0b3bf1c75341fd2957a6500ac89b80d'
SCALARS = {'Min Roughness': .42, 'Max Roughness': .85, 'Normal Intensity': .75,
           'Metalness Intensity': .85, 'Albedo Tint Intensity': .65}
TINT = (.14, .18, .22, 1.)


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def _state(actor, u):
    value = _original_state(actor, u)
    value['light_properties'] = {c.get_path_name(): {key: str(c.get_editor_property(key)) for key in
        ('intensity', 'light_color', 'cast_shadows', 'indirect_lighting_intensity',
         'volumetric_scattering_intensity', 'specular_scale', 'affects_world')}
        for c in actor.get_components_by_class(u.LightComponent)}
    return value


def _parameters(material, edit):
    def color(value):
        return tuple(float(getattr(value, key)) for key in ('r', 'g', 'b', 'a'))
    return {
        'scalars': {str(n): float(edit.get_material_instance_scalar_parameter_value(material, n))
                    for n in edit.get_scalar_parameter_names(material)},
        'vectors': {str(n): color(edit.get_material_instance_vector_parameter_value(material, n))
                    for n in edit.get_vector_parameter_names(material)},
        'textures': {str(n): (value.get_path_name() if value else None)
                     for n in edit.get_texture_parameter_names(material)
                     for value in (edit.get_material_instance_texture_parameter_value(material, n),)},
        'switches': {str(n): bool(edit.get_material_instance_static_switch_parameter_value(material, n))
                     for n in edit.get_static_switch_parameter_names(material)}}


def apply(ctx, expected_map_sha256):
    """Only eight slots on the measured central table may change; never save."""
    import unreal as u
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    map_file = root / ('Content/' + MAP[6:] + '.umap')
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    require(re.fullmatch('[0-9a-f]{64}', expected_map_sha256) and
            sha(map_file) == expected_map_sha256 and world.get_path_name().split('.')[0] == MAP,
            'Require exact latest saved owner preview')
    probe_file = root / '.agent/local/StationRefinement/StationOperationsFinishProbe1.json'
    require(sha(probe_file) == PROBE_SHA, 'Frozen native material observations changed')
    probe = json.loads(probe_file.read_text(encoding='utf-8'))
    require(probe['success'] and probe['preservation_pass'] and probe['probe']['read_only'],
            'Require preserved observations; failed probe process shutdown remains documented')
    actors = list(ctx.eas.get_all_level_actors())
    matches = [actor for actor in actors if actor.get_actor_label() == TABLE]
    require(len(matches) == 1, 'Expected exactly one measured central Goliath body')
    actor, edit = matches[0], u.MaterialEditingLibrary
    table = actor.static_mesh_component
    row = next(value for value in probe['probe']['actors'] if value['label'] == TABLE)
    parents = list(table.get_materials())
    require(len(parents) == 8 and all(isinstance(p, u.MaterialInstanceConstant) for p in parents) and
            [p.get_path_name() for p in parents] == row['materials'] and
            table.static_mesh.get_path_name() == row['mesh'],
            'Current central body differs from the exact inspected eight-slot plan')
    require(all(not u.EditorAssetLibrary.does_asset_exist(PRIVATE + '/MI_CentralBody_' + str(i)) for i in range(8)),
            'Preserve any existing material-only finish assets')
    parent_parameters = [_parameters(parent, edit) for parent in parents]
    require(all(set(SCALARS).issubset(value['scalars']) and 'Albedo Tint' in value['vectors']
                for value in parent_parameters), 'Actual satin parameter interface changed')
    # Protect the source materials, their full parent chain and native textures.
    # No source package is saved, edited or duplicated in place.
    sources = {}

    def protect(asset):
        package = asset.get_path_name().split('.')[0]
        if package.startswith('/Engine/'):
            return
        require(package.startswith('/Game/'), 'Unexpected material dependency namespace')
        parts = package[6:].split('/')
        require(all(p and p not in ('.', '..') and ':' not in p and chr(92) not in p for p in parts),
                'Invalid source package path')
        path = root / ('Content/' + package[6:] + '.uasset')
        require(path.resolve().is_relative_to((root / 'Content').resolve()), 'Material dependency escaped workspace')
        sources[package] = sha(path)

    for parent in parents:
        lineage = set()
        source = parent
        while source:
            path = source.get_path_name()
            require(path not in lineage, 'Cyclic material lineage')
            lineage.add(path)
            protect(source)
            if not isinstance(source, u.MaterialInstanceConstant):
                break
            source = source.get_editor_property('parent')
        for name in edit.get_texture_parameter_names(parent):
            texture = edit.get_material_instance_texture_parameter_value(parent, name)
            if texture:
                protect(texture)
    before = {a.get_path_name(): _state(a, u) for a in actors}
    expected = copy.deepcopy(before)
    dirty, changes = [], []
    tools = u.AssetToolsHelpers.get_asset_tools()
    for index, (parent, native) in enumerate(zip(parents, parent_parameters)):
        child = tools.create_asset('MI_CentralBody_' + str(index), PRIVATE,
                                   u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
        require(isinstance(child, u.MaterialInstanceConstant), 'Cannot create private satin child')
        edit.set_material_instance_parent(child, parent)
        for name, target in SCALARS.items():
            # The proven UE5.8 author returns false after some successful writes;
            # judge the full native parameter readback below, not that return flag.
            edit.set_material_instance_scalar_parameter_value(child, name, target)
        edit.set_material_instance_vector_parameter_value(child, 'Albedo Tint', u.LinearColor(*TINT))
        edit.update_material_instance(child)
        observed = _parameters(child, edit)
        preserved = copy.deepcopy(native)
        preserved['scalars'].update(SCALARS)
        preserved['vectors']['Albedo Tint'] = TINT
        require(observed['textures'] == preserved['textures'] and observed['switches'] == preserved['switches'] and
                observed['scalars'].keys() == preserved['scalars'].keys() and
                all(abs(observed['scalars'][name] - target) < .0001 for name, target in preserved['scalars'].items()) and
                observed['vectors'].keys() == preserved['vectors'].keys() and
                all(all(abs(a-b) < .0001 for a, b in zip(observed['vectors'][name], target))
                    for name, target in preserved['vectors'].items()),
                'Private satin child changed native texture, switch or unlisted parameter')
        require(child.get_editor_property('parent') == parent, 'Private satin child lost native parent')
        table.set_material(index, child)
        expected[actor.get_path_name()]['materials'][table.get_path_name()][index] = child.get_path_name()
        dirty.append(child)
        changes.append({'label': TABLE, 'actor': actor.get_path_name(), 'component': table.get_path_name(),
                        'slot': index, 'source': parent.get_path_name(), 'private': child.get_path_name(),
                        'scalars': dict(SCALARS), 'vectors': {'Albedo Tint': list(TINT)},
                        'native_textures_preserved': True, 'native_switches_preserved': True})
    after = {a.get_path_name(): _state(a, u) for a in ctx.eas.get_all_level_actors()}
    require(after == expected and sha(map_file) == expected_map_sha256,
            'Unlisted actor/material/pose/light/service/collision changed or helper saved map')
    require(all(sha(root / ('Content/' + p[6:] + '.uasset')) == digest for p, digest in sources.items()),
            'Native source material, parent or texture changed')
    require(len(dirty) == len(changes) == 8, 'Unexpected central satin material-only scope')
    return {'dirty_assets': dirty, 'changes': changes, 'source_sha256': sources,
            'material_slot_allowlist': [{'actor': row['actor'], 'component': row['component'], 'slot': row['slot'],
                                        'before': row['source'], 'after': row['private']} for row in changes],
            'light_changes': [], 'lens_changes': [], 'new_actor_count': 0, 'new_light_count': 0,
            'probe_sha256': PROBE_SHA,
            'probe_process_shutdown': 'FAILED3: preserved data used; not a clean native probe pass',
            'existing_layout_services_collision_screens_lights_lounge_preserved': True,
            'limits': ['PREPARED/UNRUN. Native saved pixels must judge the eight central satin children.',
                       'All four pod bodies, seven lamp lenses, lighting and podium geometry stay unchanged.']}
