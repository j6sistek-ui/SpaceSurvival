"""Plan, then apply only Kraken's two routine animation references and preview clip.

Run in an owned hidden editor. Default is read-only. -SSApplyKrakenCrawl requires
the unchanged plan and a separately reviewed animation; never rebuild the station.
"""
import hashlib
import json
import re
import shutil
from pathlib import Path
import unreal as u

P = Path(u.Paths.project_dir()).resolve()
R = P / '.agent/local/KrakenMotion_20261021'
MAP = '/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime'
CLIP = '/Game/SpaceSurvival/Licensed/StationAssets/KrakenOutfit_20261015/Crawl_20261021/A_Kraken_IndependentCrawl_24s'
MAP_FILE = P / ('Content/' + MAP.removeprefix('/Game/') + '.umap')
CLIP_FILE = P / ('Content/' + CLIP.removeprefix('/Game/') + '.uasset')
APPLY = '-SSApplyKrakenCrawl' in u.SystemLibrary.get_command_line().split()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def actor_layout():
    actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
    rows = sorted((a.get_path_name(), a.get_class().get_path_name(), a.get_actor_label(),
                   a.get_actor_transform().export_text()) for a in actors)
    return hashlib.sha256(json.dumps(rows).encode()).hexdigest(), len(rows)


def properties(obj, excluded=()):
    def value_text(value):
        if isinstance(value, u.Object):
            return value.get_path_name()
        if hasattr(value, 'export_text'):
            return value.export_text()
        if isinstance(value, (list, tuple, u.Array, u.Set)):
            return [value_text(item) for item in value]
        if isinstance(value, (dict, u.Map)):
            return {str(key): value_text(item) for key, item in value.items()}
        text = str(value)
        if 'delegate' in text and '<Unbound>' in text:
            # Wrapper addresses change on reload; the binding state is the invariant.
            text = re.sub(r'\(0x[0-9A-Fa-f]+\)', '(address omitted)', text)
        return text

    result = {}
    for key in dir(obj):
        if key.startswith('_') or key in excluded:
            continue
        try:
            value = obj.get_editor_property(key)
        except Exception:
            continue
        result[key] = value_text(value)
    return result


level = u.get_editor_subsystem(u.LevelEditorSubsystem)
assert level.load_level(MAP)
actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
matches = [a for a in actors if a.get_actor_label() == 'Crew/Kraken visitor']
assert len(matches) == 1
actor = matches[0]
assert isinstance(actor, u.SSOutpostAmbientActor)
mesh = actor.character_mesh
clip = u.load_asset(CLIP)
assert isinstance(clip, u.AnimSequence)
assert clip.get_editor_property('skeleton') == mesh.skeletal_mesh_asset.skeleton
assert abs(clip.sequence_length - 24) < .001
layout, count = actor_layout()
plan = {'map_sha256': sha(MAP_FILE), 'clip_sha256': sha(CLIP_FILE),
        'actor': actor.get_path_name(), 'layout_sha256': layout, 'actors': count,
        'before_idle': actor.idle_animation.get_path_name(),
        'before_walk': actor.walk_animation.get_path_name(), 'after_clip': CLIP,
        'other_actor_properties': properties(actor, ('idle_animation', 'walk_animation')),
        'other_mesh_properties': properties(mesh, ('animation_data',)),
        'before_preview': mesh.get_editor_property('animation_data').export_text()}
if not APPLY:
    assert actor.idle_animation != clip and actor.walk_animation != clip, 'Already applied'
    (R / 'AdoptionPlan.json').write_text(json.dumps(plan, indent=2), encoding='utf-8')
else:
    (R / 'ObservedPlan.json').write_text(json.dumps(plan, indent=2), encoding='utf-8')
    previous_plan = json.loads((R / 'AdoptionPlan.json').read_text())
    # The saved map hash is the cross-process source guard. Loaded transform text
    # can differ between editor loads; compare layout exactly within this process.
    assert {k: v for k, v in plan.items() if k != 'layout_sha256'} == {
        k: v for k, v in previous_plan.items() if k != 'layout_sha256'
    }, 'Plan became stale'
    review = json.loads((R / 'Framed/Review.json').read_text())
    assert not review['errors'] and len(review['samples']) >= 70
    assert json.loads((R / 'Exit.json').read_text())['production_saves_unchanged']
    approval = json.loads((R / 'LeadReview.json').read_text())
    assert approval['clip_sha256'] == plan['clip_sha256'] and approval['adopt']
    backup = Path('D:/SpaceSurvival_AssetArchive/KrakenMotion_20261021')
    backup.mkdir(parents=True, exist_ok=True)
    recovery = backup / ('L_WayfarerRuntime_' + plan['map_sha256'] + '.umap')
    if not recovery.exists():
        shutil.copy2(MAP_FILE, recovery)
    assert sha(recovery) == plan['map_sha256']
    actor.set_editor_property('idle_animation', clip)
    actor.set_editor_property('walk_animation', clip)
    previous = mesh.get_editor_property('animation_data')
    mesh.override_animation_data(clip, previous.saved_looping, previous.saved_playing,
                                 0., previous.saved_play_rate)
    assert actor_layout() == (layout, count)
    assert properties(actor, ('idle_animation', 'walk_animation')) == plan['other_actor_properties']
    assert properties(mesh, ('animation_data',)) == plan['other_mesh_properties']
    assert level.save_current_level()
    (R / 'Adopted.json').write_text(json.dumps({
        'before_map_sha256': plan['map_sha256'], 'map_sha256': sha(MAP_FILE),
        'clip_sha256': sha(CLIP_FILE), 'backup': str(recovery), 'actor': actor.get_path_name(),
        'layout_sha256': layout, 'actors': count, 'other_properties_preserved': True,
        'fresh_reload_pending': True}, indent=2), encoding='utf-8')
