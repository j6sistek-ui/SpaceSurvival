"""Import only the reviewed pilot derivative as SK_AcornautPilot.

Uses a transient Interchange pipeline, the original skeleton/materials, and no
physics/animation/texture import. Original content files are hash checked.
"""
import hashlib
import json
import sys
from pathlib import Path
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
BASE = "/Game/SpaceSurvival/Character"
TARGET = BASE + "/SK_AcornautPilot"
LIB = u.EditorAssetLibrary


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = ROOT / "ContentSource/Animation/PilotMesh.glb"
    manifest = json.loads(source.with_suffix(".json").read_text(encoding="utf-8"))
    assert digest(source) == manifest["derivative_sha256"]
    assert digest(ROOT / "model-rigged.glb") == manifest["source_glb_sha256"]
    reimport = "--reimport" in sys.argv
    if LIB.does_asset_exist(TARGET):
        assert reimport and LIB.get_metadata_tag(u.load_asset(TARGET), "SSPilotMeshOnly") == "ExistingA_PilotOnly", "Existing derivative requires explicit --reimport"
    original = u.load_asset(BASE + "/SK_Acornaut")
    skeleton = original.get_editor_property("skeleton")
    assert original and skeleton
    protected = {str(path): digest(path) for path in (ROOT / "Content/SpaceSurvival/Character").rglob("*.uasset") if path.stem != "SK_AcornautPilot"}
    pipeline = u.new_object(u.InterchangeGenericAssetsPipeline, name="SSPilotMeshOnlyImport")
    for key, value in {"asset_name": "SK_AcornautPilot", "use_source_name_for_asset": False,
                       "asset_type_sub_folders": False, "scene_name_sub_folder": False}.items():
        pipeline.set_editor_property(key, value)
    common = pipeline.get_editor_property("common_skeletal_meshes_and_animations_properties")
    for key, value in {"import_only_animations": False, "skeleton": skeleton,
                       "try_auto_select_skeleton": False, "use_t0_as_ref_pose": False}.items():
        common.set_editor_property(key, value)
    settings = pipeline.get_editor_property("mesh_pipeline")
    for key, value in {"import_skeletal_meshes": True, "import_static_meshes": False,
                       "create_physics_asset": False, "update_skeleton_reference_pose": False}.items():
        settings.set_editor_property(key, value)
    settings.set_editor_property("combine_skeletal_meshes_behavior", u.InterchangeCombineSkeletalMeshesBehavior.BY_SKELETON)
    pipeline.get_editor_property("animation_pipeline").set_editor_property("import_animations", False)
    material = pipeline.get_editor_property("material_pipeline")
    material.set_editor_property("import_materials", False)
    material.get_editor_property("texture_pipeline").set_editor_property("import_textures", False)
    params = u.ImportAssetParameters()
    params.set_editor_property("is_automated", True)
    params.set_editor_property("replace_existing", reimport)
    params.set_editor_property("override_pipelines", [u.SoftObjectPath(pipeline.get_path_name())])
    manager = u.InterchangeManager.get_interchange_manager_scripted()
    imported = manager.import_asset(BASE, manager.create_source_data(str(source)), params)
    meshes = [obj for obj in imported if isinstance(obj, u.SkeletalMesh)]
    assert len(meshes) == 1 and len(imported) == 1, "Expected only one new skeletal mesh"
    mesh = meshes[0]
    assert mesh.get_path_name().split(".")[0] == TARGET, "Unexpected import target"
    assert mesh.get_editor_property("skeleton") == skeleton, "Imported mesh must reuse original skeleton"
    mesh.set_editor_property("materials", original.get_editor_property("materials"))
    LIB.set_metadata_tag(mesh, "SSAuthoringVersion", "1")
    LIB.set_metadata_tag(mesh, "SSPilotMeshSourceSHA256", manifest["derivative_sha256"])
    LIB.set_metadata_tag(mesh, "SSPilotMeshOnly", "ExistingA_PilotOnly")
    assert LIB.save_loaded_asset(mesh, only_if_is_dirty=False)
    for filename, previous in protected.items():
        assert digest(Path(filename)) == previous, "Protected original character asset changed: " + filename
    receipt = {"status": "PILOT_DERIVATIVE_IMPORTED_REQUIRES_FIT_REVIEW", "engine": u.SystemLibrary.get_engine_version(),
               "mesh": mesh.get_path_name(), "shared_skeleton": skeleton.get_path_name(),
               "materials": [slot.get_editor_property("material_interface").get_path_name() for slot in mesh.get_editor_property("materials")],
               "source_glb_sha256": manifest["source_glb_sha256"], "derivative_sha256": manifest["derivative_sha256"],
               "protected_character_asset_hashes": protected, "imported_asset_count": len(imported)}
    (ROOT / "ContentSource/Animation/PilotMeshImport.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    u.log("Pilot derivative import verified: " + mesh.get_path_name())


if __name__ == "__main__":
    main()
