"""Ten-second actual-PIE proof for only the three new skyline cargo carriers.

Dedicated -RenderOffscreen editor only. No camera/UI/input changes, gameplay
transactions, asset writes or world save. Lead owns invocation. Evidence tests
motion/attachment/visible-mesh state, not rendered quality or performance.
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

TARGET = '/Game/OutpostSandbox/L_AsteroidOutpost'
PREFIX = 'SkylineAtmosphere/'
REPORT, OUT = None, None


def vector(v):
    return [float(v.x),float(v.y),float(v.z)]


def relative(component):
    t=component.get_relative_transform();q=t.rotation
    return {'position':vector(t.translation),'rotation':[q.x,q.y,q.z,q.w],'scale':vector(t.scale3d)}


def main():
    global REPORT,OUT
    if '-renderoffscreen' not in u.SystemLibrary.get_command_line().lower():
        raise RuntimeError('Cargo validation requires a dedicated -RenderOffscreen editor')
    root=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
    OUT=root/'Artifacts/Outpost/CargoPlay'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    OUT.mkdir(parents=True,exist_ok=False)
    source=root/'Content/OutpostSandbox/L_AsteroidOutpost.umap'
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    save_dir=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_saved_dir()))/'SaveGames'
    def saves():
        return {str(p.relative_to(save_dir)):hashlib.sha256(p.read_bytes()).hexdigest() for p in save_dir.rglob('*.sav')} if save_dir.exists() else {}
    before_saves=saves()
    REPORT={'map':TARGET,'source_map_sha256':digest,'checks':{},'carriers':[], 'errors':[],
            'scope':'Only three cargo carriers: actual PIE motion, attachment and visible mesh presence; no visual/performance acceptance.'}
    level=u.get_editor_subsystem(u.LevelEditorSubsystem)
    editor=u.get_editor_subsystem(u.UnrealEditorSubsystem)
    if editor.get_game_world():raise RuntimeError('Existing PIE is not a dedicated validation process')
    if not level.load_level(TARGET):raise RuntimeError('Could not load saved outpost')
    u.AutomationLibrary.finish_loading_before_screenshot()
    sys.path.insert(0,str(root/'Scripts'))
    from OutpostSkylineAtmosphere import ROUTES,MARKER
    expected={PREFIX+r['name'] for r in ROUTES}
    if len(expected)!=3:raise RuntimeError('The targeted cargo recipe no longer has three carriers')
    try:
        import ss_catalog_refresh
        h=ss_catalog_refresh._state.get('handle')
        if h:u.unregister_slate_post_tick_callback(h);ss_catalog_refresh._state['handle']=None
    except ImportError:pass
    state={'phase':'wait','start':time.monotonic(),'handle':None,'busy':False,'ready_since':None,'samples':0}
    def check(name,passed,evidence):REPORT['checks'][name]={'passed':bool(passed),'evidence':evidence}
    def stop():
        if state['phase']!='stop':
            state.update(phase='stop',stop=time.monotonic());level.editor_request_end_play()
    def finish():
        check('saved_map_unchanged',hashlib.sha256(source.read_bytes()).hexdigest()==digest,digest)
        check('save_files_unchanged',saves()==before_saves,{'directory':str(save_dir),'files':list(before_saves)})
        check('PIE_stopped',not editor.get_game_world(),'Editor end-play request; no map save')
        REPORT['status']='PASS_CARGO_MOTION_ONLY' if not REPORT['errors'] and all(c['passed'] for c in REPORT['checks'].values()) else 'FAIL'
        REPORT['finished_utc']=datetime.now(timezone.utc).isoformat()
        (OUT/'runtime.json').write_text(json.dumps(REPORT,indent=2)+'\n',encoding='utf-8')
        (OUT.parent/'latest.json').write_text(json.dumps({'status':REPORT['status'],'receipt':str(OUT/'runtime.json')},indent=2),encoding='utf-8')
        u.log('OUTPOST_CARGO_FINISHED '+REPORT['status']+' '+str(OUT))
        u.unregister_slate_post_tick_callback(state['handle'])
        u.EditorPythonScripting.set_keep_python_script_alive(False);u.SystemLibrary.quit_editor()
    def tick(dt):
        if state['busy']:return
        state['busy']=True
        try:
            if state['phase']=='stop':
                if not editor.get_game_world() or time.monotonic()-state['stop']>8:finish()
                return
            if time.monotonic()-state['start']>180:raise RuntimeError('Cargo PIE readiness/motion timed out')
            world=editor.get_game_world()
            if not world:return
            if state['phase']=='wait':
                game_time=u.GameplayStatics.get_time_seconds(world)
                if state['ready_since'] is None:
                    state['ready_since']=game_time;u.GameplayStatics.set_game_paused(world,False)
                if game_time-state['ready_since']<.5:return
                all_actors=u.GameplayStatics.get_all_actors_of_class(world,u.Actor)
                carriers=[a for a in all_actors if isinstance(a,u.SSOutpostAmbientActor) and a.get_actor_label().startswith(PREFIX)]
                check('exact_three_cargo_carriers',len(carriers)==3 and {a.get_actor_label() for a in carriers}==expected,[a.get_actor_label() for a in carriers])
                if not REPORT['checks']['exact_three_cargo_carriers']['passed']:stop();return
                state['groups']=[]
                for actor in carriers:
                    name=actor.get_actor_label();anchor=actor.drone_mesh
                    children=[a for a in all_actors if a.get_actor_label().startswith(name+'/') and MARKER in map(str,a.tags)]
                    counts={key:sum('/'+key in a.get_actor_label() for a in children) for key in ('Owned droid','Shipping carton','Tether ','Strap ')}
                    if counts!={'Owned droid':1,'Shipping carton':1,'Tether ':4,'Strap ':8}:raise RuntimeError('Incomplete cargo assembly: '+name+' '+str(counts))
                    row={'name':name,'start':vector(actor.get_actor_location()),'max_carrier_displacement_cm':0.,'anchor_bob_min':1e9,'anchor_bob_max':-1e9,'children':[]}
                    entries=[]
                    for child in children:
                        component=child.get_editor_property('root_component')
                        meshes=[c for c in child.get_components_by_class(u.StaticMeshComponent) if c.static_mesh and (not isinstance(c,u.InstancedStaticMeshComponent) or c.get_instance_count()>0)]
                        item={'name':child.get_actor_label(),'relative_start':relative(component),'world_start':vector(component.get_world_location()),'mesh_components':len(meshes),'max_world_displacement_cm':0.,'max_parent_tracking_error_cm':0.,'max_relative_translation_error_cm':0.,'max_relative_quaternion_error':0.,'max_relative_scale_error':0.,'attached':True,'visible':True}
                        row['children'].append(item);entries.append((child,component,meshes,item))
                    REPORT['carriers'].append(row);state['groups'].append((actor,anchor,entries,row))
                state.update(phase='sample',t0=game_time,last_sample=-1.)
                return
            elapsed=u.GameplayStatics.get_time_seconds(world)-state['t0']
            if elapsed-state['last_sample']<.1 and elapsed<10.:return
            state['last_sample']=elapsed;state['samples']+=1
            for actor,anchor,entries,row in state['groups']:
                row['max_carrier_displacement_cm']=max(row['max_carrier_displacement_cm'],math.dist(vector(actor.get_actor_location()),row['start']))
                bob=anchor.get_relative_transform().translation.z
                row['anchor_bob_min']=min(row['anchor_bob_min'],bob);row['anchor_bob_max']=max(row['anchor_bob_max'],bob)
                for child,component,meshes,item in entries:
                    initial=item['relative_start'];current=relative(component)
                    item['attached'] &= component.get_attach_parent()==anchor
                    item['visible'] &= bool(meshes) and not child.get_editor_property('hidden') and any(c.get_editor_property('visible') and not c.get_editor_property('hidden_in_game') for c in meshes)
                    predicted=u.MathLibrary.transform_location(anchor.get_world_transform(),u.Vector(*initial['position']))
                    item['max_parent_tracking_error_cm']=max(item['max_parent_tracking_error_cm'],(component.get_world_location()-predicted).length())
                    item['max_world_displacement_cm']=max(item['max_world_displacement_cm'],math.dist(vector(component.get_world_location()),item['world_start']))
                    item['max_relative_translation_error_cm']=max(item['max_relative_translation_error_cm'],math.dist(initial['position'],current['position']))
                    qerror=min(max(abs(a-b) for a,b in zip(initial['rotation'],current['rotation'])),max(abs(a+b) for a,b in zip(initial['rotation'],current['rotation'])))
                    item['max_relative_quaternion_error']=max(item['max_relative_quaternion_error'],qerror)
                    item['max_relative_scale_error']=max(item['max_relative_scale_error'],max(abs(a-b) for a,b in zip(initial['scale'],current['scale'])))
            if elapsed>=10.:
                REPORT.update(observed_game_seconds=elapsed,sample_count=state['samples'])
                check('ten_second_window',8.<=elapsed<=12. and state['samples']>=10,{'seconds':elapsed,'samples':state['samples']})
                for row in REPORT['carriers']:
                    check(row['name']+'/route_motion',row['max_carrier_displacement_cm']>200,row['max_carrier_displacement_cm'])
                    check(row['name']+'/native_bob',row['anchor_bob_max']-row['anchor_bob_min']>2,[row['anchor_bob_min'],row['anchor_bob_max']])
                    children=row['children']
                    valid=all(c['attached'] and c['visible'] and c['max_world_displacement_cm']>200 and c['max_parent_tracking_error_cm']<.1 and c['max_relative_translation_error_cm']<.1 and c['max_relative_quaternion_error']<.0001 and c['max_relative_scale_error']<.0001 for c in children)
                    check(row['name']+'/complete_attached_payload_follows',len(children)==14 and valid,{'children':len(children),'details':'Per-part evidence in carriers[].children'})
                stop()
        except Exception:
            REPORT['errors'].append(traceback.format_exc());u.log_error(REPORT['errors'][-1]);stop()
        finally:state['busy']=False
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    state['handle']=u.register_slate_post_tick_callback(tick)
    level.editor_request_begin_play()


if __name__=='__main__':
    try:main()
    except Exception:
        error=traceback.format_exc();u.log_error(error)
        if REPORT is not None and OUT is not None:
            REPORT['errors'].append(error);REPORT['status']='FAIL_SETUP'
            (OUT/'runtime.json').write_text(json.dumps(REPORT,indent=2)+'\n',encoding='utf-8')
        u.EditorPythonScripting.set_keep_python_script_alive(False);u.SystemLibrary.quit_editor()
