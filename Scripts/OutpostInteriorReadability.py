"""Local fixture-backed interior readability; no global exposure or fog edits.

Adds thirteen shadowless, directed emitters with bounded radii. The existing
task areas keep their downward orientation and diffuse flux; only their bright
specular contribution is reduced. Three static archive figures use a separate
warm hologram finish. Interactive wardrobe material/state remains untouched.
"""
from math import cos, radians, sin

TARGET = '/Game/OutpostSandbox/L_AsteroidOutpost'
PREFIX = 'InteriorReadability/'
TAG = 'OutpostInteriorReadability'
P5_LAMP = '/Game/P1toP5_Bundle/P5_FruitSeller/Meshes/SM_Props_ConstructionPart118_Light.SM_Props_ConstructionPart118_Light'


def layout():
    """Pure candidate light placements, in world centimetres and lumens."""
    from OutpostInteriorAssemblies import BANKS
    rows = []

    def add(name, fixture, fixture_center, position, target, power, radius,
            color, width=80, height=8, kind='native lamp'):
        rows.append({'name': PREFIX + name, 'fixture': fixture,
            'fixture_center': list(fixture_center), 'position': list(position),
            'target': list(target), 'lumens': power, 'radius_cm': radius,
            'color': list(color), 'source_width_cm': width,
            'source_height_cm': height, 'fixture_kind': kind,
            'casts_shadows': False})

    for side, x, screen_x in [('Port', 3890, 3995), ('Starboard', 4510, 4405)]:
        add('Engineering diagnostic ' + side,
            'Engineering/Diagnostic backing/' + side + ' integral lamp',
            (x, -4380, 360), (x, -4380, 350), (screen_x, -4410, 190),
            300, 420, (.72, .86, 1.0))

    # The six wall banks get one inward face wash each from their existing
    # suspended task fixture. Downward task emitters stay contract-compatible.
    for index, (name, (x, y, z), yaw) in enumerate(BANKS):
        angle = radians(yaw)
        side = -1 if index % 2 else 1
        dx, dy = side * 210, -130
        xx, yy = x + dx*cos(angle) - dy*sin(angle), y + dx*sin(angle) + dy*cos(angle)
        tx, ty = x + dx*cos(angle) + 15*sin(angle), y + dx*sin(angle) - 15*cos(angle)
        add('Operations face ' + name,
            'OperationsNative/' + name + '/Local task ' + str(side) + '/Owned light housing',
            (xx, yy, z+333), (xx, yy, z+319), (tx, ty, z+170),
            350, 520, (.7, .84, 1.0))

    add('Arcade cabinets', 'LoungeNative/Conversation 2/Owned light housing',
        (3440, 3710, 390), (3440, 3710, 367), (3810, 4180, 125),
        700, 850, (1.0, .72, .46), width=100, height=12)

    for index, y in enumerate((-3930, -2870), 1):
        add('Gallery mullions ' + str(index), 'Observation/Ceiling guidance 3100',
            (3100, -3400, 1035), (3100, y, 1027), (2910, y, 760),
            350, 600, (.62, .82, 1.0), width=90, height=4,
            kind='visible ceiling guidance strip')
        add('Gallery crew ' + str(index), 'Observation/Ceiling guidance 4100',
            (4100, -3400, 1035), (4100, y, 1027), (3990, y, 680),
            450, 620, (1.0, .82, .6), width=90, height=4,
            kind='visible ceiling guidance strip')
    assert len(rows) == 13 and len({r['name'] for r in rows}) == 13
    return rows


def apply(api):
    """Idempotently apply this local candidate after task-area adoption.

    Caller owns saving and visual acceptance. New emitters reuse exact owned
    labels/tags. Native material, mesh, Blueprint and global settings stay intact.
    """
    import unreal as u
    from OutpostGeometryUtils import mesh_union
    import OutpostTaskAreaLights
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    package = world.get_path_name().split('.')[0]
    fresh = package.startswith('/Temp/Untitled') and api.get('TARGET') == TARGET
    if package != TARGET and not fresh:
        raise RuntimeError('Interior readability is restricted to the private outpost')
    eas = api['EAS']
    actors = {}
    for actor in eas.get_all_level_actors():
        actors.setdefault(actor.get_actor_label(), []).append(actor)

    def one(name):
        found = actors.get(name, [])
        if len(found) != 1:
            raise RuntimeError('Missing or duplicate readability anchor: ' + name)
        return found[0]

    rows = layout()
    anchor_records = []
    for row in rows:
        fixture = one(row['fixture'])
        mesh_component = fixture.get_component_by_class(u.StaticMeshComponent)
        if not mesh_component or not mesh_component.static_mesh:
            raise RuntimeError('Readability fixture has no native geometry: ' + row['fixture'])
        if row['fixture_kind'] == 'native lamp' and mesh_component.static_mesh.get_path_name() != P5_LAMP:
            raise RuntimeError('Readability anchor is not the expected owned lamp')
        center, extent = mesh_union(fixture)
        values = [center.x, center.y, center.z]
        if max(abs(values[i] - row['fixture_center'][i]) for i in range(3)) > 1:
            raise RuntimeError('Readability fixture moved: ' + row['fixture'])
        if not row['position'][2] < center.z - extent.z:
            raise RuntimeError('Readability emitter is inside its physical housing')
        if row['fixture_kind'] == 'visible ceiling guidance strip':
            if abs(row['position'][1] - center.y) > extent.y:
                raise RuntimeError('Gallery light is detached from its strip')
        existing = actors.get(row['name'], [])
        if len(existing) > 1 or (existing and
                (TAG not in map(str, existing[0].tags) or not isinstance(existing[0], u.RectLight))):
            raise RuntimeError('Readability label is occupied by an unrelated actor')
        anchor_records.append({'fixture': row['fixture'], 'mesh': mesh_component.static_mesh.get_path_name(),
            'actual_center_cm': values, 'extent_cm': [extent.x, extent.y, extent.z]})

    # Resolve the complete original/adopted fixture set before editing lights.
    specular = []
    for row in OutpostTaskAreaLights.layout():
        for suffix in ('', OutpostTaskAreaLights.PERMANENT_SUFFIX):
            actor = one(row['light_label'] + suffix)
            component = actor.get_component_by_class(u.LocalLightComponent)
            if not component:
                raise RuntimeError('Task actor lacks a local light component')
            specular.append((actor, component))
    task = one('Engineering/Task light')
    specular.append((task, task.get_component_by_class(u.PointLightComponent)))
    if specular[-1][1] is None:
        raise RuntimeError('Engineering task light is no longer the expected point light')
    projections = [one('Lounge/Archive projection ' + str(i)) for i in (1, 2, 3)]
    for actor in projections:
        if 'OutpostRole:Hologram' not in map(str, actor.tags) or not actor.character_mesh:
            raise RuntimeError('Archive target is not the authored static hologram')

    receipt = {'candidate': 'Fixture-directed interior readability', 'lights': [],
        'anchors': anchor_records, 'specular_changes': [], 'archive_figures': [],
        'new_shadow_sources': 0, 'global_settings_changed': False,
        'map_saved': False, 'visual_validation': 'Pending native same-view capture'}
    for actor, component in specular:
        before = float(component.get_editor_property('specular_scale'))
        # Preserve diffuse flux; this bounded art control avoids bright hard
        # reflected flecks dominating the detailed metallic console bodies.
        after = min(before, .25)
        component.set_editor_property('specular_scale', after)
        receipt['specular_changes'].append({'actor': actor.get_actor_label(),
            'before': before, 'after': after, 'intensity_unchanged': True,
            'visibility_unchanged': True, 'orientation_unchanged': True})
    for row in rows:
        rect = actors.get(row['name'], [None])[0]
        created = rect is None
        position, target = u.Vector(*row['position']), u.Vector(*row['target'])
        rotation = u.MathLibrary.find_look_at_rotation(position, target)
        if created:
            rect = eas.spawn_actor_from_class(u.RectLight, position, rotation)
            rect.set_actor_label(row['name'])
            rect.set_folder_path('InteriorReadability')
            rect.tags = [u.Name(TAG), u.Name('OutpostAuthored')]
        else:
            rect.set_actor_location(position, False, False)
            rect.set_actor_rotation(rotation, False)
        light = rect.get_component_by_class(u.RectLightComponent)
        light.set_mobility(u.ComponentMobility.MOVABLE)
        light.set_intensity_units(u.LightUnits.LUMENS)
        light.set_intensity(row['lumens'])
        light.set_light_color(u.LinearColor(*row['color'], 1))
        light.set_attenuation_radius(row['radius_cm'])
        light.set_source_width(row['source_width_cm'])
        light.set_source_height(row['source_height_cm'])
        light.set_barn_door_angle(60)
        light.set_barn_door_length(15)
        light.set_cast_shadows(False)
        light.set_editor_property('specular_scale', .15)
        light.set_editor_property('volumetric_scattering_intensity', 0.)
        light.set_editor_property('indirect_lighting_intensity', .35)
        light.set_visibility(True, False)
        receipt['lights'].append(dict(row, created=created,
            rotation_pitch_yaw_roll=[rotation.pitch, rotation.yaw, rotation.roll]))

    # Low-opacity body and normal-dependent rims preserve the static figures'
    # form; the cycleable wardrobe keeps its existing cyan material/state.
    import OutpostHologramMaterial
    amber, archive_recipe = OutpostHologramMaterial.ensure(api)
    for actor in projections:
        component = actor.character_mesh
        for slot in range(component.get_num_materials()):
            component.set_material(slot, amber)
        receipt['archive_figures'].append(actor.get_actor_label())
    receipt['archive_material'] = archive_recipe
    receipt['active_new_rectlights'] = len(rows)
    return receipt
