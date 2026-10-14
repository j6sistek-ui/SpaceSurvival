"""Promote the owner's saved preview into the existing live station, explicitly.

Import is inert. Call promote(unreal, preview_sha, runtime_sha, apply=False)
in the sole editor for a dry run, then repeat with apply=True only after review.
The source must already be saved and Play stopped. No asset regeneration/cook.
If native overwrite fails, do not retry. Close the editor, retain the old map
offline under .agent/local/StationPromotion, reopen the source, then pass that
verified runtime_backup path. The canonical destination must be absent.
"""

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

SOURCE = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
TARGET = '/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime'


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _map_file(root, package):
    return root / ('Content/' + package.removeprefix('/Game/') + '.umap')


def _actors(u, world):
    return [a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
            if a.get_outer().get_outer() == world]


def _snapshot(actors):
    return {a.get_name(): {'label': a.get_actor_label(),
                           'class': a.get_class().get_path_name(),
                           # Unreal's struct repr includes an allocation address.
                           'transform': str(a.get_actor_transform()).split(') ', 1)[1]}
            for a in actors}


def promote(u, preview_sha, runtime_sha, apply=False, runtime_backup=None):
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    world = editor.get_editor_world()
    assert world.get_path_name() == SOURCE + '.' + SOURCE.rsplit('/', 1)[1]
    assert editor.get_game_world() is None, 'Stop Play before promotion'
    assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    assert not u.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    source, target = _map_file(root, SOURCE), _map_file(root, TARGET)
    assert _sha(source) == preview_sha, 'Preview changed; review the new saved state'
    runtime_input = target
    if runtime_backup is not None:
        assert not target.exists(), 'Offline replacement requires an absent destination'
        runtime_input = Path(runtime_backup).resolve(strict=True)
        assert runtime_input.is_relative_to((root / '.agent/local/StationPromotion').resolve())
    assert _sha(runtime_input) == runtime_sha, 'Runtime changed; preserve and review first'
    protected_paths = [p for folder in ('Content/OutpostSandbox', 'Content/BuildingLibrary')
                       for p in (root / folder).rglob('*.umap')]
    protected_paths.append(root / 'Content/Blender/Sandbox/BuildingSandbox_20260922.umap')
    protected = {p.relative_to(root).as_posix(): _sha(p) for p in protected_paths}
    actors = _actors(u, world)
    before = _snapshot(actors)
    assert len(actors) > 7000, 'Incomplete station'
    pad = [a for a in actors if a.get_actor_label() == 'Ground/Player berth']
    assert len(pad) == 1
    assert any(c.get_collision_enabled() != u.CollisionEnabled.NO_COLLISION
               for c in pad[0].get_components_by_class(u.StaticMeshComponent))
    mode = world.get_world_settings().get_editor_property('default_game_mode')
    assert mode and mode.get_path_name() == '/Script/SpaceSurvival.SSOutpostSandboxGameMode'
    report = {'status': 'DRY_RUN', 'source': SOURCE, 'target': TARGET,
              'source_sha256': preview_sha, 'previous_runtime_sha256': runtime_sha,
              'direct_actor_count': len(actors), 'protected_map_count': len(protected),
              'tag_updates': sum([str(t) for t in a.tags if str(t).startswith('OutpostLabel:')]
                                 != ['OutpostLabel:' + a.get_actor_label()] for a in actors),
              'game_mode': mode.get_path_name(), 'package_published': False}
    if not apply:
        return report
    assert runtime_backup is not None, 'Close the editor and retain the old runtime offline before replacement'
    out = root / '.agent/local/StationPromotion' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out.mkdir(parents=True, exist_ok=False)
    shutil.copy2(runtime_input, out / 'L_WayfarerRuntime.before.umap')
    shutil.copy2(source, out / 'OwnerPreview.source.umap')
    assert _sha(out / 'L_WayfarerRuntime.before.umap') == runtime_sha
    assert _sha(out / 'OwnerPreview.source.umap') == preview_sha
    report['backup_directory'] = str(out)
    report['protected_maps'] = protected
    (out / 'preflight.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    for actor in actors:
        tags = [t for t in actor.tags if not str(t).startswith('OutpostLabel:')]
        actor.tags = tags + [u.Name('OutpostLabel:' + actor.get_actor_label())]
    # UE's Save As preserves the loaded source assembly and updates internal world
    # references correctly. Never copy a .umap over a loaded package on disk.
    assert u.EditorLoadingAndSavingUtils.save_map(world, TARGET), 'Native Save As failed; inspect before retry'
    # SaveMap writes the duplicate but does not select it as the editor world.
    assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level(TARGET)
    current = editor.get_editor_world()
    assert current.get_path_name() == TARGET + '.' + TARGET.rsplit('/', 1)[1]
    adopted = _actors(u, current)
    assert _snapshot(adopted) == before, 'Actor identity/placement changed during promotion'
    assert all([str(t) for t in a.tags if str(t).startswith('OutpostLabel:')]
               == ['OutpostLabel:' + a.get_actor_label()] for a in adopted)
    assert all(_sha(root / p) == h for p, h in protected.items()), 'A protected source map changed'
    assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    assert not u.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    report.update(status='SAVED', runtime_sha256=_sha(target),
                  source_maps_preserved=True, actor_identity_and_placement_preserved=True,
                  native_reload_verified=True, gameplay_verified=False)
    (out / 'promotion.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report
