"""Add measured canopy rhythm and two physically supported illustrated TVs.

The lead owns native execution and saving. This helper preserves the complete
existing room, service mappings, light intensities and accepted lounge. Probe1
stays immutable; current geometry is rechecked before any import or spawn.
"""
import json
import math
import re

import RefineStationOperationsDensity as D
import RefineStationOperationsDensity3 as D3

ROOT, MAP, BASE, PREFIX = D.ROOT, D.MAP, D.BASE, D.PREFIX
PROBE = D.LOCAL / 'StationOperationsRoofProbe4.json'
PROBE_SHA = '231e8861c75d955a6f7ec250decbf050d0bc7981fdc629bca9d8c90f3e094454'
PLAN = D.LOCAL / 'OperationsDensityPlan2.json'
PLAN_SHA = '154eaba007a83cfae2b409d10c4ef5f445794d8005c9de32136ba669715a4f97'
SKY_FILE = D.Path('C:/Program Files/EpicGames2/UE_5.8/Engine/Content/BasicShapes/Sphere.uasset')
SKY_SHA = '0870a30b75af88e6117261b1ce6138ed90da85c90fde9fc39380705ab1870b61'
SKY_MATERIAL = '/Game/OutpostSandbox/Materials/MI_OutpostStars'
SKY_PARENT = '/Game/SpaceSurvival/Licensed/Atmosphere/M_RegionSky'
SKY_SOURCES = {SKY_MATERIAL: '4b9c2072eccf652bf057cae1976c51fd5486ff1b98dec2284fb14a43ea20b6e3',
               SKY_PARENT: '737388acccf2bccc7767d4fdaa54539703bc7fa7628f0ac9fa96552e905bb9f1'}
OUTPUTS = ('Textures/T_01_Engineering', 'Textures/T_02_Recovery',
           'Materials/M_01_Engineering', 'Materials/M_02_Recovery')


def _inputs(ctx, u, proof):
    original, sources, native = D._inputs(ctx, u)
    D._require(D._sha(PLAN) == PLAN_SHA, 'Reviewed trim-supported density plan changed')
    proposal = json.loads(PLAN.read_text(encoding='utf-8'))
    D._require(proposal['native_roof_survey_sha256'] == PROBE_SHA and
               len(proposal['parts']) == 13 and proposal['new_lights'] == 0 and
               proposal['parts'][-2:] == original['parts'][-2:] and
               proposal['source_sha256'] == original['source_sha256'],
               'Only new canopy row positions may differ from the frozen original plan')
    old_panels = [row for row in original['parts'][:12] if row['location'] != [7600., 0., 385.]]
    D._require(len(old_panels) == 11 and proposal['density_total_actor_count'] == 20 and
               proposal['retained_pendant_opening']['omitted_canopy_location_cm'] == [7600., 0., 385.],
               'Preserve the existing native pendant fixture through one deliberate canopy opening')
    for new, old in zip(proposal['parts'][:-2], old_panels):
        y = {-500.: -400., 0.: 0., 500.: 400.}[old['location'][1]]
        D._require(new['asset'] == old['asset'] and new['rotation_pyr'] == old['rotation_pyr'] and
                   new['scale'] == old['scale'] and new['location'] == [old['location'][0], y, 385.] and
                   new['name'] == 'Command canopy %d %d' % (old['location'][0], y) and
                   all(math.dist(new['bounds'][key], [old['bounds'][key][0],
                       old['bounds'][key][1]+y-old['location'][1], old['bounds'][key][2]]) < .000001
                       for key in ('minimum', 'maximum')), 'Canopy scope or measured bounds changed')
    rails = proposal['roof_rails']
    D._require(len(rails) == 3 and all(row['canopy_row_y_cm'] == y and row['rail_y_cm'] == y-98. and
               row['bottom_z_cm'] == 385. and row['required_height_band_cm'] == [385., 425.]
               for row, y in zip(rails, (-400., 0., 400.))), 'Exact three trim-mounted rails required')
    D._require(proof['height_assertion_or_authoring'] is False and len(proof['native_roof_actors']) == 28,
               'Require the successful diagnostic-only native roof survey')
    for package, digest in proof['source_sha256'].items():
        D._require(D._sha(D._asset_file(package)) == digest, 'Native roof survey source changed '+package)
    sources.update(proof['source_sha256'])
    return proposal, sources, native


def _roof_contacts(ctx, actors, native, proof, proposal, u):
    """Reproduce exact native Roof4 geometry, then contact its lower trim.

    Both survey modes agree. The previous failed385..425cm guard is retained;
    new rails span actual panel seams, avoiding the430.52cm inner recess.
    """
    from RefineStationSocialSeatedCrew import _geometry
    from RefineStationWorkroomComposition import _guard_pose
    expected = {row['label']: row for row in native if row['label'].startswith('QuietCeiling/Operations/Panel ')}
    observed = {row['label']: row for row in proof['native_roof_actors']}
    selected = [a for a in actors if a.get_actor_label() in expected]
    D._require(len(selected) == len(expected) == len(observed) == 28, 'Complete unchanged actual roof required')
    surfaces, cache = [], {}
    for actor in selected:
        label = actor.get_actor_label()
        _guard_pose(actor, expected[label]['transform'])
        row = observed[label]
        component = actor.get_component_by_class(u.StaticMeshComponent)
        D._require(component and component.static_mesh and component.get_name() == row['component'],
                   'Actual roof component identity changed')
        package = component.static_mesh.get_path_name().split('.')[0]
        D._require(package == row['mesh'], 'Actual roof mesh identity changed')
        if package not in cache:
            _, geometry = _geometry(component.static_mesh, False, u)
            recorded = proof['source_geometry'][package]
            D._require(geometry['vertices'] == recorded['raw']['vertices'] == recorded['build_applied']['vertices'] and
                       geometry['triangles'] == recorded['raw']['triangles'] == recorded['build_applied']['triangles'],
                       'Survey raw/build-applied/current native roof triangles differ')
            cache[package] = geometry
        transform = component.get_world_transform()
        actual = {'location': list(transform.translation.to_tuple()), 'rotation': list(transform.rotation.to_tuple()),
                  'scale': list(transform.scale3d.to_tuple())}
        D._require(all(math.dist(actual[key], row['current_transform'][key]) < .0001
                       for key in actual), 'Actual roof component transform changed')
        data = cache[package]
        vertices = [transform.transform_location(u.Vector(*point)).to_tuple() for point in data['vertices']]
        surfaces.append((actor, component, vertices, data['triangles']))
    rows = []
    for proposed in proposal['roof_rails']:
        y = proposed['rail_y_cm']
        candidates = []
        for actor, component, vertices, triangles in surfaces:
            for index, face in enumerate(triangles):
                polygon = [vertices[i] for i in face]
                for axis, limit, greater in ((0, 7000., True), (0, 8600., False),
                                             (1, y-5., True), (1, y+5., False)):
                    polygon = D._clip(polygon, axis, limit, greater)
                    if not polygon:
                        break
                if polygon:
                    point = min(polygon, key=lambda value: value[2])
                    candidates.append((point[2], point, actor, component, index))
        D._require(candidates, 'No actual lower roof trim at shared rail footprint')
        height, point, actor, component, index = min(candidates, key=lambda row: row[0])
        D._require(385. < height < 425. and abs(height-proposed['expected_native_trim_z_cm']) < .001,
                   'Retained roof height guard or measured trim contact failed')
        canopy_y = proposed['canopy_row_y_cm']
        D._require(min(y+5., canopy_y+100.)-max(y-5., canopy_y-100.) >= 7.-.001,
                   'Physical rail must overlap the native canopy top')
        rows.append({'y_cm': y, 'canopy_row_y_cm': canopy_y, 'underside_z_cm': height,
                     'contact_point_cm': list(point), 'actor': actor.get_path_name(),
                     'label': actor.get_actor_label(), 'component': component.get_name(), 'triangle': index,
                     'rail_length_cm': 1600., 'rail_depth_cm': 10., 'rail_height_cm': height-385.,
                     'native_contact_candidates': len(candidates), 'raw_build_current_geometry_identical': True})
    return rows


def _sky_readback(actors, u):
    """Verify actual authored backdrop; geometry remains eligible for clearance.

    AuthorOutpostSandbox creates this sphere with the owned sky material and
    NoCollision. No label or collision setting exempts it from triangle checks.
    """
    from OutpostGeometryUtils import mesh_union
    matches = [a for a in actors if 'OutpostRole:Sky' in set(map(str, a.tags))]
    D._require(len(matches) == 1 and D._sha(SKY_FILE) == SKY_SHA,
               'Require the unchanged authored sky source and one native backdrop')
    actor = matches[0]
    components = [c for c in actor.get_components_by_class(u.StaticMeshComponent) if c.static_mesh]
    D._require(len(components) == 1, 'Authored backdrop component identity differs')
    component = components[0]
    material = component.get_material(0)
    D._require(component.static_mesh.get_path_name().split('.')[0] == '/Engine/BasicShapes/Sphere' and
               component.get_collision_enabled() == u.CollisionEnabled.NO_COLLISION and
               not component.get_editor_property('cast_shadow') and isinstance(material, u.MaterialInstanceConstant) and
               material.get_path_name().split('.')[0] == SKY_MATERIAL and
               material.get_editor_property('parent').get_path_name().split('.')[0] == SKY_PARENT,
               'Authored sky mesh/material/parent/collision/shadow state differs')
    D._require(all(D._sha(D._asset_file(p)) == digest for p, digest in SKY_SOURCES.items()),
               'Protected sky material source changed')
    center, extent = mesh_union(actor)
    D._require(math.dist(center.to_tuple(), (0., 0., 0.)) < .1 and
               math.dist(extent.to_tuple(), (90000., 90000., 90000.)) < .1,
               'Native backdrop differs from the authored180000cm enclosing sphere')
    return {'actor': actor.get_path_name(), 'label': actor.get_actor_label(),
            'mesh': component.static_mesh.get_path_name(), 'material': material.get_path_name(),
            'material_parent': material.get_editor_property('parent').get_path_name(),
            'component_collision': str(component.get_collision_enabled()),
            'actor_collision': actor.get_actor_enable_collision(), 'cast_shadow': False,
            'native_world_center_cm': list(center.to_tuple()), 'native_world_extent_cm': list(extent.to_tuple()),
            'engine_source_sha256': {str(SKY_FILE): SKY_SHA}, 'material_source_sha256': SKY_SOURCES,
            'clearance_exempt': False}


def _fixture_surfaces(actor, u, cache):
    """Actual visible native surfaces, including all ISM world instances."""
    from RefineStationSocialSeatedCrew import _geometry
    surfaces, records = [], []
    for component in actor.get_components_by_class(u.StaticMeshComponent):
        if not component.static_mesh or not component.is_visible() or component.get_editor_property('hidden_in_game'):
            continue
        package = component.static_mesh.get_path_name()
        if package not in cache:
            _, cache[package] = _geometry(component.static_mesh, False, u)
        geometry = cache[package]
        transforms = [component.get_instance_transform(i, world_space=True)
                      for i in range(component.get_instance_count())] if isinstance(component, u.InstancedStaticMeshComponent) \
                     else [component.get_world_transform()]
        for transform in transforms:
            vertices = [transform.transform_location(u.Vector(*p)).to_tuple() for p in geometry['vertices']]
            surfaces.append((vertices, geometry['triangles']))
        records.append({'component': component.get_name(), 'mesh': package,
                        'source_geometry_sha256': D.hashlib.sha256(json.dumps(geometry, separators=(',', ':'),
                            sort_keys=True).encode('utf-8')).hexdigest(),
                        'native_triangle_count': len(geometry['triangles']), 'world_instance_count': len(transforms)})
    D._require(surfaces, 'Broadphase candidate has no actual visible fixture surface')
    return surfaces, records


def _box_clearance(actors, proposal, roof, u, cache):
    """Broadphase boxes then actual native fixture-triangle narrowphase.

    An enclosing sky or hollow mesh AABB is not a filled physical volume.
    Every broadphase candidate is checked; there is no label exemption.
    """
    from OutpostGeometryUtils import mesh_union
    from RefineStationLoungeCeiling import _triangle_box
    boxes = [{'name': p['name'], 'lo': p['bounds']['minimum'], 'hi': p['bounds']['maximum']}
             for p in proposal['parts']]
    boxes += [{'name': 'Trim roof rail %s' % r['y_cm'], 'lo': [7000., r['y_cm']-5., 385.],
               'hi': [8600., r['y_cm']+5., r['underside_z_cm']]} for r in roof]
    records = []
    for actor in actors:
        if actor.get_editor_property('hidden'):
            continue
        visible = [c for c in actor.get_components_by_class(u.StaticMeshComponent)
                   if c.static_mesh and c.is_visible() and not c.get_editor_property('hidden_in_game')]
        if not visible:
            continue
        center, extent = mesh_union(actor)
        lo, hi = (center-extent).to_tuple(), (center+extent).to_tuple()
        candidates = [box for box in boxes if all(box['lo'][i] < hi[i]-.05 and box['hi'][i] > lo[i]+.05 for i in range(3))]
        if not candidates:
            continue
        surfaces, source_rows = _fixture_surfaces(actor, u, cache)
        for box in candidates:
            middle = tuple((box['lo'][i]+box['hi'][i])*.5 for i in range(3))
            half = tuple(max(0., (box['hi'][i]-box['lo'][i])*.5-.05) for i in range(3))
            D._require(not any(_triangle_box([vertices[i] for i in face], middle, half)
                               for vertices, faces in surfaces for face in faces),
                       'New physical part intersects actual fixture triangles: '+box['name']+' / '+actor.get_actor_label())
        records.append({'label': actor.get_actor_label(), 'actual_native_surfaces': source_rows,
                        'new_box_candidates': [box['name'] for box in candidates],
                        'no_native_triangle_intersection': True})
    return {'new_box_count': len(boxes), 'all_existing_visible_static_fixtures_clear': True,
            'broadphase_candidates': records,
            'method': 'native transformed mesh bounds then native triangle/box SAT;0.05cm edge contact tolerance'}


def _art():
    D._require(D._sha(D.ART) == D.ART_SHA, 'Approved original ad manifest changed')
    manifest = json.loads(D.ART.read_text(encoding='utf-8'))
    D._require(manifest['dimensions'] == [2048, 1152] and len(manifest['outputs']) == 2,
               'Require exactly two reviewed landscape illustrations')
    rows = {}
    for row in manifest['outputs']:
        path = D.Path(row['file']).resolve()
        D._require(path.is_relative_to((D.LOCAL/'OperationsAds1/final').resolve()) and
                   D._sha(path) == row['sha256'] and row['size'] == [2048, 1152] and
                   row['fictional_decorative_only'], 'Final original ad pixels changed')
        rows[row['name']] = row
    D._require(set(rows) == {'01_Engineering', '02_Recovery'}, 'Unexpected ad campaigns')
    return rows


def _texture(name, row, u, dirty):
    path = BASE+'/Textures/T_'+name
    D._require(not u.EditorAssetLibrary.does_asset_exist(path), 'Preserve existing private texture')
    task = u.AssetImportTask()
    for key, value in {'filename': row['file'], 'destination_path': BASE+'/Textures',
                       'destination_name': 'T_'+name, 'automated': True,
                       'replace_existing': False, 'save': False}.items():
        task.set_editor_property(key, value)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = u.load_asset(path)
    D._require(isinstance(texture, u.Texture2D), 'Native ad texture import failed')
    for key, value in {'srgb': True, 'compression_settings': u.TextureCompressionSettings.TC_BC7,
                       'lod_group': u.TextureGroup.TEXTUREGROUP_WORLD,
                       'mip_gen_settings': u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP,
                       'address_x': u.TextureAddress.TA_CLAMP, 'address_y': u.TextureAddress.TA_CLAMP,
                       'never_stream': True}.items():
        texture.set_editor_property(key, value)
    D._require(texture.get_editor_property('never_stream') and texture.get_editor_property('srgb'),
               'Ad residency/color readback failed')
    dirty.append(texture.get_path_name())
    return texture


def _material(name, texture, u, dirty):
    path = BASE+'/Materials/M_'+name
    D._require(not u.EditorAssetLibrary.does_asset_exist(path), 'Preserve existing private display material')
    edit = u.MaterialEditingLibrary
    material = u.AssetToolsHelpers.get_asset_tools().create_asset(
        'M_'+name, BASE+'/Materials', u.Material, u.MaterialFactoryNew())
    D._require(material, 'Native display material creation failed')
    for key, value in {'shading_model': u.MaterialShadingModel.MSM_UNLIT,
                       'two_sided': True, 'blend_mode': u.BlendMode.BLEND_OPAQUE}.items():
        material.set_editor_property(key, value)

    def node(kind, **properties):
        expression = edit.create_material_expression(material, getattr(u, kind))
        D._require(expression is not None, 'Cannot create native material expression '+kind)
        for key, value in properties.items():
            expression.set_editor_property(key, value)
        return expression

    position = node('MaterialExpressionWorldPosition')
    local = node('MaterialExpressionTransformPosition',
                 transform_source_type=u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_WORLD,
                 transform_type=u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_LOCAL)
    D._require(edit.connect_material_expressions(position, '', local, ''), 'Local screen projection failed')
    artwork = node('MaterialExpressionTextureObjectParameter', parameter_name='Artwork', texture=texture,
                   sampler_type=u.MaterialSamplerType.SAMPLERTYPE_COLOR)
    vector = lambda value: 'float3('+','.join('%.11f'%v for v in value)+')'
    # The native quad is slightly wider than16:9. Preserve the artwork aspect
    # with a very narrow black side border; use the true plane, not its AABB.
    fit = D.SCREEN_SIZE[1]*(16./9.)/D.SCREEN_SIZE[0]
    code = 'float3 p=P-'+vector(D.SCREEN_CENTER)+';\n'
    code += ('float2 uv=float2(dot(p,'+vector(D.SCREEN_RIGHT)+')/%.11f+0.5,0.5-dot(p,'
             % D.SCREEN_SIZE[0]+vector(D.SCREEN_UP)+')/%.11f);\n'%D.SCREEN_SIZE[1])
    code += 'float side=(1.0-%.11f)*0.5;\n'%fit
    code += 'if(uv.x<side || uv.x>1.0-side) return float4(0,0,0,1);\n'
    code += 'uv.x=(uv.x-side)/%.11f;\n'%fit
    code += 'return float4(Texture2DSample(Artwork,ArtworkSampler,clamp(uv,0.0015,0.9985)).rgb,1);'
    custom = node('MaterialExpressionCustom', code=code, description='Original illustrated T ad / true screen fit',
                  output_type=u.CustomMaterialOutputType.CMOT_FLOAT4)
    inputs = []
    for name_in in ('P', 'Artwork'):
        pin = u.CustomInput()
        pin.set_editor_property('input_name', name_in)
        inputs.append(pin)
    custom.set_editor_property('inputs', inputs)
    D._require(edit.connect_material_expressions(local, '', custom, 'P') and
               edit.connect_material_expressions(artwork, '', custom, 'Artwork'), 'Artwork shader inputs failed')
    rgb = node('MaterialExpressionComponentMask', r=True, g=True, b=True, a=False)
    gain = node('MaterialExpressionScalarParameter', parameter_name='DisplayBrightness', default_value=6.)
    multiply = node('MaterialExpressionMultiply')
    D._require(edit.connect_material_expressions(custom, '', rgb, '') and
               edit.connect_material_expressions(rgb, '', multiply, 'A') and
               edit.connect_material_expressions(gain, '', multiply, 'B') and
               edit.connect_material_property(multiply, '', u.MaterialProperty.MP_EMISSIVE_COLOR),
               'Illustrated display color output failed')
    edit.layout_material_expressions(material)
    errors = edit.recompile_material(material)
    D._require(not errors, 'Native illustration shader errors: '+str(errors))
    dirty.append(material.get_path_name())
    return material, {'asset': material.get_path_name(), 'native_compile_errors': list(errors),
                      'true_screen_plane_projection': True, 'artwork_aspect': [16, 9],
                      'fitted_width_fraction': fit, 'display_gain': 6., 'shader': code}


def _bounds(actor):
    from OutpostGeometryUtils import mesh_union
    center, extent = mesh_union(actor)
    return list((center-extent).to_tuple()), list((center+extent).to_tuple())


def _attach(actor, component, u):
    D._require(component and actor.attach_to_component(component, u.Name(''),
        u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, False),
        'New hardware must attach to its actual physical support')


def _centred(ctx, label, asset, center, rotation, scale, u):
    from OutpostGeometryUtils import mesh_union
    actor = ctx.raw(PREFIX+label, asset, center, rotation, scale, True)
    actual, _ = mesh_union(actor)
    actor.set_actor_location(actor.get_actor_location()+u.Vector(
        *(center[i]-actual.to_tuple()[i] for i in range(3))), False, False)
    return actor


def _tv_fixture_clearance(ctx, actors, plans, u, cache):
    """Actual native TV triangles against existing fixture boxes, before import.

    TV02 is oblique and articulated: its transformed source AABB includes empty
    corners near the wall. Use the preserved true mesh triangles for this guard.
    The complete native frame geometry is unchanged by the screen-only shader.
    """
    from OutpostGeometryUtils import mesh_union
    from RefineStationLoungeCeiling import _triangle_box
    measured = json.loads(D.TV_PROBE.read_text(encoding='utf-8'))
    geometry = next(row['geometry'] for row in measured['meshes'] if row['asset'] == D.TV)
    rows = []
    for mount in plans:
        rotation = u.Rotator(yaw=mount['yaw_degrees'])
        plate_center = u.Vector((-.4339790344+17.8947677612), 0., 0.)
        offset = rotation.quaternion().rotate_vector(u.Vector(0., 5., 0.)-plate_center)
        pivot = u.Vector(mount['foot_xy_cm'][0]+offset.x,
                         mount['foot_xy_cm'][1]+offset.y, mount['pivot_z_cm'])
        vertices = [(pivot+rotation.quaternion().rotate_vector(u.Vector(*point))*D.TV_SCALE).to_tuple()
                    for point in geometry['vertices']]
        lo = [min(v[i] for v in vertices) for i in range(3)]
        hi = [max(v[i] for v in vertices) for i in range(3)]
        candidates = []
        for actor in actors:
            if actor.get_editor_property('hidden'):
                continue
            populated = [c for c in actor.get_components_by_class(u.StaticMeshComponent)
                         if c.static_mesh and c.is_visible() and not c.get_editor_property('hidden_in_game')]
            if not populated:
                continue
            center, extent = mesh_union(actor)
            alo, ahi = (center-extent).to_tuple(), (center+extent).to_tuple()
            if all(lo[i] < ahi[i]-.05 and hi[i] > alo[i]+.05 for i in range(3)):
                candidates.append((actor, center.to_tuple(), extent.to_tuple()))
        for actor, center, extent in candidates:
            # First establish whether the actual fixture surface reaches even
            # the enclosing true-TV triangle bounds. This clears the distant
            # sky surface without treating its giant AABB as filled volume.
            surfaces, _ = _fixture_surfaces(actor, u, cache)
            tv_middle = tuple((lo[i]+hi[i])*.5 for i in range(3))
            tv_half = tuple(max(0., (hi[i]-lo[i])*.5-.05) for i in range(3))
            if not any(_triangle_box([v[i] for i in face], tv_middle, tv_half)
                       for v, faces in surfaces for face in faces):
                continue
            # A small inward shrink excludes harmless exact edge contact.
            box = tuple(max(0., value-.05) for value in extent)
            D._require(not any(_triangle_box([vertices[i] for i in face], center, box)
                               for face in geometry['triangles']),
                       'Detailed TV intersects existing fixture: '+actor.get_actor_label())
        rows.append({'sign': mount['sign'], 'actual_native_triangle_bounds_cm': [lo, hi],
                     'existing_fixture_candidates': [a.get_actor_label() for a, _, _ in candidates],
                     'no_native_triangle_intersection': True})
    return rows


def apply(ctx, expected_map_sha256, native_probe_sha256):
    """Stage20 new parts/four private assets; preserve the native pendant opening."""
    import unreal as u
    from RefineStationOperationsComposition import _clearance
    from RefineStationOperationsDisplays import _state
    from RefineStationWorkroomComposition import _guard_pose
    map_file = ROOT/('Content/'+MAP[6:]+'.umap')
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    D._require(re.fullmatch('[0-9a-f]{64}', expected_map_sha256) and
               D._sha(map_file) == expected_map_sha256 and world.get_path_name().split('.')[0] == MAP,
               'Require exact latest saved owner-preview scene')
    D._require(native_probe_sha256 == PROBE_SHA and D._sha(PROBE) == native_probe_sha256,
               'Native density support proof changed')
    receipt = json.loads(PROBE.read_text(encoding='utf-8'))
    D._require(receipt['success'] and receipt['preservation_pass'] and not ctx.created,
               'Require successful immutable support probe and a fresh author context')
    proof = receipt['probe']
    proposal, sources, native = _inputs(ctx, u, proof)
    actors = list(ctx.eas.get_all_level_actors())
    D._require(not any(a.get_actor_label().startswith(PREFIX) for a in actors) and
               all(not u.EditorAssetLibrary.does_asset_exist(BASE+'/'+name) for name in OUTPUTS),
               'Preserve an existing density/ad pass')
    before = {a.get_path_name(): _state(a, u) for a in actors}
    sky_readback = _sky_readback(actors, u)
    sources.update(SKY_SOURCES)
    by_label = {a.get_actor_label(): a for a in actors}
    protected = [row for row in native if row['label'].startswith(
        ('Engineering/Primary workstation/', 'OperationsNative/Command island '))]
    D._require(len(protected) == 97, 'Complete Goliath29 and four17-part staffed pods required')
    for row in protected:
        D._require(row['label'] in by_label, 'Missing complete command/staff assembly')
        _guard_pose(by_label[row['label']], row['transform'])
    # Bind the successful Roof4 survey, rather than either failed support probe.
    # Current actual roof/floors/fixtures/routes must pass before any ad import.
    roof = _roof_contacts(ctx, actors, native, proof, proposal, u)
    geometry_cache = {}
    fixture_boxes = _box_clearance(actors, proposal, roof, u, geometry_cache)
    routes_before = _clearance(world, u)
    tv_plans = [D3.mount_plan(1 if part['location'][1] > 0 else -1)
                for part in proposal['parts'][-2:]]
    floor_proof = []
    for part in proposal['parts'][-2:]:
        sign = 1 if part['location'][1] > 0 else -1
        lo, hi = part['bounds']['minimum'], part['bounds']['maximum']
        points = [(7050., sign*1204.)]+[(x, y) for x in (lo[0]+5., hi[0]-5.)
                                      for y in (lo[1]+5., hi[1]-5.)]
        samples = [D3._floor(world, xy, [], u) for xy in points]
        floor_proof.append(samples)
    tv_floor = []
    for part, mount in zip(proposal['parts'][-2:], tv_plans):
        contacts = [D3._floor(world, xy, [], u) for xy in mount['foot_sample_xy_cm']]
        lo, hi = part['bounds']['minimum'], part['bounds']['maximum']
        D._require(all(abs(xy[1]) > max(abs(lo[1]), abs(hi[1]))+.5
                       for xy in mount['foot_sample_xy_cm']), 'TV floor post intersects fitted cabinet')
        tv_floor.append(contacts)
    profile = ctx.asset(D.POST).get_bounds()
    D._require(math.dist(profile.origin.to_tuple(), (0., 0., 100.)) < .01 and
               math.dist(profile.box_extent.to_tuple(), (5., 5., 100.)) < .01,
               'Actual native support differs from measured10x10x200 profile')
    fixture_clearance = _tv_fixture_clearance(ctx, actors, tv_plans, u, geometry_cache)
    art = _art()
    dirty, material_rows, materials = [], [], {}
    for name, row in art.items():
        texture = _texture(name, row, u, dirty)
        materials[name], record = _material(name, texture, u, dirty)
        material_rows.append(record)
    parts, rails = [], {}

    def record(actor, role, support=None):
        lo, hi = _bounds(actor)
        parts.append({'actor': actor.get_path_name(), 'label': actor.get_actor_label(), 'role': role,
                      'minimum_cm': lo, 'maximum_cm': hi,
                      'physical_support': support.get_path_name() if support else None})
        return actor

    for support in roof:
        y, top = support['y_cm'], support['underside_z_cm']
        rail = _centred(ctx, 'Shared roof rail %+.0f'%y, D.POST, (7800., y, (385.+top)*.5),
                        (90., 0., 0.), ((top-385.)/10., 1., 8.), u)
        rail.static_mesh_component.set_material(0, ctx.asset(D.DARK))
        lo, hi = _bounds(rail)
        D._require(math.dist(lo, (7000., y-5., 385.)) < .08 and
                   math.dist(hi, (8600., y+5., top)) < .08, 'Roof rail geometry/contact fit failed')
        parent = next(a for a in actors if a.get_path_name() == support['actor'])
        component = next(c for c in parent.get_components_by_class(u.StaticMeshComponent)
                         if c.get_name() == support['component'])
        _attach(rail, component, u)
        record(rail, 'profiled roof rail contacting actual roof triangle', parent)
        rails[support['canopy_row_y_cm']] = rail
    for part in proposal['parts'][:-2]:
        panel = ctx.raw(PREFIX+part['name'], D.CEILING, part['location'], part['rotation_pyr'], part['scale'])
        _attach(panel, rails[float(part['location'][1])].static_mesh_component, u)
        lo, hi = _bounds(panel)
        D._require(math.dist(lo, part['bounds']['minimum']) < .08 and
                   math.dist(hi, part['bounds']['maximum']) < .08, 'Canopy native pose/bounds changed')
        record(panel, 'native canopy rhythm preserving original pendant opening', rails[float(part['location'][1])])
    screens = []
    for index, (part, mount) in enumerate(zip(proposal['parts'][-2:], tv_plans)):
        cabinet = ctx.raw(PREFIX+part['name'], D.CABINET, part['location'], part['rotation_pyr'], part['scale'])
        lo, hi = _bounds(cabinet)
        D._require(math.dist(lo, part['bounds']['minimum']) < .08 and
                   math.dist(hi, part['bounds']['maximum']) < .08, 'Cabinet native pose/bounds changed')
        record(cabinet, 'native fitted storage unit on measured station floor')
        foot, low, top = mount['foot_xy_cm'], mount['base_z_cm'], mount['top_z_cm']
        post = ctx.grounded(PREFIX+'TV %d/Profiled floor mount'%index, D.POST, foot, floor=low,
                            yaw=mount['yaw_degrees'], scale=(4.4, 1., (top-low)/200.))
        post.static_mesh_component.set_material(0, ctx.asset(D.DARK))
        ground = by_label[tv_floor[index][0]['label']]
        floor_component = next(c for c in ground.get_components_by_class(u.StaticMeshComponent)
                               if c.get_name() == tv_floor[index][0]['component'])
        _attach(post, floor_component, u)
        record(post, 'physical TV mounting post with nine native floor contact points', ground)
        rotation = u.Rotator(yaw=mount['yaw_degrees'])
        plate_center = (.5*(-.4339790344+17.8947677612)*D.TV_SCALE, 0., 0.)
        front = rotation.quaternion().rotate_vector(u.Vector(0., 5., 0.))
        plate_offset = rotation.quaternion().rotate_vector(u.Vector(*plate_center))
        pivot = u.Vector(foot[0]+front.x-plate_offset.x, foot[1]+front.y-plate_offset.y, mount['pivot_z_cm'])
        tv = ctx.raw(PREFIX+'TV %d/Owned articulated frame'%index, D.TV, pivot, rotation, (D.TV_SCALE,)*3, False)
        component = tv.static_mesh_component
        original = [component.get_material(i).get_path_name() for i in range(component.get_num_materials())]
        D._require(len(original) == 8, 'Preserve seven native TV body slots and measured screen slot5')
        campaign = ('01_Engineering', '02_Recovery')[index]
        component.set_material(5, materials[campaign])
        D._require(all(component.get_material(i).get_path_name() == original[i] for i in range(8) if i != 5),
                   'Native TV body materials changed')
        _attach(tv, post.static_mesh_component, u)
        lo, hi = _bounds(tv)
        D._require(hi[2] < 310. and lo[2] > 100. and lo[0] > 6800. and hi[0] < 7250. and
                   lo[1] > -1300. and hi[1] < 1300., 'TV exceeds measured quiet alcove envelope')
        record(tv, 'owned detailed TV with one original illustrated campaign', post)
        screen_center = pivot+rotation.quaternion().rotate_vector(u.Vector(*D.SCREEN_CENTER))*D.TV_SCALE
        face = rotation.quaternion().rotate_vector(u.Vector(*mount['face_normal_source']))
        D._require(abs(face.x) < .0001 and face.y*mount['sign'] < -.999 and
                   abs(screen_center.z-225.) < .01, 'Measured TV screen does not face inward')
        screens.append({'campaign': campaign, 'frame': tv.get_path_name(), 'support': mount,
                        'native_floor_contact_samples': tv_floor[index], 'screen_center_cm': list(screen_center.to_tuple()),
                        'screen_front_world': list(face.to_tuple()), 'body_slots_preserved': original,
                        'native_slot5_material': materials[campaign].get_path_name(),
                        'true_aperture_probe_sha256': D.TV_PROBE_SHA})
    u.AutomationLibrary.finish_loading_before_screenshot()
    routes_after = _clearance(world, u)
    D._require(len(ctx.created) == len(parts) == 20 and len(dirty) == len(set(dirty)) == 4,
               'Unexpected density/ad scope')
    D._require(all(_state(a, u) == before[a.get_path_name()] for a in actors),
               'Existing actor pose/material/light/service/operator state changed')
    D._require(D._sha(map_file) == expected_map_sha256 and
               all(D._sha(D._asset_file(p)) == digest for p, digest in sources.items()) and
               D._sha(SKY_FILE) == SKY_SHA,
               'Helper must not save or change protected source packages')
    return {'dirty_assets': dirty, 'source_sha256': sources, 'parts': parts, 'screens': screens,
            'materials': material_rows, 'art_manifest_sha256': D.ART_SHA, 'plan_sha256': PLAN_SHA,
            'native_support_probe_sha256': native_probe_sha256, 'roof_supports': roof,
            'cabinet_floor_samples': floor_proof, 'routes_before': routes_before, 'routes_after': routes_after,
            'tv_actual_triangle_fixture_clearance': fixture_clearance,
            'canopy_storage_rail_fixture_clearance': fixture_boxes,
            'native_sky_backdrop_readback': sky_readback, 'engine_source_sha256': {str(SKY_FILE): SKY_SHA},
            'existing_actors_preserved': len(actors), 'existing_services_preserved': True,
            'existing_staff_and_command_parts_preserved': len(protected), 'new_lights': 0,
            'limits': 'Static native support/capsule evidence only. Saved pixels and ordinary walking require fresh review.'}
