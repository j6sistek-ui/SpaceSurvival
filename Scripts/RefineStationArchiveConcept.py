"""Concept-led native R-room furniture and archive composition.

Run only on the inspected live map with a retained map backup. Original kit,
crew and animation assets remain unchanged. The lead saves after staging and
reviews ordinary PIE views, contact and circulation before acceptance.
"""
import hashlib
import math
from pathlib import Path

MAP = '/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime'
PREFIX = 'Refine/ArchiveConcept77/'
PRIVATE = '/Game/OutpostSandbox/StationRefinement/ArchiveConcept77'
CREW = '/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew/'


def apply(u, expected_sha256, derivatives):
    editor=u.get_editor_subsystem(u.UnrealEditorSubsystem)
    world=editor.get_editor_world()
    assert not editor.get_game_world() and world.get_path_name().split('.')[0]==MAP
    source=Path(u.Paths.project_content_dir())/(MAP.removeprefix('/Game/')+'.umap')
    assert hashlib.sha256(source.read_bytes()).hexdigest()==expected_sha256
    assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    assert not u.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    sub=u.get_editor_subsystem(u.EditorActorSubsystem)
    actors=list(sub.get_all_level_actors())
    assert not any(a.get_actor_label().startswith(PREFIX) for a in actors)
    state={'actors':[],'new':[],'materials':[],'private':[],'texts':[],'lights':[]}
    edit=u.MaterialEditingLibrary

    def one(label):
        rows=[a for a in actors if a.get_actor_label()==label]
        assert len(rows)==1,label
        return rows[0]

    def keep(a):
        if not any(r[0]==a for r in state['actors']):
            state['actors'].append((a,a.get_actor_transform(),a.hidden,a.get_actor_enable_collision()))
        a.modify()
        return a

    def hide(a):
        keep(a).set_actor_hidden_in_game(True)
        a.set_actor_enable_collision(False)

    def named(a,label):
        a.set_actor_label(PREFIX+label)
        a.set_editor_property('tags',[u.Name('OutpostAuthored'),u.Name('OutpostLabel:'+PREFIX+label)])
        state['new'].append(a)
        return a

    def material(name,parent,scalars=None,vectors=None):
        assert not u.EditorAssetLibrary.does_asset_exist(PRIVATE+'/'+name)
        m=u.AssetToolsHelpers.get_asset_tools().create_asset(name,PRIVATE,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
        assert m
        edit.set_material_instance_parent(m,u.load_asset(parent))
        for k,v in (scalars or {}).items():
            assert k in map(str,edit.get_scalar_parameter_names(m)),k
            edit.set_material_instance_scalar_parameter_value(m,k,v)
        for k,v in (vectors or {}).items():
            assert k in map(str,edit.get_vector_parameter_names(m)),k
            edit.set_material_instance_vector_parameter_value(m,k,u.LinearColor(*v))
        edit.update_material_instance(m)
        state['private'].append(m)
        return m

    def prop(label,path,center,height,yaw=0.,width=None):
        a=named(sub.spawn_actor_from_class(u.StaticMeshActor,u.Vector()),label)
        c=a.static_mesh_component
        mesh=u.load_asset(path)
        assert isinstance(mesh,u.StaticMesh),path
        c.set_static_mesh(mesh)
        c.set_collision_profile_name('NoCollision')
        b=mesh.get_bounds()
        z=height/(2.*b.box_extent.z)
        xy=z if width is None else width/(2.*max(b.box_extent.x,b.box_extent.y))
        a.set_actor_scale3d(u.Vector(xy,xy,z))
        a.set_actor_rotation(u.Rotator(yaw=yaw),False)
        p,e=a.get_actor_bounds(False)
        a.set_actor_location(u.Vector(center[0]-p.x,center[1]-p.y,center[2]-p.z+e.z),False,True)
        return a

    def title(label,copy,p,yaw,size):
        a=named(sub.duplicate_actor(one('Refine/Archive/Identity'),world),label)
        a.set_actor_location(u.Vector(*p),False,True)
        a.set_actor_rotation(u.Rotator(yaw=yaw),False)
        a.set_actor_scale3d(u.Vector(1,1,1))
        a.text_render.set_text(copy)
        a.text_render.set_world_size(size)
        a.text_render.set_text_render_color(u.Color(209,224,245,255))
        return a

    chair_mat=material('MI_ArchiveUpholstery','/Game/Clinic/Materials/MaterialInstances/MI_Entrance_ArmChair',
        {'Roughness':.74,'Roughness Intensity':1.}, {'Base Color':(.20,.26,.32,1.)})
    tabletop=material('MI_ArchiveTable','/Game/CyberpunkRestaurant/Materials/MI_Plastic_Glossy_01',
        {'Roughness':.68,'Roughness Intensity':1.,'Metallic':.1},
        {'Base Color':(.09,.13,.16,1.),'Tint':(.3,.35,.4,1.)})
    holo=[]
    for i,color in enumerate(((.06,.35,1.,1.),(.35,.12,1.,1.),(.05,.6,1.,1.)),1):
        holo.append(material('MI_ArchiveProjection'+str(i),'/Game/OutpostSandbox/Materials/M_OutpostArchiveHologram',
            {'BodyEmission':.8,'ScanEmission':1.8,'RimEmission':2.,'BodyOpacity':.2}, {'HologramAmber':color}))
    # Reuse the complete upright kit bays. Quarter-turn their entire assemblies
    # onto the far wall so they are visible as a group from the entrance.
    bay_rows=[]
    for i,(x,old_y,name) in enumerate(((3530.,2800.,'Seer'),(4110.,3360.,'Robe'),(4690.,3960.,'Glyph')),1):
        origin=u.Vector(5350.,old_y,0.)
        dest=u.Vector(x,4330.,0.)
        group=[a for a in actors if a.get_actor_label().startswith('LoungeNative/Hologram bay '+str(i)+'/')]
        assert len(group)>=12
        for a in group:
            keep(a)
            delta=a.get_actor_location()-origin
            a.set_actor_location(dest+u.Vector(-delta.y*1.3,delta.x*1.3,delta.z*1.1),False,True)
            rot=a.get_actor_rotation();rot.yaw+=90.;a.set_actor_rotation(rot,False)
            scale=a.get_actor_scale3d();a.set_actor_scale3d(u.Vector(scale.x*1.3,scale.y*1.3,scale.z*1.1))
            if isinstance(a,u.StaticMeshActor):
                c=a.static_mesh_component
                state['materials'].append((c,list(c.get_materials())))
                for slot in range(c.get_num_materials()):
                    mat=c.get_material(slot)
                    if mat and ('Metal' in mat.get_name() or 'Balanced' in mat.get_name()) and not 'glass' in a.get_actor_label().lower():
                        c.set_material(slot,u.load_asset('/Game/OutpostSandbox/StationRefinement/Concept73/MI_ReceptionMetal'))
        old=one('Lounge/Archive projection '+str(i));hide(old)
        a=named(sub.duplicate_actor(one('Crew/Trader A'),world),'Projection '+str(i))
        a.set_actor_location(u.Vector(x,4330.,120.),False,True)
        a.set_actor_rotation(u.Rotator(yaw=-90.),False)
        a.set_actor_enable_collision(False)
        a.set_editor_property('tags',[u.Name('OutpostAuthored'),u.Name('OutpostRole:Hologram')])
        a.set_editor_property('enable_head_fill',False)
        a.set_editor_property('route_points',[]);a.set_editor_property('gesture_animations',[])
        mesh=u.load_asset(CREW+name+'/Mesh/SK_'+name)
        clip=u.load_asset(CREW+name+'/A_'+name+'_Idle')
        assert mesh.skeleton==clip.get_editor_property('skeleton')
        c=a.character_mesh;c.set_skeletal_mesh_asset(mesh)
        c.set_editor_property('override_materials',[])
        c.set_relative_location(u.Vector(0,0,-90.),False,True)
        c.set_relative_scale3d(u.Vector(1.45,1.45,1.45))
        c.set_editor_property('animation_data',u.SingleAnimationPlayData(anim_to_play=clip,saved_looping=True,saved_playing=True))
        for slot in range(c.get_num_materials()):c.set_material(slot,holo[i-1])
        a.set_editor_property('idle_animation',clip);a.refresh_readability_lighting()
        label=one('Refine/WorkroomComposition/Archive case '+str(i).zfill(2));hide(label)
        title('Bay '+str(i)+'/Header',('EXPLORERS','TRADERS','CREW')[i-1],(x,4174.,359.),-90.,21.)
        bay_rows.append({'index':i,'parts':len(group),'character':name,'position':list(a.get_actor_location().to_tuple())})
    # Keep the actual wardrobe console, projector and use point intact.
    # The old mechanical seats no longer define the waiting-room experience.
    for a in actors:
        label=a.get_actor_label()
        if label.startswith('LoungeNative/Conversation ') and any(v in label for v in ('/North/','/South/','/Low game table')):
            hide(a)
        if label.startswith('Refine/StationFinish20261009/Archive/') and any(v in label for v in ('Tablet ','Catalog ','Wardrobe instructions')):
            hide(a)
        if label in ('Lounge/Archive column','Lounge/Archive light'):
            hide(a)
    seating=[]
    for group,(x,y) in enumerate(((3500.,3000.),(3500.,3680.),(4490.,2880.)),1):
        table=prop('Group '+str(group)+'/Table','/Game/CyberpunkRestaurant/Meshes/SM_Table_02',(x,y,0.),72.,width=118.)
        for slot in (0,1,3):table.static_mesh_component.set_material(slot,tabletop)
        for side,dy,yaw in (('South',-126.,90.),('North',126.,-90.)):
            chair=prop('Group '+str(group)+'/'+side+'/Armchair','/Game/Clinic/Meshes/Props/SM_Entrance_ArmChair01',
                (x,y+dy,0.),83.,yaw-90.)
            chair.static_mesh_component.set_material(0,chair_mat)
            seating.append((group,side,x,y+dy,yaw))
        prop('Group '+str(group)+'/Tablet','/Game/Cyberpunk_Room/Mesh/SM_Tablet',(x-18.,y,72.),2.7,20.,28.)
        prop('Group '+str(group)+'/Reading','/Game/Cyberpunk_Room/Mesh/SM_Books_02',(x+21.,y+12.,72.),8.,-12.,22.)
        prop('Group '+str(group)+'/Water','/Game/Cyberpunk_Room/Mesh/SM_Bottle_01',(x+15.,y-24.,72.),17.,0.,7.)
    # Four compatible seated characters share two tables; the third group has
    # spare capacity and clear access for later owner-authored behavior.
    occupants=[]
    for placement,name,template in zip(seating[:4],('Seer','Robe','Glyph','Tendril'),('Crew/Atrium A','Crew/Trader A','Crew/Trader B','Crew/Atrium B')):
        group,side,x,y,yaw=placement
        row=next(d for d in derivatives['derivatives'] if d['name']==name)
        actor=named(sub.duplicate_actor(one(template),world),'Group '+str(group)+'/'+side+'/Visitor')
        actor.set_actor_location(u.Vector(x,y,85.),False,True)
        actor.set_actor_rotation(u.Rotator(yaw=yaw),False)
        actor.set_editor_property('route_points',[]);actor.set_editor_property('gesture_animations',[])
        actor.set_editor_property('phase_offset',group*1.7+(0. if side=='South' else 2.1))
        clip=u.load_asset(row['clip'])
        actor.set_editor_property('idle_animation',clip)
        c=actor.character_mesh
        offset=min(row['bones_cm']['ball_l'][2],row['bones_cm']['ball_r'][2])-5.5
        c.set_relative_location(u.Vector(0,0,-85.-offset),False,True)
        c.set_editor_property('animation_data',u.SingleAnimationPlayData(anim_to_play=clip,saved_looping=True,saved_playing=True))
        actor.refresh_readability_lighting()
        occupants.append({'character':name,'group':group,'side':side})
    # Screened covered visitor replaces the exposed-body model in a common area.
    old=one('Refine/Archive/Conversation guest B');hide(old)
    visitor=named(sub.duplicate_actor(one('Crew/Atrium patrol'),world),'Consultation visitor')
    visitor.set_actor_location(u.Vector(3880.,3345.,85.),False,True)
    visitor.set_actor_rotation(u.Rotator(yaw=90.),False)
    visitor.set_editor_property('route_points',[])
    visitor.set_editor_property('gesture_animations',[])
    clip=u.load_asset(CREW+'Olive/A_Olive_Listen')
    visitor.set_editor_property('idle_animation',clip)
    visitor.character_mesh.set_editor_property('animation_data',u.SingleAnimationPlayData(anim_to_play=clip,saved_looping=True,saved_playing=True))
    visitor.refresh_readability_lighting()
    identity=one('Refine/Archive/Identity');keep(identity)
    identity.set_actor_location(u.Vector(4110.,4460.,404.),False,True)
    state['texts'].append((identity.text_render,identity.text_render.text,identity.text_render.world_size,identity.text_render.text_render_color))
    identity.text_render.set_world_size(27.)
    hide(one('Refine/ServiceFinish/Refine/Archive/Identity/Plaque'))
    title('Wardrobe instructions','CHANGE YOUR CHARACTER<br>Use the Crew Wardrobe console',(5436.,3580.,283.),180.,16.)
    for label in ('UsableLighting/Lounge/Ceiling 1','UsableLighting/Lounge/Ceiling 2'):
        a=one(label);c=a.get_component_by_class(u.LightComponent)
        state['lights'].append((c,c.intensity,c.light_color));c.modify();c.set_intensity(950.)
        c.set_light_color(u.LinearColor(.82,.88,1.))
    # Reuse matching green reception plants at the doorway and consultation bays.
    for i,(x,y) in enumerate(((3890.,2840.),(3890.,3970.),(4940.,3090.),(5100.,4010.)),1):
        for source_label,suffix in (('Refine/CentralWelcomeGreeneryLights1/Planter 1','Planter'),
                                     ('Refine/Concept73/Waiting/Plant 1','Tree'),
                                     ('Refine/Concept73/Waiting/Understory 1','Understory')):
            found=[a for a in actors if a.get_actor_label()==source_label]
            if not found and suffix=='Planter':
                found=[a for a in actors if a.get_actor_label()=='Refine/WholeRooms20261009/R/Waiting greenery 1/Planter']
            assert len(found)==1,source_label
            a=named(sub.duplicate_actor(found[0],world),'Greenery '+str(i)+'/'+suffix)
            p,e=a.get_actor_bounds(False)
            a.set_actor_location(a.get_actor_location()+u.Vector(x-p.x,y-p.y,0.),False,True)
    return state,{'new_actors':len(state['new']),'changed_actors':len(state['actors']),
                  'hologram_bays':bay_rows,'seated_visitors':occupants,'common_area_model_replaced':'Amethyst -> covered Olive',
                  'map_saved':False,'contacts_and_circulation':'PENDING'}


def refine(u,state):
    """Corrections observed in the first runtime review; source parents stay intact."""
    assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    assert not u.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    sub=u.get_editor_subsystem(u.EditorActorSubsystem)
    actors=list(sub.get_all_level_actors())
    edit=u.MaterialEditingLibrary
    tools=u.AssetToolsHelpers.get_asset_tools()

    def tint_shader(name,parent,color):
        assert not u.EditorAssetLibrary.does_asset_exist(PRIVATE+'/'+name)
        m=tools.duplicate_asset(name,PRIVATE,parent)
        state['private'].append(m)
        original=edit.get_material_property_input_node(m,u.MaterialProperty.MP_BASE_COLOR)
        output=edit.get_material_property_input_node_output_name(m,u.MaterialProperty.MP_BASE_COLOR)
        tint=edit.create_material_expression(m,u.MaterialExpressionVectorParameter,-250,200)
        tint.set_editor_property('parameter_name','StationPaletteTint')
        tint.set_editor_property('default_value',u.LinearColor(*color))
        node=edit.create_material_expression(m,u.MaterialExpressionMultiply,-50,100)
        assert edit.connect_material_expressions(original,output,node,'A')
        assert edit.connect_material_expressions(tint,'',node,'B')
        assert edit.connect_material_property(node,'',u.MaterialProperty.MP_BASE_COLOR)
        edit.recompile_material(m)
        return m

    base=tint_shader('M_ArchiveUpholsteryTint',u.load_asset('/Game/Clinic/Materials/M_Default_Master'),(.12,.16,.21,1.))
    source=u.load_asset('/Game/Clinic/Materials/MaterialInstances/MI_Entrance_ArmChair')
    chair=u.load_asset(PRIVATE+'/MI_ArchiveUpholstery')
    # Texture? intentionally remains true: tint the owned textile texture rather
    # than replacing its detailed base color with a flat parameter.
    edit.set_material_instance_parent(chair,base)
    for n in edit.get_scalar_parameter_names(source):
        edit.set_material_instance_scalar_parameter_value(chair,n,edit.get_material_instance_scalar_parameter_value(source,n))
    for n in edit.get_vector_parameter_names(source):
        edit.set_material_instance_vector_parameter_value(chair,n,edit.get_material_instance_vector_parameter_value(source,n))
    for n in edit.get_texture_parameter_names(source):
        value=edit.get_material_instance_texture_parameter_value(source,n)
        if value:edit.set_material_instance_texture_parameter_value(chair,n,value)
    for n in edit.get_static_switch_parameter_names(source):
        edit.set_material_instance_static_switch_parameter_value(chair,n,edit.get_material_instance_static_switch_parameter_value(source,n))
    edit.set_material_instance_scalar_parameter_value(chair,'Roughness',.74)
    edit.update_material_instance(chair)
    branch=tint_shader('M_GreenTreeBranches',u.load_asset('/Game/CyberPunkAssets/Materials01/M_Tree01_Branch_Mat'),(.10,.8,.13,1.))
    palette={}
    changed=0
    for a in actors:
        label=a.get_actor_label()
        if isinstance(a,u.StaticMeshActor) and ('Waiting/Plant ' in label or label.startswith(PREFIX+'Greenery ') and label.endswith('/Tree')):
            c=a.static_mesh_component;c.modify();c.set_material(1,branch)
        if not isinstance(a,u.StaticMeshActor) or not (label.startswith('Lounge/Bay ') and '/Panel ' in label):
            continue
        c=a.static_mesh_component
        state['materials'].append((c,list(c.get_materials())));c.modify()
        for slot,parent in enumerate(c.get_materials()):
            if not parent or parent.get_name() not in ('MI_Balanced_382eb49cd2a1','MI_Balanced_75e8746cd43c','MI_Balanced_8bab5e5dc70e','MI_Balanced_7b7ccec0ddba'):
                continue
            key=parent.get_name()
            if key not in palette:
                name='MI_ArchiveWall_'+key.removeprefix('MI_Balanced_')
                assert not u.EditorAssetLibrary.does_asset_exist(PRIVATE+'/'+name)
                m=tools.create_asset(name,PRIVATE,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
                edit.set_material_instance_parent(m,parent)
                for parameter,color in (('Albedo Tint',(.14,.18,.23,1.)),('Albedo Tint (Damage)',(.32,.36,.41,1.)),('Albedo Tint (Dirt)',(.08,.10,.13,1.))):
                    edit.set_material_instance_vector_parameter_value(m,parameter,u.LinearColor(*color))
                edit.set_material_instance_scalar_parameter_value(m,'Min Roughness',.58)
                edit.set_material_instance_scalar_parameter_value(m,'Max Roughness',.86)
                edit.update_material_instance(m);state['private'].append(m);palette[key]=m
            c.set_material(slot,palette[key])
        changed+=1
    for i in (1,2,3):
        m=u.load_asset(PRIVATE+'/MI_ArchiveProjection'+str(i))
        for n,v in (('BodyEmission',3.),('BodyOpacity',.5),('ScanEmission',7.),('ScanOpacity',.8),('RimEmission',9.),('RimOpacity',.8)):
            edit.set_material_instance_scalar_parameter_value(m,n,v)
        edit.update_material_instance(m)
    warm=u.load_asset('/Game/OutpostSandbox/StationRefinement/Concept73/MI_WarmPractical')
    lamp=u.load_asset('/Game/CyberpunkRestaurant/Meshes/SM_Lamp_02')
    for i,x in enumerate((3530.,4110.,4690.),1):
        for side in (-1,1):
            a=sub.spawn_actor_from_class(u.StaticMeshActor,u.Vector())
            a.set_actor_label(PREFIX+'Bay '+str(i)+'/Warm edge '+str(side))
            state['new'].append(a)
            c=a.static_mesh_component;c.set_static_mesh(lamp);c.set_material(0,warm);c.set_collision_profile_name('NoCollision')
            a.set_actor_rotation(u.Rotator(pitch=90.,yaw=-90.),False)
            _,b=a.get_actor_bounds(False);s=280./(2*b.z);a.set_actor_scale3d(u.Vector(s,s,s))
            p,b=a.get_actor_bounds(False)
            a.set_actor_location(u.Vector(x+side*148.-p.x,4178.-p.y,30.-p.z+b.z),False,True)
    for a in actors:
        if a.get_actor_label().startswith('LoungeNative/Conversation ') and a.get_actor_label().endswith('/Task light'):
            c=a.get_component_by_class(u.LightComponent);c.modify();c.set_intensity(1400.)
            c.set_light_color(u.LinearColor(1.,.67,.38));c.set_attenuation_radius(480.)
    return {'dark_textured_chairs':6,'R_wall_actors':changed,'brighter_projectors':3,'warm_edge_fixtures':6,'map_saved':False}


def add_furniture_collision(u,state):
    """Private simple collision makes chair/table circulation checks meaningful."""
    assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    sub=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    tools=u.AssetToolsHelpers.get_asset_tools()
    meshes={}
    for name,source in (('Armchair','/Game/Clinic/Meshes/Props/SM_Entrance_ArmChair01'),
                        ('Table','/Game/CyberpunkRestaurant/Meshes/SM_Table_02')):
        path=PRIVATE+'/SM_Archive'+name+'Collidable'
        assert not u.EditorAssetLibrary.does_asset_exist(path)
        mesh=tools.duplicate_asset(path.rsplit('/',1)[1],PRIVATE,u.load_asset(source))
        state['private'].append(mesh)
        assert sub.get_simple_collision_count(mesh)==0
        assert sub.add_simple_collisions(mesh,u.ScriptingCollisionShapeType.BOX)>=0
        assert sub.get_simple_collision_count(mesh)==1
        meshes[name]=mesh
    changed=0
    for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        if a.get_actor_label().startswith(PREFIX+'Group ') and isinstance(a,u.StaticMeshActor):
            suffix=a.get_actor_label().rsplit('/',1)[1]
            if suffix in meshes:
                c=a.static_mesh_component;c.modify();c.set_static_mesh(meshes[suffix])
                c.set_collision_profile_name('BlockAll');a.set_actor_enable_collision(True)
                changed+=1
    assert changed==9
    return {'blocking_furniture':changed,'private_meshes':[m.get_path_name() for m in meshes.values()]}


def finish_display_labels(u):
    """Clarify bay labels and use the same holo treatment on the wardrobe preview."""
    assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    actors=list(u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors())
    def one(label):
        rows=[a for a in actors if a.get_actor_label()==label]
        assert len(rows)==1,label
        return rows[0]
    for i in (1,2,3):
        a=one(PREFIX+'Bay '+str(i)+'/Header');a.modify()
        p=a.get_actor_location();p.z=380.;a.set_actor_location(p,False,True)
        a.text_render.set_world_size(26.)
    a=one('Refine/Archive/Identity');a.modify()
    p=a.get_actor_location();p.z=422.;a.set_actor_location(p,False,True)
    terminal=one('Services/CREW WARDROBE')
    target=one('Lounge/Wardrobe projection')
    assert terminal.presentation_target==target
    material=u.load_asset(PRIVATE+'/MI_ArchiveProjection1')
    terminal.modify();terminal.set_editor_property('hologram_material',material)
    target.character_mesh.modify()
    for i in range(target.character_mesh.get_num_materials()):
        target.character_mesh.set_material(i,material)
    return {'bay_headers':3,'wardrobe_hologram':material.get_path_name(),
            'wardrobe_use_point_and_behavior':'unchanged'}


def resolve_sign_overlap(u):
    """Final view correction: one header per bay and a legible reception badge."""
    assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    actors=list(u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors())
    def one(label):
        found=[a for a in actors if a.get_actor_label()==label]
        assert len(found)==1,label
        return found[0]
    identity=one('Refine/Archive/Identity')
    identity.modify();identity.set_actor_hidden_in_game(True)
    ink=u.load_asset('/Engine/EngineMaterials/UnlitText')
    for i in (1,2,3):
        a=one(PREFIX+'Bay '+str(i)+'/Header');a.modify()
        a.text_render.set_world_size(34.)
        a.text_render.set_material(0,ink)
        a.text_render.set_text_render_color(u.Color(214,229,250,255))
    badge=one('Refine/Reception/Welcome');badge.modify()
    badge.text_render.set_world_size(26.)
    badge.text_render.set_material(0,ink)
    badge.text_render.set_text_render_color(u.Color(229,238,248,255))
    return {'overlapping_archive_identity_hidden':True,'bay_headers':3,
            'reception_nameplate_contrast':'increased','map_saved':False}


def finish_nameplate(u):
    """Keep two-line branding below the counter lip at ordinary exposure."""
    assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    path=PRIVATE+'/MI_LegibleHeaders'
    assert not u.EditorAssetLibrary.does_asset_exist(path)
    edit=u.MaterialEditingLibrary
    ink=u.AssetToolsHelpers.get_asset_tools().create_asset('MI_LegibleHeaders',PRIVATE,
        u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
    edit.set_material_instance_parent(ink,u.load_asset('/Game/OutpostSandbox/Materials/M_OutpostReadableTextOneSided'))
    assert 'OutpostTextGain' in map(str,edit.get_scalar_parameter_names(ink))
    edit.set_material_instance_scalar_parameter_value(ink,'OutpostTextGain',6.)
    edit.update_material_instance(ink)
    count=0
    for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        label=a.get_actor_label()
        if label=='Refine/Reception/Welcome' or label.startswith(PREFIX+'Bay ') and label.endswith('/Header'):
            a.modify();a.text_render.set_text_material(ink);count+=1
            if label=='Refine/Reception/Welcome':
                a.set_actor_location(u.Vector(3883.,0.,62.),False,True)
    assert count==4
    return {'labels':count,'private_material':ink.get_path_name(),'map_saved':False}
