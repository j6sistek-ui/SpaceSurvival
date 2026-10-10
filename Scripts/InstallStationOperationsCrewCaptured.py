"""Stage the exact reviewed operations-crew tracks; the root owns all saves.

No fitter or source-pose evaluation runs here. Two source clips are duplicated,
the captured121-key limb tracks are installed verbatim, and the same three
existing actors receive the reviewed mesh, placement and cosmetic idle state.
"""
import copy
import json
import math

from InspectStationOperationsCrewContacts import path, transform, require
from PreviewStationOperationsCrew6 import lifecycle, animation_values, restore
from AuthorStationWhiteFloorsRemainder4 import state as actor_state

PRIVATE = '/Game/OutpostSandbox/StationRefinement/OperationsCrewCaptured20261007'
TRACKS = tuple(part + '_' + side for side in ('l', 'r')
               for part in ('thigh', 'calf', 'foot', 'upperarm', 'lowerarm', 'hand'))
LABELS = ('Crew/Engineer', 'Crew/Ops officer', 'Refine/Operations/Operator 3')


def validate_captured(models, preview):
    """Pure schema guard. Real source/artifact hashes belong to the wrapper."""
    require(set(models) == {'Human', 'Robot'} and preview['success'] and not preview['saved'] and
            preview['retained_alien'] == 'Refine/Operations/Operator 4' and
            len(preview['operators']) == 3 and {row['label'] for row in preview['operators']} == set(LABELS),
            'Exact reviewed two-model/three-operator preview differs')
    for name, row in models.items():
        require(row == preview['models'][name] and row['keys'] == row['source_sequence_keys'] == 121 and
                row['duration_seconds'] == row['source_sequence_duration_seconds'] == 4. and
                set(row['fitted_bone_keys']) == set(row['changed_rotation_tracks']) == set(TRACKS) and
                row['bone_translations_and_scales_preserved'] and not row['saved'] and
                len(row['per_key_visible_skin_checks']) == 121 and row['native_readback_phases'] == [0, 30, 60, 90, 120] and
                set(row['source_signature']['asset_sha256']) == {'source_mesh', 'source_clip', 'skeleton'},
                'Captured full-loop motion/source signatures differ: ' + name)
        for track, keys in row['fitted_bone_keys'].items():
            require(len(keys) == 121, 'Captured track lost keys: ' + track)
            for key in keys:
                require(set(key) == {'location', 'rotation', 'scale'} and
                        len(key['location']) == len(key['scale']) == 3 and len(key['rotation']) == 4 and
                        all(isinstance(v, (int, float)) and math.isfinite(v)
                            for group in key.values() for v in group), 'Invalid captured native key: ' + track)
            dot = sum(a*b for a, b in zip(keys[0]['rotation'], keys[-1]['rotation']))
            require(abs(dot) > .99999, 'Accepted captured loop rotation differs: ' + track)
        for key in ('source_mesh', 'source_clip', 'skeleton'):
            require(row[key].startswith('/Game/') and row['source_signature'][
                    {'source_mesh': 'mesh', 'source_clip': 'clip', 'skeleton': 'skeleton'}[key]] == row[key],
                    'Captured owned mesh/clip/skeleton identity differs')
        require(all(math.isfinite(value) for value in row['actor_xy_cm'] + [row['actor_origin_z_cm']]) and
                len(row['actor_xy_cm']) == 2, 'Captured actor origin/XY invalid')
    return {'models': 2, 'tracks_per_model': 12, 'keys_per_track': 121,
            'source_pose_reevaluated': False, 'fit_reevaluated': False}


def native_api_preflight(u):
    methods = {
        'AnimPoseExtensions': ('get_anim_pose_at_time', 'get_bone_pose'),
        'EditorAssetLibrary': ('duplicate_asset', 'does_asset_exist', 'save_loaded_asset'),
        'SkeletalMeshComponent': ('get_skeletal_mesh_asset', 'set_skeletal_mesh_asset',
            'get_animation_mode', 'set_animation_mode', 'set_relative_transform',
            'set_relative_location', 'set_relative_rotation', 'set_relative_scale3d'),
        'EditorActorSubsystem': ('set_actor_transform',),
    }
    checked = {cls+'.'+method: callable(getattr(getattr(u, cls, None), method, None))
               for cls, names in methods.items() for method in names}
    require(all(checked.values()), 'Captured-only native crew API unavailable')
    return checked


def scene(actors, u):
    return json.loads(json.dumps({actor.get_path_name(): actor_state(actor, u) for actor in actors},
                                 sort_keys=True, allow_nan=False))


def apply(models, preview, restoration, accepted_scene, actors, u, progress, backups):
    """Stage two assets/three actors, returning exact native readbacks, no saves."""
    validate_captured(models, preview)
    before = scene(actors, u)
    by_label = {actor.get_actor_label(): actor for actor in actors}
    expected_original = {row['actor']: row['expected'] for row in restoration}
    require(len(restoration) == 3 and all(row['restored_exactly'] and not row['exact_deltas'] and
            not row['errors'] and row['after_restore'] == row['expected'] for row in restoration),
            'Reviewed preview must retain three exact restored original lifecycles')
    targets = []
    for placement in preview['operators']:
        actor = by_label.get(placement['label'])
        require(actor and isinstance(actor, u.SSOutpostAmbientActor) and path(actor) == placement['actor'] and
                lifecycle(actor, u) == expected_original[path(actor)] and
                not actor.get_actor_enable_collision() and not actor.get_editor_property('route_points') and
                not actor.get_editor_property('gesture_animations') and not actor.get_editor_property('drone') and
                not actor.get_editor_property('animation_managed_externally'),
                'Exact original nonblocking seated operator changed before installation')
        require(path(actor) in accepted_scene and placement['model'] in models and
                placement['mesh'] == models[placement['model']]['source_mesh'] and
                placement['clip'] == models[placement['model']]['private_clip'] and
                placement['materials'] == models[placement['model']]['source_materials'],
                'Reviewed actor and captured model disagree')
        targets.append((actor, placement))
    clips, dirty, readbacks = {}, [], {}
    for name, row in models.items():
        progress('CREATE_CAPTURED_CLIP', {'model': name, 'keys': 121, 'source_pose_reevaluated': False})
        mesh, source = u.load_asset(row['source_mesh']), u.load_asset(row['source_clip'])
        require(isinstance(mesh, u.SkeletalMesh) and isinstance(source, u.AnimSequence) and
                path(mesh.get_editor_property('skeleton')) == row['skeleton'] ==
                path(source.get_editor_property('skeleton')) and
                source.get_editor_property('data_model_interface').get_number_of_keys() == 121 and
                float(source.sequence_length) == 4. and
                [path(entry.material_interface) for entry in mesh.get_editor_property('materials')] == row['source_materials'],
                'Captured native source identities/keys/materials changed')
        output = PRIVATE+'/A_'+name+'_ReviewedSeated'
        require(not u.EditorAssetLibrary.does_asset_exist(output), 'Never overwrite an installed crew clip')
        clip = u.EditorAssetLibrary.duplicate_asset(row['source_clip'].split('.')[0], output)
        require(isinstance(clip, u.AnimSequence) and
                path(clip.get_editor_property('skeleton')) == row['skeleton'], 'Private captured clip creation failed')
        controller = clip.get_editor_property('controller')
        require(all(callable(getattr(controller, method, None)) for method in
                ('open_bracket', 'close_bracket', 'set_bone_track_keys')), 'Actual native animation controller unavailable')
        controller.open_bracket('Install exact accepted121-key operations crew motion', False)
        try:
            for track, keys in row['fitted_bone_keys'].items():
                require(controller.set_bone_track_keys(track,
                    [u.Vector(*key['location']) for key in keys],
                    [u.Quat(*key['rotation']) for key in keys],
                    [u.Vector(*key['scale']) for key in keys], False), 'Captured track write failed: '+track)
        finally:
            controller.close_bracket(False)
        require(clip.get_editor_property('data_model_interface').get_number_of_keys() == 121 and
                float(clip.sequence_length) == 4., 'Captured installed sequence count/duration differs')
        options = u.AnimPoseEvaluationOptions(optional_skeletal_mesh=mesh, evaluation_type=u.AnimDataEvalType.RAW)
        maximum_position, minimum_rotation = 0., 1.
        for frame in range(121):
            # Evaluate only the new installed clip, never the source animation or a fitter.
            pose = u.AnimPoseExtensions.get_anim_pose_at_time(clip, 4.*frame/120., options)
            for track, keys in row['fitted_bone_keys'].items():
                value = transform(u.AnimPoseExtensions.get_bone_pose(pose, track, u.AnimPoseSpaces.LOCAL))
                expected = keys[frame]
                error = math.dist(value['location'], expected['location'])
                dot = abs(sum(a*b for a,b in zip(value['rotation'], expected['rotation'])))
                maximum_position, minimum_rotation = max(maximum_position, error), min(minimum_rotation, dot)
                require(error < .015 and value['scale'] == expected['scale'] and dot > .99999,
                        'Installed native key differs from accepted captured key: '+name+'/'+track+'/'+str(frame))
            if frame % 30 == 0:
                progress('READBACK_CAPTURED_INSTALLED_KEYS', {'model': name, 'frame': frame, 'keys': 121})
        readbacks[name] = {'keys': 121, 'tracks': 12, 'max_local_position_error_cm': maximum_position,
                          'minimum_local_rotation_dot': minimum_rotation,
                          'source_pose_reevaluated': False, 'fit_reevaluated': False,
                          'source_skeleton': row['skeleton'], 'installed_clip': path(clip)}
        clips[name] = {'mesh': mesh, 'clip': clip}
        dirty.append(clip)
    placements, installations = [], []
    for actor, placement in targets:
        component = actor.character_mesh
        backup = {'restore_expected': lifecycle(actor, u), 'actor': actor,
            'transform': actor.get_actor_transform(), 'mesh': component.get_skeletal_mesh_asset(),
            'relative': component.get_relative_transform(),
            'override_materials': list(component.get_editor_property('override_materials')),
            'animation_mode': component.get_animation_mode(), 'animation_fields': animation_values(component),
            'idle_animation': actor.get_editor_property('idle_animation'),
            'phase_offset': actor.get_editor_property('phase_offset'),
            'visibility_based_anim_tick_option': component.get_editor_property('visibility_based_anim_tick_option')}
        backups.append(backup)
        model = clips[placement['model']]
        actor.set_actor_location(u.Vector(*placement['position']), False, False)
        component.set_skeletal_mesh_asset(model['mesh'])
        component.set_editor_property('override_materials', [])
        component.set_relative_location(u.Vector(), False, False)
        component.set_relative_rotation(u.Rotator(yaw=-90.), False, False)
        component.set_relative_scale3d(u.Vector(1., 1., 1.))
        actor.set_editor_property('idle_animation', model['clip'])
        actor.set_editor_property('phase_offset', placement['phase_seconds'])
        component.set_editor_property('visibility_based_anim_tick_option',
                                     u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
        component.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
        animation = component.get_editor_property('animation_data')
        animation.anim_to_play = model['clip']
        animation.saved_looping, animation.saved_playing = True, True
        animation.saved_position = placement['phase_seconds']
        animation.saved_play_rate = backup['animation_fields']['saved_play_rate']
        component.set_editor_property('animation_data', animation)
        expected = copy.deepcopy(placement)
        expected['clip'] = path(model['clip'])
        actual = lifecycle(actor, u)
        require(actual['actor_transform']['location'] == expected['position'] and
                actual['mesh_relative'] == expected['mesh_relative'] and actual['mesh'] == expected['mesh'] and
                [path(material) for material in component.get_materials()] == expected['materials'] and
                actual['idle_animation'] == expected['clip'] and actual['phase_offset'] == expected['phase_seconds'] and
                actual['animation_mode'] == str(u.AnimationMode.ANIMATION_SINGLE_NODE) and
                actual['visibility_based_anim_tick_option'] == str(u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES) and
                actual['animation_data'] == {'anim_to_play': expected['clip'], 'saved_looping': True,
                    'saved_playing': True, 'saved_position': expected['phase_seconds'],
                    'saved_play_rate': backup['animation_fields']['saved_play_rate']},
                'Actual installed actor differs from the reviewed placement/lifecycle')
        actual_scene = json.loads(json.dumps(actor_state(actor, u), sort_keys=True, allow_nan=False))
        require(actual_scene == accepted_scene[path(actor)],
                'Installed actor differs from the actual reviewed native scene')
        placements.append(expected)
        installations.append({'actor': path(actor), 'label': placement['label'],
                              'before': backup['restore_expected'], 'after': actual})
        progress('INSTALL_CAPTURED_OPERATOR', {'label': placement['label'], 'model': placement['model']})
    after = scene(actors, u)
    keys = {path(actor) for actor, _ in targets}
    require(set(before) == set(after) and
            {key:value for key,value in before.items() if key not in keys} ==
            {key:value for key,value in after.items() if key not in keys},
            'Captured crew installation changed an unrelated actor/field')
    return {'dirty_assets': dirty, 'placements': placements, 'animation_lifecycle_installation': installations,
            'native_captured_key_readbacks': readbacks, 'scene_before': before, 'scene_after': after,
            'scene_preservation_pass': True, 'changed_operator_count': 3, 'new_actor_count': 0,
            'new_light_count': 0, 'retained_alien': 'Refine/Operations/Operator 4',
            'source_pose_reevaluated': False, 'fit_reevaluated': False,
            'continuous_collision_verified': False, 'saved': False}
