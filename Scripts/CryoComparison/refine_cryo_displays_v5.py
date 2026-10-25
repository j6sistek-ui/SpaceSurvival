"""Stage-only v5_3 display reimport and bounded glass/readout refinement.

No engine launch. Default dry run validates current v5 hashes and final source
delta. Apply archives the exact successful v5 receipt and changed packages,
reimports only existing DisplayV5 meshes, edits three DisplayV5 materials,
then promotes the canonical receipt after all protected hashes are verified.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import runpy
import shutil
import traceback

WORK = Path(__file__).resolve().parent
API = runpy.run_path(str(WORK / "apply_cryo_displays_v5.py"))
FIT = API["FIT"]
BASE, STAGE, OUT = (API[key] for key in ("BASE", "STAGE", "OUT"))
require, digest, hashes = (API[key] for key in ("require", "digest", "hashes"))
MANIFEST = OUT / "assembly_displays_v5_3.json"
CANONICAL = WORK / "CryoDisplayV5Apply.json"
MATERIAL_NAMES = ("M_Glass_V5", "M_DisplayLens_V5", "M_VectorReadout_V5")
MAT_ROOT = BASE + "/Materials/DisplayV5/"


def prepare():
    original = json.loads(CANONICAL.read_text(encoding="utf-8"))
    require(original["status"] == "DISPLAY_V5_SAVED_PENDING_VISUAL_REVIEW", "Expected successful original v5 apply")
    require(Path(original["manifest"]).resolve() == API["MANIFEST"].resolve(), "This patch only advances original v5 to v5_3")
    require(digest(original["manifest"]) == original["manifest_sha256"], "Original v5 manifest changed")
    current = hashes()
    require(current == original["native_after_hashes"], "Stage differs from successful native v5 apply")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    old_manifest = json.loads(Path(original["manifest"]).read_text(encoding="utf-8-sig"))
    require([m["id"] for m in manifest["models"]] == list("ABCD"), "Expected all four assemblies")
    require(manifest["shared"] == old_manifest["shared"], "Shared generated artwork changed")
    previous_changes = {row["actor"]: row for row in original["changes"]}
    changes, sources = [], deepcopy(original["protected_source_files"])
    sources[str(MANIFEST)] = {"sha256": digest(MANIFEST)}
    for model, old in zip(manifest["models"], old_manifest["models"]):
        for field in ("source", "textures", "height_cm"):
            require(model[field] == old[field], "Body source/scale changed")
        require(digest(model["source"]) == old["source_sha256"], "Original download changed")
        old_rows = {row["name"]: row for row in old["components"]}
        require(len(model["components"]) == 21 and set(old_rows) == {r["name"] for r in model["components"]}, "Component set changed")
        for row in model["components"]:
            prior = old_rows[row["name"]]
            require(row["role"] == prior["role"], "Role changed")
            file = Path(row["file"]).resolve()
            require(file.is_relative_to(WORK.parent) and file.suffix.lower() == ".obj", "Only D-drive OBJ sources allowed")
            new_sha, old_sha = digest(file), digest(prior["file"])
            sources[str(file)] = {"sha256": new_sha}
            if new_sha == old_sha:
                continue
            actor = model["id"] + "_" + row["name"]
            require(actor in previous_changes and row["role"] in API["ROLE_PATHS"], "Only new v5 display meshes may be reimported: " + actor)
            previous = previous_changes[actor]
            require(previous["source_sha256"] == old_sha, "Native v5 source provenance mismatch")
            require(previous["asset"].startswith(BASE + "/Meshes/DisplayV5/"), "Mesh outside new DisplayV5 namespace")
            changes.append({"actor": actor, "model_id": model["id"], "name": row["name"], "role": row["role"],
                            "asset": previous["asset"], "file": str(file), "source_sha256": new_sha,
                            "previous_file": prior["file"], "previous_source_sha256": old_sha,
                            "package": API["package_path"](previous["asset"])})
    require(changes and set(row["model_id"] for row in changes) == set("ABCD"), "Expected shared refinement across all candidates")
    require(all(digest(path) == info["sha256"] for path, info in sources.items()), "Protected input changed")
    return original, manifest, changes, sources, current


def refine_materials(u, report):
    author = API["V5Author"](u, {}, digest(MANIFEST), report)
    edit = u.MaterialEditingLibrary
    made = []
    for name in MATERIAL_NAMES:
        mat = u.EditorAssetLibrary.load_asset(MAT_ROOT + name)
        require(isinstance(mat, u.Material), "Expected owned v5 material")
        require(mat.get_editor_property("two_sided"), "Expected existing two-sided v5 material")
        if name == "M_VectorReadout_V5":
            old = edit.get_material_property_input_node(mat, u.MaterialProperty.MP_EMISSIVE_COLOR)
            output = edit.get_material_property_input_node_output_name(mat, u.MaterialProperty.MP_EMISSIVE_COLOR)
            require(old is not None, "Readout emission input missing")
            author.prop(author.multiply(mat, old, 1.6, output), "MP_EMISSIVE_COLOR")
            recipe = {"emission_multiplier": 1.6, "existing_nonzero_scan_pulse_preserved": True}
        else:
            lens = name == "M_DisplayLens_V5"
            opacity = edit.get_material_property_input_node(mat, u.MaterialProperty.MP_OPACITY)
            rough = edit.get_material_property_input_node(mat, u.MaterialProperty.MP_ROUGHNESS)
            base = edit.get_material_property_input_node(mat, u.MaterialProperty.MP_BASE_COLOR)
            specular = edit.get_material_property_input_node(mat, u.MaterialProperty.MP_SPECULAR)
            require(isinstance(opacity, u.MaterialExpressionCustom) and isinstance(rough, u.MaterialExpressionCustom), "Unexpected v5 glass graph")
            require(isinstance(base, u.MaterialExpressionConstant3Vector) and isinstance(specular, u.MaterialExpressionConstant), "Unexpected glass constants")
            require(mat.get_editor_property("translucency_lighting_mode") == u.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING,
                    "Forward surface lighting missing")
            old_opacity = "return 0.045+F*0.30+Haze*0.008;" if lens else "return 0.075+F*0.34+Haze*0.020;"
            require(opacity.get_editor_property("code") == old_opacity, "Glass already refined or edited")
            opacity.set_editor_property("code", "return 0.065+F*0.30+Haze*0.012;" if lens else "return 0.155+F*0.32+Haze*0.045;")
            rough.set_editor_property("code", "return 0.055+Haze*0.030;" if lens else "return 0.110+Haze*0.070;")
            base.set_editor_property("constant", u.LinearColor(*((.10, .20, .24, 1) if lens else (.14, .26, .30, 1))))
            specular.set_editor_property("r", .65)
            uv = author.node(mat, "MaterialExpressionTextureCoordinate", coordinate_index=0)
            if lens:
                fresnel = author.node(mat, "MaterialExpressionFresnel", exponent=3.0, base_reflect_fraction=0.0)
                camera = author.node(mat, "MaterialExpressionCameraVectorWS")
                glint = author.custom(mat,
                    "float center=0.32+Camera.x*0.14+Camera.y*0.07; float d=UV.x+UV.y*0.22-center; float band=exp(-d*d*95.0); return 0.006+0.05*band*(0.15+0.85*F);",
                    {"UV": uv, "F": fresnel, "Camera": camera})
                author.prop(author.multiply(mat, author.color(mat, (.40, .70, 1.0)), glint), "MP_EMISSIVE_COLOR")
            else:
                haze = author.custom(mat,
                    "return 0.70+0.18*sin(UV.x*29.0+sin(UV.y*13.0))*sin(UV.y*37.0)+0.10*sin(UV.x*11.0-UV.y*19.0);", {"UV": uv})
                author.prop(author.multiply(mat, author.color(mat, (.045, .12, .16)), haze), "MP_EMISSIVE_COLOR")
            recipe = {"face_opacity_approx": .071 if lens else .1775, "specular": .65,
                      "soft_view_dependent_lens_glint": lens, "subtle_cold_surface_scatter": not lens,
                      "forward_surface_specular_preserved": True, "depth_test_enabled": not bool(mat.get_editor_property("disable_depth_test"))}
        for key, value in {"CryoAuthoringVersion": "CryoVectorDisplaysV5_3", "CryoManifestSHA256": digest(MANIFEST),
                           "CryoAcceptance": "PENDING_NATIVE_GLASS_AND_FONT_REVIEW"}.items():
            u.EditorAssetLibrary.set_metadata_tag(mat, key, value)
        author.compile(mat)
        made.append(mat)
        report["material_refinements"].append({"asset": mat.get_path_name(), **recipe})
    return made


def reimport_mesh(u, row, material, manifest_hash):
    folder, name = row["asset"].rsplit("/", 1)
    options = u.FbxImportUI()
    for key, value in {"automated_import_should_detect_type": False, "import_mesh": True, "import_as_skeletal": False,
                       "import_materials": False, "import_textures": False, "mesh_type_to_import": u.FBXImportType.FBXIT_STATIC_MESH}.items():
        options.set_editor_property(key, value)
    data = options.get_editor_property("static_mesh_import_data")
    for key, value in {"combine_meshes": True, "auto_generate_collision": False, "generate_lightmap_u_vs": False,
                       "build_nanite": False, "import_uniform_scale": 1., "convert_scene": False, "convert_scene_unit": False,
                       "force_front_x_axis": False, "normal_import_method": u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS}.items():
        data.set_editor_property(key, value)
    task = u.AssetImportTask()
    for key, value in {"filename": row["file"], "destination_path": folder, "destination_name": name, "automated": True,
                       "replace_existing": True, "save": False, "options": options, "factory": u.FbxFactory()}.items():
        task.set_editor_property(key, value)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = list(task.get_editor_property("imported_object_paths"))
    require(len(paths) == 1 and paths[0].split(".")[0] == row["asset"], "Unexpected reimport target")
    mesh = u.EditorAssetLibrary.load_asset(paths[0])
    require(isinstance(mesh, u.StaticMesh) and mesh.get_num_sections(0) == 1 and len(mesh.get_editor_property("static_materials")) == 1,
            "Unexpected mesh/material section result")
    mesh.set_material(0, material)
    editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    editor.remove_collisions(mesh)
    editor.enable_section_collision(mesh, False, 0, 0)
    for key, value in {"CryoAuthoringVersion": "CryoVectorDisplaysV5_3", "CryoManifestSHA256": manifest_hash,
                       "CryoRole": row["role"], "CryoModelID": row["model_id"], "CryoSourceSHA256": row["source_sha256"],
                       "CryoAcceptance": "PENDING_NATIVE_GLASS_AND_FONT_REVIEW"}.items():
        u.EditorAssetLibrary.set_metadata_tag(mesh, key, value)
    return mesh


def main(apply=False):
    report = {"status": "FAILED", "apply": apply, "utc": datetime.now(timezone.utc).isoformat(), "errors": [],
              "manifest": str(MANIFEST), "materials": [], "material_refinements": [],
              "limits": ["Native A trial is required; material compilation alone does not prove visual improvement.",
                         "No freeze, Niagara, sequence, body, owner-project, global lighting or config changes."]}
    receipt = WORK / ("CryoDisplayV5Refine.json" if apply else "CryoDisplayV5RefinePlan.json")
    u, allowed = None, False
    try:
        original, manifest, changes, sources, before = prepare()
        manifest_hash = digest(MANIFEST)
        material_packages = [API["package_path"](MAT_ROOT + name) for name in MATERIAL_NAMES]
        expected = sorted([row["package"] for row in changes] + material_packages)
        require(len(expected) == len(set(expected)) and set(expected).issubset(original["added_packages"]), "Only new v5 packages may be edited")
        report.update(manifest_sha256=manifest_hash, changes=changes, planned_changed_packages=expected, native_before_hashes=before)
        if not apply:
            report["status"] = "DRY_RUN_READY"
            return report
        import unreal as u
        require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve() == STAGE.resolve(), "Only isolated CryoStage is allowed")
        require(not u.EditorLevelLibrary.get_pie_worlds(False), "Refusing active PIE")
        allowed = True
        backup = WORK / ("pre_display_v5_refine_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
        backup.mkdir(exist_ok=False)
        archived = backup / CANONICAL.name
        shutil.copy2(CANONICAL, archived)
        require(digest(archived) == digest(CANONICAL), "Canonical receipt archive differs")
        report.update(original_apply_archive=str(archived), original_apply_archive_sha256=digest(archived), backup_directory=str(backup))
        for relative in expected:
            source, dest = STAGE / relative, backup / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            require(digest(dest) == before[relative], "Package backup differs")
        changed_assets = refine_materials(u, report)
        for row in changes:
            old_mesh = u.EditorAssetLibrary.load_asset(row["asset"])
            require(isinstance(old_mesh, u.StaticMesh), "Owned v5 mesh missing")
            require(u.EditorAssetLibrary.get_metadata_tag(old_mesh, "CryoSourceSHA256") == row["previous_source_sha256"], "Native mesh source provenance differs")
            material = old_mesh.get_material(0)
            require(material and material.get_path_name().startswith(MAT_ROOT), "Mesh material outside owned v5 namespace")
            mesh = reimport_mesh(u, row, material, manifest_hash)
            bounds = mesh.get_bounds()
            row["native_bounds_cm"] = {"origin": list(bounds.origin.to_tuple()), "extent": list(bounds.box_extent.to_tuple())}
            changed_assets.append(mesh)
        for asset in changed_assets:
            require(u.EditorAssetLibrary.save_loaded_asset(asset, False), "V5 refinement save failed")
        after = hashes()
        changed = sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))
        require(set(before) == set(after) and changed == expected, "Unexpected native package changes")
        require(all(digest(path) == info["sha256"] for path, info in sources.items()), "Protected input changed during apply")
        report.update(status="DISPLAY_V5_REFINEMENT_SAVED_PENDING_NATIVE_REVIEW", native_after_hashes=after,
                      changed_packages=changed, map_unchanged=True, old_v4_4_packages_unchanged=True,
                      protected_source_files=sources, canonical_receipt_promoted=False)
        # Canonical comparison remains v4_4 -> finalv5 so guarded owner adoption
        # still sees only new asset packages and its one original map replacement.
        canonical = deepcopy(original)
        current_rows = {model["id"] + "_" + row["name"]: row for model in manifest["models"] for row in model["components"]}
        deltas = {row["actor"]: row for row in changes}
        for row in canonical["changes"]:
            current = current_rows[row["actor"]]
            row.update(file=current["file"], source_sha256=digest(current["file"]))
            if row["actor"] in deltas:
                row["native_bounds_cm"] = deltas[row["actor"]]["native_bounds_cm"]
        canonical.update(utc=datetime.now(timezone.utc).isoformat(), manifest=str(MANIFEST), manifest_sha256=manifest_hash,
                         native_after_hashes=after, protected_source_files=sources, revision="v5_3",
                         original_apply_archive=str(archived), original_apply_archive_sha256=digest(archived),
                         refinement_receipt=str(receipt), refinement_native_before_hashes=before,
                         refinement_changed_packages=changed, material_refinements=report["material_refinements"])
        canonical["materials"] = [row for row in canonical["materials"] if row["asset"].split(".")[0] not in {MAT_ROOT + n for n in MATERIAL_NAMES}] + report["materials"]
        report["canonical_receipt_promoted"] = True
        report["canonical_receipt"] = str(CANONICAL)
        receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        canonical["refinement_receipt_sha256"] = digest(receipt)
        temporary = CANONICAL.with_suffix(".next.json")
        temporary.write_text(json.dumps(canonical, indent=2) + "\n", encoding="utf-8")
        temporary.replace(CANONICAL)
        return report
    except Exception:
        report["status"] = "FAILED"
        report["errors"].append(traceback.format_exc())
        if u:
            u.log_error(report["errors"][-1])
        return report
    finally:
        receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("CRYO_DISPLAY_V5_REFINE_RESULT " + json.dumps({"status": report["status"], "receipt": str(receipt)}), flush=True)
        if u and allowed:
            u.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main(False)
