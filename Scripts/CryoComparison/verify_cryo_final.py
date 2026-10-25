"""Fresh-load, real-RHI CryoStage verification and unsaved offscreen captures.

Lead launches a NEW full editor process with -RenderOffscreen, never -NullRHI.
No source package, map, game setting or production save is persisted. Slate
post-ticks drive all waits; a 180-second callback deadline fails closed. An
external process watchdog is still needed if the native editor itself hangs.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import struct
import time
import traceback
import zlib
import runpy


WORK = Path(__file__).resolve().parent
STAGE = WORK / "CryoStage"
BASE = "/Game/SpaceSurvival/CryoComparison"
MAP = BASE + "/Maps/L_CryoComparison"
CAP_SECONDS = 180.0


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def serial(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [serial(item) for item in value]
    if hasattr(value, "get_path_name"):
        return value.get_path_name()
    if hasattr(value, "to_tuple"):
        return serial(list(value.to_tuple()))
    if all(hasattr(value, key) for key in ("r", "g", "b", "a")):
        return [value.r, value.g, value.b, value.a]
    return str(value)


def png_header(path):
    with Path(path).open("rb") as handle:
        data = handle.read(33)
    require(len(data) >= 33 and data[:8] == b"\x89PNG\r\n\x1a\n", "Screenshot is not a complete PNG: " + str(path))
    return list(struct.unpack_from(">II", data, 16))


def read_rgb_png(path):
    """Read screenshot pixels for analysis only; no images are edited or saved."""
    data = Path(path).read_bytes()
    width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack_from(">IIBBBBB", data, 16)
    require(bit_depth == 8 and color_type in (2, 6) and interlace == 0,
            "Temporal pixel analysis requires noninterlaced 8-bit RGB/RGBA PNG")
    channels = 3 if color_type == 2 else 4
    compressed = []
    pos = 8
    while pos + 12 <= len(data):
        length = int.from_bytes(data[pos:pos + 4], "big")
        kind = data[pos + 4:pos + 8]
        if kind == b"IDAT":
            compressed.append(data[pos + 8:pos + 8 + length])
        pos += 12 + length
    raw = zlib.decompress(b"".join(compressed))
    stride = width * channels
    require(len(raw) == height * (stride + 1), "Unexpected PNG decompressed byte count")
    pixels = bytearray(height * stride)
    previous = bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        kind = raw[start]
        row = bytearray(raw[start + 1:start + 1 + stride])
        require(kind <= 4, "Unknown PNG filter")
        for x in range(stride):
            a = row[x - channels] if x >= channels else 0
            b = previous[x]
            c = previous[x - channels] if x >= channels else 0
            if kind == 1:
                row[x] = (row[x] + a) & 255
            elif kind == 2:
                row[x] = (row[x] + b) & 255
            elif kind == 3:
                row[x] = (row[x] + ((a + b) // 2)) & 255
            elif kind == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                predictor = a if pa <= pb and pa <= pc else b if pb <= pc else c
                row[x] = (row[x] + predictor) & 255
        pixels[y * stride:(y + 1) * stride] = row
        previous = row
    return width, height, channels, pixels


def compare_region(a, b, rect):
    width, height, channels, pixels = a
    require(a[:3] == b[:3], "Temporal screenshots changed dimensions or channel layout")
    other = b[3]
    x0, y0, x1, y1 = rect
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(width, x1), min(height, y1)
    require(x1 > x0 and y1 > y0, "Projected temporal region is empty")
    count, total, changed, peak = 0, 0, 0, 0
    # Two-pixel sampling is sufficient to distinguish motion from exact reuse
    # without making a CPU image comparison dominate the capture run.
    for y in range(y0, y1, 2):
        for x in range(x0, x1, 2):
            i = (y * width + x) * channels
            differences = [abs(pixels[i + k] - other[i + k]) for k in range(3)]
            total += sum(differences)
            peak = max(peak, max(differences))
            changed += max(differences) >= 8
            count += 1
    return {"rectangle_pixels": [x0, y0, x1, y1], "sampled_pixels": count,
            "mean_absolute_rgb_difference_0_255": round(total / (count * 3), 4),
            "percent_pixels_with_channel_change_ge_8": round(100 * changed / count, 4),
            "max_channel_difference": peak}


def main():
    import unreal as u
    project = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    require(project == STAGE.resolve(), "Verifier is restricted to disposable CryoStage; refusing any other editor")
    out_root = Path(os.environ.get("CRYO_PREVIEW_DIR", WORK.parent / "outputs/Cryo_Comparison/previews")).resolve()
    require(out_root.is_relative_to(WORK.parent), "Screenshots must stay within the task's D-drive workspace")
    run_id = "Unreal_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + str(os.getpid())
    output = out_root / run_id
    output.mkdir(parents=True, exist_ok=False)
    receipt_path = output / "NativeVerification.json"
    report = {"status": "RUNNING", "started_utc": datetime.now(timezone.utc).isoformat(),
              "pid": os.getpid(), "engine": u.SystemLibrary.get_engine_version(), "project": str(project),
              "map": MAP, "screenshots": [], "niagara_samples": [], "light_samples": [], "errors": [], "warnings": [],
              "limits": ["Editor/offscreen captures are not a packaged benchmark or owner acceptance.",
                         "Active components and bounds do not by themselves prove particles are visible.",
                         "Temporal image differences may include temporal AA, volumetric history or lighting; review both frames.",
                         "Native particle-count access is reported unavailable when the installed reflected API lacks it.",
                         "No PIE, game-mode transition, source package save or production save is invoked.",
                         "180-second deadline is checked on Slate callbacks; an external watchdog must handle native hangs."]}
    state = {"started": time.monotonic(), "done": False, "busy": False, "handle": None,
             "index": 0, "task": None, "shot_start": 0.0, "frames": 0,
             "frame_deltas": [], "last_sample": 0.0, "protected": {}, "source_hashes": {},
             "shots": [], "niagara": [], "temporal_regions": {}, "pulse_player": None, "pulse_actor": None}
    pulse_api = runpy.run_path(str(WORK/'add_cryo_breathing_lights.py'))

    def checkpoint():
        receipt_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    def protected_hashes():
        folder = project / "Content/SpaceSurvival/CryoComparison"
        return {str(path): sha(path) for path in sorted(folder.rglob("*"))
                if path.is_file() and path.suffix.lower() in (".uasset", ".umap", ".uexp", ".ubulk")}

    def snapshot_niagara():
        if state['pulse_player'] is not None:
            current=state['pulse_player'].get_current_time()
            seconds=(current.time.frame_number.value+current.time.sub_frame)*current.rate.denominator/current.rate.numerator
            report['light_samples'].append({'elapsed_seconds':round(time.monotonic()-state['started'],3),
                'sequence_seconds':seconds,'playing':state['pulse_player'].is_playing(),
                'lights':pulse_api['snapshot_lights'](u,state['world'])})
        rows = []
        for actor, component in state["niagara"]:
            row = {"actor": actor.get_actor_label(), "is_active": component.is_active(),
                   "asset": serial(component.get_asset()), "bounds": serial(u.SystemLibrary.get_component_bounds(component)),
                   "age_update_mode": str(component.get_age_update_mode()),
                   "desired_age_diagnostic_only": component.get_desired_age(),
                   "particle_count": None, "particle_count_status": "NOT_EXPOSED_BY_INSTALLED_PYTHON_API"}
            if hasattr(component, "get_num_particles"):
                row["particle_count"] = int(component.get_num_particles())
                row["particle_count_status"] = "REFLECTED_NATIVE_READ"
            rows.append(row)
        return {"elapsed_seconds": round(time.monotonic() - state["started"], 3),
                "world_time_seconds": u.GameplayStatics.get_time_seconds(state["world"]),
                "world_real_time_seconds": u.GameplayStatics.get_real_time_seconds(state["world"]), "components": rows}

    def project_rect(camera, points, resolution):
        comp = camera.get_component_by_class(u.CameraComponent)
        width, height = resolution
        tan_h = math.tan(math.radians(float(comp.get_editor_property("field_of_view"))) * 0.5)
        tan_v = tan_h / (width / height)
        projected = []
        for point in points:
            local = u.MathLibrary.inverse_transform_location(camera.get_actor_transform(), u.Vector(*point))
            if local.x > 1.0:
                projected.append((width * (0.5 + 0.5 * local.y / (local.x * tan_h)),
                                  height * (0.5 - 0.5 * local.z / (local.x * tan_v))))
        require(projected, "Temporal region is behind the camera")
        return [math.floor(min(p[0] for p in projected)), math.floor(min(p[1] for p in projected)),
                math.ceil(max(p[0] for p in projected)), math.ceil(max(p[1] for p in projected))]

    def finish():
        if state["done"]:
            return
        state["done"] = True
        try:
            if state['pulse_player'] is not None:
                state['pulse_player'].stop()
                u.get_editor_subsystem(u.EditorActorSubsystem).destroy_actor(state['pulse_actor'])
                live=[sample for sample in report['light_samples'] if sample['playing']]
                report['natural_editor_light_loop']={'sample_count':len(live),'ranges':{}}
                for label in [bay+'_'+role for bay in 'ABCD' for role in ('InteriorGlow','RimGlow')]:
                    values=[light['intensity_lm'] for sample in live for light in sample['lights'] if light['label']==label]
                    report['natural_editor_light_loop']['ranges'][label]=[min(values),max(values)] if values else []
                    if not values or max(values)-min(values)<1:
                        report['warnings'].append('Natural editor pulse did not vary: '+label+'; PIE verification authoritative.')
            if state["protected"]:
                after = protected_hashes()
                changed = [path for path, value in state["protected"].items() if after.get(path) != value]
                new = sorted(set(after) - set(state["protected"]))
                report["native_packages_unchanged"] = not changed and not new
                report["changed_native_packages"] = changed
                report["new_native_packages"] = new
                require(not changed and not new, "Capture changed native content bytes")
            changed_sources = [path for path, value in state["source_hashes"].items() if not Path(path).is_file() or sha(path) != value]
            report["source_hashes_unchanged"] = not changed_sources
            require(not changed_sources, "Source inputs changed: " + str(changed_sources))
            frames = {row["name"]: row for row in report["screenshots"]}
            if "A_motion_t0" in frames and "A_motion_t1" in frames:
                a = read_rgb_png(frames["A_motion_t0"]["png"])
                b = read_rgb_png(frames["A_motion_t1"]["png"])
                regions = {name: compare_region(a, b, rect) for name, rect in state["temporal_regions"].items()}
                report["temporal_pixel_analysis"] = {
                    "same_camera": frames["A_motion_t0"]["camera"] == frames["A_motion_t1"]["camera"],
                    "separation_seconds": round(frames["A_motion_t1"]["elapsed_seconds"] - frames["A_motion_t0"]["elapsed_seconds"], 3),
                    "regions": regions,
                    "status": "VISIBLE_ANIMATION_REQUIRES_REVIEW_OF_THE_CAPTURE_PAIR",
                    "interpretation": "Localized changes with stable control support temporal change; pixel differences alone do not prove correct Niagara motion."}
                if regions["holo"]["mean_absolute_rgb_difference_0_255"] < 0.2:
                    report["warnings"].append("Holo region shows little temporal pixel change; inspect material clock and visibility.")
                if regions["cold_vapor_interior"]["mean_absolute_rgb_difference_0_255"] < 0.2:
                    report["warnings"].append("Vapor region shows little temporal pixel change; visible native mist motion remains unresolved.")
        except Exception:
            report["errors"].append(traceback.format_exc())
        dt = sorted(d * 1000 for d in state["frame_deltas"] if d > 0)
        report["frame_observations"] = {"kind": "SLATE_EDITOR_OFFSCREEN_CPU_FRAME_INTERVALS_NOT_GPU_OR_PACKAGED_BENCHMARK",
            "samples": len(dt), "median_ms": statistics.median(dt) if dt else None,
            "p95_ms": dt[min(len(dt) - 1, int(len(dt) * 0.95))] if dt else None,
            "maximum_ms": max(dt) if dt else None, "includes_capture_and_loading_overhead": True}
        report["elapsed_seconds"] = round(time.monotonic() - state["started"], 3)
        report["finished_utc"] = datetime.now(timezone.utc).isoformat()
        complete = len(report["screenshots"]) == 11 and report.get("native_packages_unchanged") and report.get("source_hashes_unchanged")
        report["status"] = "FRESH_LOAD_AND_CAPTURE_PASS_VISUAL_REVIEW_PENDING" if complete and not report["errors"] else "FAILED"
        checkpoint()
        (out_root / "latest-native.json").write_text(json.dumps({"directory": str(output), "receipt": str(receipt_path),
            "status": report["status"], "screenshot_count": len(report["screenshots"])}, indent=2) + "\n", encoding="utf-8")
        u.log("CRYO_NATIVE_VERIFY " + report["status"] + " " + str(receipt_path))
        if state["handle"] is not None:
            u.unregister_slate_post_tick_callback(state["handle"])
        u.EditorPythonScripting.set_keep_python_script_alive(False)
        u.SystemLibrary.quit_editor()

    def begin_shot():
        shot = state["shots"][state["index"]]
        if 'pulse_seconds' in shot:
            state['pulse_player'].pause()
            pulse_api['set_sequence_time'](u,state['pulse_player'],shot['pulse_seconds'])
        camera = shot["actor"]
        state.update(task=None, frames=0, shot_start=time.monotonic())
        u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(
            camera.get_actor_location(), camera.get_actor_rotation())
        u.log("CRYO_CAPTURE_BEGIN " + shot["name"])

    def tick(delta):
        if state["busy"] or state["done"]:
            return
        state["busy"] = True
        try:
            now = time.monotonic()
            require(now - state["started"] <= CAP_SECONDS, "180-second capture deadline reached")
            state["frames"] += 1
            state["frame_deltas"].append(float(delta))
            if now - state["last_sample"] >= 0.5:
                report["niagara_samples"].append(snapshot_niagara())
                state["last_sample"] = now
            shot = state["shots"][state["index"]]
            path = output / (shot["name"] + ".png")
            elapsed = now - state["shot_start"]
            if state["task"] is None and elapsed >= shot["settle_seconds"] and state["frames"] >= 30:
                # This native helper can wait for shader/texture streaming work;
                # the outer-process watchdog remains authoritative on a hang.
                u.AutomationLibrary.finish_loading_before_screenshot()
                state["request_sample"] = snapshot_niagara()
                state["task"] = u.AutomationLibrary.take_high_res_screenshot(
                    shot["resolution"][0], shot["resolution"][1], str(path), shot["actor"],
                    force_game_view=True, delay=0.3)
                require(state["task"] is not None and state["task"].is_valid_task(), "Screenshot request rejected: " + shot["name"])
            if state["task"] is not None and state["task"].is_task_done() and path.is_file():
                require(png_header(path) == shot["resolution"], "Screenshot resolution mismatch: " + shot["name"])
                camera = shot["actor"]
                comp = camera.get_component_by_class(u.CameraComponent)
                report["screenshots"].append({"name": shot["name"], "png": str(path.resolve()),
                    "sha256": sha(path), "bytes": path.stat().st_size, "resolution": shot["resolution"],
                    "camera": camera.get_actor_label(), "camera_location_cm": serial(camera.get_actor_location()),
                    "camera_rotation": serial(camera.get_actor_rotation()),
                    "field_of_view": comp.get_editor_property("field_of_view"),
                    "aspect_ratio": comp.get_editor_property("aspect_ratio"),
                    "elapsed_seconds": round(now - state["started"], 3),
                    "settle_seconds": elapsed, "natural_post_ticks": state["frames"],
                    "native_state_at_request": state["request_sample"]})
                checkpoint()
                state["index"] += 1
                if state["index"] == len(state["shots"]):
                    finish()
                else:
                    begin_shot()
            elif elapsed > 45.0:
                raise RuntimeError("Screenshot failed to finish/write within 45 seconds: " + shot["name"])
        except Exception:
            report["errors"].append(traceback.format_exc())
            u.log_error(report["errors"][-1])
            finish()
        finally:
            state["busy"] = False

    checkpoint()
    try:
        command_line = u.SystemLibrary.get_command_line().lower()
        require("-nullrhi" not in command_line and "-renderoffscreen" in command_line,
                "This verification requires real RHI with -RenderOffscreen and rejects -NullRHI")
        report["real_rhi_requested"] = True
        report["offscreen_requested"] = True
        report["fog_console_variables"] = {name: u.SystemLibrary.get_console_variable_int_value(name) for name in (
            "r.VolumetricFog", "r.LocalFogVolume", "r.SupportLocalFogVolumes",
            "r.LocalFogVolume.RenderIntoVolumetricFog", "r.LocalFogVolume.ApplyOnTranslucent")}
        report["fog_console_variables"]["r.LocalFogVolume.GlobalStartDistance"] = u.SystemLibrary.get_console_variable_float_value("r.LocalFogVolume.GlobalStartDistance")
        require(all(report["fog_console_variables"][name] > 0 for name in (
            "r.VolumetricFog", "r.LocalFogVolume", "r.SupportLocalFogVolumes")), "Native volumetric/local fog rendering is disabled")
        if report["fog_console_variables"]["r.LocalFogVolume.GlobalStartDistance"] > 500.0:
            report["warnings"].append("LocalFogVolume global start distance may exclude the 650cm individual-camera views; inspect native fog visibility.")
        author_path = Path(os.environ.get("CRYO_AUTHOR_RECEIPT", WORK / "CryoFinalAuthor.json")).resolve()
        author = json.loads(author_path.read_text(encoding="utf-8-sig"))
        require(author.get("status", "").startswith("AUTHORED_SAVED_"), "Authoring did not finish successfully")
        require(author["map"] == MAP, "Author receipt identifies another map")
        report["author_receipt"] = str(author_path)
        report["author_receipt_sha256"] = sha(author_path)
        state["source_hashes"] = {path: row["sha256"] for path, row in author["source_files"].items()}
        for path, value in state["source_hashes"].items():
            require(Path(path).is_file() and sha(path) == value, "Source changed before verification: " + path)
        state["protected"] = protected_hashes()
        require(state["protected"], "No saved CryoComparison packages exist")
        report["protected_native_package_count"] = len(state["protected"])
        editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
        require(not editor.get_game_world(), "No PIE is allowed during this asset-only preview")
        require(not u.EditorLoadingAndSavingUtils.get_dirty_map_packages(), "Unexpected dirty map before comparison load")
        require(u.EditorLoadingAndSavingUtils.load_map(MAP), "Comparison map failed fresh load")
        world = editor.get_editor_world()
        require(world.get_path_name().split(".")[0] == MAP, "Wrong loaded world")
        state["world"] = world
        state['pulse_player'],state['pulse_actor']=pulse_api['make_editor_preview_player'](u,world)
        state['pulse_player'].play_looping(-1)
        all_actors = list(u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors())
        by_label = {actor.get_actor_label(): actor for actor in all_actors}
        bodies = []
        for actor in all_actors:
            if isinstance(actor, u.StaticMeshActor):
                comp = actor.get_component_by_class(u.StaticMeshComponent)
                mesh = comp.get_editor_property("static_mesh")
                if mesh and u.EditorAssetLibrary.get_metadata_tag(mesh, "CryoRole") == "body":
                    require(comp.get_num_materials() == 1, "Body material slot count changed")
                    bodies.append({"actor": actor.get_actor_label(), "mesh": mesh.get_path_name(), "material": serial(comp.get_material(0)),
                                   "bounds": serial(u.SystemLibrary.get_component_bounds(comp))})
            elif isinstance(actor, u.NiagaraActor):
                state["niagara"].append((actor, actor.get_component_by_class(u.NiagaraComponent)))
        local_fog = [actor for actor in all_actors if isinstance(actor, u.LocalFogVolume)]
        global_fog = [actor for actor in all_actors if isinstance(actor, u.ExponentialHeightFog)]
        require(len(bodies) == 4, "Expected exactly four saved body meshes")
        require(len(state["niagara"]) == 4 and len(local_fog) == 4, "Expected four Niagara actors and four local fog volumes")
        require(len(global_fog) == 1 and global_fog[0].get_component_by_class(u.ExponentialHeightFogComponent).get_editor_property("enable_volumetric_fog"),
                "Expected one enabled native exponential volumetric fog actor")
        report["bodies"] = bodies
        report["local_fog"] = [{"actor": actor.get_actor_label(), "location": serial(actor.get_actor_location()),
            "scale": serial(actor.get_actor_scale3d()), "radial_density": actor.get_component_by_class(u.LocalFogVolumeComponent).get_editor_property("radial_fog_extinction")}
            for actor in local_fog]
        for path in author["saved_assets"]:
            require(u.EditorAssetLibrary.load_asset(path) is not None, "Saved asset did not fresh-load: " + path)
        expected_materials = [row["asset"] for row in author["materials"]]
        require(len(expected_materials) >= 13, "Missing shared finish/body materials")
        report["fresh_loaded_asset_count"] = len(author["saved_assets"])
        report["material_count"] = len(expected_materials)
        report["counts"] = {"bodies": 4, "niagara_actors": 4, "local_fog_volumes": 4}
        exposure = by_label.get("CryoPreview_Exposure")
        require(isinstance(exposure, u.PostProcessVolume), "Comparison exposure volume missing")
        settings = exposure.get_editor_property("settings")
        report["exposure"] = {key: serial(settings.get_editor_property(key)) for key in (
            "auto_exposure_method", "override_auto_exposure_method", "auto_exposure_bias", "override_auto_exposure_bias",
            "auto_exposure_apply_physical_camera_exposure", "override_auto_exposure_apply_physical_camera_exposure")}
        require(settings.get_editor_property("override_auto_exposure_method") and
                settings.get_editor_property("auto_exposure_method") == u.AutoExposureMethod.AEM_MANUAL,
                "Comparison exposure must be fixed manual across all cameras")
        overview = by_label.get("CAM_AllFour_Comparison")
        require(isinstance(overview, u.CameraActor), "Overview camera missing")
        state["shots"] = [{"name": "AllFour_Overview", "actor": overview, "resolution": [1920, 1080], "settle_seconds": 7.0}]
        individual = {}
        for model in author["plan"]:
            matches = [actor for label, actor in by_label.items() if label.startswith("CAM_" + model["id"] + "_")]
            require(len(matches) == 1 and isinstance(matches[0], u.CameraActor), "Missing/ambiguous individual camera: " + model["id"])
            individual[model["id"]] = matches[0]
            comp = matches[0].get_component_by_class(u.CameraComponent)
            require(abs(float(comp.get_editor_property("aspect_ratio")) - 0.8) < 0.01, "Individual camera must use portrait .8 aspect")
            state["shots"].append({"name": model["id"] + "_Individual", "actor": matches[0], "resolution": [960, 1200], "settle_seconds": 2.0})
        require("A" in individual, "Temporal review expects model A")
        for name, delay in (("A_motion_t0", 2.0), ("A_motion_t1", 2.7)):
            state["shots"].append({"name": name, "actor": individual["A"], "resolution": [960, 1200], "settle_seconds": delay})
        detail=by_label.get('DETAIL_D_Consoles')
        require(isinstance(detail,u.CameraActor),'Raised console detail camera missing')
        for name in ('D_Console_t0','D_Console_t1'):
            state['shots'].append({'name':name,'actor':detail,'resolution':[1280,720],'settle_seconds':2.7})
        for name,phase in (('A_PulseLow',0.0),('A_PulseHigh',3.0)):
            state['shots'].append({'name':name,'actor':individual['A'],'resolution':[960,1200],'settle_seconds':2.0,'pulse_seconds':phase})
        holo_actors = []
        for actor in all_actors:
            if actor.get_actor_label().startswith("A_") and isinstance(actor, u.StaticMeshActor):
                mesh = actor.get_component_by_class(u.StaticMeshComponent).get_editor_property("static_mesh")
                if mesh and u.EditorAssetLibrary.get_metadata_tag(mesh, "CryoRole") == "holo":
                    holo_actors.append(actor)
        require(holo_actors, "Model A holo mesh missing")
        corners = []
        for actor in holo_actors:
            origin, extent = actor.get_actor_bounds(False)
            corners.extend((origin.x + sx * extent.x, origin.y + sy * extent.y, origin.z + sz * extent.z)
                           for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1))
        state["temporal_regions"]["holo"] = project_rect(individual["A"], corners, [960, 1200])
        a_x = float(next(model["x_cm"] for model in author["plan"] if model["id"] == "A"))
        vapor = [(a_x + x, y, z) for x in (-45, 45) for y in (-35, 35) for z in (35, 220)]
        state["temporal_regions"]["cold_vapor_interior"] = project_rect(individual["A"], vapor, [960, 1200])
        state["temporal_regions"]["static_corner_control"] = [20, 20, 150, 150]
        # Native warm-up advances particle simulation once. Following capture
        # waits are natural editor post-ticks, not repeated manual advancement.
        for actor, component in state["niagara"]:
            require(component is not None and isinstance(component.get_asset(), u.NiagaraSystem), "Niagara actor has no native system")
            component.activate(True)
            component.advance_simulation(60, 1.0 / 30.0)
        report["niagara_warmup"] = {"manual_ticks_per_system": 60, "tick_seconds": 1.0 / 30.0,
                                    "natural_ticking_after_warmup": True, "particle_visibility": "REQUIRES_CAPTURES"}
        report["niagara_samples"].append(snapshot_niagara())
        checkpoint()
        begin_shot()
        u.EditorPythonScripting.set_keep_python_script_alive(True)
        state["handle"] = u.register_slate_post_tick_callback(tick)
    except Exception:
        report["errors"].append(traceback.format_exc())
        u.log_error(report["errors"][-1])
        finish()
    return {"output": str(output), "receipt": str(receipt_path), "handle": state["handle"]}


if __name__ == "__main__":
    main()
