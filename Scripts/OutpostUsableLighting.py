"""Normal interior illumination and working promenade fixtures, applied last.

Private saved outpost only. Reuses existing light positions and lens slots;
replaces six ceiling points with broad downward sources supported by the
existing strips, which are moved below the measured ceiling. No exposure,
sky, character hologram, vendor material, collision or gameplay changes.
"""
import json

TARGET = '/Game/OutpostSandbox/L_AsteroidOutpost'
PREFIX = 'UsableLighting/'
TAG = 'OutpostUsableLighting'
PRIVATE = '/Game/OutpostSandbox/Materials/'
LAMP = '/Game/P1toP5_Bundle/P5_FruitSeller/Meshes/SM_Props_ConstructionPart118_Light.SM_Props_ConstructionPart118_Light'
ROOMS = {'Engineering': (9000., 1900.), 'Lounge': (7500., 1900.), 'Operations': (6500., 2000.)}


def light_recipe(label, tags):
    """Exact existing roles only; retired point copies are never enabled."""
    if label.startswith('Engineering/Workstation light/') and label.endswith(' / Area emitter'):
        return 3000., 850., (1., .9, .78)
    if label.startswith('OperationsNative/') and label.endswith(' / Area emitter'):
        return 1250., 800., (.8, .9, 1.)
    if label == 'FrontLighting/Engineering workstation key':
        return 3300., 950., (1., .92, .82)
    if label.startswith('InteriorReadability/Engineering diagnostic '):
        return 900., 550., (.76, .88, 1.)
    if label.startswith('InteriorReadability/Operations face '):
        return 600., 650., (.76, .88, 1.)
    if label.startswith('LoungeNative/Conversation ') and label.endswith('/Task light'):
        return 2400., 1000., (1., .86, .7)
    if label == 'Lounge/Conversation pool':
        return 1800., 950., (1., .88, .75)
    if label == 'Lounge/East seating pool':
        return 1700., 950., (.78, .88, 1.)
    if label == 'InteriorReadability/Arcade cabinets':
        return 1600., 1000., (1., .86, .7)
    if label.startswith('PublicLighting/Market/') and label.endswith('/Local downlight'):
        return 4200., 1450., (.85, .92, 1.)
    if label == 'Market/Pedestrian pool':
        return 3000., 1400., (.78, .87, 1.)
    if 'OutpostMarketTask' in tags:
        return 1500., 850., (1., .9, .78)
    if label.startswith('PublicLighting/Player/') and label.endswith('/Local flood'):
        return 4000., 3300., (.8, .9, 1.)
    if label.startswith(('PublicLighting/Visitor02/', 'PublicLighting/Visitor03/')) and label.endswith('/Local flood'):
        return 2000., 1800., (.8, .9, 1.)
    return None


def apply(api):
    u, eas, edit, lib = api['u'], api['EAS'], api['EDIT'], api['LIB']
    from OutpostGeometryUtils import mesh_union
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name().split('.')[0] != TARGET or api.get('TARGET') != TARGET:
        raise RuntimeError('Usable lighting requires the saved private outpost')
    actors = list(eas.get_all_level_actors())
    groups = {}
    for actor in actors:
        groups.setdefault(actor.get_actor_label(), []).append(actor)

    # Resolve ceiling support and all six original strips/points before writes.
    ceilings = []
    for room, (power, radius) in ROOMS.items():
        strips = sorted(groups.get(room+'/Ceiling luminaire', []), key=lambda a: a.get_actor_location().x)
        points = sorted(groups.get(room+'/Ceiling pool', []), key=lambda a: a.get_actor_location().x)
        if len(strips) != 2 or len(points) != 2:
            raise RuntimeError('Expected two ceiling strips and pools: '+room)
        panels = [a for a in actors if a.get_actor_label().startswith((room+'/Ceiling panel', 'QuietCeiling/'+room+'/Panel '))]
        lows = []
        for panel in panels:
            c = panel.get_component_by_class(u.StaticMeshComponent)
            if c and c.get_editor_property('visible') and not panel.get_editor_property('hidden'):
                center, extent = mesh_union(panel); lows.append(center.z-extent.z)
        if not lows: raise RuntimeError('No visible ceiling support: '+room)
        underside = min(lows)
        if not 370. < underside < 445.: raise RuntimeError('Ceiling height changed: '+room)
        for index, (strip, point) in enumerate(zip(strips, points), 1):
            if (not isinstance(point,u.PointLight) or isinstance(point,u.SpotLight) or
                    'OutpostAuthored' not in map(str,point.tags)):
                raise RuntimeError('Expected owned ceiling PointLight: '+room)
            center, extent = mesh_union(strip)
            c = strip.get_component_by_class(u.StaticMeshComponent)
            if (str(c.get_collision_enabled()) != str(u.CollisionEnabled.NO_COLLISION) or
                    abs(point.get_actor_location().x-center.x)>1 or
                    'OutpostAuthored' not in map(str, strip.tags)):
                raise RuntimeError('Unexpected ceiling fixture: '+room)
            name = PREFIX+room+'/Ceiling '+str(index)
            existing = groups.get(name, [])
            if len(existing)>1 or (existing and (TAG not in map(str, existing[0].tags) or not isinstance(existing[0],u.RectLight))):
                raise RuntimeError('Ceiling emitter namespace is not owned: '+name)
            ceilings.append((name,strip,point,center,extent,underside,power,radius,existing))
    planned = []
    for actor in actors:
        recipe = light_recipe(actor.get_actor_label(), set(map(str,actor.tags)))
        if recipe:
            components = list(actor.get_components_by_class(u.LocalLightComponent))
            if len(components)!=1 or not components[0].get_editor_property('visible'):
                raise RuntimeError('Expected one active existing light: '+actor.get_actor_label())
            planned.append((actor,components[0],recipe))
    if not planned: raise RuntimeError('No owned illumination roles found')

    # Reuse the existing simple unlit lens parent; only these private instances
    # gain brighter neutral tints. Shared archive capsule material stays intact.
    parent = api['load'](PRIVATE+'M_OutpostWorkstationWarmLens')
    if 'HullTint' not in map(str, edit.get_vector_parameter_names(parent)):
        raise RuntimeError('Lens parent no longer exposes HullTint')
    lenses = {}
    for name, color in [('Neutral',(8.,7.5,6.6)),('Cool',(6.5,8.,10.))]:
        path = PRIVATE+'MI_UsableLamp'+name
        mat = api['load'](path) if lib.does_asset_exist(path) else api['TOOLS'].create_asset(path.rsplit('/',1)[1],PRIVATE.rstrip('/'),u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
        edit.set_material_instance_parent(mat,parent)
        edit.set_material_instance_vector_parameter_value(mat,'HullTint',u.LinearColor(*color,1.))
        edit.update_material_instance(mat); lib.save_loaded_asset(mat)
        lenses[name] = mat

    report = {'map':TARGET,'ceiling_fixtures':[],'existing_lights':[],'lens_slots':[],
              'global_exposure_unchanged':True,'character_hologram_materials_unchanged':True}
    for name,strip,point,center,extent,underside,power,radius,existing in ceilings:
        # Strip top is flush with ceiling underside. Source lies below its lens.
        old = strip.get_actor_location()
        strip.set_actor_location(u.Vector(old.x,old.y,old.z+underside-extent.z-center.z),False,False)
        strip.static_mesh_component.set_material(0,lenses['Neutral'])
        strip.static_mesh_component.set_cast_shadow(False)
        center,extent = mesh_union(strip)
        position = u.Vector(center.x,center.y,center.z-extent.z-1.)
        rect = existing[0] if existing else eas.spawn_actor_from_class(u.RectLight,position,u.Rotator(pitch=-90,yaw=0,roll=0))
        rect.set_actor_label(name);rect.tags=list(set(list(rect.tags)+[u.Name(TAG)]))
        rect.set_actor_location(position,False,False);rect.set_actor_rotation(u.Rotator(pitch=-90,yaw=0,roll=0),False)
        c=rect.get_component_by_class(u.RectLightComponent);c.set_mobility(u.ComponentMobility.MOVABLE)
        c.set_intensity_units(u.LightUnits.LUMENS);c.set_intensity(power);c.set_attenuation_radius(radius)
        c.set_light_color(u.LinearColor(1.,.94,.85,1.));c.set_source_width(max(20.,extent.y*2));c.set_source_height(18.)
        c.set_barn_door_angle(88.);c.set_barn_door_length(5.);c.set_cast_shadows(True)
        c.set_editor_property('specular_scale',.22);c.set_visibility(True,False)
        point.get_component_by_class(u.PointLightComponent).set_visibility(False,False)
        report['ceiling_fixtures'].append({'name':name,'lumens':power,'radius_cm':radius,'ceiling_underside_cm':underside,'strip_top_cm':center.z+extent.z,'emitter_z_cm':position.z,'original_point_hidden':True})
    for actor,c,(power,radius,color) in planned:
        before={'lumens':c.get_editor_property('intensity'),'units':str(c.get_editor_property('intensity_units')),'radius_cm':c.get_editor_property('attenuation_radius')}
        c.set_intensity_units(u.LightUnits.LUMENS);c.set_intensity(power);c.set_attenuation_radius(radius)
        c.set_light_color(u.LinearColor(*color,1.))
        report['existing_lights'].append({'actor':actor.get_actor_label(),'before':before,'lumens':power,'radius_cm':radius,'visible':c.get_editor_property('visible')})
    for actor in actors:
        name = actor.get_actor_label()
        # Exclude archive capsules and all small character/projector emitters.
        allowed = (name.startswith(('PublicLighting/','Engineering/Workstation light/','OperationsNative/','FrontLighting/Engineering workstation','Engineering/Diagnostic backing/')) or
                   name.startswith('LoungeNative/Conversation '))
        if not allowed: continue
        for c in actor.get_components_by_class(u.StaticMeshComponent):
            if c.static_mesh and c.static_mesh.get_path_name()==LAMP:
                if c.get_num_materials()!=3: raise RuntimeError('Lamp slot layout changed: '+name)
                old=c.get_material(2).get_path_name()
                mat=lenses['Cool' if name.startswith(('PublicLighting/','OperationsNative/')) else 'Neutral']
                c.set_material(2,mat)
                report['lens_slots'].append({'actor':name,'slot':2,'before':old,'after':mat.get_path_name()})
    report['counts']={'ceiling_replacements':len(ceilings),'existing_lights_adjusted':len(planned),'visible_lens_slots':len(report['lens_slots'])}
    (api['OUT']/'usable-lighting.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report
