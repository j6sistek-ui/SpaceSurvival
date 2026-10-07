"""Owner-requested enclosed Phoenix command display; lead owns native saves.

The existing Goliath, four complete staffed pods, services, displays, shell and
lighting stay fixed. This adds an owned-kit podium and a graph-free Phoenix
presentation rig, with one decorative 60-second sequence. No gameplay code,
input, camera, exposure, source-asset edits or save calls belong in this helper.
"""
import hashlib
import json
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
BASE = '/Game/OutpostSandbox/StationRefinement/OperationsComposition20261007'
PREFIX = 'Refine/OperationsComposition/'
BASELINE = ROOT / '.agent/local/StationRefinement/StationOperationsBaseline2/manifest.json'
BASELINE_SHA = '02c279c096587a8c684f3d55e6285699cb60834198470dfc3b609ab97323d884'
PROBE = ROOT / '.agent/local/StationRefinement/StationOperationsCompositionProbe1.json'
PROBE_SHA = '594247794f1048db936dbc1beaba5284f5cfd5a80377c0ea68b1a56158b9fa39'
FROZEN_PROBE_HELPER = ROOT / '.agent/local/StationRefinement/FrozenOperationsCompositionProbe1/RefineStationOperationsComposition.py'
P4 = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/'
PANEL = P4+'Meshes/SM_WallPanel200X100_V1_SmartStorageUnit'
POST = '/Game/P1toP5_Bundle/P5_FruitSeller/Meshes/SM_Building_Structure200x10_V1'
PROJECTOR = '/Game/CyberpunkRestaurant/Meshes/SM_Hologram_Projector_01'
DARK = P4+'Materials/Instances/Opaque/MI_Metal12_PaintAnodizedAluminium_Dark'
TRIM = P4+'Materials/Instances/Opaque/MI_Metal02_AnodizedAluminium'
PHOENIX = '/Game/SpaceSurvival/Licensed/PhoenixPresentation/BP_PhoenixPresentation'
HULL = '/Game/Stellar_Phoenix/Spaceship/Meshes/Stellar_Phoenix'
POSE = '/Game/Stellar_Phoenix/Spaceship/Animation/BattleMode_Enter'
CENTRE = (8170., 0.)
HALF_WIDTH = 240.
BASE_TOP = 105.
GLASS_TOP = 285.
HOLO_CENTRE_Z = 190.
HOLO_LENGTH = 320.
PERIOD = 60.
FPS = 30
END_FRAME = int(PERIOD*FPS)
CHANNELS = ('Location.X', 'Location.Y', 'Location.Z', 'Rotation.X', 'Rotation.Y',
            'Rotation.Z', 'Scale.X', 'Scale.Y', 'Scale.Z')
OUTPUTS = ('SM_OctagonalPodiumUnit', 'M_EnclosureGlass', 'M_PhoenixHologram',
           'M_ProjectorLens', 'LS_PhoenixDisplay')
# The equipment interstice between Goliath and podium is deliberately not a
# route. The ordinary capsule uses the broad exterior circuit instead.
ROUTES = {
    'Command approach': ((7000., 0., 0.), (7440., 0., 0.)),
    'Command exterior south': ((7500., -460., 0.), (8520., -460., 0.)),
    'Command exterior north': ((7500., 460., 0.), (8520., 460., 0.)),
    'Rear connection': ((8520., -460., 0.), (8520., 460., 0.)),
}
CAMERAS = (
    {'name': '01_OperationsEntrance', 'location': [6620., 0., 185.], 'look_at': [8170., 0., 180.]},
    {'name': '02_PhoenixCommand', 'location': [7650., -540., 220.], 'look_at': [8170., 0., 185.]},
    {'name': '03_PodiumSide', 'location': [8180., -700., 185.], 'look_at': [8170., 0., 175.]},
    {'name': '04_ReverseRoom', 'location': [8820., 850., 210.], 'look_at': [7760., 0., 165.]},
)


def _require(value, message):
    if not value:
        raise RuntimeError(message)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def plan():
    """Pure geometry proposal; this is not native collision or pixel evidence."""
    radius = HALF_WIDTH/math.cos(math.pi/8)
    vertices = [(CENTRE[0]+radius*math.cos(math.pi/8+i*math.pi/4),
                 CENTRE[1]+radius*math.sin(math.pi/8+i*math.pi/4)) for i in range(8)]
    return {'centre_cm': list(CENTRE), 'bounds_cm': [[7930., -240., 0.], [8410., 240., 285.]],
            'base_top_cm': BASE_TOP, 'glass_top_cm': GLASS_TOP,
            'hologram_length_cm': HOLO_LENGTH, 'hologram_centre_z_cm': HOLO_CENTRE_Z,
            'rotation_degrees_per_second': 360./PERIOD, 'period_seconds': PERIOD,
            'octagon_vertices_cm': vertices, 'face_width_cm': 2*HALF_WIDTH*math.tan(math.pi/8),
            'front_console_interstice_is_walkway': False,
            'source_assets': [PANEL, POST, PROJECTOR, PHOENIX, HULL, POSE, DARK, TRIM],
            'routes_cm': ROUTES, 'capture_cameras': CAMERAS,
            'motion_capture': {'natural_times_seconds': [5., 20.], 'same_camera': '02_PhoenixCommand',
                               'minimum_observed_yaw_delta_degrees': 80.},
                               'status': 'UNRUN: native support, silhouette, transparency and rotation require actual evidence'}


def probe(ctx):
    """Read native kit dimensions/component templates; do not spawn or mutate."""
    import unreal as u
    sources, meshes = {}, {}
    for package in plan()['source_assets']:
        asset = ctx.asset(package)
        sources[package] = _sha(ROOT/('Content/'+package[6:]+'.uasset'))
        if isinstance(asset, (u.StaticMesh, u.SkeletalMesh)):
            b = asset.get_bounds()
            material_list = (asset.get_editor_property('materials') if isinstance(asset, u.SkeletalMesh)
                             else asset.get_editor_property('static_materials'))
            meshes[package] = {'origin_cm': list(b.origin.to_tuple()),
                'extent_cm': list(b.box_extent.to_tuple()), 'materials': [
                    {'slot': str(slot.material_slot_name), 'asset':
                     slot.material_interface.get_path_name() if slot.material_interface else None}
                    for slot in material_list]}
    blueprint = ctx.asset(PHOENIX)
    graphs = [graph.get_name() for graph in u.BlueprintEditorLibrary.list_graphs(blueprint)]
    _require(not graphs, 'Phoenix presentation must remain graph-free')
    subsystem = u.get_engine_subsystem(u.SubobjectDataSubsystem)
    lib = u.SubobjectDataBlueprintFunctionLibrary
    components = {}
    for handle in subsystem.k2_gather_subobject_data_for_blueprint(blueprint):
        data = lib.get_data(handle)
        obj = lib.get_associated_object(data)
        if not isinstance(obj, u.SceneComponent):
            continue
        parent_handle = lib.get_parent_handle(data)
        parent = lib.get_associated_object(lib.get_data(parent_handle)) if lib.is_handle_valid(parent_handle) else None
        row = {'name': obj.get_name(), 'class': obj.get_class().get_name(),
               'parent': parent.get_name() if parent else None,
               'location': list(obj.get_editor_property('relative_location').to_tuple()),
               'rotation_pyr': [float(getattr(obj.get_editor_property('relative_rotation'), axis))
                                for axis in ('pitch', 'yaw', 'roll')],
               'scale': list(obj.get_editor_property('relative_scale3d').to_tuple()),
               'absolute_scale': bool(obj.get_editor_property('absolute_scale'))}
        mesh = (obj.get_skeletal_mesh_asset() if isinstance(obj, u.SkeletalMeshComponent)
                else obj.static_mesh if isinstance(obj, u.StaticMeshComponent) else None)
        if mesh:
            row['mesh'] = mesh.get_path_name()
            b = mesh.get_bounds()
            row['mesh_origin_cm'], row['mesh_extent_cm'] = list(b.origin.to_tuple()), list(b.box_extent.to_tuple())
            package = mesh.get_path_name().split('.')[0]
            sources[package] = _sha(ROOT/('Content/'+package[6:]+'.uasset'))
        components[row['name']] = row
    _require(all(_sha(ROOT/('Content/'+p[6:]+'.uasset')) == digest for p, digest in sources.items()),
             'Read-only composition probe changed source bytes')
    return {'plan': plan(), 'meshes': meshes, 'phoenix_templates': list(components.values()),
            'source_sha256': sources, 'source_bytes_unchanged': True,
            'limits': 'Bounds/templates only; not rendered pose, collision or quality acceptance.'}


def _material(name, u, dirty):
    asset = u.AssetToolsHelpers.get_asset_tools().create_asset(name, BASE, u.Material, u.MaterialFactoryNew())
    _require(asset, 'Private material creation failed: '+name)
    dirty.append(asset.get_path_name())
    return asset


def _optical_materials(u, dirty):
    edit = u.MaterialEditingLibrary

    def node(mat, cls, **properties):
        obj = edit.create_material_expression(mat, getattr(u, cls))
        _require(obj, 'Material node creation failed: '+cls)
        for key, value in properties.items():
            obj.set_editor_property(key, value)
        return obj

    def link(a, b, pin='', output=''):
        _require(edit.connect_material_expressions(a, output, b, pin), 'Optical graph link failed: '+pin)

    def prop(a, p, output=''):
        _require(edit.connect_material_property(a, output, p), 'Optical output link failed: '+str(p))

    def mul(mat, a, value):
        b = node(mat, 'MaterialExpressionMultiply', const_b=value)
        link(a, b, 'A')
        return b

    glass = _material('M_EnclosureGlass', u, dirty)
    glass.set_editor_property('blend_mode', u.BlendMode.BLEND_TRANSLUCENT)
    glass.set_editor_property('two_sided', True)
    glass.set_editor_property('translucency_lighting_mode', u.TranslucencyLightingMode.TLM_SURFACE)
    tint = node(glass, 'MaterialExpressionConstant3Vector', constant=u.LinearColor(.08, .14, .17, 1.))
    prop(tint, u.MaterialProperty.MP_BASE_COLOR)
    fresnel = node(glass, 'MaterialExpressionFresnel', exponent=4., base_reflect_fraction=0.)
    opacity = node(glass, 'MaterialExpressionAdd', const_b=.035)
    link(mul(glass, fresnel, .18), opacity, 'A')
    prop(opacity, u.MaterialProperty.MP_OPACITY)
    for p, value in ((u.MaterialProperty.MP_ROUGHNESS, .13), (u.MaterialProperty.MP_SPECULAR, .32)):
        prop(node(glass, 'MaterialExpressionConstant', r=value), p)

    holo = _material('M_PhoenixHologram', u, dirty)
    holo.set_editor_property('blend_mode', u.BlendMode.BLEND_TRANSLUCENT)
    holo.set_editor_property('shading_model', u.MaterialShadingModel.MSM_UNLIT)
    holo.set_editor_property('two_sided', False)
    edit.set_base_material_usage(holo, u.MaterialUsage.MATUSAGE_SKELETAL_MESH, True)
    rim = node(holo, 'MaterialExpressionFresnel', exponent=2.2, base_reflect_fraction=0.)
    position = node(holo, 'MaterialExpressionWorldPosition')
    height = node(holo, 'MaterialExpressionComponentMask', r=False, g=False, b=True, a=False)
    link(position, height)
    time = node(holo, 'MaterialExpressionTime')
    phase = node(holo, 'MaterialExpressionAdd')
    link(mul(holo, height, 1./22.), phase, 'A')
    link(mul(holo, time, -.16), phase, 'B')
    sine = node(holo, 'MaterialExpressionSine', period=1.)
    link(phase, sine)
    positive = node(holo, 'MaterialExpressionAdd', const_b=.5)
    link(mul(holo, sine, .5), positive, 'A')
    stripe = node(holo, 'MaterialExpressionPower', const_exponent=36.)
    link(positive, stripe, 'Base')
    outputs = []
    for body, rim_gain, scan_gain in ((.22, .45, .06), (3., 8., 1.)):
        combined = node(holo, 'MaterialExpressionAdd')
        link(mul(holo, rim, rim_gain), combined, 'A')
        link(mul(holo, stripe, scan_gain), combined, 'B')
        total = node(holo, 'MaterialExpressionAdd', const_b=body)
        link(combined, total, 'A')
        outputs.append(total)
    prop(outputs[0], u.MaterialProperty.MP_OPACITY)
    colour = node(holo, 'MaterialExpressionConstant3Vector', constant=u.LinearColor(.12, .67, 1., 1.))
    emission = node(holo, 'MaterialExpressionMultiply')
    link(colour, emission, 'A')
    link(outputs[1], emission, 'B')
    prop(emission, u.MaterialProperty.MP_EMISSIVE_COLOR)

    lens = _material('M_ProjectorLens', u, dirty)
    prop(node(lens, 'MaterialExpressionConstant3Vector', constant=u.LinearColor(.05, .5, .75, 1.)),
         u.MaterialProperty.MP_EMISSIVE_COLOR)
    prop(node(lens, 'MaterialExpressionConstant', r=.22), u.MaterialProperty.MP_ROUGHNESS)
    for material in (glass, holo, lens):
        edit.layout_material_expressions(material)
        _require(not edit.recompile_material(material), 'Optical material compile errors: '+material.get_name())
    return glass, holo, lens


def _octagon(u, dirty, material):
    dynamic = u.DynamicMesh()
    u.GeometryScript_Primitives.append_cylinder(dynamic, u.GeometryScriptPrimitiveOptions(),
        u.Transform(rotation=u.Rotator(yaw=22.5)), radius=50./math.cos(math.pi/8), height=100.,
        radial_steps=8, height_steps=0, capped=True, origin=u.GeometryScriptPrimitiveOriginMode.CENTER)
    mesh, outcome = u.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(
        dynamic, BASE+'/SM_OctagonalPodiumUnit', u.GeometryScriptCreateNewStaticMeshAssetOptions(
            enable_nanite=False, enable_collision=True,
            collision_mode=u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE))
    _require(outcome == u.GeometryScriptOutcomePins.SUCCESS and mesh, 'Octagonal plate authoring failed')
    mesh.set_material(0, material)
    b = mesh.get_bounds()
    _require(math.dist(b.origin.to_tuple(), (0., 0., 0.)) < .02 and
             math.dist(b.box_extent.to_tuple(), (50., 50., 50.)) < .02,
             'Generated octagon coordinates differ from reviewed footprint')
    _require(24 <= dynamic.get_triangle_count() <= 64, 'Unexpected plate geometry budget')
    dirty.append(mesh.get_path_name())
    return mesh


def _centred(ctx, label, mesh, centre, rotation=(0., 0., 0.), scale=(1., 1., 1.), collision=True):
    import unreal as u
    from OutpostGeometryUtils import mesh_union
    actor = ctx.raw(PREFIX+label, mesh, centre, rotation, scale, collision)
    c, _ = mesh_union(actor)
    actor.set_actor_location(actor.get_actor_location()+u.Vector(*(centre[i]-c.to_tuple()[i] for i in range(3))), False, False)
    return actor


def _podium(ctx, plate, glass, lens, u):
    from OutpostGeometryUtils import mesh_union
    records = []

    def record(actor, role):
        c, e = mesh_union(actor)
        records.append({'label': actor.get_actor_label(), 'role': role,
                        'minimum_cm': list((c-e).to_tuple()), 'maximum_cm': list((c+e).to_tuple())})
        return actor

    for name, z, width, height, material in (
            ('Grounded plinth', 4., 480., 8., DARK), ('Recessed body', 54., 466., 92., DARK),
            ('Upper rim', 102., 480., 6., TRIM), ('Projection deck', 105.5, 470., 1., DARK)):
        actor = ctx.raw(PREFIX+name, plate, (*CENTRE, z), scale=(width/100., width/100., height/100.))
        actor.static_mesh_component.set_material(0, ctx.asset(material))
        record(actor, 'base')
    side_width = 2*HALF_WIDTH*math.tan(math.pi/8)
    for i in range(8):
        angle = i*45.
        theta = math.radians(angle)
        normal = (math.cos(theta), math.sin(theta))
        # Native panel front is local X0; +X is its inward hardware depth.
        actor = ctx.raw(PREFIX+'Owned service panel %02d'%i, PANEL,
            (CENTRE[0]+238.*normal[0], CENTRE[1]+238.*normal[1], 8.),
            (0., angle+180., 0.), (.8, (side_width-8.)/200., .90))
        record(actor, 'owned structured base panel')
        # One transparent surface per facet, enclosed by independent metal rails.
        centre = (CENTRE[0]+236.*normal[0], CENTRE[1]+236.*normal[1], 193.)
        pane = _centred(ctx, 'Glass facet %02d'%i, '/Engine/BasicShapes/Plane', centre,
                        (90., angle, 0.), (1.72, (side_width-12.)/100., 1.), False)
        pane.static_mesh_component.set_material(0, glass)
        pane.static_mesh_component.set_cast_shadow(False)
        record(pane, 'clear glass')
        for z, height, depth, material, name in (
                (108., 6., 9., TRIM, 'Glass shoe'), (282., 6., 9., TRIM, 'Crown rail'),
                (99., 1., 1.2, lens, 'Recessed rim lens')):
            rail = ctx.box(PREFIX+name+' %02d'%i,
                (CENTRE[0]+234.*normal[0], CENTRE[1]+234.*normal[1], z),
                (depth, side_width-5., height), material, False)
            rail.set_actor_rotation(u.Rotator(yaw=angle), False)
            record(rail, 'rim structure')
    radius = 231./math.cos(math.pi/8)
    for i in range(8):
        theta = math.pi/8+i*math.pi/4
        p = (CENTRE[0]+radius*math.cos(theta), CENTRE[1]+radius*math.sin(theta), 105.)
        post = ctx.grounded(PREFIX+'Owned post %02d'%i, POST, p[:2], floor=105.,
                            yaw=math.degrees(theta), scale=(.60, .60, .9), collision=False)
        post.static_mesh_component.set_material(0, ctx.asset(TRIM))
        record(post, 'profiled owned structural post')
    roof = ctx.raw(PREFIX+'Glass lid', plate, (*CENTRE, 282.), scale=(4.66, 4.66, .006), collision=False)
    roof.static_mesh_component.set_material(0, glass)
    roof.static_mesh_component.set_cast_shadow(False)
    record(roof, 'clear glass lid')
    projector = ctx.grounded(PREFIX+'Owned hologram projector', PROJECTOR, CENTRE, floor=106., collision=False)
    # The measured native slot0 is its optical lens. Keep the textured body/bars.
    projector.static_mesh_component.set_material(0, lens)
    record(projector, 'owned projector')
    _require(all(r['minimum_cm'][0] >= 7929.9 and r['maximum_cm'][0] <= 8410.1 and
                 r['minimum_cm'][1] >= -240.1 and r['maximum_cm'][1] <= 240.1 and
                 r['minimum_cm'][2] >= -.1 and r['maximum_cm'][2] <= 285.1 for r in records),
             'Podium hardware escapes its approved envelope')
    return records


def _hologram(ctx, material, u, sources, source_probe):
    # Existing presentation derivative retains authored engine pivots/airbrake
    # tree and has no demo graphs. Do not reassemble separate pieces by guess.
    blueprint = ctx.asset(PHOENIX)
    _require(not u.BlueprintEditorLibrary.list_graphs(blueprint), 'Phoenix derivative contains gameplay graphs')
    actor = ctx.raw(PREFIX+'Phoenix presentation', blueprint, (0., 0., 0.), collision=False)
    for key, value in (('auto_possess_player', u.AutoReceiveInput.DISABLED),
                       ('auto_receive_input', u.AutoReceiveInput.DISABLED),
                       ('auto_possess_ai', u.AutoPossessAI.DISABLED)):
        actor.set_editor_property(key, value)
    actor.set_actor_tick_enabled(False)
    expected = {r['name'].removesuffix('_GEN_VARIABLE'): r for r in source_probe['phoenix_templates']
                if r.get('mesh')}
    _require(len(expected) == 4 and len({r['mesh'] for r in expected.values()}) == 4,
             'Exact measured four-part Phoenix component inventory required')
    meshes, source_meshes, seen, excluded = [], [], set(), []
    for component in actor.get_components_by_class(u.ActorComponent):
        component.set_editor_property('auto_activate', False)
        component.deactivate()
        component.set_component_tick_enabled(False)
        if isinstance(component, u.LightComponent):
            component.set_visibility(False)
            component.set_intensity(0.)
        if isinstance(component, u.AudioComponent):
            component.stop()
        if isinstance(component, u.SceneComponent):
            component.set_mobility(u.ComponentMobility.MOVABLE)
        if isinstance(component, u.PrimitiveComponent):
            component.set_simulate_physics(False)
            component.set_enable_gravity(False)
            component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
            component.set_editor_property('generate_overlap_events', False)
            component.set_cast_shadow(False)
        source = None
        if isinstance(component, u.SkeletalMeshComponent):
            source = component.get_skeletal_mesh_asset()
            if source:
                component.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
                data = component.get_editor_property('animation_data')
                clip = ctx.asset(POSE) if source.get_path_name().split('.')[0] == HULL else None
                if clip:
                    _require(clip.get_editor_property('skeleton') == source.skeleton, 'Phoenix pose skeleton mismatch')
                    data.set_editor_property('anim_to_play', clip)
                    data.set_editor_property('saved_position', float(clip.sequence_length))
                else:
                    data.set_editor_property('saved_position', 0.)
                data.set_editor_property('saved_playing', False)
                data.set_editor_property('saved_looping', False)
                component.set_editor_property('animation_data', data)
                component.set_component_tick_enabled(True)
        elif isinstance(component, u.StaticMeshComponent):
            source = component.static_mesh
        name = component.get_name().removesuffix('_GEN_VARIABLE')
        if source and name in expected:
            measured = expected[name]
            _require(source.get_path_name() == measured['mesh'] and
                     component.get_class().get_name() == measured['class'],
                     'Measured Phoenix component mapping changed: '+name)
            _require(name not in seen, 'Duplicate measured Phoenix component: '+name)
            seen.add(name)
            component.set_visibility(True)
            component.set_hidden_in_game(False)
            for slot in range(component.get_num_materials()):
                component.set_material(slot, material)
            meshes.append(component)
            source_meshes.append(source.get_path_name())
            package = source.get_path_name().split('.')[0]
            sources[package] = _sha(ROOT/('Content/'+package[6:]+'.uasset'))
        elif isinstance(component, u.PrimitiveComponent):
            component.set_visibility(False)
            component.set_hidden_in_game(True)
            if source:
                excluded.append({'component': component.get_name(), 'mesh': source.get_path_name(),
                                 'reason': 'Outside exact measured Phoenix render component inventory; disabled'})
                package = source.get_path_name().split('.')[0]
                if package.startswith('/Game/'):
                    sources[package] = _sha(ROOT/('Content/'+package[6:]+'.uasset'))
    _require(seen == set(expected) and any(p.split('.')[0] == HULL for p in source_meshes) and
             any('Engine_Left' in p for p in source_meshes) and any('Engine_Right' in p for p in source_meshes),
             'Complete authored Phoenix hull and engine meshes required')
    points = []
    for component in meshes:
        source = (component.get_skeletal_mesh_asset() if isinstance(component, u.SkeletalMeshComponent)
                  else component.static_mesh)
        b, transform = source.get_bounds(), component.get_world_transform()
        for x in (-1., 1.):
            for y in (-1., 1.):
                for z in (-1., 1.):
                    points.append(u.MathLibrary.transform_location(transform,
                        b.origin+u.Vector(x*b.box_extent.x, y*b.box_extent.y, z*b.box_extent.z)).to_tuple())
    minimum = [min(p[i] for p in points) for i in range(3)]
    maximum = [max(p[i] for p in points) for i in range(3)]
    centre = [(minimum[i]+maximum[i])*.5 for i in range(3)]
    scale = HOLO_LENGTH/max(maximum[0]-minimum[0], maximum[1]-minimum[1])
    _require(.08 < scale < .15, 'Unexpected complete Phoenix size')
    pivot = ctx.raw(PREFIX+'Phoenix rotation pivot', u.TargetPoint, (*CENTRE, HOLO_CENTRE_Z), collision=False)
    pivot.get_editor_property('root_component').set_mobility(u.ComponentMobility.MOVABLE)
    actor.set_actor_scale3d(u.Vector(scale, scale, scale))
    actor.set_actor_rotation(u.Rotator(yaw=-90.), False)
    q = u.Rotator(yaw=-90.).quaternion().rotate_vector(u.Vector(*(v*scale for v in centre)))
    actor.set_actor_location(u.Vector(*CENTRE, HOLO_CENTRE_Z)-q, False, False)
    actor.attach_to_actor(pivot, '', u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD,
                          u.AttachmentRule.KEEP_WORLD, False)
    half = [(maximum[i]-minimum[i])*.5*scale for i in range(3)]
    radius = math.hypot(half[0], half[1])
    _require(radius < 213. and HOLO_CENTRE_Z-half[2] > 124. and
             HOLO_CENTRE_Z+half[2] < 273., 'Rotating complete ship would intersect enclosure/projector')
    return pivot, {'actor': actor.get_path_name(), 'pivot': pivot.get_path_name(),
        'source_meshes': source_meshes, 'scale': scale, 'source_bounds_cm': [minimum, maximum],
        'conservative_sweep_radius_cm': radius, 'height_bounds_cm': [HOLO_CENTRE_Z-half[2], HOLO_CENTRE_Z+half[2]],
        'pose': POSE, 'render_component_mapping': {name: row['mesh'] for name, row in expected.items()},
        'excluded_render_components': excluded, 'no_input_physics_audio_vfx_or_gameplay': True}


def _sequence(ctx, pivot, u, dirty):
    sequence = u.AssetToolsHelpers.get_asset_tools().create_asset(
        'LS_PhoenixDisplay', BASE, u.LevelSequence, u.LevelSequenceFactoryNew())
    _require(sequence, 'Phoenix sequence creation failed')
    dirty.append(sequence.get_path_name())
    u.MovieSceneSequenceExtensions.set_display_rate(sequence, u.FrameRate(FPS, 1))
    u.MovieSceneSequenceExtensions.set_tick_resolution_directly(sequence, u.FrameRate(24000, 1))
    u.MovieSceneSequenceExtensions.set_playback_start(sequence, 0)
    u.MovieSceneSequenceExtensions.set_playback_end(sequence, END_FRAME)
    binding = u.MovieSceneSequenceExtensions.add_possessable(sequence, pivot)
    track = u.MovieSceneBindingExtensions.add_track(binding, u.MovieScene3DTransformTrack)
    section = track.add_section()
    u.MovieSceneSectionExtensions.set_range(section, 0, END_FRAME)
    section.set_completion_mode(u.MovieSceneCompletionMode.RESTORE_STATE)
    section.set_blend_type(u.MovieSceneBlendType.ABSOLUTE)
    section.set_editor_property('use_quaternion_interpolation', False)
    channels = {str(c.get_editor_property('channel_name')): c
                for c in u.MovieSceneSectionExtensions.get_all_channels(section)}
    _require(set(CHANNELS) <= set(channels), 'Native sequence transform channels changed')
    values = (*CENTRE, HOLO_CENTRE_Z, 0., 0., 0., 1., 1., 1.)
    for index, name in enumerate(CHANNELS):
        channel = channels[name]
        channel.set_default(values[index])
        for frame in (0, END_FRAME):
            value = 360. if name == 'Rotation.Z' and frame == END_FRAME else values[index]
            key = channel.add_key(u.FrameNumber(frame), value, 0., u.MovieSceneTimeUnit.DISPLAY_RATE,
                                  u.MovieSceneKeyInterpolation.LINEAR)
            _require(key, 'Could not create Phoenix rotation key')
            key.set_value(value)
            _require(abs(key.get_value()-value) < 1.e-6, 'Phoenix sequence key readback failed')
    placed = ctx.raw(PREFIX+'Phoenix display sequence', u.LevelSequenceActor, (0., 0., 0.), collision=False)
    settings = u.MovieSceneSequencePlaybackSettings()
    settings.set_editor_property('auto_play', True)
    settings.set_editor_property('loop_count', u.MovieSceneSequenceLoopCount(value=-1))
    settings.set_editor_property('disable_camera_cuts', True)
    for field in ('disable_movement_input', 'disable_look_at_input', 'hide_player', 'hide_hud'):
        settings.set_editor_property(field, False)
    placed.set_editor_property('playback_settings', settings)
    placed.set_sequence(sequence)
    actual = placed.get_editor_property('playback_settings')
    _require(actual.get_editor_property('auto_play') and
             actual.get_editor_property('loop_count').get_editor_property('value') == -1,
             'Persistent sequence autoplay/loop readback failed')
    return {'asset': sequence.get_path_name(), 'actor': placed.get_path_name(), 'period_seconds': PERIOD,
            'rotation_track': 'Unwrapped Euler yaw0 to360; linear,60seconds; no camera/input tracks',
            'natural_runtime_motion_verified': False}


def _clearance(world, u):
    from RefineStationWorkroomComposition import _hit
    rows = []
    for name, (a, b) in ROUTES.items():
        hit = _hit(u.SystemLibrary.capsule_trace_single_by_profile(world,
            u.Vector(a[0], a[1], 78.), u.Vector(b[0], b[1], 78.), 34., 75.,
            'Pawn', False, [], u.DrawDebugTrace.NONE, True))
        _require(not hit, 'Preserved Operations route blocked: '+json.dumps({'route': name, 'hit': hit}))
        floors = []
        count = max(1, math.ceil(math.dist(a, b)/100.))
        for step in range(count+1):
            p = [a[i]+(b[i]-a[i])*step/count for i in range(3)]
            floor = _hit(u.SystemLibrary.line_trace_single_by_profile(world,
                u.Vector(p[0], p[1], 35.), u.Vector(p[0], p[1], -65.), 'Pawn', False, [],
                u.DrawDebugTrace.NONE, True))
            _require(floor and abs(floor['point'][2]) < 5. and floor['normal'][2] > .7,
                     'Native route floor support missing: '+name)
            floors.append({'feet': p, 'hit': floor})
        rows.append({'name': name, 'capsule_hit': hit, 'floor_samples': floors})
    return rows


def apply(ctx, expected_map_sha256):
    import unreal as u
    from RefineStationOperationsDisplays import _state
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    map_file = ROOT/('Content/'+MAP[6:]+'.umap')
    _require(re.fullmatch('[0-9a-f]{64}', expected_map_sha256) and
             _sha(map_file) == expected_map_sha256 and world.get_path_name().split('.')[0] == MAP,
             'Require exact latest saved owner preview')
    _require(_sha(BASELINE) == BASELINE_SHA, 'Native Operations dimensions changed')
    _require(_sha(PROBE) == PROBE_SHA, 'Native kit/Phoenix component proof changed')
    source_probe = json.loads(PROBE.read_text())
    _require(source_probe['success'] and source_probe['preservation_pass'] and
             _sha(FROZEN_PROBE_HELPER) == source_probe['recipe_sha256']['RefineStationOperationsComposition.py'],
             'Require preserved source-bound probe and frozen original recipe')
    for package, digest in source_probe['probe']['source_sha256'].items():
        _require(_sha(ROOT/('Content/'+package[6:]+'.uasset')) == digest,
                 'Measured native composition source changed: '+package)
    actors = list(ctx.eas.get_all_level_actors())
    _require(not any(a.get_actor_label().startswith(PREFIX) for a in actors), 'Preserve existing composition pass')
    _require(all(not u.EditorAssetLibrary.does_asset_exist(BASE+'/'+name) for name in OUTPUTS),
             'Preserve existing private podium output assets')
    before = {a.get_path_name(): _state(a, u) for a in actors}
    native = json.loads(BASELINE.read_text())['operations']['actors']
    by_label = {a.get_actor_label(): a for a in actors}
    protected = [r for r in native if r['label'].startswith(('Engineering/Primary workstation/',
                 'OperationsNative/Command island '))]
    _require(len(protected) == 97, 'Complete Goliath29 plus four17-part pods required')
    for row in protected:
        actor = by_label.get(row['label'])
        _require(actor and math.dist(actor.get_actor_location().to_tuple(), row['transform']['location']) < .05,
                 'Existing complete command/staff assembly moved: '+row['label'])
    sources = {}
    for package in plan()['source_assets']:
        sources[package] = _sha(ROOT/('Content/'+package[6:]+'.uasset'))
        ctx.asset(package)
    before_routes = _clearance(world, u)
    # Nine supported points cover the entire podium, not just its centre.
    floor_support = []
    from RefineStationWorkroomComposition import _hit
    for x, y in [CENTRE]+plan()['octagon_vertices_cm']:
        hit = _hit(u.SystemLibrary.line_trace_single_by_profile(world, u.Vector(x, y, 35.),
            u.Vector(x, y, -65.), 'Pawn', False, [], u.DrawDebugTrace.NONE, True))
        _require(hit and abs(hit['point'][2]) < .1 and hit['normal'][2] > .7, 'Podium has no measured floor support')
        floor_support.append(hit)
    dirty = []
    glass, hologram, lens = _optical_materials(u, dirty)
    plate = _octagon(u, dirty, ctx.asset(DARK))
    parts = _podium(ctx, plate, glass, lens, u)
    pivot, ship = _hologram(ctx, hologram, u, sources, source_probe['probe'])
    sequence = _sequence(ctx, pivot, u, dirty)
    u.AutomationLibrary.finish_loading_before_screenshot()
    after_routes = _clearance(world, u)
    _require(all(_state(a, u) == before[a.get_path_name()] for a in actors),
             'Existing scene/material/light/service/animation state changed')
    _require(_sha(map_file) == expected_map_sha256 and all(
        _sha(ROOT/('Content/'+p[6:]+'.uasset')) == digest for p, digest in sources.items()),
        'Helper must not save or mutate source packages')
    return {'dirty_assets': dirty, 'source_sha256': sources, 'plan': plan(), 'parts': parts,
            'native_kit_probe_sha256': PROBE_SHA,
            'hologram': ship, 'sequence': sequence, 'floor_support': floor_support,
            'routes_before': before_routes, 'routes_after': after_routes,
            'existing_actors_preserved': len(actors), 'existing_services_preserved': True,
            'new_lights': 0, 'source_ship_blueprint_and_materials_preserved': True,
            'limits': 'UNVERIFIED native pixels/natural animation. Static support/capsule tests are not walking or visual acceptance.'}
