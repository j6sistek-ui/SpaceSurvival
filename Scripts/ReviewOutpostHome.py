"""Focused new-annex floor/clearance checks, captures and optional PIE walk.

-HomeCapture takes four saved-scene views. -HomeWalk walks the new route into
and out of the furnished room; no save, progression, travel or terminal use.
"""
import hashlib
import json
import math
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
import unreal as u

ROOT=Path(u.Paths.project_dir()).resolve()
OUT=ROOT/'Artifacts/ApartmentHome'/('Review-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
OUT.mkdir(parents=True)
sys.path.insert(0,str(ROOT/'Scripts'))
import HomeAnnexConnector
CMD=u.SystemLibrary.get_command_line().lower()
CAPTURE='-homecapture' in CMD
WALK='-homewalk' in CMD
LIBRARY='-homelibrary' in CMD
assert '-renderoffscreen' in CMD
LEVEL=u.get_editor_subsystem(u.LevelEditorSubsystem)
EDITOR=u.get_editor_subsystem(u.UnrealEditorSubsystem)
EAS=u.get_editor_subsystem(u.EditorActorSubsystem)
paths=[ROOT/'Content/OutpostSandbox/L_AsteroidOutpost.umap',ROOT/'Content/BuildingLibrary/Home/L_CrewApartment.umap',
       ROOT/'Content/Cyberpunk_Room/Maps/Cyberpunk_Room.umap']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in paths}
save_dir=Path(u.Paths.project_saved_dir()).resolve()/'SaveGames'
saves=lambda:{str(p):sha(p) for p in save_dir.glob('*.sav')} if save_dir.exists() else {}
save_before=saves()
try:
    import ss_catalog_refresh
    h=ss_catalog_refresh._state.get('handle')
    if h:u.unregister_slate_post_tick_callback(h);ss_catalog_refresh._state['handle']=None
except ImportError:pass
assert LEVEL.load_level('/Game/OutpostSandbox/L_AsteroidOutpost')
route=HomeAnnexConnector.layout()['route_feet']+[[6280,4100,-120],[6550,4100,-120],
    [6700,4220,-120],[6700,4300,-120],[6700,4380,-145],[6700,4500,-170],[6700,4660,-170]]
shots=[('01_HomeApproach',(4460,1975,175),(5900,1975,10),85),
       ('02_HomeEntrance',(5900,4040,70),(6500,4160,30),85),
       ('03_ApartmentLiving',(6450,4570,5),(7650,4850,30),95),
       ('04_ApartmentDesk',(7680,4950,0),(6450,4540,45),90)]
state={'phase':'load','phase_start':time.monotonic(),'started':time.monotonic(),'busy':False,'handle':None,'done':False,'shot':0,'task':None}
report={'status':'running','scope':'New home only: saved-map geometry, optional scripted PIE input; no physical-controller/performance claim',
        'before':before,'checks':[],'images':[],'errors':[],'route_feet':route}
def v(p):return [round(p.x,3),round(p.y,3),round(p.z,3)]
def check(name,okay,details):report['checks'].append({'name':name,'passed':bool(okay),'details':details})
def hit_data(h):
    f=h.to_tuple() if h else None
    return {'actor':f[9].get_actor_label() if f[9] else None,'position':v(f[5]),'normal':v(f[7])} if f and f[0] else None
def finish():
    if state['done']:return
    state['done']=True
    check('maps_preserved',all(sha(p)==before[str(p)] for p in paths),before)
    check('save_files_preserved',saves()==save_before,str(save_dir))
    report['status']='PASS_SCOPED' if not report['errors'] and all(c['passed'] for c in report['checks']) else 'FAILED'
    (OUT/'review.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    (OUT.parent/'latest-review.json').write_text(json.dumps({'status':report['status'],'path':str(OUT/'review.json')}),encoding='utf-8')
    u.log('HOME_REVIEW '+report['status']+' '+str(OUT))
    u.unregister_slate_post_tick_callback(state['handle'])
    u.EditorPythonScripting.set_keep_python_script_alive(False)
    u.SystemLibrary.quit_editor()
def stop():
    if state['phase']=='stop':
        finish()
        return
    if EDITOR.get_game_world():
        LEVEL.editor_request_end_play();state.update(phase='stop',phase_start=time.monotonic())
    else:finish()
def start_walk():
    if not WALK:finish();return
    state.update(phase='wait_play',phase_start=time.monotonic())
    LEVEL.editor_request_begin_play()
def start_shot():
    name,pos,target,fov=shots[state['shot']]
    location=u.Vector(*pos);rotation=u.MathLibrary.find_look_at_rotation(location,u.Vector(*target))
    state['camera'].set_actor_location(location,False,False);state['camera'].set_actor_rotation(rotation,False)
    state['camera_component'].set_field_of_view(fov)
    EDITOR.set_level_viewport_camera_info(location,rotation)
    state.update(phase='shot',phase_start=time.monotonic(),task=None)
def geometry():
    world=EDITOR.get_editor_world()
    u.AutomationLibrary.finish_loading_before_screenshot()
    doors=[a for a in u.GameplayStatics.get_all_actors_of_class(world,u.SSOutpostDoor) if a.get_actor_label()=='HomeApartment/Automatic entry']
    check('one_home_door',len(doors)==1,[v(a.get_actor_location()) for a in doors])
    if LIBRARY:
        import ConfigureUlatLibrary as ulat
        table=u.load_asset(ulat.TABLE_PATH)
        rows=ulat._json_export(u,table)
        registration=json.loads((ROOT/'Artifacts/ApartmentHome/library-registration.json').read_text(encoding='utf-8'))
        expected_rows=registration['apply'].get('verified_rows',registration['apply']['planned_rows'])
        check('ulat_saved_row_count',len(rows)==expected_rows,len(rows))
        manager=u.get_editor_subsystem(u.CollectionManagerSubsystem)
        for row in registration['collections']:
            ref=u.Collection(container='Game',name=row['name'],share_type=u.CollectionShareType.LOCAL)
            assets=manager.get_assets_in_collection(ref)
            if isinstance(assets,tuple):assets=assets[-1]
            check('collection_'+row['name'],len(assets)>=row['assets'],len(assets))
        bp=u.load_asset('/Game/BuildingLibrary/Assembled/Home/BP_CrewApartment_Complete')
        check('home_assembly_loads',bool(bp and bp.generated_class()),str(bp))
    capsule=u.get_default_object(u.SSWalker).get_component_by_class(u.CapsuleComponent)
    radius,half=capsule.get_unscaled_capsule_radius(),capsule.get_unscaled_capsule_half_height()
    report['capsule']={'radius':radius,'half_height':half}
    for i,p in enumerate(route):
        h=u.SystemLibrary.line_trace_single_by_profile(world,u.Vector(p[0],p[1],p[2]+35),u.Vector(p[0],p[1],p[2]-80),'Pawn',False,doors,u.DrawDebugTrace.NONE,True)
        floor=hit_data(h)
        check('floor_'+str(i),floor and abs(floor['position'][2]-p[2])<28 and floor['normal'][2]>.65,{'feet':p,'hit':floor})
        # Check torso/head clearance above the walker's legal step band. A
        # full capsule placed exactly on a descending tread intersects the
        # preceding riser, even when CharacterMovement traverses it normally.
        # Feet/support and actual movement in both directions are separate gates.
        step=float(u.get_default_object(u.SSWalker).character_movement.max_step_height)
        probe_half=half-step/2
        center=u.Vector(p[0],p[1],p[2]+half+step/2+4)
        h=u.SystemLibrary.capsule_trace_single_by_profile(world,center,center+u.Vector(0,0,.1),radius,probe_half,'Pawn',False,doors,u.DrawDebugTrace.NONE,True)
        block=hit_data(h)
        check('upper_clearance_'+str(i),block is None,{'feet':p,'hit':block,'step_band_cm':step})
    if CAPTURE:
        state['camera']=EAS.spawn_actor_from_class(u.CameraActor,u.Vector())
        state['camera_component']=state['camera'].get_component_by_class(u.CameraComponent)
        state['camera_component'].set_editor_property('post_process_blend_weight',0.)
        LEVEL.editor_set_game_view(True)
        start_shot()
    else:start_walk()

def tick(delta):
    if state['done'] or state['busy']:return
    state['busy']=True
    try:
        phase=state['phase'];elapsed=time.monotonic()-state['phase_start']
        if phase=='stop':
            if not EDITOR.get_game_world():finish()
            elif elapsed>12:raise RuntimeError('PIE did not stop')
        elif phase=='load':
            doors=u.GameplayStatics.get_all_actors_of_class(EDITOR.get_editor_world(),u.SSOutpostDoor)
            if len(doors)>4 and elapsed>8:geometry()
            elif elapsed>120:raise RuntimeError('Home streamed level did not load')
        elif phase=='shot':
            name=shots[state['shot']][0];path=OUT/(name+'.png')
            if state['task'] is None and elapsed>5:
                u.AutomationLibrary.finish_loading_before_screenshot()
                state['task']=u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(path),state['camera'],force_game_view=True,delay=.3)
                assert state['task'].is_valid_task()
            if state['task'] and state['task'].is_task_done() and path.exists():
                report['images'].append(str(path));state['shot']+=1
                if state['shot']==len(shots):
                    EAS.destroy_actor(state['camera']);start_walk()
                else:start_shot()
            elif elapsed>180:raise RuntimeError('Screenshot timed out')
        elif phase=='wait_play':
            world=EDITOR.get_game_world()
            if world:
                walker=u.GameplayStatics.get_player_pawn(world,0)
                doors=u.GameplayStatics.get_all_actors_of_class(world,u.SSOutpostDoor)
                home=[a for a in doors if a.get_actor_label()=='HomeApartment/Automatic entry']
                if walker and home and elapsed>5:
                    half=walker.get_component_by_class(u.CapsuleComponent).get_scaled_capsule_half_height()
                    p=route[0]
                    walker.character_movement.stop_movement_immediately()
                    walker.set_actor_location(u.Vector(p[0],p[1],p[2]+half+3),False,True)
                    pc=u.GameplayStatics.get_player_controller(world,0)
                    state.update(phase='walk',phase_start=time.monotonic(),world=world,walker=walker,pc=pc,half=half,
                         waypoint=1,route=route,returning=False,door=home[0],max_open=0.,stalled_start=time.monotonic(),
                         last_sample=0.,max_tracking_error=0.)
                    report['walk_samples']=[]
            if elapsed>120:raise RuntimeError('PIE home/walker unavailable')
        elif phase=='walk':
            w=state['walker'];p=w.get_actor_location();goal=state['route'][state['waypoint']]
            dx,dy=goal[0]-p.x,goal[1]-p.y;distance=math.hypot(dx,dy);feet=p.z-state['half']
            door=state['door'];state['max_open']=max(state['max_open'],float(door.open_fraction))
            if time.monotonic()-state['last_sample']>.7:
                report['walk_samples'].append({'return':state['returning'],'waypoint':state['waypoint'],'feet':[p.x,p.y,feet],'open':float(door.open_fraction)})
                state['last_sample']=time.monotonic()
            if distance<22 and abs(feet-goal[2])<28:
                state['waypoint']+=1;state['stalled_start']=time.monotonic()
                if state['waypoint']==len(state['route']):
                    check('walk_return' if state['returning'] else 'walk_into_home',not w.character_movement.is_falling(),{'end':v(p),'feet_z':feet,'waypoints':state['waypoint'],'script_teleports_after_setup':0})
                    if state['returning']:
                        check('entry_opens_automatically',state['max_open']>.95,state['max_open'])
                        w.character_movement.stop_movement_immediately()
                        state.update(phase='door_close',phase_start=time.monotonic())
                    else:
                        state.update(returning=True,route=list(reversed(route)),waypoint=1,stalled_start=time.monotonic())
                    return
            elif distance>1:
                w.add_movement_input(u.Vector(dx/distance,dy/distance,0),min(1.,distance/75),True)
                state['pc'].set_control_rotation(u.Rotator(pitch=-5,yaw=math.degrees(math.atan2(dy,dx))))
            if time.monotonic()-state['stalled_start']>14:
                check('walk_return' if state['returning'] else 'walk_into_home',False,{'stalled':v(p),'feet':feet,'goal':goal,'waypoint':state['waypoint']});stop()
        elif phase=='door_close':
            if elapsed>8:
                check('entry_closes_after_departure',state['door'].open_fraction<.05,float(state['door'].open_fraction));stop()
        if time.monotonic()-state['started']>600:raise RuntimeError('Focused review timeout')
    except Exception:
        report['errors'].append(traceback.format_exc());u.log_error(report['errors'][-1]);stop()
    finally:state['busy']=False
u.EditorPythonScripting.set_keep_python_script_alive(True)
state['handle']=u.register_slate_post_tick_callback(tick)
