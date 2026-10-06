"""Bounded arcade service placement and visible local lighting; lead saves/renders."""
import hashlib
import json
import math
from pathlib import Path

from OutpostGeometryUtils import mesh_union
from PlaceStationLocalArcade import (_bounds, _existing_proposal, _floor, _hit, _intersects,
                                    _one, _require, _visible, _world)
from RefineStationSocialSeatedCrew import _geometry
from StationRefinementSupport import transform_record


MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
PREFIX = 'Refine/ArcadePresentation/'
BASE = '/Game/OutpostSandbox/StationRefinement/ArcadePresentation20261006'
CREDIT = 'Refine/LocalArcade/CreditExchange/Body'
COFFER = '/Game/CyberPunkBarAssetSet01/Materials/M_BarCeilingMat02'
FIXTURE = '/Game/CyberpunkRestaurant/Meshes/SM_Fluorescent_Light_01'
PROBE_SHA = 'cfd2105ed5d287bf63387cccb52ba1d9ed552ea3ef9e95c93616015e788aa602'
HOUSING = '/Game/OutpostSandbox/StationRefinement/SocialVisualFinish/MI_AisleLampLit'
OLD_GLASS = '/Game/OutpostSandbox/StationRefinement/SocialVisualFinish/MI_AisleLampGlassLit'
GRAPHITE = '/Game/OutpostSandbox/Materials/M_OutpostGraphite'


def _path(asset):
    return asset.get_path_name().split('.')[0] if asset else None


def _graph(material, u):
    edit = u.MaterialEditingLibrary
    result = {'asset': _path(material), 'class': material.get_class().get_name()}
    if isinstance(material, u.MaterialInstance):
        from RefineStationSocialVisualFinish import _values
        result.update(_values(edit, material))
        result['parent'] = _path(material.get_editor_property('parent'))
    else:
        result['scalars'] = {str(n): edit.get_material_default_scalar_parameter_value(material, n)
                             for n in edit.get_scalar_parameter_names(material)}
        result['vectors'] = {str(n): list(edit.get_material_default_vector_parameter_value(material, n).to_tuple())
                             for n in edit.get_vector_parameter_names(material)}
        result['textures'] = {str(n): _path(edit.get_material_default_texture_parameter_value(material, n))
                              for n in edit.get_texture_parameter_names(material)}
        result['nodes'] = []
        for node in edit.get_material_expressions(material):
            row = {'name': node.get_name(), 'class': node.get_class().get_name(),
                   'inputs': [v.get_name() if v else None for v in edit.get_inputs_for_material_expression(material, node)]}
            # These reflected properties exist on the named expression classes.
            for cls, fields in [('MaterialExpressionConstant', ('r',)),
                                ('MaterialExpressionConstant3Vector', ('constant',)),
                                ('MaterialExpressionVectorParameter', ('parameter_name', 'default_value')),
                                ('MaterialExpressionScalarParameter', ('parameter_name', 'default_value')),
                                ('MaterialExpressionTextureSample', ('texture',))]:
                if isinstance(node, getattr(u, cls)):
                    for field in fields:
                        value = node.get_editor_property(field)
                        row[field] = list(value.to_tuple()) if hasattr(value, 'to_tuple') else (
                            _path(value) if hasattr(value, 'get_path_name') else str(value) if field == 'parameter_name' else value)
            result['nodes'].append(row)
        result['outputs'] = {str(prop): n.get_name() if n else None for prop in
                             (u.MaterialProperty.MP_EMISSIVE_COLOR, u.MaterialProperty.MP_BASE_COLOR,
                              u.MaterialProperty.MP_OPACITY, u.MaterialProperty.MP_OPACITY_MASK)
                             for n in [edit.get_material_property_input_node(material, prop)]}
    return result


def _fixture_geometry(component, u):
    dynamic, geometry = _geometry(component.static_mesh, False, u)
    transform = component.get_world_transform()
    groups = {}
    for index, face in enumerate(geometry['triangles']):
        slot, valid = u.GeometryScript_Materials.get_triangle_material_id(dynamic, index)
        _require(valid, 'Fixture triangle has no native material ID')
        points = [u.MathLibrary.transform_location(transform, u.Vector(*geometry['vertices'][i])) for i in face]
        a, b = points[1]-points[0], points[2]-points[0]
        cross = (a.y*b.z-a.z*b.y, a.z*b.x-a.x*b.z, a.x*b.y-a.y*b.x)
        length = math.sqrt(sum(v*v for v in cross))
        direction = 'down' if length and cross[2]/length < -.7 else 'up' if length and cross[2]/length > .7 else 'side'
        row = groups.setdefault(str(slot)+'/'+direction, {'triangles': 0, 'area_cm2': 0., 'min': [1.e9]*3, 'max': [-1.e9]*3})
        row['triangles'] += 1
        row['area_cm2'] += length*.5
        for point in points:
            for axis, val in enumerate(point.to_tuple()):
                row['min'][axis] = min(row['min'][axis], val)
                row['max'][axis] = max(row['max'][axis], val)
    return groups


def probe(ctx):
    """Read-only actual slots/geometry/material graph and two service-bay candidates."""
    import unreal as u
    world = _world(u)
    credit = _one(ctx.actors, CREDIT)
    capsule = u.get_default_object(u.load_class(None, '/Script/SpaceSurvival.SSWalker')).get_component_by_class(u.CapsuleComponent)
    radius, half = capsule.get_unscaled_capsule_radius(), capsule.get_unscaled_capsule_half_height()
    candidates = []
    for y in (-3080., -3320.):
        row = _existing_proposal(credit, (5370.75, y), 90., u)
        lo, hi = row['bounds_cm']
        center = [(lo[i]+hi[i])*.5 for i in range(3)]
        standing = (lo[0]-radius-12., y)
        row['standing'] = standing
        row['volume_hit'] = _hit(u.SystemLibrary.box_trace_single_by_profile(world, u.Vector(*center),
            u.Vector(center[0], center[1], center[2]+.1), u.Vector(*[(hi[i]-lo[i])*.5-2 for i in range(3)]),
            u.Rotator(), 'Pawn', False, [credit], u.DrawDebugTrace.NONE, True))
        row['approach_hits'] = []
        for start, end in [((5080., -3750.), (5080., y)), ((5080., y), standing)]:
            row['approach_hits'].append(_hit(u.SystemLibrary.capsule_trace_single_by_profile(world,
                u.Vector(*start, half+3), u.Vector(*end, half+3), radius, half, 'Pawn', False,
                [credit], u.DrawDebugTrace.NONE, True)))
        row['floor'] = _floor(world, standing, [credit], u)
        row['visible_bounds_intersections'] = []
        for actor in ctx.actors:
            if actor == credit or not _visible(actor):
                continue
            try:
                bounds = _bounds(actor)
            except RuntimeError:
                continue
            if _intersects(row['bounds_cm'], bounds, -1):
                row['visible_bounds_intersections'].append({'label': actor.get_actor_label(), 'bounds': bounds})
        candidates.append(row)
    fixture = _one(ctx.actors, 'Refine/SocialAtmosphereFollowup/Aisle 1/Housing')
    component = fixture.get_component_by_class(u.StaticMeshComponent)
    materials = [_graph(m, u) for m in component.get_materials()]
    for row in materials:
        if row.get('parent'):
            row['parent_graph'] = _graph(ctx.asset(row['parent']), u)
    coffer = ctx.asset(COFFER)
    return {'credit_candidates': candidates, 'credit_current': transform_record(credit),
            'coffer': _graph(coffer, u), 'fixture_materials': materials,
            'fixture_triangle_groups': _fixture_geometry(component, u),
            'read_only': True, 'native_capsule': [radius, half]}


def _new_material(name, u, dirty):
    path = BASE + '/' + name
    _require(not u.EditorAssetLibrary.does_asset_exist(path), 'Preserve existing presentation asset: ' + path)
    material = u.AssetToolsHelpers.get_asset_tools().create_asset(name, BASE, u.Material, u.MaterialFactoryNew())
    _require(material, 'Private material creation failed')
    dirty.append(material)
    return material


def _diffuser(u, dirty):
    # Native slot1 is four upward-facing triangles. A two-sided frosted panel
    # makes the actual lens visible from below without changing vendor geometry.
    material = _new_material('M_FrostedTwoSidedDiffuser', u, dirty)
    material.set_editor_property('two_sided', True)
    material.set_editor_property('blend_mode', u.BlendMode.BLEND_OPAQUE)
    material.set_editor_property('shading_model', u.MaterialShadingModel.MSM_DEFAULT_LIT)
    edit = u.MaterialEditingLibrary
    for value, prop in [((.65, .62, .55, 1.), u.MaterialProperty.MP_BASE_COLOR),
                        ((2.2, 1.9, 1.5, 1.), u.MaterialProperty.MP_EMISSIVE_COLOR)]:
        node = edit.create_material_expression(material, u.MaterialExpressionConstant3Vector)
        node.set_editor_property('constant', u.LinearColor(*value))
        _require(edit.connect_material_property(node, '', prop), 'Diffuser color connection failed')
    rough = edit.create_material_expression(material, u.MaterialExpressionConstant)
    rough.set_editor_property('r', .55)
    _require(edit.connect_material_property(rough, '', u.MaterialProperty.MP_ROUGHNESS), 'Diffuser roughness connection failed')
    _require(not edit.recompile_material(material), 'Private diffuser failed material compilation')
    _require(material.get_editor_property('two_sided') and material.get_editor_property('blend_mode') == u.BlendMode.BLEND_OPAQUE,
             'Frosted diffuser facing/blend readback failed')
    return material


def _supported_light(ctx, u, name, location, yaw, roll, width, lumens, radius, diffuser, report):
    lamp = ctx.raw(PREFIX+name+'/Housing', FIXTURE, location, (0., yaw, roll), collision=False)
    native = lamp.static_mesh_component.static_mesh.get_bounds()
    scale = width/(2*native.box_extent.x)
    lamp.set_actor_scale3d(u.Vector(scale, scale, scale))
    component = lamp.static_mesh_component
    component.set_material(0, ctx.asset(HOUSING))
    component.set_material(1, diffuser)
    transform = component.get_world_transform()
    center, extent = mesh_union(lamp)
    _require(center.z-extent.z > 285., 'Arcade fixture violates overhead clearance')
    # Check visible structural/prop bounds before adding two thin suspension rods.
    for actor in ctx.actors:
        if not _visible(actor) or not actor.get_actor_label().startswith(('Engineering/', 'Refine/', 'Lounge_', 'QuietCeiling/')):
            continue
        try:
            bounds = _bounds(actor)
        except RuntimeError:
            continue
        _require(not _intersects(_bounds(lamp), bounds, -1.), 'Mounted arcade fixture intersects '+actor.get_actor_label())
    supports = []
    for side in (-1., 1.):
        point = u.MathLibrary.transform_location(transform, u.Vector(side*native.box_extent.x*.68, 0, native.box_extent.z))
        ceilings = []
        for actor in ctx.actors:
            if not _visible(actor) or not actor.get_actor_label().startswith(('QuietCeiling/Engineering/Panel ', 'Engineering/Ceiling panel')):
                continue
            c, e = mesh_union(actor)
            if abs(c.x-point.x) <= e.x+.01 and abs(c.y-point.y) <= e.y+.01 and point.z < c.z-e.z < 425.:
                ceilings.append((c.z-e.z, actor))
        _require(ceilings, 'No actual ceiling panel above arcade suspension')
        top, ceiling = min(ceilings, key=lambda row: row[0])
        ctx.box(PREFIX+name+'/Hanger '+str(int(side)), (point.x, point.y, (point.z+top)*.5),
                (1.5, 1.5, top-point.z), GRAPHITE, False)
        supports.append({'ceiling': ceiling.get_actor_label(), 'bottom': list(point.to_tuple()), 'top_z': top})
    origin = u.MathLibrary.transform_location(transform, u.Vector())
    normal = u.MathLibrary.transform_location(transform, u.Vector(0., 0., -1.))-origin
    normal = normal/normal.length()
    expected_direction = u.Vector(1., 0., -1.) if yaw == 90. else u.Vector(0., -1., -1.)
    alignment = (normal.x*expected_direction.x+normal.y*expected_direction.y+normal.z*expected_direction.z)/expected_direction.length()
    _require(alignment > .97, 'New native diffuser does not face the arcade surfaces')
    # The existing lens plane is -11.94 local Z; start just beyond that plane.
    position = u.MathLibrary.transform_location(transform, u.Vector(0., 0., -14.))
    light = ctx.eas.spawn_actor_from_class(u.RectLight, position, u.MathLibrary.find_look_at_rotation(position, position+normal*100.))
    ctx.register(light, PREFIX+name+'/Face wash')
    c = light.get_component_by_class(u.RectLightComponent)
    c.set_mobility(u.ComponentMobility.MOVABLE)
    c.set_intensity_units(u.LightUnits.LUMENS)
    c.set_intensity(lumens)
    c.set_attenuation_radius(radius)
    c.set_source_width(width*.9)
    c.set_source_height(18.)
    c.set_editor_property('use_temperature', True)
    c.set_editor_property('temperature', 4100.)
    c.set_editor_property('specular_scale', .18)
    c.set_editor_property('indirect_lighting_intensity', .5)
    c.set_editor_property('volumetric_scattering_intensity', 0.)
    c.set_cast_shadows(False)
    _require(light.attach_to_component(component, u.Name(''), u.AttachmentRule.KEEP_WORLD,
             u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, False), 'Arcade light failed physical-housing attachment')
    _require(abs(float(c.intensity)-lumens) < .01 and abs(float(c.attenuation_radius)-radius) < .01,
             'Arcade local-light readback failed')
    report.append({'housing': lamp.get_path_name(), 'supports': supports, 'lumens': lumens,
                   'radius_cm': radius, 'kelvin': 4100., 'diffuser_normal_world': list(normal.to_tuple()),
                   'fixture_bounds': _bounds(lamp), 'light_position': list(position.to_tuple())})


def apply(ctx, expected_map_sha256):
    """Stage a single measured service move and local material/light corrections."""
    import unreal as u
    from PlaceStationLocalArcade import _validate
    from RefineStationLoungeCeiling import _snapshot
    world = _world(u)
    root = Path(u.Paths.project_dir()).resolve()
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    map_file = root/('Content/'+MAP[6:]+'.umap')
    _require(sha(map_file) == expected_map_sha256, 'Owner preview changed since lead receipt')
    probe_file = root/'.agent/local/StationRefinement/StationArcadePresentationProbe1.json'
    _require(sha(probe_file) == PROBE_SHA, 'Native presentation probe changed')
    evidence = json.loads(probe_file.read_text(encoding='utf-8'))
    _require(evidence['success'] and evidence['before_sha256'] == evidence['after_sha256'], 'Native probe did not preserve map')
    _require(not any(a.get_actor_label().startswith(PREFIX) for a in ctx.actors), 'Preserve existing arcade presentation')
    credit = _one(ctx.actors, CREDIT)
    _require(transform_record(credit) == evidence['probe']['credit_current'], 'Credit terminal has moved since probe')
    before = {a.get_path_name(): _snapshot(a, u) for a in ctx.actors}
    source_files = {}
    def guard(package):
        path = root/('Content/'+package.split('.')[0][6:]+'.uasset')
        source_files[str(path)] = sha(path)
    for package in (COFFER, FIXTURE, HOUSING, OLD_GLASS, GRAPHITE):
        guard(package)
    for row in evidence['probe']['coffer']['nodes']:
        if row.get('texture'):
            guard(row['texture'])
    guard(_path(credit.static_mesh_component.static_mesh))
    candidate = evidence['probe']['credit_candidates'][0]
    _require(not candidate['volume_hit'] and not any(candidate['approach_hits']), 'Reviewed service alcove failed clearance')
    ctx.move(credit, candidate['location'], (0., candidate['yaw'], 0.))
    _require(max(abs(_bounds(credit)[e][i]-candidate['bounds_cm'][e][i]) for e in range(2) for i in range(3)) < .1,
             'Credit terminal differs from measured alcove placement')
    clearance = _validate(world, [candidate], {CREDIT: [credit]}, u)
    radius, half = clearance['capsule_radius_cm'], clearance['capsule_half_height_cm']
    routes = [((5080., -3750.), (5080., -3080.)), ((5080., -3080.), tuple(candidate['standing']))]
    for start, end in routes:
        hit = _hit(u.SystemLibrary.capsule_trace_single_by_profile(world, u.Vector(*start, half+3),
            u.Vector(*end, half+3), radius, half, 'Pawn', False, [], u.DrawDebugTrace.NONE, True))
        _require(hit is None, 'New service approach blocked after actual move: '+repr(hit))
    dirty, material_changes = [], {}
    diffuser = _diffuser(u, dirty)
    for index in (1, 2):
        # Owner explicitly likes the existing trim. Inspect it without authoring
        # a derivative or changing its slot; the full actor snapshot guards it.
        actor = _one(ctx.actors, 'Refine/LoungeCeiling/Coffer '+str(index))
        _require([_path(m) for m in actor.static_mesh_component.get_materials()] == [COFFER], 'Native coffer slot changed')
        actor = _one(ctx.actors, 'Refine/SocialAtmosphereFollowup/Aisle %d/Housing' % index)
        component = actor.static_mesh_component
        _require(_path(component.static_mesh) == FIXTURE and [_path(m) for m in component.get_materials()] == [HOUSING, OLD_GLASS],
                 'Reviewed central fixture slots changed')
        component.set_material(1, diffuser)
        material_changes[actor.get_path_name()] = {component.get_path_name(): [component.get_material(0).get_path_name(), diffuser.get_path_name()]}
    lights = []
    for values in [('South left', (4800., -4090., 330.), 0., 47., 200., 1400., 520.),
                   ('South right', (5150., -4060., 330.), 0., 47., 200., 1400., 520.),
                   ('East service', (5195., -3350., 330.), 90., 37., 180., 1600., 600.)]:
        _supported_light(ctx, u, *values, diffuser, lights)
    for actor in ctx.actors:
        actual, expected = _snapshot(actor, u), dict(before[actor.get_path_name()])
        if actor == credit:
            expected['location'], expected['rotation'] = actual['location'], actual['rotation']
        if actor.get_path_name() in material_changes:
            expected['materials'] = material_changes[actor.get_path_name()]
        _require(actual == expected, 'Unexpected existing actor/material/light change: '+actor.get_actor_label())
    _require(all(sha(Path(path)) == digest for path, digest in source_files.items()), 'Presentation changed original source packages')
    _require(sha(map_file) == expected_map_sha256, 'Presentation helper unexpectedly saved map')
    return {'dirty_assets': dirty, 'credit_move': candidate, 'clearance': clearance, 'service_routes': routes,
            'coffer_preserved': True, 'coffer_material': COFFER, 'new_local_lights': lights,
            'center_diffuser': {'native_slot': 1, 'native_up_triangles': 4, 'two_sided': True,
                               'material': diffuser.get_path_name(), 'existing_light_intensity_unchanged': True},
            'source_sha256': source_files, 'protected_existing_actor_count': len(before),
            'changed_existing_material_actors': list(material_changes), 'map_before_sha256': expected_map_sha256,
            'saved': False, 'limits': 'Authoring guards only; matched fresh room renders required'}
