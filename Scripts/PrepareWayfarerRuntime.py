"""Derive a tagged runtime station without changing either editable sandbox.

Run after building the integrated Editor with -RenderOffscreen. No layout rebuild.
Only the duplicate map is saved; original maps and apartment are hashed before/after.
"""
import hashlib
import json
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
SOURCE = '/Game/OutpostSandbox/L_AsteroidOutpost'
TARGET = '/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime'
OUT = ROOT / 'Artifacts/WayfarerRelease'
OUT.mkdir(parents=True, exist_ok=True)
paths = [ROOT / 'Content/OutpostSandbox/L_AsteroidOutpost.umap',
         ROOT / 'Content/BuildingLibrary/Home/L_CrewApartment.umap',
         ROOT / 'Content/Blender/Sandbox/BuildingSandbox_20260922.umap']
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
before = {str(p): sha(p) for p in paths}
lib = u.EditorAssetLibrary
levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
assert '-renderoffscreen' in u.SystemLibrary.get_command_line().lower()
# Loading a raw duplicated UWorld leaks vendor particle-world references in UE5.8.
# Tag the loaded source in memory, then Save As once; never save source packages.
exists = lib.does_asset_exist(TARGET)
assert not exists or '-ssretagwayfarerruntime' in u.SystemLibrary.get_command_line().lower(), 'Runtime copy exists; preserve before intentional refresh'
assert levels.load_level(TARGET if exists else SOURCE)
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
tagged = []
for actor in actors:
    # Do not edit nested LevelInstance source levels.
    if actor.get_outer().get_outer() != world:
        continue
    label = actor.get_actor_label()
    tags = [tag for tag in actor.tags if not str(tag).startswith('OutpostLabel:')]
    actor.tags = tags + [u.Name('OutpostLabel:' + label)]
    tagged.append(label)
assert len(tagged) > 7000, f'Incomplete station copy: {len(tagged)} actors'
assert any('Player' in label and 'solid' in label.lower() for label in tagged) or any('Berth/' in label for label in tagged)
if exists:
    assert levels.save_current_level()
else:
    assert u.EditorLoadingAndSavingUtils.save_map(world, TARGET)
assert all(sha(p) == before[str(p)] for p in paths), 'Authoring source changed'
report = {'status':'PASS', 'source':SOURCE, 'target':TARGET, 'tagged_actors':len(tagged),
          'source_maps_preserved':before, 'runtime_sha256':sha(ROOT/'Content/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime.umap')}
(OUT/'runtime-map.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
u.log('WAYFARER_RUNTIME_MAP ' + json.dumps(report))
