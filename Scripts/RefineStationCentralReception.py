"""Accepted check-in/help props and poses, separate from the welcome bay pass.

Run RefineStationCentralWelcome.apply first, then this pass. Existing live
Purpose1 props are adopted by label; replay uses stable role tags. Roll this
pass back before rolling back the welcome pass. No map loading/saving, asset
imports, source edits, animation changes or held-display changes occur here.
After both passes, use this module's verify/assert_ready_to_save entries;
the original welcome verifier intentionally does not permit staff pose moves.
The observed props are supported; label readability and hand contact are not
certified by the cropped reception-lighting photographs.
"""
import copy
import itertools
import math
from pathlib import Path

import RefineStationCentralWelcome as welcome
from InspectStationOperationsCrewContacts2 import geometry, arrays
from RefineStationSocialFinish import _surface

MAP = welcome.MAP
PREFIX = 'Refine/CentralReceptionAccepted/'
LEGACY = 'Refine/ReceptionPurpose1/'
TAG = 'CentralReceptionAccepted1'
ROLE_TAG = TAG + ':'
LAPTOP = '/Game/Cyberpunk_Room/Mesh/SM_Laptop'
TABLET = '/Game/Cyberpunk_Room/Mesh/SM_Tablet'
MATERIAL = '/Game/Cyberpunk_Room/Material/MI_Laptop'
GRAPHITE = '/Game/OutpostSandbox/Materials/M_OutpostGraphite'
CUBE = '/Engine/BasicShapes/Cube'
TEXT = '/Engine/EngineMaterials/UnlitText'
COUNTER = 'Refine/Reception/Countertop'
COLLAR = '/Game/OutpostSandbox/Geometry/SM_OutpostCollar'
# Exact accepted live placements; no new visual fit or animation evaluation.
SPOTS = (
    ('Check-in', 'Crew/Atrium A', 225., LAPTOP, 'CHECK-IN',
     (4040.900974233027, -159.09902576697317, 85.),
     (4014.7942829655653, -206.45638018437754, 107.85204215049744),
     (3989.9892859875954, -210.0107140124046, 65.),
     (3986.3123307254255, -213.68766927457463, 65.)),
    ('Help', 'Crew/Atrium B', 135., TABLET, 'STATION HELP',
     (4040.900974233027, 159.0990257669732, 85.),
     (3993.113178097878, 185.45924637774735, 106.63502613306045),
     (3989.9892859875954, 210.01071401240463, 65.),
     (3986.3123307254255, 213.68766927457466, 65.)),
)
require, path = welcome.require, welcome.path


def _record(actor, u):
    row = {'label': actor.get_actor_label(), 'tags': tuple(map(str, actor.tags)),
           'parent': path(actor.get_attach_parent_actor()), 'scene': welcome._snapshot(actor, u)}
    if isinstance(actor, u.SSOutpostTerminal):
        row['terminal'] = {name: str(actor.get_editor_property(name)) for name in
                           ('action', 'description', 'display_name', 'use_distance')}
        row['terminal']['presentation_target'] = path(actor.get_editor_property('presentation_target'))
    return row


def _relative(actor, u):
    return {c.get_name(): (c.get_relative_transform().translation.to_tuple(),
            c.get_relative_transform().rotation.to_tuple(), c.get_relative_transform().scale3d.to_tuple())
            for c in actor.get_components_by_class(u.SceneComponent) if c.get_name() != 'Body'}


def _without_world_poses(row):
    row = copy.deepcopy(row)
    row['scene'].pop('pose')
    for component in row['scene']['components'].values():
        component.pop('pose')
    return row


def _selected(actors, u):
    return [a for a in actors if a.get_actor_label().startswith((
        'Refine/Reception/', 'Welcome/', 'Refine/CentralWelcomeArrival2/',
        'Refine/CentralWelcomeGreeneryLights1/', welcome.PREFIX, LEGACY, PREFIX,
        'Refine/OperationsPortraitPanels/')) or a.get_actor_label() in
        ('Crew/Atrium A', 'Crew/Atrium B', 'Atrium/Orbital halo', 'Ground/Atrium') or
        a.get_name() in ('StaticMeshActor_7692', 'StaticMeshActor_7693',
                         'StaticMeshActor_7695', 'StaticMeshActor_7696')]


def _role(actors, role):
    rows = [a for a in actors if ROLE_TAG + role in map(str, a.tags) or
            a.get_actor_label() in (PREFIX + role, LEGACY + role)]
    require(len(rows) <= 1, 'Duplicate reception role; preserve it: ' + role)
    return rows[0] if rows else None


def _rows(u):
    rows = []
    for name, _, angle, mesh, words, _, tool, plaque, label in SPOTS:
        for part, kind, position, scale in (
                ('Tool', 'tool', tool, .65), ('Role plaque', 'plaque', plaque, None),
                ('Role label', 'label', label, 1.)):
            rows.append((name + '/' + part, kind, position, u.Rotator(yaw=angle), scale, mesh, words))
    return rows


def _verify_roles(u, state, tagged=False):
    roles, assets = state['roles'], state['assets']
    for role, kind, position, rotation, scale, mesh, words in _rows(u):
        actor = roles[role]
        require(actor is not None and not actor.get_actor_enable_collision() and
                not actor.get_editor_property('hidden'), 'Missing/hidden/blocking role: ' + role)
        if tagged:
            require(ROLE_TAG + role in map(str, actor.tags) and actor.get_actor_label() == PREFIX + role,
                    'Accepted reception role identity differs: ' + role)
        if kind == 'plaque':
            t = actor.get_actor_transform()
            require(max(abs(a-b) for a, b in zip(t.translation.to_tuple(), position)) <= .05 and
                     max(abs(a-b) for a, b in zip(t.scale3d.to_tuple(), (.09, .70, .22))) <= .0001 and
                     abs(sum(a*b for a, b in zip(t.rotation.to_tuple(), rotation.quaternion().to_tuple()))) > .99999,
                    'Accepted plaque pose differs')
        else:
            require(welcome._pose_ok(actor, position, rotation, scale), 'Accepted role pose differs: ' + role)
        if kind == 'label':
            c = actor.get_component_by_class(u.TextRenderComponent)
            require(isinstance(actor, u.TextRenderActor) and c and c.is_visible() and
                    not c.get_editor_property('hidden_in_game') and c.get_collision_enabled() == u.CollisionEnabled.NO_COLLISION and
                    str(c.get_editor_property('text')) == words and c.get_editor_property('world_size') == 10. and
                    c.get_editor_property('text_material') == assets[TEXT] and
                    c.get_editor_property('horizontal_alignment') == u.HorizTextAligment.EHTA_CENTER and
                    c.get_editor_property('vertical_alignment') == u.VerticalTextAligment.EVRTA_TEXT_CENTER and
                    actor.get_attach_parent_actor() == roles[role.replace('Role label', 'Role plaque')],
                    'Mounted label fields differ: ' + role)
            color = c.get_editor_property('text_render_color')
            require((color.r, color.g, color.b, color.a) == (245, 235, 220, 255), 'Role label color differs')
        else:
            c = actor.get_component_by_class(u.StaticMeshComponent)
            require(isinstance(actor, u.StaticMeshActor) and c and c.static_mesh == assets[mesh if kind == 'tool' else CUBE] and
                    [path(c.get_material(i)) for i in range(c.get_num_materials())] ==
                    [path(assets[MATERIAL if kind == 'tool' else GRAPHITE])] and c.is_visible() and
                    not c.get_editor_property('hidden_in_game') and c.get_collision_enabled() == u.CollisionEnabled.NO_COLLISION and
                    actor.get_attach_parent_actor() is None, 'Original whole prop/source fields differ: ' + role)
            expected_children = [roles[role.replace('Role plaque', 'Role label')]] if kind == 'plaque' else []
            require(list(actor.get_attached_actors()) == expected_children, 'Unexpected attached reception child')


def _prepare(u, target_map, expected_map_sha256, welcome_state=None):
    from PlaceStationLocalArcade import _floor

    world, eas, actors = welcome._context(u, target_map)
    root = Path(u.Paths.project_dir())
    main = root / ('Content' + target_map.removeprefix('/Game') + '.umap')
    require(welcome._sha(main) == expected_map_sha256, 'Bind actual current saved Main')
    packages = (LAPTOP, TABLET, MATERIAL, GRAPHITE, CUBE, TEXT)
    assets = {p: u.load_asset(p) for p in packages}
    require(all(assets.values()) and all(isinstance(assets[p], u.StaticMesh) for p in (LAPTOP, TABLET, CUBE)),
            'Use existing whole props; do not import/create assets')
    source_files = {root / ('Content' + p.removeprefix('/Game') + '.uasset'): None
                    for p in packages if p.startswith('/Game/')}
    counter = welcome._one(actors, COUNTER)
    require(path(counter.static_mesh_component.static_mesh).split('.')[0] == COLLAR and
            counter.get_actor_location().to_tuple() == (4200., 0., 102.) and
            counter.get_actor_scale3d().to_tuple() == (3.05, 3.05, .4), 'Preserve actual annular countertop')
    source_files[root / ('Content' + COLLAR.removeprefix('/Game') + '.uasset')] = None
    source_files = {p: welcome._sha(p) for p in source_files}
    staff = [welcome._one(actors, spot[1]) for spot in SPOTS]
    require(all(isinstance(a, u.SSOutpostAmbientActor) and not a.get_editor_property('route_points') and
                not a.get_editor_property('drone') for a in staff), 'Keep original stationary reception staff')
    roles = {row[0]: _role(actors, row[0]) for row in _rows(u)}
    require(not any((TAG in map(str, a.tags) or a.get_actor_label().startswith((LEGACY, PREFIX))) and
                    a not in roles.values() for a in actors), 'Unknown reception role; no broad cleanup')
    for actor, spot, old_y in zip(staff, SPOTS, (-80., 80.)):
        require(welcome._pose_ok(actor, spot[5], u.Rotator(yaw=spot[2]), 1.) or
                (not any(roles.values()) and welcome._pose_ok(actor, (4010., old_y, 85.), u.Rotator(yaw=180.), 1.)),
                'Preserve a separately changed owner staff pose')
    dynamic, counts = geometry(counter.static_mesh_component.static_mesh, False, u)
    require(0 < counts['triangles'] <= 10000 and 0 < counts['vertices'] <= 10000, 'Keep support geometry bounded')
    data = arrays(dynamic, counts, u, vertex_limit=10000)
    console_boxes = []
    for label in ('Refine/Reception/Welcome console -130', 'Refine/Reception/Welcome console 130'):
        console = welcome._one(actors, label)
        components = [c for c in console.get_components_by_class(u.StaticMeshComponent) if c.static_mesh]
        require(len(components) == 3, 'Keep both complete three-part welcome consoles')
        for c in components:
            b, t = c.static_mesh.get_bounds(), c.get_world_transform()
            points = [u.MathLibrary.transform_location(t, u.Vector(b.origin.x+sx*b.box_extent.x,
                b.origin.y+sy*b.box_extent.y, b.origin.z+sz*b.box_extent.z)).to_tuple()
                for sx, sy, sz in itertools.product((-1., 1.), repeat=3)]
            console_boxes.append([[min(p[i] for p in points) for i in range(3)],
                                  [max(p[i] for p in points) for i in range(3)]])
    support = []
    for spot in SPOTS:
        mesh, tool, angle = assets[spot[3]], spot[6], math.radians(spot[2])
        require([path(s.material_interface) for s in mesh.static_materials] == [path(assets[MATERIAL])],
                'Original tool material differs')
        b = mesh.get_bounds()
        center = (tool[0] + .65*(b.origin.x*math.cos(angle)-b.origin.y*math.sin(angle)),
                  tool[1] + .65*(b.origin.x*math.sin(angle)+b.origin.y*math.cos(angle)))
        points = [center] + [(center[0]+.65*(sx*b.box_extent.x*math.cos(angle)-sy*b.box_extent.y*math.sin(angle)),
                            center[1]+.65*(sx*b.box_extent.x*math.sin(angle)+sy*b.box_extent.y*math.cos(angle)))
                           for sx, sy in itertools.product((-1., 1.), repeat=2)]
        heights = [_surface(counter, data, x, y, u) for x, y in points]
        require(all(math.isfinite(z) and abs(z-106.) <= .05 for z in heights) and
                abs(tool[2]+.65*(b.origin.z-b.box_extent.z)-106.) <= .05, 'Complete tool footprint must retain support')
        tool_box = [[min(p[i] for p in points) for i in range(2)]+[106.],
                    [max(p[i] for p in points) for i in range(2)]+[tool[2]+.65*(b.origin.z+b.box_extent.z)]]
        require(not any(all(tool_box[0][i] < old[1][i] and tool_box[1][i] > old[0][i]
                            for i in range(3)) for old in console_boxes), 'Tool intersects a native welcome console')
        floor = _floor(world, spot[5][:2], staff, u)
        require(floor and floor['actor'] == 'Ground/Atrium' and abs(floor['point'][2]) < .1 and
                floor['normal'][2] > .95, 'Accepted staff floor differs')
        support.append({'role': spot[0], 'top_z_cm': heights, 'floor': floor})
    own = {a for a in roles.values() if a}
    selected = _selected(actors, u)
    state = {'target_map': target_map, 'main': main, 'base_sha256': expected_map_sha256, 'assets': assets,
             'source_files': source_files, 'roles': roles, 'created': [], 'support': support,
             'welcome_state': welcome_state,
             'protected': [(a, _record(a, u)) for a in selected if a not in own],
             'backups': [(a, a.get_actor_label(), list(a.tags), _record(a, u)) for a in own],
             'staff_before': [(a, a.get_actor_transform(), _relative(a, u)) for a in staff]}
    if all(roles.values()):
        _verify_roles(u, state)
        if welcome_state is not None:
            _verify_welcome_with_staff_poses(u, state, actors, True)
    else:
        require(not any(roles.values()), 'Partial purpose composition needs explicit owner review')
        if welcome_state is not None:
            welcome.verify(u, welcome_state)
    return state


def check_adoption(u, target_map, expected_map_sha256):
    """Standalone read-only check of the six retained live/saved accepted roles."""
    state = _prepare(u, target_map, expected_map_sha256)
    require(all(state['roles'].values()), 'Six existing purpose actors required for adoption')
    require(all(_record(a, u) == before for a, before in state['protected']) and
            all(_record(a, u) == before for a, _, _, before in state['backups']) and
            welcome._sha(state['main']) == state['base_sha256'] and
            all(welcome._sha(p) == digest for p, digest in state['source_files'].items()),
            'Standalone adoption read changed a target or source')
    return {'read_only': True, 'adoptable_actor_count': 6, 'staff_pose_count': 2,
            'support': state['support'], 'saved': False, 'label_readability_verified': False}


def apply(u, target_map, expected_map_sha256, welcome_state=None):
    require(welcome_state is not None, 'Apply the welcome pass first and supply its unchanged rollback state')
    state = _prepare(u, target_map, expected_map_sha256, welcome_state)
    _, eas, _ = welcome._context(u, target_map)
    try:
        with u.ScopedEditorTransaction('Install accepted reception check-in/help composition'):
            for actor, spot in zip((r[0] for r in state['staff_before']), SPOTS):
                if not welcome._pose_ok(actor, spot[5], u.Rotator(yaw=spot[2]), 1.):
                    actor.set_actor_location_and_rotation(u.Vector(*spot[5]), u.Rotator(yaw=spot[2]), False, True)
            for role, kind, position, rotation, scale, mesh, words in _rows(u):
                actor = state['roles'][role]
                if actor is None:
                    actor = eas.spawn_actor_from_class(u.TextRenderActor if kind == 'label' else u.StaticMeshActor,
                                                       u.Vector(*position), rotation)
                    require(actor is not None, 'Cannot create accepted purpose role: ' + role)
                    state['created'].append(actor)
                    state['roles'][role] = actor
                    actor.set_actor_enable_collision(False)
                    if kind == 'label':
                        c = actor.get_component_by_class(u.TextRenderComponent)
                        c.set_text(words)
                        c.set_world_size(10.)
                        c.set_text_material(state['assets'][TEXT])
                        c.set_horizontal_alignment(u.HorizTextAligment.EHTA_CENTER)
                        c.set_vertical_alignment(u.VerticalTextAligment.EVRTA_TEXT_CENTER)
                        # UE Python Color positional fields are B,G,R,A; keep the
                        # actual accepted warm-white label explicitly by name.
                        c.set_text_render_color(u.Color(r=245, g=235, b=220, a=255))
                        require(actor.attach_to_actor(state['roles'][role.replace('Role label', 'Role plaque')], '',
                            u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, False),
                            'Mount label on its actual plaque')
                    else:
                        c = actor.static_mesh_component
                        c.set_static_mesh(state['assets'][mesh if kind == 'tool' else CUBE])
                        if kind == 'plaque':
                            c.set_material(0, state['assets'][GRAPHITE])
                        actor.set_actor_scale3d(u.Vector(.09, .70, .22) if kind == 'plaque' else u.Vector(scale, scale, scale))
                    c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
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


def _verify_welcome_with_staff_poses(u, state, actors, check_saved_base):
    """Retain the base pass's rollback snapshot; only two accepted poses differ."""
    base = state['welcome_state']
    require(base['target_map'] == state['target_map'] and base['main'] == state['main'] and
            base['base_sha256'] == state['base_sha256'], 'Both passes must bind the same saved map')
    require(not check_saved_base or welcome._sha(base['main']) == base['base_sha256'],
            'Saved Main changed before combined root save')
    require(all(welcome._sha(p) == digest for p, digest in base['source_files'].items()),
            'Welcome source packages changed')
    require(len(base['roles']) == 13 and all(a in actors and welcome.ROLE_TAG + role in map(str, a.tags)
            for role, a in base['roles'].items()), 'Keep all thirteen accepted welcome roles')
    staff = {a for a, _, _ in state['staff_before']}
    require(staff == {a for a, _, _ in base['staff_before']}, 'Keep exactly the two original staff instances')
    for actor, before in base['protected']:
        require(actor in actors, 'Original welcome actor disappeared')
        after, expected = welcome._snapshot(actor, u), copy.deepcopy(before)
        if actor in staff:
            _, idle, gesture = next(r for r in welcome.STAFF if r[0] == actor.get_actor_label())
            expected['vendor'] = {**before['vendor'],
                'idle': path(base['assets'][welcome.VENDOR + 'A_ReceptionVendor_' + idle]),
                'gestures': [path(base['assets'][welcome.VENDOR + 'A_ReceptionVendor_' + gesture])]}
            # The companion verifier separately requires the exact accepted
            # actor pose and unchanged native local rig for these two actors.
            require(_without_world_poses({'scene': after}) == _without_world_poses({'scene': expected}),
                    'Staff changed outside accepted world poses and four vendor properties')
        else:
            require(after == expected, 'Original welcome state changed: ' + actor.get_actor_label())
    welcome._verify_roles(u, base['roles'], base['halo'], base['assets'])
    return {'role_actor_count': 13, 'vendor_property_count': 4,
            'accepted_staff_pose_count': 2, 'targeted_original_preservation_pass': True}


def verify(u, state, check_saved_base=True):
    _, _, actors = welcome._context(u, state['target_map'])
    require(not check_saved_base or welcome._sha(state['main']) == state['base_sha256'], 'Saved Main changed before root save')
    require(all(welcome._sha(p) == digest for p, digest in state['source_files'].items()), 'Owned source packages changed')
    require(all(a in actors for a in state['roles'].values()), 'Accepted purpose role disappeared')
    require(all(_role(actors, role) == a for role, a in state['roles'].items()) and
            set(_selected(actors, u))-set(state['roles'].values()) == {a for a, _ in state['protected']},
            'Protected reception population or unique role identity changed')
    _verify_roles(u, state, tagged=True)
    staff = {a for a, _, _ in state['staff_before']}
    for actor, before in state['protected']:
        after = _record(actor, u)
        require((_without_world_poses(after) == _without_world_poses(before)) if actor in staff else after == before,
                'Unrelated welcome/reception/held-T state changed: ' + actor.get_actor_label())
    for (actor, _, relative), spot in zip(state['staff_before'], SPOTS):
        require(welcome._pose_ok(actor, spot[5], u.Rotator(yaw=spot[2]), 1.) and _relative(actor, u) == relative,
                'Accepted staff pose/local rig differs')
    base_result = _verify_welcome_with_staff_poses(u, state, actors, check_saved_base)
    return {'role_actor_count': 6, 'created_actor_count': len(state['created']),
            'adopted_actor_count': 6-len(state['created']), 'staff_pose_count': 2,
            'targeted_preservation_pass': True, 'new_assets': 0, 'saved': False,
            'welcome_verification': base_result,
            'label_readability_verified': False, 'typing_or_hand_contact_claimed': False}


def assert_ready_to_save(u, state):
    _, _, actors = welcome._context(u, state['target_map'])
    require(not any(a.get_actor_label().startswith('Refine/OperationsPortraitPanels/') for a in actors),
            'Root must resolve/remove only its held T portrait trial before any shared-map save')
    return verify(u, state)


def rollback(u, state):
    """Only six new actors/tags and two original poses; old welcome rollback stays separate."""
    _, eas, _ = welcome._context(u, state['target_map'])
    errors = []
    operations = []
    for actor, label, tags, _ in state['backups']:
        operations += [(lambda a=actor, v=label: a.set_actor_label(v)),
                       (lambda a=actor, v=tags: setattr(a, 'tags', v))]
    for actor, transform, _ in state['staff_before']:
        operations.append(lambda a=actor, v=transform: a.set_actor_transform(v, False, True))
    for operation in operations:
        try:
            operation()
        except Exception as error:
            errors.append(str(error))
    for actor in reversed(state['created']):
        try:
            require(not actor.get_attached_actors(), 'Do not remove unrelated attached children')
            require(eas.destroy_actor(actor), 'Cannot remove new owned reception role')
        except Exception as error:
            errors.append(str(error))
    require(not errors, 'Reception rollback incomplete: ' + '; '.join(errors))
    require(all(_record(a, u) == before for a, before in state['protected']) and
            all(_record(a, u) == before for a, _, _, before in state['backups']), 'Restored reception state differs')
    return {'restored': True, 'saved': False}
