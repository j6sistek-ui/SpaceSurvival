"""Fresh persisted checks and optional unsaved native rock transform previews.

--preview captures current rock material, candidate, a 90 degree co-rotation and
large translated scene. All assignments belong to transient actor components.
"""
import hashlib,importlib.util,json,math,sys,time,traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ss_rock_author',ROOT/'Scripts/AuthorRockPhotographic.py');author=importlib.util.module_from_spec(spec);spec.loader.exec_module(author)
OUT=ROOT/'ContentSource/RockPhotographicPreview'


def validate(verify_adoption=False):
    manifest=author.source_manifest();library=u.EditorAssetLibrary;edit=u.MaterialEditingLibrary
    material=library.load_asset(author.MATERIAL);assert isinstance(material,u.Material)
    key=hashlib.sha256(''.join(r['sha256'] for r in manifest['maps']).encode()).hexdigest()
    assert library.get_metadata_tag(material,'SSRockVersion')==author.VERSION and library.get_metadata_tag(material,'SSRockSourceKey')==key
    assert library.get_metadata_tag(material,'SSRockMapping')=='SignedObjectLocalTriplanarNoUVs'
    assert not material.get_editor_property('tangent_space_normal') and material.get_editor_property('blend_mode')==u.BlendMode.BLEND_OPAQUE
    textures=[]
    for row in manifest['maps']:
        kind=row['kind'];path=author.BASE+'/Textures/'+author.NAMES[kind];texture=library.load_asset(path)
        assert isinstance(texture,u.Texture2D) and library.get_metadata_tag(texture,'SSRockSourceSHA256')==row['sha256']
        expected={'diff':u.TextureCompressionSettings.TC_BC7,'arm':u.TextureCompressionSettings.TC_MASKS,'nor_dx':u.TextureCompressionSettings.TC_NORMALMAP}[kind]
        assert texture.get_editor_property('compression_settings')==expected and texture.get_editor_property('srgb')==(kind=='diff')
        assert not texture.get_editor_property('flip_green_channel') and texture.get_editor_property('address_x')==u.TextureAddress.TA_WRAP and texture.get_editor_property('address_y')==u.TextureAddress.TA_WRAP
        assert edit.get_material_default_texture_parameter_value(material,author.NAMES[kind])==texture
        textures.append({'path':path,'source_sha256':row['sha256'],'compression':str(expected),'srgb':kind=='diff','flip_green':False})
    for name,value in [('RepeatLocalCm',240),('NormalStrength',.75),('Desaturation',.5),('RoughnessFloor',.68)]:assert abs(edit.get_material_default_scalar_parameter_value(material,name)-value)<1e-5,name
    expressions=edit.get_material_expressions(material);samples=[e for e in expressions if isinstance(e,u.MaterialExpressionTextureSampleParameter2D)]
    assert len(samples)==9,'Expected three projections for each of three maps'
    for prop in [u.MaterialProperty.MP_BASE_COLOR,u.MaterialProperty.MP_ROUGHNESS,u.MaterialProperty.MP_NORMAL,u.MaterialProperty.MP_AMBIENT_OCCLUSION,u.MaterialProperty.MP_METALLIC]:assert edit.get_material_property_input_node(material,prop)
    metal=edit.get_material_property_input_node(material,u.MaterialProperty.MP_METALLIC);assert isinstance(metal,u.MaterialExpressionConstant) and metal.get_editor_property('r')==0
    custom=[e for e in expressions if isinstance(e,u.MaterialExpressionCustom)];assert len(custom)==6
    assert all('WorldPosition' not in e.get_editor_property('code') and 'Time' not in e.get_editor_property('code') for e in custom)
    editor=u.get_editor_subsystem(u.StaticMeshEditorSubsystem);meshes=[]
    for name in ['SM_Asteroid','SM_AsteroidSmall','SM_AsteroidMedium','SM_AsteroidMassive']:
        mesh=library.load_asset(author.BASE+'/Meshes/'+name);assert isinstance(mesh,u.StaticMesh)
        bound=mesh.get_bounds();meshes.append({'path':mesh.get_path_name(),'sha256':author.digest(ROOT/'Content/SpaceSurvival/Meshes'/(name+'.uasset')),'triangles':mesh.get_num_triangles(0),'extent_cm':[bound.box_extent.x,bound.box_extent.y,bound.box_extent.z],'simple_collision_count':editor.get_simple_collision_count(mesh),'materials':[s.get_editor_property('material_interface').get_path_name() for s in mesh.get_editor_property('static_materials')]})
    if verify_adoption:
        baseline=json.loads((OUT/'AdoptionBaseline.json').read_text())
        for name in author.ROCK_MESHES:
            mesh=library.load_asset(author.BASE+'/Meshes/'+name)
            assert mesh.get_editor_property('static_materials')[0].get_editor_property('material_interface')==material,'Adopted rock material was reset'
            assert library.get_metadata_tag(mesh,'SSRockSurfaceVersion')==author.VERSION
            assert author.mesh_signature(mesh,'fresh')==baseline['geometry'][name],'Fresh built geometry/collision differs from pre-adoption baseline'
    u.AutomationLibrary.finish_loading_before_screenshot();statistics=edit.get_statistics(material)
    stats={name:int(statistics.get_editor_property(name)) for name in ['num_vertex_shader_instructions','num_pixel_shader_instructions','num_samplers','num_vertex_texture_samples','num_pixel_texture_samples','num_uv_scalars','num_interpolator_scalars']}
    return {'status':'PERSISTED_ROCK_CANDIDATE_VALIDATED_NOT_GAMEPLAY','errors':[],'engine':u.SystemLibrary.get_engine_version(),'material':material.get_path_name(),'version':author.VERSION,'source_key':key,'textures':textures,'texture_sample_nodes':len(samples),'statistics':stats,'existing_asteroids':meshes,'adoption_verified':verify_adoption,'content_packages':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':author.digest(p)} for p in sorted((ROOT/'Content').rglob('*.uasset')) if author.owned(p)],'limits':['Local repeat scales with asteroid actor; not constant physical texel density','No geometry, silhouette or collision repair','Statistics are editor shader estimates, not runtime performance','Fresh stock previews remain separate from gameplay acceptance']}


def preview(record):
    OUT.mkdir(parents=True,exist_ok=True);protected={p:author.digest(p) for p in (ROOT/'Content').rglob('*.uasset')}
    u.EditorLoadingAndSavingUtils.new_blank_map(False);actors=u.get_editor_subsystem(u.EditorActorSubsystem);world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    # Disable temporal accumulation so co-transformed captures can be compared.
    for command in ['r.AntiAliasingMethod 0','r.MotionBlurQuality 0','r.ScreenPercentage 100','r.Shadow.Virtual.Enable 0']:
        u.SystemLibrary.execute_console_command(world,command)
    for texture_name in author.NAMES.values():u.load_asset(author.BASE+'/Textures/'+texture_name).set_force_mip_levels_to_be_resident(90)
    mesh=u.load_asset(author.BASE+'/Meshes/SM_AsteroidMedium');rock=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0));component=rock.get_component_by_class(u.StaticMeshComponent);component.set_mobility(u.ComponentMobility.MOVABLE);component.set_static_mesh(mesh);component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);rock.set_actor_scale3d(u.Vector(3,3,3))
    original=[u.load_asset(author.BASE+'/Materials/M_Rock') for s in mesh.get_editor_property('static_materials')]
    lights=[]
    for pitch,yaw,color,intensity in [(-35,-40,(.84,.91,1,1),5),(-20,145,(1,.89,.75,1),2),(-65,75,(.6,.7,1,1),1)]:
        light=actors.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,600));lamp=light.get_component_by_class(u.DirectionalLightComponent);lamp.set_mobility(u.ComponentMobility.MOVABLE);lamp.set_light_color(u.LinearColor(*color));lamp.set_intensity(intensity);lamp.set_editor_property('cast_shadows',False);lights.append((light,pitch,yaw))
    post=actors.spawn_actor_from_class(u.PostProcessVolume,u.Vector(0,0,0));post.set_editor_property('unbound',True);settings=post.get_editor_property('settings')
    for key,value in {'override_auto_exposure_min_brightness':True,'override_auto_exposure_max_brightness':True,'auto_exposure_min_brightness':1.0,'auto_exposure_max_brightness':1.0,'override_bloom_intensity':True,'bloom_intensity':0.0}.items():settings.set_editor_property(key,value)
    post.set_editor_property('settings',settings)
    camera=actors.spawn_actor_from_class(u.CameraActor,u.Vector(0,0,0));camera.get_component_by_class(u.CameraComponent).set_field_of_view(42)
    u.get_editor_subsystem(u.LevelEditorSubsystem).editor_set_game_view(True)
    cases=[{'name':'RockPrevious','candidate':False,'yaw':0,'translation':(0,0,0)},
           {'name':'RockPhotographic','candidate':True,'yaw':0,'translation':(0,0,0)},
           {'name':'RockRotated','candidate':True,'yaw':90,'translation':(0,0,0)},
           {'name':'RockRebased','candidate':True,'yaw':90,'translation':(1000000,-2000000,300000)}]
    state={'index':0,'frames':0,'task':None,'handle':None,'start':time.monotonic(),'samples':[],'errors':[],'busy':False}
    def setup():
        case=cases[state['index']];translation=u.Vector(*case['translation']);angle=math.radians(case['yaw']);c,s=math.cos(angle),math.sin(angle)
        def transformed(v):return u.Vector(v[0]*c-v[1]*s,v[0]*s+v[1]*c,v[2])+translation
        rock.set_actor_location(translation,False,False);rock.set_actor_rotation(u.Rotator(pitch=0,yaw=case['yaw'],roll=0),False)
        for index,material in enumerate(original):component.set_material(index,u.load_asset(author.MATERIAL) if case['candidate'] else material)
        for light,pitch,yaw in lights:light.set_actor_location(translation+u.Vector(0,0,600),False,False);light.set_actor_rotation(u.Rotator(pitch=pitch,yaw=yaw+case['yaw'],roll=0),False)
        location=transformed((1400,-1280,800));rotation=u.MathLibrary.find_look_at_rotation(location,translation)
        camera.set_actor_location(location,False,False);camera.set_actor_rotation(rotation,False);u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(location,rotation)
        state['frames']=0;state['task']=None;state['case_start']=time.monotonic()
    def finish():
        changed=[str(p.relative_to(ROOT)) for p,h in protected.items() if author.digest(p)!=h]
        if changed:state['errors'].append('Preview changed existing packages: '+','.join(changed))
        receipt={'status':'NATIVE_ROCK_ASSET_PREVIEWS_CAPTURED_NOT_GAMEPLAY' if not state['errors'] else 'FAILED','errors':state['errors'],'material':author.MATERIAL,'source_key':record['source_key'],'engine':record['engine'],'samples':state['samples'],'protected_packages_unchanged':len(protected) if not changed else None,'limits':['Unsaved stock actors and studio lighting; only the three candidate textures are forced resident for90seconds by the preview','Rotated view co-rotates lights/camera; directional shadows disabled to isolate mapping from cascade/Lumen world-space changes','Large translation is a mapping stress check, not actual native gameplay origin-rebase execution','Collision/geometry unchanged; runtime cost and hazard readability not accepted']}
        (OUT/'UnrealPreview.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');u.unregister_slate_post_tick_callback(state['handle']);u.EditorPythonScripting.set_keep_python_script_alive(False)
    def tick(delta):
        # Screenshot loading can pump Slate recursively; never schedule twice.
        if state['busy']:return
        state['busy']=True
        try:
            state['frames']+=1;case=cases[state['index']];path=OUT/(case['name']+'.png')
            if state['frames']>=150 and not state['task'] and time.monotonic()-state['case_start']>5:
                u.SystemLibrary.execute_console_command(world,'ListTextures -alphasort');state['samples'].append({**case,'scale':3,'png':str(path.relative_to(ROOT))});u.AutomationLibrary.finish_loading_before_screenshot();state['task']=u.AutomationLibrary.take_high_res_screenshot(1400,1000,str(path),camera,delay=.3);assert state['task'].is_valid_task()
            if state['task'] and state['task'].is_task_done() and path.exists():
                state['index']+=1
                if state['index']==len(cases):finish()
                else:setup()
            elif time.monotonic()-state['start']>180:state['errors'].append('Rock screenshot timeout');finish()
        except Exception as error:state['errors'].append(str(error));u.log_error(str(error));finish()
        finally:state['busy']=False
    setup();u.EditorPythonScripting.set_keep_python_script_alive(True);state['handle']=u.register_slate_post_tick_callback(tick)


def main(preview_images=False,verify_adoption=False):
    record={'status':'FAILED','errors':[]}
    try:record=validate(verify_adoption)
    except Exception as error:record['errors'].append(type(error).__name__+': '+str(error));record['traceback']=traceback.format_exc();u.log_error('ROCK_VALIDATE_FAILED: '+record['traceback'])
    out=ROOT/'Saved/Validation/RockPhotographicPersisted.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    if record['errors']:raise RuntimeError('Rock candidate fresh validation failed')
    u.log('ROCK_PHOTOGRAPHIC_PERSISTED_OK')
    if preview_images:preview(record)
    return record


if __name__=='__main__':main('--preview' in sys.argv,'--adopted' in sys.argv)