"""Fresh-map native SIE autoplay verification; script only, no asset saves.

Run in a NEW full CryoStage editor with -RenderOffscreen. This script requests
Simulate in Editor, observes the saved LevelSequenceActor without playing or
seeking it from Python, and reads eight lights and four Niagara components
for at least fourteen natural seconds. Slate callbacks supply all waits.

The installed EditorLevelLibrary.editor_play_simulate() forwards to
LevelEditorSubsystem and also needs an active level viewport. Missing editor
services are a failed runtime check, never a successful simulated result.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time
import traceback


WORK = Path(__file__).resolve().parent
STAGE = WORK / "CryoStage"
BASE = "/Game/SpaceSurvival/CryoComparison"
MAP = BASE + "/Maps/L_CryoComparison"
SEQUENCE = BASE + "/Sequences/LS_CryoBreathing_Cyan"
SEQUENCE_LABEL = "Cryo_BreathingCyan_Autoplay"
LIGHT_RANGES = {bay + "_" + role: bounds for bay in "ABCD"
                for role, bounds in (("InteriorGlow", (5.0, 12.0)), ("RimGlow", (4.0, 10.0)))}
CAP_SECONDS = 90.0
SAMPLE_SECONDS = 14.0
SAMPLE_INTERVAL = 0.2
CVAR = "r.LocalFogVolume.GlobalStartDistance"
INITIAL_CVAR = 1000.0
ACTIVE_CVAR = 10.0


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(path):
    hasher = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def native_hashes():
    return {str(path.relative_to(STAGE)): digest(path) for path in sorted((STAGE / "Content").rglob("*"))
            if path.is_file() and path.suffix.lower() in (".uasset", ".umap", ".uexp", ".ubulk")}


def sequence_seconds(player):
    qualified = player.get_current_time()
    frame_time = qualified.get_editor_property("time")
    frame_number = frame_time.get_editor_property("frame_number").get_editor_property("value")
    sub_frame = frame_time.get_editor_property("sub_frame")
    rate = qualified.get_editor_property("rate")
    numerator = rate.get_editor_property("numerator")
    denominator = rate.get_editor_property("denominator")
    require(numerator > 0 and denominator > 0, "Native sequence reported an invalid frame rate")
    return (frame_number + sub_frame) * denominator / numerator


def analyse(samples):
    require(len(samples) >= 30, "Too few natural runtime observations")
    wall_span = samples[-1]["wall_elapsed_s"] - samples[0]["wall_elapsed_s"]
    world_span = samples[-1]["world_time_s"] - samples[0]["world_time_s"]
    require(wall_span >= SAMPLE_SECONDS and world_span >= SAMPLE_SECONDS,
            "Runtime sampling did not cover fourteen natural wall/world seconds")
    wraps = sum(current["sequence_time_s"] < previous["sequence_time_s"] - 3.0
                for previous, current in zip(samples, samples[1:]))
    require(wraps >= 2, "Saved sequence did not naturally wrap twice")
    require(all(sample["sequence_is_playing"] for sample in samples), "Saved sequence stopped during observation")
    require(all(abs(sample["local_fog_start_distance_cm"] - ACTIVE_CVAR) < 0.01 for sample in samples),
            "Saved CVar track did not hold 10 cm near-fog visibility throughout native looping")
    require(all(all(row["active"] for row in sample["niagara"]) and len(sample["niagara"]) == 4
                for sample in samples), "A native Niagara component was inactive during observation")
    rows = []
    for label, (low, high) in LIGHT_RANGES.items():
        values = [sample["light_intensities_lm"][label] for sample in samples]
        require(all(math.isfinite(value) and low - 0.05 <= value <= high + 0.05 for value in values),
                "Runtime intensity left intended bounds: " + label)
        require(min(values) <= low + 0.25 and max(values) >= high - 0.25,
                "Runtime intensity did not complete its expected fade range: " + label)
        rows.append({"actor": label, "observed_min_lm": min(values), "observed_max_lm": max(values),
                     "expected_min_lm": low, "expected_max_lm": high})
    max_same_role_spread = 0.0
    max_cross_role_phase_error = 0.0
    for sample in samples:
        values = sample["light_intensities_lm"]
        for role in ("InteriorGlow", "RimGlow"):
            group = [values[bay + "_" + role] for bay in "ABCD"]
            max_same_role_spread = max(max_same_role_spread, max(group) - min(group))
        for bay in "ABCD":
            inner = (values[bay + "_InteriorGlow"] - 5.0) / 7.0
            rim = (values[bay + "_RimGlow"] - 4.0) / 6.0
            max_cross_role_phase_error = max(max_cross_role_phase_error, abs(inner - rim))
    require(max_same_role_spread <= 0.02, "The four chambers' light phases diverged")
    require(max_cross_role_phase_error <= 0.02, "Interior and rim lights are not breathing together")
    return {"sample_count": len(samples), "wall_span_s": wall_span, "world_span_s": world_span,
            "natural_loop_wraps": wraps, "all_samples_native_sequence_playing": True,
            "all_four_niagara_active_throughout": True, "light_ranges": rows,
            "local_fog_start_distance_held_at_cm": ACTIVE_CVAR,
            "max_same_role_spread_lm": max_same_role_spread,
            "max_normalized_interior_rim_phase_error": max_cross_role_phase_error}


def main():
    import unreal as u
    project = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    # Exit before any world load or play request if the caller is not the stage.
    require(project == STAGE.resolve(), "Runtime verifier is restricted to the isolated D-drive CryoStage")
    report_path = WORK / ("CryoRuntime_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + str(os.getpid()) + ".json")
    report = {"status": "RUNNING", "started_utc": datetime.now(timezone.utc).isoformat(),
              "engine": u.SystemLibrary.get_engine_version(), "project": str(project),
              "map": MAP, "sequence": SEQUENCE, "mode": "NATIVE_SIMULATE_IN_EDITOR",
              "samples": [], "errors": [], "warnings": [], "events": [],
              "limits": ["This is native editor SIE, not a packaged-game benchmark or production-map test.",
                         "Intensity readback and active Niagara components do not prove visual quality or visible particles.",
                         "No Python play, seek, intensity setter, runtime driver, asset save or game save is used.",
                         "The isolated process CVar is set to 1000 cm once before SIE; native sequence must set 10 during playback and restore 1000 on EndPlay.",
                         "The ninety-second deadline runs on Slate callbacks; a native editor hang still needs an external watchdog."]}
    state = {"started": time.monotonic(), "phase": "PREFLIGHT", "done": False, "busy": False,
             "handle": None, "requested_at": None, "sampling_started": None, "last_sample": 0.0,
             "ending_at": None, "sources": {}, "native": {}, "world": None,
             "sequence_actor": None, "player": None, "lights": {}, "niagara": [],
             "initial_cvar_configured": False}

    def checkpoint():
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    def event(name, **data):
        report["events"].append({"event": name, "elapsed_s": round(time.monotonic() - state["started"], 3), **data})

    def worlds():
        return list(u.EditorLevelLibrary.get_pie_worlds(False))

    def request_end():
        if state["phase"] != "WAIT_END":
            u.EditorLevelLibrary.editor_end_play()
            state["phase"] = "WAIT_END"
            state["ending_at"] = time.monotonic()
            event("SIE_END_REQUESTED")
            checkpoint()

    def finish():
        if state["done"]:
            return
        state["done"] = True
        try:
            remaining = worlds()
            report["pie_worlds_remaining"] = [world.get_path_name() for world in remaining]
            require(not remaining, "SIE worlds still present at shutdown")
            if state["initial_cvar_configured"]:
                report["local_fog_start_distance_after_sie_cm"] = u.SystemLibrary.get_console_variable_float_value(CVAR)
                require(abs(report["local_fog_start_distance_after_sie_cm"] - INITIAL_CVAR) < 0.01,
                        "Native CVar track did not restore the initial 1000 cm after SIE")
                report["native_cvar_restoration_verified"] = bool(
                    report["samples"] and any(abs(sample["local_fog_start_distance_cm"] - ACTIVE_CVAR) < 0.01
                                              for sample in report["samples"]))
            if state["native"]:
                after = native_hashes()
                changed = sorted(key for key in set(state["native"]) | set(after) if state["native"].get(key) != after.get(key))
                report["native_hashes_unchanged"] = not changed
                report["native_changed_paths"] = changed
                require(not changed, "Native packages changed during runtime-only verification")
            if state["sources"]:
                changed = [path for path, expected in state["sources"].items() if digest(path) != expected]
                report["original_source_hashes_unchanged"] = not changed
                report["original_changed_paths"] = changed
                require(not changed, "Original GLB changed during runtime-only verification")
        except Exception:
            report["errors"].append(traceback.format_exc())
        report["status"] = "FAILED" if report["errors"] else "NATIVE_SIE_AUTOPLAY_LOOP_AND_PHASE_VERIFIED"
        report["finished_utc"] = datetime.now(timezone.utc).isoformat()
        report["elapsed_s"] = time.monotonic() - state["started"]
        checkpoint()
        print("CRYO_RUNTIME_RESULT " + json.dumps({"status": report["status"], "receipt": str(report_path),
                                                   "samples": len(report["samples"]), "errors": len(report["errors"])}), flush=True)
        if state["handle"] is not None:
            u.unregister_slate_post_tick_callback(state["handle"])
            state["handle"] = None
        u.EditorPythonScripting.set_keep_python_script_alive(False)
        u.SystemLibrary.quit_editor()

    def attach_runtime(world):
        package = world.get_path_name().split(".", 1)[0]
        expected_package = re.sub(r"/UEDPIE_\d+_", "/", package)
        require(expected_package == MAP, "SIE started an unexpected map: " + package)
        state["world"] = world
        actors = list(u.GameplayStatics.get_all_actors_of_class(world, u.LevelSequenceActor))
        selected = [actor for actor in actors if actor.get_actor_label() == SEQUENCE_LABEL]
        require(len(selected) == 1, "Expected exactly one saved breathing sequence actor in SIE")
        actor = selected[0]
        sequence = actor.get_sequence()
        require(sequence is not None and sequence.get_path_name().split(".", 1)[0] == SEQUENCE,
                "Runtime actor references an unexpected sequence")
        settings = actor.get_editor_property("playback_settings")
        require(settings.get_editor_property("auto_play"), "Saved runtime actor has autoplay disabled")
        require(settings.get_editor_property("loop_count").get_editor_property("value") == -1,
                "Saved runtime actor is not configured to loop forever")
        player = actor.get_editor_property('sequence_player')
        require(player is not None and player.is_playing(), "Saved sequence did not autoplay on native BeginPlay")
        state["sequence_actor"], state["player"] = actor, player
        for candidate in u.GameplayStatics.get_all_actors_of_class(world, u.PointLight):
            label = candidate.get_actor_label()
            if label in LIGHT_RANGES:
                require(label not in state["lights"], "Duplicate runtime light label: " + label)
                component = candidate.get_component_by_class(u.PointLightComponent)
                require(component is not None, "Point-light component missing: " + label)
                state["lights"][label] = component
        require(set(state["lights"]) == set(LIGHT_RANGES), "Expected all eight breathing lights in SIE")
        for candidate in u.GameplayStatics.get_all_actors_of_class(world, u.NiagaraActor):
            component = candidate.get_component_by_class(u.NiagaraComponent)
            asset = component.get_asset() if component else None
            if asset is not None and asset.get_path_name().startswith(BASE + "/"):
                state["niagara"].append((candidate.get_actor_label(), component))
        require(len(state["niagara"]) == 4, "Expected exactly four owned Niagara actors in SIE")
        report["runtime_world"] = world.get_path_name()
        report["runtime_saved_sequence_actor"] = actor.get_path_name()
        report["saved_autoplay"] = True
        report["saved_loop_count"] = -1
        state["phase"] = "SAMPLING"
        state["sampling_started"] = time.monotonic()
        event("SIE_AUTOPLAY_OBSERVED", sequence_is_playing=player.is_playing())

    def sample(now):
        state["last_sample"] = now
        row = {"wall_elapsed_s": now - state["sampling_started"],
               "world_time_s": float(u.GameplayStatics.get_time_seconds(state["world"])),
               "world_real_time_s": float(u.GameplayStatics.get_real_time_seconds(state["world"])),
               "sequence_time_s": sequence_seconds(state["player"]),
               "sequence_is_playing": bool(state["player"].is_playing()),
               "local_fog_start_distance_cm": u.SystemLibrary.get_console_variable_float_value(CVAR),
               "light_intensities_lm": {label: float(component.get_editor_property("intensity"))
                                        for label, component in sorted(state["lights"].items())},
               "niagara": [{"actor": label, "active": bool(component.is_active()),
                            "asset": component.get_asset().get_path_name()}
                           for label, component in state["niagara"]]}
        report["samples"].append(row)
        if len(report["samples"]) % 10 == 0:
            checkpoint()

    def tick(_delta_seconds):
        if state["done"] or state["busy"]:
            return
        state["busy"] = True
        try:
            now = time.monotonic()
            if state["phase"] == "WAIT_END":
                if not worlds():
                    event("SIE_ENDED")
                    finish()
                elif now - state["ending_at"] > 5.0:
                    report["errors"].append("Native SIE did not end within five seconds of the end-play request")
                    finish()
                return
            require(now - state["started"] <= CAP_SECONDS, "Ninety-second runtime verifier deadline expired")
            if state["phase"] == "WAIT_EDITOR":
                require(now - state["started"] < 30.0, "LevelEditorSubsystem or active viewport remained unavailable; SIE request cannot run")
                subsystem = u.get_editor_subsystem(u.LevelEditorSubsystem)
                if subsystem is None:
                    return
                if not list(subsystem.get_viewport_config_keys()):
                    return
                # This is the only play request. No direct player.play() call.
                u.EditorLevelLibrary.editor_play_simulate()
                state["requested_at"] = now
                state["phase"] = "WAIT_WORLD"
                event("NATIVE_SIE_REQUESTED")
                checkpoint()
            elif state["phase"] == "WAIT_WORLD":
                candidates = worlds()
                if candidates:
                    require(len(candidates) == 1, "Expected one isolated SIE world")
                    attach_runtime(candidates[0])
                    sample(now)
                    checkpoint()
                else:
                    require(now - state["requested_at"] < 25.0, "SIE request returned but no native PIE world appeared")
            elif state["phase"] == "SAMPLING":
                require(len(worlds()) == 1, "Native SIE ended unexpectedly")
                if now - state["last_sample"] >= SAMPLE_INTERVAL:
                    sample(now)
                samples = report["samples"]
                if len(samples) > 1 and samples[-1]["wall_elapsed_s"] - samples[0]["wall_elapsed_s"] >= SAMPLE_SECONDS and samples[-1]["world_time_s"] - samples[0]["world_time_s"] >= SAMPLE_SECONDS:
                    report["analysis"] = analyse(samples)
                    request_end()
        except Exception:
            report["errors"].append(traceback.format_exc())
            request_end()
        finally:
            state["busy"] = False

    checkpoint()
    # -ExecutePythonScript otherwise exits as soon as main() returns, before
    # Slate can service the asynchronous native SIE request and observations.
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    try:
        require(not worlds(), "An SIE/PIE world was already running; fresh runtime verification refused")
        require(u.EditorAssetLibrary.does_asset_exist(SEQUENCE), "Saved breathing sequence is missing")
        baseline = json.loads((WORK / "glb-baseline.json").read_text(encoding="utf-8"))
        state["sources"] = {row["file"]: row["sha256"].lower() for row in baseline["assets"]}
        require(len(state["sources"]) == 4, "Expected the four original GLBs in the baseline")
        require(all(digest(path) == expected for path, expected in state["sources"].items()), "Original GLB hash differs from initial baseline")
        state["native"] = native_hashes()
        require(state["native"], "No native content packages found")
        report["protected_native_file_count"] = len(state["native"])
        report["protected_native_hashes"] = state["native"]
        report["protected_original_hashes"] = state["sources"]
        world = u.EditorLoadingAndSavingUtils.load_map(MAP)
        require(world is not None and world.get_path_name().split(".", 1)[0] == MAP, "Fresh map load failed")
        report["local_fog_start_distance_process_initial_cm"] = u.SystemLibrary.get_console_variable_float_value(CVAR)
        # An unsaved, isolated-process test setup. No configuration file write.
        # Only the saved native sequence may change it after this point.
        u.SystemLibrary.execute_console_command(world, CVAR + " " + str(INITIAL_CVAR))
        report["local_fog_start_distance_before_sie_cm"] = u.SystemLibrary.get_console_variable_float_value(CVAR)
        require(abs(report["local_fog_start_distance_before_sie_cm"] - INITIAL_CVAR) < 0.01,
                "Could not establish the isolated runtime test's 1000 cm initial CVar")
        state["initial_cvar_configured"] = True
        state["phase"] = "WAIT_EDITOR"
        event("FRESH_MAP_LOADED")
        checkpoint()
        state["handle"] = u.register_slate_post_tick_callback(tick)
    except Exception:
        report["errors"].append(traceback.format_exc())
        if worlds():
            request_end()
            state["handle"] = u.register_slate_post_tick_callback(tick)
        else:
            finish()
    return report_path


if __name__ == "__main__":
    main()
