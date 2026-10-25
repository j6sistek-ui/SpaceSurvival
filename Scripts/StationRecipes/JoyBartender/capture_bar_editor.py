"""Editor-viewport stills of the bartender at her bar (no Play: the game's title menu sits in front of any scripted
PIE). Placement, scale, facing and the outfit under the station's own lighting; the owner judges the motion in play.

  set SS_BAR_OUT=<folder>
  UnrealEditor-Cmd.exe <project> -unattended -RenderOffscreen -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/capture_bar_editor.py"
Nothing is saved.
"""
import json
import math
import os
import time

import unreal as u

MAP = "/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime"
LABEL = "Crew/Lounge guest"
OUT = os.environ["SS_BAR_OUT"]
W, H = 1920, 1080
os.makedirs(OUT, exist_ok=True)
lvl = u.get_editor_subsystem(u.LevelEditorSubsystem)
assert lvl.load_level(MAP)
actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
bar = next(a for a in actors if a.get_actor_label() == LABEL)
base = bar.get_actor_location()
fwd = bar.get_actor_forward_vector()
# pose her mid-clip for the stills (the preview component plays when the viewport ticks)
cm = bar.character_mesh
cm.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
cm.play(True)
cm.set_position(6.0, False)
try:
    lvl.editor_set_game_view(True)
except Exception:  # noqa
    pass
try:
    u.EditorLevelLibrary.editor_set_game_view(True)
except Exception:  # noqa
    pass


def log(s):
    u.log_warning("BARCAP| " + str(s))


def cam(deg, dist, height=60, look_z=35):
    yaw = math.radians(deg)
    d = u.Vector(fwd.x * math.cos(yaw) - fwd.y * math.sin(yaw), fwd.x * math.sin(yaw) + fwd.y * math.cos(yaw), 0)
    loc = u.Vector(base.x + d.x * dist, base.y + d.y * dist, base.z + height)
    rot = u.MathLibrary.find_look_at_rotation(loc, u.Vector(base.x, base.y, base.z + look_z))
    return loc, rot


SHOTS = [("front", 0, 320, 60, 35), ("three_quarter", 30, 300, 60, 35), ("side", 75, 300, 50, 30), ("wide_bar", 20, 650, 120, 20),
         ("head", 10, 140, 85, 75), ("behind_bar", 160, 260, 70, 40)]
state = {"si": 0, "phase": "set", "at": None, "busy": False, "report": {"shots": [], "errors": []}, "handle": None}


def done():
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
        path = os.path.join(OUT, "Joy_bar_%s.png" % name)
        if state["phase"] == "set":
            loc, rot = cam(deg, dist, height, look_z)
            u.EditorLevelLibrary.set_level_viewport_camera_info(loc, rot)
            cm.set_position(6.0 + 2.5 * state["si"], False)
            state.update(phase="warm", at=now, frames=0)
            return
        if state["phase"] == "warm":
            state["frames"] = state.get("frames", 0) + 1
            # her three new material masters compile their shaders on first sight: the first shot waits for that
            warm_seconds = float(os.environ.get("SS_BAR_WARM", "420")) if state["si"] == 0 else 12.0
            if state["frames"] >= 30 and now - state["at"] >= warm_seconds:
                u.SystemLibrary.execute_console_command(None, 'HighResShot %dx%d filename="%s"' % (W, H, path))
                state.update(phase="wait", at=now)
            return
        if state["phase"] == "wait":
            if os.path.exists(path) and os.path.getsize(path) > 10000 and now - state["at"] > 1.0:
                state["report"]["shots"].append({"shot": name, "png": path})
                state["si"] += 1
                state["phase"] = "set"
            elif now - state["at"] > 25:
                state["report"]["errors"].append({"shot": name, "error": "no png"})
                state["si"] += 1
                state["phase"] = "set"
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
