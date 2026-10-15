"""Run only in an isolated, rendered PIE with the saved waitress/Joy station loaded.
Moves and hides the test player temporarily, starts five real native service cases,
and records body/garment pose agreement plus ordinary viewport captures in Saved.
Restores the player, HUD, view target and temporary viewport size on completion/error.
Does not save map/assets or claim natural input, audio, performance or visual acceptance.
Do not run alongside another capture or while an owner is using this PIE world.
"""
import unreal as u,time,json,math,traceback
from pathlib import Path
sv_out=Path(u.Paths.project_saved_dir())/'BarServiceReview'/time.strftime('%Y%m%dT%H%M%S');sv_out.mkdir(parents=True,exist_ok=False)
sv_world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world();sv_pc=u.GameplayStatics.get_player_controller(sv_world,0);sv_gm=u.GameplayStatics.get_game_mode(sv_world);sv_guest=u.GameplayStatics.get_player_pawn(sv_world,0)
sv_waitress=next(a for a in u.GameplayStatics.get_all_actors_of_class(sv_world,u.SSBarCrew) if not a.is_bartender);sv_joy=next(a for a in u.GameplayStatics.get_all_actors_of_class(sv_world,u.SSBarCrew) if a.is_bartender)
assert sv_gm.get_class().get_name()=='SSGameMode' and sv_guest.get_class().get_name()=='SSWalker'
assert not sv_waitress.get_editor_property('hidden') and sv_waitress.character_mesh.is_visible()
assert 'TalkType:Waitress' in [str(t) for t in sv_waitress.character_mesh.component_tags]
sv_home=sv_waitress.get_actor_location();sv_old_pawn=sv_guest.get_actor_transform();sv_old_rotation=sv_pc.get_control_rotation();sv_old_target=sv_pc.get_view_target();sv_hud=sv_pc.get_hud().show_hud;sv_hidden=sv_guest.get_editor_property('hidden')
sv_pc.get_hud().show_hud=False;sv_guest.set_actor_hidden_in_game(True)
sv_prev=set(a.get_path_name() for a in u.GameplayStatics.get_all_actors_of_class(sv_world,u.CameraActor));u.SystemLibrary.execute_console_command(sv_world,'summon CameraActor',sv_pc)
sv_cam=next(a for a in u.GameplayStatics.get_all_actors_of_class(sv_world,u.CameraActor) if a.get_path_name() not in sv_prev);sv_cam.camera_component.set_field_of_view(48.);sv_pc.set_view_target_with_blend(sv_cam,0.)
sv_jobs=[('order',0),('shared_drink',1),('seat_dismiss',2),('seat_leave',2),('order_leave',0)]
sv_state={'index':0,'phase':'prepare','at':time.monotonic(),'records':[],'last_sample':0,'max_bone_delta_cm':0.,'postprocess_motion_cm':0.,'samples':0,'shots':0}
sv_options=u.AnimPoseEvaluationOptions();sv_options.evaluation_type=u.AnimDataEvalType.COMPRESSED
u.SystemLibrary.execute_console_command(sv_world,'SS.RenderedView.Begin',sv_pc)
def sv_end():
 sv_guest.set_actor_transform(sv_old_pawn,False,True);sv_guest.set_actor_hidden_in_game(sv_hidden);sv_pc.set_control_rotation(sv_old_rotation);sv_pc.set_view_target_with_blend(sv_old_target,0.);sv_pc.get_hud().show_hud=sv_hud
 u.SystemLibrary.execute_console_command(sv_world,'SS.RenderedView.End',sv_pc);sv_cam.destroy_actor();u.unregister_slate_post_tick_callback(sv_handle)
def sv_tick(dt):
 try:
  now=time.monotonic();idx=sv_state['index'];phase=sv_state['phase'];name,action=sv_jobs[idx]
  if phase=='prepare':
   sv_guest.set_actor_location(u.Vector(3830,-3540,85),False,True);sv_pc.set_control_rotation(u.MathLibrary.find_look_at_rotation(sv_guest.get_actor_location(),sv_waitress.get_actor_location()))
   sv_state.update(phase='request',at=now);return
  if phase=='request':
   if now-sv_state['at']<3.5:return
   assert sv_waitress.request_service(action,sv_guest), sv_waitress.service_notice
   sv_state.update(phase='confirm',at=now);return
  if phase=='confirm':
   if now-sv_state['at']<.5:return
   assert sv_waitress.service_state!=u.SSBarServiceState.AVAILABLE,('Native service request was not accepted',name,sv_waitress.service_notice)
   rec={'name':name,'request_route':'SSBarCrew.RequestService','states':[],'samples':[]};sv_state['records'].append(rec)
   sv_state.update(phase='run',at=now,last=None,triggered=False,shot_states=set());return
  rec=sv_state['records'][-1];state=sv_waitress.service_state.name;elapsed=now-sv_state['at']
  if sv_state['last']!=state:rec['states'].append({'time':elapsed,'state':state});sv_state.update(last=state,state_at=now);u.SystemLibrary.execute_console_command(sv_world,'SS.RenderedView.Size',sv_pc)
  focus=sv_joy if state=='WAITING_FOR_BAR' else sv_waitress;p=focus.get_actor_location();offset=focus.get_actor_forward_vector()*250+focus.get_actor_right_vector()*90+u.Vector(0,0,65)
  sv_cam.set_actor_location_and_rotation(p+offset,u.MathLibrary.find_look_at_rotation(p+offset,p+u.Vector(0,0,20)),False,False)
  if now-sv_state['last_sample']>.1:
   body=sv_waitress.character_mesh;cloth=sv_waitress.corset
   row={'time':elapsed,'state':state,'position':p.to_tuple(),'glass':sv_waitress.glass.is_visible(),'delivered':sv_waitress.served_glass.is_visible(),'bar_glass':sv_joy.glass.is_visible(),'bar_bottle':sv_joy.bottle.is_visible(),'bones':{}}
   for bone in ['breast_l','breast_r','spine_03']:
    a=body.get_socket_transform(bone,u.RelativeTransformSpace.RTS_COMPONENT);b=cloth.get_socket_transform(bone,u.RelativeTransformSpace.RTS_COMPONENT)
    delta=(a.translation-b.translation).length();sv_state['max_bone_delta_cm']=max(sv_state['max_bone_delta_cm'],delta);row['bones'][bone]=a.translation.to_tuple()
   clip=body.get_anim_instance().get_animation_asset()
   if isinstance(clip,u.AnimSequence):
    raw=u.AnimPoseExtensions.get_anim_pose_at_time(clip,body.get_position(),sv_options)
    parent_raw=u.AnimPoseExtensions.get_bone_pose(raw,'spine_03',u.AnimPoseSpaces.WORLD);parent_actual=body.get_socket_transform('spine_03',u.RelativeTransformSpace.RTS_COMPONENT)
    for bone in ['breast_l','breast_r']:
     r=u.MathLibrary.make_relative_transform(u.AnimPoseExtensions.get_bone_pose(raw,bone,u.AnimPoseSpaces.WORLD),parent_raw)
     a=u.MathLibrary.make_relative_transform(body.get_socket_transform(bone,u.RelativeTransformSpace.RTS_COMPONENT),parent_actual)
     difference=(a.translation-r.translation).length();sv_state['postprocess_motion_cm']=max(sv_state['postprocess_motion_cm'],difference);row[bone+'_postprocess_cm']=difference
   rec['samples'].append(row);sv_state['samples']+=1;sv_state['last_sample']=now
  if now-sv_state['state_at']>2 and state not in sv_state['shot_states']:
   u.SystemLibrary.execute_console_command(sv_world,'Shot filename="'+str(sv_out/(name+'_'+state+'.png'))+'" -nosuffix',sv_pc);sv_state['shot_states'].add(state);sv_state['shots']+=1
  if name=='seat_dismiss' and state=='SEATED' and now-sv_state['state_at']>6 and not sv_state['triggered']:
   sv_pc.set_control_rotation(u.MathLibrary.find_look_at_rotation(sv_guest.get_actor_location(),sv_waitress.get_actor_location()));sv_waitress.request_service(3,sv_guest);sv_state['triggered']=True
  if (name=='seat_leave' and state=='SEATED' or name=='order_leave' and state=='WAITING_FOR_BAR') and now-sv_state['state_at']>4 and not sv_state['triggered']:
   sv_guest.set_actor_location(u.Vector(5000,-3000,85),False,True);sv_state['triggered']=True
  assert elapsed<90,(name,state,sv_waitress.service_notice)
  if elapsed>2 and state=='AVAILABLE':
   states=[r['state'] for r in rec['states']];required=['GOING_TO_BAR','WAITING_FOR_BAR','RETURNING_TO_GUEST','SERVING','RETURNING_HOME'] if name in ['order','shared_drink'] else ['JOINING_TABLE','SEATED','RETURNING_HOME'] if name.startswith('seat') else ['GOING_TO_BAR','WAITING_FOR_BAR','RETURNING_HOME']
   if name=='shared_drink':required.append('DRINKING')
   assert all(n in states for n in required),(name,states)
   if name in ['order','shared_drink']:assert sv_waitress.served_glass.is_visible()
   rec.update(passed=True,notice=sv_waitress.service_notice);sv_state['index']+=1;sv_state['phase']='prepare'
   (sv_out/'Progress.json').write_text(json.dumps({'completed':sv_state['index'],'samples':sv_state['samples'],'max_body_cloth_bone_delta_cm':sv_state['max_bone_delta_cm']},indent=2))
   if sv_state['index']==len(sv_jobs):
    (sv_out/'Result.json').write_text(json.dumps({'passed':True,'records':sv_state['records'],'samples':sv_state['samples'],'max_body_cloth_bone_delta_cm':sv_state['max_bone_delta_cm'],'postprocess_enabled':not sv_waitress.character_mesh.get_editor_property('disable_post_process_blueprint'),'physics':sv_waitress.character_mesh.skeletal_mesh_asset.physics_asset.get_path_name(),'max_postprocess_breast_motion_cm':sv_state['postprocess_motion_cm'],'physical_input_verified':False,'audio_verified':False},indent=2));sv_end()
 except Exception:
  (sv_out/'Error.txt').write_text(traceback.format_exc());(sv_out/'Failed.json').write_text(json.dumps(sv_state['records'],indent=2));sv_end()
sv_handle=u.register_slate_post_tick_callback(sv_tick)
