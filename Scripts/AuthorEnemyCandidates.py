"""Author only two separate enemy meshes and four shared candidate materials.
Mesh authoring never overwrites existing assets. The optional roster migration only replaces legacy mesh selections.
Use a fresh UnrealEditor-Cmd process, then ValidateEnemyCandidates.py separately.
"""
import hashlib
import json
import math
import runpy
from pathlib import Path

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
source_matches = runpy.run_path(str(ROOT / "Scripts/SourceDigests.py"))["matches"]
SOURCE = ROOT / "ContentSource/EnemyCandidates"
OUTPUT = ROOT / "Saved/Validation/EnemyCandidates"
BASE = "/Game/SpaceSurvival"
VERSION = "IndustrialEnemyCandidate1"
KINDS = ("Pursuer", "Flanker")
MATERIALS = ("EN_Titanium", "EN_Ceramic", "EN_Recess", "EN_Amber")
LIB = u.EditorAssetLibrary
EDIT = u.MaterialEditingLibrary


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mesh_path(kind):
    assert kind in KINDS
    return BASE + "/Meshes/SM_" + kind + "CandidateV1"


def material_path(name):
    assert name in MATERIALS
    return BASE + "/Materials/M_EnemyCandidate_" + name.removeprefix("EN_")


def owned_content(path):
    relative = path.relative_to(ROOT).as_posix()
    expected = {"Content/SpaceSurvival/Meshes/SM_" + k + "CandidateV1.uasset" for k in KINDS}
    expected |= {"Content/SpaceSurvival/Materials/M_EnemyCandidate_" + n.removeprefix("EN_") + ".uasset" for n in MATERIALS}
    return relative in expected


def checked_source():
    report = json.loads((SOURCE / "SourceReport.json").read_text(encoding="utf-8"))
    checked = json.loads((SOURCE / "Validation.json").read_text(encoding="utf-8"))
    assert checked["status"] == "CANDIDATE_SOURCE_TOPOLOGY_NORMAL_UV_EXPORT_CHECKS_PASS_NOT_UNREAL"
    assert report["generator_sha256"] == checked["generator_sha256"] == sha(SOURCE / "Generate.py")
    assert set(item["name"] for item in report["assets"]) == set(KINDS)
    assert set(item["name"] for item in report["materials"]) == set(MATERIALS)
    for item in report["assets"]:
        assert 8000 <= item["triangles"] <= 20000 and len(item["materials"]) == 4 and item["uv_layers"] == 1
        assert source_matches(SOURCE / (item["name"] + ".obj"), item["obj_sha256"])
        assert sha(SOURCE / (item["name"] + ".glb")) == item["glb_sha256"]
        match = next(row for row in checked["assets"] if row["name"] == item["name"])
        assert match["obj_sha256"] == item["obj_sha256"] and match["glb_sha256"] == item["glb_sha256"]
        assert match["all_edges_two_incident_faces"] and match["all_components_outward_positive_volume"] and match["finite_unit_normals"]
    for item in report["materials"]:
        assert all(math.isfinite(v) for v in item["base_color"] + [item["metallic"], item["roughness"], item["emission"]])
        assert len(item["base_color"]) == 4 and all(0 <= v <= 1 for v in item["base_color"])
        assert 0 <= item["metallic"] <= 1 and 0 <= item["roughness"] <= 1 and 0 <= item["emission"] <= 3
    for path, digest in report["protected_sha256"].items():
        relative = path.replace("\\", "/")
        assert source_matches(ROOT / relative, digest), "Protected original changed: " + relative
    return report


def palette_key(report):
    return hashlib.sha256(json.dumps(report["materials"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def save(asset, digest):
    LIB.set_metadata_tag(asset, "SSEnemyCandidateVersion", VERSION)
    LIB.set_metadata_tag(asset, "SSEnemyCandidateSourceSHA256", digest)
    assert LIB.save_loaded_asset(asset, only_if_is_dirty=False), asset.get_path_name()


def scalar(material, name, value, x, y):
    node = EDIT.create_material_expression(material, u.MaterialExpressionScalarParameter, x, y)
    node.set_editor_property("parameter_name", name)
    node.set_editor_property("default_value", value)
    return node


def material(item, digest):
    path = material_path(item["name"])
    if LIB.does_asset_exist(path):
        existing = LIB.load_asset(path)
        assert isinstance(existing, u.Material)
        assert LIB.get_metadata_tag(existing, "SSEnemyCandidateVersion") == VERSION
        assert LIB.get_metadata_tag(existing, "SSEnemyCandidateSourceSHA256") == digest, "Changed material requires new reviewed candidate version"
        return existing
    asset = u.AssetToolsHelpers.get_asset_tools().create_asset(path.rsplit("/", 1)[1], BASE + "/Materials", u.Material, u.MaterialFactoryNew())
    assert asset
    color = EDIT.create_material_expression(asset, u.MaterialExpressionVectorParameter, -600, -150)
    color.set_editor_property("parameter_name", "Color")
    color.set_editor_property("default_value", u.LinearColor(*item["base_color"]))
    assert EDIT.connect_material_property(color, "", u.MaterialProperty.MP_BASE_COLOR)
    for name, key, prop, y in [("Metallic", "metallic", u.MaterialProperty.MP_METALLIC, 30),
                               ("Roughness", "roughness", u.MaterialProperty.MP_ROUGHNESS, 160)]:
        node = scalar(asset, name, item[key], -300, y)
        assert EDIT.connect_material_property(node, "", prop)
    if item["emission"]:
        emission = scalar(asset, "Emission", item["emission"], -500, 300)
        product = EDIT.create_material_expression(asset, u.MaterialExpressionMultiply, -200, 300)
        assert EDIT.connect_material_expressions(color, "", product, "A")
        assert EDIT.connect_material_expressions(emission, "", product, "B")
        assert EDIT.connect_material_property(product, "", u.MaterialProperty.MP_EMISSIVE_COLOR)
    # Opaque, single-sided, texture-free PBR. No glow-driven whole-body feedback.
    asset.set_editor_property("two_sided", False)
    EDIT.recompile_material(asset)
    save(asset, digest)
    return asset


def import_mesh(item, materials):
    path = mesh_path(item["name"])
    if LIB.does_asset_exist(path):
        existing = LIB.load_asset(path)
        assert isinstance(existing, u.StaticMesh)
        assert LIB.get_metadata_tag(existing, "SSEnemyCandidateVersion") == VERSION
        assert LIB.get_metadata_tag(existing, "SSEnemyCandidateSourceSHA256") == item["obj_sha256"], "Changed mesh requires new reviewed candidate version"
        return existing
    options = u.FbxImportUI()
    for key, value in {"import_mesh": True, "import_as_skeletal": False, "import_materials": False,
                       "import_textures": False, "mesh_type_to_import": u.FBXImportType.FBXIT_STATIC_MESH}.items():
        options.set_editor_property(key, value)
    data = options.get_editor_property("static_mesh_import_data")
    for key, value in {"combine_meshes": True, "auto_generate_collision": False, "generate_lightmap_u_vs": False,
                       "import_uniform_scale": 1., "convert_scene": False, "force_front_x_axis": False,
                       "normal_import_method": u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS}.items():
        data.set_editor_property(key, value)
    task = u.AssetImportTask()
    for key, value in {"filename": str(SOURCE / (item["name"] + ".obj")), "destination_path": BASE + "/Meshes",
                       "destination_name": path.rsplit("/", 1)[1], "automated": True, "replace_existing": False,
                       "save": False, "options": options, "factory": u.FbxFactory()}.items():
        task.set_editor_property(key, value)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = [LIB.load_asset(p) for p in task.get_editor_property("imported_object_paths")]
    assert len(imported) == 1 and isinstance(imported[0], u.StaticMesh), "Unexpected import products"
    mesh = imported[0]
    assert mesh.get_path_name().split(".")[0] == path, "Unexpected destination; never rename over existing content"
    names = []
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        name = str(slot.get_editor_property("imported_material_slot_name"))
        assert name in materials
        mesh.set_material(index, materials[name])
        names.append(name)
    assert len(names) == 4 and set(names) == set(MATERIALS)
    editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    editor.remove_collisions(mesh)
    assert editor.get_lod_count(mesh) == 1
    for section in range(mesh.get_num_sections(0)):
        editor.enable_section_collision(mesh, False, 0, section)
    body = mesh.get_editor_property("body_setup")
    instance = body.get_editor_property("default_instance")
    instance.set_editor_property("collision_profile_name", "NoCollision")
    instance.set_editor_property("collision_enabled", u.CollisionEnabled.NO_COLLISION)
    body.set_editor_property("default_instance", instance)
    save(mesh, item["obj_sha256"])
    return mesh



def roster(data, migrate=False):
    """Replace only the two legacy names; preserve every authored tuning field."""
    choices = {u.SSWorldKind.PURSUER: ("SM_Pursuer", "SM_PursuerCandidateV1"),
               u.SSWorldKind.FLANKER: ("SM_Flanker", "SM_FlankerCandidateV1")}
    entries = list(data.get_editor_property("enemies"))
    assert len(entries) == 2 and {e.get_editor_property("kind") for e in entries} == set(choices), "Unexpected enemy roster"
    result = []
    replacements = []
    for entry in entries:
        kind = entry.get_editor_property("kind")
        legacy, selected = choices[kind]
        prior = str(entry.get_editor_property("mesh_name"))
        assert prior in (legacy, selected), "Unreviewed custom enemy mesh requires deliberate integration: " + prior
        revised = entry.copy()
        if migrate and prior == legacy:
            revised.set_editor_property("mesh_name", selected)
        restored = revised.copy()
        restored.set_editor_property("mesh_name", prior)
        assert restored.export_text() == entry.export_text(), "Enemy presentation migration changed tuning"
        if not migrate:
            assert prior == selected, "Legacy enemy presentation remains selected"
        replacements.append(revised)
        result.append({"kind": str(kind), "mesh_before": prior,
                       "mesh_after": str(revised.get_editor_property("mesh_name")),
                       "all_other_fields_preserved": True,
                       "tuning_with_prior_mesh_sha256": hashlib.sha256(entry.export_text().encode()).hexdigest()})
    if migrate and any(r["mesh_before"] != r["mesh_after"] for r in result):
        data.set_editor_property("enemies", replacements)
        assert [e.export_text() for e in data.get_editor_property("enemies")] == [e.export_text() for e in replacements]
    return result


def main():
    record = {"status": "FAILED", "errors": [], "engine": u.SystemLibrary.get_engine_version()}
    protected = {p: sha(p) for directory in ("Source", "Config", "Content") for p in (ROOT / directory).rglob("*") if p.is_file()}
    try:
        report = checked_source()
        key = palette_key(report)
        mats = {row["name"]: material(row, key) for row in report["materials"]}
        meshes = [import_mesh(row, mats) for row in report["assets"]]
        assert all(sha(p) == digest for p, digest in protected.items()), "Existing source/config/content changed"
        record.update(status="SEPARATE_ENEMY_ASSETS_AUTHORED_FRESH_VALIDATION_PENDING",
                      material_key=key, source_report_sha256=sha(SOURCE / "SourceReport.json"),
                      meshes=[m.get_path_name() for m in meshes], materials=[m.get_path_name() for m in mats.values()],
                      existing_protected_files_unchanged=len(protected),
                      new_content_assets=[{"path":str(p.relative_to(ROOT)), "bytes":p.stat().st_size, "sha256":sha(p)}
                                          for p in sorted((ROOT / "Content").rglob("*.uasset")) if owned_content(p)],
                      limits=["Separate candidate assets only; original enemy selections remain unchanged.",
                              "Radius150 gameplay sphere is unchanged; source meshes use the existing max-box-extent fit.",
                              "No native appearance, LOD/performance or owner quality acceptance from this import."])
    except Exception as error:
        record["errors"].append(str(error))
        u.log_error("ENEMY_CANDIDATE_IMPORT_FAILED: " + str(error))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "UnrealImport.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    if record["errors"]:
        raise RuntimeError("Enemy candidate import failed; see Saved/Validation/EnemyCandidates/UnrealImport.json")
    u.log("ENEMY_CANDIDATE_IMPORT_OK")


if __name__ == "__main__":
    main()
