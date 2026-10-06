"""Localize inspected inherited lights in the private docked-cargo map only.

The lead loads L_DockedCargo, calls apply(ctx), saves, then reloads the owner
preview for render/warning review. No loads/saves, vendor edits, intensity or
material changes here. Sphere counts are diagnostic bounds, not GPU timings.
"""
import hashlib
import json
import math
from pathlib import Path

MAP = '/Game/OutpostSandbox/StationRefinement/Cargo/L_DockedCargo'
MAP_SHA = '9963582bd67e4db6e3fd6a47f5294f732947bcc4294c3728c2c7f988e8d93627'
INVENTORY_SHA = '3ea085a734f760f2034f69e71968a38e92dc8f1a1a5e082a1605d7dd7da01c3f'
BLUEPRINT = '/Game/CargoShip/BluePrints/BP_PointLight_Blueprint.BP_PointLight_Blueprint_C'
PROTECTED = {
    'Content/BuildingLibrary/Ships/L_CargoShip_Complete.umap':
        'd2601cf5d7881481ba2be26d09af64b3776cefee75c1a1e54b49af6c74dab588',
    'Content/CargoShip/Maps/L_Showcase.umap':
        '18854441be398118a889dfdc258260bf99d2228e4373bd42dfd9ec8e8e264c62',
    'Content/BuildingLibrary/Assembled/Ships/BP_CargoShip_Complete.uasset':
        '2ebc5b2949a6f16fed538989513ec6038220ba6bf382a09757da965f5eb04af0',
    'Content/CargoShip/BluePrints/BP_PointLight_Blueprint.uasset':
        'aa4da1477096ea5cebe36a45e6d181f8d6c853b3464f49ac2a383176a7868df1',
}
# Four exterior broad keys keep shadows and cover the native hull sections.
# Their former 163.84m radii reached every station room. The two 60m-wide side
# emitters use 35m; the two 25m-wide aft emitters use 25m. Nothing is dimmed.
EXTERIOR_RADII = {'RectLight57': 3500., 'RectLight58': 3500.,
                  'RectLight59': 2500., 'RectLight60': 2500.}


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _state(component):
    transform = component.get_world_transform()
    return {'position': list(transform.translation.to_tuple()),
            'rotation': list(transform.rotation.to_tuple()),
            'scale': list(transform.scale3d.to_tuple()),
            'intensity': float(component.get_editor_property('intensity')),
            'color': list(component.get_editor_property('light_color').to_tuple()),
            'units': str(component.get_editor_property('intensity_units')),
            'radius': float(component.get_editor_property('attenuation_radius')),
            'cast_shadows': bool(component.get_editor_property('cast_shadows')),
            'visible': bool(component.get_editor_property('visible')),
            'hidden_in_game': bool(component.get_editor_property('hidden_in_game')),
            'affects_world': bool(component.get_editor_property('affects_world'))}


def apply(ctx):
    import unreal as u
    command = u.SystemLibrary.get_command_line().lower()
    if '-renderoffscreen' not in command and '-nullrhi' not in command:
        raise RuntimeError('Cargo lighting requires a dedicated headless editor')
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    if editor.get_game_world() or editor.get_editor_world().get_path_name().split('.')[0] != MAP:
        raise RuntimeError('Load only the private docked-cargo editor map before this pass')
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    map_file = root / ('Content/' + MAP[6:] + '.umap')
    inventory_file = root / '.agent/local/StationRefinement/LoadedLights2.json'
    if _sha(map_file) != MAP_SHA or _sha(inventory_file) != INVENTORY_SHA:
        raise RuntimeError('Private cargo map or inspected resident inventory changed')
    if any(_sha(root / path) != digest for path, digest in PROTECTED.items()):
        raise RuntimeError('Protected original cargo asset differs from the inspected source')
    inventory = json.loads(inventory_file.read_text(encoding='utf-8'))
    if not inventory['success'] or not inventory['cargo_coverage_complete']:
        raise RuntimeError('Resident cargo lighting evidence is incomplete')
    rows = [row for row in inventory['lights'] if row['cargo_derivative']]
    if len(rows) != 349:
        raise RuntimeError('Expected the inspected 349 resident cargo lights')
    actors = {actor.get_name(): actor for actor in ctx.actors}
    staged, snapshots, exterior, decorative = [], [], set(), set()
    for row in rows:
        actor_name = row['actor'].split(':PersistentLevel.', 1)[1]
        actor = actors.get(actor_name)
        if not actor or actor.get_actor_label() != row['label']:
            raise RuntimeError('Inspected cargo light actor missing: ' + actor_name)
        component_name = row['component'].rsplit('.', 1)[1]
        found = [c for c in actor.get_components_by_class(u.LightComponent) if c.get_name() == component_name]
        if len(found) != 1 or not isinstance(found[0], u.LocalLightComponent):
            raise RuntimeError('Inspected cargo local-light component changed: ' + row['component'])
        component = found[0]
        before = _state(component)
        # Inventory is the actual resident instance: berth yaw90 at (-3000,-8000,-484).
        # Invert that measured rigid transform to guard private-map coordinates.
        wx, wy, wz = row['world_position_cm']
        local = (wy + 8000., -wx - 3000., wz + 484.)
        if (math.dist(before['position'], local) > .1
                or before['intensity'] != row['intensity'] or before['color'] != row['light_color']
                or before['units'] != row['intensity_units'] or before['radius'] != row['attenuation_radius']
                or before['cast_shadows'] != row['cast_shadows']):
            raise RuntimeError('Native cargo light differs from resident evidence: ' + row['component'])
        snapshots.append((component, before))
        radius, shadows = before['radius'], before['cast_shadows']
        if actor.get_class().get_path_name() == BLUEPRINT:
            if (component_name not in ('PointLight', 'PointLight1') or radius != 1000.
                    or before['intensity'] != 120. or not shadows):
                raise RuntimeError('Paired decorative fixture interface changed')
            # These paired accents are 0.94–2.01m above the cargo deck. Keep
            # their full native intensity within 3m, with native room keys
            # supplying shadows instead of 126 overlapping accent casters.
            radius, shadows = 300., False
            decorative.add(actor_name)
        elif row['label'] in EXTERIOR_RADII:
            if not isinstance(component, u.RectLightComponent) or radius != 16384. or not shadows:
                raise RuntimeError('Inspected exterior broad key changed')
            radius = EXTERIOR_RADII[row['label']]
            exterior.add(row['label'])
        if radius != before['radius'] or shadows != before['cast_shadows']:
            staged.append((actor, component, before, radius, shadows))
    if len(decorative) != 63 or exterior != set(EXTERIOR_RADII) or len(staged) != 130:
        raise RuntimeError('Expected 63 paired accents plus exactly four exterior keys; no edits applied')

    changes = []
    for actor, component, before, radius, shadows in staged:
        component.set_attenuation_radius(radius)
        component.set_cast_shadows(shadows)
        expected = dict(before, radius=radius, cast_shadows=shadows)
        if _state(component) != expected:
            raise RuntimeError('Cargo light readback changed unrelated settings: ' + actor.get_name())
        changes.append({'actor': actor.get_name(), 'label': actor.get_actor_label(),
                        'component': component.get_name(), 'before': before, 'after': expected})
    changed = {component for _, component, _, _, _ in staged}
    if any(_state(component) != before for component, before in snapshots if component not in changed):
        raise RuntimeError('Untargeted cargo light changed')
    if _sha(map_file) != MAP_SHA or any(_sha(root / p) != digest for p, digest in PROTECTED.items()):
        raise RuntimeError('Cargo lighting helper unexpectedly saved or changed protected files')
    ctx.records.extend({'kind': 'private_cargo_light_localization', **row} for row in changes)
    return {'module': 'private_cargo_lighting', 'dirty_assets': [], 'changes': changes,
            'map_to_save': MAP, 'before_map_sha256': MAP_SHA, 'inventory_sha256': INVENTORY_SHA,
            'protected_source_sha256': PROTECTED, 'light_count': len(rows),
            'changed_components': len(changes), 'decorative_actor_count': len(decorative),
            'native_key_and_walkway_lights_unchanged': True,
            'intensities_colors_materials_geometry_and_transforms_unchanged': True,
            'limits': 'Radius/shadow localization only; not measured per-pixel overlap or performance.',
            'acceptance': 'Save private map, reload resident cargo, verify persisted Blueprint overrides, '
                          'then inspect cargo and wider rooms plus fresh VSM warning log.'}
