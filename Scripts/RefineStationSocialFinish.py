"""RoomPass6 social finishing; the lead owns the guarded save and render.

No map loading/saving, process launches, vendor edits or seated-pose changes.
The native counter seam, refrigerator face and table/plate surfaces determine
placement. Two complete planted dividers define the existing conversation zones.
"""
import hashlib
import json
from pathlib import Path

from OutpostGeometryUtils import mesh_union
from RefineStationSocialSeatedCrew import _geometry


MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
MAP_SHA = '9b5c8d3b968d47e3e91caad0d0fe40e7245737b52a6c13893cefd35fc1b7a16b'
SEATED_SHA = '3526bb5ed00e5957b148d8fee6b4e2692bdda47aa4a0820f69df4b3a51db1067'
PREFIX = 'Refine/SocialFinish/'
GRAPHITE = '/Game/OutpostSandbox/Materials/M_OutpostGraphite'
LAMP = '/Game/Megastructure_Scifi_World/Meshes/Lamp/SM_lamp_small'
PLANT = '/Game/P1toP5_Bundle/P5_FruitSeller/Blueprints/BP_ISM_PlantBox_V1'
APPLE = '/Game/P1toP5_Bundle/P5_FruitSeller/Meshes/SM_Props_Fruit02'
MEAL = '/Game/CyberpunkRestaurant/Meshes/SM_Food_Package_02'
SODA = '/Game/CyberpunkRestaurant/Meshes/SM_Soda_Can_01'
TABLE = '/Game/CyberpunkRestaurant/Meshes/SM_Table_01'
PLATE = '/Game/CyberPunkMegapack/Meshes/SM_RestaurantFood'
POCKETS = ((1, 3650, -2850), (2, 4740, -2850), (3, 3650, -3550))


def _one(actors, label):
    rows = [a for a in actors if a.get_actor_label() == label]
    if len(rows) != 1:
        raise RuntimeError('Expected one reviewed social actor: ' + label)
    return rows[0]


def _pose(actor):
    t = actor.get_actor_transform()
    return (*t.translation.to_tuple(), *t.rotation.to_tuple(), *t.scale3d.to_tuple())


def _bounds(actor):
    c, e = mesh_union(actor)
    return {'minimum': list((c-e).to_tuple()), 'maximum': list((c+e).to_tuple())}


def _surface(actor, data, x, y, u):
    """Actual highest triangle under XY, independent of triangle winding."""
    component = actor.get_component_by_class(u.StaticMeshComponent)
    t = component.get_world_transform()
    rotation = actor.get_actor_rotation()
    if abs(rotation.pitch) > .001 or abs(rotation.roll) > .001:
        raise RuntimeError('Reviewed horizontal serving surface is tilted')
    local = u.MathLibrary.inverse_transform_location(t, u.Vector(x, y, 0))
    heights = []
    for face in data['triangles']:
        a, b, c = (data['vertices'][i] for i in face)
        det = (b[1]-c[1])*(a[0]-c[0]) + (c[0]-b[0])*(a[1]-c[1])
        if abs(det) < 1.e-8:
            continue
        s = ((b[1]-c[1])*(local.x-c[0]) + (c[0]-b[0])*(local.y-c[1])) / det
        r = ((c[1]-a[1])*(local.x-c[0]) + (a[0]-c[0])*(local.y-c[1])) / det
        if min(s, r, 1-s-r) >= -1.e-7:
            heights.append(s*a[2] + r*b[2] + (1-s-r)*c[2])
    if not heights:
        raise RuntimeError('No native support at the proposed serving location')
    return u.MathLibrary.transform_location(t, u.Vector(local.x, local.y, max(heights))).z


def _aisle(world, u):
    rows = []
    # Includes the previously walked center route and the requested 2m band.
    for x in (4100, 4200, 4300):
        result = u.SystemLibrary.capsule_trace_single_by_profile(world,
            u.Vector(x, -2470, 78), u.Vector(x, -3780, 78), 34., 75., 'Pawn',
            False, [], u.DrawDebugTrace.NONE, True)
        fields = result.to_tuple() if result is not None else None
        if fields and fields[0]:
            raise RuntimeError('Social aisle blocked: ' + str(fields[9]))
        rows.append({'x_cm': x, 'from_y_cm': -2470, 'to_y_cm': -3780,
                     'radius_cm': 34, 'half_height_cm': 75, 'blocked': False})
    return rows


def apply(ctx):
    import unreal as u
    root = Path(u.Paths.project_dir()).resolve()
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    package = world.get_path_name().split('.')[0]
    if package != MAP:
        raise RuntimeError('Only the separate owner preview may be refined')
    map_file = root / ('Content/' + MAP[6:] + '.umap')
    compatibility = json.loads((root / '.agent/local/StationRefinement/Compatibility1.json').read_text())
    if (not compatibility['success'] or compatibility['before_sha256'] != SEATED_SHA or
            compatibility['after_sha256'] != MAP_SHA):
        raise RuntimeError('Expected the verified SocialSeated1 to Compatibility1 receipt chain')
    if hashlib.sha256(map_file.read_bytes()).hexdigest() != MAP_SHA:
        raise RuntimeError('Expected reviewed Compatibility1 map; rebind only after reviewing the new receipt')
    actors = list(ctx.actors)
    if any(a.get_actor_label().startswith(PREFIX) for a in actors):
        raise RuntimeError('Social finish already exists; restore the guarded before state')
    poses = {a: _pose(a) for a in actors}
    roof = _one(actors, 'Engineering/Roof structure')
    if abs(roof.get_actor_location().x-4200) > .01 or abs(roof.get_actor_location().y+3400) > .01:
        raise RuntimeError('Owner social-room anchor moved')
    before_routes = _aisle(world, u)
    assets = {path: ctx.asset(path) for path in
              (GRAPHITE, LAMP, PLANT, APPLE, MEAL, SODA, TABLE, PLATE)}
    hashes = {path: hashlib.sha256((root / ('Content/' + path[6:] + '.uasset')).read_bytes()).hexdigest()
              for path in assets}
    _, table_geometry = _geometry(assets[TABLE], False, u)
    _, plate_geometry = _geometry(assets[PLATE], False, u)
    counters = [_one(actors, 'Refine/Social/Bar/Counter ' + side) for side in ('left', 'right')]
    left, right = [mesh_union(a) for a in counters]
    lc, le = left
    rc, re = right
    gap = rc.x-re.x-lc.x-le.x
    top = lc.z+le.z
    if (abs(gap-10) > .1 or abs(top-(rc.z+re.z)) > .05 or
            max(abs(lc.y+4070), abs(rc.y+4070), abs(top-116.010681)) > .05):
        raise RuntimeError('Native counter seam no longer matches the reviewed render')
    fridge = _one(actors, 'Refine/Social/Bar/Drinks refrigerator')
    fc, fe = mesh_union(fridge)
    if max(abs(fc.x-4590), abs(fc.y+4380), abs(fc.z-fe.z)) > .05:
        raise RuntimeError('Reviewed refrigerator placement changed')
    menu = [_one(actors, 'Refine/SocialDetail/Menu/Kitchen/' + name)
            for name in ('Frame', 'Lens -1', 'Lens 1', 'Heading', 'Body')]
    frame_center, frame_extent = mesh_union(menu[0])
    if max(abs(frame_center.x-4630), abs(frame_center.y+4440), abs(frame_center.z-220)) > .05:
        raise RuntimeError('Kitchen menu no longer at its reviewed occluded position')
    tables = []
    for index, x, y in POCKETS:
        group = 'Refine/Social/Conversation %d/' % index
        table, plate = [_one(actors, group + part) for part in ('Low table', 'Shared food')]
        c, e = mesh_union(table)
        if max(abs(c.x-x), abs(c.y-y), abs(c.z+e.z-44.455406)) > .05:
            raise RuntimeError('Seated conversation table moved')
        tables.append((index, table, plate, x, y))

    # A dark metal saddle bridges the ten-centimetre opening, with overlaps on
    # both native counters. Neither native section or countertop prop moves.
    seam_x = (lc.x+le.x+rc.x-re.x)*.5
    front = max(lc.y+le.y, rc.y+re.y)
    ctx.box('SocialFinish/Bar/Join top', (seam_x, lc.y, top+1.2),
            (gap+4, min(le.y, re.y)*2, 2.4), GRAPHITE, False)
    ctx.box('SocialFinish/Bar/Join front', (seam_x, front+1, top-18),
            (gap+4, 2, 38.4), GRAPHITE, False)

    # Mount a compact complete plaque on the refrigerator's actual front face.
    # Its text is above the counter top; it cannot remain hidden behind the box.
    menu_center = u.Vector(fc.x, fc.y+fe.y+6, 151)
    for actor in menu:
        source = actor.get_actor_location()
        delta = source-frame_center
        ctx.move(actor, menu_center + u.Vector(delta.x*.8, delta.y, delta.z*.6))
        text = actor.get_component_by_class(u.TextRenderComponent)
        if text:
            old_size = float(text.get_editor_property('world_size'))
            ctx.records.append({'kind': 'text_size', 'label': actor.get_actor_label(),
                                'before': old_size, 'after': old_size*.7})
            text.set_world_size(old_size*.7)
            size = text.get_text_local_size()
            if max(abs(size.x), abs(size.y)) > 102 or actor.get_actor_location().z-abs(size.z)*.5 < top+2:
                raise RuntimeError('Reframed kitchen text is not wholly above the bar')
        else:
            scale = actor.get_actor_scale3d()
            ctx.records.append({'kind': 'scale', 'label': actor.get_actor_label(),
                                'before': list(scale.to_tuple()),
                                'after': [scale.x*.8, scale.y, scale.z*.6]})
            actor.set_actor_scale3d(u.Vector(scale.x*.8, scale.y, scale.z*.6))
    mb = _bounds(menu[0])
    if mb['minimum'][1] < fc.y+fe.y-.01 or mb['maximum'][2] > fc.z+fe.z:
        raise RuntimeError('Kitchen plaque is not supported on the refrigerator front')

    light_changes = []
    for index in (0, 1):
        actor = _one(actors, 'Refine/SocialDetail/Bar/Shelf key ' + str(index))
        light = actor.get_component_by_class(u.RectLightComponent)
        old = {k: float(light.get_editor_property(k)) for k in ('intensity', 'specular_scale', 'attenuation_radius')}
        if abs(old['intensity']-700) > .01 or abs(old['attenuation_radius']-170) > .01:
            raise RuntimeError('Reviewed local shelf light changed')
        light.set_intensity(160)
        light.set_editor_property('specular_scale', .08)
        row = {'label': actor.get_actor_label(), 'before': old,
               'after': {'intensity_lumens': 160, 'specular_scale': .08, 'attenuation_radius_cm': 170}}
        ctx.records.append({'kind': 'local_light_parameters', **row})
        light_changes.append(row)

    settings = []
    for index, table, plate, x, y in tables:
        # The native shallow dome is a warm, low table practical. Preserve its
        # metal and separate emissive lens, including the native usage flags.
        lamp_xy = (x-48, y+16)
        surface = _surface(table, table_geometry, *lamp_xy, u)
        lamp = ctx.grounded('SocialFinish/Pocket %d/Table practical' % index, LAMP,
                            lamp_xy, floor=surface, collision=False)
        c, e = mesh_union(lamp)
        if max(e.x, e.y) > 12.1 or abs(c.z-e.z-surface) > .05 or e.z*2 > 6.3:
            raise RuntimeError('Native table-practical geometry changed')
        lens = lamp.static_mesh_component.get_material(1)
        if not lens or lens.get_path_name() != '/Game/Megastructure_Scifi_World/Materials/MI_emissive_red.MI_emissive_red':
            raise RuntimeError('Native table-practical lens changed')
        light = ctx.light('SocialFinish/Pocket %d/Warm table pool' % index,
                          (c.x, c.y, c.z+e.z+2), 70, 170, (1., .61, .30), False)
        component = light.get_component_by_class(u.PointLightComponent)
        component.set_editor_property('specular_scale', .1)
        component.set_editor_property('indirect_lighting_intensity', .15)
        component.set_editor_property('volumetric_scattering_intensity', 0.)
        if not light.attach_to_component(lamp.static_mesh_component, u.Name(''),
                u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD,
                u.AttachmentRule.KEEP_WORLD, False):
            raise RuntimeError('Cannot attach the table light to its visible housing')
        # Fruit belongs on the existing plate. Use its actual concave surface,
        # not the highest edge of its bounding box (which would float the food).
        pc, pe = mesh_union(plate)
        for j, (ox, oy) in enumerate(((-5, -4), (5, 3))):
            z = _surface(plate, plate_geometry, pc.x+ox, pc.y+oy, u)
            fruit = ctx.grounded('SocialFinish/Pocket %d/Fruit %d' % (index, j),
                APPLE, (pc.x+ox, pc.y+oy), floor=z, yaw=index*37+j*83, collision=False)
            fb = _bounds(fruit)
            if fb['minimum'][0] < pc.x-pe.x or fb['maximum'][0] > pc.x+pe.x:
                raise RuntimeError('Native fruit no longer fits the existing plate')
        # A meal and drink at the near edge read as an occupied table, without
        # replacing the existing original glasses or adding unmotivated clutter.
        for name, path, ox, oy in (('Meal', MEAL, -5, -17), ('Drink', SODA, 54, 18)):
            z = _surface(table, table_geometry, x+ox, y+oy, u)
            prop = ctx.grounded('SocialFinish/Pocket %d/%s' % (index, name), path,
                                (x+ox, y+oy), floor=z, collision=False)
            b, tb = _bounds(prop), _bounds(table)
            if any(b['minimum'][a] < tb['minimum'][a]+2 or b['maximum'][a] > tb['maximum'][a]-2 for a in (0, 1)):
                raise RuntimeError('Native serving prop overhangs the actual table')
        settings.append({'pocket': index, 'table_surface_z_cm': surface,
                         'practical_bounds': _bounds(lamp), 'lumens': 70, 'radius_cm': 170})

    dividers = []
    for name, x in (('West', 3930), ('East', 4460)):
        for index, y in enumerate((-2750, -2850, -2950)):
            hit = u.SystemLibrary.line_trace_single_by_profile(world, u.Vector(x, y, 8),
                u.Vector(x, y, -30), 'Pawn', False, [], u.DrawDebugTrace.NONE, True)
            f = hit.to_tuple() if hit is not None else None
            if not f or not f[0] or abs(f[5].z) > .5 or f[7].z < .9:
                raise RuntimeError('Native room floor does not support the planted divider')
            actor = ctx.grounded('SocialFinish/' + name + ' planted divider/' + str(index),
                PLANT, (x, y), floor=f[5].z, scale=(2.765208,)*3)
            c, e = mesh_union(actor)
            if (not 110 < e.z*2 < 125 or e.x > 35 or e.y > 48 or
                    c.x+e.x > 4100 and c.x-e.x < 4300):
                raise RuntimeError('Complete native planted divider violates its reviewed envelope')
            dividers.append({'label': actor.get_actor_label(), **_bounds(actor),
                             'floor_actor': f[9].get_actor_label() if f[9] else None,
                             'floor_z_cm': f[5].z})

    after_routes = _aisle(world, u)
    changed_poses = set(menu)
    if any(_pose(a) != pose for a, pose in poses.items() if a not in changed_poses):
        raise RuntimeError('An unrelated owner, seated crew or furniture pose changed')
    for path, before in hashes.items():
        if hashlib.sha256((root / ('Content/' + path[6:] + '.uasset')).read_bytes()).hexdigest() != before:
            raise RuntimeError('A source asset was changed: ' + path)
    return {'module': 'social_finish', 'dirty_assets': [], 'reviewed_map_sha256': MAP_SHA,
            'native_seam_cm': gap, 'kitchen_plaque_bounds': mb,
            'shelf_keys': light_changes, 'table_settings': settings, 'planted_dividers': dividers,
            'before_routes': before_routes, 'after_routes': after_routes,
            'source_hashes_preserved': hashes, 'seated_and_owner_poses_unchanged': True,
            'acceptance': 'Native authored bounds and queries only; requires fresh social wide/bar/seated renders'}
