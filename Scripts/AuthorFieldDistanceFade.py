"""Private distance fades for streamed flight scenery; original meshes/materials remain intact.

Run without -SSAuthorFieldFade for an inventory-only dry run. The application backs
up the look asset and any existing private derivatives before saving changes.
"""
import hashlib
import json
import shutil
import uuid
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
BASE = '/Game/SpaceSurvival/Licensed/FieldFade'
LOOK = '/Game/SpaceSurvival/Licensed/Atmosphere/DA_DeepSpaceLook'
LIB = u.EditorAssetLibrary
EDIT = u.MaterialEditingLibrary
MASK_CLIP = 0.333
REQUIRED_USAGE = (u.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES, u.MaterialUsage.MATUSAGE_NANITE)
# UE5.8 MaterialTemplate.ush subtracts the clip value before
# BlueNoiseCommon.ush adds .83 * noise - .5. Do not dither this input again.
FADE_CODE = '''
float Coverage = saturate((Far-distance(Position,Eye))/max(1.0,Far-Near));
if (Coverage <= 0.0 || (UsesSourceMask > 0.5 && OriginalMask < SourceClip)) return 0.0;
if (Coverage >= 1.0) return 1.0;
return 0.003 + 0.83 * Coverage;
'''


def disk_path(asset):
    return ROOT / 'Content' / (asset.split('.')[0].removeprefix('/Game/') + '.uasset')


def source_mask_settings(source):
    """Resolve original instance overrides before replacing its blend/clip state."""
    if isinstance(source, u.MaterialInstanceConstant):
        blend, clip = source_mask_settings(source.get_editor_property('parent'))
        overrides = source.get_editor_property('base_property_overrides')
        if overrides.get_editor_property('override_blend_mode'):
            blend = overrides.get_editor_property('blend_mode')
        if overrides.get_editor_property('override_opacity_mask_clip_value'):
            clip = overrides.get_editor_property('opacity_mask_clip_value')
    else:
        blend = source.get_editor_property('blend_mode')
        clip = source.get_editor_property('opacity_mask_clip_value')
    assert blend in (u.BlendMode.BLEND_OPAQUE, u.BlendMode.BLEND_MASKED), source.get_path_name()
    return blend, float(clip)


def configure_instance(instance, source):
    blend, clip = source_mask_settings(source)
    overrides = instance.get_editor_property('base_property_overrides')
    overrides.set_editor_property('override_blend_mode', True)
    overrides.set_editor_property('blend_mode', u.BlendMode.BLEND_MASKED)
    overrides.set_editor_property('override_opacity_mask_clip_value', True)
    overrides.set_editor_property('opacity_mask_clip_value', MASK_CLIP)
    instance.set_editor_property('base_property_overrides', overrides)
    EDIT.set_material_instance_scalar_parameter_value(instance, 'SSSourceMaskClip', clip)
    EDIT.set_material_instance_scalar_parameter_value(
        instance, 'SSSourceUsesMask', float(blend == u.BlendMode.BLEND_MASKED))
    # UE5.8 permits per-instance usage overrides. A copied vendor override can
    # otherwise disable a permutation enabled on our private parent.
    for usage in REQUIRED_USAGE:
        EDIT.set_material_usage_override(instance, usage, True, True)
    EDIT.update_material_instance(instance)
    assert all(EDIT.has_material_usage(instance, usage) for usage in REQUIRED_USAGE)


def configure_master(result, source):
    # Recover the ORIGINAL mask from the untouched source graph, never the old
    # fade product. Duplicate_asset preserves expression object names.
    source_nodes = {node.get_name(): node for node in EDIT.get_material_expressions(source)}
    result_nodes = {node.get_name(): node for node in EDIT.get_material_expressions(result)}
    assert source_nodes.keys() <= result_nodes.keys(), 'Private graph lost original expressions'
    for name, node in result_nodes.items():
        if name not in source_nodes:
            EDIT.delete_material_expression(result, node)
    original_mask = EDIT.get_material_property_input_node(source, u.MaterialProperty.MP_OPACITY_MASK)
    mask_output = EDIT.get_material_property_input_node_output_name(source, u.MaterialProperty.MP_OPACITY_MASK)
    mask = result_nodes[original_mask.get_name()] if original_mask else None
    blend, clip = source_mask_settings(source)
    result.set_editor_property('blend_mode', u.BlendMode.BLEND_MASKED)
    result.set_editor_property('dither_opacity_mask', True)
    result.set_editor_property('opacity_mask_clip_value', MASK_CLIP)
    fade = EDIT.create_material_expression(result, u.MaterialExpressionCustom, 2400, 500)
    fade.set_editor_property('desc', 'SS distance fade native blue noise')
    fade.set_editor_property('description', 'SS distance fade native blue noise')
    fade.set_editor_property('output_type', u.CustomMaterialOutputType.CMOT_FLOAT1)
    inputs = []
    for name in ('Position', 'Eye', 'Near', 'Far', 'OriginalMask', 'SourceClip', 'UsesSourceMask'):
        pin = u.CustomInput()
        pin.set_editor_property('input_name', name)
        inputs.append(pin)
    fade.set_editor_property('inputs', inputs)
    fade.set_editor_property('code', FADE_CODE)
    position = EDIT.create_material_expression(result, u.MaterialExpressionWorldPosition, 2050, 400)
    eye = EDIT.create_material_expression(result, u.MaterialExpressionCameraPositionWS, 2050, 550)
    assert EDIT.connect_material_expressions(position, '', fade, 'Position')
    assert EDIT.connect_material_expressions(eye, '', fade, 'Eye')
    if mask is None:
        mask = EDIT.create_material_expression(result, u.MaterialExpressionConstant, 2050, 900)
        mask.set_editor_property('r', 1.0)
        mask_output = ''
    # OpacityMask implicitly takes the first component of a vector. Custom
    # inputs retain their type, so explicitly restore that scalar conversion.
    # The supplied masked POM root connects an RGB multiply to OpacityMask.
    scalar_mask = EDIT.create_material_expression(result, u.MaterialExpressionComponentMask, 2225, 900)
    scalar_mask.set_editor_property('desc', 'SS source opacity scalar')
    for channel in ('r', 'g', 'b', 'a'):
        scalar_mask.set_editor_property(channel, channel == 'r')
    # MaterialEditingLibrary maps an empty pin name directly to GetInput(0);
    # the graph shortens ComponentMask's "Input" label to an unnamed pin.
    assert EDIT.connect_material_expressions(mask, mask_output, scalar_mask, '')
    assert EDIT.connect_material_expressions(scalar_mask, '', fade, 'OriginalMask')
    assert [bool(scalar_mask.get_editor_property(channel)) for channel in ('r', 'g', 'b', 'a')] == [True, False, False, False]
    assert scalar_mask in EDIT.get_inputs_for_material_expression(result, fade)
    assert mask in EDIT.get_inputs_for_material_expression(result, scalar_mask)
    for index, (param, value, pin) in enumerate((
            ('SSFadeStart', 70000.0, 'Near'), ('SSFadeEnd', 95000.0, 'Far'),
            ('SSSourceMaskClip', clip, 'SourceClip'),
            ('SSSourceUsesMask', float(blend == u.BlendMode.BLEND_MASKED), 'UsesSourceMask'))):
        scalar = EDIT.create_material_expression(result, u.MaterialExpressionScalarParameter, 2050, 1050 + index * 160)
        scalar.set_editor_property('parameter_name', param)
        scalar.set_editor_property('default_value', value)
        assert EDIT.connect_material_expressions(scalar, '', fade, pin)
    assert EDIT.connect_material_property(fade, '', u.MaterialProperty.MP_OPACITY_MASK)
    assert EDIT.get_material_property_input_node(result, u.MaterialProperty.MP_OPACITY_MASK) == fade
    # Save the actual instancing/Nanite permutations, not transient editor auto
    # flags: -game and packaged runtime cannot repair a missing usage flag.
    for usage in REQUIRED_USAGE:
        EDIT.set_base_material_usage(result, usage, True)
    assert all(EDIT.has_material_usage(result, usage) for usage in REQUIRED_USAGE)
    errors = EDIT.recompile_material(result)
    assert not errors, 'Private material compilation failed: ' + repr(errors)


def main():
    apply = 'SSAuthorFieldFade' in u.SystemLibrary.get_command_line()
    out = ROOT / 'Artifacts/SurvivalQuality/FieldFade' / uuid.uuid4().hex
    out.mkdir(parents=True)
    look = u.load_asset(LOOK)
    assert look, 'Space look data missing'
    meshes = {}
    for path in LIB.list_assets('/Game/SpaceSurvival/Licensed/SolidScenery', recursive=True):
        mesh = u.load_asset(path)
        if isinstance(mesh, u.StaticMesh):
            meshes[mesh.get_path_name()] = mesh
    for recipe in look.get_editor_property('area_recipes'):
        for name in ('clutter', 'landmarks'):
            for row in recipe.get_editor_property(name):
                mesh = row.get_editor_property('mesh')
                if mesh:
                    meshes[mesh.get_path_name()] = mesh
    originals = {}
    for mesh in meshes.values():
        for slot in mesh.get_editor_property('static_materials'):
            mat = slot.get_editor_property('material_interface')
            if mat:
                originals[mat.get_path_name()] = mat
    before = {}
    copies = {}
    targets = []

    def preserve(path):
        file = disk_path(path)
        if file.exists():
            digest = hashlib.sha256(file.read_bytes()).hexdigest()
            before[path] = digest
            shutil.copy2(file, out / (digest[:12] + '-' + file.name))

    def derivative(source):
        key = source.get_path_name()
        if key in copies:
            return copies[key]
        name = source.get_name() + '_' + hashlib.sha256(key.encode()).hexdigest()[:10]
        target = BASE + '/' + name
        blend, clip = source_mask_settings(source)
        source_file = disk_path(key)
        source_hash = hashlib.sha256(source_file.read_bytes()).hexdigest()
        entry = {'source': key, 'target': target, 'source_masked': blend == u.BlendMode.BLEND_MASKED,
                 'source_clip': clip, 'private_clip': MASK_CLIP, 'source_sha256': source_hash}
        targets.append(entry)
        if isinstance(source, u.MaterialInstanceConstant):
            parent = derivative(source.get_editor_property('parent'))
        else:
            assert isinstance(source, u.Material), key
            assert not source.get_editor_property('use_material_attributes'), key
            assert source.get_editor_property('blend_mode') in (u.BlendMode.BLEND_OPAQUE, u.BlendMode.BLEND_MASKED), key
            assert not source.get_editor_property('dither_opacity_mask'), 'Already-dithered source: ' + key
            source_nodes = EDIT.get_material_expressions(source)
            for node in source_nodes:
                if isinstance(node, u.MaterialExpressionMaterialFunctionCall):
                    function = node.get_editor_property('material_function')
                    assert not function or function.get_name() != 'DitherTemporalAA', 'Source already dithers: ' + key
            if LIB.does_asset_exist(target):
                private_nodes = EDIT.get_material_expressions(LIB.load_asset(target))
                source_names = {node.get_name() for node in source_nodes}
                private_names = {node.get_name() for node in private_nodes}
                assert source_names <= private_names, 'Private graph lost original expressions: ' + target
                entry['private_fade_nodes_to_replace'] = sorted(private_names - source_names)
        if not apply:
            copies[key] = source
            return source
        preserve(target)
        result = LIB.load_asset(target) if LIB.does_asset_exist(target) else LIB.duplicate_asset(key, target)
        assert result, target
        if isinstance(result, u.MaterialInstanceConstant):
            EDIT.set_material_instance_parent(result, parent)
            configure_instance(result, source)
        else:
            configure_master(result, source)
        assert LIB.save_loaded_asset(result, False), target
        assert hashlib.sha256(source_file.read_bytes()).hexdigest() == source_hash, 'Original material changed'
        entry['source_hash_preserved'] = True
        entry['target_sha256'] = hashlib.sha256(disk_path(target).read_bytes()).hexdigest()
        copies[key] = result
        return result

    mapped = {}
    for source in originals.values():
        result = derivative(source)
        if apply and isinstance(source, u.Material):
            # Some vendor roots retain an opaque optimization after duplication.
            # An explicit instance blend override uses the supported authoring API
            # and supplies the correct masked shader permutation for direct slots.
            target = BASE + '/MI_' + result.get_name()
            preserve(target)
            instance = LIB.load_asset(target) if LIB.does_asset_exist(target) else u.AssetToolsHelpers.get_asset_tools().create_asset(
                target.rsplit('/', 1)[1], BASE, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
            assert instance
            EDIT.set_material_instance_parent(instance, result)
            configure_instance(instance, source)
            assert LIB.save_loaded_asset(instance, False)
            result = instance
        mapped[source] = result
    if apply:
        preserve(LOOK)
        look.set_editor_property('field_material_overrides', mapped)
        assert LIB.save_loaded_asset(look, False)
    report = {'status': 'AUTHORED_REQUIRES_RENDER' if apply else 'DRY_RUN_NO_ASSET_WRITES',
              'mesh_count': len(meshes), 'slot_material_count': len(originals), 'targets': targets,
              'backups': before, 'vendor_or_mesh_writes': False,
              'fade_start_cm': 70000, 'fade_end_cm': 95000, 'opacity_mask_clip': MASK_CLIP,
              'native_dither_opacity_mask': True, 'material_function_dither': False,
              'required_saved_usage': ['InstancedStaticMeshes', 'Nanite'],
              'cutout_rule': 'Original mask < original effective clip stays absent at every distance',
              'original_mask_scalar_coercion': 'ComponentMask R only, preserving OpacityMask vector-to-scalar conversion',
              'mask_code': FADE_CODE, 'requires_rendered_acceptance': True}
    (out / 'report.json').write_text(json.dumps(report, indent=2))
    u.log('FIELD_FADE_REPORT ' + str(out))


if __name__ == '__main__':
    main()
