"""Build the character photo studio: one private level with a grey cyclorama, three-point lighting, a locked
exposure and a camera. Characters are never saved into it; CaptureStudio.py spawns them per run.

  UnrealEditor-Cmd.exe <project> -unattended -RenderOffscreen -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/BuildStudio.py"
  set SS_STUDIO_REBUILD=1 to replace an existing studio.

The owner's call (2026-10-09): judge characters in a staged studio inside the game project - the game's own
renderer, materials and animation - instead of fighting the station's lighting. Lives under Licensed/ because
everything it exists to show is licensed or private content.
"""
import os

import unreal as u

MAP = "/Game/SpaceSurvival/Licensed/CharacterStudio/L_CharacterStudio"
LIB = u.EditorAssetLibrary
lvl = u.get_editor_subsystem(u.LevelEditorSubsystem)
actors = u.get_editor_subsystem(u.EditorActorSubsystem)


def log(s):
    u.log_warning("STUDIO| " + str(s))


if LIB.does_asset_exist(MAP):
    assert os.environ.get("SS_STUDIO_REBUILD") == "1", "studio exists; SS_STUDIO_REBUILD=1 to replace it"
    assert lvl.load_level(MAP), "load failed"          # new_level refuses an existing asset: empty it instead
    for a in actors.get_all_level_actors():
        actors.destroy_actor(a)
else:
    assert lvl.new_level(MAP), "new_level failed"
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
cube = u.load_asset("/Engine/BasicShapes/Cube")
grey = u.load_asset("/Engine/BasicShapes/BasicShapeMaterial")


def block(label, loc, scale):
    a = actors.spawn_actor_from_class(u.StaticMeshActor, u.Vector(*loc), u.Rotator(0, 0, 0))
    a.set_actor_label(label)
    c = a.static_mesh_component
    c.set_mobility(u.ComponentMobility.MOVABLE)
    c.set_static_mesh(cube)
    c.set_material(0, grey)
    a.set_actor_scale3d(u.Vector(*scale))
    return a


# Cyclorama: a 40 m floor whose top is z = 0, a wall 12 m behind the stage (the stage faces +Y, so the wall is at
# -Y; the back camera stands 6-7 m out on that side, so the wall must be well beyond it), and a lid high above so
# nothing is lit from a black sky.
block("Studio/Floor", (0, 0, -50), (40, 40, 1))
block("Studio/BackWall", (0, -1200, 450), (40, 0.2, 9))

# Ambient: a sky light from the engine's daylight cubemap, so every surface gets soft, neutral fill from all
# directions and the shadow side of a body is never black. The first studio had no ambient at all and every
# character came out as flat dark grey.
sky = actors.spawn_actor_from_class(u.SkyLight, u.Vector(0, 0, 400), u.Rotator(0, 0, 0))
sky.set_actor_label("Studio/Sky")
sc = sky.get_component_by_class(u.SkyLightComponent)
sc.set_mobility(u.ComponentMobility.MOVABLE)
sc.set_editor_property("source_type", u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
cube_map = u.load_asset("/Engine/MapTemplates/Sky/DaylightAmbientCubemap")
assert cube_map, "engine daylight cubemap missing"
sc.set_cubemap(cube_map)
sc.set_intensity(1.5)
sc.set_editor_property("lower_hemisphere_is_black", False)
sc.set_editor_property("lower_hemisphere_color", u.LinearColor(0.35, 0.35, 0.37, 1))

# Key: a sun. One hard-ish shadow with a real sun's softness, from high front-right.
sun = actors.spawn_actor_from_class(u.DirectionalLight, u.Vector(0, 0, 600), u.Rotator(0, 0, 0))
sun.set_actor_label("Studio/Key")
dc = sun.get_component_by_class(u.DirectionalLightComponent)
dc.set_mobility(u.ComponentMobility.MOVABLE)
dc.set_intensity(5.0)
dc.set_light_color(u.LinearColor(1.0, 0.96, 0.90, 1))
dc.set_cast_shadows(True)
dc.set_editor_property("light_source_angle", 2.5)
sun.set_actor_rotation(u.MathLibrary.find_look_at_rotation(u.Vector(320, 480, 430), u.Vector(0, 0, 105)), False)


def aim(a, target):
    a.set_actor_rotation(u.MathLibrary.find_look_at_rotation(a.get_actor_location(), u.Vector(*target)), False)


def spot(label, loc, target, lumens, color, outer, inner, shadows=True, radius=20.0):
    a = actors.spawn_actor_from_class(u.SpotLight, u.Vector(*loc), u.Rotator(0, 0, 0))
    a.set_actor_label(label)
    c = a.get_component_by_class(u.SpotLightComponent)
    c.set_mobility(u.ComponentMobility.MOVABLE)
    c.set_intensity_units(u.LightUnits.LUMENS)
    c.set_intensity(lumens)
    c.set_light_color(u.LinearColor(*color, 1))
    c.set_outer_cone_angle(outer)
    c.set_inner_cone_angle(inner)
    c.set_attenuation_radius(3000)
    c.set_cast_shadows(shadows)
    c.set_source_radius(radius)             # a real lamp has size: soft shadow edges instead of razor ones
    aim(a, target)
    return a


# Shaping lights on top of sun + sky: a soft cool fill front-left, a rim from behind-left for the silhouette, and
# a low front light so feet and the underside of bellies and tails read. None of them casts a second shadow.
spot("Studio/Fill", (-420, 380, 220), (0, 0, 100), 20000, (0.88, 0.94, 1.0), 75, 45, shadows=False, radius=80)
spot("Studio/Rim", (-240, -480, 420), (0, 0, 120), 40000, (1.0, 1.0, 1.0), 50, 25, shadows=False, radius=20)
spot("Studio/Low", (40, 360, 45), (0, 0, 60), 6000, (1.0, 0.98, 0.95), 70, 45, shadows=False, radius=40)

cam = actors.spawn_actor_from_class(u.CameraActor, u.Vector(0, 420, 110), u.Rotator(0, -90, 0))
cam.set_actor_label("Studio/Camera")
cam.get_component_by_class(u.CameraComponent).set_field_of_view(35)

# Manual exposure: a blank map has no post-process volume, so auto-exposure would run wild and every shot would
# meter differently. CaptureStudio.py measures one probe shot and sets the bias on the camera.
ppv = actors.spawn_actor_from_class(u.PostProcessVolume, u.Vector(0, 0, 0), u.Rotator(0, 0, 0))
ppv.set_actor_label("Studio/Exposure")
ppv.set_editor_property("unbound", True)
pp = ppv.get_editor_property("settings")
for prop, value in (("override_auto_exposure_method", True), ("auto_exposure_method", u.AutoExposureMethod.AEM_MANUAL),
                    ("override_auto_exposure_bias", True), ("auto_exposure_bias", 0.0),
                    ("override_bloom_intensity", True), ("bloom_intensity", 0.2),
                    ("override_vignette_intensity", True), ("vignette_intensity", 0.0)):
    pp.set_editor_property(prop, value)
ppv.set_editor_property("settings", pp)

# A plain game mode: the default pawn is hidden by the capture, which views through Studio/Camera instead.
world.get_world_settings().set_editor_property("default_game_mode", u.GameModeBase)
assert lvl.save_current_level(), "save failed"
log("built %s with %d actors" % (MAP, len(actors.get_all_level_actors())))
