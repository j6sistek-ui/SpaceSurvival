"""Four measured Operations screen graphics; the lead owns native saves.

Three rear graphic slots change; a compact display insert mounts on the central
native circuit panel with four clips. Native frames, bodies, poses, collision,
lights and services remain intact. The central cutout surface is not an LCD;
its native material stays, while the insert receives its own measured artwork.
"""
import copy
import hashlib
import json
import math
import re
from pathlib import Path

from RefineStationLoungeCeiling import _snapshot
from RefineStationSocialSeatedCrew import _one

MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
BASE = '/Game/OutpostSandbox/StationRefinement/OperationsDisplays20261007'
ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / '.agent/local/StationRefinement'
ART = LOCAL / 'OperationsGraphics1'
BASELINE = LOCAL / 'StationOperationsBaseline2/manifest.json'
BASELINE_SHA = '02c279c096587a8c684f3d55e6285699cb60834198470dfc3b609ab97323d884'
APERTURE_PROBE = LOCAL/'StationOperationsScreenApertureProbe1.json'
APERTURE_SHA = 'e742b71dfb2f0bba622a94ce1e2c38659598a16c518fde4bb1999b5cfd96f3f0'
INSERT_PREFIX = 'Refine/OperationsDisplays/Flight upgrades/'
GRAPHITE = '/Game/OutpostSandbox/Materials/M_OutpostGraphite'
ART_MANIFESTS = {
    'preview_v2/manifest.json': '314f57730a2e2c469aa831aa3ff2b276a91b86b9e0f60a301905a0bc152934cc',
    'preview_services_v1/manifest.json': '6529d0be0bcc22c738bf016c0b241e3cd4d5e757b749c983b1091018d6a89fae',
    'preview_central_insert_v1/manifest.json': '78548e050c51ec89213871cf78bee11b4339671a8b2bf254df31a7124b51e4d4',
}
LARGE = '/Game/P1toP5_Bundle/P1_WorkStation/Meshes/SM_GoliathLargeScreen01'
REAR = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Meshes/SM_Window400X200_V2_Part2_DigitalWindow'
TARGETS = (
    ('Refine/Operations/Rear data 1/Glass', '01_Navigation', REAR, (0, 1)),
    ('Refine/Operations/Rear data 2/Glass', '02_SystemDiagnostics', REAR, (0, 1)),
    ('Refine/Operations/Rear data 3/Glass', '03_ContractStatus', REAR, (0, 1)),
    ('Engineering/Primary workstation/SM_GoliathLargeScreen01', '04_FlightUpgrades', LARGE, (1,)),
)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _require(condition, message):
    if not condition:
        raise RuntimeError(message)


def _path(asset):
    return asset.get_path_name() if asset else None


def inspect_sources():
    """Verify original pixels/recipes; retain dated gameplay references as provenance.

    C++ is being changed by another authorized workstream. Its historical hashes
    remain in the art receipt, but are not an immutable art-generation input.
    """
    manifests, assets, inputs = {}, {}, {}
    for relative, digest in ART_MANIFESTS.items():
        path = ART / relative
        _require(_sha(path) == digest, 'Reviewed Operations art manifest changed')
        data = json.loads(path.read_text())
        manifests[relative] = {'sha256': digest, 'provenance': data['provenance'],
                               'historical_source_sha256': data['source_sha256']}
        for row in data['assets']:
            p = Path(row.get('file') or row['path']).resolve()
            dimensions = [2048, 768] if relative.startswith('preview_central_insert_v1/') else [2048, 1024]
            _require(p.is_relative_to(ART.resolve()) and _sha(p) == row['sha256'] and
                     row['size'] == dimensions, 'Approved art pixels/aspect changed')
            assets[row['name']] = {**row, 'file': str(p)}
            inputs[str(p)] = row['sha256']
        for filename, source_sha in data['source_sha256'].items():
            p = Path(filename).resolve()
            if p.is_relative_to(ROOT/'Source') or p.is_relative_to(ROOT/'docs'):
                continue
            _require(_sha(p) == source_sha, 'Artwork source changed: ' + str(p))
            inputs[str(p)] = source_sha
    _require(set(assets) == {row[1] for row in TARGETS}, 'Unexpected Operations graphics set')
    return manifests, assets, inputs


def _dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def _aperture(data, material_ids, slots, axis, right, up):
    """Summarize the dominant true planar display surface, never export the frame.

    Material selection precedes measurement. Small bevel faces and source frame
    triangles do not enlarge the fit. A plane's area must substantially cover
    its projected rectangle; sparse bars cannot masquerade as a display.
    """
    planes = {}
    vertices, triangles = data['vertices'], data['triangles']
    for face, slot in zip(triangles, material_ids):
        if slot not in slots:
            continue
        points = [vertices[index] for index in face]
        a, b, c = points
        e = [b[i]-a[i] for i in range(3)]
        f = [c[i]-a[i] for i in range(3)]
        cross = (e[1]*f[2]-e[2]*f[1], e[2]*f[0]-e[0]*f[2], e[0]*f[1]-e[1]*f[0])
        length = math.sqrt(_dot(cross, cross))
        if length < 1.e-8 or abs(cross[axis])/length < .995:
            continue
        key = round(sum(p[axis] for p in points)/3., 3)
        group = planes.setdefault(key, {'area': 0., 'points': [], 'triangles': 0})
        group['area'] += length*.5
        group['points'].extend(points)
        group['triangles'] += 1
    _require(planes, 'No actual planar material-slot display surface')
    plane, group = max(planes.items(), key=lambda pair: (round(pair[1]['area'], 2), pair[0]))
    points = group['points']
    x = [_dot(p, right) for p in points]
    y = [_dot(p, up) for p in points]
    width, height = max(x)-min(x), max(y)-min(y)
    _require(width > 20. and height > 12. and group['area']/(width*height) > .70,
             'Selected material slot does not form a useful screen: '+str((width, height, group['area'])))
    cx, cy = (min(x)+max(x))*.5, (min(y)+max(y))*.5
    center = [right[i]*cx+up[i]*cy for i in range(3)]
    center[axis] = plane
    # Real aspect is retained. The remaining margin is a dark display bezel;
    # it also keeps the art's own five-percent text safety away from the frame.
    image_h = min(height*.94, width*.94/2.)
    return {'center': center, 'right': list(right), 'up': list(up),
            'native_size_cm': [width, height], 'image_size_cm': [image_h*2., image_h],
            'native_plane': plane, 'selected_triangles': group['triangles'],
            'selected_surface_area_cm2': group['area'], 'letterboxed_without_stretch': True,
            'pixel_orientation_acceptance': 'PENDING_NATIVE_FRONT_VIEW'}


def _contains_xz(geometry, x, z):
    for face in geometry['triangles']:
        a, b, c = [(geometry['vertices'][index][0], geometry['vertices'][index][2]) for index in face]
        det = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(det) < 1.e-9:
            continue
        s = ((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(z-c[1]))/det
        t = ((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(z-c[1]))/det
        if s >= -1.e-6 and t >= -1.e-6 and s+t <= 1.000001:
            return True
    return False


def measure_apertures(baseline):
    """Retained native source proof; no expensive frame re-export or guessed UV."""
    native = baseline['operations']['screen_meshes']
    rear = native[REAR+'.'+REAR.rsplit('/', 1)[-1]]
    apertures = {REAR: _aperture(rear['geometry'], rear['triangle_material_ids'], (0, 1),
                                0, (0., -1., 0.), (0., 0., 1.))}
    _require(_sha(APERTURE_PROBE) == APERTURE_SHA, 'Native central slot evidence changed')
    probe = json.loads(APERTURE_PROBE.read_text())
    _require(probe['success'] and probe['preserved'] and probe['all_slot1_triangle_count'] == 7514,
             'Central slot geometry proof unavailable')
    # Each clip has a complete supported nine-point footprint on the actual
    # native surface. Its3.6cm depth spans nativeY−1.738 through insertY+1.1.
    mounts = [(x, -.2, z) for x in (-32., 32.) for z in (18., 35.)]
    for x, _, z in mounts:
        _require(all(_contains_xz(probe['selected'], x+dx, z+dz)
                     for dx in (-1.3, 0., 1.3) for dz in (-1.5, 0., 1.5)), 'Insert clip lacks native support')
    # Engine plane coordinates are100x100; its64x24cm scale matches2048x768
    # art. Project in local coordinates so moving the owner assembly stays safe.
    apertures[LARGE] = {'center': [0., 0., 0.], 'right': [1., 0., 0.], 'up': [0., -1., 0.],
        'native_size_cm': [100., 100.], 'image_size_cm': [100., 100.],
        'physical_insert_size_cm': [64., 24.], 'native_parent_center_cm': [0., 1.1, 26.],
        'native_mount_centers_cm': mounts, 'art_aspect_preserved': 2048./768.,
        'native_circuit_material_preserved': True, 'geometry_receipt_sha256': APERTURE_SHA}
    return apertures


def _texture(name, source, u, dirty):
    path = BASE+'/Textures/T_'+name
    _require(not u.EditorAssetLibrary.does_asset_exist(path), 'Preserve previous Operations texture')
    task = u.AssetImportTask()
    for key, value in {'filename': source['file'], 'destination_path': BASE+'/Textures',
                       'destination_name': 'T_'+name, 'automated': True,
                       'replace_existing': False, 'save': False}.items():
        task.set_editor_property(key, value)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = u.load_asset(path)
    _require(isinstance(texture, u.Texture2D), 'Operations texture import failed')
    for key, value in {'srgb': True, 'compression_settings': u.TextureCompressionSettings.TC_BC7,
                       'lod_group': u.TextureGroup.TEXTUREGROUP_WORLD,
                       'mip_gen_settings': u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP,
                       'address_x': u.TextureAddress.TA_CLAMP, 'address_y': u.TextureAddress.TA_CLAMP}.items():
        texture.set_editor_property(key, value)
    dirty.append(texture.get_path_name())
    return texture


def _material(name, texture, aperture, u, dirty, glass=False):
    edit = u.MaterialEditingLibrary
    _require(not u.EditorAssetLibrary.does_asset_exist(BASE+'/Materials/M_'+name), 'Preserve previous Operations material')
    mat = u.AssetToolsHelpers.get_asset_tools().create_asset('M_'+name, BASE+'/Materials', u.Material, u.MaterialFactoryNew())
    _require(mat, 'Cannot create private Operations material')
    mat.set_editor_property('shading_model', u.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property('two_sided', True)
    mat.set_editor_property('blend_mode', u.BlendMode.BLEND_TRANSLUCENT if glass else u.BlendMode.BLEND_OPAQUE)
    def node(kind, **properties):
        result = edit.create_material_expression(mat, getattr(u, kind))
        _require(result, 'Cannot create display expression '+kind)
        for key, value in properties.items():
            result.set_editor_property(key, value)
        return result
    pos = node('MaterialExpressionWorldPosition')
    local = node('MaterialExpressionTransformPosition',
                 transform_source_type=u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_WORLD,
                 transform_type=u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_LOCAL)
    _require(edit.connect_material_expressions(pos, '', local, ''), 'Local screen transform failed')
    tex = node('MaterialExpressionTextureObjectParameter', parameter_name='Artwork', texture=texture,
               sampler_type=u.MaterialSamplerType.SAMPLERTYPE_COLOR)
    gain = node('MaterialExpressionScalarParameter', parameter_name='DisplayGain', default_value=6.)
    vec = lambda v: 'float3('+','.join('%.10f'%x for x in v)+')'
    width, height = aperture['image_size_cm']
    code = 'float3 p=P-'+vec(aperture['center'])+';\n'
    code += 'float2 uv=float2(dot(p,'+vec(aperture['right'])+')/%.10f+0.5,0.5-dot(p,'%width
    code += vec(aperture['up'])+')/%.10f);\n'%height
    code += 'float inside=step(0.,uv.x)*step(uv.x,1.)*step(0.,uv.y)*step(uv.y,1.);\n'
    code += 'float3 c=Texture2DSample(Artwork,ArtworkSampler,clamp(uv,0.001,0.999)).rgb;\n'
    code += 'return lerp(float3(0.001,0.0025,0.0035),c,inside)*Gain;'
    custom = node('MaterialExpressionCustom', code=code, description='Measured native screen slot / preserved aspect / decorative briefing',
                  output_type=u.CustomMaterialOutputType.CMOT_FLOAT3)
    pins = []
    for name in ('P', 'Artwork', 'Gain'):
        pin = u.CustomInput(); pin.set_editor_property('input_name', name); pins.append(pin)
    custom.set_editor_property('inputs', pins)
    for source, key in ((local, 'P'), (tex, 'Artwork'), (gain, 'Gain')):
        _require(edit.connect_material_expressions(source, '', custom, key), 'Display input failed '+key)
    _require(edit.connect_material_property(custom, '', u.MaterialProperty.MP_EMISSIVE_COLOR), 'Display emissive connection failed')
    if glass:
        opacity = node('MaterialExpressionConstant', r=.96)
        _require(edit.connect_material_property(opacity, '', u.MaterialProperty.MP_OPACITY), 'Insert smoked-glass opacity failed')
    edit.layout_material_expressions(mat)
    errors = edit.recompile_material(mat)
    _require(not errors, 'Native Operations shader compile failed: '+str(errors))
    dirty.append(mat.get_path_name())
    return mat, {'asset': mat.get_path_name(), 'aperture': aperture, 'default_gain': 6.,
                 'native_compile_errors': list(errors), 'shader': code}


def _state(actor, u):
    result = _snapshot(actor, u)
    result['collision'] = bool(actor.get_actor_enable_collision())
    result['components'] = {}
    for component in actor.get_components_by_class(u.PrimitiveComponent):
        transform = component.get_world_transform()
        result['components'][component.get_path_name()] = {
            'visible': bool(component.is_visible()), 'hidden': bool(component.get_editor_property('hidden_in_game')),
            'collision': str(component.get_collision_enabled()),
            'location': tuple(transform.translation.to_tuple()), 'rotation': tuple(transform.rotation.to_tuple()),
            'scale': tuple(transform.scale3d.to_tuple())}
    if isinstance(actor, u.SSOutpostTerminal):
        result['service'] = {key: str(actor.get_editor_property(key)) for key in
            ('display_name', 'description', 'action', 'use_distance', 'presentation_target')}
    return result


def apply(ctx, expected_map_sha256):
    """Stage three rear displays, one supported insert/eight assets; never save."""
    import unreal as u
    map_file = ROOT/('Content/'+MAP[6:]+'.umap')
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    _require(re.fullmatch('[0-9a-f]{64}', expected_map_sha256) and _sha(map_file) == expected_map_sha256 and
             world.get_path_name().split('.')[0] == MAP, 'Require exact latest owner-preview map')
    _require(_sha(BASELINE) == BASELINE_SHA, 'Frozen Operations native baseline changed')
    baseline = json.loads(BASELINE.read_text())
    _require(baseline['success'] and baseline['files_unchanged'] and baseline['saves_unchanged'], 'Operations native baseline failed')
    manifests, art, art_inputs = inspect_sources()
    source_hashes = dict(baseline['operations']['source_sha256'])
    source_hashes[GRAPHITE] = _sha(ROOT/('Content/'+GRAPHITE[6:]+'.uasset'))
    for package, digest in source_hashes.items():
        _require(_sha(ROOT/('Content/'+package[6:]+'.uasset')) == digest, 'Native T source changed '+package)
    actors = list(ctx.eas.get_all_level_actors())
    _require(not any(a.get_actor_label().startswith(INSERT_PREFIX) for a in actors), 'Preserve previous central insert')
    before = {a.get_path_name(): _state(a, u) for a in actors}
    expected = copy.deepcopy(before)
    placements = {r['label']: r for r in baseline['operations']['screen_placements']}
    targets = []
    for label, artwork, mesh_path, slots in TARGETS:
        actor = _one(actors, label)
        component = actor.get_component_by_class(u.StaticMeshComponent)
        row = placements[label]
        _require(component and _path(component.static_mesh).split('.')[0] == mesh_path, 'Target display mesh differs')
        transform = component.get_world_transform()
        for attr, key in (('translation', 'location'), ('rotation', 'rotation'), ('scale3d', 'scale')):
            _require(math.dist(getattr(transform, attr).to_tuple(), row['world_transform'][key]) < .001,
                     'Target display pose changed '+label)
        bounds = component.static_mesh.get_bounds()
        native = baseline['operations']['screen_meshes'][row['mesh']]
        _require(math.dist(bounds.origin.to_tuple(), native['native_origin_cm']) < .001 and
                 math.dist(bounds.box_extent.to_tuple(), native['native_extent_cm']) < .001, 'Native screen bounds changed')
        targets.append((actor, component, artwork, mesh_path, slots))
    # Complete native measurement before importing or mutating any actor.
    apertures = measure_apertures(baseline)
    dirty, changes, materials, new_actors = [], [], [], []
    for actor, component, artwork, mesh_path, slots in targets:
        texture = _texture(artwork, art[artwork], u, dirty)
        central = mesh_path == LARGE
        material, material_report = _material(artwork, texture, apertures[mesh_path], u, dirty, glass=central)
        materials.append(material_report)
        if central:
            transform = component.get_world_transform()
            def world_point(local):
                return tuple(transform.transform_location(u.Vector(*local)).to_tuple())
            def attach(child):
                _require(child.attach_to_component(component, u.Name(''), u.AttachmentRule.KEEP_WORLD,
                    u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, False), 'Insert must mount to native screen')
                child.static_mesh_component.set_cast_shadow(False)
                new_actors.append(child)
            pane = ctx.raw(INSERT_PREFIX+'Glass', '/Engine/BasicShapes/Plane',
                world_point(apertures[LARGE]['native_parent_center_cm']), rot=(0., 90., 90.),
                scale=(.64, .24, 1.), collision=False)
            plane_bounds = pane.static_mesh_component.static_mesh.get_bounds()
            _require(math.dist(plane_bounds.box_extent.to_tuple(), (50., 50., 0.)) < .01, 'Basic plane dimensions differ')
            pane.static_mesh_component.set_material(0, material); attach(pane)
            for index, local in enumerate(apertures[LARGE]['native_mount_centers_cm'], 1):
                clip = ctx.box(INSERT_PREFIX+'Clip '+str(index), world_point(local),
                               (3.6, 2.6, 3.), GRAPHITE, False)
                attach(clip)
            changes.append({'label': pane.get_actor_label(), 'component': pane.static_mesh_component.get_path_name(),
                'slots': [0], 'mesh': '/Engine/BasicShapes/Plane', 'artwork': artwork,
                'before_materials': [], 'after_materials': [material.get_path_name()],
                'parent_label': actor.get_actor_label(), 'original_parent_materials_preserved': True})
            continue
        old = list(map(_path, component.get_materials()))
        for slot in slots:
            component.set_material(slot, material)
            expected[actor.get_path_name()]['materials'][component.get_path_name()][slot] = material.get_path_name()
        new = list(map(_path, component.get_materials()))
        _require(all(new[i] == old[i] for i in range(len(old)) if i not in slots), 'Non-display native slot changed')
        changes.append({'label': actor.get_actor_label(), 'component': component.get_path_name(), 'slots': list(slots),
                        'mesh': mesh_path, 'artwork': artwork, 'before_materials': old, 'after_materials': new})
    after = {a.get_path_name(): _state(a, u) for a in ctx.eas.get_all_level_actors()}
    new_paths = {actor.get_path_name() for actor in new_actors}
    _require(set(after)-set(before) == new_paths and len(new_paths) == 5 and
             {key: value for key, value in after.items() if key not in new_paths} == expected,
             'Unrelated actor, frame, light, service, visibility or collision changed')
    _require(all(not a.get_actor_enable_collision() for a in new_actors), 'Decorative insert must not alter walking collision')
    _require(_sha(map_file) == expected_map_sha256, 'Helper must not save the map')
    return {'dirty_assets': dirty, 'changes': changes, 'materials': materials, 'apertures': apertures,
            'source_sha256': source_hashes, 'art_manifest_sha256': ART_MANIFESTS,
            'art_provenance': manifests, 'art_input_sha256': art_inputs,
            'baseline_sha256': BASELINE_SHA, 'new_actor_count': len(new_paths), 'new_light_count': 0,
            'insert_actors': [{'label': a.get_actor_label(), 'state': _state(a, u)} for a in new_actors],
            'protected_existing_layout_animation_lighting_services_preserved': True,
            'limits': ['Decorative briefing graphics only; existing Information terminal action is preserved.',
                       'Central native circuit slots are unchanged; compact2.667:1 art uses a supported insert.',
                       'Front-view readability, opacity and native lighting still require actual room capture.']}
