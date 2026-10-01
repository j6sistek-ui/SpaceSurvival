"""Local task-light preview and explicit, repeatable adoption for the private outpost.

Only the 19 existing Engineering/Operations task PointLights are targeted. Their
owned lamp housings, support meshes, location, color, lumens and radius remain.
Downward rectangular emitters redirect existing flux away from the ceiling.
No map save, exposure/environment edit, collision edit or automatic adoption.

handle = sample({'u': unreal, 'EAS': editor_actor_subsystem})
handle['receipt'] is JSON-safe; restore(api, handle) reverts the preview exactly.
After review and preview restoration, apply(api) adopts the same19 emitters.
It does not save the map and reuses its owned actors on subsequent calls.
"""
from math import cos, radians, sin

FIXTURE = '/Game/P1toP5_Bundle/P5_FruitSeller/Meshes/SM_Props_ConstructionPart118_Light.SM_Props_ConstructionPart118_Light'


def layout():
    """Exact source labels and mounting positions; no Unreal dependency."""
    from OutpostInteriorAssemblies import BANKS, COMMAND_PODS
    rows = []

    def record(name, suffix, position, fixture_z, source):
        rows.append({'light_label': name + suffix,
                     'housing_label': name + ('/Owned lamp housing' if source == 'OutpostWorkstation.add_task_lights' else '/Owned light housing'),
                     'fixture_asset': FIXTURE, 'source_function': source,
                     'expected_center_cm': list(position),
                     'expected_housing_center_cm': [position[0], position[1], fixture_z],
                     'emitter_size_cm': [120, 24], 'housing_size_cm': [135, 32, 14],
                     'rotation_pitch_yaw_roll': [-90, 0, 0]})

    for name, x, y in [('Primary', 4200, -3150), ('Port diagnostics', 3685, -3465),
                       ('Starboard diagnostics', 4715, -3465)]:
        record('Engineering/Workstation light/' + name, '/Working pool', (x,y,304),328,
               'OutpostWorkstation.add_task_lights')
    for name, (x,y,z), yaw in BANKS:
        angle = radians(yaw)
        for side in (-1,1):
            dx,dy = side*210,-130
            xx,yy = x+dx*cos(angle)-dy*sin(angle), y+dx*sin(angle)+dy*cos(angle)
            record('OperationsNative/' + name + '/Local task ' + str(side), '/Task light',
                   (xx,yy,z+319),z+333,'OutpostInteriorAssemblies.build')
    for name, (x,y,z), yaw in COMMAND_PODS:
        angle = radians(yaw)
        xx,yy = x+80*sin(angle),y-80*cos(angle)
        record('OperationsNative/Command island ' + name, '/Task light',
               (xx,yy,z+367),z+390,'OutpostInteriorAssemblies.build')
    assert len(rows)==19 and len({r['light_label'] for r in rows})==19
    return rows


def _resolve(api, allow_hidden=False):
    """Validate the full physical fixture set before changing any light."""
    u,eas = api['u'],api['EAS']
    from OutpostGeometryUtils import mesh_union
    by_label = {}
    for actor in eas.get_all_level_actors():
        by_label.setdefault(actor.get_actor_label(),[]).append(actor)
    resolved = []
    for row in layout():
        matches = by_label.get(row['light_label'],[])
        fixtures = by_label.get(row['housing_label'],[])
        assert len(matches)==1 and len(fixtures)==1, 'Missing or duplicate fixture mapping: '+row['light_label']
        point,fixture = matches[0],fixtures[0]
        component = point.get_component_by_class(u.PointLightComponent)
        assert component and not isinstance(point,u.SpotLight), row['light_label']+' is not the expected task point'
        static = fixture.get_component_by_class(u.StaticMeshComponent)
        assert static and static.static_mesh.get_path_name()==FIXTURE, 'Wrong physical housing '+row['housing_label']
        location = point.get_actor_location()
        center,extent = mesh_union(fixture)
        assert max(abs(v-e) for v,e in zip((location.x,location.y,location.z),row['expected_center_cm']))<1, 'Task light moved: '+row['light_label']
        assert max(abs(v-e) for v,e in zip((center.x,center.y,center.z),row['expected_housing_center_cm']))<1, 'Fixture moved: '+row['housing_label']
        assert location.z < center.z-extent.z, 'Emitter is inside or above housing'
        assert component.get_editor_property('intensity_units')==u.LightUnits.LUMENS, 'Unexpected light units'
        assert not component.get_editor_property('cast_shadows'), 'Unexpected existing shadow policy'
        assert allow_hidden or component.get_editor_property('visible'), 'Task source already hidden'
        resolved.append((row,point,component,fixture))

    return resolved


def _configure_emitter(api, rect, original):
    """Copy source flux/color/range, retaining the sampled downward area shape."""
    u = api['u']
    c = rect.get_component_by_class(u.RectLightComponent)
    c.set_mobility(u.ComponentMobility.MOVABLE)
    c.set_intensity_units(u.LightUnits.LUMENS)
    c.set_intensity(original.get_editor_property('intensity'))
    c.set_light_color(original.get_light_color())
    c.set_attenuation_radius(original.get_editor_property('attenuation_radius'))
    c.set_cast_shadows(False)
    c.set_source_width(24)
    c.set_source_height(120)
    c.set_barn_door_angle(88)
    c.set_barn_door_length(8)
    for prop in ('indirect_lighting_intensity','volumetric_scattering_intensity','specular_scale'):
        c.set_editor_property(prop,original.get_editor_property(prop))
    forward = rect.get_actor_forward_vector()
    assert forward.z < -.999, 'Task emitter must point down'
    color = original.get_light_color()
    location = rect.get_actor_location()
    return {'lumens':original.get_editor_property('intensity'),
            'radius_cm':original.get_editor_property('attenuation_radius'),
            'color':[color.r,color.g,color.b], 'actual_center_cm':[location.x,location.y,location.z],
            'emitting_direction':[forward.x,forward.y,forward.z], 'casts_shadows':False}


def sample(api):
    """Resolve and validate the complete set first, then make a reversible swap."""
    u,eas = api['u'],api['EAS']
    resolved = _resolve(api)
    handle = {'created':[],'originals':[], 'receipt':{'candidate':'Downward task area lights',
              'scope':'Engineering3 + Operations16 local fixtures only; no automatic save or adoption.',
              'unchanged':['global exposure','environment','fixture geometry','collision','total source lumens','source colors','attenuation radii','shadow policy'],
              'lights':[]}}
    try:
        for row,point,original,fixture in resolved:
            location = point.get_actor_location()
            rect = eas.spawn_actor_from_class(u.RectLight,location,u.Rotator(pitch=-90,yaw=0,roll=0))
            assert rect, 'Could not spawn candidate area light'
            handle['created'].append(rect)
            rect.set_actor_label(row['light_label']+' / Area candidate')
            rect.tags = list(point.tags)+[u.Name('OutpostCandidate:TaskAreaLight')]
            emitter = _configure_emitter(api, rect, original)
            handle['originals'].append((original,bool(original.get_editor_property('visible'))))
            original.set_visibility(False,False)
            handle['receipt']['lights'].append(dict(row, candidate_label=rect.get_actor_label(), **emitter))
    except Exception:
        restore(api,handle)
        raise
    return handle


def restore(api,handle):
    """Restore only this sample's task lights; no map/assets are saved."""
    for component,visible in handle['originals']:
        component.set_visibility(visible,False)
    for actor in handle['created']:
        api['EAS'].destroy_actor(actor)
    handle['originals'].clear()
    handle['created'].clear()
    handle['receipt']['restored'] = True


PERMANENT_TAG = 'OutpostTaskAreaLight'
PERMANENT_SUFFIX = ' / Area emitter'


def apply(api):
    """Explicitly adopt the sampled layout, or reuse its same19 owned emitters.

    Original PointLight actors/components retain their positions, lumens, colors
    and radii; only their visibility changes to prevent double illumination.
    No extra emitter is added on repeated calls. Source fixture mismatches or an
    active unsaved preview reject before mutation. The caller saves the map.
    """
    u,eas = api['u'],api['EAS']
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    package = world.get_path_name().split('.')[0]
    target = '/Game/OutpostSandbox/L_AsteroidOutpost'
    fresh_authoring = package.startswith('/Temp/Untitled') and api.get('TARGET') == target
    if package != target and not fresh_authoring:
        raise RuntimeError('Task area adoption is restricted to the private outpost')
    actors = list(eas.get_all_level_actors())
    if any('OutpostCandidate:TaskAreaLight' in map(str,actor.tags) for actor in actors):
        raise RuntimeError('Restore the temporary task-light sample before permanent adoption')
    owned = [actor for actor in actors if PERMANENT_TAG in map(str,actor.tags)]
    expected = {row['light_label'] + PERMANENT_SUFFIX for row in layout()}
    # Never claim idempotence by deleting/recreating duplicates. A partial or
    # foreign set is a layout error to inspect before changing its original lights.
    if owned and (len(owned) != 19 or {actor.get_actor_label() for actor in owned} != expected):
        raise RuntimeError('Permanent task-light set is partial or duplicated')
    for actor in actors:
        if actor.get_actor_label() in expected and actor not in owned:
            raise RuntimeError('Task emitter label is occupied by an unowned actor')
    resolved = _resolve(api,allow_hidden=True) if owned else []
    by_label = {actor.get_actor_label():actor for actor in owned}
    for row,point,original,fixture in resolved:
        if owned:
            emitter = by_label[row['light_label'] + PERMANENT_SUFFIX]
            if not isinstance(emitter,u.RectLight):
                raise RuntimeError('Owned task emitter has the wrong class')
            delta = emitter.get_actor_location() - point.get_actor_location()
            if max(abs(delta.x),abs(delta.y),abs(delta.z)) > 1:
                raise RuntimeError('Owned task emitter moved relative to its source')
            if emitter.get_actor_forward_vector().z >= -.999:
                raise RuntimeError('Owned task emitter no longer points downward')
    lights = []
    if not owned:
        handle = sample(api)
        try:
            for row,rect in zip(layout(),handle['created']):
                rect.set_actor_label(row['light_label'] + PERMANENT_SUFFIX)
                rect.set_folder_path(row['light_label'].split('/')[0])
                rect.tags = [tag for tag in rect.tags if str(tag) != 'OutpostCandidate:TaskAreaLight'] + [u.Name(PERMANENT_TAG)]
            lights = [dict(entry, emitter_label=entry['light_label'] + PERMANENT_SUFFIX)
                      for entry in handle['receipt']['lights']]
            for entry in lights:
                entry.pop('candidate_label',None)
        except Exception:
            restore(api,handle)
            raise
    else:
        for row,point,original,fixture in resolved:
            rect = by_label[row['light_label'] + PERMANENT_SUFFIX]
            emitter = _configure_emitter(api,rect,original)
            rect.get_component_by_class(u.RectLightComponent).set_visibility(True,False)
            original.set_visibility(False,False)
            lights.append(dict(row,emitter_label=rect.get_actor_label(),**emitter))
    return {'adopted':'Downward task area lights','created':0 if owned else 19,
            'reused':len(owned),'active_area_emitters':19,
            'original_point_parameters_preserved':True,'original_points_hidden':True,
            'map_saved':False,'source_assets_modified':False,
            'scope':'Engineering3 + Operations16 local fixtures only; no global lighting changes.',
            'lights':lights}
