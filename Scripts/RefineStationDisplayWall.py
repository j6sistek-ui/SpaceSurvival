"""Native blue graphic walls for the reviewed T and R rooms.

The lead invokes apply(ctx) inside the guarded owner-preview transaction and
saves its returned dirty_assets. This module never loads/saves a map or changes
vendor assets, exposure, bloom, lighting, furniture or the apartment. Native
frame/pane pairs receive the same planar fit; frame depth remains unchanged.
"""
import hashlib
from pathlib import Path

from OutpostGeometryUtils import mesh_union
from StationRefinementSupport import transform_record


P4 = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/'
MASTER = P4 + 'Materials/Masters/MM_MasterMaterial02_Translucent'
VARIANTS = P4 + 'Materials/Instances/Translucent/MI_DigitalGlass_Window400X200_'
PRIVATE = '/Game/OutpostSandbox/OwnerPreview/Materials/DisplayWall'
TAG = 'StationDisplayWall20261006'
BACKGROUND = (.12, .42, 1.1, 1.)


def _one(actors, label):
    rows = [actor for actor in actors if actor.get_actor_label() == label]
    if len(rows) != 1:
        raise RuntimeError('Expected one reviewed display actor: ' + label)
    return rows[0]


def _pose(actor):
    t = actor.get_actor_transform()
    return (tuple(t.translation.to_tuple()), tuple(t.rotation.to_tuple()), tuple(t.scale3d.to_tuple()))


def _file(root, asset):
    path = asset.split('.')[0]
    if not path.startswith('/Game/'):
        raise RuntimeError('Expected a project-owned source: ' + path)
    return root / ('Content/' + path[6:] + '.uasset')


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _native_graph(edit, master):
    """Verify the exact masking/pulse paths from ServiceMaterialProbe before editing a copy."""
    nodes = {node.get_name(): node for node in edit.get_material_expressions(master)}
    expected = {
        'MaterialExpressionLinearInterpolate_8': ('MaterialExpressionLinearInterpolate_6',
            'MaterialExpressionConstant_0', 'MaterialExpressionMultiply_0'),
        'MaterialExpressionMultiply_0': ('MaterialExpressionScalarParameter_4',
            'MaterialExpressionLinearInterpolate_31'),
        'MaterialExpressionLinearInterpolate_2': ('MaterialExpressionVectorParameter_16',
            'MaterialExpressionVectorParameter_15', 'MaterialExpressionSine_3'),
        'MaterialExpressionMultiply_33': ('MaterialExpressionStaticSwitch_24', 'MaterialExpressionMultiply_4'),
        'MaterialExpressionMultiply_4': ('MaterialExpressionStaticSwitch_24', 'MaterialExpressionLinearInterpolate_2')}
    for name, inputs in expected.items():
        if name not in nodes or tuple(n.get_name() for n in edit.get_inputs_for_material_expression(master, nodes[name]) if n) != inputs:
            raise RuntimeError('Inspected native display graph changed: ' + name)
    return {'verified_nodes': list(expected),
            'emission': 'Native mask squared times intensity and sine-interpolated color endpoints',
            'opacity': 'Opacity/Fresnel blend, then dusty roughness blend; both modulation coefficients become zero'}


def _master(ctx, u, dirty):
    edit = u.MaterialEditingLibrary
    source = ctx.asset(MASTER)
    if (not isinstance(source, u.Material) or source.get_editor_property('blend_mode') != u.BlendMode.BLEND_TRANSLUCENT or
            source.get_editor_property('use_material_attributes')):
        raise RuntimeError('Expected the inspected native translucent P4 master')
    evidence = _native_graph(edit, source)
    path = PRIVATE + '/M_NativeBlueDisplayWall_20261006'
    if u.EditorAssetLibrary.does_asset_exist(path):
        raise RuntimeError('Preserve existing private display master: ' + path)
    master = u.EditorAssetLibrary.duplicate_asset(MASTER, path)
    if not master:
        raise RuntimeError('Failed to copy native display master')
    dirty.append(master.get_path_name())
    original = edit.get_material_property_input_node(master, u.MaterialProperty.MP_EMISSIVE_COLOR)
    if not original or original.get_class().get_name() != 'MaterialExpressionAdd':
        raise RuntimeError('Native display emission root changed')
    background = edit.create_material_expression(master, u.MaterialExpressionVectorParameter, 700, 200)
    background.set_editor_property('parameter_name', 'SSDisplayBackground')
    background.set_editor_property('default_value', u.LinearColor(*BACKGROUND))
    add = edit.create_material_expression(master, u.MaterialExpressionAdd, 950, 0)
    if not (edit.connect_material_expressions(original, '', add, 'A') and
            edit.connect_material_expressions(background, '', add, 'B') and
            edit.connect_material_property(add, '', u.MaterialProperty.MP_EMISSIVE_COLOR)):
        raise RuntimeError('Could not preserve native emission plus its blue glass background')
    master.set_editor_property('shading_model', u.MaterialShadingModel.MSM_UNLIT)
    master.set_editor_property('two_sided', True)
    errors = edit.recompile_material(master)
    if errors:
        raise RuntimeError('Private display material failed compilation: ' + repr(list(errors)))
    evidence['private_master'] = master.get_path_name()
    evidence['background_linear_radiance'] = list(BACKGROUND)
    return master, evidence


def _material(ctx, u, master, variant, dirty):
    edit = u.MaterialEditingLibrary
    source = ctx.asset(VARIANTS + variant)
    if not isinstance(source, u.MaterialInstanceConstant) or source.get_editor_property('parent') != ctx.asset(MASTER):
        raise RuntimeError('Expected the inspected direct native variant: ' + variant)
    name = 'MI_BlueDisplayWall_' + variant + '_20261006'
    path = PRIVATE + '/' + name
    if u.EditorAssetLibrary.does_asset_exist(path):
        raise RuntimeError('Preserve existing private display variant: ' + path)
    material = u.AssetToolsHelpers.get_asset_tools().create_asset(
        name, PRIVATE, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
    if not material:
        raise RuntimeError('Could not create private native display variant')
    dirty.append(material.get_path_name())
    edit.set_material_instance_parent(material, master)
    # Copy effective values, including parameters inherited by the original MIC.
    # Reparenting alone would otherwise reset those values to the master defaults.
    scalars = {str(n): float(edit.get_material_instance_scalar_parameter_value(source, n))
               for n in edit.get_scalar_parameter_names(source)}
    vectors = {str(n): edit.get_material_instance_vector_parameter_value(source, n)
               for n in edit.get_vector_parameter_names(source)}
    textures = {str(n): edit.get_material_instance_texture_parameter_value(source, n)
                for n in edit.get_texture_parameter_names(source)}
    switches = {str(n): bool(edit.get_material_instance_static_switch_parameter_value(source, n))
                for n in edit.get_static_switch_parameter_names(source)}
    changed = {'Opacity': .9, 'Opacity_Lerp': 0., 'Height Roughness Mask': 0.,
               'Refraction': 1., 'Refraction_Lerp': 1., 'Normal Intensity': 0.,
               'Intensity EM1': 18. if variant == 'DigitalPanel' else 24.,
               'Intensity EM2': 10. if variant == 'DigitalPanel' else 3., 'Intensity EM3': 3.}
    if not set(changed) <= set(scalars):
        raise RuntimeError('Native display scalar interface changed')
    scalars.update(changed)
    for channel, color in ((1, (.32, .72, 1., 1.)), (2, (.62, .84, 1., 1.)), (3, (.24, .64, 1., 1.))):
        # Identical non-black endpoints retain all native UV/scroll functions
        # while removing whole-screen dark pulses, even at negative sine values.
        for endpoint in (1, 2):
            name = 'Color %d EM%d' % (endpoint, channel)
            if name not in vectors:
                raise RuntimeError('Native display color interface changed: ' + name)
            vectors[name] = u.LinearColor(*color)
    for name, value in scalars.items():
        edit.set_material_instance_scalar_parameter_value(material, name, value)
    for name, value in vectors.items():
        edit.set_material_instance_vector_parameter_value(material, name, value)
    for name, value in textures.items():
        if not value:
            raise RuntimeError('Native display lost a texture: ' + name)
        edit.set_material_instance_texture_parameter_value(material, name, value)
    for name, value in switches.items():
        edit.set_material_instance_static_switch_parameter_value(material, name, value)
    edit.set_material_instance_vector_parameter_value(material, 'SSDisplayBackground', u.LinearColor(*BACKGROUND))
    edit.update_material_instance(material)
    if (material.get_editor_property('parent') != master or
            master.get_editor_property('blend_mode') != u.BlendMode.BLEND_TRANSLUCENT):
        raise RuntimeError('Private display lost its native translucent parent')
    actual_background = edit.get_material_instance_vector_parameter_value(material, 'SSDisplayBackground')
    if any(abs(a - b) > .0001 for a, b in zip(actual_background.to_tuple(), BACKGROUND)):
        raise RuntimeError('Private blue glass background readback differs')
    for name, value in scalars.items():
        if abs(edit.get_material_instance_scalar_parameter_value(material, name) - value) > .0001:
            raise RuntimeError('Display scalar readback differs: ' + name)
    for name, value in textures.items():
        if edit.get_material_instance_texture_parameter_value(material, name) != value:
            raise RuntimeError('Display texture inheritance differs: ' + name)
    for name, value in vectors.items():
        if tuple(edit.get_material_instance_vector_parameter_value(material, name).to_tuple()) != tuple(value.to_tuple()):
            raise RuntimeError('Display color readback differs: ' + name)
    for name, value in switches.items():
        if bool(edit.get_material_instance_static_switch_parameter_value(material, name)) != value:
            raise RuntimeError('Native display switch readback differs: ' + name)
    return material, {'variant': variant, 'source': source.get_path_name(), 'private': material.get_path_name(),
                      'changed_scalars': changed, 'original_textures': {n: t.get_path_name() for n, t in textures.items()},
                      'native_uv_scroll_and_masks_preserved': True, 'constant_opacity': .9,
                      'native_pulse_blackouts_removed': True}


def _fit_pair(ctx, u, frame, pane, target_center, factor, width_axis, limits):
    """Scale both actors about their common measured frame center, preserving thickness."""
    if frame.get_editor_property('hidden') or pane.get_editor_property('hidden'):
        raise RuntimeError('Expected visible reviewed native display pair')
    original_center, original_extent = mesh_union(frame)
    frame_t = frame.get_actor_transform()
    pane_t = pane.get_actor_transform()
    if tuple(frame_t.rotation.to_tuple()) != tuple(pane_t.rotation.to_tuple()):
        raise RuntimeError('Display pane/frame rotations differ')
    preserved = {actor: (tuple(actor.static_mesh_component.get_materials()),
                         actor.get_actor_enable_collision(), actor.static_mesh_component.get_collision_enabled())
                 for actor in (frame, pane)}
    # All inspected Genesis window frames are native X-depth/Y-width/Z-height.
    # Use one common affine transform, preserving native pane recess and layers.
    for actor in (frame, pane):
        before = transform_record(actor)
        transform = actor.get_actor_transform()
        delta = transform.translation - original_center
        projected = u.MathLibrary.quat_unrotate_vector(frame_t.rotation, delta)
        projected = u.Vector(projected.x, projected.y * factor, projected.z * factor)
        transformed = u.MathLibrary.quat_rotate_vector(frame_t.rotation, projected)
        location = u.Vector(*target_center) + transformed
        scale = transform.scale3d
        actor.set_actor_scale3d(u.Vector(scale.x, scale.y * factor, scale.z * factor))
        ctx.move(actor, location)
        ctx.records.append({'kind': 'display_complete_pair_fit', 'before': before, 'after': transform_record(actor)})
    center, extent = mesh_union(frame)
    if abs(getattr(extent, width_axis) - getattr(original_extent, width_axis) * factor) > .05:
        raise RuntimeError('Native display width did not match the complete pair fit')
    depth_axis = 'y' if width_axis == 'x' else 'x'
    if abs(getattr(extent, depth_axis) - getattr(original_extent, depth_axis)) > .05:
        raise RuntimeError('Native frame thickness changed')
    low = [getattr(center, a) - getattr(extent, a) for a in ('x', 'y', 'z')]
    high = [getattr(center, a) + getattr(extent, a) for a in ('x', 'y', 'z')]
    if any(low[i] < limits[0][i] or high[i] > limits[1][i] for i in range(3)):
        raise RuntimeError('Display exceeds its inspected wall-only envelope: ' + repr((low, high)))
    for actor, before in preserved.items():
        if before != (tuple(actor.static_mesh_component.get_materials()),
                      actor.get_actor_enable_collision(), actor.static_mesh_component.get_collision_enabled()):
            raise RuntimeError('Fitting the complete native pair changed materials or collision')
    return {'frame': frame.get_actor_label(), 'pane': pane.get_actor_label(),
            'center_cm': list(center.to_tuple()), 'extent_cm': list(extent.to_tuple()),
            'before_extent_cm': list(original_extent.to_tuple()), 'planar_scale': factor,
            'native_frame_depth_preserved': True, 'route_guard_min_cm': limits[0], 'route_guard_max_cm': limits[1]}


def apply(ctx):
    import unreal as u
    actors = list(ctx.actors)
    marker = _one(actors, 'Refine/Operations/Identity')
    if TAG in map(str, marker.tags) or 'StationServiceGraphics20261006' not in map(str, marker.tags):
        raise RuntimeError('Display wall requires exactly the reviewed RoomPass4 graphics candidate')
    pairs = []
    for index, y, variant in ((1, -650, 'Graph1'), (2, 0, 'DigitalPanel'), (3, 650, 'Graph2')):
        prefix = 'Refine/Operations/Rear data %d/' % index
        pairs.append((_one(actors, prefix + 'Frame'), _one(actors, prefix + 'Glass'),
                      (9148, y, 165), 1.5, 'y', ((9110, y - 301, 14), (9186, y + 301, 316)), variant))
    pairs.append((_one(actors, 'Lounge/RearHoloArchive1/Frame'),
                  _one(actors, 'Lounge/RearHoloArchive1/AnimatedGlass'),
                  (3260, 4460, 175), 1.5, 'x', ((3034, 4438, 24), (3486, 4482, 326)), 'DigitalPanel'))
    selected = {actor for pair in pairs for actor in pair[:2]}
    untouched = {actor: _pose(actor) for actor in actors if actor not in selected}
    for frame, pane, *_ in pairs:
        for actor in (frame, pane):
            c = actor.get_component_by_class(u.StaticMeshComponent)
            if not c or not c.static_mesh or not c.static_mesh.get_path_name().startswith(P4 + 'Meshes/SM_Window'):
                raise RuntimeError('Display pair lost native window geometry')
        if not pane.static_mesh_component.static_mesh.get_name().endswith('_V2_Part2_DigitalWindow'):
            raise RuntimeError('Display pane is no longer the inspected native graphic mesh')
    root = Path(u.Paths.project_dir())
    sources = {path: _hash(_file(root, path)) for path in (MASTER,) + tuple(VARIANTS + v for v in ('Graph1', 'DigitalPanel', 'Graph2'))}
    dirty = []
    master, graph = _master(ctx, u, dirty)
    materials, material_rows = {}, []
    for variant in ('Graph1', 'DigitalPanel', 'Graph2'):
        material, row = _material(ctx, u, master, variant, dirty)
        materials[variant] = material
        material_rows.append(row)
    fitted = []
    for frame, pane, center, factor, axis, limits, variant in pairs:
        fitted.append(_fit_pair(ctx, u, frame, pane, center, factor, axis, limits))
        component = pane.static_mesh_component
        for slot in range(component.get_num_materials()):
            old = component.get_material(slot)
            ctx.records.append({'kind': 'display_wall_material', 'actor': pane.get_actor_label(), 'slot': slot,
                                'before': old.get_path_name() if old else None, 'after': materials[variant].get_path_name()})
            component.set_material(slot, materials[variant])
    if any(_pose(actor) != before for actor, before in untouched.items()):
        raise RuntimeError('Display wall changed an unrelated owner actor transform')
    for path, before in sources.items():
        if _hash(_file(root, path)) != before:
            raise RuntimeError('Native display source file changed: ' + path)
    marker.tags = list(marker.tags) + [TAG]
    return {'module': 'native_blue_display_wall', 'dirty_assets': dirty, 'graph_evidence': graph,
            'materials': material_rows, 'complete_assemblies': fitted, 'source_hashes_preserved': sources,
            'basis': 'Station-Design-Targets; RoomPass4/04_Operations and 05_CrewArchive; ServiceMaterialProbe',
            'unchanged': ['native frames and pane recesses', 'all native source assets', 'owner architecture',
                          'furniture', 'Earth', 'Home/apartment', 'lights', 'exposure', 'bloom'],
            'acceptance': 'Native compile/readbacks, matched room renders at multiple time samples and geometry required.'}
