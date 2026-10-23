"""Seed a new observatory with the workshop and a native lounge copy.

Run in the full hidden editor, not a Python commandlet. Exit and use a fresh
process for author_observatory.py after copying into an inactive world.
Never saves the source station or replaces an existing observatory.
"""
import json
from pathlib import Path
import unreal as u

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / '.agent/local/Observatory_20261023'
OUT.mkdir(parents=True, exist_ok=True)
DEST = '/Game/SpaceSurvival/Licensed/EntertainmentObservatory/L_EntertainmentObservatory'
es = u.get_editor_subsystem(u.EditorActorSubsystem)
lib = u.EditorAssetLibrary
try:
    import ss_catalog_refresh
    ss_catalog_refresh.unregister()
except ImportError:
    pass
assert '-RenderOffscreen' in u.SystemLibrary.get_command_line(), 'Use the full hidden editor'
assert not lib.does_asset_exist(DEST), 'Existing observatory preserved'
source = u.EditorLoadingAndSavingUtils.load_map('/Game/SpaceSurvival/Licensed/CharacterWorkshop/L_EntertainmentWorkshop')
assert u.EditorLoadingAndSavingUtils.save_map(source, DEST)
station = u.EditorLoadingAndSavingUtils.load_map('/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime')
assert station
selected = []
for actor in es.get_all_level_actors():
    text = (actor.get_actor_label() + ' ' + str(actor.get_folder_path())).lower()
    if any(key in text for key in ('lounge', 'wardrobe', 'refine/archive', 'r/performance')) and 'skyline' not in text:
        selected.append(actor)
target = lib.load_asset(DEST)
assert isinstance(target, u.World)
copies = es.duplicate_actors(selected, target, u.Vector(-4200, -3400, 0))
assert len(copies) == len(selected)
for actor in copies:
    actor.set_actor_label('Legacy/' + actor.get_actor_label())
    actor.set_folder_path('Observatory/01/ExistingLounge')
assert u.EditorLoadingAndSavingUtils.save_map(target, DEST)
(OUT / 'LoungeCopy.json').write_text(json.dumps({
    'ok': True, 'count': len(copies), 'map': DEST,
    'source_labels': [actor.get_actor_label() for actor in selected]
}, indent=2), encoding='utf-8')
u.SystemLibrary.quit_editor()
