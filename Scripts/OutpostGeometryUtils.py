"""Geometry-derived authoring bounds, including every actual ISM instance.

Actor/component cached bounds can be stale immediately after spawn or scaling.
Measure native mesh bounds through current component/instance world transforms;
root positions, empty components and editor billboards must not enlarge a fit.
This module starts no Unreal process and edits no vendor assets.
"""
import itertools


def mesh_union(actor):
    """Return (world centre, world extent) from rendered mesh geometry bounds."""
    import unreal as u
    low = [float('inf')] * 3
    high = [float('-inf')] * 3
    count = 0
    for component in actor.get_components_by_class(u.StaticMeshComponent):
        mesh = component.static_mesh
        if not mesh:
            continue
        bounds = mesh.get_bounds()
        transforms = [component.get_instance_transform(i, world_space=True)
                      for i in range(component.get_instance_count())] \
            if isinstance(component, u.InstancedStaticMeshComponent) else [component.get_world_transform()]
        corners = [bounds.origin + u.Vector(bounds.box_extent.x * x,
                    bounds.box_extent.y * y, bounds.box_extent.z * z)
                   for x, y, z in itertools.product((-1, 1), repeat=3)]
        for transform in transforms:
            count += 1
            for point in corners:
                point = u.MathLibrary.transform_location(transform, point)
                values = (point.x, point.y, point.z)
                low = [min(low[i], values[i]) for i in range(3)]
                high = [max(high[i], values[i]) for i in range(3)]
    if not count:
        raise RuntimeError('No populated static geometry to fit: ' + actor.get_name())
    center = u.Vector(*[(low[i] + high[i]) * .5 for i in range(3)])
    extent = u.Vector(*[(high[i] - low[i]) * .5 for i in range(3)])
    return center, extent


def inspect_scale_inheritance(actor):
    """Read actual flags on every scene component, including non-mesh parents."""
    import unreal as u
    result = []
    for component in actor.get_components_by_class(u.SceneComponent):
        parent = component.get_attach_parent()
        world = component.get_world_transform()
        relative = component.get_relative_transform()
        result.append({'component': component.get_name(),
            'parent': parent.get_name() if parent else None,
            'absolute_location': bool(component.get_editor_property('absolute_location')),
            'absolute_rotation': bool(component.get_editor_property('absolute_rotation')),
            'absolute_scale': bool(component.get_editor_property('absolute_scale')),
            'world_scale': [world.scale3d.x, world.scale3d.y, world.scale3d.z],
            'relative_scale': [relative.scale3d.x, relative.scale3d.y, relative.scale3d.z]})
    return result


def inherit_parent_scale_preserving_world(actor):
    """Remove child absolute-scale barriers without changing current geometry.

    UE5.8 SceneComponent::SetAbsolute only updates flags and component-to-world;
    it does not retain the old pose. Snapshot every node first, then handle
    parents before children and restore each changed node with SetWorldTransform.
    This recomputes the corresponding relative transform under inherited scale.
    Vendor Blueprint/class assets remain untouched; only this placed actor's
    component instances change. Location/rotation absolute flags are preserved.
    """
    import unreal as u
    before = inspect_scale_inheritance(actor)
    nodes = list(actor.get_components_by_class(u.SceneComponent))
    saved = {component.get_name(): component.get_world_transform() for component in nodes}

    def depth(component):
        level, seen = 0, set()
        parent = component.get_attach_parent()
        while parent is not None:
            name = parent.get_path_name()
            if name in seen:
                raise RuntimeError('Scene component attachment cycle: ' + name)
            seen.add(name)
            level += 1
            parent = parent.get_attach_parent()
        return level

    center_before, extent_before = mesh_union(actor)
    changed = []
    for component in sorted(nodes, key=depth):
        if component.get_attach_parent() is None:
            continue
        if not component.get_editor_property('absolute_scale'):
            continue
        absolute_location = bool(component.get_editor_property('absolute_location'))
        absolute_rotation = bool(component.get_editor_property('absolute_rotation'))
        component.set_absolute(absolute_location, absolute_rotation, False)
        component.set_world_transform(saved[component.get_name()], False, False)
        changed.append(component.get_name())
    center_after, extent_after = mesh_union(actor)
    deviations = [abs(getattr(a, axis) - getattr(b, axis))
                  for a, b in ((center_before, center_after), (extent_before, extent_after))
                  for axis in ('x', 'y', 'z')]
    if max(deviations) > .05:
        raise RuntimeError('Scale inheritance normalization changed native geometry: '
                           + actor.get_name() + ' by ' + str(max(deviations)) + 'cm')
    return {'before': before, 'normalized_components': changed,
            'preserved_geometry_max_error_cm': max(deviations)}


def fit_blueprint_from_geometry(actor, target, height):
    """Uniformly fit full Blueprint geometry; preserve all child proportions.

    target is the desired world bounds centre, height is positive world cm.
    Native actor rotation and any existing relative scale are preserved.
    """
    import unreal as u
    if height <= 0:
        raise ValueError('Blueprint fitted height must be positive')
    inheritance = inherit_parent_scale_preserving_world(actor)
    _, extent = mesh_union(actor)
    if extent.z <= .0001:
        raise RuntimeError('Blueprint geometry has no measurable height')
    factor = height / (extent.z * 2)
    scale = actor.get_actor_scale3d()
    actor.set_actor_scale3d(u.Vector(scale.x * factor, scale.y * factor, scale.z * factor))
    center, _ = mesh_union(actor)
    position = actor.get_actor_location()
    actor.set_actor_location(position + u.Vector(*target) - center, False, False)
    center, extent = mesh_union(actor)
    actual = [center.x, center.y, center.z]
    if abs(extent.z * 2 - height) > .05 or max(abs(actual[i] - target[i]) for i in range(3)) > .05:
        raise RuntimeError('Blueprint geometry fit did not converge: ' + actor.get_name())
    return {'actor': actor.get_name(), 'center': actual,
            'size': [extent.x * 2, extent.y * 2, extent.z * 2],
            'scale_factor': factor, 'method': 'transformed_native_mesh_union',
            'scale_inheritance': inheritance}