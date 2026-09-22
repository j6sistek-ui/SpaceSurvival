"""Build native Blender assets from the existing SS catalog, without opening Unreal.

Run in a background Blender: --python this.py -- --project ROOT [--output DIR].
The working .blend and user preferences are never loaded or saved.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import uuid

import bpy

sys.path.insert(0, str(Path(__file__).parent))
from ss_live_link import core, library

NAMESPACE = uuid.UUID('dc01c7de-068a-49c6-b6f5-6a47e5f77724')


def catalog_id(path):
    return str(uuid.uuid5(NAMESPACE, path))


def build(root, output):
    output = output.resolve()
    core.project_root = lambda: root
    data = core.load_catalog(force=True)
    known = {r['asset'] for r in data['meshes']}
    rows = list(data['meshes']) + [r for r in core.read_sent() if r['asset'] not in known]
    rows = list({r['asset']: r for r in rows}.values())
    core.teach_sent(rows)
    output.mkdir(parents=True, exist_ok=True)
    chunks = output / 'Assets'
    chunks.mkdir(exist_ok=True)
    previous_file = output / 'build.json'
    previous = json.loads(previous_file.read_text()).get('entries', {}) if previous_file.exists() else {}
    entries = {}
    catalogs = {'SpaceSurvival'}
    assets, missing = set(), []
    digest = hashlib.sha256()
    for name in ('catalog.json', core.SENT):
        file = core.library_dir() / name
        if file.is_file():
            digest.update(file.read_bytes())
    for row in rows:
        if not row.get('proxy') or not (core.library_dir() / row['proxy']).is_file():
            missing.append(row['asset'])
            continue  # never present a bounds box as a real library mesh
        category = row.get('category', 'Misc').replace('/', '-')
        group = row.get('group') or library.group_of(category)
        path = f'SpaceSurvival/{group}/{category}'
        catalogs.update((f'SpaceSurvival/{group}', path))
        filename = hashlib.sha256(row['asset'].encode()).hexdigest()[:24] + '.blend'
        fingerprint = hashlib.sha256(json.dumps(row, sort_keys=True).encode())
        for field in ('proxy', 'thumb'):
            source = core.library_dir() / row.get(field, '')
            if source.is_file():
                stat = source.stat()
                fingerprint.update(f'{stat.st_size}:{stat.st_mtime_ns}'.encode())
        digest_key = fingerprint.hexdigest()
        entries[row['asset']] = {'file': 'Assets/' + filename, 'digest': digest_key}
        if previous.get(row['asset']) == entries[row['asset']] and (chunks / filename).is_file():
            continue
        obj = core.add_part(row['asset'])
        obj.location = (0, 0, 0)
        del obj[core.PROP_LINK]  # each placement gets a new link, never the library's ID
        obj.asset_mark()
        obj.asset_data.catalog_id = catalog_id(path)
        obj.asset_data.description = f"{row.get('pack', '')} | Placement preview"
        for tag in (group, category, row.get('pack', ''), 'Placement preview'):
            if tag:
                obj.asset_data.tags.new(tag)
        thumb = core.library_dir() / row.get('thumb', '')
        if thumb.is_file():
            with bpy.context.temp_override(id=obj):
                bpy.ops.ed.lib_id_load_custom_preview(filepath=str(thumb))
        assets.add(obj)
        # One asset per file: refresh only changed parts and load only parts the user places.
        temp = chunks / (filename + '.pending')
        bpy.data.libraries.write(str(temp), {obj}, fake_user=True, compress=True)
        temp.replace(chunks / filename)
    lines = ['# Blender Asset Catalog Definition File', 'VERSION 1', '']
    for path in sorted(catalogs):
        lines.append(f'{catalog_id(path)}:{path}:{path.rsplit("/", 1)[-1]}')
    (output / 'blender_assets.cats.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    result = {'assets': len(entries), 'rebuilt': len(assets), 'entries': entries, 'unavailable_meshes': missing,
              'schema_version': 1, 'catalog_digest': digest.hexdigest()}
    pending_manifest = output / 'build.pending.json'
    pending_manifest.write_text(json.dumps(result, indent=2), encoding='utf-8')
    pending_manifest.replace(output / 'build.json')
    # Remove only prior generated files named in our own manifest, after the replacement is complete.
    for old in previous.values():
        if old['file'] not in {e['file'] for e in entries.values()}:
            stale = (output / old['file']).resolve()
            if stale.is_relative_to(chunks.resolve()) and stale.suffix == '.blend':
                stale.unlink(missing_ok=True)
    print('SS_ASSET_LIBRARY_OK ' + json.dumps({k: v for k, v in result.items() if k != 'entries'}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', required=True)
    parser.add_argument('--output')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    root = Path(args.project).resolve()
    build(root, Path(args.output) if args.output else root / 'Artifacts/PrefabLibrary/BlenderAssets')
