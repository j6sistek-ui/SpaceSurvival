"""Faint rear-tower haze and three decorative native cargo drones.

UE5.8 LocalFogVolumeSceneProxy uses max(scale)*500cm as a SPHERICAL radius.
LocalFogVolumeCommon.ush normalizes the full central radial optical depth to
RadialFogExtinction. These .02-.025 volumes have no height fog or emission.
No global atmosphere, exposure, light, globe or character changes are made.

Cargo motion uses SSOutpostAmbientActor's existing local route and bob. The
full owned Mech4 Blueprint is retained, uniformly fitted and attached to its
moving DroneMesh. Payloads/tethers follow that same component. No asset saves.
"""
import json
import math
import os
from pathlib import Path

TARGET = '/Game/OutpostSandbox/L_AsteroidOutpost'
MARKER = 'OutpostSkylineAtmosphere'
DRONE = '/Game/P1toP5_Bundle/P5_FruitSeller/Blueprints/BP_Mech4_FlyingDroid'
CARGO = '/Game/P1toP5_Bundle/P5_FruitSeller/Meshes/SM_Props_Box03.SM_Props_Box03'
FOG = [
    {'name': 'South service haze', 'center': [11600, -3500, 4250], 'radius': 1100, 'density': .025},
    {'name': 'Command rear haze', 'center': [11400, 0, 3650], 'radius': 900, 'density': .020},
    {'name': 'North service haze', 'center': [11600, 3700, 5050], 'radius': 1100, 'density': .025},
]
ROUTES = [
    {'name': 'South tower freight', 'speed': 260, 'phase': .4,
     'points': [[10000,-5000,4520], [11700,-4300,4550], [11700,-2400,4530], [10000,-2600,4510]]},
    {'name': 'North tower freight', 'speed': 240, 'phase': 1.1,
     'points': [[10200,2550,5350], [11800,2700,5380], [11800,5200,5350], [10200,5000,5350]]},
    {'name': 'Cross district freight', 'speed': 300, 'phase': 2.0,
     'points': [[9900,-1800,6100], [11400,-300,6150], [11400,1800,6100], [9800,700,6100]]},
]
# Rotation-invariant envelope includes native 280cm-wide drone, 70cm-high
# payload, tethers, +/-8cm bob and the native +/-3deg pitch/4deg roll.
ENVELOPE = 350.
REAR_MASSIF = [9950, -7250, -4850, 16450, 8250, 3650]
GALLERY = [2900, -4400, 520, 4300, -2400, 1100]


def segment_hits_box(start, end, bounds, padding=0.):
    """Exact closed segment versus padded AABB; avoids missing between samples."""
    enter, leave = 0., 1.
    for axis in range(3):
        low, high = bounds[axis]-padding, bounds[axis+3]+padding
        delta = end[axis]-start[axis]
        if abs(delta) < 1e-9:
            if not low <= start[axis] <= high:
                return False
        else:
            a, b = (low-start[axis])/delta, (high-start[axis])/delta
            enter, leave = max(enter, min(a,b)), min(leave, max(a,b))
            if enter > leave:
                return False
    return True


def audit(catalog):
    import OutpostSkyline
    from OutpostSkylineLighting import bounds
    architecture = OutpostSkyline.build(catalog)
    obstacles = [(row['name'], bounds(row)) for row in architecture]
    obstacles += [('Rear massif', REAR_MASSIF), ('Observation gallery', GALLERY),
                  ('Approved globe and halo', [3250,-950,200,5150,950,2200])]
    failures, samples = [], 0
    for fog in FOG:
        if fog['center'][0]-fog['radius'] < 10500 or fog['center'][2]-fog['radius'] < 2500:
            failures.append(fog['name']+': haze escapes rear upper background')
        if not 0 < fog['density'] <= .025:
            failures.append(fog['name']+': density exceeds faint-haze cap')
    for route in ROUTES:
        points = route['points']
        for a,b in zip(points, points[1:]+points[:1]):
            for label, box in obstacles:
                if segment_hits_box(a,b,box,ENVELOPE):
                    failures.append(route['name']+': envelope crosses '+label)
            steps = max(1, math.ceil(math.dist(a,b)/100.))
            for step in range(steps+1):
                point = [a[i]+(b[i]-a[i])*step/steps for i in range(3)]
                samples += 1
                if point[0]-ENVELOPE < 9400 or point[2]-ENVELOPE < 4000:
                    failures.append(route['name']+': enters inhabited station envelope')
    # Even if all route legs overlap in XY, their vertical lanes cannot touch.
    for i, route in enumerate(ROUTES):
        for other in ROUTES[i+1:]:
            gap = min(p[2] for p in other['points'])-max(p[2] for p in route['points'])
            if gap < 2*ENVELOPE:
                failures.append('Freight vertical lanes are insufficiently separated')
    return {'source_geometry_only': True, 'skyline_parts_checked': len(architecture),
            'route_segments': sum(len(r['points']) for r in ROUTES), 'sample_points': samples,
            'conservative_drone_payload_radius_cm': ENVELOPE, 'failures': failures,
            'fog_max_combined_central_optical_depth': sum(f['density'] for f in FOG),
            'fog_max_combined_central_opacity': 1-math.exp(-sum(f['density'] for f in FOG))}


def apply(api):
    """Idempotent placed-actor pass; caller owns saving, native motion and visual review."""
    u, eas = api['u'], api['EAS']
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if api.get('TARGET') != TARGET or world.get_path_name().split('.')[0] != TARGET:
        raise RuntimeError('Skyline atmosphere requires the private outpost map')
    root = Path(api['ROOT'])
    catalog = json.loads(Path(os.environ.get('SS_PREFAB_CATALOG',
        str(root/'Artifacts/PrefabLibrary/catalog.json'))).read_text(encoding='utf-8'))
    evidence = audit(catalog)
    if evidence['failures']:
        raise RuntimeError('; '.join(evidence['failures']))
    from OutpostGeometryUtils import mesh_union, fit_blueprint_from_geometry
    blueprint, carton = api['load'](DRONE), api['load'](CARGO)
    cube = api['load']('/Engine/BasicShapes/Cube.Cube')
    cylinder = api['load']('/Engine/BasicShapes/Cylinder.Cylinder')
    graphite = api['load']('/Game/OutpostSandbox/Materials/M_OutpostGraphite')
    if not all((blueprint, carton, cube, cylinder, graphite)):
        raise RuntimeError('Required native drone, shipping carton or tether assets missing')
    for actor in list(eas.get_all_level_actors()):
        if MARKER in [str(t) for t in actor.tags]:
            if not eas.destroy_actor(actor):
                raise RuntimeError('Cannot replace prior skyline atmosphere actor')
    created, fog_report, drones = [], [], []

    def mark(actor, name):
        actor.set_actor_label('SkylineAtmosphere/'+name)
        actor.set_folder_path('SkylineAtmosphere')
        actor.tags = list(actor.tags)+[u.Name(MARKER), u.Name('OutpostAuthored')]
        created.append(actor)
        return actor

    def no_physics(actor):
        actor.set_actor_enable_collision(False)
        for component in actor.get_components_by_class(u.SceneComponent):
            component.set_mobility(u.ComponentMobility.MOVABLE)
            if isinstance(component, u.PrimitiveComponent):
                component.set_simulate_physics(False)
                component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
                component.set_cast_shadow(False)
            if isinstance(component, (u.AudioComponent, u.NiagaraComponent)):
                component.deactivate()
                component.set_visibility(False)
            if isinstance(component, u.LightComponent):
                component.set_visibility(False)

    def attach(actor, parent):
        if not actor.attach_to_component(parent, u.Name(''), u.AttachmentRule.KEEP_WORLD,
                u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, False):
            raise RuntimeError('Cargo presentation attachment failed')

    def static(name, mesh, center, size, parent, material=None):
        actor = mark(eas.spawn_actor_from_class(u.StaticMeshActor, u.Vector()), name)
        c = actor.static_mesh_component
        c.set_static_mesh(mesh)
        b = mesh.get_bounds()
        scale = [size[i]/(2*getattr(b.box_extent, 'xyz'[i])) for i in range(3)]
        actor.set_actor_scale3d(u.Vector(*scale))
        offset = [getattr(b.origin, 'xyz'[i])*scale[i] for i in range(3)]
        actor.set_actor_location(u.Vector(*[center[i]-offset[i] for i in range(3)]), False, False)
        if material:
            c.set_material(0, material)
        no_physics(actor)
        attach(actor, parent)
        return actor

    try:
        for spec in FOG:
            actor = mark(eas.spawn_actor_from_class(u.LocalFogVolume, u.Vector(*spec['center'])), spec['name'])
            radius = spec['radius']
            actor.set_actor_scale3d(u.Vector(radius/500., radius/500., radius/500.))
            c = actor.get_component_by_class(u.LocalFogVolumeComponent)
            if not c:
                raise RuntimeError('LocalFogVolume native component is unavailable')
            values = {'radial_fog_extinction': spec['density'], 'height_fog_extinction': 0.,
                      'height_fog_falloff': 1000., 'height_fog_offset': 0., 'fog_phase_g': .05,
                      'fog_start_distance': 0., 'fog_sort_priority': -10}
            for key,value in values.items():
                c.set_editor_property(key,value)
            c.set_editor_property('fog_albedo', u.LinearColor(.32,.40,.48,1))
            c.set_editor_property('fog_emissive', u.LinearColor(0,0,0,1))
            actual = {key: c.get_editor_property(key) for key in values}
            if any(abs(float(actual[key])-float(value)) > 1e-6 for key,value in values.items()):
                raise RuntimeError('Fog property readback failed')
            fog_report.append(dict(spec, properties=actual, scale=radius/500.))

        for index,route in enumerate(ROUTES):
            position = route['points'][0]
            carrier = mark(eas.spawn_actor_from_class(u.SSOutpostAmbientActor, u.Vector(*position)), route['name'])
            no_physics(carrier)
            carrier.set_editor_property('drone', True)
            carrier.set_editor_property('travel_speed', route['speed'])
            carrier.set_editor_property('pause_at_waypoint', .8)
            carrier.set_editor_property('bob_amplitude', 8.)
            carrier.set_editor_property('phase_offset', route['phase'])
            carrier.set_editor_property('route_points', [u.Vector(*[p[i]-position[i] for i in range(3)]) for p in route['points']])
            visual = mark(eas.spawn_actor_from_class(blueprint.generated_class(),u.Vector()), route['name']+'/Owned droid')
            visual.set_actor_tick_enabled(False)
            no_physics(visual)
            for c in visual.get_components_by_class(u.ActorComponent):
                c.set_component_tick_enabled(False)
            _, ext = mesh_union(visual)
            height = ext.z*2*280./(max(ext.x,ext.y,ext.z)*2)
            fitted = fit_blueprint_from_geometry(visual, position, height)
            attach(visual, carrier.drone_mesh)
            # Four short dark suspension cables connect the underside to a
            # uniformly scaled owned, labelled shipping carton; no fake crate.
            _, ext = mesh_union(visual)
            underside = position[2]-ext.z+3.
            bounds = carton.get_bounds()
            cargo_scale = 70./(bounds.box_extent.z*2)
            cargo_size = [getattr(bounds.box_extent,a)*2*cargo_scale for a in 'xyz']
            top = underside-55.
            cargo_center = [position[0],position[1],top-cargo_size[2]/2]
            cargo = static(route['name']+'/Shipping carton',carton,cargo_center,cargo_size,carrier.drone_mesh)
            for x in (-cargo_size[0]*.28,cargo_size[0]*.28):
                for y in (-cargo_size[1]*.28,cargo_size[1]*.28):
                    static(route['name']+'/Tether '+str((round(x),round(y))),cylinder,
                           [position[0]+x,position[1]+y,top+27.5],[2.5,2.5,55.],carrier.drone_mesh,graphite)
            for side in (-1,1):
                x=position[0]+side*cargo_size[0]*.28
                for z in (cargo_center[2]-cargo_size[2]/2,cargo_center[2]+cargo_size[2]/2):
                    static(route['name']+'/Strap horizontal '+str((side,z)),cube,
                           [x,position[1],z],[3.5,cargo_size[1]+2,2.],carrier.drone_mesh,graphite)
                for y in (-1,1):
                    static(route['name']+'/Strap side '+str((side,y)),cube,
                           [x,position[1]+y*(cargo_size[1]/2+.5),cargo_center[2]],
                           [3.5,2.,cargo_size[2]],carrier.drone_mesh,graphite)
            # The envelope is rotation invariant; include the lowest loaded
            # carton corner and spare margin for bob and native visual tilt.
            low_radius = math.sqrt((cargo_size[0]/2)**2+(cargo_size[1]/2)**2+
                                   (position[2]-cargo_center[2]+cargo_size[2]/2)**2)
            actual_radius = max(math.sqrt(ext.x**2+ext.y**2+ext.z**2),low_radius)+25.
            if actual_radius > ENVELOPE:
                raise RuntimeError('Native cargo exceeds proven route envelope')
            drones.append(dict(route, blueprint=DRONE, native_fit=fitted,
                               payload=CARGO,payload_size_cm=cargo_size,envelope_actual_cm=actual_radius,
                               no_collision=True, source_forward_axis='Preserved vendor Z-up; near-radial flying droid'))
    except Exception:
        # Roll back only newly created tagged actors; original map stays unsaved.
        for actor in reversed(created):
            eas.destroy_actor(actor)
        raise
    result={'audit':evidence,'fog':fog_report,'drones':drones,'created_actors':len(created),
            'scope':'Local rear background haze and native cargo motion only; no global environment changes',
            'native_render_and_runtime_motion':'PENDING_LEAD_VALIDATION'}
    (Path(api['OUT'])/'skyline-atmosphere.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result
