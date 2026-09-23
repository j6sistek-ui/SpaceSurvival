"""Copy the owned building demos into a private, walkable authoring map.

Uses the reviewed layout beside this script, or an explicit artifact override.
Never saves the vendor examples or replaces an existing sandbox.
"""
import hashlib
from collections import Counter
import json
import math
import os
from pathlib import Path
import uuid

import unreal as u
import ss_prefabs

ROOT = Path(u.Paths.project_dir())
OUT = ROOT / 'Artifacts/BuildingSandbox'
OUT.mkdir(parents=True, exist_ok=True)
layout_path = OUT / 'layout.json'
if not layout_path.exists():
    layout_path = Path(__file__).with_name('BuildingSandboxLayout.json')
LAYOUT = json.loads(layout_path.read_text(encoding='utf-8'))
TARGET = LAYOUT['target_map']
EAS = u.get_editor_subsystem(u.EditorActorSubsystem)


def map_file(path):
    return ROOT / 'Content' / (path.removeprefix('/Game/') + '.umap')


def digest(path):
    return hashlib.sha256(map_file(path).read_bytes()).hexdigest()


def infrastructure(actor):
    name = actor.get_class().get_name()
    if isinstance(actor, u.InstancedFoliageActor):
        return not any(c.get_instance_count() for c in actor.get_components_by_class(u.InstancedStaticMeshComponent))
    return (isinstance(actor, (u.WorldSettings, u.LevelScriptActor)) or
            name in ('WorldDataLayers',
                     'WorldPartitionMiniMap', 'NavigationDataChunkActor',
                     'RecastNavMesh', 'PlayerStart') or
            name.endswith('HLOD') or actor.get_name() == 'Brush_0')


def global_environment(actor):
    name = actor.get_class().get_name()
    return (name in ('DirectionalLight', 'SkyLight', 'SkyAtmosphere', 'AtmosphericFog',
                     'ExponentialHeightFog', 'VolumetricCloud', 'PostProcessVolume') or
            'sky' in actor.get_actor_label().lower())


def emit(receipt):
    (OUT / 'build.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')


assert TARGET.startswith('/Game/Blender/Sandbox/'), TARGET
source_hashes = {area['map']: digest(area['map']) for area in LAYOUT['areas']}
if os.environ.get('SS_SANDBOX_RESUME') == '1':
    receipt = json.loads((OUT / 'build.json').read_text(encoding='utf-8'))
    assert receipt['target_map'] == TARGET and not receipt['complete'], 'Only an incomplete matching build may resume'
    assert receipt['source_hashes'] == source_hashes, 'Source examples changed since the partial build'
else:
    assert not map_file(TARGET).exists(), 'Existing sandbox kept: choose a new target map'
    assert LAYOUT['areas'][0]['offset'] == [0, 0, 0], 'Keep the Genesis source origin and world settings'
    world = u.EditorLoadingAndSavingUtils.load_map(LAYOUT['areas'][0]['map'])
    assert u.EditorLoadingAndSavingUtils.save_map(world, TARGET)
    receipt = {'target_map': TARGET, 'areas': [], 'complete': False, 'source_hashes': source_hashes}
    emit(receipt)

copied_this_pass = False
for index, area in enumerate(LAYOUT['areas']):
    if area['name'] in {a['name'] for a in receipt['areas']}:
        continue
    if index == 0:
        # Native Save As preserves Genesis High Settings' world and level-script settings.
        target = u.EditorLoadingAndSavingUtils.load_map(TARGET)
        actors = list(EAS.get_all_level_actors())
        for actor in actors:
            if isinstance(actor, u.PlayerStart):
                EAS.destroy_actor(actor)
        copied = [a for a in EAS.get_all_level_actors() if not infrastructure(a)]
        for actor in copied:
            actor.set_folder_path(area['name'])
            actor.tags = list(actor.tags) + [u.Name('SSSandboxArea:' + area['name'])]
        assert u.EditorLoadingAndSavingUtils.save_map(target, TARGET)
        receipt['areas'].append({'name': area['name'], 'source': area['map'], 'copied': len(copied),
                                 'offset': area['offset'], 'native_save_as': True})
        emit(receipt)
        continue
    source = u.EditorLoadingAndSavingUtils.load_map(area['map'])
    assert source, area['map']
    if area['name'] == 'ComputerStation':
        descs = u.WorldPartitionBlueprintLibrary.get_actor_descs()
        if isinstance(descs, tuple):
            descs = descs[-1]
        assert descs, 'ComputerStation actor descriptors missing'
        u.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs])
    actors = list(EAS.get_all_level_actors())
    chosen = [a for a in actors if not infrastructure(a) and
              (index == 0 or not global_environment(a))]
    target = u.load_asset(TARGET)
    assert isinstance(target, u.World), TARGET
    copied = list(EAS.duplicate_actors(chosen, target, u.Vector(*area['offset'])))
    source_foliage = {c.static_mesh.get_path_name(): c.get_instance_count()
        for a in actors if isinstance(a, u.InstancedFoliageActor)
        for c in a.get_components_by_class(u.InstancedStaticMeshComponent) if c.static_mesh}
    target_foliage = {c.static_mesh.get_path_name(): c.get_instance_count()
        for a in u.GameplayStatics.get_all_actors_of_class(target, u.InstancedFoliageActor)
        for c in a.get_components_by_class(u.InstancedStaticMeshComponent) if c.static_mesh}
    u.log('SS_FOLIAGE_COPY ' + json.dumps({'source': source_foliage, 'target': target_foliage}))
    # Unreal may dissolve an editor-only GroupActor during native duplication.
    # Visible/functional actor counts must still match by class.
    expected = Counter(a.get_class().get_name() for a in chosen if not isinstance(a, u.GroupActor))
    actual = Counter(a.get_class().get_name() for a in copied if not isinstance(a, u.GroupActor))
    assert expected == actual, f'{area["name"]}: actor classes differ {expected - actual} / {actual - expected}'
    assert all(target_foliage.get(mesh, 0) >= count for mesh, count in source_foliage.items()), 'Foliage instances missing'
    for actor in copied:
        actor.set_folder_path(area['name'])
        actor.tags = list(actor.tags) + [u.Name('SSSandboxArea:' + area['name'])]
        # New GUIDs cannot use the source map's baked lighting. These copies are a Lumen workbench.
        for light in actor.get_components_by_class(u.LightComponent):
            light.set_mobility(u.ComponentMobility.MOVABLE)
    assert u.EditorLoadingAndSavingUtils.save_map(target, TARGET)
    receipt['areas'].append({'name': area['name'], 'source': area['map'], 'copied': len(copied),
                             'offset': area['offset'], 'omitted_infrastructure_or_global': len(actors)-len(chosen)})
    emit(receipt)
    copied_this_pass = True
    u.log('SS_SANDBOX_COPIED ' + json.dumps(receipt['areas'][-1]))

if copied_this_pass:
    # Loading the newly assembled inactive world in this same editor process can
    # retain imported actors across GC. Finalize in a fresh resume invocation.
    u.log('SS_SANDBOX_RESTART_TO_FINALIZE: run again with SS_SANDBOX_RESUME=1')
    raise SystemExit(0)

world = u.EditorLoadingAndSavingUtils.load_map(TARGET)
settings = world.get_world_settings()
mode = u.load_class(None, '/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode.BP_FirstPersonGameMode_C')
assert mode, 'Install the engine First Person template content before authoring'
settings.set_editor_property('default_game_mode', mode)

floor = EAS.spawn_actor_from_class(u.StaticMeshActor, u.Vector(*LAYOUT['platform_center']))
floor.set_actor_label('Sandbox connecting floor')
floor.set_folder_path('Sandbox foundation')
floor.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube.Cube'))
floor.static_mesh_component.set_collision_profile_name('BlockAll')
floor.set_actor_scale3d(u.Vector(*(v / 100 for v in LAYOUT['platform_size'])))
for area in LAYOUT['areas'][1:]:
    # A gentle solid ramp connects the common platform to each example's original floor height.
    ramp = area['ramp']
    rise = ramp['top_z'] - LAYOUT['platform_top']
    angle = math.atan2(rise, ramp['run'])
    actor = EAS.spawn_actor_from_class(u.StaticMeshActor,
        u.Vector(ramp['x'], ramp['front_y'] - ramp['run'] / 2,
                 (ramp['top_z'] + LAYOUT['platform_top']) / 2 - 5 * math.cos(angle)))
    actor.set_actor_label(area['name'] + ' access ramp')
    actor.set_folder_path('Sandbox foundation')
    actor.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube.Cube'))
    actor.static_mesh_component.set_collision_profile_name('BlockAll')
    actor.set_actor_scale3d(u.Vector(math.hypot(rise, ramp['run']) / 100, 2, 0.1))
    actor.set_actor_rotation(u.Rotator(pitch=math.degrees(angle), yaw=90), False)
start = EAS.spawn_actor_from_class(u.PlayerStart, u.Vector(*LAYOUT['start']))
start.set_actor_label('Sandbox walk start')
start.set_actor_rotation(u.Rotator(yaw=LAYOUT.get('start_yaw', 0)), False)

rows, retained = [], {}
for actor in EAS.get_all_level_actors():
    row = ss_prefabs.describe_actor(actor)
    if row and not row.get('light'):
        link = uuid.uuid4().hex
        ss_prefabs._set_tag(actor, ss_prefabs.TAG_LINK, link)
        row['link'] = link
        row['area'] = str(actor.get_folder_path()) or 'Sandbox foundation'
        rows.append(row)
    else:
        kind = actor.get_class().get_name()
        retained[kind] = retained.get(kind, 0) + 1
assert rows, 'No editable mesh actors exported'
try:
    ss_prefabs.apply_link({'target_map': TARGET + '_wrong', 'objects': []})
except RuntimeError:
    pass
else:
    raise AssertionError('Wrong-map push was accepted')
original = next(row for row in rows if row['link'] == ss_prefabs._tag_value(floor, ss_prefabs.TAG_LINK))
moved = json.loads(json.dumps(original))
moved['matrix'][3][0] += 10
try:
    result = ss_prefabs.apply_link({'target_map': TARGET, 'objects': [moved]})
    assert result['moved'] == 1 and not result['errors'], result
    assert abs(floor.get_actor_location().x - moved['matrix'][3][0]) < 0.01
finally:
    ss_prefabs.apply_link({'target_map': TARGET, 'objects': [original]})
assert abs(floor.get_actor_location().x - original['matrix'][3][0]) < 0.01
assert u.EditorLoadingAndSavingUtils.save_map(world, TARGET)
assert all(digest(path) == before for path, before in source_hashes.items()), 'Source map changed'
(OUT / 'scene.json').write_text(json.dumps({'target_map': TARGET, 'objects': rows,
    'retained_in_unreal': retained}, indent=2), encoding='utf-8')
receipt.update(complete=True, linked_meshes=len(rows), retained_in_unreal=retained,
               vendor_map_hashes_unchanged=True, game_mode=mode.get_path_name(),
               wrong_map_rejected=True, linked_move_and_restore=True)
emit(receipt)
u.log('SS_SANDBOX_BUILD_OK ' + json.dumps(receipt))
