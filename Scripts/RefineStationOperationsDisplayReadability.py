"""Four resident display derivatives and three complete rear-pair offsets.

No source materials, walls, global streaming settings, lighting or services change.
The lead owns saves and fresh matched visual review.
"""
import copy
import json
import math
import re

import RefineStationOperationsDisplays as original
from RefineStationSocialSeatedCrew import _one

MAP = original.MAP
BASE = '/Game/OutpostSandbox/StationRefinement/OperationsDisplayReadability20261007'
NAMES = tuple(row[1] for row in original.TARGETS)
TEXTURE_PROPERTIES = ('srgb', 'compression_settings', 'lod_group', 'mip_gen_settings',
                      'address_x', 'address_y', 'lod_bias', 'max_texture_size', 'filter',
                      'virtual_texture_streaming')
OFFSET = (-15., 0., 0.)


def apply(ctx, expected_map_sha256):
    import unreal as u
    require, sha, path = original._require, original._sha, original._path
    root = original.ROOT
    map_file = root/('Content/'+MAP[6:]+'.umap')
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    require(re.fullmatch('[0-9a-f]{64}', expected_map_sha256) and sha(map_file) == expected_map_sha256 and
            world.get_path_name().split('.')[0] == MAP, 'Require exact latest saved owner preview')
    require(sha(original.BASELINE) == original.BASELINE_SHA, 'Preserve native Operations inventory')
    baseline = json.loads(original.BASELINE.read_text())['operations']
    native = {row['label']: row for row in baseline['actors']}
    actors = list(ctx.eas.get_all_level_actors())
    before = {a.get_path_name(): original._state(a, u) for a in actors}
    expected = copy.deepcopy(before)
    dirty, sources, textures, materials, assignments, offsets = [], {}, [], [], [], []
    edit = u.MaterialEditingLibrary

    def guard(asset):
        package = path(asset).split('.')[0]
        require(package.startswith('/Game/'), 'Unexpected private display source')
        sources[package] = sha(root/('Content/'+package[6:]+'.uasset'))
        return package

    replacements = {}
    for name in NAMES:
        source_texture = ctx.asset(original.BASE+'/Textures/T_'+name)
        source_material = ctx.asset(original.BASE+'/Materials/M_'+name)
        texture_package, material_package = guard(source_texture), guard(source_material)
        source_nodes = edit.get_material_expressions(source_material)
        source_art = [n for n in source_nodes if isinstance(n, u.MaterialExpressionTextureObjectParameter)]
        source_shader = [n for n in source_nodes if isinstance(n, u.MaterialExpressionCustom)]
        require(len(source_art) == len(source_shader) == 1 and
                path(source_art[0].get_editor_property('texture')) == path(source_texture),
                'Expected one unchanged approved artwork input')
        texture_destination, material_destination = BASE+'/Textures/T_'+name, BASE+'/Materials/M_'+name
        require(not u.EditorAssetLibrary.does_asset_exist(texture_destination) and
                not u.EditorAssetLibrary.does_asset_exist(material_destination), 'Preserve previous readability assets')
        texture = u.EditorAssetLibrary.duplicate_asset(texture_package, texture_destination)
        require(isinstance(texture, u.Texture2D), 'Cannot copy private Operations texture')
        properties = {key: source_texture.get_editor_property(key) for key in TEXTURE_PROPERTIES}
        texture.set_editor_property('never_stream', True)
        require(texture.get_editor_property('never_stream') and all(
            texture.get_editor_property(key) == value for key, value in properties.items()),
            'Residency correction changed texture appearance/mip settings')
        dimensions = [int(texture.blueprint_get_size_x()), int(texture.blueprint_get_size_y())]
        require(dimensions == ([2048, 768] if name == '04_FlightUpgrades' else [2048, 1024]),
                'Approved pixel dimensions changed')
        material = u.EditorAssetLibrary.duplicate_asset(material_package, material_destination)
        require(material is not None, 'Cannot copy private Operations material')
        nodes = edit.get_material_expressions(material)
        art = [n for n in nodes if isinstance(n, u.MaterialExpressionTextureObjectParameter)]
        shader = [n for n in nodes if isinstance(n, u.MaterialExpressionCustom)]
        require(len(art) == len(shader) == 1, 'Copied display graph differs')
        art[0].set_editor_property('texture', texture)
        errors = edit.recompile_material(material)
        require(not errors and shader[0].get_editor_property('code') == source_shader[0].get_editor_property('code'),
                'Readability copy changed UV/gain/artwork shader or failed compilation')
        require(material.get_editor_property('blend_mode') == source_material.get_editor_property('blend_mode') and
                material.get_editor_property('two_sided') == source_material.get_editor_property('two_sided'),
                'Readability copy changed blend/side behavior')
        dirty.extend((path(texture), path(material)))
        replacements[path(source_material)] = material
        textures.append({'source': path(source_texture), 'private': path(texture), 'dimensions': dimensions,
                         'never_stream': bool(texture.get_editor_property('never_stream')),
                         'original_mips_compression_filter_preserved': True})
        materials.append({'source': path(source_material), 'private': path(material),
                          'native_compile_errors': list(errors), 'original_uv_gain_opacity_shader_preserved': True})

    allowed = {row[0] for row in original.TARGETS[:3]} | {original.INSERT_PREFIX+'Glass'}
    for actor in actors:
        for component in actor.get_components_by_class(u.StaticMeshComponent):
            for slot, material in enumerate(component.get_materials()):
                if path(material) not in replacements:
                    continue
                require(actor.get_actor_label() in allowed, 'Original display source escaped reviewed scope')
                replacement = replacements[path(material)]
                component.set_material(slot, replacement)
                expected[actor.get_path_name()]['materials'][component.get_path_name()][slot] = path(replacement)
                assignments.append({'label': actor.get_actor_label(), 'component': component.get_name(), 'slot': slot,
                                    'before_material': path(material), 'after_material': path(replacement)})
    require(len(assignments) == 7 and {row['label'] for row in assignments} == allowed,
            'Expected precisely three double-sided panes and one central insert')

    # Original SmartStorage wall fronts reachX9142.85. The prior graphic surface
    # wasX9150.86, inside that hardware. Move each complete native pair15cm toward
    # the room. Its retained42.3cm-deep frame still overlaps the supporting wall.
    for index in (1, 2, 3):
        for part in ('Frame', 'Glass'):
            label = 'Refine/Operations/Rear data %d/%s' % (index, part)
            actor = _one(actors, label)
            row = native[label]
            component = actor.get_component_by_class(u.StaticMeshComponent)
            require(component and path(component.static_mesh) == row['components'][0]['mesh'] and
                    math.dist(actor.get_actor_location().to_tuple(), row['transform']['location']) < .001,
                    'Rear pair no longer matches actual baseline')
            old = tuple(actor.get_actor_location().to_tuple())
            new = tuple(old[i]+OFFSET[i] for i in range(3))
            ctx.move(actor, new)
            snapshot = expected[actor.get_path_name()]
            snapshot['location'] = new
            for state in snapshot['components'].values():
                state['location'] = tuple(state['location'][i]+OFFSET[i] for i in range(3))
            bounds = {key: [value[i]+OFFSET[i] for i in range(3)] for key, value in row['bounds'].items()
                      if key in ('minimum', 'maximum', 'center')}
            if part == 'Glass':
                require(bounds['maximum'][0] < 9142.8-3., 'Pane must clear the actual protruding storage wall')
            else:
                require(bounds['maximum'][0] > 9142.8+5., 'Rear frame must remain supported against native wall')
            offsets.append({'label': label, 'old_location': old, 'new_location': new,
                            'shift_cm': list(OFFSET), 'native_bounds_after': bounds,
                            'collision_preserved': True})
    require(all(original._state(a, u) == expected[a.get_path_name()] for a in actors),
            'Unrelated actor, pose, source material, collision, light or service changed')
    require(sha(map_file) == expected_map_sha256 and all(
        sha(root/('Content/'+p[6:]+'.uasset')) == digest for p, digest in sources.items()),
        'Helper must not save or mutate any source package')
    return {'dirty_assets': dirty, 'source_sha256': sources, 'textures': textures, 'materials': materials,
            'assignments': assignments, 'pair_offsets': offsets, 'new_actor_count': 0, 'new_light_count': 0,
            'protected_existing_layout_animation_lighting_services_preserved': True,
            'original_walls_and_outer_frames_preserved': True,
            'resident_budget': 'Four BC7 images:7.5MiB base levels, approximately10MiB with full mip chains; no global pool change.',
            'limits': 'NeverStream addresses suspected streaming mip residency; visual cause/repair requires matched actual pixels. Source texture pixels, material shaders, collision and all lights unchanged.'}
