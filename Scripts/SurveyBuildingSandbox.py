"""Read-only bounds and actor survey of the five owned building examples, inside Unreal."""
import collections
import hashlib
import json
import os
from pathlib import Path
import unreal as u

MAPS = [
    ('Genesis', '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Maps/DemoLevel_HighSettings'),
    ('WorkStation', '/Game/P1toP5_Bundle/P1_WorkStation/Maps/DemoLevel'),
    ('StarterPack', '/Game/P1toP5_Bundle/P2_StarterPack/Maps/Demonstration_ClassicAtmosphere'),
    ('ComputerStation', '/Game/P1toP5_Bundle/P3_ComputerStation/Map/Demonstration_ComputerStation'),
    ('FruitSeller', '/Game/P1toP5_Bundle/P5_FruitSeller/Maps/DemoLevel_FruitSeller'),
]

def vec(v):
    return [round(v.x, 2), round(v.y, 2), round(v.z, 2)]

if __name__ == '__main__':
    out = Path(u.Paths.project_dir()) / 'Artifacts/BuildingSandbox'
    out.mkdir(parents=True, exist_ok=True)
    only = os.environ.get('SS_SURVEY_ONLY')
    result = json.loads((out/'survey.json').read_text()) if only and (out/'survey.json').exists() else []
    for name, path in MAPS:
        if only and name != only:
            continue
        world = u.EditorLoadingAndSavingUtils.load_map(path)
        assert world, path
        if name == 'ComputerStation':
            descs = u.WorldPartitionBlueprintLibrary.get_actor_descs()
            if isinstance(descs, tuple):
                descs = descs[-1]
            assert descs, 'ComputerStation actor descriptors missing'
            u.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs])
        actors = list(u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors())
        meshes, floors, starts = [], [], []
        for actor in actors:
            center, extent = actor.get_actor_bounds(False)
            label = actor.get_actor_label()
            if actor.get_components_by_class(u.StaticMeshComponent):
                row = {'name': label, 'class': actor.get_class().get_name(), 'center': vec(center), 'extent': vec(extent)}
                meshes.append(row)
                if any(key in label.lower() for key in ('floor', 'ground', 'platform')):
                    floors.append(row)
            if isinstance(actor, u.PlayerStart):
                starts.append({'name': label, 'location': vec(actor.get_actor_location())})
        entry = {'name': name, 'map': path, 'actors': len(actors), 'classes': dict(collections.Counter(a.get_class().get_name() for a in actors)),
                 'mesh_actors': len(meshes), 'floors': floors, 'starts': starts, 'meshes': meshes,
                 'light_mobility': dict(collections.Counter(str(c.mobility) for a in actors for c in a.get_components_by_class(u.LightComponent)))}
        result = [r for r in result if r['name'] != name]
        result.append(entry)
        (out/'survey.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        u.log('SS_SANDBOX_SURVEY ' + json.dumps({k:v for k,v in entry.items() if k not in ('meshes','floors')}))
    mode = u.load_class(None, '/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode.BP_FirstPersonGameMode_C')
    assert mode, 'First Person template game mode did not load'
    pawn = u.get_default_object(mode).get_editor_property('default_pawn_class')
    assert pawn, 'Sandbox walking pawn missing'
    u.log('SS_SANDBOX_WALKER ' + pawn.get_path_name())
    u.log('SS_SANDBOX_SURVEY_DONE')
