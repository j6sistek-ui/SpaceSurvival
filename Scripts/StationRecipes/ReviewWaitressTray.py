"""Review optional tray service in an isolated, rendered PIE with the saved bar loaded.
Checks complete normal/shared orders, cancellation, and missing/incompatible tray data.
Restores temporary guest/camera/HUD/config changes; saves no map, asset or owner save.
Native scripted evidence only: not physical input, audible mix or packaged acceptance.
Do not run alongside another capture or in the owner's active Play session.
"""
from pathlib import Path
import json,os,time,traceback
import unreal as u
D=Path(os.environ.get('SS_TRAY_REVIEW_OUTPUT',str(Path(u.Paths.project_saved_dir())/'TrayServiceReview'/time.strftime('%Y%m%dT%H%M%S'))))
D.mkdir(parents=True,exist_ok=False)
bw=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world();assert bw
bp=u.GameplayStatics.get_player_controller(bw,0);bg=u.GameplayStatics.get_game_mode(bw);bg.close_panel()
ba=u.GameplayStatics.get_all_actors_of_class(bw,u.Actor)
joy=next(a for a in ba if a.get_actor_label()=='Crew/Lounge guest')
astra=next(a for a in ba if a.get_actor_label()=='Crew/Bar waitress')
offset=joy.get_actor_location()-u.Vector(4150,-4140,85)
old_view=bp.get_view_target();old_hud=bp.get_hud().show_hud
before_cam={a.get_path_name() for a in u.GameplayStatics.get_all_actors_of_class(bw,u.CameraActor)}
u.SystemLibrary.execute_console_command(bw,'summon CameraActor',bp)
bcam=next(a for a in u.GameplayStatics.get_all_actors_of_class(bw,u.CameraActor) if a.get_path_name() not in before_cam)
bp.set_view_target_with_blend(bcam,0.);bp.get_hud().show_hud=False

guest=u.GameplayStatics.get_player_pawn(bw,0);guest_old=guest.get_actor_transform();guest_hidden=guest.get_editor_property('hidden')
guest.set_actor_hidden_in_game(True);bcam.camera_component.set_constraint_aspect_ratio(False)
settings={'breaks':astra.ambient_bar_breaks,'carry':astra.tray_carry_animation,'serve':astra.tray_serve_animation,'hand':astra.tray_hand}
astra.ambient_bar_breaks=False
jobs=[('order',0),('shared_drink',1),('cancel_carry',0),('missing_clip',0),('wrong_skeleton',0),('missing_socket',0)]
check={'index':0,'phase':'prepare','time':time.monotonic(),'last_sample':0,'records':[]}
def finish_checks(passed,error=None):
    u.unregister_slate_post_tick_callback(service_check_h)
    astra.ambient_bar_breaks=settings['breaks'];astra.tray_carry_animation=settings['carry'];astra.tray_serve_animation=settings['serve'];astra.tray_hand=settings['hand']
    astra.serving_tray.attach_to_component(astra.character_mesh,settings['hand'],u.AttachmentRule.KEEP_RELATIVE,u.AttachmentRule.KEEP_RELATIVE,u.AttachmentRule.KEEP_RELATIVE,False)
    astra.serving_tray.set_relative_transform(astra.tray_grip,False,True)
    guest.set_actor_transform(guest_old,False,True);guest.set_actor_hidden_in_game(guest_hidden)
    bp.set_view_target_with_blend(old_view,0.);bp.get_hud().show_hud=old_hud;bcam.destroy_actor();u.SystemLibrary.execute_console_command(bw,'SS.RenderedView.End',bp)
    (D/'ServiceChecks.json').write_text(json.dumps({'passed':passed,'error':error,'records':check['records'],'physical_input_verified':False,'audio_verified':False},indent=2))
def service_check_tick(dt):
    try:
        now=time.monotonic();name,action=jobs[check['index']]
        if check['phase']=='prepare':
            assert astra.service_state.name=='AVAILABLE'
            astra.tray_carry_animation=None if name=='missing_clip' else joy.actions[1].clip if name=='wrong_skeleton' else settings['carry']
            astra.tray_hand='MissingTraySocket' if name=='missing_socket' else settings['hand']
            guest.set_actor_location(u.Vector(3830,-3540,85)+offset,False,True)
            check.update(phase='request',time=now);return
        if check['phase']=='request':
            if now-check['time']<1:return
            assert astra.request_service(action,guest),(name,astra.service_notice)
            check['records'].append({'name':name,'states':[],'samples':[],'shots':[]})
            check.update(phase='run',time=now,last_state=None,triggered=False);return
        rec=check['records'][-1];state=astra.service_state.name;elapsed=now-check['time']
        if state!=check['last_state']:
            rec['states'].append(state);check.update(last_state=state,state_at=now)
            u.SystemLibrary.execute_console_command(bw,'SS.RenderedView.End',bp);u.SystemLibrary.execute_console_command(bw,'SS.RenderedView.Begin',bp);u.SystemLibrary.execute_console_command(bw,'SS.RenderedView.Size',bp)
        p=astra.get_actor_location();pos=p+astra.get_actor_forward_vector()*240+astra.get_actor_right_vector()*95+u.Vector(0,0,65)
        bcam.set_actor_location_and_rotation(pos,u.MathLibrary.find_look_at_rotation(pos,p+u.Vector(0,0,20)),False,False);bcam.camera_component.set_field_of_view(48.)
        active=state in ['RETURNING_TO_GUEST','SERVING'];expected_tray=active and name in ['order','shared_drink','cancel_carry']
        if active:
            clip=astra.character_mesh.get_anim_instance().get_animation_asset()
            target=(settings['carry'] if state=='RETURNING_TO_GUEST' else settings['serve']) if expected_tray else (astra.carry_animation if state=='RETURNING_TO_GUEST' else astra.serve_animation)
            assert clip==target,(name,state,'first-frame clip',clip)
        if now-check['state_at']>.15:
            assert astra.serving_tray.is_visible()==expected_tray,(name,state,'tray visibility')
            if active:
                assert astra.glass.get_attach_parent()==(astra.serving_tray if expected_tray else astra.character_mesh),(name,state,'glass parent')
            if state=='DRINKING':
                assert astra.glass.get_attach_parent()==astra.character_mesh and str(astra.glass.get_attach_socket_name())==str(astra.drink_hand)
                assert astra.character_mesh.get_anim_instance().get_animation_asset()==astra.drink_animation
        tr=astra.serving_tray.get_world_transform();up=tr.rotation.rotate_vector(u.Vector(0,0,1))
        if expected_tray:
            assert up.z>.995,(name,state,'tray tilt including pickup',up.z)
            rec['tray_frames_checked']=rec.get('tray_frames_checked',0)+1
        if now-check['last_sample']>.1:
            row={'time':elapsed,'state':state,'tray':astra.serving_tray.is_visible(),'glass':astra.glass.is_visible(),'delivered':astra.served_glass.is_visible(),'tray_up':list(up.to_tuple()),'position':list(p.to_tuple()),'cloth_bone_delta_cm':max((astra.character_mesh.get_socket_location(b)-astra.corset.get_socket_location(b)).length() for b in ['breast_l','breast_r','spine_03'])}
            rec['samples'].append(row);check['last_sample']=now
        if active and now-check['state_at']>.8 and state not in rec['shots']:
            rec['shots'].append(state);u.SystemLibrary.execute_console_command(bw,'Shot filename="'+str(D/(name+'_'+state+'.png'))+'" -nosuffix',bp)
        if name=='cancel_carry' and state=='RETURNING_TO_GUEST' and now-check['state_at']>1 and not check['triggered'] and (astra.get_actor_location()-guest.get_actor_location()).length()<390:
            assert astra.request_service(3,guest);check['triggered']=True
        assert elapsed<100,(name,state,astra.service_notice)
        if state=='AVAILABLE' and elapsed>2:
            required=['GOING_TO_BAR','WAITING_FOR_BAR','RETURNING_TO_GUEST','RETURNING_HOME']
            if name!='cancel_carry':required.append('SERVING');assert astra.served_glass.is_visible()
            else:assert check['triggered'] and 'SERVING' not in rec['states']
            if name=='shared_drink':required.append('DRINKING')
            assert all(s in rec['states'] for s in required),(name,rec['states'])
            assert not astra.serving_tray.is_visible() and not astra.glass.is_visible()
            assert astra.glass.get_attach_parent()==astra.character_mesh and str(astra.glass.get_attach_socket_name())==str(astra.glass_hand)
            rec.update(passed=True,notice=astra.service_notice);check['index']+=1;check['phase']='prepare'
            (D/'ServiceProgress.json').write_text(json.dumps({'completed':check['index'],'last_case':name,'samples':sum(len(r['samples']) for r in check['records'])},indent=2))
            if check['index']==len(jobs):finish_checks(True)
    except Exception:finish_checks(False,traceback.format_exc())
service_check_h=u.register_slate_post_tick_callback(service_check_tick)
