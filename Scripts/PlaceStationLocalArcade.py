"""Measured arcade-corner plan and bounded owner-preview placement; never saves.

Run probe(ctx) with the import pass first. The lead reviews that receipt and
owns apply(ctx, import_report, expected_map_sha256) and subsequent room captures.
"""
import hashlib
import math
from pathlib import Path

from OutpostGeometryUtils import mesh_union
from StationRefinementSupport import transform_record


MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
PREFIX = 'Refine/LocalArcade/'
RELOCATE = ('Lounge_Arcade_SpaceHunt', 'Lounge_Arcade_RetroConsole', 'Refine/Social/Food/Drinks')
NEW_NAMES = ('AcornautNormal', 'AcornautDebrisField', 'AcornautArcade', 'AcornautHyperRun', 'GalaxyPinball')


def _require(condition, message):
    if not condition:
        raise RuntimeError(message)


def _world(u):
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    _require(world.get_path_name().split('.')[0] == MAP, 'Only the separate owner preview may receive arcade props')
    return world


def _one(actors, label):
    rows = [a for a in actors if a.get_actor_label() == label]
    _require(len(rows) == 1, 'Expected one reviewed actor: ' + label)
    return rows[0]


def _bounds(actor):
    c, e = mesh_union(actor)
    return [list((c-e).to_tuple()), list((c+e).to_tuple())]


def _intersects(a, b, margin=0):
    return all(a[0][i] < b[1][i]+margin and a[1][i] > b[0][i]-margin for i in range(3))


def _visible(actor):
    return not actor.get_editor_property('hidden') and not actor.is_temporarily_hidden_in_editor()


def _hit(result):
    fields = result.to_tuple() if result is not None else None
    if not fields or not fields[0]:
        return None
    return {'actor': fields[9].get_actor_label() if fields[9] else None,
            'point': list(fields[5].to_tuple()), 'normal': list(fields[7].to_tuple())}


def _material_values(material, u):
    edit = u.MaterialEditingLibrary
    if not isinstance(material, u.MaterialInstance):
        return {'path': material.get_path_name() if material else None}
    return {'path': material.get_path_name(),
            'scalars': {str(n): float(edit.get_material_instance_scalar_parameter_value(material, n))
                        for n in edit.get_scalar_parameter_names(material)},
            'vectors': {str(n): list(edit.get_material_instance_vector_parameter_value(material, n).to_tuple())
                        for n in edit.get_vector_parameter_names(material)},
            'textures': {str(n): (t.get_path_name() if t else None)
                         for n in edit.get_texture_parameter_names(material)
                         for t in [edit.get_material_instance_texture_parameter_value(material, n)]}}


def probe(ctx):
    """Read-only compact room, material and native fixture-orientation evidence."""
    import unreal as u
    _world(u)
    room = [[2800, -4550, -10], [5550, -2250, 450]]
    rows = []
    for actor in ctx.actors:
        if not _visible(actor):
            continue
        label = actor.get_actor_label()
        if not (label.startswith(('Refine/Social', 'Refine/OrbitPool', 'Lounge_', 'Engineering/'))):
            continue
        try:
            bounds = _bounds(actor)
        except RuntimeError:
            continue
        if not _intersects(room, bounds) or '/Return/' in label or '/Ball ' in label:
            continue
        rows.append({'label': label, 'bounds_cm': bounds, 'transform': transform_record(actor)})
    fixtures = []
    for index in (1, 2):
        actor = _one(ctx.actors, 'Refine/SocialAtmosphereFollowup/Aisle %d/Housing' % index)
        component = actor.get_component_by_class(u.StaticMeshComponent)
        transform = component.get_world_transform()
        origin = u.MathLibrary.transform_location(transform, u.Vector(0, 0, 0))
        axes = {axis: list((u.MathLibrary.transform_location(transform, u.Vector(*value))-origin).to_tuple())
                for axis, value in [('x', (1, 0, 0)), ('y', (0, 1, 0)), ('z', (0, 0, 1))]}
        fixtures.append({'label': actor.get_actor_label(), 'bounds_cm': _bounds(actor),
                         'mesh': component.static_mesh.get_path_name(), 'world_axes': axes,
                         'slots': [_material_values(m, u) for m in component.get_materials()]})
    glass = ctx.asset('/Game/CyberpunkRestaurant/Materials/MI_Light_Lamp_Glass')
    # This is a source-geometry orientation probe, not a lighting acceptance test.
    from RefineStationSocialSeatedCrew import _geometry
    component = _one(ctx.actors, 'Refine/SocialAtmosphereFollowup/Aisle 1/Housing').get_component_by_class(u.StaticMeshComponent)
    _, geometry = _geometry(component.static_mesh, False, u)
    normal_counts = {'up': 0, 'down': 0, 'side': 0, 'degenerate': 0}
    transform = component.get_world_transform()
    for face in geometry['triangles']:
        a, b, c = [u.MathLibrary.transform_location(transform, u.Vector(*geometry['vertices'][i])) for i in face]
        ab, ac = b-a, c-a
        normal = (ab.y*ac.z-ab.z*ac.y, ab.z*ac.x-ab.x*ac.z, ab.x*ac.y-ab.y*ac.x)
        length = math.sqrt(sum(v*v for v in normal))
        key = 'degenerate' if length < 1.e-8 else 'up' if normal[2]/length > .7 else 'down' if normal[2]/length < -.7 else 'side'
        normal_counts[key] += 1
    return {'actors': rows, 'center_fixtures': fixtures, 'fixture_world_triangle_normal_counts': normal_counts,
            'lamp_glass': _material_values(glass, u),
            'scope': 'Read-only native bounds, material parameters and geometry orientation; no scene changes'}


def _combined(parts):
    return [[min(p['bounds_cm'][0][i] for p in parts) for i in range(3)],
            [max(p['bounds_cm'][1][i] for p in parts) for i in range(3)]]


def _proposal(name, bounds, xy, yaw, parts=None, actor=None):
    """Place union bounds centre at XY; retain shared pivots for crane glass."""
    angle = math.radians(yaw)
    points = [(x*math.cos(angle)-y*math.sin(angle), x*math.sin(angle)+y*math.cos(angle), z)
              for x in (bounds[0][0], bounds[1][0]) for y in (bounds[0][1], bounds[1][1])
              for z in (bounds[0][2], bounds[1][2])]
    low = [min(p[i] for p in points) for i in range(3)]
    high = [max(p[i] for p in points) for i in range(3)]
    location = [xy[0]-(low[0]+high[0])*.5, xy[1]-(low[1]+high[1])*.5, -low[2]]
    world_bounds = [[low[i]+location[i] for i in range(3)], [high[i]+location[i] for i in range(3)]]
    return {'name': name, 'location': location, 'yaw': yaw, 'bounds_cm': world_bounds,
            'parts': parts or [], 'existing_actor': actor}


def _existing_proposal(actor, xy, yaw, u):
    # Rotation is relative to the native original actor frame, including existing scale.
    transform = actor.get_actor_transform()
    current_yaw = actor.get_actor_rotation().yaw
    _require(abs(actor.get_actor_rotation().pitch) < .01 and abs(actor.get_actor_rotation().roll) < .01,
             'Reviewed existing arcade cabinet is tilted')
    bounds = _bounds(actor)
    origin = actor.get_actor_location()
    relative = [[v[i]-origin.to_tuple()[i] for i in range(3)] for v in bounds]
    result = _proposal(actor.get_actor_label(), relative, xy, yaw-current_yaw, actor=actor.get_path_name())
    result['yaw'] = yaw
    return result


def plan(ctx, import_report, optional_props=None):
    """Deterministic L-shaped corner using imported/native extents; no actor writes."""
    import unreal as u
    _world(u)
    optional_props = optional_props or {}
    _require(set(optional_props) <= {'RiftSalvage', 'CreditExchange'}, 'Unknown optional arcade prop')
    _require(all(source != role for role, source in optional_props.items()),
             'The owner rejected the first crane/terminal prototypes; require explicit reviewed replacement names')
    selection = dict.fromkeys(NEW_NAMES)
    selection.update(optional_props)
    imported = {role: [m for m in import_report['meshes'] if m['name'] == (source or role)]
                for role, source in selection.items()}
    _require(all(imported.values()), 'A requested arcade prop is missing from the native import receipt')
    _require(not any(a.get_actor_label().startswith(PREFIX) for a in ctx.actors), 'Local arcade already placed')
    combined = {name: _combined(parts) for name, parts in imported.items()}
    # Native Import1 probe: refrigerator ends X4660.336; allow 19.664cm clear.
    rows, cursor = [], 4680.
    for name in NEW_NAMES[:4]:
        bounds = combined[name]
        width = bounds[1][0]-bounds[0][0]
        depth = bounds[1][1]-bounds[0][1]
        # Back edge at -4400, ahead of the existing arcade sign support posts.
        rows.append(_proposal(name, bounds, (cursor+width*.5, -4400+depth*.5), 0, imported[name]))
        cursor += width+28.
    _require(cursor-28 <= 5410, 'Four cabinets do not fit the reviewed south-wall bay at native scale')
    # East branch faces west, with space between cabinets rather than overlapping fronts.
    for name, y in [('GalaxyPinball', -3810), ('RiftSalvage', -3580)]:
        if name not in combined:
            continue
        bounds = combined[name]
        depth = bounds[1][1]-bounds[0][1]
        rows.append(_proposal(name, bounds, (5410-depth*.5, y), 90, imported[name]))
    if 'CreditExchange' in combined:
        rows.append(_proposal('CreditExchange', combined['CreditExchange'], (4635, -3630), 0,
                              imported['CreditExchange']))
    for label, xy in [(RELOCATE[0], (5360, -4130)), (RELOCATE[1], (5370, -3990))]:
        rows.append(_existing_proposal(_one(ctx.actors, label), xy, 90, u))
    drinks = _one(ctx.actors, RELOCATE[2])
    # South of the existing dining table, clear of the NE planter and north panel.
    rows.append(_existing_proposal(drinks, (5340, -2780), drinks.get_actor_rotation().yaw, u))
    protected_pool = [[4640, -3460, 0], [5030, -2820, 240]]
    for row in rows:
        bounds = row['bounds_cm']
        _require(bounds[0][0] > 4440 and bounds[1][0] < 5450 and bounds[0][1] > -4420 and bounds[1][1] < -2280,
                 'Arcade placement exceeds the reviewed corner: ' + row['name'])
        _require(not _intersects(bounds, protected_pool, 10), 'Arcade overlaps pool action area: ' + row['name'])
        for other in rows:
            if other is row:
                break
            _require(not _intersects(bounds, other['bounds_cm'], 6),
                     'Arcade props overlap: ' + row['name'] + ' / ' + other['name'])
    return {'placements': rows, 'reserved_pool_cm': protected_pool,
            'reserved_future_props': {'RiftSalvage': [[5285, -3645, 0], [5420, -3515, 225]],
                                      'CreditExchange': [[4575, -3680, 0], [4695, -3580, 210]]},
            'optional_replacement_names': optional_props,
            'preserved_center_aisle_x_cm': [4000, 4400],
            'native_front_axis': '+Y; south row yaw0, east branch yaw90',
            'moved_existing_labels': list(RELOCATE), 'scale_policy': 'Native exported human scale, no fit-by-distortion'}


def _floor(world, xy, ignored, u):
    hit = _hit(u.SystemLibrary.line_trace_single_by_profile(world, u.Vector(xy[0], xy[1], 18),
        u.Vector(xy[0], xy[1], -35), 'Pawn', False, ignored, u.DrawDebugTrace.NONE, True))
    _require(hit and abs(hit['point'][2]) <= 1.5 and hit['normal'][2] >= .7,
             'No solid level floor at arcade point: ' + repr(xy) + ' hit=' + repr(hit))
    return hit


def _validate(world, rows, actors_by_name, u):
    cls = u.load_class(None, '/Script/SpaceSurvival.SSWalker')
    capsule = u.get_default_object(cls).get_component_by_class(u.CapsuleComponent)
    radius, half = capsule.get_unscaled_capsule_radius(), capsule.get_unscaled_capsule_half_height()
    _require(radius > 0 and half > radius, 'Native walker capsule unavailable')
    floors, approaches, volumes = [], [], []
    for row in rows:
        lo, hi = row['bounds_cm']
        own = actors_by_name[row['name']]
        for x in (lo[0]+4, hi[0]-4):
            for y in (lo[1]+4, hi[1]-4):
                floors.append({'name': row['name'], 'xy': [x, y], 'hit': _floor(world, (x, y), own, u)})
        center = [(lo[i]+hi[i])*.5 for i in range(3)]
        # Test the cabinet volume against actual room collision, excluding only
        # its own opaque/glass parts. Shrink 2cm to avoid tangential floor contact.
        half_size = [max(.1, (hi[i]-lo[i])*.5-2) for i in range(3)]
        volume_hit = _hit(u.SystemLibrary.box_trace_single_by_profile(world,
            u.Vector(*center), u.Vector(center[0], center[1], center[2]+.1),
            u.Vector(*half_size), u.Rotator(0, 0, 0), 'Pawn', False, own, u.DrawDebugTrace.NONE, True))
        _require(volume_hit is None, 'Arcade volume intersects existing collision: ' + row['name'] + ' ' + repr(volume_hit))
        volumes.append({'name': row['name'], 'clear': True, 'bounds_cm': row['bounds_cm']})
        angle = math.radians(row['yaw'])
        front = (-math.sin(angle), math.cos(angle))
        reach = (hi[1]-lo[1])*.5 if abs(front[1]) > .7 else (hi[0]-lo[0])*.5
        xy = [center[i]+front[i]*(reach+radius+12) for i in range(2)]
        _floor(world, xy, [], u)
        start = u.Vector(xy[0], xy[1], half+3)
        obstruction = _hit(u.SystemLibrary.capsule_trace_single_by_profile(world, start, start+u.Vector(0, 0, .1),
            radius, half, 'Pawn', False, [], u.DrawDebugTrace.NONE, True))
        _require(obstruction is None, 'Arcade standing space blocked: ' + row['name'] + ' ' + repr(obstruction))
        approaches.append({'name': row['name'], 'standing_xy': xy, 'clear': True})
    # Connect the arcade's public front to the existing room circulation.
    routes = [((4200, -3750), (5080, -3750)), ((5080, -3750), (5080, -4080))]
    for start, end in routes:
        hit = _hit(u.SystemLibrary.capsule_trace_single_by_profile(world,
            u.Vector(*start, half+3), u.Vector(*end, half+3), radius, half, 'Pawn', False, [], u.DrawDebugTrace.NONE, True))
        _require(hit is None, 'Arcade approach route blocked: ' + repr(hit))
    return {'floor_samples': floors, 'standing_spaces': approaches, 'volumes': volumes, 'routes': routes,
            'capsule_radius_cm': radius, 'capsule_half_height_cm': half}


def apply(ctx, import_report, expected_map_sha256, optional_props=None):
    import unreal as u
    world = _world(u)
    root = Path(u.Paths.project_dir()).resolve()
    map_file = root / ('Content/' + MAP[6:] + '.umap')
    _require(len(expected_map_sha256) == 64 and hashlib.sha256(map_file.read_bytes()).hexdigest() == expected_map_sha256,
             'Owner preview changed since the lead approved this placement pass')
    report = plan(ctx, import_report, optional_props)
    before = {a.get_path_name(): transform_record(a) for a in ctx.actors}
    relocated = {_one(ctx.actors, label).get_path_name() for label in RELOCATE}
    placed = {}
    for row in report['placements']:
        if row['existing_actor']:
            actor = next(a for a in ctx.actors if a.get_path_name() == row['existing_actor'])
            ctx.move(actor, row['location'], (0, row['yaw'], 0))
            placed[row['name']] = [actor]
        else:
            placed[row['name']] = [ctx.raw(PREFIX + row['name'] + '/' + part['part'],
                part['mesh'], row['location'], (0, row['yaw'], 0), collision=part['collision'] != 'none')
                for part in row['parts']]
        actual = _combined([{'bounds_cm': _bounds(a)} for a in placed[row['name']]])
        _require(max(abs(actual[e][i]-row['bounds_cm'][e][i]) for e in range(2) for i in range(3)) < .1,
                 'Native placement differs from its measured plan: ' + row['name'])
    report['clearance'] = _validate(world, report['placements'], placed, u)
    changes = [a.get_actor_label() for a in ctx.actors if a.get_path_name() not in relocated
               and transform_record(a) != before[a.get_path_name()]]
    _require(not changes, 'Protected owner/room transforms changed: ' + repr(changes))
    _require(hashlib.sha256(map_file.read_bytes()).hexdigest() == expected_map_sha256, 'Placement helper unexpectedly saved the map')
    report.update({'dirty_assets': [], 'protected_actor_count': len(before)-len(relocated),
                   'protected_transform_changes': changes, 'map_before_sha256': expected_map_sha256,
                   'created_actors': {n: [a.get_path_name() for a in actors] for n, actors in placed.items()},
                   'saved': False})
    return report
