"""Bounded T/R/reception material and fixture correction from RoomPass2.

The lead owns serialized authoring and saving returned dirty_assets. No map
loads/saves, vendor writes, new furniture or architecture/route transforms.
Existing complete desk, chair, screen and reception assemblies remain intact.
"""
import hashlib
import math

PRIVATE = '/Game/OutpostSandbox/OwnerPreview/Materials/ServicePolish'
TAG = 'StationServicePolish20261006'


def _one(actors, label):
    found = [a for a in actors if a.get_actor_label() == label]
    if len(found) != 1:
        raise RuntimeError('Expected one inspected service actor: ' + label)
    return found[0]


def _pose(actor):
    t = actor.get_actor_transform()
    return (tuple(t.translation.to_tuple()), tuple(t.rotation.to_tuple()), tuple(t.scale3d.to_tuple()))


def _assign(ctx, actor, component, slot, material):
    current = component.get_material(slot)
    ctx.records.append({'kind':'service_material_override','actor':actor.get_actor_label(),
        'component':component.get_name(),'slot':slot,
        'before':current.get_path_name() if current else None,'after':material.get_path_name()})
    component.set_material(slot,material)


def _blend(material,u):
    """Effective instance override first; then the actual inherited master."""
    visited = set()
    current = material
    while isinstance(current,u.MaterialInstanceConstant):
        path = current.get_path_name()
        if path in visited:
            raise RuntimeError('Cyclic material chain: '+path)
        visited.add(path)
        overrides = current.get_editor_property('base_property_overrides')
        if overrides.get_editor_property('override_blend_mode'):
            return overrides.get_editor_property('blend_mode')
        current = current.get_editor_property('parent')
    if not isinstance(current,u.Material):
        raise RuntimeError('Cannot inspect final material master: '+material.get_path_name())
    return current.get_editor_property('blend_mode')


def _child(parent, role, u, dirty, cache):
    key = (role,parent.get_path_name())
    if key in cache:
        return cache[key]
    name = 'MI_Service_'+role+'_'+hashlib.sha1('|'.join(key).encode()).hexdigest()[:12]
    path = PRIVATE+'/'+name
    if u.EditorAssetLibrary.does_asset_exist(path):
        raise RuntimeError('Preserve existing private polish asset: '+path)
    child = u.AssetToolsHelpers.get_asset_tools().create_asset(name,PRIVATE,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
    if not child:
        raise RuntimeError('Failed private material creation: '+path)
    u.MaterialEditingLibrary.set_material_instance_parent(child,parent)
    cache[key] = child
    dirty.append(child.get_path_name())
    return child


def _finish(ctx, actors, u, dirty):
    edit = u.MaterialEditingLibrary
    cache, rows = {}, []
    for actor in actors:
        label = actor.get_actor_label()
        if actor.get_editor_property('hidden'):
            continue
        role = None
        if label.startswith('Operations/Deck '):
            p = actor.get_actor_location()
            role = 'OperationsWorkZone' if 7350 < p.x < 8250 and abs(p.y) < 500 else 'OperationsDeck'
        elif label.startswith('Lounge/Deck '):
            role = 'ArchiveDeck'
        elif label.startswith('QuietCeiling/Operations/Panel '):
            role = 'OperationsCeiling'
        elif label.startswith('Refine/Operations/Rear data ') and label.endswith('/Frame'):
            role = 'ScreenFrame'
        if role is None:
            continue
        for c in actor.get_components_by_class(u.StaticMeshComponent):
            for slot,parent in enumerate(c.get_materials()):
                if not isinstance(parent,u.MaterialInstanceConstant):
                    continue
                vectors = set(map(str,edit.get_vector_parameter_names(parent)))
                scalars = set(map(str,edit.get_scalar_parameter_names(parent)))
                channels = {'R Color','G Color','B Color','Other Color'}
                if 'Albedo Tint' not in vectors and not channels <= vectors:
                    continue
                key = (role,parent.get_path_name())
                first = key not in cache
                child = _child(parent,role,u,dirty,cache)
                if first:
                    overrides = {}
                    if 'Albedo Tint' in vectors:
                        tint = {'OperationsWorkZone':(.09,.069,.043),
                                'OperationsDeck':(.065,.085,.105),'ArchiveDeck':(.085,.066,.105),
                                'ScreenFrame':(.07,.09,.12),'OperationsCeiling':(.065,.075,.085)}[role]
                        edit.set_material_instance_vector_parameter_value(child,'Albedo Tint',u.LinearColor(*tint,1))
                        overrides['Albedo Tint'] = list(tint)
                        if 'Albedo Tint Intensity' in scalars:
                            edit.set_material_instance_scalar_parameter_value(child,'Albedo Tint Intensity',.98)
                            overrides['Albedo Tint Intensity'] = .98
                    elif channels <= vectors:
                        # Actual central ceiling uses StarterBundle's four-color
                        # graph rather than the Genesis perimeter's tint input.
                        for parameter in sorted(channels):
                            value = edit.get_material_instance_vector_parameter_value(parent,parameter)
                            target = (value.r*.72,value.g*.70,value.b*.67,value.a)
                            edit.set_material_instance_vector_parameter_value(child,parameter,u.LinearColor(*target))
                            overrides[parameter] = list(target)
                    for parameter in scalars:
                        value = float(edit.get_material_instance_scalar_parameter_value(parent,parameter))
                        target = None
                        if parameter.startswith('Min Roughness'):
                            target = max(.58,min(.9,value))
                        elif parameter.startswith('Max Roughness'):
                            target = max(.8,min(1.,value))
                        elif parameter in ('R Roughness','G Roughness','B Roughness','Other Roughness','Roughness') and 0 <= value <= 1:
                            target = max(.55,value)
                        if target is not None and target != value:
                            edit.set_material_instance_scalar_parameter_value(child,parameter,target)
                            overrides[parameter] = target
                    for parameter in edit.get_texture_parameter_names(parent):
                        if edit.get_material_instance_texture_parameter_value(child,parameter) != edit.get_material_instance_texture_parameter_value(parent,parameter):
                            raise RuntimeError('Finish changed inherited texture: '+str(parameter))
                    edit.update_material_instance(child)
                    rows.append({'role':role,'source':parent.get_path_name(),
                                 'private':child.get_path_name(),'overrides':overrides})
                _assign(ctx,actor,c,slot,child)
    return rows


def _desk_surfaces(ctx, actors, u, dirty):
    """Repair the existing panes; retain every inherited graphic/UV texture."""
    edit = u.MaterialEditingLibrary
    cache, rows, fallback, displays = {}, [], [], set()
    for actor in actors:
        label = actor.get_actor_label()
        if actor.get_editor_property('hidden'):
            continue
        pod = label.startswith('OperationsNative/Command island ')
        welcome = label.startswith('Refine/Reception/Welcome console ')
        rear = label.startswith('Refine/Operations/Rear data ') and label.endswith('/Glass')
        if not (pod or welcome or rear):
            continue
        for component in actor.get_components_by_class(u.StaticMeshComponent):
            mesh = component.get_editor_property('static_mesh')
            if not mesh:
                continue
            screen = rear or mesh.get_name() == 'SM_SciFiScreen_V1_Part3'
            if screen:
                displays.add(label)
            translucent = False
            for slot, parent in enumerate(component.get_materials()):
                if not isinstance(parent, u.MaterialInstanceConstant):
                    continue
                blend = _blend(parent, u)
                is_translucent = blend not in (u.BlendMode.BLEND_OPAQUE, u.BlendMode.BLEND_MASKED)
                translucent |= is_translucent
                # Fixtures from P5 retain their existing balanced materials.
                if not screen and '/P3_ComputerStation/' not in mesh.get_path_name():
                    continue
                role = 'RearGraphic' if rear else 'DeskGraphic' if screen else 'DeskFinish'
                key = (role, parent.get_path_name())
                if key not in cache:
                    child = _child(parent, role, u, dirty, cache)
                    scalars = {str(n): float(edit.get_material_instance_scalar_parameter_value(parent, n))
                               for n in edit.get_scalar_parameter_names(parent)}
                    values = {}
                    if any(not math.isfinite(v) for v in scalars.values()):
                        raise RuntimeError('Nonfinite service material parameter: '+parent.get_path_name())
                    for name, value in scalars.items():
                        if name.startswith('Min Roughness'):
                            values[name] = max(.45, min(.8, value))
                        elif name.startswith('Max Roughness'):
                            values[name] = max(.8, min(1., value))
                        elif name.startswith('Normal Intensity') and abs(value) > .6:
                            values[name] = math.copysign(.6, value)
                    channels = {n:v for n,v in scalars.items() if n.startswith('Intensity EM')}
                    peak = max((abs(v) for v in channels.values()), default=0.)
                    cap = 8. if rear else 12.
                    gain = min(1., cap/peak) if peak else 1.
                    values.update({n:v*gain for n,v in channels.items()})
                    if 'Emissive Intensity' in scalars:
                        values['Emissive Intensity'] = min(4., scalars['Emissive Intensity'])
                    if rear:
                        # The actual P4 opacity graph lerps to a constant with
                        # HeightRoughnessMask*roughness as its unclamped alpha.
                        # Source values 3 and 50 extrapolate outside the intended
                        # interpolation range; .6 bounds the inherited texture.
                        for name, value in {'Height Roughness Mask':.6, 'Opacity':.7,
                                            'Opacity_Lerp':.15}.items():
                            if name not in scalars:
                                raise RuntimeError('Inspected rear pane interface changed: '+name)
                            values[name] = value
                    if screen:
                        if not is_translucent:
                            raise RuntimeError('Inspected display blend mode changed: '+label)
                        base = child.get_editor_property('base_property_overrides')
                        base.set_editor_property('override_two_sided', True)
                        base.set_editor_property('two_sided', True)
                        child.set_editor_property('base_property_overrides', base)
                    colors = {}
                    if screen:
                        for parameter in edit.get_vector_parameter_names(parent):
                            name = str(parameter)
                            if not name.startswith(('Color 1 EM', 'Color 2 EM')):
                                continue
                            color = edit.get_material_instance_vector_parameter_value(parent, parameter)
                            # Keep native dark channels dark and retain contrast;
                            # cool the existing artwork, without replacing it.
                            target = (color.r*.18, color.g*.7, color.b, color.a)
                            edit.set_material_instance_vector_parameter_value(child, parameter, u.LinearColor(*target))
                            colors[name] = list(target)
                    for name, value in values.items():
                        edit.set_material_instance_scalar_parameter_value(child, name, value)
                        if abs(edit.get_material_instance_scalar_parameter_value(child, name)-value) > .0001:
                            raise RuntimeError('Service scalar readback failed: '+name)
                    for parameter in edit.get_texture_parameter_names(parent):
                        if edit.get_material_instance_texture_parameter_value(child, parameter) != edit.get_material_instance_texture_parameter_value(parent, parameter):
                            raise RuntimeError('Service pass changed native artwork: '+str(parameter))
                    edit.update_material_instance(child)
                    rows.append({'role':role, 'source':parent.get_path_name(), 'private':child.get_path_name(),
                                 'scalars':values, 'vectors':colors, 'two_sided':screen,
                                 'textures_and_emission_channel_ratios_preserved':True})
                _assign(ctx, actor, component, slot, cache[key])
            # Inspect actual effective blend modes, never infer transparency
            # from a material's Glass name. Probe found these panes non-Nanite.
            if translucent and mesh.get_editor_property('nanite_settings').get_editor_property('enabled'):
                old = bool(component.get_editor_property('disallow_nanite'))
                component.set_editor_property('disallow_nanite', True)
                row = {'actor':label, 'component':component.get_name(), 'before':old, 'after':True}
                fallback.append(row)
                ctx.records.append({'kind':'service_translucent_nanite_fallback', **row})
    if len(displays) != 9:
        raise RuntimeError('Expected four pod, two welcome and three rear display actors; found '+str(len(displays)))
    return {'materials':rows, 'display_actors':sorted(displays), 'nanite_fallbacks':fallback}


def _fixtures(ctx, actors, u):
    targets = {'UsableLighting/Operations/Ceiling 1':(3000,(1.,.90,.76)),
        'UsableLighting/Operations/Ceiling 2':(3000,(1.,.90,.76)),
        'UsableLighting/Lounge/Ceiling 1':(2700,(.88,.81,1.)),
        'UsableLighting/Lounge/Ceiling 2':(2700,(.88,.81,1.)),
        'Operations/Ceiling pool':(750,(1.,.86,.68)),
        'Lounge/Ceiling pool':(650,(.82,.74,1.)),
        'Refine/Operations/Central task pool':(1100,(1.,.82,.63)),
        'Refine/Archive/Bay pool 2800':(400,(.72,.59,1.)),
        'Refine/Archive/Bay pool 3960':(400,(.72,.59,1.)),
        'Refine/Reception/Staff light':(1100,(1.,.87,.72))}
    rows = []
    for actor in actors:
        label = actor.get_actor_label()
        # These six fills belonged to complete wall banks retired in Operations1.
        if label.startswith('InteriorReadability/Operations face '):
            ctx.hide(actor)
        if label not in targets:
            continue
        intensity,color = targets[label]
        for c in actor.get_components_by_class(u.LocalLightComponent):
            before = {'intensity':float(c.get_editor_property('intensity')),
                      'units':str(c.get_editor_property('intensity_units')),
                      'specular_scale':float(c.get_editor_property('specular_scale'))}
            c.set_intensity_units(u.LightUnits.LUMENS)
            c.set_intensity(intensity)
            c.set_light_color(u.LinearColor(*color,1))
            c.set_editor_property('specular_scale',.15)
            row = {'label':label,'before':before,'after_lumens':intensity,'color':list(color),
                   'after_specular_scale':.15}
            ctx.records.append({'kind':'service_fixture',**row})
            rows.append(row)
    return rows


def _signage(ctx, actors, u):
    rows = []
    for actor in actors:
        label = actor.get_actor_label()
        if not ((label.startswith('Refine/Reception/Direction ') and label.endswith('/Title')) or
                label in ('Refine/Operations/Identity','Refine/Archive/Identity','Refine/Reception/Welcome')):
            continue
        c = actor.get_component_by_class(u.TextRenderComponent)
        old = float(c.get_editor_property('world_size'))
        target = (32 if '/Direction ' in label else 42 if '/Identity' in label else 26)
        c.set_world_size(target)
        bounds = c.get_text_local_size()
        width = max(abs(bounds.x),abs(bounds.y))
        # Each direction sign has an actual native 200cm frame, with 182cm
        # clear text width. Fit measured text, never allow it to cross the frame.
        if '/Direction ' in label and width > 182:
            target *= 182/width
            c.set_world_size(target)
        c.set_text_render_color(u.Color(198,221,242,255) if '/Archive/' not in label else u.Color(229,203,246,255))
        row = {'label':label,'old_size':old,'new_size':target,
               'actual_local_size':list(c.get_text_local_size().to_tuple())}
        ctx.records.append({'kind':'service_sign_legibility',**row})
        rows.append(row)
    return rows


def apply(ctx):
    """Native-probe-backed material/fixture pass; lead saves returned assets."""
    import unreal as u
    actors = list(ctx.actors)
    marker = _one(actors,'Refine/Operations/Identity')
    if TAG in map(str,marker.tags):
        raise RuntimeError('Service polish already applied; preserve reviewed candidate')
    before = {a:_pose(a) for a in actors}
    dirty = []
    finishes = _finish(ctx,actors,u,dirty)
    desk_surfaces = _desk_surfaces(ctx,actors,u,dirty)
    fixtures = _fixtures(ctx,actors,u)
    signs = _signage(ctx,actors,u)
    assert all(_pose(a)==pose for a,pose in before.items()), 'Service polish moved an existing actor'
    marker.tags = list(marker.tags)+[TAG]
    return {'module':'service_polish','dirty_assets':dirty,'finishes':finishes,
            'desk_surfaces':desk_surfaces,
            'fixtures':fixtures,'signs':signs,'basis':'RoomPass2/04,05,06,09 and native material probe',
            'existing_actor_transforms_unchanged':True,'new_furniture':0,
            'acceptance':'Requires native material compilation and fresh rendered room/contact review.'}


def apply_graphics_followup(ctx):
    """RoomPass3: readable existing displays/signs, no furniture/floor edits."""
    import unreal as u
    edit = u.MaterialEditingLibrary
    actors = list(ctx.actors)
    marker = _one(actors, 'Refine/Operations/Identity')
    tag = 'StationServiceGraphics20261006'
    if TAG not in map(str, marker.tags) or tag in map(str, marker.tags):
        raise RuntimeError('Graphics follow-up requires exactly the reviewed first polish')
    poses = {a:_pose(a) for a in actors}
    dirty, cache, screens, signs = [], {}, [], []
    p3 = '/Game/P1toP5_Bundle/P3_ComputerStation/Materials/Instances/Base/'
    p4 = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Materials/Instances/Translucent/'
    variants = {
        'OperationsNative/Command island Port South/SM_SciFiScreen_V1_Part3':
            p3+'MI_Glass02_SciFiScreen_V1_Part3_V2_Curve_V1',
        'OperationsNative/Command island Port North/SM_SciFiScreen_V1_Part3':
            p3+'MI_Glass02_SciFiScreen_V1_Part3_V2_Curve_V2',
        'OperationsNative/Command island Starboard South/SM_SciFiScreen_V1_Part3':
            p3+'MI_Glass02_SciFiScreen_V1_Part3_RobotScreen_V3',
        'OperationsNative/Command island Starboard North/SM_SciFiScreen_V1_Part3':
            p3+'MI_Glass02_SciFiScreen_V1_Part3_SpacemanScreen_V1',
        'Refine/Reception/Welcome console -130':
            p3+'MI_Glass02_SciFiScreen_V1_Part3_Keos_V1',
        'Refine/Reception/Welcome console 130':
            p3+'MI_Glass02_SciFiScreen_V1_Part3_RobotScreen_V2',
        'Refine/Operations/Rear data 1/Glass':
            p4+'MI_DigitalGlass_Window400X200_Graph1',
        'Refine/Operations/Rear data 2/Glass':
            p4+'MI_DigitalGlass_Window400X200_KeosAdvertisment',
        'Refine/Operations/Rear data 3/Glass':
            p4+'MI_DigitalGlass_Window400X200_Graph2'}
    for label, source_path in variants.items():
        actor = _one(actors, label)
        rear = '/Rear data ' in label
        expected = 'SM_Window400X200_V2_Part2_DigitalWindow' if rear else 'SM_SciFiScreen_V1_Part3'
        components = [c for c in actor.get_components_by_class(u.StaticMeshComponent)
                      if c.static_mesh and c.static_mesh.get_name() == expected]
        if len(components) != 1:
            raise RuntimeError('Native display mesh changed: '+label)
        component = components[0]
        source = ctx.asset(source_path)
        if not isinstance(source, u.MaterialInstanceConstant) or _blend(source, u) != u.BlendMode.BLEND_TRANSLUCENT:
            raise RuntimeError('Expected original native translucent display: '+source_path)
        child = _child(source, 'GraphicClarity', u, dirty, cache)
        scalars = {str(n):float(edit.get_material_instance_scalar_parameter_value(source, n))
                   for n in edit.get_scalar_parameter_names(source)}
        channels = {n:v for n,v in scalars.items() if n.startswith('Intensity EM')}
        peak = max((abs(v) for v in channels.values()), default=0.)
        if not channels or peak <= 0 or not math.isfinite(peak):
            raise RuntimeError('Missing native graphic intensity channels: '+source_path)
        gain = 24./peak
        values = {n:v*gain for n,v in channels.items()}
        # A display must retain a stable dark backdrop instead of reflecting
        # the busy world through its artwork. Keep the native translucent pane.
        values['Opacity'] = .88
        if rear:
            values.update({'Height Roughness Mask':.1, 'Opacity_Lerp':0.})
        for name,value in values.items():
            if name not in scalars:
                raise RuntimeError('Native display interface changed: '+name)
            edit.set_material_instance_scalar_parameter_value(child, name, value)
            if abs(edit.get_material_instance_scalar_parameter_value(child, name)-value) > .0001:
                raise RuntimeError('Display scalar readback failed: '+name)
        base = child.get_editor_property('base_property_overrides')
        for name,value in (('override_two_sided',True), ('two_sided',True),
                           ('override_shading_model',True), ('shading_model',u.MaterialShadingModel.MSM_UNLIT)):
            base.set_editor_property(name, value)
        child.set_editor_property('base_property_overrides', base)
        switches = set(map(str, edit.get_static_switch_parameter_names(source)))
        if 'Activate Cov1' in switches:
            edit.set_material_instance_static_switch_parameter_value(child, 'Activate Cov1', False)
        for parameter in edit.get_vector_parameter_names(source):
            if str(parameter).startswith(('Color 1 EM', 'Color 2 EM')):
                color = edit.get_material_instance_vector_parameter_value(source, parameter)
                edit.set_material_instance_vector_parameter_value(child, parameter,
                    u.LinearColor(color.r*.25, color.g*.8, color.b, color.a))
        for parameter in edit.get_texture_parameter_names(source):
            if edit.get_material_instance_texture_parameter_value(child, parameter) != edit.get_material_instance_texture_parameter_value(source, parameter):
                raise RuntimeError('Display variant lost its original native texture: '+str(parameter))
        edit.update_material_instance(child)
        for slot in range(component.get_num_materials()):
            _assign(ctx, actor, component, slot, child)
        screens.append({'actor':label, 'source_variant':source_path, 'private':child.get_path_name(),
                        'source_relative_gain':gain, 'scalars':values, 'unlit':True,
                        'native_texture_uv_animation_preserved':True})

    # Keep the actual central service workstation's mesh-specific interface;
    # strengthen its three existing screens, not unrelated metal/light slots.
    for suffix in ('SM_GoliathLargeScreen01', 'SM_GoliathMediumScreen01', 'SM_GoliathMediumScreen2'):
        actor = _one(actors, 'Engineering/Primary workstation/'+suffix)
        component = actor.get_component_by_class(u.StaticMeshComponent)
        if component.get_num_materials() != 2:
            raise RuntimeError('Goliath screen slot layout changed')
        parent = component.get_material(1)
        key = ('ServiceScreen', parent.get_path_name())
        if key not in cache:
            child = _child(parent, 'ServiceScreen', u, dirty, cache)
            values = {str(n):float(edit.get_material_instance_scalar_parameter_value(parent, n))
                      for n in edit.get_scalar_parameter_names(parent) if str(n).startswith('Intensity EM')}
            peak = max((abs(v) for v in values.values()), default=0.)
            if not values or peak <= 0 or not math.isfinite(peak):
                raise RuntimeError('Goliath display lost native emission channels')
            gain = 18./peak
            for name,value in values.items():
                edit.set_material_instance_scalar_parameter_value(child, name, value*gain)
            base = child.get_editor_property('base_property_overrides')
            base.set_editor_property('override_shading_model', True)
            base.set_editor_property('shading_model', u.MaterialShadingModel.MSM_UNLIT)
            child.set_editor_property('base_property_overrides', base)
            edit.update_material_instance(child)
            screens.append({'actor_group':'Goliath service display', 'source':parent.get_path_name(),
                            'private':child.get_path_name(), 'source_relative_gain':gain,
                            'native_texture_uv_animation_preserved':True})
        _assign(ctx, actor, component, 1, cache[key])

    # Existing project material is a verified Engine UnlitText derivative with
    # the original font/alpha graph and a single OutpostTextGain parameter.
    text_source = ctx.asset('/Game/OutpostSandbox/Materials/M_OutpostReadableTextOneSided')
    if text_source.get_editor_property('shading_model') != u.MaterialShadingModel.MSM_UNLIT or text_source.get_editor_property('two_sided'):
        raise RuntimeError('Expected preserved one-sided unlit font material')
    if 'OutpostTextGain' not in set(map(str, edit.get_scalar_parameter_names(text_source))):
        raise RuntimeError('Readable font gain interface changed')
    text_material = _child(text_source, 'ServiceLabels', u, dirty, cache)
    edit.set_material_instance_scalar_parameter_value(text_material, 'OutpostTextGain', 3.)
    edit.update_material_instance(text_material)
    service_faces = {'Services/'+name+'/Face' for name in (
        'FLIGHT UPGRADES', 'SHIP & PARTS', 'PILOT LEADERBOARD', 'CONTRACT EXCHANGE', 'TRADE NETWORK')}
    for actor in actors:
        label = actor.get_actor_label()
        if not (label.startswith(('Refine/Operations/', 'Refine/Archive/', 'Refine/Reception/')) or label in service_faces):
            continue
        component = actor.get_component_by_class(u.TextRenderComponent)
        if not component or actor.get_editor_property('hidden'):
            continue
        before = component.get_editor_property('text_material')
        component.set_text_material(text_material)
        component.set_text_render_color(u.Color(100,210,255,255))
        old_size = float(component.get_editor_property('world_size'))
        size, width = old_size, None
        if label in ('Refine/Operations/Identity','Refine/Archive/Identity'):
            size, width = 58., 1450.
        elif label == 'Refine/Archive/Home direction':
            size, width = 30., 350.
        elif label == 'Refine/Reception/Welcome':
            size, width = 32., 440.
        elif '/Direction ' in label:
            size, width = 38., 182.
        elif label in service_faces:
            size, width = 26., 240.
        component.set_world_size(size)
        measured = component.get_text_local_size()
        measured_width = max(abs(measured.x), abs(measured.y))
        if width and measured_width > width:
            size *= width/measured_width
            component.set_world_size(size)
        row = {'actor':label, 'before_material':before.get_path_name() if before else None,
               'after_material':text_material.get_path_name(), 'old_size':old_size,
               'new_size':size, 'measured_size':list(component.get_text_local_size().to_tuple()),
               'one_sided':True, 'font_and_text_unchanged':True}
        ctx.records.append({'kind':'service_unlit_label', **row})
        signs.append(row)
    ctx.hide(_one(actors, 'Lounge/Archive title'))
    if not service_faces <= {row['actor'] for row in signs}:
        raise RuntimeError('Missing actual Operations service face labels')
    assert all(_pose(a)==pose for a,pose in poses.items()), 'Graphics follow-up moved an actor'
    marker.tags = list(marker.tags)+[tag]
    return {'module':'service_graphics_followup', 'dirty_assets':dirty, 'screens':screens,
            'signs':signs, 'retired_duplicate':'Lounge/Archive title',
            'furniture_floor_globe_collision_and_actor_transforms_unchanged':True,
            'basis':'RoomPass3/04,05,06,09,10; matched existing kit screen variants and project unlit font graph',
            'acceptance':'Native compilation and fresh rendered service/sign review required.'}
