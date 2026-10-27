"""Fetch pinned MIT Three.js browser files into the ignored private library."""
from pathlib import Path
import hashlib
import json
import urllib.request

ROOT = Path(__file__).resolve().parents[2] / 'SourceAssets' / 'MotionBoard' / 'vendor'
BASE = 'https://raw.githubusercontent.com/mrdoob/three.js/r180/'
FILES = ['build/three.module.js', 'build/three.core.js',
         'examples/jsm/loaders/GLTFLoader.js', 'examples/jsm/controls/OrbitControls.js',
         'examples/jsm/loaders/FBXLoader.js', 'examples/jsm/libs/fflate.module.js',
         'examples/jsm/curves/NURBSCurve.js', 'examples/jsm/curves/NURBSUtils.js',
         'examples/jsm/utils/BufferGeometryUtils.js', 'examples/jsm/utils/SkeletonUtils.js', 'LICENSE']


def main():
    records = []
    for name in FILES:
        path = ROOT / name
        if not path.exists():
            with urllib.request.urlopen(BASE + name, timeout=30) as response:
                data = response.read()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        data = path.read_bytes()
        records.append({'file': name, 'source': BASE + name, 'bytes': len(data),
                        'sha256': hashlib.sha256(data).hexdigest()})
    (ROOT / 'provenance.json').write_text(json.dumps({'revision': 'r180', 'license': 'MIT', 'files': records}, indent=2))
    print(f'Prepared {len(records)} pinned browser files in {ROOT}')


if __name__ == '__main__':
    main()
