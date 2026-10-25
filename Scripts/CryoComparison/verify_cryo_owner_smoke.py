"""Read-only owner compatibility smoke; root owns the native process launch.

Launch SpaceSurvival.uproject /Engine/Maps/Entry?game=/Script/SSCryoRuntime.SSCryoPreviewGameMode
-game -RenderOffscreen -ForceEnablePython -ExecCmds="py D:/.../verify_cryo_owner_smoke.py"
No asset/config/save-game write, screenshot, manual tick, FX setter or sequence seek.
The native preview controller action is invoked; physical E/X input is not tested.
"""
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
OWNER = Path("C:/Users/j6sis/SpaceSurvival")
BASE = "/Game/SpaceSurvival/CryoComparison"
MAP = BASE + "/Maps/L_CryoComparison"
ENTRY = "/Engine/Maps/Entry"
MODE = "/Script/SSCryoRuntime.SSCryoPreviewGameMode"
CVAR = "r.LocalFogVolume.GlobalStartDistance"
PROOF = WORK / "CryoInteractionRuntime_20261022T051814Z_35888.json"


def require(value, message):
    if not value:
        raise RuntimeError(message)


def digest(path):
    hasher = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def main():
    import unreal as u
    require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve() == OWNER.resolve(),
            "Smoke restricted to the named owner SpaceSurvival project")
    command = u.SystemLibrary.get_command_line()
    require(re.search(r"(?:^|\s)-game(?:\s|$)", command, re.I) and "-renderoffscreen" in command.lower(),
            "Requires a disposable offscreen native game process")
    require(ENTRY + "?game=" + MODE in command, "Start Entry with explicit native cryo preview game mode")
    require(all(hasattr(u, name) for name in ("SSCryoChamber", "SSCryoPreviewController", "SSCryoPreviewGameMode")),
            "Owner native cryo plugin is unavailable")
    proof = json.loads(PROOF.read_text(encoding="utf-8"))
    require(not proof["errors"] and proof["status"].startswith("FOUR_NATIVE_FREEZE_CYCLES_VERIFIED"),
            "Final isolated interaction proof is invalid")
    expected = proof["protected_native_hashes"]
    receipt = WORK / ("CryoOwnerSmoke_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + str(os.getpid()) + ".json")
    report = {"status": "RUNNING", "project": str(OWNER), "started_utc": datetime.now(timezone.utc).isoformat(),
              "stage_proof": str(PROOF), "stage_proof_sha256": digest(PROOF), "errors": [], "samples": [],
              "limits": ["One uncooked owner-project compatibility cycle using the native preview controller action.",
                         "Physical keys, production game-mode interaction, packaged performance and owner visual acceptance are not tested.",
                         "No asset/config/save-game writes or rendering/effect parameter overrides requested."]}
    state = {"phase": "ENTRY", "started": time.monotonic(), "busy": False, "done": False, "handle": None,
             "world": None, "chambers": {}, "panes": {}, "ambient": [], "controller": None, "pawn": None,
             "last_sample": 0.0, "peak": 0.0, "jets_seen": False, "reset": None, "initial_fog": None,
             "guard_before": None}

    def checkpoint():
        receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    def protected_snapshot():
        files = {OWNER / name for name in expected}
        files.add(OWNER / "SpaceSurvival.uproject")
        for folder in ("Config", "Saved/SaveGames", "Plugins/SSCryoRuntime/Source", "Plugins/SSCryoRuntime/Binaries/Win64"):
            files.update(p for p in (OWNER / folder).rglob("*") if p.is_file() and p.suffix.lower() != ".pdb")
        files.add(OWNER / "Plugins/SSCryoRuntime/SSCryoRuntime.uplugin")
        return {str(p.relative_to(OWNER)): digest(p) for p in sorted(files)}

    def world_for(package):
        worlds = [w for w in u.ObjectIterator(u.World) if w.get_path_name().split(".", 1)[0] == package
                  and u.GameplayStatics.get_game_instance(w) is not None]
        require(len(worlds) <= 1, "Ambiguous native world")
        return worlds[0] if worlds else None

    def travel(world, target, phase):
        state.update(phase=phase, world=None, chambers={}, panes={}, ambient=[], controller=None, pawn=None)
        u.GameplayStatics.open_level(world, target, True, "game=" + MODE)

    def finish():
        if state["done"]:
            return
        state["done"] = True
        try:
            require(state["phase"] == "RETURNED" and state["reset"] is not None, "Native owner cycle/return incomplete")
            report["fog_after_endplay"] = u.SystemLibrary.get_console_variable_float_value(CVAR)
            require(abs(report["fog_after_endplay"] - state["initial_fog"]) < .01, "Fog CVar did not restore")
            require(protected_snapshot() == state["guard_before"], "Owner protected assets/config/save-game/plugin files changed")
            report.update(protected_files_unchanged=True, fog_restored=True, first_observed_reset_s=state["reset"],
                          actual_mid_reached_one=state["peak"] >= .999, native_jets_active_with_nontrivial_bounds=state["jets_seen"])
        except Exception:
            report["errors"].append(traceback.format_exc())
        report["status"] = "FAILED" if report["errors"] else "OWNER_NATIVE_COMPATIBILITY_SMOKE_PASS"
        report["finished_utc"] = datetime.now(timezone.utc).isoformat()
        checkpoint()
        print("CRYO_OWNER_SMOKE " + json.dumps({"status": report["status"], "receipt": str(receipt)}), flush=True)
        if state["handle"] is not None:
            u.unregister_slate_post_tick_callback(state["handle"])
        state.update(world=None, chambers={}, panes={}, ambient=[], controller=None, pawn=None)
        u.SystemLibrary.execute_console_command(None, "quit")

    def attach(world):
        require(isinstance(u.GameplayStatics.get_game_mode(world), u.SSCryoPreviewGameMode), "Unexpected owner game mode")
        state["world"] = world
        for actor in u.GameplayStatics.get_all_actors_of_class(world, u.SSCryoChamber):
            surfaces = list(actor.get_editor_property("frost_surfaces"))
            require(len(surfaces) == 1 and actor.is_configured() and actor.get_bound_pane_count() == 1,
                    "Owner chamber material binding failed")
            bay = surfaces[0].get_actor_label()[0]
            require(bay in "ABCD" and bay not in state["chambers"], "Unexpected owner chamber binding")
            state["chambers"][bay] = actor
            state["panes"][bay] = surfaces[0].get_component_by_class(u.StaticMeshComponent).get_material(0)
        require(set(state["chambers"]) == set("ABCD"), "Four configured owner chambers were not loaded")
        for actor in u.GameplayStatics.get_all_actors_of_class(world, u.NiagaraActor):
            comp = actor.get_component_by_class(u.NiagaraComponent)
            if comp and comp.get_asset() and comp.get_asset().get_path_name().startswith(BASE + "/"):
                state["ambient"].append(comp)
        require(len(state["ambient"]) == 4, "Four owner ambient Niagara systems were not loaded")
        state["controller"] = u.GameplayStatics.get_player_controller(world, 0)
        state["pawn"] = u.GameplayStatics.get_player_pawn(world, 0)
        require(isinstance(state["controller"], u.SSCryoPreviewController) and state["pawn"], "Native preview controller/pawn missing")
        state["pawn"].get_component_by_class(u.CharacterMovementComponent).disable_movement()
        point = state["chambers"]["A"].get_use_location()
        state["pawn"].set_actor_location(u.Vector(point.x, point.y + 140, max(88.0, point.z - 64)), False, True)
        delta = point - state["pawn"].get_actor_eyes_view_point()[0]
        state["controller"].set_control_rotation(u.Rotator(pitch=math.degrees(math.atan2(delta.z, math.hypot(delta.x, delta.y))),
                                                          yaw=math.degrees(math.atan2(delta.y, delta.x))))
        report["game_instance"] = u.GameplayStatics.get_game_instance(world).get_class().get_path_name()
        report["configured_chamber_count"] = 4
        state.update(phase="WARMUP", warmup=time.monotonic())

    def observe(now):
        elapsed = u.GameplayStatics.get_time_seconds(state["world"]) - state["cycle_start"]
        chamber = state["chambers"]["A"]
        freeze = state["panes"]["A"].get_scalar_parameter_value("FreezeAmount")
        require(abs(freeze - chamber.get_freeze_amount()) < .002, "Owner native frost and actual MID diverged")
        jets = [chamber.get_editor_property(name) for name in ("left_nozzle", "right_nozzle")]
        live = [bool(j.is_active()) for j in jets]
        radii = [u.SystemLibrary.get_component_bounds(j)[2] for j in jets]
        state["peak"] = max(state["peak"], freeze)
        state["jets_seen"] |= all(live) and all(radius > 10 for radius in radii)
        for bay in "BCD":
            other = state["chambers"][bay]
            require(not other.is_cooling() and state["panes"][bay].get_scalar_parameter_value("FreezeAmount") == 0,
                    "Owner interaction affected another bay")
        require(all(c.is_active() and u.SystemLibrary.get_component_bounds(c)[2] > 1 for c in state["ambient"]),
                "Owner ambient Niagara inactive or trivial")
        require(abs(u.SystemLibrary.get_console_variable_float_value(CVAR) - 10) < .01, "Owner native fog track is not active")
        report["samples"].append({"elapsed_world_s": elapsed, "cooling": chamber.is_cooling(), "mid_freeze": freeze,
                                  "nozzles_active": live, "nozzle_bounds_radii_cm": radii, "four_ambient_active": True})
        if not chamber.is_cooling() and state["reset"] is None:
            require(3.9 <= elapsed <= 4.25 and freeze == 0 and not any(live), "Owner four-second reset failed")
            state["reset"] = elapsed
        if elapsed >= 4.6:
            require(state["reset"] is not None and state["peak"] >= .999 and state["jets_seen"], "Owner native effect cycle incomplete")
            travel(state["world"], ENTRY, "RETURN")

    def tick(_delta):
        if state["done"] or state["busy"]:
            return
        state["busy"] = True
        try:
            now = time.monotonic()
            require(now - state["started"] < 90, "Owner smoke deadline exceeded")
            if state["phase"] == "ENTRY":
                world = world_for(ENTRY)
                if world:
                    require(isinstance(u.GameplayStatics.get_game_mode(world), u.SSCryoPreviewGameMode), "Entry used production game mode")
                    state["initial_fog"] = u.SystemLibrary.get_console_variable_float_value(CVAR)
                    report["initial_fog"] = state["initial_fog"]
                    travel(world, MAP, "TARGET")
            elif state["phase"] == "TARGET":
                world = world_for(MAP)
                if world:
                    attach(world)
            elif state["phase"] == "WARMUP" and now - state["warmup"] >= 2.0:
                require(state["controller"].focused_chamber() == state["chambers"]["A"], "Native owner controller focus failed")
                state["cycle_start"] = u.GameplayStatics.get_time_seconds(state["world"])
                state["controller"].interact()
                require(state["chambers"]["A"].is_cooling(), "Native owner controller action did not start cooling")
                state["phase"] = "CYCLE"
            elif state["phase"] == "CYCLE" and now - state["last_sample"] >= .045:
                state["last_sample"] = now
                observe(now)
            elif state["phase"] == "RETURN" and world_for(ENTRY):
                state["phase"] = "RETURNED"
                finish()
        except Exception:
            report["errors"].append(traceback.format_exc())
            if state["world"] is not None and state["phase"] != "RETURN":
                travel(state["world"], ENTRY, "RETURN")
            else:
                finish()
        finally:
            state["busy"] = False

    checkpoint()
    try:
        installed = {name: digest(OWNER / name) for name in expected}
        require(installed == expected, "Installed owner cryo/dependency packages differ from final tested stage")
        report.update(verified_installed_package_count=len(installed),
                      verified_cryo_package_count=sum(name.startswith("Content\\SpaceSurvival\\CryoComparison\\") for name in installed))
        state["guard_before"] = protected_snapshot()
        report["protected_before_hashes"] = state["guard_before"]
        state["handle"] = u.register_slate_post_tick_callback(tick)
        checkpoint()
    except Exception:
        report["errors"].append(traceback.format_exc())
        finish()


if __name__ == "__main__":
    main()
