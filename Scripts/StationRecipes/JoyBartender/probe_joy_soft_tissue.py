"""Prove Joy's body dynamics in Play: the BodyDynamics component binds on her placed actor, its offsets move and stay
finite and bounded through her idle, a Dance and a Pour, and settle back to zero. Frames are HighResShots of the player's
own view with the HUD hidden (the walker is moved close in front, then along the counter for a side view) and go to
SS_JOY_ST_OUT for a GIF the owner can judge motion from. Python cannot spawn a capture actor into a Play world
(AddComponentByClass is ScriptNoExport; summon needs the cheat manager), so the player camera is the lens.

  set SS_JOY_ST_OUT=<folder>
  UnrealEditor-Cmd.exe <project> -unattended -RenderOffscreen -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/probe_joy_soft_tissue.py"
Nothing is saved to the project.
"""
import json
import math
import os
import time
import traceback

import unreal as u

MAP = "/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime"
LABEL = "Crew/Lounge guest"
OUT = os.environ["SS_JOY_ST_OUT"]
W, H = 960, 1080
FPS = 8
REGIONS = ("Breast_L", "Breast_R", "Hip_L", "Hip_R")
LIMITS = (1.6, 1.6, 1.2, 1.2)
# (phase, seconds, action index or None, view)
PHASES = [("idle", 5.0, None, "front"), ("dance", 8.0, 2, "front"), ("pour", 5.0, 0, "front"), ("dance_side", 6.0, 2, "side"), ("settle", 5.0, None, "side")]
DILATION = 0.25  # slow motion: an offscreen PIE renders ~5 frames a second; at 0.25x each is a ~0.05 s game step like a player's machine
os.makedirs(OUT, exist_ok=False)
lvl = u.get_editor_subsystem(u.LevelEditorSubsystem)
editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
assert not editor.get_game_world(), "fresh process required"
assert lvl.load_level(MAP)
state = {"phase": "wait", "start": time.monotonic(), "busy": False, "stage": -1, "samples": [], "frames": [], "next_frame": 0.0, "handle": None,
         "report": {"status": "RUNNING", "errors": []}}


def log(s):
    u.log_warning("JOYPROBE| " + str(s))


def finish(status):
    r = state["report"]
    r["status"] = status
    rows = state["samples"]
    r["summary"] = {}
    for name, _, _, _ in PHASES:
        rr = [x for x in rows if x["phase"] == name]
        r["summary"][name] = {"samples": len(rr), "max_offset_cm": [max((math.sqrt(sum(v * v for v in x["offsets"][i])) for x in rr), default=0.0) for i in range(4)],
                              "final_offsets": rr[-1]["offsets"] if rr else None,
                              "game_dt": {"mean": sum(x["game_dt"] for x in rr) / len(rr), "max": max(x["game_dt"] for x in rr)} if rr else None}
    r["time_dilation"] = DILATION
    r["frames"] = state["frames"]
    r["wall_seconds"] = time.monotonic() - state["start"]
    json.dump(r, open(os.path.join(OUT, "Probe.json"), "w"), indent=1)
    log("%s %s" % (status, json.dumps(r["summary"])))
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


def place_capture(pc, pawn, bar, view):
    """The walker's third-person camera is the lens: close in front over its shoulder, or from the side along the counter."""
    b = bar.get_actor_location()
    f = bar.get_actor_forward_vector()
    r = bar.get_actor_right_vector()
    if view == "front":
        loc = u.Vector(b.x + f.x * 150 + r.x * 55, b.y + f.y * 150 + r.y * 55, b.z + 4)
        target = u.Vector(b.x, b.y, b.z + 50)
    else:
        loc = u.Vector(b.x + f.x * 110 + r.x * 230, b.y + f.y * 110 + r.y * 230, b.z + 4)
        target = u.Vector(b.x, b.y, b.z + 20)
    pawn.set_actor_location(loc, False, True)
    pc.set_control_rotation(u.MathLibrary.find_look_at_rotation(u.Vector(loc.x, loc.y, loc.z + 70), target))


def advance(world, bar):
    state["stage"] += 1
    name, secs, action, view = PHASES[state["stage"]]
    state["phase_start"] = u.GameplayStatics.get_time_seconds(world)
    if action is not None:
        assert bar.trigger_action(action), action
    # controller and pawn wrappers go stale between ticks: always looked up fresh
    place_capture(u.GameplayStatics.get_player_controller(world, 0), u.GameplayStatics.get_player_pawn(world, 0), bar, view)
    state["view"] = view
    log("phase %s (%s)" % (name, view))


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
        if now - state["start"] > 600:
            raise RuntimeError("timeout")
        world = editor.get_game_world()
        if not world:
            if now - state["start"] > 120:
                raise RuntimeError("PIE world missing")
            return
        bar = next((a for a in u.GameplayStatics.get_all_actors_of_class(world, u.SSOutpostAmbientActor) if a.get_actor_label() == LABEL), None)
        if state["phase"] == "wait":
            pc = u.GameplayStatics.get_player_controller(world, 0)
            pawn = u.GameplayStatics.get_player_pawn(world, 0)
            if not pc or not pawn or not bar:
                if now - state["start"] > 150:
                    raise RuntimeError("in play but missing: pc=%s pawn=%s bar=%s" % (bool(pc), bool(pawn), bool(bar)))
                return
            if u.GameplayStatics.is_game_paused(world):
                u.GameplayStatics.set_game_paused(world, False)
            u.GameplayStatics.set_global_time_dilation(world, DILATION)
            comps = bar.get_components_by_class(u.SSSoftTissueComponent)
            assert len(comps) == 1, comps
            d = comps[0]
            state["report"]["binding_valid"] = d.get_editor_property("binding_valid")
            assert state["report"]["binding_valid"], "BodyDynamics did not bind (see the log line 'Soft tissue binding invalid')"
            # the walker at a stool 3.5 m in front of her, as a player would be
            b = bar.get_actor_location()
            f = bar.get_actor_forward_vector()
            stand = u.Vector(b.x + f.x * 350, b.y + f.y * 350, b.z + 4)
            pawn.set_actor_location(stand, False, True)
            pc.set_control_rotation(u.MathLibrary.find_look_at_rotation(stand, u.Vector(b.x, b.y, b.z + 40)))
            state.update(phase="run")
            for cmd in ("r.TextureStreaming 0", "r.Streaming.FullyLoadUsedTextures 1", "showhud"):
                u.SystemLibrary.execute_console_command(world, cmd, pc)
            advance(world, bar)
            return
        if state["phase"] == "run":
            if not bar:
                raise RuntimeError("bartender actor vanished")
            d = bar.get_components_by_class(u.SSSoftTissueComponent)[0]
            name, secs, action, view = PHASES[state["stage"]]
            t = u.GameplayStatics.get_time_seconds(world) - state["phase_start"]
            offsets = [[v.x, v.y, v.z] for v in d.get_editor_property("current_offsets_cm")]
            assert len(offsets) == 4 and all(math.isfinite(v) for row in offsets for v in row), offsets
            for row, limit in zip(offsets, LIMITS):
                assert math.sqrt(sum(v * v for v in row)) <= limit + 1e-3, (row, limit)
            weights = [bar.character_mesh.get_morph_target("ST_%s_%s" % (r, a)) for r in REGIONS for a in "XYZ"]
            assert max(abs(w - v) for w, v in zip(weights, [v for row in offsets for v in row])) < 1e-3, (weights, offsets)
            state["samples"].append({"phase": name, "t": round(t, 3), "dt": round(dt, 4), "game_dt": round(u.GameplayStatics.get_world_delta_seconds(world), 4),
                                     "offsets": [[round(v, 4) for v in row] for row in offsets],
                                     "clip": bar.character_mesh.get_editor_property("animation_data").anim_to_play.get_name() if bar.character_mesh.get_editor_property("animation_data").anim_to_play else None})
            if t >= state["next_frame"]:
                state["next_frame"] = t + 1.0 / FPS
                fname = "%04d.png" % len(state["frames"])
                u.SystemLibrary.execute_console_command(world, 'HighResShot %dx%d filename="%s"' % (W, H, os.path.join(OUT, fname)), u.GameplayStatics.get_player_controller(world, 0))
                state["frames"].append({"file": fname, "phase": name, "view": view, "t": round(t, 3), "offsets_cm": offsets})
            if t >= secs:
                if state["stage"] == len(PHASES) - 1:
                    finish("PASS_FINITE_BOUNDED")
                    return
                state["next_frame"] = 0.0
                advance(world, bar)
            return
    except Exception as e:  # noqa
        state["report"]["errors"].append({"error": str(e), "trace": traceback.format_exc()[-1500:]})
        log("ERROR " + str(e))
        finish("FAILED")
    finally:
        state["busy"] = False


u.EditorPythonScripting.set_keep_python_script_alive(True)
state["handle"] = u.register_slate_post_tick_callback(tick)
lvl.editor_request_begin_play()
