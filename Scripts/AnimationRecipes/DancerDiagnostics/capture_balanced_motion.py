import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

import unreal as u,json,time,traceback,math,os
from pathlib import Path
LEG_PLANE=os.environ.get('SS_REVIEW_LEG_PLANE')=='1'
SHOULDER=True
RECOMPUTE=os.environ.get('SS_REVIEW_RECOMPUTE')=='1'
CACHE_TEST=os.environ.get('SS_REVIEW_COMPUTE')=='1'
SURFACE_TEST=os.environ.get('SS_REVIEW_SURFACE')=='1'
CPU_MORPH=os.environ.get('SS_REVIEW_CPU_MORPH')=='1'
MATERIAL_TEST=os.environ.get('SS_REVIEW_MORPH_MATERIAL')=='1'
PRECISE=os.environ.get('SS_REVIEW_PRECISE')=='1'
SURFACE_READBACK=False
BONE_TEST=False
assert not BONE_TEST or SHOULDER
assert not PRECISE or SHOULDER, 'Precision comparison is Vexa-only'
assert not SURFACE_TEST or SHOULDER, 'Surface-normal control is Vexa-only'
assert not RECOMPUTE or SHOULDER, 'Tangent comparison is Vexa-only'
assert not CACHE_TEST or (SHOULDER and RECOMPUTE), 'Compiled-cache comparison is Vexa-only'
assert not CACHE_TEST or u.SystemLibrary.get_console_variable_int_value('r.SkinCache.CompileShaders')==1, 'Compute shader support must be enabled at process startup'
assert not (SHOULDER and LEG_PLANE), 'Choose one proof'
BASE='/Game/SpaceSurvival/Licensed/'+('VexaBalancedProof_20261025' if SHOULDER else 'LegPlaneProof_20261025' if LEG_PLANE else 'HipCurveProof_Legacy_20261025')
OUT=R/('NativeVexaBalancedCleanViews' if SHOULDER else 'NativeLegPlaneViews' if LEG_PLANE else 'NativeHipViews_Legacy');OUT.mkdir(exist_ok=True)
if RECOMPUTE:OUT=R/'NativeVexaShoulderRecomputeViews';OUT.mkdir(exist_ok=True)
if CACHE_TEST:OUT=R/'NativeVexaShoulderComputeViews';OUT.mkdir(exist_ok=True)
if SURFACE_TEST:OUT=R/'NativeVexaShoulderSurfaceViews';OUT.mkdir(exist_ok=True)
if CPU_MORPH:OUT=R/'NativeVexaCpuMorphViews';OUT.mkdir(exist_ok=True)
if MATERIAL_TEST:OUT=R/'NativeVexaMorphMaterialViews';OUT.mkdir(exist_ok=True)
if PRECISE:OUT=R/'NativeVexaShoulderPreciseViews';OUT.mkdir(exist_ok=True)
asset='SK_VexaBalancedProof' if SHOULDER else 'SK_RoxieHipProof'
assert 'CharacterWorkbench' in u.Paths.get_project_file_path()
es=u.get_editor_subsystem(u.EditorActorSubsystem);ls=u.get_editor_subsystem(u.LevelEditorSubsystem);ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
assert u.EditorLoadingAndSavingUtils.new_map_from_template('/Game/SpaceSurvival/Licensed/ZeroGSourceBaseline_20261025/L_SourceBaseline_Review',False)
for a in es.get_all_level_actors():
 if a.get_components_by_class(u.SkeletalMeshComponent) or a.get_actor_label().startswith(('Contact/','OriginalSource/')):es.destroy_actor(a)
actor=es.spawn_actor_from_class(u.SkeletalMeshActor,u.Vector(0,0,1080));actor.set_actor_label('HipProof');mesh=actor.skeletal_mesh_component;sk=u.load_asset(BASE+'/SK_VexaShoulderPrecise' if PRECISE else BASE+'/'+asset);clip=u.load_asset(BASE+'/'+asset+'_Anim');assert sk and clip and sk.skeleton and clip.get_editor_property('skeleton'), 'Proof dependencies must survive fresh load'
mesh.set_editor_property('visibility_based_anim_tick_option',u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
mesh.set_editor_property('bounds_scale',4.0)
mesh.set_skeletal_mesh_asset(sk);mesh.override_animation_data(clip,False,False,8,0);mesh.set_update_animation_in_editor(True);mesh.set_collision_profile_name('NoCollision')
mat=u.AssetToolsHelpers.get_asset_tools().create_asset('M_ProofGray',BASE,u.Material,u.MaterialFactoryNew()) if not u.EditorAssetLibrary.does_asset_exist(BASE+'/M_ProofGray') else u.load_asset(BASE+'/M_ProofGray')
material_before={n:mat.get_editor_property(n) for n in ('used_with_skeletal_mesh','used_with_morph_targets')}
print('PROOF_MATERIAL_BEFORE',material_before,flush=True)
if MATERIAL_TEST:
 for name in material_before:mat.set_editor_property(name,True)
 u.MaterialEditingLibrary.recompile_material(mat)
 assert all(mat.get_editor_property(n) for n in material_before)
u.MaterialEditingLibrary.delete_all_material_expressions(mat);color=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionConstant3Vector);color.set_editor_property('constant',u.LinearColor(.35,.35,.35,1));u.MaterialEditingLibrary.connect_material_property(color,'',u.MaterialProperty.MP_BASE_COLOR);u.MaterialEditingLibrary.recompile_material(mat);u.EditorAssetLibrary.save_loaded_asset(mat)
for i in range(mesh.get_num_materials()):mesh.set_material(i,mat)
if LEG_PLANE or SHOULDER:
 # Normal-based diagnostic shading avoids imported review-map exposure/lights
 # clipping the white surface. This is geometry evidence, not skin materials.
 mat.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
 u.MaterialEditingLibrary.delete_all_material_expressions(mat)
 normal=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionVertexNormalWS)
 if SURFACE_TEST:
  position=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionWorldPosition)
  dx=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionDDX)
  dy=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionDDY)
  cross=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionCrossProduct)
  normal=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionNormalize)
  for a,p,b,q in ((position,'',dx,''),(position,'',dy,''),(dx,'',cross,'A'),(dy,'',cross,'B'),(cross,'',normal,'')):
   assert u.MaterialEditingLibrary.connect_material_expressions(a,p,b,q)
 direction=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionConstant3Vector);direction.set_editor_property('constant',u.LinearColor(.3,-.5,.8,1))
 dot=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionDotProduct)
 absolute=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionAbs)
 gain=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionMultiply);gain.set_editor_property('const_b',.3)
 fill=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionAdd);fill.set_editor_property('const_b',.45)
 for a,p,b,q in ((normal,'',dot,'A'),(direction,'',dot,'B'),(dot,'',gain,'A'),(gain,'',fill,'A')):
  assert u.MaterialEditingLibrary.connect_material_expressions(a,p,b,q), (b.get_class().get_name(),q,u.MaterialEditingLibrary.get_material_expression_input_names(b))
 assert u.MaterialEditingLibrary.connect_material_property(fill,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
 u.MaterialEditingLibrary.recompile_material(mat);u.EditorAssetLibrary.save_loaded_asset(mat)
camera=es.spawn_actor_from_class(u.CameraActor,u.Vector());camera.set_actor_label('HipProofCamera')
camera.camera_component.set_editor_property('constrain_aspect_ratio',False)
assert u.EditorLoadingAndSavingUtils.save_map(ed.get_editor_world(),BASE+'/L_HipProof_Review')

cap=es.spawn_actor_from_class(u.SceneCapture2D,u.Vector());cap.set_actor_label('BalancedMotionCapture')
state={'start':time.monotonic(),'stage':'wait','frame':0,'angle':0,'busy':False};report={'fps':24,'seconds':16,'frames_per_view':384,'views':['front','back'],'captured':[],'errors':[],'status':'PRIVATE NATIVE CAPTURE, NOT OWNER ACCEPTANCE'}
OUT=R/'NativeVexaBalancedMotion';OUT.mkdir(exist_ok=True)
for angle in report['views']:(OUT/angle).mkdir(exist_ok=True)
def finish():
 report['ok']=not report['errors'] and len(report['captured'])==768
 (R/'NativeVexaBalancedMotion.json').write_text(json.dumps(report,indent=2))
 print('BALANCED_NATIVE_MOTION',report['ok'],len(report['captured']),report['errors'],flush=True)
 u.unregister_slate_post_tick_callback(state['handle']);ls.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False);u.SystemLibrary.quit_editor()
def unit(v):return v/max(math.sqrt(v.x*v.x+v.y*v.y+v.z*v.z),1e-8)
def tick(dt):
 if state['busy']:return
 state['busy']=True
 try:
  now=time.monotonic()
  if now-state['start']>300:raise RuntimeError('Native motion timeout')
  if state['stage']=='wait':
   if now-state['start']<5:return
   ls.editor_request_begin_play();state['stage']='starting';return
  if state['stage']=='starting':
   world=ed.get_game_world()
   if not world:return
   actors={a.get_actor_label():a for a in u.GameplayStatics.get_all_actors_of_class(world,u.Actor)}
   if 'BalancedMotionCapture' not in actors:return
   c=actors['HipProof'].skeletal_mesh_component;ca=actors['BalancedMotionCapture'];cc=ca.get_editor_property('capture_component2d')
   target=u.RenderingLibrary.create_render_target2d(world,640,640,u.TextureRenderTargetFormat.RTF_RGBA8,u.LinearColor(0,0,0,1),False,False)
   cc.set_editor_property('texture_target',target);cc.set_editor_property('capture_source',u.SceneCaptureSource.SCS_FINAL_COLOR_LDR);cc.set_editor_property('capture_every_frame',False);cc.set_editor_property('capture_on_movement',False);cc.set_editor_property('fov_angle',60)
   c.play_animation(clip,False);c.set_play_rate(0)
   pawn=u.GameplayStatics.get_player_pawn(world,0)
   if pawn:pawn.set_actor_hidden_in_game(True)
   u.SystemLibrary.execute_console_command(world,'t.MaxFPS 30');u.SystemLibrary.execute_console_command(world,'r.EyeAdaptationQuality 0')
   state.update(world=world,mesh=c,cap=ca,component=cc,target=target,stage='pose');return
  c=state['mesh'];frame=state['frame'];angle=report['views'][state['angle']];sec=frame/24
  if state['stage']=='pose':
   c.set_position(sec,False);state['ticks']=0;state['stage']='settle';return
  if state['stage']=='settle':
   state['ticks']+=1
   if state['ticks']<2:return
   l=c.get_socket_location('upperarm_l');rr=c.get_socket_location('upperarm_r');center=(l+rr)*.5;side=unit(l-rr);up=unit(c.get_socket_location('neck_01')-c.get_socket_location('spine_03'));front=unit(u.Vector(up.y*side.z-up.z*side.y,up.z*side.x-up.x*side.z,up.x*side.y-up.y*side.x))
   loc=center+front*(110 if angle=='front' else -110)+up*15;state['cap'].set_actor_location(loc,False,True);state['cap'].set_actor_rotation(u.MathLibrary.find_look_at_rotation(loc,center),False)
   state['component'].capture_scene();state['stage']='export';return
  name=f'{frame:04d}.png';u.RenderingLibrary.export_render_target(state['world'],state['target'],str(OUT/angle),name)
  file=OUT/angle/name;assert file.is_file() and file.stat().st_size>5000
  report['captured'].append({'view':angle,'frame':frame,'seconds':sec,'actual_position':c.get_position(),'path':str(file)})
  if frame%96==0:print('MOTION_PROGRESS',angle,frame,flush=True)
  state['frame']+=1;state['stage']='pose'
  if state['frame']==384:state['frame']=0;state['angle']+=1
  if state['angle']==2:finish()
 except Exception:report['errors'].append(traceback.format_exc());finish()
 finally:state['busy']=False
u.EditorPythonScripting.set_keep_python_script_alive(True);state['handle']=u.register_slate_post_tick_callback(tick)
