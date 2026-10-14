"""Guarded Central-only architectural pass; dry-run before applying once.

The caller owns native save, matched captures and adoption. Original assets,
floors, staff, directions, services and other rooms are not regenerated.
"""
import hashlib
import math
from pathlib import Path

MAP = '/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime'
PREFIX = 'Refine/CentralArchitecture97/'
PRIVATE = '/Game/OutpostSandbox/StationRefinement/CentralArchitecture97'
P4 = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Meshes/'
ARCHIVE = '/Game/OutpostSandbox/StationRefinement/ArchiveConcept77/'


def run(u, expected_sha256, apply=False):
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    world = editor.get_editor_world()
    assert world.get_path_name().split('.')[0] == MAP and not editor.get_game_world()
    file = Path(u.Paths.project_content_dir()) / (MAP.removeprefix('/Game/')+'.umap')
    assert hashlib.sha256(file.read_bytes()).hexdigest() == expected_sha256
    assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    assert not u.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    sub = u.get_editor_subsystem(u.EditorActorSubsystem)
    actors = list(sub.get_all_level_actors())
    assert not any(a.get_actor_label().startswith(PREFIX) for a in actors), 'Adopted pass; do not replay'
    assert not u.EditorAssetLibrary.does_directory_exist(PRIVATE), 'Inspect partial prior assets first'
    def one(label):
        found = [a for a in actors if a.get_actor_label() == label]
        assert len(found) == 1, label
        return found[0]
    required = [P4+'SM_CornerWallCeiling400X70_V13_ElectricalEquipment',
                P4+'SM_WallPanel200X100_V1_SmartStorageUnit',
                ARCHIVE+'SM_ArchiveArmchairCollidable', ARCHIVE+'SM_ArchiveTableCollidable',
                ARCHIVE+'MI_ArchiveUpholstery', ARCHIVE+'MI_ArchiveTable',
                '/Game/OutpostSandbox/StationRefinement/Concept73/MI_ReceptionMetal',
                '/Game/CyberpunkRestaurant/Meshes/SM_Lamp_02']
    for path in required: assert u.EditorAssetLibrary.does_asset_exist(path), path
    for label in ('Atrium_Bench_0','Atrium_Bench_3','Refine/Reception/Circular body',
                  'Refine/CentralWelcomeArrival2/NE/Planter left','Refine/Concept73/Waiting/Plant 1',
                  'Refine/Concept73/Waiting/Understory 1'):
        one(label)
    wall_actors = [a for a in actors if isinstance(a,u.StaticMeshActor) and not a.hidden and (
        a.get_actor_label() == 'Atrium/Upper service panel' or
        a.get_actor_label().startswith('Atrium/Bay ') and '/Panel ' in a.get_actor_label())]
    assert len(wall_actors) == 20, len(wall_actors)
    report = {'dry_run':not apply,'wall_surfaces':len(wall_actors),
              'architecture':'Eight paired mechanical pilasters and integrated header rails',
              'reception':'Twenty-four fitted cabinet fascias and narrow assembly seams',
              'waiting':'Two furnished two-chair groups; occupied benches remain intact',
              'preserved':'Floors, NPCs, service identities, directions, L/T/R/market/dock',
              'map_saved':False,'expected_map':expected_sha256}
    if not apply: return None, report
    state = {'actors':[], 'materials':[], 'new':[], 'private':[]}
    edit = u.MaterialEditingLibrary
    def keep(a):
        if not any(row[0] == a for row in state['actors']):
            state['actors'].append((a,a.get_actor_transform(),a.hidden,a.get_actor_enable_collision()))
            a.modify()
        return a
    def named(a,label):
        a.set_actor_label(PREFIX+label)
        a.set_editor_property('tags',[u.Name('OutpostAuthored'),u.Name('OutpostLabel:'+PREFIX+label)])
        state['new'].append(a)
        return a
    def instance(name,parent,colors=None,scalars=None):
        m=u.AssetToolsHelpers.get_asset_tools().create_asset(name,PRIVATE,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
        assert m
        state['private'].append(m)
        edit.set_material_instance_parent(m,parent)
        vectors=set(map(str,edit.get_vector_parameter_names(m)))
        parameters=set(map(str,edit.get_scalar_parameter_names(m)))
        for key,value in (colors or {}).items():
            assert key in vectors,key
            edit.set_material_instance_vector_parameter_value(m,key,u.LinearColor(*value))
        for key,value in (scalars or {}).items():
            assert key in parameters,key
            edit.set_material_instance_scalar_parameter_value(m,key,value)
        edit.update_material_instance(m)
        return m
    def surface(a,material,slots=None):
        c=keep(a).static_mesh_component
        state['materials'].append((c,list(c.get_materials())))
        c.modify()
        for slot in (range(c.get_num_materials()) if slots is None else slots): c.set_material(slot,material)
    def fit(label,path,center,dimensions,rotation,collision=False):
        mesh=u.load_asset(path); assert isinstance(mesh,u.StaticMesh),path
        bounds=mesh.get_bounds(); extent=bounds.box_extent
        scale=u.Vector(dimensions[0]/(2*extent.x),dimensions[1]/(2*extent.y),dimensions[2]/(2*extent.z))
        a=named(sub.spawn_actor_from_class(u.StaticMeshActor,u.Vector()),label)
        c=a.static_mesh_component;c.set_static_mesh(mesh)
        c.set_collision_profile_name('BlockAll' if collision else 'NoCollision')
        a.set_actor_enable_collision(collision)
        a.set_actor_rotation(rotation,False);a.set_actor_scale3d(scale)
        p,_=a.get_actor_bounds(False)
        a.set_actor_location(u.Vector(*center)-p,False,True)
        return a
    def grounded(label,path,xy,height,yaw,collision=False,width=None):
        mesh=u.load_asset(path); assert mesh
        e=mesh.get_bounds().box_extent
        factor=height/(2*e.z)
        dx,dy=2*e.x*factor,2*e.y*factor
        if width:
            f=width/max(dx,dy);dx*=f;dy*=f
        return fit(label,path,(xy[0],xy[1],height/2),(dx,dy,height),u.Rotator(yaw=yaw),collision)
    def duplicate_at(source,label,center):
        a=named(sub.duplicate_actor(source,world),label)
        p,_=a.get_actor_bounds(False)
        a.set_actor_location(a.get_actor_location()+u.Vector(*center)-p,False,True)
        return a
    try:
        graphite=u.load_asset('/Game/OutpostSandbox/StationRefinement/Concept73/MI_ReceptionMetal')
        warm=u.load_asset('/Game/OutpostSandbox/StationRefinement/Concept73/MI_WarmPractical')
        bronze=instance('MI_ChampagneJoinery',u.load_asset('/Game/P1toP5_Bundle/P4_Genesis_Vol1/Materials/Instances/Opaque/MI_Metal02_AnodizedAluminium'),
            {'Albedo Tint':(.28,.19,.105,1.)},{'Min Roughness':.5,'Max Roughness':.78,'Specular Intensity':.28})
        wall_palette={}
        for a in wall_actors:
            c=keep(a).static_mesh_component
            state['materials'].append((c,list(c.get_materials())));c.modify()
            for slot,parent in enumerate(c.get_materials()):
                if not parent:continue
                if not (parent.get_name().startswith('MI_CentralStructure_') or parent.get_name()=='MI_Balanced_7b7ccec0ddba'):continue
                key=parent.get_path_name()
                if key not in wall_palette:
                    wall_palette[key]=instance('MI_CentralWall_'+hashlib.sha256(key.encode()).hexdigest()[:8],parent,
                      {'Albedo Tint':(.065,.081,.10,1.),'Albedo Tint (Damage)':(.2,.22,.25,1.),'Albedo Tint (Dirt)':(.035,.045,.06,1.)},
                      {'Min Roughness':.58,'Max Roughness':.86})
                c.set_material(slot,wall_palette[key])
        # Full-height profiled kit pieces sit against solid wall hosts. The paired
        # warm fixtures and cap rail form a coherent surround for each direction.
        for i in range(1,9):
            angle=22.5+(i-1)*45.;r=math.radians(angle)
            radial=u.Vector(math.cos(r),math.sin(r),0)
            tangent=u.Vector(-radial.y,radial.x,0)
            for side in (-1,1):
                center=u.Vector(4200,0,320)+radial*1506+tangent*(165*side)
                a=fit('Bay %02d/Pilaster %s'%(i,side),required[0],center.to_tuple(),(590,45,38),u.Rotator(pitch=90,yaw=angle+90))
                # Keep all native panel, cable and label slots. Only shell trim
                # takes the shared reception metal.
                a.static_mesh_component.set_material(0,graphite)
                old=one('Refine/Concept73/Rib '+str(i)+'/Housing')
                if side==1:
                    fixture=keep(old)
                else:
                    fixture=named(sub.duplicate_actor(old,world),'Bay %02d/Warm fixture'%i)
                p,b=fixture.get_actor_bounds(False)
                target=u.Vector(4200,0,356)+radial*1468+tangent*(118*side)
                fixture.set_actor_location(fixture.get_actor_location()+target-p,False,True)
                if side==-1:
                    source=one('Refine/Concept73/Rib '+str(i)+'/Light')
                    lamp=named(sub.duplicate_actor(source,world),'Bay %02d/Practical light'%i)
                    lp=u.Vector(4200,0,320)+radial*1418+tangent*(118*side)
                    lamp.set_actor_location(lp,False,True)
                    lamp.set_actor_rotation(u.MathLibrary.find_look_at_rotation(lp,u.Vector(4200,0,160)+radial*1130),False)
                    lamp.rect_light_component.set_intensity(850.)
                    lamp.rect_light_component.set_attenuation_radius(490.)
            center=u.Vector(4200,0,615)+radial*1490
            a=fit('Bay %02d/Header service rail'%i,required[0],center.to_tuple(),(580,45,45),u.Rotator(yaw=angle+90))
            a.static_mesh_component.set_material(0,graphite)
        # Detail stays inside the established counter footprint and below its lip.
        for i in range(24):
            angle=i*15.;r=math.radians(angle)
            radial=u.Vector(math.cos(r),math.sin(r),0)
            center=u.Vector(4200,0,49)+radial*297
            a=fit('Reception/Fascia %02d'%i,required[1],center.to_tuple(),(5,70,84),u.Rotator(yaw=angle))
            for slot in range(a.static_mesh_component.get_num_materials()):
                old=a.static_mesh_component.get_material(slot)
                if old and ('Metal' in old.get_name()):a.static_mesh_component.set_material(slot,graphite)
            r=math.radians(angle+7.5);center=u.Vector(4200,0,48)+u.Vector(math.cos(r),math.sin(r),0)*299
            a=fit('Reception/Joint %02d'%i,'/Engine/BasicShapes/Cube',center.to_tuple(),(2,1.2,80),u.Rotator(yaw=angle+7.5))
            a.static_mesh_component.set_material(0,bronze)
        # The two previously sparse quadrants gain complete accessible furniture
        # groups. New furniture has the existing verified private collision meshes.
        for group,sign in (('NW',1),('SE',-1)):
            def xy(x,y):return (4200+(x-4200)*sign,y*sign)
            table=grounded('Waiting '+group+'/Table',required[3],xy(3370,830),64,0,True,width=105)
            for slot in (0,1,3):table.static_mesh_component.set_material(slot,u.load_asset(ARCHIVE+'MI_ArchiveTable'))
            for index,(x,y,yaw) in enumerate(((3215,755,-55),(3450,990,140)),1):
                a=grounded('Waiting '+group+'/Chair '+str(index),required[2],xy(x,y),83,yaw+(180 if sign<0 else 0),True)
                a.static_mesh_component.set_material(0,u.load_asset(ARCHIVE+'MI_ArchiveUpholstery'))
            for label,path,p,height,width in (
                ('Tablet','/Game/Cyberpunk_Room/Mesh/SM_Tablet',(3352,815),2.7,28),
                ('Reading','/Game/Cyberpunk_Room/Mesh/SM_Books_02',(3395,850),8,22),
                ('Water','/Game/Cyberpunk_Room/Mesh/SM_Bottle_01',(3355,855),17,7)):
                a=grounded('Waiting '+group+'/'+label,path,xy(*p),height,20,width=width)
                a.set_actor_location(a.get_actor_location()+u.Vector(0,0,64),False,True)
            # Copy the complete owned planter assembly; all source components stay.
            p=xy(3180,1040)
            source=one('Refine/CentralWelcomeArrival2/NE/Planter left')
            _,b=source.get_actor_bounds(False)
            planter=duplicate_at(source,'Waiting '+group+'/Planter',(p[0],p[1],b.z))
            tree=duplicate_at(one('Refine/Concept73/Waiting/Plant 1'),'Waiting '+group+'/Tree',(p[0],p[1],119.5))
            shrub=duplicate_at(one('Refine/Concept73/Waiting/Understory 1'),'Waiting '+group+'/Understory',(p[0],p[1],61.1))
            for a in (tree,shrub):a.set_actor_enable_collision(False)
            old=keep(one('Atrium_Bench_'+('0' if sign==1 else '3')))
            old.set_actor_hidden_in_game(True);old.set_actor_enable_collision(False)
        report.update(new_actors=len(state['new']),changed_originals=len(state['actors']),private_materials=[m.get_path_name() for m in state['private']],dry_run=False)
        return state,report
    except Exception:
        restore(u,state)
        raise


def restore(u,state):
    for c,materials in reversed(state['materials']):
        for i,m in enumerate(materials):c.set_material(i,m)
    for a,transform,hidden,collision in reversed(state['actors']):
        a.set_actor_transform(transform,False,True)
        a.set_actor_hidden_in_game(hidden);a.set_actor_enable_collision(collision)
    sub=u.get_editor_subsystem(u.EditorActorSubsystem)
    for a in reversed(state['new']):sub.destroy_actor(a)
