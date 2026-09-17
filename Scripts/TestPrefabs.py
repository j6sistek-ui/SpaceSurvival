"""Self-test of the prefab library and live-link endpoint, headless.

  UnrealEditor-Cmd.exe <project> -unattended -stdout -FullStdOutLogOutput -DisablePlugins=UAssetBrowser \
      "-ExecutePythonScript=<abs path>/Scripts/TestPrefabs.py"

The script path must be absolute: a relative one resolves against the engine's Binaries folder (docs/BUILD_RUN.md).

Runs in the editor's start-up level without saving it: places parts, saves them as a prefab, places the
prefab, drives the live-link endpoint through create, move, pull and remove, and checks the transform
round trips. Prints PREFABS_SELFTEST_OK with the numbers, or raises.
"""
from pathlib import Path
import json
import math
import sys

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Content' / 'Python'))
import ss_prefabs  # noqa: E402


def rows_from_rotator(loc, rot, scale):
    """UE's FScaleRotationTranslationMatrix in plain Python; the Blender add-on carries the same formula."""
    pitch, yaw, roll = (math.radians(v) for v in rot)
    sp, cp, sy, cy, sr, cr = math.sin(pitch), math.cos(pitch), math.sin(yaw), math.cos(yaw), math.sin(roll), math.cos(roll)
    rows = [[cp * cy, cp * sy, sp, 0.0],
            [sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, -sr * cp, 0.0],
            [-(cr * sp * cy + sr * sy), cy * sr - cr * sp * sy, cr * cp, 0.0],
            [loc[0], loc[1], loc[2], 1.0]]
    for i in range(3):
        rows[i] = [v * scale[i] for v in rows[i]]
    return rows


# The rotator formula the Blender side uses must agree with the engine to the last digit that matters.
for loc, rot, scale in (([0, 0, 0], [0, 90, 0], [1, 1, 1]), ([10, 20, 30], [30, -45, 12], [1, 2, 3]), ([-5, 0, 2], [-80, 170, -170], [0.5, 0.5, 0.5])):
    mine = rows_from_rotator(loc, rot, scale)
    engine = ss_prefabs.matrix_rows(u.Transform(u.Vector(*loc), u.Rotator(roll=rot[2], pitch=rot[0], yaw=rot[1]), u.Vector(*scale)))
    for r in range(4):
        for c in range(4):
            assert abs(mine[r][c] - engine[r][c]) < 1e-4, (loc, rot, scale, r, c, mine[r][c], engine[r][c])
result = ss_prefabs.selftest()
result['rotator_formula'] = 'matches engine'
u.log('PREFABS_SELFTEST_OK ' + json.dumps(result))
