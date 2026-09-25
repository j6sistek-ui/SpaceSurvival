"""Extend ULAT's StaticMesh palette without touching a level.

Unreal Python: apply(entries, apply=False, roots=()). Entries are asset paths or
dicts with asset_path, optional category (Modular/Prop), and optional type_label.
Only explicit roots are scanned. CLI: --entries FILE [--root /Game/Pack] [--apply].
The JSON file can be a list or an object with entries and roots.

ULAT 1.3.1 stores the palette in ENGINE plugin assets shared across projects.
There is no supported project-specific data-path setting. Collections are level
folders; Actor Blueprints belong in a native Content Browser library instead.
This script preserves existing rows, labels and collections and never changes
plugin source, actors or maps. Reports/backups go to Artifacts/PrefabLibrary.
"""

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


TABLE_PATH = '/UltimateLevelArtTool/Data/DT_MB_ModAssetData'
DATA_PATH = '/UltimateLevelArtTool/Data/DA_MB_ToolData'
EXPECTED_COLUMNS = {'MeshType', 'MeshCategory', 'AssetReference'}


def _object_path(value):
    value = str(value).strip()
    if "'" in value:
        value = value.split("'", 1)[1].rsplit("'", 1)[0]
    if not value.startswith('/') or ':' in value:
        raise ValueError('Expected an Unreal asset path: ' + value)
    if '.' not in value.rsplit('/', 1)[-1]:
        value += '.' + value.rsplit('/', 1)[-1]
    return value


def _classify(path):
    # Caller-supplied labels take precedence over these modest filename groups.
    name = path.rsplit('/', 1)[-1].split('.', 1)[0].lower()
    # Digital/lit window parts still belong with their structural window kit.
    if 'window' in name:
        return 'Modular', 'Buildings and Structure'
    groups = (
        ('Prop', 'Screens and Displays', ('screen', 'monitor', 'display', 'billboard', 'hologram', 'advert', 'signage')),
        ('Prop', 'Light Fixtures', ('light', 'lamp', 'lantern', 'sconce', 'floodlight')),
        ('Prop', 'Furniture and Workstations', ('chair', 'desk', 'table', 'bench', 'sofa', 'shelf', 'shelves', 'workstation', 'console', 'terminal', 'cabinet', 'locker')),
        ('Prop', 'Ships and Vehicles', ('ship', 'shuttle', 'vehicle', 'fighter', 'frigate', 'spaceship', 'drone')),
        ('Modular', 'Buildings and Structure', ('building', 'wall', 'floor', 'roof', 'ceiling', 'door', 'window', 'pillar', 'column', 'beam', 'stair', 'ramp', 'railing', 'corridor', 'platform', 'panel', 'structure')),
    )
    for category, label, terms in groups:
        if any(term in name for term in terms):
            return category, label
    return 'Prop', 'Props and Details'


def _json_export(u, table):
    result = u.DataTableFunctionLibrary.export_data_table_to_json_string(table)
    if isinstance(result, tuple):
        result = next((part for part in result if isinstance(part, str)), None)
    if not isinstance(result, str):
        raise RuntimeError('DataTable JSON export did not return a string')
    rows = json.loads(result)
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise RuntimeError('Unexpected DataTable JSON representation')
    return rows


def _digest(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _backup(u, output, run_id):
    source_dir = Path(u.Paths.convert_relative_path_to_full(u.Paths.engine_plugins_dir())) / 'UltimateLevelArtTool/Content/Data'
    backup_dir = output / 'ULATBackups' / run_id
    records = []
    for name in ('DT_MB_ModAssetData', 'DA_MB_ToolData'):
        if not (source_dir / (name + '.uasset')).is_file():
            raise RuntimeError('Cannot prove installed plugin package backup source: ' + str(source_dir / name))
        for source in sorted(source_dir.glob(name + '.*')):
            if source.suffix.lower() not in ('.uasset', '.uexp', '.ubulk', '.uptnl'):
                continue
            backup_dir.mkdir(parents=True, exist_ok=True)
            destination = backup_dir / source.name
            before = _digest(source)
            shutil.copy2(source, destination)
            if _digest(destination) != before or _digest(source) != before:
                raise RuntimeError('Plugin package changed during backup: ' + str(source))
            records.append({'source': str(source), 'backup': str(destination), 'sha256': before})
    (backup_dir / 'manifest.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
    return records


def apply(entries=(), apply=False, roots=()):
    """Return a report, including errors, without propagating an import failure.

    JSON fill replaces a whole table, so the merge retains every old row and is
    checked before saving. Same-short-name meshes are skipped: ULAT itself uses
    mesh names, not full object paths, for placement/lookups.
    """
    report = {
        'mode': 'apply' if apply else 'dry_run', 'status': 'initializing',
        'scope': 'Engine-global ULAT palette shared across projects',
        'table': TABLE_PATH, 'tool_data': DATA_PATH,
        'added': [], 'skipped': [], 'failed_entries': [], 'errors': [], 'saved_assets': [],
        'backups': [], 'types_added': {'Modular': [], 'Prop': []},
    }
    u = table = data = None
    old_rows = old_modular = old_props = None
    changed_memory = False
    output = None
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid4().hex[:8]
    report['run_id'] = run_id
    try:
        import unreal as u

        output = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())) / 'Artifacts/PrefabLibrary'
        table = u.load_asset(TABLE_PATH)
        data = u.load_asset(DATA_PATH)
        if not table or not data:
            raise RuntimeError('ULAT must be enabled and its native data assets loadable')
        row_struct = u.DataTableFunctionLibrary.get_data_table_row_struct(table)
        if not row_struct or row_struct.get_name() != 'ModularBuildingAssetData':
            raise RuntimeError('Unexpected ULAT DataTable row struct')
        raw_columns = [str(value) for value in u.DataTableFunctionLibrary.get_data_table_column_names(table)]
        export_columns = list(u.DataTableFunctionLibrary.get_data_table_column_export_names(table))
        if set(raw_columns) != EXPECTED_COLUMNS or len(raw_columns) != len(export_columns):
            raise RuntimeError('ULAT schema differs from supported three-column schema')
        columns = dict(zip(raw_columns, export_columns))
        old_rows = _json_export(u, table)
        old_modular = list(data.get_editor_property('modular_mesh_types'))
        old_props = list(data.get_editor_property('prop_mesh_types'))
        report['collections_preserved'] = list(map(str, data.get_editor_property('collections')))
        report['schema'] = {'row_struct': row_struct.get_path_name(), 'columns': columns}
        report['existing_rows'] = len(old_rows)
        report['existing_types'] = {'Modular': list(map(str, old_modular)), 'Prop': list(map(str, old_props))}
        old_paths, short_names, row_names = set(), {}, set()
        for row in old_rows:
            if not all(key in row for key in ['Name', *columns.values()]):
                raise RuntimeError('An existing ULAT row has an unexpected schema')
            row_names.add(str(row['Name']).casefold())
            reference = row[columns['AssetReference']]
            if reference and reference != 'None':
                path = _object_path(reference)
                old_paths.add(path.casefold())
                short_names.setdefault(path.rsplit('.', 1)[-1].casefold(), path)

        registry = u.AssetRegistryHelpers.get_asset_registry()
        requested = list(entries)
        for root in roots:
            if not isinstance(root, str) or not root.startswith('/Game/') or '.' in root:
                raise ValueError('Roots must be explicit /Game/... content folders')
            assets = registry.get_assets_by_path(root, recursive=True)
            if not assets:
                report['skipped'].append({'asset_path': root, 'reason': 'Content root has no registered assets'})
            for asset in assets:
                if str(asset.asset_class_path.asset_name) == 'StaticMesh':
                    requested.append(str(asset.package_name))

        new_rows = list(old_rows)
        seen_paths = set(old_paths)
        for entry in requested:
            try:
                details = {'asset_path': entry} if isinstance(entry, str) else dict(entry)
                path = _object_path(details['asset_path'])
                if path.casefold() in seen_paths:
                    report['skipped'].append({'asset_path': path, 'reason': 'Already registered or duplicate input'})
                    continue
                # This installed UE Python binding exposes the legacy FName
                # overload even though the C++ API also has SoftObjectPath.
                asset_data = registry.get_asset_by_object_path(u.Name(path))
                if not asset_data.is_valid() or str(asset_data.asset_class_path.asset_name) != 'StaticMesh':
                    report['skipped'].append({'asset_path': path, 'reason': 'Missing asset or not a StaticMesh; Actor Blueprints stay in native library'})
                    continue
                short_name = str(asset_data.asset_name)
                if short_name.casefold() in short_names or short_name.casefold() in row_names:
                    report['skipped'].append({'asset_path': path, 'reason': 'ULAT short-name collision', 'existing': short_names.get(short_name.casefold(), 'Existing row name')})
                    continue
                category, label = _classify(path)
                category = str(details.get('category', category))
                label = str(details.get('type_label', label)).strip()
                if category not in ('Modular', 'Prop') or not label or len(label) > 96 or any(ord(char) < 32 for char in label):
                    raise ValueError('Invalid category or type_label')
                if not re.fullmatch(r'[A-Za-z0-9_]+', short_name):
                    report['skipped'].append({'asset_path': path, 'reason': 'Nonstandard mesh name; manual ULAT import required'})
                    continue
                new_rows.append({'Name': short_name, columns['MeshType']: label,
                                 columns['MeshCategory']: category, columns['AssetReference']: path})
                report['added'].append({'asset_path': path, 'row_name': short_name, 'category': category, 'type_label': label})
                seen_paths.add(path.casefold())
                short_names[short_name.casefold()] = path
                row_names.add(short_name.casefold())
                labels = report['existing_types'][category] + report['types_added'][category]
                if label.casefold() not in {value.casefold() for value in labels}:
                    report['types_added'][category].append(label)
            except Exception as error:
                report['failed_entries'].append({'entry': str(entry), 'reason': str(error)})
                report['errors'].append('Entry inspection failed for ' + str(entry) + ': ' + str(error))

        report['planned_rows'] = len(new_rows)
        if report['failed_entries']:
            raise RuntimeError('Entry inspection had errors; palette mutation and successful dry-run status are blocked')
        if not apply:
            report['status'] = 'dry_run_ready'
        elif not report['added']:
            report['status'] = 'unchanged'
        else:
            targets = {TABLE_PATH.casefold(), DATA_PATH.casefold()}
            dirty = [package.get_path_name() for package in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
            if any(path.casefold() in targets for path in dirty):
                raise RuntimeError('ULAT target has unsaved edits; preserve/save those before applying')
            report['backups'] = _backup(u, output, run_id)
            snapshot = output / 'ULATBackups' / run_id / 'original_data.json'
            snapshot.write_text(json.dumps({'rows': old_rows, 'types': report['existing_types'], 'collections': report['collections_preserved']}, indent=2), encoding='utf-8')
            changed_memory = True
            if not u.DataTableFunctionLibrary.fill_data_table_from_json_string(table, json.dumps(new_rows), row_struct):
                raise RuntimeError('ULAT JSON import failed; no save attempted')
            data.set_editor_property('modular_mesh_types', old_modular + [u.Name(value) for value in report['types_added']['Modular']])
            data.set_editor_property('prop_mesh_types', old_props + [u.Name(value) for value in report['types_added']['Prop']])
            current = _json_export(u, table)
            by_name = {row['Name']: row for row in current}
            if len(current) != len(new_rows) or any(by_name.get(row['Name']) != row for row in old_rows):
                raise RuntimeError('Existing row preservation or row-count verification failed')
            for added in report['added']:
                row = by_name[added['row_name']]
                if (str(row[columns['MeshType']]) != added['type_label']
                        or _object_path(row[columns['AssetReference']]).casefold() != added['asset_path'].casefold()
                        or str(row[columns['MeshCategory']]).split('::')[-1] != added['category']):
                    raise RuntimeError('New row verification failed: ' + added['row_name'])
            for prop, before, category in (('modular_mesh_types', old_modular, 'Modular'), ('prop_mesh_types', old_props, 'Prop')):
                expected = list(map(str, before)) + report['types_added'][category]
                if list(map(str, data.get_editor_property(prop))) != expected:
                    raise RuntimeError('Type label preservation failed: ' + prop)
            if list(map(str, data.get_editor_property('collections'))) != report['collections_preserved']:
                raise RuntimeError('ULAT collection preservation failed')
            for asset in (table, data):
                if not u.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False):
                    raise RuntimeError('Failed to save ' + asset.get_path_name())
                report['saved_assets'].append(asset.get_path_name())
            report['verified_rows'] = len(current)
            report['status'] = 'applied'
            report['refresh'] = 'Close and reopen the ULAT tool window to rebuild its palette widgets.'
    except Exception as error:
        report['errors'].append(str(error))
        report['status'] = 'partial_save' if report['saved_assets'] else 'blocked'
        if changed_memory and not report['saved_assets']:
            try:
                restored = u.DataTableFunctionLibrary.fill_data_table_from_json_string(table, json.dumps(old_rows), row_struct)
                data.set_editor_property('modular_mesh_types', old_modular)
                data.set_editor_property('prop_mesh_types', old_props)
                report['memory_restored'] = bool(restored and _json_export(u, table) == old_rows)
            except Exception as restore_error:
                report['memory_restored'] = False
                report['errors'].append('In-memory restore failed: ' + str(restore_error))
        if report['saved_assets']:
            report['recovery'] = 'Partial save: inspect/recover both target assets from backups before another apply; no automatic on-disk rollback attempted.'
    finally:
        if output:
            try:
                output.mkdir(parents=True, exist_ok=True)
                report_path = output / ('ULAT-' + run_id + '.json')
                report['report_path'] = str(report_path)
                report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
            except Exception as error:
                report['errors'].append('Report write failed: ' + str(error))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--entries', type=Path)
    parser.add_argument('--root', action='append', default=[])
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    payload = json.loads(args.entries.read_text(encoding='utf-8-sig')) if args.entries else []
    entries = payload.get('entries', []) if isinstance(payload, dict) else payload
    roots = args.root + (payload.get('roots', []) if isinstance(payload, dict) else [])
    report = apply(entries, apply=args.apply, roots=roots)
    print(json.dumps({key: report[key] for key in ('status', 'mode', 'errors', 'saved_assets', 'report_path') if key in report}))
    return 0 if report['status'] in ('dry_run_ready', 'unchanged', 'applied') else 1


if __name__ == '__main__':
    sys.exit(main())
