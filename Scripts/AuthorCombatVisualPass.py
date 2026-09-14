"""Author private derivatives of inspected owner-licensed combat Niagara.

Prerequisites: stage the two unchanged vendor roots, run InspectCombatVisualAssets,
build SSVFXPresentation, and have the lead run this in the main Unreal project.
Only /Game/SpaceSurvival/Licensed/Combat is saved; source materials and systems
remain unchanged. The output still requires normal-speed rendered validation.
"""
import hashlib
import json
from pathlib import Path

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
BASE = '/Game/SpaceSurvival/Licensed/Combat'
WEAPONS = '/Game/Sci_Fi_Weapons_VFX_AIO/VFX/'
PYRO = '/Game/PyroVFX/Niagara_FX/Explosions/'
CYAN = (.08, .9, 2.2, 1.)
AMBER = (2.4, .58, .055, 1.)
RED = (2.5, .045, .012, 1.)
VIOLET = (.42, .14, 1.3, 1.)
# name, source, emissive tint, local particles, transform scale, seconds, cap
PLAN = [
    ('RapidBolt', WEAPONS+'NS_Gun_Beam_2', CYAN, True, (.28, .28, .28), 6., 16),
    ('CannonBolt', WEAPONS+'NS_Gun_Beam_4', AMBER, True, (.5, .5, .5), 6., 8),
    ('EnemyBolt', WEAPONS+'NS_Gun_Beam_2', RED, True, (.34, .34, .34), 6., 16),
    ('RapidMuzzle', WEAPONS+'NS_Gun_Start_Poin_1', CYAN, True, (.25, .25, .25), .055, 4),
    ('CannonMuzzle', WEAPONS+'NS_Gun_Start_Poin_2', AMBER, True, (.45, .45, .45), .10, 4),
    ('EnemyMuzzle', WEAPONS+'NS_Gun_Start_Poin_1', RED, True, (.30, .30, .30), .10, 6),
    ('RapidImpact', WEAPONS+'NS_Simple_Core_Impact_1', CYAN, True, (.65, .65, .65), .25, 12),
    ('CannonImpact', WEAPONS+'NS_Simple_Impact_2', AMBER, True, (.60, .60, .60), .6, 6),
    ('EnemyImpact', WEAPONS+'NS_Simple_Core_Impact_1', RED, True, (.8, .8, .8), .35, 6),
    ('EnemyExplosion', PYRO+'NS_General_S_Ex_01', None, False, (1., 1., 1.), 3.2, 4),
    ('WormholeMouth', WEAPONS+'NS_Anomal_Hole', VIOLET, True, (2.8, 2.8, 2.8), 8., 1),
]


def duplicate(source, target):
    lib = u.EditorAssetLibrary
    obj = lib.load_asset(target) if lib.does_asset_exist(target) else lib.duplicate_asset(source, target)
    assert obj is not None, f'Failed to duplicate {source}'
    assert obj.get_path_name().startswith(BASE+'/'), 'Refuse writes outside private combat content'
    return obj


def recolor_material(source, name, tint, saved):
    lib = u.EditorAssetLibrary
    edit = u.MaterialEditingLibrary
    # Material instances need their original overrides. Pautinka's inspected
    # sprite/ribbon renderers use master materials; fail rather than flatten a graph.
    assert isinstance(source, u.Material), f'Uninspected material type: {source.get_path_name()}'
    if edit.get_material_property_input_node(source, u.MaterialProperty.MP_EMISSIVE_COLOR) is None:
        # The anomaly's refraction-only layer has no light/color output. Preserve
        # that original graph rather than manufacture an emissive surface.
        return source
    material = duplicate(source.get_path_name(), BASE+'/M_'+name)
    if lib.get_metadata_tag(material, 'SSCombatTintVersion') != '1':
        previous = edit.get_material_property_input_node(material, u.MaterialProperty.MP_EMISSIVE_COLOR)
        assert previous, f'No emissive output: {source.get_path_name()}'
        desaturate = edit.create_material_expression(material, u.MaterialExpressionDesaturation, 1600, 0)
        color = edit.create_material_expression(material, u.MaterialExpressionVectorParameter, 1600, 200)
        color.set_editor_property('parameter_name', 'CombatTint')
        color.set_editor_property('default_value', u.LinearColor(*tint))
        multiply = edit.create_material_expression(material, u.MaterialExpressionMultiply, 1850, 0)
        assert edit.connect_material_expressions(previous, '', desaturate,
            edit.get_material_expression_input_names(desaturate)[0])
        assert edit.connect_material_expressions(desaturate, '', multiply, 'A')
        assert edit.connect_material_expressions(color, '', multiply, 'B')
        assert edit.connect_material_property(multiply, '', u.MaterialProperty.MP_EMISSIVE_COLOR)
        lib.set_metadata_tag(material, 'SSCombatTintVersion', '1')
        edit.recompile_material(material)
    saved.append(material)
    return material


def native_row(system):
    return json.loads(u.SSVFXPresentationLibrary.describe_system(system))


def main():
    assert hasattr(u, 'SSVFXPresentationLibrary'), 'Build the Editor target before authoring combat data'
    receipt_path = ROOT/'Artifacts/VisualEnhancement/CombatAssetInspection.json'
    inspected = {r['path']: r for r in json.loads(receipt_path.read_text(encoding='utf-8'))['assets']}
    for _, source, *_ in PLAN:
        assert inspected.get(source, {}).get('loaded'), f'Inspect {source} first'
        assert not any('/Modules/Collision/' in dep for dep in inspected[source]['dependencies']), source
    lib = u.EditorAssetLibrary
    lib.make_directory(BASE)
    saved = []
    definitions = []
    report = {'status': 'AUTHORED_REQUIRES_RENDERED_REVIEW', 'effects': [],
              'inspection_sha256': hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
              'maximum_active': 48, 'maximum_distance_cm': 22000,
              'vendor_writes': False, 'gameplay_changes': False}
    for name, source, tint, local, scale, lifetime, cap in PLAN:
        system = duplicate(source, BASE+'/NS_'+name)
        # Source example scalability is not the game's combat budget. The native
        # subsystem admits the actual world position and enforces explicit caps.
        system.set_editor_property('effect_type', None)
        assert u.SSVFXPresentationLibrary.prepare_private_system(system, local), source
        materials = {}
        if tint:
            renderers = []
            for obj in u.ObjectIterator(u.Object):
                try:
                    path = obj.get_path_name()
                    if not path.startswith(system.get_path_name()+':'):
                        continue
                    obj_class = obj.get_class()
                    if obj_class is None:
                        continue
                    cls = obj_class.get_name()
                except TypeError:
                    continue
                if cls in ('NiagaraSpriteRendererProperties', 'NiagaraRibbonRendererProperties'):
                    renderers.append(obj)
            # Capture owned renderers before material creation or recompilation
            # mutates Unreal's global object array.
            for obj in renderers:
                original = obj.get_editor_property('material')
                if original is None:
                    continue
                # A repeat authoring run keeps its existing private material.
                if original.get_path_name().startswith(BASE+'/'):
                    continue
                key = original.get_path_name()
                if key not in materials:
                    suffix = hashlib.sha256(key.encode()).hexdigest()[:8]
                    materials[key] = recolor_material(original, name+'_'+suffix, tint, saved)
                obj.set_editor_property('material', materials[key])
        # Final compile includes renderer-material substitutions as well as local space.
        assert u.SSVFXPresentationLibrary.prepare_private_system(system, local)
        row = u.SSCombatVFXDefinition()
        row.set_editor_property('kind', getattr(u.SSCombatVFX, ''.join(
            ('_'+char if char.isupper() and i else char) for i, char in enumerate(name)).upper()))
        row.set_editor_property('system', system)
        row.set_editor_property('scale', u.Vector(*scale))
        row.set_editor_property('maximum_seconds', lifetime)
        row.set_editor_property('active_limit', cap)
        row.set_editor_property('bounds_radius', 3000. if name in ('EnemyExplosion', 'WormholeMouth') else 1500.)
        audit = native_row(system)
        if name == 'EnemyExplosion':
            parameters = {p['name']: p for p in audit['parameters']}
            assert 'User.scale' in parameters, 'Sidearm scale name must be verified at runtime'
            assert parameters['User.scale']['type'] in ('float', 'NiagaraFloat'), parameters['User.scale']
            row.set_editor_property('particle_scale_parameter', 'User.scale')
            row.set_editor_property('particle_scale', .7)
        definitions.append(row)
        saved.append(system)
        report['effects'].append({'kind': name, 'source': source, 'system': system.get_path_name(),
            'transform_scale': scale, 'maximum_seconds': lifetime, 'active_limit': cap,
            'native_audit': audit})
    path = BASE+'/DA_CombatVisuals'
    data = lib.load_asset(path) if lib.does_asset_exist(path) else None
    if data is None:
        cls = u.load_class(None, '/Script/SpaceSurvival.SSCombatVFXData')
        factory = u.DataAssetFactory()
        factory.set_editor_property('data_asset_class', cls)
        data = u.AssetToolsHelpers.get_asset_tools().create_asset('DA_CombatVisuals', BASE, cls, factory)
    assert data is not None
    data.set_editor_property('effects', definitions)
    data.set_editor_property('maximum_active', 48)
    data.set_editor_property('maximum_distance', 22000.)
    saved.append(data)
    for asset in saved:
        assert lib.save_loaded_asset(asset, only_if_is_dirty=False), asset.get_path_name()
    assert len(data.get_editor_property('effects')) == len(PLAN)
    (ROOT/'Artifacts/VisualEnhancement/CombatAuthor.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    u.log('COMBAT_VISUAL_PASS_AUTHORED')


if __name__ == '__main__':
    main()
