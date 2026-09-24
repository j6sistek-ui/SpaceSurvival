"""Measured, narrowly scoped embedded-light normalization for the private outpost.

inventory(api) stays read-only. apply(api) requires the earlier native inventory
receipt, changes only exact vendor decorative roles, and records before/after.
Intensity, units, source Blueprints/materials and global settings stay unchanged.
"""
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

TARGET_MAP = '/Game/OutpostSandbox/L_AsteroidOutpost'
VENDOR = '/Game/P1toP5_Bundle/P5_FruitSeller/Blueprints/'
COSMETIC_RANGES = {
    'BP_ISM_Screen_V1_C': 300., 'BP_ISM_Screen_V2_C': 300.,
    'BP_ISM_Screen_V3_C': 300., 'BP_ISM_Screen_V4_C': 300.,
    'BP_ISM_AppleSign_V1_C': 300., 'BP_Mech2_SmartTray_C': 250.,
    'BP_ISM_FruitTree_V1_C': 350., 'BP_ISM_FruitTree_V2_C': 350.,
    'BP_ISM_FruitTree_V3_C': 350., 'BP_Mech4_FlyingDroid_C': 300.,
}

# Five measured native overhead fixtures. These are deliberately distinct from
# the six task fixtures owned by OutpostMarketPresentation.
KEEP_SHADOW_LABELS = {
    'MarketNative/NorthCommerce/BP_ISM_Light_V1',
    'MarketNative/NorthCommerce/BP_ISM_Light_V14',
    'MarketNative/SouthMachinery/BP_ISM_Light_V3',
    'MarketNative/SouthMachinery/BP_ISM_Light_V9',
    'MarketNative/SouthBotany/BP_ISM_Light_V14',
}


def _active(row):
    return row['visible'] and row['affects_world'] and row['intensity'] > 0


def overlap_summary(rows):
    """Conservative radius-sphere count, NOT the GPU VSM culled-light count.

    Rect/spot direction and occlusion are deliberately not approximated. Samples
    include actual fixture positions plus a250cm grid at human and canopy height.
    This locates suspicious volume overlap without claiming rendered causality.
    """
    active = [row for row in rows if _active(row) and row['casts_shadows']]
    points = [tuple(row['location']) for row in active]
    points += [(x, y, z) for x in range(-2250, 2501, 250)
               for y in range(-2500, 2501, 250) for z in (160, 350)]
    worst = []
    for point in points:
        covering = [row['id'] for row in active
                    if math.dist(point, row['location']) <= row['attenuation_radius_cm']]
        if covering:
            worst.append({'position': list(point), 'count': len(covering), 'light_ids': covering})
    worst.sort(key=lambda row: row['count'], reverse=True)
    return {'model': 'conservative attenuation spheres; not actual VSM per-pixel count',
            'sample_count': len(points), 'max_count': worst[0]['count'] if worst else 0,
            'worst_samples': worst[:8]}


def candidate_policy(rows):
    """Pure, unapplied proposal from measured native components.

    Decorative display/produce/drone fills become shadowless at250-350cm max.
    Five measured overhead lamps retain their existing shadows at650cm max.
    Never enable shadows, expand a small radius, or change intensity/units.
    UE5.8 RectLight maps5000 legacy unitless to about25.1lm, not5000lm; the
    apparent large numbers do not justify dimming or a direct numeric conversion.
    """
    keep = {row['id'] for row in rows if row['actor_label'] in KEEP_SHADOW_LABELS
            and row['class_name'] == 'BP_ISM_Light_V1_C'
            and row['actor_class'].startswith(VENDOR)
            and _active(row) and row['casts_shadows']}
    changes, predicted = [], []
    for row in rows:
        updated = dict(row)
        owned = row['actor_label'].startswith(('MarketNative/', 'Drones/', 'Welcome/'))
        if 'OutpostMarketTask' in row.get('component_tags', []):
            owned = False
        cap = None
        role = None
        shadow = row['casts_shadows']
        if row['actor_class'].startswith(VENDOR) and owned:
            if row['class_name'] in COSMETIC_RANGES:
                cap, shadow = COSMETIC_RANGES[row['class_name']], False
                role = 'cosmetic display, produce or drone fill'
            elif row['class_name'] == 'BP_ISM_Light_V1_C' and row['actor_label'].startswith('MarketNative/'):
                cap, shadow = 650., row['id'] in keep and row['casts_shadows']
                role = 'overhead physical fixture; one of five measured retained shadow sources'
        if cap is not None:
            radius = min(row['attenuation_radius_cm'], cap)
            updated.update(attenuation_radius_cm=radius, casts_shadows=shadow)
            if radius != row['attenuation_radius_cm'] or shadow != row['casts_shadows']:
                changes.append({'id': row['id'], 'actor_label': row['actor_label'],
                                'component': row['component'], 'role': role,
                                'before': {'attenuation_radius_cm': row['attenuation_radius_cm'],
                                           'casts_shadows': row['casts_shadows']},
                                'after': {'attenuation_radius_cm': radius, 'casts_shadows': shadow},
                                'intensity_unchanged': True})
        predicted.append(updated)
    return {'status': 'CANDIDATE_ONLY_NOT_APPLIED', 'changes': changes,
            'retained_market_shadow_light_ids': sorted(keep),
            'predicted_active_shadow_local_lights': sum(_active(row) and row['casts_shadows'] for row in predicted),
            'predicted_radius_overlap': overlap_summary(predicted),
            'source_assets_changed': False, 'global_settings_changed': False}


def _read_world(api):
    """Collect current reflected components without altering the world."""
    u, eas = api['u'], api['EAS']
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name().split('.')[0] != TARGET_MAP:
        raise RuntimeError('Local light audit is restricted to the private outpost')
    rows, components = [], {}
    for actor in eas.get_all_level_actors():
        for component in actor.get_components_by_class(u.LocalLightComponent):
            p = component.get_world_location()
            rotation = component.get_world_rotation()
            actor_class = actor.get_class().get_path_name()
            identity = actor.get_path_name() + ':' + component.get_name()
            components[identity] = component
            rows.append({'id': identity,
                'actor_label': actor.get_actor_label(), 'actor_class': actor_class,
                'class_name': actor_class.split('.')[-1], 'component': component.get_name(),
                'component_class': component.get_class().get_name(),
                'component_tags': [str(tag) for tag in component.get_editor_property('component_tags')],
                'location': [p.x, p.y, p.z],
                'rotation': [rotation.pitch, rotation.yaw, rotation.roll],
                'intensity': float(component.get_editor_property('intensity')),
                'intensity_units': str(component.get_editor_property('intensity_units')),
                'attenuation_radius_cm': float(component.get_editor_property('attenuation_radius')),
                'casts_shadows': bool(component.get_editor_property('cast_shadows')),
                'casts_dynamic_shadows': bool(component.get_editor_property('cast_dynamic_shadows')),
                'visible': bool(component.get_editor_property('visible')),
                'affects_world': bool(component.get_editor_property('affects_world')),
                'mobility': str(component.get_editor_property('mobility'))})
    rows.sort(key=lambda row: row['id'])
    return rows, components


def inventory(api):
    """Export actual editor-world local-light components; perform no mutations."""
    rows, _ = _read_world(api)
    receipt = {'date': datetime.now(timezone.utc).isoformat(), 'map': TARGET_MAP,
        'mode': 'READ_ONLY', 'local_light_components': len(rows),
        'active_shadow_local_lights': sum(_active(row) and row['casts_shadows'] for row in rows),
        'component_classes': dict(Counter(row['component_class'] for row in rows)),
        'lights': rows, 'radius_overlap': overlap_summary(rows),
        'candidate': candidate_policy(rows),
        'limits': 'Radius sphere overlap is conservative. Read the actual GPU warning and capture after any approved local change.'}
    destination = Path(api['OUT']) / 'local-light-inventory.json'
    destination.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    return receipt


def apply(api, prior=None):
    """Apply the measured local policy, retaining the original inventory receipt.

    Run after authored actors exist and BEFORE MarketPresentation task lights.
    Tagged task components remain untouched on subsequent calls. The caller
    owns saving the map and native render validation. No source assets are saved.
    """
    path = Path(api['OUT']) / 'local-light-inventory.json'
    if prior is None:
        prior = json.loads(path.read_text(encoding='utf-8'))
    elif isinstance(prior, (str, Path)):
        prior = json.loads(Path(prior).read_text(encoding='utf-8'))
    if prior.get('map') != TARGET_MAP or prior.get('mode') != 'READ_ONLY' or not prior.get('lights'):
        raise RuntimeError('A measured native outpost light inventory is required before applying')
    rows, components = _read_world(api)
    plan = candidate_policy(rows)
    measured = {(row['actor_label'], row['component']): row for row in prior['lights']}
    current = {row['id']: row for row in rows}
    for change in plan['changes']:
        row = current[change['id']]
        old = measured.get((row['actor_label'], row['component']))
        if old is None or old['actor_class'] != row['actor_class']:
            raise RuntimeError('Target was not present in the measured native inventory: ' + row['actor_label'])
    # Complete preflight before mutating any component. A missing overhead lamp
    # means the assembly changed and deserves inspection, not silent substitution.
    actual_labels = {row['actor_label'] for row in rows if row['class_name'] == 'BP_ISM_Light_V1_C'}
    if not KEEP_SHADOW_LABELS.issubset(actual_labels):
        raise RuntimeError('One of the five measured overhead fixtures is missing')
    for change in plan['changes']:
        component = components[change['id']]
        component.set_cast_shadows(change['after']['casts_shadows'])
        component.set_attenuation_radius(change['after']['attenuation_radius_cm'])
    after, _ = _read_world(api)
    resulting = {row['id']: row for row in after}
    targeted = {row['id']: row for row in plan['changes']}
    for before in rows:
        observed = resulting[before['id']]
        for key in ('intensity', 'intensity_units', 'location', 'rotation', 'visible', 'affects_world', 'mobility'):
            if before[key] != observed[key]:
                raise RuntimeError('Light normalization changed an unrelated property: ' + key)
        expected = targeted[before['id']]['after'] if before['id'] in targeted else before
        for key in ('attenuation_radius_cm', 'casts_shadows'):
            if observed[key] != expected[key]:
                raise RuntimeError('Local light normalization failed its component readback: ' + before['actor_label'])
    authored = [row for row in after if row['class_name'] == 'PointLight' and _active(row) and row['casts_shadows']]
    kept = [row for row in after if row['actor_label'] in KEEP_SHADOW_LABELS and row['casts_shadows']]
    receipt = {'date': datetime.now(timezone.utc).isoformat(), 'map': TARGET_MAP,
        'mode': 'APPLIED_TO_PRIVATE_MAP_COMPONENTS', 'measured_inventory_date': prior['date'],
        'local_light_components': len(after), 'changes': plan['changes'],
        'shadow_local_lights_before': sum(_active(row) and row['casts_shadows'] for row in rows),
        'shadow_local_lights_after': sum(_active(row) and row['casts_shadows'] for row in after),
        'retained_market_shadow_lights': len(kept),
        'preserved_authored_shadow_pools': len(authored),
        'before_radius_overlap': overlap_summary(rows), 'after_radius_overlap': overlap_summary(after),
        'intensity_and_units_preserved': True, 'source_assets_changed': False,
        'global_settings_changed': False, 'native_render_validation': 'PENDING', 'lights_after': after}
    (Path(api['OUT']) / 'local-light-normalization.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    return receipt
