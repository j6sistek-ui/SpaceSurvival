"""Incremental local catalog refresh while the editor is idle; one changed mesh per tick.

Enabled by the SS Link Auto-refresh Library checkbox via a local marker. Does not save levels.
"""
import time
import unreal as u
import ss_prefabs

_state = {'handle': None, 'next_scan': 0.0, 'stamp': None, 'steps': None, 'busy': False}
_manual = {'id': '', 'status': 'idle', 'processed': 0, 'total': 0, 'error': ''}


def request_manual_refresh():
    """Queue one local export without enabling recurring scans or saving a level."""
    levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
    if levels is None or levels.is_in_play_in_editor():
        raise RuntimeError('Stop Play before rescanning the library')
    if _manual['status'] in ('queued', 'running'):
        return dict(_manual)
    _manual.update(id=str(time.monotonic_ns()), status='queued', processed=0,
                   total=len(ss_prefabs._static_meshes()), error='')
    _state['next_scan'] = 0.0
    return dict(_manual)


def manual_refresh_status(job_id):
    if job_id != _manual['id']:
        raise RuntimeError('Library rescan identity changed; press Rescan again')
    return dict(_manual)


def tick(_delta):
    # Export/thumbnail work pumps Slate, which can call this callback again
    # before next(steps) returns. Keep the same iterator alive until it yields.
    if _state['busy']:
        return
    _state['busy'] = True
    try:
        marker = ss_prefabs.LIBRARY / 'auto-refresh.enabled'
        manual = _manual['status'] in ('queued', 'running')
        if not marker.exists() and not manual:
            _state['steps'] = None
            _state['stamp'] = None
            return
        levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
        if levels is None or levels.is_in_play_in_editor():
            return
        if _state['steps'] is not None:
            # Cached rows should not each cost an entire editor frame. An actual
            # export remains indivisible; stop after it exceeds this time budget.
            deadline = time.monotonic() + 0.008
            for _ in range(100 if manual else 1):
                try:
                    result = next(_state['steps'])
                    if manual:
                        _manual['status'] = 'running'
                        _manual['processed'] = min(_manual['processed'] + 1, _manual['total'])
                    if isinstance(result, dict) and manual:
                        failures = result.get('proxies_failed', [])
                        _manual.update(status='failed' if failures else 'complete',
                                       error=f'{len(failures)} mesh exports failed' if failures else '')
                except StopIteration:
                    _state['steps'] = None
                    _state['next_scan'] = time.monotonic() + 30.0
                    if manual and _manual['status'] != 'failed':
                        _manual.update(status='complete', processed=_manual['total'])
                    break
                if time.monotonic() >= deadline:
                    break
            return
        if time.monotonic() < _state['next_scan']:
            return
        _state['next_scan'] = time.monotonic() + 30.0
        registry = u.AssetRegistryHelpers.get_asset_registry()
        if registry.is_loading_assets():
            return
        stamp = tuple((p, ss_prefabs._source_stamp(p)) for p in ss_prefabs._static_meshes())
        if stamp != _state['stamp'] or manual:
            _state['stamp'] = stamp
            _state['steps'] = ss_prefabs.catalog_steps()
    except Exception as exc:
        _state.update(steps=None, stamp=None, next_scan=time.monotonic() + 60.0)
        if _manual['status'] in ('queued', 'running'):
            _manual.update(status='failed', error=str(exc))
        u.log_warning(f'SS library auto-refresh paused: {exc}')
    finally:
        _state['busy'] = False


def register():
    # Editor -game may expose ToolMenus without a LevelEditorSubsystem. It must
    # not run a catalog scan (or emit a warning every frame) during gameplay.
    if (_state['handle'] is None and u.ToolMenus.get() is not None
            and u.get_editor_subsystem(u.LevelEditorSubsystem) is not None):
        _state['handle'] = u.register_slate_post_tick_callback(tick)


def unregister():
    if _state['handle'] is not None:
        u.unregister_slate_post_tick_callback(_state['handle'])
        _state['handle'] = None
