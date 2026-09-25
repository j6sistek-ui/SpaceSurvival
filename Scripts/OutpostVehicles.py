"""Owned vehicle presentations for the isolated outpost map; no original assets are saved.

Called by the lead author script. The safe Phoenix derivative retains the purchased
component hierarchy. Tint derivatives multiply its existing base colour, preserving
textures, normals and material-instance overrides. Unsupported graphs are skipped.
"""
import json
from pathlib import Path
import unreal as u

BASE = '/Game/OutpostSandbox/Materials/Vehicles'
PHOENIX = '/Game/SpaceSurvival/Licensed/PhoenixPresentation/BP_PhoenixPresentation'
HULL = '/Game/Stellar_Phoenix/Spaceship/Meshes/Stellar_Phoenix'
LANDING = '/Game/Stellar_Phoenix/Spaceship/Animation/Landing_On'
FRUIT = '/Game/P1toP5_Bundle/P5_FruitSeller/Blueprints/'


def build(eas, load, material, terminal, out):
    """Return actors: ship, hull, drones, paint_terminal, flight_terminal; writes receipt to out."""
    lib = u.EditorAssetLibrary
    edit = u.MaterialEditingLibrary
    tool = u.AssetToolsHelpers.get_asset_tools()
    receipt = {'ship_blueprint': PHOENIX, 'pose': LANDING, 'paint_slots': [], 'drones': [], 'access_proxies': []}
    palette = [u.LinearColor(.12, .48, .68, 1), u.LinearColor(.8, .23, .07, 1),
               u.LinearColor(.9, .92, 1, 1), u.LinearColor(.32, .08, .6, 1), u.LinearColor(.08, .10, .13, 1)]

    def label(actor, name):
        actor.set_actor_label(name)
        actor.set_folder_path(name.split('/')[0])
        actor.tags = list(actor.tags) + [u.Name('OutpostAuthored')]
        return actor

    def tint_material(source):
        # Duplicating the MIC retains all vendor texture/scalar overrides. Only its copied root graph changes.
        import hashlib
        name = hashlib.sha1(source.get_path_name().encode()).hexdigest()[:12]
        result_path = BASE + '/MI_Paint_' + name
        if lib.does_asset_exist(result_path):
            return load(result_path)
        root = source
        visited = set()
        while isinstance(root, u.MaterialInstanceConstant):
            if root.get_path_name() in visited:
                return None
            visited.add(root.get_path_name())
            root = root.get_editor_property('parent')
        if not isinstance(root, u.Material):
            return None
        root_name = hashlib.sha1(root.get_path_name().encode()).hexdigest()[:12]
        root_path = BASE + '/M_Paint_' + root_name
        if lib.does_asset_exist(root_path):
            target_root = load(root_path)
        else:
            target_root = lib.duplicate_asset(root.get_path_name().split('.')[0], root_path)
            node = edit.get_material_property_input_node(target_root, u.MaterialProperty.MP_BASE_COLOR)
            if not node:
                # Material-attributes graphs require manual adaptation; do not replace their surface.
                receipt.setdefault('paint_unsupported', []).append(source.get_path_name())
                return None
            tint = edit.create_material_expression(target_root, u.MaterialExpressionVectorParameter)
            tint.set_editor_property('parameter_name', 'HullTint')
            tint.set_editor_property('default_value', u.LinearColor(1, 1, 1, 1))
            multiply = edit.create_material_expression(target_root, u.MaterialExpressionMultiply)
            output = edit.get_material_property_input_node_output_name(target_root, u.MaterialProperty.MP_BASE_COLOR)
            edit.connect_material_expressions(node, output, multiply, 'A')
            edit.connect_material_expressions(tint, '', multiply, 'B')
            edit.connect_material_property(multiply, '', u.MaterialProperty.MP_BASE_COLOR)
            edit.recompile_material(target_root)
            lib.save_loaded_asset(target_root)
        if 'HullTint' not in [str(n) for n in edit.get_vector_parameter_names(target_root)]:
            return None
        if isinstance(source, u.MaterialInstanceConstant):
            result = lib.duplicate_asset(source.get_path_name().split('.')[0], result_path)
            # Copy each intermediate material instance as well, retaining its inherited overrides.
            ancestors = []
            parent = source.get_editor_property('parent')
            while isinstance(parent, u.MaterialInstanceConstant):
                ancestors.append(parent)
                parent = parent.get_editor_property('parent')
            target_parent = target_root
            for ancestor in reversed(ancestors):
                ancestor_name = hashlib.sha1(ancestor.get_path_name().encode()).hexdigest()[:12]
                ancestor_path = BASE + '/MI_Parent_' + ancestor_name
                copied = load(ancestor_path) if lib.does_asset_exist(ancestor_path) else lib.duplicate_asset(ancestor.get_path_name().split('.')[0], ancestor_path)
                edit.set_material_instance_parent(copied, target_parent)
                lib.save_loaded_asset(copied)
                target_parent = copied
            edit.set_material_instance_parent(result, target_parent)
        else:
            result = tool.create_asset('MI_Paint_' + name, BASE, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
            edit.set_material_instance_parent(result, target_root)
        edit.set_material_instance_vector_parameter_value(result, 'HullTint', u.LinearColor(1, 1, 1, 1))
        lib.save_loaded_asset(result)
        return result

    ship = label(eas.spawn_actor_from_class(load(PHOENIX).generated_class(), u.Vector(-4200, 0, 0)), 'Berth/Phoenix current ship')
    # Native hull definition MeshYaw=-90 plus world-facing180: nose points out toward -worldX.
    ship.set_actor_rotation(u.Rotator(yaw=90), False)
    ship.set_editor_property('auto_possess_player', u.AutoReceiveInput.DISABLED)
    ship.set_editor_property('auto_possess_ai', u.AutoPossessAI.DISABLED)
    ship.set_actor_tick_enabled(False)
    hull = None
    landing = load(LANDING)
    for component in ship.get_components_by_class(u.ActorComponent):
        component.set_component_tick_enabled(False)
        if isinstance(component, u.PrimitiveComponent):
            component.set_simulate_physics(False)
            component.set_enable_gravity(False)
            component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        if isinstance(component, u.SceneComponent):
            component.set_mobility(u.ComponentMobility.MOVABLE)
        if isinstance(component, u.SkeletalMeshComponent):
            mesh = component.get_skeletal_mesh_asset()
            if mesh and mesh.get_path_name().split('.')[0] == HULL:
                hull = component
                component.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
                data = component.get_editor_property('animation_data')
                data.anim_to_play = landing
                data.saved_looping = False
                data.saved_playing = False
                data.saved_position = landing.get_play_length()
                component.set_editor_property('animation_data', data)
                component.set_animation(landing)
                component.set_position(landing.get_play_length(), False)
                component.set_component_tick_enabled(True)
                component.set_editor_property('pause_anims', True)
        if isinstance(component, (u.CameraComponent, u.AudioComponent, u.NiagaraComponent)):
            component.deactivate()
            if isinstance(component, u.SceneComponent):
                component.set_visibility(False)
        if isinstance(component, u.TextRenderComponent):
            component.set_visibility(False)
        if isinstance(component, u.PointLightComponent):
            component.set_intensity(2000)
            component.set_attenuation_radius(2200)
            component.set_cast_shadows(False)
    assert hull, 'Safe Phoenix Blueprint lost its skeletal hull'
    all_slots = []
    for component in ship.get_components_by_class(u.MeshComponent):
        eligible = []
        for slot, source in enumerate(component.get_materials()):
            if not source:
                continue
            lowered = source.get_name().lower()
            if any(word in lowered for word in ('glass','window','canopy','cockpit','interior','light','emiss','padding','seat','enginefire')):
                continue
            result = tint_material(source)
            if result:
                component.set_material(slot, result)
                eligible.append(slot)
                all_slots.append(slot)
                receipt['paint_slots'].append({'component':component.get_name(),'slot':slot,'original':source.get_path_name(),'derivative':result.get_path_name()})
        if eligible:
            component.component_tags = list(component.component_tags) + [u.Name('OutpostPaintable')]

    # Interior footprint follows the current ship's measured rear cabin (~Z230cm) and ramp toe.
    # These proxies are exact local route supports, never a hull-sized invisible bounding box.
    proxy_mat = material('M_OutpostShipWalkProxy', (.055,.075,.09), .6, .4)
    cube = load('/Engine/BasicShapes/Cube.Cube')

    def proxy(name, native_center, size, pitch=0):
        # Native +X forward is -worldX, +Y right is -worldY for this parked heading.
        center = u.Vector(-4200-native_center[0], -native_center[1], native_center[2])
        actor = label(eas.spawn_actor_from_class(u.StaticMeshActor, center), 'Berth/Access/'+name)
        actor.static_mesh_component.set_static_mesh(cube)
        actor.static_mesh_component.set_material(0, proxy_mat)
        actor.set_actor_scale3d(u.Vector(size[0]/100, size[1]/100, size[2]/100))
        actor.set_actor_rotation(u.Rotator(pitch=pitch, yaw=180), False)
        actor.static_mesh_component.set_collision_profile_name('BlockAll')
        actor.set_actor_hidden_in_game(True)
        receipt['access_proxies'].append({'name':name,'native_center':native_center,'size':size,'pitch':pitch})
        return actor

    # Shallow continuous ramp; lower end meets deck, upper end meets the rear-cabin sole level.
    proxy('Cargo ramp',(-1180,0,113),(610,205,12),25)
    proxy('Cabin floor',(-600,0,222),(620,330,16))
    proxy('Forward passage',(60,0,222),(720,165,16))
    proxy('Cockpit floor',(590,0,222),(360,300,16))
    for side in (-1,1):
        proxy('Cabin edge '+str(side),(-600,side*192,330),(620,20,230))
    paint = terminal('Services/SHIP FINISH',(-2900,-1150,100),u.SSOutpostAction.CYCLE_SHIP_PAINT,
                     'Cycle the parked ship finish. This sandbox preview does not modify account paint.',ship,yaw=90)
    paint.set_editor_property('paint_material_slots', sorted(set(all_slots)))
    paint.set_editor_property('paint_palette', palette)
    flight = terminal('Berth/COCKPIT / FREE FLIGHT',(-4790,0,320),u.SSOutpostAction.FREE_FLIGHT,
                      'Launch casual Free Flight in the current gameplay map. No Survival run is started.',yaw=0)
    flight.set_editor_property('use_distance',250)

    drones = []
    for index, (name, bp_name, position, route, height, speed) in enumerate([
        ('Market delivery drone','BP_Mech4_FlyingDroid',(-300,450,510),[(0,0,0),(1800,0,40),(1800,650,0),(0,650,50)],160,165),
        ('Berth inspection drone','BP_Mech3_FlyingInsect',(-3700,-900,780),[(0,0,0),(-1700,0,150),(-1700,1700,60),(0,1700,0)],115,190),
    ]):
        carrier = label(eas.spawn_actor_from_class(u.SSOutpostAmbientActor, u.Vector(*position)), 'Drones/'+name)
        carrier.set_editor_property('drone',True)
        carrier.set_editor_property('travel_speed',speed)
        carrier.set_editor_property('pause_at_waypoint',.4)
        carrier.set_editor_property('phase_offset',index*2.4)
        carrier.set_editor_property('route_points',[u.Vector(*point) for point in route])
        path = FRUIT+bp_name
        visual = label(eas.spawn_actor_from_class(load(path).generated_class(),u.Vector()),'Drones/'+name+'/Assembly')
        visual.set_actor_tick_enabled(False)
        for component in visual.get_components_by_class(u.SceneComponent):
            component.set_mobility(u.ComponentMobility.MOVABLE)
            if isinstance(component,u.PrimitiveComponent):
                component.set_simulate_physics(False)
                component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        centre, extent = visual.get_actor_bounds(False)
        scale = height / max(1,extent.z*2)
        visual.set_actor_scale3d(u.Vector(scale,scale,scale))
        centre, extent = visual.get_actor_bounds(False)
        visual.set_actor_location(u.Vector(position[0]-centre.x,position[1]-centre.y,position[2]-centre.z),False,False)
        visual.attach_to_component(carrier.drone_mesh,u.Name(''),u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,False)
        drones.append(carrier)
        receipt['drones'].append({'name':name,'blueprint':path,'height_cm':height,'world_origin':position,'route_local':route})
    destination = Path(out)/'vehicles.json'
    destination.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    return {'ship':ship,'hull':hull,'drones':drones,'paint_terminal':paint,'flight_terminal':flight}
