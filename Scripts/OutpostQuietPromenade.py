"""Calm owned floor panels in the central eight-metre promenade strip only.

Call after OutpostSurfaceFinish in the saved private map. Existing decorative
tiles remain hidden for provenance; Ground/Market remains the sole collision
surface. Guidance, vendor assemblies, furniture, NPCs and edge decking stay.
"""
TARGET = '/Game/OutpostSandbox/L_AsteroidOutpost'
SOURCE = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Meshes/SM_UniversalPanel400X200_V2.SM_UniversalPanel400X200_V2'
PANEL = '/Game/StarterBundle/ModularScifiProps/Meshes/SM_Floor_A.SM_Floor_A'
PREFIX = 'QuietPromenade/'
TAG = 'OutpostQuietPromenade'
REPLACED_TAG = 'OutpostQuietPromenade:ReplacedCentralTile'
LOW = (-1500., -400., -18.)
HIGH = (2600., 400., 0.)


def source_tiles():
    """Exact two existing central rows of floor_rect('Market',550,0,4100,4800)."""
    rows = []
    for ix in range(20):
        for iy in (5, 6):
            rows.append({'name':'Market/Deck %02d-%02d' % (ix,iy),
                'center':[-1500.+(ix+.5)*205., -2400.+(iy+.5)*400., -9.],
                'size':[205.,400.,18.]})
    return rows


def layout():
    """Near-native 315x400cm panels tile the exact existing walking strip."""
    nx, ny = 13, 2
    size = [(HIGH[0]-LOW[0])/nx, (HIGH[1]-LOW[1])/ny, HIGH[2]-LOW[2]]
    return [{'name':PREFIX+'Panel %02d-%02d' % (ix,iy),
        'center':[LOW[0]+(ix+.5)*size[0],LOW[1]+(iy+.5)*size[1],-9.],
        'size':list(size)} for ix in range(nx) for iy in range(ny)]


def apply(api):
    """Replace visual tiles idempotently; do not save map or modify collision."""
    import unreal as u
    from OutpostGeometryUtils import mesh_union
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name().split('.')[0] != TARGET or api.get('TARGET') != TARGET:
        raise RuntimeError('Quiet promenade requires the saved private outpost')
    eas = api['EAS']
    actors = list(eas.get_all_level_actors())
    labels = {}
    for actor in actors:
        labels.setdefault(actor.get_actor_label(),[]).append(actor)

    def one(label):
        found = labels.get(label,[])
        if len(found) != 1 or 'OutpostAuthored' not in map(str,found[0].tags):
            raise RuntimeError('Missing, ambiguous or unowned promenade source: '+label)
        return found[0]

    def component(actor, path):
        components = list(actor.get_components_by_class(u.StaticMeshComponent))
        if (len(components) != 1 or not components[0].static_mesh or
                components[0].static_mesh.get_path_name() != path):
            raise RuntimeError('Unexpected promenade geometry: '+actor.get_actor_label())
        return components[0]

    def bounds(actor):
        center, extent = mesh_union(actor)
        return ([getattr(center,axis)-getattr(extent,axis) for axis in ('x','y','z')],
                [getattr(center,axis)+getattr(extent,axis) for axis in ('x','y','z')])

    def matches_bounds(actor, expected_low, expected_high):
        lo,hi = bounds(actor)
        error = max(abs(a-b) for a,b in zip(lo+hi,list(expected_low)+list(expected_high)))
        if error > .05:
            raise RuntimeError('Promenade bounds changed: '+actor.get_actor_label())
        return lo,hi,error

    ground = one('Ground/Market')
    ground_component = component(ground,'/Engine/BasicShapes/Cube.Cube')
    if (ground_component.get_collision_enabled() != u.CollisionEnabled.QUERY_AND_PHYSICS or
            str(ground_component.get_collision_profile_name()) != 'BlockAll'):
        raise RuntimeError('Ground/Market no longer provides the expected solid floor')
    ground_low,ground_high,_ = matches_bounds(ground,(-1500.,-2400.,-48.),(2600.,2400.,0.))
    originals = []
    selected_names = {row['name'] for row in source_tiles()}
    for actor in actors:
        if REPLACED_TAG in map(str,actor.tags) and actor.get_actor_label() not in selected_names:
            raise RuntimeError('A tile outside the walking strip was marked replaced')
    for row in source_tiles():
        actor = one(row['name'])
        static = component(actor,SOURCE)
        if static.get_collision_enabled() != u.CollisionEnabled.NO_COLLISION:
            raise RuntimeError('Decorative source tile has collision; refusing to alter it')
        if static.get_editor_property('cast_hidden_shadow'):
            raise RuntimeError('Source floor unexpectedly casts hidden shadows')
        if not static.get_editor_property('visible') and REPLACED_TAG not in map(str,actor.tags):
            raise RuntimeError('Unmarked source tile is already hidden: '+row['name'])
        lo = [row['center'][i]-row['size'][i]/2 for i in range(3)]
        hi = [row['center'][i]+row['size'][i]/2 for i in range(3)]
        matches_bounds(actor,lo,hi)
        originals.append((actor,static))

    native = api['load'](PANEL)
    if not isinstance(native,u.StaticMesh):
        raise RuntimeError('Owned promenade panel is not a static mesh')
    box = native.get_bounds()
    native_size = [box.box_extent.x*2,box.box_extent.y*2,box.box_extent.z*2]
    if any(abs(a-b) > .1 for a,b in zip(native_size,(320.,360.,20.69666))):
        raise RuntimeError('Owned floor native dimensions changed')
    materials = list(native.static_materials)
    if (len(materials) != 2 or any(not m.material_interface for m in materials) or
            tuple(m.material_interface.get_name() for m in materials) != ('MI_Base_Dark','MI_Base_Light')):
        raise RuntimeError('Owned floor clean material assignments changed')
    rows = layout()
    names = {row['name'] for row in rows}
    existing = {}
    for actor in actors:
        if not (actor.get_actor_label().startswith(PREFIX) or TAG in map(str,actor.tags)):
            continue
        name = actor.get_actor_label()
        if name not in names or TAG not in map(str,actor.tags) or name in existing:
            raise RuntimeError('Unknown or duplicate quiet promenade actor: '+name)
        static = component(actor,PANEL)
        if static.get_collision_enabled() != u.CollisionEnabled.NO_COLLISION:
            raise RuntimeError('Existing quiet floor unexpectedly has collision')
        existing[name] = actor

    # All source, support, asset and ownership checks above precede mutation.
    for actor,static in originals:
        static.set_visibility(False,False)
        actor.set_actor_hidden_in_game(True)
        if REPLACED_TAG not in map(str,actor.tags):
            actor.tags = list(actor.tags)+[u.Name(REPLACED_TAG)]
    placements = []
    for row in rows:
        actor = existing.get(row['name'])
        created = actor is None
        if created:
            actor = eas.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0))
            if actor is None:
                raise RuntimeError('Could not spawn quiet promenade '+row['name'])
            actor.set_actor_label(row['name'])
            actor.set_folder_path('QuietPromenade')
            actor.tags = [u.Name('OutpostAuthored'),u.Name(TAG)]
            actor.static_mesh_component.set_static_mesh(native)
        static = actor.static_mesh_component
        static.set_collision_profile_name('NoCollision')
        static.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        static.set_simulate_physics(False)
        for index,material in enumerate(materials):
            static.set_material(index,material.material_interface)
        scale = [row['size'][i]/native_size[i] for i in range(3)]
        native_origin = [box.origin.x,box.origin.y,box.origin.z]
        position = [row['center'][i]-native_origin[i]*scale[i] for i in range(3)]
        actor.set_actor_rotation(u.Rotator(pitch=0,yaw=0,roll=0),False)
        actor.set_actor_scale3d(u.Vector(*scale))
        actor.set_actor_location(u.Vector(*position),False,False)
        actor.set_actor_hidden_in_game(False)
        static.set_visibility(True,False)
        lo = [row['center'][i]-row['size'][i]/2 for i in range(3)]
        hi = [row['center'][i]+row['size'][i]/2 for i in range(3)]
        actual_low,actual_high,error = matches_bounds(actor,lo,hi)
        if abs(actual_high[2]) > .05:
            raise RuntimeError('Quiet floor top no longer matches the walking surface')
        placements.append(dict(row,created=created,scale=scale,location=position,
            actual_low_cm=actual_low,actual_high_cm=actual_high,native_bounds_error_cm=error))
    # Confirm the supporting floor remained unchanged through this operation.
    matches_bounds(ground,ground_low,ground_high)
    return {'candidate':'Quiet central promenade walking strip','asset':PANEL,
        'native_dimensions_cm':native_size,
        'native_materials':[m.material_interface.get_path_name() for m in materials],
        'strip_low_cm':list(LOW),'strip_high_cm':list(HIGH),
        'source_tiles_retained_hidden':len(originals),'clean_panels':len(rows),
        'created_panels':len(rows)-len(existing),'placements':placements,
        'ground_actor':'Ground/Market','ground_collision_unchanged':True,
        'new_collision_components':0,'deleted_actors':0,'vendor_assemblies_changed':False,
        'guidance_changed':False,'npcs_changed':False,'map_saved':False,
        'validation':'Native transformed bounds checked; appearance pending same-view capture'}
