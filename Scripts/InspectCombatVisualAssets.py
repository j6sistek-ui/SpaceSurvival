"""Read-only mounted Niagara inspection; the integration lead schedules Unreal.

Writes an ignored JSON receipt, never saves or simulates vendor content. Native
parameter names/types are included when SSVFXPresentation has been compiled.
"""
import json
from pathlib import Path

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
WEAPONS = '/Game/Sci_Fi_Weapons_VFX_AIO/VFX/'
PYRO = '/Game/PyroVFX/Niagara_FX/Explosions/'
NERVES = '/Game/NERVES/FX/'
PATHS = [WEAPONS + name for name in [
    'NS_Gun_Beam_1', 'NS_Gun_Beam_2', 'NS_Gun_Beam_3', 'NS_Gun_Beam_4',
    'NS_Gun_Start_Poin_1', 'NS_Gun_Start_Poin_2',
    'NS_Simple_Impact_1', 'NS_Simple_Impact_2',
    'NS_Simple_Core_Impact_1', 'NS_Anomal_Hole', 'NS_Lighting_Ball',
]] + [PYRO + name for name in ['NS_General_S_Ex_01', 'NS_General_S_Ex_02', 'NS_General_M_Ex_01']] + [
    NERVES + 'NS_ElectircBeams_Blue',
    WEAPONS + 'NS_Lightning_Damage_Land_Mid',
]


def prop(obj, name):
    try:
        value = obj.get_editor_property(name)
        if isinstance(value, u.Object):
            return value.get_path_name()
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)
    except Exception as exc:
        return {'unavailable': str(exc)}


def main():
    registry = u.AssetRegistryHelpers.get_asset_registry()
    registry.search_all_assets(True)
    report = {'engine': u.SystemLibrary.get_engine_version(),
              'status': 'READ_ONLY_REQUIRES_RENDERED_REVIEW', 'assets': []}
    options = u.AssetRegistryDependencyOptions(include_soft_package_references=True,
        include_hard_package_references=True, include_searchable_names=False,
        include_soft_management_references=False, include_hard_management_references=False)
    for path in PATHS:
        obj = u.load_asset(path)
        row = {'path': path, 'loaded': obj is not None}
        report['assets'].append(row)
        if obj is None:
            continue
        row['class'] = obj.get_class().get_name()
        row['properties'] = {key: prop(obj, key) for key in
            ['fixed_bounds', 'fixed_bounds_enabled', 'effect_type', 'warmup_time', 'warmup_tick_count']}
        row['dependencies'] = [str(x) for x in registry.get_dependencies(path, options)]
        row['owned_objects'] = []
        for nested in u.ObjectIterator(u.Object):
            try:
                if not nested.get_path_name().startswith(obj.get_path_name() + ':'):
                    continue
                obj_class = nested.get_class()
                if obj_class is None:
                    continue
                cls = obj_class.get_name()
                if cls.endswith('RendererProperties'):
                    row['owned_objects'].append({'path': nested.get_path_name(), 'class': cls,
                        'properties': {key: prop(nested, key) for key in
                            ['material', 'is_enabled', 'motion_vector_setting', 'sort_mode']}})
            except TypeError:
                continue
        if hasattr(u, 'SSVFXPresentationLibrary'):
            row['native_audit'] = json.loads(u.SSVFXPresentationLibrary.describe_system(obj))
    out = ROOT / 'Artifacts/VisualEnhancement'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'CombatAssetInspection.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    u.log('COMBAT_VISUAL_ASSETS_INSPECTED')


if __name__ == '__main__':
    main()
