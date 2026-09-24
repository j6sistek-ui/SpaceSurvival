"""Install the add-on package into the Blender that runs this script, and record the project root for it.

  blender --background --python Tools/SSLiveLink/install.py

The double-click route is "Install Blender Add-on.cmd" beside this file, which runs this script in every Blender
it finds under Program Files. To try it without touching the real preferences, point BLENDER_USER_RESOURCES,
BLENDER_USER_CONFIG and BLENDER_USER_SCRIPTS at a scratch folder first.

No Blender version is named anywhere in here: the add-on goes into the user scripts folder of whichever
Blender runs the script, so run it once with each version in use (5.1 for the headless tools, 5.2 live).
Arguments after '--' are accepted and ignored, '--blender-version-agnostic' included.

Copies the ss_live_link folder to <user scripts>/addons/ss_live_link/, replacing an earlier copy and
removing the single-file ss_live_link.py older installs left there (two add-ons under one module name
would leave it to chance which one loads). Writes the project and engine roots into Blender's config
folder (the add-on reads them when its own preferences are empty), and enables the add-on in the saved
user preferences. A Blender that is already open picks it up the next time it starts.
"""
from pathlib import Path
from datetime import datetime, timezone
import json
import shutil
import sys

import addon_utils
import bpy

MODULE = 'ss_live_link'
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
source = HERE / MODULE
addons = Path(bpy.utils.user_resource('SCRIPTS', path='addons', create=True))
target = addons / MODULE
config = Path(bpy.utils.user_resource('CONFIG', create=True)) / 'ss_live_link.json'
# Keep a reversible copy before upgrading. It lives outside addons so Blender cannot load it twice.
backup = Path(bpy.utils.user_resource('CONFIG', create=True)) / 'SSLinkBackups' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
backup.mkdir(parents=True)
if target.exists():
    shutil.copytree(target, backup / MODULE)
for previous in (addons / (MODULE + '.py'), config, config.parent / 'userpref.blend'):
    if previous.is_file():
        shutil.copy2(previous, backup / previous.name)

# Without --factory-startup the saved preferences have already loaded whatever copy was installed. Take it
# out of this session first, or enabling below would find the old module in sys.modules and register that.
if MODULE in bpy.context.preferences.addons or MODULE in sys.modules:
    addon_utils.disable(MODULE, default_set=True)
for name in [n for n in sys.modules if n == MODULE or n.startswith(MODULE + '.')]:
    del sys.modules[name]

removed = []
old_file = addons / (MODULE + '.py')
if old_file.exists():
    old_file.unlink()
    removed.append(str(old_file))
for pyc in (addons / '__pycache__').glob(MODULE + '.*.pyc'):
    pyc.unlink()
if target.exists():
    if target.resolve().parent != addons.resolve() or target.name != MODULE:
        raise RuntimeError('Refusing to replace an add-on outside the expected user add-ons directory')
    shutil.rmtree(target)
shutil.copytree(source, target, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))

engine = next((r for r in (r'C:\Program Files\EpicGames2\UE_5.8', r'C:\Program Files\Epic Games\UE_5.8')
               if (Path(r) / 'Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python/remote_execution.py').exists()), '')
config.write_text(json.dumps({'project_root': str(ROOT), 'engine_root': engine}, indent=1), encoding='utf-8')
bpy.ops.preferences.addon_refresh()
bpy.ops.preferences.addon_enable(module=MODULE)
bpy.context.preferences.addons[MODULE].preferences.project_root = str(ROOT)
from ss_live_link import popout
if (ROOT / 'Artifacts/PrefabLibrary/BlenderAssets/build.json').is_file():
    popout.attach_library()
bpy.ops.wm.save_userpref()
enabled = MODULE in bpy.context.preferences.addons and hasattr(bpy.types, 'SSLINK_PT_panel')
print(json.dumps({'installed': str(target), 'files': sorted(p.name for p in target.glob('*.py')), 'removed': removed, 'enabled': enabled,
                  'blender': bpy.app.version_string, 'config': str(config), 'project_root': str(ROOT), 'engine_root': engine}))
if not enabled:
    sys.exit(1)
