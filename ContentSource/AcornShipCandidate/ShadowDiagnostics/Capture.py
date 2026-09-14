"""Unsaved fixed-fixture shadow diagnosis; no project assets or runtime policies saved."""
import hashlib,json,time,traceback
from datetime import datetime,timezone
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'ContentSource/AcornShipCandidate/ShadowDiagnostics';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protected={p:sha(p) for directory in ('Source','Config','Content') for p in (ROOT/directory).rglob('*') if p.is_file()}
mesh=u.load_asset('/Game/SpaceSurvival/Meshes/SM_AcornShipV2');assert isinstance(mesh,u.StaticMesh)
u.EditorLoadingAndSavingUtils.new_blank_map(False)
actors=u.get_editor_subsystem(u.EditorActorSubsystem);world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
CVARS=['r.Shadow.Virtual.Enable','r.Shadow.Virtual.NormalBias','r.Shadow.Virtual.ScreenRayLength','r.Shadow.Virtual.SMRT.RayCountDirectional','r.RayTracing']
get=lambda name:u.SystemLibrary.get_console_variable_float_value(name)
baseline={name:get(name) for name in CVARS}
assert baseline['r.Shadow.Virtual.Enable']==1 and baseline['r.RayTracing']==0
for command in ('r.AntiAliasingMethod 0','r.MotionBlurQuality 0','r.ScreenPercentage 100'):u.SystemLibrary.execute_console_command(world,command)
ship=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0));component=ship.get_component_by_class(u.StaticMeshComponent);component.set_mobility(u.ComponentMobility.MOVABLE);component.set_static_mesh(mesh);component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);component.set_cast_shadow(True)
lamps=[]
light_fixture=[(-35,-30,(.9,.95,1,1),4),(-25,145,(1,.89,.75,1),2),(-65,70,(.5,.7,1,1),1)]
for pitch,yaw,color,intensity in light_fixture:
 actor=actors.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,500),u.Rotator(pitch=pitch,yaw=yaw,roll=0));lamp=actor.get_component_by_class(u.DirectionalLightComponent);lamp.set_mobility(u.ComponentMobility.MOVABLE);lamp.set_light_color(u.LinearColor(*color));lamp.set_intensity(intensity);lamp.set_editor_property('cast_shadows',True);lamps.append(lamp)
PROPS=['shadow_bias','shadow_slope_bias','contact_shadow_length','light_source_angle','cast_shadows']
light_baseline=[{p:lamp.get_editor_property(p) for p in PROPS} for lamp in lamps]
post=actors.spawn_actor_from_class(u.PostProcessVolume,u.Vector(0,0,0));post.set_editor_property('unbound',True);settings=post.get_editor_property('settings')
for key,value in {'override_auto_exposure_min_brightness':True,'override_auto_exposure_max_brightness':True,'auto_exposure_min_brightness':1.0,'auto_exposure_max_brightness':1.0,'override_bloom_intensity':True,'bloom_intensity':0.0}.items():settings.set_editor_property(key,value)
post.set_editor_property('settings',settings)
location=u.Vector(-720,470,310);target=u.Vector(-15,0,20);rotation=u.MathLibrary.find_look_at_rotation(location,target);camera=actors.spawn_actor_from_class(u.CameraActor,location,rotation);camera.get_component_by_class(u.CameraComponent).set_field_of_view(42);u.get_editor_subsystem(u.LevelEditorSubsystem).editor_set_game_view(True);u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(location,rotation)
cases=[('Baseline',{},{}),('LightBias1',{}, {'shadow_bias':1.0}),('LightSlope1',{}, {'shadow_slope_bias':1.0}),('VSMTraceOff',{'r.Shadow.Virtual.ScreenRayLength':0},{}),('VSMNormal1',{'r.Shadow.Virtual.NormalBias':1},{}),('VSMNormal2',{'r.Shadow.Virtual.NormalBias':2},{}),('HardVSM',{'r.Shadow.Virtual.SMRT.RayCountDirectional':0},{}),('SourceAngle2',{}, {'light_source_angle':2.0}),('BaselineRestored',{}, {})]
if any(item['contact_shadow_length']!=0 for item in light_baseline):cases.insert(1,('ContactOff',{}, {'contact_shadow_length':0.0}))
record={'status':'FAILED','engine':u.SystemLibrary.get_engine_version(),'started_utc':datetime.now(timezone.utc).isoformat(),'errors':[],'baseline_cvars':baseline,'baseline_lights':light_baseline,'contact_off_case_skipped_because_already_zero':all(item['contact_shadow_length']==0 for item in light_baseline),'camera_cm':[-720,470,310],'target_cm':[-15,0,20],'fov':42,'light_fixture':light_fixture,'images':[],'limits':['Unsaved stock actor studio; no gameplay/performance/art acceptance','AA0, exposure1,bloom0 are isolated diagnostic process settings','Only one variable changes per case; shadows remain on in every view']}
state={'index':0,'frames':0,'task':None,'busy':False,'start':time.monotonic(),'handle':None,'finished':False}
def reset():
 for name,value in baseline.items():
  if get(name)!=value:u.SystemLibrary.execute_console_command(world,name+' '+str(value))
 for lamp,values in zip(lamps,light_baseline):
  for key,value in values.items():lamp.set_editor_property(key,value)
def setup():
 reset();name,cvars,properties=cases[state['index']]
 for key,value in cvars.items():u.SystemLibrary.execute_console_command(world,key+' '+str(value));assert abs(get(key)-value)<1e-5
 for lamp in lamps:
  for key,value in properties.items():lamp.set_editor_property(key,value)
 state.update(frames=0,task=None,case_start=time.monotonic())
def finish():
 if state['finished']:return
 state['finished']=True
 try:
  reset();record['restored_cvars']={name:get(name)for name in CVARS};assert record['restored_cvars']==baseline
  changed=[str(p.relative_to(ROOT))for p,digest in protected.items()if not p.exists()or sha(p)!=digest]
  added=[str(p.relative_to(ROOT))for directory in ('Source','Config','Content')for p in(ROOT/directory).rglob('*')if p.is_file()and p not in protected]
  record['changed_protected_files']=changed;record['added_protected_files']=added;assert not changed and not added,'Protected project files changed'
  record['protected_file_count']=len(protected);record['protected_manifest_sha256']=hashlib.sha256(json.dumps({str(p.relative_to(ROOT)):digest for p,digest in protected.items()},sort_keys=True).encode()).hexdigest()
  if not record['errors']:record['status']='UNSAVED_SHADOW_MATRIX_COMPLETE_PROJECT_UNCHANGED'
 except Exception as error:record['errors'].append(str(error));u.log_error(str(error))
 record['finished_utc']=datetime.now(timezone.utc).isoformat();(OUT/'NativeMatrix.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
 u.unregister_slate_post_tick_callback(state['handle']);u.EditorPythonScripting.set_keep_python_script_alive(False)
 u.log('ACORN_SHADOW_MATRIX_FINISHED '+record['status'])
def tick(delta):
 if state['busy']or state['finished']:return
 state['busy']=True
 try:
  state['frames']+=1;name=cases[state['index']][0];path=OUT/(name+'.png')
  if state['task']is None and state['frames']>=90 and time.monotonic()-state['case_start']>2:
   u.AutomationLibrary.finish_loading_before_screenshot();state['task']=u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(path),camera,delay=.3);assert state['task'].is_valid_task()
  if state['task']and state['task'].is_task_done()and path.exists():
   record['images'].append({'file':path.name,'sha256':sha(path),'cvars':{key:get(key)for key in CVARS},'lights':[{key:lamp.get_editor_property(key)for key in PROPS}for lamp in lamps]});state['index']+=1
   if state['index']==len(cases):finish()
   else:setup()
  elif time.monotonic()-state['start']>150:raise RuntimeError('Shadow matrix timeout')
 except Exception as error:record['errors'].append(str(error));u.log_error(traceback.format_exc());finish()
 finally:state['busy']=False
setup();u.EditorPythonScripting.set_keep_python_script_alive(True);state['handle']=u.register_slate_post_tick_callback(tick)
