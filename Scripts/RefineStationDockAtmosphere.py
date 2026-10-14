"""Stage dock workers on the existing saved Wayfarer equipment and clearways.

Run once after baseline inspection, with Play stopped and an exact map digest.
Only private carry derivatives are authored. The lead owns saves, rendered
review, route checks and reload verification; source cast/clips remain intact.
"""
import hashlib
from pathlib import Path

MAP = '/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime'
PREFIX = 'Refine/DockAtmosphere87/'
PRIVATE = '/Game/OutpostSandbox/StationRefinement/DockAtmosphere87'
CREW = '/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew/'


def carry_clips(u):
    lib = u.EditorAssetLibrary
    outputs = [PRIVATE + '/A_Crest_CarryInPlace', PRIVATE + '/A_Crest_HoldCase']
    assert not any(lib.does_asset_exist(p) for p in outputs), 'Inspect adopted derivatives instead of reapplying'
    source = u.load_asset(CREW + 'Crest/Role/A_Crest_Crew_CarryBoxWalk_Medium')
    idle = u.load_asset(CREW + 'Crest/Role/A_Crest_Crew_Worker_Idle')
    assert source and idle and source.get_editor_property('skeleton') == idle.get_editor_property('skeleton')
    walk = lib.duplicate_asset(source.get_path_name().split('.')[0], outputs[0])
    hold = lib.duplicate_asset(idle.get_path_name().split('.')[0], outputs[1])
    assert walk and hold
    model = source.get_editor_property('data_model_interface')
    keys = model.get_number_of_keys()
    roots = [u.AnimationLibrary.get_bone_pose_for_time(source, 'root', source.sequence_length*i/(keys-1), False)
             for i in range(keys)]
    distance = (roots[-1].translation-roots[0].translation).length()
    c = walk.get_editor_property('controller')
    c.open_bracket('Keep source carry gait in place for swept ambient route', False)
    try:
        assert c.set_bone_track_keys('root',
            [u.Vector(roots[0].translation.x, roots[0].translation.y, t.translation.z) for t in roots],
            [t.rotation for t in roots], [t.scale3d for t in roots], False)
    finally:
        c.close_bracket(False)
    # Retain grounded breathing legs/pelvis; use the same carrying upper body
    # while stopped so the case never switches to an arms-down idle.
    hold_keys = hold.get_editor_property('data_model_interface').get_number_of_keys()
    upper = [b for b in model.get_bone_track_names() if str(b).startswith(
        ('spine_', 'clavicle_', 'upperarm_', 'lowerarm_', 'hand_',
         'thumb_', 'index_', 'middle_', 'ring_', 'pinky_'))]
    assert len(upper) >= 30
    c = hold.get_editor_property('controller')
    c.open_bracket('Carry-compatible upper body over existing grounded idle', False)
    try:
        for bone in upper:
            t = u.AnimationLibrary.get_bone_pose_for_time(source, bone, 0., False)
            assert c.set_bone_track_keys(bone, [t.translation]*hold_keys,
                                         [t.rotation]*hold_keys, [t.scale3d]*hold_keys, False)
    finally:
        c.close_bracket(False)
    return walk, hold, distance / source.sequence_length


def apply(u, expected_sha256):
    global LAST_STATE
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    world = editor.get_editor_world()
    assert not editor.get_game_world() and world.get_path_name().split('.')[0] == MAP
    file = Path(u.Paths.project_content_dir()) / (MAP.removeprefix('/Game/') + '.umap')
    assert hashlib.sha256(file.read_bytes()).hexdigest() == expected_sha256
    assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    assert not u.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    sub = u.get_editor_subsystem(u.EditorActorSubsystem)
    actors = list(sub.get_all_level_actors())
    assert not any(a.get_actor_label().startswith(PREFIX) for a in actors)
    state = {'new': [], 'private': [], 'existing': [], 'base_sha256': expected_sha256}
    LAST_STATE = state

    def one(label):
        found = [a for a in actors if a.get_actor_label() == label]
        assert len(found) == 1, label
        return found[0]

    def dup(name, donor):
        a = sub.duplicate_actor(one(donor), world)
        assert a
        a.set_actor_label(PREFIX + name)
        a.set_editor_property('tags', [u.Name('OutpostAuthored'), u.Name('OutpostLabel:' + PREFIX + name)])
        state['new'].append(a)
        return a

    def worker(name, donor, pos, yaw, clip=None, route=()):
        a = dup(name, donor)
        a.set_actor_location(u.Vector(*pos), False, True)
        a.set_actor_rotation(u.Rotator(yaw=yaw), False)
        a.set_editor_property('route_points', [u.Vector(*p) for p in route])
        a.set_editor_property('gesture_animations', [])
        a.set_editor_property('phase_offset', len(state['new'])*.73)
        a.set_actor_hidden_in_game(False)
        a.set_actor_enable_collision(True)
        c = a.character_mesh
        c.set_editor_property('visibility_based_anim_tick_option',
                              u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
        if clip:
            assert clip.get_editor_property('skeleton') == c.skeletal_mesh_asset.skeleton
            a.set_editor_property('idle_animation', clip)
            c.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
            c.set_editor_property('animation_data', u.SingleAnimationPlayData(
                anim_to_play=clip, saved_looping=True, saved_playing=True))
        a.refresh_readability_lighting()
        return a

    # Existing terminals/ships and all physical deck/bridge surfaces stay put.
    # These stations already have supported owned power cores, tools and cases.
    work = u.load_asset(CREW + 'Warden/Role/A_Warden_Crew_FuseBox_Swich_On')
    assert work
    for name, pos, phase in (('Finish technician', (-2262., -1842., 85.), .7),
                             ('Outer technician', (-5912., 1738., 85.), 1.6)):
        a = worker(name, 'Crew/Machinery attendant', pos, 180., work)
        a.set_editor_property('phase_offset', phase)
    worker('Maintenance colleague', 'Crew/Trader B', (-5910., 1920., 85.), -110.,
           u.load_asset(CREW + 'Glyph/A_Glyph_Talk'))
    guard = worker('Dock security patrol', 'Crew/Atrium patrol', (-1550., -980., 85.), 0., route=(
        (0., 0., 0.), (0., 570., 0.), (-430., 570., 0.), (-430., 0., 0.)))
    guard.set_editor_property('travel_speed', 85.)
    guard.set_editor_property('pause_at_waypoint', 4.)
    worker('North security', 'Crew/Atrium patrol', (-1800., 1080., 85.), 20.)
    worker('Cargo coordinator', 'Crew/Atrium A', (-1460., -4460., 85.), -125.,
           u.load_asset(CREW + 'Seer/A_Seer_Talk'))

    walk, hold, speed = carry_clips(u)
    state['private'] += [walk, hold]
    carrier = worker('Case carrier', 'Crew/Market courier', (-3300., -1950., 85.), 0., hold, (
        (0., 0., 0.), (750., 0., 0.), (750., -350., 0.), (0., -350., 0.)))
    carrier.set_editor_property('walk_animation', walk)
    carrier.set_editor_property('travel_speed', speed)
    carrier.set_editor_property('pause_at_waypoint', 2.)

    # Bind the rigid case to the pelvis, which the source hands track closely.
    # Relative transform is computed from the actual compatible carrying pose.
    box = dup('Carried service case', 'BerthDetail/Finish service/Ground equipment case')
    c = box.static_mesh_component
    c.set_mobility(u.ComponentMobility.MOVABLE)
    c.set_collision_profile_name('NoCollision')
    mesh = carrier.character_mesh.skeletal_mesh_asset
    pose = u.AnimPoseExtensions.get_anim_pose_at_time(walk, 0.,
        u.AnimPoseEvaluationOptions(optional_skeletal_mesh=mesh, evaluation_type=u.AnimDataEvalType.RAW))
    pelvis = u.AnimPoseExtensions.get_bone_pose(pose, 'pelvis', u.AnimPoseSpaces.WORLD)
    b = c.static_mesh.get_bounds()
    scale = u.Vector(1., 1., 1.)
    origin = u.Vector(0., 27., 111.) - b.origin
    relative = u.MathLibrary.make_relative_transform(u.Transform(location=origin, scale=scale), pelvis)
    assert box.attach_to_component(carrier.character_mesh, 'pelvis', u.AttachmentRule.KEEP_RELATIVE,
        u.AttachmentRule.KEEP_RELATIVE, u.AttachmentRule.KEEP_RELATIVE, False)
    box.root_component.set_relative_transform(relative, False, True)

    # Workbench task lights have visible owned fixtures and small local reach.
    for name, x, y in (('Finish', -2350., -1880.), ('Outer', -6000., 1700.),
                       ('Cargo', -1580., -4570.), ('Flanker', -1580., 4570.)):
        a = dup(name + '/Task fixture', 'Refine/MarketAtmosphere83/Table/Light pole')
        p, e = a.get_actor_bounds(False)
        a.set_actor_location(a.get_actor_location() + u.Vector(x-65.-p.x, y+165.-p.y, -p.z+e.z), False, True)
        light = dup(name + '/Task light', 'Refine/MarketAtmosphere83/Table/Warm local light')
        light.set_actor_location(u.Vector(x+35., y, 230.), False, True)
        c = light.point_light_component
        c.set_intensity(2100.)
        c.set_attenuation_radius(440.)
        c.set_light_color(u.LinearColor(.7, .84, 1.))

    return state, {'new_actors': len(state['new']), 'new_crew': 7,
        'carrier_speed_cm_s': speed, 'private_clips': [a.get_path_name() for a in state['private']],
        'source_preserved': True, 'map_saved': False, 'runtime_contacts_routes_visibility': 'PENDING'}


def refine(u, state):
    """Repair the measured first candidate; do not restage existing workers."""
    assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    actors = list(u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors())

    def one(label):
        rows = [a for a in actors if a.get_actor_label() == label]
        assert len(rows) == 1, label
        return rows[0]

    def move(a, p, yaw):
        a.modify()
        a.set_actor_location(u.Vector(*p), False, True)
        a.set_actor_rotation(u.Rotator(yaw=yaw), False)

    # Two existing small generic pilots become covered conversation partners.
    # Actor identities and asset sources remain; no new gameplay/interaction.
    for label, donor, pos, yaw, clip in (
        ('Crew/Pilot berth02', 'Crew/Trader B', (-1485., -4685., 85.), 90.,
         CREW + 'Glyph/A_Glyph_Listen'),
        ('Crew/Pilot berth03', 'Crew/Trader A', (-1615., 1070., 85.), 180.,
         CREW + 'Robe/A_Robe_Talk')):
        a, source = one(label), one(donor)
        c = a.character_mesh
        state['existing'].append({'actor': a, 'transform': a.get_actor_transform(),
            'mesh': c.skeletal_mesh_asset, 'relative': c.get_relative_transform(),
            'materials': list(c.get_editor_property('override_materials')),
            'idle': a.idle_animation, 'walk': a.walk_animation,
            'gestures': list(a.gesture_animations), 'route': list(a.route_points),
            'animation_data': c.animation_data})
        a.modify(); c.modify()
        c.set_skeletal_mesh_asset(source.character_mesh.skeletal_mesh_asset)
        c.set_relative_transform(source.character_mesh.get_relative_transform(), False, True)
        c.set_editor_property('override_materials', [])
        idle = u.load_asset(clip)
        assert idle and idle.get_editor_property('skeleton') == c.skeletal_mesh_asset.skeleton
        a.set_editor_property('idle_animation', idle)
        a.set_editor_property('walk_animation', source.walk_animation)
        a.set_editor_property('gesture_animations', [])
        a.set_editor_property('route_points', [])
        c.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
        c.set_editor_property('animation_data', u.SingleAnimationPlayData(
            anim_to_play=idle, saved_looping=True, saved_playing=True))
        c.set_editor_property('visibility_based_anim_tick_option',
                              u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
        move(a, pos, yaw)
    move(one(PREFIX + 'Cargo coordinator'), (-1485., -4475., 85.), -90.)
    move(one(PREFIX + 'North security'), (-1800., 1080., 85.), 0.)
    for a in actors:
        if isinstance(a, u.SSOutpostAmbientActor) and (
                a.get_actor_label().startswith(PREFIX) or a.get_actor_label() in
                ('Crew/Pilot berth02', 'Crew/Pilot berth03')):
            a.modify()
            a.set_editor_property('head_fill_lumens', 80.)
            a.set_editor_property('head_fill_radius', 110.)
            a.refresh_readability_lighting()
    for name, z in (('Case carrier', -82.), ('Finish technician', -83.5),
                     ('Outer technician', -83.5)):
        c = one(PREFIX + name).character_mesh
        c.modify(); p = c.relative_location
        c.set_relative_location(u.Vector(p.x, p.y, z), False, True)
    return {'existing_pilots_reassigned': 2, 'purposeful_groups': 3,
            'dock_head_fill': '80lm/110cm NPC-only; zero specular/GI/reflection/shadows',
            'sole_offset_repairs_cm': {'carrier': 3., 'technicians': 1.5}, 'map_saved': False}


def ground_technicians(u, state):
    """Keep one supporting toe near deck throughout the measured work loop."""
    assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    output = PRIVATE + '/A_Warden_ServiceGrounded'
    assert not u.EditorAssetLibrary.does_asset_exist(output)
    mesh = u.load_asset(CREW + 'Warden/Mesh/SK_Warden')
    source = u.load_asset(CREW + 'Warden/Role/A_Warden_Crew_FuseBox_Swich_On')
    options = u.AnimPoseEvaluationOptions(optional_skeletal_mesh=mesh, evaluation_type=u.AnimDataEvalType.RAW)
    count = source.get_editor_property('data_model_interface').get_number_of_keys()
    roots, offsets = [], []
    for i in range(count):
        t = source.sequence_length*i/(count-1)
        pose = u.AnimPoseExtensions.get_anim_pose_at_time(source, t, options)
        toe = min(u.AnimPoseExtensions.get_bone_pose(pose, b, u.AnimPoseSpaces.WORLD).translation.z
                  for b in ('ball_l', 'ball_r'))
        tr = u.AnimationLibrary.get_bone_pose_for_time(source, 'root', t, False)
        # Placed component already includes the measured +1.5cm sole offset.
        offsets.append(-toe)
        tr.translation = tr.translation + u.Vector(0., 0., -toe)
        roots.append(tr)
    clip = u.EditorAssetLibrary.duplicate_asset(source.get_path_name().split('.')[0], output)
    assert clip
    state['private'].append(clip)
    controller = clip.get_editor_property('controller')
    controller.open_bracket('Retain a supporting foot through the service loop', False)
    try:
        assert controller.set_bone_track_keys('root', [t.translation for t in roots],
            [t.rotation for t in roots], [t.scale3d for t in roots], False)
    finally:
        controller.close_bracket(False)
    clip.set_editor_property('rate_scale', .65)
    for actor in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        if actor.get_actor_label() in (PREFIX+'Finish technician', PREFIX+'Outer technician'):
            actor.modify(); actor.character_mesh.modify()
            actor.set_editor_property('idle_animation', clip)
            actor.character_mesh.set_editor_property('animation_data', u.SingleAnimationPlayData(
                anim_to_play=clip, saved_looping=True, saved_playing=True))
    return {'private_clip': clip.get_path_name(), 'keys': count,
            'root_z_offsets_cm': [min(offsets), max(offsets)],
            'supporting_toe_target_world_z_cm': 1.5, 'rate_scale': .65,
            'skin_contact_and_interpolation': 'NATIVE_REVIEW_PENDING'}


def standing_technicians(u, state):
    """Keep the proven standing legs while the upper body services the core.

    Revision89's toe markers stayed grounded but the visible kneeling boot pose
    still looked suspended. Preserve that rejected derivative as evidence.
    """
    assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    output = PRIVATE + '/A_Warden_ServiceStanding'
    assert not u.EditorAssetLibrary.does_asset_exist(output)
    source = u.load_asset(CREW + 'Warden/Role/A_Warden_Crew_FuseBox_Swich_On')
    idle = u.load_asset(CREW + 'Warden/Role/A_Warden_Crew_Worker_Idle')
    clip = u.EditorAssetLibrary.duplicate_asset(source.get_path_name().split('.')[0], output)
    assert clip and source.get_editor_property('skeleton') == idle.get_editor_property('skeleton')
    state['private'].append(clip)
    model = clip.get_editor_property('data_model_interface')
    keys = model.get_number_of_keys()
    lower = [b for b in model.get_bone_track_names() if str(b) in ('root', 'pelvis') or
             str(b).startswith(('thigh_', 'calf_', 'foot_', 'ball_', 'ik_foot_'))]
    controller = clip.get_editor_property('controller')
    controller.open_bracket('Stable standing service stance with original upper-body work', False)
    try:
        for b in lower:
            tracks = [u.AnimationLibrary.get_bone_pose_for_time(idle, b, idle.sequence_length*i/(keys-1), False)
                      for i in range(keys)]
            assert controller.set_bone_track_keys(b, [t.translation for t in tracks],
                [t.rotation for t in tracks], [t.scale3d for t in tracks], False)
    finally:
        controller.close_bracket(False)
    clip.set_editor_property('rate_scale', .65)
    for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        if a.get_actor_label() in (PREFIX+'Finish technician', PREFIX+'Outer technician'):
            a.modify(); c = a.character_mesh; c.modify()
            c.set_relative_location(u.Vector(0., 0., -85.), False, True)
            a.set_editor_property('idle_animation', clip)
            c.set_editor_property('animation_data', u.SingleAnimationPlayData(
                anim_to_play=clip, saved_looping=True, saved_playing=True))
    return {'private_clip': output, 'lower_tracks': len(lower), 'keys': keys,
            'source_clips_preserved': True, 'visual_review': 'PENDING'}
