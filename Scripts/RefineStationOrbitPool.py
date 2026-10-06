"""An authored ambient alien pool corner in the owner's L lounge.

The lead owns the guarded map transaction. Keep the native pool table, replace
only the agent's duplicate east sofa pocket, and retain the central walking
route. Animation and sequence authoring are separate measured helpers.
"""
from OutpostGeometryUtils import mesh_union
from RefineStationSocialFinish import _aisle


PREFIX = 'Refine/OrbitPool/'
POOL = '/Game/Rocket/MLR_PoolTable/SM_MLR_PoolTable'
GRAPHITE = '/Game/OutpostSandbox/Materials/M_OutpostGraphite'
TEXT = '/Game/OutpostSandbox/Materials/M_OutpostReadableTextOneSided'
FIXTURE = '/Game/CyberpunkRestaurant/Meshes/SM_Fluorescent_Light_01'
MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
CENTER = (4800., -3150., 0.)


def _one(actors, label):
    found = [a for a in actors if a.get_actor_label() == label]
    if len(found) != 1:
        raise RuntimeError('Expected one reviewed lounge actor: ' + label)
    return found[0]


def _position(actor):
    t = actor.get_actor_transform()
    return (*t.translation.to_tuple(), *t.rotation.to_tuple(), *t.scale3d.to_tuple())


def _mark_material(ctx, u, name, color):
    """Small polished ball surface with a restrained normal-dependent rim."""
    folder = '/Game/OutpostSandbox/StationRefinement/OrbitPool/Materials'
    path = folder + '/' + name
    if u.EditorAssetLibrary.does_asset_exist(path):
        raise RuntimeError('Pool material already exists; review before replay: ' + path)
    mat = u.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, u.Material, u.MaterialFactoryNew())
    edit = u.MaterialEditingLibrary
    edit.set_base_material_usage(mat, u.MaterialUsage.MATUSAGE_NANITE, True)
    assert edit.has_material_usage(mat, u.MaterialUsage.MATUSAGE_NANITE)
    tint = edit.create_material_expression(mat, u.MaterialExpressionVectorParameter)
    tint.set_editor_property('parameter_name', 'BallTint')
    tint.set_editor_property('default_value', u.LinearColor(*color, 1))
    assert edit.connect_material_property(tint, 'RGB', u.MaterialProperty.MP_BASE_COLOR)
    for value, prop in ((.22, u.MaterialProperty.MP_ROUGHNESS), (.25, u.MaterialProperty.MP_METALLIC)):
        scalar = edit.create_material_expression(mat, u.MaterialExpressionConstant)
        scalar.set_editor_property('r', value)
        assert edit.connect_material_property(scalar, '', prop)
    rim = edit.create_material_expression(mat, u.MaterialExpressionFresnel)
    rim.set_editor_property('base_reflect_fraction', .015)
    rim.set_editor_property('exponent', 5.)
    multiply = edit.create_material_expression(mat, u.MaterialExpressionMultiply)
    assert edit.connect_material_expressions(tint, 'RGB', multiply, 'A')
    assert edit.connect_material_expressions(rim, '', multiply, 'B')
    assert edit.connect_material_property(multiply, '', u.MaterialProperty.MP_EMISSIVE_COLOR)
    edit.recompile_material(mat)
    return mat


def _score_glass(u):
    folder='/Game/OutpostSandbox/StationRefinement/OrbitPool/Materials'
    name='M_OrbitScoreGlass'
    if u.EditorAssetLibrary.does_asset_exist(folder+'/'+name):
        raise RuntimeError('Orbit glass already exists; review before replay')
    mat=u.AssetToolsHelpers.get_asset_tools().create_asset(name,folder,u.Material,u.MaterialFactoryNew())
    mat.set_editor_property('blend_mode',u.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property('two_sided',True)
    edit=u.MaterialEditingLibrary
    color=edit.create_material_expression(mat,u.MaterialExpressionConstant3Vector)
    color.set_editor_property('constant',u.LinearColor(.025,.24,.40,1))
    assert edit.connect_material_property(color,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
    opacity=edit.create_material_expression(mat,u.MaterialExpressionConstant)
    opacity.set_editor_property('r',.45)
    assert edit.connect_material_property(opacity,'',u.MaterialProperty.MP_OPACITY)
    edit.recompile_material(mat)
    return mat


def prepare(ctx):
    """Place measured furnishings before the atmosphere and animation helpers."""
    import unreal as u
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name().split('.')[0] != MAP:
        raise RuntimeError('Orbit Pool belongs only to the separate owner preview')
    actors = list(ctx.actors)
    if any(a.get_actor_label().startswith(PREFIX) for a in actors):
        raise RuntimeError('Orbit Pool already exists; review before replay')
    protected = {a: _position(a) for a in actors}
    _aisle(world, u)
    retired = []
    prefixes = ('Refine/Social/Conversation 2/', 'Refine/SocialFollowup/Conversation 2/',
                'Refine/SocialFinish/Pocket 2/', 'Refine/SocialFinish/East planted divider/')
    for actor in actors:
        if actor.get_actor_label().startswith(prefixes) or actor.get_actor_label() == 'Crew/Lounge conversation B':
            ctx.hide(actor)
            retired.append(actor.get_actor_label())
    if not retired:
        raise RuntimeError('Expected the duplicate east conversation pocket')

    # Move the complete small dining assembly into its own window-side nook.
    # Keep original relative locations, yaw, support and materials unchanged.
    moved = []
    for actor in actors:
        label = actor.get_actor_label()
        if label.startswith('Refine/Social/Food/') and not label.endswith('/Drinks'):
            ctx.move(actor, actor.get_actor_location() + u.Vector(80, 940, 0))
            moved.append(actor.get_actor_label())
            protected.pop(actor)
    if len(moved) != 5:
        raise RuntimeError('Dining assembly changed; inspect before moving')
    food_light = _one(actors, 'Refine/Social/Lighting/Food')
    ctx.move(food_light, (5130, -2630, 300))
    protected.pop(food_light)

    table = ctx.grounded('OrbitPool/Table', POOL + '_Base_c1_Nanite', CENTER[:2], yaw=90)
    c, e = mesh_union(table)
    if max(abs(c.x-4800), abs(c.y+3150), abs(c.z-e.z)) > .05 or abs(e.y*2-256.8794) > .1:
        raise RuntimeError('Native table footprint changed')
    table.static_mesh_component.set_collision_profile_name('BlockAll')
    cue = ctx.raw('OrbitPool/Cue', POOL+'_CueStick_c1_Nanite', (4800, -3330, 100), collision=False)
    cue.static_mesh_component.set_mobility(u.ComponentMobility.MOVABLE)
    balls = []
    dirty = []
    for index, (name, color) in enumerate((('Ivory', (.82, .85, .75)),
                                         ('IonBlue', (.045, .40, .65)),
                                         ('SolarAmber', (.8, .28, .035)))):
        material = _mark_material(ctx, u, 'M_OrbitBall_'+name, color)
        dirty.append(material.get_path_name())
        ball = ctx.raw('OrbitPool/Ball '+name, POOL+'_Ball01_c1_Nanite', (4800+index*18, -3150, 83), collision=False)
        ball.static_mesh_component.set_mobility(u.ComponentMobility.MOVABLE)
        ball.static_mesh_component.set_material(0, material)
        balls.append(ball)
    # Genuine native cue rack, against the east wall, out of the playing area.
    rack = ctx.grounded('OrbitPool/Cue rack', POOL+'_CueRack_c1_Nanite', (5435, -3400), yaw=90)
    rc, re = mesh_union(rack)
    if rc.x+re.x > 5525 or rc.z-re.z < -.05:
        raise RuntimeError('Cue rack does not fit the existing east wall')

    # The table lamp is a detailed owned fixture with visible supports, not a
    # floating emissive bar. Two warm-white pools remain contained over the felt.
    lamp = ctx.raw('OrbitPool/Table pendant', FIXTURE, (4800, -3150, 300), rot=(0,90,0), collision=False)
    lc, le = mesh_union(lamp)
    scale = 230/(2*le.y)
    lamp.set_actor_scale3d(u.Vector(scale, scale, scale))
    lc, le = mesh_union(lamp)
    lamp.set_actor_location(lamp.get_actor_location()+u.Vector(4800,-3150,310)-lc, False, False)
    lc, le = mesh_union(lamp)
    roof = 397.56696
    for side in (-1, 1):
        ctx.box('OrbitPool/Pendant hanger '+str(side),
                (4800,-3150+side*80,(lc.z+le.z+roof)*.5),
                (1.5,1.5,roof-lc.z-le.z), GRAPHITE, False)
    light = ctx.eas.spawn_actor_from_class(u.RectLight, u.Vector(4800,-3150,lc.z-le.z-1), u.Rotator(pitch=-90))
    ctx.register(light, 'OrbitPool/Table key')
    key = light.get_component_by_class(u.RectLightComponent)
    key.set_mobility(u.ComponentMobility.MOVABLE)
    key.set_intensity_units(u.LightUnits.LUMENS)
    key.set_intensity(1800)
    key.set_attenuation_radius(480)
    key.set_source_width(210)
    key.set_source_height(25)
    key.set_cast_shadows(True)
    key.set_editor_property('use_temperature', True)
    key.set_editor_property('temperature', 4200)
    key.set_editor_property('specular_scale', .25)
    key.set_editor_property('volumetric_scattering_intensity', 0.)

    # Compact glass scoreboard on the east wall, clear of the entry sightline.
    # The field-return rule communicates why the balls levitate back each round.
    ctx.box('OrbitPool/Score console wall bracket', (5440,-3200,176), (26,8,8), GRAPHITE, False)
    ctx.box('OrbitPool/Score console projector', (5420,-3200,141), (10,112,8), GRAPHITE, False)
    glass=_score_glass(u);dirty.append(glass.get_path_name())
    pane=ctx.raw('OrbitPool/Score console glass','/Engine/BasicShapes/Plane',
                 (5416,-3200,183),rot=(90,0,0),scale=(.84,1.12,1),collision=False)
    pane.static_mesh_component.set_material(0,glass)
    for label, content, z, size, color in (
            ('Title','ORBIT POOL',211,15,(.62,.87,1.)),
            ('Teams','DRIFTERS    03\nIRON GUARD  02',180,10,(.92,.86,.65)),
            ('Rule','CAROM / FIELD RETURN',151,7,(.55,.78,.86))):
        actor = ctx.text('OrbitPool/Score console '+label, content, (5414,-3200,z), 180, size, color)
        actor.get_component_by_class(u.TextRenderComponent).set_text_material(ctx.asset(TEXT))

    # Native mechanical emitters sit on the wooden rails and explain the quiet
    # magnetic return. The detailed housings retain the kit's metal and lenses.
    for index,(x,y) in enumerate(((4733,-3250),(4867,-3250),(4733,-3050),(4867,-3050))):
        ctx.grounded('OrbitPool/Field return emitter '+str(index),
                     '/Game/Megastructure_Scifi_World/Meshes/Lamp/SM_lamp_small',
                     (x,y),floor=85.3,scale=(.35,.35,.35),collision=False)

    if any(_position(a) != p for a, p in protected.items()):
        raise RuntimeError('Orbit Pool moved a protected owner actor')
    _aisle(world, u)
    return {'table': table, 'cue': cue, 'balls': balls,
            'report': {'module':'orbit_pool_composition', 'dirty_assets': dirty,
                       'retired_duplicate_group': retired, 'moved_complete_dining_group': moved,
                       'native_table_center': list(c.to_tuple()), 'native_table_extent': list(e.to_tuple()),
                       'central_aisle_preserved': True, 'existing_architecture_preserved': True,
                       'pool_gameplay': 'Ambient scene only; no player minigame or interaction prompt'}}


def observer(ctx, label, mesh_path, clip_path, xy, yaw, height, phase=0):
    """Native compatible standing observer; final soles require rendered review."""
    import unreal as u
    mesh, clip = ctx.asset(mesh_path), ctx.asset(clip_path)
    if mesh.skeleton != clip.get_editor_property('skeleton'):
        raise RuntimeError('Observer clip uses a different skeleton: '+label)
    bounds = mesh.get_bounds()
    scale = height/(2*bounds.box_extent.z)
    actor = ctx.eas.spawn_actor_from_class(u.SkeletalMeshActor, u.Vector(xy[0],xy[1],0), u.Rotator(yaw=yaw))
    ctx.register(actor, 'OrbitPool/'+label)
    comp = actor.skeletal_mesh_component
    comp.set_skeletal_mesh_asset(mesh)
    comp.set_relative_scale3d(u.Vector(scale,scale,scale))
    comp.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
    data = comp.get_editor_property('animation_data')
    data.anim_to_play, data.saved_looping, data.saved_playing = clip, True, True
    data.saved_position = phase
    comp.set_editor_property('animation_data', data)
    comp.set_update_animation_in_editor(True)
    comp.play_animation(clip,True)
    comp.set_position(phase,False)
    actor.set_actor_location(u.Vector(xy[0],xy[1],(bounds.box_extent.z-bounds.origin.z)*scale),False,False)
    actor.set_actor_enable_collision(False)
    return actor
