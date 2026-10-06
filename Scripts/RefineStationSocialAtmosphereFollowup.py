"""Bounded whole-lounge follow-up after the grounded ambient pool match.

Two supported aisle practicals, two distinct native Genesis graphics, and three
seated conversation guests. The lead owns native execution, saving and matched
room renders. No source asset, existing actor transform, gameplay or exposure edits.
"""
import hashlib
import json
import math
from pathlib import Path

from OutpostGeometryUtils import mesh_union
from RefineStationSocialFinish import _aisle
from RefineStationSocialSeatedCrew import MESH, PRIVATE_CLIP, SOFA
from RefineStationSocialAtmosphere import FIXTURE, GRAPHITE


MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
PREFIX = 'Refine/SocialAtmosphereFollowup/'
PRIVATE = '/Game/OutpostSandbox/StationRefinement/SocialAtmosphereFollowup/Materials'
P4 = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/'
MASTER = '/Game/OutpostSandbox/OwnerPreview/Materials/DisplayWall/M_NativeBlueDisplayWall_20261006'
VARIANTS = P4 + 'Materials/Instances/Translucent/MI_DigitalGlass_Window400X200_'
PANES = (('Engineering/Bay W1/Glass', 'CosmoAdvertisment', 'WAYFARER / DISCOVER'),
         ('Engineering/Bay S1/Glass', 'DigitalPanel', 'THE LONGER ROUTE / SOCIAL'))


def _one(actors, label):
    rows = [actor for actor in actors if actor.get_actor_label() == label]
    if len(rows) != 1:
        raise RuntimeError('Expected one reviewed lounge actor: ' + label)
    return rows[0]


def _pose(actor):
    t = actor.get_actor_transform()
    return (*t.translation.to_tuple(), *t.rotation.to_tuple(), *t.scale3d.to_tuple())


def _hash(root, path):
    return hashlib.sha256((root / ('Content/' + path.split('.')[0][6:] + '.uasset')).read_bytes()).hexdigest()


def _screen(ctx, u, variant, dirty, guard):
    """Reuse the already verified DisplayWall interface and native owned masks."""
    edit = u.MaterialEditingLibrary
    source, master = ctx.asset(VARIANTS + variant), ctx.asset(MASTER)
    if source.get_editor_property('parent').get_path_name().split('.')[0] != P4 + 'Materials/Masters/MM_MasterMaterial02_Translucent':
        raise RuntimeError('Native Genesis screen parent changed')
    if master.get_editor_property('blend_mode') != u.BlendMode.BLEND_TRANSLUCENT:
        raise RuntimeError('Reviewed private display master changed')
    scalars = {str(n): float(edit.get_material_instance_scalar_parameter_value(source, n))
               for n in edit.get_scalar_parameter_names(source)}
    vectors = {str(n): edit.get_material_instance_vector_parameter_value(source, n)
               for n in edit.get_vector_parameter_names(source)}
    textures = {str(n): edit.get_material_instance_texture_parameter_value(source, n)
                for n in edit.get_texture_parameter_names(source)}
    switches = {str(n): bool(edit.get_material_instance_static_switch_parameter_value(source, n))
                for n in edit.get_static_switch_parameter_names(source)}
    for asset in (source, master, *(texture for texture in textures.values() if texture)):
        if asset.get_path_name().startswith('/Game/'):
            guard(asset.get_path_name())
    changes = {'Opacity': .88, 'Opacity_Lerp': 0., 'Height Roughness Mask': 0.,
               'Refraction': 1., 'Refraction_Lerp': 1., 'Normal Intensity': 0.,
               'Intensity EM1': 12. if variant == 'DigitalPanel' else 8.,
               'Intensity EM2': 6. if variant == 'DigitalPanel' else 2., 'Intensity EM3': 2.}
    if not set(changes) <= scalars.keys() or 'SSDisplayBackground' not in map(str, edit.get_vector_parameter_names(master)):
        raise RuntimeError('Reviewed native display controls are missing')
    scalars.update(changes)
    for channel, color in ((1, (.28, .62, 1., 1.)), (2, (.60, .80, 1., 1.)), (3, (.23, .53, .85, 1.))):
        for endpoint in (1, 2):
            parameter = 'Color %d EM%d' % (endpoint, channel)
            if parameter not in vectors:
                raise RuntimeError('Native screen color channel missing: ' + parameter)
            vectors[parameter] = u.LinearColor(*color)
    vectors['SSDisplayBackground'] = u.LinearColor(.035, .09, .18, 1.)
    name = 'MI_Lounge_' + variant
    destination = PRIVATE + '/' + name
    if u.EditorAssetLibrary.does_asset_exist(destination):
        raise RuntimeError('Preserve prior private lounge graphic: ' + destination)
    material = u.AssetToolsHelpers.get_asset_tools().create_asset(
        name, PRIVATE, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
    if not material:
        raise RuntimeError('Could not create private lounge graphic')
    edit.set_material_instance_parent(material, master)
    for parameter, value in scalars.items():
        edit.set_material_instance_scalar_parameter_value(material, parameter, value)
    for parameter, value in vectors.items():
        edit.set_material_instance_vector_parameter_value(material, parameter, value)
    for parameter, value in textures.items():
        if not value:
            raise RuntimeError('Native screen texture is missing: ' + parameter)
        edit.set_material_instance_texture_parameter_value(material, parameter, value)
    for parameter, value in switches.items():
        edit.set_material_instance_static_switch_parameter_value(material, parameter, value)
    edit.update_material_instance(material)
    for parameter, value in scalars.items():
        if abs(edit.get_material_instance_scalar_parameter_value(material, parameter)-value) > .0001:
            raise RuntimeError('Lounge screen scalar readback differs: ' + parameter)
    for parameter, value in vectors.items():
        actual = edit.get_material_instance_vector_parameter_value(material, parameter)
        if max(abs(a-b) for a, b in zip(actual.to_tuple(), value.to_tuple())) > .0001:
            raise RuntimeError('Lounge screen color readback differs: ' + parameter)
    for parameter, value in textures.items():
        if edit.get_material_instance_texture_parameter_value(material, parameter) != value:
            raise RuntimeError('Lounge screen lost its native graphic: ' + parameter)
    for parameter, value in switches.items():
        if bool(edit.get_material_instance_static_switch_parameter_value(material, parameter)) != value:
            raise RuntimeError('Lounge screen lost its native animation switch: ' + parameter)
    dirty.append(material.get_path_name())
    return material, {'variant': variant, 'private': material.get_path_name(),
                      'textures': {n: texture.get_path_name() for n, texture in textures.items()},
                      'changes': changes, 'native_masks_scroll_and_uv_preserved': True}


def apply(ctx):
    import unreal as u
    root = Path(u.Paths.project_dir()).resolve()
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name().split('.')[0] != MAP:
        raise RuntimeError('Whole-lounge follow-up belongs only to the owner preview')
    actors = list(ctx.eas.get_all_level_actors())
    if any(actor.get_actor_label().startswith(PREFIX) for actor in actors):
        raise RuntimeError('Whole-lounge follow-up already exists; preserve it')
    _one(actors, 'Refine/OrbitPool/Alternating match sequence')
    roof = _one(actors, 'Engineering/Roof structure')
    if math.dist(roof.get_actor_location().to_tuple()[:2], (4200., -3400.)) > .05:
        raise RuntimeError('Owner lounge anchor moved')
    before = {actor.get_path_name(): _pose(actor) for actor in actors}
    before_routes = _aisle(world, u)
    sources, dirty = {}, []

    def guard(path):
        package = path.split('.')[0]
        if package not in sources:
            sources[package] = _hash(root, package)

    for path in (FIXTURE, GRAPHITE, MESH, SOFA, PRIVATE_CLIP):
        ctx.asset(path)
        guard(path)
    report = {'module': 'whole_lounge_atmosphere_followup', 'dirty_assets': dirty,
              'fixtures': [], 'graphics': [], 'seated_guests': [], 'before_routes': before_routes,
              'limits': 'Authoring only; requires fresh matched lounge/bar/reverse/booth renders and native playback.'}
    ceilings = []
    for actor in actors:
        if actor.get_actor_label().startswith(('QuietCeiling/Engineering/Panel ', 'Engineering/Ceiling panel')):
            component = actor.get_component_by_class(u.StaticMeshComponent)
            if component and component.get_editor_property('visible') and not actor.get_editor_property('hidden'):
                c, e = mesh_union(actor)
                ceilings.append((actor, c, e))
    if not ceilings:
        raise RuntimeError('Actual visible lounge ceiling support is missing')

    # Two modest central practicals connect the pools without lifting global exposure.
    for index, y in enumerate((-3000., -3600.), 1):
        lamp = ctx.raw('SocialAtmosphereFollowup/Aisle %d/Housing' % index,
                       FIXTURE, (4200, y, 350), collision=False)
        c, e = mesh_union(lamp)
        factor = 160. / (2*e.x)
        lamp.set_actor_scale3d(u.Vector(factor, factor, factor))
        c, e = mesh_union(lamp)
        lamp.set_actor_location(lamp.get_actor_location()+u.Vector(4200, y, 350)-c, False, False)
        c, e = mesh_union(lamp)
        if c.z-e.z < 310 or c.z+e.z >= 390:
            raise RuntimeError('Central fixture violates head/ceiling clearance')
        # Match the native ceiling underside as in OutpostFrontLighting. These
        # decorative panels may omit Pawn collision; their actual mesh bounds
        # provide support without inventing an invisible collision ceiling.
        supports = []
        for side in (-1, 1):
            x, bottom = c.x + side*55, c.z+e.z
            candidates = [(actor, center.z-extent.z) for actor, center, extent in ceilings
                          if abs(center.x-x) <= extent.x+.01 and abs(center.y-y) <= extent.y+.01
                          and bottom < center.z-extent.z < 425]
            if not candidates:
                raise RuntimeError('No actual ceiling support above central fixture')
            support, top = min(candidates, key=lambda row: row[1])
            ctx.box('SocialAtmosphereFollowup/Aisle %d/Hanger %d' % (index, side),
                    (x, y, (bottom+top)*.5), (1.5, 1.5, top-bottom), GRAPHITE, False)
            supports.append({'roof_z': top, 'roof_actor': support.get_actor_label(),
                             'evidence': 'Native visible ceiling mesh bounds at hanger XY'})
        position = u.Vector(c.x, c.y, c.z-e.z-1)
        light = ctx.eas.spawn_actor_from_class(u.RectLight, position, u.Rotator(pitch=-90))
        ctx.register(light, 'SocialAtmosphereFollowup/Aisle %d/Local key' % index)
        component = light.get_component_by_class(u.RectLightComponent)
        component.set_mobility(u.ComponentMobility.MOVABLE)
        component.set_intensity_units(u.LightUnits.LUMENS)
        component.set_intensity(1150.)
        component.set_attenuation_radius(850.)
        component.set_source_width(145.)
        component.set_source_height(20.)
        component.set_light_color(u.LinearColor(1., 1., 1., 1.))
        component.set_editor_property('use_temperature', True)
        component.set_editor_property('temperature', 3800.)
        component.set_editor_property('specular_scale', .12)
        component.set_editor_property('indirect_lighting_intensity', 1.)
        component.set_editor_property('volumetric_scattering_intensity', 0.)
        component.set_cast_shadows(False)
        if not light.attach_to_component(lamp.static_mesh_component, u.Name(''), u.AttachmentRule.KEEP_WORLD,
                u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, False):
            raise RuntimeError('Central key could not attach to its physical housing')
        report['fixtures'].append({'center': list(c.to_tuple()), 'extent': list(e.to_tuple()),
                                   'supports': supports, 'lumens': 1150., 'radius_cm': 850., 'kelvin': 3800.})

    for label, variant, heading in PANES:
        actor = _one(actors, label)
        component = actor.get_component_by_class(u.StaticMeshComponent)
        if (not component or not component.static_mesh or
                not component.static_mesh.get_name().endswith('_V2_Part2_DigitalWindow')):
            raise RuntimeError('Selected graphic lost its native digital pane')
        original = [m.get_path_name() if m else None for m in component.get_materials()]
        if not original or any(not value or 'MI_HologramWallBlue_KeosAdvertisment' not in value for value in original):
            raise RuntimeError('Selected repeated advertisement has changed; preserve owner override')
        collision = component.get_collision_enabled()
        material, row = _screen(ctx, u, variant, dirty, guard)
        for slot in range(component.get_num_materials()):
            component.set_material(slot, material)
        if component.get_collision_enabled() != collision:
            raise RuntimeError('Screen graphic changed collision')
        c, e = mesh_union(actor)
        forward = actor.get_actor_forward_vector()
        depth = abs(forward.x)*e.x + abs(forward.y)*e.y
        title = ctx.text('SocialAtmosphereFollowup/Screen %s/Heading' % variant, heading,
                         c + forward*(depth+2) + u.Vector(0, 0, e.z*.73), actor.get_actor_rotation().yaw,
                         18., (.66, .86, 1.))
        title.set_actor_enable_collision(False)
        row.update(actor=label, original_materials=original, title=heading)
        report['graphics'].append(row)

    # Reuse the measured native sofa pose; three guests form two facing pairs.
    seated_receipt = json.loads((root / '.agent/local/StationRefinement/SocialSeated1.json').read_text(encoding='utf-8'))
    if not seated_receipt['success']:
        raise RuntimeError('Measured seated authoring receipt is not successful')
    anchor = _one(actors, 'Crew/Lounge conversation A')
    anchor_mesh = anchor.get_component_by_class(u.SkeletalMeshComponent)
    clip = ctx.asset(PRIVATE_CLIP)
    mesh = ctx.asset(MESH)
    if anchor_mesh.get_skeletal_mesh_asset() != mesh or mesh.skeleton != clip.get_editor_property('skeleton'):
        raise RuntimeError('Existing seated rig/clip changed')
    origin_z = float(seated_receipt['result']['animation']['fixed_actor_origin_z'])
    scale = anchor_mesh.get_relative_transform().scale3d
    reference_sofa = _one(actors, 'Refine/Social/Conversation 1/Sofa south')
    expected = reference_sofa.static_mesh_component.get_world_transform().transform_location(u.Vector(91, -30, origin_z))
    if (anchor.get_actor_location()-expected).length() > .05:
        raise RuntimeError('Existing measured seated reference moved')
    for index, (pocket, side, phase) in enumerate(((1, 'north', 1.1), (3, 'south', 2.3), (3, 'north', 3.2)), 1):
        sofa = _one(actors, 'Refine/Social/Conversation %d/Sofa %s' % (pocket, side))
        native = sofa.static_mesh_component
        if native.static_mesh.get_path_name().split('.')[0] != SOFA or sofa.get_editor_property('hidden'):
            raise RuntimeError('Conversation seat is not the visible measured sofa')
        transform = native.get_world_transform()
        if max(abs(value-1.) for value in transform.scale3d.to_tuple()) > .0001:
            raise RuntimeError('Measured sofa must retain its unit scale')
        position = transform.transform_location(u.Vector(91, -30, origin_z))
        rotation = sofa.get_actor_rotation()
        if abs(rotation.pitch) > .001 or abs(rotation.roll) > .001:
            raise RuntimeError('Conversation sofa is tilted')
        actor = ctx.eas.spawn_actor_from_class(u.SkeletalMeshActor, position, u.Rotator(yaw=rotation.yaw))
        ctx.register(actor, 'SocialAtmosphereFollowup/Conversation guest %d' % index)
        component = actor.skeletal_mesh_component
        component.set_skeletal_mesh_asset(mesh)
        component.set_relative_scale3d(scale)
        for slot, material in enumerate(anchor_mesh.get_materials()):
            component.set_material(slot, material)
        component.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
        data = component.get_editor_property('animation_data')
        data.anim_to_play, data.saved_looping, data.saved_playing, data.saved_position = clip, True, True, phase
        component.set_editor_property('animation_data', data)
        component.set_update_animation_in_editor(True)
        component.play_animation(clip, True)
        component.set_position(phase, False)
        actor.set_actor_enable_collision(False)
        if position.x > 3950 or not -4000 < position.y < -2400:
            raise RuntimeError('Seated guest intrudes on the walking corridor or room boundary')
        # Rigid Z rotation preserves the proven sole/sofa contacts. Match the
        # actual sofa's grounded base to the measured reference; a hip trace
        # would hit that sofa's collision rather than the floor beneath it.
        sofa_center, sofa_extent = mesh_union(sofa)
        floor_z = sofa_center.z-sofa_extent.z
        if abs(floor_z) > .5:
            raise RuntimeError('Measured sofa is no longer grounded on the shared room floor')
        report['seated_guests'].append({'actor': actor.get_actor_label(), 'sofa': sofa.get_actor_label(),
            'location': list(position.to_tuple()), 'yaw': rotation.yaw, 'mesh_scale': list(scale.to_tuple()),
            'clip': clip.get_path_name(), 'phase_seconds': phase, 'seat_local_anchor': [91, -30, origin_z],
            'sofa_base_z': floor_z, 'evidence': 'Rigid reuse of measured private seated pose; requires rendered contact review'})

    current = {actor.get_path_name(): actor for actor in ctx.eas.get_all_level_actors()}
    changed = [path for path, pose in before.items() if path not in current or _pose(current[path]) != pose]
    if changed:
        raise RuntimeError('Whole-lounge follow-up changed protected actor transforms: ' + str(changed))
    if any(_hash(root, path) != digest for path, digest in sources.items()):
        raise RuntimeError('Whole-lounge follow-up changed a source asset')
    report.update(protected_actors=len(before), protected_actor_transforms_unchanged=True,
                  source_hashes_preserved=sources, after_routes=_aisle(world, u),
                  unchanged=['owner architecture and layout', 'existing furniture/characters', 'pool match',
                             'other rooms', 'global exposure', 'original assets'])
    return report
