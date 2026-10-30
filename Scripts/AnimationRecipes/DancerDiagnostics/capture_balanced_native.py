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
SURFACE_READBACK=True
BONE_TEST=False
assert not BONE_TEST or SHOULDER
assert not PRECISE or SHOULDER, 'Precision comparison is Vexa-only'
assert not SURFACE_TEST or SHOULDER, 'Surface-normal control is Vexa-only'
assert not RECOMPUTE or SHOULDER, 'Tangent comparison is Vexa-only'
assert not CACHE_TEST or (SHOULDER and RECOMPUTE), 'Compiled-cache comparison is Vexa-only'
assert not CACHE_TEST or u.SystemLibrary.get_console_variable_int_value('r.SkinCache.CompileShaders')==1, 'Compute shader support must be enabled at process startup'
assert not (SHOULDER and LEG_PLANE), 'Choose one proof'
BASE='/Game/SpaceSurvival/Licensed/'+('VexaBalancedProof_20261025' if SHOULDER else 'LegPlaneProof_20261025' if LEG_PLANE else 'HipCurveProof_Legacy_20261025')
OUT=R/('NativeVexaBalancedViews' if SHOULDER else 'NativeLegPlaneViews' if LEG_PLANE else 'NativeHipViews_Legacy');OUT.mkdir(exist_ok=True)
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
 gain=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionMultiply);gain.set_editor_property('const_b',.5)
 fill=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionAdd);fill.set_editor_property('const_b',.16)
 for a,p,b,q in ((normal,'',dot,'A'),(direction,'',dot,'B'),(dot,'',absolute,''),(absolute,'',gain,'A'),(gain,'',fill,'A')):
  assert u.MaterialEditingLibrary.connect_material_expressions(a,p,b,q), (b.get_class().get_name(),q,u.MaterialEditingLibrary.get_material_expression_input_names(b))
 assert u.MaterialEditingLibrary.connect_material_property(fill,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
 u.MaterialEditingLibrary.recompile_material(mat);u.EditorAssetLibrary.save_loaded_asset(mat)
camera=es.spawn_actor_from_class(u.CameraActor,u.Vector());camera.set_actor_label('HipProofCamera')
camera.camera_component.set_editor_property('constrain_aspect_ratio',False)
assert u.EditorLoadingAndSavingUtils.save_map(ed.get_editor_world(),BASE+'/L_HipProof_Review')
state={'start':time.monotonic(),'stage':'wait','task':None,'index':0,'busy':False};report={'private_only':True,'asset':BASE+'/'+asset,'shots':[],'errors':[],'curve_count':len(u.AnimationLibrary.get_animation_curve_names(clip,u.RawCurveTrackTypes.RCT_FLOAT))};shots=[(t,a) for t in ((0,8,9.033333,12.2) if SHOULDER else (8,9.033333,9.5,10.066667) if LEG_PLANE else (6,8,10)) for a in ('front','back','side')]
if SURFACE_TEST or PRECISE or MATERIAL_TEST or CPU_MORPH:shots=[(t,a) for t in (8,9.033333) for a in ('front','back','side')]
if BONE_TEST:shots=[(t,'front') for t in (0,8,9.033333,12.2)]
def finish():
 report['ok']=not report['errors'] and len([x for x in report['shots'] if 'path' in x])==len(shots);report['unlimited_influences']=u.SystemLibrary.get_console_variable_int_value('r.GPUSkin.UnlimitedBoneInfluences');report['lod_influence_limits']=[lod.get_editor_property('build_settings').get_editor_property('bone_influence_limit') for lod in sk.get_editor_property('source_models')];report['material_usage_before']=material_before;report['material_usage_after']={n:mat.get_editor_property(n) for n in material_before};report['surface_normal_control']=SURFACE_TEST;report['precision_probe']=PRECISE;report['recompute_tangents_probe']=RECOMPUTE;report['skin_cache_cvars']={name:u.SystemLibrary.get_console_variable_int_value(name) for name in ('r.SkinCache.CompileShaders','r.SkinCache.Mode','r.SkinCache.RecomputeTangents','r.MorphTarget.Mode','r.GPUSkin.Limit2BoneInfluences')};(R/('NativeVexaCpuMorphCapture.json' if CPU_MORPH else 'NativeVexaMorphMaterialCapture.json' if MATERIAL_TEST else 'NativeVexaBalancedRuntimeSkin.json' if SURFACE_READBACK else 'NativeVexaRuntimeBones.json' if BONE_TEST else 'NativeVexaShoulderPreciseCapture.json' if PRECISE else 'NativeVexaShoulderSurfaceCapture.json' if SURFACE_TEST else 'NativeVexaShoulderComputeCapture.json' if CACHE_TEST else 'NativeVexaShoulderRecomputeCapture.json' if RECOMPUTE else 'NativeVexaShoulderCapture.json' if SHOULDER else 'NativeLegPlaneCapture.json' if LEG_PLANE else 'NativeHipCapture.json')).write_text(json.dumps(report,indent=2));print('HIP_CAPTURE_RESULT',report['ok'],len(report['shots']),report['errors'],flush=True)
 u.unregister_slate_post_tick_callback(state['handle']);ls.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False);u.SystemLibrary.quit_editor()
def tick(dt):
 if state['busy']:return
 state['busy']=True
 try:
  now=time.monotonic()
  if now-state['start']>150:raise RuntimeError('Hip capture timeout')
  if state['stage']=='wait':
   if now-state['start']<8:return
   ls.editor_request_begin_play();state['stage']='starting';return
  if state['stage']=='starting':
   world=ed.get_game_world()
   if not world:return
   actors={a.get_actor_label():a for a in u.GameplayStatics.get_all_actors_of_class(world,u.Actor)}
   if 'HipProof' not in actors:return
   state.update(world=world,mesh=actors['HipProof'].skeletal_mesh_component,camera=actors['HipProofCamera'],stage='pose')
   pc=u.GameplayStatics.get_player_controller(world,0);pc.set_view_target_with_blend(state['camera'],0);pawn=u.GameplayStatics.get_player_pawn(world,0)
   if pawn:pawn.set_actor_hidden_in_game(True)
   u.SystemLibrary.execute_console_command(world,'t.MaxFPS 30',pc)
   u.SystemLibrary.execute_console_command(world,'viewmode lit',pc)
   if LEG_PLANE or SHOULDER:u.SystemLibrary.execute_console_command(world,'r.EyeAdaptationQuality 0',pc)
   if CPU_MORPH:
    u.SystemLibrary.execute_console_command(world,'r.MorphTarget.Mode 0',pc)
   if RECOMPUTE:
    u.SystemLibrary.execute_console_command(world,'r.SkinCache.Mode 1',pc)
    u.SystemLibrary.execute_console_command(world,'r.SkinCache.RecomputeTangents 1',pc)
  if state['task']:
   if not state['task'].is_task_done():return
   state['task']=None;state['index']+=1;state['stage']='pose'
  if state['index']==len(shots):finish();return
  sec,angle=shots[state['index']];c=state['mesh']
  if state['stage']=='pose':
   c.play_animation(clip,False);c.set_position(sec,False);c.set_play_rate(0);state['posed']=now;state['stage']='settle';return
  if state['stage']=='settle':
   if now-state['posed']<.5:return
   # Re-seek after the new single-node instance has evaluated. The old harness
   # sometimes captured the preceding pose on the first view at a new time.
   c.set_position(sec,False);state['posed']=now;state['stage']='capture';return
  if now-state['posed']<.7:return
  if SURFACE_READBACK and angle=='front':
   bones={}
   for index in range(c.get_num_bones()):
    name=c.get_bone_name(index);transform=c.get_socket_transform(name,u.RelativeTransformSpace.RTS_COMPONENT)
    bones[str(name)]={'translation':transform.translation.to_tuple(),'rotation':transform.rotation.to_tuple(),'scale':transform.scale3d.to_tuple()}
   instance=c.get_anim_instance();names=u.AnimationLibrary.get_animation_curve_names(clip,u.RawCurveTrackTypes.RCT_FLOAT)
   report['shots'].append({'seconds':sec,'actual_position':c.get_position(),'bones':bones,'curves':{str(n):instance.get_curve_value(n) for n in names}})
   if SURFACE_READBACK:
    print('GEOMETRY_API',u.GeometryScript_SceneUtils.copy_mesh_from_component.__doc__,u.GeometryScript_MeshQueries.get_all_vertex_positions.__doc__,u.GeometryScript_List.convert_vector_list_to_array.__doc__,flush=True)
    dynamic=u.DynamicMesh()
    result=u.GeometryScript_SceneUtils.copy_mesh_from_component(c,dynamic,u.GeometryScriptCopyMeshFromComponentOptions(),False)
    print('GEOMETRY_COPY',result,flush=True)
    query=u.GeometryScript_MeshQueries.get_all_vertex_positions(dynamic,False)
    vectors=u.GeometryScript_List.convert_vector_list_to_array(query[1])
    report['shots'][-1]['vertices_cm']=[v.to_tuple() for v in vectors]
    report['shots'][-1]['copy_outcome']=str(result[-1])
    if state['index']==0:
     print('WEIGHT_READBACK_API',u.GeometryScript_BoneWeights.get_vertex_bone_weights.__doc__,flush=True)
     counts=[];worst=[]
     for vi in range(len(vectors)):
      bw=u.GeometryScript_BoneWeights.get_vertex_bone_weights(dynamic,vi)
      if bw[-1]:
       values=[(int(w.bone_index),float(w.weight)) for w in bw[1] if w.weight>0]
       counts.append(len(values))
       if len(values)>len(worst):worst=values
     report['runtime_weight_count']={'vertices':len(counts),'max':max(counts,default=0),'over8':sum(n>8 for n in counts),'largest_weight_set':worst,'note':'GeometryScript component-copy attributes, not direct GPU render-buffer introspection'}
  left=c.get_socket_location('upperarm_l');right=c.get_socket_location('upperarm_r');center=(left+right)*.5
  def unit(v):return v/max(math.sqrt(v.x*v.x+v.y*v.y+v.z*v.z),1e-8)
  lateral=unit(left-right);up=unit(c.get_socket_location('neck_01')-c.get_socket_location('spine_03'));front=unit(u.Vector(up.y*lateral.z-up.z*lateral.y,up.z*lateral.x-up.x*lateral.z,up.x*lateral.y-up.y*lateral.x))
  direction={'front':front,'back':front*-1,'side':lateral}[angle];loc=center+direction*110+up*15;cam=state['camera'];cam.set_actor_location(loc,False,True);cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(loc,center),False);cam.camera_component.set_field_of_view(60)
  label=f'{sec}_{angle}';u.AutomationLibrary.finish_loading_before_screenshot();state['task']=u.AutomationLibrary.take_high_res_screenshot(700,700,str(OUT/(label+'.png')),cam,force_game_view=True,delay=.2)
  instance=c.get_anim_instance();sample_names=['REVIEW_Vexa_Shoulder_00','REVIEW_Vexa_Nude_Legs_Hip_00'] if SHOULDER else ['REVIEW_Roxie_Nude_Legs_Hip_00','REVIEW_Roxie_Bottom_Hip_00']
  report['shots'].append({'seconds':sec,'actual_position':c.get_position(),'angle':angle,'curves':{n:instance.get_curve_value(n) for n in sample_names},'hip':center.to_tuple(),'bounds':str(u.SystemLibrary.get_component_bounds(c)),'path':str(OUT/(label+'.png'))})
 except Exception:report['errors'].append(traceback.format_exc());finish()
 finally:state['busy']=False
u.EditorPythonScripting.set_keep_python_script_alive(True);state['handle']=u.register_slate_post_tick_callback(tick)
