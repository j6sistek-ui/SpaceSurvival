"""Fresh persisted rig checks and optional unsaved native Unreal pose preview.

Use --preview as a Python script argument for four native asset captures. This
never edits a map/content package or establishes gameplay/CPU-vertex contact QA.
"""
import hashlib,importlib.util,json,sys,time
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ss_tail_import',ROOT/'Scripts/AuthorTailRepair.py');author=importlib.util.module_from_spec(spec);spec.loader.exec_module(author)
OUT=ROOT/'ContentSource/TailCandidateV2Preview'


def vector(v):return [float(v.x),float(v.y),float(v.z)]


def validate():
    source,manifest=author.verify_source();library=u.EditorAssetLibrary;mesh=library.load_asset(author.TARGET);original=library.load_asset(author.BASE+'/SK_Acornaut')
    assert isinstance(mesh,u.SkeletalMesh) and isinstance(original,u.SkeletalMesh)
    assert library.get_metadata_tag(mesh,'SSTailRepairVersion')==author.VERSION
    assert library.get_metadata_tag(mesh,'SSTailRepairSourceSHA256')==manifest['sha256']
    skeleton=original.get_editor_property('skeleton');assert mesh.get_editor_property('skeleton')==skeleton
    material=lambda asset:[slot.get_editor_property('material_interface').get_path_name() for slot in asset.get_editor_property('materials')]
    assert material(mesh)==material(original),'Original materials changed'
    assert mesh.get_editor_property('physics_asset') is None,'Unrequested physics asset'
    clips=[]
    for name,seconds in [('Pilot',4.0),('Walk',74/30),('Disembark',2.4)]:
        clip=library.load_asset(author.BASE+'/A_'+name);assert isinstance(clip,u.AnimSequence)
        assert clip.get_editor_property('skeleton')==skeleton,'Animation skeleton mismatch'
        assert abs(clip.get_editor_property('sequence_length')-seconds)<.04,'Unexpected clip duration'
        assert not clip.get_editor_property('enable_root_motion'),'Unexpected root-motion extraction'
        clips.append({'path':clip.get_path_name(),'seconds':float(clip.get_editor_property('sequence_length')),'same_skeleton':True,'root_motion':False})
    bounds=mesh.get_imported_bounds();path=ROOT/'Content/SpaceSurvival/Character/SK_AcornautTailV2.uasset'
    return {'status':'TAIL_V2_PERSISTED_RIG_VALIDATED_NOT_RUNTIME_ACCEPTANCE','engine':u.SystemLibrary.get_engine_version(),'errors':[],
            'source_sha256':manifest['sha256'],'mesh':mesh.get_path_name(),'mesh_package_sha256':author.digest(path),'mesh_package_bytes':path.stat().st_size,
            'original_skeleton':skeleton.get_path_name(),'materials':material(mesh),'animations':clips,'no_new_physics_asset':True,
            'imported_bounds_origin_cm':vector(bounds.origin),'imported_bounds_extent_cm':vector(bounds.box_extent),
            'limits':['Shared skeleton/materials and asset checks do not prove CPU-skinned body equality or frame contact',
                      'Exact269-frame source body equality is in Deformation.json; native station CPU-vertex contact test remains lead-owned',
                      'Thin residual fragments remain; provisional visual repair, not owner quality approval']}


def preview(record):
    u.EditorLoadingAndSavingUtils.new_blank_map(False);actors=u.get_editor_subsystem(u.EditorActorSubsystem);world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    protected={path:author.digest(path) for path in (ROOT/'Content').rglob('*.uasset')}
    def static(path,position,scale=(1,1,1),material=None):
        actor=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*position));component=actor.get_component_by_class(u.StaticMeshComponent);component.set_mobility(u.ComponentMobility.MOVABLE);component.set_static_mesh(u.load_asset(path));component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);actor.set_actor_scale3d(u.Vector(*scale))
        if material:component.set_material(0,u.load_asset(material))
        return actor
    ship=static('/Game/SpaceSurvival/Meshes/SM_AcornShipV2',(0,0,0));floor=static('/Engine/BasicShapes/Cube',(0,0,-82.25),(30,30,.1),'/Game/SpaceSurvival/Materials/M_AcornV2_GraphiteStructure')
    for rotation,color,intensity in [((-40,-30,0),(.72,.85,1,1),7),((-28,150,0),(1,.7,.4,1),9),((-65,70,0),(.5,.7,1,1),3)]:
        light=actors.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,500),u.Rotator(pitch=rotation[0],yaw=rotation[1],roll=0));lamp=light.get_component_by_class(u.DirectionalLightComponent);lamp.set_mobility(u.ComponentMobility.MOVABLE);lamp.set_light_color(u.LinearColor(*color));lamp.set_intensity(intensity)
    post=actors.spawn_actor_from_class(u.PostProcessVolume,u.Vector(0,0,0));post.set_editor_property('unbound',True);settings=post.get_editor_property('settings')
    for key,value in {'override_auto_exposure_min_brightness':True,'override_auto_exposure_max_brightness':True,'auto_exposure_min_brightness':1.0,'auto_exposure_max_brightness':1.0,'override_bloom_intensity':True,'bloom_intensity':.2}.items():settings.set_editor_property(key,value)
    post.set_editor_property('settings',settings)
    camera=actors.spawn_actor_from_class(u.CameraActor,u.Vector(0,0,0));u.get_editor_subsystem(u.LevelEditorSubsystem).editor_set_game_view(True)
    cases=[{'name':'UnrealSeatedRear','clip':'Pilot','time':1.0,'position':(-15,0,72),'camera':(-280,310,200),'target':(-15,0,93),'fov':50,'ship':False,'floor_top':-77.25},
           {'name':'UnrealShipPilotRear','clip':'Pilot','time':1.0,'position':(-15,0,72),'camera':(-820,530,400),'target':(-40,0,55),'fov':50,'ship':True,'floor_top':-77.25},
           {'name':'UnrealWalkHandoff','clip':'Walk','time':.308333333,'position':(0,0,97.10404241),'camera':(-340,380,175),'target':(20,0,100),'fov':52,'ship':False,'floor_top':2.75},
           {'name':'UnrealExitContact','clip':'Disembark','time':1.6,'position':(0,0,97.10404241),'camera':(-340,380,175),'target':(20,0,100),'fov':52,'ship':False,'floor_top':2.75}]
    state={'index':0,'frames':0,'task':None,'actors':[],'components':[],'handle':None,'start':time.monotonic(),'samples':[],'errors':[]}
    def set_case():
        for actor in state['actors']:actors.destroy_actor(actor)
        state['actors']=[];state['components']=[];case=cases[state['index']]
        for path in (author.TARGET,author.BASE+'/SK_Acornaut'):
            actor=actors.spawn_actor_from_class(u.SkeletalMeshActor,u.Vector(*case['position']),u.Rotator(pitch=0,yaw=-90,roll=0));component=actor.get_component_by_class(u.SkeletalMeshComponent);component.set_skeletal_mesh_asset(u.load_asset(path));component.set_update_animation_in_editor(True);component.set_editor_property('visibility_based_anim_tick_option',u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES);component.set_animation_mode(u.AnimationMode.ANIMATION_BLUEPRINT);actor.set_actor_scale3d(u.Vector(1.5,1.5,1.5));component.override_animation_data(u.load_asset(author.BASE+'/A_'+case['clip']),True,False,case['time'],1.0);component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
            if path!=author.TARGET:component.set_visibility(False);component.set_editor_property('cast_shadow',False)
            state['actors'].append(actor);state['components'].append(component)
        ship.set_is_temporarily_hidden_in_editor(not case['ship']);ship.set_actor_hidden_in_game(not case['ship']);floor.set_actor_location(u.Vector(0,0,case['floor_top']-5),False,False)
        location=u.Vector(*case['camera']);rotation=u.MathLibrary.find_look_at_rotation(location,u.Vector(*case['target']));camera.set_actor_location(location,False,False);camera.set_actor_rotation(rotation,False);camera.get_component_by_class(u.CameraComponent).set_field_of_view(case['fov']);u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(location,rotation)
        state['frames']=0;state['task']=None
    def finish(status):
        changed=[str(path.relative_to(ROOT)) for path,digest in protected.items() if author.digest(path)!=digest]
        if changed:state['errors'].append('Content changed during stock preview: '+','.join(changed))
        receipt={'status':status if not state['errors'] else 'FAILED','errors':state['errors'],'source_sha256':record['source_sha256'],'mesh_package_sha256':record['mesh_package_sha256'],'engine':record['engine'],'samples':state['samples'],'protected_content_packages_unchanged':len(protected) if not changed else None,'limits':['Unsaved stock actors, not native game flow','Sampled pose and bone comparisons do not establish CPU-skinned vertex equality or collision/sole contact','Floor at2.75cm models visible deck top only; lead-owned real station automation checks actual CPU-skinned sole','Thin residual fur fragments remain; no owner visual approval']}
        (OUT/'UnrealPreview.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');u.unregister_slate_post_tick_callback(state['handle']);u.EditorPythonScripting.set_keep_python_script_alive(False);u.SystemLibrary.quit_editor()
    def tick(delta):
        try:
            state['frames']+=1;case=cases[state['index']];path=OUT/(case['name']+'.png')
            if state['frames']==30:
                repaired,original=state['components'];names=[str(repaired.get_bone_name(i)) for i in range(repaired.get_num_bones())];assert names==[str(original.get_bone_name(i)) for i in range(original.get_num_bones())] and len(names)==52
                error=max((repaired.get_socket_location(name)-original.get_socket_location(name)).length() for name in names);assert error<.001,'Original body skeleton pose differs'
                # get_socket_location answers a name the rig does not have with the component transform and no
                # complaint, so a bone that stopped existing would be filed below as a plausible measurement
                # rather than as a gap. Unreal matches these names without regard to case; so does this.
                probes=('Pelvis','Head','L_Foot','R_Foot','L_Ankle','R_Ankle');present={name.lower() for name in names};absent=[name for name in probes if name.lower() not in present];assert not absent,'Repaired hero has no such bones to sample: '+','.join(absent)
                sample={**case,'scale':1.5,'yaw':-90,'bone_count':len(names),'max_original_vs_repaired_bone_location_difference_cm':error,'sampled_seconds':repaired.get_position(),'sockets_world_cm':{name:vector(repaired.get_socket_location(name)) for name in probes},'png':str(path.relative_to(ROOT))};state['samples'].append(sample)
                u.AutomationLibrary.finish_loading_before_screenshot();state['task']=u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(path),camera,delay=.3);assert state['task'].is_valid_task()
            if state['task'] and state['task'].is_task_done() and path.exists():
                state['index']+=1
                if state['index']==len(cases):finish('NATIVE_UNREAL_ASSET_PREVIEW_CAPTURED_NOT_GAMEPLAY')
                else:set_case()
            elif time.monotonic()-state['start']>150:state['errors'].append('Screenshot timeout');finish('FAILED')
        except Exception as error:state['errors'].append(str(error));u.log_error(str(error));finish('FAILED')
    set_case();u.EditorPythonScripting.set_keep_python_script_alive(True);state['handle']=u.register_slate_post_tick_callback(tick)


def main(preview_images=False):
    record={'status':'FAILED','errors':[]}
    try:record=validate()
    except Exception as error:record['errors'].append(str(error));u.log_error('TAIL_REPAIR_VALIDATE_FAILED: '+str(error))
    path=ROOT/'Saved/Validation/TailRepairPersisted.json';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    if record['errors']:raise RuntimeError('Tail repair fresh validation failed')
    u.log('TAIL_REPAIR_PERSISTED_OK')
    if preview_images:preview(record)
    return record


if __name__=='__main__':main('--preview' in sys.argv)
