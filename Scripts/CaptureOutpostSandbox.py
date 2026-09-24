"""Capture the actual authored outpost map without changing its lighting.

Run ONLY in a dedicated UnrealEditor-Cmd process with -RenderOffscreen and
-ExecutePythonScript=Scripts/CaptureOutpostSandbox.py. The lead owns launching.
Thirteen raw 1600x900 PNGs and a manifest are written under Artifacts/Outpost/Captures.
Add -OutpostWalkthrough for 31 room-by-room and detail views at 1920x1080.
No exposure correction, material replacement, asset saving, PIE or HUD is used.
"""
import hashlib
import json
from pathlib import Path
import time
import traceback
from datetime import datetime, timezone

import unreal as u

TARGET = '/Game/OutpostSandbox/L_AsteroidOutpost'
WIDTH, HEIGHT = 1600, 900
# Position and look-at target are world centimetres. Interior cameras remain at
# standing height, below real ceilings and inside rooms rather than through walls.
SHOTS = [
    ('01_ExteriorArrival', (-7200,-10500,6200), (2000,0,1100), 65),
    ('02_PlayerPadApproach', (-4100,-1700,340), (1550,0,260), 72),
    ('03_MarketPromenade', (-1100,-100,185), (1400,450,220), 82),
    ('04_StationEntrance', (1520,-170,170), (2550,0,335), 76),
    ('05_AtriumConcourse', (3100,-830,185), (4700,350,240), 85),
    ('06_FlightEngineering', (4440,-2540,180), (4200,-3820,160), 78),
    ('07_CrewLoungeWardrobe', (4350,3300,180), (5350,3360,155), 78),
    ('08_ArcadeConversation', (4430,3390,180), (3610,4070,145), 76),
    ('09_Operations', (6750,-240,185), (8130,100,200), 82),
    ('10_VisitorBerths', (-2550,6600,1550), (-1300,2000,160), 75),
    ('11_PlanetaryArchive', (3610,-200,185), (4200,0,770), 95),
    ('12_ObservationGallery', (4050,-4200,700), (-2200,-1200,450), 80),
    ('13_MarketMiniKits', (500,0,190), (700,1550,180), 80),
]


def main():
    global SHOTS, WIDTH, HEIGHT
    command_line = u.SystemLibrary.get_command_line()
    if '-renderoffscreen' not in command_line.lower():
        raise RuntimeError('Outpost capture requires a dedicated -RenderOffscreen editor process')
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
    if '-outpostwalkthrough' in command_line.lower():
        SHOTS = json.loads((root/'Scripts/OutpostWalkthroughShots.json').read_text(encoding='utf-8-sig'))
        WIDTH, HEIGHT = 1920, 1080
    captures = root / 'Artifacts/Outpost/Captures'
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = captures / run_id
    output.mkdir(parents=True, exist_ok=False)
    map_file = root / 'Content/OutpostSandbox/L_AsteroidOutpost.umap'
    if not map_file.is_file():
        raise RuntimeError('Authored outpost map does not exist: ' + str(map_file))
    source_digest = hashlib.sha256(map_file.read_bytes()).hexdigest()
    level = u.get_editor_subsystem(u.LevelEditorSubsystem)
    if not level.load_level(TARGET):
        raise RuntimeError('Could not load authored outpost map: ' + TARGET)
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    world = editor.get_editor_world()
    import sys
    sys.path.insert(0,str(root/'Scripts'))
    import ValidateOutpostSandbox
    placement = ValidateOutpostSandbox.run(output/'placement-audit.json')
    try:
        import ss_catalog_refresh
        h=ss_catalog_refresh._state.get('handle')
        if h:u.unregister_slate_post_tick_callback(h);ss_catalog_refresh._state['handle']=None
    except ImportError:pass
    report = {
        'map': TARGET, 'run_id': run_id, 'started_utc': datetime.now(timezone.utc).isoformat(),
        'resolution': [WIDTH,HEIGHT], 'engine': u.SystemLibrary.get_engine_version(),
        'source_map_sha256': source_digest, 'images': [], 'errors': [],
        'scene_postprocess': [], 'exposure_overridden': False,
        'placement_audit': {'path': str(output/'placement-audit.json'),
                            'status': placement['status'],
                            'failures': len(placement['failures']),
                            'deferred': len(placement['deferred'])},
        'scope': 'Native editor map images; not runtime animation, traversal, controller or performance acceptance',
    }
    if placement['status'] != 'PASS_AUTHOR_TIME_ONLY':
        report['errors'].append('Saved-map placement audit did not pass; inspect placement-audit.json')
    # Report actual grading instead of changing it to make screenshots look nicer.
    for actor in actors.get_all_level_actors():
        if isinstance(actor, u.PostProcessVolume):
            settings = actor.get_editor_property('settings')
            names = ('auto_exposure_method','auto_exposure_min_brightness',
                     'auto_exposure_max_brightness','auto_exposure_bias',
                     'override_auto_exposure_min_brightness',
                     'override_auto_exposure_max_brightness','override_auto_exposure_bias',
                     'bloom_intensity')
            report['scene_postprocess'].append({
                'name':actor.get_actor_label(),
                'settings':{name:str(settings.get_editor_property(name)) for name in names},
            })
    camera = actors.spawn_actor_from_class(u.CameraActor, u.Vector())
    camera.set_actor_label('OutpostCapture_UnsavedCamera')
    component = camera.get_component_by_class(u.CameraComponent)
    component.set_editor_property('post_process_blend_weight',0.0)
    component.set_editor_property('aspect_ratio',WIDTH/HEIGHT)
    component.set_editor_property('constrain_aspect_ratio',True)
    level.editor_set_game_view(True)
    u.SystemLibrary.execute_console_command(world,'DisableAllScreenMessages')
    state = {'index':0,'frames':0,'task':None,'busy':False,'done':False,
             'started':time.monotonic(),'shot_start':0.0,'handle':None}

    def begin_shot():
        name,position,target,fov = SHOTS[state['index']]
        location = u.Vector(*position)
        rotation = u.MathLibrary.find_look_at_rotation(location,u.Vector(*target))
        camera.set_actor_location(location,False,False)
        camera.set_actor_rotation(rotation,False)
        component.set_field_of_view(fov)
        editor.set_level_viewport_camera_info(location,rotation)
        state.update(frames=0,task=None,shot_start=time.monotonic())
        u.log('OUTPOST_CAPTURE_BEGIN '+name)

    def finish():
        if state['done']:
            return
        state['done'] = True
        report['finished_utc'] = datetime.now(timezone.utc).isoformat()
        report['elapsed_seconds'] = round(time.monotonic()-state['started'],3)
        report['source_map_unchanged'] = hashlib.sha256(map_file.read_bytes()).hexdigest()==source_digest
        if not report['source_map_unchanged']:
            report['errors'].append('Saved source map changed during unsaved capture')
        report['status'] = 'CAPTURED_NOT_ACCEPTED' if not report['errors'] and len(report['images'])==len(SHOTS) else 'FAILED'
        (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        (captures/'latest.json').write_text(json.dumps({
            'run_id':run_id,'directory':str(output),'manifest':str(output/'manifest.json'),
            'status':report['status'],'images':len(report['images'])},indent=2)+'\n',encoding='utf-8')
        u.log('OUTPOST_CAPTURE_FINISHED '+report['status']+' '+str(output))
        if state['handle'] is not None:
            u.unregister_slate_post_tick_callback(state['handle'])
        u.EditorPythonScripting.set_keep_python_script_alive(False)
        u.SystemLibrary.quit_editor()

    def tick(delta):
        if state['busy'] or state['done']:
            return
        state['busy'] = True
        try:
            state['frames'] += 1
            name,position,target,fov = SHOTS[state['index']]
            path = output/(name+'.png')
            elapsed = time.monotonic()-state['shot_start']
            warm_frames = 90 if state['index']==0 else 45
            warm_seconds = 8 if state['index']==0 else 4
            if state['task'] is None and state['frames']>=warm_frames and elapsed>=warm_seconds:
                u.AutomationLibrary.finish_loading_before_screenshot()
                state['task'] = u.AutomationLibrary.take_high_res_screenshot(
                    WIDTH,HEIGHT,str(path),camera,force_game_view=True,delay=.3)
                if not state['task'].is_valid_task():
                    raise RuntimeError('Invalid capture task: '+name)
            if state['task'] and state['task'].is_task_done() and path.is_file():
                data=path.read_bytes()
                if len(data)<24 or data[:8]!=b'\x89PNG\r\n\x1a\n':
                    raise RuntimeError('Capture did not write a complete PNG: '+name)
                dimensions=[int.from_bytes(data[16:20],'big'),int.from_bytes(data[20:24],'big')]
                if dimensions!=[WIDTH,HEIGHT]:
                    raise RuntimeError('Unexpected capture resolution: '+str(dimensions))
                report['images'].append({
                    'name':name,'png':str(path),'camera_cm':list(position),'target_cm':list(target),
                    'fov_degrees':fov,'captured_utc':datetime.now(timezone.utc).isoformat(),
                    'elapsed_seconds':round(time.monotonic()-state['started'],3),
                    'warm_frames':state['frames'],'sha256':hashlib.sha256(data).hexdigest(),
                    'resolution':dimensions,
                })
                state['index']+=1
                if state['index']==len(SHOTS):
                    finish()
                else:
                    begin_shot()
            elif elapsed>180 or time.monotonic()-state['started']>900:
                raise RuntimeError('Outpost render timed out at '+name)
        except Exception:
            report['errors'].append(traceback.format_exc())
            u.log_error(report['errors'][-1])
            finish()
        finally:
            state['busy']=False

    begin_shot()
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    state['handle']=u.register_slate_post_tick_callback(tick)


if __name__=='__main__':
    main()
