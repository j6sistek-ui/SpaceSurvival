"""Stage concept-led station detail in the live map; the lead reviews before saving.

Original kit assets, player state and held T content are preserved. Native scene
state is retained for rollback; this recipe refuses replay over its own adoption.
"""
import hashlib
import math
from pathlib import Path

MAP = '/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime'
PREFIX = 'Refine/Concept73/'
PRIVATE = '/Game/OutpostSandbox/StationRefinement/Concept73'
P4 = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/'
P5 = '/Game/P1toP5_Bundle/P5_FruitSeller/'
BOARDS = (
    ('OPERATIONS', 'SHIP LOADOUT<br>AND UPGRADES', '^'),
    ('CREW<br>ARCHIVE', 'CHANGE YOUR<br>CHARACTER', '>'),
    ('WAYFARER', 'PEOPLE<br>WORLDS<br>POSSIBILITIES', ''),
    ('MARKET', 'ARRIVAL WALK<br>AND BERTHS', '>'),
    ('DEPARTURES', 'RETURN TO<br>YOUR SHIP', '<'),
    ('SOCIAL<br>LOUNGE', 'BAR, BOOTHS<br>AND ARCADE', '<'),
    ('WELCOME', 'TAKE A MOMENT<br>FIND YOUR<br>NEXT STOP', ''),
    ('WAYFARER', 'EXCHANGE<br>GOOD COMPANY<br>BETWEEN RUNS', ''),
)


def apply_central(u, expected_sha256, after_verified_rollback=False):
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    world = editor.get_editor_world()
    assert not editor.get_game_world() and world.get_path_name().split('.')[0] == MAP
    file = Path(u.Paths.project_content_dir()) / (MAP.removeprefix('/Game/') + '.umap')
    assert hashlib.sha256(file.read_bytes()).hexdigest() == expected_sha256
    dirty_maps = [p.get_name() for p in u.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
    dirty_content = [p.get_name() for p in u.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
    assert not dirty_maps or (after_verified_rollback and dirty_maps == [MAP])
    assert not dirty_content or (after_verified_rollback and all(p.startswith(PRIVATE+'/') for p in dirty_content))
    sub = u.get_editor_subsystem(u.EditorActorSubsystem)
    actors = list(sub.get_all_level_actors())
    assert not any(a.get_actor_label().startswith(PREFIX) for a in actors), 'Already staged; inspect current state'
    state = {'actors': [], 'new': [], 'materials': [], 'texts': [], 'lights': [], 'private': []}
    edit = u.MaterialEditingLibrary

    def one(label):
        found = [a for a in actors if a.get_actor_label() == label]
        assert len(found) == 1, label
        return found[0]

    def keep(a):
        if not any(row[0] == a for row in state['actors']):
            state['actors'].append((a, a.get_actor_transform(), a.hidden, a.get_actor_enable_collision()))
            a.modify()
        return a

    def hidden(a):
        keep(a).set_actor_hidden_in_game(True)
        a.set_actor_enable_collision(False)

    def named(a, label):
        a.set_actor_label(PREFIX + label)
        a.set_editor_property('tags', [u.Name('OutpostAuthored'), u.Name('OutpostLabel:' + PREFIX + label)])
        state['new'].append(a)
        return a

    def instance(name, parent, scalars=None, vectors=None):
        exists = u.EditorAssetLibrary.does_asset_exist(PRIVATE+'/'+name)
        assert not exists or after_verified_rollback, 'Inspect existing private material before reuse'
        m = u.load_asset(PRIVATE+'/'+name) if exists else u.AssetToolsHelpers.get_asset_tools().create_asset(
            name, PRIVATE, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
        assert m
        assert not exists or m.parent == u.load_asset(parent), 'Preserve changed parent'
        state['private'].append(m)
        edit.set_material_instance_parent(m, u.load_asset(parent))
        for k, v in (scalars or {}).items():
            assert k in map(str, edit.get_scalar_parameter_names(m)), k
            edit.set_material_instance_scalar_parameter_value(m, k, v)
        for k, v in (vectors or {}).items():
            assert k in map(str, edit.get_vector_parameter_names(m)), k
            edit.set_material_instance_vector_parameter_value(m, k, u.LinearColor(*v))
        edit.update_material_instance(m)
        return m

    def surface(a, material, slots=None):
        c = keep(a).static_mesh_component
        state['materials'].append((c, list(c.get_materials())))
        c.modify()
        for slot in (range(c.get_num_materials()) if slots is None else slots):
            c.set_material(slot, material)

    def prop(label, mesh, center, size, rotation, material=None, fit='height'):
        a = named(sub.spawn_actor_from_class(u.StaticMeshActor, u.Vector()), label)
        c = a.static_mesh_component
        m = u.load_asset(mesh)
        assert isinstance(m, u.StaticMesh)
        c.set_static_mesh(m)
        c.set_collision_profile_name('NoCollision')
        a.set_actor_rotation(rotation, False)
        _, b = a.get_actor_bounds(False)
        scale = size / (2.*(b.z if fit == 'height' else max(b.x,b.y,b.z)))
        a.set_actor_scale3d(u.Vector(scale,scale,scale))
        p,b = a.get_actor_bounds(False)
        a.set_actor_location(u.Vector(center[0]-p.x,center[1]-p.y,center[2]-p.z+b.z),False,True)
        if material:
            for i in range(c.get_num_materials()):
                c.set_material(i,material)
        return a

    def text(a, copy, center, yaw, size, color=(219,237,255,255)):
        keep(a)
        c=a.text_render
        state['texts'].append((c,c.text,c.world_size,c.text_render_color))
        c.modify()
        c.set_text(copy)
        c.set_world_size(size)
        c.set_text_render_color(u.Color(*color))
        a.set_actor_location(u.Vector(*center),False,True)
        a.set_actor_rotation(u.Rotator(yaw=yaw),False)
        a.set_actor_scale3d(u.Vector(1,1,1))
        a.set_actor_hidden_in_game(False)

    def light(label, position, target, lumens, radius, width, height, warm=True):
        a=named(sub.spawn_actor_from_class(u.RectLight,u.Vector(*position)),label)
        a.set_actor_rotation(u.MathLibrary.find_look_at_rotation(u.Vector(*position),u.Vector(*target)),False)
        c=a.rect_light_component
        c.set_mobility(u.ComponentMobility.MOVABLE)
        c.set_intensity_units(u.LightUnits.LUMENS)
        c.set_intensity(lumens)
        c.set_attenuation_radius(radius)
        c.set_source_width(width)
        c.set_source_height(height)
        c.set_light_color(u.LinearColor(1.,.70,.42) if warm else u.LinearColor(.82,.9,1.))
        c.set_cast_shadows(False)
        c.set_specular_scale(.12)
        c.set_indirect_lighting_intensity(.12)
        return a

    try:
        blue=instance('MI_WayfindingBlue','/Game/OutpostSandbox/Materials/M_OutpostCyan',
                      vectors={'HullTint':(.012,.075,.25,1.)})
        warm=instance('MI_WarmPractical','/Game/CyberpunkRestaurant/Materials/MI_Emissive_09',
                      {'Intensity':3.2},{'Emissive Color':(1.,.72,.43,1.)})
        graphite=instance('MI_ReceptionMetal',P4+'Materials/Instances/Opaque/MI_Metal02_AnodizedAluminium',
             {'Min Roughness':.48,'Max Roughness':.8,'Specular Intensity':.32},
             {'Albedo Tint':(.16,.21,.26,1.)})
        glass=instance('MI_DirectionGlass',P4+'Materials/Instances/Translucent/MI_DigitalGlass_Window200X250',
             {'Reflection':.02,'Refraction':1.,'Refraction_Lerp':1.,'Intensity EM1':.12,
              'Intensity EM2':0.,'Intensity EM3':0.,'Opacity':.24,'Opacity_Lerp':.24})
        # Keep proper upright kit frames; remove the old low-standing supports
        # and tiny duplicate headers from the same central wall bays.
        for a in actors:
            label=a.get_actor_label()
            if label.startswith('AtriumDetail/Wall service ') and ('/Information screen' in label or '/Screen hanger' in label):
                hidden(a)
            if label.startswith('Refine/Reception/Direction ') and '/Support ' in label:
                hidden(a)
        template=one('Refine/Reception/Direction 1/Title')
        for i,(heading,body,arrow) in enumerate(BOARDS,1):
            angle=22.5+(i-1)*45.
            r=math.radians(angle)
            radial=u.Vector(math.cos(r),math.sin(r),0.)
            base=u.Vector(4200,0,225)+radial*1470.
            yaw=angle+180.
            parts={}
            for suffix in ('Frame','Glass','Backing','Title'):
                a=one('Refine/Reception/Direction '+str(i if i<=7 else 1)+'/'+suffix)
                if i==8:
                    a=named(sub.duplicate_actor(a,world),'Direction 8/'+suffix)
                keep(a).set_actor_hidden_in_game(False)
                a.set_actor_enable_collision(False)
                parts[suffix]=a
            for suffix in ('Frame','Glass'):
                a=parts[suffix]
                a.set_actor_location(base,False,True)
                a.set_actor_rotation(u.Rotator(yaw=yaw),False)
                a.set_actor_scale3d(u.Vector(1.,.88,1.4))
            surface(parts['Glass'],glass)
            b=parts['Backing']
            b.set_actor_location(base+radial*4.+u.Vector(0,0,175),False,True)
            b.set_actor_rotation(u.Rotator(yaw=angle),False)
            b.set_actor_scale3d(u.Vector(.06,1.55,3.16))
            surface(b,blue)
            face=u.Vector(4200,0,0)+radial*1443.
            text(parts['Title'],heading,(face.x,face.y,505.),yaw,25.)
            small=named(sub.duplicate_actor(template,world),'Direction '+str(i)+'/Purpose')
            text(small,body,(face.x,face.y,402.),yaw,17.)
            if arrow:
                mark=named(sub.duplicate_actor(template,world),'Direction '+str(i)+'/Arrow')
                text(mark,{'<':'\u2190','>':'\u2192','^':'\u2191'}[arrow],(face.x,face.y,302.),yaw,44.)
            # Warm integrated fixture to one side of each panel, centred on its rib.
            tangent=u.Vector(-radial.y,radial.x,0.)
            f=u.Vector(4200,0,0)+radial*1475.+tangent*133.
            fixture=prop('Rib '+str(i)+'/Housing','/Game/CyberpunkRestaurant/Meshes/SM_Lamp_02',
                         (f.x,f.y,250.),250.,u.Rotator(pitch=90.,yaw=angle+180.))
            fixture.static_mesh_component.set_material(0,warm)
            source=u.Vector(4200,0,360)+radial*1430.+tangent*133.
            target=u.Vector(4200,0,180)+radial*900.+tangent*133.
            light('Rib '+str(i)+'/Light',source.to_tuple(),target.to_tuple(),800.,720.,18.,240.)

        # Use tall owned organic geometry rooted inside the existing planters.
        for i in range(1,5):
            old=one('Refine/CentralWelcomeGreeneryLights1/Foliage '+str(i))
            p,_=old.get_actor_bounds(False)
            hidden(old)
            prop('Waiting/Plant '+str(i),P5+'Meshes/SM_ConstructionPart'+str(108 if i%2 else 110)+'_Plant',
                 (p.x,p.y,32.),145. if i%2 else 125.,u.Rotator(yaw=i*67.))

        for a in actors:
            if a.get_actor_label().startswith('Refine/Reception/Body segment ') or a.get_actor_label()=='Refine/Reception/Circular body':
                surface(a,graphite)
        welcome=one('Refine/Reception/Welcome')
        text(welcome,'WAYFARER<br>EXCHANGE',(3891.,0.,78.),180.,20.)
        # A broad local fill makes both sides of the staffed desk readable.
        light('Reception/Rear soft fill',(4620.,0.,340.),(4250.,0.,105.),1300.,760.,200.,150.,False)
        light('Reception/Overhead soft fill',(4200.,0.,480.),(4200.,0.,100.),900.,690.,200.,200.,False)

        # Clothed/visually screened members of the existing cast meet at the
        # waiting bays. Their vendor labels do not restrict these ambient roles.
        for label,source,p,yaw,phase in (
            ('Waiting/Visitor A','Crew/Trader A',(4830.,700.,85.),100.,1.),
            ('Waiting/Visitor B','Crew/Trader B',(4800.,835.,85.),-80.,8.),
            ('Reception/Visitor','Crew/Trader A',(3740.,-310.,85.),48.,4.),
        ):
            a=named(sub.duplicate_actor(one(source),world),label)
            a.set_actor_location(u.Vector(*p),False,True)
            a.set_actor_rotation(u.Rotator(yaw=yaw),False)
            a.set_editor_property('route_points',[])
            a.set_editor_property('phase_offset',phase)
            name='Robe' if source.endswith(' A') else 'Glyph'
            root='/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew/'+name+'/A_'+name+'_'
            idle=u.load_asset(root+('Listen' if label.endswith('B') else 'Idle'))
            talk=u.load_asset(root+'Talk')
            assert idle.get_editor_property('skeleton') == a.character_mesh.get_skeletal_mesh_asset().skeleton == talk.get_editor_property('skeleton')
            a.set_editor_property('idle_animation',idle)
            a.set_editor_property('gesture_animations',[talk])
            a.character_mesh.set_editor_property('animation_data',u.SingleAnimationPlayData(
                anim_to_play=idle,saved_looping=True,saved_playing=True))
            a.refresh_readability_lighting()
        return state, {'staged':True,'new_actors':len(state['new']),
                       'changed_original_actors':len(state['actors']),
                       'private_materials':[m.get_path_name() for m in state['private']],
                       'map_saved':False,'concept':'Station-Design-Targets.png / Atrium Welcome'}
    except Exception:
        restore(u,state)
        raise


def restore(u,state):
    sub=u.get_editor_subsystem(u.EditorActorSubsystem)
    for c,intensity,color in reversed(state['lights']):
        c.set_intensity(intensity)
        c.set_editor_property('light_color',color)
    for c,materials in reversed(state['materials']):
        for i,m in enumerate(materials):
            c.set_material(i,m)
    for c,copy,size,color in reversed(state['texts']):
        c.set_text(copy)
        c.set_world_size(size)
        c.set_text_render_color(color)
    for a,transform,hidden,collision in reversed(state['actors']):
        if a not in state['new']:
            a.set_actor_transform(transform,False,True)
            a.set_actor_hidden_in_game(hidden)
            a.set_actor_enable_collision(collision)
    for a in reversed(state['new']):
        sub.destroy_actor(a)


def refine_central(u, state):
    """Apply observed first-review corrections, retaining the original rollback."""
    sub=u.get_editor_subsystem(u.EditorActorSubsystem)
    actors=list(sub.get_all_level_actors())
    assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    assert not u.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    edit=u.MaterialEditingLibrary
    mats={}

    def one(label):
        return next(a for a in actors if a.get_actor_label()==label)

    def keep(a):
        if not any(row[0]==a for row in state['actors']):
            state['actors'].append((a,a.get_actor_transform(),a.hidden,a.get_actor_enable_collision()))
        a.modify()
        return a

    def mi(name,parent,color):
        assert not u.EditorAssetLibrary.does_asset_exist(PRIVATE+'/'+name)
        m=u.AssetToolsHelpers.get_asset_tools().create_asset(name,PRIVATE,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
        edit.set_material_instance_parent(m,parent)
        edit.set_material_instance_vector_parameter_value(m,'HullTint' if name=='MI_DirectionInk' else 'Albedo Tint',u.LinearColor(*color))
        state['private'].append(m)
        edit.update_material_instance(m)
        return m

    ink=mi('MI_DirectionInk',u.load_asset('/Game/OutpostSandbox/Materials/M_OutpostCyan'),(.7,.85,1.,1.))
    # Simple native arrow geometry avoids a font's missing Unicode glyphs.
    for i,(_,_,direction) in enumerate(BOARDS,1):
        if not direction:
            continue
        old=keep(one(PREFIX+'Direction '+str(i)+'/Arrow'))
        old.set_actor_hidden_in_game(True)
        angle=math.radians(22.5+(i-1)*45.)
        radial=u.Vector(math.cos(angle),math.sin(angle),0.)
        tangent=u.Vector(-radial.y,radial.x,0.)
        center=u.Vector(4200,0,315)+radial*1442.
        segments=[((-24,0),(24,0)),((24,0),(5,19)),((24,0),(5,-19))]
        def point(p):
            x,y=p
            if direction=='<':x=-x
            if direction=='^':x,y=-y,x
            return center+tangent*x+u.Vector(0,0,y)
        for j,(a,b) in enumerate(segments):
            p,q=point(a),point(b)
            actor=sub.spawn_actor_from_class(u.StaticMeshActor,(p+q)*.5)
            actor.set_actor_label(PREFIX+'Direction '+str(i)+'/Arrow geometry '+str(j))
            actor.set_editor_property('tags',[u.Name('OutpostAuthored')])
            actor.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube'))
            actor.static_mesh_component.set_material(0,ink)
            actor.static_mesh_component.set_collision_profile_name('NoCollision')
            actor.set_actor_rotation(u.MathLibrary.find_look_at_rotation(p,q),False)
            actor.set_actor_scale3d(u.Vector((q-p).length()/100.,.035,.035))
            state['new'].append(actor)
    tree=u.load_asset('/Game/CyberPunkAssets/Environment01/SM_Tree01')
    for i in range(1,5):
        a=keep(one(PREFIX+'Waiting/Plant '+str(i)))
        p,b=a.get_actor_bounds(False)
        center=u.Vector(p.x,p.y,32.)
        c=a.static_mesh_component
        c.set_static_mesh(tree)
        c.set_editor_property('override_materials',[])
        scale=(175. if i%2 else 160.)/(2.*tree.get_bounds().box_extent.z)
        a.set_actor_scale3d(u.Vector(scale,scale,scale))
        a.set_actor_location(u.Vector(),False,True)
        p,b=a.get_actor_bounds(False)
        a.set_actor_location(center-u.Vector(p.x,p.y,p.z-b.z),False,True)
    # Only central structural surfaces get private palette variants. Floor and
    # functional display materials retain their current assignments.
    selected=('MI_Balanced_382eb49cd2a1','MI_Balanced_75e8746cd43c','MI_Balanced_8bab5e5dc70e')
    changed=0
    for a in actors:
        label=a.get_actor_label()
        if not (label.startswith('Atrium/') and 'Floor' not in label and isinstance(a,u.StaticMeshActor)):
            continue
        c=a.static_mesh_component
        slots=[(i,m) for i,m in enumerate(c.get_materials()) if m and m.get_name() in selected]
        if not slots:
            continue
        keep(a)
        state['materials'].append((c,list(c.get_materials())))
        c.modify()
        for i,parent in slots:
            key=parent.get_path_name()
            if key not in mats:
                m=mi('MI_CentralStructure_'+hashlib.sha256(key.encode()).hexdigest()[:8],parent,(.25,.30,.36,1.))
                for parameter,value in (('Min Roughness',.55),('Max Roughness',.85),('Specular Intensity',.28)):
                    if parameter in map(str,edit.get_scalar_parameter_names(m)):
                        edit.set_material_instance_scalar_parameter_value(m,parameter,value)
                edit.update_material_instance(m)
                mats[key]=m
            c.set_material(i,mats[key])
        changed+=1
    for a in actors:
        label=a.get_actor_label()
        if label.startswith('AtriumDetail/Wall service ') and '/Vertical feed ' in label:
            keep(a).set_actor_hidden_in_game(True)
            a.set_actor_enable_collision(False)
        if label=='Atrium/Light pool':
            c=a.get_component_by_class(u.LightComponent)
            state['lights'].append((c,c.intensity,c.light_color))
            c.modify()
            c.set_intensity(1000.)
            c.set_light_color(u.LinearColor(1.,.85,.68))
        if label.startswith(PREFIX+'Rib ') and label.endswith('/Light'):
            a.rect_light_component.set_intensity(1300.)
    visitor=keep(one(PREFIX+'Reception/Visitor'))
    visitor.set_actor_location(u.Vector(3928.,-272.,85.),False,True)
    visitor.set_actor_rotation(u.Rotator(yaw=45.),False)
    return {'arrow_geometry':15,'full_canopy_plants':4,'central_structure_actors':changed,
            'central_light_pools':8,'map_saved':False}


def occupy_waiting(u, state, derivatives):
    """Two native seated readers and foliage understory, fitted for review."""
    assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    sub=u.get_editor_subsystem(u.EditorActorSubsystem)
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    actors=list(sub.get_all_level_actors())
    def one(label):
        rows=[a for a in actors if a.get_actor_label()==label]
        assert len(rows)==1,label
        return rows[0]
    def named(a,label):
        a.set_actor_label(PREFIX+label)
        a.set_editor_property('tags',[u.Name('OutpostAuthored'),u.Name('StationAtmosphere:SeatedReader')])
        state['new'].append(a)
        return a
    assert not any(a.get_actor_label().startswith(PREFIX+'Reader ') for a in actors)
    record=[]
    for side,name,source,yaw in (('NE','Tendril','Crew/Atrium B',-135.),('SW','Robe','Crew/Trader A',45.)):
        row=next(r for r in derivatives['derivatives'] if r['name']==name)
        bench=one('Refine/CentralWelcomeArrival2/'+side+'/Bench')
        p,_=bench.get_actor_bounds(False)
        offset=min(row['bones_cm']['ball_l'][2],row['bones_cm']['ball_r'][2])-5.5
        a=named(sub.duplicate_actor(one(source),world),'Reader '+side)
        a.set_actor_location(u.Vector(p.x,p.y,85.),False,True)
        a.set_actor_rotation(u.Rotator(yaw=yaw),False)
        a.set_editor_property('route_points',[])
        a.set_editor_property('gesture_animations',[])
        a.set_editor_property('phase_offset',.65 if side=='NE' else 2.3)
        clip=u.load_asset(row['clip'])
        c=a.character_mesh
        c.set_relative_location(u.Vector(0,0,-85.-offset),False,True)
        c.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
        c.set_editor_property('animation_data',u.SingleAnimationPlayData(anim_to_play=clip,saved_looping=True,saved_playing=True))
        a.set_editor_property('idle_animation',clip)
        a.refresh_readability_lighting()
        # The low loop's hands rest together above the lap. The tablet follows
        # the reader through the same small idle motion as the existing clip.
        hands=[row['bones_cm'][n] for n in ('hand_l','hand_r')]
        local=u.Vector(*[(hands[0][i]+hands[1][i])*.5 for i in range(3)])
        point=c.get_world_transform().transform_location(local)
        tablet=named(sub.spawn_actor_from_class(u.StaticMeshActor,u.Vector()),'Reader '+side+'/Tablet')
        tc=tablet.static_mesh_component
        tc.set_static_mesh(u.load_asset('/Game/Cyberpunk_Room/Mesh/SM_Tablet'))
        tc.set_mobility(u.ComponentMobility.MOVABLE)
        tc.set_collision_profile_name('NoCollision')
        b=tc.static_mesh.get_bounds()
        scale=24./(2.*max(b.box_extent.x,b.box_extent.y,b.box_extent.z))
        tablet.set_actor_scale3d(u.Vector(scale,scale,scale))
        tablet.set_actor_rotation(u.Rotator(pitch=-20.,yaw=yaw),False)
        q,_=tablet.get_actor_bounds(False)
        tablet.set_actor_location(point-q+u.Vector(0,0,1.),False,True)
        tablet.attach_to_component(c,'hand_l',u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,False)
        record.append({'side':side,'character':name,'actor':a.get_path_name(),'clip':row['clip'],'lowering_cm':offset})
    shrub=u.load_asset('/Game/Nanite_Plants_Sample_Collection/Geometries/SM_Abelia_x_grandiflora_Nanite_Free_Sample')
    for i in range(1,5):
        tree=one(PREFIX+'Waiting/Plant '+str(i))
        p,b=tree.get_actor_bounds(False)
        a=named(sub.spawn_actor_from_class(u.StaticMeshActor,u.Vector()),'Waiting/Understory '+str(i))
        a.static_mesh_component.set_static_mesh(shrub)
        a.static_mesh_component.set_collision_profile_name('NoCollision')
        scale=95./(2.*max(shrub.get_bounds().box_extent.x,shrub.get_bounds().box_extent.y))
        a.set_actor_scale3d(u.Vector(scale,scale,scale))
        a.set_actor_rotation(u.Rotator(yaw=i*42.),False)
        q,e=a.get_actor_bounds(False)
        a.set_actor_location(u.Vector(p.x-q.x,p.y-q.y,31.-q.z+e.z),False,True)
    return {'readers':record,'understory_plants':4,'native_motion_and_contacts':'PENDING','map_saved':False}


def finish_central_signs(u, state):
    """Increase direction readability and derive green leaves from the owned tree."""
    assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    actors=list(u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors())
    edit=u.MaterialEditingLibrary
    name='M_CentralGreenLeaves'
    assert not u.EditorAssetLibrary.does_asset_exist(PRIVATE+'/'+name)
    source=u.load_asset('/Game/CyberPunkAssets/Materials01/M_Tree01_Leaf_Mat')
    material=u.AssetToolsHelpers.get_asset_tools().duplicate_asset(name,PRIVATE,source)
    state['private'].append(material)
    original=edit.get_material_property_input_node(material,u.MaterialProperty.MP_BASE_COLOR)
    output=edit.get_material_property_input_node_output_name(material,u.MaterialProperty.MP_BASE_COLOR)
    assert original
    tint=edit.create_material_expression(material,u.MaterialExpressionVectorParameter,-250,200)
    tint.set_editor_property('parameter_name','LeafTint')
    tint.set_editor_property('default_value',u.LinearColor(.13,.82,.19,1.))
    multiply=edit.create_material_expression(material,u.MaterialExpressionMultiply,-50,100)
    assert edit.connect_material_expressions(original,output,multiply,'A')
    assert edit.connect_material_expressions(tint,'',multiply,'B')
    assert edit.connect_material_property(multiply,'',u.MaterialProperty.MP_BASE_COLOR)
    edit.recompile_material(material)
    for a in actors:
        label=a.get_actor_label()
        if label.startswith(PREFIX+'Waiting/Plant '):
            c=a.static_mesh_component
            state['materials'].append((c,list(c.get_materials())))
            c.modify()
            c.set_material(2,material)
        if ('/Direction ' in label and label.endswith(('/Frame','/Glass','/Backing','/Title','/Purpose'))
                and (label.startswith('Refine/Reception/') or label.startswith(PREFIX))):
            a.modify()
            if label.endswith(('/Frame','/Glass')):
                scale=a.get_actor_scale3d();scale.y=1.24;a.set_actor_scale3d(scale)
            elif label.endswith('/Backing'):
                scale=a.get_actor_scale3d();scale.y=2.20;a.set_actor_scale3d(scale)
            else:
                a.text_render.set_world_size(31. if label.endswith('/Title') else 22.)
        if label.startswith(PREFIX+'Rib '):
            i=int(label.split('Rib ')[1].split('/')[0])
            angle=math.radians(22.5+(i-1)*45.)
            delta=u.Vector(-math.sin(angle)*43.,math.cos(angle)*43.,0.)
            a.modify();a.set_actor_location(a.get_actor_location()+delta,False,True)
    return {'wider_panels':8,'green_leaf_material':material.get_path_name(),
            'source_leaf_shader_preserved':True,'map_saved':False}
