import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Two editable 76-second loop orders referencing the verified private clips."""
import unreal as u,json,hashlib,traceback
from pathlib import Path
O=R/'ZeroGLoop';O.mkdir(exist_ok=True)
B='/Game/SpaceSurvival/Licensed/VexaZeroGSharedHipProof_20261026'
D='/Game/SpaceSurvival/Licensed/VexaZeroGLoopProof_20261026';MAP=D+'/L_ZeroGDuet_Review'
assert 'WorkbenchNative/CharacterWorkbench' in u.Paths.get_project_file_path().replace('\\','/')
guard=Path(u.Paths.project_content_dir())/'SpaceSurvival/Licensed/VexaZeroGSharedHipProof_20261026'
before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in guard.rglob('*') if p.is_file()}
report={'map':MAP,'actors':[],'errors':[],'scope':'Private two-Vexa choreography fixture; not other dancer, anatomy or production approval'}
try:
 lib=u.EditorAssetLibrary;es=u.get_editor_subsystem(u.EditorActorSubsystem);ls=u.get_editor_subsystem(u.LevelEditorSubsystem);ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
 assert not lib.does_asset_exist(MAP),'Refuse overwrite'
 assert u.EditorLoadingAndSavingUtils.new_map_from_template('/Game/SpaceSurvival/Licensed/ZeroGChoreography_20261025/L_ZeroG_Choreography_Review',False)
 for a in es.get_all_level_actors():
  label=a.get_actor_label()
  keep=label.startswith(('Chamber/','Review/softbox','Review/contact_light','Review/platform')) or a.get_class().get_name() in ('WorldSettings','Brush','PostProcessVolume')
  if not keep:es.destroy_actor(a)
 world=ed.get_editor_world();world.get_world_settings().set_editor_property('default_game_mode',u.GameModeBase)
 assert u.EditorLoadingAndSavingUtils.save_map(world,MAP)
 sk=u.load_asset(B+'/SK_VexaZeroGWhiteMask');mat=u.load_asset(B+'/M_ProofGray');assert sk and mat
 names=('01_Drift','02_Spiral','03_Butterfly','04_Inversion','05_LateralArc')
 clips={n:u.load_asset(B+'/A_ZG_'+n) for n in names};assert all(clips.values())
 for who,x,order in (('OrderA',-170,names),('OrderB',170,(names[2],names[4],names[0],names[3],names[1]))):
  a=es.spawn_actor_from_class(u.SkeletalMeshActor,u.Vector(x,0,1080));a.set_actor_label('Duet/'+who);c=a.skeletal_mesh_component
  c.set_skeletal_mesh_asset(sk);c.set_collision_profile_name('NoCollision');c.set_editor_property('bounds_scale',4.0)
  c.set_editor_property('visibility_based_anim_tick_option',u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
  c.set_editor_property('skin_cache_usage',[u.SkinCacheUsage.ENABLED]);c.override_animation_data(clips[order[0]],False,False,0,0)
  for i in range(c.get_num_materials()):c.set_material(i,mat)
  name='LS_ZeroG_'+who;assert not lib.does_asset_exist(D+'/'+name),'Refuse overwrite'
  seq=u.AssetToolsHelpers.get_asset_tools().create_asset(name,D,u.LevelSequence,u.LevelSequenceFactoryNew());assert seq
  u.MovieSceneSequenceExtensions.set_display_rate(seq,u.FrameRate(60,1));u.MovieSceneSequenceExtensions.set_tick_resolution_directly(seq,u.FrameRate(24000,1))
  ab=u.MovieSceneSequenceExtensions.add_possessable(seq,a);cb=u.MovieSceneSequenceExtensions.add_possessable(seq,c);u.MovieSceneBindingExtensions.set_parent(cb,ab)
  track=u.MovieSceneBindingExtensions.add_track(cb,u.MovieSceneSkeletalAnimationTrack);start=0;rows=[]
  for part in order:
   clip=clips[part];assert clip.get_editor_property('skeleton')==sk.skeleton
   end=start+round(clip.sequence_length*60);sec=track.add_section();params=u.MovieSceneSkeletalAnimationParams();params.animation=clip;params.force_custom_mode=True;params.skip_anim_notifiers=True
   sec.set_editor_property('params',params);sec.set_completion_mode(u.MovieSceneCompletionMode.RESTORE_STATE);u.MovieSceneSectionExtensions.set_range(sec,start,end)
   rows.append({'clip':clip.get_path_name(),'start':start/60,'end':end/60});start=end
  assert start==4560
  assert c in u.MovieSceneSequenceExtensions.locate_bound_objects(seq,cb,world)
  u.MovieSceneSequenceExtensions.set_playback_start(seq,0);u.MovieSceneSequenceExtensions.set_playback_end(seq,start);assert lib.save_loaded_asset(seq)
  player=es.spawn_actor_from_class(u.LevelSequenceActor,u.Vector());player.set_actor_label('Playback/'+who)
  settings=u.MovieSceneSequencePlaybackSettings();settings.auto_play=True;settings.loop_count=u.MovieSceneSequenceLoopCount(value=-1);settings.disable_camera_cuts=True
  player.set_editor_property('playback_settings',settings);player.set_sequence(seq)
  report['actors'].append({'label':a.get_actor_label(),'sequence':seq.get_path_name(),'x_cm':x,'segments':rows,'duration':start/60})
 cap=es.spawn_actor_from_class(u.SceneCapture2D,u.Vector(0,-1400,1270));cap.set_actor_label('DuetCapture');cap.set_actor_rotation(u.MathLibrary.find_look_at_rotation(cap.get_actor_location(),u.Vector(0,0,1190)),False)
 es.spawn_actor_from_class(u.PlayerStart,u.Vector(0,-1000,1100))
 assert ls.save_current_level()
 report['existing_proof_unchanged']=all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in before.items())
 assert report['existing_proof_unchanged'];report['ok']=True
except Exception:report['errors'].append(traceback.format_exc());report['ok']=False
(O/'Author.json').write_text(json.dumps(report,indent=2));print('ZERO_G_DUET_AUTHOR',json.dumps(report),flush=True)
u.SystemLibrary.quit_editor()
