"""Temporary Wayfarer daylight for layout editing; never saves or changes game lighting."""
import unreal as u

TARGET = '/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime'
OWNER = 'SSDaylightPreview'
_actors = []
_hidden = []
_entries = []


def disable():
    """Restore each existing actor's editor visibility and remove only our temporary rig."""
    if u.get_editor_subsystem(u.LevelEditorSubsystem).is_in_play_in_editor():
        raise RuntimeError('Stop Play before changing the daylight preview.')
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    for actor, was_hidden in _hidden:
        if u.SystemLibrary.is_valid(actor):
            actor.set_is_temporarily_hidden_in_editor(was_hidden)
    _hidden.clear()
    for actor in _actors:
        if u.SystemLibrary.is_valid(actor):
            actors.destroy_actor(actor)
    _actors.clear()
    u.log('Station daylight preview OFF; original editor lighting restored.')


def enable():
    """Build a transient, editor-only sun/sky/exposure rig on the current station."""
    levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
    if levels.is_in_play_in_editor():
        raise RuntimeError('Stop Play before changing the daylight preview.')
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if not world or world.get_path_name().split('.')[0] != TARGET:
        raise RuntimeError('Open the current Wayfarer station first.')
    disable()
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    cube = u.load_asset('/Engine/MapTemplates/Sky/DaylightAmbientCubemap')
    if not cube:
        raise RuntimeError('Engine daylight cubemap is unavailable.')

    def spawn(cls, name):
        actor = actors.spawn_actor_from_class(cls, u.Vector(), transient=True)
        if not actor:
            raise RuntimeError('Cannot create daylight preview ' + name)
        _actors.append(actor)
        actor.set_actor_label('Daylight preview / ' + name)
        actor.set_editor_property('is_editor_only_actor', True)
        return actor

    try:
        for actor in actors.get_all_level_actors():
            # Temporary editor visibility does not modify the saved actor or its game visibility.
            tags = {str(tag) for tag in actor.tags}
            if (isinstance(actor, (u.DirectionalLight, u.SkyLight, u.SkyAtmosphere))
                    or 'OutpostRole:Sky' in tags
                    or actor.get_actor_label() in ('Environment/Starfield', 'Sandbox stars')):
                _hidden.append((actor, actor.is_temporarily_hidden_in_editor()))
                actor.set_is_temporarily_hidden_in_editor(True)

        sun = spawn(u.DirectionalLight, 'Sun')
        sun.set_actor_rotation(u.Rotator(pitch=-45, yaw=-35), False)
        light = sun.get_component_by_class(u.DirectionalLightComponent)
        light.set_mobility(u.ComponentMobility.MOVABLE)
        light.set_intensity(30000.)
        light.set_light_color(u.LinearColor(1., .97, .93, 1.))
        light.set_editor_property('atmosphere_sun_light', True)
        light.set_editor_property('light_source_angle', 1.)
        sky = spawn(u.SkyLight, 'Ambient fill')
        ambient = sky.get_component_by_class(u.SkyLightComponent)
        ambient.set_mobility(u.ComponentMobility.MOVABLE)
        ambient.set_editor_property('source_type', u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
        ambient.set_cubemap(cube)
        ambient.set_intensity(4000.)
        ambient.set_editor_property('lower_hemisphere_is_black', False)
        spawn(u.SkyAtmosphere, 'Blue sky')

        exposure = spawn(u.PostProcessVolume, 'Stable exposure')
        exposure.set_editor_property('unbound', True)
        exposure.set_editor_property('priority', 10000.)
        settings = exposure.get_editor_property('settings')
        # This project uses the legacy luminance range. Do not pass EV numbers as luminance.
        extended = u.SystemLibrary.get_console_variable_int_value('r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange')
        brightness = 14. if extended else 2048.
        for prop, value in (
            ('override_auto_exposure_method', True),
            ('auto_exposure_method', u.AutoExposureMethod.AEM_HISTOGRAM),
            ('override_auto_exposure_min_brightness', True), ('auto_exposure_min_brightness', brightness),
            ('override_auto_exposure_max_brightness', True), ('auto_exposure_max_brightness', brightness),
            ('override_auto_exposure_bias', True), ('auto_exposure_bias', 0.),
            ('override_bloom_intensity', True), ('bloom_intensity', .15),
        ):
            settings.set_editor_property(prop, value)
        exposure.set_editor_property('settings', settings)
        u.log('Station daylight preview ON. SS Prefabs > Restore game lighting turns it off. Nothing saved.')
    except Exception:
        disable()
        raise


@u.uclass()
class SSDaylightMenuEntry(u.ToolMenuEntryScript):
    @u.ufunction(override=True)
    def execute(self, context):
        try:
            if str(self.data.name).endswith('On'):
                enable()
            else:
                disable()
        except Exception as error:
            u.EditorDialog.show_message('Station lighting', str(error), u.AppMsgType.OK)


def register():
    menus = u.ToolMenus.get()
    if menus is None:
        return
    menus.unregister_owner_by_name(OWNER)
    _entries.clear()
    menu = menus.extend_menu('LevelEditor.MainMenu.SSPrefabs')
    for name, label in (
        ('On', 'Daylight editing preview'),
        ('Off', 'Restore game lighting'),
    ):
        entry = SSDaylightMenuEntry()
        entry.init_entry(u.Name(OWNER), menu.menu_name, u.Name('Station lighting'), u.Name(OWNER + name),
                         label, 'Temporary editor lighting only. Your saved station and Play lighting stay unchanged.')
        entry.register_menu_entry()
        _entries.append(entry)
    menus.refresh_all_widgets()
