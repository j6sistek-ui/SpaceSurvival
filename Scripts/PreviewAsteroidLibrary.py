"""Audition supplied construction-script fields in an unsaved editor world.

No vendor or game assets are saved. Overview views fit each native field;
approach views use the same 30,000 cm stand-off from its bounds. These are
composition evidence, not equivalent-density or gameplay performance tests.
"""
import hashlib
import json
from pathlib import Path
import time
import traceback
import uuid

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
BASE = "/Game/Asteroid_Library"


def vector(v):
    return [v.x, v.y, v.z]


def main():
    out = ROOT / "Artifacts/AsteroidAudition" / uuid.uuid4().hex
    out.mkdir(parents=True)
    vendor = ROOT / "Content/Asteroid_Library"
    def hashes():
        return {str(p.relative_to(vendor)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in vendor.rglob("*") if p.is_file()}
    protected = hashes()
    u.EditorLoadingAndSavingUtils.new_blank_map(False)
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    world = editor.get_editor_world()
    sky = actors.spawn_actor_from_class(u.StaticMeshActor, u.Vector())
    mesh = sky.get_component_by_class(u.StaticMeshComponent)
    mesh.set_static_mesh(u.load_asset("/Engine/BasicShapes/Sphere"))
    mesh.set_material(0, u.load_asset("/Game/SpaceSurvival/Licensed/Atmosphere/M_RegionSky"))
    mesh.set_editor_property("cast_shadow", False)
    sky.set_actor_scale3d(u.Vector(100000, 100000, 100000))
    for pitch, yaw, color, intensity in [(-35, -40, (.60, .77, 1, 1), 3.5),
                                         (20, 140, (1, .52, .24, 1), 1.2)]:
        light = actors.spawn_actor_from_class(u.DirectionalLight, u.Vector(),
                                              u.Rotator(pitch=pitch, yaw=yaw))
        lamp = light.get_component_by_class(u.DirectionalLightComponent)
        lamp.set_mobility(u.ComponentMobility.MOVABLE)
        lamp.set_light_color(u.LinearColor(*color))
        lamp.set_intensity(intensity)
    post = actors.spawn_actor_from_class(u.PostProcessVolume, u.Vector())
    post.set_editor_property("unbound", True)
    settings = post.get_editor_property("settings")
    for name, val in {"override_auto_exposure_min_brightness": True,
                      "override_auto_exposure_max_brightness": True,
                      "auto_exposure_min_brightness": 1., "auto_exposure_max_brightness": 1.,
                      "override_motion_blur_amount": True, "motion_blur_amount": 0.}.items():
        settings.set_editor_property(name, val)
    post.set_editor_property("settings", settings)
    camera = actors.spawn_actor_from_class(u.CameraActor, u.Vector())
    camera.get_component_by_class(u.CameraComponent).set_field_of_view(70)
    u.get_editor_subsystem(u.LevelEditorSubsystem).editor_set_game_view(True)
    record = {"status": "RUNNING", "engine": u.SystemLibrary.get_engine_version(),
              "fields": [], "meshes": [], "textures": [], "images": [], "errors": [],
              "limits": ["Unsaved constructed editor actors, not runtime adoption.",
                         "Overview fits native bounds; approach stand-off is 30000 cm.",
                         "No physical input, balance, FPS or owner acceptance."]}
    for path in u.EditorAssetLibrary.list_assets(BASE + "/Static_Meshes", recursive=True):
        obj = u.load_asset(path)
        if isinstance(obj, u.StaticMesh):
            record["meshes"].append({"path": path, "radius": obj.get_bounds().sphere_radius,
                                      "lods": obj.get_num_lods(),
                                      "materials": [str(s.material_interface.get_path_name())
                                                    if s.material_interface else None
                                                    for s in obj.get_editor_property("static_materials")]})
    for path in ["/Game/SpaceSurvival/Licensed/Atmosphere/T_Region_Skybox_8",
                 "/Game/SpaceNebulaFantasy/Textures/Skybox_8/T_Nebula_Turquoise_Dark_8"]:
        obj = u.load_asset(path)
        record["textures"].append({"path": path, "max_size": obj.get_editor_property("max_texture_size"),
                                    "lod_bias": obj.get_editor_property("lod_bias"),
                                    "source": str(obj.blueprint_get_texture_source_disk_and_memory_size()),
                                    "built": str(obj.blueprint_get_built_texture_size())})
    state = {"case": 0, "actor": None, "task": None, "busy": False, "done": False,
             "start": time.monotonic(), "frames": 0}
    def setup():
        field_name = ("Arch", "Globular", "Linear")[state["case"] // 2]
        if state["case"] % 2 == 0:
            if state["actor"]:
                actors.destroy_actor(state["actor"])
            path = BASE + "/Blueprints/BP_AsteroidField_" + field_name
            actor = actors.spawn_actor_from_class(u.EditorAssetLibrary.load_blueprint_class(path), u.Vector())
            assert actor, path
            state["actor"] = actor
            properties = {}
            for name in ("Number of Asteroids", "Number of Clusters", "Asteroid Scale",
                         "Asteroid Scale Variation Fraction", "Clusters Dispersion", "Arch Degrees", "Arch Radius"):
                try:
                    val = actor.get_editor_property(name)
                    if isinstance(val, (int, float, str, bool)):
                        properties[name] = val
                except Exception:
                    pass
            components = []
            for component in actor.get_components_by_class(u.StaticMeshComponent):
                rock = component.get_editor_property("static_mesh")
                components.append({"name": component.get_name(), "mesh": rock.get_path_name() if rock else None,
                                   "instances": component.get_instance_count() if isinstance(component, u.InstancedStaticMeshComponent) else 1,
                                   "collision": str(component.get_collision_enabled())})
            origin, extent = actor.get_actor_bounds(False)
            record["fields"].append({"path": path, "origin_cm": vector(origin), "extent_cm": vector(extent),
                                      "properties": properties, "components": components})
        origin, extent = state["actor"].get_actor_bounds(False)
        if state["case"] % 2 == 0:
            radius = max(extent.x, extent.y, extent.z, 1000)
            position = origin + u.Vector(-radius * 2.2, -radius * 1.4, radius * 1.1)
        else:
            position = origin + u.Vector(-extent.x - 30000, 0, 0)
        rotation = u.MathLibrary.find_look_at_rotation(position, origin)
        camera.set_actor_location(position, False, False)
        camera.set_actor_rotation(rotation, False)
        editor.set_level_viewport_camera_info(position, rotation)
        state.update(task=None, frames=0, case_start=time.monotonic(),
                     name=field_name + ("Overview" if state["case"] % 2 == 0 else "Approach"),
                     camera=vector(position))
    def finish():
        state["done"] = True
        record["vendor_unchanged"] = hashes() == protected
        record["status"] = "CAPTURED_NOT_ACCEPTED" if not record["errors"] and record["vendor_unchanged"] else "FAILED"
        (out / "report.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        (out.parent / "latest.json").write_text(json.dumps({"root": str(out), "status": record["status"]}), encoding="utf-8")
        u.unregister_slate_post_tick_callback(state["handle"])
        u.EditorPythonScripting.set_keep_python_script_alive(False)
    def tick(delta):
        if state["busy"] or state["done"]:
            return
        state["busy"] = True
        try:
            state["frames"] += 1
            path = out / (state["name"] + ".png")
            if state["task"] is None and state["frames"] >= 90 and time.monotonic() - state["case_start"] > 4:
                u.AutomationLibrary.finish_loading_before_screenshot()
                state["task"] = u.AutomationLibrary.take_high_res_screenshot(1600, 1000, str(path), camera, delay=.3)
                assert state["task"].is_valid_task()
            if state["task"] and state["task"].is_task_done() and path.exists():
                record["images"].append({"file": path.name, "camera_cm": state["camera"],
                                          "width": int.from_bytes(path.read_bytes()[16:20], "big"),
                                          "height": int.from_bytes(path.read_bytes()[20:24], "big"),
                                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
                state["case"] += 1
                if state["case"] == 6:
                    finish()
                else:
                    setup()
            elif time.monotonic() - state["start"] > 240:
                raise RuntimeError("Asteroid audition timed out")
        except Exception as exc:
            record["errors"].append(str(exc))
            u.log_error(traceback.format_exc())
            finish()
        finally:
            state["busy"] = False
    setup()
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    state["handle"] = u.register_slate_post_tick_callback(tick)


if __name__ == "__main__":
    main()
