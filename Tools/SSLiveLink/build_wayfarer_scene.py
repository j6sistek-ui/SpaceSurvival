"""Build a new Wayfarer .blend without loading, changing or replacing an owner's working file.

Blender --background --factory-startup --python-exit-code 1 --python this.py --
  --project ROOT --output NEW.blend [--input scene.json]
"""
import argparse
import json
from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path(__file__).parent))
import ss_live_link
from ss_live_link import wayfarer

parser = argparse.ArgumentParser()
parser.add_argument('--project', required=True, type=Path)
parser.add_argument('--input', type=Path)
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
if args.output.exists():
    raise FileExistsError(f'Existing working files are preserved: choose a new output, {args.output}')
ss_live_link.core.project_root = lambda: args.project.resolve()
ss_live_link.register()
result = wayfarer.open_snapshot(args.input)
args.output.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(args.output.resolve()), compress=True)
print('SS_WAYFARER_BLEND_OK ' + json.dumps(dict(result, output=str(args.output.resolve()))))
