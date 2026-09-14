"""Transient stock-actor fit study of actual imported ship and pilot assets.

Run UnrealEditor-Cmd SpaceSurvival.uproject -unattended -RenderOffscreen
-ExecutePythonScript=<this file>. No content assets or maps are saved. PNGs and
JSON document visual fit only; they do not establish integrated gameplay QA.
"""
import hashlib
import json
from pathlib import Path
import time
import sys
if "--measure-source" not in sys.argv:
    import unreal as u

ROOT = Path(__file__).resolve().parents[1]
BASE = "/Game/SpaceSurvival"
START = time.monotonic()
STATE = {"frames": 0, "index": 0, "task": None, "handle": None, "samples": []}
OUTPUT = ROOT / "ContentSource"
DERIVATIVE = "--derivative" in sys.argv
CASES = [
    {"name": "CockpitScale12Front", "scale": 1.2, "position": (-27, 0, 69), "camera": (520, -610, 380), "target": (-20, 0, 40), "fov": 46},
    {"name": "CockpitScale15Front", "scale": 1.5, "position": (-27, 0, 72), "camera": (520, -610, 380), "target": (-20, 0, 40), "fov": 46},
    {"name": "CockpitScale18Front", "scale": 1.8, "position": (-27, 0, 76), "camera": (520, -610, 380), "target": (-20, 0, 40), "fov": 46},
    {"name": "CockpitScale15Rear", "scale": 1.5, "position": (-27, 0, 72), "camera": (-520, 470, 320), "target": (-30, 0, 70), "fov": 46},
    {"name": "CockpitScale15Side", "scale": 1.5, "position": (-27, 0, 72), "camera": (0, -760, 130), "target": (-25, 0, 65), "fov": 46},
    {"name": "CockpitScale15Chase", "scale": 1.5, "position": (-27, 0, 72), "camera": (-650, 0, 175), "target": (350, 0, 175), "fov": 80},
    {"name": "CockpitScale15RaisedRear", "scale": 1.5, "position": (-15, 0, 87), "camera": (-520, 470, 320), "target": (-30, 0, 70), "fov": 46},
    {"name": "WalkerFit", "scale": 1.0, "position": (0, 0, 65), "camera": (210, -280, 130), "target": (0, 0, 50), "fov": 45, "walk": True, "sample": 0.0},
    {"name": "WalkerFit06", "scale": 1.0, "position": (0, 0, 65), "camera": (210, -280, 130), "target": (0, 0, 50), "fov": 45, "walk": True, "sample": .6},
    {"name": "WalkerFit12", "scale": 1.0, "position": (0, 0, 65), "camera": (210, -280, 130), "target": (0, 0, 50), "fov": 45, "walk": True, "sample": 1.2},
    {"name": "WalkerFit18", "scale": 1.0, "position": (0, 0, 65), "camera": (210, -280, 130), "target": (0, 0, 50), "fov": 45, "walk": True, "sample": 1.8},
]


if DERIVATIVE:
    CASES = [case for case in CASES if "Scale15" in case["name"] and "Raised" not in case["name"]]
    for case in CASES:
        case["position"] = (-15, 0, 72)
        if "Chase" in case["name"]:
            case["target"] = (335, 0, 0)
    for seconds in (0.0, 2.0, 3.9):
        CASES.append({"name": "CockpitCycle" + str(seconds), "scale": 1.5, "position": (-15, 0, 72), "camera": (-520, 470, 320), "target": (-30, 0, 70), "fov": 46, "sample": seconds})

def vector(v):
    return [round(v.x, 5), round(v.y, 5), round(v.z, 5)]


def main():
    u.EditorLoadingAndSavingUtils.new_blank_map(False)
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    def static(path, position, scale=(1, 1, 1), material=None):
        actor = actors.spawn_actor_from_class(u.StaticMeshActor, u.Vector(*position))
        component = actor.get_component_by_class(u.StaticMeshComponent)
        component.set_mobility(u.ComponentMobility.MOVABLE)
        component.set_static_mesh(u.load_asset(path))
        actor.set_actor_scale3d(u.Vector(*scale))
        if material:
            component.set_material(0, u.load_asset(material))
        return actor
    ship = static(BASE + "/Meshes/SM_AcornShip", (0, 0, 0))
    floor = static("/Engine/BasicShapes/Cube", (0, 0, -90), (30, 30, .1), BASE + "/Materials/M_Hull")
    hero = actors.spawn_actor_from_class(u.SkeletalMeshActor, u.Vector(0, 0, 0), u.Rotator(pitch=0, yaw=-90, roll=0))
    component = hero.get_component_by_class(u.SkeletalMeshComponent)
    component.set_skeletal_mesh_asset(u.load_asset(BASE + ("/Character/SK_AcornautPilot" if DERIVATIVE else "/Character/SK_Acornaut")))
    component.set_update_animation_in_editor(True)
    pilot = u.load_asset(BASE + "/Character/A_Pilot")
    walk = u.load_asset(BASE + "/Character/A_Walk")
    assert pilot and walk, "Required animations must exist before preview"
    for rotation, color, intensity in [((-40, -30, 0), (.72, .85, 1, 1), 7), ((-28, 150, 0), (1, .7, .4, 1), 9), ((-65, 70, 0), (.5, .7, 1, 1), 3)]:
        light = actors.spawn_actor_from_class(u.DirectionalLight, u.Vector(0, 0, 500), u.Rotator(pitch=rotation[0], yaw=rotation[1], roll=rotation[2]))
        lamp = light.get_component_by_class(u.DirectionalLightComponent)
        lamp.set_mobility(u.ComponentMobility.MOVABLE)
        lamp.set_light_color(u.LinearColor(*color))
        lamp.set_intensity(intensity)
    post = actors.spawn_actor_from_class(u.PostProcessVolume, u.Vector(0, 0, 0))
    post.set_editor_property("unbound", True)
    settings = post.get_editor_property("settings")
    for key, value in {"override_auto_exposure_min_brightness": True, "override_auto_exposure_max_brightness": True, "auto_exposure_min_brightness": 1.0, "auto_exposure_max_brightness": 1.0, "override_bloom_intensity": True, "bloom_intensity": .2}.items():
        settings.set_editor_property(key, value)
    post.set_editor_property("settings", settings)
    camera = actors.spawn_actor_from_class(u.CameraActor, u.Vector(0, 0, 0))
    u.get_editor_subsystem(u.LevelEditorSubsystem).editor_set_game_view(True)
    u.EditorPythonScripting.set_keep_python_script_alive(True)

    def pose(case):
        nonlocal hero, component
        actors.destroy_actor(hero)
        hero = actors.spawn_actor_from_class(u.SkeletalMeshActor, u.Vector(0, 0, 0), u.Rotator(pitch=0, yaw=-90, roll=0))
        component = hero.get_component_by_class(u.SkeletalMeshComponent)
        component.set_skeletal_mesh_asset(u.load_asset(BASE + ("/Character/SK_AcornautPilot" if DERIVATIVE else "/Character/SK_Acornaut")))
        component.set_update_animation_in_editor(True)
        component.set_animation_mode(u.AnimationMode.ANIMATION_BLUEPRINT)
        is_walk = case.get("walk", False)
        hero.set_actor_location(u.Vector(*case["position"]), False, False)
        hero.set_actor_scale3d(u.Vector(case["scale"], case["scale"], case["scale"]))
        component.override_animation_data(walk if is_walk else pilot, True, False, case.get("sample", 1.0), 1.0)
        ship.set_actor_hidden_in_game(is_walk)
        ship.set_is_temporarily_hidden_in_editor(is_walk)
        floor.set_actor_location(u.Vector(0, 0, -5 if is_walk else -90), False, False)
        location = u.Vector(*case["camera"])
        rotation = u.MathLibrary.find_look_at_rotation(location, u.Vector(*case["target"]))
        camera.set_actor_location(location, False, False)
        camera.set_actor_rotation(rotation, False)
        camera.get_component_by_class(u.CameraComponent).set_field_of_view(case["fov"])
        u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(location, rotation)
        STATE["frames"] = 0
        STATE["task"] = None

    def finish(status):
        bones = [str(component.get_bone_name(i)) for i in range(component.get_num_bones())]
        record = {"status": status, "engine": u.SystemLibrary.get_engine_version(), "elapsed_seconds": round(time.monotonic() - START, 3), "source_glb_sha256": hashlib.sha256((ROOT / "model-rigged.glb").read_bytes()).hexdigest(), "samples": STATE["samples"], "bone_names": bones, "limits": "Unsaved stock actors with explicitly sampled imported animations, no game mode or gameplay control. Source GLB and all content assets unchanged. Skeletal actor bounds may reflect import bounds rather than deformed sole geometry. Camera matches current chase transform only in the Chase view."}
        (OUTPUT / ("PilotMeshCockpitPreview.json" if DERIVATIVE else "CockpitPreview.json")).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        u.unregister_slate_post_tick_callback(STATE["handle"])
        u.EditorPythonScripting.set_keep_python_script_alive(False)
        u.SystemLibrary.quit_editor()

    def tick(delta):
        try:
            STATE["frames"] += 1
            case = CASES[STATE["index"]]
            path = OUTPUT / (("UnrealPilotMesh" if DERIVATIVE else "Unreal") + case["name"] + ".png")
            if STATE["frames"] == 25:
                names = [str(component.get_bone_name(i)) for i in range(component.get_num_bones())]
                sockets = {name: vector(component.get_socket_location(name)) for name in names if any(s in name.lower() for s in ("foot", "ankle", "pelvis", "head", "tail", "wrist"))}
                STATE["samples"].append({**case, "png": path.name, "animation_seconds": component.get_position(), "animation_asset": component.get_editor_property("animation_data").get_editor_property("anim_to_play").get_path_name(), "sockets_world_cm": sockets, "actor_bounds": [vector(v) for v in hero.get_actor_bounds(False)]})
                u.AutomationLibrary.finish_loading_before_screenshot()
                STATE["task"] = u.AutomationLibrary.take_high_res_screenshot(1600, 1000, str(path), camera, delay=.3)
                assert STATE["task"].is_valid_task(), "Screenshot task not scheduled"
            if STATE["task"] and STATE["task"].is_task_done() and path.exists():
                STATE["index"] += 1
                if STATE["index"] == len(CASES):
                    finish("FIT_STUDY_CAPTURED_NOT_GAMEPLAY")
                else:
                    pose(CASES[STATE["index"]])
            elif time.monotonic() - START > 180:
                finish("FAILED_SCREENSHOT_TIMEOUT")
        except Exception as error:
            u.log_error(str(error))
            finish("FAILED: " + str(error))
    pose(CASES[0])
    STATE["handle"] = u.register_slate_post_tick_callback(tick)


def measure_source():
    """Existing Blender, read-only evaluation; writes one numeric fit receipt."""
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)
    source = ROOT / "model-rigged.glb"
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.import_scene.gltf(filepath=str(source))
    rig = next(obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE")
    mesh = next(obj for obj in bpy.context.scene.objects if obj.type == "MESH")
    scene = bpy.context.scene
    first, last = rig.animation_data.action.frame_range
    samples = []
    for index in range(17):
        frame = first + (last - first) * index / 16
        scene.frame_set(int(frame), subframe=frame - int(frame))
        evaluated = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
        vertices = [evaluated.matrix_world @ vertex.co for vertex in evaluated.data.vertices]
        samples.append({"seconds": round(frame / scene.render.fps, 6),
                        "min_vertex_z_cm": round(min(vertex.z for vertex in vertices) * 100, 5),
                        "max_vertex_z_cm": round(max(vertex.z for vertex in vertices) * 100, 5),
                        "foot_socket_z_cm": {name: round((rig.matrix_world @ rig.pose.bones[name].head).z * 100, 5)
                                             for name in ("L_Foot", "R_Foot")}})
    tail_indices = [vertex.index for vertex in mesh.data.vertices if vertex.co.y > .08 and vertex.co.z > .10]
    tail_weights = {}
    for index in tail_indices:
        for group in mesh.data.vertices[index].groups:
            name = mesh.vertex_groups[group.group].name
            tail_weights[name] = tail_weights.get(name, 0.0) + group.weight
    tail_audit = {"selection": "Unposed mesh coordinates: Blender Y > 0.08m and Z > 0.10m; upper rear curl region, not a production repair mask.",
                  "vertices": len(tail_indices),
                  "weight_fractions": {name: round(weight / len(tail_indices), 6) for name, weight in sorted(tail_weights.items(), key=lambda item: -item[1])},
                  "finding": "Upper rear curl has dominant right middle finger skin influences; these drive tail deformation when hands are posed.",
                  "proposed_derivative": "Pilot-only duplicate skeletal mesh, existing 52-bone skeleton/A_Pilot. Reweight a visually verified rear-tail mask to Pelvis, with rigid bind-space compensation to preserve original upright curl in seated pose. Geometry shape/UVs/materials remain source-derived. Simple reweight without compensation rotates curl rearward. No derivative mesh has been written or imported; repair mask and cockpit clearance remain unverified."}
    assert before == hashlib.sha256(source.read_bytes()).hexdigest(), "Source asset changed"
    record = {"status": "SOURCE_EVALUATED_NOT_GAMEPLAY", "blender": bpy.app.version_string,
              "source_glb_sha256": before, "vertex_count": len(mesh.data.vertices), "samples": samples, "tail_skinning_audit": tail_audit,
              "walker_fit": {"mesh_scale": 1.0, "mesh_origin_above_floor_cm": 65,
                             "capsule_half_height_cm": 88, "proposed_relative_z_cm": -23,
                             "method": "88 + relative_z + source_min_z = sole above floor. Source socket positions cross-checked against fresh Unreal A_Walk at 0/.6/1.2/1.8 seconds.",
                             "limits": "17 source samples bound sampled skin deformation only; no IK, collision, locomotion control or full-cycle runtime foot contact validation."},
              "pilot_fit": {"best_seat_contact_candidate_cm": [-27, 0, 72], "scale": 1.5, "yaw_degrees": -90,
                            "status": "BODY_FIT_ONLY_TAIL_OCCLUSION_UNRESOLVED",
                            "limitations": "The seated body/head fit the ship while its hull remains dominant. Rear/side PNGs reveal tail/hull/backrest intersections. Raising to [-15,0,87] reveals more tail but loses thigh/seat contact. No tail-named bone is present in the 52-bone imported skeleton. Offset alone did not meet full silhouette requirements; upper rear curl source finger weights are quantified in tail_skinning_audit."}}
    (OUTPUT / "CockpitSourceMeasurements.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))

if __name__ == "__main__":
    if "--measure-source" in sys.argv:
        measure_source()
    else:
        main()
