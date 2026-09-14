"""Author four field assets; optional roster migration selects only reviewed V3 meshes.
Mesh authoring never changes the Data Asset. The separate roster() API replaces
only legacy field mesh names, and never edits the shared emissive or wormhole.
"""
import hashlib
import json
import runpy
import subprocess
from pathlib import Path

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
source_matches = runpy.run_path(str(ROOT / "Scripts/SourceDigests.py"))["matches"]
SOURCE = ROOT / "ContentSource/FieldCandidates/V3"
BASE = "/Game/SpaceSurvival"
VERSION = "FieldCandidate3"
KINDS = {
    "SM_ElectricalFieldCandidateV3": ("M_ElectricalFieldCandidateV3", "ElectricalField.hlsl"),
    "SM_GravityFieldCandidateV3": ("M_GravityFieldCandidateV3", "GravityField.hlsl"),
}
OWNED_PATHS = {BASE+"/Meshes/"+name for name in KINDS} | {BASE+"/Materials/"+m for m,_ in KINDS.values()}
LIB = u.EditorAssetLibrary
EDIT = u.MaterialEditingLibrary


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def owned_content(path):
    relative = Path(path).resolve().relative_to((ROOT/"Content").resolve()).with_suffix("")
    return "/Game/"+relative.as_posix() in OWNED_PATHS


def protected_snapshot():
    return {str(p.relative_to(ROOT)):sha(p) for folder in ("Source","Config","Content")
            for p in sorted((ROOT/folder).rglob("*")) if p.is_file()
            and not (folder=="Content" and owned_content(p))}


def source_report():
    report = json.loads((SOURCE/"SourceReport.json").read_text(encoding="utf-8"))
    if report["version"] != VERSION or {m["name"] for m in report["meshes"]} != set(KINDS):
        raise RuntimeError("Unexpected field candidate source set/version")
    assert sha(SOURCE/"Generate.py") == report["generator_sha256"], "Generator changed after source receipt"
    assert source_matches(SOURCE/"FieldPalette.mtl", report["palette_sha256"]), "Candidate palette changed"
    for name,digest in report["protected_sha256"].items():
        assert source_matches(ROOT/name, digest), "Protected field/runtime input changed; review before import: "+name
    historical=report["historical_runtime_git"]
    for name,digest in historical["sha256"].items():
        blob=subprocess.check_output(["git","show",historical["base"]+":"+name],cwd=ROOT)
        assert hashlib.sha256(blob).hexdigest()==digest,"Historical runtime Git evidence changed: "+name
    for name,digest in report["shader_sha256"].items():
        assert sha(SOURCE/name) == digest, "Candidate shader changed after source receipt"
    for item in report["meshes"]:
        assert item["material"] == KINDS[item["name"]][0]
        assert 0 < item["triangles"] <= 5000 and item["material_sections"] == 1
        for output in item["outputs"]:
            assert source_matches(SOURCE/output["file"], output["sha256"]), "Candidate bytes changed: "+output["file"]
    return report


def source_key(item):
    # Preserve the reviewed OBJ identity across exact LF/CRLF representations.
    mesh_key = next(output["sha256"] for output in item["outputs"] if output["file"] == item["name"]+".obj")
    payload = {"version": VERSION, "mesh": mesh_key,
               "shader": sha(SOURCE/KINDS[item["name"]][1]), "tint": item["tint"],
               "material": item["material"], "uv": "Role4Longitudinal_Strand4CrossRibbonWidth"}
    return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()


def save(asset, key):
    path = asset.get_path_name().split(".")[0]
    if path not in OWNED_PATHS:
        raise RuntimeError("Refusing to save outside the four candidate paths: "+path)
    for name,value in {"SSAuthoringVersion":"1", "SSFieldCandidateVersion":VERSION,
                       "SSFieldSourceKey":key, "SSFieldRuntimeAdoption":"None"}.items():
        LIB.set_metadata_tag(asset,name,value)
    if not LIB.save_loaded_asset(asset,only_if_is_dirty=False):
        raise RuntimeError("Candidate save failed: "+path)


def existing(path,key,cls):
    asset = LIB.load_asset(path)
    if asset and (not isinstance(asset,cls) or LIB.get_metadata_tag(asset,"SSFieldCandidateVersion") != VERSION or
                  LIB.get_metadata_tag(asset,"SSFieldSourceKey") != key):
        raise RuntimeError("Existing asset requires explicit review; no automatic overwrite: "+path)
    return asset


def create_material(item,key):
    path = BASE+"/Materials/"+item["material"]
    material = existing(path,key,u.Material)
    if material:
        return material
    material = u.AssetToolsHelpers.get_asset_tools().create_asset(item["material"],BASE+"/Materials",u.Material,u.MaterialFactoryNew())
    if not material:
        raise RuntimeError("Material creation failed: "+path)
    material.set_editor_property("shading_model",u.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property("blend_mode",u.BlendMode.BLEND_ADDITIVE)
    material.set_editor_property("two_sided",True)
    material.set_editor_property("disable_depth_test",False)
    inputs = {}
    for index,(name,cls) in enumerate((("UV",u.MaterialExpressionTextureCoordinate),
                                     ("Time",u.MaterialExpressionTime),
                                     ("Tint",u.MaterialExpressionVectorParameter),
                                     ("Color",u.MaterialExpressionVectorParameter),
                                     ("Emission",u.MaterialExpressionScalarParameter),
                                     ("Normal",u.MaterialExpressionPixelNormalWS),
                                     ("View",u.MaterialExpressionCameraVectorWS))):
        inputs[name] = EDIT.create_material_expression(material,cls,-700,index*160)
    inputs["UV"].set_editor_property("coordinate_index",0)
    for name,value in (("Tint",item["tint"]),("Color",(1,1,1))):
        inputs[name].set_editor_property("parameter_name",name)
        inputs[name].set_editor_property("default_value",u.LinearColor(*value,1))
    inputs["Emission"].set_editor_property("parameter_name","Emission")
    inputs["Emission"].set_editor_property("default_value",.25)
    custom = EDIT.create_material_expression(material,u.MaterialExpressionCustom,-250,0)
    shader = (SOURCE/KINDS[item["name"]][1]).read_text(encoding="utf-8")
    custom.set_editor_property("code",shader)
    custom.set_editor_property("description","Field V3: additive extent and broad soft ribbons with derivative-filtered cores")
    custom.set_editor_property("output_type",u.CustomMaterialOutputType.CMOT_FLOAT4)
    pins = []
    for name in inputs:
        pin = u.CustomInput()
        pin.set_editor_property("input_name",name)
        pins.append(pin)
    custom.set_editor_property("inputs",pins)
    for name,expression in inputs.items():
        assert EDIT.connect_material_expressions(expression,"",custom,name), "Material input failed: "+name
    for name,channels,property in (("Color",(True,True,True,False),u.MaterialProperty.MP_EMISSIVE_COLOR),
                                    ("Opacity",(False,False,False,True),u.MaterialProperty.MP_OPACITY)):
        mask=EDIT.create_material_expression(material,u.MaterialExpressionComponentMask,0,0 if name=="Color" else 180)
        for channel,value in zip(("r","g","b","a"),channels):mask.set_editor_property(channel,value)
        assert EDIT.connect_material_expressions(custom,"",mask,"")
        assert EDIT.connect_material_property(mask,"",property)
    EDIT.recompile_material(material)
    LIB.set_metadata_tag(material,"SSFieldShaderSHA256",sha(SOURCE/KINDS[item["name"]][1]))
    save(material,key)
    return material


def import_mesh(item,material,key):
    path = BASE+"/Meshes/"+item["name"]
    mesh = existing(path,key,u.StaticMesh)
    if mesh:
        # Fresh validation checks its contract; no-change authoring preserves bytes.
        return mesh
    if not mesh:
        options = u.FbxImportUI()
        for name,value in {"import_mesh":True,"import_as_skeletal":False,"import_materials":False,
                           "import_textures":False,"mesh_type_to_import":u.FBXImportType.FBXIT_STATIC_MESH}.items():
            options.set_editor_property(name,value)
        data = options.get_editor_property("static_mesh_import_data")
        for name,value in {"combine_meshes":True,"auto_generate_collision":False,"generate_lightmap_u_vs":False,
                           "import_uniform_scale":1.0,"convert_scene":False,"force_front_x_axis":False,
                           "normal_import_method":u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS}.items():
            data.set_editor_property(name,value)
        task = u.AssetImportTask()
        for name,value in {"filename":str(SOURCE/(item["name"]+".obj")),"destination_path":BASE+"/Meshes",
                           "destination_name":item["name"],"automated":True,"replace_existing":False,
                           "save":False,"options":options,"factory":u.FbxFactory()}.items():
            task.set_editor_property(name,value)
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        imported = [LIB.load_asset(p) for p in task.get_editor_property("imported_object_paths")]
        if len(imported) != 1 or not isinstance(imported[0],u.StaticMesh):
            raise RuntimeError("Import did not create exactly one static mesh")
        mesh = imported[0]
        if mesh.get_path_name().split(".")[0] != path:
            raise RuntimeError("Unexpected import destination; refusing rename/adoption: "+mesh.get_path_name())
    slots = list(mesh.get_editor_property("static_materials"))
    assert len(slots) == 1 and mesh.get_num_sections(0) == 1, "Lost single-section field contract"
    names = {str(slots[0].get_editor_property(n)) for n in ("material_slot_name","imported_material_slot_name")}
    assert item["material"] in names, "Unexpected material group"
    mesh.set_material(0,material)
    editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    editor.remove_collisions(mesh)
    for lod in range(editor.get_lod_count(mesh)):
        for section in range(mesh.get_num_sections(lod)):
            editor.enable_section_collision(mesh,False,lod,section)
    body = mesh.get_editor_property("body_setup")
    instance = body.get_editor_property("default_instance")
    instance.set_editor_property("collision_profile_name","NoCollision")
    instance.set_editor_property("collision_enabled",u.CollisionEnabled.NO_COLLISION)
    body.set_editor_property("default_instance",instance)
    save(mesh,key)
    return mesh


def roster(data, migrate=False):
    """Replace only legacy field meshes; retain all six hazard definitions."""
    choices = {
        u.SSWorldKind.ELECTRICAL_STORM: ("SM_StormRing", "SM_ElectricalFieldCandidateV3"),
        u.SSWorldKind.GRAVITY_ANOMALY: ("SM_GravityRing", "SM_GravityFieldCandidateV3"),
    }
    expected = set(choices) | {u.SSWorldKind.SMALL_ASTEROID, u.SSWorldKind.MEDIUM_ASTEROID,
                              u.SSWorldKind.MASSIVE_ASTEROID, u.SSWorldKind.WRECKAGE}
    entries = list(data.get_editor_property("hazards"))
    assert len(entries) == 6 and {entry.get_editor_property("kind") for entry in entries} == expected, "Unexpected hazard roster"
    replacements = []
    result = []
    for entry in entries:
        kind = entry.get_editor_property("kind")
        prior = str(entry.get_editor_property("mesh_name"))
        revised = entry.copy()
        if kind in choices:
            legacy, selected = choices[kind]
            assert prior in (legacy, selected), "Unreviewed custom field mesh requires deliberate integration: " + prior
            if migrate and prior == legacy:
                revised.set_editor_property("mesh_name", selected)
            if not migrate:
                assert prior == selected, "Legacy field presentation remains selected"
        restored = revised.copy()
        restored.set_editor_property("mesh_name", prior)
        assert restored.export_text() == entry.export_text(), "Field presentation migration changed hazard tuning"
        replacements.append(revised)
        result.append({"kind": str(kind), "mesh_before": prior,
                       "mesh_after": str(revised.get_editor_property("mesh_name")),
                       "all_other_fields_preserved": True,
                       "tuning_with_prior_mesh_sha256": hashlib.sha256(entry.export_text().encode()).hexdigest()})
    if migrate and any(row["mesh_before"] != row["mesh_after"] for row in result):
        data.set_editor_property("hazards", replacements)
        assert [entry.export_text() for entry in data.get_editor_property("hazards")] == [entry.export_text() for entry in replacements]
    return result


def main():
    result = {"status":"FAILED","version":VERSION,"errors":[],"engine":u.SystemLibrary.get_engine_version(),
              "limits":["Candidate import only; no Data Asset selection or gameplay references changed.",
                        "Fresh validation, rendered readability and actual material/render cost remain pending."]}
    protected = protected_snapshot()
    try:
        report = source_report()
        # Validate every pre-existing owned package before creating any asset.
        for item in report["meshes"]:
            key = source_key(item)
            existing(BASE+"/Meshes/"+item["name"],key,u.StaticMesh)
            existing(BASE+"/Materials/"+item["material"],key,u.Material)
        meshes = []
        for item in report["meshes"]:
            key = source_key(item)
            mesh = import_mesh(item,create_material(item,key),key)
            meshes.append({"path":mesh.get_path_name(),"source_key":key})
        assert protected_snapshot() == protected, "Source/Config/unrelated Content changed during authoring"
        result.update(status="FIELD_CANDIDATES_IMPORTED_NOT_ADOPTED_FRESH_VALIDATION_PENDING",meshes=meshes,
                      protected_source_config_content_files_unchanged=len(protected))
    except Exception as error:
        result["errors"].append(str(error))
        u.log_error("FIELD_CANDIDATE_IMPORT_FAILED: "+str(error))
    folder = ROOT/"Saved/Validation"
    folder.mkdir(parents=True,exist_ok=True)
    (folder/"FieldCandidatesV3Import.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    if result["errors"]:
        raise RuntimeError("Field candidate import failed; inspect FieldCandidatesV3Import.json")
    u.log("FIELD_CANDIDATES_V3_IMPORT_OK; runtime adoption remains separate")


if __name__ == "__main__":
    main()
