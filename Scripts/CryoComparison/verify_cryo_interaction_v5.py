"""Observe four native freeze interactions in isolated uncooked CryoStage.

Launch Entry with -game -RenderOffscreen -Windowed -ForceRes -ResX=960 -ResY=1200
-ForceEnablePython and
-ExecCmds="py D:/.../verify_cryo_interaction.py". Python positions the review
pawn/camera, calls the same native controller action as E/X, and observes.
It never sets FreezeAmount, ticks an actor, activates jets, or saves assets.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import runpy
import struct
import time
import traceback

WORK = Path(__file__).resolve().parent
CHECKS = runpy.run_path(str(WORK / "verify_cryo_runtime.py"))
ANGLES = runpy.run_path(str(WORK / "verify_cryo_fit_angles.py"))
STAGE, BASE, MAP, CVAR = (CHECKS[key] for key in ("STAGE", "BASE", "MAP", "CVAR"))
require, digest, native_hashes = (CHECKS[key] for key in ("require", "digest", "native_hashes"))
ENTRY = "/Engine/Maps/Entry"
SHOTS = (("jet_start", .70), ("full_frost", 1.40), ("hold", 2.0), ("restored", 4.30))
C_SHOTS = (("jet_start", .70), ("full_frost", 1.40), ("frozen_left", 1.8),
           ("hold", 2.2), ("frozen_back", 2.6), ("frozen_right", 3.0), ("restored", 4.30))


def main():
    import unreal as u
    require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve() == STAGE.resolve(),
            "Restricted to isolated CryoStage")
    require(re.search(r"(?:^|\s)-game(?:\s|$)", u.SystemLibrary.get_command_line(), re.I), "Requires native -game")
    require(hasattr(u, "SSCryoChamber") and hasattr(u, "SSCryoPreviewController"), "Runtime plugin classes missing")
    receipt = WORK / ("CryoInteractionV5_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                      + "_" + str(os.getpid()) + ".json")
    captures = WORK.parent / "outputs/Cryo_Comparison/previews" / receipt.stem
    captures.mkdir(exist_ok=False)
    report = {"status": "RUNNING", "started_utc": datetime.now(timezone.utc).isoformat(),
              "mode": "UNCOOKED_NATIVE_CONTROLLER_INTERACTION", "errors": [], "events": [],
              "samples": [], "screenshots": [], "cycles": [], "map": MAP,
              "capture_command": "Shot", "capture_kind": "ORDINARY_VIEWPORT_WITH_TSR_HISTORY",
              "limits": ["Native action invoked through Python; physical keyboard/controller input is not simulated.",
                         "No manual tick, timer, FreezeAmount setter, Niagara activation, sequence seek, asset/config save.",
                         "Uncooked review-map proof; no packaged performance or production-map claim.",
                         "Particle active/bounds readback needs the captured frames for visual jet acceptance."]}
    state = {"started": time.monotonic(), "phase": "WAIT_ENTRY", "phase_started": time.monotonic(),
             "busy": False, "done": False, "handle": None, "world": None, "controller": None,
             "pawn": None, "camera": None, "chambers": {}, "panes": {}, "lights": {}, "ambient": [],
             "bay_index": 0, "cycle": None, "shots": [], "last_sample": 0.0, "cvar_set": False,
             "native": {}, "sources": {}, "blocker": None, "world_start": None, "pending_capture": None}

    def checkpoint():
        receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    def event(name, **data):
        report["events"].append({"event": name, "wall_s": time.monotonic() - state["started"], **data})
        checkpoint()

    def world_for(package):
        worlds = [w for w in u.ObjectIterator(u.World) if w.get_path_name().split(".", 1)[0] == package
                  and u.GameplayStatics.get_game_instance(w) is not None]
        require(len(worlds) <= 1, "Multiple game worlds")
        return worlds[0] if worlds else None

    def clear():
        state.update(world=None, controller=None, pawn=None, camera=None, chambers={}, panes={}, lights={}, ambient=[], blocker=None)

    def travel(world, destination, phase):
        state["phase"], state["phase_started"] = phase, time.monotonic()
        clear()
        event("NATIVE_TRAVEL", destination=destination)
        u.GameplayStatics.open_level(world, destination, True, "")

    def finish():
        if state["done"]:
            return
        state["done"] = True
        try:
            cvar = u.SystemLibrary.get_console_variable_float_value(CVAR)
            report["fog_start_distance_after_endplay"] = cvar
            if state["cvar_set"]:
                require(abs(cvar - 1000.0) < .01, "Sequence did not restore 1000cm fog distance on native EndPlay")
            after = native_hashes()
            require(after == state["native"], "Native packages changed while observing")
            require(all(digest(path) == expected for path, expected in state["sources"].items()), "Original GLB changed")
            require(len(report["cycles"]) == 4 and state["phase"] == "RETURNED_ENTRY", "Four native cycles not complete")
            for shot in report["screenshots"]:
                path = Path(shot["png"])
                require(path.is_file(), "Capture missing: " + str(path))
                with path.open("rb") as handle:
                    header = handle.read(24)
                require(header[:8] == b"\x89PNG\r\n\x1a\n" and list(struct.unpack_from(">II", header, 16)) == [960, 1200],
                        "Invalid capture output")
                shot.update(sha256=digest(path), bytes=path.stat().st_size)
            require(len(report["screenshots"]) == 19, "Expected four states each plus three C frozen-side captures")
            report.update(native_hashes_unchanged=True, original_source_hashes_unchanged=True, cvar_restored=True)
        except Exception:
            report["errors"].append(traceback.format_exc())
        report["status"] = "FAILED" if report["errors"] else "FOUR_NATIVE_FREEZE_CYCLES_VERIFIED_PENDING_VISUAL_REVIEW"
        report["finished_utc"], report["wall_duration_s"] = datetime.now(timezone.utc).isoformat(), time.monotonic() - state["started"]
        checkpoint()
        print("CRYO_INTERACTION_RESULT " + json.dumps({"status": report["status"], "receipt": str(receipt)}), flush=True)
        if state["handle"] is not None:
            u.unregister_slate_post_tick_callback(state["handle"])
        clear()
        u.SystemLibrary.execute_console_command(None, "quit")

    def rotation_towards(origin, target):
        delta = target - origin
        return u.Rotator(pitch=math.degrees(math.atan2(delta.z, math.hypot(delta.x, delta.y))),
                         yaw=math.degrees(math.atan2(delta.y, delta.x)))

    def position_user(chamber, distance=140.0):
        point = chamber.get_use_location()
        location = u.Vector(point.x, point.y + distance, max(88.0, point.z - 64.0))
        state["pawn"].set_actor_location(location, False, True)
        view = state["pawn"].get_actor_eyes_view_point()[0]
        state["controller"].set_control_rotation(rotation_towards(view, point))
        return location

    def check_native_collision(chamber):
        capsule = chamber.get_editor_property("body_collision")
        radius, half_height = capsule.get_scaled_capsule_radius(), capsule.get_scaled_capsule_half_height()
        require(abs(radius - 80.0) < .01 and abs(half_height - 160.0) < .01,
                "Saved chamber collision capsule differs from the shared recipe")
        # EngineTypes.h exposes ECollisionResponse as CollisionResponseType;
        # PyWrapperEnum.cpp provides its numeric value property (Block == 2).
        require(capsule.get_collision_response_to_channel(u.CollisionChannel.ECC_PAWN).value == 2,
                "Chamber capsule does not block the Pawn channel")
        pawn, origin = state["pawn"], chamber.get_actor_location()
        floor_start = u.Vector(origin.x, 270.0, 200.0)
        pawn.set_actor_location(floor_start, False, True)
        pawn.set_actor_location(u.Vector(origin.x, 270.0, -200.0), True, True)
        floor_end = pawn.get_actor_location()
        require(80.0 <= floor_end.z <= 95.0, "Review pawn sweep passed through the floor")
        forward_start = u.Vector(origin.x, 270.0, 100.0)
        pawn.set_actor_location(forward_start, False, True)
        pawn.set_actor_location(u.Vector(origin.x, 0.0, 100.0), True, True)
        forward_end = pawn.get_actor_location()
        require(100.0 <= forward_end.y <= 140.0 and abs(forward_end.z - 100.0) < .1,
                "Review pawn sweep did not stop at the chamber capsule")
        return {"capsule_radius_cm": radius, "capsule_half_height_cm": half_height,
                "floor_sweep_end_cm": list(floor_end.to_tuple()),
                "forward_sweep_end_cm": list(forward_end.to_tuple()),
                "native_sweeps_blocked": True, "physical_input_tested": False}

    def attach(world):
        state["world"] = world
        actors = list(u.GameplayStatics.get_all_actors_of_class(world, u.SSCryoChamber))
        require(len(actors) == 4, "Expected four saved interaction actors")
        # Infer bay from the explicitly bound frost actor, not an assumed interaction label.
        for actor in actors:
            surfaces = list(actor.get_editor_property("frost_surfaces"))
            require(len(surfaces) == 1, "Expected one joined frost surface per chamber")
            label = surfaces[0].get_actor_label()
            require(label in [bay + "_Frost" for bay in "ABCD"], "Unexpected frost surface")
            bay = label[0]
            require(bay not in state["chambers"] and actor.is_configured() and actor.get_bound_pane_count() == 1,
                    "Native material bindings failed for " + bay)
            state["chambers"][bay] = actor
            pane = surfaces[0].get_component_by_class(u.StaticMeshComponent).get_material(0)
            require(isinstance(pane, u.MaterialInstanceDynamic), "Native BeginPlay did not create a frost MID")
            state["panes"][bay] = pane
        state["controller"] = u.GameplayStatics.get_player_controller(world, 0)
        state["pawn"] = u.GameplayStatics.get_player_pawn(world, 0)
        require(isinstance(state["controller"], u.SSCryoPreviewController) and state["pawn"] is not None,
                "Saved review game mode did not provide the native preview controller/pawn")
        report["actual_viewport_size"] = list(state["controller"].get_viewport_size())
        require(report["actual_viewport_size"] == [960, 1200], "Launch must provide a real 960x1200 viewport")
        state["pawn"].get_component_by_class(u.CharacterMovementComponent).disable_movement()
        state["pawn"].set_actor_hidden_in_game(True)
        cameras = [a for a in u.GameplayStatics.get_all_actors_of_class(world, u.CameraActor)
                   if a.get_actor_label() == "CAM_D_Meshy_Raccoon"]
        require(len(cameras) == 1, "Missing saved review camera")
        state["camera"] = cameras[0]
        for actor in u.GameplayStatics.get_all_actors_of_class(world, u.PointLight):
            if actor.get_actor_label() in CHECKS["LIGHT_RANGES"]:
                state["lights"][actor.get_actor_label()] = actor.get_component_by_class(u.PointLightComponent)
        for actor in u.GameplayStatics.get_all_actors_of_class(world, u.NiagaraActor):
            comp = actor.get_component_by_class(u.NiagaraComponent)
            if comp and comp.get_asset() and comp.get_asset().get_path_name().startswith(BASE + "/"):
                state["ambient"].append(comp)
        require(len(state["lights"]) == 8 and len(state["ambient"]) == 4, "Shared light/ambient effects missing")
        begin_bay()

    def begin_bay():
        bay = "ABCD"[state["bay_index"]]
        chamber = state["chambers"][bay]
        point = chamber.get_actor_location()
        position = u.Vector(point.x - 210.0, 620.0, 235.0)
        target = u.Vector(point.x, 0.0, 160.0)
        state["camera"].set_actor_location_and_rotation(position, rotation_towards(position, target), False, True)
        camera_component = state["camera"].get_component_by_class(u.CameraComponent)
        camera_component.set_field_of_view(35.0)
        camera_component.set_aspect_ratio(.8)
        state["controller"].set_view_target_with_blend(state["camera"], 0.0)
        for actor in u.GameplayStatics.get_all_actors_of_class(state["world"], u.Actor):
            if re.match(r"^[ABCD]_", actor.get_actor_label()):
                actor.set_actor_hidden_in_game(not actor.get_actor_label().startswith(bay + "_"))
        collision = check_native_collision(chamber)
        position_user(chamber, 700.0)
        require(not chamber.can_use(state["pawn"]), "Distant use was allowed")
        distant_reply = chamber.interact(state["pawn"])
        require(not chamber.is_cooling(), "Distant interaction started a cycle")
        position_user(chamber)
        require(chamber.can_use(state["pawn"]), "Unblocked nearby use point is inaccessible")
        # Reuse the owned review-floor cube for a synchronous visibility test.
        # Native deferred spawning is Blueprint-internal and not Python-exposed.
        # Restore its exact transform/mobility before rendering another frame.
        midpoint = (state["pawn"].get_actor_eyes_view_point()[0] + chamber.get_use_location()) * .5
        floors = [a for a in u.GameplayStatics.get_all_actors_of_class(state["world"], u.StaticMeshActor)
                  if a.get_actor_label() == "Comparison_DarkFloor"]
        require(len(floors) == 1, "Owned review floor missing")
        blocker = floors[0]
        comp = blocker.get_component_by_class(u.StaticMeshComponent)
        original_transform, original_mobility = blocker.get_actor_transform(), comp.get_editor_property("mobility")
        try:
            comp.set_mobility(u.ComponentMobility.MOVABLE)
            blocker.set_actor_scale3d(u.Vector(.3, .3, .3))
            blocker.set_actor_location(midpoint, False, True)
            require(not chamber.can_use(state["pawn"]), "Occluded use was allowed")
            blocked_reply = chamber.interact(state["pawn"])
            require(not chamber.is_cooling(), "Blocked interaction started a cycle")
        finally:
            blocker.set_actor_transform(original_transform, False, True)
            comp.set_mobility(original_mobility)
        require(chamber.can_use(state["pawn"]), "Removed test blocker still blocks use")
        require(state["controller"].focused_chamber() == chamber, "Native controller focuses the wrong bay")
        state["cycle"] = {"bay": bay, "distant_reply": distant_reply, "blocked_reply": blocked_reply,
                          "collision": collision,
                          "distant_and_blocked_use_refused": True, "repeat_tested": False,
                          "finish_world_s": None, "sample_start": len(report["samples"])}
        state["phase"], state["phase_started"] = "SETTLE", time.monotonic()
        event("BAY_POSITIONED_AND_ACCESS_CHECKED", bay=bay)

    def sample():
        world_time = u.GameplayStatics.get_time_seconds(state["world"])
        values = {}
        for bay, actor in state["chambers"].items():
            jets = []
            for key in ("left_nozzle", "right_nozzle"):
                comp = actor.get_editor_property(key)
                origin, extent, radius = u.SystemLibrary.get_component_bounds(comp)
                jets.append({"component": key, "active": comp.is_active(), "origin": list(origin.to_tuple()),
                             "extent": list(extent.to_tuple()), "radius": radius,
                             "location": list(comp.get_world_location().to_tuple())})
            values[bay] = {"cooling": actor.is_cooling(), "freeze": actor.get_freeze_amount(),
                          "mid_freeze": state["panes"][bay].get_scalar_parameter_value("FreezeAmount"),
                          "native_elapsed": actor.get_cycle_elapsed(), "jets": jets}
        row = {"world_time_s": world_time, "cycle_world_elapsed": world_time - state["world_start"],
               "bay": state["cycle"]["bay"], "chambers": values,
               "lights": {name: float(comp.get_editor_property("intensity")) for name, comp in state["lights"].items()},
               "ambient_active": [comp.is_active() for comp in state["ambient"]],
               "fog_start_distance": u.SystemLibrary.get_console_variable_float_value(CVAR)}
        require(all(row["ambient_active"]) and abs(row["fog_start_distance"] - 10.0) < .01, "Ambient/fog playback regressed")
        for bay, value in values.items():
            require(abs(value["freeze"] - value["mid_freeze"]) < .002, "Actual MID differs from native freeze state")
            if bay != row["bay"]:
                require(not value["cooling"] and value["freeze"] == 0.0 and not any(j["active"] for j in value["jets"]),
                        "Interaction affected another chamber")
        report["samples"].append(row)
        return row

    def collect_viewport_capture(now):
        pending = state["pending_capture"]
        if pending is None or now - pending["requested_wall_s"] < .05:
            return
        fresh = [p for p in (STAGE / "Saved/Screenshots").rglob("*.png")
                 if p.resolve() not in pending["existing"] and p.stat().st_size > 24]
        require(len(fresh) <= 1, "Multiple ordinary screenshots prevent unambiguous attribution")
        if not fresh:
            require(now - pending["requested_wall_s"] < 5.0, "Ordinary Shot write timed out")
            return
        row = pending["row"]
        path = Path(row["png"])
        require(not path.exists(), "Refusing to overwrite an existing inspection frame")
        row["native_screenshot_path"] = str(fresh[0])
        # Ordinary screenshots are written asynchronously. Keep observing the
        # native cycle while the PNG writer finishes; never delay world time.
        try:
            with fresh[0].open("rb") as handle:
                handle.seek(-12, 2)
                complete = handle.read(12) == b"\x00\x00\x00\x00IEND\xaeB`\x82"
            if not complete:
                require(now - pending["requested_wall_s"] < 5.0, "Ordinary PNG writer did not finish")
                return
            fresh[0].replace(path)
        except PermissionError:
            require(now - pending["requested_wall_s"] < 5.0, "Ordinary PNG writer retained its file lock")
            return
        report["screenshots"].append(row)
        state["pending_capture"] = None

    def cycle_tick(now):
        row = sample()
        cycle, elapsed = state["cycle"], row["cycle_world_elapsed"]
        own = row["chambers"][cycle["bay"]]
        if elapsed >= 1.0 and not cycle["repeat_tested"]:
            actor = state["chambers"][cycle["bay"]]
            before = actor.get_cycle_elapsed()
            reply = actor.interact(state["pawn"])
            require(actor.is_cooling() and abs(actor.get_cycle_elapsed() - before) < .001,
                    "Repeated use reset/extended cycle state")
            cycle.update(repeat_tested=True, repeat_reply=reply, repeat_at_world_elapsed=elapsed)
        if not own["cooling"] and cycle["finish_world_s"] is None:
            require(3.9 <= elapsed <= 4.25, "Native cycle did not end at four world seconds: " + str(elapsed))
            require(own["freeze"] == 0.0 and not any(j["active"] for j in own["jets"]), "Frost/jets failed to reset")
            cycle["finish_world_s"] = elapsed
        if state["shots"] and elapsed >= state["shots"][0][1] and state["pending_capture"] is None:
            name, threshold = state["shots"].pop(0)
            point=state['chambers'][cycle['bay']].get_actor_location()
            delta={'frozen_left':(-650,0,160),'frozen_back':(0,-650,160),'frozen_right':(650,0,160)}.get(name,(-210,620,235))
            position=u.Vector(point.x+delta[0],delta[1],delta[2]);target=u.Vector(point.x,0,160)
            state['camera'].set_actor_location_and_rotation(position,rotation_towards(position,target),False,True)
            if name.startswith('frozen_'):require(own['freeze']>=.999,'Side capture must show fully frozen windows')
            path = captures / (cycle["bay"] + "_" + name + ".png")
            existing = {p.resolve() for p in (STAGE / "Saved/Screenshots").rglob("*.png")}
            u.SystemLibrary.execute_console_command(state["world"], "Shot")
            row = {"bay": cycle["bay"], "state": name, "png": str(path),
                "request_world_elapsed": elapsed, "actual_freeze_at_request": own["freeze"], "jets_at_request": own["jets"]}
            state["pending_capture"] = {"row": row, "existing": existing, "requested_wall_s": now}
        if elapsed >= 5.0 and not state["shots"] and state["pending_capture"] is None:
            require(cycle["finish_world_s"] is not None and cycle["repeat_tested"], "Cycle reset/repeat not observed")
            rows = report["samples"][cycle["sample_start"]:]
            require(len(rows) >= 20, "Too few native observations")
            require(max(r["chambers"][cycle["bay"]]["mid_freeze"] for r in rows) >= .999, "Windows never fully froze")
            moving = [r for r in rows if .7 <= r["cycle_world_elapsed"] <= 3.0]
            require(moving and all(all(j["active"] and j["radius"] > 10 for j in r["chambers"][cycle["bay"]]["jets"])
                                  for r in moving), "Jet components did not produce nontrivial active bounds")
            require(any(all(j["origin"][2] < j["location"][2] - 10.0 and j["extent"][2] > 20.0
                            for j in r["chambers"][cycle["bay"]]["jets"]) for r in moving),
                    "Native jet particle bounds did not extend downward from both nozzles")
            cycle.update(samples=len(rows), maximum_mid_freeze=max(r["chambers"][cycle["bay"]]["mid_freeze"] for r in rows),
                         jets_active_with_nontrivial_bounds=True, jet_bounds_extend_downward=True, other_bays_unchanged=True)
            report["cycles"].append(dict(cycle))
            state["bay_index"] += 1
            event("NATIVE_CYCLE_RESET_VERIFIED", bay=cycle["bay"], duration=cycle["finish_world_s"])
            if state["bay_index"] == 4:
                travel(state["world"], ENTRY, "WAIT_RETURN")
            else:
                begin_bay()

    def tick(_delta):
        if state["busy"] or state["done"]:
            return
        state["busy"] = True
        try:
            now = time.monotonic()
            require(now - state["started"] < 120.0, "Interaction observer deadline")
            if state["phase"] == "WAIT_ENTRY":
                world = world_for(ENTRY)
                if world:
                    report["process_rendering_overrides"] = {}
                    for name in ("r.AntiAliasingMethod",):
                        original = u.SystemLibrary.get_console_variable_float_value(name)
                        u.SystemLibrary.execute_console_command(world, name + " 4")
                        applied_value = u.SystemLibrary.get_console_variable_float_value(name)
                        require(applied_value == 4.0, "Transient rendering override failed: " + name)
                        report["process_rendering_overrides"][name] = {"before": original, "during": applied_value,
                            "scope": "DISPOSABLE_GAME_PROCESS_ONLY", "reason": "Match owner TSR and retain temporal history for dithered frost"}
                    u.SystemLibrary.execute_console_command(world, CVAR + " 1000")
                    require(u.SystemLibrary.get_console_variable_float_value(CVAR) == 1000.0, "Cannot set transient CVar baseline")
                    state["cvar_set"] = True
                    travel(world, MAP, "WAIT_TARGET")
            elif state["phase"] == "WAIT_TARGET":
                world = world_for(MAP)
                if world:
                    attach(world)
            elif state["phase"] == "SETTLE" and now - state["phase_started"] >= 1.5:
                state["world_start"] = u.GameplayStatics.get_time_seconds(state["world"])
                state["shots"] = list(C_SHOTS if state['cycle']['bay']=='C' else SHOTS)
                state["controller"].interact()
                require(state["chambers"][state["cycle"]["bay"]].is_cooling(), "Native controller did not start cooling")
                state["phase"] = "CYCLE"
                sample()
            elif state["phase"] == "CYCLE":
                collect_viewport_capture(now)
                if now - state["last_sample"] >= .045:
                    state["last_sample"] = now
                    cycle_tick(now)
            elif state["phase"] == "WAIT_RETURN" and world_for(ENTRY):
                state["phase"] = "RETURNED_ENTRY"
                finish()
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
        require(all(digest(path) == expected for path, expected in state["sources"].items()), "Original source hash mismatch")
        state["native"] = native_hashes()
        applied = json.loads((WORK / "CryoDisplayV5Apply.json").read_text(encoding="utf-8"))
        require(applied['status'] == 'DISPLAY_V5_SAVED_PENDING_VISUAL_REVIEW', 'V5 authoring did not pass')
        expected, chain = applied['native_after_hashes'], [str(WORK / 'CryoDisplayV5Apply.json')]
        require(state["native"] == expected, "Stage differs from exact v5 authoring receipt")
        report.update(matched_authoring_receipts=chain, protected_native_hashes=state["native"], protected_original_hashes=state["sources"])
        report.update(fit_manifest=applied["manifest"], fit_manifest_sha256=applied["manifest_sha256"])
        for matched in chain:
            if Path(matched).name in ("CryoTailFitApply.json", "CryoRearConsoleApply.json"):
                transition = json.loads(Path(matched).read_text(encoding="utf-8"))
                if transition.get("manifest"):
                    report.setdefault("base_fit_manifest", report["fit_manifest"])
                    report.update(fit_manifest=transition["manifest"], fit_manifest_sha256=digest(transition["manifest"]))
        state["handle"] = u.register_slate_post_tick_callback(tick)
        event("NATIVE_INTERACTION_OBSERVER_REGISTERED")
    except Exception:
        report["errors"].append(traceback.format_exc())
        finish()


if __name__ == "__main__":
    main()
