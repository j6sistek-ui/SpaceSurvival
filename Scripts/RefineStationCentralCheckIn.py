"""Owner-directed front check-in podium and removal of flat cyan ring art."""
from pathlib import Path
import hashlib
import json

PREFIX='Refine/CentralCheckIn100/'
PRIVATE='/Game/OutpostSandbox/StationRefinement/CentralCheckIn100'

def run(u, screen_folder, execute=False, resume_partial=False):
    ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
    assert not ed.get_game_world()
    assert ed.get_editor_world().get_path_name().split('.')[0]=='/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime'
    sub=u.get_editor_subsystem(u.EditorActorSubsystem);actors=list(sub.get_all_level_actors())
    assert not any(a.get_actor_label().startswith(PREFIX) for a in actors)
    names=['Atrium/Navigation ring','Atrium/Oculus light','Atrium/Projection emitter','Atrium/Orbital halo','Refine/Reception/Light reveal']
    selected=[a for a in actors if a.get_actor_label() in names]
    assert len(selected)==len(names)
    folder=Path(screen_folder);manifest=json.loads((folder/'manifest.json').read_text('utf-8'))
    assert hashlib.sha256((folder/'CheckIn.png').read_bytes()).hexdigest()==manifest['sha256']['CheckIn.png']
    if resume_partial:
        assert set(map(str,u.EditorAssetLibrary.list_assets(PRIVATE,False,False)))=={PRIVATE+'/T_CheckIn.T_CheckIn',PRIVATE+'/M_CheckIn.M_CheckIn'}
        assert u.MaterialEditingLibrary.get_num_material_expressions(u.load_asset(PRIVATE+'/M_CheckIn'))==5
    else:
        assert not u.EditorAssetLibrary.does_directory_exist(PRIVATE)
    if not execute:return {'dry_run':True,'hide':names,'podium':'Owned complete Sci_fi_Console_Game','position':[3695,-160,0],'screen':'Factual reception information'}
    state={'new':[],'originals':[],'assets':[]}
    def named(a,name):
        a.set_actor_label(PREFIX+name);a.set_editor_property('tags',[u.Name('OutpostAuthored'),u.Name('OutpostLabel:'+PREFIX+name)])
        state['new'].append(a);return a
    try:
        for a in selected:
            state['originals'].append((a,a.hidden,a.get_actor_enable_collision()))
            a.modify();a.set_actor_hidden_in_game(True);a.set_actor_enable_collision(False)
        if not resume_partial:
            task=u.AssetImportTask()
            for k,v in dict(filename=str(folder/'CheckIn.png'),destination_path=PRIVATE,destination_name='T_CheckIn',
                            automated=True,replace_existing=False,save=False).items():task.set_editor_property(k,v)
            u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        texture=u.load_asset(PRIVATE+'/T_CheckIn');assert isinstance(texture,u.Texture2D)
        state['assets'].append(texture)
        texture.set_editor_property('srgb',True)
        texture.set_editor_property('address_x',u.TextureAddress.TA_CLAMP);texture.set_editor_property('address_y',u.TextureAddress.TA_CLAMP)
        material=u.load_asset(PRIVATE+'/M_CheckIn') if resume_partial else u.AssetToolsHelpers.get_asset_tools().create_asset('M_CheckIn',PRIVATE,u.Material,u.MaterialFactoryNew())
        state['assets'].append(material);material.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
        lib=u.MaterialEditingLibrary
        if resume_partial:lib.delete_all_material_expressions(material)
        sample=lib.create_material_expression(material,u.MaterialExpressionTextureSample);sample.texture=texture
        uv=lib.create_material_expression(material,u.MaterialExpressionTextureCoordinate);uv.v_tiling=-1.
        offset=lib.create_material_expression(material,u.MaterialExpressionConstant2Vector);offset.r=0.;offset.g=1.
        add=lib.create_material_expression(material,u.MaterialExpressionAdd)
        gain=lib.create_material_expression(material,u.MaterialExpressionMultiply);gain.set_editor_property('const_b',8.)
        assert lib.connect_material_expressions(uv,'',add,'A')
        assert lib.connect_material_expressions(offset,'',add,'B')
        assert lib.connect_material_expressions(add,'',sample,'UVs')
        assert lib.connect_material_expressions(sample,'RGB',gain,'A')
        assert lib.connect_material_property(gain,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
        lib.recompile_material(material)
        m=u.load_asset('/Game/Fab/Sci_fi_Console_Game/SM_Sci_fi_Console_Game')
        assert u.get_editor_subsystem(u.StaticMeshEditorSubsystem).get_simple_collision_count(m)>0
        a=named(sub.spawn_actor_from_class(u.StaticMeshActor,u.Vector()),'Podium')
        a.static_mesh_component.set_static_mesh(m)
        a.set_actor_rotation(u.Rotator(yaw=90),False)
        factor=142./(2*m.get_bounds().box_extent.z);a.set_actor_scale3d(u.Vector(factor,factor,factor))
        p,e=a.get_actor_bounds(False);a.set_actor_location(u.Vector(3695,-160,71)-p,False,True)
        a.static_mesh_component.set_material(1,material)
        a.static_mesh_component.set_collision_profile_name('BlockAll');a.set_actor_enable_collision(True)
        lamp=named(sub.spawn_actor_from_class(u.RectLight,u.Vector(3500,-290,300)),'Podium light')
        lamp.set_actor_rotation(u.MathLibrary.find_look_at_rotation(lamp.get_actor_location(),u.Vector(3695,-160,90)),False)
        c=lamp.rect_light_component;c.set_mobility(u.ComponentMobility.MOVABLE)
        c.set_intensity_units(u.LightUnits.LUMENS);c.set_intensity(1800.);c.set_attenuation_radius(470.)
        c.set_light_color(u.LinearColor(1,.79,.57,1));c.set_source_width(110);c.set_source_height(90)
        c.set_cast_shadows(False);c.set_indirect_lighting_intensity(.2);c.set_volumetric_scattering_intensity(0)
        return state,{'hidden_rings':names,'podium_bounds':[v.to_tuple() for v in a.get_actor_bounds(False)],'new_actors':len(state['new']),'saved':False}
    except Exception:
        for a,h,c in state['originals']:a.set_actor_hidden_in_game(h);a.set_actor_enable_collision(c)
        for a in reversed(state['new']):sub.destroy_actor(a)
        raise
