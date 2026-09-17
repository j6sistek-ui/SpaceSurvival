"""Build the prefab library catalogue and the Blender proxies, headless.

  UnrealEditor-Cmd.exe <project> -unattended -stdout -FullStdOutLogOutput \
      -ExecutePythonScript="Scripts/ExportPrefabCatalog.py" [-- --no-proxies] [--limit N]

Writes Artifacts/PrefabLibrary/catalog.json and Artifacts/PrefabLibrary/proxies/<pack>/<mesh>.glb.
The same thing is available in the editor under SS Prefabs > Rebuild Catalogue. Proxies that already
exist are kept, so a rerun only adds what is new.
"""
from pathlib import Path
import json
import sys

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Content' / 'Python'))
import ss_prefabs  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
limit = int(argv[argv.index('--limit') + 1]) if '--limit' in argv else 0
catalog = ss_prefabs.build_catalog(export_proxies='--no-proxies' not in argv, limit=limit)
summary = {'meshes': len(catalog['meshes']), 'categories': catalog['categories'], 'proxies': sum(1 for m in catalog['meshes'] if 'proxy' in m),
           'proxies_failed': len(catalog['proxies_failed']), 'catalog': str(ss_prefabs.CATALOG)}
u.log('PREFAB_CATALOG ' + json.dumps(summary))
