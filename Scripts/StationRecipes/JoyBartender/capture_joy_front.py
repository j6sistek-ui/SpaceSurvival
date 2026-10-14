"""A full-length front still of Joy in the station's own light, for outfit choices (owner 2026-10-14: "send me a front
facing render, i'm trying to pick pants to match"). A temporary SK_Joy actor stands on the open floor in front of the
bar, playing A_Joy_Idle; the editor viewport looks at her and HighResShot writes the frames. Nothing is saved.

  set SS_FRONT_OUT=<folder>        set SS_FRONT_WARM=<seconds before the first shot, default 300>
  UnrealEditor-Cmd.exe <project> -unattended -RenderOffscreen -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/capture_joy_front.py"
"""
import json
import math
import os
import time

import unreal as u

MAP = "/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime"
LABEL = "Crew/Lounge guest"
MESH = "/Game/SpaceSurvival/Licensed/StationAssets/JoyBartender/Mesh/SK_Joy"
IDLE = os.environ.get("SS_FRONT_ANIM", "/Game/SpaceSurvival/Licensed/StationAssets/JoyLightBlue117/Animations/A_Joy_Idle")
OUT = os.environ["SS_FRONT_OUT"]
WARM = float(os.environ.get("SS_FRONT_WARM", "300"))
W, H = 1600, 1800
os.makedirs(OUT, exist_ok=True)
lvl = u.get_editor_subsystem(u.LevelEditorSubsystem)
actors_sub = u.get_editor_subsystem(u.EditorActorSubsystem)
assert lvl.load_level(MAP)
bar = next(a for a in actors_sub.get_all_level_actors() if a.get_actor_label() == LABEL)
b = bar.get_actor_location()
fwd = bar.get_actor_forward_vector()
right = bar.get_actor_right_vector()
feet = b.z - bar.body.get_scaled_capsule_half_height()
# out past the bar stools (they stand ~3.5 m in front of her) so nothing sits between her and the camera
spot = u.Vector(b.x + fwd.x * 450, b.y + fwd.y * 450, feet + float(os.environ.get("SS_FRONT_LIFT", "0")))  # shoes: the sole depth
# Joy faces +Y in asset space, so the actor is turned -90 from the bar's forward. On a SkeletalMeshActor the mesh IS the
# root, so its relative rotation would replace the actor's facing rather than add to it (the first stills were profiles)
yaw = math.degrees(math.atan2(fwd.y, fwd.x)) - 90.0
temp = actors_sub.spawn_actor_from_class(u.SkeletalMeshActor, spot, u.Rotator(roll=0.0, pitch=0.0, yaw=yaw))
temp.set_actor_label("TEMP_JoyFront")
sk = temp.skeletal_mesh_component
sk.set_skeletal_mesh_asset(u.load_asset(MESH))
idle = u.load_asset(IDLE)
if isinstance(idle, u.AnimSequence):
    sk.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
    sk.set_editor_property("animation_data", u.SingleAnimationPlayData(anim_to_play=idle, saved_looping=True, saved_playing=False, saved_position=1.0, saved_play_rate=0.0))
    sk.play_animation(idle, True)
    sk.set_position(1.0, False)
    sk.set_play_rate(0.0)
try:
    u.EditorLevelLibrary.editor_set_game_view(True)
except Exception:  # noqa
    pass


def log(s):
    u.log_warning("JOYFRONT| " + str(s))


def cam(deg, dist, height, look_z):
    a = math.radians(deg)
    d = u.Vector(fwd.x * math.cos(a) - fwd.y * math.sin(a), fwd.x * math.sin(a) + fwd.y * math.cos(a), 0)
    loc = u.Vector(spot.x + d.x * dist, spot.y + d.y * dist, spot.z + height)
    return loc, u.MathLibrary.find_look_at_rotation(loc, u.Vector(spot.x, spot.y, spot.z + look_z))


SHOTS = [("front", 0, 210, 100, 90), ("front_upper", 0, 115, 138, 126), ("three_quarter", 35, 210, 100, 90),
         ("feet_side", 90, 140, 12, 8)]  # floor level, side on: do the soles touch the floor
if os.environ.get("SS_FRONT_ONLY_FEET"):
    SHOTS = [SHOTS[-1]]
state = {"si": 0, "phase": "set", "at": None, "busy": False, "report": {"shots": [], "errors": [], "spot": list(spot.to_tuple())}, "handle": None}


def done():
    # where her feet are against the floor, from the bones (the floor is the bar actor's capsule bottom)
    floor = spot.z - float(os.environ.get("SS_FRONT_LIFT", "0"))
    # the real floor under her, traced, in case the bar actor's capsule bottom is not on it
    hit = u.SystemLibrary.line_trace_single(temp, u.Vector(spot.x, spot.y, spot.z + 60), u.Vector(spot.x, spot.y, spot.z - 120),
                                            u.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [temp], u.DrawDebugTrace.NONE, True)
    try:
        hr = hit.to_tuple()
        state["report"]["traced_floor_minus_capsule_floor_cm"] = round(hr[4].z - floor, 2) if hr[0] else None
    except Exception as e:  # noqa
        state["report"]["traced_floor_minus_capsule_floor_cm"] = "trace failed: %s" % e
    state["report"]["bones_above_floor_cm"] = {n: round(sk.get_socket_location(n).z - floor, 2) for n in
                                                ("CC_Base_L_Foot", "CC_Base_R_Foot", "CC_Base_L_ToeBase", "CC_Base_R_ToeBase")}
    log("FEET " + json.dumps({"bones": state["report"]["bones_above_floor_cm"], "traced_floor": state["report"].get("traced_floor_minus_capsule_floor_cm"), "anim": IDLE}))
    try:
        actors_sub.destroy_actor(temp)
    except Exception:  # noqa
        pass
    json.dump(state["report"], open(os.path.join(OUT, "capture.json"), "w"), indent=1)
    log("DONE %d shots" % len(state["report"]["shots"]))
    u.unregister_slate_post_tick_callback(state["handle"])
    u.EditorPythonScripting.set_keep_python_script_alive(False)
    u.SystemLibrary.quit_editor()


def tick(dt):
    if state["busy"]:
        return
    state["busy"] = True
    try:
        now = time.monotonic()
        if state["si"] >= len(SHOTS):
            done()
            return
        name, deg, dist, height, look_z = SHOTS[state["si"]]
        path = os.path.join(OUT, "Joy_%s.png" % name)
        if state["phase"] == "set":
            loc, rot = cam(deg, dist, height, look_z)
            u.EditorLevelLibrary.set_level_viewport_camera_info(loc, rot)
            state.update(phase="warm", at=now, frames=0)
            return
        if state["phase"] == "warm":
            state["frames"] += 1
            # the jacket's material compiles its shaders on first sight: the first shot waits for that
            if state["frames"] >= 30 and now - state["at"] >= (WARM if state["si"] == 0 else 10.0):
                u.SystemLibrary.execute_console_command(None, 'HighResShot %dx%d filename="%s"' % (W, H, path))
                state.update(phase="wait", at=now)
            return
        if state["phase"] == "wait":
            if os.path.exists(path) and os.path.getsize(path) > 10000 and now - state["at"] > 1.0:
                state["report"]["shots"].append({"shot": name, "png": path})
                state.update(si=state["si"] + 1, phase="set")
            elif now - state["at"] > 30:
                state["report"]["errors"].append({"shot": name, "error": "no png"})
                state.update(si=state["si"] + 1, phase="set")
            return
    except Exception as e:  # noqa
        import traceback
        state["report"]["errors"].append({"error": str(e), "trace": traceback.format_exc()[-1000:]})
        log("ERROR " + str(e))
        done()
    finally:
        state["busy"] = False


u.EditorPythonScripting.set_keep_python_script_alive(True)
state["handle"] = u.register_slate_post_tick_callback(tick)
