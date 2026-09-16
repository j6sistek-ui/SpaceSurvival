"""Render and inspect vendor showcase in an unsaved editor session; never save it."""
import hashlib
import json
from pathlib import Path
import time
import traceback
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Artifacts/Megastructure/Showcase'
OUT.mkdir(parents=True, exist_ok=True)
VENDOR = ROOT / 'Content/Megastructure_Scifi_World'
def hashes():
    return {p.relative_to(VENDOR).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in VENDOR.rglob('*') if p.is_file()}
protected = hashes()
level = u.get_editor_subsystem(u.LevelEditorSubsystem)
assert level.load_level('/Game/Megastructure_Scifi_World/Level/L_Showcase_level')
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
position, rotation = editor.get_level_viewport_camera_info()
report = {'actors': [], 'stored_view': [list(position.to_tuple()), list(rotation.to_tuple())], 'images': [], 'errors': []}
for actor in actors.get_all_level_actors():
    meshes = actor.get_components_by_class(u.StaticMeshComponent)
    row = {'name':actor.get_actor_label(), 'class':actor.get_class().get_name(),
           'location':list(actor.get_actor_location().to_tuple()), 'rotation':list(actor.get_actor_rotation().to_tuple()),
           'meshes':[c.static_mesh.get_path_name() for c in meshes if c.static_mesh]}
    report['actors'].append(row)
    if isinstance(actor, u.PostProcessVolume):
        settings=actor.get_editor_property('settings')
        report['vendor_exposure']={k:str(settings.get_editor_property(k)) for k in ('auto_exposure_method','auto_exposure_min_brightness','auto_exposure_max_brightness','auto_exposure_bias')}
        # Adapt preview exposure only. Vendor packages remain untouched.
        for key,value in {'override_auto_exposure_min_brightness':True,'override_auto_exposure_max_brightness':True,
                          'auto_exposure_min_brightness':1.,'auto_exposure_max_brightness':1.,
                          'override_auto_exposure_bias':True,'auto_exposure_bias':1.}.items():
            settings.set_editor_property(key,value)
        actor.set_editor_property('settings',settings)
    if isinstance(actor,u.DirectionalLight):
        report['directional_intensity']=actor.get_component_by_class(u.DirectionalLightComponent).get_editor_property('intensity')
position=u.Vector(35000,-20000,26000)
rotation=u.MathLibrary.find_look_at_rotation(position,u.Vector(0,14000,0))
camera = actors.spawn_actor_from_class(u.CameraActor, position, rotation)
editor.set_level_viewport_camera_info(position,rotation)
camera.get_component_by_class(u.CameraComponent).set_field_of_view(80)
level.editor_set_game_view(True)
state = {'start':time.monotonic(), 'frames':0, 'task':None, 'busy':False, 'done':False}
def finish():
    state['done']=True
    report['vendor_unchanged']=hashes()==protected
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    u.unregister_slate_post_tick_callback(state['handle'])
    u.EditorPythonScripting.set_keep_python_script_alive(False)
def tick(delta):
    if state['busy'] or state['done']: return
    state['busy']=True
    try:
        state['frames']+=1
        path=OUT/'VendorShowcase.png'
        if state['task'] is None and state['frames']>120 and time.monotonic()-state['start']>8:
            u.AutomationLibrary.finish_loading_before_screenshot()
            state['task']=u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(path),camera,delay=.3)
        if state['task'] and state['task'].is_task_done() and path.exists():
            report['images'].append(str(path)); finish()
        elif time.monotonic()-state['start']>180:
            raise RuntimeError('Showcase capture timed out')
    except Exception:
        report['errors'].append(traceback.format_exc()); finish()
    finally:
        state['busy']=False
u.EditorPythonScripting.set_keep_python_script_alive(True)
state['handle']=u.register_slate_post_tick_callback(tick)
