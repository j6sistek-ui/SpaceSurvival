"""Fresh-process checks and optional unsaved native enemy-candidate previews."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys
import time
import traceback

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ss_enemy_author", ROOT / "Scripts/AuthorEnemyCandidates.py")
author = importlib.util.module_from_spec(spec)
spec.loader.exec_module(author)
OUT = author.SOURCE
LIB = u.EditorAssetLibrary
EDIT = u.MaterialEditingLibrary


def built_geometry(mesh, kind):
    # Read built LOD0 attributes through the installed exporter. No asset save.
    path = OUT / (kind + "-Built.fbx")
    options = u.FbxExportOption()
    for key, value in {"ascii": True, "level_of_detail": False, "collision": False,
                       "export_source_mesh": False, "vertex_color": True}.items():
        options.set_editor_property(key, value)
    task = u.AssetExportTask()
    for key, value in {"object": mesh, "filename": str(path), "automated": True, "prompt": False,
                       "replace_identical": True, "exporter": u.StaticMeshExporterFBX(), "options": options}.items():
        task.set_editor_property(key, value)
    assert u.Exporter.run_asset_export_task(task) and path.is_file()
    text = path.read_text(encoding="utf-8-sig")
    arrays = {}
    for name, count, values in re.findall(r"\b(Vertices|PolygonVertexIndex|Normals|NormalsIndex|Tangents|TangentsIndex|Binormals|BinormalsIndex|UV|UVIndex)\s*:\s*\*(\d+)\s*\{\s*a:\s*([^}]*)\}", text, re.S):
        numbers = values.replace("\n", "").replace("\r", "").replace("\t", "").replace(" ", "").strip(",").split(",")
        assert len(numbers) == int(count)
        assert all(math.isfinite(float(n)) for n in numbers)
        arrays.setdefault(name, []).append(numbers)
    assert all(name in arrays for name in ("Vertices", "PolygonVertexIndex", "Normals", "UV"))
    for values in arrays["Normals"]:
        assert len(values) % 3 == 0
        lengths = [sum(float(v) ** 2 for v in values[i:i+3]) for i in range(0, len(values), 3)]
        assert all(abs(value - 1) < .001 for value in lengths), "Built normals are not finite unit vectors"
    for values in arrays["UV"]:
        assert len(values) % 2 == 0 and all(-.00001 <= float(v) <= 1.00001 for v in values), "Built UV out of range"
    return {"built_lod0_attributes_sha256": hashlib.sha256(json.dumps(arrays, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "fbx_sha256": author.sha(path), "arrays_present": sorted(arrays),
            "built_normals_finite_unit": True, "built_uvs_finite_in_unit_square": True}


def validate():
    report = author.checked_source()
    palette_key = author.palette_key(report)
    editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    result = {"status": "PERSISTED_SEPARATE_ENEMY_ASSETS_VERIFIED_NOT_ADOPTED", "errors": [],
              "engine": u.SystemLibrary.get_engine_version(), "meshes": [], "materials": [],
              "source_report_sha256": author.sha(OUT / "SourceReport.json")}
    for item in report["materials"]:
        material = LIB.load_asset(author.material_path(item["name"]))
        assert isinstance(material, u.Material)
        assert LIB.get_metadata_tag(material, "SSEnemyCandidateVersion") == author.VERSION
        assert LIB.get_metadata_tag(material, "SSEnemyCandidateSourceSHA256") == palette_key
        assert material.get_editor_property("blend_mode") == u.BlendMode.BLEND_OPAQUE
        assert not material.get_editor_property("two_sided")
        color = EDIT.get_material_default_vector_parameter_value(material, "Color")
        assert all(abs(a-b) < 1e-5 for a,b in zip((color.r,color.g,color.b,color.a),item["base_color"]))
        for name,key in [("Metallic","metallic"),("Roughness","roughness")]:
            assert abs(EDIT.get_material_default_scalar_parameter_value(material,name)-item[key]) < 1e-5
        for prop in (u.MaterialProperty.MP_BASE_COLOR,u.MaterialProperty.MP_METALLIC,u.MaterialProperty.MP_ROUGHNESS):
            assert EDIT.get_material_property_input_node(material,prop)
        if item["emission"]:
            assert abs(EDIT.get_material_default_scalar_parameter_value(material,"Emission")-item["emission"]) < 1e-5
            assert EDIT.get_material_property_input_node(material,u.MaterialProperty.MP_EMISSIVE_COLOR)
        expressions = EDIT.get_material_expressions(material)
        assert not any(isinstance(e,u.MaterialExpressionTextureSample) for e in expressions)
        result["materials"].append({"path":material.get_path_name(),"source_palette_sha256":palette_key,**item})
    for item in report["assets"]:
        mesh = LIB.load_asset(author.mesh_path(item["name"]))
        assert isinstance(mesh,u.StaticMesh)
        assert LIB.get_metadata_tag(mesh,"SSEnemyCandidateVersion") == author.VERSION
        assert LIB.get_metadata_tag(mesh,"SSEnemyCandidateSourceSHA256") == item["obj_sha256"]
        assert editor.get_lod_count(mesh) == 1 and mesh.get_num_sections(0) == 4
        assert mesh.get_num_triangles(0) == item["triangles"]
        assert editor.get_num_uv_channels(mesh,0) == 1
        assert editor.get_simple_collision_count(mesh) == 0
        assert all(not editor.is_section_collision_enabled(mesh,0,i) for i in range(4))
        instance=mesh.get_editor_property("body_setup").get_editor_property("default_instance")
        assert instance.get_editor_property("collision_enabled") == u.CollisionEnabled.NO_COLLISION
        assert str(instance.get_editor_property("collision_profile_name")) == "NoCollision"
        import_data=mesh.get_editor_property("asset_import_data")
        assert import_data.get_editor_property("normal_import_method") == u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
        bound=mesh.get_bounds()
        origin=[bound.origin.x,bound.origin.y,bound.origin.z]
        extent=[bound.box_extent.x,bound.box_extent.y,bound.box_extent.z]
        actual=[[origin[a]-extent[a] for a in range(3)],[origin[a]+extent[a] for a in range(3)]]
        assert all(abs(actual[e][a]-item["bounds_cm"][e][a]) < .03 for e in range(2) for a in range(3)), "Imported bounds/axes differ"
        assert all(abs(v) < .03 for v in origin), "Candidate pivot is not centered"
        slots=[]
        for slot in mesh.get_editor_property("static_materials"):
            name=str(slot.get_editor_property("imported_material_slot_name"))
            material=slot.get_editor_property("material_interface")
            assert material.get_path_name().split(".")[0] == author.material_path(name)
            slots.append(name)
        assert len(slots)==4 and set(slots)==set(author.MATERIALS)
        result["meshes"].append({"kind":item["name"],"path":mesh.get_path_name(),"triangles":mesh.get_num_triangles(0),
                                "render_vertices":editor.get_number_verts(mesh,0),"bounds_cm":actual,"origin_cm":origin,
                                "max_extent_cm":max(extent),"runtime_scale_at_radius150":150/max(extent),
                                "source_farthest_vertex_at_radius150_cm":item["farthest_vertex_at_runtime_radius150_cm"],
                                "material_slots":slots,"lods":1,"uv_channels":1,"simple_collision_shapes":0,
                                "all_section_collision_disabled":True,"normal_import_method":"IMPORT_NORMALS",
                                **built_geometry(mesh,item["name"])})
    result["packages"]=[{"path":str(p.relative_to(ROOT)),"bytes":p.stat().st_size,"sha256":author.sha(p)}
                       for p in sorted((ROOT/"Content").rglob("*.uasset")) if author.owned_content(p)]
    assert len(result["packages"]) == 6
    result["limits"]=["Only two separate enemy meshes and four shared materials; no production enemy selection.",
                      "Existing Radius150 actor collision sphere retained. Max-extent fitting can leave outer corners beyond that sphere, as recorded; no additional collider.",
                      "One LOD and four draw sections per mesh; no runtime LOD/performance or final art acceptance."]
    return result


def preview(record, protected):
    u.EditorLoadingAndSavingUtils.new_blank_map(False)
    actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    for command in ("r.MotionBlurQuality 0","r.ScreenPercentage 100","r.AntiAliasingMethod 2"):
        u.SystemLibrary.execute_console_command(world,command)
    actor=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0),u.Rotator(pitch=0,yaw=0,roll=0))
    component=actor.get_component_by_class(u.StaticMeshComponent)
    component.set_mobility(u.ComponentMobility.MOVABLE)
    component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    for pitch,yaw,color,intensity in [(-35,-35,(.90,.95,1,1),4),(-25,145,(1,.86,.72,1),2),(-65,70,(.60,.74,1,1),1)]:
        light=actors.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,500),u.Rotator(pitch=pitch,yaw=yaw,roll=0))
        lamp=light.get_component_by_class(u.DirectionalLightComponent)
        lamp.set_mobility(u.ComponentMobility.MOVABLE)
        lamp.set_light_color(u.LinearColor(*color))
        lamp.set_intensity(intensity)
    post=actors.spawn_actor_from_class(u.PostProcessVolume,u.Vector(0,0,0))
    post.set_editor_property("unbound",True)
    settings=post.get_editor_property("settings")
    for key,value in {"override_auto_exposure_min_brightness":True,"override_auto_exposure_max_brightness":True,
                      "auto_exposure_min_brightness":1.,"auto_exposure_max_brightness":1.,
                      "override_bloom_intensity":True,"bloom_intensity":.1}.items():
        settings.set_editor_property(key,value)
    post.set_editor_property("settings",settings)
    camera=actors.spawn_actor_from_class(u.CameraActor,u.Vector(0,0,0))
    camera.get_component_by_class(u.CameraComponent).set_field_of_view(35)
    camera.get_component_by_class(u.CameraComponent).set_editor_property("aspect_ratio",1.4)
    u.get_editor_subsystem(u.LevelEditorSubsystem).editor_set_game_view(True)
    views=[("ForwardQuarter",(650,-650,500)),("RearQuarter",(-650,-650,450)),
           ("TopSilhouette",(.01,0,1000)),("HeadOn",(800,0,0))]
    cases=[(kind,name,position) for kind in author.KINDS for name,position in views]
    state={"index":0,"frames":0,"task":None,"busy":False,"done":False,"handle":None,"start":time.monotonic()}
    record["images"]=[]
    record["preview_method"]="Unsaved StaticMeshActor, unchanged +X-forward orientation, uniform scale150/maxBoxExtent, three studio directional lights, ordinary shadows. HeadOn camera lies on +X, matching ASSEnemy::Tick's existing direction toward the player; no AI or physical input simulated."
    def setup():
        kind,name,position=cases[state["index"]]
        mesh=LIB.load_asset(author.mesh_path(kind))
        component.set_static_mesh(mesh)
        b=mesh.get_bounds().box_extent
        scale=150/max(b.x,b.y,b.z)
        actor.set_actor_scale3d(u.Vector(scale,scale,scale))
        location=u.Vector(*position)
        rotation=u.MathLibrary.find_look_at_rotation(location,u.Vector(0,0,0))
        camera.set_actor_location(location,False,False)
        camera.set_actor_rotation(rotation,False)
        u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(location,rotation)
        state.update(frames=0,task=None,case_start=time.monotonic(),scale=scale)
    def finish():
        if state["done"]:
            return
        state["done"]=True
        changed=[str(p.relative_to(ROOT)) for p,d in protected.items() if author.sha(p)!=d]
        if changed:
            record["errors"].append("Protected source/config/content changed: "+",".join(changed))
        record["existing_protected_files_unchanged"]=len(protected) if not changed else None
        record["status"]="NATIVE_SEPARATE_ENEMY_PREVIEWS_CAPTURED_NOT_ADOPTED" if not record["errors"] else "FAILED"
        (OUT/"UnrealPreview.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8", newline="\n")
        u.unregister_slate_post_tick_callback(state["handle"])
        u.EditorPythonScripting.set_keep_python_script_alive(False)
        u.log("ENEMY_CANDIDATE_PREVIEW_FINISHED")
    def tick(delta):
        if state["busy"] or state["done"]:
            return
        state["busy"]=True
        try:
            state["frames"]+=1
            kind,name,position=cases[state["index"]]
            path=OUT/("Unreal"+kind+name+".png")
            if state["task"] is None and state["frames"]>=90 and time.monotonic()-state["case_start"]>3:
                u.AutomationLibrary.finish_loading_before_screenshot()
                state["task"]=u.AutomationLibrary.take_high_res_screenshot(1400,1000,str(path),camera,delay=.3)
                assert state["task"].is_valid_task()
            if state["task"] and state["task"].is_task_done() and path.exists():
                record["images"].append({"file":path.name,"sha256":author.sha(path),"kind":kind,"view":name,"scale":state["scale"],"camera_cm":list(position)})
                state["index"]+=1
                if state["index"]==len(cases):
                    finish()
                else:
                    setup()
            elif time.monotonic()-state["start"]>180:
                raise RuntimeError("Enemy preview timeout")
        except Exception as error:
            record["errors"].append(str(error))
            u.log_error(traceback.format_exc())
            finish()
        finally:
            state["busy"]=False
    setup()
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    state["handle"]=u.register_slate_post_tick_callback(tick)


def main(render=False):
    protected={p:author.sha(p) for directory in ("Source","Config","Content") for p in (ROOT/directory).rglob("*") if p.is_file()}
    result={"status":"FAILED","errors":[]}
    try:
        result=validate()
        assert all(author.sha(p)==d for p,d in protected.items()),"Validation changed protected files"
        result["existing_protected_files_unchanged"]=len(protected)
    except Exception as error:
        result["errors"].append(str(error))
        u.log_error("ENEMY_CANDIDATE_VALIDATE_FAILED: "+traceback.format_exc())
    (OUT/"UnrealPersisted.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8", newline="\n")
    if result["errors"]:
        raise RuntimeError("Enemy candidate validation failed")
    u.log("ENEMY_CANDIDATE_PERSISTED_OK")
    if render:
        preview(result,protected)
    return result


if __name__=="__main__":
    main("--preview" in sys.argv)
