"""Photograph the bartender at her bar, in Play, for the OWNER to judge: four moments of her gesture cycle and each of
her four actions triggered in turn.

  set SS_BAR_OUT=<folder>
  UnrealEditor-Cmd.exe <project> -unattended -RenderOffscreen -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/capture_bar.py"

Same mechanics as Scripts/CharacterStudio/CaptureStudio.py (PIE, a camera the view is switched to, HighResShot after a
few frames). The pilot pawn is moved out of frame; nothing is saved.
"""
import json
import os
import time

import unreal as u

MAP = "/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime"
LABEL = "Crew/Lounge guest"
OUT = os.environ["SS_BAR_OUT"]
W, H = 1920, 1080
WARM = 40
os.makedirs(OUT, exist_ok=True)
lvl = u.get_editor_subsystem(u.LevelEditorSubsystem)
editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
assert not editor.get_game_world(), "fresh process required"
assert lvl.load_level(MAP)
# The game travels to its own "Survival" world at play start, so nothing spawned in the editor world survives: the
# camera is summoned inside the play world (the dev "summon" cheat) once the walker is there.


def log(s):
    u.log_warning("BARCAP| " + str(s))


# shots: (name, seconds into play before the shot, action index or None, camera angle in degrees around her, distance)
SHOTS = [("player_view", 5.0, None, 0, 0), ("idle_front", 3.0, None, 0, 320), ("gesture_a", 12.0, None, 25, 300), ("gesture_b", 22.0, None, -25, 300),
         ("pour", 2.5, 0, 15, 280), ("cheers", 2.5, 1, 15, 280), ("dance", 4.0, 2, 30, 360), ("story", 3.0, 3, -15, 280), ("wide", 3.0, None, 40, 520)]
state = {"phase": "wait", "start": time.monotonic(), "si": 0, "busy": False, "frames": 0, "shot_at": None, "report": {"shots": [], "errors": []}}


def camera_for(bar, deg, dist):
    import math
    base = bar.get_actor_location()
    fwd = bar.get_actor_forward_vector()  # she faces the customers
    yaw = math.radians(deg)
    dirv = u.Vector(fwd.x * math.cos(yaw) - fwd.y * math.sin(yaw), fwd.x * math.sin(yaw) + fwd.y * math.cos(yaw), 0)
    loc = u.Vector(base.x + dirv.x * dist, base.y + dirv.y * dist, base.z + 60)
    look = u.Vector(base.x, base.y, base.z + 35)
    rot = u.MathLibrary.find_look_at_rotation(loc, look)
    return loc, rot


def finish():
    # Ask Play to end, then leave once the game world is gone (CaptureStudio.py does the same).
    json.dump(state["report"], open(os.path.join(OUT, "capture.json"), "w"), indent=1)
    log("DONE %d shots, %d errors" % (len(state["report"]["shots"]), len(state["report"]["errors"])))
    state.update(phase="stop", stop_at=time.monotonic())
    try:
        lvl.editor_request_end_play()
    except Exception:  # noqa
        pass


def quit_now():
    state["phase"] = "done"
    u.unregister_slate_post_tick_callback(state["handle"])
    u.EditorPythonScripting.set_keep_python_script_alive(False)
    u.SystemLibrary.quit_editor()


def tick(dt):
    if state["busy"] or state["phase"] == "done":
        return
    state["busy"] = True
    try:
        now = time.monotonic()
        if state["phase"] == "stop":
            if not editor.get_game_world() or now - state["stop_at"] > 12:
                quit_now()
            return
        if now - state["start"] > 900:
            raise RuntimeError("timeout")
        world = editor.get_game_world()
        if not world:
            if now - state["start"] > 120:
                raise RuntimeError("PIE world missing")
            return
        # Actors are looked up by label every time: a cached reference went stale between ticks on the first run.
        def find_bar():
            return next((a for a in u.GameplayStatics.get_all_actors_of_class(world, u.SSOutpostAmbientActor) if a.get_actor_label() == LABEL), None)

        def find_cam():
            cams = [c for c in u.GameplayStatics.get_all_actors_of_class(world, u.CameraActor) if c.get_name() not in state.get("old_cams", set())]
            return cams[0] if cams else None

        if state["phase"] == "wait":
            pc = u.GameplayStatics.get_player_controller(world, 0)
            pawn = u.GameplayStatics.get_player_pawn(world, 0)
            bar = find_bar()
            if not pc or not pawn or not bar:
                if now - state["start"] > 150:
                    raise RuntimeError("in play but missing: pc=%s pawn=%s bar=%s world=%s" % (bool(pc), bool(pawn), bool(bar), world.get_name()))
                return
            log("play world %s: bartender found, summoning a camera" % world.get_name())
            # the walker stands at a stool, 3.5 m in front of her, looking at her: the talk hint and action row appear
            b = bar.get_actor_location()
            fwd = bar.get_actor_forward_vector()
            stand = u.Vector(b.x + fwd.x * 350, b.y + fwd.y * 350, b.z + 4)
            pawn.set_actor_location(stand, False, True)
            pc.set_control_rotation(u.MathLibrary.find_look_at_rotation(stand, u.Vector(b.x, b.y, b.z + 40)))
            state["old_cams"] = {c.get_name() for c in u.GameplayStatics.get_all_actors_of_class(world, u.CameraActor)}
            u.SystemLibrary.execute_console_command(world, "summon CameraActor", pc)
            for cmd in ("r.TextureStreaming 0", "r.Streaming.FullyLoadUsedTextures 1"):
                u.SystemLibrary.execute_console_command(world, cmd, pc)
            state["pc"] = pc
            state.update(phase="camera", camera_at=now)
            return
        if state["phase"] == "camera":
            cam = find_cam()
            if cam:
                cam.get_component_by_class(u.CameraComponent).set_field_of_view(40)
                log("camera %s ready" % cam.get_name())
                state["phase"] = "next"
            elif now - state["camera_at"] > 10:
                log("summon gave no camera; shooting from the walker's own view")
                state["phase"] = "next"
            return
        if state["phase"] == "next":
            if state["si"] >= len(SHOTS):
                finish()
                return
            bar, cam = find_bar(), find_cam()
            pc = u.GameplayStatics.get_player_controller(world, 0)
            if not bar or not pc:
                raise RuntimeError("lost the bartender or the controller in world %s" % world.get_name())
            state["pc"] = pc
            name, wait, action, deg, dist = SHOTS[state["si"]]
            if cam and name != "player_view":
                loc, rot = camera_for(bar, deg, dist)
                cam.set_actor_location_and_rotation(loc, rot, False, False)
                pc.set_view_target_with_blend(cam, 0.0, u.ViewTargetBlendFunction.VT_BLEND_LINEAR, 0.0, False)
            else:
                pawn = u.GameplayStatics.get_player_pawn(world, 0)
                pc.set_view_target_with_blend(pawn, 0.0, u.ViewTargetBlendFunction.VT_BLEND_LINEAR, 0.0, False)
            if action is not None:
                ok = bar.trigger_action(action)
                log("trigger action %d -> %s" % (action, ok))
            state.update(phase="hold", shot_at=now + wait, frames=0, path=os.path.join(OUT, "Joy_bar_%s.png" % name))
            return
        if state["phase"] == "hold":
            state["frames"] += 1
            if now >= state["shot_at"] and state["frames"] >= WARM:
                u.SystemLibrary.execute_console_command(world, 'HighResShot %dx%d filename="%s"' % (W, H, state["path"]), state["pc"])
                state["phase"] = "written"
                state["written_at"] = now
            return
        if state["phase"] == "written":
            if os.path.exists(state["path"]) and os.path.getsize(state["path"]) > 10000 and now - state["written_at"] > 1.0:
                state["report"]["shots"].append({"shot": SHOTS[state["si"]][0], "png": state["path"]})
                state["si"] += 1
                state["phase"] = "next"
            elif now - state["written_at"] > 20:
                state["report"]["errors"].append({"shot": SHOTS[state["si"]][0], "error": "no png"})
                state["si"] += 1
                state["phase"] = "next"
            return
    except Exception as e:  # noqa
        import traceback
        state["report"]["errors"].append({"error": str(e), "trace": traceback.format_exc()[-1200:]})
        log("ERROR " + str(e))
        finish()
    finally:
        state["busy"] = False


u.EditorPythonScripting.set_keep_python_script_alive(True)
state["handle"] = u.register_slate_post_tick_callback(tick)
lvl.editor_request_begin_play()  # Play as the game: the game mode, the walker and the bartender actor all exist
