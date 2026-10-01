"""One shared space-lighting setup for the private outpost scene.

An explicit, dim neutral ambient cube makes the colony silhouette readable
without importing any vendor sky, sun, fog volume or exposure profile.
"""
import unreal as u


def apply(api):
    actors = {a.get_actor_label(): a for a in api['EAS'].get_all_level_actors()}
    key = actors['Environment/Cold starlight'].get_component_by_class(u.DirectionalLightComponent)
    key.set_intensity(7.)
    key.set_light_color(u.LinearColor(.76, .86, 1., 1.))
    bounce = actors['Environment/Soft orbital bounce'].get_component_by_class(u.DirectionalLightComponent)
    bounce.set_intensity(3.)
    bounce.set_light_color(u.LinearColor(.32, .48, .72, 1.))
    name = 'Environment/Orbital ambient'
    sky = actors.get(name)
    if sky is None:
        sky = api['label'](api['EAS'].spawn_actor_from_class(u.SkyLight, u.Vector(4200, 0, 2200)), name)
    component = sky.get_component_by_class(u.SkyLightComponent)
    component.set_mobility(u.ComponentMobility.MOVABLE)
    component.set_editor_property('source_type', u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    component.set_editor_property('cubemap', api['load']('/Engine/MapTemplates/Sky/DaylightAmbientCubemap'))
    component.set_intensity(.8)
    component.set_light_color(u.LinearColor(.64, .76, 1., 1.))
    component.set_editor_property('lower_hemisphere_is_black', True)
    component.set_editor_property('lower_hemisphere_color', u.LinearColor(.025, .035, .055, 1.))
    component.recapture_sky()
    sky_material = api['load']('/Game/OutpostSandbox/Materials/MI_OutpostStars')
    api['EDIT'].set_material_instance_scalar_parameter_value(sky_material, 'SkyBrightness', .12)
    api['EDIT'].set_material_instance_scalar_parameter_value(sky_material, 'StarBrightness', 8.)
    api['LIB'].save_loaded_asset(sky_material)
    return {'key_lux': 7., 'bounce_lux': 3., 'ambient_intensity': .8,
            'ambient_cube': '/Engine/MapTemplates/Sky/DaylightAmbientCubemap',
            'global_fog': False, 'exposure_changed': False}
