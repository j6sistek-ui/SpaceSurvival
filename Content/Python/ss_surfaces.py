"""Resolve portable simple surfaces into private, content-addressed Unreal materials.

Never edits a source material or a mesh's default slots. Call resolve_rows before applying a recipe.
Only constant PBR values are supported; Blender graphs are not translated.
"""
import copy
import hashlib
import json
import math

import unreal as u

ROOT = '/Game/SpaceSurvival/Licensed/BlenderSurfaces'
FIELDS = {'base_color', 'metallic', 'roughness', 'opacity', 'transmission', 'ior'}


def checked(values):
    if not isinstance(values, dict) or set(values) != FIELDS:
        raise ValueError('Surface must contain only base_color, metallic, roughness, opacity, transmission and ior')
    color = values['base_color']
    if not isinstance(color, list) or len(color) != 3:
        raise ValueError('Surface color must have three channels')
    out = {k: [float(v) for v in color] if k == 'base_color' else float(v) for k, v in values.items()}
    for key, value in out.items():
        for number in value if isinstance(value, list) else [value]:
            high = 4.0 if key == 'ior' else 1.0
            low = 1.0 if key == 'ior' else 0.0
            if not math.isfinite(number) or not low <= number <= high:
                raise ValueError(f'Surface {key} must be within {low}..{high}')
    return out


def material_for(values):
    values = checked(values)
    encoded = json.dumps(values, sort_keys=True, separators=(',', ':'))
    name = 'M_SS_' + hashlib.sha256(('v1:' + encoded).encode()).hexdigest()[:24]
    path = ROOT + '/' + name
    lib = u.EditorAssetLibrary
    if lib.does_asset_exist(path):
        mat = lib.load_asset(path)
        if not isinstance(mat, u.Material) or lib.get_metadata_tag(mat, 'SSSurface') != encoded:
            raise RuntimeError(f'Refusing to replace an unrelated or incomplete asset: {path}')
        return path
    mat = u.AssetToolsHelpers.get_asset_tools().create_asset(name, ROOT, u.Material, u.MaterialFactoryNew())
    if not mat:
        raise RuntimeError(f'Could not create {path}')
    edit = u.MaterialEditingLibrary
    translucent = values['opacity'] < 1.0 or values['transmission'] > 0.0
    if translucent:
        mat.set_editor_property('blend_mode', u.BlendMode.BLEND_TRANSLUCENT)
        mat.set_editor_property('translucency_lighting_mode', u.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
    mat.set_editor_property('two_sided', True)
    color = edit.create_material_expression(mat, u.MaterialExpressionConstant3Vector, -400, 0)
    color.set_editor_property('constant', u.LinearColor(*values['base_color'], 1.0))
    edit.connect_material_property(color, '', u.MaterialProperty.MP_BASE_COLOR)
    props = [('metallic', u.MaterialProperty.MP_METALLIC), ('roughness', u.MaterialProperty.MP_ROUGHNESS)]
    if translucent:
        props += [('opacity', u.MaterialProperty.MP_OPACITY), ('ior', u.MaterialProperty.MP_REFRACTION)]
    for index, (key, prop) in enumerate(props):
        node = edit.create_material_expression(mat, u.MaterialExpressionConstant, -400, (index + 1) * 100)
        value = min(values['opacity'], 1.0 - 0.85 * values['transmission']) if key == 'opacity' else values[key]
        node.set_editor_property('r', value)
        edit.connect_material_property(node, '', prop)
    edit.recompile_material(mat)
    lib.set_metadata_tag(mat, 'SSSurface', encoded)
    if not lib.save_loaded_asset(mat):
        raise RuntimeError(f'Could not save {path}')
    return path


def resolve_rows(rows):
    """Preflight all overrides before creating any asset, then return a copy with material paths."""
    result = copy.deepcopy(rows)
    plans = []
    for row in result:
        overrides = row.get('surface_overrides', {})
        if not isinstance(overrides, dict):
            raise ValueError('surface_overrides must be a slot-index dictionary')
        if not overrides:
            continue
        mesh = u.load_asset(row['asset'])
        if not isinstance(mesh, u.StaticMesh):
            raise ValueError(f'Surface target is not a static mesh: {row["asset"]}')
        count = len(mesh.get_editor_property('static_materials'))
        materials = list(row.get('materials') or [])
        if len(materials) > count:
            raise ValueError(f'Too many material slots: {row["asset"]}')
        materials.extend([''] * (count - len(materials)))
        for key, values in overrides.items():
            slot = int(key)
            if str(slot) != str(key) or not 0 <= slot < count:
                raise ValueError(f'Invalid material slot {key}: {row["asset"]}')
            plans.append((materials, slot, checked(values)))
        row['materials'] = materials
    for materials, slot, values in plans:
        materials[slot] = material_for(values)
    return result
