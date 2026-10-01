"""Focused fresh-load assembly/ULAT checks and optional unsaved native previews.

Run in Entry with -NullRHI, or -RenderOffscreen -SSCaptureBuildingLibrary.
No source asset or map is saved. Script owns its dedicated editor process.
"""
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback
import unreal as u

ROOT=Path(u.Paths.project_dir()).resolve()
OUT=ROOT/'Artifacts/BuildingLibrary'
try:
    import ss_catalog_refresh
    refresh_handle=ss_catalog_refresh._state.get('handle')
    if refresh_handle:
        u.unregister_slate_post_tick_callback(refresh_handle)
        ss_catalog_refresh._state['handle']=None
except ImportError:
    pass
sys.path.insert(0,str(Path(__file__).parent))
import ConfigureUlatLibrary
EAS=u.get_editor_subsystem(u.EditorActorSubsystem)
editor=u.get_editor_subsystem(u.UnrealEditorSubsystem)
world=editor.get_editor_world()
assert world.get_path_name().startswith('/Engine/Maps/Entry')
capture='-SSCaptureBuildingLibrary' in u.SystemLibrary.get_command_line()
assert not capture or '-renderoffscreen' in u.SystemLibrary.get_command_line().lower()
paths=[ROOT/'Content/OutpostSandbox/L_AsteroidOutpost.umap',ROOT/'Content/CargoShip/Maps/L_Showcase.umap',
       ROOT/'Content/BuildingLibrary/Ships/L_CargoShip_Complete.umap']
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):digest(p) for p in paths}
report={'status':'running','errors':[],'images':[],'protected_before':before}
(OUT/'library-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
receipt=json.loads((OUT/'prefab-author.json').read_text())
report['prefabs_verified']=0
for path,record in receipt['prefabs'].items():
    bp=u.load_asset(path)
    a=EAS.spawn_actor_from_class(bp.generated_class(),u.Vector())
    parts=a.get_components_by_class(u.StaticMeshComponent)
    assert len(parts)==record['parts'] and all(p.static_mesh for p in parts),path
    start=[p.get_world_location() for p in parts]
    assert a.set_actor_location(u.Vector(137,251,389),False,False)
    assert all((p.get_world_location()-v-u.Vector(137,251,389)).length()<.1 for p,v in zip(parts,start)),path
    EAS.destroy_actor(a)
    report['prefabs_verified']+=1
table=u.load_asset(ConfigureUlatLibrary.TABLE_PATH)
rows=ConfigureUlatLibrary._json_export(u,table)
report['ulat_rows']=len(rows)
assert len(rows)>=1150, 'ULAT palette did not persist'
base='/Game/BuildingLibrary/Assembled/'
ship=EAS.spawn_actor_from_class(u.load_asset(base+'Ships/BP_CargoShip_Complete').generated_class(),u.Vector(12000,0,0))
assert ship
state={'stage':'load','started':time.monotonic(),'phase':time.monotonic(),'busy':False,'handle':None,'done':False,'shot':0,'task':None}
shots=[]

def finish():
    if state['done']:return
    state['done']=True
    report['protected_unchanged']=all(digest(p)==before[str(p)] for p in paths)
    if not report['protected_unchanged']:report['errors'].append('Protected map changed')
    report['status']='PASS' if not report['errors'] else 'FAILED'
    (OUT/'library-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    u.log('BUILDING_LIBRARY_VALIDATION '+report['status'])
    u.unregister_slate_post_tick_callback(state['handle'])
    u.EditorPythonScripting.set_keep_python_script_alive(False)
    u.SystemLibrary.quit_editor()

def setup_shots():
    for name,pos in [('Windows/Genesis_Window_400x200_Glass',(0,0,0)),('Screens/Genesis_Screen_400x200_Graph1',(0,500,0)),
                     ('Workstations/Goliath_CompleteWorkstation',(0,1800,0))]:
        a=EAS.spawn_actor_from_class(u.load_asset(base+name).generated_class(),u.Vector(*pos))
        assert a
    for x,y,z,pitch,yaw,intensity in [(0,-800,1500,-45,90,3.),(600,2400,1400,-40,-90,2.)]:
        a=EAS.spawn_actor_from_class(u.DirectionalLight,u.Vector(x,y,z),u.Rotator(pitch=pitch,yaw=yaw))
        a.light_component.set_mobility(u.ComponentMobility.MOVABLE)
        a.light_component.set_editor_property('intensity',intensity)
    sky=EAS.spawn_actor_from_class(u.SkyLight,u.Vector(0,0,2000))
    sky.light_component.set_mobility(u.ComponentMobility.MOVABLE)
    sky.light_component.set_editor_property('source_type',u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    sky.light_component.set_editor_property('cubemap',u.load_asset('/Engine/MapTemplates/Sky/DaylightAmbientCubemap'))
    sky.light_component.set_editor_property('intensity',3.)
    pp=EAS.spawn_actor_from_class(u.PostProcessVolume,u.Vector())
    pp.set_editor_property('unbound',True)
    settings=pp.get_editor_property('settings')
    extended=u.SystemLibrary.get_console_variable_int_value('r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange')
    exposure=0. if extended else 1.
    report['preview_exposure']={'extended':bool(extended),'fixed_value':exposure,'scope':'Unsaved preview scene only'}
    for k,v in [('auto_exposure_min_brightness',exposure),('auto_exposure_max_brightness',exposure),
                ('auto_exposure_bias',0.),('bloom_intensity',.2),('motion_blur_amount',0.)]:
        settings.set_editor_property('override_'+k,True)
        settings.set_editor_property(k,v)
    pp.set_editor_property('settings',settings)
    cam=EAS.spawn_actor_from_class(u.CameraActor,u.Vector())
    state['camera']=cam
    state['camera_component']=cam.get_component_by_class(u.CameraComponent)
    state['camera_component'].set_editor_property('post_process_blend_weight',0.)
    shots.extend([('Windows',(850,250,180),(0,250,100),65),
                  ('Workstation',(450,1300,260),(0,1800,100),50),
                  ('CargoShip',(18000,-6500,4000),(12321,0,600),65)])
    begin_shot()

def begin_shot():
    name,pos,target,fov=shots[state['shot']]
    loc=u.Vector(*pos)
    rotation=u.MathLibrary.find_look_at_rotation(loc,u.Vector(*target))
    state['camera'].set_actor_location(loc,False,False)
    state['camera'].set_actor_rotation(rotation,False)
    state['camera_component'].set_field_of_view(fov)
    editor.set_level_viewport_camera_info(loc,rotation)
    state.update(stage='capture',phase=time.monotonic(),task=None)

def tick(delta):
    if state['busy'] or state['done']:return
    state['busy']=True
    try:
        elapsed=time.monotonic()-state['phase']
        if state['stage']=='load':
            # EditorActorSubsystem excludes locked LevelInstance children after
            # streaming completes; query the world's loaded actors directly.
            hulls=[a for a in u.GameplayStatics.get_all_actors_of_class(world,u.StaticMeshActor) if a.static_mesh_component.static_mesh and a.static_mesh_component.static_mesh.get_name()=='SM_SpaceShip_Outer_Body2']
            if hulls and elapsed>10:
                u.AutomationLibrary.finish_loading_before_screenshot()
                assert not any(a.static_mesh_component.static_mesh and a.static_mesh_component.static_mesh.get_name()=='SM_Planet' for a in u.GameplayStatics.get_all_actors_of_class(world,u.StaticMeshActor)), 'Cargo includes vendor showcase planets'
                state['hull']=hulls[0]
                state['hull_start']=hulls[0].get_actor_location()
                report['loaded_actors']=len(u.GameplayStatics.get_all_actors_of_class(world,u.Actor))
                transform=ship.get_actor_transform()
                transform.translation=ship.get_actor_location()+u.Vector(321,0,0)
                assert EAS.set_actor_transform(ship,transform)
                state.update(stage='move',phase=time.monotonic())
            elif elapsed>60:raise RuntimeError('Cargo LevelInstance did not load its hull within 60 seconds')
        elif state['stage']=='move' and elapsed>2:
            offset=state['hull'].get_actor_location()-state['hull_start']
            report['cargo_move_offset']=[offset.x,offset.y,offset.z]
            assert (offset-u.Vector(321,0,0)).length()<1.,'Cargo children did not follow LevelInstance'
            report['cargo_load_and_move']=True
            if capture:setup_shots()
            else:finish()
        elif state['stage']=='capture':
            name,_,_,_=shots[state['shot']]
            path=OUT/(name+'.png')
            if state['task'] is None and elapsed>6:
                u.AutomationLibrary.finish_loading_before_screenshot()
                state['task']=u.AutomationLibrary.take_high_res_screenshot(1440,900,str(path),state['camera'],force_game_view=True,delay=.3)
                assert state['task'].is_valid_task()
            if state['task'] and state['task'].is_task_done() and path.is_file():
                report['images'].append(str(path))
                state['shot']+=1
                if state['shot']==len(shots):finish()
                else:begin_shot()
            elif elapsed>180:raise RuntimeError('Capture timed out: '+name)
    except Exception:
        report['errors'].append(traceback.format_exc())
        u.log_error(report['errors'][-1])
        finish()
    finally:state['busy']=False

u.EditorPythonScripting.set_keep_python_script_alive(True)
state['handle']=u.register_slate_post_tick_callback(tick)
