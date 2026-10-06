"""Refresh the complete current project's native library and ULAT mesh palette.

Run in an offscreen Entry-map editor with -ExecutePythonScript=<this file>.
The default is a dry-run; add -SSApplyBuildingCollections to apply. Every public
/Game asset gets a pack collection, including materials, Blueprints and maps.
ULAT receives only StaticMeshes through its existing backup-preserving importer.
Short-name collisions stay in native collections; vendor assets are not renamed.
Existing collection members, palette rows, maps and content packages are retained.
Reports and collection backups live under Artifacts/BuildingLibrary/Refresh.
"""

import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


PACK_ALIASES = {
    'CargoShip': 'SS_New___Cargo_Ship',
    'Rocket': 'SS_New___Furniture_Lights_and_Props',
    'CyberpunkRestaurant': 'SS_New___Nova_Space_Burgers',
    'ImportedLibrary': 'SS_New___Solar_and_Portal_Materials',
    'Cyberpunk_Room': 'SS_New_CP_Apartment',
    'CyberPunkBarAssetSet01': 'SS_New_CP_Bar',
    'CyberPunkMegapack': 'SS_New_CP_Megapack',
    'CyberPunkAssets': 'SS_New_CP_SciFi',
    'CyberpunkHolograms': 'SS_New_CP_Holograms',
}
CP_LABELS = {
    'Cyberpunk_Room': 'CP Apartment',
    'CyberPunkBarAssetSet01': 'CP Bar',
    'CyberPunkMegapack': 'CP Megapack',
    'CyberPunkAssets': 'CP SciFi',
    'CyberpunkHolograms': 'CP Holograms',
}
ASSEMBLED = 'SS_01_Assembled___Drag_These'


def collection_name(value):
    return re.sub(r'[^A-Za-z0-9_]', '_', value)


def build_plan(inventory, classify):
    """Pure planning step; retain full object paths even when names collide."""
    groups, entries, pack_counts, seen = {}, [], {}, set()

    def add(name, path):
        groups.setdefault(name, set()).add(path)

    for asset in sorted(inventory, key=lambda item: item['path']):
        path, kind = asset['path'], asset['class']
        if not path.startswith('/Game/') or path in seen:
            continue
        pack = path.split('/')[2]
        # External actor/object packages are implementation storage, not assets
        # that can be placed from the Content Browser. Redirectors are aliases.
        if pack.startswith('__') or kind == 'ObjectRedirector':
            continue
        seen.add(path)
        pack_counts[pack] = pack_counts.get(pack, 0) + 1
        add('SS_All_Project_Assets', path)
        add(collection_name('SS_Pack_' + pack), path)
        if pack in PACK_ALIASES:
            add(PACK_ALIASES[pack], path)
        if path.startswith('/Game/BuildingLibrary/Assembled/') and kind == 'Blueprint':
            add(ASSEMBLED, path)
        if path.startswith('/Game/BuildingLibrary/Assembled/Home/') and kind == 'Blueprint':
            add('SS_New_CP_Apartment', path)
        if kind == 'World':
            add('SS_02_Maps_and_Complete_Scenes', path)
        if kind == 'StaticMesh':
            category, label = classify(path)
            add(collection_name('SS Parts - ' + label), path)
            entries.append({'asset_path': path, 'category': category,
                            'type_label': CP_LABELS.get(pack, label)})
    return {name: sorted(paths) for name, paths in sorted(groups.items())}, entries, pack_counts


def collection_members(u, manager, ref, allow_missing=False):
    # UE5.8 returns None (and logs a warning) when querying an absent collection.
    # Its AddAssetsToCollection creates missing static collections automatically.
    if allow_missing and not manager.collection_exists(
            u.CollectionContainerSource(), ref.name, ref.share_type):
        return set()
    members = manager.get_assets_in_collection(ref)
    if isinstance(members, tuple):
        if members and members[0] is False:
            raise RuntimeError('Cannot read collection: ' + str(ref.name))
        members = members[-1]
    if members is None:
        raise RuntimeError('Cannot read collection: ' + str(ref.name))
    return {str(asset.package_name) + '.' + str(asset.asset_name) for asset in members}


def run(apply=False):
    import unreal as u

    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
    sys.path.insert(0, str(root / 'Scripts'))
    import ConfigureUlatLibrary as ulat

    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid4().hex[:8]
    output = root / 'Artifacts/BuildingLibrary/Refresh' / run_id
    output.mkdir(parents=True, exist_ok=True)
    report = {'status': 'blocked', 'mode': 'apply' if apply else 'dry_run',
              'project_dir': str(root), 'collections': [], 'errors': [],
              'report_path': str(output / 'refresh.json'),
              'collision_policy': 'Preserve vendor names and existing ULAT rows; full paths remain in native collections.'}
    try:
        world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
        if not world or not world.get_path_name().startswith('/Engine/Maps/Entry'):
            raise RuntimeError('Run only in an empty Entry-map editor, not an owner editing session')
        # Avoid background proxy/catalog export in this process while indexing.
        refresh = sys.modules.get('ss_catalog_refresh')
        if refresh is not None:
            refresh.unregister()
        registry = u.AssetRegistryHelpers.get_asset_registry()
        registry.search_all_assets(True)
        inventory = [{'path': str(asset.package_name) + '.' + str(asset.asset_name),
                      'class': str(asset.asset_class_path.asset_name)}
                     for asset in registry.get_assets_by_path('/Game', recursive=True)]
        groups, entries, packs = build_plan(inventory, ulat._classify)
        if not groups or not entries:
            raise RuntimeError('No project assets/static meshes found; refusing an empty refresh')
        report.update(packs=packs, asset_count=len(groups['SS_All_Project_Assets']),
                      requested_meshes=len(entries))
        dry = ulat.apply(entries, apply=False)
        report['ulat_dry_run'] = dry
        if dry['status'] != 'dry_run_ready':
            raise RuntimeError('ULAT preflight failed: ' + str(dry['errors']))
        collisions = sorted({item['asset_path'] for item in dry['skipped']
                             if item['reason'] == 'ULAT short-name collision'})
        if collisions:
            groups['SS_ULAT_Name_Collisions'] = collisions
        report['collision_count'] = len(collisions)
        report['planned_collections'] = {name: len(paths) for name, paths in groups.items()}
        if not apply:
            report['status'] = 'dry_run_ready'
            return report

        backup = output / 'CollectionBackups'
        backup.mkdir()
        report['collection_backups'] = []
        for source in sorted((root / 'Saved/Collections').glob('*.collection')):
            shutil.copy2(source, backup / source.name)
            report['collection_backups'].append(str(backup / source.name))
        manager = u.get_editor_subsystem(u.CollectionManagerSubsystem)
        for name, paths in groups.items():
            ref = u.Collection(container='Game', name=name, share_type=u.CollectionShareType.LOCAL)
            before = collection_members(u, manager, ref, allow_missing=True)
            # False may mean every requested object was already a member; the
            # set checks below verify both additions and owner-item retention.
            manager.add_assets_to_collection(ref, [u.SoftObjectPath(path) for path in paths])
            after = collection_members(u, manager, ref)
            if not set(paths).issubset(after) or not before.issubset(after):
                raise RuntimeError('Collection coverage/preservation failed: ' + name)
            report['collections'].append({'name': name, 'requested': len(paths),
                                          'before': len(before), 'after': len(after)})
        applied = ulat.apply(entries, apply=True)
        report['ulat_apply'] = applied
        if applied['status'] not in ('applied', 'unchanged'):
            raise RuntimeError('ULAT apply failed: ' + str(applied['errors']))
        report['verified_rows'] = len(ulat._json_export(u, u.load_asset(ulat.TABLE_PATH)))
        report['all_project_assets_in_native_collections'] = True
        report['status'] = 'applied'
        return report
    except Exception as error:
        report['errors'].append(str(error))
        report['status'] = 'partial' if report['collections'] else 'blocked'
        return report
    finally:
        Path(report['report_path']).write_text(json.dumps(report, indent=2), encoding='utf-8')
        u.log('BUILDING_COLLECTION_REFRESH ' + json.dumps({key: report[key]
              for key in ('status', 'mode', 'errors', 'report_path')}))


if __name__ == '__main__':
    import unreal as u

    result = run(apply='-SSApplyBuildingCollections' in u.SystemLibrary.get_command_line().split())
    if result['status'] not in ('dry_run_ready', 'applied'):
        raise RuntimeError('Building collection refresh failed: ' + result['report_path'])
