"""Isolated rendered PIE review of Astra/Joy and the side chat panel. Saves no assets.
Run only in a disposable review session with the normal station/player loaded.
Writes Saved/AstraSocialReview; restores the review view/player when finished.
Native scripted evidence does not establish physical input, audio or frame-rate acceptance.
"""
import unreal as u,json,time,traceback,math
from pathlib import Path
bcdir=Path(u.Paths.project_saved_dir())/'AstraSocialReview';bcdir.mkdir(exist_ok=True)
bcw=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world();bcg=u.GameplayStatics.get_game_mode(bcw);bcpc=u.GameplayStatics.get_player_controller(bcw,0);bch=u.GameplayStatics.get_player_pawn(bcw,0);bcg.close_panel();assert 'UEDPIE_' in bcw.get_path_name(), 'Use an isolated editor PIE session'
bca=next(a for a in u.GameplayStatics.get_all_actors_of_class(bcw,u.SSBarCrew) if not a.is_bartender);bcj=next(a for a in u.GameplayStatics.get_all_actors_of_class(bcw,u.SSBarCrew) if a.is_bartender)
bcold=(bch.get_actor_transform(),bcpc.get_control_rotation(),bcpc.get_view_target(),bch.get_editor_property('hidden'))
bch.set_actor_location(u.Vector(3870,-3530,85),False,True);bch.set_actor_hidden_in_game(True)
bcprev=set(x.get_path_name() for x in u.GameplayStatics.get_all_actors_of_class(bcw,u.CameraActor));u.SystemLibrary.execute_console_command(bcw,'summon CameraActor',bcpc);bccam=next(x for x in u.GameplayStatics.get_all_actors_of_class(bcw,u.CameraActor) if x.get_path_name() not in bcprev)
bccam.camera_component.set_field_of_view(58.);bccam.set_actor_location_and_rotation(u.Vector(3850,-3650,182),u.MathLibrary.find_look_at_rotation(u.Vector(3850,-3650,182),u.Vector(4100,-4000,132)),False,True);bcpc.set_view_target_with_blend(bccam,0.)
u.SystemLibrary.execute_console_command(bcw,'SS.RenderedView.Begin',bcpc);u.SystemLibrary.execute_console_command(bcw,'SS.RenderedView.Size',bcpc)
bcnow=u.GameplayStatics.get_time_seconds(bcw);bcg.chat_lines.clear();bcg.chat_lines.extend([u.SSChatLine(speaker='Astra' if i%2 else 'You',text=('This is an older message that should scroll away.' if i<10 else 'I found my home on this station. Joy makes the drinks; I bring them to your table. Would you like to stay and talk?' if i==10 else 'LongToken_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'),shown_at=bcnow) for i in range(12)])
bcinterval=bca.bar_break_interval;bcambient=bca.ambient_bar_breaks;bca.ambient_bar_breaks=False;bca.bar_break_interval=u.Vector2D(1,1);bca.reset_bar_break_timer();bcstate={'phase':'ui','at':time.monotonic(),'start':time.monotonic(),'cycles':[],'rows':[],'last':None,'seen':set(),'shot':False,'delta':0.,'eye':0.,'lastsample':0}
def bcfinish():
 bca.ambient_bar_breaks=bcambient;bca.bar_break_interval=bcinterval;bca.reset_bar_break_timer();bch.set_actor_transform(bcold[0],False,True);bch.set_actor_hidden_in_game(bcold[3]);bcpc.set_control_rotation(bcold[1]);bcpc.set_view_target_with_blend(bcold[2],0.);bccam.destroy_actor();u.SystemLibrary.execute_console_command(bcw,'SS.RenderedView.End',bcpc);u.unregister_slate_post_tick_callback(bchandle)
def bctick(dt):
 try:
  now=time.monotonic();elapsed=now-bcstate['at']
  if bcstate['phase']=='ui':
   if elapsed>4 and not bcstate['shot']:u.SystemLibrary.execute_console_command(bcw,'Shot filename="'+str(bcdir/'Chat_LongHistory.png')+'" -nosuffix',bcpc);bcstate['shot']=True
   if elapsed>6:
    bcg.chat_lines.clear();bca.ambient_bar_breaks=True;bcstate.update(phase='social',at=now,last=None,shot=False);bcstate['cycles'].append({'states':[],'lines':[]})
   return
  state=bca.service_state.name;rec=bcstate['cycles'][-1]
  if state!=bcstate['last']:rec['states'].append({'t':elapsed,'state':state});bcstate['last']=state
  for line in bcg.chat_lines:
   key=(line.speaker,line.text)
   if key not in bcstate['seen']:
    bcstate['seen'].add(key);rec['lines'].append({'speaker':line.speaker,'text':line.text,'t':elapsed})
  if now-bcstate['lastsample']>.15:
   row={'t':elapsed,'cycle':len(bcstate['cycles']),'state':state,'astra_glass':bca.glass.is_visible(),'joy_glass':bcj.glass.is_visible(),'astra':bca.get_actor_location().to_tuple(),'joy':bcj.get_actor_location().to_tuple()}
   for bone in ['breast_l','breast_r','spine_03']:
    delta=(bca.character_mesh.get_socket_location(bone)-bca.corset.get_socket_location(bone)).length();bcstate['delta']=max(bcstate['delta'],delta)
   delta=(bca.character_mesh.get_socket_location('head')-bca.eyes.get_world_location()).length();bcstate['eye']=max(bcstate['eye'],delta)
   bcstate['rows'].append(row);bcstate['lastsample']=now
  if bca.glass.is_visible() and bcj.glass.is_visible() and not bcstate['shot']:
   u.SystemLibrary.execute_console_command(bcw,'Shot filename="'+str(bcdir/('Together_'+str(len(bcstate['cycles']))+'.png'))+'" -nosuffix',bcpc);bcstate['shot']=True;rec['both_drinking']=True
  if state=='AVAILABLE' and any(x['state']=='BAR_BANTER' for x in rec['states']):
   assert rec.get('both_drinking'),rec
   assert any(x['speaker']=='Astra' for x in rec['lines']) and any(x['speaker']=='Joy' for x in rec['lines']),rec
   rec['passed']=True
   if len(bcstate['cycles'])==2:
    (bcdir/'Result.json').write_text(json.dumps({'passed':True,'cycles':bcstate['cycles'],'samples':bcstate['rows'],'cloth_bone_max_cm':bcstate['delta'],'eye_head_max_cm':bcstate['eye'],'physical_input':False,'audible_playback':False},indent=2));bcfinish();return
   bcstate['cycles'].append({'states':[],'lines':[]});bcstate.update(at=now,last=None,shot=False)
  assert elapsed<125,(state,rec)
  (bcdir/'Progress.json').write_text(json.dumps({'state':state,'elapsed':elapsed,'cycles':bcstate['cycles'],'samples':len(bcstate['rows'])},indent=2))
 except Exception:
  (bcdir/'Error.txt').write_text(traceback.format_exc());(bcdir/'Failed.json').write_text(json.dumps(bcstate['cycles'],indent=2));bcfinish()
bchandle=u.register_slate_post_tick_callback(bctick)
