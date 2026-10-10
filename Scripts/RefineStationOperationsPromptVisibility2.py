"""Retire exactly six redundant Operations text labels; never load or save.

The lead's transaction owns the preview map and prior receipt. All terminal
identities, access, geometry, text source fields and collision are preserved.
Nearby actions come from the existing HUD; fitted graphic displays remain.
"""
import copy
import json
import math
import re

import RefineStationOperationsDisplays as displays
from RefineStationSocialSeatedCrew import _one

MAP = displays.MAP
SERVICES = ('FLIGHT UPGRADES', 'SHIP & PARTS', 'PILOT LEADERBOARD',
            'CONTRACT EXCHANGE', 'TRADE NETWORK')
LABELS = ('Refine/Operations/Identity',) + tuple('Services/'+name+'/Face' for name in SERVICES)
TEXT_PROPERTIES = ('text', 'world_size', 'x_scale', 'y_scale', 'horizontal_alignment',
                   'vertical_alignment', 'text_render_color')


def _state(actor, u):
    result = displays._state(actor, u)
    result.update(label=actor.get_actor_label(), tags=tuple(map(str, actor.tags)),
                  folder=str(actor.get_folder_path()), editor_hidden=actor.is_temporarily_hidden_in_editor(),
                  parent=displays._path(actor.get_attach_parent_actor()))
    result['text'] = {}
    for component in actor.get_components_by_class(u.TextRenderComponent):
        result['text'][component.get_path_name()] = {
            key: str(component.get_editor_property(key)) for key in TEXT_PROPERTIES}
        result['text'][component.get_path_name()].update({
            key: displays._path(component.get_editor_property(key)) for key in ('font', 'text_material')})
    return result


def apply(ctx, expected_map_sha256):
    """Stage visibility-only edits after all exact-label/type/identity guards."""
    import unreal as u
    require, sha = displays._require, displays._sha
    map_file = displays.ROOT/('Content/'+MAP[6:]+'.umap')
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    require(re.fullmatch('[0-9a-f]{64}', expected_map_sha256) and
            sha(map_file) == expected_map_sha256 and world.get_path_name().split('.')[0] == MAP,
            'Require exact latest saved owner preview')
    require(sha(displays.BASELINE) == displays.BASELINE_SHA, 'Native Operations inventory changed')
    native = {row['label']: row for row in json.loads(displays.BASELINE.read_text())['operations']['actors']}
    actors = list(ctx.eas.get_all_level_actors())
    before = {actor.get_path_name(): _state(actor, u) for actor in actors}
    expected = copy.deepcopy(before)
    sources, retired, targets = {}, [], []
    terminals = [_one(actors, 'Services/'+name) for name in SERVICES]
    for name, actor in zip(SERVICES, terminals):
        require(isinstance(actor, u.SSOutpostTerminal) and actor.get_editor_property('display_name') == name,
                'Expected original service identity '+name)
    for label in LABELS:
        actor = _one(actors, label)
        row = native[label]
        require(isinstance(actor, u.TextRenderActor) and actor.get_path_name() == row['actor'],
                'Text label identity changed '+label)
        transform = actor.get_actor_transform()
        require(all(math.dist(getattr(transform, attr).to_tuple(), row['transform'][key]) < .001
                    for attr, key in (('translation', 'location'), ('rotation', 'rotation'), ('scale3d', 'scale'))),
                'Reviewed label placement changed '+label)
        components = actor.get_components_by_class(u.TextRenderComponent)
        require(len(components) == 1 and str(components[0].get_editor_property('text')) == row['text']['text'],
                'Reviewed label text changed '+label)
        # TextRenderActor also has an editor ArrowComponent hidden in game by
        # default. Its visibility is not the label's presentation state. Guard
        # and retire the exact measured TextRenderComponent, preserving arrows.
        component_path = components[0].get_path_name()
        require(component_path in before[actor.get_path_name()]['components'],
                'Expected native TextRenderComponent visibility state '+label)
        for key in ('font', 'text_material'):
            asset = components[0].get_editor_property(key)
            if asset and asset.get_path_name().startswith('/Game/'):
                package = asset.get_path_name().split('.')[0]
                sources[package] = sha(displays.ROOT/('Content/'+package[6:]+'.uasset'))
        targets.append(actor)

    persistent_changes = 0
    for actor in targets:
        actor_path = actor.get_path_name()
        text_component = actor.get_component_by_class(u.TextRenderComponent)
        previous = before[actor_path]['components'][text_component.get_path_name()]
        already_retired = before[actor_path]['hidden'] and not previous['visible'] and previous['hidden']
        persistent_changes += int(not already_retired)
        actor.set_actor_hidden_in_game(True)
        actor.set_is_temporarily_hidden_in_editor(True)
        expected[actor_path]['hidden'] = True
        expected[actor_path]['editor_hidden'] = True
        text_component.set_visibility(False)
        text_component.set_hidden_in_game(True)
        state = expected[actor_path]['components'][text_component.get_path_name()]
        state['visible'], state['hidden'] = False, True
        retired.append({'label': actor.get_actor_label(), 'actor': actor_path,
                        'retained_text': before[actor_path]['text'], 'already_retired': bool(already_retired),
                        'previous_actor_hidden': before[actor_path]['hidden'],
                        'previous_text_visibility': dict(previous),
                        'collision_and_source_preserved': True})
        ctx.records.append({'kind': 'retire_redundant_operations_text', 'label': actor.get_actor_label(),
                            'actor': actor_path, 'source_text_and_collision_preserved': True})

    require(len(actors) == len(ctx.eas.get_all_level_actors()) and
            all(_state(actor, u) == expected[actor.get_path_name()] for actor in actors),
            'Unexpected actor, text source, service access, collision, transform, light or material change')
    require(sha(map_file) == expected_map_sha256 and
            all(sha(displays.ROOT/('Content/'+package[6:]+'.uasset')) == digest
                for package, digest in sources.items()), 'Helper cannot save or mutate source packages')
    return {'dirty_assets': [], 'source_sha256': sources, 'retired_labels': retired,
            'terminal_identities': [{'actor': actor.get_path_name(),
                                     'label': actor.get_actor_label(),
                                     'service': before[actor.get_path_name()]['service']}
                                    for actor in terminals],
            'new_actor_count': 0, 'new_light_count': 0, 'persistent_label_changes': persistent_changes,
            'all_terminal_access_anchors_and_unrelated_actors_preserved': True,
            'limits': 'Six exact TextRender visibility targets, including already-retired no-ops; editor arrows preserved. Source text remains reversible; original terminal '
                      'actions/access/anchors and fitted graphics remain. Contextual HUD changes require a native '
                      'build and current rendered readability review; preview Information actions stay informational.'}
