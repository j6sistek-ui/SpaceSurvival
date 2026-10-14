"""Measured market composition on the saved Wayfarer map.

Keep original kit assemblies and actor identities. New seating reuses screened
covered cast and collidable furniture. No interaction, vending, import or save
is performed by this staging recipe; native visual/contact checks follow it.
"""
import hashlib
from pathlib import Path

MAP = '/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime'
PREFIX = 'Refine/MarketAtmosphere83/'
PRIVATE = '/Game/OutpostSandbox/StationRefinement/MarketAtmosphere83'
CREW = '/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew/'
CAMPAIGNS = ('M01_CosmicTacos', 'M02_MoonjarPantry', 'M03_AnchorSaucer',
             'M04_RelativelyGoodClocks', 'M05_RockSolidCompanions')


def apply(u, expected_sha256):
    global LAST_STATE
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    world = editor.get_editor_world()
    assert not editor.get_game_world() and world.get_path_name().split('.')[0] == MAP
    source = Path(u.Paths.project_content_dir()) / (MAP.removeprefix('/Game/') + '.umap')
    assert hashlib.sha256(source.read_bytes()).hexdigest() == expected_sha256
    assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    assert not u.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    sub = u.get_editor_subsystem(u.EditorActorSubsystem)
    actors = list(sub.get_all_level_actors())
    assert not any(a.get_actor_label().startswith(PREFIX) for a in actors)
    state = {'poses': [], 'hidden': [], 'crew': [], 'texts': [], 'materials': [],
             'lights': [], 'new': [], 'private': [], 'base_sha256': expected_sha256}
    LAST_STATE = state

    def one(label):
        rows = [a for a in actors if a.get_actor_label() == label]
        assert len(rows) == 1, label
        return rows[0]

    def keep(a):
        if not any(row[0] == a for row in state['poses']):
            state['poses'].append((a, a.get_actor_transform()))
        a.modify()
        return a

    def duplicate(label, donor):
        a = sub.duplicate_actor(one(donor), world)
        assert a
        a.set_actor_label(PREFIX + label)
        a.set_editor_property('tags', [u.Name('OutpostAuthored'), u.Name('OutpostLabel:' + PREFIX + label)])
        state['new'].append(a)
        return a

    def move(a, p, yaw=None):
        keep(a).set_actor_location(u.Vector(*p), False, True)
        if yaw is not None:
            a.set_actor_rotation(u.Rotator(yaw=yaw), False)

    groups = (('MarketNative/NorthCommerce/', -200.),
              ('MarketNative/SouthBotany/', 500.),
              ('MarketNative/SouthMachinery/', 450.),
              ('Refine/Market/Produce/', -200.),
              ('Refine/Market/Botany/', 500.),
              ('Refine/Market/Machinery/', 450.),
              ('Refine/Market/Nova/', -200.))
    counts = {}
    selected = [(a, dy) for prefix, dy in groups for a in actors if a.get_actor_label().startswith(prefix)]
    assert len({a.get_path_name() for a, _ in selected}) == len(selected)
    # An attached actor would inherit its parent's motion; reject before writes.
    assert all(a.get_attach_parent_actor() is None for a, _ in selected)
    for prefix, dy in groups:
        rows = [a for a in actors if a.get_actor_label().startswith(prefix)]
        assert rows, prefix
        counts[prefix] = len(rows)
        for a in rows:
            p = a.get_actor_location()
            move(a, (p.x, p.y + dy, p.z))

    blue = u.load_asset('/Game/OutpostSandbox/StationRefinement/Concept73/MI_WayfindingBlue')
    text_mat = u.load_asset('/Game/OutpostSandbox/StationRefinement/ArchiveConcept77/MI_LegibleHeaders')
    assert blue and text_mat
    for name, copy in (('Produce', 'SOL & SON<br>FRESH FROM MANY WORLDS'),
                       ('Botany', 'VERDANT ISLES<br>LIVING PLANTS / GROWING SUPPLIES'),
                       ('Machinery', 'KEL-TEC<br>PACKING / ROBOTICS / SERVICE'),
                       ('Nova', 'NOVA BITES<br>HOT FOOD / LONG JOURNEYS')):
        a = one('Refine/Market/' + name + '/Identity/Name')
        c = a.text_render
        state['texts'].append((c, c.text, c.world_size, c.get_material(0), c.text_render_color))
        c.modify(); c.set_text(copy); c.set_world_size(25.)
        c.set_text_render_color(u.Color(216, 232, 248, 255)); c.set_material(0, text_mat)
        backing = one('Refine/Market/' + name + '/Identity/Backing').static_mesh_component
        state['materials'].append((backing, list(backing.get_materials())))
        backing.modify(); backing.set_material(0, blue)
    for a in actors:
        if not a.get_actor_label().startswith('Refine/Market/'):
            continue
        c = a.get_component_by_class(u.PointLightComponent)
        if c:
            state['lights'].append((c, c.intensity, c.light_color))
            c.modify(); c.set_intensity(1000.); c.set_light_color(u.LinearColor(1., .77, .52))

    # Put vendor heads in open counter bays rather than behind plant columns.
    for label, p, yaw in (
        ('Crew/Trader A', (670., 1100., 85.), -90.),
        ('Crew/Trader B', (-1056.2098, 1103.27946, 85.), -90.),
        ('Crew/Botanist', (-780., -1165., 85.), 90.),
        ('Crew/Machinery attendant', (1510., -1005., 85.), 180.),
        ('Crew/Weighing shopper', (30., -600., 85.), -90.),
    ):
        move(one(label), p, yaw)

    courier = one('Crew/Market courier')
    state['crew'].append((courier, list(courier.route_points)))
    move(courier, (-100., 360., 85.), 0.)
    courier.set_editor_property('route_points', [u.Vector(*p) for p in
        ((0., 0., 0.), (1300., 0., 0.), (1300., -220., 0.), (0., -220., 0.))])

    # Covered existing cast replaces two old generic customers, preserving them
    # hidden for rollback. Compatible talk/listen clips carry the encounter.
    for label, donor, old, p, yaw, clipname in (
        ('Produce customer', 'Crew/Atrium patrol', 'Crew/Produce shopper',
         (690., 525., 85.), 90., 'Olive/A_Olive_Listen'),
        ('Botany customer', 'Crew/Atrium A', 'Crew/Buyer',
         (-820., -560., 85.), -90., 'Seer/A_Seer_Talk'),
    ):
        previous = one(old)
        state['hidden'].append((previous, previous.hidden, previous.get_actor_enable_collision()))
        previous.modify(); previous.set_actor_hidden_in_game(True); previous.set_actor_enable_collision(False)
        a = duplicate(label, donor)
        a.set_actor_location(u.Vector(*p), False, True); a.set_actor_rotation(u.Rotator(yaw=yaw), False)
        a.set_editor_property('route_points', []); a.set_editor_property('gesture_animations', [])
        clip = u.load_asset(CREW + clipname)
        assert clip and clip.get_editor_property('skeleton') == a.character_mesh.skeletal_mesh_asset.skeleton
        a.set_editor_property('idle_animation', clip)
        a.character_mesh.set_editor_property('animation_data', u.SingleAnimationPlayData(
            anim_to_play=clip, saved_looping=True, saved_playing=True))
        a.refresh_readability_lighting()

    # A pair at a table gives this entrance a social use beyond selling goods.
    # Clone proven chair/sole offsets, original animations and simple collision.
    translation = u.Vector(1810. - 3500., 1260. - 3000., 0.)
    for suffix in ('Table', 'South/Armchair', 'North/Armchair', 'Tablet', 'Reading', 'Water'):
        donor = 'Refine/ArchiveConcept77/Group 1/' + suffix
        a = duplicate('Table/' + suffix, donor)
        a.set_actor_location(one(donor).get_actor_location() + translation, False, True)
    for side, donor in (('South', 'Refine/ArchiveConcept77/Group 2/North/Visitor'),
                        ('North', 'Refine/ArchiveConcept77/Group 1/North/Visitor')):
        a = duplicate('Table/' + side + '/Visitor', donor)
        p = one(donor).get_actor_location()
        a.set_actor_location(u.Vector(1810., 1260. + (-126. if side == 'South' else 126.), p.z), False, True)
        a.set_actor_rotation(u.Rotator(yaw=90. if side == 'South' else -90.), False)
        a.set_editor_property('phase_offset', 1.4 if side == 'South' else 3.1)
        a.refresh_readability_lighting()
    for suffix in ('Planter', 'Tree', 'Understory'):
        donor = 'Refine/ArchiveConcept77/Greenery 4/' + suffix
        a = duplicate('Table/Greenery/' + suffix, donor)
        p, e = a.get_actor_bounds(False)
        a.set_actor_location(a.get_actor_location() + u.Vector(2160. - p.x, 1260. - p.y, 0.), False, True)

    return state, {'moved_groups': counts, 'new_actors': len(state['new']),
                   'screened_seated_cast': ['Tendril', 'Robe'],
                   'screened_customers': ['Olive', 'Seer'], 'map_saved': False,
                   'contacts_visibility_and_circulation': 'PENDING_NATIVE_REVIEW'}


def add_displays(u, state):
    """Private animated glass material, full-copy fit on upright owned hosts."""
    assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    edit = u.MaterialEditingLibrary
    tools = u.AssetToolsHelpers.get_asset_tools()
    sub = u.get_editor_subsystem(u.EditorActorSubsystem)
    actors = list(sub.get_all_level_actors())
    source_path = '/Game/OutpostSandbox/StationRefinement/CustomizationCampaigns20261008A/Materials/M_R_UprightFive'
    source = u.load_asset(source_path)
    assert source and not u.EditorAssetLibrary.does_asset_exist(PRIVATE + '/M_MarketGlassFive')
    master = tools.duplicate_asset('M_MarketGlassFive', PRIVATE, source)
    state['private'].append(master)
    custom = [n for n in edit.get_material_expressions(master) if isinstance(n, u.MaterialExpressionCustom)]
    assert len(custom) == 1
    code = str(custom[0].get_editor_property('code'))
    assert 'return lerp(a,b,alpha)*DisplayBrightness;' in code
    # Preserve complete aspect fit. The original R dimensions differ only by
    # 0.04 percent for two campaigns; replace them with exact market ratios.
    for i in (1, 2):
        start = code.index('float2 q' + str(i) + '=')
        end = code.index('\n', start)
        code = code[:start] + f'float2 q{i}=uv;' + code[end:]
    code = code.replace('return lerp(a,b,alpha)*DisplayBrightness;',
        'float3 art=lerp(a,b,alpha);\n'
        'float scan=.96+.04*sin((uv.y*201.0-Clock*8.0)*3.14159265);\n'
        'float edge=smoothstep(0.,.012,min(min(uv.x,1.-uv.x),min(uv.y,1.-uv.y)));\n'
        'float ink=saturate(max(max(art.r,art.g),art.b)*2.0);\n'
        'return float4(art*DisplayBrightness*scan,edge*(.18+.70*ink));')
    custom[0].set_editor_property('code', code)
    custom[0].set_editor_property('output_type', u.CustomMaterialOutputType.CMOT_FLOAT4)
    master.set_editor_property('blend_mode', u.BlendMode.BLEND_TRANSLUCENT)
    rgb = edit.create_material_expression(master, u.MaterialExpressionComponentMask, 400, 0)
    opacity = edit.create_material_expression(master, u.MaterialExpressionComponentMask, 400, 180)
    for node, values in ((rgb, (True, True, True, False)), (opacity, (False, False, False, True))):
        for key, value in zip(('r', 'g', 'b', 'a'), values): node.set_editor_property(key, value)
        assert edit.connect_material_expressions(custom[0], '', node, 'None')
    assert edit.connect_material_property(rgb, '', u.MaterialProperty.MP_EMISSIVE_COLOR)
    assert edit.connect_material_property(opacity, '', u.MaterialProperty.MP_OPACITY)
    edit.recompile_material(master)
    return place_prepared_displays(u, state, master)


def place_prepared_displays(u, state, master):
    """Complete placement after inspecting an interrupted private graph build."""
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    assert not editor.get_game_world() and editor.get_editor_world().get_path_name().split('.')[0] == MAP
    assert master in state['private'] and master.get_name() == 'M_MarketGlassFive'
    edit = u.MaterialEditingLibrary
    tools = u.AssetToolsHelpers.get_asset_tools()
    sub = u.get_editor_subsystem(u.EditorActorSubsystem)
    actors = list(sub.get_all_level_actors())
    assert not any(a.get_actor_label().startswith(PREFIX + 'Campaigns/') for a in actors)
    textures = [u.load_asset('/Game/OutpostSandbox/StationRefinement/MarketCampaigns20261008A/Textures/T_' + n) for n in CAMPAIGNS]
    assert all(isinstance(t, u.Texture2D) for t in textures)
    donors = {}
    for role, label in (('Frame', 'Refine/CustomizationCampaigns/West wall Frame'),
                         ('Pane', 'Refine/CustomizationCampaigns/West wall Pane')):
        matches = [a for a in actors if a.get_actor_label() == label]
        assert len(matches) == 1, label
        donors[role] = matches[0]
    for side, y, phase in (('North', 1850., 0.), ('South', -1850., 40.)):
        material = tools.create_asset('MI_Market' + side, PRIVATE, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
        state['private'].append(material); edit.set_material_instance_parent(material, master)
        for i, texture in enumerate(textures): edit.set_material_instance_texture_parameter_value(material, 'Artwork' + str(i), texture)
        for key, value in (('CycleSeconds', 20.), ('CrossfadeSeconds', .6), ('PhaseOffsetSeconds', phase), ('DisplayBrightness', 7.)):
            edit.set_material_instance_scalar_parameter_value(material, key, value)
        edit.update_material_instance(material)
        for role in ('Frame', 'Pane'):
            a = sub.duplicate_actor(donors[role], u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world())
            state['new'].append(a); a.set_actor_label(PREFIX + 'Campaigns/' + side + '/' + role)
            a.set_actor_location(u.Vector(2310., y, 0.), False, True)
            a.set_actor_rotation(u.Rotator(yaw=180.), False)
            a.set_actor_scale3d(u.Vector(1.25, 1.25, 1.25))
            a.set_editor_property('tags', [u.Name('OutpostAuthored')])
            if role == 'Pane': a.static_mesh_component.set_material(1, material)
    return {'private_materials': len(state['private']), 'campaign_count': 5,
            'upright_displays': 2, 'material_and_fit_review': 'PENDING'}


def rollback(u, state):
    """Only this staging state's retained actors/assets; never broad cleanup."""
    sub = u.get_editor_subsystem(u.EditorActorSubsystem)
    for a in reversed(state['new']): sub.destroy_actor(a)
    for c, values in reversed(state['materials']):
        for i, material in enumerate(values): c.set_material(i, material)
    for c, text, size, mat, color in reversed(state['texts']):
        c.set_text(text); c.set_world_size(size); c.set_material(0, mat); c.set_text_render_color(color)
    for c, intensity, color in reversed(state['lights']):
        c.set_intensity(intensity); c.set_editor_property('light_color', color)
    for a, hidden, collision in reversed(state['hidden']):
        a.set_actor_hidden_in_game(hidden); a.set_actor_enable_collision(collision)
    for a, route in reversed(state['crew']): a.set_editor_property('route_points', route)
    for a, transform in reversed(state['poses']): a.set_actor_transform(transform, False, True)
    return {'new_actors_removed': len(state['new']), 'source_poses_restored': len(state['poses']),
            'private_materials_retained_for_inspection': len(state['private']), 'map_saved': False}


def refine(u, state):
    """Repair observed candidate83 sightlines and lighting, not inferred finish."""
    assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    assert not u.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    sub = u.get_editor_subsystem(u.EditorActorSubsystem)
    actors = list(sub.get_all_level_actors())
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()

    def one(label):
        rows = [a for a in actors if a.get_actor_label() == label]
        assert len(rows) == 1, label
        return rows[0]

    def move(a, p):
        if not any(r[0] == a for r in state['poses']): state['poses'].append((a, a.get_actor_transform()))
        a.modify(); a.set_actor_location(u.Vector(*p), False, True)

    hidden = []
    for a in actors:
        label = a.get_actor_label()
        if label.startswith(('Refine/SocialFollowup/Market/', 'PromenadeKit/Waiting pocket/Complete waiting seat ')):
            state['hidden'].append((a, a.hidden, a.get_actor_enable_collision()))
            a.modify(); a.set_actor_hidden_in_game(True); a.set_actor_enable_collision(False)
            hidden.append(label)
        if label.startswith(PREFIX + 'Campaigns/'):
            a.modify(); a.set_actor_rotation(u.Rotator(yaw=0.), False)
    move(one('Crew/Botanist'), (-740., -705., 85.))
    # Move the actual fixture and its small local light together above the food
    # counter. The shared NPC-only light remains unchanged on each character.
    housing = one('Refine/Market/Nova/Task housing')
    p = housing.get_actor_location(); move(housing, (p.x, 1000., p.z))
    lamp = one('Refine/Market/Nova/Working light')
    move(lamp, (-1056.2098, 1000., 265.))
    lamp.point_light_component.set_intensity(2000.)

    edit = u.MaterialEditingLibrary
    assert not u.EditorAssetLibrary.does_asset_exist(PRIVATE + '/MI_StorefrontInk')
    material = u.AssetToolsHelpers.get_asset_tools().create_asset(
        'MI_StorefrontInk', PRIVATE, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
    edit.set_material_instance_parent(material, u.load_asset('/Game/OutpostSandbox/Materials/M_OutpostCyan'))
    edit.set_material_instance_vector_parameter_value(material, 'HullTint', u.LinearColor(.006, .023, .066, 1.))
    edit.update_material_instance(material); state['private'].append(material)
    for name in ('Produce', 'Botany', 'Machinery', 'Nova'):
        one('Refine/Market/' + name + '/Identity/Backing').static_mesh_component.set_material(0, material)

    a = sub.spawn_actor_from_class(u.StaticMeshActor, u.Vector())
    a.set_actor_label(PREFIX + 'Table/Light pole'); state['new'].append(a)
    c = a.static_mesh_component
    c.set_static_mesh(u.load_asset('/Game/CyberpunkRestaurant/Meshes/SM_Light_Pole_01'))
    c.set_collision_profile_name('NoCollision')
    s = 310. / (2. * c.static_mesh.get_bounds().box_extent.z)
    a.set_actor_scale3d(u.Vector(s, s, s))
    p, e = a.get_actor_bounds(False)
    a.set_actor_location(u.Vector(1620. - p.x, 1260. - p.y, -p.z + e.z), False, True)
    light = sub.duplicate_actor(one('Refine/Market/Nova/Working light'), world)
    light.set_actor_label(PREFIX + 'Table/Warm local light'); state['new'].append(light)
    light.set_actor_location(u.Vector(1650., 1260., 255.), False, True)
    c = light.point_light_component
    c.set_intensity(2400.); c.set_attenuation_radius(560.)
    c.set_light_color(u.LinearColor(1., .79, .56)); c.set_cast_shadows(False)
    c.set_specular_scale(.12); c.set_indirect_lighting_intensity(.1)
    return {'retired_redundant_signs_and_seat_parts': len(hidden), 'corrected_ad_faces': 2,
            'botanist_visible_forecourt': True, 'food_and_seating_local_lights': 2, 'map_saved': False}
