"""Author a native six-second cyan breathing loop in the isolated CryoStage.

Dry run: python add_cryo_breathing_lights.py
Apply in a full Unreal Editor with SequencerScripting enabled:
    runpy.run_path(script_path)["main"](True)

Only the owned comparison map and one new Level Sequence are saved. There is
no Python runtime light updater. The saved LevelSequenceActor starts the loop
on BeginPlay; normal editor viewports need explicit preview playback.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import traceback


WORK = Path(__file__).resolve().parent
STAGE = WORK / "CryoStage"
BASE = "/Game/SpaceSurvival/CryoComparison"
MAP = BASE + "/Maps/L_CryoComparison"
SEQUENCE = BASE + "/Sequences/LS_CryoBreathing_Cyan"
SEQUENCE_LABEL = "Cryo_BreathingCyan_Autoplay"
TAG = "CryoBreathingCyanV1"
FPS = 30
PERIOD = 6.0
KEY_TIMES = (0.0, 1.5, 3.0, 4.5, 6.0)
BAYS = tuple(zip("ABCD", (-540.0, -180.0, 180.0, 540.0)))
PROFILES = {
    "InteriorGlow": {"values": (5.0, 8.5, 12.0, 8.5, 5.0),
                     "offset": (0.0, 0.0, 260.0), "radius_cm": 175.0},
    "RimGlow": {"values": (4.0, 7.0, 10.0, 7.0, 4.0),
                "offset": (0.0, -30.0, 190.0), "radius_cm": 115.0},
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def playback_settings(u, auto_play):
    settings = u.MovieSceneSequencePlaybackSettings()
    settings.set_editor_property("auto_play", bool(auto_play))
    count = u.MovieSceneSequenceLoopCount()
    count.set_editor_property("value", -1)
    settings.set_editor_property("loop_count", count)
    settings.set_editor_property("play_rate", 1.0)
    settings.set_editor_property("random_start_time", False)
    settings.set_editor_property("start_time", 0.0)
    settings.set_editor_property("disable_camera_cuts", True)
    settings.set_editor_property("disable_movement_input", False)
    settings.set_editor_property("disable_look_at_input", False)
    settings.set_editor_property("hide_player", False)
    settings.set_editor_property("hide_hud", False)
    return settings


def snapshot_lights(u, world):
    """Read actual native component intensity; also usable in a PIE world."""
    expected = {bay + "_" + role for bay, _x in BAYS for role in PROFILES}
    rows = []
    for actor in u.GameplayStatics.get_all_actors_of_class(world, u.PointLight):
        label = actor.get_actor_label()
        if label in expected:
            component = actor.get_component_by_class(u.PointLightComponent)
            rows.append({"label": label, "intensity_lm": float(component.get_editor_property("intensity")),
                         "radius_cm": float(component.get_editor_property("attenuation_radius")),
                         "volumetric_scattering_intensity": float(component.get_editor_property("volumetric_scattering_intensity")),
                         "cast_shadows": bool(component.get_editor_property("cast_shadows"))})
    require({row["label"] for row in rows} == expected, "Expected exactly eight chamber breathing lights")
    return sorted(rows, key=lambda row: row["label"])


def make_editor_preview_player(u, world):
    """Create a transient native player for unsaved offscreen editor preview.

    Keep both returned objects referenced until capture finishes. Call
    player.play_looping(-1) once, then allow normal engine ticks; do not drive
    intensity from Python. Stop/destroy the transient actor without saving.
    This proves editor playback only, not saved-actor BeginPlay autoplay.
    """
    sequence = u.EditorAssetLibrary.load_asset(SEQUENCE)
    require(sequence is not None, "Breathing sequence is missing")
    player, actor = u.LevelSequencePlayer.create_level_sequence_player(
        world, sequence, playback_settings(u, False))
    require(player is not None and actor is not None, "Native preview player creation failed")
    return player, actor


def set_sequence_time(u, player, seconds):
    params = u.MovieSceneSequencePlaybackParams()
    params.set_editor_property("time", float(seconds))
    params.set_editor_property("position_type", u.MovieScenePositionType.TIME)
    params.set_editor_property("update_method", u.UpdatePositionMethod.JUMP)
    player.set_playback_position(params)


def add_intensity_track(u, sequence, actor, component, values):
    actor_binding = sequence.add_possessable(actor)
    component_binding = sequence.add_possessable(component)
    component_binding.set_parent(actor_binding)
    track = component_binding.add_track(u.MovieSceneFloatTrack)
    # Native reflected property spelling, not the Python snake_case alias.
    track.set_property_name_and_path("Intensity", "Intensity")
    section = track.add_section()
    section.set_start_frame_seconds(0.0)
    # The final key at 6 s is needed for interpolation up to the exclusive
    # sequence end. Keep the section unbounded so that key remains evaluable.
    section.set_end_frame_bounded(False)
    channels = section.get_channels_by_type(u.MovieSceneScriptingFloatChannel)
    require(len(channels) == 1, "Intensity must expose exactly one float channel")
    channel = channels[0]
    for seconds, value in zip(KEY_TIMES, values):
        channel.add_key(u.FrameNumber(round(seconds * FPS)), value, 0.0,
                        u.MovieSceneTimeUnit.DISPLAY_RATE, u.MovieSceneKeyInterpolation.AUTO)
    keys = channel.get_keys()
    require(len(keys) == 5, "Breathing track must contain five keys")
    readback = [{"seconds": key.get_time(u.MovieSceneTimeUnit.DISPLAY_RATE).frame_number.value / FPS,
                 "intensity_lm": float(key.get_value()),
                 "interpolation": str(key.get_interpolation_mode()),
                 "tangent": str(key.get_tangent_mode())} for key in keys]
    require([row["intensity_lm"] for row in readback] == list(values), "Intensity key readback mismatch")
    samples = list(channel.evaluate_keys(sequence.make_range(0, int(PERIOD * FPS)), u.FrameRate(60, 1)))
    require(samples and min(samples) >= min(values) - 0.01 and max(samples) <= max(values) + 0.01,
            "Breathing curve exceeded its intended intensity range")
    return {"actor": actor.get_actor_label(), "actor_binding": str(actor_binding.get_id()),
            "component_binding": str(component_binding.get_id()), "property": "Intensity",
            "keys": readback, "sampled_min_lm": min(samples), "sampled_max_lm": max(samples)}


def apply(u, report):
    actual_project = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    require(actual_project == STAGE.resolve(), "Refusing writes outside the isolated D-drive CryoStage")
    for name in ("LevelSequenceFactoryNew", "MovieSceneFloatTrack", "MovieSceneScriptingFloatChannel"):
        require(hasattr(u, name), "Required native API missing; enable SequencerScripting: " + name)
    assets = u.EditorAssetLibrary
    require(assets.does_asset_exist(MAP), "Comparison map is missing")
    require(not assets.does_asset_exist(SEQUENCE), "Sequence already exists; refuse to overwrite a saved iteration")
    world = u.EditorLoadingAndSavingUtils.load_map(MAP)
    require(world is not None and world.get_path_name().split(".")[0] == MAP, "Loaded world differs from owned comparison map")
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    require(actors is not None, "A full editor, not a commandlet, is required")
    labels = {}
    for actor in actors.get_all_level_actors():
        labels.setdefault(actor.get_actor_label(), []).append(actor)
    require(SEQUENCE_LABEL not in labels, "Breathing sequence actor already exists")
    for bay, _x in BAYS:
        require(len(labels.get(bay + "_InteriorGlow", [])) == 1, "Missing or duplicated existing interior light: " + bay)
        require(bay + "_RimGlow" not in labels, "Rim light already exists: " + bay)
        require(labels[bay + "_InteriorGlow"][0].get_component_by_class(u.PointLightComponent) is not None,
                "Existing interior light is not a PointLight: " + bay)
    report["engine"] = u.SystemLibrary.get_engine_version()
    report["map_sha256_before"] = digest(STAGE / "Content/SpaceSurvival/CryoComparison/Maps/L_CryoComparison.umap")
    sequence = u.AssetToolsHelpers.get_asset_tools().create_asset(
        SEQUENCE.rsplit("/", 1)[1], SEQUENCE.rsplit("/", 1)[0], u.LevelSequence, u.LevelSequenceFactoryNew())
    require(sequence is not None, "Level Sequence creation failed")
    sequence.set_display_rate(u.FrameRate(FPS, 1))
    sequence.set_playback_start(0)
    sequence.set_playback_end(int(FPS * PERIOD))
    assets.set_metadata_tag(sequence, "CryoScope", "Four-chamber shared breathing cyan lights")
    assets.set_metadata_tag(sequence, "CryoAuthoringVersion", TAG)
    assets.set_metadata_tag(sequence, "CryoPeriodSeconds", str(PERIOD))
    for bay, x in BAYS:
        for role, profile in PROFILES.items():
            label = bay + "_" + role
            if role == "InteriorGlow":
                actor = labels[label][0]
            else:
                dx, y, z = profile["offset"]
                actor = actors.spawn_actor_from_class(u.PointLight, u.Vector(x + dx, y, z))
                require(actor is not None, "Rim light spawn failed: " + bay)
                actor.set_actor_label(label)
                actor.set_folder_path("CryoComparison/Lighting")
            component = actor.get_component_by_class(u.PointLightComponent)
            component.set_mobility(u.ComponentMobility.MOVABLE)
            component.set_intensity_units(u.LightUnits.LUMENS)
            component.set_editor_property("use_inverse_squared_falloff", True)
            component.set_intensity(profile["values"][0])
            component.set_light_color(u.LinearColor(0.12, 0.72, 1.0, 1.0))
            component.set_attenuation_radius(profile["radius_cm"])
            component.set_source_radius(8.0)
            component.set_soft_source_radius(15.0)
            component.set_cast_shadows(False)
            component.set_volumetric_scattering_intensity(1.5)
            tags = list(actor.get_editor_property("tags"))
            if TAG not in [str(tag) for tag in tags]:
                actor.set_editor_property("tags", tags + [u.Name(TAG)])
            report["tracks"].append(add_intensity_track(u, sequence, actor, component, profile["values"]))
    sequence_actor = actors.spawn_actor_from_class(u.LevelSequenceActor, u.Vector(0.0, 0.0, 0.0))
    require(sequence_actor is not None, "LevelSequenceActor spawn failed")
    sequence_actor.set_actor_label(SEQUENCE_LABEL)
    sequence_actor.set_folder_path("CryoComparison/Lighting")
    sequence_actor.set_editor_property("tags", [u.Name(TAG)])
    sequence_actor.set_editor_property("playback_settings", playback_settings(u, True))
    sequence_actor.set_sequence(sequence)
    sequence_actor.set_editor_property('replicate_playback', False)
    settings = sequence_actor.get_editor_property("playback_settings")
    require(settings.get_editor_property("auto_play"), "Autoplay setting failed")
    require(settings.get_editor_property("loop_count").get_editor_property("value") == -1, "Infinite looping setting failed")
    report["autoplay"] = True
    report["loop_count"] = -1
    report["camera_cut_tracks"] = 0

    # Native component binding evaluation, before save. This is separate from
    # natural ticking, rendering, and PIE autoplay verification.
    player, transient_actor = make_editor_preview_player(u, world)
    try:
        for key_index, seconds in enumerate(KEY_TIMES[:-1]):
            set_sequence_time(u, player, seconds)
            sample = snapshot_lights(u, world)
            for row in sample:
                role = row["label"].split("_", 1)[1]
                require(abs(row["intensity_lm"] - PROFILES[role]["values"][key_index]) < 0.02,
                        "Native binding did not apply intensity at " + str(seconds) + " s: " + row["label"])
            report["native_evaluation_samples"].append({"sequence_seconds": seconds, "lights": sample})
    finally:
        player.stop()
        actors.destroy_actor(transient_actor)
        for actor in actors.get_all_level_actors():
            label = actor.get_actor_label()
            if label in {bay + "_" + role for bay, _x in BAYS for role in PROFILES}:
                component = actor.get_component_by_class(u.PointLightComponent)
                component.set_intensity(PROFILES[label.split("_", 1)[1]]["values"][0])
    require(len(report["tracks"]) == 8, "Expected eight native intensity tracks")
    report["saved_resting_lights"] = snapshot_lights(u, world)
    require(assets.save_loaded_asset(sequence, only_if_is_dirty=False), "Sequence save failed")
    require(u.EditorLoadingAndSavingUtils.save_map(world, MAP), "Owned comparison map save failed")
    report["map_sha256_after"] = digest(STAGE / "Content/SpaceSurvival/CryoComparison/Maps/L_CryoComparison.umap")
    report["saved_assets"] = [MAP, SEQUENCE]
    report["status"] = "SAVED_NATIVE_LOOP_BINDINGS_VERIFIED_RENDER_AND_AUTOPLAY_PENDING"


def main(do_apply=False):
    report = {"version": TAG, "utc": datetime.now(timezone.utc).isoformat(), "apply": bool(do_apply),
              "status": "DRY_RUN_NO_UNREAL_WRITES", "project": str(STAGE), "map": MAP,
              "sequence": SEQUENCE, "period_seconds": PERIOD, "display_rate_fps": FPS,
              "plan": {"bays": list(BAYS), "profiles": PROFILES, "key_seconds": KEY_TIMES,
                       "cyan_linear_rgb": [0.12, 0.72, 1.0], "scattering_multiplier": 1.5,
                       "new_point_lights": 4, "modified_point_lights": 4,
                       "shadow_casting": False, "phase_identical": True},
              "tracks": [], "native_evaluation_samples": [], "errors": [],
              "limits": ["Saved autoplay configuration and native curve evaluation are not runtime or visual acceptance.",
                         "Normal editor viewports do not invoke BeginPlay; use explicit transient native preview playback.",
                         "Verify at least two natural six-second cycles, including a loop boundary, in a freshly loaded map.",
                         "Real-RHI low/high phase captures must show subtle cyan fog illumination and a readable subject silhouette.",
                         "Eight animated light tracks and four added shadowless point lights still need representative runtime profiling."]}
    try:
        require(STAGE.is_dir(), "Isolated CryoStage directory is missing")
        require(len(BAYS) == 4 and all(len(p["values"]) == len(KEY_TIMES) for p in PROFILES.values()), "Invalid shared breathing plan")
        if do_apply:
            import unreal
            report["status"] = "FAILED"
            apply(unreal, report)
    except Exception:
        report["status"] = "FAILED"
        report["errors"].append(traceback.format_exc())
    receipt = WORK / ("CryoBreathingLights.json" if do_apply else "CryoBreathingLightsDryRun.json")
    receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("CRYO_BREATHING_LIGHT_RESULT " + json.dumps({"status": report["status"], "receipt": str(receipt), "errors": len(report["errors"])}), flush=True)
    if report["errors"]:
        raise RuntimeError("Breathing light authoring failed; inspect " + str(receipt))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args, _unknown = parser.parse_known_args()
    main(args.apply)
