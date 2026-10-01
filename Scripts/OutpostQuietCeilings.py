"""Replace only two central decorative ceiling fields with owned clean panels.

Call apply(api) after OutpostSurfaceFinish in the saved private outpost. Keep
the perimeter Genesis panels, structural slabs, observation floor/roof, cables,
pendant fixtures and every collision component. The original central actors
remain in the level but stop rendering; no unknown actors are deleted. The
tray's authored relief faces down at pitch180, with its fitted bounds retained.
"""
TARGET = '/Game/OutpostSandbox/L_AsteroidOutpost'
SOURCE = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Meshes/SM_CeilingPanel400X200_V1.SM_CeilingPanel400X200_V1'
PANEL = '/Game/StarterBundle/ModularScifiProps/Meshes/SM_Ceiling_B.SM_Ceiling_B'
PREFIX = 'QuietCeiling/'
TAG = 'OutpostQuietCeiling'
REPLACED_TAG = 'OutpostQuietCeiling:ReplacedCentralPanel'
ROOMS = {'Engineering': (4200, -3400, 2600, 2200),
         'Operations': (7800, 0, 2800, 2600)}


def source_grid(room):
    """Exact existing room() grid; the outside row/column is never replaced."""
    x, y, width, depth = ROOMS[room]
    xs = list(range(int(x-width/2+100), int(x+width/2), 200))
    ys = list(range(int(y-depth/2+200), int(y+depth/2), 400))
    return xs, ys


def fitted_tiles(room, low, high):
    """Fit larger calm tiles inside the measured central field, without gaps."""
    width, depth, height = [high[i]-low[i] for i in range(3)]
    if min(width, depth, height) <= 0:
        raise ValueError('Quiet ceiling has invalid measured bounds')
    nx, ny = max(1, round(width/360.)), max(1, round(depth/400.))
    size = [width/nx, depth/ny, height]
    return [{'name': PREFIX+room+'/Panel %02d-%02d' % (ix, iy),
             'center': [low[0]+(ix+.5)*size[0], low[1]+(iy+.5)*size[1],
                        (low[2]+high[2])*.5],
             'size': list(size)} for ix in range(nx) for iy in range(ny)]


def apply(api):
    """Idempotent geometry replacement; caller owns map save and appearance QA."""
    import unreal as u
    from OutpostGeometryUtils import mesh_union
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name().split('.')[0] != TARGET or api.get('TARGET') != TARGET:
        raise RuntimeError('Quiet ceilings require the saved private outpost')
    eas = api['EAS']
    actors = list(eas.get_all_level_actors())
    native = api['load'](PANEL)
    if not isinstance(native, u.StaticMesh):
        raise RuntimeError('Owned quiet ceiling is not a static mesh')
    native_bounds = native.get_bounds()
    native_size = [native_bounds.box_extent.x*2, native_bounds.box_extent.y*2,
                   native_bounds.box_extent.z*2]
    if any(abs(a-b) > .1 for a, b in zip(native_size, (320., 360., 61.3481))):
        raise RuntimeError('Quiet panel native dimensions differ from inspected asset')
    materials = list(native.static_materials)
    if len(materials) != 2 or any(not slot.material_interface for slot in materials):
        raise RuntimeError('Quiet panel native material slots are incomplete')
    expected_materials = ('MI_Base_Light', 'MI_Base_Dark')
    if tuple(slot.material_interface.get_name() for slot in materials) != expected_materials:
        raise RuntimeError('Quiet panel native clean finishes changed')

    def bounds(actor):
        center, extent = mesh_union(actor)
        return ([getattr(center, axis)-getattr(extent, axis) for axis in ('x','y','z')],
                [getattr(center, axis)+getattr(extent, axis) for axis in ('x','y','z')])

    def one_static(actor, mesh_path):
        components = list(actor.get_components_by_class(u.StaticMeshComponent))
        if (len(components) != 1 or not components[0].static_mesh or
                components[0].static_mesh.get_path_name() != mesh_path):
            raise RuntimeError('Unexpected ceiling geometry: '+actor.get_actor_label())
        return components[0]

    planned, room_records, central = [], [], []
    # Validate both complete source grids and every existing owned replacement
    # before editing visibility or geometry. A hand-edited/missing panel rejects.
    for room in ROOMS:
        xs, ys = source_grid(room)
        found = {}
        for actor in actors:
            if not actor.get_actor_label().startswith(room+'/Ceiling panel'):
                continue
            if 'OutpostAuthored' not in map(str, actor.tags):
                raise RuntimeError('Unowned actor occupies authored ceiling namespace')
            component = one_static(actor, SOURCE)
            if component.get_collision_enabled() != u.CollisionEnabled.NO_COLLISION:
                raise RuntimeError('Original ceiling has collision; refusing to change it')
            if component.get_editor_property('cast_hidden_shadow'):
                raise RuntimeError('Original ceiling unexpectedly casts hidden shadows')
            position, rotation, scale = (actor.get_actor_location(), actor.get_actor_rotation(),
                                         actor.get_actor_scale3d())
            key = (round(position.x), round(position.y))
            if (key[0] not in xs or key[1] not in ys or key in found or
                    abs(position.x-key[0]) > .05 or abs(position.y-key[1]) > .05 or
                    abs(position.z-438.) > .05 or
                    max(abs(v) for v in (rotation.pitch, rotation.yaw, rotation.roll)) > .01 or
                    max(abs(v-1.) for v in (scale.x,scale.y,scale.z)) > .001):
                raise RuntimeError('Authored ceiling grid changed: '+actor.get_actor_label())
            lo, hi = bounds(actor)
            if abs(hi[0]-lo[0]-200.) > .1 or abs(hi[1]-lo[1]-400.) > .1:
                raise RuntimeError('Original ceiling mesh footprint changed')
            interior = key[0] in xs[1:-1] and key[1] in ys[1:-1]
            was_replaced = REPLACED_TAG in map(str, actor.tags)
            if was_replaced and not interior:
                raise RuntimeError('A perimeter tile was marked replaced unexpectedly')
            if not component.get_editor_property('visible') and not was_replaced:
                raise RuntimeError('An unmarked source ceiling is already hidden')
            found[key] = (actor, component, lo, hi, interior)
        if len(found) != len(xs)*len(ys):
            raise RuntimeError('Missing source ceiling grid in '+room)
        selected = [item for item in found.values() if item[4]]
        lo = [min(item[2][i] for item in selected) for i in range(3)]
        hi = [max(item[3][i] for item in selected) for i in range(3)]
        # All source panels must share one ceiling plane, not a stepped region.
        if any(max(abs(item[2][2]-lo[2]),abs(item[3][2]-hi[2])) > .05 for item in selected):
            raise RuntimeError('Central ceiling has inconsistent source heights')
        slabs = [actor for actor in actors if actor.get_actor_label() == room+'/Roof structure']
        if len(slabs) != 1 or 'OutpostAuthored' not in map(str,slabs[0].tags):
            raise RuntimeError('Missing or ambiguous supporting roof in '+room)
        slab_lo, slab_hi = bounds(slabs[0])
        if (slab_lo[2]-hi[2] < .25 or lo[0] < slab_lo[0] or lo[1] < slab_lo[1] or
                hi[0] > slab_hi[0] or hi[1] > slab_hi[1]):
            raise RuntimeError('Quiet field does not fit below its structural roof')
        rows = fitted_tiles(room, lo, hi)
        planned.extend(rows)
        central.extend((actor, component) for actor,component,_,_,_ in selected)
        room_records.append({'room':room,'source_panels':len(found),
            'perimeter_panels_preserved':len(found)-len(selected),
            'central_source_panels_hidden':len(selected),'clean_panels':len(rows),
            'field_low_cm':lo,'field_high_cm':hi,'original_underside_z':lo[2],
            'roof_bottom_z':slab_lo[2],'roof_clearance_cm':slab_lo[2]-hi[2]})

    names = {row['name'] for row in planned}
    existing = {}
    for actor in actors:
        if not (actor.get_actor_label().startswith(PREFIX) or TAG in map(str,actor.tags)):
            continue
        name = actor.get_actor_label()
        if name not in names or TAG not in map(str,actor.tags) or name in existing:
            raise RuntimeError('Unknown or duplicate quiet-ceiling actor: '+name)
        component = one_static(actor,PANEL)
        if component.get_collision_enabled() != u.CollisionEnabled.NO_COLLISION:
            raise RuntimeError('Existing quiet ceiling unexpectedly has collision')
        existing[name] = actor

    # Retain source actors for provenance/reversal, removing only their render.
    for actor, component in central:
        component.set_visibility(False,False)
        actor.set_actor_hidden_in_game(True)
        if REPLACED_TAG not in map(str,actor.tags):
            actor.tags = list(actor.tags)+[u.Name(REPLACED_TAG)]

    placements = []
    for row in planned:
        actor = existing.get(row['name'])
        created = actor is None
        if created:
            actor = eas.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0))
            if actor is None:
                raise RuntimeError('Could not spawn quiet ceiling '+row['name'])
            actor.set_actor_label(row['name'])
            actor.set_folder_path('QuietCeiling')
            actor.tags = [u.Name('OutpostAuthored'),u.Name(TAG)]
            actor.static_mesh_component.set_static_mesh(native)
        component = actor.static_mesh_component
        component.set_collision_profile_name('NoCollision')
        component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        component.set_simulate_physics(False)
        for index, slot in enumerate(materials):
            component.set_material(index,slot.material_interface)
        scale = [row['size'][i]/native_size[i] for i in range(3)]
        origin = [getattr(native_bounds.origin,axis) for axis in ('x','y','z')]
        # Native tray lips extend above its broad plane. Present that designed
        # relief below the roof, not the flat reverse. Rotate the scaled pivot
        # offset too; merely rotating the actor would displace the entire grid.
        offset = [-origin[0]*scale[0],origin[1]*scale[1],-origin[2]*scale[2]]
        position = [row['center'][i]-offset[i] for i in range(3)]
        actor.set_actor_rotation(u.Rotator(pitch=180,yaw=0,roll=0),False)
        actor.set_actor_scale3d(u.Vector(*scale))
        actor.set_actor_location(u.Vector(*position),False,False)
        actor.set_actor_hidden_in_game(False)
        component.set_visibility(True,False)
        lo,hi = bounds(actor)
        expected_lo = [row['center'][i]-row['size'][i]*.5 for i in range(3)]
        expected_hi = [row['center'][i]+row['size'][i]*.5 for i in range(3)]
        error = max(abs(a-b) for a,b in zip(lo+hi,expected_lo+expected_hi))
        if error > .05:
            raise RuntimeError('Quiet panel actual bounds failed: '+row['name'])
        placements.append(dict(row, created=created, scale=scale, rotation_pitch_yaw_roll=[180,0,0],
            location=position, actual_low_cm=lo, actual_high_cm=hi,
            native_bounds_error_cm=error))
    return {'candidate':'Clean central ceiling fields','asset':PANEL,
        'native_dimensions_cm':native_size,
        'native_materials':[slot.material_interface.get_path_name() for slot in materials],
        'rooms':room_records,'placements':placements,'new_panels':len(planned)-len(existing),
        'deleted_actors':0,'existing_collision_components_changed':0,'lights_changed':0,
        'structural_roofs_changed':False,'gallery_changed':False,'map_saved':False,
        'presentation':'Native tray relief faces down; native two-sided finish required',
        'validation':'Native transformed bounds checked; appearance pending same-view capture'}
