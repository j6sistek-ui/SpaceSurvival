"""Central-only daylight balance and foliage correction after native review100.

Vendor materials, exposure, floor and other rooms stay untouched. New materials
retain the source foliage masks/normals. This stages changes; saving is explicit.
"""
import hashlib
import math
from pathlib import Path

PRIVATE = '/Game/OutpostSandbox/StationRefinement/CentralLightGarden101'
PREFIX = 'Refine/CentralLightGarden101/'
PREVIOUS = '/Game/OutpostSandbox/StationRefinement/CentralFeatures99/'
MAP = '/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime'


def run(u, expected_sha, execute=False):
    ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
    sub=u.get_editor_subsystem(u.EditorActorSubsystem)
    lib=u.MaterialEditingLibrary
    tools=u.AssetToolsHelpers.get_asset_tools()
    assert not ed.get_game_world() and ed.get_editor_world().get_path_name().split('.')[0]==MAP
    disk=Path(u.Paths.project_content_dir())/(MAP.removeprefix('/Game/')+'.umap')
    assert hashlib.sha256(disk.read_bytes()).hexdigest()==expected_sha
    assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    assert not u.EditorAssetLibrary.does_directory_exist(PRIVATE)
    actors=list(sub.get_all_level_actors())
    assert len(actors)==8959 and not any(a.get_actor_label().startswith(PREFIX) for a in actors)
    if not execute:
        return {'dry_run':True,'scope':'Central walls, ceiling, planting, lighting and desk trim',
                'preserve':['Floor','Exposure','NPCs','Other rooms','Target image']}
    state={'new':[],'materials':[],'originals':[],'lights':[],'private':[],'meshes':[]}

    def keep(a):
        if not any(t[0]==a for t in state['originals']):
            state['originals'].append((a,a.get_actor_transform(),a.hidden,a.get_actor_enable_collision()))
        a.modify()

    def surface(a,m,slots=None):
        c=a.static_mesh_component;c.modify()
        state['materials'].append((c,list(c.get_materials())))
        for i in range(c.get_num_materials()) if slots is None else slots:c.set_material(i,m)

    def mi(name,parent):
        m=tools.duplicate_asset(name,PRIVATE,parent)
        assert m;state['private'].append(m);return m

    def green(source):
        key=source.get_path_name()
        if key in leaves:return leaves[key]
        parent=source.parent
        pkey=parent.get_path_name()
        if pkey not in green_bases:
            base=tools.duplicate_asset('M_Green_'+parent.get_name().removeprefix('M_'),PRIVATE,parent)
            assert base;state['private'].append(base)
            original=lib.get_material_property_input_node(base,u.MaterialProperty.MP_BASE_COLOR)
            output=lib.get_material_property_input_node_output_name(base,u.MaterialProperty.MP_BASE_COLOR)
            tint=lib.create_material_expression(base,u.MaterialExpressionVectorParameter,-250,200)
            tint.set_editor_property('parameter_name','StationGreenTint')
            tint.set_editor_property('default_value',u.LinearColor(.23,.68,.12,1))
            node=lib.create_material_expression(base,u.MaterialExpressionMultiply,-50,100)
            assert lib.connect_material_expressions(original,output,node,'A')
            assert lib.connect_material_expressions(tint,'',node,'B')
            assert lib.connect_material_property(node,'',u.MaterialProperty.MP_BASE_COLOR)
            lib.recompile_material(base);green_bases[pkey]=base
        result=mi('MI_Green_'+source.get_name().removeprefix('MI_'),source)
        lib.set_material_instance_parent(result,green_bases[pkey]);lib.update_material_instance(result)
        leaves[key]=result;return result

    def polar(angle,radius,z):
        r=math.radians(angle);return (4200+radius*math.cos(r),radius*math.sin(r),z)

    def named(a,label):
        a.set_actor_label(PREFIX+label)
        a.set_editor_property('tags',[u.Name('OutpostAuthored'),u.Name('OutpostLabel:'+PREFIX+label)])
        state['new'].append(a);return a

    def fit(a,center,size,rotation):
        a.set_actor_rotation(rotation,False)
        ext=a.static_mesh_component.static_mesh.get_bounds().box_extent.to_tuple()
        a.set_actor_scale3d(u.Vector(*(size[i]/(2*ext[i]) for i in range(3))))
        p,_=a.get_actor_bounds(False)
        a.set_actor_location(a.get_actor_location()+u.Vector(*center)-p,False,True)

    def mesh(label,path,center,size,rotation,material):
        a=named(sub.spawn_actor_from_class(u.StaticMeshActor,u.Vector()),label)
        c=a.static_mesh_component;c.set_static_mesh(u.load_asset(path))
        fit(a,center,size,rotation);c.set_collision_profile_name('NoCollision');a.set_actor_enable_collision(False)
        surface(a,material);return a

    def light(label,position,target,power,radius,width,height,color=(1,.84,.65,1)):
        a=named(sub.spawn_actor_from_class(u.RectLight,u.Vector(*position)),label)
        a.set_actor_rotation(u.MathLibrary.find_look_at_rotation(u.Vector(*position),u.Vector(*target)),False)
        c=a.rect_light_component;c.set_mobility(u.ComponentMobility.MOVABLE)
        c.set_intensity_units(u.LightUnits.LUMENS);c.set_intensity(power)
        c.set_light_color(u.LinearColor(*color));c.set_attenuation_radius(radius)
        c.set_source_width(width);c.set_source_height(height);c.set_cast_shadows(False)
        c.set_indirect_lighting_intensity(.3);c.set_volumetric_scattering_intensity(0)
        c.set_specular_scale(.08);return a

    leaves={};green_bases={}
    try:
        dark=mi('MI_SatinGraphite',u.load_asset(PREVIOUS+'MI_Graphite'))
        lib.set_material_instance_vector_parameter_value(dark,'HullTint',u.LinearColor(.12,.135,.15,1))
        lib.update_material_instance(dark)
        bronze=u.load_asset(PREVIOUS+'MI_Champagne')
        warm=u.load_asset(PREVIOUS+'MI_SolidWarm')
        walls={}
        for a in actors:
            label=a.get_actor_label()
            if not isinstance(a,u.StaticMeshActor):continue
            if label=='Atrium/Upper service panel' or label.startswith('Atrium/Bay ') and '/Panel ' in label:
                for i,m in enumerate(a.static_mesh_component.get_materials()):
                    if m and m.get_path_name().startswith(PREVIOUS+'MI_Wall_'):
                        key=m.get_path_name()
                        if key not in walls:
                            new=mi('MI_Wall_'+m.get_name().removeprefix('MI_Wall_'),m)
                            lib.set_material_instance_vector_parameter_value(new,'Albedo Tint',u.LinearColor(.14,.16,.18,1))
                            lib.set_material_instance_scalar_parameter_value(new,'Min Roughness',.72)
                            lib.set_material_instance_scalar_parameter_value(new,'Max Roughness',.9)
                            lib.update_material_instance(new);walls[key]=new
                        surface(a,walls[key],[i])
                # The broad white patches were the source mesh's Light1 surface.
                # Keep lighting in the added narrow practical fixtures instead.
                for i,slot in enumerate(a.static_mesh_component.static_mesh.static_materials):
                    if str(slot.material_slot_name)=='Light1':surface(a,dark,[i])
            elif label.startswith('Refine/CentralFeatures99/Ceiling/') and ' panel ' in label:
                surface(a,dark,[0,1,2,4,5,6])
            elif label.startswith('Refine/CentralFeatures99/Waiting ') and '/Broadleaf ' in label:
                keep(a);c=a.static_mesh_component
                state['meshes'].append((c,c.static_mesh,list(c.get_materials())))
                p,e=a.get_actor_bounds(False);j=int(label.rsplit(' ',1)[-1])
                asset='/Game/Nanite_Plants_Sample_Collection/Geometries/SM_3DGardenPlants_Acer_buergerianum_02_002_Free'
                c.set_static_mesh(u.load_asset(asset))
                # All old component overrides are removed before reading source slots.
                c.set_editor_property('override_materials',[])
                height=175 if j%2 else 205
                fit(a,(p.x,p.y,70+height/2),(170,140,height),a.get_actor_rotation())
                for i,m in enumerate(c.get_materials()):
                    if m and 'Leaves' in m.get_name():surface(a,green(m),[i])
            elif label.startswith('Refine/CentralFeatures99/Waiting ') and '/Low planting ' in label:
                for i,m in enumerate(a.static_mesh_component.get_materials()):
                    if m and any(s in m.get_name() for s in ('Leaves','Flowers')):surface(a,green(m),[i])
        # Avoid a rectangular specular hotspot from every broad area source.
        for a in actors:
            label=a.get_actor_label()
            if label.startswith(('Refine/CentralFeatures99/','Refine/CentralArchitecture97/','Refine/Concept73/Rib ','Refine/CentralCheckIn100/')):
                c=a.get_component_by_class(u.RectLightComponent)
                if c:
                    state['lights'].append((c,c.intensity,c.specular_scale,c.get_light_color()))
                    c.modify();c.set_specular_scale(.08)
                    if '/Plant wash' in label:c.set_intensity(210)
                    elif '/Ceiling/Wash ' in label:c.set_intensity(2100)
                    elif '/Practical light' in label or '/Rib ' in label:
                        c.set_intensity(1500);c.set_light_color(u.LinearColor(1,.83,.64,1))
        # Outward and upward light lifts the dark structure without blowing out floor.
        for i in range(8):
            angle=22.5+i*45
            light('Ceiling bounce %02d'%i,polar(angle,1160,470),polar(angle,1270,647),2600,700,270,100)
            light('Wall wash %02d'%i,polar(angle,1100,360),polar(angle,1560,340),2400,720,200,220)
            # Two framed warm glass diffusers beside each navigation placard.
            for j,offset in enumerate((-118,118)):
                r=math.radians(angle);p=u.Vector(*polar(angle,1438,350))+u.Vector(-math.sin(r)*offset,math.cos(r)*offset,0)
                mesh('Practical %02d/%d Housing'%(i,j),'/Engine/BasicShapes/Cube',p.to_tuple(),(10,10,205),u.Rotator(yaw=angle),bronze)
                p-=u.Vector(math.cos(r)*6,math.sin(r)*6,0)
                mesh('Practical %02d/%d Lens'%(i,j),'/Engine/BasicShapes/Cube',p.to_tuple(),(2,4.5,183),u.Rotator(yaw=angle),warm)
        # Three continuous mechanical bands visually tie the reception panels.
        for label,z,diameter,height,mat in [('Upper rail',97,608,4,bronze),('Mid rail',33,606,3,bronze),('Upper reveal',102,609,1.5,warm)]:
            mesh('Reception/'+label,'/Game/OutpostSandbox/Geometry/SM_OutpostHalo',(4200,0,z),(diameter,diameter,height),u.Rotator(),mat)
        for i,angle in enumerate((45,135,225,315)):
            light('Reception soft key %d'%i,polar(angle,580,320),(4200,0,105),650,650,160,120,(1,.92,.81,1))
        return state,{'actors_added':len(state['new']),'plant_replacements':len(state['meshes']),
                     'lights_tuned':len(state['lights']),'private_assets':[m.get_path_name() for m in state['private']],
                     'saved':False}
    except Exception:
        restore(u,state);raise


def restore(u,state):
    for c,p,s,color in reversed(state['lights']):c.set_intensity(p);c.set_specular_scale(s);c.set_light_color(color)
    for c,mats in reversed(state['materials']):
        for i,m in enumerate(mats):c.set_material(i,m)
    for c,mesh,mats in reversed(state['meshes']):
        c.set_static_mesh(mesh);c.set_editor_property('override_materials',[])
        for i,m in enumerate(mats):c.set_material(i,m)
    for a,t,h,c in reversed(state['originals']):
        a.set_actor_transform(t,False,True);a.set_actor_hidden_in_game(h);a.set_actor_enable_collision(c)
    sub=u.get_editor_subsystem(u.EditorActorSubsystem)
    for a in reversed(state['new']):sub.destroy_actor(a)


def correct_material_response(u, execute=False):
    """Follow-up to capture101: foliage transmission and texture-driven gloss."""
    ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
    assert not ed.get_game_world() and not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    lib=u.MaterialEditingLibrary;tools=u.AssetToolsHelpers.get_asset_tools()
    assert u.EditorAssetLibrary.does_asset_exist(PRIVATE+'/M_Green_Acer_buergerianum_Leaves01')
    assert not u.EditorAssetLibrary.does_asset_exist(PRIVATE+'/M_CentralFabric')
    if not execute:return {'dry_run':True,'changes':['Tint leaf transmission','Remove inherited wall emission','Correct sofa texture and roughness','Balance local fills']}
    # Both leaf faces must use the green result; the imported shader had retained
    # the original yellow diffuse texture directly in Subsurface Color.
    for name in ('M_Green_Acer_buergerianum_Leaves01','M_Green_Abelia_x_grandiflora_Leaves01'):
        m=u.load_asset(PRIVATE+'/'+name);m.modify()
        node=lib.get_material_property_input_node(m,u.MaterialProperty.MP_BASE_COLOR)
        scaled=lib.create_material_expression(m,u.MaterialExpressionMultiply,180,160)
        scaled.set_editor_property('const_b',.35)
        assert lib.connect_material_expressions(node,'',scaled,'A')
        assert lib.connect_material_property(scaled,'',u.MaterialProperty.MP_SUBSURFACE_COLOR)
        lib.recompile_material(m)
    for asset in u.EditorAssetLibrary.list_assets(PRIVATE):
        m=u.load_asset(asset)
        if isinstance(m,u.MaterialInstanceConstant) and m.get_name().startswith('MI_Wall_'):
            m.modify()
            for parameter in ('Intensity EM1','Intensity EM2','Intensity EM3'):
                lib.set_material_instance_scalar_parameter_value(m,parameter,0.)
            lib.update_material_instance(m)
    base=tools.duplicate_asset('M_CentralFabric',PRIVATE,u.load_asset('/Game/OutpostSandbox/StationRefinement/ArchiveConcept77/M_ArchiveUpholsteryTint'))
    assert base
    for prop,value in ((u.MaterialProperty.MP_ROUGHNESS,.82),(u.MaterialProperty.MP_METALLIC,0.)):
        node=lib.create_material_expression(base,u.MaterialExpressionConstant,150,350)
        node.set_editor_property('r',value)
        assert lib.connect_material_property(node,'',prop)
    lib.recompile_material(base)
    fabric={}
    for kind,source in [('Sofa','/Game/Clinic/Materials/MaterialInstances/MI_Entrance_Sofa'),
                        ('Chair','/Game/Clinic/Materials/MaterialInstances/MI_Entrance_ArmChair')]:
        m=tools.duplicate_asset('MI_Central'+kind,PRIVATE,u.load_asset(source));assert m
        lib.set_material_instance_parent(m,base);lib.update_material_instance(m);fabric[kind]=m
    sub=u.get_editor_subsystem(u.EditorActorSubsystem)
    changed=[]
    for a in sub.get_all_level_actors():
        label=a.get_actor_label()
        if isinstance(a,u.StaticMeshActor):
            kind='Sofa' if label.startswith('Refine/CentralFeatures99/Waiting ') and label.endswith('/Sofa') else 'Chair' if label.startswith('Refine/CentralArchitecture97/Waiting ') and '/Chair ' in label else None
            if kind:a.static_mesh_component.modify();a.static_mesh_component.set_material(0,fabric[kind]);changed.append(label)
        if not isinstance(a,u.Light):continue
        c=a.get_component_by_class(u.LightComponent)
        if label.startswith(PREFIX+'Ceiling bounce '):
            c.modify();c.set_intensity(1400);c.set_light_color(u.LinearColor(1,.70,.40,1))
        elif label.startswith(PREFIX+'Wall wash '):
            c.modify();c.set_intensity(1800);c.set_light_color(u.LinearColor(1,.78,.54,1))
        elif label in ('Atrium/Globe key','Atrium/Light pool') or label.startswith('Refine/CentralWelcomeGreeneryLights1/'):
            c.modify();c.set_specular_scale(.05)
            if label=='Atrium/Globe key':c.set_intensity(14000)
    return {'fabric_actors':changed,'leaf_transmission_corrected':True,'saved':False}


def compose_installed_plants(u, execute=False):
    """Use the collection's green Acer, flowering Vitex and soft grass together."""
    ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
    sub=u.get_editor_subsystem(u.EditorActorSubsystem)
    assert not ed.get_game_world() and not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    actors=list(sub.get_all_level_actors())
    assert not any(a.get_actor_label().startswith(PREFIX+'Grass ') for a in actors)
    sources='/Game/Nanite_Plants_Sample_Collection/Geometries/'
    trees=[u.load_asset(sources+n) for n in ('SM_3DGardenPlants_Acer_buergerianum_01_003_Free','SM_3DGardenPlants_Free_Sample')]
    grass=u.load_asset(sources+'SM_Free_Ophiopogon_japonicus_3DGardenPlants')
    assert all(isinstance(m,u.StaticMesh) for m in trees+[grass])
    if not execute:return {'dry_run':True,'plants':[m.get_path_name() for m in trees+[grass]],'new_grass_clumps':20}
    lib=u.MaterialEditingLibrary
    dark=u.load_asset(PRIVATE+'/MI_SatinGraphite')
    bronze=u.load_asset(PREVIOUS+'MI_Champagne')
    warm=u.load_asset(PREVIOUS+'MI_SolidWarm');warm.modify()
    lib.set_material_instance_vector_parameter_value(warm,'HullTint',u.LinearColor(80,28,6,1))
    lib.update_material_instance(warm)
    replaced=[];wall_slots=[];frames=[]
    for a in actors:
        if not isinstance(a,u.StaticMeshActor):continue
        label=a.get_actor_label();c=a.static_mesh_component
        if label.startswith('Refine/CentralFeatures99/Waiting ') and '/Broadleaf ' in label:
            a.modify();c.modify();p,e=a.get_actor_bounds(False);j=int(label.rsplit(' ',1)[-1])
            plant=trees[0 if j in (1,5) else 1]
            c.set_static_mesh(plant);c.set_editor_property('override_materials',[])
            height=200 if j in (1,5) else 150+(j%2)*20
            size=(180,155,height);ext=plant.get_bounds().box_extent.to_tuple()
            a.set_actor_scale3d(u.Vector(*(size[k]/(2*ext[k]) for k in range(3))))
            q,_=a.get_actor_bounds(False)
            a.set_actor_location(a.get_actor_location()+u.Vector(p.x,p.y,70+height/2)-q,False,True)
            replaced.append(label)
        elif label.startswith('Refine/CentralFeatures99/Waiting ') and '/Low planting ' in label:
            # Native Abelia shades naturally once the harsh plant wash is reduced.
            c.modify();c.set_editor_property('override_materials',[])
        elif label=='Atrium/Upper service panel' or label.startswith('Atrium/Bay ') and '/Panel ' in label:
            c.modify();c.set_material(4,dark);wall_slots.append(label)
        elif label.startswith('Refine/Reception/Direction ') and label.endswith('/Frame'):
            c.modify()
            for i in range(c.get_num_materials()):c.set_material(i,bronze if i in (1,2) else dark)
            frames.append(label)
        elif label.startswith('Refine/CentralArchitecture97/Bay '):
            if '/Pilaster ' in label or label.endswith('/Header service rail'):
                c.modify()
                for i in range(c.get_num_materials()):c.set_material(i,bronze if i==2 else dark)
    for i,angle in enumerate((45,135,225,315)):
        for j in range(5):
            a=sub.spawn_actor_from_class(u.StaticMeshActor,u.Vector())
            label=PREFIX+'Grass %d/%d'%(i,j);a.set_actor_label(label)
            a.set_editor_property('tags',[u.Name('OutpostAuthored'),u.Name('OutpostLabel:'+label)])
            c=a.static_mesh_component;c.set_static_mesh(grass)
            c.set_collision_profile_name('NoCollision');a.set_actor_enable_collision(False)
            ext=grass.get_bounds().box_extent.to_tuple()
            a.set_actor_scale3d(u.Vector(*(s/(2*e) for s,e in zip((80,72,42),ext))))
            turn=angle-9+j*4.5;a.set_actor_rotation(u.Rotator(yaw=turn+j*77),False)
            r=math.radians(turn);p,_=a.get_actor_bounds(False)
            a.set_actor_location(u.Vector(4200+1268*math.cos(r),1268*math.sin(r),90)-p,False,True)
    return {'replaced':len(replaced),'new_grass_clumps':20,'wall_base5':len(wall_slots),'frames':len(frames),'saved':False}


def balance_final(u, execute=False):
    """Correct observed furniture emission; give planting depth with local shadow."""
    assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    lib=u.MaterialEditingLibrary
    base=u.load_asset(PRIVATE+'/M_CentralFabric')
    assert lib.get_material_property_input_node(base,u.MaterialProperty.MP_EMISSIVE_COLOR).get_class()==u.MaterialExpressionMultiply.static_class()
    if not execute:return {'dry_run':True,'fixes':['Disable inherited sofa emission','Reduce overlapping floor light','Shadow the four planting washes']}
    base.modify()
    zero=lib.create_material_expression(base,u.MaterialExpressionConstant,260,350)
    zero.set_editor_property('r',0.)
    lib.connect_material_property(zero,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
    lib.recompile_material(base)
    plants={}
    for i in range(1,6):
        name='MI_Green_Abelia_x_grandiflora_Leaves%02d'%i
        m=u.load_asset(PRIVATE+'/'+name);m.modify()
        lib.set_material_instance_vector_parameter_value(m,'StationGreenTint',u.LinearColor(.4,.8,.32,1))
        lib.update_material_instance(m);plants['MI_Abelia_x_grandiflora_Leaves%02d'%i]=m
    lights=[]
    for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        label=a.get_actor_label()
        if isinstance(a,u.StaticMeshActor) and label.startswith('Refine/CentralFeatures99/Waiting ') and '/Low planting ' in label:
            c=a.static_mesh_component;c.modify()
            for i,m in enumerate(c.get_materials()):
                if m and m.get_name() in plants:c.set_material(i,plants[m.get_name()])
        if not isinstance(a,u.Light):continue
        c=a.get_component_by_class(u.LightComponent)
        if label=='Atrium/Light pool':c.modify();c.set_intensity(600);lights.append(label)
        elif label=='Atrium/Globe key':c.modify();c.set_intensity(9000);lights.append(label)
        elif label.startswith('Refine/CentralWelcomeGreeneryLights1/'):
            c.modify();c.set_intensity(500);lights.append(label)
        elif label.startswith('Refine/CentralFeatures99/Waiting ') and label.endswith('/Plant wash'):
            c.modify();c.set_intensity(100);c.set_cast_shadows(True);lights.append(label)
    return {'lights':len(lights),'furniture_emission_removed':True,'saved':False}


def tone_fabric(u, execute=False):
    """Neutral upholstery albedo; keep the owned normal/AO detail and geometry."""
    assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    lib=u.MaterialEditingLibrary;m=u.load_asset(PRIVATE+'/M_CentralFabric')
    old=lib.get_material_property_input_node(m,u.MaterialProperty.MP_BASE_COLOR)
    assert isinstance(old,u.MaterialExpressionMultiply)
    if not execute:return {'dry_run':True,'scope':'Six new Central seats only; preserve fabric normal and AO'}
    m.modify()
    color=lib.create_material_expression(m,u.MaterialExpressionVectorParameter,200,-180)
    color.set_editor_property('parameter_name','CentralFabricColor')
    color.set_editor_property('default_value',u.LinearColor(.035,.045,.055,1))
    assert lib.connect_material_property(color,'',u.MaterialProperty.MP_BASE_COLOR)
    spec=lib.create_material_expression(m,u.MaterialExpressionConstant,220,120)
    spec.set_editor_property('r',.15)
    assert lib.connect_material_property(spec,'',u.MaterialProperty.MP_SPECULAR)
    lib.recompile_material(m)
    return {'neutral_albedo':True,'source_normal_ao_retained':True,'saved':False}


def finish_ceiling(u, execute=False):
    """Continue the existing recessed warm seam along the engineered radial ribs."""
    assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    sub=u.get_editor_subsystem(u.EditorActorSubsystem)
    assert not any(a.get_actor_label().startswith(PREFIX+'Ceiling seam ') for a in sub.get_all_level_actors())
    if not execute:return {'dry_run':True,'new_actors':17,'new_assets':0,'scope':'Ceiling above 6 metres only'}
    mat=u.load_asset(PREVIOUS+'MI_SolidWarm')
    def place(label,path,center,size,rotation):
        a=sub.spawn_actor_from_class(u.StaticMeshActor,u.Vector())
        a.set_actor_label(PREFIX+'Ceiling seam '+label)
        a.set_editor_property('tags',[u.Name('OutpostAuthored')])
        c=a.static_mesh_component;c.set_static_mesh(u.load_asset(path));c.set_material(0,mat)
        c.set_collision_profile_name('NoCollision');a.set_actor_enable_collision(False)
        a.set_actor_rotation(rotation,False);ext=c.static_mesh.get_bounds().box_extent.to_tuple()
        a.set_actor_scale3d(u.Vector(*(s/(2*e) for s,e in zip(size,ext))))
        p,_=a.get_actor_bounds(False);a.set_actor_location(u.Vector(*center)-p,False,True)
        return a
    for i in range(16):
        angle=11.25+i*22.5;r=math.radians(angle)
        place('Radial %02d'%i,'/Engine/BasicShapes/Cube',(4200+1130*math.cos(r),1130*math.sin(r),616),
              (320,5,3),u.Rotator(yaw=angle))
    place('Inner ring',PREVIOUS+'SM_CentralWarmRing',(4200,0,614),(1810,1810,3),u.Rotator())
    return {'new_actors':17,'saved':False}
