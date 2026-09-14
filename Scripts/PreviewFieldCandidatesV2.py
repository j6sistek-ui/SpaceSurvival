"""Unsaved native field material/geometry inspection, never runtime adoption.
Explicit scalar samples use current gameplay Emission values. This preview does
not execute, replace or validate the authoritative pulse/force clock.
"""
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import time
import traceback
import uuid

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/"ContentSource/FieldCandidates/V2"
BASE = "/Game/SpaceSurvival"
spec=importlib.util.spec_from_file_location("ss_field_author",ROOT/"Scripts/AuthorFieldCandidatesV2.py")
author=importlib.util.module_from_spec(spec)
spec.loader.exec_module(author)


def snapshot():
    return {str(p.relative_to(ROOT)):author.sha(p) for folder in ("Source","Config","Content")
            for p in sorted((ROOT/folder).rglob("*")) if p.is_file()}


def main():
    report=author.source_report()
    persisted=json.loads((ROOT/"Saved/Validation/FieldCandidatesV2Persisted.json").read_text(encoding="utf-8"))
    assert persisted["status"]=="FIELD_CANDIDATES_PERSISTED_CONTRACT_VERIFIED_NOT_VISUAL_ACCEPTANCE"
    for package in persisted["candidate_packages"]:
        assert author.sha(ROOT/package["path"])==package["sha256"],"Candidate changed after fresh validation"
    protected=snapshot()
    run_dir=OUT/"Native"/uuid.uuid4().hex
    run_dir.mkdir(parents=True,exist_ok=False)
    u.EditorLoadingAndSavingUtils.new_blank_map(False)
    actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()

    def static(name,path,position,scale=1,cast_shadow=True):
        actor=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*position))
        actor.set_actor_label(name)
        actor.set_actor_enable_collision(False)
        component=actor.get_component_by_class(u.StaticMeshComponent)
        component.set_mobility(u.ComponentMobility.MOVABLE)
        component.set_static_mesh(u.load_asset(path))
        assert component.get_editor_property("static_mesh"),path
        component.set_collision_profile_name("NoCollision")
        component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        component.set_editor_property("cast_shadow",cast_shadow)
        actor.set_actor_location(u.Vector(*position),False,False)
        actor.set_actor_scale3d(u.Vector(scale,scale,scale))
        return actor,component

    _,sky=static("Unchanged space panorama","/Engine/BasicShapes/Sphere",(0,0,0),100000,False)
    sky.set_material(0,u.load_asset(BASE+"/Materials/M_Space"))
    static("Unchanged stars",BASE+"/Meshes/SM_Starfield",(0,0,0),1,False)
    ship,ship_component=static("Scale reference - actual starter mesh",BASE+"/Meshes/SM_AcornShipV2",(-1100,-1800,-250))
    for i,(position,radius) in enumerate([((1400,500,250),480),((200,-700,900),260),((-1400,600,-500),650)]):
        mesh=u.load_asset(BASE+"/Meshes/SM_AsteroidMedium")
        extent=mesh.get_bounds().box_extent
        _,component=static("Asteroid reference "+str(i),mesh.get_path_name(),position,radius/max(extent.x,extent.y,extent.z))
        component.prestream_textures(120,False)
    field,component=static("Field candidate only",BASE+"/Meshes/SM_ElectricalFieldCandidateV2",(0,0,0),34,False)
    for pitch,yaw,color,intensity in [(-35,-40,(.60,.77,1,1),3.5),(20,140,(1,.52,.24,1),1.2)]:
        light=actors.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,500),u.Rotator(pitch=pitch,yaw=yaw,roll=0))
        lamp=light.get_component_by_class(u.DirectionalLightComponent)
        lamp.set_mobility(u.ComponentMobility.MOVABLE)
        lamp.set_light_color(u.LinearColor(*color))
        lamp.set_intensity(intensity)
    post=actors.spawn_actor_from_class(u.PostProcessVolume,u.Vector(0,0,0))
    post.set_editor_property("unbound",True)
    settings=post.get_editor_property("settings")
    for name,value in {"override_auto_exposure_min_brightness":True,"override_auto_exposure_max_brightness":True,
                       "auto_exposure_min_brightness":1.,"auto_exposure_max_brightness":1.,
                       "override_bloom_intensity":True,"bloom_intensity":.35,
                       "override_motion_blur_amount":True,"motion_blur_amount":0.}.items():
        settings.set_editor_property(name,value)
    post.set_editor_property("settings",settings)
    camera=actors.spawn_actor_from_class(u.CameraActor,u.Vector(0,0,0))
    cam=camera.get_component_by_class(u.CameraComponent)
    cam.set_field_of_view(55)
    cam.set_editor_property("aspect_ratio",1.6)
    u.get_editor_subsystem(u.LevelEditorSubsystem).editor_set_game_view(True)
    quarter=(8000,-6500,5000)
    cases=[
        ("ElectricalWarning","Electrical",.35,quarter,(0,0,0)),
        ("ElectricalCharged","Electrical",2.05,quarter,(0,0,0)),
        ("ElectricalDischarge","Electrical",2.8,quarter,(0,0,0)),
        ("ElectricalEdge","Electrical",2.8,(0,-9000,200),(0,0,0)),
        ("GravityWarning","Gravity",.35,quarter,(0,0,0)),
        ("GravityActive","Gravity",1.1,quarter,(0,0,0)),
        ("GravityEdge","Gravity",1.1,(0,-9000,200),(0,0,0)),
        ("GravityInside","Gravity",1.1,(-500,-2200,100),(1800,1000,250)),
    ]
    record={"status":"RUNNING","errors":[],"images":[],"engine":u.SystemLibrary.get_engine_version(),
            "process_id":os.getpid(),"run_directory":str(run_dir.relative_to(ROOT)),
            "source_report_sha256":author.sha(OUT/"SourceReport.json"),
            "persisted_receipt_sha256":author.sha(ROOT/"Saved/Validation/FieldCandidatesV2Persisted.json"),
            "method":"Unsaved stock static-mesh actors; actual ship/rocks/sky; fixed scalar samples, no gameplay or actor clocks.",
            "field_radius_cm":3400,"ship_scale":1,"asteroid_radii_cm":[480,260,650],
            "exposure_min_max":1,"bloom":.35,"no_collision_on_preview_meshes":True,
            "field_and_background_shadows":False,"ship_and_rock_shadows":True,
            "limits":["Material samples use existing numerical Emission values, not live pulse/force integration.",
                      "No GI Init, play session, save calls, Data Asset edits or runtime adoption.",
                      "Captures are material/geometry inspection; no physical controls, natural fairness, frame-time or owner art acceptance.",
                      "Static ship mesh is a scale reference; pilot animation/contact is outside this preview."]}
    state={"index":0,"frames":0,"task":None,"handle":None,"start":time.monotonic(),"busy":False,"done":False,"mid":None}

    def setup():
        name,kind,emission,position,target=cases[state["index"]]
        mesh_name="SM_"+kind+"FieldCandidateV2"
        material_name="M_"+kind+"FieldCandidateV2"
        component.set_static_mesh(u.load_asset(BASE+"/Meshes/"+mesh_name))
        state["mid"]=component.create_dynamic_material_instance(0,u.load_asset(BASE+"/Materials/"+material_name))
        assert state["mid"]
        state["mid"].set_scalar_parameter_value("Emission",emission)
        location=u.Vector(*position)
        ship_position=u.Vector(-1100,-1800,-250)
        if name.endswith("Inside"):
            direction=u.Vector(*target)-location
            direction=direction/direction.length()
            ship_position=location+direction*900+u.Vector(0,0,-170)
        ship.set_actor_location(ship_position,False,False)
        rotation=u.MathLibrary.find_look_at_rotation(location,u.Vector(*target))
        camera.set_actor_location(location,False,False)
        camera.set_actor_rotation(rotation,False)
        u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(location,rotation)
        state.update(frames=0,task=None,case_start=time.monotonic())

    def finish():
        if state["done"]:return
        state["done"]=True
        if snapshot()!=protected:
            record["errors"].append("Source/Config/Content changed during preview")
        record["status"]="NATIVE_FIELD_CANDIDATE_SCALAR_SAMPLES_CAPTURED_NOT_ADOPTED" if not record["errors"] else "FAILED"
        record["protected_files_unchanged"]=len(protected) if not record["errors"] else None
        receipt=json.dumps(record,indent=2)+"\n"
        (run_dir/"UnrealPreview.json").write_text(receipt,encoding="utf-8")
        (OUT/"UnrealPreview.json").write_text(receipt,encoding="utf-8")
        u.unregister_slate_post_tick_callback(state["handle"])
        u.EditorPythonScripting.set_keep_python_script_alive(False)
        u.log("FIELD_CANDIDATE_V2_PREVIEW_FINISHED")

    def tick(delta):
        if state["busy"] or state["done"]:return
        state["busy"]=True
        try:
            state["frames"]+=1
            name,kind,emission,position,target=cases[state["index"]]
            path=run_dir/("Unreal"+name+".png")
            if state["task"] is None and state["frames"]>=120 and time.monotonic()-state["case_start"]>5:
                u.AutomationLibrary.finish_loading_before_screenshot()
                state["task"]=u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(path),camera,delay=.3)
                assert state["task"].is_valid_task()
            if state["task"] and state["task"].is_task_done() and path.exists():
                record["images"].append({"file":str(path.relative_to(OUT)),"sha256":author.sha(path),"kind":kind,"emission":emission,
                                         "camera_cm":list(position),"target_cm":list(target)})
                state["index"]+=1
                if state["index"]==len(cases):finish()
                else:setup()
            elif time.monotonic()-state["start"]>180:
                raise RuntimeError("Field preview exceeded180 seconds")
        except Exception as error:
            record["errors"].append(str(error))
            u.log_error(traceback.format_exc())
            finish()
        finally:
            state["busy"]=False
    setup()
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    state["handle"]=u.register_slate_post_tick_callback(tick)


if __name__=="__main__":
    main()
