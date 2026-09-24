"""Incremental local catalog refresh while the editor is idle; one changed mesh per tick.

Enabled by the SS Link Auto-refresh Library checkbox via a local marker. Does not save levels.
"""
import time
import unreal as u
import ss_prefabs

_state = {'handle': None, 'next_scan': 0.0, 'stamp': None, 'steps': None}


def tick(_delta):
    marker = ss_prefabs.LIBRARY / 'auto-refresh.enabled'
    if not marker.exists():
        _state['steps'] = None
        return
    try:
        if u.get_editor_subsystem(u.LevelEditorSubsystem).is_in_play_in_editor():
            return
        if _state['steps'] is not None:
            try:
                next(_state['steps'])
            except StopIteration:
                _state['steps'] = None
                _state['next_scan'] = time.monotonic() + 30.0
            return
        if time.monotonic() < _state['next_scan']:
            return
        _state['next_scan'] = time.monotonic() + 30.0
        registry = u.AssetRegistryHelpers.get_asset_registry()
        if registry.is_loading_assets():
            return
        stamp = tuple((p, ss_prefabs._source_stamp(p)) for p in ss_prefabs._static_meshes())
        if stamp != _state['stamp']:
            _state['stamp'] = stamp
            _state['steps'] = ss_prefabs.catalog_steps()
    except Exception as exc:
        _state.update(steps=None, stamp=None, next_scan=time.monotonic() + 60.0)
        u.log_warning(f'SS library auto-refresh paused: {exc}')


def register():
    if _state['handle'] is None and u.ToolMenus.get() is not None:
        _state['handle'] = u.register_slate_post_tick_callback(tick)


def unregister():
    if _state['handle'] is not None:
        u.unregister_slate_post_tick_callback(_state['handle'])
        _state['handle'] = None
