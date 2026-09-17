"""Editor start-up: register the SS Prefabs menu (prefab library, parts catalogue, Blender live link).

The Python plugin runs every init_unreal.py it finds on the script path when the editor starts,
including in commandlets, where there is no menu bar; that case is skipped quietly.
"""
import unreal

try:
    import ss_prefabs
    if unreal.ToolMenus.get() is not None:
        ss_prefabs.register_menus()
except Exception as e:  # start-up must never fail the editor over a menu
    unreal.log_warning(f'SSPrefabs: menus not registered ({e})')
