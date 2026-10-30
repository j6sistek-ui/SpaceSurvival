import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Compare sequencer output with the referenced clip around every loop join."""
import unreal as u,json,time,traceback,math
from pathlib import Path
O=R/'ZeroGLoop'
data=json.loads((O/'Author.json').read_text());assert data['ok']
assert 'WorkbenchNative/CharacterWorkbench' in u.Paths.get_project_file_path().replace('\\','/')
ls=u.get_editor_subsystem(u.LevelEditorSubsystem);ed=u.get_editor_subsystem(u.UnrealEditorSubsystem);es=u.get_editor_subsystem(u.EditorActorSubsystem)
assert ls.load_level(data['map'])
sk=u.load_asset('/Game/SpaceSurvival/Licensed/VexaZeroGSharedHipProof_20261026/SK_VexaZeroGWhiteMask')
ref=es.spawn_actor_from_class(u.SkeletalMeshActor,u.Vector(1000,0,1080));ref.set_actor_label('JoinReference');ref.skeletal_mesh_component.set_skeletal_mesh_asset(sk)
ref.skeletal_mesh_component.set_editor_property('visibility_based_anim_tick_option',u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
ref.set_actor_hidden_in_game(True)
events=[]
for row in data['actors']:
 name=row['label'].split('/')[-1]
 times={round((segment['start']+delta)%76,6) for segment in row['segments'] for delta in (-1/60,0,1/60)}
 times.update((segment['start']+segment['end'])/2 for segment in row['segments'])
 for sec in sorted(times):
  segment=next(s for s in row['segments'] if s['start']<=sec<s['end']);events.append((name,sec,segment['clip'],sec-segment['start']))
report={'scope':'Fresh Sequencer versus standalone source-clip evaluation at joins/midpoints; no full anatomical acceptance','samples':[],'errors':[]}
state={'start':time.monotonic(),'stage':'wait','busy':False,'index':0}
def finish():
 report['ok']=not report['errors'] and len(report['samples'])==len(events) and max((s['max_bone_mm'] for s in report['samples']),default=1e9)<.1 and max((s['max_curve_error'] for s in report['samples']),default=1e9)<1e-4
 (O/'JoinParity.json').write_text(json.dumps(report,indent=2));print('ZERO_G_SEQUENCE_JOINS',report['ok'],len(report['samples']),report['errors'],flush=True)
 u.unregister_slate_post_tick_callback(state['handle']);ls.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False);u.SystemLibrary.quit_editor()
def tick(dt):
 if state['busy']:return
 state['busy']=True
 try:
  if time.monotonic()-state['start']>150:raise RuntimeError('Join parity timeout')
  if state['stage']=='wait':
   if time.monotonic()-state['start']<5:return
   ls.editor_request_begin_play();state['stage']='starting';return
  if state['stage']=='starting':
   world=ed.get_game_world()
   if not world:return
   by={a.get_actor_label():a for a in u.GameplayStatics.get_all_actors_of_class(world,u.Actor)}
   if 'JoinReference' not in by:return
   players={n:by['Playback/'+n].get_editor_property('sequence_player') for n in ('OrderA','OrderB')}
   for p in players.values():p.pause()
   state.update(stage='pose',players=players,meshes={n:by['Duet/'+n].skeletal_mesh_component for n in players},reference=by['JoinReference'].skeletal_mesh_component)
   return
  name,sec,path,local=events[state['index']];c=state['meshes'][name];ref=state['reference'];clip=u.load_asset(path)
  if state['stage']=='pose':
   params=u.MovieSceneSequencePlaybackParams();params.set_editor_property('time',sec);params.set_editor_property('position_type',u.MovieScenePositionType.TIME);params.set_editor_property('update_method',u.UpdatePositionMethod.JUMP)
   state['players'][name].set_playback_position(params)
   ref.play_animation(clip,False);ref.set_play_rate(0);ref.set_position(local,False);state.update(stage='settle',ticks=0);return
  state['ticks']+=1
  if state['ticks']<3:return
  origin=c.get_world_location();reference_origin=ref.get_world_location();errors=[]
  for i in range(c.get_num_bones()):
   b=c.get_bone_name(i);errors.append(((c.get_socket_location(b)-origin)-(ref.get_socket_location(b)-reference_origin)).length()*10)
  names=[str(n) for n in u.AnimationLibrary.get_animation_curve_names(clip,u.RawCurveTrackTypes.RCT_FLOAT) if str(n).casefold().startswith('review_zg_')];assert len(names)==160
  instance=c.get_anim_instance();reference=ref.get_anim_instance();curve_errors=[abs(instance.get_curve_value(n)-reference.get_curve_value(n)) for n in names]
  report['samples'].append({'order':name,'time':sec,'source':path,'source_time':local,'bones':len(errors),'curves':len(names),'max_bone_mm':max(errors),'max_curve_error':max(curve_errors),'curve_magnitude':max(abs(instance.get_curve_value(n)) for n in names)})
  state['index']+=1;state['stage']='pose'
  if state['index']==len(events):finish()
 except Exception:report['errors'].append(traceback.format_exc());finish()
 finally:state['busy']=False
u.EditorPythonScripting.set_keep_python_script_alive(True);state['handle']=u.register_slate_post_tick_callback(tick)
