"""Saved counter pickup and table service on isolated PIE, including cancellation and fallback.
No native saves. Owner physical input, audible mix and final appearance remain separate.
"""
from pathlib import Path
import json,math,os,time,traceback
import unreal as u
OUT=Path(os.environ.get('SS_COUNTER_REVIEW_OUTPUT',str(Path(u.Paths.project_saved_dir())/'CounterPickupReview'/time.strftime('%Y%m%dT%H%M%S'))));OUT.mkdir(parents=True,exist_ok=False)
w=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world();assert w
pc=u.GameplayStatics.get_player_controller(w,0);u.GameplayStatics.get_game_mode(w).close_panel()
actors=u.GameplayStatics.get_all_actors_of_class(w,u.Actor)
a=next(x for x in actors if x.get_actor_label()=='Crew/Bar waitress')
j=next(x for x in actors if x.get_actor_label()=='Crew/Lounge guest')
table=next(x for x in actors if x.get_actor_label()=='Crew/Waitress table contact')
offset=j.get_actor_location()-u.Vector(4150,-4140,85)
guest=u.GameplayStatics.get_player_pawn(w,0)
old=dict(guest=guest.get_actor_transform(),hidden=guest.get_editor_property('hidden'),view=pc.get_view_target(),hud=pc.get_hud().show_hud,breaks=a.ambient_bar_breaks,clip=a.tray_set_down_animation,window=a.tray_set_down_window,pose=table.has_set_down_pose,serve=table.serve_from.get_relative_transform(),drink=table.drink_contact.get_relative_transform(),waypoints=list(a.service_waypoints))
counterold=dict(pickup=a.pickup_offset,clip=a.tray_pickup_animation,window=a.tray_pickup_window,ready=a.tray_ready_seconds,delivery=j.counter_delivery_animation,release=j.counter_release_seconds,contact=j.counter_glass_transform)
assert a.tray_pickup_animation and j.counter_delivery_animation, 'Review requires saved counter pickup setup'
original_delivery=j.counter_delivery_animation;original_pickup=a.tray_pickup_animation;original_pour=j.actions[0].clip
a.ambient_bar_breaks=False
assert a.tray_set_down_animation and table.has_set_down_pose, 'Review requires the saved set-down setup'
guest.set_actor_hidden_in_game(True);pc.get_hud().show_hud=False
existing={x.get_path_name() for x in u.GameplayStatics.get_all_actors_of_class(w,u.CameraActor)}
u.SystemLibrary.execute_console_command(w,'summon CameraActor',pc)
cam=next(x for x in u.GameplayStatics.get_all_actors_of_class(w,u.CameraActor) if x.get_path_name() not in existing)
pc.set_view_target_with_blend(cam,0);cam.camera_component.set_constraint_aspect_ratio(False);cam.camera_component.set_field_of_view(54.)
pos=u.Vector(3500,-3370,140)+offset;focus=u.Vector(3730,-3550,90)+offset
cam.set_actor_location_and_rotation(pos,u.MathLibrary.find_look_at_rotation(pos,focus),False,True)
u.SystemLibrary.execute_console_command(w,'SS.RenderedView.End',pc);u.SystemLibrary.execute_console_command(w,'SS.RenderedView.Begin',pc);u.SystemLibrary.execute_console_command(w,'SS.RenderedView.Size',pc)
jobs=[('order',0),('shared',1),('cancel_counter',0),('invalid_counter_window',0),('missing_delivery',0)]
s=dict(index=0,phase='prepare',at=time.monotonic(),records=[])
def finish(passed,error=None):
    u.unregister_slate_post_tick_callback(handle)
    a.pickup_offset=counterold['pickup'];a.tray_pickup_animation=counterold['clip'];a.tray_pickup_window=counterold['window'];a.tray_ready_seconds=counterold['ready'];j.counter_delivery_animation=counterold['delivery'];j.counter_release_seconds=counterold['release'];j.counter_glass_transform=counterold['contact']
    a.ambient_bar_breaks=old['breaks'];a.reset_bar_break_timer();a.tray_set_down_animation=old['clip'];a.tray_set_down_window=old['window']
    a.service_waypoints=old['waypoints']
    table.has_set_down_pose=old['pose'];table.serve_from.set_relative_transform(old['serve'],False,True);table.drink_contact.set_relative_transform(old['drink'],False,True)
    guest.set_actor_transform(old['guest'],False,True);guest.set_actor_hidden_in_game(old['hidden'])
    pc.set_view_target_with_blend(old['view'],0);pc.get_hud().show_hud=old['hud'];cam.destroy_actor()
    u.SystemLibrary.execute_console_command(w,'SS.RenderedView.End',pc)
    (OUT/'ServiceChecks.json').write_text(json.dumps(dict(passed=passed,error=error,records=s['records'],saved_assets=False),indent=2),encoding='utf-8')
def tick(dt):
    try:
        now=time.monotonic();name,action=jobs[s['index']]
        if s['phase']=='prepare':
            assert a.service_state.name=='AVAILABLE'
            u.SystemLibrary.execute_console_command(w,'SS.RenderedView.End',pc);u.SystemLibrary.execute_console_command(w,'SS.RenderedView.Begin',pc);u.SystemLibrary.execute_console_command(w,'SS.RenderedView.Size',pc)
            a.tray_set_down_window=u.Vector2D(.7,2.05);a.tray_pickup_window=u.Vector2D(2.4,1.2) if name=='invalid_counter_window' else u.Vector2D(1.2,2.4);j.counter_delivery_animation=None if name=='missing_delivery' else original_delivery
            guest.set_actor_location(u.Vector(3830,-3540,85)+offset,False,True)
            s.update(phase='request',at=now);return
        if s['phase']=='request':
            if now-s['at']<1:return
            assert a.request_service(action,guest),(name,a.service_notice)
            s['records'].append(dict(name=name,states=[],samples=[],transfers=[],shots=[]))
            s.update(phase='run',at=now,last_state=None,prev=None,cancelled=False);return
        r=s['records'][-1];state=a.service_state.name;elapsed=now-s['at'];t=a.character_mesh.get_position()
        if state!=s['last_state']:r['states'].append(state);s['last_state']=state
        p=a.glass.get_world_location();delivered=a.served_glass.is_visible();visible=a.glass.is_visible()
        parent=a.glass.get_attach_parent().get_name()
        row=dict(time=elapsed,state=state,pose=t,glass=list(p.to_tuple()),visible=visible,delivered=delivered,parent=parent,actor=list(a.get_actor_location().to_tuple()))
        if state=='SERVING' and name!='invalid_window_fallback':
            assert a.character_mesh.get_anim_instance().get_animation_asset()==a.tray_set_down_animation
            assert a.serving_tray.is_visible()
            tr=a.serving_tray.get_world_transform();head=a.character_mesh.get_socket_location('head');v=head-tr.translation
            row['head_clearance_cm']=math.hypot(max(0,math.hypot(v.x,v.y)-17),max(0,abs(v.z)-1))-13
            row['tray_up_z']=tr.rotation.rotate_vector(u.Vector(0,0,1)).z
            assert row['head_clearance_cm']>2,(name,'head/tray',row)
            assert row['tray_up_z']>.995,(name,'tray level',row)
            if .9<t<1.95:assert parent=='CharacterMesh' and str(a.glass.get_attach_socket_name())==str(a.drink_hand)
            if 2.15<t:assert delivered and not visible
            for tag,when in [('pickup',.76),('lowering',1.4),('release',2.06),('recovery',2.7)]:
                if t>=when and tag not in r['shots']:
                    r['shots'].append(tag);u.SystemLibrary.execute_console_command(w,'Shot filename="'+str(OUT/(name+'_'+tag+'.png'))+'" -nosuffix',pc)
            if name=='cancel_setdown' and t>1.2 and not s['cancelled']:
                assert a.request_service(3,guest);s['cancelled']=True
        if state=='DRINKING':
            assert visible and parent=='CharacterMesh' and str(a.glass.get_attach_socket_name())==str(a.drink_hand)
        prev=s['prev']
        if prev and state=='SERVING':
            if prev['parent']!=parent and visible:
                r['transfers'].append(dict(kind='tray_to_hand',distance_cm=(p-u.Vector(*prev['glass'])).length(),pose=t))
            if delivered and not prev['delivered']:
                r['transfers'].append(dict(kind='hand_to_table',distance_cm=(a.served_glass.get_world_location()-u.Vector(*prev['glass'])).length(),pose=t))
        extend_counter(row,r);r['samples'].append(row);s['prev']=row
        assert elapsed<100,(name,state,a.service_notice)
        if state=='AVAILABLE' and elapsed>2:
            assert ('COLLECTING_DRINK' if name=='cancel_counter' else 'SERVING') in r['states'],(name,r['states'],a.service_notice)
            assert not a.serving_tray.is_visible() and not visible
            if name=='cancel_counter':assert s['cancelled'] and not delivered and not j.served_glass.is_visible()
            else:assert delivered
            if name=='shared':assert 'DRINKING' in r['states']
            if name in ['order','shared']:
                assert {x['kind'] for x in r['transfers']}=={'tray_to_hand','hand_to_table'},r['transfers']
                assert max(x['distance_cm'] for x in r['transfers'])<6,r['transfers']
            check_counter(r);r.update(passed=True,notice=a.service_notice);s['index']+=1;s['phase']='prepare'
            if s['index']==len(jobs):finish(True)
    except Exception:finish(False,traceback.format_exc())

def vec(p):return list(p.to_tuple())
def extend_counter(row,r):
    name=r['name'];state=row['state'];t=row['pose']
    row['counter']=vec(j.served_glass.get_world_location());row['counter_visible']=j.served_glass.is_visible();row['joy_glass']=vec(j.glass.get_world_location());row['joy_visible']=j.glass.is_visible();row['joy_pose']=j.character_mesh.get_position();row['tray_visible']=a.serving_tray.is_visible();row['tray']=vec(a.serving_tray.get_world_location())
    prev=s['prev'];r.setdefault('counter_transfers',[])
    if prev:
        if row['counter_visible'] and not prev.get('counter_visible',False):r['counter_transfers'].append(dict(kind='joy_to_counter',cm=math.dist(row['counter'],prev['joy_glass'])))
        if state=='COLLECTING_DRINK' and row['visible'] and not prev['visible']:r['counter_transfers'].append(dict(kind='counter_to_hand',cm=math.dist(row['glass'],prev['counter'])))
        if state=='COLLECTING_DRINK' and row['visible'] and prev['parent']!=row['parent']:r['counter_transfers'].append(dict(kind='hand_to_tray',cm=math.dist(row['glass'],prev['glass'])))
    if state=='COLLECTING_DRINK':
        assert a.character_mesh.get_anim_instance().get_animation_asset()==original_pickup
        if t>.5:assert row['tray_visible']
        if 1.3<t<2.3:assert row['visible'] and row['parent']=='CharacterMesh' and not row['counter_visible']
        if t>2.5:assert row['visible'] and row['parent']=='ServingTray'
        head=a.character_mesh.get_socket_location('head');v=head-a.serving_tray.get_world_location()
        if row['tray_visible']:
            row['head_clearance_cm']=math.hypot(max(0,math.hypot(v.x,v.y)-17),max(0,abs(v.z)-1))-13
            assert row['head_clearance_cm']>2,row
        if name=='cancel_counter' and t>1.6 and not s['cancelled']:
            guest.set_actor_location(a.get_actor_location()+u.Vector(0,320,0),False,True)
            assert a.request_service(3,guest);s['cancelled']=True
    if state=='SERVING':
        p=u.Vector(3500,-3370,140)+offset;cam.set_actor_location_and_rotation(p,u.MathLibrary.find_look_at_rotation(p,u.Vector(3730,-3550,90)+offset),False,True)
    if state in ['WAITING_FOR_BAR','COLLECTING_DRINK']:
        p=u.Vector(4000,-3820,155)+offset;cam.set_actor_location_and_rotation(p,u.MathLibrary.find_look_at_rotation(p,u.Vector(4180,-4070,113)+offset),False,True)
        for tag,ready in [('counter_release',row['counter_visible']),('counter_pickup',state=='COLLECTING_DRINK' and t>1.25),('counter_tray',state=='COLLECTING_DRINK' and t>2.45)]:
            if ready and tag not in r['shots']:r['shots'].append(tag);u.SystemLibrary.execute_console_command(w,'Shot filename="'+str(OUT/(name+'_'+tag+'.png'))+'" -nosuffix',pc)
def check_counter(r):
    assert j.actions[0].clip==original_pour
    assert not j.served_glass.is_visible()
    if r['name'] in ['order','shared']:
        assert 'COLLECTING_DRINK' in r['states']
        assert {v['kind'] for v in r['counter_transfers']}=={'joy_to_counter','counter_to_hand','hand_to_tray'},r['counter_transfers']
        assert max(v['cm'] for v in r['counter_transfers'])<6,r['counter_transfers']
    if r['name'] in ['invalid_counter_window','missing_delivery']:assert 'COLLECTING_DRINK' not in r['states']

handle=u.register_slate_post_tick_callback(tick)
