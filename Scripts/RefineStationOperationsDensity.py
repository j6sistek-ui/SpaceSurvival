"""Measured ceiling rhythm, two storage alcoves and original image-led TVs.

probe() reads actual kit geometry and floor/roof support without spawning.
apply() creates a bounded addition only; the lead wrapper owns all saves.
"""
import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / '.agent/local/StationRefinement'
MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
BASE = '/Game/OutpostSandbox/StationRefinement/OperationsDensity20261007'
PREFIX = 'Refine/OperationsDensity/'
PLAN = LOCAL / 'OperationsDensityPlan1.json'
PLAN_SHA = '78d1d33e3426bd7d6db2cf63bf7fc3601b390b3046d02df1ad514faa0c1f9ad3'
BASELINE = LOCAL / 'StationOperationsBaseline2/manifest.json'
BASELINE_SHA = '02c279c096587a8c684f3d55e6285699cb60834198470dfc3b609ab97323d884'
TV_PROBE = LOCAL / 'BarDisplays1/NativeDisplayProbe1.json'
TV_PROBE_SHA = 'b7b315605bcdb9892d119f09b838e532da4dd77fcb7e7cc313e97a8346262bda'
ART = LOCAL / 'OperationsAds1/final_manifest.json'
ART_SHA = '8a5f4ecf04d7b83209125109447d3eabf6ab4309237aab14cc7137479a65dda3'
P4 = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/'
CEILING = P4 + 'Meshes/SM_CeilingPanel400X200_V1'
CABINET = P4 + 'Meshes/SM_WallPanel400X200_V1_SmartStorageUnit'
POST = '/Game/P1toP5_Bundle/P5_FruitSeller/Meshes/SM_Building_Structure200x10_V1'
DARK = P4 + 'Materials/Instances/Opaque/MI_Metal12_PaintAnodizedAluminium_Dark'
TV = '/Game/CyberpunkRestaurant/Meshes/SM_TV_Screen_02'
SCREEN_CENTER = (15.4304671288, 56.0843825340, -10.7984161377)
SCREEN_RIGHT = (.67750667714, -.73551149966, .00274523214)
SCREEN_UP = (-.00412942915, -.00007138854, .99999147132)
SCREEN_SIZE = (86.2190632285, 48.3440479405)
TV_SCALE = 2.
STORAGE_SIGNS = (-1, 1)


def _require(condition, message):
    if not condition:
        raise RuntimeError(message)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _asset_file(package):
    return ROOT / ('Content/' + package.split('.')[0][6:] + '.uasset')


def _inputs(ctx, u):
    _require(_sha(PLAN) == PLAN_SHA and _sha(BASELINE) == BASELINE_SHA and _sha(TV_PROBE) == TV_PROBE_SHA and
             _sha(ART) == ART_SHA, 'Frozen native geometry or approved artwork changed')
    proposal = json.loads(PLAN.read_text(encoding='utf-8'))
    _require(len(proposal['parts']) == 14 and proposal['new_lights'] == 0,
             'Require exact twelve canopy panels and two storage units')
    source = dict(proposal['source_sha256'])
    tv_probe = json.loads(TV_PROBE.read_text(encoding='utf-8'))
    _require(tv_probe['success'], 'Require successful true TV surface probe')
    source.update(tv_probe['source_sha256'])
    source[POST] = _sha(_asset_file(POST))
    source[DARK] = _sha(_asset_file(DARK))
    for package, digest in source.items():
        _require(_sha(_asset_file(package)) == digest, 'Owned source changed: ' + package)
    native = json.loads(BASELINE.read_text(encoding='utf-8'))['operations']['actors']
    measured = {}
    for row in native:
        for component in row['components']:
            package = (component.get('mesh') or '').split('.')[0]
            if package in (CEILING, CABINET) and package not in measured:
                measured[package] = {'origin_cm': component['native_origin_cm'],
                                     'extent_cm': component['native_extent_cm']}
    tv_row = next(row for row in tv_probe['meshes'] if row['asset'] == TV)
    measured[TV] = tv_row
    for package, row in measured.items():
        bounds = ctx.asset(package).get_bounds()
        _require(math.dist(bounds.origin.to_tuple(), row['origin_cm']) < .001 and
                 math.dist(bounds.box_extent.to_tuple(), row['extent_cm']) < .001,
                 'Measured source bounds differ: ' + package)
    _require(len(tv_row['slots']) == 8 and tv_row['slots'][5]['name'] == 'Screen',
             'TV material aperture changed')
    return proposal, source, native


def _clip(polygon, axis, boundary, keep_greater):
    """Clip a 3D polygon against an XY half-plane, interpolating actual Z."""
    out = []
    if not polygon:
        return out
    previous = polygon[-1]
    inside_previous = (previous[axis] >= boundary if keep_greater else previous[axis] <= boundary)
    for current in polygon:
        inside = (current[axis] >= boundary if keep_greater else current[axis] <= boundary)
        if inside != inside_previous:
            ratio = (boundary - previous[axis]) / (current[axis] - previous[axis])
            out.append(tuple(previous[i] + (current[i] - previous[i]) * ratio for i in range(3)))
        if inside:
            out.append(tuple(current))
        previous, inside_previous = current, inside
    return out


def _roof_contacts(ctx, actors, native, u):
    """Find actual lowest roof triangles within each narrow shared-rail footprint."""
    from RefineStationSocialSeatedCrew import _geometry
    from RefineStationWorkroomComposition import _guard_pose
    cache, surfaces = {}, []
    expected = {row['label']: row for row in native
                if row['label'].startswith('QuietCeiling/Operations/Panel ')}
    selected = [actor for actor in actors if actor.get_actor_label() in expected]
    _require(len(selected) == len(expected) == 28, 'Complete native quiet roof required')
    for actor in selected:
        _guard_pose(actor, expected[actor.get_actor_label()]['transform'])
        component = actor.get_component_by_class(u.StaticMeshComponent)
        _require(component and component.static_mesh, 'Roof has no measured native component')
        key = component.static_mesh.get_path_name()
        if key not in cache:
            _, cache[key] = _geometry(component.static_mesh, False, u)
        data = cache[key]
        transform = component.get_world_transform()
        vertices = [transform.transform_location(u.Vector(*point)).to_tuple() for point in data['vertices']]
        surfaces.append((actor, component, vertices, data['triangles']))
    rows = []
    for y in (-500., 0., 500.):
        candidates = []
        for actor, component, vertices, triangles in surfaces:
            for index, face in enumerate(triangles):
                polygon = [vertices[i] for i in face]
                for axis, limit, greater in ((0, 7000., True), (0, 8600., False),
                                               (1, y - 5., True), (1, y + 5., False)):
                    polygon = _clip(polygon, axis, limit, greater)
                    if not polygon:
                        break
                if polygon:
                    point = min(polygon, key=lambda value: value[2])
                    candidates.append((point[2], point, actor, component, index))
        _require(candidates, 'No actual roof triangle supports canopy rail')
        height, point, actor, component, index = min(candidates, key=lambda row: row[0])
        _require(385. < height < 425., 'Roof support outside measured quiet-ceiling band')
        rows.append({'y_cm': y, 'underside_z_cm': height, 'contact_point_cm': list(point),
                     'actor': actor.get_path_name(), 'label': actor.get_actor_label(),
                     'component': component.get_name(), 'triangle': index,
                     'rail_length_cm': 1600., 'rail_depth_cm': 10., 'rail_height_cm': height - 385.})
    return rows


def _cabinet_top(data, part, xy):
    """Highest source triangle at a proposed post foot, from exact yaw/scale."""
    angle = math.radians(part['rotation_pyr'][1])
    c, s = math.cos(angle), math.sin(angle)
    local = []
    dx, dy = xy[0] - part['location'][0], xy[1] - part['location'][1]
    local.extend(((c * dx + s * dy) / part['scale'][0],
                  (-s * dx + c * dy) / part['scale'][1]))
    heights = []
    for face in data['triangles']:
        a, b, z = (data['vertices'][i] for i in face)
        determinant = (b[1] - z[1]) * (a[0] - z[0]) + (z[0] - b[0]) * (a[1] - z[1])
        if abs(determinant) < 1.e-8:
            continue
        first = ((b[1] - z[1]) * (local[0] - z[0]) +
                 (z[0] - b[0]) * (local[1] - z[1])) / determinant
        second = ((z[1] - a[1]) * (local[0] - z[0]) +
                  (a[0] - z[0]) * (local[1] - z[1])) / determinant
        if min(first, second, 1 - first - second) >= -1.e-7:
            heights.append(part['location'][2] + part['scale'][2] *
                           (first * a[2] + second * b[2] + (1 - first - second) * z[2]))
    _require(heights, 'No actual native cabinet support at post foot')
    return max(heights)


def probe(ctx):
    """No spawning/import/material change or saving; lead records preservation."""
    import unreal as u
    from RefineStationOperationsComposition import _clearance
    from RefineStationOperationsDisplays import _state
    from RefineStationSocialSeatedCrew import _geometry
    from PlaceStationLocalArcade import _floor
    proposal, source, native = _inputs(ctx, u)
    actors = list(ctx.eas.get_all_level_actors())
    before = {actor.get_path_name(): _state(actor, u) for actor in actors}
    _require(not any(actor.get_actor_label().startswith(PREFIX) for actor in actors),
             'Density already exists; preserve previous pass')
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    _, geometry = _geometry(ctx.asset(CABINET), False, u)
    storage = []
    for part in proposal['parts'][-2:]:
        sign = 1 if part['location'][1] > 0 else -1
        lo, hi = part['bounds']['minimum'], part['bounds']['maximum']
        points = [(7050., sign * 1204.)] + [(x, y) for x in (lo[0] + 5., hi[0] - 5.)
                                          for y in (lo[1] + 5., hi[1] - 5.)]
        floors = [_floor(world, xy, [], u) for xy in points]
        foot = (7050., sign * 1220.)
        tops = [_cabinet_top(geometry, part, (foot[0] + dx, foot[1] + dy))
                for dx, dy in ((0., 0.), (-21., -9.), (-21., 9.), (21., -9.), (21., 9.))]
        _require(max(tops) - min(tops) < .08 and abs(max(tops) - 100.) < .08,
                 'TV post requires a genuinely flat cabinet top')
        storage.append({'part': part['name'], 'sign': sign, 'floor_samples': floors,
                        'post_xy_cm': list(foot), 'post_foot_size_cm': [44., 20.],
                        'post_foot_surface_z_cm': tops, 'supported_post_base_z_cm': max(tops),
                        'tv_mount_plate': {'native_plane_y_cm': 0., 'native_x_range_cm': [-.433979, 17.894768],
                                           'native_z_range_cm': [-.000003, 19.318535]},
                        'tv_screen_yaw_degrees': 0. if sign < 0 else 180.,
                        'tv_screen_center_z_cm': 225., 'max_tv_top_cm': 310.})
    roofs = _roof_contacts(ctx, actors, native, u)
    post = ctx.asset(POST).get_bounds()
    _require(math.dist(post.origin.to_tuple(), (0., 0., 100.)) < .01 and
             math.dist(post.box_extent.to_tuple(), (5., 5., 100.)) < .01,
             'Native support profile is not measured 10x10x200')
    _require(all(_state(actor, u) == before[actor.get_path_name()] for actor in actors),
             'Read-only support probe changed actor state')
    return {'source_sha256': source, 'plan_sha256': _sha(PLAN), 'art_manifest_sha256': ART_SHA,
            'roof_supports': roofs, 'storage_supports': storage, 'routes': _clearance(world, u),
            'existing_actors_preserved': len(actors), 'actor_count_proposal': 21,
            'scope': '12 native canopies +3 shared roof rails +2 cabinets +2 cabinet TV supports +2 original TVs',
            'native_tv_aperture_probe_sha256': TV_PROBE_SHA,
            'limits': 'Measured geometry and static traces only; actual saved pixels and walking remain unverified.'}
