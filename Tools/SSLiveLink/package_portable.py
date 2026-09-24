"""Create a private offline library ZIP, containing only referenced previews and add-on files."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import zipfile


def contained(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f'Library entry escapes its folder: {relative}')
    return path


@contextmanager
def completed_archive(output, size):
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError('Choose a new export filename; existing libraries are kept')
    if shutil.disk_usage(output.parent).free < size + 256 * 1024 ** 2:
        raise RuntimeError(f'Export needs about {size / 1024 ** 3:.1f} GiB of free space plus 256 MiB headroom')
    handle, name = tempfile.mkstemp(prefix=output.stem + '-', suffix='.partial', dir=output.parent)
    os.close(handle)
    partial = Path(name)
    try:
        with zipfile.ZipFile(partial, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=3) as archive:
            yield archive
        if output.exists():
            raise FileExistsError('Another export already created this filename')
        partial.rename(output)
    finally:
        partial.unlink(missing_ok=True)


def package(project, code, native, output):
    lib = project / 'Artifacts/PrefabLibrary'
    catalog = json.loads((lib / 'catalog.json').read_text(encoding='utf-8'))
    sent = json.loads((lib / 'sent.json').read_text(encoding='utf-8')) if (lib / 'sent.json').exists() else []
    known = {r['asset'] for r in catalog['meshes']}
    rows = list({r['asset']: r for r in catalog['meshes'] + [r for r in sent if r['asset'] not in known]}.values())
    files = {'Artifacts/PrefabLibrary/catalog.json': lib / 'catalog.json'}
    if sent:
        files['Artifacts/PrefabLibrary/sent.json'] = lib / 'sent.json'
    missing = []
    for row in rows:
        for field in ('proxy', 'thumb'):
            relative = row.get(field)
            if not relative:
                continue
            path = contained(lib, relative)
            if path.is_file():
                files['Artifacts/PrefabLibrary/' + Path(relative).as_posix()] = path
            else:
                missing.append({'asset': row['asset'], 'missing': field})
    for path in (code / 'Tools/SSLiveLink').rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts and path.suffix in ('.py', '.cmd', '.json'):
            files[path.relative_to(code).as_posix()] = path
    for path in (project / 'Prefabs').rglob('*.json'):
        files[path.relative_to(project).as_posix()] = path
    if not (native / 'build.json').is_file():
        raise RuntimeError('Prepare the large Blender library before packaging it')
    built = json.loads((native / 'build.json').read_text(encoding='utf-8'))
    digest = hashlib.sha256()
    for name in ('catalog.json', 'sent.json'):
        if (lib / name).is_file():
            digest.update((lib / name).read_bytes())
    if built.get('catalog_digest') != digest.hexdigest():
        raise RuntimeError('The catalog changed. Wait for Prepare Large Library to finish, then export again')
    for relative in ['blender_assets.cats.txt', 'build.json'] + [v['file'] for v in built['entries'].values()]:
        path = contained(native, relative)
        if not path.is_file():
            raise RuntimeError(f'Prepared library is incomplete: {relative}')
        files['Artifacts/PrefabLibrary/BlenderAssets/' + relative] = path
    stamps = {name: (path.stat().st_size, path.stat().st_mtime_ns) for name, path in files.items()}
    hashes = {}
    for name, path in files.items():
        with path.open('rb') as source:
            hashes[name] = hashlib.file_digest(source, 'sha256').hexdigest()
    manifest = {'schema_version': 1, 'assets': len(rows), 'missing_previews': missing, 'files': hashes}
    with completed_archive(output, sum(s[0] for s in stamps.values())) as archive:
        for name, path in files.items():
            archive.write(path, 'SpaceSurvivalLibrary/' + name,
                          compress_type=zipfile.ZIP_STORED if path.suffix in ('.blend', '.png') else zipfile.ZIP_DEFLATED)
            if (path.stat().st_size, path.stat().st_mtime_ns) != stamps[name]:
                raise RuntimeError('Library changed during export. Wait for refresh to finish and retry')
        archive.writestr('SpaceSurvivalLibrary/SSPortableLibrary.json', json.dumps(manifest, indent=2))
        archive.writestr('SpaceSurvivalLibrary/README.txt', '''SpaceSurvival offline Blender library (private copy of owned assets)

1. Extract the whole SpaceSurvivalLibrary folder; keep its structure intact.
2. On Windows with Blender installed, run Tools/SSLiveLink/Install Blender Add-on.cmd.
   On other systems, zip Tools/SSLiveLink/ss_live_link, install that ZIP in Blender,
   and set SS Link's Project root to this extracted SpaceSurvivalLibrary folder.
3. In Blender: N sidebar > SS Link > Parts library > Pop Out Library.
   Move that window to your second screen. Browse categories, search, drag objects.

Unreal is not needed for browsing or arranging. The library contains placement previews,
not the original Unreal materials or working gameplay Blueprints. The large browser
includes actual exported meshes only. Your .blend embeds placed meshes and simple surface edits.

For later updates, use SS Link > Export Library on the desktop, then Import Library
on the laptop. Import preserves the old snapshot and the scene already open.

Save your scene as .blend. Copy that file back to your desktop and open it there with
SS Link 0.4.0 or later configured for the original Unreal project. The /Game asset
references stay the same. Push Selected/Apply is explicit; merely opening a file
does not change Unreal. Keep Live off until you deliberately want synchronization.
For separate review, Export Placement + Materials JSON includes simple surface edits.
New custom meshes and external textures need Send to Unreal and File > External Data >
Pack Resources as appropriate. Vendor assets stay private; do not publicly distribute.
''')
    return {'zip': str(output), 'assets': len(rows), 'files': len(files), 'missing': missing}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--code-root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--native-library', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(package(args.project, args.code_root, args.native_library, args.output)))
