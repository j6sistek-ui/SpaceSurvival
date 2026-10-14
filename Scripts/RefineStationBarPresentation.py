"""Bounded owned-bar inventory; lead alone authors/saves/renders the preview.

The initial probe is read-only. Counter footprint/worktop and approved ceiling
lighting are protected design constraints, not candidates for this inventory.
"""
import hashlib
import json
import math
import re
from pathlib import Path

from OutpostGeometryUtils import mesh_union
from RefineStationArcadePresentation import _graph
from RefineStationSocialSeatedCrew import _geometry
from RefineStationSocialFinish import _surface
from StationRefinementSupport import transform_record

MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
BAR = '/Game/CyberPunkBarAssetSet01/'
FOOD = '/Game/CyberpunkRestaurant/'
MEGA = '/Game/CyberPunkMegapack/'
MESHES = tuple(BAR+'StaticMeshes/'+n for n in
               ('SM_Bardesk01', 'SM_Bardesk02', 'SM_Bardesk03', 'SM_Bardesk04', 'SM_CyberChair01')) + (
    FOOD+'Meshes/SM_Bar_01', FOOD+'Meshes/SM_BarTable_01', FOOD+'Meshes/SM_Stool_01',
    MEGA+'Meshes/SM_RestaurantBarTable', MEGA+'Meshes/SM_RestaurantSFChairA01',
    MEGA+'Meshes/SM_RestaurantSFChairB01', MEGA+'Meshes/SM_RestaurantSFChairC01')
METALS = tuple(FOOD+'Materials/'+n for n in
               ('MI_Metal_01', 'MI_Metal_03', 'MI_Metal_04', 'MI_Painted_Metal_01', 'MI_Painted_Metal_02'))
PRIVATE = '/Game/OutpostSandbox/StationRefinement/BarPresentation20261006'
PREFIX = 'Refine/BarPresentation/'
PROBE_SHA = 'e0dd3ac45a7dbcc997b04455bf8d59f9d7002db2162029083fd550c32d528e31'
GRAPHITE = '/Game/OutpostSandbox/Materials/M_OutpostGraphite'
TEXT = '/Game/OutpostSandbox/Materials/M_OutpostReadableTextOneSided'


def _path(asset):
    return asset.get_path_name().split('.')[0] if asset else None


def _faces(mesh, u):
    """Native upward surface bands and material IDs, no temporary scene actors."""
    dynamic, data = _geometry(mesh, False, u)
    bands, slots = {}, {}
    for index, face in enumerate(data['triangles']):
        slot, valid = u.GeometryScript_Materials.get_triangle_material_id(dynamic, index)
        if not valid:
            raise RuntimeError('Native bar triangle material ID unavailable')
        slots[str(slot)] = slots.get(str(slot), 0)+1
        a, b, c = [data['vertices'][i] for i in face]
        x, y = [b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)]
        cross = (x[1]*y[2]-x[2]*y[1], x[2]*y[0]-x[0]*y[2], x[0]*y[1]-x[1]*y[0])
        length = sum(v*v for v in cross)**.5
        if length < 1.e-8 or cross[2]/length < .7:
            continue
        z = sum(p[2] for p in (a, b, c))/3.
        key = '%d:%d' % (slot, round(z/5.)*5)
        row = bands.setdefault(key, {'slot': slot, 'z_band_cm': round(z/5.)*5,
                                    'area_cm2': 0., 'min': [1.e9]*3, 'max': [-1.e9]*3})
        row['area_cm2'] += length*.5
        for point in (a, b, c):
            for axis in range(3):
                row['min'][axis] = min(row['min'][axis], point[axis])
                row['max'][axis] = max(row['max'][axis], point[axis])
    return {'triangle_material_counts': slots,
            'upward_surface_bands': sorted(bands.values(), key=lambda row: row['area_cm2'], reverse=True)[:16]}


def probe(ctx):
    """Read exact local alternatives/current slots without edits, loads or saves."""
    import unreal as u
    root = Path(u.Paths.project_dir()).resolve()
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name().split('.')[0] != MAP:
        raise RuntimeError('Bar inventory requires the already-loaded owner preview')
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    map_file = root / ('Content/'+MAP[6:]+'.umap')
    before = sha(map_file)
    source_hashes, materials, meshes = {}, {}, []

    def record(asset):
        path = _path(asset)
        if path and path.startswith('/Game/'):
            source_hashes[path] = sha(root / ('Content/'+path[6:]+'.uasset'))

    def material(asset):
        if asset and _path(asset) not in materials:
            record(asset)
            row = _graph(asset, u)
            materials[_path(asset)] = row
            parent = row.get('parent')
            if parent:
                material(ctx.asset(parent))

    for path in MESHES:
        mesh = ctx.asset(path)
        if not isinstance(mesh, u.StaticMesh):
            raise RuntimeError('Expected an owned static mesh: '+path)
        record(mesh)
        bounds = mesh.get_bounds()
        slots = mesh.get_editor_property('static_materials')
        row = {'asset': path, 'origin_cm': list(bounds.origin.to_tuple()),
               'extent_cm': list(bounds.box_extent.to_tuple()),
               'dimensions_cm': [2*v for v in bounds.box_extent.to_tuple()],
               'slots': [{'index': i, 'name': str(s.material_slot_name), 'material': _path(s.material_interface)}
                         for i, s in enumerate(slots)]}
        for slot in slots:
            material(slot.material_interface)
        if path.endswith(('SM_Bardesk01', 'SM_CyberChair01', 'SM_Stool_01')):
            row.update(_faces(mesh, u))
        meshes.append(row)
    for path in METALS:
        material(ctx.asset(path))
    actors = []
    for actor in ctx.actors:
        label = actor.get_actor_label()
        if not label.startswith(('Refine/Social/Bar/', 'Refine/SocialFinish/Bar/',
                                 'Refine/SocialFollowup/Bar/', 'Refine/SocialDetail/Bar/')):
            continue
        row = transform_record(actor)
        row['class'] = actor.get_class().get_name()
        components = actor.get_components_by_class(u.StaticMeshComponent)
        if components:
            c, e = mesh_union(actor)
            row['bounds_cm'] = [list((c-e).to_tuple()), list((c+e).to_tuple())]
            row['components'] = []
            for component in components:
                record(component.static_mesh)
                row['components'].append({'component': component.get_path_name(), 'mesh': _path(component.static_mesh),
                    'slots': [_path(m) for m in component.get_materials()]})
                for m in component.get_materials():
                    material(m)
        actors.append(row)
    work_surfaces = []
    for side, xs in (('left', (3850., 3920., 4020., 4120.)), ('right', (4250., 4340., 4430., 4520.))):
        actor = next(a for a in ctx.actors if a.get_actor_label() == 'Refine/Social/Bar/Counter '+side)
        _, geometry = _geometry(actor.static_mesh_component.static_mesh, False, u)
        points = []
        for x in xs:
            for y in (-4085., -4070., -4055.):
                try:
                    points.append({'xy': [x, y], 'top_z': _surface(actor, geometry, x, y, u)})
                except RuntimeError as error:
                    points.append({'xy': [x, y], 'error': str(error)})
        work_surfaces.append({'counter': actor.get_actor_label(), 'points': points})
    if sha(map_file) != before or any(sha(root / ('Content/'+path[6:]+'.uasset')) != digest
                                    for path, digest in source_hashes.items()):
        raise RuntimeError('Read-only bar probe detected a source/map change')
    return {'scope': 'READ_ONLY_OWNED_BAR_NATIVE_INVENTORY', 'map_sha256': before,
            'meshes': meshes, 'materials': materials, 'actors': actors, 'work_surfaces': work_surfaces,
            'source_sha256': source_hashes,
            'map_unchanged': True, 'sources_unchanged': True,
            'limits': 'Bounds, material slots and upward face bands; not a visual replacement approval'}


def _require(condition, message):
    if not condition:
        raise RuntimeError(message)


def _one(actors, label):
    rows = [a for a in actors if a.get_actor_label() == label]
    _require(len(rows) == 1, 'Expected exactly one reviewed bar actor: '+label)
    return rows[0]


def _new_material(name, u, dirty, source=None):
    path = PRIVATE+'/'+name
    _require(not u.EditorAssetLibrary.does_asset_exist(path), 'Preserve existing bar material: '+path)
    material = (u.EditorAssetLibrary.duplicate_asset(source, path) if source else
                u.AssetToolsHelpers.get_asset_tools().create_asset(name, PRIVATE, u.Material, u.MaterialFactoryNew()))
    _require(material, 'Could not create private bar material: '+path)
    dirty.append(material.get_path_name())
    return material


def _constant(material, value, prop, u):
    edit = u.MaterialEditingLibrary
    vector = isinstance(value, tuple)
    node = edit.create_material_expression(material,
        u.MaterialExpressionConstant3Vector if vector else u.MaterialExpressionConstant)
    _require(node, 'Could not create private finish expression')
    node.set_editor_property('constant' if vector else 'r', u.LinearColor(*value) if vector else value)
    _require(edit.connect_material_property(node, '', prop), 'Could not connect private bar finish')
    _require(edit.get_material_property_input_node(material, prop) == node, 'Bar finish graph readback differs')


def _finishes(ctx, u, dirty):
    edit = u.MaterialEditingLibrary
    source = BAR+'Materials/M_BarDeskMat01'
    original = ctx.asset(source)
    normal = edit.get_material_property_input_node(original, u.MaterialProperty.MP_NORMAL)
    ao = edit.get_material_property_input_node(original, u.MaterialProperty.MP_AMBIENT_OCCLUSION)
    _require(normal is not None and ao is not None, 'Reviewed counter normal/AO inputs missing')
    material = _new_material('M_BarGraphiteHull', u, dirty, source)
    _constant(material, (.038, .062, .078, 1.), u.MaterialProperty.MP_BASE_COLOR, u)
    _constant(material, .72, u.MaterialProperty.MP_METALLIC, u)
    _constant(material, .32, u.MaterialProperty.MP_ROUGHNESS, u)
    params = [n for n in edit.get_material_expressions(material)
              if isinstance(n, u.MaterialExpressionScalarParameter) and str(n.get_editor_property('parameter_name')) == 'Param']
    _require(len(params) == 1, 'Counter native emission parameter changed')
    params[0].set_editor_property('default_value', 2.5)
    _require(abs(float(params[0].get_editor_property('default_value'))-2.5) < .0001,
             'Private counter emission value did not persist in memory')
    _require(edit.get_material_property_input_node(material, u.MaterialProperty.MP_NORMAL).get_name() == normal.get_name()
             and edit.get_material_property_input_node(material, u.MaterialProperty.MP_AMBIENT_OCCLUSION).get_name() == ao.get_name(),
             'Private counter lost native normal/AO detail')
    _require(not edit.recompile_material(material), 'Private counter material compilation failed')

    metal = _new_material('M_BarSatinMetal', u, dirty)
    lens = _new_material('M_BarCoolDiffuser', u, dirty)
    for finish, color, metallic, roughness, emission in (
            (metal, (.28, .34, .38, 1.), .76, .31, (0., 0., 0., 1.)),
            (lens, (.52, .76, .80, 1.), .05, .40, (1.1, 3.0, 3.6, 1.))):
        for value, prop in ((color, u.MaterialProperty.MP_BASE_COLOR),
                            (metallic, u.MaterialProperty.MP_METALLIC),
                            (roughness, u.MaterialProperty.MP_ROUGHNESS),
                            (emission, u.MaterialProperty.MP_EMISSIVE_COLOR)):
            _constant(finish, value, prop, u)
        _require(not edit.recompile_material(finish), 'Private metal/diffuser compilation failed')

    stool = _new_material('MI_StoolsClean', u, dirty, FOOD+'Materials/MI_Stool_01')
    scalars = {'DeSaturation': 1., 'Dirt Opcaity': .06, 'Contrast': 1.1,
               'Normal Intensity': .45, 'Roughness Intensity': .72}
    _require(set(scalars) <= set(map(str, edit.get_scalar_parameter_names(stool))), 'Reviewed stool parameters changed')
    _require('Tint' in map(str, edit.get_vector_parameter_names(stool)), 'Reviewed stool Tint is missing')
    for parameter, value in scalars.items():
        edit.set_material_instance_scalar_parameter_value(stool, parameter, value)
    tint = (.65, .77, .82, 1.)
    edit.set_material_instance_vector_parameter_value(stool, 'Tint', u.LinearColor(*tint))
    edit.update_material_instance(stool)
    # UE5.8 setters can return false after applying the value; inspect the actual value.
    _require(all(abs(edit.get_material_instance_scalar_parameter_value(stool, n)-v) < .0001
                 for n, v in scalars.items()), 'Clean stool scalar readback differs')
    _require(max(abs(a-b) for a, b in zip(tint,
        edit.get_material_instance_vector_parameter_value(stool, 'Tint').to_tuple())) < .0001,
        'Clean stool tint readback differs')
    return material, metal, lens, stool


def _top_faces(actor, geometry, xy, u):
    """Record the highest supporting triangle and winding, not a guessed band."""
    t = actor.static_mesh_component.get_world_transform()
    p = u.MathLibrary.inverse_transform_location(t, u.Vector(*xy, 0.))
    rows = []
    for face in geometry['triangles']:
        a, b, c = (geometry['vertices'][i] for i in face)
        det = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(det) < 1.e-8:
            continue
        s = ((b[1]-c[1])*(p.x-c[0])+(c[0]-b[0])*(p.y-c[1]))/det
        r = ((c[1]-a[1])*(p.x-c[0])+(a[0]-c[0])*(p.y-c[1]))/det
        if min(s, r, 1.-s-r) < -1.e-7:
            continue
        x, y = [b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)]
        n = (x[1]*y[2]-x[2]*y[1], x[2]*y[0]-x[0]*y[2], x[0]*y[1]-x[1]*y[0])
        length = math.sqrt(sum(v*v for v in n))
        z = u.MathLibrary.transform_location(t, u.Vector(p.x, p.y, s*a[2]+r*b[2]+(1.-s-r)*c[2])).z
        rows.append({'top_z': z, 'local_normal_z': n[2]/length})
    _require(rows, 'No actual counter triangle under workpoint')
    return max(rows, key=lambda row: row['top_z'])


def apply(ctx, expected_map_sha256):
    """Stage a measured furniture finish only; the lead owns explicit save/render."""
    import unreal as u
    from RefineStationLoungeCeiling import _snapshot
    from RefineStationSocialFinish import _aisle
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    _require(re.fullmatch('[0-9a-f]{64}', expected_map_sha256), 'Require the exact latest preview SHA')
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    map_file = root/('Content/'+MAP[6:]+'.umap')
    _require(world.get_path_name().split('.')[0] == MAP and sha(map_file) == expected_map_sha256,
             'Bar presentation targets only the guarded owner preview')
    receipt_file = root/'.agent/local/StationRefinement/StationBarNativeProbe2.json'
    _require(sha(receipt_file) == PROBE_SHA, 'Expected the frozen exact-surface bar probe')
    receipt = json.loads(receipt_file.read_text())
    _require(receipt['success'] and receipt['probe']['map_unchanged'] and receipt['probe']['sources_unchanged'],
             'Native bar probe did not succeed')
    measured = receipt['probe']
    actors = list(ctx.eas.get_all_level_actors())
    _require(not any(a.get_actor_label().startswith(PREFIX) for a in actors), 'Preserve existing bar presentation')
    before = {a.get_path_name(): _snapshot(a, u) for a in actors}
    source_hashes = dict(measured['source_sha256'])
    for path, row in measured['materials'].items():
        for node in row.get('nodes', []):
            texture = node.get('texture')
            if texture and texture.startswith('/Game/'):
                source_hashes.setdefault(texture, sha(root/('Content/'+texture[6:]+'.uasset')))
    for path in (GRAPHITE, TEXT):
        source_hashes[path] = sha(root/('Content/'+path[6:]+'.uasset'))
    _require(all(sha(root/('Content/'+p[6:]+'.uasset')) == digest for p, digest in source_hashes.items()),
             'A measured source asset changed since the bar probe')
    native_actors = {row['label']: row for row in measured['actors']}
    for label, row in native_actors.items():
        actor = _one(actors, label)
        current = transform_record(actor)
        _require(all(math.dist(current[key], row[key]) < .001 for key in ('location', 'rotation', 'scale')),
                 'A reviewed bar actor moved: '+label)
    counters = [_one(actors, 'Refine/Social/Bar/Counter '+side) for side in ('left', 'right')]
    _, geometry = _geometry(counters[0].static_mesh_component.static_mesh, False, u)
    surface_rows = []
    for group, actor in zip(measured['work_surfaces'], counters):
        for point in group['points']:
            _require('top_z' in point, 'The exact bar probe contains an unsupported point')
            actual = _surface(actor, geometry, *point['xy'], u)
            _require(abs(actual-point['top_z']) < .03, 'Actual counter surface differs from the exact probe')
            surface_rows.append({'counter': actor.get_actor_label(), 'xy': point['xy'],
                                 **_top_faces(actor, geometry, point['xy'], u)})
    _require(len(surface_rows) == 24, 'Expected all24 native work-surface samples')
    worktop = max(row['top_z'] for row in surface_rows)
    _require(abs(worktop-107.554184) < .03, 'Broad bar worktop is not the measured standing height')
    before_routes = _aisle(world, u)

    # Validate flat support for each complete prop footprint BEFORE material/scene edits.
    props, support_search = [], []
    for name, counter, xy in (('Coffee machine', counters[0], (3910., -4070.)),
                              ('Coffee glasses', counters[0], (4120., -4060.)),
                              ('Wine glass', counters[1], (4520., -4060.)),
                              ('Serving glasses', counters[1], (4340., -4060.))):
        actor = _one(actors, 'Refine/Social/Bar/'+name)
        center, extent = mesh_union(actor)
        # The coffee machine's first full footprint failed the flatness guard.
        # Attempt2 measured112.272cm at the rear lip versus107.554cm worktop.
        # Evaluate a bounded forward/sideways search on
        # actual triangles; keep the original .08cm flatness/contact tolerances.
        candidates = [xy]
        if name == 'Coffee machine':
            candidates += [(xy[0], y) for y in (-4066., -4064., -4062., -4060.)]
            candidates += [(x, y) for x in (3900., 3920.) for y in (-4066., -4064., -4062.)]
        candidates.sort(key=lambda p: math.dist(p, xy))
        _require(all(math.dist(p, xy) <= 13. for p in candidates), 'Support search exceeds the allowed13cm bar adjustment')
        evaluated, accepted = [], None
        cc, ce = mesh_union(counter)
        for candidate in candidates:
            points = [candidate]+[(candidate[0]+sx*extent.x, candidate[1]+sy*extent.y)
                                  for sx in (-1., 1.) for sy in (-1., 1.)]
            row = {'center_xy': candidate, 'footprint_xy': points}
            try:
                _require(all(cc.x-ce.x <= x <= cc.x+ce.x and cc.y-ce.y <= y <= cc.y+ce.y
                             for x, y in points), 'Footprint leaves native counter XY bounds')
                supports = [_surface(counter, geometry, *point, u) for point in points]
                row.update(support_z_cm=supports, spread_cm=max(supports)-min(supports),
                           top_error_cm=abs(max(supports)-worktop))
                row['accepted'] = row['spread_cm'] < .08 and row['top_error_cm'] < .08
                if row['accepted']:
                    accepted = (actor, candidate, max(supports), points, supports)
            except RuntimeError as error:
                row.update(accepted=False, error=str(error))
            evaluated.append(row)
            if accepted:
                break
        support_search.append({'actor': actor.get_actor_label(), 'evaluated': evaluated})
        _require(accepted is not None, 'No flat broad native worktop supports '+name+': '+json.dumps(evaluated))
        props.append(accepted)
    dirty = []
    hull, metal, lens, stool = _finishes(ctx, u, dirty)
    material_allowed, pose_allowed, changed = set(), set(), []

    def override(actor, finish):
        component = actor.get_component_by_class(u.StaticMeshComponent)
        _require(component and component.get_num_materials() == 1, 'Expected a single-slot bar component')
        material_allowed.add(actor.get_path_name())
        component.set_material(0, finish)
        _require(component.get_material(0) == finish, 'Component finish readback failed')

    def box(name, center, size, finish, parent):
        actor = ctx.box(PREFIX+name, center, size, finish, collision=False)
        _require(actor.attach_to_component(parent.static_mesh_component, u.Name(''),
            u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, False),
            'Bar trim failed to attach to its actual supporting fixture')
        return actor

    for actor in counters:
        override(actor, hull)
    for index in range(1, 5):
        override(_one(actors, 'Refine/Social/Bar/Stool '+str(index)), stool)
    for actor, xy, top, points, supports in props:
        center, extent = mesh_union(actor)
        destination = actor.get_actor_location()+u.Vector(xy[0]-center.x, xy[1]-center.y, top-(center.z-extent.z))
        pose_allowed.add(actor.get_path_name())
        ctx.move(actor, destination)
        c, e = mesh_union(actor)
        _require(abs(c.z-e.z-top) < .03 and math.dist((c.x, c.y), xy) < .03, 'Native bar prop grounding readback differs')
        changed.append({'actor': actor.get_actor_label(), 'support_xy': points, 'support_z_cm': supports,
                        'bottom_z_cm': c.z-e.z, 'location': list(destination.to_tuple())})

    seam = _one(actors, 'Refine/SocialFinish/Bar/Join top')
    seam_front = _one(actors, 'Refine/SocialFinish/Bar/Join front')
    for actor, center_z in ((seam, worktop-1.2), (seam_front, worktop-19.2)):
        pose_allowed.add(actor.get_path_name())
        p = actor.get_actor_location()
        ctx.move(actor, (p.x, p.y, center_z))
        override(actor, hull)
    _require(abs(sum((mesh_union(seam)[0].z, mesh_union(seam)[1].z))-worktop) < .03,
             'Seam cap is not flush with the native worktop')

    # Real shallow metal fascias overlap the native body; small diffusers sit
    # inside dark housings. No luminous floor outline or new room light.
    for counter_index, actor in enumerate(counters):
        center, extent = mesh_union(actor)
        front = center.y+extent.y
        for index, offset in enumerate((-135., 0., 135.), 1):
            x = center.x+offset
            base = 'Counter %d/Panel %d/' % (counter_index+1, index)
            box(base+'Bezel', (x, front+.5, 62.), (124., 3., 52.), ctx.asset(GRAPHITE), actor)
            box(base+'Satin face', (x, front+2.3, 62.), (116., 1., 44.), metal, actor)
            box(base+'Practical housing', (x, front+2.4, 85.5), (112., 2., 5.), ctx.asset(GRAPHITE), actor)
            box(base+'Recessed diffuser', (x, front+3.55, 85.5), (104., .5, 1.4), lens, actor)
        box('Counter %d/Toe band' % (counter_index+1), (center.x, front+.7, 8.),
            (398., 3., 10.), metal, actor)

    # Keep every bottle/shelf transform. Framing overlaps the existing uprights
    # and shelf edges; its dark backing is behind the bottles, never over them.
    shelf = _one(actors, 'Refine/Social/Bar/Bottle shelf 0')
    for index in (0, 1):
        override(_one(actors, 'Refine/Social/Bar/Bottle shelf '+str(index)), metal)
        override(_one(actors, 'Refine/SocialDetail/Bar/Shelf lens '+str(index)), lens)
    box('Bottle display/Backing', (4190., -4451., 232.), (376., 4., 152.), ctx.asset(GRAPHITE), shelf)
    shelf_supports = []
    for side in (-1., 1.):
        from PlaceStationLocalArcade import _floor
        x = 4190.+side*182.
        floor = _floor(world, (x, -4433.), [], u)
        box('Bottle display/Floor support '+str(int(side)), (x, -4433., 79.),
            (10., 34., 158.), metal, shelf)
        shelf_supports.append({'x_cm': x, 'y_cm': -4433., 'floor': floor, 'top_z_cm': 158.})
        box('Bottle display/Side '+str(int(side)), (4190.+side*182., -4433., 232.),
            (10., 34., 152.), metal, shelf)
        box('Bottle display/Vertical inset '+str(int(side)), (4190.+side*182., -4415.8, 232.),
            (1.5, .5, 132.), lens, shelf)
        box('Bottle display/Rail '+str(int(side)), (4190., -4433., 232.+side*72.),
            (374., 34., 10.), metal, shelf)

    backing = _one(actors, 'Refine/Social/Bar/Identity/Backing')
    override(backing, ctx.asset(GRAPHITE))
    for side in (-1, 1):
        override(_one(actors, 'Refine/Social/Bar/Identity/Post '+str(side)), metal)
        box('Identity/Side bezel '+str(side), (4200.+side*294., -4425., 348.),
            (10., 4., 70.), metal, backing)
        box('Identity/Edge bezel '+str(side), (4200., -4425., 348.+side*31.),
            (580., 4., 7.), metal, backing)
    name = _one(actors, 'Refine/Social/Bar/Identity/Name')
    text = name.get_component_by_class(u.TextRenderComponent)
    _require(text is not None, 'Existing venue title is not TextRender')
    font = ctx.asset('/Engine/EngineFonts/RobotoDistanceField')
    text.set_font(font)
    text.set_text('THE LONGER ROUTE<br>LOUNGE / REFRESHMENTS')
    text.set_world_size(23.)
    text.set_horizontal_alignment(u.HorizTextAligment.EHTA_CENTER)
    text.set_vertical_alignment(u.VerticalTextAligment.EVRTA_TEXT_CENTER)
    text.set_text_render_color(u.Color(192, 231, 239, 255))
    text.set_text_material(ctx.asset(TEXT))
    size = text.get_text_local_size()
    _require(max(abs(size.x), abs(size.y)) <= 554. and abs(size.z) <= 57., 'Venue title exceeds its native plaque')
    _require(text.get_editor_property('font') == font and abs(float(text.get_editor_property('world_size'))-23.) < .001,
             'Clean venue lettering readback differs')
    after_routes = _aisle(world, u)
    route = u.SystemLibrary.capsule_trace_single_by_profile(world, u.Vector(3780., -3795., 78.),
        u.Vector(4630., -3795., 78.), 34., 75., 'Pawn', False, [], u.DrawDebugTrace.NONE, True)
    _require(route is None or not route.to_tuple()[0], 'Bar frontage approach is blocked')
    for actor in actors:
        key = actor.get_path_name()
        actual, old = _snapshot(actor, u), before[key]
        for field in ('rotation', 'scale', 'hidden', 'lights'):
            _require(actual[field] == old[field], 'Protected existing bar/room state changed: '+actor.get_actor_label()+'/'+field)
        if key not in pose_allowed:
            _require(actual['location'] == old['location'], 'Protected existing actor moved: '+actor.get_actor_label())
        if key not in material_allowed:
            _require(actual['materials'] == old['materials'], 'Protected existing actor material changed: '+actor.get_actor_label())
    _require(sha(map_file) == expected_map_sha256 and all(sha(root/('Content/'+p[6:]+'.uasset')) == digest
             for p, digest in source_hashes.items()), 'Bar helper must not save or mutate source packages')
    return {'dirty_assets': dirty, 'created': [transform_record(a) for a in ctx.created if a.get_actor_label().startswith(PREFIX)],
            'surface_probe_sha256': PROBE_SHA, 'work_surfaces': surface_rows, 'worktop_cm': worktop,
            'surface_correction': 'Positive-winding bands were not a reliable top-height estimate; highest triangles give107.554cm broad/92.247cm recess',
            'counter_transforms_preserved': True, 'prop_support': changed, 'support_search': support_search,
            'shelf_floor_supports': shelf_supports,
            'seam_top_cm': worktop, 'venue_title': str(text.get_editor_property('text')), 'venue_title_size_cm': list(size.to_tuple()),
            'source_sha256': source_hashes, 'protected_existing_actor_count': len(before),
            'pose_allowlist': sorted(pose_allowed), 'material_allowlist': sorted(material_allowed),
            'before_routes': before_routes, 'after_routes': after_routes, 'frontage_capsule_clear': True,
            'existing_lights_ceiling_and_owner_architecture_preserved': True,
            'limits': 'Unsaved furniture presentation candidate; native render and owner review still required'}
