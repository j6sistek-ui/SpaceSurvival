"""In-engine turnaround of one crew mesh with its real materials: an offscreen SceneCapture2D in the startup world,
nothing saved. Clay renders (render_strip.py) show deformation; this shows what the player sees - textures, shading.

  set SS_CAP_MESH=/Game/.../SK_Silver       SS_CAP_OUT=<folder>   SS_CAP_NAME=Silver
      (several meshes separated by commas = parts of one body, e.g. a glTF import)
  UnrealEditor-Cmd.exe <project> -unattended -RenderOffscreen -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/capture_ue.py"

Writes <name>_<view>__b<bias>.png: eight yaws around the body plus head close-ups, each bracketed in exposure (the
SceneCapture cannot meter itself; pick afterwards). Lights are movable because nothing builds lighting here.

REFERENCE POSE ONLY. A -ExecutePythonScript world never ticks, and every route tried for posing a clip without a
tick failed (set_position/override_animation_data + mesh re-init, PoseableMeshComponent bone writes): the bones
stayed at the bind pose. Animated, game-lit checks need a ticking route (-game or Movie Render Queue) - this
script is the full-body material/bind check that the clay sheets are not. (2026-10-08: the Elf passed every clay
sheet and still warped in game; Silver's twisted thighs were visible here and nowhere else.)
"""
import math
import os

import unreal as u

def game_path(p):
    # Git Bash rewrites /Game/... and /Engine/... into Windows paths
    for root in ("/Game/", "/Engine/"):
        if p and root in p:
            return p[p.index(root):]
    return p


MESHES = [game_path(p) for p in os.environ["SS_CAP_MESH"].split(",") if p]   # several = parts of one body (glTF)
MESH = MESHES[0]
OUT = os.environ["SS_CAP_OUT"]
NAME = os.environ.get("SS_CAP_NAME", "cap")
# SS_CAP_POS=x,y,z puts the body somewhere other than the world origin (the station map has actors standing there)
POS = u.Vector(*[float(v) for v in os.environ.get("SS_CAP_POS", "0,0,0").split(",")])
W, H, FOV = 900, 1200, 30.0
BRACKET = (0.0, 1.0, 2.0)


def log(s):
    u.log_warning("CAPUE| " + str(s))


os.makedirs(OUT, exist_ok=True)
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
mesh = u.load_asset(MESH)
assert mesh, "mesh not found: " + MESH

# SS_CAP_ACTOR=<mesh path>: capture the FIRST placed actor in the open map that carries that skeletal mesh, in place,
# with the map's own lights and that actor's own materials - what the game shows, not a fresh spawn under sun lights.
ACTOR_MESH = game_path(os.environ.get("SS_CAP_ACTOR", ""))
placed = None
if ACTOR_MESH:
    for a in actors.get_all_level_actors():
        comp = a.get_component_by_class(u.SkeletalMeshComponent)
        if comp and comp.get_skeletal_mesh_asset() and comp.get_skeletal_mesh_asset().get_path_name().startswith(ACTOR_MESH):
            placed = a
            log("placed actor %s (%s) at %s, materials %s" % (a.get_actor_label(), a.get_class().get_name(), a.get_actor_location(),
                [comp.get_material(i).get_name() if comp.get_material(i) else None for i in range(comp.get_num_materials())]))
            break
    assert placed, "no placed actor carries " + ACTOR_MESH
    POS = placed.get_actor_location()
floor = None if placed else actors.spawn_actor_from_class(u.StaticMeshActor, POS, u.Rotator(0, 0, 0))
if floor:
    floor.static_mesh_component.set_static_mesh(u.load_asset("/Engine/BasicShapes/Plane"))
    floor.set_actor_scale3d(u.Vector(30, 30, 1))
    floor.static_mesh_component.set_material(0, u.load_asset("/Engine/BasicShapes/BasicShapeMaterial"))


def light(rot, lux, color=(1, 1, 1)):
    a = actors.spawn_actor_from_class(u.DirectionalLight, POS + u.Vector(0, 0, 300), u.Rotator(rot[2], rot[0], rot[1]))
    c = a.get_component_by_class(u.DirectionalLightComponent)
    c.set_mobility(u.ComponentMobility.MOVABLE)
    c.set_intensity(lux)
    c.set_light_color(u.LinearColor(*color, 1))
    if os.environ.get("SS_CAP_SHADOWS", "1") == "0":   # tells shadow acne from shading faults
        c.set_cast_shadows(False)
    return a


if not placed:
    light((-40, 35, 0), 6.0)                      # key, front-left high
    light((-20, -140, 0), 2.0, (0.85, 0.9, 1))    # fill, other side
    light((-25, 180, 0), 4.0)                     # rim from behind
    sky = actors.spawn_actor_from_class(u.SkyLight, POS + u.Vector(0, 0, 400), u.Rotator(0, 0, 0))
    sc = sky.get_component_by_class(u.SkyLightComponent)
    sc.set_mobility(u.ComponentMobility.MOVABLE)
    sc.set_intensity(0.6)

# Reference pose, Unreal's own skinning: a bad bind pose shows here exactly as it does in game.
if placed:
    body = placed
    comp = placed.get_component_by_class(u.SkeletalMeshComponent)
    mesh = comp.get_skeletal_mesh_asset()
else:
    body = actors.spawn_actor_from_class(u.SkeletalMeshActor, POS, u.Rotator(0, 0, 0))
    comp = body.skeletal_mesh_component
    comp.set_skeletal_mesh_asset(mesh)
comp.set_forced_lod(1)
# SS_CAP_MATERIAL=<material path> overrides every slot (a plain grey tells mesh faults from texture faults)
if os.environ.get("SS_CAP_MATERIAL"):
    override = u.load_asset(game_path(os.environ["SS_CAP_MATERIAL"]))
    slots = max(comp.get_num_materials(), len(mesh.get_editor_property("materials")))
    for i in range(slots):
        comp.set_material(i, override)
    log("material override %s on %d slots (now %s)" % (override.get_name() if override else None, slots,
        [comp.get_material(i).get_name() if comp.get_material(i) else None for i in range(slots)]))
for extra in MESHES[1:]:                                   # the other parts of a split body
    part = actors.spawn_actor_from_class(u.SkeletalMeshActor, POS, u.Rotator(0, 0, 0))
    part.skeletal_mesh_component.set_skeletal_mesh_asset(u.load_asset(extra))
# Shaders, textures and meshes finish compiling/streaming asynchronously; the capture otherwise renders the
# engine's default grey material.
u.AutomationLibrary.finish_loading_before_screenshot()

b = mesh.get_bounds()
top = b.origin.z + b.box_extent.z
centre = POS + u.Vector(b.origin.x, b.origin.y, top / 2)
head = comp.get_socket_location("head")

target = u.RenderingLibrary.create_render_target2d(world, W, H, u.TextureRenderTargetFormat.RTF_RGBA8)
cap = actors.spawn_actor_from_class(u.SceneCapture2D, u.Vector(0, 0, 0), u.Rotator(0, 0, 0))
cc = cap.get_component_by_class(u.SceneCaptureComponent2D)
cc.texture_target = target
cc.capture_source = u.SceneCaptureSource.SCS_FINAL_COLOR_LDR
for prop, value in (("b_capture_every_frame", False), ("b_capture_on_movement", False),
                    ("b_always_persist_rendering_state", True)):
    try:
        cc.set_editor_property(prop, value)
    except Exception:
        pass


def expose(bias):
    pp = u.PostProcessSettings()
    for prop, value in (("override_auto_exposure_method", True),
                        ("auto_exposure_method", u.AutoExposureMethod.AEM_HISTOGRAM),
                        ("override_auto_exposure_min_brightness", True), ("auto_exposure_min_brightness", 0.03),
                        ("override_auto_exposure_max_brightness", True), ("auto_exposure_max_brightness", 0.6),
                        ("override_auto_exposure_bias", True), ("auto_exposure_bias", bias)):
        pp.set_editor_property(prop, value)
    cc.post_process_settings = pp


def shoot(view, look_at, dist, yaw, pitch=-5.0, fov=FOV):
    a = math.radians(yaw + (body.get_actor_rotation().yaw if placed else 0.0))
    # yaw 0 looks from +Y toward -Y; the Tripo crew face +Y, so yaw 0 is the front.
    loc = u.Vector(look_at.x + math.sin(a) * dist, look_at.y + math.cos(a) * dist,
                   look_at.z - math.sin(math.radians(pitch)) * dist)
    rot = u.MathLibrary.find_look_at_rotation(loc, look_at)
    cap.set_actor_location_and_rotation(loc, rot, False, False)
    cc.fov_angle = fov
    for bias in BRACKET:
        expose(bias)
        cc.capture_scene()
        u.RenderingLibrary.export_render_target(world, target, OUT, "%s_%s__b%.1f.png" % (NAME, view, bias))


full = (top * 0.58) / math.tan(math.radians(FOV / 2))
for yaw in range(0, 360, 45):
    shoot("y%03d" % yaw, centre, full, yaw)
close = 34.0 / math.tan(math.radians(FOV / 2))
for yaw in (0, 90, 180, 270):
    shoot("head%03d" % yaw, head, close, yaw, pitch=-8.0)
log("done %s height %.1f cm -> %s" % (NAME, top, OUT))
