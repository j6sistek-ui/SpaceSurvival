import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Fresh five-segment motion capture; native normal-band defect remains OPEN."""
import unreal as u,json,time,traceback,math,hashlib
from pathlib import Path
B='/Game/SpaceSurvival/Licensed/VexaZeroGSharedHipProof_20261026';O=R/'ZeroGSharedHip/FullMotion';O.mkdir(exist_ok=True)
assert json.loads((R/'ZeroGSharedHip/WhiteMaskImport.json').read_text())['ok']
for cmd in ('r.SkinCache.Mode 1','r.SkinCache.RecomputeTangents 2'):u.SystemLibrary.execute_console_command(None,cmd)
BASE=B;code=(Path(__file__).resolve().parent/'capture_balanced_motion.py').read_text();code=code[:code.index("state={'start':time.monotonic()")]
code=code.replace('VexaBalancedProof_20261025','VexaZeroGSharedHipProof_20261026').replace('SK_VexaBalancedProof','SK_VexaZeroGWhiteMask').replace("clip=u.load_asset(BASE+'/'+asset+'_Anim')","clip=u.load_asset(BASE+'/A_ZG_02_Spiral')")
exec(compile(code,__file__,'exec'))
editor=u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem)
sections=[{'index':i,'recompute':editor.get_section_recompute_tangent(sk,0,i),'mask':editor.get_section_recompute_tangents_vertex_mask_channel(sk,0,i)} for i in range(editor.get_num_sections(sk,0))]
assert all(x['recompute'] and x['mask']==1 for x in sections)
assert editor.get_lod_build_settings(sk,0).get_editor_property('bone_influence_limit')==12
mesh.set_editor_property('skin_cache_usage',[u.SkinCacheUsage.ENABLED])
clips={n:u.load_asset(B+'/A_ZG_'+n) for n in ('01_Drift','02_Spiral','03_Butterfly','04_Inversion','05_LateralArc')};assert all(clips.values())
for clip in clips.values():
 assert clip.get_editor_property('skeleton')==sk.skeleton
 assert len([x for x in u.AnimationLibrary.get_animation_curve_names(clip,u.RawCurveTrackTypes.RCT_FLOAT) if str(x).casefold().startswith('review_zg_')])==160
FPS=24;views=('front','back','stage');events=[]
for name,clip in clips.items():
 for view in views:
  (O/name/view).mkdir(parents=True,exist_ok=True)
  events.extend((name,view,i,i/FPS) for i in range(round(clip.sequence_length*FPS)))
report={'status':'Private native motion review; normal-band defect OPEN; no owner or production acceptance','mesh':sk.get_path_name(),'fps':FPS,'sections':sections,'clips':{n:c.sequence_length for n,c in clips.items()},'captures':[],'errors':[]}
state={'start':time.monotonic(),'stage':'wait','event':0,'busy':False,'loaded':None}
def unit(v):return v/max(math.sqrt(v.x*v.x+v.y*v.y+v.z*v.z),1e-8)
def finish():
 report['ok']=not report['errors'] and len(report['captures'])==len(events)
 (R/'ZeroGSharedHip/FullMotion.json').write_text(json.dumps(report,indent=2));print('ZERO_G_FULL_MOTION',report['ok'],len(report['captures']),report['errors'],flush=True)
 u.unregister_slate_post_tick_callback(state['handle']);ls.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False);u.SystemLibrary.quit_editor()
def tick(dt):
 if state['busy']:return
 state['busy']=True
 try:
  if time.monotonic()-state['start']>950:raise RuntimeError('Full native capture timeout')
  if state['stage']=='wait':
   if time.monotonic()-state['start']<5:return
   ls.editor_request_begin_play();state['stage']='start';return
  if state['stage']=='start':
   world=ed.get_game_world()
   if not world:return
   actors={a.get_actor_label():a for a in u.GameplayStatics.get_all_actors_of_class(world,u.Actor)}
   if 'BalancedMotionCapture' not in actors:return
   c=actors['HipProof'].skeletal_mesh_component;c.set_editor_property('skin_cache_usage',[u.SkinCacheUsage.ENABLED]);ca=actors['BalancedMotionCapture'];cc=ca.get_editor_property('capture_component2d');target=u.RenderingLibrary.create_render_target2d(world,640,640,u.TextureRenderTargetFormat.RTF_RGBA8,u.LinearColor(0,0,0,1),False,False)
   cc.set_editor_property('texture_target',target);cc.set_editor_property('capture_source',u.SceneCaptureSource.SCS_FINAL_COLOR_LDR);cc.set_editor_property('capture_every_frame',False);cc.set_editor_property('capture_on_movement',False);cc.set_editor_property('fov_angle',45)
   pawn=u.GameplayStatics.get_player_pawn(world,0)
   if pawn:pawn.set_actor_hidden_in_game(True)
   for cmd in ('t.MaxFPS 60','r.EyeAdaptationQuality 0','r.SkinCache.Mode 1','r.SkinCache.RecomputeTangents 2'):u.SystemLibrary.execute_console_command(world,cmd)
   report['cache_cvars']={n:u.SystemLibrary.get_console_variable_int_value(n) for n in ('r.SkinCache.CompileShaders','r.SkinCache.Mode','r.SkinCache.RecomputeTangents')};assert report['cache_cvars']['r.SkinCache.CompileShaders']==1
   state.update(world=world,mesh=c,cap=ca,component=cc,target=target,stage='pose');return
  name,view,index,sec=events[state['event']];c=state['mesh'];clip=clips[name]
  if state['stage']=='pose':
   if state['loaded']!=name:c.play_animation(clip,False);c.set_play_rate(0);state['loaded']=name
   c.set_position(sec,False);state['ticks']=0;state['stage']='settle';return
  if state['stage']=='settle':
   state['ticks']+=1
   if state['ticks']<2:return
   l=c.get_socket_location('upperarm_l');rr=c.get_socket_location('upperarm_r');side=unit(l-rr);up=unit(c.get_socket_location('neck_01')-c.get_socket_location('spine_03'));front=unit(u.Vector(up.y*side.z-up.z*side.y,up.z*side.x-up.x*side.z,up.x*side.y-up.y*side.x));center=c.get_socket_location('pelvis')+up*15
   if view=='stage':center=u.Vector(0,0,1200);loc=center+u.Vector(500,-800,200)
   else:loc=center+front*(300 if view=='front' else -300)+up*15
   state['cap'].set_actor_location(loc,False,True);state['cap'].set_actor_rotation(u.MathLibrary.find_look_at_rotation(loc,center),False)
   if state['event']==0:
    dyn=u.DynamicMesh();u.GeometryScript_AssetUtils.copy_mesh_from_skeletal_mesh(sk,dyn,u.GeometryScriptCopyMeshFromAssetOptions(),u.GeometryScriptMeshReadLOD());colors=u.GeometryScript_VertexColors.get_mesh_per_vertex_colors(dyn,True)
    report['vertex_color_valid']=colors[2]
    if colors[2]:
     values=u.GeometryScript_List.convert_color_list_to_array(colors[1]);report['green_mask_range']=[min(x.g for x in values),max(x.g for x in values)];assert min(x.g for x in values)>.999
   state['component'].capture_scene();state['stage']='export';return
  folder=O/name/view;filename=f'{index:05d}.png';u.RenderingLibrary.export_render_target(state['world'],state['target'],str(folder),filename);assert (folder/filename).is_file()
  report['captures'].append({'clip':name,'view':view,'frame':index,'seconds':sec,'actual':c.get_position()})
  state['event']+=1;state['stage']='pose'
  if state['event']%384==0:print('ZERO_G_CAPTURE_PROGRESS',state['event'],len(events),flush=True)
  if state['event']==len(events):finish()
 except Exception:report['errors'].append(traceback.format_exc());finish()
 finally:state['busy']=False
u.EditorPythonScripting.set_keep_python_script_alive(True);state['handle']=u.register_slate_post_tick_callback(tick)
