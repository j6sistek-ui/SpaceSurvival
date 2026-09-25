"""Private Nanite-compatible copy of the owned arcade's original material graph.

No material values, textures, mesh defaults or source assets are changed. The
caller owns the editor process and saving the sandbox map after assignment.
"""
import hashlib
from pathlib import Path

LABEL = 'Lounge_Arcade_SpaceHunt'
MESH = '/Game/Fab/Space_hunt_Arcade_Machine/SM_Space_hunt_Arcade_Machine.SM_Space_hunt_Arcade_Machine'
SOURCE = '/Game/Fab/Space_hunt_Arcade_Machine/Material_6'
TARGET = '/Game/OutpostSandbox/Materials/M_ArcadeSpaceHuntNanite'


def apply(api):
    u,eas,lib,edit = api['u'],api['EAS'],api['LIB'],api['EDIT']
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    package = world.get_path_name().split('.')[0]
    target_map = '/Game/OutpostSandbox/L_AsteroidOutpost'
    fresh = package.startswith('/Temp/Untitled') and api.get('TARGET') == target_map
    if package != target_map and not fresh:
        raise RuntimeError('Arcade material repair is restricted to the private outpost')
    matches = [actor for actor in eas.get_all_level_actors() if actor.get_actor_label() == LABEL]
    if len(matches) != 1:
        raise RuntimeError('Expected one owned Space Hunt arcade cabinet')
    component = matches[0].get_component_by_class(u.StaticMeshComponent)
    if not component or component.static_mesh.get_path_name() != MESH or component.get_num_materials() != 1:
        raise RuntimeError('Arcade source mesh or material-slot layout changed')
    current = component.get_material(0)
    if not current or current.get_path_name().split('.')[0] not in (SOURCE,TARGET):
        raise RuntimeError('Arcade has an unrecognized material override')
    source_file = Path(api['ROOT']) / 'Content/Fab/Space_hunt_Arcade_Machine/Material_6.uasset'
    before = hashlib.sha256(source_file.read_bytes()).hexdigest()
    created = not lib.does_asset_exist(TARGET)
    material = lib.duplicate_asset(SOURCE,TARGET) if created else api['load'](TARGET)
    if not isinstance(material,u.Material):
        raise RuntimeError('Expected a private copy of the arcade base material')
    usage = u.MaterialUsage.MATUSAGE_NANITE
    flag_changed = not edit.has_material_usage(material,usage)
    if flag_changed:
        edit.set_base_material_usage(material,usage,True)
    if not edit.has_material_usage(material,usage):
        raise RuntimeError('Private arcade material did not acquire Nanite usage')
    if not lib.save_loaded_asset(material):
        raise RuntimeError('Could not save private arcade material')
    assigned = current != material
    if assigned:
        component.set_material(0,material)
    after = hashlib.sha256(source_file.read_bytes()).hexdigest()
    if before != after:
        raise RuntimeError('Source arcade material unexpectedly changed on disk')
    return {'actor':LABEL,'source_material':SOURCE,'private_material':TARGET,
            'created':created,'usage_flag_changed':flag_changed,'slot_assigned':assigned,
            'nanite_usage':True,'source_material_sha256':before,'source_material_unchanged':True,
            'source_graph_and_visual_parameters_preserved':True,'map_saved':False}
