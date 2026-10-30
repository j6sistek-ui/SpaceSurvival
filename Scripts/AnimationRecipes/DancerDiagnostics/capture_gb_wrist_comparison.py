import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Native before/after event capture plus the whole repaired G1 candidate."""
from pathlib import Path
import sys
sys.path.insert(0,str(R))
from distal_native_common import source
code=source('capture_balanced_motion.py')
marker="mesh.set_editor_property('visibility_based_anim_tick_option'"
pos=code.index(marker)
imports="""
u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
clips={}
for entry in json.loads((R/'VexaDistalRepair/GBWristExport.json').read_text())['exports']:
 name='A_Wrist_'+entry['clip']+'_'+entry['kind']
 task=u.AssetImportTask();task.filename=entry['file'];task.destination_path=BASE;task.destination_name=name;task.automated=True;task.save=True;task.replace_existing=True
 opt=u.FbxImportUI();opt.automated_import_should_detect_type=False;opt.import_mesh=False;opt.import_animations=True;opt.import_materials=False;opt.import_textures=False;opt.skeleton=sk.skeleton;opt.mesh_type_to_import=u.FBXImportType.FBXIT_ANIMATION
 opt.anim_sequence_import_data.set_editor_property('use_default_sample_rate',False);opt.anim_sequence_import_data.set_editor_property('custom_sample_rate',60);opt.anim_sequence_import_data.set_editor_property('preserve_local_transform',True);task.options=opt
 u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
 value=u.load_asset(BASE+'/'+name);assert value and abs(value.sequence_length-entry['seconds'])<.02
 assert u.EditorAssetLibrary.save_loaded_asset(value,False)
 clips[entry['clip']+'_'+entry['kind']]=value
clip=clips['g1_after']
"""
code=code[:pos]+imports+code[pos:]
start=code.index("state={'start':time.monotonic()")
code=code[:start]+'''
events=[('g1',220,'l'),('g1',978,'l'),('g2',238,'l'),('b1',1540,'r')]
segments=[]
for key,frame,side in events:
 for kind in ('before','after'):
  length=clips[key+'_'+kind].sequence_length
  start=max(0,min((frame-1)/60-.8,length-47/30))
  segments.append({'name':f'{key}_{frame}_{kind}','key':key+'_'+kind,'start':start,'frames':48,'fps':30,'side':side,'camera':'wrist'})
segments.append({'name':'g1_whole_after','key':'g1_after','start':0,'frames':405,'fps':24,'camera':'body'})
OUT=R/'NativeGBWristComparison';OUT.mkdir(exist_ok=True)
for seg in segments:(OUT/seg['name']).mkdir(exist_ok=True)
state={'start':time.monotonic(),'stage':'wait','frame':0,'segment':0,'busy':False}
report={'segments':segments,'captured':[],'errors':[],'status':'Private unconstrained clips on Vexa. Spiral morph curves absent; no contact or anatomy acceptance.'}
def finish():
 report['ok']=not report['errors'] and len(report['captured'])==sum(x['frames'] for x in segments)
 (R/'NativeGBWristComparison.json').write_text(json.dumps(report,indent=2))
 print('GB_NATIVE_COMPARISON',report['ok'],len(report['captured']),report['errors'],flush=True)
 u.unregister_slate_post_tick_callback(state['handle']);ls.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False);u.SystemLibrary.quit_editor()
def unit(v):return v/max(math.sqrt(v.x*v.x+v.y*v.y+v.z*v.z),1e-8)
def cross(a,b):return u.Vector(a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x)
def tick(dt):
 if state['busy']:return
 state['busy']=True
 try:
  now=time.monotonic()
  if now-state['start']>360:raise RuntimeError('GB comparison timeout')
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
   pawn=u.GameplayStatics.get_player_pawn(world,0)
   if pawn:pawn.set_actor_hidden_in_game(True)
   for cmd in ('t.MaxFPS 60','r.EyeAdaptationQuality 0','r.SkinCache.Mode 1','r.SkinCache.RecomputeTangents 1'):u.SystemLibrary.execute_console_command(world,cmd)
   state.update(world=world,mesh=c,cap=ca,component=cc,target=target,stage='pose');return
  seg=segments[state['segment']];frame=state['frame'];sec=seg['start']+frame/seg['fps'];c=state['mesh']
  if state['stage']=='pose':
   if frame==0:c.play_animation(clips[seg['key']],False);c.set_play_rate(0)
   c.set_position(sec,False);state['ticks']=0;state['stage']='settle';return
  if state['stage']=='settle':
   state['ticks']+=1
   if state['ticks']<2:return
   l=c.get_socket_location('upperarm_l');rr=c.get_socket_location('upperarm_r');side=unit(l-rr);up=unit(c.get_socket_location('neck_01')-c.get_socket_location('spine_03'));front=unit(cross(up,side))
   if seg['camera']=='wrist':
    hand=c.get_socket_location('hand_'+seg['side']);elbow=c.get_socket_location('lowerarm_'+seg['side']);center=hand+unit(hand-elbow)*4
    loc=center+front*33+side*(18 if seg['side']=='l' else -18)
   else:center=c.get_socket_location('pelvis')+up*15;loc=center+front*230+side*65+up*20
   state['cap'].set_actor_location(loc,False,True);state['cap'].set_actor_rotation(u.MathLibrary.find_look_at_rotation(loc,center),False)
   state['component'].capture_scene();state['stage']='export';return
  name=f'{frame:04d}.png';folder=OUT/seg['name'];u.RenderingLibrary.export_render_target(state['world'],state['target'],str(folder),name)
  file=folder/name;assert file.is_file() and file.stat().st_size>5000
  assert abs(sec-c.get_position())<1e-5,(seg['name'],sec,c.get_position())
  report['captured'].append({'segment':seg['name'],'frame':frame,'seconds':sec,'actual_position':c.get_position(),'path':str(file)})
  state['frame']+=1;state['stage']='pose'
  if state['frame']==seg['frames']:
   print('GB_SEGMENT_DONE',seg['name'],flush=True);state['frame']=0;state['segment']+=1
  if state['segment']==len(segments):finish()
 except Exception:report['errors'].append(traceback.format_exc());finish()
 finally:state['busy']=False
u.EditorPythonScripting.set_keep_python_script_alive(True);state['handle']=u.register_slate_post_tick_callback(tick)
'''
exec(compile(code,__file__,'exec'))
