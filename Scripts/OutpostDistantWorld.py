"""A distant owned-texture world gives the observation gallery a visual destination.

Private material and one decorative actor only. No atmosphere, sky Blueprint,
light, collision or flight objective is introduced. The sphere lies inside the
existing90,000cm star dome and outside every station/asteroid walking surface.
"""
import json

TARGET='/Game/OutpostSandbox/L_AsteroidOutpost'
LABEL='Environment/Distant blue world'
CENTER=(-65000,28000,16000)
DIAMETER=32000


def apply(api):
    u,edit,lib=api['u'],api['EDIT'],api['LIB']
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name().split('.')[0]!=TARGET:
        raise RuntimeError('Distant world is restricted to the saved outpost')
    name='M_OutpostDistantWorld'
    path='/Game/OutpostSandbox/Materials/'+name
    material=api['load'](path) if lib.does_asset_exist(path) else api['TOOLS'].create_asset(
        name,'/Game/OutpostSandbox/Materials',u.Material,u.MaterialFactoryNew())
    edit.delete_all_material_expressions(material)
    material.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
    def node(kind,**props):
        n=edit.create_material_expression(material,getattr(u,'MaterialExpression'+kind))
        for key,value in props.items():n.set_editor_property(key,value)
        return n
    def link(a,b,pin,output=''):
        assert edit.connect_material_expressions(a,output,b,pin)
    texture=node('TextureSample',texture=api['load']('/Game/Planet_Project/Assets/Textures/Moon/T_8k_moon'))
    tint=node('Constant3Vector',constant=u.LinearColor(.18,.48,.88,1))
    color=node('Multiply');link(texture,color,'A','RGB');link(tint,color,'B')
    normal=node('VertexNormalWS')
    key=node('Constant3Vector',constant=u.LinearColor(.60,-.25,.76,1))
    dot=node('DotProduct');link(normal,dot,'A');link(key,dot,'B')
    day=node('Clamp',min_default=0.,max_default=1.);link(dot,day,'')
    amp=node('Multiply',const_b=7.);link(day,amp,'A')
    shade=node('Add',const_b=.12);link(amp,shade,'A')
    shaded=node('Multiply');link(color,shaded,'A');link(shade,shaded,'B')
    rim=node('Fresnel',exponent=7.,base_reflect_fraction=0.)
    blue=node('Constant3Vector',constant=u.LinearColor(.025,.24,.65,1))
    rim_color=node('Multiply');link(rim,rim_color,'A');link(blue,rim_color,'B')
    emission=node('Add');link(shaded,emission,'A');link(rim_color,emission,'B')
    assert edit.connect_material_property(emission,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
    edit.recompile_material(material)
    assert lib.save_loaded_asset(material)
    matching=[a for a in api['EAS'].get_all_level_actors() if a.get_actor_label()==LABEL]
    if len(matching)>1:raise RuntimeError('Duplicate distant worlds')
    from OutpostGeometryUtils import mesh_union
    mesh=api['load']('/Game/Planet_Project/Assets/Static_Meshes/SM_Earth_Planet')
    if matching:
        actor=matching[0]
        if 'OutpostDistantWorld' not in map(str,actor.tags) or actor.static_mesh_component.static_mesh!=mesh:
            raise RuntimeError('Distant world label occupied by unowned geometry')
        c,e=mesh_union(actor)
        if max(abs(v-DIAMETER/2) for v in (e.x,e.y,e.z))>1:raise RuntimeError('Distant world scale changed')
        actor.set_actor_location(actor.get_actor_location()+u.Vector(*CENTER)-c,False,False)
        actor.static_mesh_component.set_material(0,material)
    else:
        actor=api['place'](LABEL,mesh.get_path_name(),CENTER,size=[DIAMETER]*3,material=material)
        api['tag'](actor,'OutpostDistantWorld')
    c=actor.static_mesh_component
    c.set_cast_shadow(False)
    c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    c.set_editor_property('affect_distance_field_lighting',False)
    c.set_editor_property('visible_in_ray_tracing',False)
    report={'actor':LABEL,'center_cm':CENTER,'diameter_cm':DIAMETER,
            'source_texture':'/Game/Planet_Project/Assets/Textures/Moon/T_8k_moon',
            'private_material':path,'source_assets_modified':False,'lights_added':0,
            'collision':False,'global_atmosphere_changed':False}
    (api['OUT']/'distant-world.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report
