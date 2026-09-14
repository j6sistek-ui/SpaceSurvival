"""Validate persistent map collision and hero material usage; --repair fixes these owned assets."""
import json
from pathlib import Path
import sys
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
BASE = '/Game/SpaceSurvival'
repair = '--repair' in sys.argv
levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
if not levels.load_level(BASE + '/Maps/Survival'):
    raise RuntimeError('Could not load the actual gameplay map')
record = {'repair': repair, 'actors': [], 'materials': [], 'errors': []}
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    mesh = actor.get_component_by_class(u.StaticMeshComponent)
    if mesh:
        item = {'label': label, 'location': str(actor.get_actor_location()),
                'collision_before': str(mesh.get_collision_enabled()),
                'profile_before': str(mesh.get_collision_profile_name()),
                'actor_collision_before': actor.get_actor_enable_collision()}
        if label in ('DistantStarfield', 'DeepSpaceBackdrop'):
            if repair:
                actor.set_actor_enable_collision(False)
                mesh.set_collision_profile_name('NoCollision')
                mesh.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
            if actor.get_actor_enable_collision() or mesh.get_collision_enabled() != u.CollisionEnabled.NO_COLLISION:
                record['errors'].append(label + ': presentation backdrop still collides')
        item['collision_after'] = str(mesh.get_collision_enabled())
        item['actor_collision_after'] = actor.get_actor_enable_collision()
        record['actors'].append(item)
    if label in ('SpaceKey', 'SpaceRim') and repair:
        actor.get_component_by_class(u.DirectionalLightComponent).set_editor_property('forward_shading_priority', 2 if label == 'SpaceKey' else 1)
mesh = u.EditorAssetLibrary.load_asset(BASE + '/Character/SK_Acornaut')
for slot in mesh.get_editor_property('materials'):
    material = slot.get_editor_property('material_interface')
    if not material:
        record['errors'].append('Hero material missing')
        continue
    base = material.get_base_material()
    item = {'path': base.get_path_name(), 'skeletal_before': base.get_editor_property('used_with_skeletal_mesh')}
    if repair:
        base.set_editor_property('used_with_skeletal_mesh', True)
        u.MaterialEditingLibrary.recompile_material(base)
        u.EditorAssetLibrary.save_loaded_asset(base)
    item['skeletal_after'] = base.get_editor_property('used_with_skeletal_mesh')
    if not item['skeletal_after']:
        record['errors'].append('Hero material cannot render skeletal mesh in game')
    record['materials'].append(item)
for name in ('M_Hull', 'M_Gold', 'M_Cyan'):
    material = u.EditorAssetLibrary.load_asset(BASE + '/Materials/' + name)
    if not material:
        record['errors'].append(name + ': material missing')
        continue
    item = {'path': material.get_path_name(), 'instanced_before': material.get_editor_property('used_with_instanced_static_meshes')}
    if repair and not item['instanced_before']:
        material.set_editor_property('used_with_instanced_static_meshes', True)
        u.MaterialEditingLibrary.recompile_material(material)
        if not u.EditorAssetLibrary.save_loaded_asset(material):
            raise RuntimeError('Failed to save instanced material ' + name)
    item['instanced_after'] = material.get_editor_property('used_with_instanced_static_meshes')
    if not item['instanced_after']:
        record['errors'].append(name + ': station batches would use default material in game')
    record['materials'].append(item)
if repair and not levels.save_current_level():
    raise RuntimeError('Failed to save repaired gameplay map')
output = ROOT / 'Saved/Validation/SceneValidation.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
u.log('SS_SCENE_VALIDATION ' + json.dumps(record))
if record['errors']:
    raise RuntimeError('Scene validation failed: ' + '; '.join(record['errors']))
