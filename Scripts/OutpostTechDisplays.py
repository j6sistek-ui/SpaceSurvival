"""Native commercial mini-kits and framed holographic station displays.

Called by the lead author with build(globals()). No engine launch occurs here.
The market uses complete owned source actors, not individually grounded pieces.
Source floor Z203 is removed once; full rotations, scales, material overrides
and per-instance mesh transforms remain authored. Native animated materials and
Blueprint behavior stay active. Terrain, sky, movie cameras and vendor lighting
are excluded. Tangible structure and machinery use native mesh collision;
small wares, holograms and animated robots remain cosmetic. The station shell
supplies continuous walkable support. No vendor collision assets are modified.
"""
import json
import math
from pathlib import Path

P4 = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Meshes/'


def _rotate(point, yaw):
    angle = math.radians(yaw)
    c, s = math.cos(angle), math.sin(angle)
    return [point[0] * c - point[1] * s,
            point[0] * s + point[1] * c, point[2]]


def placement(record, block, pivot):
    """Compose a single uniform parent transform without altering child poses."""
    local = [record['location'][i] - pivot[i] for i in range(3)]
    aligned_center = _rotate([*block['source_aligned_center'], 0], -20)
    local = [local[i] - aligned_center[i] for i in range(3)]
    location = _rotate(local, block['yaw_delta'])
    scale = block['uniform_scale']
    location = [location[i] * scale + block['target'][i] for i in range(3)]
    rotation = list(record['rotation'])
    rotation[1] += block['yaw_delta']
    return location, rotation, [v * scale for v in record['scale']]


def build(api):
    """Return runtime placement receipt; api is the author module globals()."""
    import unreal as u

    eas, load, finish, raw = (api[k] for k in ('EAS', 'load', 'finish', 'raw'))
    data = json.loads(Path(__file__).with_name('OutpostMarketAssemblies.json').read_text(encoding='utf-8'))
    receipt = {'blocks': [], 'display_assemblies': [], 'source_map': data['source_map'],
               'structural_collision': {}, 'collision_attention': []}

    def transform(location, rotation, scale):
        result = u.Transform()
        result.translation = u.Vector(*location)
        result.rotation = u.Rotator(pitch=rotation[0], yaw=rotation[1], roll=rotation[2]).quaternion()
        result.scale3d = u.Vector(*scale)
        return result

    def restore_components(actor, record):
        available = {component.get_name(): component
                     for component in actor.get_components_by_class(u.StaticMeshComponent)}
        for saved in record['components']:
            component = available.get(saved['name'])
            if component is None:
                raise RuntimeError('Missing native kit component: ' + record['name'] + '/' + saved['name'])
            component.set_static_mesh(load(saved['mesh']))
            # Root relative transform is already the actor world transform.
            if component.get_attach_parent() is not None:
                component.set_relative_transform(transform(saved['relative_location'],
                    saved['relative_rotation'], saved['relative_scale']), False, False)
            if isinstance(component, u.InstancedStaticMeshComponent):
                component.clear_instances()
                for instance in saved['instances']:
                    component.add_instance(transform(instance['location'], instance['rotation'],
                                                     instance['scale']), world_space=False)
            for index, path in enumerate(saved['materials']):
                if path:
                    component.set_material(index, load(path))

    def tangible_collision(actor, record):
        robot = 'BP_Mech' in record['class']
        for component in actor.get_components_by_class(u.StaticMeshComponent):
            mesh = component.static_mesh
            if not mesh:
                continue
            name = mesh.get_name().lower()
            cosmetic = robot or any(word in name for word in (
                'hologram', 'screen', 'fruit', 'paper', 'book', 'cable',
                'constructionpart115', 'constructionpart116', 'constructionpart123_fruittree'))
            component.set_simulate_physics(False)
            component.set_collision_profile_name('NoCollision' if cosmetic else 'BlockAll')
            component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION if cosmetic
                                            else u.CollisionEnabled.QUERY_AND_PHYSICS)
            if cosmetic or mesh.get_path_name() in receipt['structural_collision']:
                continue
            body = mesh.get_editor_property('body_setup')
            count = 0
            trace = 'NoBodySetup'
            if body:
                agg = body.get_editor_property('agg_geom')
                for field in ('convex_elems', 'box_elems', 'sphere_elems', 'sphyl_elems'):
                    count += len(agg.get_editor_property(field))
                trace = str(body.get_editor_property('collision_trace_flag'))
            check = {'native_simple_elements': count, 'trace_flag': trace,
                     'instanced': isinstance(component, u.InstancedStaticMeshComponent)}
            receipt['structural_collision'][mesh.get_path_name()] = check
            if count == 0 or (check['instanced'] and 'USE_COMPLEX_AS_SIMPLE' in trace):
                receipt['collision_attention'].append({'asset': mesh.get_path_name(), **check})

    for block in data['blocks']:
        block_receipt = {'name': block['name'], 'actors': [], 'uniform_scale': block['uniform_scale']}
        for index, record in enumerate(block['actors']):
            location, rotation, scale = placement(record, block, data['source_pivot'])
            name = 'MarketNative/' + block['name'] + '/' + record['name']
            if record['class'] == '/Script/Engine.StaticMeshActor':
                source = record['components'][0]
                materials = [api['balanced'](load(path)) if path else None
                             for path in source['materials']]
                actor = raw(name, source['mesh'], location, scale=scale,
                            solid=False, materials=materials, rotation=rotation)
            else:
                bp_path = record['class'][:-2] if record['class'].endswith('_C') else record['class']
                blueprint = load(bp_path)
                actor = eas.spawn_actor_from_class(blueprint.generated_class(), u.Vector(*location))
                actor.set_actor_rotation(u.Rotator(pitch=rotation[0], yaw=rotation[1], roll=rotation[2]), False)
                actor.set_actor_scale3d(u.Vector(*scale))
                restore_components(actor, record)
                finish(actor, name, False)
                # Do not freeze vendor robotic animation. ISM structure classes
                # retain their normal tick settings; Mech actors explicitly run.
                if 'BP_Mech' in record['class']:
                    actor.set_actor_tick_enabled(True)
            tangible_collision(actor, record)
            tags = list(actor.tags)
            tags.extend([u.Name('OutpostRole:VendorMiniKit'), u.Name('OutpostAssembly:' + block['name'])])
            actor.tags = tags
            block_receipt['actors'].append({'name': name, 'location': location,
                'rotation': rotation, 'scale': scale, 'native_blueprint': record['class'] != '/Script/Engine.StaticMeshActor'})
        receipt['blocks'].append(block_receipt)

    def framed(name, dimensions, location, yaw=0, scale=1, mounting='Wall'):
        # Frame/glass use the same original pivot. Never independently center
        # the transparent layer, which would detach the authored frame inset.
        frame = 'SM_Window' + dimensions + '_V1_Part1'
        glass = 'SM_Window' + dimensions + '_V2_Part2_DigitalWindow'
        for part, asset in [('Frame', frame), ('AnimatedGlass', glass)]:
            actor = raw(name + '/' + part, P4 + asset + '.' + asset,
                        location, yaw=yaw, scale=(scale, scale, scale), solid=False)
            actor.tags = list(actor.tags) + [u.Name('OutpostRole:MountedDisplay'),
                                           u.Name('OutpostMount:' + mounting)]
        receipt['display_assemblies'].append({'name': name, 'location': location,
            'yaw': yaw, 'scale': scale, 'mounting': mounting, 'native_animation': True})

    # Forward of the east equipment, native 300x100 windows form a readable
    # upper status band. InteriorGraphics adds measured ceiling brackets once
    # the banks/quiet ceiling exist, and migrates old saved placements safely.
    from OutpostOperationsStatusBand import layout as status_band_layout
    for row in status_band_layout():
        framed(row['name'], row['dimensions'], row['location'], mounting='Ceiling')
    # Shallow double-sided station-status windows hang from the ceiling above
    # the console side aisles. Their 295cm bottom clears people and machinery.
    for index, y in enumerate((-650, 650)):
        framed('Operations/SuspendedTelemetry' + str(index + 1), '300X100',
               (7860, y, 295), yaw=-90 if y < 0 else 90, mounting='Ceiling')
    # Holographic panes back the lounge as an inhabited sci-fi space while
    # respecting the wardrobe projector, arcade screens and walking approach.
    for index, x in enumerate((3260, 4320, 5310)):
        framed('Lounge/RearHoloArchive' + str(index + 1), '300X200',
               (x, 4460, 130), yaw=90, mounting='RearWall')
    for index, y in enumerate((3020, 3730)):
        framed('Lounge/WestHoloWindow' + str(index + 1), '200X250',
               (2940, y, 65), yaw=180, mounting='WestWall')
    return receipt
