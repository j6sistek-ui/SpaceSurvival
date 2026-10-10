"""Bounded measured furniture replacement candidate; lead owns native execution.

Read-only probe first: actual central seat surfaces and owned metal trim geometry.
Never infer a sitting surface from a mesh's total height or triangle winding.
"""
import hashlib
import math
import json
import re
from pathlib import Path

from OutpostGeometryUtils import mesh_union
from RefineStationBarPresentation import _path, _one, _require
from RefineStationArcadePresentation import _graph
from RefineStationSocialSeatedCrew import _geometry
from StationRefinementSupport import transform_record

MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
CHAIR = '/Game/CyberPunkBarAssetSet01/StaticMeshes/SM_CyberChair01'
OLD = '/Game/CyberpunkRestaurant/Meshes/SM_Stool_01'
TRIMS = tuple('/Game/CyberpunkRestaurant/Meshes/SM_Metal_Trim_0'+str(i) for i in (1, 2, 3))
MATERIALS = tuple('/Game/CyberPunkBarAssetSet01/Materials/M_CyberChairMat0'+str(i) for i in (1, 2, 3))
PREFIX = 'Refine/BarFurniture/'
PROBE = 'StationBarFurnitureProbe1.json'


def _local_surface(data, x, y):
    heights = []
    for face in data['triangles']:
        a, b, c = (data['vertices'][i] for i in face)
        det = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(det) < 1.e-8:
            continue
        s = ((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/det
        r = ((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/det
        if min(s, r, 1.-s-r) >= -1.e-7:
            heights.append(s*a[2]+r*b[2]+(1.-s-r)*c[2])
    _require(heights, 'No actual native seat surface at '+str((x, y)))
    return max(heights)


def probe(ctx):
    """Native geometry/material read only; no spawning, edits, loads or saves."""
    import unreal as u
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    _require(world.get_path_name().split('.')[0] == MAP, 'Furniture probe requires loaded owner preview')
    map_file = root/('Content/'+MAP[6:]+'.umap')
    before = sha(map_file)
    sources, materials, meshes = {}, {}, []

    def protect(path):
        if path and path.startswith('/Game/'):
            sources[path] = sha(root/('Content/'+path[6:]+'.uasset'))

    def material(asset):
        path = _path(asset)
        if path in materials:
            return
        protect(path)
        row = _graph(asset, u)
        materials[path] = row
        for node in row.get('nodes', []):
            protect(node.get('texture'))
        for texture in row.get('textures', {}).values():
            protect(texture)
        if row.get('parent'):
            material(ctx.asset(row['parent']))

    for path in (CHAIR, OLD, *TRIMS):
        mesh = ctx.asset(path)
        _require(isinstance(mesh, u.StaticMesh), 'Expected owned furniture mesh: '+path)
        protect(path)
        bounds = mesh.get_bounds()
        _, geometry = _geometry(mesh, False, u)
        slots = mesh.get_editor_property('static_materials')
        for slot in slots:
            _require(slot.material_interface is not None, 'Owned furniture slot is empty')
            material(slot.material_interface)
        row = {'asset': path, 'origin_cm': list(bounds.origin.to_tuple()),
               'extent_cm': list(bounds.box_extent.to_tuple()),
               'slots': [{'index': i, 'name': str(s.material_slot_name), 'material': _path(s.material_interface)}
                         for i, s in enumerate(slots)],
               'geometry': geometry}
        if path in (CHAIR, OLD):
            points = []
            for x in (-12., 0., 12.):
                for y in (-12., 0., 12.):
                    try:
                        points.append({'xy': [x, y], 'top_z': _local_surface(geometry, x, y)})
                    except RuntimeError as error:
                        points.append({'xy': [x, y], 'error': str(error)})
            row['central_seat_grid'] = points
            # High geometry identifies the backrest side independently of an
            # assumed forward convention; the lead verifies the actual silhouette.
            threshold = bounds.origin.z+bounds.box_extent.z-25.
            high = [p for p in geometry['vertices'] if p[2] > threshold]
            row['upper_backrest_centroid'] = ([sum(p[i] for p in high)/len(high) for i in range(3)]
                                              if high else None)
        meshes.append(row)
    for path in MATERIALS:
        material(ctx.asset(path))
    actors = []
    for index in range(1, 5):
        actor = _one(ctx.actors, 'Refine/Social/Bar/Stool '+str(index))
        center, extent = mesh_union(actor)
        row = transform_record(actor)
        row['bounds_cm'] = [list((center-extent).to_tuple()), list((center+extent).to_tuple())]
        row['mesh'] = _path(actor.static_mesh_component.static_mesh)
        row['materials'] = [_path(m) for m in actor.static_mesh_component.get_materials()]
        old = next(m for m in meshes if m['asset'] == OLD)
        t = actor.static_mesh_component.get_world_transform()
        row['seat_grid_world'] = []
        for point in old['central_seat_grid']:
            _require('top_z' in point, 'Original stool central surface has a gap')
            p = u.MathLibrary.transform_location(t, u.Vector(*point['xy'], point['top_z']))
            row['seat_grid_world'].append(list(p.to_tuple()))
        actors.append(row)
    panels = []
    for actor in ctx.actors:
        if actor.get_actor_label().startswith('Refine/BarPresentation/Counter ') and actor.get_actor_label().endswith('/Satin face'):
            c, e = mesh_union(actor)
            panels.append({'actor': transform_record(actor), 'bounds_cm': [list((c-e).to_tuple()), list((c+e).to_tuple())]})
    _require(len(panels) == 6, 'Expected the six saved flat satin inserts')
    _require(sha(map_file) == before and all(sha(root/('Content/'+p[6:]+'.uasset')) == h for p, h in sources.items()),
             'Furniture probe changed a map or source')
    return {'scope': 'READ_ONLY_OWNED_BAR_FURNITURE_AND_TRIM', 'map_sha256': before,
            'meshes': meshes, 'materials': materials, 'stools': actors, 'front_inserts': panels,
            'source_sha256': sources, 'map_unchanged': True, 'sources_unchanged': True,
            'limits': 'Central seat triangles and upper-backrest centroid guide fitting; rendered orientation and room clearance remain separate'}


def apply(ctx, expected_map_sha256):
    """Replace only four empty seats, preserving native seat height and bounds centers.

    No material assets, counter changes, lighting edits, source writes or saves.
    Native room rendering remains necessary to accept the purchased silhouette.
    """
    import unreal as u
    from RefineStationLoungeCeiling import _snapshot
    from RefineStationSocialFinish import _aisle
    from PlaceStationLocalArcade import _floor, _hit
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    _require(re.fullmatch('[0-9a-f]{64}', expected_map_sha256), 'Require latest saved map identity')
    map_file = root/('Content/'+MAP[6:]+'.umap')
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    _require(world.get_path_name().split('.')[0] == MAP and sha(map_file) == expected_map_sha256,
             'Only stage furniture in the exact guarded owner preview')
    receipt_path = root/'.agent/local/StationRefinement'/PROBE
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    _require(receipt['success'] and receipt['preservation_pass'] and receipt['probe']['map_unchanged'],
             'Require successful read-only native chair inspection')
    data = receipt['probe']
    protected = data['source_sha256']
    _require(all(sha(root/('Content/'+p[6:]+'.uasset')) == h for p, h in protected.items()),
             'Inspected chair/trim/material sources changed')
    actors = list(ctx.eas.get_all_level_actors())
    before = {a.get_path_name(): _snapshot(a, u) for a in actors}
    old_meshes = {c.get_path_name(): _path(c.static_mesh) for a in actors
                  for c in a.get_components_by_class(u.StaticMeshComponent)}
    old_seats = [_one(actors, 'Refine/Social/Bar/Stool '+str(i)) for i in range(1, 5)]
    _require(all(_path(a.static_mesh_component.static_mesh) == OLD for a in old_seats),
             'Preserve chairs that have already been replaced')
    mesh = ctx.asset(CHAIR)
    bounds = mesh.get_bounds()
    measured = next(row for row in data['meshes'] if row['asset'] == CHAIR)
    _require(math.dist(bounds.origin.to_tuple(), measured['origin_cm']) < .001 and
             math.dist(bounds.box_extent.to_tuple(), measured['extent_cm']) < .001,
             'Chair bounds differ from the native probe')
    _, geometry = _geometry(mesh, False, u)
    native_seat = _local_surface(geometry, 0., 0.)
    bottom = bounds.origin.z-bounds.box_extent.z
    _require(abs(native_seat-59.397833596316936) < .005 and
             abs(bottom+33.2746696472168) < .005, 'Native central seat/support changed')
    source_materials = [s.material_interface for s in mesh.get_editor_property('static_materials')]
    _require(len(source_materials) == 2 and all(_path(m) == MATERIALS[0] for m in source_materials),
             'Chair default native material slots changed')
    before_routes = _aisle(world, u)
    plans = []
    # Native backrest is +X; yaw90 puts it toward the room (+Y), facing the bar (-Y).
    rotation = u.Rotator(pitch=0., yaw=90., roll=0.)
    for actor in old_seats:
        old = next(row for row in data['stools'] if row['label'] == actor.get_actor_label())
        current = transform_record(actor)
        _require(all(math.dist(current[key], old[key]) < .005 for key in ('location', 'rotation', 'scale')),
                 'Original bar seat moved after native inspection: '+actor.get_actor_label())
        center, extent = mesh_union(actor)
        floor = center.z-extent.z
        target = old['seat_grid_world'][4][2]
        scale = (target-floor)/(native_seat-bottom)
        _require(.94 < scale < 1.02 and abs(floor) < .05, 'Unexpected chair fit or bar floor')
        # Preserve horizontal rendered bounds center, not an asymmetric import pivot.
        location = u.Vector(center.x+scale*bounds.origin.y,
                            center.y-scale*bounds.origin.x, floor-scale*bottom)
        size = [bounds.box_extent.y*scale, bounds.box_extent.x*scale, bounds.box_extent.z*scale]
        z_center = floor+size[2]
        floors = [_floor(world, (center.x+sx*size[0]*.85, center.y+sy*size[1]*.85), old_seats, u)
                  for sx in (-1., 1.) for sy in (-1., 1.)]
        collision = _hit(u.SystemLibrary.box_trace_single_by_profile(world,
            u.Vector(center.x, center.y, z_center), u.Vector(center.x, center.y, z_center+.1),
            u.Vector(size[0]-.5, size[1]-.5, size[2]-.5), u.Rotator(pitch=0., yaw=0., roll=0.),
            'Pawn', False, old_seats, u.DrawDebugTrace.NONE, True))
        _require(collision is None, 'Wider sci-fi chair overlaps existing room collision: '+repr(collision))
        # Standing region behind the empty chair connects to the existing bar approach.
        _floor(world, (center.x, -3795.), old_seats, u)
        plans.append({'actor': actor, 'location': location, 'scale': scale,
                      'center_xy_cm': [center.x, center.y], 'seat_height_cm': target,
                      'floor_z_cm': floor, 'floor_hits': floors, 'half_size_cm': size})
    changed, allowed = [], {a.get_path_name() for a in old_seats}
    for plan in plans:
        actor = plan['actor']
        component = actor.static_mesh_component
        _require(component.set_static_mesh(mesh), 'Could not set inspected sci-fi chair')
        for index, material in enumerate(source_materials):
            component.set_material(index, material)
            _require(component.get_material(index) == material, 'Chair source finish readback differs')
        actor.set_actor_scale3d(u.Vector(plan['scale'], plan['scale'], plan['scale']))
        ctx.move(actor, plan['location'], rotation)
        center, extent = mesh_union(actor)
        seat = u.MathLibrary.transform_location(component.get_world_transform(), u.Vector(0., 0., native_seat))
        _require(math.dist((center.x, center.y), plan['center_xy_cm']) < .03 and
                 abs(center.z-extent.z-plan['floor_z_cm']) < .03 and
                 abs(seat.z-plan['seat_height_cm']) < .03, 'Chair seat/center/grounding readback differs')
        changed.append({'before': next(row for row in data['stools'] if row['label'] == actor.get_actor_label()),
                        'after': transform_record(actor), 'material': MATERIALS[0],
                        'native_seat_z_cm': native_seat, 'actual_seat_z_cm': seat.z,
                        'floor_hits': plan['floor_hits'],
                        'bounds_cm': [list((center-extent).to_tuple()), list((center+extent).to_tuple())]})
    after_routes = _aisle(world, u)
    capsule = _hit(u.SystemLibrary.capsule_trace_single_by_profile(world,
        u.Vector(3780., -3795., 78.), u.Vector(4630., -3795., 78.), 34., 75.,
        'Pawn', False, [], u.DrawDebugTrace.NONE, True))
    _require(capsule is None, 'Replacement chairs block actual bar-frontage capsule route: '+repr(capsule))
    for actor in actors:
        path = actor.get_path_name()
        now = _snapshot(actor, u)
        if path in allowed:
            _require(now['hidden'] == before[path]['hidden'] and now['lights'] == before[path]['lights'],
                     'Chair visibility/light state changed')
        else:
            _require(now == before[path], 'Protected room actor changed: '+actor.get_actor_label())
            for component in actor.get_components_by_class(u.StaticMeshComponent):
                _require(_path(component.static_mesh) == old_meshes[component.get_path_name()],
                         'Protected existing mesh changed')
    _require(sha(map_file) == expected_map_sha256 and
             all(sha(root/('Content/'+p[6:]+'.uasset')) == h for p, h in protected.items()),
             'Furniture helper saved a map or changed an original asset')
    return {'dirty_assets': [], 'source_sha256': protected, 'probe_sha256': sha(receipt_path),
            'replacements': changed, 'protected_existing_actor_count': len(before),
            'changed_actor_allowlist': sorted(allowed), 'uniform_scale': plans[0]['scale'],
            'before_routes': before_routes, 'after_routes': after_routes, 'frontage_capsule_clear': True,
            'counter_worktop_ceiling_lights_preserved': True,
            'limits': 'Four empty native sci-fi chairs staged only; actual room render and owner review still required'}
