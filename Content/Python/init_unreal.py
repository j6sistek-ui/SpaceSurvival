"""Editor start-up: register the SS Prefabs menu (prefab library, parts catalogue, Blender live link).

The Python plugin runs every init_unreal.py it finds on the script path when the editor starts,
including in commandlets, where there is no menu bar; that case is skipped quietly.

ss_send (Send to Unreal) and ss_scenes (Open Scene / Apply) are optional: when the module is in this
folder its register() is called, when it is not nothing is said. Their register() also runs in
commandlets, so it checks unreal.ToolMenus.get() itself before touching a menu.
"""
import importlib

import unreal

try:
    import ss_prefabs
    if unreal.ToolMenus.get() is not None:
        ss_prefabs.register_menus()
except Exception as e:  # start-up must never fail the editor over a menu
    unreal.log_warning(f'SSPrefabs: menus not registered ({e})')

for _name in ('ss_send', 'ss_scenes', 'ss_catalog_refresh'):
    try:
        _module = importlib.import_module(_name)
    except ImportError as e:
        # Absent is fine. Present but failing on an import of its own is a fault worth a line in the log.
        if e.name != _name:
            unreal.log_warning(f'SSPrefabs: {_name} not loaded ({e})')
        continue
    except Exception as e:
        unreal.log_warning(f'SSPrefabs: {_name} not loaded ({e})')
        continue
    try:
        if hasattr(_module, 'register'):
            _module.register()
    except Exception as e:  # same rule as above: a feature must never fail the editor's start-up
        unreal.log_warning(f'SSPrefabs: {_name} not registered ({e})')
