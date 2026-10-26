import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Fresh native morph/geometry readback, three-angle hip stills and full loop."""
import unreal as u
import json, time, traceback, hashlib, math
from pathlib import Path
variant=os.environ.get('SS_G2_VARIANT','')
assert variant in ('', 'glute_follow', 'glute_follow_240', 'palmar', 'g1_shoulder', 'g1_shoulder_cap', 'g1_g2_join', 'floating_phrase'), 'Unknown proof variant'
join=variant=='g1_g2_join'
g1_shoulder=variant in ('g1_shoulder','g1_shoulder_cap','g1_g2_join')
palmar=variant in ('palmar','floating_phrase')
glute_follow=g1_shoulder or variant in ('glute_follow','glute_follow_240','palmar','floating_phrase')
refined_rate=variant=='glute_follow_240'
stem='G1Shoulder240' if g1_shoulder else 'G2Palmar240' if palmar else 'G2GluteFollow240' if refined_rate else 'G2GluteFollow' if glute_follow else 'G2PosteriorHip'
O=R/('G1ShoulderNative240' if g1_shoulder else 'G2PalmarNative240' if palmar else 'G2GluteFollowNative240' if refined_rate else 'G2GluteFollowNative' if glute_follow else 'G2PosteriorHip')
if variant=='g1_shoulder_cap':
    O,stem=R/'G1ShoulderCapNative240','G1ShoulderCap240'
if join:
    O,stem=R/'G1G2JoinNative240','G1G2Join240'
if variant=='floating_phrase':
    O,stem=R/'G2FloatingPhraseNative240','G2FloatingPhrase240'
normal_control=os.environ.get('SS_G1_NORMAL_CONTROL') in ('1','local')
recompute=os.environ.get('SS_G1_RECOMPUTE') in ('1','local')
local_normals='local' in (os.environ.get('SS_G1_NORMAL_CONTROL'),os.environ.get('SS_G1_RECOMPUTE'))
if join:
    recompute=local_normals=True
shoulder_motion=os.environ.get('SS_G1_SHOULDER_MOTION')=='1'
assert not shoulder_motion or (g1_shoulder and local_normals and not normal_control)
assert not (normal_control or recompute) or variant in ('g1_shoulder_cap','g1_g2_join')
control_name='NativeLocalNormalControl' if local_normals else 'NativeNormalControl'
OUT=O/(control_name if normal_control else 'NativeShoulderMotion' if shoulder_motion else 'NativeViews');OUT.mkdir(exist_ok=True)
BASE='/Game/SpaceSurvival/Licensed/Vexa'+stem+'Proof_20261026'
assert 'WorkbenchNative/CharacterWorkbench' in u.Paths.get_project_file_path().replace('\\','/')
receipt=json.loads((O/'NativeImport.json').read_text()); assert receipt['ok']
controls=json.loads((O/'SourceControls.json').read_text()); assert controls['source_sha256']==receipt['source_sha256']
if glute_follow:assert controls['action_sha256']==receipt['action_sha256']
sk=u.load_asset(receipt['mesh']); clip=u.load_asset(receipt['clip'])
if local_normals and not join:
    normal_receipt=json.loads((O/'NativeLocalNormals.json').read_text())
    assert normal_receipt['ok'] and normal_receipt['source_sha256']==receipt['source_sha256']
    sk=u.load_asset(normal_receipt['mesh'])
assert sk and clip and sk.skeleton==clip.get_editor_property('skeleton')
normal_settings=[]
if normal_control or recompute:
    editor=u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem)
    for i in range(editor.get_num_sections(sk,0)):
        normal_settings.append({'section':i,'before':editor.get_section_recompute_tangent(sk,0,i),'mask_before':editor.get_section_recompute_tangents_vertex_mask_channel(sk,0,i)})
        assert editor.set_section_recompute_tangent(sk,0,i,True)
        # Installed ESkinVertexColorChannel::None == Alpha == 3. No colour mask.
        assert editor.set_section_recompute_tangents_vertex_mask_channel(sk,0,i,1 if local_normals else 3)
    # No source asset save: this is a bounded rendering control.
content_root=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_content_dir())).resolve()
protected={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (content_root/BASE.replace('/Game/','')).glob('*.uasset')}
assert protected, 'Native proof guard must cover actual files'
if palmar:
    reused=content_root/'SpaceSurvival/Licensed/VexaG2GluteFollow240Proof_20261026'
    protected.update({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in reused.glob('*.uasset')})
es=u.get_editor_subsystem(u.EditorActorSubsystem); ls=u.get_editor_subsystem(u.LevelEditorSubsystem); ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
assert u.EditorLoadingAndSavingUtils.new_map_from_template('/Game/SpaceSurvival/Licensed/ZeroGSourceBaseline_20261025/L_SourceBaseline_Review',False)
for a in es.get_all_level_actors():
    if a.get_components_by_class(u.SkeletalMeshComponent) or a.get_actor_label().startswith(('Contact/','OriginalSource/')): es.destroy_actor(a)
actor=es.spawn_actor_from_class(u.SkeletalMeshActor,u.Vector(0,0,1080)); actor.set_actor_label('PosteriorHipProof'); mesh=actor.skeletal_mesh_component
mesh.set_skeletal_mesh_asset(sk); mesh.override_animation_data(clip,False,False,0,0); mesh.set_update_animation_in_editor(True)
mesh.set_collision_profile_name('NoCollision'); mesh.set_editor_property('bounds_scale',5.)
mesh.set_editor_property('visibility_based_anim_tick_option',u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
if normal_control or recompute:mesh.set_editor_property('skin_cache_usage',[u.SkinCacheUsage.ENABLED])
gray=u.load_asset('/Game/SpaceSurvival/Licensed/VexaHandIsolationProof_20261026/M_ProofGray'); assert gray
for i in range(mesh.get_num_materials()):mesh.set_material(i,gray)
pole=es.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,1330)); pole.set_actor_label('Orange50mmPole')
pole.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cylinder')); pole.set_actor_scale3d(u.Vector(.05,.05,5.))
orange=u.load_asset('/Game/SpaceSurvival/Licensed/VexaPoleReleaseProof_20261026/M_OrangePole'); assert orange
pole.static_mesh_component.set_material(0,orange); pole.static_mesh_component.set_collision_profile_name('NoCollision')
cap=es.spawn_actor_from_class(u.SceneCapture2D,u.Vector()); cap.set_actor_label('PosteriorHipCapture')
if not (normal_control or shoulder_motion):assert u.EditorLoadingAndSavingUtils.save_map(ed.get_editor_world(),BASE+'/L_'+stem+'_Review')
fps=24;count=round(clip.sequence_length*fps)+1
events=[{'kind':'still','row':row,'view':view,'seconds':row['seconds'],'filename':row['label']+'_'+view+'.png'} for row in controls['rows'] for view in ('front','back','side')]
if palmar:
    events += [{'kind':'hand','row':row,'view':view,'seconds':row['seconds'],'filename':row['label']+'_hand_'+view+'.png'} for row in controls['rows'][1:] for view in ('front','back')]
if g1_shoulder:
    events += [{'kind':'shoulder','row':row,'view':view,'seconds':row['seconds'],'filename':row['label']+'_shoulder_'+view+'.png'} for row in controls['rows'] for view in ('front','back','side')]
events += [{'kind':'motion','view':'back','seconds':min(i/fps,clip.sequence_length),'filename':f'loop_{i:04d}.png'} for i in range(count)]
if normal_control:
    events=[{'kind':'shoulder','row':row,'view':view,'normal_mode':mode,'seconds':row['seconds'],'filename':row['label']+'_'+view+'_'+mode+'.png'} for row in controls['rows'][1:4] for view in ('front','back','side') for mode in ('skinned','recomputed')]
if shoulder_motion:
    events=[{'kind':'shoulder_motion','view':'front','row':controls['rows'][0],'seconds':min(i/fps,clip.sequence_length),'filename':f'loop_{i:04d}.png'} for i in range(count)]
report={'source_sha256':receipt['source_sha256'],'action_sha256':receipt.get('action_sha256'),'asset':receipt['clip'],'map':BASE+'/L_'+stem+'_Review','fps':fps,'frames':count,'captures':[],'errors':[], 'scope':'Private single-character source/native parity and visual review; not full anatomy, garments or production acceptance.'}
if normal_control:
    report['map']=None
    report['frames']=0
state={'start':time.monotonic(),'stage':'wait','event':0,'busy':False}
def unit(v):return v/max(math.sqrt(v.x*v.x+v.y*v.y+v.z*v.z),1e-8)
def finish():
    report['native_inputs_unchanged']=all(Path(p).is_file() and hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in protected.items())
    report['ok']=not report['errors'] and report['native_inputs_unchanged'] and len(report['captures'])==len(events)
    report['normal_settings']=normal_settings
    report['cache_cvars']={n:u.SystemLibrary.get_console_variable_int_value(n) for n in ('r.SkinCache.CompileShaders','r.SkinCache.Mode','r.SkinCache.RecomputeTangents')}
    report['mesh']=sk.get_path_name()
    report['local_normal_mask']=local_normals
    (O/(control_name+'.json' if normal_control else 'NativeShoulderMotion.json' if shoulder_motion else 'NativeCapture.json')).write_text(json.dumps(report,indent=2)); print('G2_POSTERIOR_NATIVE_CAPTURE',report['ok'],len(report['captures']),report['errors'],flush=True)
    u.unregister_slate_post_tick_callback(state['handle']);ls.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False);u.SystemLibrary.quit_editor()
def tick(dt):
    if state['busy']:return
    state['busy']=True
    try:
        now=time.monotonic()
        if now-state['start']>600:raise RuntimeError('Native posterior review timed out')
        if state['stage']=='wait':
            if now-state['start']<5:return
            ls.editor_request_begin_play();state['stage']='start';return
        if state['stage']=='start':
            world=ed.get_game_world()
            if not world:return
            actors={a.get_actor_label():a for a in u.GameplayStatics.get_all_actors_of_class(world,u.Actor)}
            if 'PosteriorHipCapture' not in actors:return
            c=actors['PosteriorHipProof'].skeletal_mesh_component;ca=actors['PosteriorHipCapture'];cc=ca.get_editor_property('capture_component2d')
            target=u.RenderingLibrary.create_render_target2d(world,800,800,u.TextureRenderTargetFormat.RTF_RGBA8,u.LinearColor(0,0,0,1),False,False)
            cc.set_editor_property('texture_target',target);cc.set_editor_property('capture_source',u.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
            cc.set_editor_property('capture_every_frame',False);cc.set_editor_property('capture_on_movement',False);cc.set_editor_property('fov_angle',45.)
            pawn=u.GameplayStatics.get_player_pawn(world,0)
            if pawn:pawn.set_actor_hidden_in_game(True)
            for cmd in ('t.MaxFPS 60','r.EyeAdaptationQuality 0'):u.SystemLibrary.execute_console_command(world,cmd)
            if normal_control or recompute:
                c.set_editor_property('skin_cache_usage',[u.SkinCacheUsage.ENABLED])
                for cmd in ('r.SkinCache.Mode 1','r.SkinCache.RecomputeTangents 2'):u.SystemLibrary.execute_console_command(world,cmd)
            c.play_animation(clip,False);c.set_play_rate(0)
            state.update(world=world,mesh=c,cap=ca,component=cc,target=target,stage='pose');return
        event=events[state['event']];c=state['mesh'];sec=event['seconds']
        if state['stage']=='pose':
            if normal_control:u.SystemLibrary.execute_console_command(state['world'],'r.SkinCache.RecomputeTangents '+('2' if event['normal_mode']=='recomputed' else '0'))
            c.set_position(sec,False);state['ticks']=0;state['stage']='settle';return
        if state['stage']=='settle':
            state['ticks']+=1
            if state['ticks']<2:return
            if event['kind'] in ('still','hand','shoulder','shoulder_motion'):
                side=unit(c.get_socket_location('upperarm_l')-c.get_socket_location('upperarm_r'))
                up=unit(c.get_socket_location('neck_01')-c.get_socket_location('spine_03'))
                front=unit(u.Vector(up.y*side.z-up.z*side.y,up.z*side.x-up.x*side.z,up.x*side.y-up.y*side.x))
                center=c.get_socket_location('pelvis')
                direction=front if event['view']=='front' else front*-1 if event['view']=='back' else side
                loc=center+direction*185+up*15
                row=event['row'];state['bones']={n:c.get_socket_location(n).to_tuple() for n in row['bones_m']}
                if event['kind']=='hand':
                    center=c.get_socket_location('hand_r')
                    loc=center+unit(u.Vector(3,-5,2) if event['view']=='front' else u.Vector(-3,5,2))*55
                if event['kind'] in ('shoulder','shoulder_motion'):
                    center=c.get_socket_location('spine_05')*.65+c.get_socket_location('upperarm_l')*.35
                    loc=center+direction*115+up*12
                if event['view']=='front' and event['kind']=='still':
                    dynamic=u.DynamicMesh(); result=u.GeometryScript_SceneUtils.copy_mesh_from_component(c,dynamic,u.GeometryScriptCopyMeshFromComponentOptions(),True)
                    query=u.GeometryScript_MeshQueries.get_all_vertex_positions(dynamic,False); vectors=u.GeometryScript_List.convert_vector_list_to_array(query[1])
                    (OUT/(row['label']+'_Surface.json')).write_text(json.dumps({'outcome':str(result[-1]),'vertices_world_cm':[v.to_tuple() for v in vectors]}))
            else:
                points=[c.get_socket_location(n) for n in controls['rows'][0]['bones_m'] if n not in ('root','Root') and not n.startswith('ik_')]
                center=u.Vector((min(v.x for v in points)+max(v.x for v in points))*.5,(min(v.y for v in points)+max(v.y for v in points))*.5,(min(v.z for v in points)+max(v.z for v in points))*.5)
                radius=max(math.sqrt((v.x-center.x)**2+(v.y-center.y)**2+(v.z-center.z)**2) for v in points)
                distance=max(450.,(radius+30.)/math.sin(math.radians(22.5)))
                loc=center+unit(u.Vector(-390,585,70))*distance;state['bones']={}
                state['framing']={'radius_cm':radius,'distance_cm':distance,'center':center.to_tuple()}

            state['cap'].set_actor_location(loc,False,True);state['cap'].set_actor_rotation(u.MathLibrary.find_look_at_rotation(loc,center),False)
            state['component'].capture_scene();state['stage']='export';return
        u.RenderingLibrary.export_render_target(state['world'],state['target'],str(OUT),event['filename']);path=OUT/event['filename']
        assert path.is_file() and path.stat().st_size>5000 and abs(c.get_position()-sec)<.0001
        report['captures'].append({'kind':event['kind'],'label':event.get('row',{}).get('label'),'view':event['view'],'normal_mode':event.get('normal_mode'),'seconds':sec,'bones_world_cm':state['bones'],'path':str(path)})
        state['event']+=1;state['stage']='pose'
        if state['event']==len(events):finish()
    except Exception:report['errors'].append(traceback.format_exc());finish()
    finally:state['busy']=False
u.EditorPythonScripting.set_keep_python_script_alive(True);state['handle']=u.register_slate_post_tick_callback(tick)
