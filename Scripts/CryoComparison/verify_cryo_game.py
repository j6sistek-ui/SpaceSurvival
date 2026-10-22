"""Observe saved native BeginPlay autoplay in an uncooked -game process.

Launch only CryoStage, initially /Engine/Maps/Entry, with -game -RenderOffscreen
-ForceEnablePython and -ExecCmds="py D:/.../verify_cryo_game.py". Do not use
-ExecutePythonScript: that executor explicitly requires GIsEditor.

Python observes game actors; it never plays/seeks a sequence or sets lights.
Two native map travels establish BeginPlay and EndPlay. No package/config saves.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import runpy
import time
import traceback

WORK = Path(__file__).resolve().parent
CHECKS = runpy.run_path(str(WORK / "verify_cryo_runtime.py"))
STAGE = CHECKS["STAGE"]
BASE, MAP, SEQUENCE = (CHECKS[key] for key in ("BASE", "MAP", "SEQUENCE"))
LIGHT_RANGES = CHECKS["LIGHT_RANGES"]
require, digest, native_hashes = (CHECKS[key] for key in ("require", "digest", "native_hashes"))
CVAR = CHECKS["CVAR"]
ENTRY = "/Engine/Maps/Entry"


def main():
    import unreal as u
    project = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    require(project == STAGE.resolve(), "Restricted to the isolated D-drive CryoStage")
    require(re.search(r"(?:^|\s)-game(?:\s|$)", u.SystemLibrary.get_command_line(), re.I),
            "This observer requires an uncooked native -game process")
    report_path = WORK / ("CryoGameRuntime_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                          + "_" + str(os.getpid()) + ".json")
    captures = WORK.parent / 'outputs/Cryo_Comparison/previews' / report_path.stem
    captures.mkdir(exist_ok=False)
    report = {"status": "RUNNING", "started_utc": datetime.now(timezone.utc).isoformat(),
              "engine": u.SystemLibrary.get_engine_version(), "project": str(project),
              "map": MAP, "sequence": SEQUENCE, "mode": "UNCOOKED_NATIVE_GAME",
              "samples": [], "errors": [], "events": [], "screenshots": [],
              "limits": ["Uncooked native game verification, not packaged performance or production-map validation.",
                         "No Python sequence play/seek, light setters, asset saves or config writes.",
                         "Readback of intensity and Niagara active state does not prove visual quality.",
                         "Ninety-second Slate-callback deadline; native hangs require external watchdog."]}
    state = {"started": time.monotonic(), "phase": "WAIT_ENTRY", "done": False, "busy": False,
             "handle": None, "world": None, "player": None, "lights": {}, "niagara": [],
             "native": {}, "sources": {}, "phase_started": time.monotonic(),
             "sampling_started": None, "last_sample": 0.0, "initial_cvar_configured": False}
    state['overview_selected'] = False

    def checkpoint():
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    def event(name, **fields):
        report["events"].append({"event": name, "elapsed_s": time.monotonic() - state["started"], **fields})
        checkpoint()

    def find_game_world(package):
        found = [world for world in u.ObjectIterator(u.World)
                 if world.get_path_name().split(".", 1)[0] == package
                 and u.GameplayStatics.get_game_instance(world) is not None]
        require(len(found) <= 1, "Multiple game worlds match " + package)
        return found[0] if found else None

    def clear_world_references():
        # Do not keep old-world Python object wrappers alive across native travel.
        state["world"], state["player"] = None, None
        state["lights"], state["niagara"] = {}, []

    def travel(world, destination, phase):
        state["phase"], state["phase_started"] = phase, time.monotonic()
        clear_world_references()
        event("NATIVE_MAP_TRAVEL_REQUESTED", destination=destination)
        u.GameplayStatics.open_level(world, destination, True, "")

    def finish():
        if state["done"]:
            return
        state["done"] = True
        try:
            report["local_fog_start_distance_after_endplay_cm"] = u.SystemLibrary.get_console_variable_float_value(CVAR)
            if state["initial_cvar_configured"]:
                require(abs(report["local_fog_start_distance_after_endplay_cm"] - 1000.0) < 0.01,
                        "Native EndPlay did not restore the initial 1000 cm CVar")
                report["native_cvar_restoration_verified"] = bool(report.get("analysis")
                    and state["phase"] == "RETURNED_ENTRY")
            if state["native"]:
                after = native_hashes()
                changed = sorted(key for key in set(state["native"]) | set(after)
                                 if state["native"].get(key) != after.get(key))
                report["native_hashes_unchanged"], report["native_changed_paths"] = not changed, changed
                require(not changed, "Native content changed during observation")
            if state["sources"]:
                changed = [path for path, expected in state["sources"].items() if digest(path) != expected]
                report["original_source_hashes_unchanged"], report["original_changed_paths"] = not changed, changed
                require(not changed, "Original GLB changed during observation")
            require(report.get("native_cvar_restoration_verified"), "Full native autoplay/travel/restoration not verified")
        except Exception:
            report["errors"].append(traceback.format_exc())
        report["status"] = "FAILED" if report["errors"] else "NATIVE_GAME_AUTOPLAY_LOOP_PHASE_AND_RESTORE_VERIFIED"
        report["finished_utc"] = datetime.now(timezone.utc).isoformat()
        report["elapsed_s"] = time.monotonic() - state["started"]
        checkpoint()
        print("CRYO_GAME_RUNTIME_RESULT " + json.dumps({"status": report["status"], "receipt": str(report_path),
              "samples": len(report["samples"]), "errors": len(report["errors"])}), flush=True)
        if state["handle"] is not None:
            u.unregister_slate_post_tick_callback(state["handle"])
            state["handle"] = None
        clear_world_references()
        u.SystemLibrary.execute_console_command(None, "quit")

    def attach(world):
        state['world'] = world
        selected = [actor for actor in u.GameplayStatics.get_all_actors_of_class(world, u.LevelSequenceActor)
                    if actor.get_actor_label() == CHECKS["SEQUENCE_LABEL"]]
        require(len(selected) == 1, "Expected exactly one saved sequence actor")
        actor = selected[0]
        sequence = actor.get_sequence()
        require(sequence and sequence.get_path_name().split(".", 1)[0] == SEQUENCE, "Unexpected sequence asset")
        settings = actor.get_editor_property("playback_settings")
        require(settings.get_editor_property("auto_play"), "Saved autoplay disabled")
        require(settings.get_editor_property("loop_count").get_editor_property("value") == -1, "Saved loop count changed")
        player = actor.get_editor_property('sequence_player')
        require(player and player.is_playing(), "Saved sequence did not autoplay on native BeginPlay")
        state["world"], state["player"] = world, player
        for candidate in u.GameplayStatics.get_all_actors_of_class(world, u.PointLight):
            label = candidate.get_actor_label()
            if label in LIGHT_RANGES:
                require(label not in state["lights"], "Duplicate light label")
                state["lights"][label] = candidate.get_component_by_class(u.PointLightComponent)
        require(set(state["lights"]) == set(LIGHT_RANGES) and all(state["lights"].values()), "Missing breathing lights")
        for candidate in u.GameplayStatics.get_all_actors_of_class(world, u.NiagaraActor):
            component = candidate.get_component_by_class(u.NiagaraComponent)
            asset = component.get_asset() if component else None
            if asset and asset.get_path_name().startswith(BASE + "/"):
                state["niagara"].append((candidate.get_actor_label(), component))
        require(len(state["niagara"]) == 4, "Missing native Niagara actors")
        cameras = [a for a in u.GameplayStatics.get_all_actors_of_class(world,u.CameraActor)
                   if a.get_actor_label() == 'CAM_D_Meshy_Raccoon']
        require(len(cameras)==1, 'Missing saved D review camera')
        controller = u.GameplayStatics.get_player_controller(world,0)
        require(controller is not None, 'Game preview controller missing')
        pawn=u.GameplayStatics.get_player_pawn(world,0)
        if pawn is not None:
            pawn.set_actor_hidden_in_game(True)
            report['preview_pawn_hidden_for_detached_camera_only']=pawn.get_path_name()
        controller.set_view_target_with_blend(cameras[0],0.0)
        report["runtime_world"], report["runtime_saved_sequence_actor"] = world.get_path_name(), actor.get_path_name()
        report["saved_autoplay"], report["saved_loop_count"] = True, -1
        state["phase"], state["sampling_started"] = "SAMPLING", time.monotonic()
        event("NATIVE_BEGINPLAY_AUTOPLAY_OBSERVED")

    def sample(now):
        state["last_sample"] = now
        niagara = []
        for label, component in state["niagara"]:
            origin, extent, radius = u.SystemLibrary.get_component_bounds(component)
            niagara.append({"actor": label, "active": bool(component.is_active()),
                            "asset": component.get_asset().get_path_name(),
                            "bounds_extent_cm": [extent.x, extent.y, extent.z],
                            "bounds_radius_cm": radius})
        report["samples"].append({"wall_elapsed_s": now - state["sampling_started"],
            "world_time_s": float(u.GameplayStatics.get_time_seconds(state["world"])),
            "world_real_time_s": float(u.GameplayStatics.get_real_time_seconds(state["world"])),
            "sequence_time_s": CHECKS["sequence_seconds"](state["player"]),
            "sequence_is_playing": bool(state["player"].is_playing()),
            "local_fog_start_distance_cm": u.SystemLibrary.get_console_variable_float_value(CVAR),
            "light_intensities_lm": {label: float(component.get_editor_property("intensity"))
                                     for label, component in sorted(state["lights"].items())},
            "niagara": niagara})
        if len(report["samples"]) % 10 == 0:
            checkpoint()

    def tick(_delta_seconds):
        if state["done"] or state["busy"]:
            return
        state["busy"] = True
        try:
            now = time.monotonic()
            require(now - state["started"] <= 90.0, "Ninety-second native-game observation deadline expired")
            if state["phase"] == "WAIT_ENTRY":
                world = find_game_world(ENTRY)
                if world is None:
                    require(now - state["phase_started"] <= 20.0, "Initial Entry game world unavailable")
                    return
                report["local_fog_start_distance_process_initial_cm"] = u.SystemLibrary.get_console_variable_float_value(CVAR)
                u.SystemLibrary.execute_console_command(world, CVAR + " 1000")
                require(abs(u.SystemLibrary.get_console_variable_float_value(CVAR) - 1000.0) < 0.01,
                        "Could not establish unsaved 1000 cm initial CVar")
                state["initial_cvar_configured"] = True
                report["local_fog_start_distance_before_beginplay_cm"] = 1000.0
                travel(world, MAP, "WAIT_TARGET")
            elif state["phase"] == "WAIT_TARGET":
                world = find_game_world(MAP)
                if world is None:
                    require(now - state["phase_started"] <= 35.0, "Target native game world unavailable")
                    return
                attach(world)
                sample(now)
            elif state["phase"] == "SAMPLING":
                if now-state['sampling_started'] >= 10.0 and not state['overview_selected']:
                    cameras=[a for a in u.GameplayStatics.get_all_actors_of_class(state['world'],u.CameraActor)
                             if a.get_actor_label()=='CAM_AllFour_Comparison']
                    require(len(cameras)==1,'Missing overview camera')
                    u.GameplayStatics.get_player_controller(state['world'],0).set_view_target_with_blend(cameras[0],0.0)
                    state['overview_selected']=True
                for index, seconds in enumerate((4.0,8.0)):
                    if now-state['sampling_started'] >= seconds and len(report['screenshots']) == index:
                        png = captures / ('D_Runtime_t'+str(index)+'.png')
                        u.SystemLibrary.execute_console_command(state['world'], 'HighResShot 960x1200 filename="'+png.as_posix()+'"')
                        report['screenshots'].append({'png':str(png),'at_elapsed_s':now-state['sampling_started'],'camera':'CAM_D_Meshy_Raccoon'})
                        break
                if now-state['sampling_started'] >= 12.0 and len(report['screenshots'])==2:
                    png=captures/'AllFour_Runtime.png'
                    u.SystemLibrary.execute_console_command(state['world'],'HighResShot 1920x1080 filename="'+png.as_posix()+'"')
                    report['screenshots'].append({'png':str(png),'at_elapsed_s':now-state['sampling_started'],'camera':'CAM_AllFour_Comparison'})
                if now - state["last_sample"] >= CHECKS["SAMPLE_INTERVAL"]:
                    sample(now)
                rows = report["samples"]
                if (len(rows) > 1 and rows[-1]["wall_elapsed_s"] - rows[0]["wall_elapsed_s"] >= 14.0
                        and rows[-1]["world_time_s"] - rows[0]["world_time_s"] >= 14.0):
                    report["analysis"] = CHECKS["analyse"](rows)
                    require(all(item["bounds_radius_cm"] > 1.0 and max(item["bounds_extent_cm"]) > 1.0
                                for item in rows[-1]["niagara"]), "A native Niagara component retained trivial bounds")
                    report["analysis"]["four_niagara_active_with_nontrivial_bounds"] = True
                    for shot in report['screenshots']:
                        path=Path(shot['png'])
                        require(path.is_file() and path.read_bytes()[:8] == b'\x89PNG\r\n\x1a\n','Missing actual-game screenshot')
                        shot['sha256']=digest(path)
                    travel(state["world"], ENTRY, "WAIT_RETURN")
            elif state["phase"] == "WAIT_RETURN":
                if find_game_world(ENTRY) is not None:
                    state["phase"] = "RETURNED_ENTRY"
                    event("NATIVE_ENDPLAY_AND_ENTRY_RETURN_OBSERVED")
                    finish()
                else:
                    require(now - state["phase_started"] <= 20.0, "Native EndPlay/return travel timed out")
        except Exception:
            report["errors"].append(traceback.format_exc())
            if state["world"] is not None and state["phase"] != "WAIT_RETURN":
                travel(state["world"], ENTRY, "WAIT_RETURN")
            else:
                finish()
        finally:
            state["busy"] = False

    checkpoint()
    try:
        baseline = json.loads((WORK / "glb-baseline.json").read_text(encoding="utf-8"))
        state["sources"] = {row["file"]: row["sha256"].lower() for row in baseline["assets"]}
        require(len(state["sources"]) == 4 and all(digest(path) == expected for path, expected in state["sources"].items()),
                "Original source hashes differ from the four-file baseline")
        state["native"] = native_hashes()
        require(state["native"], "No native content packages found")
        report["protected_native_file_count"] = len(state["native"])
        report["protected_native_hashes"], report["protected_original_hashes"] = state["native"], state["sources"]
        state["handle"] = u.register_slate_post_tick_callback(tick)
        event("GAME_OBSERVER_REGISTERED")
    except Exception:
        report["errors"].append(traceback.format_exc())
        finish()
    return report_path


if __name__ == "__main__":
    main()
