"""Stock and light the existing lounge bar without changing room circulation.

Native props keep their original scale and materials. The lead owns the guarded
map transaction and rendered review; this module never loads or saves a map.
"""
from OutpostGeometryUtils import mesh_union
from RefineStationSocialMarket import BAR, GRAPHITE, object_path


def _one(actors, label):
    found = [a for a in actors if a.get_actor_label() == label]
    if len(found) != 1:
        raise RuntimeError('Expected one preserved bar part: ' + label)
    return found[0]


def apply(ctx):
    import unreal as u
    actors = list(ctx.actors)
    if any(a.get_actor_label().startswith('Refine/SocialDetail/') for a in actors):
        raise RuntimeError('Lounge detail pass already exists')
    roof = _one(actors, 'Engineering/Roof structure')
    if abs(roof.get_actor_rotation().yaw) > .01:
        raise RuntimeError('Owner room axes changed')
    origin = roof.get_actor_location()
    dx, dy = origin.x - 4200, origin.y + 3400
    shelves = [_one(actors, 'Refine/Social/Bar/Bottle shelf ' + str(i)) for i in (0, 1)]
    backs = [_one(actors, 'Refine/SocialPolish/Bar/Back panel')]
    text_material = ctx.asset('/Game/OutpostSandbox/Materials/M_OutpostReadableTextOneSided')
    amber = ctx.asset('/Game/OutpostSandbox/Materials/M_OutpostAmber')
    native_bottles = ('SM_BWineBottle01', 'SM_BVodkaBottle01',
                      'SM_BMalibuBottle01', 'SM_BoChampagneBottle01')
    for name in native_bottles:
        ctx.asset(object_path(BAR, name))
    poses = {a: a.get_actor_transform() for a in actors}

    def p(x, y, z):
        return (x + dx, y + dy, z)

    # Fill measured gaps between the ten existing bottles; none replaces or
    # intersects an original bottle. Their native widths are verified below.
    filled = []
    xs = (4040, 4080, 4100, 4140, 4160, 4175, 4210, 4230, 4280, 4300, 4340)
    for level, shelf in enumerate(shelves):
        center, extent = mesh_union(shelf)
        top = center.z + extent.z
        row = []
        for index, x in enumerate(xs):
            name = native_bottles[(index + level) % len(native_bottles)]
            actor = ctx.grounded('SocialDetail/Bar/Bottle %d-%02d' % (level, index),
                object_path(BAR, name), (x + dx, -4435 + dy), floor=top,
                yaw=(index % 3 - 1) * 12, collision=False)
            c, e = mesh_union(actor)
            if e.x * 2 > 14 or c.x-e.x < center.x-extent.x or c.x+e.x > center.x+extent.x:
                raise RuntimeError('Native bottle does not fit shelf gap: ' + name)
            row.append({'label': actor.get_actor_label(), 'center': list(c.to_tuple()),
                        'extent': list(e.to_tuple()), 'shelf_top_cm': top})
        filled += row

        # A visible under-shelf lens and a bounded light illuminate the bottles
        # against the existing dark backing. No global exposure or room fill.
        lens = ctx.box('SocialDetail/Bar/Shelf lens ' + str(level),
            (center.x, center.y + 14, center.z - extent.z - 1), (344, 2, 2), amber, False)
        light = ctx.eas.spawn_actor_from_class(u.RectLight,
            u.Vector(center.x, center.y + 20, center.z + 47),
            u.Rotator(pitch=-25, yaw=-90, roll=0))
        ctx.register(light, 'SocialDetail/Bar/Shelf key ' + str(level))
        component = light.get_component_by_class(u.RectLightComponent)
        component.set_mobility(u.ComponentMobility.MOVABLE)
        component.set_intensity_units(u.LightUnits.LUMENS)
        component.set_intensity(700)
        component.set_attenuation_radius(170)
        component.set_source_width(330)
        component.set_source_height(5)
        component.set_light_color(u.LinearColor(1., .56, .23, 1.))
        component.set_cast_shadows(False)
        component.set_editor_property('specular_scale', .35)
        component.set_editor_property('volumetric_scattering_intensity', 0.)

    menus = []
    for label, x, heading, body in (
            ('Drinks', 3780, 'DRINKS', 'COFFEE\nESPRESSO\nTEA\nCOLD BREW'),
            ('Kitchen', 4630, 'KITCHEN', 'WARM PLATES\nFRESH FRUIT\nSHARED BITES\nTAKE A SEAT')):
        ctx.box('SocialDetail/Menu/' + label + '/Frame', p(x, -4440, 220),
                (142, 12, 218), GRAPHITE, False)
        for side in (-1, 1):
            ctx.box('SocialDetail/Menu/' + label + '/Lens ' + str(side),
                    p(x + side * 67, -4433, 220), (2, 2, 206), amber, False)
        for name, text, z, size in (('Heading', heading, 296, 23), ('Body', body, 206, 17)):
            actor = ctx.text('SocialDetail/Menu/' + label + '/' + name,
                text, p(x, -4432, z), 90, size=size, color=(1., .84, .61))
            component = actor.get_component_by_class(u.TextRenderComponent)
            component.set_text_material(text_material)
            bounds = component.get_text_local_size()
            width = max(abs(bounds.x), abs(bounds.y))
            if width > 128:
                component.set_world_size(size * 128 / width)
            menus.append({'label': actor.get_actor_label(), 'text': text,
                          'size_cm': list(component.get_text_local_size().to_tuple())})

    # Native Transform wrappers do not reliably support value equality.
    def values(t):
        return (*t.translation.to_tuple(), *t.rotation.to_tuple(), *t.scale3d.to_tuple())
    assert all(values(a.get_actor_transform()) == values(t) for a, t in poses.items())
    return {'module': 'social_bar_detail', 'native_bottles_added': filled,
            'menu_labels': menus, 'local_shelf_keys': 2, 'dirty_assets': [],
            'existing_actor_transforms_unchanged': True,
            'all_new_parts_outside_walkways': True,
            'basis': 'RoomPass3 lounge bar too sparse; approved target has a stocked warm backbar',
            'acceptance': 'Requires actual bar render; no quality acceptance inferred from prop count'}
