"""Raise three exact archive displays into a supported Operations status band.

The owned 300x100 frame/glass share their original pivot and face west. Their
Z295..395 band clears the measured ceiling underside at397.568; six small
native brackets overlap frame corners and that ceiling. Native banks, lighting,
graphics and all collision stay untouched. Caller owns capture and map save.
"""
TARGET = '/Game/OutpostSandbox/L_AsteroidOutpost'
P4 = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Meshes/'
BRACKET = '/Game/P1toP5_Bundle/P5_FruitSeller/Meshes/SM_Props_ConstructionPart119.SM_Props_ConstructionPart119'
PREFIX = 'Operations/Status band mounting/'
TAG = 'OutpostOperationsStatusBand'
X, BOTTOM, TOP = 8700., 295., 395.
Y_POSITIONS = (-650., 0., 650.)


def window(dimensions, part):
    suffix = '_V1_Part1' if part == 'Frame' else '_V2_Part2_DigitalWindow'
    name = 'SM_Window' + dimensions + suffix
    return P4 + name + '.' + name


def layout():
    """Native actor pivots, not arbitrary separately centered frame layers."""
    return [{'name': 'Operations/HoloArchive' + str(i),
             'location': [X, y, BOTTOM], 'dimensions': '300X100',
             'old_location': [9130., y, 150.]}
            for i, y in enumerate(Y_POSITIONS, 1)]


def apply(api):
    import unreal as u
    from OutpostGeometryUtils import mesh_union
    package = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world().get_path_name().split('.')[0]
    fresh = package.startswith('/Temp/Untitled') and api.get('TARGET') == TARGET
    if package != TARGET and not fresh:
        raise RuntimeError('Operations status band requires the private outpost')
    eas = api['EAS']
    actors = list(eas.get_all_level_actors())
    by_name = {}
    for actor in actors:
        by_name.setdefault(actor.get_actor_label(), []).append(actor)

    def bounds(actor):
        center, extent = mesh_union(actor)
        return ([getattr(center, axis)-getattr(extent, axis) for axis in ('x','y','z')],
                [getattr(center, axis)+getattr(extent, axis) for axis in ('x','y','z')])

    def one(name):
        found = by_name.get(name, [])
        if len(found) != 1 or 'OutpostAuthored' not in map(str, found[0].tags):
            raise RuntimeError('Missing, duplicate or unowned status-band actor: ' + name)
        return found[0]

    def static(actor):
        components = actor.get_components_by_class(u.StaticMeshComponent)
        if len(components) != 1 or not components[0].static_mesh:
            raise RuntimeError('Unexpected status-band geometry: ' + actor.get_actor_label())
        if components[0].get_collision_enabled() != u.CollisionEnabled.NO_COLLISION:
            raise RuntimeError('Refusing to change a colliding status display')
        return components[0]

    def pose_matches(actor, position):
        p, r, s = actor.get_actor_location(), actor.get_actor_rotation(), actor.get_actor_scale3d()
        observed = [p.x,p.y,p.z,r.pitch,r.yaw,r.roll,s.x,s.y,s.z]
        expected = list(position) + [0,0,0,1,1,1]
        return max(abs(a-b) for a,b in zip(observed, expected)) < .05

    native = {part: api['load'](window('300X100', part)) for part in ('Frame','AnimatedGlass')}
    bracket = api['load'](BRACKET)
    for asset in list(native.values()) + [bracket]:
        if not isinstance(asset, u.StaticMesh):
            raise RuntimeError('Status band requires its exact owned static meshes')
    frame_bounds = native['Frame'].get_bounds()
    frame_size = [getattr(frame_bounds.box_extent, axis)*2 for axis in ('x','y','z')]
    if max(abs(a-b) for a,b in zip(frame_size, (24.541985,300.,100.))) > .05:
        raise RuntimeError('Native 300x100 window axes or dimensions changed')
    if abs(frame_bounds.origin.z-frame_bounds.box_extent.z) > .05:
        raise RuntimeError('Native status frame no longer uses its bottom pivot')

    # Actual geometry confirms the candidate is forward of both equipment and
    # service trays. Do not use stale actor bounds or hide overlapping actors.
    clearance = []
    for bank in ('East Tracking','East Contracts'):
        group = [a for a in actors if a.get_actor_label().startswith('OperationsNative/'+bank+'/')]
        if len(group) < 100:
            raise RuntimeError('Complete native east bank is missing: ' + bank)
        lo = min(bounds(a)[0][0] for a in group if a.get_components_by_class(u.StaticMeshComponent))
        gap = lo-(X+frame_size[0]*.5)
        if gap < 40.:
            raise RuntimeError('Status frame overlaps the east bank/service geometry')
        clearance.append({'bank':bank,'nearest_geometry_x':lo,'frame_gap_cm':gap})

    ceilings = []
    for actor in actors:
        if not actor.get_actor_label().startswith(('QuietCeiling/Operations/','Operations/Ceiling panel')):
            continue
        components = actor.get_components_by_class(u.StaticMeshComponent)
        if len(components) == 1 and components[0].get_editor_property('visible'):
            ceilings.append((actor.get_actor_label(), *bounds(actor)))
    prepared, supports = [], []
    for row in layout():
        for part in ('Frame','AnimatedGlass'):
            actor = one(row['name']+'/'+part)
            component = static(actor)
            source = component.static_mesh.get_path_name()
            old = source == window('400X200',part) and pose_matches(actor,row['old_location'])
            current = source == window('300X100',part) and pose_matches(actor,row['location'])
            if not old and not current:
                raise RuntimeError('Status display was hand-edited; refusing migration: '+row['name'])
            prepared.append((row,part,actor,component,old,list(component.get_materials())))
        for side in (-1,1):
            y = row['location'][1] + side*144.
            ceiling = [(name,lo,hi) for name,lo,hi in ceilings
                       if lo[0] <= X <= hi[0] and lo[1] <= y <= hi[1]]
            if not ceiling or any(not 397. <= lo[2] <= 399. for _,lo,_ in ceiling):
                raise RuntimeError('Status-frame corner has no expected real ceiling mount')
            underside = min(lo[2] for _,lo,_ in ceiling)
            # The bracket overlaps the upper frame rail by12cm and embeds3cm
            # into the ceiling; its Y position is outside the digital inset.
            low_z, high_z = TOP-12., underside+3.
            supports.append({'name':PREFIX+row['name'].split('/')[-1]+'/'+str(side),
                'center':[X,y,(low_z+high_z)*.5],'size':[8.,8.,high_z-low_z],
                'ceiling':[name for name,_,_ in ceiling],'ceiling_underside':underside})
    support_names = {r['name'] for r in supports}
    for actor in actors:
        if actor.get_actor_label().startswith(PREFIX):
            if actor.get_actor_label() not in support_names or TAG not in map(str,actor.tags):
                raise RuntimeError('Unknown actor in status-band mounting namespace')
            if static(actor).static_mesh.get_path_name() != BRACKET:
                raise RuntimeError('Existing status-band bracket uses unexpected geometry')

    report = {'placements':[],'mountings':[],'east_bank_clearance':clearance,
              'source_frame_dimensions_cm':frame_size,'native_banks_unchanged':True,
              'no_new_lights':True,'collision_unchanged':True,'map_saved':False}
    for row,part,actor,component,old,materials in prepared:
        if old:
            component.set_static_mesh(native[part])
            if part == 'Frame':
                component.set_editor_property('override_materials', [])
                for slot, entry in enumerate(native[part].static_materials):
                    component.set_material(slot,api['balanced'](entry.material_interface))
            else:
                # Keep the selected native graph/private ratio-balanced image.
                for slot, material in enumerate(materials):
                    component.set_material(slot,material)
            actor.set_actor_location(u.Vector(*row['location']),False,False)
        tags = [tag for tag in actor.tags if str(tag) != 'OutpostMount:RearWall']
        if 'OutpostMount:Ceiling' not in map(str,tags):
            tags.append(u.Name('OutpostMount:Ceiling'))
        actor.tags = tags
        lo,hi = bounds(actor)
        if lo[0] < X-13 or hi[0] > X+13 or lo[2] < BOTTOM-.05 or hi[2] > TOP+.05:
            raise RuntimeError('Status display escaped its measured upper band')
        report['placements'].append({'name':actor.get_actor_label(),'migrated':old,
            'mesh':component.static_mesh.get_path_name(),'location':row['location'],
            'bounds_min':lo,'bounds_max':hi})
    for row in supports:
        existing = by_name.get(row['name'],[])
        if len(existing) > 1:
            raise RuntimeError('Duplicate status-band bracket')
        if existing:
            actor = existing[0]
            lo,hi = bounds(actor)
            expected = [row['center'][i]-row['size'][i]*.5 for i in range(3)] + [row['center'][i]+row['size'][i]*.5 for i in range(3)]
            if max(abs(a-b) for a,b in zip(lo+hi,expected)) > .05:
                raise RuntimeError('Existing status bracket was moved; refusing overwrite')
        else:
            actor = api['place'](row['name'],BRACKET,row['center'],size=row['size'],solid=False)
            actor.tags = list(actor.tags)+[u.Name(TAG),u.Name('OutpostMount:Ceiling')]
            lo,hi = bounds(actor)
        if lo[2] >= TOP or hi[2] <= row['ceiling_underside']:
            raise RuntimeError('Status bracket does not physically join frame and ceiling')
        report['mountings'].append(dict(row,bounds_min=lo,bounds_max=hi,created=not existing))
    report['validation'] = 'Exact actor/native geometry and real ceiling contact checks; rendered readability pending'
    return report
