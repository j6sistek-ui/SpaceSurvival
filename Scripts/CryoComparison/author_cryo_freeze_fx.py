"""Author shared freeze materials and a native downward Niagara jet in CryoStage.

Dry-run default. Apply requires bundled CascadeToNiagaraConverter enabled only
for editor authoring. Creates three new assets; changes four frost material
overrides in the owned map. Ambient fog, light sequence and source assets stay
unchanged. C++ interaction owns the four-second activation/reset, not this file.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import runpy
import shutil
import traceback

WORK = Path(__file__).resolve().parent
API = runpy.run_path(str(WORK / "author_cryo_unreal.py"))
GUARD = runpy.run_path(str(WORK / "upgrade_cryo_fit_unreal.py"))
BASE, MAP, STAGE = (GUARD[key] for key in ("BASE", "MAP", "STAGE"))
require, digest = API["require"], API["digest"]
FROST = BASE + "/Materials/M_FrostFreeze"
JET_MATERIAL = BASE + "/Materials/M_NiagaraFreezeJet"
JET_SYSTEM = BASE + "/FX/NS_CryoFreezeJet"


def frost_material(u, author, report):
    edit = u.MaterialEditingLibrary
    mat = u.EditorAssetLibrary.duplicate_asset(BASE + "/Materials/M_Frost", FROST)
    require(mat is not None, "Frost master duplication failed")
    author.created.append(mat)
    require(mat.get_editor_property("two_sided"), "Frozen windows must remain two-sided")
    freeze = author.node(mat, "MaterialExpressionScalarParameter", parameter_name="FreezeAmount", default_value=0.0)
    amount = author.node(mat, "MaterialExpressionSaturate")
    author.wire(freeze, amount, "Input")
    old = {}
    for name in ("MP_OPACITY", "MP_BASE_COLOR", "MP_EMISSIVE_COLOR", "MP_ROUGHNESS"):
        prop = getattr(u.MaterialProperty, name)
        node = edit.get_material_property_input_node(mat, prop)
        output = edit.get_material_property_input_node_output_name(mat, prop)
        require(node is not None, "Baseline frost input missing: " + name)
        old[name] = (node, output)
    uv = author.node(mat, "MaterialExpressionTextureCoordinate", coordinate_index=0)
    mist = author.sample(mat, u.EditorAssetLibrary.load_asset(BASE + "/Textures/T_Cryo_Mist"), "FreezeCrystals", "mask", uv)
    texture = author.sample(mat, u.EditorAssetLibrary.load_asset(BASE + "/Textures/T_Cryo_Frost"), "FreezeRime", "mask", uv)
    # Alpha noise supplies crystal variation across the clear center too.
    # Window opacity reaches exactly one at
    # FreezeAmount=1; no transparent holes inherited from edge-only frost art.
    mist_alpha = author.node(mat, "MaterialExpressionComponentMask", r=False, g=False, b=False, a=True)
    frost_alpha = author.node(mat, "MaterialExpressionComponentMask", r=False, g=False, b=False, a=True)
    author.wire(mist, mist_alpha, "Input", "RGBA")
    author.wire(texture, frost_alpha, "Input", "RGBA")
    crystal = author.custom(mat, "return saturate(0.30+0.50*M+0.20*F);", {"M": mist_alpha, "F": frost_alpha})
    frozen_color = author.node(mat, "MaterialExpressionLinearInterpolate")
    author.wire(author.color(mat, (.30, .62, .74)), frozen_color, "A")
    author.wire(author.color(mat, (.80, .96, 1.0)), frozen_color, "B")
    author.wire(crystal, frozen_color, "Alpha")
    frozen = {"MP_OPACITY": author.scalar(mat, 1.0), "MP_BASE_COLOR": frozen_color,
              "MP_EMISSIVE_COLOR": author.multiply(mat, frozen_color, .10),
              "MP_ROUGHNESS": author.scalar(mat, .88)}
    for name, end in frozen.items():
        blend = author.node(mat, "MaterialExpressionLinearInterpolate")
        author.wire(old[name][0], blend, "A", old[name][1])
        author.wire(end, blend, "B")
        author.wire(amount, blend, "Alpha")
        author.prop(blend, name)
    author.compile(mat)
    u.EditorAssetLibrary.set_metadata_tag(mat, "CryoFreezeParameter", "FreezeAmount: default0; fully opaque1")
    report["frost"] = {"asset": FROST, "parameter": "FreezeAmount", "default": 0.0,
                       "full_freeze_opacity": 1.0, "normal_state_keeps_original_graph_inputs": True,
                       "two_sided": True}
    return mat


def jet_material(u, author):
    mat = author.material("M_NiagaraFreezeJet", translucent=True, unlit=True, two_sided=True)
    u.MaterialEditingLibrary.set_material_usage(mat, u.MaterialUsage.MATUSAGE_NIAGARA_SPRITES)
    mist = author.sample(mat, u.EditorAssetLibrary.load_asset(BASE + "/Textures/T_Cryo_Mist"), "JetMist", "mask")
    particle = author.node(mat, "MaterialExpressionParticleColor")
    age = author.node(mat, "MaterialExpressionParticleRelativeTime")
    fade = author.custom(mat, "return smoothstep(0.0,0.08,A)*(1.0-smoothstep(0.72,1.0,A));", {"A": age})
    opacity = author.multiply(mat, author.multiply(mat, mist, particle, "A", "A"), fade)
    author.prop(author.multiply(mat, opacity, .65), "MP_OPACITY")
    author.prop(author.multiply(mat, particle, 1.15, "RGB"), "MP_EMISSIVE_COLOR")
    author.compile(mat)
    require(mat.get_editor_property("used_with_niagara_sprites"), "Missing Niagara sprite permutation")
    return mat


def jet_system(u, material, report, system_name="NS_CryoFreezeJet",
               velocity_min=(-5.0, -5.0, -140.0), velocity_max=(5.0, 5.0, -110.0),
               sprite_size=(16.0, 26.0)):
    fx = u.FXConverterUtilitiesLibrary
    plugin_python = Path(u.Paths.convert_relative_path_to_full(u.Paths.engine_plugins_dir())) / "FX/CascadeToNiagaraConverter/Content/Python"
    paths = runpy.run_path(str(plugin_python / "Paths.py"))
    system = u.AssetToolsHelpers.get_asset_tools().create_asset(
        system_name, BASE + "/FX", u.NiagaraSystem, u.NiagaraSystemFactoryNew())
    require(system is not None, "Empty Niagara system creation failed")
    system.set_editor_property("effect_type", None)
    context = fx.create_system_conversion_context(system)
    require(context is not None, "Niagara conversion context unavailable")
    try:
        emitter = context.add_empty_emitter("CryoDownwardJet")
        require(emitter is not None, "Empty jet emitter creation failed")
        emitter.set_local_space(True)
        emitter.set_sim_target(u.NiagaraSimTarget.CPU_SIM)
        emitter.set_enabled(True)
        E = u.ScriptExecutionCategory

        def module(name, path, category, version=None):
            data = fx.create_asset_data(path)
            args = u.CreateScriptContextArgs(data, version) if version else u.CreateScriptContextArgs(data)
            result = emitter.find_or_add_module_script(name, args, category)
            require(result is not None, "Missing native module: " + name)
            return result

        def set_input(script, name, value, *condition):
            require(script.set_parameter(name, value, *condition), "Native module input rejected: " + name)

        state = module("EmitterState", "/Niagara/Modules/Emitter/EmitterState.EmitterState", E.EMITTER_UPDATE, [1, 0])
        set_input(state, "Life Cycle Mode", fx.create_script_input_enum(paths["enum_niagara_emitter_life_cycle_mode"], "Self"))
        set_input(state, "Inactive Response", fx.create_script_input_enum(paths["enum_niagara_inactive_mode"], "Kill (Emitter and Particles Die Immediately)"))
        set_input(state, "Loop Behavior", fx.create_script_input_enum(paths["enum_niagara_emitter_state_options"], "Once"))
        set_input(state, "Loop Duration", fx.create_script_input_float(4.0))
        spawn = module("SpawnRate", paths["script_spawnrate"], E.EMITTER_UPDATE, [1, 0])
        set_input(spawn, "SpawnRate", fx.create_script_input_float(35.0))
        initialize = module("InitializeParticle", paths["script_initialize_particle"], E.PARTICLE_SPAWN, [1, 0])
        set_input(initialize, "Lifetime", fx.create_script_input_float(1.15))
        set_input(initialize, "Sprite Size Mode", fx.create_script_input_enum(paths["enum_niagara_size_scale_mode"], "Non-Uniform"))
        set_input(initialize, "Sprite Size", fx.create_script_input_vec2(u.Vector2D(*sprite_size)), True, True)
        color = module("JetInitialColor", paths["script_color"], E.PARTICLE_SPAWN)
        set_input(color, "Color", fx.create_script_input_linear_color(u.LinearColor(.48, .82, 1.0, .8)))
        # Explicit local velocity, independent of donor wind/gravity conventions.
        random = fx.create_script_context(u.CreateScriptContextArgs(fx.create_asset_data(paths["di_random_range_vector"]), [1, 0]))
        require(random is not None, "Native random velocity context unavailable")
        set_input(random, "Minimum", fx.create_script_input_vector(u.Vector(*velocity_min)))
        set_input(random, "Maximum", fx.create_script_input_vector(u.Vector(*velocity_max)))
        set_input(random, "Evaluation Type", fx.create_script_input_enum(paths["enum_niagara_randomness_evaluation"], "Spawn Only"))
        # Converter finalization inserts direct-set entries before modules.
        # Use the native AddVelocity module after InitializeParticle so its
        # initialization cannot overwrite the intended downward velocity.
        velocity = module("JetDownwardVelocity", paths["script_add_velocity"], E.PARTICLE_SPAWN, [1, 2])
        set_input(velocity, "Velocity", fx.create_script_input_dynamic(random, u.NiagaraScriptInputType.VEC3))
        particle_state = module("ParticleState", paths["script_particle_state"], E.PARTICLE_UPDATE, [1, 1])
        set_input(particle_state, "Kill Particles When Lifetime Has Elapsed", fx.create_script_input_bool(True))
        module("SolveForcesAndVelocity", paths["script_solve_forces_and_velocity"], E.PARTICLE_UPDATE)
        renderer = u.NiagaraSpriteRendererProperties()
        renderer.set_editor_property("material", material)
        renderer.set_editor_property("sub_image_size", u.Vector2D(1.0, 1.0))
        emitter.add_renderer("CryoJetSprites", renderer)
        context.finalize()
        # UNiagaraSystem::PreSave waits for outstanding compilation natively.
        require(u.EditorAssetLibrary.save_loaded_asset(system, False), "Native jet system save failed")
        infos = list(u.NiagaraFunctionLibrary.get_all_emitters(system))
        require(len(infos) == 1 and infos[0].get_editor_property("is_enabled"), "Expected one enabled jet emitter")
        used = [mat.get_path_name() for mat in infos[0].get_editor_property("used_renderer_materials")]
        require(material.get_path_name() in used, "Jet renderer material not connected")
        report["jet"] = {"system": BASE + "/FX/" + system_name, "emitter": "CryoDownwardJet", "local_space": True,
            "local_velocity_min_cm_s": list(velocity_min), "local_velocity_max_cm_s": list(velocity_max),
            "component_rotation_pitch_yaw_roll": [0, 0, 0], "spawn_rate_per_second": 35,
            "particle_lifetime_s": 1.15, "emitter_duration_s": 4.0, "sprite_size_cm": list(sprite_size),
            "maximum_downward_particle_center_travel_cm": 1.15 * abs(velocity_min[2]),
            "maximum_side_drift_cm": 1.15 * max(abs(velocity_min[0]), abs(velocity_max[0])),
            "maximum_inward_particle_center_travel_cm": 1.15 * max(0.0, -velocity_min[1]),
            "estimated_live_particles_per_nozzle": 41, "renderer_materials": used,
            "runtime_contract": "autoactivate false; Activate(reset) on interaction; DeactivateImmediate at four seconds"}
        return system
    finally:
        context.cleanup()


def main(apply=False):
    report = {"status": "DRY_RUN_READY", "apply": apply, "utc": datetime.now(timezone.utc).isoformat(),
              "new_assets": [FROST, JET_MATERIAL, JET_SYSTEM], "materials": [], "errors": [],
              "runtime_parameters": {"FreezeAmount": {"default": 0.0, "full": 1.0}},
              "requires_editor_plugin": "CascadeToNiagaraConverter",
              "limits": ["Native script authoring is not visual/runtime acceptance.",
                         "Jet components and four-second interaction are owned by the runtime interaction actor."]}
    u, allowed = None, False
    receipt = WORK / ("CryoFreezeFX.json" if apply else "CryoFreezeFXPlan.json")
    try:
        if not apply:
            return report
        import unreal as u
        require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve() == STAGE.resolve(), "Restricted to isolated CryoStage")
        allowed = True
        require(hasattr(u, "FXConverterUtilitiesLibrary"), "Enable bundled CascadeToNiagaraConverter in stage authoring project")
        require(not u.EditorLevelLibrary.get_pie_worlds(False), "Refusing active PIE")
        require(all(not u.EditorAssetLibrary.does_asset_exist(path) for path in report["new_assets"]), "Freeze assets already exist; refusing overwrite")
        before = GUARD["package_hashes"]()
        world = u.EditorLoadingAndSavingUtils.load_map(MAP)
        require(world is not None, "Map load failed")
        actors = {actor.get_actor_label(): actor for actor in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
        frost_components = []
        for bay in "ABCD":
            actor = actors.get(bay + "_Frost")
            require(actor is not None and isinstance(actor, u.StaticMeshActor), "Missing frost surface: " + bay)
            comp = actor.get_component_by_class(u.StaticMeshComponent)
            require(comp.get_num_materials() == 1 and comp.get_material(0).get_path_name().split(".")[0] == BASE + "/Materials/M_Frost", "Unexpected frost baseline")
            frost_components.append(comp)
        map_file = STAGE / "Content/SpaceSurvival/CryoComparison/Maps/L_CryoComparison.umap"
        backup = WORK / ("pre_freeze_fx_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
        backup.mkdir(exist_ok=False)
        shutil.copy2(map_file, backup / map_file.name)
        require(digest(map_file) == digest(backup / map_file.name), "Map recovery failed")
        report["map_recovery"] = str(backup / map_file.name)
        author = API["Author"](u, {}, "cryo-four-second-freeze-v1", report)
        frost = frost_material(u, author, report)
        material = jet_material(u, author)
        for asset in author.created:
            require(u.EditorAssetLibrary.save_loaded_asset(asset, False), "Freeze material save failed")
        system = jet_system(u, material, report)
        for comp in frost_components:
            comp.set_material(0, frost)
        require(u.EditorLoadingAndSavingUtils.save_map(world, MAP), "Freeze material map assignment save failed")
        after = GUARD["package_hashes"]()
        changed = [key for key in before if before[key] != after.get(key)]
        require(changed == ["Content\\SpaceSurvival\\CryoComparison\\Maps\\L_CryoComparison.umap"], "Existing package besides map changed")
        expected_added = sorted("Content\\" + path[len("/Game/"):].replace("/", "\\") + ".uasset" for path in report["new_assets"])
        require(sorted(set(after) - set(before)) == expected_added, "Unexpected new package output")
        report.update(status="FREEZE_MATERIAL_AND_JET_SAVED_PENDING_INTERACTION_RUNTIME", native_before_hashes=before,
                      native_after_hashes=after, changed_existing_packages=changed,
                      frost_actor_labels=[bay + "_Frost" for bay in "ABCD"], ambient_effects_and_breathing_sequence_unchanged=True)
        return report
    except Exception:
        report["status"] = "FAILED"
        report["errors"].append(traceback.format_exc())
        if u:
            u.log_error(report["errors"][-1])
        return report
    finally:
        receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("CRYO_FREEZE_FX_RESULT " + json.dumps({"status": report["status"], "receipt": str(receipt)}), flush=True)
        if u and allowed:
            u.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main(False)
