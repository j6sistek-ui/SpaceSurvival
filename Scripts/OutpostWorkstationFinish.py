"""Remove verified damage overlays from the authored Goliath workstation only.

Native cleaned base textures, colors, animation and channel ratios remain intact.
The tested Access01 display receives one common 8x emissive gain. All writes are
private material children and exact recipe component slots; no vendor/map save.
"""
import hashlib
import json
import math
from pathlib import Path

TARGET = '/Game/OutpostSandbox/L_AsteroidOutpost'
ACTORS = 'Engineering/Primary workstation/'
NATIVE = '/Game/P1toP5_Bundle/P1_WorkStation/'
PRIVATE = '/Game/OutpostSandbox/Materials/MI_WorkstationFinish_'
ACCESS = NATIVE + 'Materials/Instances/MI_LargeScreen01_slot2_Access01.MI_LargeScreen01_slot2_Access01'
ACCESS_ACTOR = ACTORS + 'SM_GoliathLargeScreen01'
CHANNELS = ('Intensity EM1', 'Intensity EM2', 'Intensity EM3')


def _path(value):
    return value.get_path_name() if value else None


def _native(current, u):
    """Accept only our own documented wrappers, never an arbitrary artist edit."""
    seen = set()
    while isinstance(current, u.MaterialInstanceConstant):
        path = current.get_path_name()
        if path.startswith(NATIVE):
            return path
        if path in seen or not path.startswith((PRIVATE, '/Game/OutpostSandbox/Materials/MI_Balanced_')):
            break
        seen.add(path)
        current = current.get_editor_property('parent')
    raise RuntimeError('Unexpected workstation material lineage: ' + str(_path(current)))


def _parameters(edit, material):
    scalars = {str(n): float(edit.get_material_instance_scalar_parameter_value(material, n))
               for n in edit.get_scalar_parameter_names(material)}
    vectors = {}
    for name in edit.get_vector_parameter_names(material):
        color = edit.get_material_instance_vector_parameter_value(material, name)
        vectors[str(name)] = [float(color.r), float(color.g), float(color.b), float(color.a)]
    if not all(math.isfinite(v) for v in list(scalars.values()) + [v for c in vectors.values() for v in c]):
        raise RuntimeError('Nonfinite workstation material parameter')
    return {'scalars': scalars, 'vectors': vectors,
            'textures': {str(n): _path(edit.get_material_instance_texture_parameter_value(material, n))
                         for n in edit.get_texture_parameter_names(material)},
            'switches': {str(n): bool(edit.get_material_instance_static_switch_parameter_value(material, n))
                         for n in edit.get_static_switch_parameter_names(material)}}


def _eligibility(parameters):
    base = parameters['textures'].get('Albedo') or ''
    overlay = parameters['textures'].get('Albedo Cov1') or ''
    if parameters['switches'].get('Activate Cov1') is not True:
        return False, 'Cov1 absent or already disabled in native source'
    if not base.startswith(NATIVE + 'Textures/') or '/Cleaned/' not in base:
        return False, 'Native base Albedo is not a confirmed cleaned P1 texture'
    if not overlay.startswith(NATIVE + 'Textures/') or '/Damaged/' not in overlay:
        return False, 'Cov1 Albedo is not a confirmed damaged P1 texture; layer retained'
    return True, 'Cleaned P1 base with enabled damaged P1 Cov1 overlay'


def _verify_parameters(native, actual, scalars, switches, where):
    if native['textures'] != actual['textures'] or native['vectors'] != actual['vectors']:
        raise RuntimeError('Workstation texture/color inheritance changed: ' + where)
    expected_switches = dict(native['switches'], **switches)
    if actual['switches'] != expected_switches:
        raise RuntimeError('Workstation static-switch readback mismatch: ' + where)
    expected = dict(native['scalars'], **scalars)
    if actual['scalars'].keys() != expected.keys() or any(
            abs(actual['scalars'][n] - v) > max(1e-5, abs(v) * 1e-5) for n, v in expected.items()):
        raise RuntimeError('Workstation scalar/animation readback mismatch: ' + where)


def _pose(actor, component):
    def numeric(transform):
        location, rotation, scale = transform.translation, transform.rotation, transform.scale3d
        return ((float(location.x), float(location.y), float(location.z)),
                (float(rotation.x), float(rotation.y), float(rotation.z), float(rotation.w)),
                (float(scale.x), float(scale.y), float(scale.z)))
    return (numeric(actor.get_actor_transform()), numeric(component.get_relative_transform()),
            str(component.get_collision_enabled()), str(component.get_collision_profile_name()))


def apply(api):
    """Apply after OutpostWorkstation.build; caller owns map save and captures."""
    import unreal as u
    import OutpostWorkstation
    edit, lib, root = api['EDIT'], api['LIB'], Path(api['ROOT'])
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    package = world.get_path_name().split('.')[0]
    fresh = package.startswith('/Temp/Untitled') and api.get('TARGET') == TARGET
    if package != TARGET and not fresh:
        raise RuntimeError('Workstation finish is restricted to the private outpost')
    rows = {r['name']: r for r in OutpostWorkstation.layout(api['PLAN']['workstation'])
            if r['name'].startswith(ACTORS)}
    if len(rows) != 29:
        raise RuntimeError('Goliath source assembly changed; review the new recipe first')
    found = {}
    for actor in api['EAS'].get_all_level_actors():
        if actor.get_actor_label().startswith(ACTORS):
            found.setdefault(actor.get_actor_label(), []).append(actor)
    if set(found) != set(rows) or any(len(v) != 1 for v in found.values()):
        raise RuntimeError('Missing, duplicate or unreviewed primary-workstation actor')

    prepared, sources, decisions, hashes, poses = [], {}, [], {}, []

    def record_hash(material):
        visited = set()
        while material and _path(material).startswith(NATIVE):
            path = material.get_path_name()
            if path in visited:
                raise RuntimeError('Cyclic native material parent chain')
            visited.add(path)
            filename = root / ('Content/' + path.split('.')[0][len('/Game/'):] + '.uasset')
            if path not in hashes:
                hashes[path] = (filename, hashlib.sha256(filename.read_bytes()).hexdigest())
            material = material.get_editor_property('parent') if isinstance(material, u.MaterialInstanceConstant) else None

    # Resolve every source and current slot before any private asset mutation.
    for name, row in rows.items():
        actor = found[name][0]
        if 'OutpostAuthored' not in map(str, actor.tags):
            raise RuntimeError('Unowned primary-workstation actor: ' + name)
        components = actor.get_components_by_class(u.StaticMeshComponent)
        if len(components) != 1 or _path(components[0].static_mesh) != row['asset']:
            raise RuntimeError('Workstation source mesh mismatch: ' + name)
        component = components[0]
        if component.get_num_materials() != len(row['materials']):
            raise RuntimeError('Workstation source material-slot count changed: ' + name)
        poses.append((actor, component, _pose(actor, component)))
        for slot, path in enumerate(row['materials']):
            if not path.startswith(NATIVE + 'Materials/Instances/'):
                raise RuntimeError('Unreviewed workstation recipe material: ' + path)
            current = component.get_material(slot)
            if _native(current, u) != path:
                raise RuntimeError('Workstation slot differs from recipe source: ' + name)
            if path not in sources:
                source = api['load'](path)
                if not isinstance(source, u.MaterialInstanceConstant):
                    raise RuntimeError('Workstation source is not a native material instance')
                parameters = _parameters(edit, source)
                eligible, reason = _eligibility(parameters)
                record_hash(source)
                sources[path] = {'material': source, 'parameters': parameters,
                                 'eligible': eligible, 'reason': reason}
            source = sources[path]
            main_screen = name == ACCESS_ACTOR and slot == 1
            if main_screen and (path != ACCESS or not source['eligible']):
                raise RuntimeError('Access01 no longer matches the inspected cleaned/damaged-layer recipe')
            if path == ACCESS and not main_screen:
                raise RuntimeError('Access01 gain must remain restricted to the exact main-screen slot')
            decisions.append({'actor': name, 'slot': slot, 'source': path,
                              'before': _path(current), 'eligible': source['eligible'], 'reason': source['reason']})
            if source['eligible']:
                prepared.append((component, slot, path, decisions[-1], main_screen))
    if not any(row[-1] for row in prepared):
        raise RuntimeError('Confirmed Access01 slot was not found')

    replacements, material_receipts = {}, []
    for _, _, path, _, main_screen in prepared:
        if path in replacements:
            continue
        entry = sources[path]
        source, native = entry['material'], entry['parameters']
        scalars, switches = {}, {'Activate Cov1': False}
        if main_screen:
            expected = dict(zip(CHANNELS, (1., 1.5, 1.)))
            if any(n not in native['scalars'] or abs(native['scalars'][n] - v) > 1e-5
                   for n, v in expected.items()):
                raise RuntimeError('Access01 emission channels differ from the reviewed comparison')
            if any(native['switches'].get('Activate Emissive ' + str(i)) is not True for i in (1, 2, 3)):
                raise RuntimeError('Access01 native emissive activation changed')
            scalars = {n: native['scalars'][n] * 8. for n in CHANNELS}
        name = 'MI_WorkstationFinish_' + hashlib.sha1(path.encode()).hexdigest()[:12]
        dest = '/Game/OutpostSandbox/Materials/' + name
        exists = lib.does_asset_exist(dest)
        child = api['load'](dest) if exists else api['TOOLS'].create_asset(
            name, '/Game/OutpostSandbox/Materials', u.MaterialInstanceConstant,
            u.MaterialInstanceConstantFactoryNew())
        if not isinstance(child, u.MaterialInstanceConstant):
            raise RuntimeError('Private workstation finish path is not a material instance')
        if exists and child.get_editor_property('parent') != source:
            raise RuntimeError('Private workstation finish has an unexpected parent')
        if not exists:
            edit.set_material_instance_parent(child, source)
        before = _parameters(edit, child)
        # Detect foreign overrides before touching an existing private child.
        allowed_before_scalars = {n: before['scalars'][n] for n in scalars}
        allowed_before_switches = {'Activate Cov1': before['switches']['Activate Cov1']}
        _verify_parameters(native, before, allowed_before_scalars, allowed_before_switches, dest)
        edit.set_material_instance_static_switch_parameter_value(child, 'Activate Cov1', False)
        for parameter, value in scalars.items():
            # UE5.8 scalar setter returns false even after a successful write.
            edit.set_material_instance_scalar_parameter_value(child, parameter, value)
        edit.update_material_instance(child)
        after = _parameters(edit, child)
        _verify_parameters(native, after, scalars, switches, dest)
        replacements[path] = child
        material_receipts.append({'source': path, 'private': _path(child),
            'qualification': entry['reason'], 'source_parameters': native,
            'private_parameters': after, 'common_emission_gain': 8. if main_screen else 1.,
            'preserved_textures_colors_animation': True, 'readback_verified': True})

    # Save only verified private children. Native materials and the map are never saved here.
    for child in replacements.values():
        if not lib.save_loaded_asset(child):
            raise RuntimeError('Could not save private workstation finish: ' + _path(child))
    for component, slot, path, decision, _ in prepared:
        child = replacements[path]
        component.set_material(slot, child)
        if component.get_material(slot) != child:
            raise RuntimeError('Workstation component material assignment failed')
        decision['after'] = _path(child)
    for actor, component, before in poses:
        if _pose(actor, component) != before:
            raise RuntimeError('Workstation placement or collision changed during material-only pass')
    for path, (filename, digest) in hashes.items():
        if hashlib.sha256(filename.read_bytes()).hexdigest() != digest:
            raise RuntimeError('Vendor source material changed on disk: ' + path)
    receipt = {'map': TARGET, 'inspected_actors': len(rows), 'inspected_slots': len(decisions),
        'assigned_slots': len(prepared), 'private_materials': len(replacements),
        'decisions': decisions, 'materials': material_receipts,
        'native_source_hashes': {path: digest for path, (_, digest) in hashes.items()},
        'vendor_sources_unchanged': True, 'geometry_and_collision_unchanged': True,
        'scope': 'Exact29-part Goliath workstation; confirmed cleaned-base damaged-Cov1 slots only; '
                 '8x common emission gain on main Access01 slot1 only.',
        'validation': 'Source, parameter and slot readbacks; final saved appearance requires native capture.'}
    (Path(api['OUT']) / 'workstation-finish.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt
