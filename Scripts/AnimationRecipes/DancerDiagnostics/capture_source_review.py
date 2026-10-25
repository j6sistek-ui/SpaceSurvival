import os
from pathlib import Path
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

import unreal as u,time,json,traceback
from pathlib import Path
OUT=R/'NativeViews_SourceBaseline';OUT.mkdir(exist_ok=True)
ls=u.get_editor_subsystem(u.LevelEditorSubsystem);ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
assert 'CharacterWorkbench' in u.Paths.get_project_file_path()
assert ls.load_level('/Game/SpaceSurvival/Licensed/ZeroGSourceBaseline_20261025/L_SourceBaseline_Review')
camera=u.get_editor_subsystem(u.EditorActorSubsystem).spawn_actor_from_class(u.CameraActor,u.Vector())
camera.set_actor_label('Review/RuntimeCamera')
u.SystemLibrary.execute_console_command(ed.get_editor_world(),'t.MaxFPS 30')
u.SystemLibrary.execute_console_command(ed.get_editor_world(),'r.Streaming.PoolSize 2200')
shots=[('Vexa',4,'front'),('Vexa',4,'back'),('Vexa',4,'side'),('Vexa',4,'arm'),('Roxie',4,'front'),('Jinx',8,'front'),('Vesper',8,'side')]
state={'start':time.monotonic(),'stage':'wait','task':None,'index':0,'busy':False};report={'shots':[],'errors':[],'quality':'Unaccepted source-baseline comparison'}
def finish():
 report['ok']=not report['errors'] and len(report['shots'])==len(shots);(R/'SourceReviewCaptures.json').write_text(json.dumps(report,indent=2));print('BASELINE_CAPTURE_RESULT',report,flush=True)
 u.unregister_slate_post_tick_callback(state['handle']);ls.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False);u.SystemLibrary.quit_editor()
def tick(dt):
 if state['busy']:return
 state['busy']=True
 try:
  if time.monotonic()-state['start']>200:raise RuntimeError('Capture timeout')
  if state['stage']=='wait':
   if time.monotonic()-state['start']<8:return
   ls.editor_request_begin_play();state['stage']='starting';return
  if state['stage']=='starting':
   world=ed.get_game_world()
   if not world:return
   actors={a.get_actor_label():a for a in u.GameplayStatics.get_all_actors_of_class(world,u.Actor)}
   if 'Vexa' not in actors:return
   state['actors']=actors;state['world']=world;state['camera']=actors['Review/RuntimeCamera']
   pc=u.GameplayStatics.get_player_controller(world,0);pc.set_view_target_with_blend(state['camera'],0)
   pawn=u.GameplayStatics.get_player_pawn(world,0)
   if pawn:pawn.set_actor_hidden_in_game(True)
   state['stage']='pose'
  if state['task']:
   if not state['task'].is_task_done():return
   state['task']=None;state['index']+=1;state['stage']='pose'
  if state['index']>=len(shots):finish();return
  who,seconds,angle=shots[state['index']];actor=state['actors'][who]
  main=next(c for c in actor.get_components_by_class(u.SkeletalMeshComponent) if c.get_name()=='CharacterMesh0')
  if state['stage']=='pose':
   for name in ('Vexa','Jinx','Roxie','Vesper','OriginalSource/g1'):
    for c in state['actors'][name].get_components_by_class(u.SkeletalMeshComponent):
     if c.get_editor_property('skeletal_mesh_asset'):c.set_position(seconds,False);c.set_play_rate(0)
   state['posed']=time.monotonic();state['stage']='capture';return
  if time.monotonic()-state['posed']<.6:return
  head=main.get_socket_location('head');pelvis=main.get_socket_location('pelvis');target=(head+pelvis)*.5
  offsets={'front':u.Vector(0,-420,40),'back':u.Vector(0,420,40),'side':u.Vector(420,0,40),'arm':u.Vector(-120,-120,35)}
  if angle=='arm':target=(main.get_socket_location('lowerarm_r')+main.get_socket_location('hand_r'))*.5
  camera=state['camera'];location=target+offsets[angle];camera.set_actor_location(location,False,True);camera.set_actor_rotation(u.MathLibrary.find_look_at_rotation(location,target),False)
  camera.get_component_by_class(u.CameraComponent).set_field_of_view(48)
  label=f'{who}_{seconds}s_{angle}'
  u.AutomationLibrary.finish_loading_before_screenshot();state['task']=u.AutomationLibrary.take_high_res_screenshot(800,900,str(OUT/(label+'.png')),camera,force_game_view=True,delay=.2)
  report['shots'].append({'name':label,'head':head.to_tuple(),'right_hand':main.get_socket_location('hand_r').to_tuple(),'right_elbow':main.get_socket_location('lowerarm_r').to_tuple()})
 except Exception:report['errors'].append(traceback.format_exc());finish()
 finally:state['busy']=False
u.EditorPythonScripting.set_keep_python_script_alive(True);state['handle']=u.register_slate_post_tick_callback(tick)
