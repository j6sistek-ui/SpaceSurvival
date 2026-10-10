"""Stage central/R composition for whole-room review, without saving the map.

Reuses the owned furniture and original materials through private instances.
The lead owns the saved-map backup, matched native views and circulation check.
This is a placed-content pass; L, T, floor assets, crew rigs and gameplay stay intact.
"""
import hashlib
from pathlib import Path

MAP = '/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime'
PREFIX = 'Refine/WholeRooms20261009/'
PRIVATE = '/Game/OutpostSandbox/StationRefinement/WholeRooms20261009'
P3 = '/Game/P1toP5_Bundle/P3_ComputerStation/Meshes/'


def apply(u, expected_sha256):
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    world = editor.get_editor_world()
    assert not editor.get_game_world() and world.get_path_name().split('.')[0] == MAP
    file = Path(u.Paths.project_content_dir()) / (MAP.removeprefix('/Game/') + '.umap')
    assert hashlib.sha256(file.read_bytes()).hexdigest() == expected_sha256
    assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages(), 'Preserve unsaved work'
    assert not u.EditorLoadingAndSavingUtils.get_dirty_content_packages(), 'Preserve unsaved content'
    subsystem = u.get_editor_subsystem(u.EditorActorSubsystem)
    actors = list(subsystem.get_all_level_actors())
    assert not any(a.get_actor_label().startswith(PREFIX) for a in actors), 'Already staged; inspect instead of replaying'
    state = {'actors': [], 'new': [], 'lights': [], 'texts': [], 'materials': [], 'private': []}
    edit = u.MaterialEditingLibrary
    finishes = {}

    def one(label):
        found = [a for a in actors if a.get_actor_label() == label]
        if label.startswith('Wayfinding/'):
            found = [a for a in found if isinstance(a, u.TextRenderActor)]
        assert len(found) == 1, label
        return found[0]

    def keep(a):
        if not any(row[0] == a for row in state['actors']):
            state['actors'].append((a, a.get_actor_transform(), a.hidden, a.get_actor_enable_collision()))
            a.modify()
        return a

    def move(a, delta):
        keep(a).set_actor_location(a.get_actor_location() + u.Vector(*delta), False, True)

    def hide(a):
        keep(a).set_actor_hidden_in_game(True)
        a.set_actor_enable_collision(False)

    def text(a, copy, size=None, color=None):
        keep(a)
        c = a.text_render
        state['texts'].append((c, c.text, c.world_size, c.text_render_color))
        c.modify()
        c.set_text(copy)
        if size is not None:
            c.set_world_size(size)
        if color is not None:
            c.set_text_render_color(u.Color(*color))

    def light(a, intensity):
        keep(a)
        c = a.get_component_by_class(u.LightComponent)
        assert c
        state['lights'].append((c, c.intensity))
        c.modify()
        c.set_intensity(intensity)

    def named(a, label):
        state['new'].append(a)
        a.set_actor_label(PREFIX + label)
        a.set_editor_property('tags', [u.Name('OutpostAuthored'), u.Name('OutpostLabel:' + PREFIX + label)])
        return a

    def prop(label, path, center, height, yaw=0., collision=True, max_width=None):
        mesh = u.load_asset(path)
        assert isinstance(mesh, u.StaticMesh), path
        a = named(subsystem.spawn_actor_from_class(u.StaticMeshActor, u.Vector()), label)
        c = a.static_mesh_component
        c.set_static_mesh(mesh)
        c.set_collision_profile_name('BlockAll' if collision else 'NoCollision')
        b = mesh.get_bounds()
        scale = height / (b.box_extent.z * 2.)
        if max_width is not None:
            scale = min(scale, max_width / (max(b.box_extent.x, b.box_extent.y) * 2.))
        a.set_actor_scale3d(u.Vector(scale, scale, scale))
        a.set_actor_rotation(u.Rotator(yaw=yaw), False)
        p, e = a.get_actor_bounds(False)
        a.set_actor_location(u.Vector(center[0]-p.x, center[1]-p.y, center[2]-p.z+e.z), False, True)
        return a

    def storage(label, center, scale, yaw):
        # These two kit parts share one assembly pivot. Align the body once,
        # then apply its exact transform to the matching drawer assembly.
        body = prop(label+'/Body', P3+'SM_Storage3000Series_V1_Part1', center, 127.985663*scale, yaw)
        drawer = named(subsystem.spawn_actor_from_class(u.StaticMeshActor, u.Vector()), label+'/Drawers')
        drawer.static_mesh_component.set_static_mesh(u.load_asset(P3+'SM_Storage3000Series_V1_Part2'))
        drawer.static_mesh_component.set_collision_profile_name('BlockAll')
        drawer.set_actor_transform(body.get_actor_transform(), False, True)
        return body, drawer

    def finish(c):
        state['materials'].append((c, list(c.get_materials())))
        c.modify()
        for slot, parent in enumerate(c.get_materials()):
            if not isinstance(parent, u.MaterialInstanceConstant):
                continue
            scalars = set(map(str, edit.get_scalar_parameter_names(parent)))
            if 'Min Roughness' not in scalars:
                continue
            key = parent.get_path_name()
            if key not in finishes:
                name = 'MI_ArchiveSatin_' + hashlib.sha256(key.encode()).hexdigest()[:10]
                path = PRIVATE + '/' + name
                child = u.load_asset(path) if u.EditorAssetLibrary.does_asset_exist(path) else None
                if child:
                    assert isinstance(child, u.MaterialInstanceConstant) and child.parent == parent, path
                else:
                    child = u.AssetToolsHelpers.get_asset_tools().create_asset(name, PRIVATE,
                        u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
                    assert child
                    edit.set_material_instance_parent(child, parent)
                state['private'].append(child)
                for suffix in ('', ' Cov1', ' Cov2'):
                    for parameter, value in (('Min Roughness', .48), ('Max Roughness', .82),
                                             ('Specular Intensity', .3), ('Metalness Intensity', .55)):
                        if parameter+suffix in scalars:
                            edit.set_material_instance_scalar_parameter_value(child, parameter+suffix, value)
                # Preserve original maps, normal detail, accents and emissive controls.
                edit.update_material_instance(child)
                finishes[key] = child
            c.set_material(slot, finishes[key])

    try:
        # Compress each reading group around its real low table, leaving the
        # central entrance-to-wardrobe path and the display approaches open.
        for number, old_y, new_y in ((1, 2870., 2920.), (2, 3710., 3860.)):
            base = 'LoungeNative/Conversation '+str(number)
            for side, offset in (('South', -130.), ('North', 130.)):
                for part in (1, 2, 3):
                    a = one(base+'/'+side+'/SM_TitaniumIndustrySeat_V1_Part'+str(part))
                    p = a.get_actor_location()
                    move(a, (0., new_y+offset-p.y, 0.))
                    finish(a.static_mesh_component)
            for suffix in ('Low game table', 'Owned light housing', 'Task light', 'Fixture suspension'):
                move(one(base+'/'+suffix), (0., new_y-old_y, 0.))
            for role in ('Tablet', 'Catalog'):
                move(one('Refine/StationFinish20261009/Archive/'+role+(' A' if number == 1 else ' B')),
                     (0., new_y-old_y, 0.))

        # Give the existing consultation pair a supported, clearly identifiable
        # work station instead of placing two figures in the middle of the floor.
        desk = prop('R/Consultation desk', '/Game/P1toP5_Bundle/P1_WorkStation/Meshes/SM_GoliathTable02',
                    (4200., 3400., 0.), 96., 0.)
        for label, p, yaw in (('Refine/Archive/Conversation guest A', (4200., 3570., 85.), -90.),
                              ('Refine/Archive/Conversation guest B', (4200., 3230., 85.), 90.)):
            a = keep(one(label))
            a.set_actor_location(u.Vector(*p), False, True)
            a.set_actor_rotation(u.Rotator(yaw=yaw), False)
        prop('R/Consultation tablet', '/Game/Cyberpunk_Room/Mesh/SM_Tablet', (4165., 3400., 96.), 3., -90., False, 30.)
        prop('R/Consultation records', '/Game/Cyberpunk_Room/Mesh/SM_Paper_Pile_01', (4240., 3400., 96.), 2., 15., False, 22.)
        plaque = named(subsystem.duplicate_actor(one('Services/CREW WARDROBE/Face'), world), 'R/Consultation label')
        plaque.set_actor_location(u.Vector(4200., 3350., 77.), False, True)
        plaque.set_actor_rotation(u.Rotator(yaw=-90.), False)
        plaque.text_render.set_text('WARDROBE HELP')
        plaque.text_render.set_world_size(11.)
        plaque.text_render.set_text_render_color(u.Color(178,226,237,255))

        for label, p, scale, yaw in (('R/Archive storage', (3800., 4340., 0.), 1., 0.),
                                    ('Reception/Records storage', (4330., 0., 0.), .7, -90.)):
            for a in storage(label, p, scale, yaw):
                finish(a.static_mesh_component)

        # The wardrobe and waiting groups now own the light hierarchy. Remove
        # redundant legacy arcade/seating floods left from the earlier lounge.
        for label, value in (('Lounge/Arcade key', 0.), ('Lounge/Conversation pool', 450.),
                             ('Lounge/East seating pool', 450.), ('InteriorReadability/Arcade cabinets', 0.),
                             ('UsableLighting/Lounge/Ceiling 1', 1000.), ('UsableLighting/Lounge/Ceiling 2', 1000.)):
            light(one(label), value)
        for a in actors:
            if a.get_actor_label() == 'Lounge/Ceiling pool':
                light(a, 300.)
        reception_light = one('Refine/CentralWelcomeGreeneryLights1/ReceptionFront')
        light(reception_light, 1600.)
        reception_light.set_actor_location(u.Vector(3510., 0., 410.), False, True)
        reception_light.set_actor_rotation(u.MathLibrary.find_look_at_rotation(
            u.Vector(3510., 0., 410.), u.Vector(4100., 0., 125.)), False)

        # Four readable regional signs replace seven competing generic labels.
        # Existing directory/flight boards remain the detailed instructions.
        for number in (3, 5, 7):
            for suffix in ('Frame', 'Glass', 'Backing', 'Title'):
                hide(one('Refine/Reception/Direction '+str(number)+'/'+suffix))
        for number, copy in ((1, 'OPERATIONS<br>SHIP LOADOUT'), (2, 'CREW ARCHIVE<br>CHARACTER WARDROBE'),
                             (4, 'MARKET<br>DEPARTURES'), (6, 'SOCIAL LOUNGE<br>BAR / ARCADE')):
            text(one('Refine/Reception/Direction '+str(number)+'/Title'), copy, 14., (180,226,237,255))
        text(one('Wayfinding/ENGINEERING'), 'SOCIAL LOUNGE', 26., (214,211,178,255))
        text(one('Wayfinding/CREW LOUNGE'), 'CREW ARCHIVE  /  WARDROBE', 24., (180,226,237,255))
        text(one('Lounge/Archive title'), 'CHARACTER WARDROBE', 24.)
        text(one('Refine/Archive/Identity'), 'CREW ARCHIVE', 30.)
        for number, heading, subheading in (
            (1, 'OPERATIONS', 'SHIP LOADOUT / UPGRADES'),
            (2, 'CREW ARCHIVE', 'CHOOSE YOUR CHARACTER'),
            (3, 'CREW ARCHIVE', 'WARDROBE / INFORMATION'),
            (4, 'MARKET', 'LOCAL VENDORS / SERVICES'),
            (5, 'DEPARTURES', 'RETURN TO YOUR SHIP'),
            (6, 'SOCIAL LOUNGE', 'BAR / POOL / ARCADE'),
            (7, 'SOCIAL LOUNGE', 'TAKE A BREAK BETWEEN FLIGHTS'),
            (8, 'OPERATIONS', 'SHIP LOADOUT / PILOT RECORDS')):
            prefix = 'AtriumDetail/Wall service '+str(number).zfill(2)+'/Information screen/'
            text(one(prefix+'Heading'), heading)
            text(one(prefix+'Subheading'), subheading)
        return state
    except Exception:
        rollback(u, state)
        raise


def rollback(u, state):
    changed_materials = set()
    for material, parameter, value in reversed(state.get('vectors', [])):
        u.MaterialEditingLibrary.set_material_instance_vector_parameter_value(material, parameter, value)
        changed_materials.add(material)
    for material in changed_materials:
        u.MaterialEditingLibrary.update_material_instance(material)
    for c, materials in reversed(state['materials']):
        for index, material in enumerate(materials):
            c.set_material(index, material)
    for c, copy, size, color in reversed(state['texts']):
        c.set_text(copy)
        c.set_world_size(size)
        c.set_text_render_color(color)
    for c, intensity in reversed(state['lights']):
        c.set_intensity(intensity)
    for a in reversed(state['new']):
        u.get_editor_subsystem(u.EditorActorSubsystem).destroy_actor(a)
    for a, transform, hidden, collision in reversed(state['actors']):
        a.set_actor_transform(transform, False, True)
        a.set_actor_hidden_in_game(hidden)
        a.set_actor_enable_collision(collision)


def refine_grouping(u, expected_sha256):
    """Second bounded pass after the saved first whole-room comparison.

    Keep the entrance axis clear and group the reading/consultation zone.
    Returns changed objects for the lead's save and native review; never saves.
    """
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    world = editor.get_editor_world()
    assert not editor.get_game_world() and world.get_path_name().split('.')[0] == MAP
    file = Path(u.Paths.project_content_dir()) / (MAP.removeprefix('/Game/') + '.umap')
    assert hashlib.sha256(file.read_bytes()).hexdigest() == expected_sha256
    assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    assert not u.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    subsystem = u.get_editor_subsystem(u.EditorActorSubsystem)
    actors = list(subsystem.get_all_level_actors())
    assert not any(a.get_actor_label().startswith(PREFIX+'R/Waiting greenery') for a in actors)
    state = {'actors': [], 'new': [], 'lights': [], 'texts': [], 'materials': [], 'private': [], 'vectors': []}

    def one(label):
        found = [a for a in actors if a.get_actor_label() == label]
        assert len(found) == 1, label
        return found[0]

    def keep(a):
        state['actors'].append((a, a.get_actor_transform(), a.hidden, a.get_actor_enable_collision()))
        a.modify()
        return a

    try:
        for label in ('R/Consultation desk', 'R/Consultation tablet', 'R/Consultation records', 'R/Consultation label'):
            a = keep(one(PREFIX+label))
            a.set_actor_location(a.get_actor_location()+u.Vector(-320., 80., 0.), False, True)
        for label in ('Refine/Archive/Conversation guest A', 'Refine/Archive/Conversation guest B'):
            a = keep(one(label))
            a.set_actor_location(a.get_actor_location()+u.Vector(-320., 80., 0.), False, True)

        planter = one('Refine/CentralWelcomeArrival2/NE/Planter left')
        foliage = one('Refine/CentralWelcomeGreeneryLights1/Foliage 1')
        foliage_delta = foliage.get_actor_location()-planter.get_actor_location()
        for number, position in ((1, (3660., 3160., 0.)), (2, (3660., 3650., 0.))):
            for kind, source, p in (('Planter', planter, u.Vector(*position)),
                                     ('Foliage', foliage, u.Vector(*position)+foliage_delta)):
                a = subsystem.duplicate_actor(source, world)
                state['new'].append(a)
                label = PREFIX+'R/Waiting greenery '+str(number)+'/'+kind
                a.set_actor_label(label)
                a.set_editor_property('tags', [u.Name('OutpostAuthored'), u.Name('OutpostLabel:'+label)])
                a.set_actor_location(p, False, True)
                a.set_actor_hidden_in_game(False)

        for number, copy in ((1, 'OPERATIONS<br>SHIP LOADOUT'), (2, 'CREW ARCHIVE<br>WARDROBE'),
                             (4, 'MARKET<br>DEPARTURES'), (6, 'SOCIAL LOUNGE<br>BAR / ARCADE')):
            c = one('Refine/Reception/Direction '+str(number)+'/Title').text_render
            state['texts'].append((c, c.text, c.world_size, c.text_render_color))
            c.modify()
            c.set_text(copy)
            c.set_world_size(26.)

        # All original surface detail and masks stay inherited. Darker paint
        # gives the original mechanical chairs contrast against the white floor.
        edit = u.MaterialEditingLibrary
        for path in u.EditorAssetLibrary.list_assets(PRIVATE, recursive=False, include_folder=False):
            m = u.load_asset(path)
            if not isinstance(m, u.MaterialInstanceConstant):
                continue
            assert m.get_name().startswith('MI_ArchiveSatin_')
            vectors = set(map(str, edit.get_vector_parameter_names(m)))
            for parameter in ('Albedo Tint', 'Albedo Tint Cov1', 'Albedo Tint Cov2'):
                if parameter in vectors:
                    state['vectors'].append((m, parameter, edit.get_material_instance_vector_parameter_value(m, parameter)))
                    original = edit.get_material_instance_vector_parameter_value(m.parent, parameter)
                    edit.set_material_instance_vector_parameter_value(m, parameter,
                        u.LinearColor(original.r*.26, original.g*.40, original.b*.46, original.a))
            edit.update_material_instance(m)
            state['private'].append(m)
        return state
    except Exception:
        rollback(u, state)
        raise
