"""Render the large station from fixed viewpoints, headless.

  UnrealEditor-Cmd.exe <project> -unattended -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser -ExecutePythonScript="<abs>/Scripts/RenderStationLarge.py"

Two earlier approaches failed and are worth not repeating. `HighResShot` is queued on the render
thread and needs frames, but `-ExecutePythonScript` exits the editor the moment the script returns,
so the shot never happens; and driving it from a GUI session via `-ExecCmds="py ..."` lost its
quoting crossing the shell and never ran at all. A SceneCapture2D writing into a render target
captures synchronously inside the script, so none of that matters.

Note the level's lights must be MOVABLE. Nothing runs Lightmass here, so static lights with no built
lighting contribute nothing and the level renders black.
"""
import os
import unreal

LEVEL = os.environ.get("SS_STATION_LEVEL", "/Game/SpaceSurvival/Maps/StationLarge")
OUT_DIR = unreal.Paths.convert_relative_path_to_full(
    os.path.join(unreal.Paths.project_saved_dir(), "StationLarge"))
WIDTH, HEIGHT = 2560, 1440
FOV = 88.0

# name, location (cm), rotation (pitch, yaw, roll), exposure bias
# Exposure is per shot on purpose. A bias tuned for a lit interior blows an exterior's empty space
# to white, which is exactly what one global value produced.
# Fixed exterior framings, plus interior anchors loaded from the authoring pass. Interior camera
# positions are NOT written here: guessing them from room extents put four cameras outside the
# geometry or nose-first into a pillar. AuthorStationLarge.py derives them from light positions,
# which by definition sit in open space, and carries over the vendor's own showcase cameras.
SHOTS = [
    ("01_overview", (-3600.0, -5400.0, 1900.0), (-17.0, 42.0, 0.0), 1.5),
    ("02_high_plan", (1200.0, 0.0, 4800.0), (-88.0, 0.0, 0.0), 2.0),
]

import json
ANCHORS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "Artifacts", "StationLarge", "anchors.json")
if os.path.exists(ANCHORS):
    with open(ANCHORS, encoding="utf-8") as f:
        for a in json.load(f):
            SHOTS.append((a["name"], tuple(a["loc"]),
                          (a["rot"][0], a["rot"][1], a["rot"][2]), a.get("bias", 3.5)))


def line(s=""):
    unreal.log_warning("SHOT| " + str(s))


os.makedirs(OUT_DIR, exist_ok=True)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL)
world = unreal.EditorLevelLibrary.get_editor_world()
line("level  %s" % (world.get_name() if world else "None"))
line("output %s" % OUT_DIR)

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
total = len(actors.get_all_level_actors())
line("actors %d" % total)

# 8-bit target on purpose: export_render_target writes OpenEXR for a float target, whatever
# extension you hand it, and an .exr called .png fools nothing downstream.
target = unreal.RenderingLibrary.create_render_target2d(
    world, WIDTH, HEIGHT, unreal.TextureRenderTargetFormat.RTF_RGBA8)
if target is None:
    line("could not create a render target")
    raise SystemExit

cap = actors.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(0, 0, 0),
                                    unreal.Rotator(0, 0, 0))
# The accessor name moves around between versions; take the component off the actor instead.
comp = None
for c in cap.get_components_by_class(unreal.SceneCaptureComponent2D):
    comp = c
    break
if comp is None:
    line("SceneCapture2D spawned without a capture component")
    raise SystemExit
comp.texture_target = target
comp.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
comp.fov_angle = FOV

# The vendor rooms looked right in their own maps partly because those maps carry post-process
# volumes, which are not copied here. Without one, a SceneCapture auto-exposes against whatever it
# happens to see and the interior clips to white. Lock exposure instead so every shot is comparable.
def set_exposure(bias):
    pp = unreal.PostProcessSettings()
    for prop, value in (("override_auto_exposure_method", True),
                        ("auto_exposure_method", unreal.AutoExposureMethod.AEM_HISTOGRAM),
                        ("override_auto_exposure_min_brightness", True),
                        ("override_auto_exposure_max_brightness", True),
                        # 1.0 tells the tonemapper to assume a very bright scene, so a room lit to a
                        # couple of hundred lux renders near-black and no amount of bias rescues it.
                        # These are interior-scale adaptation targets.
                        ("auto_exposure_min_brightness", 0.02),
                        ("auto_exposure_max_brightness", 0.35),
                        ("override_auto_exposure_bias", True),
                        ("auto_exposure_bias", bias),
                        ("override_bloom_intensity", True),
                        ("bloom_intensity", 0.35)):
        try:
            pp.set_editor_property(prop, value)
        except Exception as e:
            line("  pp %s: %s" % (prop, str(e)[:60]))
    comp.post_process_settings = pp


# Exposure is bracketed, not guessed and not measured in-engine. A single hand-picked bias blew out
# exteriors while crushing interiors, and RenderingLibrary.read_render_target_pixel returns near-zero
# here - it is not synchronised with capture_scene - so in-engine metering chose nonsense. Three
# exposures per shot and the pick made afterwards in PIL is reliable and costs seconds.
BRACKET = (-1.0, 0.0, 1.0, 2.0)

for prop, value in (("b_capture_every_frame", False),
                    ("b_capture_on_movement", False),
                    ("b_always_persist_rendering_state", True)):
    try:
        comp.set_editor_property(prop, value)
    except Exception:
        pass

done, failed = [], []
for name, loc, rot, bias in SHOTS:
    # unreal.Rotator is (roll, pitch, yaw). Feeding it (pitch, yaw, roll) rolls every camera on its
    # side and points it at the sky, which is exactly what the first pass produced.
    cap.set_actor_location_and_rotation(
        unreal.Vector(loc[0], loc[1], loc[2]),
        unreal.Rotator(rot[2], rot[0], rot[1]), False, False)
    wrote = 0
    for b in BRACKET:
        try:
            set_exposure(b)
            comp.capture_scene()
            unreal.RenderingLibrary.export_render_target(
                world, target, OUT_DIR, "%s__b%.1f.png" % (name, b))
            wrote += 1
        except Exception as e:
            failed.append(("%s b%.1f" % (name, b), str(e)[:100]))
    if wrote:
        done.append(name)
        line("  %-14s %d exposures  at (%7.0f %7.0f %6.0f)" % (name, wrote, loc[0], loc[1], loc[2]))
    else:
        failed.append((name, "nothing written"))

for name, why in failed:
    line("  FAILED %-14s %s" % (name, why))
line("captured %d/%d" % (len(done), len(SHOTS)))
line("SHOT| DONE")
