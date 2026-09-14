"""Render imported assets in an unsaved editor scene; not a gameplay screenshot.

Run with full UnrealEditor-Cmd -RenderOffscreen -ExecutePythonScript=<this file>.
The editor scene is discarded; imported assets and gameplay maps are not edited.
"""
import json
from pathlib import Path
import time
import sys
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
BASE = "/Game/SpaceSurvival"
PILOT = "--pilot" in sys.argv
CLOSE = "--hero" in sys.argv or PILOT
OUTPUT = ROOT / ("ContentSource/UnrealPilotPreview.png" if PILOT else "ContentSource/UnrealHeroPreview.png" if CLOSE else "ContentSource/UnrealAssetPreview.png")
START = time.monotonic()
STATE = {"frames": 0, "task": None, "handle": None}


def main():
    world = u.EditorLoadingAndSavingUtils.new_blank_map(False)
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)

    def static(name, position, scale=(1,1,1), material=None):
        actor = actors.spawn_actor_from_class(u.StaticMeshActor, u.Vector(*position))
        component = actor.get_component_by_class(u.StaticMeshComponent)
        component.set_mobility(u.ComponentMobility.MOVABLE)
        component.set_static_mesh(u.load_asset(name))
        actor.set_actor_scale3d(u.Vector(*scale))
        if material:
            component.set_material(0,u.load_asset(material))
        return actor

    static(BASE+"/Meshes/SM_AcornShip", (0,-225,140))
    static(BASE+"/Meshes/SM_AgileShip", (0,240,140))
    static("/Engine/BasicShapes/Cube",(0,0,-12),(18,18,.2),BASE+"/Materials/M_Hull")
    hero = actors.spawn_actor_from_class(u.SkeletalMeshActor, u.Vector(290,0,60),u.Rotator(pitch=0,yaw=-90,roll=0))
    component = hero.get_component_by_class(u.SkeletalMeshComponent)
    component.set_skeletal_mesh_asset(u.load_asset(BASE+"/Character/SK_Acornaut"))
    component.set_update_animation_in_editor(True)
    component.set_animation_mode(u.AnimationMode.ANIMATION_BLUEPRINT)
    component.override_animation_data(u.load_asset(BASE+("/Character/A_Pilot" if PILOT else "/Character/A_Walk")),True,False,1.0 if PILOT else .6,1.0)
    if PILOT:
        static("/Engine/BasicShapes/Cube",(290,0,49),(.45,.45,.12),BASE+"/Materials/M_Gold")
    for rotation, color, intensity in ((u.Rotator(pitch=-45,yaw=-35,roll=0),u.LinearColor(.72,.85,1,1),7.0),
                                        (u.Rotator(pitch=-20,yaw=145,roll=0),u.LinearColor(1,.65,.34,1),12.0 if CLOSE else 3.0)):
        light = actors.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,500),rotation)
        lamp = light.get_component_by_class(u.DirectionalLightComponent)
        lamp.set_mobility(u.ComponentMobility.MOVABLE)
        lamp.set_light_color(color)
        lamp.set_intensity(intensity)
    post = actors.spawn_actor_from_class(u.PostProcessVolume,u.Vector(0,0,0))
    post.set_editor_property("unbound",True)
    settings = post.get_editor_property("settings")
    for key,value in {"override_auto_exposure_min_brightness":True,"override_auto_exposure_max_brightness":True,
                      "auto_exposure_min_brightness":1.0,"auto_exposure_max_brightness":1.0,
                      "override_bloom_intensity":True,"bloom_intensity":.25}.items():
        settings.set_editor_property(key,value)
    post.set_editor_property("settings",settings)
    location = u.Vector(450,-250,160) if CLOSE else u.Vector(960,-1020,800)
    rotation = u.MathLibrary.find_look_at_rotation(location,u.Vector(290,0,65) if CLOSE else u.Vector(0,0,110))
    camera = actors.spawn_actor_from_class(u.CameraActor,location,rotation)
    camera.get_component_by_class(u.CameraComponent).set_field_of_view(47)
    u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(location,rotation)
    u.get_editor_subsystem(u.LevelEditorSubsystem).editor_set_game_view(True)
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    animation_start = component.get_position()

    def finish(status):
        record={"status":status,"engine":u.SystemLibrary.get_engine_version(),"elapsed_seconds":time.monotonic()-START,
                "animation_start_seconds":animation_start,"animation_end_seconds":component.get_position(),
                "hero_actor_location_cm":[290,0,60],"hero_actor_rotation_degrees":[0,-90,0],
                "animation_sampling":"Explicit OverrideAnimationData pose sample; not time-based playback",
                "actual_actor_rotation":str(hero.get_actor_rotation()),"animation_instance":str(component.get_anim_instance()),
                "foot_socket_world_cm":{name:[component.get_socket_location(name).x,component.get_socket_location(name).y,component.get_socket_location(name).z] for name in ["L_Foot","R_Foot","Pelvis","Head"]},
                "limits":"Unsaved stock-actor asset preview, not SpaceSurvival gameplay. No game mode, controls, collision, packaged build or performance validation."}
        (ROOT/("Saved/Validation/PilotPreview.json" if PILOT else "Saved/Validation/HeroPreview.json" if CLOSE else "Saved/Validation/AssetPreview.json")).write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
        u.unregister_slate_post_tick_callback(STATE["handle"])
        u.EditorPythonScripting.set_keep_python_script_alive(False)
        u.SystemLibrary.quit_editor()

    def tick(delta):
        try:
            STATE["frames"]+=1
            if STATE["frames"]==30:
                u.AutomationLibrary.finish_loading_before_screenshot()
                STATE["task"]=u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(OUTPUT),camera,delay=2.0)
                assert STATE["task"].is_valid_task(),"Screenshot task was not scheduled"
            if STATE["task"] and STATE["task"].is_task_done() and OUTPUT.exists():
                finish("ASSET_PREVIEW_CAPTURED_NOT_GAMEPLAY")
            elif time.monotonic()-START>180:
                finish("FAILED_SCREENSHOT_TIMEOUT")
        except Exception as error:
            u.log_error(str(error))
            finish("FAILED: "+str(error))
    STATE["handle"]=u.register_slate_post_tick_callback(tick)


if __name__=="__main__":
    main()
