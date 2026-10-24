"""Capture v5 displays/glass in the native game, trial first then all angles.

Launch only CryoStage, initially /Engine/Maps/Entry, with -game -RenderOffscreen
-Windowed -ForceRes -ResX=960 -ResY=1200
-ForceEnablePython and -ExecCmds="py D:/.../verify_cryo_fit_angles.py". Do not use
-ExecutePythonScript: that executor explicitly requires GIsEditor.

Derived from the successful native-game observer. Cameras and hidden states are
temporary game-world changes. Existing native effects advance naturally; no
sequence seek/light setter or package/config save is used. Root owns launches.
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
STAGE = CHECKS["STAGE"]
BASE, MAP, SEQUENCE = (CHECKS[key] for key in ("BASE", "MAP", "SEQUENCE"))
LIGHT_RANGES = CHECKS["LIGHT_RANGES"]
require, digest, native_hashes = (CHECKS[key] for key in ("require", "digest", "native_hashes"))
CVAR = CHECKS["CVAR"]
ENTRY = "/Engine/Maps/Entry"
ANGLES = {
    "front": (0.0, 650.0, 160.0), "front_left": (-420.0, 520.0, 220.0),
    "left": (-650.0, 0.0, 160.0), "back_left": (-420.0, -520.0, 220.0),
    "back": (0.0, -650.0, 160.0), "back_right": (420.0, -520.0, 220.0),
    "right": (650.0, 0.0, 160.0), "front_right": (420.0, 520.0, 220.0),
    "top": (0.0, 0.0, 700.0),
}
X_OFFSETS = dict(zip("ABCD", (-540.0, -180.0, 180.0, 540.0)))
TRIAL = True  # The final wrapper sets this False without editing this file.
APPLY = WORK / 'CryoDisplayV5Apply.json'


def shot_plan():
    wide = [{"bay": bay, "angle": angle, "name": bay + "_" + angle,
             "position_cm": [X_OFFSETS[bay] + delta[0], delta[1], delta[2]],
             "target_cm": [X_OFFSETS[bay], 0.0, 160.0], "fov": 35.0,
             "resolution": [960, 1200]}
            for bay in "ABCD" for angle, delta in ANGLES.items()]
    closeups = []
    for bay in ('A' if TRIAL else 'ABCD'):
        x = X_OFFSETS[bay]
        for name, position, target, fov in (
                ('console_detail', [-85, 210, 95], [-65, 72, 46], 27),
                ('status_detail', [-82, 180, 210], [-78, 40, 198], 25),
                ('glass_detail', [-165, 250, 165], [-20, 55, 160], 38)):
            closeups.append({'bay': bay, 'angle': name, 'name': bay + '_' + name,
                'position_cm': [position[0] + x, position[1], position[2]],
                'target_cm': [target[0] + x, target[1], target[2]], 'fov': fov,
                'resolution': [960, 1200]})
    if TRIAL:
        motion = {**closeups[0], 'angle': 'console_motion', 'name': 'A_console_motion', 'any_phase': True}
        return [wide[0], wide[1], closeups[0], motion] + closeups[1:]
    # Inspect every physical console; D's first mesh contains front and rear faces.
    extras = []
    for bay in 'ABCD':
        extra = dict(next(s for s in closeups if s['bay'] == bay and s['angle'] == 'console_detail'))
        extra.update(angle='console_other_detail', name=bay + '_console_other_detail')
        extras.append(extra)
    rear = dict(extras[-1])
    rear.update(angle='console_rear_detail', name='D_console_rear_detail')
    return wide + closeups + extras + [rear]


def final_authoring_hashes(applied):
    """Follow exact saved package transitions, regardless of authoring order."""
    expected, matched = applied["native_after_hashes"], []
    pending = {
        "CryoFit360Lighting.json": "REAR_FILL_SAVED_PENDING_360_REVIEW",
        "CryoFreezeFX.json": "FREEZE_MATERIAL_AND_JET_SAVED_PENDING_INTERACTION_RUNTIME",
        "CryoInteractionApply.json": "INTERACTION_MAP_SAVED_PENDING_RUNTIME",
        "CryoFreezeMasked.json": "MASKED_FREEZE_SAVED_PENDING_VISUAL_REVIEW",
        "CryoTailFitApply.json": "TAIL_GLASS_FIT_SAVED_PENDING_REVIEW",
        "CryoJetContainment.json": "INWARD_JET_SAVED_PENDING_VISUAL_REVIEW",
        "CryoRearConsoleApply.json": "REAR_CONSOLE_SAVED_PENDING_VISUAL_REVIEW",
    }
    while pending:
        progressed = False
        for name, status in list(pending.items()):
            path = WORK / name
            if not path.is_file():
                continue
            receipt = json.loads(path.read_text(encoding="utf-8"))
            if receipt.get("status") == status and receipt.get("native_before_hashes") == expected:
                expected = receipt["native_after_hashes"]
                matched.append(str(path))
                del pending[name]
                progressed = True
                break
        if not progressed:
            break
    return expected, matched


def authored_sidedness(current_hashes):
    """Editor-only material properties are unavailable in native -game.

    Bind saved authoring readbacks to the exact material package hashes seen
    by the game observer, so a stale receipt cannot attest a changed material.
    """
    rows = {}
    for filename, wanted_status in (("CryoFit360Lighting.json", "REAR_FILL_SAVED_PENDING_360_REVIEW"),
                                    ("CryoFreezeMasked.json", "MASKED_FREEZE_SAVED_PENDING_VISUAL_REVIEW")):
        path = WORK / filename
        require(path.is_file(), "Missing material authoring evidence: " + filename)
        receipt = json.loads(path.read_text(encoding="utf-8"))
        require(receipt.get("status") == wanted_status, "Authoring readback did not pass: " + filename)
        for row in receipt["native_material_sidedness"]:
            asset = row["asset"].split(".")[0]
            key = "Content\\" + asset[len("/Game/"):].replace("/", "\\") + ".uasset"
            require(current_hashes.get(key) == receipt["native_after_hashes"].get(key) and current_hashes.get(key),
                    "Material differs from authoring readback: " + asset)
            rows[asset.rsplit("/", 1)[-1]] = {**row, "authoring_receipt": str(path), "package_sha256": current_hashes[key],
                                           "evidence": "EDITOR_AUTHORING_READBACK_BOUND_TO_RUNTIME_PACKAGE_HASH"}
    required = {"M_Glass", "M_Frost", "M_Mist", "M_NiagaraColdMist", "M_FrostFreeze"}
    require(required.issubset(rows) and all(rows[name]["two_sided"] for name in required),
            "Two-sided window/fog evidence missing")
    return list(rows.values())


def main():
    import unreal as u
    project = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    require(project == STAGE.resolve(), "Restricted to the isolated D-drive CryoStage")
    require(re.search(r"(?:^|\s)-game(?:\s|$)", u.SystemLibrary.get_command_line(), re.I),
            "This observer requires an uncooked native -game process")
    report_path = WORK / (("CryoDisplayV5Trial_" if TRIAL else "CryoDisplayV5Angles_") + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                          + "_" + str(os.getpid()) + ".json")
    captures = WORK.parent / 'outputs/Cryo_Comparison/previews' / report_path.stem
    captures.mkdir(exist_ok=False)
    report = {"status": "RUNNING", "started_utc": datetime.now(timezone.utc).isoformat(),
              "engine": u.SystemLibrary.get_engine_version(), "project": str(project),
              "map": MAP, "sequence": SEQUENCE, "mode": "UNCOOKED_NATIVE_GAME_MULTIVIEW",
              "capture_command": "Shot", "capture_kind": "ORDINARY_VIEWPORT_WITH_TSR_HISTORY",
              "samples": [], "errors": [], "events": [], "screenshots": [],
              "limits": ["Uncooked native game verification, not packaged performance or production-map validation.",
                         "No Python sequence play/seek, light setters, asset saves or config writes.",
                         "Readback of intensity and Niagara active state does not prove visual quality.",
                         "Other bays are hidden temporarily for unobstructed fit inspection; this is not an all-four performance sample.",
                         "Each screenshot request waits for native peak phase (2.85-3.15s), never seeks the sequence.",
                         "390-second Slate-callback deadline; native hangs require external watchdog."]}
    state = {"started": time.monotonic(), "phase": "WAIT_ENTRY", "done": False, "busy": False,
             "handle": None, "world": None, "player": None, "lights": {}, "niagara": [],
             "native": {}, "sources": {}, "phase_started": time.monotonic(),
             "sampling_started": None, "last_sample": 0.0, "initial_cvar_configured": False}
    state.update(shots=shot_plan(), shot_index=0, shot_started=None, shot_requested=None,
                 camera=None, bay_actors=[], capture_complete=False)

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
        state["camera"], state["bay_actors"] = None, []
        state['mesh_actors'] = {}

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
        report["status"] = "FAILED" if report["errors"] else "NATIVE_DISPLAY_V5_CAPTURED_PENDING_VISUAL_REVIEW"
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
        report["actual_viewport_size"] = list(controller.get_viewport_size())
        require(report["actual_viewport_size"] == [960, 1200], "Launch must provide a real 960x1200 viewport")
        pawn=u.GameplayStatics.get_player_pawn(world,0)
        if pawn is not None:
            pawn.set_actor_hidden_in_game(True)
            report['preview_pawn_hidden_for_detached_camera_only']=pawn.get_path_name()
        state["camera"] = cameras[0]
        state["bay_actors"] = [actor for actor in u.GameplayStatics.get_all_actors_of_class(world, u.Actor)
                               if re.match(r"^[ABCD]_", actor.get_actor_label())]
        require(len(state["bay_actors"]) >= 76, "Missing bay actors for unobstructed inspection")
        applied = json.loads(APPLY.read_text(encoding="utf-8"))
        mesh_actors = {actor.get_actor_label(): actor for actor in u.GameplayStatics.get_all_actors_of_class(world, u.StaticMeshActor)}
        state['mesh_actors'] = mesh_actors
        for change in applied["changes"]:
            mesh = mesh_actors[change["actor"]].get_component_by_class(u.StaticMeshComponent).get_editor_property("static_mesh")
            require(mesh.get_path_name().split(".")[0] == change["asset"], "Runtime addon does not use v5: " + change["actor"])
        report["runtime_v5_addon_meshes_verified"] = len(applied["changes"])
        report["native_material_sidedness"] = authored_sidedness(state["native"])
        for binding in applied['role_bindings']:
            component = mesh_actors[binding['actor']].get_component_by_class(u.StaticMeshComponent)
            require(component.get_material(0).get_path_name().split('.')[0] == binding['material'],
                    'Runtime v5 material differs: ' + binding['actor'])
        report['runtime_v5_material_bindings_verified'] = len(applied['role_bindings'])
        report['v5_material_authoring_readbacks'] = applied['native_material_sidedness']
        controller.set_view_target_with_blend(state["camera"],0.0)
        report["runtime_world"], report["runtime_saved_sequence_actor"] = world.get_path_name(), actor.get_path_name()
        report["saved_autoplay"], report["saved_loop_count"] = True, -1
        state["phase"], state["sampling_started"] = "SAMPLING", time.monotonic()
        event("NATIVE_BEGINPLAY_AUTOPLAY_OBSERVED")
        begin_shot()

    def begin_shot():
        shot = state["shots"][state["shot_index"]]
        for actor in state["bay_actors"]:
            actor.set_actor_hidden_in_game(not actor.get_actor_label().startswith(shot["bay"] + "_"))
        position, target = shot["position_cm"], shot["target_cm"]
        if shot['angle'] in ('console_detail', 'console_motion', 'console_other_detail', 'console_rear_detail', 'status_detail'):
            console = shot['angle'].startswith('console_')
            component_name = ('Console_2_Glass' if shot['bay'] == 'D' else 'Console_1_Glass') if console else 'Status_Glass'
            if shot['angle'] == 'console_other_detail':
                component_name = 'Console_1_Glass' if shot['bay'] == 'D' else 'Console_2_Glass'
            elif shot['angle'] == 'console_rear_detail':
                component_name = 'Console_1_Glass'
            component = state['mesh_actors'][shot['bay'] + '_' + component_name].get_component_by_class(u.StaticMeshComponent)
            center, extent, radius = u.SystemLibrary.get_component_bounds(component)
            target = list(center.to_tuple())
            offset = ([70 if shot['bay'] == 'D' else -70, 125, 65] if console else [-12, 145, 5])
            if shot['angle'] == 'console_other_detail':
                offset = [-70 if shot['bay'] == 'D' else 70, 125, 65]
            if shot['bay'] == 'D' and component_name == 'Console_1_Glass':
                # The hash-verified source has two disconnected panes, on opposite Y sides.
                author = json.loads(APPLY.read_text(encoding='utf-8'))
                manifest = json.loads(Path(author['manifest']).read_text(encoding='utf-8-sig'))
                model = next(m for m in manifest['models'] if m['id'] == 'D')
                source = next(c for c in model['components'] if c['name'] == component_name)
                require(digest(source['file']) == source['source_sha256'], 'D console source changed')
                vertices = [list(map(float, line.split()[1:4])) for line in Path(source['file']).read_text().splitlines() if line.startswith('v ')]
                rear = shot['angle'] == 'console_rear_detail'
                vertices = [v for v in vertices if (v[1] > 0) == rear]
                require(vertices, 'Missing D front/rear console island')
                local = [(min(v[i] for v in vertices) + max(v[i] for v in vertices)) / 2 for i in range(3)]
                target = [X_OFFSETS['D'] + local[0], -local[1], local[2]]
                if rear:
                    offset = [0, -145, 65]
            position = [target[i] + offset[i] for i in range(3)]
            shot['position_cm'], shot['target_cm'] = position, target
        delta = [target[i] - position[i] for i in range(3)]
        yaw = math.degrees(math.atan2(delta[1], delta[0])) if math.hypot(delta[0], delta[1]) > 0.01 else -90.0
        pitch = math.degrees(math.atan2(delta[2], math.hypot(delta[0], delta[1])))
        state["camera"].set_actor_location_and_rotation(u.Vector(*position), u.Rotator(pitch=pitch, yaw=yaw), False, True)
        component = state["camera"].get_component_by_class(u.CameraComponent)
        component.set_field_of_view(shot["fov"])
        component.set_aspect_ratio(0.8)
        u.GameplayStatics.get_player_controller(state["world"], 0).set_view_target_with_blend(state["camera"], 0.0)
        state["shot_started"], state["shot_requested"] = time.monotonic(), None
        event("MULTIVIEW_CAMERA_SELECTED", shot_name=shot["name"], position_cm=position)

    def capture_tick(now):
        if state["capture_complete"]:
            return
        shot = state["shots"][state["shot_index"]]
        path = captures / (shot["name"] + ".png")
        if state["shot_requested"] is None:
            phase = CHECKS["sequence_seconds"](state["player"])
            if now - state["shot_started"] >= 2.5 and (shot.get('any_phase') or 2.85 <= phase <= 3.15):
                state["existing_shots"] = {p.resolve() for p in (STAGE / "Saved/Screenshots").rglob("*.png")}
                u.SystemLibrary.execute_console_command(state["world"], "Shot")
                state["shot_requested"] = now
                state["shot_metadata"] = {**shot, "png": str(path), "native_sequence_seconds_at_request": phase,
                    "at_elapsed_s": now - state["sampling_started"], "other_bays_hidden": True,
                    "light_intensities_at_request_lm": {name: float(comp.get_editor_property("intensity")) for name, comp in state["lights"].items()}}
            require(now - state["shot_started"] < 20.0, "No settled native peak phase for " + shot["name"])
        elif now - state["shot_requested"] >= 0.4:
            if not path.is_file():
                fresh = [p for p in (STAGE / "Saved/Screenshots").rglob("*.png")
                         if p.resolve() not in state["existing_shots"] and p.stat().st_size > 24]
                require(len(fresh) <= 1, "Multiple new standard screenshots prevent unambiguous attribution")
                if not fresh:
                    require(now - state["shot_requested"] < 15.0, "Ordinary Shot write timed out")
                    return
                state["shot_metadata"]["native_screenshot_path"] = str(fresh[0])
                fresh[0].replace(path)
            with path.open("rb") as handle:
                header = handle.read(24)
            require(header[:8] == b"\x89PNG\r\n\x1a\n" and list(struct.unpack_from(">II", header, 16)) == [960, 1200],
                    "Invalid screenshot output for " + shot["name"])
            report["screenshots"].append({**state["shot_metadata"], "sha256": digest(path), "bytes": path.stat().st_size})
            state["shot_index"] += 1
            if state["shot_index"] == len(state["shots"]):
                state["capture_complete"] = True
                event("ALL_REQUESTED_NATIVE_VIEWS_CAPTURED", count=len(state['shots']))
            else:
                begin_shot()
        else:
            require(now - state["shot_requested"] < 15.0, "Screenshot write timed out for " + shot["name"])

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
            require(now - state["started"] <= 390.0, "390-second native-game multi-angle deadline expired")
            if state["phase"] == "WAIT_ENTRY":
                world = find_game_world(ENTRY)
                if world is None:
                    require(now - state["phase_started"] <= 20.0, "Initial Entry game world unavailable")
                    return
                report["process_rendering_overrides"] = {}
                for name in ("r.AntiAliasingMethod",):
                    original = u.SystemLibrary.get_console_variable_float_value(name)
                    u.SystemLibrary.execute_console_command(world, name + " 4")
                    applied_value = u.SystemLibrary.get_console_variable_float_value(name)
                    require(applied_value == 4.0, "Transient rendering override failed: " + name)
                    report["process_rendering_overrides"][name] = {"before": original, "during": applied_value,
                        "scope": "DISPOSABLE_GAME_PROCESS_ONLY", "reason": "Match owner TSR and retain temporal history for dithered frost"}
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
                capture_tick(now)
                if now - state["last_sample"] >= CHECKS["SAMPLE_INTERVAL"]:
                    sample(now)
                rows = report["samples"]
                if (state["capture_complete"] and len(rows) > 1 and rows[-1]["wall_elapsed_s"] - rows[0]["wall_elapsed_s"] >= 14.0
                        and rows[-1]["world_time_s"] - rows[0]["world_time_s"] >= 14.0):
                    report["analysis"] = CHECKS["analyse"](rows)
                    require(all(item["bounds_radius_cm"] > 1.0 and max(item["bounds_extent_cm"]) > 1.0
                                for item in rows[-1]["niagara"]), "A native Niagara component retained trivial bounds")
                    report["analysis"]["four_niagara_active_with_nontrivial_bounds"] = True
                    require(len(report["screenshots"]) == len(state['shots']), "Incomplete v5 shot coverage")
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
        applied = json.loads(APPLY.read_text(encoding="utf-8"))
        require(applied['status'] == 'DISPLAY_V5_SAVED_PENDING_VISUAL_REVIEW', 'V5 import has not passed')
        expected_hashes = applied['native_after_hashes']
        report['matched_authoring_receipts'] = [str(APPLY)]
        require(state["native"] == expected_hashes, "Stage packages differ from the saved v5 authoring receipt")
        report["fit_manifest"] = applied["manifest"]
        report["fit_manifest_sha256"] = applied["manifest_sha256"]
        for matched in report["matched_authoring_receipts"]:
            if Path(matched).name in ("CryoTailFitApply.json", "CryoRearConsoleApply.json"):
                tail = json.loads(Path(matched).read_text(encoding="utf-8"))
                if tail.get("manifest"):
                    report.setdefault("base_fit_manifest", report["fit_manifest"])
                    report["fit_manifest"] = tail["manifest"]
                    report["fit_manifest_sha256"] = digest(tail["manifest"])
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
