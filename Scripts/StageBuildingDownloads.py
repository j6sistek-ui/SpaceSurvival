"""Stage requested native Content only. Default dry run; never overwrite different bytes."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import zipfile


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def run(manifest, project, groups, apply=False):
    data = json.loads(manifest.read_text(encoding='utf-8'))
    project = project.resolve()
    content = (project / 'Content').resolve()
    source_root = Path(data['source_directory']).resolve()
    plan = {}
    archives = {}
    try:
        for row in data['entries']:
            if row['group'] not in groups:
                continue
            rel = PurePosixPath(row['destination_relative'])
            if rel.is_absolute() or '..' in rel.parts or rel.parts[0] != 'Content':
                raise ValueError('Invalid destination: ' + str(rel))
            if rel.suffix.lower() not in ('.uasset', '.umap', '.uexp', '.ubulk'):
                raise ValueError('Not native Content: ' + str(rel))
            source = Path(row['source_path']).resolve()
            if not source.is_relative_to(source_root):
                raise ValueError('Source outside owner-specified download folder')
            target = project.joinpath(*rel.parts).resolve()
            if not target.is_relative_to(content):
                raise ValueError('Destination leaves private project Content')
            if row['source_kind'] == 'zip':
                archive = archives.setdefault(str(source), zipfile.ZipFile(source)) if str(source) not in archives else archives[str(source)]
                entry = PurePosixPath(row['archive_entry'])
                if entry.is_absolute() or '..' in entry.parts:
                    raise ValueError('Unsafe archive entry')
                raw = archive.read(row['archive_entry'])
                digest = hashlib.sha256(raw).hexdigest()
            else:
                digest = sha(source)
            if str(target) in plan and plan[str(target)]['sha256'] != digest:
                raise ValueError('Conflicting source packages: ' + str(rel))
            if target.exists() and sha(target) != digest:
                raise ValueError('Refusing to overwrite existing different package: ' + str(target))
            plan[str(target)] = {'row': row, 'sha256': digest, 'exists': target.exists()}
        result = {'mode': 'apply' if apply else 'dry-run', 'groups': sorted(groups),
                  'unique_packages': len(plan), 'new_bytes': sum(r['row']['bytes'] for r in plan.values() if not r['exists']),
                  'written': [], 'already_identical': sum(r['exists'] for r in plan.values())}
        if apply:
            for path, item in plan.items():
                if item['exists']:
                    continue
                target = Path(path)
                target.parent.mkdir(parents=True, exist_ok=True)
                row = item['row']
                if row['source_kind'] == 'zip':
                    with archives[str(Path(row['source_path']).resolve())].open(row['archive_entry']) as src, target.open('xb') as dst:
                        shutil.copyfileobj(src, dst)
                else:
                    with Path(row['source_path']).open('rb') as src, target.open('xb') as dst:
                        shutil.copyfileobj(src, dst)
                if sha(target) != item['sha256']:
                    raise ValueError('Copied package checksum mismatch: ' + path)
                result['written'].append({'path': path, 'sha256': item['sha256']})
        output = project / 'Artifacts/BuildingLibrary'
        output.mkdir(parents=True, exist_ok=True)
        label = '-'.join(sorted(groups)) + ('-apply' if apply else '-dry-run')
        (output / ('staging-' + label + '.json')).write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps({k: v if k != 'written' else len(v) for k, v in result.items()}))
    finally:
        for archive in archives.values():
            archive.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--groups', nargs='+', required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    run(args.manifest, args.project, set(args.groups), args.apply)
