"""Stage two small occupied-table compositions from existing purchased props.

The lead owns native execution, map transaction, saving and rendered acceptance.
Three new props and one cup move; no furniture, crew, material or light edits.
"""
import hashlib
from pathlib import Path

from OutpostGeometryUtils import mesh_union
from RefineStationLoungeCeiling import _snapshot
from RefineStationSocialFinish import _surface
from RefineStationSocialSeatedCrew import _geometry, _one


MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
PREFIX = 'Refine/LoungeTableSettings/'
BAR = '/Game/CyberPunkBarAssetSet01/StaticMeshes/'
TABLE = '/Game/CyberpunkRestaurant/Meshes/SM_Table_01'
SOURCES = {
    TABLE: '5d788cc9bba6aca4619875f4542a24077f7863d1394bd00dfb3ebe967cabe0df',
    BAR+'SM_CoffeeGlasses01': '361ccd6452a7ee9c6c3ed7c887517e82ab9620132d417a77735d7a3e0aece71c',
    BAR+'SM_Glasses02': '759cc264b8f0915213c28684e7f11e697ab579ee2ba90579709b3c34baf8bae9',
    BAR+'SM_BWineBottle01': '3a3e52822a1408b44c727f038ba22ee6c1cf77f697824fa19d045d099147d610',
}
# Native half-bounds from Social1 and SocialBottleBounds, centimetres.
EXTENTS = {
    'SM_CoffeeGlasses01': (3.14675045, 3.14675903, 6.72860098),
    'SM_Glasses02': (5.30334997, 5.33256245, 14.48526859),
    'SM_BWineBottle01': (4.24652004, 4.21555424, 17.11256218),
}
POCKETS = {1: (3650., -2850.), 3: (3650., -3550.)}
TABLE_EXTENT = (73.34800720, 37.58012772, 22.22770309)
TABLE_TOP = 44.45540619
SETTINGS = (
    (1, 'Coffee near', 'SM_CoffeeGlasses01', (-35., -20.), True),
    (1, 'Coffee far', 'SM_CoffeeGlasses01', (-20., 20.), False),
    (3, 'Shared bottle', 'SM_BWineBottle01', (-7., 17.), False),
    (3, 'Stem glass', 'SM_Glasses02', (54., -20.), False),
)


def _require(condition, message):
    if not condition:
        raise RuntimeError(message)


def _path(asset):
    return asset.get_path_name().split('.')[0] if asset else None


def _bounds(actor):
    center, extent = mesh_union(actor)
    return [list((center-extent).to_tuple()), list((center+extent).to_tuple())]


def _overlap(a, b, padding=1.):
    return all(a[0][i] < b[1][i]+padding and a[1][i] > b[0][i]-padding for i in range(3))


def apply(ctx, expected_map_sha256):
    import unreal as u
    root = Path(u.Paths.project_dir()).resolve()
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    map_file = root / ('Content/' + MAP[6:] + '.umap')
    _require(world.get_path_name().split('.')[0] == MAP and
             len(expected_map_sha256) == 64 and sha(map_file) == expected_map_sha256,
             'Only the current lead-approved owner preview may receive table settings')
    actors = list(ctx.eas.get_all_level_actors())
    _require(not any(a.get_actor_label().startswith(PREFIX) for a in actors),
             'Preserve an existing table-settings pass')
    files = {path: root / ('Content/' + path[6:] + '.uasset') for path in SOURCES}
    _require(all(sha(files[path]) == digest for path, digest in SOURCES.items()),
             'A measured purchased table/prop source changed')
    assets = {path: ctx.asset(path) for path in SOURCES}
    for name, extent in EXTENTS.items():
        actual = assets[BAR+name].get_bounds().box_extent.to_tuple()
        _require(max(abs(a-b) for a, b in zip(actual, extent)) < .01,
                 'Native serving-prop dimensions changed: ' + name)
    _, geometry = _geometry(assets[TABLE], False, u)
    tables = {}
    for index, xy in POCKETS.items():
        actor = _one(actors, 'Refine/Social/Conversation %d/Low table' % index)
        component = actor.get_component_by_class(u.StaticMeshComponent)
        center, extent = mesh_union(actor)
        rotation = actor.get_actor_rotation()
        _require(component and _path(component.static_mesh) == TABLE and
                 max(abs(center.x-xy[0]), abs(center.y-xy[1]), abs(center.z+extent.z-TABLE_TOP)) < .05 and
                 max(abs(a-b) for a, b in zip(extent.to_tuple(), TABLE_EXTENT)) < .05 and
                 max(abs(rotation.pitch), abs(rotation.yaw), abs(rotation.roll)) < .001,
                 'The reviewed occupied table moved or changed: ' + str(index))
        tables[index] = actor
    coffee = _one(actors, 'Refine/Social/Conversation 1/Coffee')
    component = coffee.get_component_by_class(u.StaticMeshComponent)
    center, extent = mesh_union(coffee)
    _require(component and _path(component.static_mesh) == BAR+'SM_CoffeeGlasses01' and
             max(abs(center.x-3615.), abs(center.y+2850.), abs(center.z-extent.z-TABLE_TOP)) < .05 and
             max(abs(a-b) for a, b in zip(extent.to_tuple(), EXTENTS['SM_CoffeeGlasses01'])) < .01,
             'The original coffee is no longer at its reviewed position/scale')

    # Validate all support points and all prop gaps before the first scene edit.
    plans = []
    for index, label, name, offset, move in SETTINGS:
        xy = tuple(POCKETS[index][i]+offset[i] for i in range(2))
        extent = EXTENTS[name]
        heights = [_surface(tables[index], geometry, xy[0]+dx, xy[1]+dy, u)
                   for dx, dy in ((0., 0.), (-extent[0], -extent[1]), (-extent[0], extent[1]),
                                  (extent[0], -extent[1]), (extent[0], extent[1]))]
        _require(max(heights)-min(heights) < .05 and abs(max(heights)-TABLE_TOP) < .05,
                 'Serving prop does not rest on the flat tabletop: ' + label)
        floor = max(heights)
        bounds = [[xy[0]-extent[0], xy[1]-extent[1], floor],
                  [xy[0]+extent[0], xy[1]+extent[1], floor+2*extent[2]]]
        support = _bounds(tables[index])
        _require(all(bounds[0][i] >= support[0][i]+2 and bounds[1][i] <= support[1][i]-2
                     for i in (0, 1)), 'Serving prop would overhang the table: ' + label)
        neighbors = [a for a in actors if a != coffee and a != tables[index] and
                     a.get_actor_label().startswith(('Refine/Social/Conversation %d/' % index,
                                                     'Refine/SocialFinish/Pocket %d/' % index)) and
                     a.get_component_by_class(u.StaticMeshComponent)]
        _require(not any(_overlap(bounds, _bounds(a)) for a in neighbors),
                 'Serving prop would intersect existing furniture/tableware: ' + label)
        _require(not any(_overlap(bounds, r['bounds_cm']) for r in plans),
                 'Proposed table settings intersect each other')
        plans.append({'pocket': index, 'label': label, 'asset': BAR+name,
                      'xy_cm': xy, 'floor_z_cm': floor, 'bounds_cm': bounds, 'move_existing': move})

    before = {a.get_path_name(): _snapshot(a, u) for a in actors}
    coffee_path = coffee.get_path_name()
    for row in plans:
        if row['move_existing']:
            center, extent = mesh_union(coffee)
            position = coffee.get_actor_location() + u.Vector(row['xy_cm'][0]-center.x,
                row['xy_cm'][1]-center.y, row['floor_z_cm']-(center.z-extent.z))
            ctx.move(coffee, position)
            expected = dict(before[coffee_path], location=tuple(position.to_tuple()))
            _require(_snapshot(coffee, u) == expected, 'Cup move changed more than its position')
            actor = coffee
        else:
            actor = ctx.grounded(PREFIX+'Pocket %d/' % row['pocket']+row['label'], row['asset'],
                                 row['xy_cm'], floor=row['floor_z_cm'], collision=False)
        actual = _bounds(actor)
        _require(max(abs(actual[e][i]-row['bounds_cm'][e][i]) for e in (0, 1) for i in range(3)) < .05,
                 'Native tabletop placement differs from the measured plan')
        row['actor'] = actor.get_path_name()
    _require(all(_snapshot(a, u) == before[a.get_path_name()] for a in actors if a != coffee),
             'Table settings changed a protected pose, material, visibility or light')
    _require(all(sha(files[path]) == digest for path, digest in SOURCES.items()) and
             sha(map_file) == expected_map_sha256, 'Unexpected source/map write')
    return {'module': 'lounge_table_settings', 'dirty_assets': [], 'saved': False,
            'settings': plans, 'new_prop_count': 3, 'moved_existing_cups': 1,
            'source_hashes_preserved': SOURCES, 'protected_existing_actors': len(before)-1,
            'lighting_changes': [], 'furniture_or_crew_changes': [],
            'map_before_sha256': expected_map_sha256,
            'acceptance': 'Staged static tableware only; actual support/material/composition awaits native render'}
