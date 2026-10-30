import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Private native G1 support/release; never open or modify the game map."""
import unreal as u,json,time,traceback,hashlib,math
from pathlib import Path
assert 'WorkbenchNative/CharacterWorkbench' in u.Paths.get_project_file_path().replace('\\','/')
OLD='/Game/SpaceSurvival/Licensed/VexaHandIsolationProof_20261026'
BASE='/Game/SpaceSurvival/Licensed/VexaPoleReleaseProof_20261026'
OUT=R/'NativeSupportedRelease';OUT.mkdir(exist_ok=True)
export=json.loads((R/'GBSupportedRelease/Export.json').read_text())
assert hashlib.sha256(Path(export['file']).read_bytes()).hexdigest()==export['sha256']
guard=Path(u.Paths.project_content_dir())/'SpaceSurvival/Licensed/VexaHandIsolationProof_20261026'
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in guard.rglob('*') if p.is_file()}
sk=u.load_asset(OLD+'/SK_VexaHandIsolationProof');assert sk and sk.skeleton
u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
name='A_G1_SupportedRelease'
task=u.AssetImportTask();task.filename=export['fbx'];task.destination_path=BASE;task.destination_name=name;task.automated=True;task.save=True;task.replace_existing=False
assert not u.EditorAssetLibrary.does_asset_exist(BASE+'/'+name),'Keep prior native candidate intact'
options=u.FbxImportUI();options.automated_import_should_detect_type=False;options.import_mesh=False;options.import_animations=True;options.import_materials=False;options.import_textures=False;options.skeleton=sk.skeleton;options.mesh_type_to_import=u.FBXImportType.FBXIT_ANIMATION
options.anim_sequence_import_data.set_editor_property('use_default_sample_rate',False);options.anim_sequence_import_data.set_editor_property('custom_sample_rate',60);options.anim_sequence_import_data.set_editor_property('preserve_local_transform',True);task.options=options
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);clip=u.load_asset(BASE+'/'+name)
assert clip and abs(clip.sequence_length-export['seconds'])<.02
assert u.EditorAssetLibrary.save_loaded_asset(clip,False)
es=u.get_editor_subsystem(u.EditorActorSubsystem);ls=u.get_editor_subsystem(u.LevelEditorSubsystem);ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
assert u.EditorLoadingAndSavingUtils.new_map_from_template('/Game/SpaceSurvival/Licensed/ZeroGSourceBaseline_20261025/L_SourceBaseline_Review',False)
for a in es.get_all_level_actors():
 if a.get_components_by_class(u.SkeletalMeshComponent) or a.get_actor_label().startswith(('Contact/','OriginalSource/')):es.destroy_actor(a)
actor=es.spawn_actor_from_class(u.SkeletalMeshActor,u.Vector(0,0,1080));actor.set_actor_label('ReleaseProof');mesh=actor.skeletal_mesh_component
mesh.set_skeletal_mesh_asset(sk);mesh.override_animation_data(clip,False,False,0,0);mesh.set_update_animation_in_editor(True);mesh.set_collision_profile_name('NoCollision');mesh.set_editor_property('bounds_scale',5.)
mesh.set_editor_property('visibility_based_anim_tick_option',u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
gray=u.load_asset(OLD+'/M_ProofGray');assert gray
for i in range(mesh.get_num_materials()):mesh.set_material(i,gray)
pole=es.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,1330));pole.set_actor_label('Orange50mmPole');pc=pole.static_mesh_component;pc.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cylinder'));pc.set_collision_profile_name('NoCollision');pole.set_actor_scale3d(u.Vector(.05,.05,5.))
mat=u.AssetToolsHelpers.get_asset_tools().create_asset('M_OrangePole',BASE,u.Material,u.MaterialFactoryNew());mat.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
color=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionConstant3Vector);color.set_editor_property('constant',u.LinearColor(1,.12,0,1));assert u.MaterialEditingLibrary.connect_material_property(color,'',u.MaterialProperty.MP_EMISSIVE_COLOR);u.MaterialEditingLibrary.recompile_material(mat);u.EditorAssetLibrary.save_loaded_asset(mat);pc.set_material(0,mat)
cap=es.spawn_actor_from_class(u.SceneCapture2D,u.Vector());cap.set_actor_label('ReleaseCapture')
assert u.EditorLoadingAndSavingUtils.save_map(ed.get_editor_world(),BASE+'/L_G1SupportedRelease_Review')
state={'start':time.monotonic(),'stage':'wait','frame':0,'view':0,'busy':False};views=['front','back'];fps=24;count=round(clip.sequence_length*fps)+1
report={'source_sha256':export['sha256'],'asset':BASE+'/'+name,'map':BASE+'/L_G1SupportedRelease_Review','duration':clip.sequence_length,'fps':fps,'frames_per_view':count,'captured':[],'bone_samples':{},'errors':[],'limitations':'Private action and unchanged mesh; no complete G1/G2, loop, chamber or production acceptance.'}
for view in views:(OUT/view).mkdir(exist_ok=True)
expected_frames={round((int(f)-1)/60*fps):f for f in export['expected_bones']}
def finish():
 report['old_proof_unchanged']=all(Path(p).is_file() and hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
 report['ok']=not report['errors'] and report['old_proof_unchanged'] and len(report['captured'])==count*2
 (OUT/'Capture.json').write_text(json.dumps(report,indent=2));print('SUPPORTED_RELEASE_NATIVE',report['ok'],len(report['captured']),report['errors'],flush=True)
 u.unregister_slate_post_tick_callback(state['handle']);ls.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False);u.SystemLibrary.quit_editor()
def tick(dt):
 if state['busy']:return
 state['busy']=True
 try:
  now=time.monotonic()
  if now-state['start']>360:raise RuntimeError('Bounded native release review timed out')
  if state['stage']=='wait':
   if now-state['start']<5:return
   ls.editor_request_begin_play();state['stage']='starting';return
  if state['stage']=='starting':
   world=ed.get_game_world()
   if not world:return
   actors={a.get_actor_label():a for a in u.GameplayStatics.get_all_actors_of_class(world,u.Actor)}
   if 'ReleaseCapture' not in actors:return
   c=actors['ReleaseProof'].skeletal_mesh_component;ca=actors['ReleaseCapture'];cc=ca.get_editor_property('capture_component2d')
   target=u.RenderingLibrary.create_render_target2d(world,640,640,u.TextureRenderTargetFormat.RTF_RGBA8,u.LinearColor(0,0,0,1),False,False)
   cc.set_editor_property('texture_target',target);cc.set_editor_property('capture_source',u.SceneCaptureSource.SCS_FINAL_COLOR_LDR);cc.set_editor_property('capture_every_frame',False);cc.set_editor_property('capture_on_movement',False);cc.set_editor_property('fov_angle',45.)
   c.play_animation(clip,False);c.set_play_rate(0)
   pawn=u.GameplayStatics.get_player_pawn(world,0)
   if pawn:pawn.set_actor_hidden_in_game(True)
   for cmd in ['t.MaxFPS 60','r.EyeAdaptationQuality 0']:u.SystemLibrary.execute_console_command(world,cmd)
   state.update(world=world,mesh=c,cap=ca,component=cc,target=target,stage='pose');return
  c=state['mesh'];frame=state['frame'];view=views[state['view']];seconds=frame/fps
  if state['stage']=='pose':
   c.set_position(seconds,False);state['ticks']=0;state['stage']='settle';return
  if state['stage']=='settle':
   state['ticks']+=1
   if state['ticks']<2:return
   center=u.Vector(25,0,1380);offset=u.Vector(240,-360,45) if view=='front' else u.Vector(-240,360,45)
   state['cap'].set_actor_location(center+offset,False,True);state['cap'].set_actor_rotation(u.MathLibrary.find_look_at_rotation(center+offset,center),False)
   if view=='front' and frame in expected_frames:
    key=expected_frames[frame];data={}
    for bone in export['expected_bones'][key]:
     v=c.get_socket_location(bone);data[bone]=[v.x,v.y,v.z-1080]
    report['bone_samples'][key]=data
   state['component'].capture_scene();state['stage']='export';return
  filename=f'{frame:04d}.png';u.RenderingLibrary.export_render_target(state['world'],state['target'],str(OUT/view),filename)
  p=OUT/view/filename;assert p.is_file() and p.stat().st_size>5000
  assert abs(c.get_position()-seconds)<1e-4
  report['captured'].append({'view':view,'frame':frame,'seconds':seconds,'actual_position':c.get_position(),'path':str(p)})
  state['frame']+=1;state['stage']='pose'
  if state['frame']==count:state['frame']=0;state['view']+=1
  if state['view']==2:finish()
 except Exception:report['errors'].append(traceback.format_exc());finish()
 finally:state['busy']=False
u.EditorPythonScripting.set_keep_python_script_alive(True);state['handle']=u.register_slate_post_tick_callback(tick)
