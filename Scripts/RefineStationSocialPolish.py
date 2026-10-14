"""Second visual pass for L, based on RoomPass1's actual social-room renders.

Run after the corrected keyword-Rotator social pass and Operations relocation.
No map loads/saves or vendor edits. New private material instances are returned
to the lead as dirty_assets; the guarded transaction owns saving those packages.
"""

import hashlib

from OutpostGeometryUtils import mesh_union


PRIVATE = '/Game/OutpostSandbox/OwnerPreview/Materials/SocialPolish'
P4 = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/'
GRAPHITE = '/Game/OutpostSandbox/Materials/M_OutpostGraphite.M_OutpostGraphite'
BLUE_GRAPHIC = '/Game/OutpostSandbox/Materials/MI_HologramWallBlue_KeosAdvertisment.MI_HologramWallBlue_KeosAdvertisment'
PLAIN_PANE = P4 + 'Meshes/SM_Window400X250_V1_Part2.SM_Window400X250_V1_Part2'
DIGITAL_PANE = P4 + 'Meshes/SM_Window400X250_V2_Part2_DigitalWindow.SM_Window400X250_V2_Part2_DigitalWindow'
PANE_LABELS = ('Engineering/Bay W1/Glass', 'Engineering/Bay E4/Glass',
               'Engineering/Bay S1/Glass')


def _one(actors, label):
    found = [a for a in actors if a.get_actor_label() == label]
    if len(found) != 1:
        raise RuntimeError('Social polish requires one %s; found %d' % (label, len(found)))
    return found[0]


def _record_material(ctx, actor, component, slot, material):
    current = component.get_material(slot)
    ctx.records.append({'kind': 'material_override', 'before': {
        'actor': actor.get_path_name(), 'label': actor.get_actor_label(),
        'component': component.get_name(), 'slot': slot,
        'material': current.get_path_name() if current else None},
        'after_material': material.get_path_name()})
    component.set_material(slot, material)


def _textured_finishes(ctx, actors, u):
    """Keep every current graph, texture and material slot; tint private children."""
    edit = u.MaterialEditingLibrary
    cache, dirty = {}, []
    changed = 0
    for actor in actors:
        label = actor.get_actor_label()
        role = ('Deck' if label.startswith('Engineering/Deck ') else
                'Ceiling' if label == 'Engineering/Ceiling panel' else None)
        if not role:
            continue
        for component in actor.get_components_by_class(u.StaticMeshComponent):
            for slot, parent in enumerate(component.get_materials()):
                if not isinstance(parent, u.MaterialInstanceConstant):
                    continue
                key = (role, parent.get_path_name())
                if key not in cache:
                    vectors = set(map(str, edit.get_vector_parameter_names(parent)))
                    scalars = set(map(str, edit.get_scalar_parameter_names(parent)))
                    # This exact interface is already used by OutpostSurfaceFinish.
                    # A changed vendor interface fails instead of silently tinting
                    # an unrelated layer or replacing the textured material.
                    if 'Albedo Tint' not in vectors:
                        cache[key] = None
                        continue
                    if 'Albedo Tint Intensity' not in scalars:
                        raise RuntimeError('Native finish tint interface changed: ' + parent.get_path_name())
                    name = 'MI_Social_' + role + '_' + hashlib.sha1('|'.join(key).encode()).hexdigest()[:12]
                    path = PRIVATE + '/' + name
                    if u.EditorAssetLibrary.does_asset_exist(path):
                        raise RuntimeError('Private social finish already exists; review guarded replay: ' + path)
                    child = u.AssetToolsHelpers.get_asset_tools().create_asset(
                        name, PRIVATE, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
                    if not child:
                        raise RuntimeError('Could not create private social finish: ' + path)
                    edit.set_material_instance_parent(child, parent)
                    # The first render loses both floor pattern and fixture shape
                    # to broad white response. Retain detail, reduce paint value,
                    # and keep a moderately rough metal rather than mirror chrome.
                    tint = (.055, .080, .105) if role == 'Deck' else (.035, .050, .065)
                    edit.set_material_instance_vector_parameter_value(child, 'Albedo Tint', u.LinearColor(*tint, 1))
                    changes = {'Albedo Tint Intensity': .98,
                               'Min Roughness': .56 if role == 'Deck' else .67,
                               'Max Roughness': .84 if role == 'Deck' else .94}
                    for parameter, value in changes.items():
                        if parameter in scalars:
                            edit.set_material_instance_scalar_parameter_value(child, parameter, value)
                    edit.update_material_instance(child)
                    actual = edit.get_material_instance_vector_parameter_value(child, 'Albedo Tint')
                    if max(abs(getattr(actual, channel) - value)
                           for channel, value in zip('rgb', tint)) > .00001:
                        raise RuntimeError('Private social tint readback failed: ' + path)
                    for parameter in edit.get_texture_parameter_names(parent):
                        if edit.get_material_instance_texture_parameter_value(child, parameter) != \
                                edit.get_material_instance_texture_parameter_value(parent, parameter):
                            raise RuntimeError('Social finish changed an inherited texture')
                    cache[key] = child
                    dirty.append(child.get_path_name())
                if cache[key]:
                    _record_material(ctx, actor, component, slot, cache[key])
                    changed += 1
    if not dirty or not changed:
        raise RuntimeError('No inspected L floor/ceiling finishes were found')
    return {'slots_changed': changed, 'dirty_assets': dirty,
            'native_graphs_and_textures_inherited': True}


def _graphic_windows(ctx, actors, u):
    mesh = ctx.asset(DIGITAL_PANE)
    original = ctx.asset(PLAIN_PANE)
    a, b = original.get_bounds(), mesh.get_bounds()
    for field in ('origin', 'box_extent'):
        if max(abs(getattr(getattr(a, field), axis) - getattr(getattr(b, field), axis))
               for axis in ('x', 'y', 'z')) > .01:
            raise RuntimeError('Digital pane no longer matches the existing architectural glass')
    graphic = ctx.asset(BLUE_GRAPHIC)
    result = []
    for label in PANE_LABELS:
        actor = _one(actors, label)
        component = actor.get_component_by_class(u.StaticMeshComponent)
        if not component or component.static_mesh.get_path_name() != PLAIN_PANE:
            raise RuntimeError('Blank pane changed before social polish: ' + label)
        transform = actor.get_actor_transform()
        before_pose = (tuple(transform.translation.to_tuple()), tuple(transform.rotation.to_tuple()),
                       tuple(transform.scale3d.to_tuple()))
        before_collision = component.get_collision_enabled()
        ctx.records.append({'kind': 'mesh_override', 'before': {
            'actor': actor.get_path_name(), 'label': label, 'component': component.get_name(),
            'mesh': component.static_mesh.get_path_name(),
            'materials': [m.get_path_name() if m else None for m in component.get_materials()]}})
        component.set_static_mesh(mesh)
        for slot in range(component.get_num_materials()):
            component.set_material(slot, graphic)
        transform = actor.get_actor_transform()
        after_pose = (tuple(transform.translation.to_tuple()), tuple(transform.rotation.to_tuple()),
                      tuple(transform.scale3d.to_tuple()))
        if component.get_collision_enabled() != before_collision or after_pose != before_pose:
            raise RuntimeError('Architectural pane placement/collision changed: ' + label)
        result.append(label)
    return result


def _lighting(ctx, actors, u):
    # The screenshot's broad white hot spots correspond to two 9000-unit room
    # ceiling fills, in addition to the original ceiling and local task pools.
    targets = {'UsableLighting/Engineering/Ceiling 1': 2800,
               'UsableLighting/Engineering/Ceiling 2': 2800,
               'Engineering/Ceiling pool': 700,
               'Refine/Social/Lighting/Bar': 1400,
               'Refine/Social/Lighting/West conversations': 650,
               'Refine/Social/Lighting/Food': 650,
               'Refine/Social/Lighting/Arcade': 400}
    changes = []
    for actor in actors:
        label = actor.get_actor_label()
        if label in ('InteriorReadability/Engineering diagnostic Port',
                     'InteriorReadability/Engineering diagnostic Starboard'):
            ctx.hide(actor)  # Their diagnostic desks were already retired.
        if label not in targets:
            continue
        for component in actor.get_components_by_class(u.LightComponent):
            before = float(component.get_editor_property('intensity'))
            ctx.records.append({'kind': 'light_intensity', 'before': {
                'actor': actor.get_path_name(), 'label': label,
                'component': component.get_name(), 'intensity': before},
                'after_intensity': targets[label]})
            component.set_intensity(targets[label])
            changes.append({'label': label, 'before': before, 'after': targets[label]})
    if not all(any(row['label'] == label for row in changes)
               for label in ('UsableLighting/Engineering/Ceiling 1', 'UsableLighting/Engineering/Ceiling 2')):
        raise RuntimeError('Expected broad L ceiling pools were not found')
    return changes


def _bar_frame(ctx, actors):
    roof = _one(actors, 'Engineering/Roof structure').get_actor_location()
    dx, dy = roof.x - 4200, roof.y + 3400

    def p(x, y, z):
        return (x + dx, y + dy, z)

    # A dark working back-bar joins existing shelves/appliances. The native
    # architecture remains intact behind this shallow, reversible installation.
    ctx.box('SocialPolish/Bar/Back panel', p(4190, -4449, 210),
            (650, 10, 260), GRAPHITE, False)
    ctx.box('SocialPolish/Bar/Header', p(4200, -4438, 386),
            (970, 25, 28), GRAPHITE, False)
    for side in (-1, 1):
        ctx.box('SocialPolish/Bar/Upright ' + str(side), p(4200 + side * 485, -4438, 200),
                (16, 25, 400), GRAPHITE, False)
    # Keep the first-pass title in front of the new feature backing. Never alter
    # its corrected yaw or native scale while moving this complete sign group.
    for actor in actors:
        if actor.get_actor_label().startswith('Refine/Social/Bar/Identity/'):
            pos = actor.get_actor_location()
            ctx.move(actor, (pos.x, pos.y + 30, pos.z))

    ceiling_actors = [a for a in actors if a.get_actor_label() == 'Engineering/Ceiling panel']
    if not ceiling_actors:
        raise RuntimeError('Missing actual L ceiling fixture support')
    ceiling = min(mesh_union(a)[0].z - mesh_union(a)[1].z for a in ceiling_actors)
    fixture = '/Game/CyberpunkRestaurant/Meshes/SM_Fluorescent_Light_01.SM_Fluorescent_Light_01'
    for index, x in enumerate((3950, 4450), 1):
        lamp = ctx.grounded('SocialPolish/Bar/Pendant ' + str(index), fixture,
                            (x + dx, -4020 + dy), floor=350, collision=False)
        center, extent = mesh_union(lamp)
        top = center.z + extent.z
        if not 0 < ceiling - top < 100:
            raise RuntimeError('Bar fixture cannot attach to actual ceiling')
        for side in (-1, 1):
            ctx.box('SocialPolish/Bar/Pendant %d drop %d' % (index, side),
                    p(x + side * 95, -4020, (ceiling + top) * .5),
                    (3, 3, ceiling - top), GRAPHITE, False)
    return {'new_fixture_housings': 2, 'actual_ceiling_underside_cm': ceiling,
            'architecture_transforms_unchanged': True}


def apply(ctx):
    """Prepare the bounded second pass; lead saves returned dirty_assets."""
    import unreal as u
    actors = list(ctx.actors)
    if any(a.get_actor_label().startswith('Refine/SocialPolish/') for a in actors):
        raise RuntimeError('Social polish already applied; restore the guarded prior state')
    _one(actors, 'Refine/Social/Bar/Counter left')
    _one(actors, 'Engineering/Roof structure')
    for label in PANE_LABELS:
        _one(actors, label)
    finishes = _textured_finishes(ctx, actors, u)
    panes = _graphic_windows(ctx, actors, u)
    lighting = _lighting(ctx, actors, u)
    bar = _bar_frame(ctx, actors)
    return {'module': 'social_polish', 'dirty_assets': finishes['dirty_assets'],
            'finishes': finishes, 'blue_graphic_panes': panes, 'lighting': lighting, 'bar': bar,
            'basis': 'RoomPass1/02_Social and 03_SocialReverse',
            'acceptance': 'Requires actual corrected-room render; no visual pass inferred from changes',
            'market': 'Await corrected-yaw storefront render before another market delta'}


def apply_visible_ceiling(ctx, *, light_gain, dark_gain):
    """Follow-up for the actual central StarterBundle panels, after render review.

    Gains are explicit lead-selected inputs: main apply() intentionally does not
    repeat. The 18 visible central panels use a different shader from the Genesis
    perimeter, with four color channels rather than Albedo Tint. No light changes.
    """
    import unreal as u
    if not 0 < light_gain <= 1 or not 0 < dark_gain <= 1:
        raise ValueError('Ceiling source-relative color gains must be in (0, 1]')
    mesh_path = '/Game/StarterBundle/ModularScifiProps/Meshes/SM_Ceiling_B.SM_Ceiling_B'
    parents = {
        '/Game/OutpostSandbox/Materials/MI_SatinPanel_MI_Base_Light.MI_SatinPanel_MI_Base_Light': light_gain,
        '/Game/OutpostSandbox/Materials/MI_SatinPanel_MI_Base_Dark.MI_SatinPanel_MI_Base_Dark': dark_gain,
    }
    actors = [a for a in ctx.actors if a.get_actor_label().startswith('QuietCeiling/Engineering/Panel ')]
    if len(actors) != 18:
        raise RuntimeError('Expected the inspected 18 central L ceiling panels')
    edit = u.MaterialEditingLibrary
    colors = ('R Color', 'G Color', 'B Color', 'Other Color')
    staged, source_materials = [], {}
    for actor in actors:
        components = actor.get_components_by_class(u.StaticMeshComponent)
        if (len(components) != 1 or components[0].static_mesh.get_path_name() != mesh_path or
                actor.get_editor_property('hidden') or
                not components[0].get_editor_property('visible')):
            raise RuntimeError('Central L ceiling geometry/visibility changed: ' + actor.get_actor_label())
        component = components[0]
        if component.get_num_materials() != 2:
            raise RuntimeError('Central L ceiling slot count changed')
        for slot, parent in enumerate(component.get_materials()):
            if not isinstance(parent, u.MaterialInstanceConstant) or parent.get_path_name() not in parents:
                raise RuntimeError('Central L ceiling has an unreviewed material override')
            if not set(colors) <= set(map(str, edit.get_vector_parameter_names(parent))):
                raise RuntimeError('Native M_Base_3C four-color interface differs from inspected source')
            source_materials[parent.get_path_name()] = parent
            staged.append((actor, component, slot, parent.get_path_name()))
    if set(source_materials) != set(parents):
        raise RuntimeError('Both inspected central ceiling material channels are required')
    children, dirty, values = {}, [], []
    for path, parent in source_materials.items():
        gain = parents[path]
        name = 'MI_Social_QuietCeiling_' + ('Light' if '_Light.' in path else 'Dark')
        destination = PRIVATE + '/' + name
        if u.EditorAssetLibrary.does_asset_exist(destination):
            raise RuntimeError('Quiet-ceiling derivative already exists; review replay before changing it')
        child = u.AssetToolsHelpers.get_asset_tools().create_asset(
            name, PRIVATE, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
        if not child:
            raise RuntimeError('Failed to create private quiet-ceiling finish')
        edit.set_material_instance_parent(child, parent)
        channel_record = {}
        for parameter in colors:
            source = edit.get_material_instance_vector_parameter_value(parent, parameter)
            target = (source.r * gain, source.g * gain, source.b * gain, source.a)
            edit.set_material_instance_vector_parameter_value(child, parameter, u.LinearColor(*target))
            actual = edit.get_material_instance_vector_parameter_value(child, parameter)
            if max(abs(getattr(actual, c) - v) for c, v in zip('rgba', target)) > .00001:
                raise RuntimeError('Quiet-ceiling vector readback failed: ' + parameter)
            channel_record[parameter] = {'before': [source.r, source.g, source.b, source.a],
                                         'after': list(target)}
        # Keep the existing normal map, scratches, channel masks, roughness and
        # two-sided satin behavior inherited from the actual placed parent.
        for parameter in edit.get_texture_parameter_names(parent):
            if edit.get_material_instance_texture_parameter_value(child, parameter) != \
                    edit.get_material_instance_texture_parameter_value(parent, parameter):
                raise RuntimeError('Quiet-ceiling derivative changed an inherited texture')
        edit.update_material_instance(child)
        children[path] = child
        dirty.append(child.get_path_name())
        values.append({'source': path, 'gain': gain, 'channels': channel_record,
                       'private': child.get_path_name()})
    for actor, component, slot, path in staged:
        _record_material(ctx, actor, component, slot, children[path])
    return {'module': 'social_visible_ceiling', 'dirty_assets': dirty, 'materials': values,
            'visible_panels': len(actors), 'unchanged': ['geometry', 'transforms', 'collision',
            'lights', 'roughness', 'textures', 'other rooms'],
            'acceptance': 'Private color correction only; actual room render still required'}


def apply_followup(ctx):
    """RoomPass2 distribution and fixture keys; no further surface darkening.

    Move complete furnishings rigidly, keep the central route, and give the
    existing market fronts a second face readable when approaching along +X.
    All original emissive materials and native decorative lights are preserved.
    """
    import unreal as u
    actors = list(ctx.actors)
    prefix = 'Refine/SocialFollowup/'
    if any(a.get_actor_label().startswith(prefix) for a in actors):
        raise RuntimeError('Social follow-up already exists; restore the guarded prior state')
    roof = _one(actors, 'Engineering/Roof structure')
    if abs(roof.get_actor_rotation().yaw) > .01:
        raise RuntimeError('L room axes changed; review distribution before authoring')
    origin = roof.get_actor_location()
    dx, dy = origin.x - 4200, origin.y + 3400
    pockets = ((1, (3370, -3000), (3650, -2850)),
               (2, (5050, -3000), (4740, -2850)),
               (3, (3370, -3800), (3650, -3550)))
    members = ('Sofa south', 'Sofa north', 'Low table', 'Coffee', 'Shared food')
    staged = []
    for index, old, new in pockets:
        group = [_one(actors, 'Refine/Social/Conversation %d/%s' % (index, part))
                 for part in members]
        center, _ = mesh_union(group[2])
        if max(abs(center.x - old[0] - dx), abs(center.y - old[1] - dy)) > .05:
            raise RuntimeError('Conversation group moved since RoomPass2: ' + str(index))
        staged.append((index, group, (new[0] - old[0], new[1] - old[1])))
    pendants = [_one(actors, 'Refine/SocialPolish/Bar/Pendant ' + str(i)) for i in (1, 2)]
    replaced_pools = [_one(actors, 'Refine/Social/Lighting/' + name)
                      for name in ('Bar', 'West conversations')]
    title_actor = _one(actors, 'Refine/Social/Bar/Identity/Name')
    title = title_actor.get_component_by_class(u.TextRenderComponent)
    if not title:
        raise RuntimeError('Expected existing bar TextRender title')
    gantries = []
    for section in ('Exchange', 'Arrivals'):
        for index in (0, 3):
            actor = _one(actors, 'PublicLighting/Market/%s gantry/%d/Local downlight' % (section, index))
            component = actor.get_component_by_class(u.RectLightComponent)
            if not component:
                raise RuntimeError('Expected physical gantry RectLight: ' + actor.get_actor_label())
            before = {key: float(component.get_editor_property(key)) for key in
                      ('intensity', 'attenuation_radius', 'source_width', 'source_height')}
            before['intensity_units'] = str(component.get_editor_property('intensity_units'))
            before['cast_shadows'] = bool(component.get_editor_property('cast_shadows'))
            before['visible'] = bool(component.get_editor_property('visible'))
            if abs(before['intensity'] - 4200) > .01 or abs(before['attenuation_radius'] - 1450) > .01:
                raise RuntimeError('Market gantry baseline changed: ' + actor.get_actor_label())
            gantries.append((actor, component, before))
    vendors = (
        ('Produce', 'SOL & SON\nPRODUCE', (1., .90, .70)),
        ('Botany', 'VERDANT\nBOTANY', (.65, .95, .72)),
        ('Machinery', 'KEL-TEC\nROBOTICS', (.65, .84, 1.)),
        ('Nova', 'NOVA BITES\nHOT FOOD', (1., .72, .40)))
    posts = [_one(actors, 'Refine/Market/' + role + '/Identity/Post -1')
             for role, _, _ in vendors]
    for post in posts:
        center, _ = mesh_union(post)
        if abs(center.y) - 100 < 600:
            raise RuntimeError('Arrival-facing blade would intrude on the market route')
    ceiling_actors = [a for a in actors if a.get_actor_label() == 'Engineering/Ceiling panel']
    if not ceiling_actors:
        raise RuntimeError('Missing actual L ceiling support')
    ceiling = min(mesh_union(a)[0].z - mesh_union(a)[1].z for a in ceiling_actors)
    fixture = '/Game/CyberpunkRestaurant/Meshes/SM_Lamp_02.SM_Lamp_02'
    ctx.asset(fixture)
    ctx.asset(GRAPHITE)

    keys = []

    def rect_key(label, housing, target, lumens, radius, width):
        center, extent = mesh_union(housing)
        position = u.Vector(center.x, center.y, center.z - extent.z - 1)
        rotation = u.MathLibrary.find_look_at_rotation(position, u.Vector(*target))
        light = ctx.eas.spawn_actor_from_class(u.RectLight, position, rotation)
        if not light:
            raise RuntimeError('Could not create fixture key: ' + label)
        ctx.register(light, 'SocialFollowup/' + label)
        component = light.get_component_by_class(u.RectLightComponent)
        component.set_mobility(u.ComponentMobility.MOVABLE)
        component.set_intensity_units(u.LightUnits.LUMENS)
        component.set_intensity(lumens)
        component.set_attenuation_radius(radius)
        component.set_source_width(width)
        component.set_source_height(8)
        component.set_light_color(u.LinearColor(1., .80, .58, 1.))
        component.set_cast_shadows(False)
        component.set_editor_property('specular_scale', .4)
        component.set_editor_property('indirect_lighting_intensity', .25)
        component.set_editor_property('volumetric_scattering_intensity', 0.)
        mount = housing.get_component_by_class(u.StaticMeshComponent)
        if not light.attach_to_component(mount, u.Name(''), u.AttachmentRule.KEEP_WORLD,
                u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, False):
            raise RuntimeError('Could not attach local key to its physical fixture')
        keys.append({'label': label, 'housing': housing.get_actor_label(),
                     'position_cm': list(position.to_tuple()), 'target_cm': list(target),
                     'lumens': lumens, 'radius_cm': radius, 'source_width_cm': width,
                     'source_height_cm': 8, 'cast_shadows': False})

    distributions = []
    for index, group, delta in staged:
        for actor in group:
            pos = actor.get_actor_location()
            ctx.move(actor, (pos.x + delta[0], pos.y + delta[1], pos.z))
        table_center, table_extent = mesh_union(group[2])
        for actor in group:
            center, extent = mesh_union(actor)
            if center.x + extent.x > 4000 + dx and center.x - extent.x < 4400 + dx:
                raise RuntimeError('Moved conversation geometry crosses the central route')
        lamp = ctx.grounded('SocialFollowup/Conversation %d/Pendant' % index,
                            fixture, (table_center.x, table_center.y), floor=350, collision=False)
        center, extent = mesh_union(lamp)
        top = center.z + extent.z
        if not 0 < ceiling - top < 100:
            raise RuntimeError('Conversation pendant cannot attach to actual ceiling')
        for side in (-1, 1):
            ctx.box('SocialFollowup/Conversation %d/Drop %d' % (index, side),
                    (center.x + side * 55, center.y, (top + ceiling) * .5),
                    (2, 2, ceiling - top), GRAPHITE, False)
        rect_key('Conversation %d/Table key' % index, lamp,
                 (table_center.x, table_center.y, table_center.z + table_extent.z), 950, 550, 120)
        distributions.append({'group': index, 'rigid_delta_xy_cm': list(delta),
                              'table_center_cm': list(table_center.to_tuple()), 'members': len(group)})
    for index, lamp in enumerate(pendants, 1):
        center, _ = mesh_union(lamp)
        rect_key('Bar/Counter key ' + str(index), lamp,
                 (center.x, -4180 + dy, 140), 1800, 650, 200)
    for actor in replaced_pools:
        ctx.hide(actor)  # Replace the two invisible free-floating local pools.
    before_size = float(title.get_editor_property('world_size'))
    ctx.records.append({'kind': 'text_size', 'before': {'actor': title_actor.get_path_name(),
                        'label': title_actor.get_actor_label(), 'world_size': before_size},
                        'after_world_size': 36})
    title.set_world_size(36)

    blades = []
    for (role, content, color), post in zip(vendors, posts):
        center, extent = mesh_union(post)
        z = center.z + extent.z - 15
        if z - 55 < 205:
            raise RuntimeError('Market blade lacks pedestrian head clearance')
        ctx.box('SocialFollowup/Market/' + role + '/Blade', (center.x, center.y, z),
                (8, 200, 110), GRAPHITE, False)
        ctx.text('SocialFollowup/Market/' + role + '/Arrival name', content,
                 (center.x - 4.5, center.y, z), 180, size=24, color=color)
        blades.append({'vendor': role, 'mount': post.get_actor_label(),
                       'center_cm': [center.x, center.y, z], 'size_cm': [8, 200, 110],
                       'front_yaw': 180, 'head_clearance_cm': z - 55})
    gantry_changes = []
    for actor, component, before in gantries:
        ctx.records.append({'kind': 'light_parameters', 'before': {
            'actor': actor.get_path_name(), 'label': actor.get_actor_label(),
            'component': component.get_name(), **before},
            'after_intensity': 1800, 'after_attenuation_radius': 900})
        component.set_intensity(1800)
        component.set_attenuation_radius(900)
        gantry_changes.append({'label': actor.get_actor_label(), 'before': before,
                               'after': {'intensity': 1800, 'attenuation_radius': 900,
                                         'intensity_units': before['intensity_units']}})
    return {'module': 'social_market_followup', 'dirty_assets': [],
            'basis': 'RoomPass2/02_Social, 03_SocialReverse and 07_Market',
            'conversation_groups': distributions, 'fixture_keys': keys,
            'bar_title_world_size': {'before': before_size, 'after': 36},
            'market_blades': blades, 'market_gantries': gantry_changes,
            'central_social_route_x_cm': [4000 + dx, 4400 + dx],
            'market_route_y_cm': [-500, 500], 'all_emissive_materials_preserved': True,
            'ceiling_and_platform_materials_unchanged': True,
            'acceptance': 'Requires native route checks and matched actual room render; no visual pass inferred'}
