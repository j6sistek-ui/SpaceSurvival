"""Move the two existing glass menus from basins to measured dry counter patches.

No new assets, materials, lighting or actors. The lead saves the owner preview.
Source geometry and the native dry-top survey are pinned before any mutation.
"""
import hashlib
import json
import math
import re
from pathlib import Path

from OutpostGeometryUtils import mesh_union
from RefineStationBarPresentation import _one, _require
from RefineStationLoungeCeiling import _snapshot
from StationRefinementSupport import transform_record

MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
PREFIX = 'Refine/BarDisplays/Tablet '
SURVEY = 'StationBarDisplayReadabilityCapture3/manifest.json'
SURVEY_SHA = '2332d7e1a20f99d299b27383ff56e860231e405642991acce29e01e0e3ae6961'
DESTINATIONS = ((3840., -4055.), (4265., -4055.))
PARTS = ('Native dock', 'Stem', 'Clamp', 'Glass menu', 'Status lens')
TOP = 107.55418


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def apply(ctx, expected_map_sha256):
    """Stage only ten measured actor transforms; retain attachment relationships."""
    import unreal as u
    from RefineStationSocialSeatedCrew import _geometry
    from RefineStationSocialFinish import _surface

    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    map_file = root / ('Content/' + MAP[6:] + '.umap')
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    _require(re.fullmatch('[0-9a-f]{64}', expected_map_sha256) and
             _sha(map_file) == expected_map_sha256 and world.get_path_name().split('.')[0] == MAP,
             'Require the exact latest saved owner preview')
    survey_file = root / '.agent/local/StationRefinement' / SURVEY
    _require(_sha(survey_file) == SURVEY_SHA, 'Native dry-counter survey changed')
    survey = json.loads(survey_file.read_text())
    _require(survey['success'] and survey['map_sha256'] == expected_map_sha256 and
             survey['files_unchanged'] and survey['saves_unchanged'], 'Survey does not match this scene')
    actors = list(ctx.eas.get_all_level_actors())
    before = {a.get_path_name(): _snapshot(a, u) for a in actors}
    counters = [_one(actors, 'Refine/Social/Bar/Counter ' + side) for side in ('left', 'right')]
    obstacles = [_one(actors, 'Refine/Social/Bar/' + name) for name in
                 ('Coffee machine', 'Coffee glasses', 'Wine glass', 'Serving glasses')]
    _, geometry = _geometry(counters[0].static_mesh_component.static_mesh, False, u)
    source_hashes, staged = {}, []
    for index, (counter, xy) in enumerate(zip(counters, DESTINATIONS)):
        matched = [r for r in survey['dry_counter_probe']['accepted']
                   if r['tablet'] == index and r['xy'] == list(xy)]
        _require(len(matched) == 1, 'Chosen tablet location was not accepted by native survey')
        points = [xy] + [(xy[0] + sx*10., xy[1] + sy*7.) for sx in (-1., 1.) for sy in (-1., 1.)]
        heights = [_surface(counter, geometry, *point, u) for point in points]
        _require(max(heights)-min(heights) < .08 and abs(max(heights)-TOP) < .08,
                 'Actual dry counter footprint is no longer supported')
        prop_rows = []
        for item in obstacles:
            c, e = mesh_union(item)
            clear = not (abs(c.x-xy[0]) < e.x+24. and abs(c.y-xy[1]) < e.y+15.)
            _require(clear, 'Dry tablet overlaps existing bar prop: ' + item.get_actor_label())
            prop_rows.append({'label': item.get_actor_label(), 'center': list(c.to_tuple()),
                              'extent': list(e.to_tuple()), 'clear': clear})
        group = {part: _one(actors, PREFIX + '%d/' % index + part) for part in PARTS}
        old = {part: transform_record(actor) for part, actor in group.items()}
        parents = {'Native dock': counter, 'Stem': group['Native dock'],
                   'Clamp': group['Stem'], 'Glass menu': group['Stem'], 'Status lens': group['Stem']}
        for part, actor in group.items():
            _require(actor.get_attach_parent_actor() == parents[part], 'Tablet attachment changed: ' + part)
            _require(not actor.get_actor_enable_collision(), 'Decorative tablet collision changed')
            _require(not actor.get_editor_property('hidden'), 'Tablet was hidden by owner')
            for asset in [actor.static_mesh_component.static_mesh, *actor.static_mesh_component.get_materials()]:
                if asset and asset.get_path_name().startswith('/Game/'):
                    package = asset.get_path_name().split('.')[0]
                    source_hashes[package] = _sha(root / ('Content/' + package[6:] + '.uasset'))
        old_xy = (4045.+415.*index, -4059.7)
        c, e = mesh_union(group['Native dock'])
        _require(math.dist((c.x, c.y), old_xy) < .02 and abs(c.z-e.z-92.24733) < .02,
                 'Refuse to overwrite an unexpected owner tablet placement')
        _require(math.dist(old['Glass menu']['location'], (old_xy[0], old_xy[1]-4.7, 126.)) < .02,
                 'Original tablet glass mark changed')
        _require(e.x < 10. and e.y < 7., 'Native dock exceeds the measured five-point footprint')
        staged.append((index, group, old, parents, xy, max(heights), heights, prop_rows))

    changed, rows = set(), []
    for index, group, old, parents, xy, top, heights, props in staged:
        old_xy = (4045.+415.*index, -4059.7)
        dx, dy = xy[0]-old_xy[0], xy[1]-old_xy[1]
        stem_bottom, stem_top = top+.5, 116.3
        targets = {part: actor.get_actor_transform() for part, actor in group.items()}
        dock_center, dock_extent = mesh_union(group['Native dock'])
        targets['Native dock'].translation = targets['Native dock'].translation + u.Vector(
            dx, dy, top-(dock_center.z-dock_extent.z))
        targets['Stem'].translation = u.Vector(xy[0], xy[1], (stem_bottom+stem_top)*.5)
        targets['Stem'].scale3d = u.Vector(.04, .04, (stem_top-stem_bottom)/100.)
        for part in ('Clamp', 'Glass menu', 'Status lens'):
            targets[part].translation = targets[part].translation + u.Vector(dx, dy, 0.)
        # Parent first, then restore each child's absolute world transform. This
        # prevents both inherited double translation and stem-scale distortion.
        for part in PARTS:
            _require(ctx.eas.set_actor_transform(group[part], targets[part]), 'Tablet transform failed: ' + part)
            changed.add(group[part].get_path_name())
        c, e = mesh_union(group['Native dock'])
        _require(math.dist((c.x, c.y), xy) < .02 and abs(c.z-e.z-top) < .02,
                 'Native dock does not sit on the dry counter')
        sc, se = mesh_union(group['Stem'])
        _require(abs(sc.z-se.z-stem_bottom) < .02 and abs(sc.z+se.z-stem_top) < .02,
                 'Shortened pedestal is not physically continuous')
        for part in PARTS:
            actual = transform_record(group[part])
            target = targets[part]
            _require(math.dist(actual['location'], target.translation.to_tuple()) < .01 and
                     math.dist(actual['scale'], target.scale3d.to_tuple()) < .0001 and
                     math.dist(actual['rotation'], old[part]['rotation']) < .0001,
                     'World-space tablet restoration differs: ' + part)
            _require(group[part].get_attach_parent_actor() == parents[part] and
                     not group[part].get_actor_enable_collision(), 'Tablet attachment/collision changed')
        glass = group['Glass menu'].static_mesh_component
        bottom = glass.get_world_transform().transform_location(u.Vector(0., 50., 0.))
        clamp_center, clamp_extent = mesh_union(group['Clamp'])
        _require(abs(bottom.x-clamp_center.x) < .02 and abs(bottom.y-clamp_center.y) < 1. and
                 abs(bottom.z-clamp_center.z) < clamp_extent.z, 'Glass no longer seats in the clamp')
        rows.append({'tablet': index, 'destination_xy': list(xy), 'support_z_cm': top,
                     'footprint_heights_cm': heights, 'prop_clearance': props, 'before': old,
                     'after': {part: transform_record(a) for part, a in group.items()},
                     'pedestal_z_cm': [stem_bottom, stem_top], 'glass_bottom_cm': list(bottom.to_tuple()),
                     'attachments_preserved': True, 'collision_disabled': True})
    for actor in actors:
        old, now = before[actor.get_path_name()], _snapshot(actor, u)
        if actor.get_path_name() in changed:
            _require(all(now[k] == old[k] for k in ('hidden', 'materials', 'lights')),
                     'Tablet relocation altered more than location/shortened stem')
        else:
            _require(now == old, 'Protected room actor changed: ' + actor.get_actor_label())
    _require(_sha(map_file) == expected_map_sha256 and not ctx.created and all(
        _sha(root / ('Content/' + p[6:] + '.uasset')) == digest for p, digest in source_hashes.items()),
        'Tablet helper must not save, create actors or alter source packages')
    return {'dirty_assets': [], 'source_sha256': source_hashes, 'tablets': rows,
            'survey_sha256': SURVEY_SHA, 'moved_actor_count': len(changed), 'created_actor_count': 0,
            'new_light_count': 0, 'protected_existing_layout_animation_lighting_preserved': True,
            'limits': 'Decorative ordering displays only. Fresh saved-scene pixels must confirm composition.'}
