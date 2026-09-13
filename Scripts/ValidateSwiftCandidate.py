"""Fresh saved Swift validation and optional unsaved native Hero/Chase/Cockpit.
Reports, FBX readback and preview PNGs stay under Saved/Validation/SwiftCandidate.
Preview requires -abslog=<project>/Saved/Validation/SwiftCandidate/SwiftPreview.log.
"""
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys
import time
import traceback
import uuid

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ss_swift_author",ROOT/"Scripts/AuthorSwiftCandidate.py")
author = importlib.util.module_from_spec(spec);spec.loader.exec_module(author)
OUT = author.OUT
LIB = u.EditorAssetLibrary


def built_attributes(mesh):
    path = OUT/"SwiftBuiltLOD0.fbx"
    options = u.FbxExportOption()
    for key,value in {"ascii":True,"level_of_detail":False,"collision":False,"export_source_mesh":False}.items():
        options.set_editor_property(key,value)
    task = u.AssetExportTask()
    for key,value in {"object":mesh,"filename":str(path),"automated":True,"prompt":False,"replace_identical":True,
                      "exporter":u.StaticMeshExporterFBX(),"options":options}.items():
        task.set_editor_property(key,value)
    assert u.Exporter.run_asset_export_task(task) and path.is_file()
    arrays = {}
    for name,count,values in re.findall(r"\b(Vertices|PolygonVertexIndex|Normals|NormalsIndex|Tangents|TangentsIndex|Binormals|BinormalsIndex|UV|UVIndex)\s*:\s*\*(\d+)\s*\{\s*a:\s*([^}]*)\}",path.read_text(encoding="utf-8-sig"),re.S):
        numbers=re.sub(r"\s","",values).strip(",").split(",")
        assert len(numbers)==int(count) and all(math.isfinite(float(n))for n in numbers)
        arrays.setdefault(name,[]).append(numbers)
    assert all(name in arrays for name in ("Vertices","PolygonVertexIndex","Normals","UV"))
    for values in arrays["Normals"]:
        assert len(values)%3==0
        assert all(abs(sum(float(v)**2 for v in values[i:i+3])-1)<.001 for i in range(0,len(values),3))
    for values in arrays["UV"]:
        assert len(values)%2==0 and all(-.00001<=float(v)<=1.00001 for v in values)
    return {"built_attributes_sha256":hashlib.sha256(json.dumps(arrays,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
            "export_fbx_sha256":author.sha(path),"finite_unit_normals":True,"finite_unit_square_uvs":True,"arrays":sorted(arrays)}


def validate():
    OUT.mkdir(parents=True,exist_ok=True)
    report=author.source_report()
    materials,rows=author.checked_materials(report)
    mesh=LIB.load_asset(author.PATH)
    assert isinstance(mesh,u.StaticMesh),"Missing separate Swift mesh"
    assert LIB.get_metadata_tag(mesh,"SSSwiftCandidateVersion")==author.VERSION
    assert author.source_matches(author.SOURCE/"SwiftCandidate.obj", LIB.get_metadata_tag(mesh,"SSSwiftSourceSHA256"))
    editor=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    assert editor.get_lod_count(mesh)==1 and mesh.get_num_sections(0)==7
    assert editor.get_num_uv_channels(mesh,0)==1 and editor.get_simple_collision_count(mesh)==0
    assert all(not editor.is_section_collision_enabled(mesh,0,i)for i in range(7))
    instance=mesh.get_editor_property("body_setup").get_editor_property("default_instance")
    assert instance.get_editor_property("collision_enabled")==u.CollisionEnabled.NO_COLLISION
    assert str(instance.get_editor_property("collision_profile_name"))=="NoCollision"
    data=mesh.get_editor_property("asset_import_data")
    assert data.get_editor_property("normal_import_method")==u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
    assert abs(data.get_editor_property("import_uniform_scale")-1)<1e-6
    translation=data.get_editor_property("import_translation")
    rotation=data.get_editor_property("import_rotation")
    assert all(abs(v)<1e-6 for v in (translation.x,translation.y,translation.z,rotation.pitch,rotation.yaw,rotation.roll))
    b=mesh.get_bounds()
    origin=[b.origin.x,b.origin.y,b.origin.z];extent=[b.box_extent.x,b.box_extent.y,b.box_extent.z]
    bounds=[[origin[i]-extent[i]for i in range(3)],[origin[i]+extent[i]for i in range(3)]]
    assert all(abs(bounds[e][i]-report["bounds_cm"][e][i])<.03 for e in range(2)for i in range(3))
    source_triangles=report["triangles"];native_triangles=mesh.get_num_triangles(0)
    assert source_triangles*.99<=native_triangles<=source_triangles,"Unexpected triangle loss beyond 1% import cleanup bound"
    slots=[]
    for slot in mesh.get_editor_property("static_materials"):
        name=str(slot.get_editor_property("imported_material_slot_name"))
        material=slot.get_editor_property("material_interface")
        assert name in materials and material==materials[name]
        slots.append({"slot":name,"material":material.get_path_name()})
    assert len(slots)==7 and {s["slot"]for s in slots}==author.MATERIAL_NAMES
    package=ROOT/"Content/SpaceSurvival/Meshes/SM_SwiftCandidateV1.uasset"
    record={"status":"SWIFT_PERSISTED_MESH_VALIDATED_NOT_VISUAL_ACCEPTANCE","errors":[],"engine":u.SystemLibrary.get_engine_version(),
            "mesh":mesh.get_path_name(),"source_report_sha256":author.sha(author.SOURCE/"Report.json"),
            "source_obj_sha256":author.sha(author.SOURCE/"SwiftCandidate.obj"),"bounds_cm":bounds,"import_translation_cm":[0,0,0],
            "import_rotation_degrees":[0,0,0],"import_scale":1,"pilot_transform":report["pilot_transform"],
            "source_triangles":source_triangles,"native_triangles":native_triangles,"triangle_cleanup_delta":source_triangles-native_triangles,
            "triangle_cleanup_limit":"At most1% accepted for initial importer cleanup; exact removed source-face mapping has not been proven.",
            "vertices":editor.get_number_verts(mesh,0),"lods":1,"material_sections":7,"uv_channels":1,"normal_import_method":"IMPORT_NORMALS",
            "collision_shapes":0,"all_section_collision_disabled":True,"collision_profile":"NoCollision","slots":slots,"materials":rows,
            "package":{"path":str(package.relative_to(ROOT)),"bytes":package.stat().st_size,"sha256":author.sha(package)},
            "built_geometry":built_attributes(mesh),
            "limits":["One separate mesh; original Swift/stat/pilot transform and seven shared material packages remain unchanged.",
                      "Known retained cockpit bevel degeneracies may be removed by importer; exact triangle mapping is unproven.",
                      "No runtime selection, authored-main hook, full animated clearance, performance or owner acceptance."]}
    return mesh,record


def read_residency(log_path,marker,texture_name):
    if not log_path.is_file():return None
    text=log_path.read_text(encoding="utf-8",errors="replace")
    start=text.rfind(marker+"_BEGIN")
    if start<0:return None
    end=text.find(marker+"_END",start)
    if end<0:return None
    section=text[start:end]
    rows=[]
    for line in section.splitlines():
        if texture_name not in line:continue
        match=re.search(r"(\d+,\d+,\d+,[^,]*,\d+,\d+,\d+,[^\r\n]+)",line)
        if not match:continue
        row=next(csv.reader([match.group(1)]))
        if len(row)==16 and row[9]==texture_name:
            rows.append(row)
    assert len(rows)==1,"Expected one exact hero CSV texture row"
    row=rows[0]
    assert int(row[0])==int(row[4]) and int(row[1])==int(row[5]),"Hero texture not fully resident"
    assert int(row[4])>0 and int(row[6])>0 and int(row[14])>0
    return {"texture":row[9],"maximum_dimensions":[int(row[0]),int(row[1])],"current_dimensions":[int(row[4]),int(row[5])],
            "current_kb":int(row[6]),"format":row[7],"mips":int(row[14]),"usage_count":int(row[13]),
            "raw_csv":",".join(row),"section_sha256":hashlib.sha256(section.encode()).hexdigest()}


def preview(mesh,record,protected):
    preview_dir=OUT/("Preview-"+uuid.uuid4().hex)
    preview_dir.mkdir(parents=True,exist_ok=False)
    log_path=OUT/"SwiftPreview.log"
    u.EditorLoadingAndSavingUtils.new_blank_map(False)
    actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    for command in ("r.MotionBlurQuality 0","r.ScreenPercentage 100","r.AntiAliasingMethod 2"):
        u.SystemLibrary.execute_console_command(world,command)
    ship=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0),u.Rotator(0,0,0))
    visual=ship.get_component_by_class(u.StaticMeshComponent);visual.set_mobility(u.ComponentMobility.MOVABLE)
    visual.set_static_mesh(mesh);visual.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    pilot=actors.spawn_actor_from_class(u.SkeletalMeshActor,u.Vector(-15,0,72),u.Rotator(pitch=0,yaw=-90,roll=0))
    pilot.set_actor_scale3d(u.Vector(1.5,1.5,1.5))
    hero=pilot.get_component_by_class(u.SkeletalMeshComponent)
    hero.set_skeletal_mesh_asset(LIB.load_asset("/Game/SpaceSurvival/Character/SK_AcornautTailV2"))
    hero.set_update_animation_in_editor(True)
    hero.set_editor_property("visibility_based_anim_tick_option",u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
    hero.set_animation_mode(u.AnimationMode.ANIMATION_BLUEPRINT);hero.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    hero.override_animation_data(LIB.load_asset("/Game/SpaceSurvival/Character/A_Pilot"),True,False,0,1)
    used_textures=u.MaterialEditingLibrary.get_material_used_textures(hero.get_material(0))
    textures={t.get_path_name():t for t in used_textures if isinstance(t,u.Texture2D) and
              t.get_path_name().startswith("/Game/SpaceSurvival/Character/")}
    assert len(textures)==1,"Expected one real character texture after filtering Interchange defaults"
    texture=next(iter(textures.values()));texture.set_force_mip_levels_to_be_resident(120.0)
    record["hero_material_used_textures"]=sorted({t.get_path_name() for t in used_textures})
    record["temporary_hero_residency"]={"texture":texture.get_path_name(),"seconds":120,"minimum_wait_per_view_seconds":10,
                                      "saved_streaming_flag_changes":False,"require_full_and_equal_current_dimensions":True}
    for pitch,yaw,color,intensity in [(-35,-30,(.9,.95,1,1),4),(-25,145,(1,.89,.75,1),2),(-65,70,(.5,.7,1,1),1)]:
        light=actors.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,500),u.Rotator(pitch=pitch,yaw=yaw,roll=0))
        lamp=light.get_component_by_class(u.DirectionalLightComponent);lamp.set_mobility(u.ComponentMobility.MOVABLE)
        lamp.set_light_color(u.LinearColor(*color));lamp.set_intensity(intensity)
    post=actors.spawn_actor_from_class(u.PostProcessVolume,u.Vector(0,0,0));post.set_editor_property("unbound",True)
    settings=post.get_editor_property("settings")
    for key,value in {"override_auto_exposure_min_brightness":True,"override_auto_exposure_max_brightness":True,
                      "auto_exposure_min_brightness":1.0,"auto_exposure_max_brightness":1.0,
                      "override_bloom_intensity":True,"bloom_intensity":.1}.items():
        settings.set_editor_property(key,value)
    post.set_editor_property("settings",settings)
    camera=actors.spawn_actor_from_class(u.CameraActor,u.Vector(0,0,0))
    camera.get_component_by_class(u.CameraComponent).set_field_of_view(35)
    camera.get_component_by_class(u.CameraComponent).set_editor_property("aspect_ratio",4/3)
    u.get_editor_subsystem(u.LevelEditorSubsystem).editor_set_game_view(True)
    cases=[("Hero",(580,-740,450),(0,0,30)),("Chase",(-750,-490,340),(-15,0,32)),
           ("Cockpit",(210,-220,225),(-15,0,75))]
    state={"index":0,"frames":0,"task":None,"busy":False,"done":False,"handle":None,"start":time.monotonic(),
           "residency_requested":False,"residency":None}
    record["images"]=[]
    record["preview_method"]="Unsaved StaticMeshActor at unit scale/world zero, preserved TailV2/Pilot0s pose and native pilot mount, three ordinary shadow-casting studio lights. No GameMode/run/physical input or save calls."
    record["preview_directory"]=str(preview_dir.relative_to(ROOT))
    def setup():
        name,position,target=cases[state["index"]]
        loc=u.Vector(*position);rotation=u.MathLibrary.find_look_at_rotation(loc,u.Vector(*target))
        camera.set_actor_location(loc,False,False);camera.set_actor_rotation(rotation,False)
        u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(loc,rotation)
        state.update(frames=0,task=None,case_start=time.monotonic(),residency_requested=False,residency=None)
    def finish():
        if state["done"]:return
        state["done"]=True
        try:
            author.check_unchanged(protected)
            record["existing_protected_files_unchanged"]=len(protected)
            if not record["errors"]:
                assert len(record["images"])==3
                signatures={(tuple(r["residency"]["current_dimensions"]),r["residency"]["format"],r["residency"]["mips"])for r in record["images"]}
                assert len(signatures)==1,"Hero residency differs between views"
                record["status"]="SEPARATE_SWIFT_NATIVE_STUDIO_PREVIEW_CAPTURED_NOT_ADOPTED"
        except Exception as error:record["errors"].append(str(error))
        if record["errors"]:record["status"]="FAILED";u.log_error("SWIFT_CANDIDATE_PREVIEW_FAILED: "+"; ".join(record["errors"]))
        author.write("SwiftPreview.json",record)
        u.unregister_slate_post_tick_callback(state["handle"])
        u.EditorPythonScripting.set_keep_python_script_alive(False)
        u.log("SWIFT_CANDIDATE_PREVIEW_FINISHED")
    def tick(delta):
        if state["busy"] or state["done"]:return
        state["busy"]=True
        try:
            state["frames"]+=1
            name,position,target=cases[state["index"]]
            marker="SWIFT_RESIDENCY_"+preview_dir.name+"_"+name
            path=preview_dir/(name+".png")
            if not state["residency_requested"] and state["frames"]>=90 and time.monotonic()-state["case_start"]>=10:
                u.AutomationLibrary.finish_loading_before_screenshot()
                u.log(marker+"_BEGIN")
                u.SystemLibrary.execute_console_command(world,"ListTextures -CSV")
                u.log(marker+"_END")
                state["residency_requested"]=True
            if state["residency_requested"] and state["residency"] is None:
                state["residency"]=read_residency(log_path,marker,texture.get_path_name())
            if state["residency"] and state["task"] is None:
                state["task"]=u.AutomationLibrary.take_high_res_screenshot(1600,1200,str(path),camera,delay=.3)
                assert state["task"].is_valid_task()
            if state["task"] and state["task"].is_task_done() and path.is_file():
                record["images"].append({"file":str(path.relative_to(ROOT)),"sha256":author.sha(path),"view":name,
                                         "camera_cm":list(position),"target_cm":list(target),"pilot_seconds":0,
                                         "residency":state["residency"]})
                state["index"]+=1
                if state["index"]==len(cases):finish()
                else:setup()
            elif time.monotonic()-state["start"]>150:raise RuntimeError("Swift native preview timeout or missing CSV residency log")
        except Exception as error:record["errors"].append(str(error));u.log_error(traceback.format_exc());finish()
        finally:state["busy"]=False
    setup()
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    state["handle"]=u.register_slate_post_tick_callback(tick)


def main(render=False):
    protected=author.snapshot()
    result={"status":"FAILED","errors":[]}
    try:
        mesh,result=validate()
        author.check_unchanged(protected)
        result["existing_protected_files_unchanged"]=len(protected)
    except Exception as error:result["errors"].append(str(error));u.log_error(traceback.format_exc())
    author.write("SwiftPersisted.json",result)
    if result["errors"]:raise RuntimeError("Swift persisted validation failed; see Saved/Validation/SwiftCandidate/SwiftPersisted.json")
    u.log("SWIFT_CANDIDATE_PERSISTED_OK")
    if render:
        try:preview(mesh,result,protected)
        except Exception as error:
            result["status"]="FAILED";result["errors"].append(str(error))
            author.write("SwiftPreview.json",result)
            u.EditorPythonScripting.set_keep_python_script_alive(False)
            u.log_error("SWIFT_CANDIDATE_PREVIEW_SETUP_FAILED: "+traceback.format_exc())
            raise
    return result


if __name__=="__main__":main("--preview" in sys.argv)
