import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Fresh native paired-curve controls, bone samples and five posed surfaces."""
import unreal as u,json,time,traceback,math
from pathlib import Path
BASE='/Game/SpaceSurvival/Licensed/VexaZeroGSharedHipProof_20261026';OUT=R/'ZeroGSharedHip/NativeControls';OUT.mkdir(exist_ok=True)
receipt=json.loads((R/'ZeroGSharedHip/NativeImport.json').read_text());assert receipt['ok']
controls=json.loads((R/'ZeroGSharedHip/Controls/Report.json').read_text())
clips={n:u.load_asset(BASE+'/A_ZG_'+n) for n in ('01_Drift','02_Spiral','03_Butterfly','04_Inversion','05_LateralArc')};assert all(clips.values())
code=(Path(__file__).resolve().parent/'capture_balanced_motion.py').read_text();code=code[:code.index("state={'start':time.monotonic()")]
code=code.replace('VexaBalancedProof_20261025','VexaZeroGSharedHipProof_20261026').replace('SK_VexaBalancedProof','SK_VexaZeroGShared').replace("clip=u.load_asset(BASE+'/'+asset+'_Anim')","clip=clips['02_Spiral']")
exec(compile(code,__file__,'exec'))
OUT=R/'ZeroGSharedHip/NativeControls';OUT.mkdir(exist_ok=True)
events=[(row,view) for row in controls['rows'] for view in ('front','back')]
state={'start':time.monotonic(),'stage':'wait','event':0,'busy':False};report={'status':'Native paired-curve controls, not full routine acceptance','captures':[],'errors':[]}
def unit(v):return v/max(math.sqrt(v.x*v.x+v.y*v.y+v.z*v.z),1e-8)
def finish():
 report['ok']=not report['errors'] and len(report['captures'])==len(events)
 (R/'ZeroGSharedHip/NativeControls.json').write_text(json.dumps(report,indent=2));print('ZERO_G_NATIVE_CONTROLS',report['ok'],len(report['captures']),report['errors'],flush=True)
 u.unregister_slate_post_tick_callback(state['handle']);ls.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False);u.SystemLibrary.quit_editor()
def tick(dt):
 if state['busy']:return
 state['busy']=True
 try:
  if time.monotonic()-state['start']>300:raise RuntimeError('Native control timeout')
  if state['stage']=='wait':
   if time.monotonic()-state['start']<5:return
   ls.editor_request_begin_play();state['stage']='start';return
  if state['stage']=='start':
   world=ed.get_game_world()
   if not world:return
   actors={a.get_actor_label():a for a in u.GameplayStatics.get_all_actors_of_class(world,u.Actor)}
   if 'BalancedMotionCapture' not in actors:return
   c=actors['HipProof'].skeletal_mesh_component;ca=actors['BalancedMotionCapture'];cc=ca.get_editor_property('capture_component2d');target=u.RenderingLibrary.create_render_target2d(world,800,800,u.TextureRenderTargetFormat.RTF_RGBA8,u.LinearColor(0,0,0,1),False,False)
   cc.set_editor_property('texture_target',target);cc.set_editor_property('capture_source',u.SceneCaptureSource.SCS_FINAL_COLOR_LDR);cc.set_editor_property('capture_every_frame',False);cc.set_editor_property('capture_on_movement',False);cc.set_editor_property('fov_angle',45)
   pawn=u.GameplayStatics.get_player_pawn(world,0)
   if pawn:pawn.set_actor_hidden_in_game(True)
   u.SystemLibrary.execute_console_command(world,'t.MaxFPS 30');u.SystemLibrary.execute_console_command(world,'r.EyeAdaptationQuality 0')
   state.update(world=world,mesh=c,cap=ca,component=cc,target=target,stage='pose');return
  row,view=events[state['event']];name=row['action'].split('ZeroG_')[1];clip=clips[name];sec=min(row['seconds'],clip.sequence_length-.00001);c=state['mesh']
  if state['stage']=='pose':
   c.play_animation(clip,False);c.set_play_rate(0);c.set_position(sec,False);state['ticks']=0;state['stage']='settle';return
  if state['stage']=='settle':
   state['ticks']+=1
   if state['ticks']<2:return
   l=c.get_socket_location('upperarm_l');rr=c.get_socket_location('upperarm_r');side=unit(l-rr);up=unit(c.get_socket_location('neck_01')-c.get_socket_location('spine_03'));front=unit(u.Vector(up.y*side.z-up.z*side.y,up.z*side.x-up.x*side.z,up.x*side.y-up.y*side.x));center=c.get_socket_location('pelvis')+up*15
   loc=center+front*(300 if view=='front' else -300)+up*15;state['cap'].set_actor_location(loc,False,True);state['cap'].set_actor_rotation(u.MathLibrary.find_look_at_rotation(loc,center),False)
   state['bones']={n:c.get_socket_location(n).to_tuple() for n in row['bones_m']}
   if view=='front' and abs(row['seconds']-clip.sequence_length*.5)<.001:
    dynamic=u.DynamicMesh();out=u.GeometryScript_SceneUtils.copy_mesh_from_component(c,dynamic,u.GeometryScriptCopyMeshFromComponentOptions(),True);query=u.GeometryScript_MeshQueries.get_all_vertex_positions(dynamic,False);vectors=u.GeometryScript_List.convert_vector_list_to_array(query[1]);path=OUT/(name+'_Surface.json');path.write_text(json.dumps({'outcome':str(out[-1]),'vertices_world_cm':[v.to_tuple() for v in vectors]}))
   state['component'].capture_scene();state['stage']='export';return
  filename=row['label']+'_'+view+'.png';u.RenderingLibrary.export_render_target(state['world'],state['target'],str(OUT),filename);assert (OUT/filename).is_file()
  report['captures'].append({'label':row['label'],'action':name,'view':view,'seconds':sec,'actual':c.get_position(),'bones_world_cm':state['bones'],'path':str(OUT/filename)})
  state['event']+=1;state['stage']='pose'
  if state['event']==len(events):finish()
 except Exception:report['errors'].append(traceback.format_exc());finish()
 finally:state['busy']=False
u.EditorPythonScripting.set_keep_python_script_alive(True);state['handle']=u.register_slate_post_tick_callback(tick)
