"""Fixture-mounted rear habitat accents, based on RoomPass3's actual overview.

The lead calls apply(ctx) inside the guarded owner-preview transaction. No map
loads/saves, asset edits, atmosphere, exposure, collision or geometry changes.
Existing lights are replaced one-for-one at their actual placed cornice fixtures;
two small upper-rock accents share the actual crown fixtures. Their bounds-based
aim is explicitly provisional until the lead reviews a rendered overview.
"""
import hashlib
import json
import math
from pathlib import Path

from OutpostGeometryUtils import mesh_union


PREFIX = 'Refine/SkylineRefinement/'
HOUSING = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Meshes/SM_CornerWallCeiling400X70_V6_Lights_Part1.SM_CornerWallCeiling400X70_V6_Lights_Part1'
TOWERS = ((1, 1, 3), (2, 3, 6), (3, 3, 7), (4, 2, 4))
GALLERIES = (-3800, -1600, 1600, 4100)
WARM = (1., .72, .42)
COOL = (.62, .78, 1.)


def _one(actors, label):
    matches = [a for a in actors if a.get_actor_label() == label]
    if len(matches) != 1:
        raise RuntimeError('Expected one placed skyline actor: ' + label)
    return matches[0]


def _snapshot(actor, component):
    color = component.get_light_color()
    return {'actor': actor.get_path_name(), 'label': actor.get_actor_label(),
            'component': component.get_name(), 'location_cm': list(actor.get_actor_location().to_tuple()),
            'rotation_xyzw': list(actor.get_actor_transform().rotation.to_tuple()),
            'intensity': float(component.get_editor_property('intensity')),
            'units': str(component.get_editor_property('intensity_units')),
            'radius_cm': float(component.get_editor_property('attenuation_radius')),
            'color': [color.r, color.g, color.b, color.a],
            'visible': bool(component.get_editor_property('visible')),
            'cast_shadows': bool(component.get_editor_property('cast_shadows')),
            'specular_scale': float(component.get_editor_property('specular_scale')),
            'indirect_lighting_intensity': float(component.get_editor_property('indirect_lighting_intensity')),
            'volumetric_scattering_intensity': float(component.get_editor_property('volumetric_scattering_intensity'))}


def _pose(actor):
    # Compare plain values, not Python UObject/UStruct wrapper identity. UE's
    # Transform exports == but not != as a ScriptOperator. Keep exact precision
    # and the same quaternion representation as the read-only owner inventory.
    transform = actor.get_actor_transform()
    return {'location': tuple(transform.translation.to_tuple()),
            'rotation': tuple(transform.rotation.to_tuple()),
            'scale': tuple(transform.scale3d.to_tuple())}


def apply(ctx):
    import unreal as u
    actors = list(ctx.actors)
    if any(a.get_actor_label().startswith(PREFIX) for a in actors):
        raise RuntimeError('Skyline refinement already exists; restore the guarded previous state')
    inventory_path = Path(u.Paths.project_dir()) / '.agent/local/StationRefinement/OwnerAudit/actors.json'
    inventory_bytes = inventory_path.read_bytes()
    inventory = json.loads(inventory_bytes.decode('utf-8-sig'))
    if not inventory.get('success') or not inventory.get('map_unchanged'):
        raise RuntimeError('Expected successful read-only owner inventory')
    labels = {row['label'] for row in inventory['actors']}
    planned, crowns, retained = [], [], []

    def fixture(key, source_label, expected_power):
        if key + '/Part 1' not in labels or source_label not in labels:
            raise RuntimeError('Fixture was not present in the inspected owner inventory: ' + key)
        housing = _one(actors, key + '/Part 1')
        mount = housing.get_component_by_class(u.StaticMeshComponent)
        if (not mount or not mount.static_mesh or mount.static_mesh.get_path_name() != HOUSING or
                housing.get_editor_property('hidden') or not mount.get_editor_property('visible')):
            raise RuntimeError('Expected visible native cornice fixture: ' + key)
        source = _one(actors, source_label)
        lights = source.get_components_by_class(u.LocalLightComponent)
        if len(lights) != 1:
            raise RuntimeError('Fixture light is ambiguous: ' + source_label)
        light = lights[0]
        state = _snapshot(source, light)
        if (not state['visible'] or source.get_editor_property('hidden') or state['cast_shadows'] or
                light.get_editor_property('intensity_units') != u.LightUnits.LUMENS or
                abs(state['intensity'] - expected_power) > .1):
            raise RuntimeError('Inspected fixture light state changed: ' + source_label)
        if math.dist(state['location_cm'], housing.get_actor_location().to_tuple()) > 110:
            raise RuntimeError('Source light is no longer at its physical fixture: ' + key)
        retained.append((housing, _pose(housing), tuple(mount.get_materials())))
        return key, housing, mount, source, light, state

    for tower, middle, top in TOWERS:
        key = 'SkylineLighting/Tower %d/Storey %d' % (tower, middle)
        replacement = tower in (2, 3)
        source = 'FrontLighting/Tower %d facade wash' % tower if replacement else key + '/Local wash'
        planned.append((fixture(key, source, 750 if replacement else 1300),
                        'Tower %d inhabited band' % tower, 1800, 1050, 360, WARM if tower in (1, 4) else COOL))
        key = 'SkylineLighting/Tower %d/Storey %d' % (tower, top)
        crowns.append((tower, fixture(key, key + '/Local wash', 1000)))
    for y in GALLERIES:
        key = 'SkylineLighting/Upper gallery/' + str(y)
        planned.append((fixture(key, key + '/Local wash', 800),
                        'Gallery link ' + str(y), 1000, 800, 260, COOL))

    rock = _one(actors, 'Asteroid/Foundation')
    rock_center, rock_extent = mesh_union(rock)
    rock_pose = _pose(rock)
    accents = []
    for tower, row in crowns:
        if tower not in (2, 3):
            continue
        _, housing, mount, _, _, state = row
        outward = housing.get_actor_right_vector()
        position = u.Vector(*state['location_cm']) + u.Vector(0, 0, 14)
        # In the actual overview the remaining massif rises behind the crown.
        # Do not enable collision or copy the huge owner mesh just to aim a light.
        # Keep the provisional aim within its actual bounds and above the roof.
        aim = position - outward * 1200 + u.Vector(0, 0, 1000)
        target = u.Vector(*[max(getattr(rock_center, axis) - getattr(rock_extent, axis) + 10,
                           min(getattr(aim, axis), getattr(rock_center, axis) + getattr(rock_extent, axis) - 10))
                           for axis in ('x', 'y', 'z')])
        distance = math.dist(position.to_tuple(), target.to_tuple())
        if not 600 < distance < 1900 or target.z - position.z < 400:
            raise RuntimeError('Rock accent no longer fits the inspected upper backdrop')
        accents.append((tower, housing, mount, position, target, distance))

    changes = []

    def emitter(label, cls, position, target, mount, lumens, radius, color):
        rotation = u.MathLibrary.find_look_at_rotation(position, target)
        actor = ctx.eas.spawn_actor_from_class(cls, position, rotation)
        if not actor:
            raise RuntimeError('Could not create mounted skyline accent: ' + label)
        ctx.register(actor, PREFIX + label)
        component = actor.get_component_by_class(u.LocalLightComponent)
        component.set_mobility(u.ComponentMobility.MOVABLE)
        component.set_intensity_units(u.LightUnits.LUMENS)
        component.set_intensity(lumens)
        component.set_attenuation_radius(radius)
        component.set_light_color(u.LinearColor(*color, 1.))
        component.set_cast_shadows(False)
        component.set_editor_property('specular_scale', .25)
        component.set_editor_property('indirect_lighting_intensity', .25)
        component.set_editor_property('volumetric_scattering_intensity', 0.)
        if isinstance(component, u.RectLightComponent):
            component.set_source_width(240)
            component.set_source_height(12)
        else:
            component.set_inner_cone_angle(12)
            component.set_outer_cone_angle(24)
        if not actor.attach_to_component(mount, u.Name(''), u.AttachmentRule.KEEP_WORLD,
                u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, False):
            raise RuntimeError('Could not attach skyline light to existing cornice')
        actual = _snapshot(actor, component)
        if abs(actual['intensity'] - lumens) > .1 or abs(actual['radius_cm'] - radius) > .1:
            raise RuntimeError('Skyline emitter parameter readback failed')
        actual['aim_cm'] = list(target.to_tuple())
        return actual

    for row, name, power, radius, drop, color in planned:
        key, housing, mount, source, component, before = row
        position = source.get_actor_location()
        target = position - housing.get_actor_right_vector() * 100 - u.Vector(0, 0, drop)
        after = emitter(name, u.RectLight, position, target, mount, power, radius, color)
        ctx.records.append({'kind': 'skyline_light_replacement', 'before': before,
                            'replacement': after, 'fixture': key})
        component.set_visibility(False, False)
        changes.append({'fixture': key, 'before': before, 'after': after})
    crown_changes = []
    for tower, row in crowns:
        key, _, _, actor, component, before = row
        ctx.records.append({'kind': 'skyline_crown_light', 'before': before})
        component.set_intensity(1400)
        component.set_attenuation_radius(1050)
        component.set_light_color(u.LinearColor(*WARM, 1.))
        component.set_editor_property('volumetric_scattering_intensity', 0.)
        crown_changes.append({'fixture': key, 'before': before, 'after': _snapshot(actor, component)})
    rock_changes = []
    for tower, housing, mount, position, target, distance in accents:
        after = emitter('Tower %d upper rock accent' % tower, u.SpotLight, position, target,
                        mount, 1800, distance + 220, COOL)
        rock_changes.append({'fixture': housing.get_actor_label(), 'after': after,
                             'inner_cone_degrees': 12, 'outer_cone_degrees': 24,
                             'aim_basis': 'Actual fixture/rock bounds plus reviewed overview; not a measured surface hit'})

    # Only local light actors/components changed. Retain the owner transforms,
    # native lens materials and rock placement; no stand-in luminous geometry.
    for actor, pose, materials in retained:
        now = _pose(actor)
        if (now != pose or
                tuple(actor.get_component_by_class(u.StaticMeshComponent).get_materials()) != materials):
            raise RuntimeError('Existing skyline fixture pose/material was changed: ' +
                               repr({'label': actor.get_actor_label(), 'before': pose, 'after': now}))
    rock_after = _pose(rock)
    if rock_after != rock_pose:
        raise RuntimeError('Owner rock placement changed: ' + repr({'before': rock_pose, 'after': rock_after}))
    return {'module': 'skyline_lighting', 'dirty_assets': [],
            'basis': 'RoomPass3/07_Market and 08_Overview; approved Station-Design-Targets',
            'inventory_sha256': hashlib.sha256(inventory_bytes).hexdigest(),
            'facade_replacements': changes, 'warm_crowns': crown_changes, 'rock_accents': rock_changes,
            'new_light_actors': 10, 'replaced_active_lights': 8, 'net_added_active_lights': 2,
            'new_shadow_sources': 0, 'original_emissive_materials_preserved': True,
            'owner_rock_pose_before': rock_pose, 'owner_rock_pose_after': rock_after,
            'unchanged': ['owner geometry/transforms', 'Earth', 'Home', 'collision', 'materials',
                          'fog', 'global lighting', 'exposure', 'sky and space'],
            'acceptance': 'Matched actual overview and rear-district render required; rock aim is provisional'}
