"""Adopt/check or place the measured upright R display from prepared assets.

No import, material authoring, map load/save or PIE. This recipe records the
native trial's geometry and parameters; it does not certify visual fit/cycling.
Existing trial actors can only be checked, never taken over by apply/rollback.
"""
import hashlib
import struct
from pathlib import Path

MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
PREFIX = 'Refine/CustomizationCampaigns/West wall '
PRIVATE = '/Game/OutpostSandbox/StationRefinement/CustomizationCampaigns20261008A'
MASTER = PRIVATE + '/Materials/M_R_UprightFive'
INSTANCE = PRIVATE + '/Materials/MI_R_WestBay'
FRAME = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Meshes/SM_Window200X250_V1_Part1'
PANE = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Meshes/SM_Window200X250_V2_Part2_DigitalWindow'
STORAGE = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Meshes/SM_WallPanel400X200_V1_SmartStorageUnit'
GLASS = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Materials/Instances/Translucent/MI_DigitalGlass_Window200X250'
GRAPHITE = '/Game/OutpostSandbox/Materials/M_OutpostGraphite'
POSITION = (2927.318441390991, 3221.666666666667, 75.)
TEXTURES = tuple(PRIVATE + '/Textures/T_' + name for name in (
    'R01_MorphClinic', 'R02_HologramDoctor', 'R03_ZeroGMassage',
    'R04_VacuumValet', 'R05_FirstContactPhoto'))
DIMENSIONS = ((853, 1280),) * 3 + ((1024, 1536),) * 2
SCALARS = {'CycleSeconds': 20., 'CrossfadeSeconds': .6,
           'PhaseOffsetSeconds': 0., 'DisplayBrightness': 8.}
PANELS = ('Lounge/Bay W2/Panel 0', 'Lounge/Bay W2/Panel 200')
BACKING = 'Lounge/Bay W2/Solid wall'
DONORS = ('Lounge/WestHoloWindow1/Frame', 'Lounge/WestHoloWindow1/AnimatedGlass')


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def path(value):
    return value.get_path_name() if value else None


def _object(package):
    return package + '.' + package.rsplit('/', 1)[1]


def _sha(filename):
    return hashlib.sha256(Path(filename).read_bytes()).hexdigest()


def _f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def _pose(actor):
    r = actor.get_actor_rotation()
    return (actor.get_actor_location().to_tuple(), (r.pitch, r.yaw, r.roll),
            actor.get_actor_scale3d().to_tuple())


def _record(actor):
    c = actor.static_mesh_component
    return {'path': path(actor), 'label': actor.get_actor_label(), 'pose': _pose(actor),
            'mesh': path(c.static_mesh), 'materials': tuple(path(m) for m in c.get_materials()),
            'visible': c.is_visible(), 'hidden_in_game': c.get_editor_property('hidden_in_game'),
            'hidden': actor.get_editor_property('hidden'), 'collision': c.get_collision_enabled(),
            'actor_collision': actor.get_actor_enable_collision(),
            'parent': path(actor.get_attach_parent_actor()),
            'children': tuple(path(a) for a in actor.get_attached_actors())}


def _one(actors, label, u):
    matches = [a for a in actors if a.get_actor_label() == label]
    require(len(matches) == 1 and isinstance(matches[0], u.StaticMeshActor),
            'Require one exact native actor: ' + label)
    return matches[0]


def _context(u, target_map, expected_map_sha256):
    require(target_map == MAP, 'Explicitly target the owner preview')
    sub = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    world = sub.get_editor_world()
    require(sub.get_game_world() is None and path(world) == _object(MAP),
            'Require the correct editor world with PIE stopped')
    main = Path(u.Paths.project_dir()) / ('Content' + MAP.removeprefix('/Game') + '.umap')
    require(len(expected_map_sha256) == 64 and _sha(main) == expected_map_sha256,
            'Bind the current saved map; unsaved owner changes are preserved')
    return world, u.get_editor_subsystem(u.EditorActorSubsystem), list(
        u.GameplayStatics.get_all_actors_of_class(world, u.Actor)), main


def _shader():
    code = 'float2 uv=float2(0.5+P.y/134.0,0.5-(P.z-125.0)/201.0);\n'
    code += 'float duration=max(CycleSeconds,1.0); float position=max(Clock+PhaseOffsetSeconds,0.0)/duration;\n'
    code += 'int cycleIndex=(int)floor(position); int current=cycleIndex%5; int following=(current+1)%5;\nfloat3 a=0,b=0;\n'
    for i, (width, height) in enumerate(DIMENSIONS):
        ratio = width / height
        aw, ah = min(1., ratio / (134. / 201.)), min(1., (134. / 201.) / ratio)
        code += f'float2 q{i}=(uv-.5)/float2({aw:.17g},{ah:.17g})+.5;\n'
        code += f'float inside{i}=step(0.,q{i}.x)*step(q{i}.x,1.)*step(0.,q{i}.y)*step(q{i}.y,1.);\n'
        sample = f'lerp(float3(.002,.004,.005),Texture2DSample(Artwork{i},Artwork{i}Sampler,clamp(q{i},0.,1.)).rgb,inside{i})'
        code += f'if(current=={i})a={sample}; if(following=={i})b={sample};\n'
    return code + ('float fade=clamp(CrossfadeSeconds,0.,duration*.25);\n'
                   'float alpha=fade>0.?smoothstep(duration-fade,duration,frac(position)*duration):0.;\n'
                   'return lerp(a,b,alpha)*DisplayBrightness;')


def _material(u, prepared_material):
    require(isinstance(prepared_material, u.MaterialInstanceConstant) and
            path(prepared_material) == _object(INSTANCE), 'Use the separately prepared R instance')
    edit, master = u.MaterialEditingLibrary, prepared_material.get_editor_property('parent')
    require(isinstance(master, u.Material) and path(master) == _object(MASTER) and
            master.get_editor_property('two_sided') and
            master.get_editor_property('blend_mode') == u.BlendMode.BLEND_OPAQUE and
            master.get_editor_property('shading_model') == u.MaterialShadingModel.MSM_UNLIT,
            'Keep the prepared private opaque two-sided master')
    nodes = list(edit.get_material_expressions(master))
    customs = [n for n in nodes if isinstance(n, u.MaterialExpressionCustom)]
    times = [n for n in nodes if isinstance(n, u.MaterialExpressionTime)]
    require(len(nodes) == 13 and len(customs) == len(times) == 1 and
            str(customs[0].get_editor_property('code')) == _shader() and
            edit.get_material_property_input_node(master, u.MaterialProperty.MP_EMISSIVE_COLOR) == customs[0] and
            not times[0].get_editor_property('ignore_pause') and
            not times[0].get_editor_property('override_period'), 'Keep the full 134x201 projection and five-index clock')
    textures = tuple(edit.get_material_instance_texture_parameter_value(prepared_material, 'Artwork' + str(i))
                     for i in range(5))
    require(tuple(path(t) for t in textures) == tuple(map(_object, TEXTURES)) and
            all(isinstance(t, u.Texture2D) and (t.blueprint_get_size_x(), t.blueprint_get_size_y()) == size
                for t, size in zip(textures, DIMENSIONS)), 'Require all five staged R campaigns in order')
    scalars = {k: float(edit.get_material_instance_scalar_parameter_value(prepared_material, k)) for k in SCALARS}
    require(scalars == {k: _f32(v) for k, v in SCALARS.items()}, 'Keep root-reviewed timing and brightness')
    return (path(master), path(prepared_material), tuple(path(t) for t in textures), scalars,
            tuple(tuple(v.export_text() for v in prepared_material.get_editor_property(k)) for k in
                  ('scalar_parameter_values', 'vector_parameter_values', 'texture_parameter_values')))


def _prepare(u, target_map, expected_map_sha256, prepared_material):
    _, _, actors, main = _context(u, target_map, expected_map_sha256)
    panels = tuple(_one(actors, label, u) for label in PANELS)
    backing = _one(actors, BACKING, u)
    donors = tuple(_one(actors, label, u) for label in DONORS)
    for actor, z in zip(panels, (0., 200.)):
        require(path(actor.static_mesh_component.static_mesh) == _object(STORAGE) and
                _pose(actor) == ((2900., 3216.666666666667, z), (0., 0., 0.), (1., .9166666666666667, 1.)) and
                actor.get_actor_location().y > 0. and
                actor.static_mesh_component.get_collision_enabled() == u.CollisionEnabled.NO_COLLISION,
                'Only the positive-Y decorative W2 source panels are eligible')
    require(path(backing.static_mesh_component.static_mesh) == '/Engine/BasicShapes/Cube.Cube' and
            _pose(backing) == ((2900., 3216.666666666667, 200.), (0., 0., 0.), (.3, 3.666666666666667, 4.)) and
            path(backing.static_mesh_component.get_material(0)) == _object(GRAPHITE), 'Require the existing W2 solid backing')
    for actor, mesh, count in zip(donors, (FRAME, PANE), (4, 2)):
        require(path(actor.static_mesh_component.static_mesh) == _object(mesh) and
                _pose(actor) == ((2940., 3020., 65.), (0., 180., 0.), (1., 1., 1.)) and
                actor.static_mesh_component.get_num_materials() == count, 'Preserve the original upright window donors')
    require(path(donors[1].static_mesh_component.get_material(0)) == _object(GLASS) and
            path(donors[1].static_mesh_component.get_material(1)) == _object(GLASS) and
            u.get_editor_subsystem(u.StaticMeshEditorSubsystem).get_lod_material_slot(
                donors[1].static_mesh_component.static_mesh, 0, 1) == 1, 'Native roomward section1 must remain slot1')
    roles = {kind: [a for a in actors if a.get_actor_label() == PREFIX + kind] for kind in ('Frame', 'Pane')}
    require(all(len(rows) <= 1 for rows in roles.values()) and
            not any(a.get_actor_label().startswith(PREFIX) and a not in sum(roles.values(), []) for a in actors),
            'Unknown or duplicate display role; no broad cleanup')
    root = Path(u.Paths.project_dir())
    files = {root / ('Content' + p.removeprefix('/Game') + '.uasset'): None for p in (FRAME, PANE, STORAGE, MASTER, INSTANCE) + TEXTURES}
    return {'target_map': target_map, 'base_sha256': expected_map_sha256, 'main': main,
            'material': prepared_material, 'material_before': _material(u, prepared_material),
            'panels': panels, 'backing': backing, 'donors': donors, 'roles': roles, 'created': [],
            'originals': tuple((a, _record(a)) for a in panels + (backing,) + donors),
            'source_files': {p: _sha(p) for p in files if p.exists()}}


def _verify(u, state):
    _, _, actors, _ = _context(u, state['target_map'], state['base_sha256'])
    require(_material(u, state['material']) == state['material_before'] and
            all(_sha(p) == digest for p, digest in state['source_files'].items()), 'Prepared/source assets changed')
    for actor, before in state['originals']:
        expected = dict(before)
        if actor in state['panels']:
            expected['visible'] = False
        if actor == state['backing']:
            expected['hidden'] = False
        require(actor in actors and _record(actor) == expected, 'Source state changed outside declared visibility fields')
    for kind, donor in zip(('Frame', 'Pane'), state['donors']):
        rows = [a for a in actors if a.get_actor_label() == PREFIX + kind]
        require(len(rows) == 1 and isinstance(rows[0], u.StaticMeshActor), 'Require exactly two display actors')
        actor, c = rows[0], rows[0].static_mesh_component
        materials = list(donor.static_mesh_component.get_materials())
        if kind == 'Pane':
            materials[1] = state['material']
        require(_pose(actor) == (POSITION, (0., 180., 0.), (1., 1., 1.)) and
                c.static_mesh == donor.static_mesh_component.static_mesh and list(c.get_materials()) == materials and
                c.get_collision_enabled() == u.CollisionEnabled.NO_COLLISION and
                str(c.get_collision_profile_name()) == 'NoCollision' and c.is_visible() and
                not c.get_editor_property('hidden_in_game') and not actor.get_editor_property('hidden') and
                actor.get_attach_parent_actor() is None and not actor.get_attached_actors(),
                'Keep exact upright geometry/original frame and rear glass')
    return {'role_actor_count': 2, 'changed_source_visibility_count': 3, 'new_asset_count': 0,
            'safe_art_rectangle_local_cm': {'y': (-67., 67.), 'z': (24.5, 225.5), 'front_slot': 1},
            'map_save_performed': False, 'visual_fit_and_cycle_acceptance': 'UNVERIFIED_BY_THIS_HELPER'}


def check_adoption(u, target_map, expected_map_sha256, prepared_material):
    """Read-only check; does not acquire ownership of an existing trial."""
    state = _prepare(u, target_map, expected_map_sha256, prepared_material)
    require(all(len(rows) == 1 for rows in state['roles'].values()), 'Two trial actors required')
    result = _verify(u, state)
    result['read_only'] = True
    return result


def apply(u, target_map, expected_map_sha256, prepared_material):
    """Fresh placement only, using caller-prepared assets; exact rollback on failure."""
    state = _prepare(u, target_map, expected_map_sha256, prepared_material)
    require(not any(state['roles'].values()), 'Existing trials are read-only: call check_adoption')
    require(all(a.static_mesh_component.is_visible() for a in state['panels']) and
            state['backing'].get_editor_property('hidden'), 'Fresh placement requires the original W2 visibility')
    _, eas, _, _ = _context(u, target_map, expected_map_sha256)
    try:
        with u.ScopedEditorTransaction('Place upright customization campaigns'):
            for kind, donor in zip(('Frame', 'Pane'), state['donors']):
                actor = eas.spawn_actor_from_class(u.StaticMeshActor, u.Vector(*POSITION), u.Rotator(yaw=180.))
                require(actor is not None, 'Cannot spawn ' + kind)
                state['created'].append(actor)
                actor.set_actor_label(PREFIX + kind)
                c = actor.static_mesh_component
                require(c.set_static_mesh(donor.static_mesh_component.static_mesh), 'Cannot assign native mesh')
                for index, material in enumerate(donor.static_mesh_component.get_materials()):
                    c.set_material(index, state['material'] if kind == 'Pane' and index == 1 else material)
                c.set_collision_profile_name('NoCollision')
            for panel in state['panels']:
                panel.static_mesh_component.set_visibility(False)
            state['backing'].set_actor_hidden_in_game(False)
        state['verification'] = _verify(u, state)
        return state
    except Exception as error:
        try:
            rollback(u, state)
        except Exception as cleanup:
            raise RuntimeError(f'Display apply failed: {error!r}; rollback failed: {cleanup!r}') from error
        raise


def rollback(u, state):
    """Attempt every owned actor/visibility restore independently; never delete donors."""
    _, eas, actors, _ = _context(u, state['target_map'], state['base_sha256'])
    errors, removed = [], 0
    for actor in reversed(state['created']):
        try:
            if actor in actors:
                require(eas.destroy_actor(actor), 'Cannot remove owned display')
                removed += 1
        except Exception as error:
            errors.append(repr(error))
    for actor, before in state['originals']:
        try:
            if actor in state['panels']:
                actor.static_mesh_component.set_visibility(before['visible'])
            elif actor == state['backing']:
                actor.set_actor_hidden_in_game(before['hidden'])
            require(_record(actor) == before, 'Original state was not restored')
        except Exception as error:
            errors.append(repr(error))
    state['rollback_errors'] = errors
    require(not errors, 'Display rollback failed: ' + '; '.join(errors))
    state['created'].clear()
    return {'removed_owned_actor_count': removed, 'restored_source_visibility_count': 3, 'map_save_performed': False}
