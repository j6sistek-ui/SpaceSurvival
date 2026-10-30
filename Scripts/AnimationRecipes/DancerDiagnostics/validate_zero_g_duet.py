import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Fresh native natural-play loop check, multi-angle views, no saved mutations."""
import unreal as u,json,time,traceback,math,hashlib
from pathlib import Path
O=R/'ZeroGLoop';OUT=O/'NaturalViews';OUT.mkdir(exist_ok=True)
assert 'WorkbenchNative/CharacterWorkbench' in u.Paths.get_project_file_path().replace('\\','/')
data=json.loads((O/'Author.json').read_text());assert data['ok']
ls=u.get_editor_subsystem(u.LevelEditorSubsystem);ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
assert ls.load_level(data['map'])
report={'map':data['map'],'samples':[],'captures':[],'wraps':{'OrderA':0,'OrderB':0},'errors':[],'scope':'Natural native sequence playback and staged clearance; anatomical acceptance remains open.'}
state={'stage':'wait','start':time.monotonic(),'busy':False,'last':{},'last_sample':0,'shot':0}
shots=[(4,'front',(0,-1400,1270)),(12,'quarter',(900,-1100,1350)),(20,'side',(1400,0,1270)),(30,'back',(0,1400,1270)),(40,'opposite',(-900,1100,1350)),(50,'front_late',(0,-1400,1270)),(65,'above',(0,-500,2100)),(75,'before_wrap',(0,-1400,1270)),(78,'after_wrap',(0,-1400,1270))]
bones=('pelvis','head','upperarm_l','upperarm_r','hand_l','hand_r','foot_l','foot_r')
def finish():
 report['ok']=not report['errors'] and min(report['wraps'].values())>=1 and len(report['captures'])==len(shots)
 (O/'NaturalPlayback.json').write_text(json.dumps(report,indent=2));print('ZERO_G_NATURAL',report['ok'],report['wraps'],len(report['samples']),report['errors'],flush=True)
 u.unregister_slate_post_tick_callback(state['handle']);ls.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False);u.SystemLibrary.quit_editor()
def tick(dt):
 if state['busy']:return
 state['busy']=True
 try:
  now=time.monotonic()
  if now-state['start']>180:raise RuntimeError('Bounded natural-play timeout')
  if state['stage']=='wait':
   if now-state['start']<5:return
   ls.editor_request_begin_play();state['stage']='starting';return
  if state['stage']=='starting':
   world=ed.get_game_world()
   if not world:return
   by={a.get_actor_label():a for a in u.GameplayStatics.get_all_actors_of_class(world,u.Actor)}
   if not all('Playback/'+n in by for n in report['wraps']):return
   actors={n:by['Duet/'+n] for n in report['wraps']};players={n:by['Playback/'+n].get_editor_property('sequence_player') for n in report['wraps']}
   for n,a in actors.items():
    expected=u.Vector(-170 if n=='OrderA' else 170,0,1080);assert (a.get_actor_location()-expected).length()<.001,(n,a.get_actor_location())
    assert players[n].is_playing(),n
   cap=by['DuetCapture'];cc=cap.get_editor_property('capture_component2d');target=u.RenderingLibrary.create_render_target2d(world,960,800,u.TextureRenderTargetFormat.RTF_RGBA8,u.LinearColor(0,0,0,1),False,False)
   cc.set_editor_property('texture_target',target);cc.set_editor_property('capture_source',u.SceneCaptureSource.SCS_FINAL_COLOR_LDR);cc.set_editor_property('capture_every_frame',False);cc.set_editor_property('capture_on_movement',False);cc.set_editor_property('fov_angle',48.)
   pawn=u.GameplayStatics.get_player_pawn(world,0)
   if pawn:pawn.set_actor_hidden_in_game(True)
   for cmd in ('t.MaxFPS 60','r.EyeAdaptationQuality 0','r.SkinCache.Mode 1','r.SkinCache.RecomputeTangents 2'):u.SystemLibrary.execute_console_command(world,cmd)
   state.update(stage='playing',world=world,actors=actors,players=players,cap=cap,cc=cc,target=target,play_start=now);return
  elapsed=now-state['play_start']
  if now-state['last_sample']>.1:
   row={'wall':elapsed,'dancers':{}}
   for n,a in state['actors'].items():
    p=state['players'][n];qt=p.get_current_time();seconds=(qt.time.frame_number.value+qt.time.sub_frame)*qt.rate.denominator/qt.rate.numerator
    if n in state['last'] and seconds<state['last'][n]-1:report['wraps'][n]+=1
    state['last'][n]=seconds;c=a.skeletal_mesh_component
    row['dancers'][n]={'seconds':seconds,'playing':p.is_playing(),'actor':list(a.get_actor_location().to_tuple()),'bones':{b:list(c.get_socket_location(b).to_tuple()) for b in bones}}
   report['samples'].append(row);state['last_sample']=now
  if state.get('pending'):
   label=state.pop('pending');u.RenderingLibrary.export_render_target(state['world'],state['target'],str(OUT),label+'.png');assert (OUT/(label+'.png')).is_file();report['captures'].append({'label':label,'wall':elapsed,'times':dict(state['last'])});state['shot']+=1
  if state['shot']<len(shots):
   at,label,loc=shots[state['shot']]
   if elapsed>=at:
    cap=state['cap'];cap.set_actor_location(u.Vector(*loc),False,True);cap.set_actor_rotation(u.MathLibrary.find_look_at_rotation(u.Vector(*loc),u.Vector(0,0,1190)),False);state['cc'].capture_scene();state['pending']=label
  if elapsed>82 and not state.get('pending') and min(report['wraps'].values())>=1:finish()
 except Exception:report['errors'].append(traceback.format_exc());finish()
 finally:state['busy']=False
u.EditorPythonScripting.set_keep_python_script_alive(True);state['handle']=u.register_slate_post_tick_callback(tick)
