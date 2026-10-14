"""Bounded practical bar lighting; the lead alone saves and reviews native pixels.

Reuse four existing bar lights, add two short-range shadowless counter washes,
and house the shelf emitters. Furniture, character materials and approved room
lighting stay unchanged. No global exposure or source-asset edits.
"""
import hashlib
import math
import re
from pathlib import Path

from OutpostGeometryUtils import mesh_union
from RefineStationBarPresentation import _one, _path, _require
from RefineStationLoungeCeiling import _snapshot
from StationRefinementSupport import transform_record

MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
PREFIX = 'Refine/BarLighting/'
GRAPHITE = '/Game/OutpostSandbox/Materials/M_OutpostGraphite'
LENS = '/Game/OutpostSandbox/StationRefinement/BarPresentation20261006/M_BarCoolDiffuser'
FEMALE = '/Game/SpaceSurvival/Licensed/AlienFemalePresentation/SK_AlienFemalePresentation'
LIGHT_FIELDS = ('intensity', 'attenuation_radius', 'source_width', 'source_height',
                'temperature', 'use_temperature', 'specular_scale', 'cast_shadows',
                'indirect_lighting_intensity', 'volumetric_scattering_intensity')


def _light_state(component):
    values = {}
    for name in LIGHT_FIELDS:
        if hasattr(component, name):
            value = component.get_editor_property(name)
            values[name] = value if isinstance(value, bool) else float(value)
    color = component.get_editor_property('light_color')
    values['color_rgba'] = [color.r, color.g, color.b, color.a]
    values['visible'] = component.is_visible()
    return values


def apply(ctx, expected_map_sha256):
    """Stage local lighting and six shelf housing pieces; never save or import."""
    import unreal as u
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    file = root/('Content/'+MAP[6:]+'.umap')
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    _require(re.fullmatch('[0-9a-f]{64}', expected_map_sha256) and sha(file) == expected_map_sha256,
             'Require exact current preview identity')
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    _require(world.get_path_name().split('.')[0] == MAP, 'Lighting targets only the owner preview')
    actors = list(ctx.eas.get_all_level_actors())
    _require(not any(a.get_actor_label().startswith(PREFIX) for a in actors), 'Preserve existing bar-lighting pass')
    staff = _one(actors, 'Crew/Lounge guest')
    female = staff.get_component_by_class(u.SkeletalMeshComponent)
    _require(_path(female.get_skeletal_mesh_asset()) == FEMALE and
             math.dist(staff.get_actor_location().to_tuple(), (4150., -4160., 85.)) < .01,
             'Require reviewed saved female at her service mark')
    before = {a.get_path_name(): _snapshot(a, u) for a in actors}
    old_lights = {c.get_path_name(): _light_state(c) for a in actors for c in a.get_components_by_class(u.LightComponent)}
    old_meshes = {c.get_path_name(): _path(c.static_mesh) for a in actors for c in a.get_components_by_class(u.StaticMeshComponent)}
    source_paths = (GRAPHITE, LENS)
    sources = {p: sha(root/('Content/'+p[6:]+'.uasset')) for p in source_paths}
    for path in source_paths:
        ctx.asset(path)
    changed, allowed, fixtures = [], set(), []

    def attach(actor, parent):
        component = parent.get_component_by_class(u.StaticMeshComponent)
        _require(component is not None and actor.attach_to_component(component, u.Name(''),
                 u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, False),
                 'Bar practical needs its measured physical mount')

    def box(label, center, size, material, parent):
        actor = ctx.box(PREFIX+label, center, size, material, False)
        actor.static_mesh_component.set_cast_shadow(False)
        attach(actor, parent)
        return actor

    def tune(actor, lumens, radius, kelvin, width, height, specular, target=None):
        component = actor.get_component_by_class(u.RectLightComponent)
        _require(component is not None, 'Expected existing/new RectLight')
        previous = {'pose': transform_record(actor), 'light': _light_state(component)}
        if target is not None:
            position = actor.get_actor_location()
            actor.set_actor_rotation(u.MathLibrary.find_look_at_rotation(position, u.Vector(*target)), False)
        component.set_mobility(u.ComponentMobility.MOVABLE)
        component.set_intensity_units(u.LightUnits.LUMENS)
        component.set_intensity(lumens)
        component.set_attenuation_radius(radius)
        component.set_source_width(width)
        component.set_source_height(height)
        component.set_light_color(u.LinearColor(1., 1., 1., 1.))
        component.set_editor_property('use_temperature', True)
        component.set_editor_property('temperature', kelvin)
        component.set_editor_property('specular_scale', specular)
        component.set_editor_property('indirect_lighting_intensity', .25)
        component.set_editor_property('volumetric_scattering_intensity', 0.)
        component.set_cast_shadows(False)
        actual = _light_state(component)
        _require(abs(actual['intensity']-lumens) < .01 and not actual['cast_shadows'] and
                 abs(actual['temperature']-kelvin) < .01, 'Bar light readback differs')
        changed.append({'label': actor.get_actor_label(), 'before': previous,
                        'after': {'pose': transform_record(actor), 'light': actual}})
        return component

    # Existing pendants already have visible housings and suspension. Their
    # previous 3300K/1100lm warm downlight left the black-chrome face unreadable.
    for index, lumens in ((1, 3200.), (2, 2600.)):
        actor = _one(actors, 'Refine/SocialFollowup/Bar/Counter key '+str(index))
        parent = actor.get_attach_parent_actor()
        _require(parent is not None, 'Counter key has lost its existing practical housing')
        c, e = mesh_union(parent)
        p = actor.get_actor_location()
        _require(abs(p.z-(c.z-e.z-1.)) < .1 and abs(p.y+4020.) < .1 and p.z > 300.,
                 'Existing pendant geometry or emitter location changed')
        allowed.add(actor.get_path_name())
        tune(actor, lumens, 600., 5000., min(220., e.x*1.8), min(20., e.y*1.8), .65,
             (4150., -4160., 135.))
        fixtures.append({'kind': 'existing_pendant', 'housing': parent.get_actor_label(),
                         'light': actor.get_actor_label(), 'position_cm': list(p.to_tuple())})

    # Reuse the two shelf lights; add a shallow, visibly attached hood and lens
    # above each emitter. The light lies below the opaque hood, facing bottles.
    for index in (0, 1):
        actor = _one(actors, 'Refine/SocialDetail/Bar/Shelf key '+str(index))
        p = actor.get_actor_location()
        _require(math.dist(p.to_tuple(), (4190., -4415., 237.+60.*index)) < .01, 'Shelf key moved')
        parent = _one(actors, 'Refine/Social/Bar/Bottle shelf 1' if index == 0 else
                      'Refine/BarPresentation/Bottle display/Rail 1')
        hood = box('Shelf '+str(index)+'/Hood', (4190., -4424., p.z+4.5),
                   (338., 30., 5.), GRAPHITE, parent)
        box('Shelf '+str(index)+'/Diffuser', (4190., -4424., p.z+1.9),
            (328., 24., .4), LENS, hood)
        c, e = mesh_union(parent)
        gap = c.z-e.z-(p.z+7.)
        if gap > .01:
            _require(gap < 12., 'Shelf housing is not close to measured support')
            for side in (-1, 1):
                box('Shelf '+str(index)+'/Mount '+str(side), (4190.+side*162., -4433., p.z+7.+gap*.5),
                    (3., 10., gap+.2), GRAPHITE, parent)
        else:
            _require(gap > -8., 'Shelf hood excessively intersects its support')
        attach(actor, hood)
        allowed.add(actor.get_path_name())
        tune(actor, 440., 185., 5200., 326., 5., .18)
        fixtures.append({'kind': 'shelf', 'housing': hood.get_actor_label(), 'parent': parent.get_actor_label(),
                         'support_gap_cm': gap, 'light_below_hood_cm': 2.})

    # Two narrow local washes originate beyond existing center-panel diffusers.
    # They add no shadow maps and do not illuminate the whole lounge floor.
    for index in (1, 2):
        base = 'Refine/BarPresentation/Counter %d/Panel 2/' % index
        housing = _one(actors, base+'Practical housing')
        lens = _one(actors, base+'Recessed diffuser')
        c, e = mesh_union(lens)
        position = u.Vector(c.x, c.y+e.y+.4, c.z)
        light = ctx.eas.spawn_actor_from_class(u.RectLight, position)
        _require(light is not None, 'Cannot create bounded counter wash')
        ctx.register(light, PREFIX+'Counter '+str(index)+'/Recess wash')
        attach(light, housing)
        tune(light, 320., 230., 6000., min(100., e.x*1.9), 1.2, .22,
             (c.x, c.y+60., 25.))
        fixtures.append({'kind': 'recessed_counter', 'housing': housing.get_actor_label(),
                         'diffuser': lens.get_actor_label(), 'position_cm': list(position.to_tuple()),
                         'outside_diffuser_cm': .4})

    for actor in actors:
        key = actor.get_path_name()
        old, now = before[key], _snapshot(actor, u)
        if key in allowed:
            for field in ('location', 'scale'):
                _require(math.dist(now[field], old[field]) < .005, 'Local bar light moved or rescaled')
            for field in ('hidden', 'materials'):
                _require(now[field] == old[field], 'Local bar light changed unrelated state')
        else:
            _require(now == old, 'Protected room actor changed: '+actor.get_actor_label())
            for component in actor.get_components_by_class(u.LightComponent):
                _require(_light_state(component) == old_lights[component.get_path_name()], 'Other light parameters changed')
        for component in actor.get_components_by_class(u.StaticMeshComponent):
            _require(_path(component.static_mesh) == old_meshes[component.get_path_name()], 'Existing mesh changed')
    _require(len(allowed) == 4 and len(changed) == 6, 'Unexpected local-light scope')
    _require(sha(file) == expected_map_sha256 and all(sha(root/('Content/'+p[6:]+'.uasset')) == h for p, h in sources.items()),
             'Lighting helper must not save or change source packages')
    return {'dirty_assets': [], 'source_sha256': sources, 'lights': changed, 'fixtures': fixtures,
            'changed_existing_light_allowlist': sorted(allowed), 'new_light_count': 2,
            'new_shadow_casting_light_count': 0, 'all_modified_lights_shadowless': True,
            'furniture_character_materials_and_approved_lighting_preserved': True,
            'created': [transform_record(a) for a in ctx.created],
            'limits': 'Prepared bar-local practical lighting; actual saved close and roomwide pixels determine acceptance.'}
