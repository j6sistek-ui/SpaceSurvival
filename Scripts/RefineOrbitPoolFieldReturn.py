"""Quiet, sequence-synchronized light spill from the pool rail emitters.

Only the private owner-preview sequence and four new local lights are changed.
The lead owns backups, map/asset saves and actual playback inspection.
"""
from OutpostGeometryUtils import mesh_union


def apply(ctx, sequence):
    import unreal as u
    from RefineStationOrbitPool import MAP
    from AuthorOrbitPoolSequence import ASSET
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name().split('.')[0] != MAP or sequence.get_path_name().split('.')[0] != ASSET:
        raise RuntimeError('Return lighting belongs only to the private Orbit Pool scene')
    prefix = 'Refine/OrbitPool/Return spill '
    if any(a.get_actor_label().startswith(prefix) for a in ctx.actors):
        raise RuntimeError('Return lighting already exists; do not duplicate it')
    rows = []
    for index in range(4):
        label = 'Refine/OrbitPool/Field return emitter ' + str(index)
        found = [a for a in ctx.actors if a.get_actor_label() == label]
        if len(found) != 1:
            raise RuntimeError('Expected the measured rail housing: ' + label)
        center, extent = mesh_union(found[0])
        light = ctx.light('OrbitPool/Return spill ' + str(index),
                          (center.x, center.y, center.z + extent.z + .25),
                          0., 70., (.25, .7, 1.), False)
        component = light.get_component_by_class(u.PointLightComponent)
        component.set_editor_property('source_radius', 1.)
        component.set_editor_property('specular_scale', .2)
        component.set_editor_property('volumetric_scattering_intensity', 0.)
        owner = u.MovieSceneSequenceExtensions.add_possessable(sequence, light)
        binding = u.MovieSceneSequenceExtensions.add_possessable(sequence, component)
        u.MovieSceneBindingExtensions.set_parent(binding, owner)
        u.MovieSceneBindingExtensions.set_name(binding, 'Return spill ' + str(index))
        track = u.MovieSceneBindingExtensions.add_track(binding, u.MovieSceneFloatTrack)
        u.MovieScenePropertyTrackExtensions.set_property_name_and_path(track, 'Intensity', 'Intensity')
        section = track.add_section()
        u.MovieSceneSectionExtensions.set_range(section, 0, 420)
        section.set_completion_mode(u.MovieSceneCompletionMode.RESTORE_STATE)
        channels = u.MovieSceneSectionExtensions.get_all_channels(section)
        if len(channels) != 1:
            raise RuntimeError('Intensity track must have exactly one scalar channel')
        channel = channels[0]
        channel.set_default(0.)
        # Soft rise before the lift, sustained through the glide, then fade out.
        keys = ((0, 0.), (294, 0.), (309, 12.), (399, 12.), (417, 0.), (420, 0.))
        for frame, value in keys:
            key = channel.add_key(u.FrameNumber(frame), value, 0.,
                                  u.MovieSceneTimeUnit.DISPLAY_RATE, u.MovieSceneKeyInterpolation.LINEAR)
            if abs(key.get_value() - value) > 1e-6:
                raise RuntimeError('Return light key readback differs')
        if str(u.MovieScenePropertyTrackExtensions.get_property_path(track)) != 'Intensity':
            raise RuntimeError('Return light track bound to a different property')
        rows.append({'label': light.get_actor_label(), 'keys_frame_lumens': keys,
                     'radius_cm': 70., 'casts_shadows': False})
    return {'lights': rows, 'scope': 'Ambient field-return cue, no gameplay or global lighting change'}
