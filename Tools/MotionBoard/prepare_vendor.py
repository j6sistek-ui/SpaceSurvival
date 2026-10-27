"""Fetch pinned MIT Three.js browser files into the ignored private library."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[2] / 'SourceAssets' / 'MotionBoard' / 'vendor'
BASE = 'https://raw.githubusercontent.com/mrdoob/three.js/r180/'
FILES = ['build/three.module.js', 'build/three.core.js',
         'examples/jsm/loaders/GLTFLoader.js', 'examples/jsm/controls/OrbitControls.js',
         'examples/jsm/loaders/FBXLoader.js', 'examples/jsm/libs/fflate.module.js',
         'examples/jsm/curves/NURBSCurve.js', 'examples/jsm/curves/NURBSUtils.js',
         'examples/jsm/utils/BufferGeometryUtils.js', 'examples/jsm/utils/SkeletonUtils.js', 'LICENSE']
EXPECTED = dict(zip(FILES, [
    'c8211c69345d2e9949dc7a8ac969380497aa0600a5a8ac6a459c8cd02dd9cb8a',
    'eb077d2417f61d3e6d9264c317cabc4ea35769ed6b0ab533067292a550784c20',
    '67ac5551fdafa6e349bd80c8f8e5e39c136d6b2fb1ad647db9abb21dc86f9e4a',
    'b97879c748170baadeb3fb84cea1ffdf4674e283dc06042f34e2acb95a76042c',
    'd97724a6bea228003e02c64651d969a9a62003a00be314ef6995c390116f547d',
    '209a4412eb48ce609edb4391992a792ffcc3983d30ee7e2b0b89a8c470f3cd8a',
    'bef2607618a7778455e71a1f0bd206951c382d313e2e245808cc7d3533d60fb6',
    'c6bd7c4137d585098923f189687898ea3e8762ea3ecbe255d749a56353894379',
    'fda7e946b8e0b5ab39b779206589e7a1079a22eb24efb89d7223e03fdfb1f751',
    '0761b1e003917b215d25dd81439d854b36034b5a57ce84c2cfe3b02428d7b253',
    'bfe119ea4fd413f5f7ca3fcd63adb0c4a073ed39daa2fe7d3e6b769e21272601',
]))
FBX = 'examples/jsm/loaders/FBXLoader.js'
PATCH = Path(__file__).with_name('fbx_r180_patch.json')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def patch_loader(data, recipe):
    """Accept exact upstream or exact patched bytes; never guess at a fork."""
    if recipe['upstreamSha256'] != EXPECTED[FBX]:
        raise ValueError('Patch recipe does not target the pinned r180 loader')
    current = digest(data)
    if current == recipe['patchedSha256']:
        return data
    if current != recipe['upstreamSha256']:
        raise ValueError(f'Unknown FBXLoader bytes: {current}; nothing was written')
    text = data.decode('utf-8')
    for edit in recipe['patches']:
        if text.count(edit['old']) != 1:
            raise ValueError(f"Patch anchor is not unique: {edit['name']}")
        text = text.replace(edit['old'], edit['new'], 1)
    patched = text.encode('utf-8')
    if digest(patched) != recipe['patchedSha256']:
        raise ValueError('Patched loader hash mismatch; nothing was written')
    return patched


def download(name):
    with urllib.request.urlopen(BASE + name, timeout=30) as response:
        return response.read()


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f'.{path.name}.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def prepare(root=ROOT, fetch=download, check=False):
    """Preflight every dependency before any file or provenance mutation."""
    root = Path(root)
    patch_bytes = PATCH.read_bytes()
    recipe = json.loads(patch_bytes)
    records = []
    prepared = {}
    originals = {}
    for name in FILES:
        path = root / name
        originals[name] = path.read_bytes() if path.exists() else None
        data = originals[name] if originals[name] is not None else fetch(name)
        if name == FBX:
            data = patch_loader(data, recipe)
        elif digest(data) != EXPECTED[name]:
            raise ValueError(f'Unknown r180 dependency bytes: {name}; nothing was written')
        prepared[name] = data
        record = {'file': name, 'source': BASE + name, 'bytes': len(data),
                  'sha256': digest(data), 'upstreamSha256': EXPECTED[name]}
        if name == FBX:
            record.update({'compatibilityPatch': PATCH.name, 'patchSha256': digest(patch_bytes),
                           'limitations': recipe['limitations']})
        records.append(record)
    if not check:
        # Refuse to overwrite a file changed while the other inputs were read.
        for name in FILES:
            path = root / name
            current = path.read_bytes() if path.exists() else None
            if current != originals[name]:
                raise ValueError(f'Vendor file changed during preflight: {name}')
        for name, data in prepared.items():
            if data != originals[name]:
                atomic_write(root / name, data)
        provenance = json.dumps({'revision': 'r180', 'license': 'MIT', 'files': records}, indent=2).encode('utf-8')
        atomic_write(root / 'provenance.json', provenance)
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--check', action='store_true', help='Validate without writing vendor files')
    args = parser.parse_args()
    records = prepare(args.root, check=args.check)
    print(f"{'Validated' if args.check else 'Prepared'} {len(records)} pinned browser files in {args.root}")


if __name__ == '__main__':
    main()
