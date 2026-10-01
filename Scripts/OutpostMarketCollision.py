"""Read-only saved-reload inspection of the three failed native market probes.

No collision mutation, physics refresh, reconstruction, actor spawn or save.
Call inspect(api) immediately after reload and after the lead's render warmup;
compare flags and unchanged isolated Pawn traces before selecting a repair.
"""
TARGET = '/Game/OutpostSandbox/L_AsteroidOutpost'
ROOT = '/Game/P1toP5_Bundle/P5_FruitSeller/Meshes/'
TARGETS = (
    ('NorthCommerce','BP_ISM_Storage12','InstancedStaticMesh5','SM_Props_ConstructionPart97_Wood'),
    ('SouthBotany','BP_ISM_Storage12','InstancedStaticMesh5','SM_Props_ConstructionPart97_Wood'),
    ('NorthCommerce','BP_ISM_Structure_V4','ISM_Building_StructureBase_V1','SM_Building_StructureBase_V1'),
)


def inspect(api):
    """Return JSON-safe native flags and the exact existing three target tests."""
    import datetime
    import unreal as u
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name().split('.')[0] != TARGET:
        raise RuntimeError('Market collision inspection requires the saved private map')
    actors = list(api['EAS'].get_all_level_actors())
    by_name = {}
    for actor in actors:
        by_name.setdefault(actor.get_actor_label(),[]).append(actor)

    def point(value):
        return [float(value.x),float(value.y),float(value.z)]

    def optional_call(obj, name):
        method = getattr(obj,name,None)
        if method is None:
            return 'Unavailable in Python binding'
        try:
            result = method()
            return result if isinstance(result,(str,bool,int,float)) else str(result)
        except Exception as error:
            return 'Unavailable: '+str(error)

    def property_value(obj,name):
        try:
            result = obj.get_editor_property(name)
            return result if isinstance(result,(str,bool,int,float)) else str(result)
        except Exception as error:
            return 'Unavailable: '+str(error)

    result = {'map':TARGET,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'read_only':True,'targets':[],'scope':'Unchanged selected component probes; not all market collision'}
    for block,suffix,component_name,mesh_name in TARGETS:
        label = 'MarketNative/'+block+'/'+suffix
        found = by_name.get(label,[])
        if len(found) != 1:
            raise RuntimeError('Missing or duplicate market target: '+label)
        actor = found[0]
        matches = [c for c in actor.get_components_by_class(u.StaticMeshComponent)
                   if c.get_name() == component_name]
        if len(matches) != 1:
            raise RuntimeError('Missing or duplicate target component: '+label+'/'+component_name)
        component = matches[0]
        expected_mesh = ROOT+mesh_name+'.'+mesh_name
        if (not isinstance(component,u.InstancedStaticMeshComponent) or
                not component.static_mesh or component.static_mesh.get_path_name() != expected_mesh or
                component.get_instance_count() < 1):
            raise RuntimeError('Target is not the expected populated native ISM: '+label)
        body = component.static_mesh.get_editor_property('body_setup')
        simple = {}
        if body:
            aggregate = body.get_editor_property('agg_geom')
            simple = {name:len(aggregate.get_editor_property(name)) for name in
                      ('convex_elems','box_elems','sphere_elems','sphyl_elems')}
        parent = component.get_attach_parent()
        row = {'actor':label,'actor_class':actor.get_class().get_path_name(),
            'actor_collision_enabled':optional_call(actor,'get_actor_enable_collision'),
            'component':component_name,'component_path':component.get_path_name(),
            'creation_method':property_value(component,'creation_method'),
            'collision_enabled':str(component.get_collision_enabled()),
            'collision_profile':str(component.get_collision_profile_name()),
            'pawn_response':str(component.get_collision_response_to_channel(u.CollisionChannel.ECC_PAWN)),
            'object_type':str(component.get_collision_object_type()),
            'registered':optional_call(component,'is_registered'),
            'physics_state_created':optional_call(component,'is_physics_state_created'),
            'mobility':property_value(component,'mobility'),
            'always_create_physics_state':property_value(component,'always_create_physics_state'),
            'parent':parent.get_name() if parent else None,
            'absolute_location':property_value(component,'absolute_location'),
            'absolute_rotation':property_value(component,'absolute_rotation'),
            'absolute_scale':property_value(component,'absolute_scale'),
            'asset':expected_mesh,'instances':component.get_instance_count(),
            'body_setup':body.get_path_name() if body else None,'simple_geometry':simple,
            'collision_trace_flag':property_value(body,'collision_trace_flag') if body else None,
            'instance0_world':{},'rays':[]}
        body_instance = component.get_editor_property('body_instance')
        row['body_instance_flags'] = {name:property_value(body_instance,name) for name in
            ('collision_profile_name','collision_enabled','object_type','simulate_physics')}
        transform = component.get_instance_transform(0,world_space=True)
        row['instance0_world'] = {'location':point(transform.translation),
            'scale':point(transform.scale3d),'rotation':str(transform.rotation)}
        bounds = component.static_mesh.get_bounds()
        isolated = [other for other in actors if other != actor]
        for axis in range(3):
            origin = point(bounds.origin)
            extent = point(bounds.box_extent)
            start,end = list(origin),list(origin)
            start[axis] -= extent[axis]+10
            end[axis] += extent[axis]+10
            start = u.MathLibrary.transform_location(transform,u.Vector(*start))
            end = u.MathLibrary.transform_location(transform,u.Vector(*end))
            native_hit = u.SystemLibrary.line_trace_single_by_profile(world,start,end,
                'Pawn',False,isolated,u.DrawDebugTrace.NONE,True)
            fields = native_hit.to_tuple() if native_hit is not None else None
            hit = None
            if fields and fields[0]:
                hit = {'actor':fields[9].get_actor_label() if fields[9] else None,
                    'component':fields[10].get_name() if fields[10] else None,
                    'point':point(fields[5]),'normal':point(fields[7]),
                    'initial_overlap':bool(fields[1])}
            row['rays'].append({'local_axis':axis,'start':point(start),'end':point(end),'hit':hit})
        row['probe_pass'] = any(r['hit'] and r['hit']['actor']==label and
            r['hit']['component']==component_name for r in row['rays'])
        result['targets'].append(row)
    return result
