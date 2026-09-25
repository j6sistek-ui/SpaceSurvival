"""Reversible, unsaved comparison of native interior screen and metal finishes.

The source recipe is authoritative for each display slot. Screen gain scales all
Intensity EM channels together, retaining their ratios, textures and animation.
No generic per-channel clamps, global lighting changes, asset saves or map saves.
"""
import math

P3_BASE = '/Game/P1toP5_Bundle/P3_ComputerStation/Materials/Instances/Base/'
CLEAN_NAMES = {
    'MI_Metal01_OxydizedSteel1_Stains': 'MI_Metal01_OxydizedSteel',
    'MI_Metal01_OxydizedSteel1_Stains_Tilling2': 'MI_Metal01_OxydizedSteel',
    'MI_Metal02_AnodizedAluminium_Stains': 'MI_Metal02_AnodizedAluminium',
    'MI_Metal07_ParkerizedSteel_Stains': 'MI_Metal07_ParkerizedSteel',
    'MI_Metal09_Silver_Stains': 'MI_Metal09_Silver',
}


def _world(api, allow_fresh=False):
    import unreal as u
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    package = world.get_path_name().split('.')[0]
    target = '/Game/OutpostSandbox/L_AsteroidOutpost'
    fresh = allow_fresh and package.startswith('/Temp/Untitled') and api.get('TARGET') == target
    if package != target and not fresh:
        raise RuntimeError('Preview is restricted to the private outpost map')
    return u, api.get('EAS') or u.get_editor_subsystem(u.EditorActorSubsystem)


def _native_parent(u, material):
    visited = set()
    while material and isinstance(material, u.MaterialInstanceConstant):
        path = material.get_path_name()
        if path.startswith('/Game/P1toP5_Bundle/'):
            return material
        if path in visited:
            raise RuntimeError('Cyclic material parent chain: ' + path)
        visited.add(path)
        material = material.get_editor_property('parent')
    return None


def screen_sample(api, peak=None):
    """Restore original graphic slots or apply a single common gain per material.

    peak=None is the original native-source comparison. peak=40 is the bounded
    ratio-preserving candidate. Keep the returned handle until restore() is called.
    A caller may photograph both without saving or touching vendor assets.
    """
    import OutpostInteriorAssemblies
    u, eas = _world(api)
    if peak is not None and (not math.isfinite(peak) or peak <= 0):
        raise ValueError('Screen target peak must be finite and positive')
    edit = u.MaterialEditingLibrary
    rows = {row['name']: row for row in OutpostInteriorAssemblies.source_layout()
            if row['name'].startswith('OperationsNative/')}
    cache, undo, changes, comparisons = {}, [], [], []
    # Resolve every asset and scalar before changing any component.
    staged = []
    for actor in eas.get_all_level_actors():
        row = rows.get(actor.get_actor_label())
        if row is None:
            continue
        component = actor.static_mesh_component
        if not component.static_mesh or component.static_mesh.get_path_name() != row['asset']:
            raise RuntimeError('Source display mesh mismatch: ' + row['name'])
        for slot, path in enumerate(row['materials']):
            # Glass02 is the vendor's image/advertisement shader. Glass01 is its
            # illuminated glass/trim and must not be confused with the image.
            if '/MI_Glass02_' not in path:
                continue
            if path not in cache:
                original = u.load_asset(path)
                if not isinstance(original, u.MaterialInstanceConstant):
                    raise RuntimeError('Missing source graphic material: ' + path)
                channels = {str(name): edit.get_material_instance_scalar_parameter_value(original, name)
                            for name in edit.get_scalar_parameter_names(original)
                            if str(name).lower().startswith('intensity em')}
                if not channels:
                    raise RuntimeError('Graphic has no confirmed Intensity EM channels: ' + path)
                maximum = max(abs(value) for value in channels.values())
                if not math.isfinite(maximum) or maximum <= 0:
                    raise RuntimeError('Invalid source emission peak: ' + path)
                gain = 1.0 if peak is None else min(1.0, peak / maximum)
                replacement = original
                if peak is not None:
                    replacement = u.new_object(u.MaterialInstanceConstant)
                    edit.set_material_instance_parent(replacement, original)
                    for name, value in channels.items():
                        edit.set_material_instance_scalar_parameter_value(replacement, name, value * gain)
                cache[path] = replacement
                comparisons.append({'source': path, 'original_channels': channels,
                    'common_gain': gain,
                    'result_channels': {name: value * gain for name, value in channels.items()}})
            staged.append((component, slot, cache[path], actor.get_actor_label(), path))
    if not staged:
        raise RuntimeError('No exact native Operations graphics found')
    for component, slot, replacement, name, source in staged:
        previous = component.get_material(slot)
        undo.append((component, slot, previous))
        component.set_material(slot, replacement)
        changes.append({'actor': name, 'slot': slot, 'source': source,
                        'previous': previous.get_path_name() if previous else None})
    return {'undo': undo, 'keepalive': list(cache.values()), 'receipt': {
        'mode': 'native-original' if peak is None else 'common-channel-gain',
        'requested_peak': peak, 'slot_count': len(changes),
        'material_count': len(cache), 'materials': comparisons, 'changes': changes,
        'saved': False, 'scope': 'Operations source Glass02 graphics only',
        'acceptance': 'Pending matched-view visual comparison'}}


def clean_sample(api, *, allow_fresh=False, require_change=True):
    """Use owned clean metal counterparts in Engineering/Operations only.

    This deliberately compares named vendor finishes, retaining metallic texture
    identity and every screen/material slot. Goliath already uses its cleaned
    finish, so it is left unchanged. No generic damage-opacity guess is applied.
    """
    u, eas = _world(api, allow_fresh=allow_fresh)
    staged, undo, changes, materials = [], [], [], {}
    for actor in eas.get_all_level_actors():
        name = actor.get_actor_label()
        if not name.startswith(('Engineering/', 'Engineering_', 'OperationsNative/')):
            continue
        for component in actor.get_components_by_class(u.StaticMeshComponent):
            if not component.static_mesh:
                continue
            for slot, current in enumerate(component.get_materials()):
                native = _native_parent(u, current)
                if native is None:
                    continue
                path = native.get_path_name()
                basename = path.rsplit('.', 1)[-1]
                clean = CLEAN_NAMES.get(basename)
                if not clean or not path.startswith(P3_BASE):
                    continue
                target = P3_BASE + clean + '.' + clean
                if target not in materials:
                    materials[target] = u.load_asset(target)
                    if materials[target] is None:
                        raise RuntimeError('Missing exact owned finish: ' + target)
                staged.append((component, slot, current, materials[target], name, path, target))
    if not staged and require_change:
        raise RuntimeError('No named distressed P3 metal slots found')
    for component, slot, current, replacement, name, source, target in staged:
        undo.append((component, slot, current))
        component.set_material(slot, replacement)
        changes.append({'actor': name, 'slot': slot, 'source': source, 'replacement': target})
    return {'undo': undo, 'keepalive': list(materials.values()), 'receipt': {
        'mode': 'named-vendor-clean-metal', 'slot_count': len(changes),
        'material_count': len(materials), 'changes': changes, 'saved': False,
        'scope': 'Engineering and Operations native P3 metal slots; Goliath already cleaned',
        'acceptance': 'Pending matched-view visual comparison'}}


def apply_clean(api):
    """Idempotently author the approved named finishes into the private map.

    Caller owns the eventual map save. Only component material references change;
    no vendor material or mesh is edited and no asset is created or saved here.
    """
    handle = clean_sample(api, allow_fresh=True, require_change=False)
    receipt = handle['receipt']
    receipt['mode'] = 'authored-native-clean-metal'
    receipt['acceptance'] = 'Native comparison reviewed; final scene and owner acceptance pending'
    return receipt


def restore(api, handle):
    _world(api)
    for component, slot, previous in reversed(handle['undo']):
        component.set_material(slot, previous)
    handle['undo'].clear()
    handle['keepalive'].clear()
