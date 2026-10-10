"""Unsaved, measured small placement correction for three operations staff.

Full visible skins and the four real chair/footrest poses are retained inputs.
The retained Contact5 finite triangles provide limited real support evidence;
they do not establish full-chair or continuous collision, and never save content.
The lead advances prepare() once per tick, owns captures and restores actors.
"""
import copy
import math
import traceback

import FitStationOperationsCrew5 as fitter
import StationOperationsCrewContactPatches as contact_patches
from InspectStationOperationsCrewContacts import path, transform, require
from RefineStationSocialSeatedCrew import _dot

PRIVATE = '/Game/OutpostSandbox/StationRefinement/OperationsCrewPreview20261007_5'
PLACEMENTS = (
    ('Crew/Engineer', 'Human', 'Port South', 0.),
    ('Crew/Ops officer', 'Human', 'Port North', 2.),
    ('Refine/Operations/Operator 3', 'Robot', 'Starboard South', 1.),
)
SEAT_STATUS = 'CONTACT5_NATIVE_PATCHES_LIMITED_COVERAGE_NO_CONTINUOUS_COLLISION_PROOF'
CORRECTIONS = {'Human': {'root_z_cm': .5, 'chair_y_cm': 0.},
               'Robot': {'root_z_cm': 0., 'chair_y_cm': .5}}


def native_api_preflight(u):
    methods = {
        'AnimPoseExtensions': ('get_anim_pose_at_time', 'get_bone_names', 'get_bone_pose'),
        'EditorAssetLibrary': ('duplicate_asset', 'does_asset_exist'),
        'SkeletalMeshComponent': ('get_skeletal_mesh_asset', 'set_skeletal_mesh_asset',
                                 'get_animation_mode', 'set_animation_mode', 'set_relative_transform',
                                 'set_relative_location', 'set_relative_rotation', 'set_relative_scale3d'),
        'MathLibrary': ('transform_location', 'inverse_transform_location'),
        'EditorActorSubsystem': ('set_actor_transform',),
    }
    checked = {cls + '.' + name: callable(getattr(getattr(u, cls, None), name, None))
               for cls, names in methods.items() for name in names}
    require(all(checked.values()), 'Actual unsaved crew author API unavailable')
    return checked


def support(data, actors, station, u):
    """Measured footrest in native chair space; seat coordinate is provisional."""
    chair = actors['OperationsNative/Command island ' + station + '/SM_TitaniumIndustrySeat_V1_Part2']
    footrest = actors['Refine/Operations/' + station + '/Footrest']
    basis = chair.get_component_by_class(u.StaticMeshComponent).get_world_transform()
    foot = footrest.get_component_by_class(u.StaticMeshComponent).get_world_transform()
    cube = data['fixtures']['/Engine/BasicShapes/Cube.Cube']['vertices']
    points = [u.MathLibrary.inverse_transform_location(basis,
        u.MathLibrary.transform_location(foot, u.Vector(*point))).to_tuple() for point in cube]
    bounds = [[min(p[j] for p in points) for j in range(3)],
              [max(p[j] for p in points) for j in range(3)]]
    require(len(cube) == 26 and basis.scale3d.to_tuple() == (1., 1., 1.),
            'Measured actual footrest/chair basis differs')
    return {'seat_z_cm': 60.267, 'seat_height_status': SEAT_STATUS,
            'actor_xy_cm': [0., 10.], 'footrest_box_cm': bounds,
            'hand_front_cm': 16., 'chair': chair.get_path_name(),
            'footrest': footrest.get_path_name()}


def lifecycle(actor, u):
    """Exact typed native source lifecycle, without UObject address strings."""
    component = actor.character_mesh
    animation = component.get_editor_property('animation_data')
    return {'actor_transform': transform(actor.get_actor_transform()),
            'mesh': path(component.get_skeletal_mesh_asset()),
            'mesh_relative': transform(component.get_relative_transform()),
            'override_materials': [path(value) for value in component.get_editor_property('override_materials')],
            'idle_animation': path(actor.get_editor_property('idle_animation')),
            'phase_offset': float(actor.get_editor_property('phase_offset')),
            'animation_mode': str(component.get_animation_mode()),
            'visibility_based_anim_tick_option': str(component.get_editor_property('visibility_based_anim_tick_option')),
            'animation_data': {'anim_to_play': path(animation.anim_to_play),
                               'saved_looping': bool(animation.saved_looping),
                               'saved_playing': bool(animation.saved_playing),
                               'saved_position': float(animation.saved_position),
                               'saved_play_rate': float(animation.saved_play_rate)}}


def animation_values(component):
    """Own primitive values/UObject reference, never a mutable native struct view."""
    value = component.get_editor_property('animation_data')
    return {'anim_to_play': value.anim_to_play, 'saved_looping': bool(value.saved_looping),
            'saved_playing': bool(value.saved_playing), 'saved_position': float(value.saved_position),
            'saved_play_rate': float(value.saved_play_rate)}


def prepare(data, actors, u, restoration_reports, patches):
    """Yield all121 fitted source keys, two UNSAVED clips, then three substitutions."""
    api = u.AnimPoseExtensions
    fitted, evidence = {}, {}
    for model_name in ('Human', 'Robot'):
        model = data['models'][model_name]
        mesh, source = u.load_asset(model['mesh']), u.load_asset(model['clip'])
        require(isinstance(mesh, u.SkeletalMesh) and isinstance(source, u.AnimSequence) and
                path(mesh.get_editor_property('skeleton')) == model['skeleton'] ==
                path(source.get_editor_property('skeleton')),
                'Actual source mesh/clip/skeleton identity differs')
        native_model = source.get_editor_property('data_model_interface')
        count, duration = native_model.get_number_of_keys(), float(source.sequence_length)
        require(count == 121 and duration == 4., 'Retain native four-second121-key seated source')
        source_controller = source.get_editor_property('controller')
        require(all(callable(getattr(source_controller, name, None)) for name in
                    ('open_bracket', 'close_bracket', 'set_bone_track_keys')),
                'Native source animation controller API missing before fitting')
        output = PRIVATE + '/A_' + model_name + '_ProvisionalSeated'
        require(not u.EditorAssetLibrary.does_asset_exist(output), 'Preserve existing preview derivative')
        options = u.AnimPoseEvaluationOptions(optional_skeletal_mesh=mesh, evaluation_type=u.AnimDataEvalType.RAW)
        prepared = fitter.setup(model)
        measured = support(data, actors, 'Port South' if model_name == 'Human' else 'Starboard South', u)
        measured['hand_front_cm'] = 16. if model_name == 'Human' else 20.
        correction = CORRECTIONS[model_name]
        measured['actor_xy_cm'][1] += correction['chair_y_cm']
        measured['placement_correction_cm'] = correction
        tracks = {name: [] for name in fitter.TRACKS}
        reports, readbacks, origin = [], {}, None
        body_bounds = [[math.inf] * 3, [-math.inf] * 3]
        for frame in range(count):
            seconds = duration * frame / (count - 1)
            pose = api.get_anim_pose_at_time(source, seconds, options)
            sample = {'seconds': seconds, 'bones': {bone['name']: {
                'local': transform(api.get_bone_pose(pose, bone['name'], u.AnimPoseSpaces.LOCAL)),
                'world': transform(api.get_bone_pose(pose, bone['name'], u.AnimPoseSpaces.WORLD))}
                for bone in model['geometry']['bones']}}
            if origin is None:
                source_world = fitter._forward({name: row['local'] for name, row in sample['bones'].items()},
                                               model['geometry']['bones'])
                hip = fitter._points(source_world, prepared['prepared'], prepared['contact_groups']['pelvis'])
                origin = measured['seat_z_cm'] + .5 - min(point[2] for point in hip) + correction['root_z_cm']
            local, world, skin, report = fitter.fit(model, sample, measured, prepared, origin)
            origin = report['actor_origin_z_cm']
            report['actual_cached_surface_samples'] = contact_patches.sample_skin(
                model_name, skin, origin, measured['actor_xy_cm'], patches)
            for _, point in skin:
                for axis in range(3):
                    value = point[axis] + (origin if axis == 2 else measured['actor_xy_cm'][axis])
                    body_bounds[0][axis] = min(body_bounds[0][axis], value)
                    body_bounds[1][axis] = max(body_bounds[1][axis], value)
            for name in fitter.TRACKS:
                if tracks[name] and _dot(tracks[name][-1]['rotation'], local[name]['rotation']) < 0.:
                    local[name]['rotation'] = [-v for v in local[name]['rotation']]
                tracks[name].append(copy.deepcopy(local[name]))
            report.update(frame=frame, seconds=seconds, seat_height_status=SEAT_STATUS,
                          actual_chair_contact_verified=False, actual_desk_contact_verified=False)
            reports.append(report)
            if frame % 30 == 0:
                readbacks[frame] = {'local': local, 'world': world}
            yield {'stage': 'FIT_' + model_name.upper(), 'details': {'frame': frame, 'keys': count,
                   'origin_z_cm': origin, 'seat_height_status': SEAT_STATUS}}
        for name, keys in tracks.items():
            require(abs(_dot(keys[0]['rotation'], keys[-1]['rotation'])) > .99999,
                    'Provisional private fit breaks native closed-loop rotation')
        clip = u.EditorAssetLibrary.duplicate_asset(model['clip'].split('.')[0], output)
        require(isinstance(clip, u.AnimSequence) and
                clip.get_editor_property('skeleton') == mesh.get_editor_property('skeleton'),
                'Cannot create separate unsaved fitted clip')
        controller = clip.get_editor_property('controller')
        require(all(callable(getattr(controller, name, None)) for name in
                    ('open_bracket', 'close_bracket', 'set_bone_track_keys')), 'Native animation controller API missing')
        controller.open_bracket('Unsaved provisional operations crew preview', False)
        try:
            for name, keys in tracks.items():
                require(controller.set_bone_track_keys(name,
                    [u.Vector(*row['location']) for row in keys], [u.Quat(*row['rotation']) for row in keys],
                    [u.Vector(*row['scale']) for row in keys], False), 'Private preview track write failed: ' + name)
        finally:
            controller.close_bracket(False)
        maximum_position_error = 0.
        for frame, expected in readbacks.items():
            pose = api.get_anim_pose_at_time(clip, duration * frame / (count - 1), options)
            for name, value in expected['world'].items():
                actual = api.get_bone_pose(pose, name, u.AnimPoseSpaces.WORLD)
                error = math.dist(actual.translation.to_tuple(), value['location'])
                maximum_position_error = max(maximum_position_error, error)
                require(error < .015, 'Native provisional full pose readback differs: ' + name)
                actual_local = api.get_bone_pose(pose, name, u.AnimPoseSpaces.LOCAL)
                require(abs(_dot(actual_local.rotation.to_tuple(), expected['local'][name]['rotation'])) > .99999,
                        'Native provisional rotation readback differs: ' + name)
        fitted[model_name] = {'mesh': mesh, 'clip': clip, 'origin_z_cm': origin, 'support': measured}
        evidence[model_name] = {'source_mesh': model['mesh'], 'source_clip': model['clip'], 'private_clip': path(clip),
            'keys': count, 'duration_seconds': duration, 'changed_rotation_tracks': list(fitter.TRACKS),
            'bone_translations_and_scales_preserved': True, 'native_readback_phases': list(readbacks),
            'max_native_position_error_cm': maximum_position_error, 'per_key_visible_skin_checks': reports,
            'fitted_complete_skin_bounds_chair_cm': body_bounds,
            'placement_correction_cm': correction,
            'cached_contact_summary': contact_patches.summarize(reports),
            'seat_height_status': SEAT_STATUS, 'actual_chair_contact_verified': False,
            'actual_desk_contact_verified': False, 'saved': False}
        yield {'stage': 'UNSAVED_CLIP_' + model_name.upper(), 'details': {k: v for k, v in evidence[model_name].items()
                                                                      if k != 'per_key_visible_skin_checks'}}
    backups, substitutions = [], []
    try:
        for label, model_name, station, phase in PLACEMENTS:
            actor = actors[label]; component = actor.character_mesh; row = fitted[model_name]
            basis = actors['OperationsNative/Command island ' + station + '/SM_TitaniumIndustrySeat_V1_Part2'].static_mesh_component.get_world_transform()
            actual_support = support(data, actors, station, u)
            require(max(abs(a - b) for expected, actual in zip(row['support']['footrest_box_cm'], actual_support['footrest_box_cm'])
                        for a, b in zip(expected, actual)) < .005, 'Reused clip footrest basis differs across real chairs')
            backup = {'restore_expected': lifecycle(actor, u), 'actor': actor, 'transform': actor.get_actor_transform(), 'mesh': component.get_skeletal_mesh_asset(),
                'relative': component.get_relative_transform(), 'override_materials': list(component.get_editor_property('override_materials')),
                'animation_mode': component.get_animation_mode(),
                'animation_fields': animation_values(component),
                'idle_animation': actor.get_editor_property('idle_animation'),
                'phase_offset': actor.get_editor_property('phase_offset'),
                'visibility_based_anim_tick_option': component.get_editor_property('visibility_based_anim_tick_option')}
            backups.append(backup)
            require(not actor.get_actor_enable_collision() and not actor.get_editor_property('route_points') and
                    not actor.get_editor_property('gesture_animations') and not actor.get_editor_property('drone') and
                    not actor.get_editor_property('animation_managed_externally'), 'Retain existing nonblocking seated lifecycle')
            position = u.MathLibrary.transform_location(basis, u.Vector(
                *row['support']['actor_xy_cm'], row['origin_z_cm']))
            actor.set_actor_location(position, False, False)
            # Preserve the native actor yaw; only its source mesh local yaw is retained.
            component.set_skeletal_mesh_asset(row['mesh'])
            component.set_editor_property('override_materials', [])
            component.set_relative_location(u.Vector(), False, False)
            component.set_relative_rotation(u.Rotator(yaw=-90.), False, False)
            component.set_relative_scale3d(u.Vector(1., 1., 1.))
            expected_materials = [entry.material_interface for entry in row['mesh'].get_editor_property('materials')]
            require(expected_materials and all(expected_materials) and list(component.get_materials()) == expected_materials,
                    'Owned human/robot default materials were not applied exactly')
            actor.set_editor_property('idle_animation', row['clip']); actor.set_editor_property('phase_offset', phase)
            component.set_editor_property('visibility_based_anim_tick_option', u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
            component.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
            animation = component.get_editor_property('animation_data')
            animation.anim_to_play, animation.saved_looping, animation.saved_playing, animation.saved_position = row['clip'], True, True, phase
            component.set_editor_property('animation_data', animation)
            substitutions.append({'label': label, 'model': model_name, 'actor': path(actor), 'position': list(position.to_tuple()),
                'chair': actual_support['chair'], 'footrest': actual_support['footrest'], 'phase_seconds': phase,
                'mesh': path(row['mesh']), 'clip': path(row['clip']), 'mesh_relative': transform(component.get_relative_transform()),
                'materials': [path(material) for material in component.get_materials()], 'seat_height_status': SEAT_STATUS})
        yield {'stage': 'THREE_UNSAVED_OPERATOR_SUBSTITUTIONS', 'details': {'count': len(substitutions), 'contacts_fitted': False},
               'result': {'success': True, 'saved': False, 'contacts_fitted': False, 'models': evidence,
                          'operators': substitutions, 'retained_alien': 'Refine/Operations/Operator 4',
                          'backups': backups, 'private_clips': [row['clip'] for row in fitted.values()]}}
    except Exception:
        restoration_reports.extend(restore(backups, u))
        raise


def exact_deltas(before, after, prefix=''):
    if isinstance(before, dict) and isinstance(after, dict):
        rows = []
        for key in sorted(set(before) | set(after)):
            name = prefix + '/' + key
            if key not in before or key not in after:
                rows.append({'field': name, 'before': before.get(key), 'after': after.get(key)})
            else:
                rows.extend(exact_deltas(before[key], after[key], name))
        return rows
    return [] if before == after else [{'field': prefix, 'before': before, 'after': after}]


def restore(backups, u):
    """Restore every actor, preserving exact native readbacks even on failures."""
    eas = u.get_editor_subsystem(u.EditorActorSubsystem)
    results = []
    for row in backups:
        actor = row['actor']
        result = {'actor': path(actor), 'expected': row['restore_expected'], 'errors': [], 'write_attempts': []}
        def attempt(field, function):
            try:
                function()
                result['write_attempts'].append({'field': field, 'success': True})
            except Exception:
                error = traceback.format_exc()
                result['write_attempts'].append({'field': field, 'success': False, 'error': error})
                result['errors'].append(field + ': ' + error)
        try:
            component = actor.character_mesh
        except Exception:
            result['errors'].append(traceback.format_exc())
            result['restored_exactly'] = False
            results.append(result)
            continue
        try:
            result['before_restore'] = lifecycle(actor, u)
        except Exception:
            result['errors'].append(traceback.format_exc())
        attempt('actor_transform', lambda: require(eas.set_actor_transform(actor, row['transform']),
                'Cannot restore original unsaved actor transform'))
        attempt('mesh', lambda: component.set_skeletal_mesh_asset(row['mesh']))
        attempt('override_materials', lambda: component.set_editor_property('override_materials', row['override_materials']))
        attempt('mesh_relative', lambda: component.set_relative_transform(row['relative'], False, False))
        attempt('idle_animation', lambda: actor.set_editor_property('idle_animation', row['idle_animation']))
        attempt('phase_offset', lambda: actor.set_editor_property('phase_offset', row['phase_offset']))
        attempt('animation_mode', lambda: component.set_animation_mode(row['animation_mode']))
        def restore_animation():
            animation = component.get_editor_property('animation_data')
            values = row['animation_fields']
            animation.anim_to_play = values['anim_to_play']
            animation.saved_looping, animation.saved_playing = values['saved_looping'], values['saved_playing']
            animation.saved_position, animation.saved_play_rate = values['saved_position'], values['saved_play_rate']
            component.set_editor_property('animation_data', animation)
        attempt('animation_data', restore_animation)
        attempt('visibility_based_anim_tick_option', lambda: component.set_editor_property(
                'visibility_based_anim_tick_option', row['visibility_based_anim_tick_option']))
        try:
            result['after_restore'] = lifecycle(actor, u)
            result['exact_deltas'] = exact_deltas(result['expected'], result['after_restore'])
        except Exception:
            result['errors'].append(traceback.format_exc())
        result['restored_exactly'] = not result['errors'] and 'exact_deltas' in result and not result['exact_deltas']
        results.append(result)
    return results
