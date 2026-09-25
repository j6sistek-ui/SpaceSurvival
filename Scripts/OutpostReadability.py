"""Private world-space text gain for the outpost's fixed-exposure review scene.

Source plan: duplicate Engine UnlitText with its font/alpha graph intact, append
one Multiply and an adjustable OutpostTextGain scalar to Emissive only. The two
observation signs retain their one-sided rendering. No font, color, placement,
HUD, exposure, source asset or gameplay-map changes. Caller owns map save/render.

UE5.8 MaterialEditingLibrary.h supplies get_material_property_input_node,
get_material_property_input_node_output_name, get_material_expressions and
get_inputs_for_material_expression; no material editor window is required.

Focused proof: python Tests/TestOutpostReadability.py checks retained font/alpha
links and source/unowned text, one-sided signs, non-stacking repeated gain,
wrong-map/unknown-material rejection and corrupted-alpha rejection. These are
offline API doubles; native shader compilation and appearance remain pending.
"""
import hashlib
import json
import math
from pathlib import Path

MAP = '/Game/OutpostSandbox/L_AsteroidOutpost'
SOURCE = '/Engine/EngineMaterials/UnlitText'
ONE_SIDED_SOURCE = '/Game/OutpostSandbox/Materials/M_ObservationTextOneSided'
TARGET = '/Game/OutpostSandbox/Materials/M_OutpostReadableText'
ONE_SIDED_TARGET = TARGET + 'OneSided'
PARAMETER = 'OutpostTextGain'
MULTIPLY_MARKER = 'OutpostReadability:EmissiveMultiply:v1'
GAIN_MARKER = 'OutpostReadability:Gain:v1'


def _path(asset):
    return asset.get_path_name().split('.')[0] if asset else None


def _node_key(node):
    return (node.get_name(), node.get_class().get_name()) if node else None


def _link(edit, material, prop):
    node = edit.get_material_property_input_node(material, prop)
    return (_node_key(node),
            edit.get_material_property_input_node_output_name(material, prop) if node else '')


def _graph(edit, material, excluded=()):
    """Original expression identities and connections, excluding only our nodes."""
    return sorted((_node_key(node), tuple(_node_key(child) for child in
                   edit.get_inputs_for_material_expression(material, node)))
                  for node in edit.get_material_expressions(material) if node not in excluded)


def _prepare(api, source, one_sided, gain):
    u, lib, edit = api['u'], api['LIB'], api['EDIT']
    target = ONE_SIDED_TARGET if one_sided else TARGET
    material = api['load'](target) if lib.does_asset_exist(target) else lib.duplicate_asset(SOURCE, target)
    if not isinstance(material, u.Material):
        raise RuntimeError('Readable text requires a private Material: ' + target)
    emissive = u.MaterialProperty.MP_EMISSIVE_COLOR
    alpha_props = (u.MaterialProperty.MP_OPACITY, u.MaterialProperty.MP_OPACITY_MASK)
    expressions = list(edit.get_material_expressions(material))
    multipliers = [n for n in expressions if str(n.get_editor_property('desc')) == MULTIPLY_MARKER]
    gains = [n for n in expressions if str(n.get_editor_property('desc')) == GAIN_MARKER]
    if bool(multipliers) != bool(gains) or len(multipliers) > 1 or len(gains) > 1:
        raise RuntimeError('Readable text has a partial or duplicated gain graph: ' + target)
    excluded = tuple(multipliers + gains)
    source_graph = _graph(edit, source)
    if _graph(edit, material, excluded) != source_graph:
        raise RuntimeError('Private text no longer preserves the source font graph: ' + target)
    for prop in alpha_props:
        if _link(edit, material, prop) != _link(edit, source, prop):
            raise RuntimeError('Private text alpha graph differs from Engine UnlitText')
    for prop in ('blend_mode', 'shading_model', 'opacity_mask_clip_value'):
        if material.get_editor_property(prop) != source.get_editor_property(prop):
            raise RuntimeError('Private text rendering property changed: ' + prop)
    source_emissive = _link(edit, source, emissive)
    if source_emissive[0] is None:
        raise RuntimeError('Engine UnlitText has no direct emissive input')
    changed, added = False, not multipliers
    if added:
        if _link(edit, material, emissive) != source_emissive:
            raise RuntimeError('Private text has an unrecognized emissive override')
        original = edit.get_material_property_input_node(material, emissive)
        output = edit.get_material_property_input_node_output_name(material, emissive)
        multiplier = edit.create_material_expression(material, u.MaterialExpressionMultiply, 240, 0)
        parameter = edit.create_material_expression(material, u.MaterialExpressionScalarParameter, 0, 160)
        multiplier.set_editor_property('desc', MULTIPLY_MARKER)
        parameter.set_editor_property('desc', GAIN_MARKER)
        parameter.set_editor_property('parameter_name', PARAMETER)
        parameter.set_editor_property('slider_min', 1.)
        parameter.set_editor_property('slider_max', 8.)
        if not (edit.connect_material_expressions(original, output, multiplier, 'A')
                and edit.connect_material_expressions(parameter, '', multiplier, 'B')
                and edit.connect_material_property(multiplier, '', emissive)):
            raise RuntimeError('Could not connect private text emissive gain')
        changed = True
    else:
        multiplier, parameter = multipliers[0], gains[0]
        if (not isinstance(multiplier, u.MaterialExpressionMultiply)
                or not isinstance(parameter, u.MaterialExpressionScalarParameter)
                or str(parameter.get_editor_property('parameter_name')) != PARAMETER
                or edit.get_material_property_input_node(material, emissive) != multiplier):
            raise RuntimeError('Readable text gain graph has an unexpected identity')
    inputs = list(edit.get_inputs_for_material_expression(material, multiplier))
    if len(inputs) != 2 or _node_key(inputs[0]) != source_emissive[0] or inputs[1] != parameter:
        raise RuntimeError('Readable text must apply one gain to the original emissive input')
    if abs(float(parameter.get_editor_property('default_value')) - gain) > 1e-6:
        parameter.set_editor_property('default_value', gain)
        changed = True
    sided = False if one_sided else source.get_editor_property('two_sided')
    if material.get_editor_property('two_sided') != sided:
        material.set_editor_property('two_sided', sided)
        changed = True
    # Adding the gain must leave every original node and alpha connection intact.
    if _graph(edit, material, (multiplier, parameter)) != source_graph:
        raise RuntimeError('Original text graph changed while appending emissive gain')
    for prop in alpha_props:
        if _link(edit, material, prop) != _link(edit, source, prop):
            raise RuntimeError('Text alpha connection changed during gain setup')
    if changed:
        edit.recompile_material(material)
    if not lib.save_loaded_asset(material):
        raise RuntimeError('Could not save private readable text material')
    return material, {'material': target, 'gain': gain, 'one_sided': one_sided,
                      'added_gain_nodes': 2 if added else 0, 'changed': changed,
                      'original_graph_preserved': True, 'alpha_preserved': True}


def apply(api, gain=4.):
    """Apply to tagged authored TextRenderActors only; no level save or UE launch.

    gain is an artist-facing source default (1..8); repeated runs reuse exactly
    one multiplier per private material and update the scalar without stacking.
    A material instance may also expose OutpostTextGain for later tuning.
    """
    gain = float(gain)
    if not math.isfinite(gain) or not 1. <= gain <= 8.:
        raise ValueError('Outpost text gain must be finite and between 1 and 8')
    u, eas, lib = api['u'], api['EAS'], api['LIB']
    package = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world().get_path_name().split('.')[0]
    fresh = package.startswith('/Temp/Untitled') and api.get('TARGET') == MAP
    if package != MAP and not fresh:
        raise RuntimeError('Readable text is restricted to the private outpost')
    staged = []
    recognized = {SOURCE: False, TARGET: False, ONE_SIDED_SOURCE: True, ONE_SIDED_TARGET: True}
    for actor in eas.get_all_level_actors():
        if not isinstance(actor, u.TextRenderActor) or 'OutpostAuthored' not in map(str, actor.tags):
            continue
        component = actor.get_component_by_class(u.TextRenderComponent)
        material = component.get_editor_property('text_material') if component else None
        if _path(material) not in recognized:
            raise RuntimeError('Unrecognized authored text material on ' + actor.get_actor_label())
        staged.append((actor, component, material, recognized[_path(material)]))
    if not staged:
        raise RuntimeError('No authored outpost TextRenderActors found')
    source_file = Path(u.Paths.convert_relative_path_to_full(u.Paths.engine_content_dir())) / 'EngineMaterials/UnlitText.uasset'
    before = hashlib.sha256(source_file.read_bytes()).hexdigest()
    source = api['load'](SOURCE)
    if not isinstance(source, u.Material):
        raise RuntimeError('Engine UnlitText is not a material')
    materials, receipts = {}, []
    # Resolve/create both variants before assigning any component.
    for one_sided in sorted({row[3] for row in staged}):
        material, receipt = _prepare(api, source, one_sided, gain)
        materials[one_sided] = material
        receipts.append(receipt)
    after = hashlib.sha256(source_file.read_bytes()).hexdigest()
    if before != after:
        raise RuntimeError('Engine UnlitText source changed on disk')
    assignments = []
    for actor, component, previous, one_sided in staged:
        replacement = materials[one_sided]
        if previous != replacement:
            component.set_text_material(replacement)
            assignments.append(actor.get_actor_label())
    report = {'gain': gain, 'text_actor_count': len(staged), 'assigned_count': len(assignments),
              'assigned_labels': assignments, 'materials': receipts,
              'engine_source_sha256': before, 'engine_source_unchanged': True,
              'scope': 'OutpostAuthored TextRenderActors only; no HUD/UI/font/color/transform changes',
              'map_saved': False, 'validation': 'Source graph guards; native visual review pending'}
    (Path(api['OUT']) / 'text-readability.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report
