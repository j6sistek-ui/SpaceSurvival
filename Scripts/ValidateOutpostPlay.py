"""Focused actual-map PIE check. Run only in a dedicated -RenderOffscreen editor.

Exercises native door/ambient motion and local-only terminals. Movement is injected
through CharacterMovement; this is not physical controller or full gameplay acceptance.
No map travel, Survival start, asset save or account transaction is performed.
"""
import hashlib
import json
import time
import sys
import math
import traceback
from datetime import datetime, timezone
from pathlib import Path
import unreal as u

TARGET = '/Game/OutpostSandbox/L_AsteroidOutpost'

def main():
    assert '-renderoffscreen' in u.SystemLibrary.get_command_line().lower(), 'Dedicated offscreen editor required'
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
    out = root/'Artifacts/Outpost/Play'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out.mkdir(parents=True)
    source = root/'Content/OutpostSandbox/L_AsteroidOutpost.umap'
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    saved = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_saved_dir()))/'SaveGames'
    def saves():
        return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in saved.glob('*.sav')} if saved.exists() else {}
    original_saves = saves()
    level = u.get_editor_subsystem(u.LevelEditorSubsystem)
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    assert not editor.get_game_world(), 'Use a fresh dedicated process, not an existing Play session'
    assert level.load_level(TARGET), 'Could not load saved outpost'
    try:
        import ss_catalog_refresh
        handle = ss_catalog_refresh._state.get('handle')
        if handle: u.unregister_slate_post_tick_callback(handle); ss_catalog_refresh._state['handle'] = None
    except ImportError:
        pass
    report = {'map':TARGET,'source_map_sha256':digest,'checks':{},'samples':[], 'images':[], 'errors':[],
              'scope':'Actual saved map in PIE. Injected walking and local preview use; not hardware input acceptance.'}
    # Installed LevelEditorSubsystem requests PIE with optional StartLocation unset,
    # leaving spawn selection to the map's PlayerStart instead of a camera override.
    report['spawn_request']='LevelEditorSubsystem.editor_request_begin_play; default PlayerStart (StartLocation unset)'
    report['editor_starts']=[{'label':a.get_actor_label(),'position':[a.get_actor_location().x,a.get_actor_location().y,a.get_actor_location().z]} for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if isinstance(a,u.PlayerStart)]
    sys.path.insert(0,str(root/'Scripts'))
    from OutpostObservation import LAYOUT
    from OutpostDoorVisuals import ASSET as DOOR_ASSET, MARKER as DOOR_VISUAL_TAG
    door_source = root/'Content'/(DOOR_ASSET.split('.')[0].removeprefix('/Game/')+'.uasset')
    door_source_digest = hashlib.sha256(door_source.read_bytes()).hexdigest()
    report['native_door_source']={'asset':DOOR_ASSET,'sha256':door_source_digest}
    report['observation_route_feet']=LAYOUT['route_feet']
    state = {'start':time.monotonic(),'phase':'wait','busy':False,'handle':None,'shots':set(),'sample':0.,'stop':None}
    def point(v): return [round(float(v.x),3),round(float(v.y),3),round(float(v.z),3)]
    def check(name, value, evidence): report['checks'][name] = {'passed':bool(value),'evidence':evidence}
    def actors(cls): return u.GameplayStatics.get_all_actors_of_class(state['world'],cls)
    def door_physics(door):
        result={}
        for key in ('left_closed','right_closed','left_travel','right_travel','leaf_half_extent',
                    'safety_half_extent','sensor_radius','slide_seconds','hold_open_seconds'):
            value=door.get_editor_property(key)
            result[key]=point(value) if isinstance(value,u.Vector) else float(value)
        result['blockers']=[{'extent':point(c.get_scaled_box_extent()),
                            'collision':str(c.get_collision_enabled()),'profile':str(c.get_collision_profile_name())}
                           for c in (door.left_blocker,door.right_blocker)]
        return result
    authored_doors={a.get_actor_label():door_physics(a) for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if isinstance(a,u.SSOutpostDoor)}
    report['authored_door_physics']=authored_doors
    def sample_door_visuals():
        for door in state['all_doors']:
            name=door.get_actor_label()
            if door_physics(door)!=authored_doors.get(name):state['door_physics_errors'].add(name+': settings or blocker shape changed')
            for anchor,blocker in ((door.left_leaf,door.left_blocker),(door.right_leaf,door.right_blocker)):
                if (anchor.get_world_location()-blocker.get_world_location()).length()>.05:
                    state['door_physics_errors'].add(name+': moving blocker diverged from leaf')
        for row in state['door_visuals']:
            mesh,anchor=row['actor'].static_mesh_component,row['anchor']
            moved=row['actor'].get_actor_location()-u.Vector(*row['start'])
            anchor_moved=anchor.get_world_location()-u.Vector(*row['anchor_start'])
            row['max_displacement']=max(row['max_displacement'],moved.length())
            row['max_tracking_error']=max(row['max_tracking_error'],(moved-anchor_moved).length())
            row['attachment_ok'] &= mesh.get_attach_parent()==anchor
            row['no_collision'] &= mesh.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION
    def shot(name):
        if name in state['shots']: return
        state['shots'].add(name)
        path = out/(name+'.png')
        u.SystemLibrary.execute_console_command(state['world'],'HighResShot 1600x900 filename="'+str(path)+'"',state['pc'])
        report['images'].append({'path':str(path),'game_time':u.GameplayStatics.get_time_seconds(state['world'])})
    def finish():
        if state['phase'] == 'stop': return
        state['phase']='stop'; state['stop']=time.monotonic()
        level.editor_request_end_play()
    def final_report():
        check('saved_map_unchanged',hashlib.sha256(source.read_bytes()).hexdigest()==digest,digest)
        check('save_files_unchanged',saves()==original_saves,{'directory':str(saved),'files':list(original_saves)})
        check('native_door_source_unchanged',hashlib.sha256(door_source.read_bytes()).hexdigest()==door_source_digest,report['native_door_source'])
        if 'door_visuals' in state:
            visuals=[{k:r[k] for k in ('name','attachment_ok','no_collision','max_tracking_error')} for r in state['door_visuals']]
            check('native_door_visuals_noncolliding',len(visuals)==16 and all(r['no_collision'] and r['attachment_ok'] for r in visuals),visuals)
            check('native_door_physics_preserved',not state['door_physics_errors'],sorted(state['door_physics_errors']))
        for image in report['images']:
            path=Path(image['path']); valid=path.is_file() and path.stat().st_size>24
            image['exists']=valid
            if valid: image['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        check('runtime_frames',len(report['images'])>=2 and all(i['exists'] for i in report['images']),len(report['images']))
        report['status']='PASS_SCRIPTED_MAP_ONLY' if not report['errors'] and all(c['passed'] for c in report['checks'].values()) else 'FAIL'
        report['finished_utc']=datetime.now(timezone.utc).isoformat()
        (out/'runtime.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        (out.parent/'latest.json').write_text(json.dumps({'status':report['status'],'receipt':str(out/'runtime.json')},indent=2),encoding='utf-8')
        u.log('OUTPOST_PLAY_FINISHED '+report['status']+' '+str(out))
        u.unregister_slate_post_tick_callback(state['handle'])
        u.EditorPythonScripting.set_keep_python_script_alive(False)
        u.SystemLibrary.quit_editor()
    def position_for(terminal):
        walker=state['walker']; p=terminal.get_actor_location()
        walker.character_movement.stop_movement_immediately()
        # The current wardrobe faces south at (4750,3570). Resolve its live
        # terminal position and stand in the open south approach, off the dais.
        dx,dy=(0,-160) if terminal.action==u.SSOutpostAction.CYCLE_WARDROBE else (-160,0)
        half=walker.get_component_by_class(u.CapsuleComponent).get_scaled_capsule_half_height()
        walker.set_actor_location(u.Vector(p.x+dx,p.y+dy,half+3),False,True)
        state['pc'].set_control_rotation(u.Rotator(pitch=-10,yaw=math.degrees(math.atan2(-dy,-dx))))
        report.setdefault('terminal_approaches',[]).append({'terminal':terminal.get_actor_label(),
            'terminal_position':point(p),'walker_position':point(walker.get_actor_location())})
    def tick(dt):
        if state['busy']: return
        state['busy']=True
        try:
            if state['phase']=='stop':
                if not editor.get_game_world() or time.monotonic()-state['stop']>8: final_report()
                return
            if time.monotonic()-state['start']>600: raise RuntimeError('Actual-map PIE timed out')
            if state['phase']=='wait':
                world=editor.get_game_world()
                if not world:
                    if time.monotonic()-state['start']>90: raise RuntimeError('PIE game world did not start')
                    return
                pc=u.GameplayStatics.get_player_controller(world,0); walker=u.GameplayStatics.get_player_pawn(world,0)
                if not pc or not walker: return
                state.update(world=world,pc=pc,walker=walker,t0=u.GameplayStatics.get_time_seconds(world),phase='walk')
                check('sandbox_game_mode',isinstance(u.GameplayStatics.get_game_mode(world),u.SSOutpostSandboxGameMode),u.GameplayStatics.get_game_mode(world).get_class().get_name())
                check('native_walker_controller',isinstance(walker,u.SSWalker) and isinstance(pc,u.SSOutpostSandboxController),[walker.get_class().get_name(),pc.get_class().get_name()])
                state['hero']=walker.get_component_by_class(u.SkeletalMeshComponent).get_skeletal_mesh_asset().get_path_name()
                state['initial']=point(walker.get_actor_location()); state['door_max']=0.
                starts=[{'label':a.get_actor_label(),'class':a.get_class().get_name(),'position':point(a.get_actor_location())} for a in actors(u.PlayerStart)]
                expected=next((r for r in starts if r['label']=='Start/Player approach'),None)
                check('spawn_at_authored_player_start',expected and (walker.get_actor_location()-u.Vector(*expected['position'])).length()<150,{'actual':state['initial'],'all_pie_starts':starts})
                state['ambient']=[(a,point(a.get_actor_location()),0.) for a in actors(u.SSOutpostAmbientActor) if len(a.route_points)>1]
                doors=actors(u.SSOutpostDoor)
                state['doors']=[min(doors,key=lambda a:(a.get_actor_location()-u.Vector(2600,0,0)).length())]
                state.update(all_doors=doors,door_visuals=[],door_physics_errors=set(),door_visual_sample=-1.)
                visual_actors={a.get_actor_label():a for a in actors(u.StaticMeshActor) if DOOR_VISUAL_TAG in [str(v) for v in a.tags]}
                expected=[]
                for door in doors:
                    for side in ('left','right'):
                        anchor=getattr(door,side+'_leaf')
                        for piece in ('panel','seal'):
                            name=door.get_actor_label()+'/Native '+side+' '+piece; expected.append(name)
                            if name not in visual_actors:continue
                            child=visual_actors[name]
                            state['door_visuals'].append({'actor':child,'anchor':anchor,'name':name,
                                'main':door==state['doors'][0],'start':point(child.get_actor_location()),
                                'anchor_start':point(anchor.get_world_location()),'max_displacement':0.,
                                'max_tracking_error':0.,'attachment_ok':True,'no_collision':True})
                check('native_door_visual_inventory',len(doors)==len(authored_doors)==4 and set(visual_actors)==set(expected),
                      {'expected':expected,'actual':sorted(visual_actors)})
                sample_door_visuals()
                state['animation']=[(a.character_mesh,a.get_actor_label(),float(a.character_mesh.get_position()),0.) for a in actors(u.SSOutpostAmbientActor) if not a.drone and a.character_mesh.get_skeletal_mesh_asset()]
                pc.set_control_rotation(u.Rotator(pitch=-9,yaw=0))
                u.GameplayStatics.set_game_paused(world,False)
                return
            world=state['world']; walker=state['walker']; t=u.GameplayStatics.get_time_seconds(world)-state['t0']
            state['ambient']=[(a,p,max(m,(a.get_actor_location()-u.Vector(*p)).length())) for a,p,m in state['ambient']]
            state['animation']=[(m,n,p,max(d,abs(float(m.get_position())-p))) for m,n,p,d in state['animation']]
            state['door_max']=max([state['door_max']]+[float(a.open_fraction) for a in state['doors']])
            if t-state['door_visual_sample']>.12:
                sample_door_visuals();state['door_visual_sample']=t
            if state['phase']=='walk':
                p=walker.get_actor_location()
                if t<17: walker.add_movement_input(u.Vector(1,0,0),1.,True)
                if t-state['sample']>.4:
                    report['samples'].append({'t':round(t,3),'position':point(p),'speed':walker.get_velocity().length(),'door_max':state['door_max']}); state['sample']=t
                if t>5: shot('01_MarketWalk')
                if p.x>2400 or t>14: shot('02_MainDoor')
                if t<18: return
                check('forward_walk_through_entrance',p.x>3000 and abs(p.y)<160,{'start':state['initial'],'end':point(p),'seconds':t})
                hit=u.SystemLibrary.line_trace_single_by_profile(world,p,p-u.Vector(0,0,140),'Pawn',False,[walker],u.DrawDebugTrace.NONE,True)
                values=hit.to_tuple() if hit else None
                check('walking_floor_support',bool(values and values[0] and abs(values[5].z)<5 and values[7].z>.7),str(values[5]) if values and values[0] else None)
                check('door_automatically_opened',state['door_max']>.95,{'door':state['doors'][0].get_actor_label(),'maximum':state['door_max']})
                visuals=[{k:r[k] for k in ('name','main','max_displacement','max_tracking_error','attachment_ok','no_collision')} for r in state['door_visuals']]
                moving=[r for r in visuals if r['main']]
                check('native_door_visuals_follow_opening',len(moving)==4 and all(r['max_displacement']>150 and r['max_tracking_error']<.1 and r['attachment_ok'] for r in moving),moving)
                check('native_door_visuals_noncolliding',len(visuals)==16 and all(r['no_collision'] and r['attachment_ok'] for r in visuals),visuals)
                check('native_door_physics_preserved',not state['door_physics_errors'],sorted(state['door_physics_errors']))
                anim=[{'actor':n,'max_playback_delta':round(d,3),'clip':m.get_anim_instance().get_animation_asset().get_path_name() if isinstance(m.get_anim_instance(),u.AnimSingleNodeInstance) and m.get_anim_instance().get_animation_asset() else None} for m,n,p,d in state['animation']]
                check('crew_animation_advances',sum(r['max_playback_delta']>.15 and bool(r['clip']) for r in anim)>=3,anim)
                motions=[{'name':a.get_actor_label(),'drone':bool(a.drone),'max_displacement_cm':round(m,3)} for a,p,m in state['ambient']]
                check('crew_route_moved',any(not row['drone'] and row['max_displacement_cm']>80 for row in motions),motions)
                check('drone_routes_moved',sum(row['drone'] and row['max_displacement_cm']>150 for row in motions)>=2,motions)
                state['paint']=next(a for a in actors(u.SSOutpostTerminal) if a.action==u.SSOutpostAction.CYCLE_SHIP_PAINT)
                state['ward']=next(a for a in actors(u.SSOutpostTerminal) if a.action==u.SSOutpostAction.CYCLE_WARDROBE)
                position_for(state['paint']); state.update(phase='paint',stage_time=t)
            elif state['phase']=='paint' and t-state['stage_time']>1:
                terminal=state['paint']; result=terminal.use(state['pc']); colours=[]
                for mesh in terminal.presentation_target.get_components_by_class(u.MeshComponent):
                    for mat in mesh.get_materials():
                        if isinstance(mat,u.MaterialInstanceDynamic):
                            colour=mat.get_vector_parameter_value('HullTint'); colours.append([colour.r,colour.g,colour.b])
                wanted=terminal.paint_palette[0]
                check('ship_paint_applied',result.startswith('Hull finish') and any(max(abs(v[i]-[wanted.r,wanted.g,wanted.b][i]) for i in range(3))<.001 for v in colours),{'message':result,'colours':colours})
                shot('03_PaintedShip'); state.update(phase='paint_settle',stage_time=t)
            elif state['phase']=='paint_settle' and t-state['stage_time']>1:
                position_for(state['ward']); state.update(phase='wardrobe',stage_time=t)
            elif state['phase']=='wardrobe' and t-state['stage_time']>1:
                terminal=state['ward']
                check('wardrobe_preview_access',state['pc'].focused_terminal()==terminal,{'terminal':point(terminal.get_actor_location()),'walker':point(walker.get_actor_location())})
                result=terminal.use(state['pc'])
                target=terminal.presentation_target.get_component_by_class(u.SkeletalMeshComponent)
                state['projected']=target.get_skeletal_mesh_asset().get_path_name()
                check('wardrobe_preview',result.startswith('CREW APPEARANCE'),{'message':result,'projected':state['projected']})
                state.update(phase='settle',stage_time=t)
            elif state['phase']=='settle' and t-state['stage_time']>2:
                actual=walker.get_component_by_class(u.SkeletalMeshComponent).get_skeletal_mesh_asset().get_path_name()
                check('equipped_hero_unchanged',actual==state['hero'],{'before':state['hero'],'after':actual})
                bottom=LAYOUT['route_feet'][0]; half=walker.get_component_by_class(u.CapsuleComponent).get_scaled_capsule_half_height()
                walker.character_movement.stop_movement_immediately()
                walker.set_actor_location(u.Vector(bottom[0],bottom[1],bottom[2]+half+3),False,True)
                report['observation_bottom_setup']=point(walker.get_actor_location())
                state.update(phase='stairs',stage_time=t,route_index=1,half=half)
            elif state['phase']=='stairs':
                route=LAYOUT['route_feet']; p=walker.get_actor_location(); goal=route[state['route_index']]
                dx,dy=goal[0]-p.x,goal[1]-p.y; distance=math.hypot(dx,dy); feet=p.z-state['half']
                if distance<28 and abs(feet-goal[2])<28:
                    state['route_index']+=1
                    if state['route_index']==len(route):
                        walker.character_movement.stop_movement_immediately()
                        state['pc'].set_control_rotation(u.Rotator(pitch=7,yaw=78))
                        check('natural_stair_ascent',abs(feet-LAYOUT['floor_z'])<10 and not walker.character_movement.is_falling(),{'end':point(p),'feet_z':feet,'waypoints_reached':state['route_index'],'seconds':t-state['stage_time'],'teleports_after_bottom':0})
                        state.update(phase='observation',stage_time=t)
                        return
                elif distance>1:
                    walker.add_movement_input(u.Vector(dx/distance,dy/distance,0),min(1.,distance/80.),True)
                    state['pc'].set_control_rotation(u.Rotator(pitch=-8,yaw=math.degrees(math.atan2(dy,dx))))
                if t-state['sample']>.4:
                    report['samples'].append({'phase':'stairs','t':round(t,3),'position':point(p),'waypoint':state['route_index']});state['sample']=t
                if t-state['stage_time']>45:
                    check('natural_stair_ascent',False,{'stalled_at':point(p),'waypoint':state['route_index'],'goal':goal});finish()
            elif state['phase']=='observation':
                if t-state['stage_time']>1:shot('04_ObservationGallery')
                if t-state['stage_time']>4:
                    walker.character_movement.stop_movement_immediately()
                    walker.set_actor_location(u.Vector(-2500,0,state['half']+3),False,True)
                    report['boarding_bottom_setup']=point(walker.get_actor_location())
                    state['boarding_route']=[[-2744,0,0],[-3020,0,113],[-3310,0,230],[-3600,0,230],[-4200,0,230],[-4790,0,230]]
                    state.update(phase='boarding',stage_time=t,route_index=0)
            elif state['phase']=='boarding':
                route=state['boarding_route']; p=walker.get_actor_location(); goal=route[state['route_index']]
                dx,dy=goal[0]-p.x,goal[1]-p.y; distance=math.hypot(dx,dy); feet=p.z-state['half']
                if distance<28 and abs(feet-goal[2])<28:
                    state['route_index']+=1
                    if state['route_index']==len(route):
                        walker.character_movement.stop_movement_immediately()
                        flight=next(a for a in actors(u.SSOutpostTerminal) if a.action==u.SSOutpostAction.FREE_FLIGHT)
                        near=(p-flight.get_actor_location()).length()<250
                        check('natural_walk_to_cockpit',near and not walker.character_movement.is_falling(),{'end':point(p),'feet_z':feet,'waypoints_reached':state['route_index'],'seconds':t-state['stage_time'],'teleports_after_bottom':0})
                        # FocusedTerminal invokes native range and line-of-sight validation. Never Use: it travels.
                        check('cockpit_freeflight_available',state['pc'].focused_terminal()==flight,flight.get_actor_label())
                        shot('05_CockpitWalk'); state.update(phase='cockpit',stage_time=t); return
                elif distance>1:
                    walker.add_movement_input(u.Vector(dx/distance,dy/distance,0),min(1.,distance/80.),True)
                    state['pc'].set_control_rotation(u.Rotator(pitch=-8,yaw=math.degrees(math.atan2(dy,dx))))
                if t-state['sample']>.4:
                    report['samples'].append({'phase':'boarding','t':round(t,3),'position':point(p),'waypoint':state['route_index']});state['sample']=t
                if t-state['stage_time']>45:
                    check('natural_walk_to_cockpit',False,{'stalled_at':point(p),'waypoint':state['route_index'],'goal':goal});finish()
            elif state['phase']=='cockpit' and t-state['stage_time']>3:finish()
        except Exception:
            report['errors'].append(traceback.format_exc()); u.log_error(report['errors'][-1]); finish()
        finally:
            state['busy']=False
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    state['handle']=u.register_slate_post_tick_callback(tick)
    # Installed LevelEditorSubsystem explicitly requests the current Slate viewport, not a new window.
    level.editor_request_begin_play()

if __name__=='__main__':
    main()
