"""Accepted central waiting bays, greenery, local keys and vendor assignments.

The caller supplies the already-open owner preview and its current saved hash.
This placed-content pass adopts the accepted live trial by label, then uses
stable role tags on replay. It never loads or saves a map, imports assets, edits
source assets, or changes held displays. Root owns backup, one-map save and PIE.
"""
import hashlib
from pathlib import Path
import struct

MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
PREFIX = 'Refine/CentralWelcomeAccepted/'
TAG = 'CentralWelcomeAccepted1'
ROLE_TAG = TAG + ':'
BENCH = '/Game/CyberPunkAssets/Environment01/SM_CyberBench01'
BENCH_MATERIAL = '/Game/CyberPunkAssets/Materials01/M_CyberBench02'
PLANT = '/Game/P1toP5_Bundle/P5_FruitSeller/Blueprints/BP_ISM_PlantBox_V1'
SHRUB = '/Game/CyberpunkRestaurant/Meshes/SM_Shrub_With_LODs_01'
GREEN = '/Game/OutpostSandbox/StationRefinement/SocialAtmosphere/Materials/MI_LoungeShrubs_Green'
BLACK = '/Game/P1toP5_Bundle/P5_FruitSeller/Materials/Instances/Opaque/MI_Plastic04_Black_2'
VENDOR = '/Game/OutpostSandbox/StationRefinement/ReceptionVendorCandidates20261007/Preview/'
STAFF = (('Crew/Atrium A', 'AS_IdleBartering', 'AS_TalkLoop'),
         ('Crew/Atrium B', 'AS_TalkLoop', 'AS_ShowBoothFull_Lt'))
FURNITURE = (
    ('NE/Bench', 'bench', (5114.757642574609, 793.7590765424673, .0000019073486328125), -135., 1.),
    ('NE/Planter left', 'planter', (5166.147036733564, 712.6984540843221, .000005839426606257803), -135., 2.765208052611151),
    ('NE/Planter right', 'planter', (4918.659663318273, 960.1858274996137, .000005839426606257803), -135., 2.765208052611151),
    ('SW/Bench', 'bench', (3285.2423574253908, -793.759076542467, .0000019073486328125), 45., 1.),
    ('SW/Planter left', 'planter', (3233.8529632664367, -712.698454084322, .00000583942661336323), 45., 2.765208052611151),
    ('SW/Planter right', 'planter', (3481.3403366817283, -960.1858274996134, .00000583942661336323), 45., 2.765208052611151),
)
FOLIAGE = (
    ('Foliage 1', (5168.718963809957, 710.61780326265, 32.98352502027392)),
    ('Foliage 2', (4921.231590394666, 958.1051766779416, 32.98352502027392)),
    ('Foliage 3', (3236.422831844341, -714.7807268466344, 32.98352502027393)),
    ('Foliage 4', (3483.9102052596327, -962.2681002619257, 32.98352502027393)),
)
KEYS = (
    ('ReceptionFront', (4928.9, 0., 556.5), (4011.581261643681, -.5560764021163637, 133.30798860297654), 1500., 1400.),
    ('NEWaiting', (4715.410132806875, 515.4101328068743, 556.5), (5041.457069611992, 841.4570696119915, 55.), 1600., 950.),
    ('SWWaiting', (3684.5898671931254, -515.4101328068743, 556.5), (3358.542930388008, -841.4570696119915, 55.), 1600., 950.),
)


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def path(obj):
    return obj.get_path_name() if obj else None


def _sha(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def _context(u, target_map):
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    require(target_map == MAP and editor.get_game_world() is None and
            path(editor.get_editor_world()) == MAP + '.' + MAP.rsplit('/', 1)[-1],
            'Explicitly target the already-open owner preview with PIE stopped')
    eas = u.get_editor_subsystem(u.EditorActorSubsystem)
    return editor.get_editor_world(), eas, list(eas.get_all_level_actors())


def _one(actors, label):
    rows = [a for a in actors if a.get_actor_label() == label]
    require(len(rows) == 1, 'Require one original central actor: ' + label)
    return rows[0]


def _role(actors, role, legacy):
    rows = [a for a in actors if ROLE_TAG + role in map(str, a.tags) or
            a.get_actor_label() in (PREFIX + role, legacy)]
    require(len(rows) <= 1, 'Duplicate central role; do not delete or overwrite: ' + role)
    return rows[0] if rows else None


def _snapshot(actor, u):
    """Small exact placed-state record, independent of Python object repr."""
    t = actor.get_actor_transform()
    result = {'pose': (t.translation.to_tuple(), t.rotation.to_tuple(), t.scale3d.to_tuple()),
              'hidden': bool(actor.get_editor_property('hidden')),
              'collision': bool(actor.get_actor_enable_collision()), 'components': {}}
    for c in actor.get_components_by_class(u.PrimitiveComponent):
        t = c.get_world_transform()
        row = {'pose': (t.translation.to_tuple(), t.rotation.to_tuple(), t.scale3d.to_tuple()),
               'visible': bool(c.is_visible()), 'hidden': bool(c.get_editor_property('hidden_in_game')),
               'collision': str(c.get_collision_enabled())}
        if isinstance(c, (u.StaticMeshComponent, u.SkeletalMeshComponent)):
            row['materials'] = [path(c.get_material(i)) for i in range(c.get_num_materials())]
        if isinstance(c, u.StaticMeshComponent):
            row['mesh'] = path(c.get_editor_property('static_mesh'))
        if isinstance(c, u.SkeletalMeshComponent):
            row['mesh'] = path(c.get_skeletal_mesh_asset())
        result['components'][c.get_name()] = row
    if isinstance(actor, u.SSOutpostAmbientActor):
        result['vendor'] = {'idle': path(actor.get_editor_property('idle_animation')),
            'gestures': [path(c) for c in actor.get_editor_property('gesture_animations')],
            'phase': float(actor.get_editor_property('phase_offset')),
            'routes': [v.to_tuple() for v in actor.get_editor_property('route_points')],
            'drone': bool(actor.get_editor_property('drone')),
            'external_animation': bool(actor.get_editor_property('animation_managed_externally'))}
    return result


def _pose_ok(actor, position, rotation, scale):
    t = actor.get_actor_transform()
    # Placement readback uses the existing authoring 0.05cm/native-quaternion
    # contract. Original actors are protected by exact before/after snapshots.
    q, expected = t.rotation.to_tuple(), rotation.quaternion().to_tuple()
    return max(abs(a-b) for a, b in zip(t.translation.to_tuple(), position)) <= .05 and \
        max(abs(v-scale) for v in t.scale3d.to_tuple()) <= .0001 and \
        abs(sum(a*b for a, b in zip(q, expected))) > .99999


def _backup(actor, u):
    return {'actor': actor, 'label': actor.get_actor_label(), 'tags': list(actor.tags),
            'snapshot': _snapshot(actor, u),
            'parts': [(c, list(c.get_editor_property('override_materials')), bool(c.is_visible()),
                       bool(c.get_editor_property('hidden_in_game')), c.get_collision_enabled())
                      for c in actor.get_components_by_class(u.StaticMeshComponent)]}


def _planter(actor, black, u):
    parts = {c.get_name(): c for c in actor.get_components_by_class(u.StaticMeshComponent)}
    expected = {'InstancedStaticMesh': 'SM_Props_ConstructionPart114',
                'InstancedStaticMesh1': 'SM_Props_ConstructionPart115',
                'InstancedStaticMesh2': 'SM_NaturalEnvironment_Mud01',
                'InstancedStaticMesh3': 'SM_ConstructionPart113_Plant'}
    require(all(n in parts and parts[n].get_editor_property('static_mesh') is not None and
                parts[n].get_editor_property('static_mesh').get_name() == mesh for n, mesh in expected.items()),
            'Use the original complete P5 planter components')
    require(parts['InstancedStaticMesh'].get_num_materials() == 6, 'Native planter base has six slots')
    for name in ('InstancedStaticMesh1', 'InstancedStaticMesh3'):
        c = parts[name]
        if c.is_visible():
            c.set_visibility(False, False)
        if not c.get_editor_property('hidden_in_game'):
            c.set_hidden_in_game(True, False)
        if c.get_collision_enabled() != u.CollisionEnabled.NO_COLLISION:
            c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    for slot in (4, 5):
        if parts['InstancedStaticMesh'].get_material(slot) != black:
            parts['InstancedStaticMesh'].set_material(slot, black)


def _light(actor, lumens, radius, u):
    c = actor.get_component_by_class(u.RectLightComponent)
    require(c is not None, 'Use an actual RectLight role')
    c.set_mobility(u.ComponentMobility.MOVABLE)
    c.set_intensity_units(u.LightUnits.LUMENS)
    c.set_intensity(lumens)
    c.set_attenuation_radius(radius)
    c.set_source_width(100.)
    c.set_source_height(8.)
    c.set_light_color(u.LinearColor(1., 1., 1., 1.))
    for name, value in (('use_temperature', True), ('temperature', 4200.),
                        ('specular_scale', .4), ('indirect_lighting_intensity', .2),
                        ('volumetric_scattering_intensity', 0.)):
        c.set_editor_property(name, value)
    c.set_cast_shadows(True)
    actor.set_actor_enable_collision(False)


def _verify_roles(u, roles, halo, assets):
    rows = [(r, kind, pos, u.Rotator(yaw=yaw), scale) for r, kind, pos, yaw, scale in FURNITURE]
    rows += [(r, 'shrub', pos, u.Rotator(), 1.12) for r, pos in FOLIAGE]
    rows += [(r, 'light', pos, u.MathLibrary.find_look_at_rotation(u.Vector(*pos), u.Vector(*aim)), 1.)
             for r, pos, aim, _, _ in KEYS]
    f32 = lambda v: struct.unpack('f', struct.pack('f', v))[0]
    for role, kind, pos, rotation, scale in rows:
        actor = roles[role]
        require(_pose_ok(actor, pos, rotation, scale), 'Accepted role placement differs: ' + role)
        if kind == 'light':
            c = actor.get_component_by_class(u.RectLightComponent)
            _, _, _, lumens, radius = next(r for r in KEYS if r[0] == role)
            color = c.get_editor_property('light_color')
            require(actor.get_attach_parent_actor() == halo and not actor.get_actor_enable_collision() and
                c.get_editor_property('intensity') == lumens and c.get_editor_property('attenuation_radius') == radius and
                c.get_editor_property('source_width') == 100. and c.get_editor_property('source_height') == 8. and
                [color.r, color.g, color.b, color.a] == [255, 255, 255, 255] and
                c.get_editor_property('use_temperature') and c.get_editor_property('temperature') == 4200. and
                c.get_editor_property('specular_scale') == f32(.4) and
                c.get_editor_property('indirect_lighting_intensity') == f32(.2) and
                c.get_editor_property('volumetric_scattering_intensity') == 0. and c.get_editor_property('cast_shadows') and
                c.get_editor_property('intensity_units') == u.LightUnits.LUMENS and
                c.get_editor_property('mobility') == u.ComponentMobility.MOVABLE, 'Accepted key fields differ: ' + role)
        elif kind == 'planter':
            parts = {c.get_name(): c for c in actor.get_components_by_class(u.StaticMeshComponent)}
            require(all(not parts[n].is_visible() and parts[n].get_editor_property('hidden_in_game') and
                        parts[n].get_collision_enabled() == u.CollisionEnabled.NO_COLLISION
                        for n in ('InstancedStaticMesh1', 'InstancedStaticMesh3')) and
                    all(parts['InstancedStaticMesh'].get_material(i) == assets[BLACK] for i in (4, 5)),
                    'Accepted planter glass, organic flags or two mirror replacements differ')
        else:
            c = actor.get_component_by_class(u.StaticMeshComponent)
            require(c.get_num_materials() == 1 and c.get_material(0) == assets[BENCH_MATERIAL if kind == 'bench' else GREEN] and
                    c.get_collision_enabled() == (u.CollisionEnabled.QUERY_AND_PHYSICS if kind == 'bench' else u.CollisionEnabled.NO_COLLISION) and
                    actor.get_actor_enable_collision() == (kind == 'bench'), 'Accepted furnishing finish/collision differs: ' + role)


def apply(u, target_map, expected_map_sha256):
    """Adopt accepted previews or create missing roles; return rollback state.

    All thirteen role identities and source assets are checked before mutation.
    Existing role poses are retained. Only owned planter-instance presentation,
    role tags and the four declared receptionist properties can be updated.
    """
    from OutpostGeometryUtils import inherit_parent_scale_preserving_world
    world, eas, actors = _context(u, target_map)
    main = Path(u.Paths.project_dir()) / ('Content' + MAP.removeprefix('/Game') + '.umap')
    require(_sha(main) == expected_map_sha256, 'Caller must bind actual saved Main bytes')
    source_paths = (BENCH, BENCH_MATERIAL, PLANT, SHRUB, GREEN, BLACK) + tuple(
        VENDOR + 'A_ReceptionVendor_' + name for name in ('AS_IdleBartering', 'AS_TalkLoop', 'AS_ShowBoothFull_Lt'))
    assets = {p: u.load_asset(p) for p in source_paths}
    require(all(assets.values()), 'All accepted owned assets must already exist; no implicit imports')
    require(isinstance(assets[BENCH], u.StaticMesh) and isinstance(assets[SHRUB], u.StaticMesh) and
            all(isinstance(assets[p], u.MaterialInterface) for p in (BENCH_MATERIAL, GREEN, BLACK)),
            'Require original meshes and existing material interfaces')
    plant_class = u.EditorAssetLibrary.load_blueprint_class(PLANT)
    require(plant_class is not None, 'Require the whole owned planter Blueprint')
    root = Path(u.Paths.project_dir())
    source_files = {root / ('Content' + p.removeprefix('/Game') + '.uasset'): None for p in source_paths}
    source_files = {p: _sha(p) for p in source_files}
    people = [_one(actors, label) for label, _, _ in STAFF]
    for actor in people:
        require(isinstance(actor, u.SSOutpostAmbientActor), 'Keep original reception staff actors')
        skeleton = actor.character_mesh.get_skeletal_mesh_asset().get_editor_property('skeleton')
        require(not actor.get_editor_property('route_points') and not actor.get_editor_property('drone') and
                not actor.get_editor_property('animation_managed_externally') and
                all(isinstance(assets[p], u.AnimSequence) and assets[p].get_editor_property('skeleton') == skeleton
                    for p in source_paths if p.startswith(VENDOR)), 'Recovered vendor clips must match stationary staff')
    halo = _one(actors, 'Atrium/Orbital halo')
    require(halo is not None and path(halo.get_component_by_class(u.StaticMeshComponent)
            .get_editor_property('static_mesh')).split('.')[0] == '/Game/OutpostSandbox/Geometry/SM_OutpostHalo',
            'Require the original physical central halo support')
    rows = [(r, kind, pos, u.Rotator(yaw=yaw), scale, 'Refine/CentralWelcomeArrival2/' + r)
            for r, kind, pos, yaw, scale in FURNITURE]
    rows += [(r, 'shrub', pos, u.Rotator(), 1.12, 'Refine/CentralWelcomeGreeneryLights1/' + r) for r, pos in FOLIAGE]
    rows += [(r, 'light', pos, u.MathLibrary.find_look_at_rotation(u.Vector(*pos), u.Vector(*aim)),
              1., 'Refine/CentralWelcomeGreeneryLights1/' + r) for r, pos, aim, _, _ in KEYS]
    selected = {r[0]: _role(actors, r[0], r[5]) for r in rows}
    require(not any(TAG in map(str, a.tags) and not any(a == v for v in selected.values()) for a in actors),
            'Unknown previously tagged welcome role; no broad cleanup')
    for role, kind, pos, rotation, scale, _ in rows:
        actor = selected[role]
        if actor is None:
            continue
        require(_pose_ok(actor, pos, rotation, scale), 'Existing role moved; preserve owner pose: ' + role)
        if kind == 'planter':
            require(actor.get_class() == plant_class, 'Existing role must be the original complete planter')
        elif kind == 'light':
            require(isinstance(actor, u.RectLight) and actor.get_attach_parent_actor() == halo,
                    'Existing key must retain the actual halo attachment')
        else:
            require(isinstance(actor, u.StaticMeshActor) and actor.get_component_by_class(u.StaticMeshComponent)
                    .get_editor_property('static_mesh') == assets[BENCH if kind == 'bench' else SHRUB],
                    'Existing role mesh differs: ' + role)
    originals = [a for a in actors if a in people or a == halo or a.get_name() == 'StaticMeshActor_5149' or
        a.get_actor_label() == 'Ground/Atrium' or a.get_actor_label().startswith('Refine/Reception/') or
        (isinstance(a, u.SSOutpostTerminal) and a.get_actor_label().startswith('Welcome/'))]
    require(sum(isinstance(a, u.SSOutpostTerminal) for a in originals) == 7, 'Keep all seven welcome actions')
    state = {'world': world, 'target_map': target_map, 'main': main, 'base_sha256': expected_map_sha256,
             'roles': selected, 'created': [], 'backups': [_backup(a, u) for a in selected.values() if a],
             'staff_before': [(a, a.get_editor_property('idle_animation'), list(a.get_editor_property('gesture_animations'))) for a in people],
             'protected': [(a, _snapshot(a, u)) for a in originals], 'assets': assets, 'halo': halo,
             'source_files': source_files, 'saved': False}
    try:
        with u.ScopedEditorTransaction('Install accepted central welcome composition'):
            for role, kind, pos, rotation, scale, _ in rows:
                actor = selected[role]
                if actor is None:
                    cls = plant_class if kind == 'planter' else u.RectLight if kind == 'light' else u.StaticMeshActor
                    actor = eas.spawn_actor_from_class(cls, u.Vector(*pos), rotation)
                    require(actor is not None, 'Cannot create welcome role: ' + role)
                    state['created'].append(actor)
                    selected[role] = actor
                    if kind == 'planter':
                        inherit_parent_scale_preserving_world(actor)
                    elif kind != 'light':
                        c = actor.get_component_by_class(u.StaticMeshComponent)
                        c.set_static_mesh(assets[BENCH if kind == 'bench' else SHRUB])
                        c.set_material(0, assets[BENCH_MATERIAL if kind == 'bench' else GREEN])
                        c.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS if kind == 'bench' else u.CollisionEnabled.NO_COLLISION)
                        actor.set_actor_enable_collision(kind == 'bench')
                    actor.set_actor_scale3d(u.Vector(scale, scale, scale))
                    if kind == 'light':
                        _, _, _, lumens, radius = next(r for r in KEYS if r[0] == role)
                        _light(actor, lumens, radius, u)
                        require(actor.attach_to_component(halo.get_component_by_class(u.StaticMeshComponent), u.Name(''),
                            u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, False),
                            'Cannot mount new key under the original halo')
                if kind == 'planter':
                    _planter(actor, assets[BLACK], u)
                if actor.get_actor_label() != PREFIX + role:
                    actor.set_actor_label(PREFIX + role)
                tags = list(actor.tags)
                for tag in (TAG, ROLE_TAG + role):
                    if tag not in map(str, tags):
                        tags.append(u.Name(tag))
                if list(map(str, actor.tags)) != list(map(str, tags)):
                    actor.tags = tags
            for actor, (_, idle, gesture) in zip(people, STAFF):
                desired = assets[VENDOR + 'A_ReceptionVendor_' + idle]
                if actor.get_editor_property('idle_animation') != desired:
                    actor.set_editor_property('idle_animation', desired)
                desired = [assets[VENDOR + 'A_ReceptionVendor_' + gesture]]
                if list(actor.get_editor_property('gesture_animations')) != desired:
                    actor.set_editor_property('gesture_animations', desired)
        state['verification'] = verify(u, state)
        return state
    except Exception:
        rollback(u, state)
        raise


def verify(u, state, check_saved_base=True):
    _, _, actors = _context(u, state['target_map'])
    require(not check_saved_base or _sha(state['main']) == state['base_sha256'], 'Saved Main changed before root save')
    require(all(_sha(p) == digest for p, digest in state['source_files'].items()), 'Existing owned source packages changed')
    require(len(state['roles']) == 13 and all(a in actors and ROLE_TAG + role in map(str, a.tags)
            for role, a in state['roles'].items()), 'Thirteen unique accepted role actors required')
    for actor, before in state['protected']:
        after = _snapshot(actor, u)
        expected = dict(before)
        if actor.get_actor_label() in [r[0] for r in STAFF]:
            _, idle, gesture = next(r for r in STAFF if r[0] == actor.get_actor_label())
            expected['vendor'] = {**before['vendor'], 'idle': path(state['assets'][VENDOR + 'A_ReceptionVendor_' + idle]),
                'gestures': [path(state['assets'][VENDOR + 'A_ReceptionVendor_' + gesture])]}
        require(after == expected, 'Original central actor changed outside four vendor properties: ' + actor.get_actor_label())
    _verify_roles(u, state['roles'], state['halo'], state['assets'])
    return {'role_actor_count': 13, 'created_actor_count': len(state['created']),
            'adopted_actor_count': 13-len(state['created']), 'vendor_property_count': 4,
            'targeted_original_preservation_pass': True, 'new_assets': 0, 'saved': False,
            'limits': 'Accepted placed recipe; fresh saved-map replay, walking, contact and performance remain root checks.'}


def assert_ready_to_save(u, state):
    """Save remains root-owned; never persist the held T display trial by accident."""
    _, _, actors = _context(u, state['target_map'])
    require(not any(a.get_actor_label().startswith('Refine/OperationsPortraitPanels/') for a in actors),
            'Root must resolve/remove only its held T portrait trial before saving this shared map')
    return verify(u, state)


def rollback(u, state):
    """Independent restoration attempts; never save or remove an original actor."""
    _, eas, _ = _context(u, state['target_map'])
    errors = []
    operations = []
    for actor, idle, gestures in state['staff_before']:
        operations += [(lambda a=actor, v=idle: a.set_editor_property('idle_animation', v)),
                       (lambda a=actor, v=gestures: a.set_editor_property('gesture_animations', v))]
    for row in state['backups']:
        actor = row['actor']
        operations += [(lambda a=actor, v=row['label']: a.set_actor_label(v)),
                       (lambda a=actor, v=row['tags']: setattr(a, 'tags', v))]
        for c, overrides, visible, hidden, collision in row['parts']:
            operations += [(lambda c=c, v=overrides: c.set_editor_property('override_materials', v)),
                           (lambda c=c, v=visible: c.set_visibility(v, False)),
                           (lambda c=c, v=hidden: c.set_hidden_in_game(v, False)),
                           (lambda c=c, v=collision: c.set_collision_enabled(v))]
    for operation in operations:
        try:
            operation()
        except Exception as error:
            errors.append(str(error))
    for actor in reversed(state['created']):
        try:
            require(not actor.get_attached_actors(), 'Do not remove an unrelated attached child')
            require(eas.destroy_actor(actor), 'Cannot remove new owned welcome role')
        except Exception as error:
            errors.append(str(error))
    require(not errors, 'Central rollback incomplete: ' + '; '.join(errors))
    require(all(_snapshot(row['actor'], u) == row['snapshot'] and
                row['actor'].get_actor_label() == row['label'] and list(row['actor'].tags) == row['tags']
                for row in state['backups']) and
            all(_snapshot(a, u) == before for a, before in state['protected']), 'Restored central state differs')
    return {'restored': True, 'saved': False}
