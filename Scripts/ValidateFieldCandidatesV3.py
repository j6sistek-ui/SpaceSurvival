"""Fresh Unreal read-only validation of the four isolated field candidate assets.
Writes only a validation receipt; never changes material, mesh, map or runtime refs.
"""
import hashlib
import importlib.util
import json
import math
import re
from pathlib import Path

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ss_field_author",ROOT/"Scripts/AuthorFieldCandidatesV3.py")
author = importlib.util.module_from_spec(spec)
spec.loader.exec_module(author)



def built_geometry(mesh):
    """Export actual built LOD0 arrays read-only, including packed UV roles."""
    path = author.SOURCE/(mesh.get_name()+"-Built.fbx")
    options = u.FbxExportOption()
    for name,value in {"ascii":True,"level_of_detail":False,"collision":False,
                       "export_source_mesh":False,"vertex_color":True}.items():
        options.set_editor_property(name,value)
    task = u.AssetExportTask()
    for name,value in {"object":mesh,"filename":str(path),"automated":True,"prompt":False,
                       "replace_identical":True,"exporter":u.StaticMeshExporterFBX(),"options":options}.items():
        task.set_editor_property(name,value)
    assert u.Exporter.run_asset_export_task(task) and path.is_file(),"Built mesh export failed"
    arrays = {}
    for name,count,values in re.findall(r"\b(Vertices|PolygonVertexIndex|Normals|UV|UVIndex)\s*:\s*\*(\d+)\s*\{\s*a:\s*([^}]*)\}",path.read_text(encoding="utf-8-sig"),re.S):
        numbers = [v for v in re.split(r"[,\s]+",values.strip()) if v]
        assert len(numbers) == int(count) and all(math.isfinite(float(v)) for v in numbers)
        arrays.setdefault(name,[]).append(numbers)
    assert all(name in arrays for name in ("Vertices","PolygonVertexIndex","Normals","UV"))
    points = arrays["Vertices"][0]
    assert len(points)%3 == 0
    max_radius = max(math.sqrt(sum(float(v)**2 for v in points[i:i+3])) for i in range(0,len(points),3))
    assert max_radius <= 100.01,"Built visual exceeds the normalized field radius"
    for normals in arrays["Normals"]:
        assert len(normals)%3 == 0
        assert all(abs(sum(float(v)**2 for v in normals[i:i+3])-1)<.001 for i in range(0,len(normals),3))
    assert len(arrays["UV"]) == 1,"Unexpected built UV layers"
    uv = list(map(float,arrays["UV"][0]))
    assert len(uv)%2 == 0
    roles = {math.floor(value*.25+1e-5) for value in uv[0::2]}
    assert roles == ({0,1,2} if "Electrical" in mesh.get_name() else {0,1}),"Packed material roles were lost"
    assert all(0 <= value <= 9.001 for value in uv[0::2]),"Packed longitudinal UVs changed"
    return {"built_fbx_sha256":author.sha(path),"built_arrays_sha256":hashlib.sha256(json.dumps(arrays,sort_keys=True).encode()).hexdigest(),
            "built_max_radius_cm":max_radius,"built_uv_roles":sorted(roles),"built_normals_finite_unit":True}


def main(verify_adoption=False):
    result = {"status":"FAILED","errors":[],"meshes":[],"engine":u.SystemLibrary.get_engine_version(),
              "limits":["Persisted geometry/material contract, not rendered readability or performance.",
                        "Compiled material statistics are estimates; actual frame cost and warning/flash appearance require rendered inspection.",
                        "No runtime Data Asset or original wormhole/emissive references are changed."]}
    protected = author.protected_snapshot()
    try:
        report = author.source_report()
        editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
        edit = u.MaterialEditingLibrary
        for item in report["meshes"]:
            key = author.source_key(item)
            mesh = author.existing(author.BASE+"/Meshes/"+item["name"],key,u.StaticMesh)
            material = author.existing(author.BASE+"/Materials/"+item["material"],key,u.Material)
            assert mesh and material,"Missing field candidate"
            assert editor.get_lod_count(mesh) == 1
            assert mesh.get_num_triangles(0) == item["triangles"] <= 5000
            assert len(mesh.get_editor_property("static_materials")) == mesh.get_num_sections(0) == 1
            assert editor.get_num_uv_channels(mesh,0) == 1,"Packed role/flow UV contract changed"
            assert mesh.get_material(0) == material
            bounds = mesh.get_bounds()
            for axis in ("x","y","z"):
                assert abs(getattr(bounds.origin,axis)) < .01,"Field origin moved"
                assert abs(getattr(bounds.box_extent,axis)-100) < .01,"Radius normalization changed"
            assert editor.get_simple_collision_count(mesh) == 0
            assert not editor.is_section_collision_enabled(mesh,0,0)
            instance = mesh.get_editor_property("body_setup").get_editor_property("default_instance")
            assert instance.get_editor_property("collision_enabled") == u.CollisionEnabled.NO_COLLISION
            assert str(instance.get_editor_property("collision_profile_name")) == "NoCollision"
            assert material.get_editor_property("shading_model") == u.MaterialShadingModel.MSM_UNLIT
            assert material.get_editor_property("blend_mode") == u.BlendMode.BLEND_ADDITIVE
            assert material.get_editor_property("two_sided")
            assert not material.get_editor_property("disable_depth_test")
            for prop in (u.MaterialProperty.MP_OPACITY_MASK,
                         u.MaterialProperty.MP_WORLD_POSITION_OFFSET,u.MaterialProperty.MP_REFRACTION):
                assert edit.get_material_property_input_node(material,prop) is None,"Unexpected opacity/deformation/refraction input"
            expressions = edit.get_material_expressions(material)
            custom = [e for e in expressions if isinstance(e,u.MaterialExpressionCustom)]
            assert len(custom) == 1
            shader = (author.SOURCE/author.KINDS[item["name"]][1]).read_text(encoding="utf-8")
            assert custom[0].get_editor_property("code") == shader,"Shader differs from reviewed source"
            for prop,channels in ((u.MaterialProperty.MP_EMISSIVE_COLOR,(True,True,True,False)),
                                  (u.MaterialProperty.MP_OPACITY,(False,False,False,True))):
                mask=edit.get_material_property_input_node(material,prop)
                assert isinstance(mask,u.MaterialExpressionComponentMask)
                assert tuple(mask.get_editor_property(c) for c in ("r","g","b","a"))==channels
                assert edit.get_inputs_for_material_expression(material,mask)==[custom[0]]
            assert custom[0].get_editor_property("output_type")==u.CustomMaterialOutputType.CMOT_FLOAT4
            inputs = edit.get_inputs_for_material_expression(material,custom[0])
            assert len(inputs) == 7 and all(inputs),"Unconnected field shader input"
            assert isinstance(inputs[0],u.MaterialExpressionTextureCoordinate)
            assert inputs[0].get_editor_property("coordinate_index") == 0
            assert isinstance(inputs[1],u.MaterialExpressionTime)
            assert isinstance(inputs[5],u.MaterialExpressionPixelNormalWS)
            assert isinstance(inputs[6],u.MaterialExpressionCameraVectorWS)
            for expression,name,cls in zip(inputs[2:],("Tint","Color","Emission"),
                                           (u.MaterialExpressionVectorParameter,u.MaterialExpressionVectorParameter,u.MaterialExpressionScalarParameter)):
                assert isinstance(expression,cls) and str(expression.get_editor_property("parameter_name")) == name
            tint = edit.get_material_default_vector_parameter_value(material,"Tint")
            color = edit.get_material_default_vector_parameter_value(material,"Color")
            assert all(abs(a-b)<1e-5 for a,b in zip((tint.r,tint.g,tint.b),item["tint"]))
            assert all(abs(c-1)<1e-5 for c in (color.r,color.g,color.b))
            assert abs(edit.get_material_default_scalar_parameter_value(material,"Emission")-.25)<1e-5
            assert len(expressions) == 10,"Unexpected texture or extra material pass dependency"
            u.AutomationLibrary.finish_loading_before_screenshot()
            statistics = edit.get_statistics(material)
            stats = {name:int(statistics.get_editor_property(name)) for name in ("num_vertex_shader_instructions",
                "num_pixel_shader_instructions","num_samplers","num_vertex_texture_samples",
                "num_pixel_texture_samples","num_virtual_texture_samples","num_uv_scalars","num_interpolator_scalars")}
            assert stats["num_pixel_shader_instructions"] > 0,"No compiled material statistics available"
            assert not edit.get_material_used_textures(material),"Unexpected bitmap/texture dependency"
            result["meshes"].append({"path":mesh.get_path_name(),"triangles":mesh.get_num_triangles(0),
                "render_vertices":editor.get_number_verts(mesh,0),"material_sections":1,"uv_channels":1,
                "bounds_origin_cm":[bounds.origin.x,bounds.origin.y,bounds.origin.z],
                "bounds_extent_cm":[bounds.box_extent.x,bounds.box_extent.y,bounds.box_extent.z],
                "material":material.get_path_name(),"source_key":key,"shader_sha256":hashlib.sha256(shader.encode()).hexdigest(),
                "simple_collision_count":0,"collision_profile":"NoCollision","additive_edge_opacity":True,"no_mask_WPO_refraction":True,"depth_test_enabled":True,
                "material_statistics":stats,"statistics_limit":"Editor compiled shader estimates; not measured frame time",
                **built_geometry(mesh)})
        if verify_adoption:
            data = u.EditorAssetLibrary.load_asset(author.BASE + "/Data/DA_Phase1")
            assert isinstance(data, u.SSPhase1Data), "Missing Phase 1 Data Asset"
            result["roster"] = author.roster(data)
            result["limits"].append("Persisted V3 field selection verified; live gameplay appearance and owner acceptance remain separate.")
        assert author.protected_snapshot() == protected,"Validation changed Source/Config/unrelated Content"
        result["candidate_packages"] = [{"path":str(p.relative_to(ROOT)),"bytes":p.stat().st_size,"sha256":author.sha(p)}
            for p in sorted((ROOT/"Content").rglob("*.uasset")) if author.owned_content(p)]
        assert len(result["candidate_packages"]) == 4
        result.update(status="FIELD_CANDIDATES_PERSISTED_CONTRACT_VERIFIED_NOT_VISUAL_ACCEPTANCE",
                      protected_source_config_content_files_unchanged=len(protected),
                      adoption_verified=verify_adoption)
    except Exception as error:
        result["errors"].append(str(error))
        u.log_error("FIELD_CANDIDATE_VALIDATE_FAILED: "+str(error))
    folder = ROOT/"Saved/Validation"
    folder.mkdir(parents=True,exist_ok=True)
    (folder/"FieldCandidatesV3Persisted.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    if result["errors"]:
        raise RuntimeError("Field candidate validation failed; inspect FieldCandidatesV3Persisted.json")
    u.log("FIELD_CANDIDATES_V3_PERSISTED_OK; integrated gameplay appearance remains separate")
    return result


if __name__ == "__main__":
    main()
