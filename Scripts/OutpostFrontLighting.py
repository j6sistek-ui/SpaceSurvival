"""Three directed, fixture-supported light replacements for the private outpost.

The existing Engineering task point becomes a broad workstation-front key. Two
middle-storey tower points become shallow facade washes. Originals stay present
with parameters intact and visibility off; there is no additive double lighting.
One native housing and hanger visibly support the previously bare Engineering
task-light position. No engine launch, asset/map save, exposure or material edits.
"""
import json
import math
import os
from pathlib import Path

TARGET = '/Game/OutpostSandbox/L_AsteroidOutpost'
PREFIX = 'FrontLighting/'
TAG = 'OutpostFrontLighting'
MOUNT_TAG = 'OutpostFrontLightingMount'
P5 = '/Game/P1toP5_Bundle/P5_FruitSeller/Meshes/'
HOUSING = P5 + 'SM_Props_ConstructionPart118_Light.SM_Props_ConstructionPart118_Light'
HANGER = P5 + 'SM_Props_ConstructionPart119.SM_Props_ConstructionPart119'


def layout(catalog):
    """Derive exterior mounting positions from the existing fixture recipe."""
    import OutpostSkylineLighting
    fixtures = {f['name']: f for f in OutpostSkylineLighting.layout(catalog)}
    rows = [{'name': PREFIX + 'Engineering workstation key',
        'source': 'Engineering/Task light', 'position': [4200, -2900, 290],
        'target': [4200, -3200, 140], 'lumens': 1050., 'radius_cm': 650.,
        'source_lumens': 1600., 'source_radius_cm': 850.,
        'width_cm': 120., 'height_cm': 12., 'color': [1., .83, .65],
        'anchor': 'Engineering/Primary workstation/SM_GoliathLargeScreen01',
        'anchor_mesh': '/Game/P1toP5_Bundle/P1_WorkStation/Meshes/SM_GoliathLargeScreen01.SM_GoliathLargeScreen01',
        'anchor_actor_position': [4200, -3210, 130],
        'mounting': 'Native135cm pendant housing with uniform support to measured ceiling underside',
        'specular_scale': .08, 'source_tag': 'OutpostAuthored'}]
    for tower in (2, 3):
        key = 'SkylineLighting/Tower ' + str(tower) + '/Storey 3'
        if key not in fixtures:
            raise ValueError('Reviewed middle-storey skyline fixture changed: ' + key)
        fixture = fixtures[key]
        part = fixture['parts'][0]
        rows.append({'name': PREFIX + 'Tower ' + str(tower) + ' facade wash',
            'source': key + '/Local wash', 'position': list(fixture['light_position']),
            'target': [*fixture['surface'], fixture['light_position'][2] - 380.],
            'lumens': 750., 'radius_cm': 950.,
            'source_lumens': fixture['lumens'], 'source_radius_cm': fixture['radius'],
            'width_cm': 240., 'height_cm': 12., 'color': [.5, .72, 1.],
            'anchor': key + '/Part 1', 'anchor_mesh': part['asset'],
            'anchor_bounds_center': part['center'], 'anchor_size': part['size'],
            'mounting': 'Existing native Genesis cornice light housing/lens position',
            'specular_scale': .08, 'source_tag': 'OutpostSkylineFixture'})
    for row in rows:
        distance = math.dist(row['position'], row['target'])
        if distance >= row['radius_cm'] or distance < 1 or row['lumens'] > row['source_lumens']:
            raise ValueError('Invalid bounded front-light recipe: ' + row['name'])
    return rows


def _xyz(vector):
    return [float(vector.x), float(vector.y), float(vector.z)]


def _snapshot(actor, component):
    transform = actor.get_actor_transform()
    rotation, color = transform.rotation, component.get_light_color()
    return {'position': _xyz(transform.translation), 'scale': _xyz(transform.scale3d),
        'rotation_xyzw': [float(rotation.x), float(rotation.y), float(rotation.z), float(rotation.w)],
        'lumens': float(component.get_editor_property('intensity')),
        'units': str(component.get_editor_property('intensity_units')),
        'radius_cm': float(component.get_editor_property('attenuation_radius')),
        'color': [float(color.r), float(color.g), float(color.b), float(color.a)],
        'specular_scale': float(component.get_editor_property('specular_scale')),
        'indirect_lighting_intensity': float(component.get_editor_property('indirect_lighting_intensity')),
        'volumetric_scattering_intensity': float(component.get_editor_property('volumetric_scattering_intensity')),
        'casts_shadows': bool(component.get_editor_property('cast_shadows')),
        'visible': bool(component.get_editor_property('visible'))}


def _same_position(actual, expected, context):
    if max(abs(a - b) for a, b in zip(actual, expected)) > 1.:
        raise RuntimeError('Front-light source/fixture moved: ' + context)


def _mount_preflight(api, actors):
    """Derive two native-proportion mounting pieces from actual ceiling bounds."""
    u = api['u']
    from OutpostGeometryUtils import mesh_union
    ceiling = []
    for name, group in actors.items():
        if not name.startswith('QuietCeiling/Engineering/Panel '):
            continue
        if len(group) != 1 or 'OutpostQuietCeiling' not in map(str, group[0].tags):
            raise RuntimeError('Engineering ceiling support is ambiguous/unowned')
        component = group[0].get_component_by_class(u.StaticMeshComponent)
        if not component or not component.get_editor_property('visible'):
            continue
        center, extent = mesh_union(group[0])
        if abs(center.x - 4200) <= extent.x + .01 and abs(center.y + 2900) <= extent.y + .01:
            ceiling.append((group[0], float(center.z - extent.z)))
    if not ceiling or any(abs(z - 397.567688) > .2 for _, z in ceiling):
        raise RuntimeError('No confirmed Engineering ceiling underside above key fixture')
    ceiling_z = min(z for _, z in ceiling)
    specifications = [(PREFIX + 'Engineering key housing', HOUSING,
                       'Engineering/Workstation light/Primary/Owned lamp housing'),
                      (PREFIX + 'Engineering key hanger', HANGER,
                       'Engineering/Workstation light/Primary/Native pendant support')]
    owned = [a for values in actors.values() for a in values if MOUNT_TAG in map(str, a.tags)]
    if owned and (len(owned) != 2 or {a.get_actor_label() for a in owned} != {r[0] for r in specifications}):
        raise RuntimeError('Engineering key mount is partial or duplicated')
    rows, materials = [], {}
    housing_top = None
    for index, (name, path, material_source) in enumerate(specifications):
        matches = actors.get(material_source, [])
        if len(matches) != 1 or 'OutpostAuthored' not in map(str, matches[0].tags):
            raise RuntimeError('Missing existing native fixture material reference')
        reference = matches[0].get_component_by_class(u.StaticMeshComponent)
        if not reference or not reference.static_mesh or reference.static_mesh.get_path_name() != path:
            raise RuntimeError('Existing primary fixture mesh changed')
        source_center, _ = mesh_union(matches[0])
        _same_position(_xyz(source_center), [4200, -3150, 328 if index == 0 else 385], material_source)
        mesh = api['load'](path)
        bounds = mesh.get_bounds()
        dims = [getattr(bounds.box_extent, axis) * 2 for axis in ('x', 'y', 'z')]
        expected = [100., 26.53924, 10.23287] if index == 0 else [21.21283, 21.21285, 120.06414]
        if max(abs(a - b) for a, b in zip(dims, expected)) > .1:
            raise RuntimeError('Native pendant dimensions changed')
        if index == 0:
            scale = 1.35
            height = dims[2] * scale
            center = [4200., -2900., 300. + height * .5]
            housing_top = 300. + height
        else:
            height = ceiling_z - housing_top
            scale = height / dims[2]
            center = [4200., -2900., (ceiling_z + housing_top) * .5]
        size = [v * scale for v in dims]
        if index == 0 and (size[0] < 120 or size[1] < 12):
            raise RuntimeError('Rectangular emitter exceeds its physical housing')
        existing = actors.get(name, [])
        if len(existing) > 1 or (existing and MOUNT_TAG not in map(str, existing[0].tags)):
            raise RuntimeError('Key-mount label is occupied by an unrelated actor')
        if existing:
            static = existing[0].get_component_by_class(u.StaticMeshComponent)
            if (not static or not static.static_mesh or static.static_mesh.get_path_name() != path or
                    static.get_collision_enabled() != u.CollisionEnabled.NO_COLLISION):
                raise RuntimeError('Existing key mount has foreign geometry/collision')
        materials[name] = list(reference.get_materials())
        if len(materials[name]) != len(mesh.static_materials) or any(m is None for m in materials[name]):
            raise RuntimeError('Existing fixture material references are incomplete')
        rows.append({'name': name, 'asset': path, 'center': center, 'size': size,
            'uniform_scale': scale, 'native_origin': _xyz(bounds.origin),
            'materials_from': material_source, 'existing': existing[0] if existing else None})
    # The light stays10cm below the housing; support touches the housing top
    # and ceiling underside exactly. Native geometry stays above head clearance.
    return rows, materials, {'ceiling_actors': [a.get_actor_label() for a, _ in ceiling],
        'ceiling_underside_z': ceiling_z, 'housing_bottom_z': 300.,
        'housing_top_z': housing_top, 'hanger_top_z': ceiling_z,
        'emitter_clearance_below_housing_cm': 10., 'native_uniform_scaling': True}


def _place_mounts(api, rows, materials):
    u, eas = api['u'], api['EAS']
    from OutpostGeometryUtils import mesh_union
    actors, receipt = {}, []
    for row in rows:
        actor = row['existing']
        created = actor is None
        if created:
            actor = eas.spawn_actor_from_class(u.StaticMeshActor, u.Vector())
            actor.set_actor_label(row['name'])
            actor.set_folder_path('FrontLighting')
            actor.tags = [u.Name('OutpostAuthored'), u.Name(MOUNT_TAG)]
        component = actor.get_component_by_class(u.StaticMeshComponent)
        component.set_static_mesh(api['load'](row['asset']))
        component.set_collision_profile_name('NoCollision')
        component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        component.set_simulate_physics(False)
        component.set_cast_shadow(False)
        for slot, material in enumerate(materials[row['name']]):
            component.set_material(slot, material)
        position = [row['center'][i] - row['native_origin'][i] * row['uniform_scale'] for i in range(3)]
        actor.set_actor_rotation(u.Rotator(), False)
        actor.set_actor_scale3d(u.Vector(*([row['uniform_scale']] * 3)))
        actor.set_actor_location(u.Vector(*position), False, False)
        center, extent = mesh_union(actor)
        _same_position(_xyz(center), row['center'], row['name'])
        if max(abs(a * 2 - b) for a, b in zip(_xyz(extent), row['size'])) > .1:
            raise RuntimeError('Native key-mount actual dimensions differ from recipe')
        actors[row['name']] = actor
        receipt.append({k: v for k, v in dict(row, created=created).items() if k != 'existing'})
    return actors, receipt


def preflight(api, rows):
    """Read-only exact actor, source-light and physical-anchor validation."""
    u = api['u']
    from OutpostGeometryUtils import mesh_union
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    package = world.get_path_name().split('.')[0]
    fresh = package.startswith('/Temp/Untitled') and api.get('TARGET') == TARGET
    if package != TARGET and not fresh:
        raise RuntimeError('Front lighting is restricted to the private outpost')
    actors = {}
    for actor in api['EAS'].get_all_level_actors():
        actors.setdefault(actor.get_actor_label(), []).append(actor)
    expected = {row['name'] for row in rows}
    owned = [a for group in actors.values() for a in group if TAG in map(str, a.tags)]
    if owned and (len(owned) != len(rows) or {a.get_actor_label() for a in owned} != expected):
        raise RuntimeError('Front-light replacement set is partial or duplicated')

    def one(label):
        matches = actors.get(label, [])
        if len(matches) != 1:
            raise RuntimeError('Missing or duplicate front-light anchor: ' + label)
        return matches[0]

    staged, report = [], []
    for row in rows:
        original, anchor = one(row['source']), one(row['anchor'])
        if not isinstance(original, u.PointLight) or isinstance(original, u.SpotLight):
            raise RuntimeError('Expected the existing authored point light: ' + row['source'])
        if row['source_tag'] not in map(str, original.tags) or 'OutpostAuthored' not in map(str, anchor.tags):
            raise RuntimeError('Front-light source or anchor is not owned')
        source = original.get_component_by_class(u.PointLightComponent)
        static = anchor.get_component_by_class(u.StaticMeshComponent)
        if not static or not static.static_mesh or static.static_mesh.get_path_name() != row['anchor_mesh']:
            raise RuntimeError('Front-light native fixture/workstation mesh changed')
        state = _snapshot(original, source)
        _same_position(state['position'], row['position'], row['source'])
        if source.get_editor_property('intensity_units') != u.LightUnits.LUMENS or state['casts_shadows']:
            raise RuntimeError('Front-light source has an unreviewed unit/shadow policy')
        if abs(state['lumens'] - row['source_lumens']) > .1 or abs(state['radius_cm'] - row['source_radius_cm']) > 1:
            raise RuntimeError('Front-light original power/radius changed; review before replacement')
        center, extent = mesh_union(anchor)
        if 'anchor_bounds_center' in row:
            _same_position(_xyz(center), row['anchor_bounds_center'], row['anchor'])
            # The lens light is 100cm in front of the wall, aimed downward back
            # toward its facade. Target and full source rectangle stay outside
            # the actual wall and below this existing cornice housing.
            if row['position'][0] >= row['target'][0] or row['target'][2] >= row['position'][2]:
                raise RuntimeError('Skyline wash no longer faces its own facade')
            if row['width_cm'] > max(2 * extent.x, 2 * extent.y) + 1:
                raise RuntimeError('Skyline emitting width exceeds physical fixture span')
        else:
            _same_position(_xyz(anchor.get_actor_location()), row['anchor_actor_position'], row['anchor'])
        existing = actors.get(row['name'], [])
        if len(existing) > 1 or (existing and (TAG not in map(str, existing[0].tags)
                                             or not isinstance(existing[0], u.RectLight))):
            raise RuntimeError('Front-light replacement label is occupied by an unrelated actor')
        if not existing and not state['visible']:
            raise RuntimeError('Original point was hidden by another pass; do not assume ownership')
        report.append({'source': row['source'], 'before': state, 'anchor': row['anchor'],
            'anchor_mesh': row['anchor_mesh'], 'anchor_center': _xyz(center),
            'anchor_extent': _xyz(extent), 'replacement_exists': bool(existing),
            'target_within_radius': True, 'replacement_lumens': row['lumens']})
        staged.append((row, original, source, anchor, static, existing[0] if existing else None, state))
    mounts, materials, mount_report = _mount_preflight(api, actors)
    return staged, report, mounts, materials, mount_report


def apply(api):
    """Run after task/readability/skyline passes; caller saves map and captures."""
    u, eas = api['u'], api['EAS']
    catalog_path = Path(os.environ.get('SS_PREFAB_CATALOG',
                        str(Path(api['ROOT']) / 'Artifacts/PrefabLibrary/catalog.json')))
    rows = layout(json.loads(catalog_path.read_text(encoding='utf-8')))
    staged, checks, mount_rows, mount_materials, mount_report = preflight(api, rows)
    mounts, mount_receipt = _place_mounts(api, mount_rows, mount_materials)
    changes = []
    for row, original, source, anchor, static, rect, before in staged:
        created = rect is None
        position, target = u.Vector(*row['position']), u.Vector(*row['target'])
        rotation = u.MathLibrary.find_look_at_rotation(position, target)
        if created:
            rect = eas.spawn_actor_from_class(u.RectLight, position, rotation)
            if not rect:
                raise RuntimeError('Could not create private front-light replacement')
            rect.set_actor_label(row['name'])
            rect.set_folder_path('FrontLighting')
            rect.tags = [u.Name('OutpostAuthored'), u.Name(TAG)]
        else:
            rect.set_actor_location(position, False, False)
            rect.set_actor_rotation(rotation, False)
        component = rect.get_component_by_class(u.RectLightComponent)
        component.set_mobility(u.ComponentMobility.MOVABLE)
        component.set_intensity_units(u.LightUnits.LUMENS)
        component.set_intensity(row['lumens'])
        component.set_attenuation_radius(row['radius_cm'])
        component.set_light_color(u.LinearColor(*row['color'], 1.))
        component.set_source_width(row['width_cm'])
        component.set_source_height(row['height_cm'])
        component.set_barn_door_angle(70.)
        component.set_barn_door_length(12.)
        component.set_cast_shadows(False)
        component.set_editor_property('specular_scale', row['specular_scale'])
        component.set_editor_property('volumetric_scattering_intensity', 0.)
        component.set_editor_property('indirect_lighting_intensity', .25)
        component.set_visibility(True, False)
        light_mount = static if 'anchor_bounds_center' in row else mounts[PREFIX + 'Engineering key housing'].static_mesh_component
        if not rect.attach_to_component(light_mount, u.Name(''), u.AttachmentRule.KEEP_WORLD,
                u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, False):
            raise RuntimeError('Could not attach front light to its physical housing')
        source.set_visibility(False, False)
        after_source = _snapshot(original, source)
        expected = dict(before, visible=False)
        if after_source != expected:
            raise RuntimeError('Original point parameters changed during visibility-only replacement')
        direction = rect.get_actor_forward_vector()
        delta = [row['target'][i] - row['position'][i] for i in range(3)]
        length = math.sqrt(sum(v * v for v in delta))
        if sum(a * b / length for a, b in zip(_xyz(direction), delta)) < .9999:
            raise RuntimeError('Front-light aiming verification failed')
        measured = _snapshot(rect, component)
        if (abs(measured['lumens'] - row['lumens']) > .01 or
                abs(measured['radius_cm'] - row['radius_cm']) > .01 or
                measured['casts_shadows'] or not measured['visible'] or
                abs(measured['specular_scale'] - row['specular_scale']) > 1e-5):
            raise RuntimeError('Front-light parameter readback failed')
        changes.append(dict(row, created=created, before_source=before, after_source=after_source,
                            replacement=measured, actual_forward=_xyz(direction)))
    receipt = {'map': TARGET, 'preflight': checks, 'lights': changes,
        'created': sum(r['created'] for r in changes), 'active_replacements': len(changes),
        'hidden_original_points': len(changes), 'original_parameters_preserved': True,
        'new_shadow_sources': 0, 'original_total_lumens': sum(r['source_lumens'] for r in rows),
        'replacement_total_lumens': sum(r['lumens'] for r in rows),
        'global_lighting_or_exposure_changed': False, 'existing_geometry_changed': False,
        'geometry_added': True, 'native_mount_parts': 2,
        'mount_preflight': mount_report, 'mount_placements': mount_receipt,
        'material_assets_changed': False, 'fixture_material_references_copied': True,
        'map_saved': False, 'vendor_assets_modified': False,
        'validation': 'Source/fixture and parameter preflight; actual front-face and facade readability require matched native capture.'}
    (Path(api['OUT']) / 'front-lighting.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt
