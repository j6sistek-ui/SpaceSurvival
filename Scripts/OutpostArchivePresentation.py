"""Local archive and projected trim presentation; private outpost map only."""
import json
import math
import itertools

TARGET='/Game/OutpostSandbox/L_AsteroidOutpost'
REAR_PREFIX='Welcome/Reverse information/'


def apply(api):
    u=api['u']
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name().split('.')[0] != TARGET:
        raise RuntimeError('Archive presentation requires the saved private outpost')
    eas=api['EAS']
    by_label={a.get_actor_label():a for a in eas.get_all_level_actors()}
    globe=by_label['Atrium/Planetary archive/World']
    from OutpostGeometryUtils import mesh_union
    center,extent=mesh_union(globe)
    if max(abs(v-650) for v in (extent.x,extent.y,extent.z))>1:
        raise RuntimeError('Unexpected archive globe diameter')
    delta=u.Vector(4200,0,1170)-center
    globe.set_actor_location(globe.get_actor_location()+delta,False,False)
    halo=by_label['Atrium/Orbital halo']
    hc,he=mesh_union(halo)
    halo.set_actor_location(halo.get_actor_location()+u.Vector(0,0,560-hc.z),False,False)
    import OutpostPlanetDisplay
    globe.static_mesh_component.set_material(0,OutpostPlanetDisplay.build(api))
    for name,color,strength,opacity in [
        ('Cyan',(.08,.68,1),6,None),('Amber',(1,.37,.06),5,None),
        ('Violet',(.45,.12,1),4,None),('Hologram',(.05,.58,1),6,.4)]:
        api['material']('M_Outpost'+name,color,emission=strength,opacity=opacity)
    # Both approach directions receive readable local information. The native
    # screen shell remains, with no duplicated coplanar mesh or new blocker.
    headings=['WAYFARER EXCHANGE','FLIGHT ENGINEERING','CREW ARCHIVE','OPERATIONS',
              'SURVIVAL DEPARTURES','OBSERVATION GALLERY','MARKET / BERTHS']
    for actor in list(eas.get_all_level_actors()):
        if actor.get_actor_label().startswith(REAR_PREFIX):
            if 'OutpostArchiveReverse' not in map(str,actor.tags):
                raise RuntimeError('Reverse information label occupied by unowned actor')
            eas.destroy_actor(actor)
    for i,title in enumerate(headings):
        angle=22.5+i*45
        rad=math.radians(angle); nx,ny=math.cos(rad),math.sin(rad)
        x,y=4200+1040*nx,1040*ny
        display=by_label['Welcome/'+str(i+1)+'/Display']
        depths=[]
        for component in display.get_components_by_class(u.StaticMeshComponent):
            if not component.static_mesh: continue
            b=component.static_mesh.get_bounds()
            transforms=[component.get_instance_transform(k,world_space=True)
                        for k in range(component.get_instance_count())] if isinstance(component,u.InstancedStaticMeshComponent) else [component.get_world_transform()]
            for transform in transforms:
                for signs in itertools.product((-1,1),repeat=3):
                    v=b.origin+u.Vector(b.box_extent.x*signs[0],b.box_extent.y*signs[1],b.box_extent.z*signs[2])
                    q=u.MathLibrary.transform_location(transform,v)
                    depths.append((q.x-x)*nx+(q.y-y)*ny)
        if not depths: raise RuntimeError('Archive display has no geometry')
        for side,depth,yaw in [('Inward',min(depths)-.8,angle+180),('Outward',max(depths)+.8,angle)]:
            actor=api['text'](REAR_PREFIX+str(i+1)+'/'+side,title+'\nINFORMATION / '+str(i+1),
                              (x+nx*depth,y+ny*depth,205),yaw,7,(140,225,255))
            api['tag'](actor,'OutpostArchiveReverse')
    result={'globe_diameter_cm':1300,'globe_center_cm':[4200,0,1170],
            'globe_lowest_surface_cm':520,'halo_center_z_cm':560,
            'information_kiosks':7,'information_faces':14,'exposure_changed':False,
            'collision_changed':False,'global_environment_changed':False}
    (api['OUT']/'archive-presentation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result
