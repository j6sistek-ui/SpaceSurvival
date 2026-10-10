"""Place/adopt two source-backed central guides on owned landscape monitors.

Reuse the five already staged private assets. No import, asset editing, map
loading/saving, PIE or settings changes. Root reviews actual text/brightness,
backs up the shared map and resolves its held T display trial before saving.
"""
import itertools
import math
from pathlib import Path

import RefineStationCentralWelcome as welcome
import RefineStationCentralReception as reception

MAP = welcome.MAP
PREFIX = 'Refine/CentralInformationBoardsAccepted/'
LEGACY = 'Refine/CentralInformationBoards4/'
TAG = 'CentralInformationBoards1'
ROLE_TAG = TAG + ':'
PRIVATE = '/Game/OutpostSandbox/StationRefinement/CentralInformationBoards20261007'
HOUSING = '/Game/SciFiCorridor/Meshes/SM_Monitor'
SCREEN = '/Game/SciFiCorridor/Meshes/SM_MonitorScreen'
HOUSING_MATERIAL = '/Game/SciFiCorridor/Materials/MI_Assets'
WALL_MESH = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Meshes/SM_WallPanel400X200_V1_SmartStorageUnit'
MASTER = PRIVATE + '/Materials/M_MonitorInformation'
SCALE, SCREEN_OFFSET_CM, DEFAULT_BRIGHTNESS = 3., .15, 8.
BOARDS = (
    ('NE', 'Atrium/Bay 2/Panel 200', (5271.033383806704, 1071.0333838067038, 260.), 135.,
     '01_StationDirectory', (5324.29978208661, 1124.2997820866105, 200.), 225.),
    ('SW', 'Atrium/Bay 10/Panel 200', (3128.966616193296, -1071.0333838067038, 260.), -45.,
     '02_FlightGuide', (3075.700217913389, -1124.2997820866105, 200.), 45.),
)
SHADER = ('float2 p=(UV-float2(0.53556102514266968,0.02609097957611084))/'
          'float2(0.44492596387863159,0.22721999883651733);\n'
          'return Texture2DSample(Artwork,ArtworkSampler,clamp(p,0.0,1.0)).rgb*DisplayBrightness;')
require, path = welcome.require, welcome.path


def _role(actors, role):
    rows = [a for a in actors if ROLE_TAG + role in map(str, a.tags) or
            a.get_actor_label() in (PREFIX + role, LEGACY + role)]
    require(len(rows) <= 1, 'Duplicate board role; preserve it: ' + role)
    return rows[0] if rows else None


def _rows(u):
    for side, _, pivot, yaw, _, _, _ in BOARDS:
        angle = math.radians(yaw)
        for kind in ('housing', 'screen'):
            p = pivot if kind == 'housing' else (
                pivot[0]-SCREEN_OFFSET_CM*SCALE*math.sin(angle),
                pivot[1]+SCREEN_OFFSET_CM*SCALE*math.cos(angle), pivot[2])
            yield side + '/' + kind, kind, p, yaw


def _asset_state(u, assets, brightness):
    edit, master = u.MaterialEditingLibrary, assets[MASTER]
    require(isinstance(master, u.Material) and master.get_editor_property('two_sided') and
            master.get_editor_property('blend_mode') == u.BlendMode.BLEND_OPAQUE and
            master.get_editor_property('shading_model') == u.MaterialShadingModel.MSM_UNLIT and
            not master.get_editor_property('use_material_attributes'), 'Use the existing private unlit board master')
    nodes = list(edit.get_material_expressions(master))
    custom = [n for n in nodes if isinstance(n, u.MaterialExpressionCustom)]
    require(len(nodes) == 4 and len(custom) == 1 and str(custom[0].get_editor_property('code')) == SHADER and
            edit.get_material_property_input_node(master, u.MaterialProperty.MP_EMISSIVE_COLOR) == custom[0],
            'Keep the measured atlas projection and native emissive route')
    result = {'master': (path(master), SHADER, tuple(path(n) for n in nodes)), 'textures': [], 'instances': []}
    for _, _, _, _, name, _, _ in BOARDS:
        texture, leaf = assets[PRIVATE + '/Textures/T_' + name], assets[PRIVATE + '/Materials/MI_' + name]
        require(isinstance(texture, u.Texture2D) and isinstance(leaf, u.MaterialInstanceConstant) and
                (texture.blueprint_get_size_x(), texture.blueprint_get_size_y()) == (1960, 1000) and
                texture.get_editor_property('srgb') and texture.get_editor_property('never_stream') and
                leaf.get_editor_property('parent') == master and
                edit.get_material_instance_texture_parameter_value(leaf, 'Artwork') == texture and
                float(edit.get_material_instance_scalar_parameter_value(leaf, 'DisplayBrightness')) == brightness,
                'Reuse exact staged artwork/parent and root-reviewed brightness')
        result['textures'].append((path(texture), tuple(str(texture.get_editor_property(k)) for k in
            ('compression_settings', 'lod_group', 'mip_gen_settings', 'address_x', 'address_y'))))
        result['instances'].append((path(leaf), path(master), path(texture), brightness,
            tuple(tuple(v.export_text() for v in leaf.get_editor_property(k)) for k in
                  ('scalar_parameter_values', 'vector_parameter_values', 'texture_parameter_values'))))
    return result


def _points(actor, u):
    points, total = [], 0
    for c in actor.get_components_by_class(u.StaticMeshComponent):
        if not c.static_mesh or not c.is_visible() or c.get_editor_property('hidden_in_game'):
            continue
        count = c.get_instance_count() if isinstance(c, u.InstancedStaticMeshComponent) else 1
        total += count
        require(0 <= count <= 64 and total <= 128, 'Keep furnishing bounds finite and bounded')
        transforms = [c.get_instance_transform(i, world_space=True) for i in range(count)] \
            if isinstance(c, u.InstancedStaticMeshComponent) else [c.get_world_transform()]
        b = c.static_mesh.get_bounds()
        for t in transforms:
            points += [u.MathLibrary.transform_location(t, b.origin + u.Vector(
                x*b.box_extent.x, y*b.box_extent.y, z*b.box_extent.z)).to_tuple()
                for x, y, z in itertools.product((-1., 1.), repeat=3)]
    require(points and all(math.isfinite(v) for p in points for v in p), 'Require visible native furnishing geometry')
    return points


def _placement(actor, position, yaw, u):
    """Eight native source-box corners constrain the complete affine placement.

    Keep-world attachment can round scale3 to 2.9999999999999996. Physical
    corners use the existing 0.0001cm gate; every original snapshot stays exact.
    """
    c, angle = actor.static_mesh_component, math.radians(yaw)
    b, t = c.static_mesh.get_bounds(), c.get_world_transform()
    for x, y, z in itertools.product((-1., 1.), repeat=3):
        v = b.origin + u.Vector(x*b.box_extent.x, y*b.box_extent.y, z*b.box_extent.z)
        expected = (position[0]+SCALE*(v.x*math.cos(angle)-v.y*math.sin(angle)),
                    position[1]+SCALE*(v.x*math.sin(angle)+v.y*math.cos(angle)), position[2]+SCALE*v.z)
        require(math.dist(expected, u.MathLibrary.transform_location(t, v).to_tuple()) <= .0001,
                'Board physical placement differs: ' + actor.get_actor_label())


def _verify_roles(u, state, tagged=False):
    for role, kind, position, yaw in _rows(u):
        a = state['roles'][role]
        require(isinstance(a, u.StaticMeshActor), 'Require the original complete native monitor actors')
        c, side = a.static_mesh_component, role.split('/')[0]
        parent = state['walls'][side] if kind == 'housing' else state['roles'][side + '/housing']
        material = state['assets'][HOUSING_MATERIAL] if kind == 'housing' else state['assets'][
            PRIVATE + '/Materials/MI_' + next(b[4] for b in BOARDS if b[0] == side)]
        require(c.static_mesh == state['assets'][HOUSING if kind == 'housing' else SCREEN] and
                c.get_num_materials() == 1 and c.get_material(0) == material and a.get_attach_parent_actor() == parent and
                not a.get_actor_enable_collision() and c.get_collision_enabled() == u.CollisionEnabled.NO_COLLISION and
                c.is_visible() and not c.get_editor_property('hidden_in_game') and not a.get_editor_property('hidden'),
                'Native board mesh/material/support/state differs: ' + role)
        expected_children = [state['roles'][side + '/screen']] if kind == 'housing' else []
        require(list(a.get_attached_actors()) == expected_children, 'Unexpected board attachment')
        if tagged:
            require(a.get_actor_label() == PREFIX + role and ROLE_TAG + role in map(str, a.tags), 'Board role identity differs')
        _placement(a, position, yaw, u)


def _prepare(u, target_map, expected_map_sha256, display_brightness):
    _, _, actors = welcome._context(u, target_map)
    require(math.isfinite(display_brightness) and display_brightness > 0., 'Require root-reviewed finite brightness')
    root = Path(u.Paths.project_dir())
    main = root / ('Content' + MAP.removeprefix('/Game') + '.umap')
    require(welcome._sha(main) == expected_map_sha256, 'Bind the actual current saved map')
    packages = (HOUSING, SCREEN, HOUSING_MATERIAL, MASTER) + tuple(
        PRIVATE + folder + name for _, _, _, _, name, _, _ in BOARDS
        for folder in ('/Textures/T_', '/Materials/MI_'))
    assets = {p: u.load_asset(p) for p in packages}
    require(all(assets.values()) and all(isinstance(assets[p], u.StaticMesh) for p in (HOUSING, SCREEN)) and
            isinstance(assets[HOUSING_MATERIAL], u.MaterialInterface), 'Stage the five private assets separately first')
    before_assets = _asset_state(u, assets, display_brightness)
    walls = {side: welcome._one(actors, label) for side, label, _, _, _, _, _ in BOARDS}
    for side, _, _, _, _, pos, yaw in BOARDS:
        wall = walls[side]
        require(isinstance(wall, u.StaticMeshActor) and path(wall.static_mesh_component.static_mesh).split('.')[0] == WALL_MESH and
                wall.get_actor_location().to_tuple() == pos and wall.get_actor_scale3d().to_tuple() == (1., 1.575, 1.) and
                abs(sum(a*b for a, b in zip(wall.get_actor_transform().rotation.to_tuple(),
                    u.Rotator(yaw=yaw).quaternion().to_tuple()))) > .99999, 'Use the existing solid diagonal wall')
    roles = {role: _role(actors, role) for role, _, _, _ in _rows(u)}
    require(sum(a is not None for a in roles.values()) in (0, 4), 'Partial board composition requires explicit review')
    require(not any((TAG in map(str, a.tags) or a.get_actor_label().startswith((PREFIX, LEGACY))) and
                    a not in roles.values() for a in actors), 'Unknown board role; no broad cleanup')
    own = {a for a in roles.values() if a}
    selected = set(reception._selected(actors, u)) | set(walls.values()) | {
        welcome._one(actors, 'Atrium/Bay 2/Panel 0'), welcome._one(actors, 'Atrium/Bay 10/Panel 0')}
    source_files = {root / ('Content' + p.removeprefix('/Game') + '.uasset'): None
                    for p in (HOUSING, SCREEN, HOUSING_MATERIAL, WALL_MESH)}
    source_files = {p: welcome._sha(p) for p in source_files}
    state = {'target_map': target_map, 'main': main, 'base_sha256': expected_map_sha256, 'assets': assets,
             'asset_before': before_assets, 'brightness': display_brightness, 'walls': walls, 'roles': roles,
             'created': [], 'source_files': source_files, 'protected': [(a, reception._record(a, u)) for a in selected-own],
             'backups': [(a, a.get_actor_label(), list(a.tags), reception._record(a, u)) for a in own]}
    if own:
        _verify_roles(u, state)
    furnishings = [a for a in selected if a.get_actor_label().startswith((
        'Refine/CentralWelcomeArrival2/', 'Refine/CentralWelcomeGreeneryLights1/Foliage ', welcome.PREFIX)) and
        not isinstance(a, u.Light)]
    for _, _, pivot, yaw, _, _, _ in BOARDS:
        angle, b = math.radians(yaw), assets[HOUSING].get_bounds()
        center = (pivot[0]+SCALE*(b.origin.x*math.cos(angle)-b.origin.y*math.sin(angle)),
                  pivot[1]+SCALE*(b.origin.x*math.sin(angle)+b.origin.y*math.cos(angle)), pivot[2]+SCALE*b.origin.z)
        axes = ((math.cos(angle), math.sin(angle), 0.), (-math.sin(angle), math.cos(angle), 0.), (0., 0., 1.))
        for actor in furnishings:
            points = _points(actor, u)
            ranges = [[min(sum((p[k]-center[k])*axis[k] for k in range(3)) for p in points),
                       max(sum((p[k]-center[k])*axis[k] for k in range(3)) for p in points)] for axis in axes]
            require(any(lo > SCALE*half or hi < -SCALE*half for (lo, hi), half in
                        zip(ranges, b.box_extent.to_tuple())), 'Board intersects visible furnishing bounds')
    return state


def check_adoption(u, target_map, expected_map_sha256, *, display_brightness=DEFAULT_BRIGHTNESS):
    """Read-only fit/source check of the four retained live or saved board roles."""
    state = _prepare(u, target_map, expected_map_sha256, display_brightness)
    require(all(state['roles'].values()), 'Four existing board actors required for adoption')
    require(all(reception._record(a, u) == before for a, before in state['protected']) and
            all(reception._record(a, u) == before for a, _, _, before in state['backups']) and
            welcome._sha(state['main']) == state['base_sha256'] and
            all(welcome._sha(p) == digest for p, digest in state['source_files'].items()) and
            _asset_state(u, state['assets'], display_brightness) == state['asset_before'],
            'Read-only board check changed a target/source asset')
    return {'read_only': True, 'adoptable_actor_count': 4, 'existing_private_asset_count': 5,
            'brightness': display_brightness, 'saved': False}


def apply(u, target_map, expected_map_sha256, *, display_brightness=DEFAULT_BRIGHTNESS):
    """Adopt four trial actors or place them from already staged assets; no save."""
    state = _prepare(u, target_map, expected_map_sha256, display_brightness)
    _, eas, _ = welcome._context(u, target_map)
    roles, assets, walls = state['roles'], state['assets'], state['walls']
    try:
        with u.ScopedEditorTransaction('Place central information guides'):
            for role, kind, position, yaw in _rows(u):
                actor, side = roles[role], role.split('/')[0]
                if actor is None:
                    actor = eas.spawn_actor_from_class(u.StaticMeshActor, u.Vector(*position), u.Rotator(yaw=yaw))
                    require(actor is not None, 'Cannot create board role: ' + role)
                    state['created'].append(actor)
                    roles[role] = actor
                    c = actor.static_mesh_component
                    require(c.set_static_mesh(assets[HOUSING if kind == 'housing' else SCREEN]), 'Cannot assign native board mesh')
                    c.set_material(0, assets[HOUSING_MATERIAL] if kind == 'housing' else assets[
                        PRIVATE + '/Materials/MI_' + next(b[4] for b in BOARDS if b[0] == side)])
                    actor.set_actor_scale3d(u.Vector(SCALE, SCALE, SCALE))
                    actor.set_actor_enable_collision(False)
                    c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
                    c.set_visibility(True, False)
                    actor.set_actor_hidden_in_game(False)
                    parent = walls[side] if kind == 'housing' else roles[side + '/housing']
                    require(actor.attach_to_actor(parent, u.Name(), u.AttachmentRule.KEEP_WORLD,
                        u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, False), 'Cannot mount board on physical support')
                if actor.get_actor_label() != PREFIX + role:
                    actor.set_actor_label(PREFIX + role)
                tags = list(actor.tags)
                for tag in (TAG, ROLE_TAG + role):
                    if tag not in map(str, tags):
                        tags.append(u.Name(tag))
                if list(map(str, actor.tags)) != list(map(str, tags)):
                    actor.tags = tags
        state['verification'] = verify(u, state)
        return state
    except Exception:
        rollback(u, state)
        raise


def verify(u, state, check_saved_base=True):
    _, _, actors = welcome._context(u, state['target_map'])
    require(not check_saved_base or welcome._sha(state['main']) == state['base_sha256'], 'Saved map changed before root save')
    require(all(welcome._sha(p) == digest for p, digest in state['source_files'].items()) and
            _asset_state(u, state['assets'], state['brightness']) == state['asset_before'], 'Board/source assets changed')
    require(all(a in actors and _role(actors, r) == a for r, a in state['roles'].items()), 'Four unique board actors required')
    require(all(a in actors and reception._record(a, u) == before for a, before in state['protected']),
            'Original central/held-T state changed')
    _verify_roles(u, state, tagged=True)
    return {'role_actor_count': 4, 'created_actor_count': len(state['created']), 'adopted_actor_count': 4-len(state['created']),
            'new_asset_count': 0, 'targeted_preservation_pass': True, 'map_save_performed': False,
            'limits': 'Actual mounted readability, approach, owner acceptance and fresh saved replay remain root gates.'}


def assert_ready_to_save(u, state, *, appearance_reviewed=False):
    _, _, actors = welcome._context(u, state['target_map'])
    require(appearance_reviewed is True, 'Root must accept current mounted text/brightness before saving')
    require(not any(a.get_actor_label().startswith('Refine/OperationsPortraitPanels/') for a in actors),
            'Resolve/remove only the held T display trial before a shared-map save')
    return verify(u, state)


def rollback(u, state):
    _, eas, actors = welcome._context(u, state['target_map'])
    errors, known = [], set(state['created'])
    for actor, label, tags, _ in state['backups']:
        for operation in (lambda a=actor, v=label: a.set_actor_label(v), lambda a=actor, v=tags: setattr(a, 'tags', v)):
            try:
                operation()
            except Exception as error:
                errors.append(str(error))
    for actor in reversed(state['created']):
        try:
            require(actor in actors and set(actor.get_attached_actors()) <= known, 'Do not remove unrelated board children')
            require(eas.destroy_actor(actor), 'Cannot remove owned board actor')
        except Exception as error:
            errors.append(str(error))
    _, _, after = welcome._context(u, state['target_map'])
    require(not errors and not any(a in after for a in known), 'Board rollback incomplete: ' + '; '.join(errors))
    require(all(reception._record(a, u) == before for a, before in state['protected']) and
            all(reception._record(a, u) == before for a, _, _, before in state['backups']) and
            _asset_state(u, state['assets'], state['brightness']) == state['asset_before'], 'Restored board/original state differs')
    return {'restored': True, 'map_save_performed': False}
