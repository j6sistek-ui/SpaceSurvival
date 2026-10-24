"""Add small continuous top-nozzle mist in isolated CryoStage; dry-run first.

Creates one native Niagara system and eight auto-activating Niagara actors.
The accepted burst system, native interaction components, freeze materials,
breathing sequence and existing actors are preserved. No engine launch or
owner writes. Root serializes this after the optional v6 core geometry apply.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import runpy
import shutil
import traceback

WORK = Path(__file__).resolve().parent
G = runpy.run_path(str(WORK / "upgrade_cryo_fit_unreal.py"))
STAGE, BASE, MAP = (G[k] for k in ("STAGE", "BASE", "MAP"))
require, digest, package_hashes = (G[k] for k in ("require", "digest", "package_hashes"))
BASELINE = WORK / "CryoPolishV6Baseline.json"
CORE = WORK / "CryoCoreV6Apply.json"
NAME = "NS_CryoIdleJet_V6"
ASSET = BASE + "/FX/" + NAME
MATERIAL = BASE + "/Materials/M_NiagaraFreezeJet"
BURST = BASE + "/FX/NS_CryoFreezeJet_Contained"
MAP_FILE = "Content/SpaceSurvival/CryoComparison/Maps/L_CryoComparison.umap"
ASSET_FILE = "Content/SpaceSurvival/CryoComparison/FX/" + NAME + ".uasset"
LABELS = [bay + "_IdleJet_" + side for bay in "ABCD" for side in ("Left", "Right")]
RECIPE = {
    "spawn_rate_per_second": 10.0, "particle_lifetime_s": 0.95,
    "sprite_size_cm": [5.0, 9.0], "particle_color_rgba": [0.48, 0.82, 1.0, 0.55],
    "velocity_min_cm_s": [-1.0, -32.0, -46.0],
    "velocity_max_cm_s": [1.0, -26.0, -38.0],
    "loop_behavior": "Infinite", "loop_duration_s": 4.0, "loop_delay_s": 0.0,
    "local_culling_bounds_cm": {"min": [-25.0, -60.0, -75.0], "max": [25.0, 25.0, 25.0]},
    "local_space": True, "cpu_simulation": True,
    "estimated_live_particles_per_nozzle": 10,
    "maximum_center_downward_travel_cm": 43.7,
    "maximum_center_inward_travel_cm": 30.4,
    "behavior_during_freeze": "Continue; the separate existing burst remains stronger.",
}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def normalized(mapping):
    return {k.replace("\\", "/"): v for k, v in mapping.items()}


def check_protected(baseline):
    owner = Path(baseline["owner"])
    require(all(digest(owner / p) == h for p, h in baseline["owner_protected"].items()), "Owner protected files changed")
    require(all(digest(p) == h for p, h in baseline["source_glbs"].items()), "Original GLB changed")


def prepare():
    baseline = read(BASELINE)
    require(baseline["status"] == "V5_4_OWNER_AND_STAGE_MATCH", "Expected accepted v5.4 baseline")
    require(Path(baseline["stage"]).resolve() == STAGE.resolve(), "Baseline stage mismatch")
    require(digest(baseline["manifest"]) == baseline["manifest_sha256"], "Baseline geometry manifest changed")
    require(digest(baseline["previous_author"]) == baseline["previous_author_sha256"], "Accepted author receipt changed")
    expected = normalized(baseline["native_all"])
    transition = None
    if CORE.exists():
        core = read(CORE)
        require(core["status"].startswith("CORE_V6_SAVED") and not core["errors"], "Core transition is not a successful apply")
        require(normalized(core["native_before_hashes"]) == expected, "Core transition does not start at accepted baseline")
        expected = normalized(core["native_after_hashes"])
        transition = {"path": str(CORE), "sha256": digest(CORE)}
    require(normalized(package_hashes()) == expected, "Live stage differs from the explicit accepted hash chain")
    require(ASSET_FILE not in expected, "Idle system already exists; refusing overwrite")
    check_protected(baseline)
    manifest = read(baseline["manifest"])
    outlets = {}
    for model, x in zip(manifest["models"], (-540, -180, 180, 540)):
        require(model["id"] in "ABCD", "Unexpected bay")
        points = model["fit_v4"]["nozzle_outlets_blender_m"]
        require(len(points) == 2, "Expected two top outlets")
        for side, point in zip(("Left", "Right"), points):
            outlets[model["id"] + "_IdleJet_" + side] = [x + point[0] * 100, -point[1] * 100, point[2] * 100]
    require(set(outlets) == set(LABELS), "Incomplete nozzle placement plan")
    return baseline, expected, transition, outlets


def pose(component):
    rot = component.get_world_rotation()
    return {"location": list(component.get_world_location().to_tuple()),
            "rotation": [rot.pitch, rot.yaw, rot.roll],
            "scale": list(component.get_world_scale().to_tuple())}


def box_values(box):
    return {"min": list(box.get_editor_property("min").to_tuple()),
            "max": list(box.get_editor_property("max").to_tuple()),
            "is_valid": bool(box.get_editor_property("is_valid"))}


def existing_state(u, actor):
    row = G["actor_state"](u, actor)
    parent = actor.get_attach_parent_actor()
    row["attachment_parent"] = parent.get_path_name() if parent else None
    if isinstance(actor, u.SSCryoChamber):
        row.update(jet_system=actor.get_editor_property("jet_system").get_path_name(),
                   frost_surfaces=[v.get_path_name() for v in actor.get_editor_property("frost_surfaces")],
                   use_point=list(actor.get_editor_property("use_point").to_tuple()),
                   use_distance=actor.get_editor_property("use_distance"))
        row["nozzles"] = {}
        for key in ("left_nozzle", "right_nozzle"):
            comp = actor.get_editor_property(key)
            saved_system = comp.get_asset()
            row["nozzles"][key] = dict(pose(comp), system=saved_system.get_path_name() if saved_system else None,
                                       auto_activate=comp.get_editor_property("auto_activate"))
    if isinstance(actor, u.PointLight):
        light = actor.get_component_by_class(u.PointLightComponent)
        color = light.get_editor_property("light_color")
        row["light_color"] = [color.r, color.g, color.b, color.a]
        row["cast_shadows"] = light.get_editor_property("cast_shadows")
    if isinstance(actor, u.LocalFogVolume):
        comp = actor.get_component_by_class(u.LocalFogVolumeComponent)
        row["fog"] = {key: comp.get_editor_property(key) for key in (
            "radial_fog_extinction", "height_fog_extinction", "height_fog_falloff",
            "height_fog_offset", "fog_phase_g", "fog_start_distance", "fog_sort_priority")}
        for key in ("fog_albedo", "fog_emissive"):
            color = comp.get_editor_property(key)
            row["fog"][key] = [color.r, color.g, color.b, color.a]
    return row


def create_system(u, material, report):
    """Reuse the proven burst's native module stack with smaller idle settings."""
    fx = u.FXConverterUtilitiesLibrary
    plugin = Path(u.Paths.convert_relative_path_to_full(u.Paths.engine_plugins_dir())) / "FX/CascadeToNiagaraConverter/Content/Python"
    paths = runpy.run_path(str(plugin / "Paths.py"))
    system = u.AssetToolsHelpers.get_asset_tools().create_asset(NAME, BASE + "/FX", u.NiagaraSystem, u.NiagaraSystemFactoryNew())
    require(system is not None, "Idle system creation failed")
    system.set_editor_property("effect_type", None)
    bounds = u.Box()
    for key in ("min", "max"):
        bounds.set_editor_property(key, u.Vector(*RECIPE["local_culling_bounds_cm"][key]))
    bounds.set_editor_property("is_valid", True)
    # Use exact reflected C++ property names: the boolean and box have similar Python aliases.
    system.set_editor_property("bFixedBounds", True)
    system.set_editor_property("FixedBounds", bounds)
    require(bool(system.get_editor_property("bFixedBounds")), "Fixed bounds not enabled")
    require(box_values(system.get_editor_property("FixedBounds")) == dict(RECIPE["local_culling_bounds_cm"], is_valid=True), "Fixed bounds readback differs")
    context = fx.create_system_conversion_context(system)
    require(context is not None, "Native converter unavailable")
    try:
        emitter = context.add_empty_emitter("CryoIdleDownwardJet")
        emitter.set_local_space(True)
        emitter.set_sim_target(u.NiagaraSimTarget.CPU_SIM)
        emitter.set_enabled(True)
        E = u.ScriptExecutionCategory

        def module(name, path, category, version=None):
            data = fx.create_asset_data(path)
            args = u.CreateScriptContextArgs(data, version) if version else u.CreateScriptContextArgs(data)
            result = emitter.find_or_add_module_script(name, args, category)
            require(result is not None, "Native module unavailable: " + name)
            return result

        def put(script, name, value, *condition):
            require(script.set_parameter(name, value, *condition), "Native input rejected: " + name)

        state = module("EmitterState", "/Niagara/Modules/Emitter/EmitterState.EmitterState", E.EMITTER_UPDATE, [1, 0])
        for name, enum, value in (
            ("Life Cycle Mode", "enum_niagara_emitter_life_cycle_mode", "Self"),
            ("Inactive Response", "enum_niagara_inactive_mode", "Kill (Emitter and Particles Die Immediately)"),
            ("Loop Behavior", "enum_niagara_emitter_state_options", "Infinite")):
            put(state, name, fx.create_script_input_enum(paths[enum], value))
        put(state, "Loop Duration", fx.create_script_input_float(RECIPE["loop_duration_s"]))
        put(state, "Loop Delay", fx.create_script_input_float(0.0), True, True)
        spawn = module("SpawnRate", paths["script_spawnrate"], E.EMITTER_UPDATE, [1, 0])
        put(spawn, "SpawnRate", fx.create_script_input_float(RECIPE["spawn_rate_per_second"]))
        initialize = module("InitializeParticle", paths["script_initialize_particle"], E.PARTICLE_SPAWN, [1, 0])
        put(initialize, "Lifetime", fx.create_script_input_float(RECIPE["particle_lifetime_s"]))
        put(initialize, "Sprite Size Mode", fx.create_script_input_enum(paths["enum_niagara_size_scale_mode"], "Non-Uniform"))
        put(initialize, "Sprite Size", fx.create_script_input_vec2(u.Vector2D(*RECIPE["sprite_size_cm"])), True, True)
        color = module("JetInitialColor", paths["script_color"], E.PARTICLE_SPAWN)
        put(color, "Color", fx.create_script_input_linear_color(u.LinearColor(*RECIPE["particle_color_rgba"])))
        random = fx.create_script_context(u.CreateScriptContextArgs(fx.create_asset_data(paths["di_random_range_vector"]), [1, 0]))
        put(random, "Minimum", fx.create_script_input_vector(u.Vector(*RECIPE["velocity_min_cm_s"])))
        put(random, "Maximum", fx.create_script_input_vector(u.Vector(*RECIPE["velocity_max_cm_s"])))
        put(random, "Evaluation Type", fx.create_script_input_enum(paths["enum_niagara_randomness_evaluation"], "Spawn Only"))
        velocity = module("JetDownwardVelocity", paths["script_add_velocity"], E.PARTICLE_SPAWN, [1, 2])
        put(velocity, "Velocity", fx.create_script_input_dynamic(random, u.NiagaraScriptInputType.VEC3))
        particle = module("ParticleState", paths["script_particle_state"], E.PARTICLE_UPDATE, [1, 1])
        put(particle, "Kill Particles When Lifetime Has Elapsed", fx.create_script_input_bool(True))
        module("SolveForcesAndVelocity", paths["script_solve_forces_and_velocity"], E.PARTICLE_UPDATE)
        renderer = u.NiagaraSpriteRendererProperties()
        renderer.set_editor_property("material", material)
        renderer.set_editor_property("sub_image_size", u.Vector2D(1.0, 1.0))
        emitter.add_renderer("CryoIdleJetSprites", renderer)
        context.finalize()
        u.EditorAssetLibrary.set_metadata_tag(system, "CryoIdleRecipe", json.dumps(RECIPE, sort_keys=True))
        u.EditorAssetLibrary.set_metadata_tag(system, "CryoBurstReference", BURST)
        require(u.EditorAssetLibrary.save_loaded_asset(system, False), "Idle system save failed")
        info = list(u.NiagaraFunctionLibrary.get_all_emitters(system))
        require(len(info) == 1 and info[0].get_editor_property("is_enabled"), "Expected one enabled idle emitter")
        used = [v.get_path_name() for v in info[0].get_editor_property("used_renderer_materials")]
        require(used == [material.get_path_name()], "Idle renderer material changed")
        report["renderer_materials"] = used
        report["fixed_bounds_readback"] = box_values(system.get_editor_property("FixedBounds"))
        return system
    finally:
        context.cleanup()


def main(apply=False):
    receipt = WORK / ("CryoIdleJetV6Apply.json" if apply else "CryoIdleJetV6Plan.json")
    require(not receipt.exists(), "Never overwrite an idle-jet receipt")
    report = {"status": "PREPARING", "apply": apply, "utc": datetime.now(timezone.utc).isoformat(),
              "asset": ASSET, "map": MAP, "labels": LABELS, "recipe": RECIPE,
              "errors": [], "actors": [], "requires_editor_plugin": "CascadeToNiagaraConverter",
              "limits": ["Native save is not runtime or visual acceptance.",
                         "Fixed bounds limit culling, not particle positions; containment requires actual-game images.",
                         "Eight additional CPU systems/sprite renderers and about 80 live idle particles across four bays; no measured frame-time claim."]}
    u, allowed = None, False
    try:
        baseline, expected, transition, outlets = prepare()
        report.update(baseline=str(BASELINE), baseline_sha256=digest(BASELINE),
                      previous_transition=transition, native_before_hashes=package_hashes(),
                      planned_nozzle_origins_cm=outlets, manifest=baseline["manifest"], manifest_sha256=baseline["manifest_sha256"])
        if not apply:
            report["status"] = "DRY_RUN_READY_IDLE_JETS_V6"
            return report
        import unreal as u
        require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve() == STAGE.resolve(), "Restricted to isolated CryoStage")
        allowed = True
        require(hasattr(u, "FXConverterUtilitiesLibrary"), "Enable the bundled converter in stage authoring only")
        require(not u.EditorLevelLibrary.get_pie_worlds(False), "Refusing active PIE")
        require(not u.EditorAssetLibrary.does_asset_exist(ASSET), "Idle asset already exists")
        world = u.EditorLoadingAndSavingUtils.load_map(MAP)
        require(world is not None, "Comparison map load failed")
        subsystem = u.get_editor_subsystem(u.EditorActorSubsystem)
        actors = {a.get_actor_label(): a for a in subsystem.get_all_level_actors()}
        require(not set(LABELS) & set(actors), "Idle actor labels already exist")
        before_states = {name: existing_state(u, actor) for name, actor in actors.items()}
        parents = {bay: actors[bay + "_CryoInteraction"] for bay in "ABCD"}
        for bay, actor in parents.items():
            require(isinstance(actor, u.SSCryoChamber), "Native chamber class missing")
            require(actor.get_editor_property("jet_system").get_path_name().split(".")[0] == BURST, "Accepted burst binding changed")
            for side, key in (("Left", "left_nozzle"), ("Right", "right_nozzle")):
                actual = pose(actor.get_editor_property(key))
                planned = outlets[bay + "_IdleJet_" + side]
                require(max(abs(a-b) for a, b in zip(actual["location"], planned)) < 0.001, "Saved nozzle differs from accepted fit")
                require(max(abs(v) for v in actual["rotation"]) < 0.001 and actual["scale"] == [1.0, 1.0, 1.0], "Unexpected nozzle basis")
        material = u.EditorAssetLibrary.load_asset(MATERIAL)
        require(material and not material.get_editor_property("disable_depth_test"), "Shared sprite material must depth-test")
        require(material.get_editor_property("used_with_niagara_sprites"), "Shared material lacks Niagara usage")
        backup = WORK / ("pre_idle_jet_v6_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
        backup.mkdir(exist_ok=False)
        shutil.copy2(STAGE / MAP_FILE, backup / "L_CryoComparison.umap")
        require(digest(backup / "L_CryoComparison.umap") == expected[MAP_FILE], "Map backup mismatch")
        shutil.copy2(BASELINE, backup / BASELINE.name)
        if transition:
            shutil.copy2(CORE, backup / CORE.name)
        report.update(map_recovery=str(backup / "L_CryoComparison.umap"), existing_actor_states_before=before_states,
                      material_depth_test_enabled=True, original_burst_asset_sha256=expected["Content/SpaceSurvival/CryoComparison/FX/NS_CryoFreezeJet_Contained.uasset"])
        system = create_system(u, material, report)
        for bay, parent in parents.items():
            for side, key in (("Left", "left_nozzle"), ("Right", "right_nozzle")):
                nozzle = parent.get_editor_property(key)
                label = bay + "_IdleJet_" + side
                actor = subsystem.spawn_actor_from_class(u.NiagaraActor, nozzle.get_world_location(), nozzle.get_world_rotation())
                require(actor is not None, "Idle actor spawn failed")
                actor.set_actor_label(label)
                actor.set_folder_path("CryoComparison/NativeFX/IdleJetsV6")
                require(actor.attach_to_actor(parent, "", u.AttachmentRule.KEEP_WORLD,
                                              u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, False), "Idle parent attachment failed")
                comp = actor.get_component_by_class(u.NiagaraComponent)
                comp.set_asset(system)
                comp.set_auto_activate(True)
                comp.set_cast_shadow(False)
                comp.activate(True)
                actual_pose, target_pose = pose(comp), pose(nozzle)
                require(all(max(abs(a-b) for a, b in zip(actual_pose[key], target_pose[key])) < 0.0001
                            for key in ("location", "rotation", "scale")), "Idle actor does not share the nozzle pose")
                report["actors"].append({"bay": bay, "label": label, "path": actor.get_path_name(),
                    "component": comp.get_path_name(), "parent": parent.get_path_name(), "pose": pose(comp),
                    "auto_activate": comp.get_editor_property("auto_activate"),
                    "system": comp.get_asset().get_path_name(), "fixed_bounds": box_values(comp.get_system_fixed_bounds())})
        after_actors = {a.get_actor_label(): a for a in subsystem.get_all_level_actors()}
        require(set(after_actors) == set(actors) | set(LABELS), "Unexpected actor creation/removal")
        after_states = {name: existing_state(u, after_actors[name]) for name in actors}
        require(before_states == after_states, "Existing actor configuration changed")
        require(normalized(package_hashes()) == dict(expected, **{ASSET_FILE: digest(STAGE / ASSET_FILE)}), "Existing package changed before map save")
        require(u.EditorLoadingAndSavingUtils.save_map(world, MAP), "Idle actor map save failed")
        after = package_hashes()
        changed = sorted(k for k, value in expected.items() if normalized(after).get(k) != value)
        added = sorted(set(normalized(after)) - set(expected))
        require(changed == [MAP_FILE] and added == [ASSET_FILE], "Unexpected native package mutation")
        check_protected(baseline)
        report.update(status="IDLE_JETS_V6_SAVED_PENDING_RUNTIME_VISUAL_REVIEW", native_after_hashes=after,
                      changed_existing_packages=changed, added_packages=added,
                      existing_actor_states_after=after_states, existing_actor_configuration_unchanged=True,
                      accepted_freeze_materials_niagara_sequence_unchanged=True, owner_protected_and_sources_unchanged=True)
        return report
    except Exception:
        report["status"] = "FAILED"
        report["errors"].append(traceback.format_exc())
        if u:
            u.log_error(report["errors"][-1])
        return report
    finally:
        receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("CRYO_IDLE_JET_V6_RESULT " + json.dumps({"status": report["status"], "receipt": str(receipt)}), flush=True)
        if u and allowed:
            u.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main(False)
