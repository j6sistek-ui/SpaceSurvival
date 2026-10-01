"""Private textured finishes for the outpost's broad deck and ceiling surfaces.

Retain the vendor material graph, textures and slot assignments. Change only
local paint/metal/roughness parameters on map-specific material children.
"""
import hashlib
import unreal as u


def apply(api, save=True):
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    package = world.get_path_name().split('.')[0]
    target = '/Game/OutpostSandbox/L_AsteroidOutpost'
    fresh_authoring = package.startswith('/Temp/Untitled') and api.get('TARGET') == target
    if package != target and not fresh_authoring:
        raise RuntimeError('Surface finishes are restricted to the private outpost')
    edit, lib, tools = api['EDIT'], api['LIB'], api['TOOLS']
    cache, changes, modified = {}, [], set()
    floor_mesh = api['ASSETS']['floor_main']['asset'].split('.')[0]
    ceiling_mesh = api['ASSETS']['ceiling_main']['asset'].split('.')[0]
    for actor in api['EAS'].get_all_level_actors():
        name = actor.get_actor_label()
        if not any(name.startswith(prefix) for prefix in ('Market/', 'Engineering/', 'Operations/',
                  'Lounge/', 'Atrium/', 'Observation/', 'BerthDetail/', 'RoofDetail/')):
            continue
        for component in actor.get_components_by_class(u.StaticMeshComponent):
            mesh = component.static_mesh
            if not mesh:
                continue
            asset = mesh.get_path_name().split('.')[0]
            role = 'Deck' if asset == floor_mesh else 'Ceiling' if asset == ceiling_mesh else None
            if not role:
                continue
            for slot, current in enumerate(component.get_materials()):
                if not isinstance(current, u.MaterialInstanceConstant):
                    continue
                parent, visited = current, set()
                while parent.get_path_name().startswith('/Game/OutpostSandbox/Materials/MI_Finish_'):
                    path = parent.get_path_name()
                    if path in visited or not isinstance(parent, u.MaterialInstanceConstant):
                        raise RuntimeError('Invalid private finish parent chain: ' + path)
                    visited.add(path)
                    parent = parent.get_editor_property('parent')
                    if parent is None:
                        raise RuntimeError('Private finish has no source parent: ' + path)
                key = (role, parent.get_path_name())
                if key not in cache:
                    scalar_names = set(map(str, edit.get_scalar_parameter_names(parent)))
                    vector_names = set(map(str, edit.get_vector_parameter_names(parent)))
                    if 'Albedo Tint' not in vector_names:
                        cache[key] = parent
                    else:
                        suffix = hashlib.sha1('|'.join(key).encode()).hexdigest()[:12]
                        child_name = 'MI_Finish_' + role + '_' + suffix
                        path = '/Game/OutpostSandbox/Materials/' + child_name
                        child = api['load'](path) if lib.does_asset_exist(path) else tools.create_asset(
                            child_name, '/Game/OutpostSandbox/Materials',
                            u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
                        if not isinstance(child, u.MaterialInstanceConstant):
                            raise RuntimeError('Could not resolve private finish instance: ' + path)
                        changed = child.get_editor_property('parent') != parent
                        if changed:
                            edit.set_material_instance_parent(child, parent)
                        tint = (.12, .17, .22) if role == 'Deck' else (.18, .22, .27)
                        old_tint = edit.get_material_instance_vector_parameter_value(child, 'Albedo Tint')
                        if max(abs(a-b) for a,b in zip((old_tint.r,old_tint.g,old_tint.b,old_tint.a), (*tint,1))) > 1e-6:
                            edit.set_material_instance_vector_parameter_value(child, 'Albedo Tint', u.LinearColor(*tint,1))
                            changed = True
                        values = {'Albedo Tint Intensity': .85, 'Metalness Intensity': .35,
                            'Metalness (Damage)': .4, 'Metalness Intensity (Dirt)': .15,
                            'Min Roughness': .7, 'Max Roughness': 1.,
                            'Min Roughness (Damage)': .6, 'Max Roughness (Damage)': 1.,
                            'Min Roughness (Dirt)': .8, 'Max Roughness (Dirt)': 1.}
                        for parameter, value in values.items():
                            if parameter in scalar_names and abs(edit.get_material_instance_scalar_parameter_value(child,parameter)-value) > 1e-6:
                                edit.set_material_instance_scalar_parameter_value(child,parameter,value)
                                changed = True
                        if changed:
                            modified.add(path)
                        if save:
                            lib.save_loaded_asset(child)
                        cache[key] = child
                child = cache[key]
                if child != current:
                    component.set_material(slot, child)
                    changes.append([name, slot, current.get_path_name(), child.get_path_name()])
    private = {material.get_path_name() for material in cache.values()
               if material.get_path_name().startswith('/Game/OutpostSandbox/Materials/MI_Finish_')}
    return {'surface_slots_changed':len(changes),'private_materials':len(private),
            'private_materials_modified':len(modified),'changes':changes,
            'vendor_materials_unchanged':True,'scope':'Private painted deck/ceiling finish; preserves native texture detail and geometry.'}
