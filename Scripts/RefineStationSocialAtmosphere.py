"""L-only foliage and practical-light finish; the lead owns loading and saving.

Uses measured native parts and placed component overrides. Vendor assets,
owner fixtures, the floor finish, other rooms and global exposure are untouched.
Run after the lead's furniture composition so retired pockets stay retired.
"""
import hashlib
import itertools
import json
from pathlib import Path

from OutpostGeometryUtils import mesh_union
from RefineStationSocialFinish import _aisle


MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
MAP_SHA = '762e366a4383aec3526d4b787b27f97b20a742dd0aa847ed7da498e21dab3d59'
PREFIX = 'Refine/SocialAtmosphere/'
SHRUB = '/Game/CyberpunkRestaurant/Meshes/SM_Shrub_With_LODs_01'
SHRUB_MATERIAL = '/Game/CyberpunkRestaurant/Materials/MI_Shrubs_01'
GREEN_SHRUB_MATERIAL = '/Game/OutpostSandbox/StationRefinement/SocialAtmosphere/Materials/MI_LoungeShrubs_Green'
FIXTURE = '/Game/CyberpunkRestaurant/Meshes/SM_Fluorescent_Light_01'
BLACK = '/Game/P1toP5_Bundle/P5_FruitSeller/Materials/Instances/Opaque/MI_Plastic04_Black_2'
GRAPHITE = '/Game/OutpostSandbox/Materials/M_OutpostGraphite'
PLANTERS = tuple('Refine/Social/Planter %d' % i for i in range(3)) + tuple(
    'Refine/SocialFinish/%s planted divider/%d' % (side, i)
    for side in ('West', 'East') for i in range(3))


def _one(actors, label):
    found = [a for a in actors if a.get_actor_label() == label]
    if len(found) != 1:
        raise RuntimeError('Expected one reviewed social actor: ' + label)
    return found[0]


def _pose(actor):
    t = actor.get_actor_transform()
    return (*t.translation.to_tuple(), *t.rotation.to_tuple(), *t.scale3d.to_tuple())


def _visible(actor):
    return not actor.is_temporarily_hidden_in_editor() and not actor.get_editor_property('hidden')


def _component_bounds(component, u):
    """Current native ISM geometry, including real instance world transforms."""
    bounds = component.static_mesh.get_bounds()
    transforms = [component.get_instance_transform(i, world_space=True)
                  for i in range(component.get_instance_count())] if isinstance(
                      component, u.InstancedStaticMeshComponent) else [component.get_world_transform()]
    low, high = [float('inf')] * 3, [float('-inf')] * 3
    for t in transforms:
        for signs in itertools.product((-1, 1), repeat=3):
            p = u.MathLibrary.transform_location(t, bounds.origin + u.Vector(
                *[getattr(bounds.box_extent, axis) * signs[i] for i, axis in enumerate('xyz')]))
            for i, axis in enumerate('xyz'):
                low[i], high[i] = min(low[i], getattr(p, axis)), max(high[i], getattr(p, axis))
    if not transforms:
        raise RuntimeError('Empty planter component: ' + component.get_path_name())
    return low, high


def _light_values(c):
    color = c.get_editor_property('light_color')
    row = {'intensity': float(c.intensity), 'radius': float(c.attenuation_radius),
           'color_rgba': [color.r, color.g, color.b, color.a],
           'specular': float(c.get_editor_property('specular_scale')),
           'shadows': bool(c.cast_shadows)}
    for name in ('source_width', 'source_height'):
        if hasattr(c, name):
            row[name] = float(c.get_editor_property(name))
    return row


def _tune_light(actor, u, lumens, radius, kelvin, specular=.18, width=None):
    c = actor.get_component_by_class(u.LocalLightComponent)
    if not c:
        raise RuntimeError('Expected native local light: ' + actor.get_actor_label())
    before = _light_values(c)
    c.set_intensity_units(u.LightUnits.LUMENS)
    c.set_intensity(lumens)
    c.set_attenuation_radius(radius)
    c.set_light_color(u.LinearColor(r=1., g=1., b=1., a=1.))
    c.set_editor_property('use_temperature', True)
    c.set_editor_property('temperature', float(kelvin))
    c.set_editor_property('specular_scale', specular)
    c.set_editor_property('volumetric_scattering_intensity', 0.)
    if width is not None:
        if not isinstance(c, u.RectLightComponent):
            raise RuntimeError('Source sizing requires RectLight')
        c.set_source_width(width)
        c.set_source_height(22.)
    return {'label': actor.get_actor_label(), 'before': before,
            'after': _light_values(c), 'temperature_kelvin': kelvin}


def _green_shrub_material(ctx, u):
    """Inherit native leaves; override only four measured foliage parameters."""
    parent = ctx.asset(SHRUB_MATERIAL)
    edit = u.MaterialEditingLibrary
    vectors = {'Color Tint': (.12, .42, .18), 'SSS Color Tint': (.08, .24, .055)}
    scalars = {'Desatuartion': .15, 'Normal Strength': 1.5}
    if not set(vectors).issubset({str(n) for n in edit.get_vector_parameter_names(parent)}):
        raise RuntimeError('Native shrub vector parameters differ from OrbitLounge1 probe')
    if not set(scalars).issubset({str(n) for n in edit.get_scalar_parameter_names(parent)}):
        raise RuntimeError('Native shrub scalar parameters differ from OrbitLounge1 probe')
    if u.EditorAssetLibrary.does_asset_exist(GREEN_SHRUB_MATERIAL):
        raise RuntimeError('Private shrub material already exists; review before replay')
    folder, name = GREEN_SHRUB_MATERIAL.rsplit('/', 1)
    material = u.AssetToolsHelpers.get_asset_tools().create_asset(
        name, folder, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
    edit.set_material_instance_parent(material, parent)
    # UE5.8 MaterialEditingLibrary.cpp initializes bResult=false in these
    # setters and never updates it, despite applying the value. Verify the
    # real parameter readbacks below instead of treating that return as truth.
    for name, rgb in vectors.items():
        edit.set_material_instance_vector_parameter_value(material, name, u.LinearColor(*rgb, 1.))
    for name, value in scalars.items():
        edit.set_material_instance_scalar_parameter_value(material, name, value)
    edit.update_material_instance(material)
    read_vectors = {}
    for name, rgb in vectors.items():
        value = edit.get_material_instance_vector_parameter_value(material, name)
        read_vectors[name] = [value.r, value.g, value.b]
        if max(abs(a - b) for a, b in zip(read_vectors[name], rgb)) > 1e-5:
            raise RuntimeError('Shrub vector readback mismatch: ' + name)
    read_scalars = {name: float(edit.get_material_instance_scalar_parameter_value(material, name))
                    for name in scalars}
    if any(abs(read_scalars[name] - value) > 1e-5 for name, value in scalars.items()):
        raise RuntimeError('Shrub scalar readback mismatch')
    return material, {'parent': parent.get_path_name(), 'asset': material.get_path_name(),
                      'vectors': read_vectors, 'scalars': read_scalars,
                      'native_graph_textures_and_other_parameters_inherited': True}


def apply(ctx):
    import unreal as u
    root = Path(u.Paths.project_dir()).resolve()
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name().split('.')[0] != MAP:
        raise RuntimeError('Atmosphere is restricted to the separate owner preview')
    file = root / ('Content/' + MAP[6:] + '.umap')
    if hashlib.sha256(file.read_bytes()).hexdigest() != MAP_SHA:
        raise RuntimeError('Expected ServiceFinish1 saved map; review any new baseline before rebinding')
    probe_file = root / '.agent/local/StationRefinement/SocialQualityProbe2.json'
    probe = json.loads(probe_file.read_text(encoding='utf-8'))
    if not probe['success'] or probe['map_sha256'] != MAP_SHA:
        raise RuntimeError('Missing native social material/actor evidence')
    actors = list(ctx.eas.get_all_level_actors())
    if any(a.get_actor_label().startswith(PREFIX) for a in actors):
        raise RuntimeError('Atmosphere already authored; do not duplicate the pass')
    poses = {a: _pose(a) for a in actors}
    before_routes = _aisle(world, u)
    source_paths = {SHRUB, SHRUB_MATERIAL, FIXTURE, BLACK, GRAPHITE}
    for label in PLANTERS:
        for c in _one(actors, label).get_components_by_class(u.StaticMeshComponent):
            if c.static_mesh:
                source_paths.add(c.static_mesh.get_path_name().split('.')[0])
    hashes = {p: hashlib.sha256((root / ('Content/' + p[6:] + '.uasset')).read_bytes()).hexdigest()
              for p in source_paths}
    shrub, fixture, black = [ctx.asset(p) for p in (SHRUB, FIXTURE, BLACK)]
    shrub_bounds = shrub.get_bounds()
    if max(abs(shrub_bounds.box_extent.x - 40.29723),
           abs(shrub_bounds.box_extent.y - 43.13400),
           abs(shrub_bounds.box_extent.z - 20.01692)) > .02:
        raise RuntimeError('Native foliage bounds differ from OrbitPoolProbeWrapper1')
    result = {'module': 'social_atmosphere', 'dirty_assets': [], 'planters': [],
              'fixtures': [], 'lights': [], 'retired_pockets_preserved': [],
              'source_probe_sha256': hashlib.sha256(probe_file.read_bytes()).hexdigest()}
    green_shrub, result['foliage_material'] = _green_shrub_material(ctx, u)
    result['dirty_assets'].append(green_shrub.get_path_name())

    for index, label in enumerate(PLANTERS):
        actor = _one(actors, label)
        if not _visible(actor):
            result['planters'].append({'label': label, 'skipped_retired': True})
            continue
        components = {c.get_name(): c for c in actor.get_components_by_class(u.StaticMeshComponent)}
        if set(components) != {'InstancedStaticMesh', 'InstancedStaticMesh1',
                               'InstancedStaticMesh2', 'InstancedStaticMesh3'}:
            raise RuntimeError('P5 planter assembly no longer matches native probe: ' + label)
        base, glass, soil, organic = [components[n] for n in
            ('InstancedStaticMesh', 'InstancedStaticMesh1', 'InstancedStaticMesh2', 'InstancedStaticMesh3')]
        if 'SM_Props_ConstructionPart115' not in glass.static_mesh.get_path_name():
            raise RuntimeError('Do not hide an unrecognized planter component')
        low, high = _component_bounds(soil, u)
        if not 0 < high[2] < 90 or min(high[i] - low[i] for i in (0, 1)) < 15:
            raise RuntimeError('Unexpected native planter soil surface: ' + label)
        cx, cy = (low[0] + high[0]) * .5, (low[1] + high[1]) * .5
        # Fit native foliage uniformly; the stem enters the measured soil.
        # Broad native leaves remain intact instead of stretching into a tree.
        scale = min((high[0] - low[0] + 18.) / (2 * shrub_bounds.box_extent.x),
                    (high[1] - low[1] + 18.) / (2 * shrub_bounds.box_extent.y), 1.12)
        for c in (glass, organic):
            c.set_visibility(False)
            c.set_hidden_in_game(True)
            c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        # The base's two native mirror-emissive slots read as blue circuitry.
        # Use its existing detailed black-plastic finish on this instance only.
        overrides = []
        for slot in range(base.get_num_materials()):
            material = base.get_material(slot)
            if material and 'MI_Glass01_Mirror_Emissive' in material.get_path_name():
                overrides.append({'slot': slot, 'before': material.get_path_name()})
                base.set_material(slot, black)
        plant = ctx.grounded('SocialAtmosphere/Planter %02d/Foliage' % index,
            shrub, (cx, cy), floor=high[2] - 1.5, scale=(scale,) * 3, collision=False)
        foliage_slots = []
        for slot in range(plant.static_mesh_component.get_num_materials()):
            original = plant.static_mesh_component.get_material(slot)
            if original and original.get_path_name().split('.')[0] == SHRUB_MATERIAL:
                plant.static_mesh_component.set_material(slot, green_shrub)
                foliage_slots.append(slot)
        if not foliage_slots:
            raise RuntimeError('Native shrub has no expected leaf material slot')
        pc, pe = mesh_union(plant)
        if abs(pc.z - pe.z - (high[2] - 1.5)) > .05:
            raise RuntimeError('Native foliage stem grounding failed')
        result['planters'].append({'label': label, 'hidden_components': [glass.get_name(), organic.get_name()],
            'base_instance_material_overrides': overrides, 'soil_min': low, 'soil_max': high,
            'foliage_material_override_slots': foliage_slots,
            'foliage_center': list(pc.to_tuple()), 'foliage_extent': list(pe.to_tuple()),
            'uniform_scale': scale, 'existing_actor_pose_preserved': _pose(actor) == poses[actor]})

    changed_poses = set()
    for index in (1, 2, 3):
        prefix = 'Refine/SocialFollowup/Conversation %d/' % index
        table = _one(actors, 'Refine/Social/Conversation %d/Low table' % index)
        if not _visible(table):
            result['retired_pockets_preserved'].append(index)
            continue
        tc, _ = mesh_union(table)
        old = [_one(actors, prefix + suffix) for suffix in ('Pendant', 'Drop -1', 'Drop 1')]
        for a in old:
            ctx.hide(a)
        body = ctx.raw('SocialAtmosphere/Pocket %d/Fluorescent housing' % index,
                       fixture, (tc.x, tc.y, 338), collision=False)
        bc, be = mesh_union(body)
        scale = 180. / (2 * be.x)
        body.set_actor_scale3d(u.Vector(scale, scale, scale))
        bc, be = mesh_union(body)
        body.set_actor_location(body.get_actor_location() + u.Vector(tc.x, tc.y, 338) - bc, False, False)
        bc, be = mesh_union(body)
        roof_z = 397.56696
        if bc.z - be.z < 300 or bc.z + be.z >= roof_z:
            raise RuntimeError('Native pendant has insufficient character/ceiling clearance')
        for side in (-1, 1):
            z0 = bc.z + be.z
            ctx.box('SocialAtmosphere/Pocket %d/Hanger %d' % (index, side),
                    (bc.x + side * 68, bc.y, (z0 + roof_z) * .5),
                    (1.5, 1.5, roof_z - z0), GRAPHITE, False)
        key = _one(actors, prefix + 'Table key')
        ctx.move(key, (bc.x, bc.y, bc.z - be.z - 1))
        changed_poses.add(key)
        result['lights'].append(_tune_light(key, u, 1100, 480, 3400, .16, 165))
        result['fixtures'].append({'pocket': index, 'native_mesh': FIXTURE,
            'center': list(bc.to_tuple()), 'extent': list(be.to_tuple()),
            'bottom_clearance_cm': bc.z - be.z, 'top_attached_to_cm': roof_z,
            'replaces_only_agent_pendant_labels': [a.get_actor_label() for a in old]})

    for index in (1, 2):
        actor = _one(actors, 'UsableLighting/Engineering/Ceiling %d' % index)
        # The center aisle is about 840 cm from each fill: a 900 cm radius
        # left it at near-zero falloff in OrbitRoomPreview1. Keep the small
        # emitter and room-local reach while restoring a readable floor.
        result['lights'].append(_tune_light(actor, u, 2800, 1500, 4400, .12, 220))
        actor = _one(actors, 'Refine/SocialFollowup/Bar/Counter key %d' % index)
        result['lights'].append(_tune_light(actor, u, 1100, 550, 3300, .2))
    for name, power, radius, kelvin in (
            ('Bar', 500, 520, 3500), ('West conversations', 350, 650, 3600),
            ('Food', 300, 520, 4200), ('Arcade', 350, 450, 6500)):
        actor = _one(actors, 'Refine/Social/Lighting/' + name)
        if _visible(actor):
            result['lights'].append(_tune_light(actor, u, power, radius, kelvin))
    for actor, pose in poses.items():
        if actor not in changed_poses and _pose(actor) != pose:
            raise RuntimeError('Unrelated actor pose changed: ' + actor.get_actor_label())
    result['after_routes'] = _aisle(world, u)
    result['before_routes'] = before_routes
    result['source_sha256'] = hashes
    result['vendor_files_unchanged'] = all(hashlib.sha256(
        (root / ('Content/' + p[6:] + '.uasset')).read_bytes()).hexdigest() == sha for p, sha in hashes.items())
    if not result['vendor_files_unchanged']:
        raise RuntimeError('Vendor source changed during placed-only atmosphere pass')
    result['owner_fixtures_global_exposure_floors_other_rooms_unchanged'] = True
    result['acceptance'] = 'Requires fresh room render and reloaded component overrides; no quality acceptance inferred'
    return result
