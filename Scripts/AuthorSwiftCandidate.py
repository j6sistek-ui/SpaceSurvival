"""Author only SM_SwiftCandidateV1; reuse seven exact existing Acorn materials.
Run validation in a fresh UnrealEditor-Cmd process. No gameplay selection.
Routine reports go to Saved/Validation/SwiftCandidate and use explicit LF.
"""
import hashlib
import json
import runpy
from pathlib import Path
import traceback

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
source_matches = runpy.run_path(str(ROOT / "Scripts/SourceDigests.py"))["matches"]
SOURCE = ROOT / "ContentSource/SwiftCandidate"
OUT = ROOT / "Saved/Validation/SwiftCandidate"
PATH = "/Game/SpaceSurvival/Meshes/SM_SwiftCandidateV1"
VERSION = "SwiftPreservedCockpit1"
LIB = u.EditorAssetLibrary
EDIT = u.MaterialEditingLibrary
MATERIAL_NAMES = {"AC01_ChampagneEdges", "AC01_CockpitPadding", "AC01_GraphiteStructure",
                  "AC01_IonAndNav", "AC01_IvoryPanels", "AC01_MachinedTitanium", "AC01_Windscreen"}
PILOT = {"position_cm": [-15, 0, 72], "unreal_yaw_degrees": -90,
         "blender_z_rotation_degrees": 90, "scale": 1.5}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(name, record):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")


def snapshot():
    return {p: sha(p) for directory in ("Source", "Config", "Content")
            for p in (ROOT / directory).rglob("*") if p.is_file()}


def check_unchanged(protected):
    changed = [str(p.relative_to(ROOT)) for p, digest in protected.items() if not p.is_file() or sha(p) != digest]
    assert not changed, "Existing source/config/content changed: " + ", ".join(changed)


def source_report():
    report = json.loads((SOURCE / "Report.json").read_text(encoding="utf-8"))
    validation = json.loads((SOURCE / "Validation.json").read_text(encoding="utf-8"))
    assert validation["status"] == "SWIFT_FRESH_SOURCE_GEOMETRY_COCKPIT_EXPORT_CHECKS_PASS_NOT_UNREAL"
    assert report["generator_sha256"] == validation["generator_sha256"] == sha(SOURCE / "Generate.py")
    assert validation["validator_sha256"] == sha(SOURCE / "Validate.py")
    assert source_matches(SOURCE / "Report.json", validation["report_sha256"])
    assert report["pilot_transform"] == PILOT and report["pivot_cm"] == [0, 0, 0]
    assert report["parts"] == 85 and len(report["preserved_cockpit"]) == validation["cockpit_parts_preserved"] == 24
    assert report["triangles"] == validation["obj"]["triangles"] == validation["glb"]["triangles"]
    assert {m["name"] for m in report["materials"]} == MATERIAL_NAMES
    assert all(name in report["preserved_cockpit"] for name in report["joined_degenerate_by_part"])
    for row in report["outputs"]:
        assert source_matches(SOURCE / row["file"], row["sha256"]), "Candidate source changed: " + row["file"]
    for path, digest in report["protected_sha256"].items():
        assert source_matches(ROOT / path, digest), "Protected original changed: " + path
    return report


def material_path(name):
    assert name in MATERIAL_NAMES
    return "/Game/SpaceSurvival/Materials/M_AcornV2_" + name.removeprefix("AC01_")


def checked_materials(report):
    result = {}
    records = []
    original_obj = ROOT / "ContentSource/AcornShipCandidate/AcornShipCandidate.obj"
    for row in report["materials"]:
        mat = LIB.load_asset(material_path(row["name"]))
        assert isinstance(mat, u.Material), "Missing existing material: " + row["name"]
        assert source_matches(original_obj, LIB.get_metadata_tag(mat, "SSAcornSourceSHA256"))
        color = EDIT.get_material_default_vector_parameter_value(mat, "Color")
        assert all(abs(a-b) < 1e-5 for a,b in zip((color.r,color.g,color.b,color.a), row["base_color"]))
        for name,key in (("Metallic","metallic"),("Roughness","roughness")):
            assert abs(EDIT.get_material_default_scalar_parameter_value(mat,name)-row[key]) < 1e-5
        glass = row["name"] == "AC01_Windscreen"
        assert mat.get_editor_property("blend_mode") == (u.BlendMode.BLEND_TRANSLUCENT if glass else u.BlendMode.BLEND_OPAQUE)
        if glass:
            assert mat.get_editor_property("two_sided")
            assert abs(EDIT.get_material_default_scalar_parameter_value(mat,"Opacity")-.18) < 1e-5
        if row["name"] == "AC01_IonAndNav":
            assert abs(EDIT.get_material_default_scalar_parameter_value(mat,"Emission")-3.5) < 1e-5
        if row["name"] not in ("AC01_CockpitPadding","AC01_IonAndNav","AC01_Windscreen"):
            assert LIB.get_metadata_tag(mat,"SSAcornMicrodetailVersion") == "ObjectLocalPosition2"
            expressions = EDIT.get_material_expressions(mat)
            groups = [[e for e in expressions if isinstance(e,cls)] for cls in
                      (u.MaterialExpressionWorldPosition,u.MaterialExpressionTransformPosition,u.MaterialExpressionNoise)]
            assert all(len(g)==1 for g in groups)
            world,local,noise = [g[0] for g in groups]
            assert EDIT.get_inputs_for_material_expression(mat,local)[0] == world
            assert EDIT.get_inputs_for_material_expression(mat,noise)[0] == local
        result[row["name"]] = mat
        records.append({"path":mat.get_path_name(),"source_material":row["name"],"values":row,
                        "translucent":glass,"existing_material_changed":False})
    return result, records


def import_candidate(report, materials):
    digest = sha(SOURCE / "SwiftCandidate.obj")
    if LIB.does_asset_exist(PATH):
        mesh = LIB.load_asset(PATH)
        assert isinstance(mesh,u.StaticMesh)
        assert LIB.get_metadata_tag(mesh,"SSSwiftCandidateVersion") == VERSION
        assert source_matches(SOURCE / "SwiftCandidate.obj", LIB.get_metadata_tag(mesh,"SSSwiftSourceSHA256")), "Changed source needs a new reviewed candidate version"
        return mesh
    options = u.FbxImportUI()
    for key,value in {"import_mesh":True,"import_as_skeletal":False,"import_materials":False,"import_textures":False,
                      "mesh_type_to_import":u.FBXImportType.FBXIT_STATIC_MESH}.items():
        options.set_editor_property(key,value)
    data = options.get_editor_property("static_mesh_import_data")
    for key,value in {"combine_meshes":True,"auto_generate_collision":False,"generate_lightmap_u_vs":False,
                      "import_uniform_scale":1.0,"convert_scene":False,"force_front_x_axis":False,
                      "normal_import_method":u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS}.items():
        data.set_editor_property(key,value)
    task = u.AssetImportTask()
    for key,value in {"filename":str(SOURCE/"SwiftCandidate.obj"),"destination_path":"/Game/SpaceSurvival/Meshes",
                      "destination_name":"SM_SwiftCandidateV1","automated":True,"replace_existing":False,"save":False,
                      "options":options,"factory":u.FbxFactory()}.items():
        task.set_editor_property(key,value)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    assets = [LIB.load_asset(p) for p in task.get_editor_property("imported_object_paths")]
    assert len(assets) == 1 and isinstance(assets[0],u.StaticMesh), "Unexpected importer product"
    mesh = assets[0]
    assert mesh.get_path_name().split(".")[0] == PATH, "Unexpected destination; refuse renaming over existing assets"
    names = []
    for index,slot in enumerate(mesh.get_editor_property("static_materials")):
        name = str(slot.get_editor_property("imported_material_slot_name"))
        assert name in materials
        mesh.set_material(index,materials[name]);names.append(name)
    assert len(names)==7 and set(names)==MATERIAL_NAMES
    editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    editor.remove_collisions(mesh)
    for section in range(mesh.get_num_sections(0)):
        editor.enable_section_collision(mesh,False,0,section)
    body = mesh.get_editor_property("body_setup")
    instance = body.get_editor_property("default_instance")
    instance.set_editor_property("collision_profile_name","NoCollision")
    instance.set_editor_property("collision_enabled",u.CollisionEnabled.NO_COLLISION)
    body.set_editor_property("default_instance",instance)
    LIB.set_metadata_tag(mesh,"SSSwiftCandidateVersion",VERSION)
    LIB.set_metadata_tag(mesh,"SSSwiftSourceSHA256",digest)
    LIB.set_metadata_tag(mesh,"SSSwiftPilotMount","Position -15,0,72 cm; yaw -90; scale1.5; geometry pivot0")
    assert LIB.save_loaded_asset(mesh,only_if_is_dirty=False)
    return mesh


def main():
    protected = snapshot()
    record = {"status":"FAILED","errors":[],"engine":u.SystemLibrary.get_engine_version()}
    try:
        report = source_report()
        materials,rows = checked_materials(report)
        mesh = import_candidate(report,materials)
        check_unchanged(protected)
        package = ROOT / "Content/SpaceSurvival/Meshes/SM_SwiftCandidateV1.uasset"
        added = [str(p.relative_to(ROOT)) for p in (ROOT/"Content").rglob("*") if p.is_file() and p not in protected]
        assert set(added) <= {str(package.relative_to(ROOT))}, "Unexpected new Content asset"
        record.update(status="SEPARATE_SWIFT_MESH_AUTHORED_FRESH_VALIDATION_PENDING",mesh=mesh.get_path_name(),
                      materials=rows,source_report_sha256=sha(SOURCE/"Report.json"),obj_sha256=sha(SOURCE/"SwiftCandidate.obj"),
                      pilot_transform=report["pilot_transform"],existing_protected_files_unchanged=len(protected),
                      new_content_assets=added,package={"path":str(package.relative_to(ROOT)),"bytes":package.stat().st_size,"sha256":sha(package)},
                      limits=["One separate mesh only; existing seven material packages unchanged.",
                              "No runtime selection, stat/collision/pilot transform or author-main pipeline change.",
                              "Source cockpit degeneracies are retained; native cleanup count is a separate fresh check.",
                              "No native appearance, animated clearance, performance or owner quality acceptance from import."])
    except Exception as error:
        record["errors"].append(str(error));u.log_error(traceback.format_exc())
    write("SwiftImport.json",record)
    if record["errors"]:raise RuntimeError("Swift import failed; see Saved/Validation/SwiftCandidate/SwiftImport.json")
    u.log("SWIFT_CANDIDATE_IMPORT_OK")
    return record


if __name__=="__main__":main()
