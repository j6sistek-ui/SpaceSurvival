"""Read-only final Cryo assembly metrics; writes only work/cryo-costs-final.json.

Uses the already installed Pillow for image inspection. No Unreal process,
asset imports, source changes, cook, GPU allocation or performance benchmark.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from PIL import Image


WORK = Path(__file__).resolve().parent
OUTPUT = WORK / "cryo-costs-final.json"
MANIFEST = WORK.parent / "outputs/Cryo_Comparison/assembly_holo_consoles.json"
CONTENT = WORK / "CryoStage/Content"
NAMESPACE = CONTENT / "SpaceSurvival/CryoComparison"
MIB = 1024 * 1024
BUILD_DIMS = {"status": [1024, 2048], "console": [2048, 1024],
              "holo": [1024, 2048], "frost": [1024, 2048], "mist": [1024, 1024]}


def sha(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * MIB), b""):
            result.update(chunk)
    return result.hexdigest()


def size_info(path):
    path = Path(path).resolve()
    count = path.stat().st_size
    return {"path": str(path), "bytes": count, "MiB": round(count / MIB, 6)}


def native_file(asset):
    package = asset.split(".")[0]
    assert package.startswith("/Game/")
    path = CONTENT / (package[len("/Game/"):] + ".uasset")
    assert path.is_file(), path
    return path


def aggregate_files(paths):
    rows = [size_info(path) for path in sorted(set(Path(p).resolve() for p in paths))]
    total = sum(row["bytes"] for row in rows)
    return {"files": rows, "count": len(rows), "bytes": total, "MiB": round(total / MIB, 6)}


def bc_estimate(width, height, fmt):
    block_bytes = {"BC1": 8, "BC3": 16, "BC5": 16}[fmt]
    rows = []
    while True:
        count = max(1, (width + 3) // 4) * max(1, (height + 3) // 4) * block_bytes
        rows.append({"width": width, "height": height, "bytes": count})
        if width == height == 1:
            break
        width, height = max(1, width // 2), max(1, height // 2)
    total = sum(row["bytes"] for row in rows)
    return {"status": "ESTIMATE_NOT_MEASURED_GPU_ALLOCATION", "format": fmt,
            "nominal_bits_per_pixel": 4 if fmt == "BC1" else 8,
            "full_mip_count": len(rows), "bytes": total, "MiB": round(total / MIB, 6),
            "mips": rows}


def image_info(path, role, build_dims=None):
    path = Path(path).resolve()
    with Image.open(path) as im:
        width, height = im.size
        has_alpha = "A" in im.getbands() or "transparency" in im.info
        alpha_extrema = list(im.convert("RGBA").getchannel("A").getextrema()) if has_alpha else [255, 255]
        opaque = alpha_extrema == [255, 255]
        result = {**size_info(path), "sha256": sha(path), "format": im.format,
                  "source_width": width, "source_height": height, "source_mode": im.mode,
                  "has_alpha_channel_or_transparency": has_alpha,
                  "alpha_extrema_0_255": alpha_extrema, "alpha_fully_opaque": opaque}
    dims = build_dims or [width, height]
    fmt = "BC5" if role == "normal" else "BC1" if role == "orm" or opaque else "BC3"
    result["estimate_build_dimensions"] = dims
    result["estimated_standard_bc_full_mips"] = bc_estimate(*dims, fmt)
    return result


def obj_info(path):
    vertices = texcoords = normals = faces = triangles = 0
    referenced = set()
    corners = set()
    material_names = set()
    nontriangles = 0
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            fields = line.split()
            if not fields:
                continue
            if fields[0] == "v":
                vertices += 1
            elif fields[0] == "vt":
                texcoords += 1
            elif fields[0] == "vn":
                normals += 1
            elif fields[0] == "usemtl":
                material_names.add(" ".join(fields[1:]))
            elif fields[0] == "f":
                faces += 1
                n = len(fields) - 1
                assert n >= 3, (path, line)
                triangles += n - 2
                nontriangles += n != 3
                for corner in fields[1:]:
                    index = int(corner.split("/")[0])
                    referenced.add(index if index > 0 else vertices + index + 1)
                    corners.add(corner)
    return {**size_info(path), "sha256": sha(path), "vertices_position_records": vertices,
            "referenced_position_records": len(referenced), "texcoord_records": texcoords,
            "normal_records": normals, "distinct_position_uv_normal_corner_tokens": len(corners),
            "faces": faces, "triangles": triangles, "nontriangle_faces": nontriangles,
            "obj_material_names": sorted(material_names),
            "vertex_note": "OBJ position records are not measured Unreal render vertices; UV/normal splits can change GPU vertex count."}


def import_warning_evidence():
    # Use each successful author run once, not duplicate console/backup copies.
    results = {model_id: [] for model_id in "ABCD"}
    for path in (WORK / "CryoAuthor2.log", WORK / "CryoConsoleUpgrade.log"):
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            match = re.search(r"FBXImport: Warning: (SM_([ABCD])_\S+) has some (.+)", line)
            if match:
                results[match[2]].append({"log": str(path), "line": number,
                                          "mesh": match[1], "message": match[3].strip()})
    return results


def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    baseline_path = WORK / "glb-baseline.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8-sig"))
    author_path = WORK / "CryoFinalAuthor.json"
    author = json.loads(author_path.read_text(encoding="utf-8-sig"))
    refinement_path = WORK / "CryoNativeRefinement.json"
    refinement = json.loads(refinement_path.read_text(encoding="utf-8-sig"))
    console_path = WORK / "CryoConsoleUpgrade.json"
    console = json.loads(console_path.read_text(encoding="utf-8-sig"))
    breathing_path = WORK / "CryoBreathingLights.json"
    breathing = json.loads(breathing_path.read_text(encoding="utf-8-sig"))
    assert author["status"].startswith("AUTHORED_SAVED_")
    assert refinement["status"].startswith("NATIVE_REFINEMENT_SAVED_")
    assert console["status"].startswith("CONSOLE_GLASS_HUD_SAVED_")
    assert breathing["status"].startswith("SAVED_NATIVE_LOOP_")
    assert author["counts"]["active_mesh_actors"] == len(author["meshes"]) == 76
    by_hash = {row["sha256"]: row for row in baseline["assets"]}
    saved_meshes = {(row["model_id"], row["component"]): row for row in author["meshes"]}
    warnings = import_warning_evidence()
    input_hashes = {str(path): sha(path) for path in (MANIFEST, baseline_path, author_path, refinement_path,
        console_path, breathing_path, WORK / "cryo-costs.json")}
    report = {"measured_utc": datetime.now(timezone.utc).isoformat(),
        "status": "STATIC_METRICS_ONLY_NO_RANKING_OR_RUNTIME_BENCHMARK",
        "method": {
            "geometry": "Counts read from all finished component OBJ files; native LOD0 section counts from successful author receipt.",
            "native_bytes": "Actual uncooked .uasset file lengths, not resident RAM/VRAM, cooked package size or load time.",
            "texture_estimate": "All mips down to 1x1; each dimension rounded up to 4x4 blocks, minimum one block. BC1 8 bytes/block for opaque color and ORM; BC3 16 bytes/block for color with nonopaque alpha; BC5 16 bytes/block for normal.",
            "format_authority": "Installed UE5.8 Engine/Source/Runtime/Core/Private/Misc/PixelFormat.cpp:39,41,57.",
            "excluded_from_gpu_estimate": ["Niagara donor texture formats and residency", "material shader storage", "mesh buffers", "render targets", "translucency overdraw", "volumetric grid", "particle buffers", "driver alignment", "streaming policy"],
            "no_runtime_claim": "No engine launch, cook, packaged FPS, GPU timing, draw-call measurement or performance ranking was performed.",
            "file_size_note": "GLB disk bytes include compressed image media; this does not assert Draco/meshopt compressed geometry.",
            "shared_accounting": "Shared texture/native effects bytes counted once in common; do not multiply by four. Per-model rows exclude common Niagara references.",
            "active_recovery_accounting": "Active per-model meshes/materials follow final manifest and final native author receipt. Eight superseded console meshes, M_Console and T_Cryo_Console are classified as recovery. Other namespace materials/effects/sequence are retained scene support by final authoring records; no new runtime dependency-registry probe was run."},
        "inputs": {"manifest": str(MANIFEST), "baseline": str(baseline_path),
                   "native_author_receipt": str(author_path), "native_refinement_receipt": str(refinement_path),
                   "console_upgrade_receipt": str(console_path), "breathing_lights_receipt": str(breathing_path),
                   "preserved_prior_metrics": str(WORK / "cryo-costs.json")},
        "models": [], "common": {}}
    model_owned_files = set()
    for model in manifest["models"]:
        model_id = model["id"]
        source = Path(model["source"]).resolve()
        source_hash = sha(source)
        assert source_hash == model["source_sha256"]
        original = by_hash[source_hash]
        input_hashes[str(source)] = source_hash
        components = []
        roles = defaultdict(lambda: {"components": 0, "vertices_position_records": 0, "triangles": 0, "native_lod0_material_sections": 0})
        mesh_files = []
        material_refs = set()
        for component in model["components"]:
            row = {"name": component["name"], "role": component["role"], **obj_info(component["file"])}
            assert row["triangles"] == component["triangles"]
            saved = saved_meshes[(model_id, component["name"])]
            assert saved["sections_lod0"] == 1 and saved["lod_count"] == 1
            row["native_lod0_material_sections"] = saved["sections_lod0"]
            row["native_lod_count"] = saved["lod_count"]
            row["native_mesh_uasset"] = size_info(native_file(saved["asset"]))
            row["material_reference"] = saved["material"]
            input_hashes[row["path"]] = row["sha256"]
            mesh_files.append(row["native_mesh_uasset"]["path"])
            material_refs.add(saved["material"])
            for key in ("vertices_position_records", "triangles", "native_lod0_material_sections"):
                roles[component["role"]][key] += row[key]
            roles[component["role"]]["components"] += 1
            components.append(row)
        assert len(components) == 19
        pbr = {role: image_info(path, role) for role, path in model["textures"].items()}
        texture_files = []
        for role, row in pbr.items():
            row["native_texture_uasset"] = size_info(NAMESPACE / "Textures" / ("T_" + model_id + "_" + role + ".uasset"))
            texture_files.append(row["native_texture_uasset"]["path"])
            input_hashes[row["path"]] = row["sha256"]
            assert row["sha256"] in {image["sha256"] for image in original["images"]}, "Extracted body texture diverged from source"
        material_file = NAMESPACE / "Materials" / ("M_" + model_id + "_Body.uasset")
        owned = mesh_files + texture_files + [material_file]
        model_owned_files.update(Path(path).resolve() for path in owned)
        gpu_bytes = sum(row["estimated_standard_bc_full_mips"]["bytes"] for row in pbr.values())
        report["models"].append({"id": model_id, "label": model["label"],
            "original": {"path": str(source), "sha256": source_hash, "source_hash_unchanged": True,
                "glb_file_bytes": original["bytes"], "glb_file_MiB": round(original["bytes"] / MIB, 6),
                "vertices": original["counts"]["vertices_primitive_sum"],
                "triangles": original["counts"]["triangles_primitive_sum"]},
            "finished_geometry": {"components": components, "by_role": dict(roles),
                "component_count": len(components), "role_count": len(roles),
                "vertices_position_records": sum(row["vertices_position_records"] for row in components),
                "triangles": sum(row["triangles"] for row in components),
                "added_triangles": sum(row["triangles"] for row in components) - original["counts"]["triangles_primitive_sum"],
                "native_lod0_material_sections": sum(row["native_lod0_material_sections"] for row in components),
                "distinct_referenced_materials": len(material_refs),
                "section_note": "19 active static mesh sections; actual rendering passes/draw calls and particle draws are not measured."},
            "pbr_source_images": pbr,
            "estimated_body_texture_gpu_full_mips": {"status": "ESTIMATE_NOT_MEASURED_GPU_ALLOCATION", "bytes": gpu_bytes, "MiB": round(gpu_bytes / MIB, 6)},
            "native_uncooked": {"meshes": aggregate_files(mesh_files), "body_textures": aggregate_files(texture_files),
                "body_material": size_info(material_file), "model_owned_total": aggregate_files(owned)},
            "import_warning_evidence": warnings[model_id],
            "warning_note": "No matching warning in this successful import log does not prove defect-free shading."})
    shared = {}
    for role, path in manifest["shared"].items():
        if role == "console":
            native = native_file(console["textures"][0]["asset"])
            assert Path(console["textures"][0]["source"]).resolve() == Path(path).resolve()
            build_evidence = "Successful ConsoleUpgrade import uses author_cryo_unreal.py Shared Console resize_during_build_x/y=2048/1024; source pixels unchanged."
        else:
            native = NAMESPACE / "Textures" / ("T_Cryo_" + role.title() + ".uasset")
            refinement_row = next(row for row in refinement["textures"] if row["asset"].split(".")[0].endswith(native.stem))
            assert refinement_row["build_size"] == BUILD_DIMS[role]
            build_evidence = "Native refinement receipt; original source pixels preserved."
        shared[role] = image_info(path, role, BUILD_DIMS[role])
        shared[role]["native_texture_uasset"] = size_info(native)
        shared[role]["build_dimensions_evidence"] = build_evidence
        input_hashes[shared[role]["path"]] = shared[role]["sha256"]
    assert shared["console"]["estimated_standard_bc_full_mips"]["format"] == "BC3"
    all_native_files = set(path.resolve() for path in NAMESPACE.rglob("*.uasset"))
    recovery_files = {NAMESPACE / "Meshes" / model_id / ("SM_" + model_id + "_Console_" + index + ".uasset")
                      for model_id in "ABCD" for index in ("1", "2")}
    recovery_files.update((NAMESPACE / "Materials/M_Console.uasset", NAMESPACE / "Textures/T_Cryo_Console.uasset"))
    recovery_files = {path.resolve() for path in recovery_files}
    assert recovery_files <= all_native_files and not (recovery_files & model_owned_files)
    common_files = all_native_files - model_owned_files - recovery_files
    donor_files = list((CONTENT / "NiagaraExamples").rglob("*.uasset"))
    shared_gpu_bytes = sum(row["estimated_standard_bc_full_mips"]["bytes"] for row in shared.values())
    report["common"] = {"shared_images": shared,
        "estimated_shared_texture_gpu_full_mips": {"status": "ESTIMATE_NOT_MEASURED_GPU_ALLOCATION", "bytes": shared_gpu_bytes, "MiB": round(shared_gpu_bytes / MIB, 6)},
        "namespace_active_shared_and_scene_support_uassets": aggregate_files(common_files),
        "niagara_donor_stored_uncooked_dependencies": aggregate_files(donor_files),
        "donor_reference_limit": "Original copied 16-package closure retained. Bounded Niagara now overrides the sprite material/cutout; exact final live subset of donor packages was not re-probed, so these bytes describe stored dependency support, not per-chamber or resident runtime cost.",
        "comparison_maps": aggregate_files(NAMESPACE.rglob("*.umap")),
        "native_effect_instances": {"niagara_system_actors": author["counts"]["niagara_actors"],
            "local_fog_volumes": author["counts"]["local_fog_volumes"], "global_exponential_volumetric_fog": 1,
            "added_shadowless_point_lights": breathing["plan"]["new_point_lights"],
            "modified_existing_point_lights": breathing["plan"]["modified_point_lights"],
            "animated_intensity_tracks": len(breathing["tracks"]), "loop_period_seconds": breathing["period_seconds"],
            "all_eight_animated_lights_cast_shadows": any(row["cast_shadows"] for row in breathing["saved_resting_lights"]),
            "sequence_asset": breathing["sequence"], "light_effect_evidence": str(breathing_path),
            "runtime_cost": "UNMEASURED; identical per-chamber effect setup is not a GPU timing or FPS result."},
        "effect_instance_evidence": str(author_path),
        "niagara_gpu_texture_cost": "UNMEASURED; not included in standard BC estimate, and shared rather than charged four times."}
    report["stored_recovery"] = {"reason": "Eight original console meshes plus their old opaque console material and texture were retained after replacing their actors.",
        "namespace_uncooked_uassets": aggregate_files(recovery_files),
        "excluded_from_active_texture_gpu_estimate": True, "no_deletion_performed": True}
    report["totals"] = {"triangles_all_four_static_assemblies": sum(row["finished_geometry"]["triangles"] for row in report["models"]),
        "static_material_sections_all_four": sum(row["finished_geometry"]["native_lod0_material_sections"] for row in report["models"]),
        "namespace_stored_uassets_including_recovery": aggregate_files(all_native_files),
        "namespace_active_and_scene_support_uassets": aggregate_files(all_native_files - recovery_files),
        "estimated_body_plus_shared_texture_gpu_full_mips_bytes": sum(row["estimated_body_texture_gpu_full_mips"]["bytes"] for row in report["models"]) + shared_gpu_bytes}
    report["totals"]["estimated_body_plus_shared_texture_gpu_full_mips_MiB"] = round(report["totals"]["estimated_body_plus_shared_texture_gpu_full_mips_bytes"] / MIB, 6)
    changed = [path for path, value in input_hashes.items() if sha(path) != value]
    assert not changed, changed
    report["read_only_validation"] = {"input_hash_count": len(input_hashes), "all_inputs_unchanged": True, "prior_metrics_json_unchanged": True,
                                      "source_glb_hashes_match_baseline": True, "engine_launched": False}
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "models": [{"id": row["id"], "original_triangles": row["original"]["triangles"],
        "finished_triangles": row["finished_geometry"]["triangles"], "finished_obj_vertices": row["finished_geometry"]["vertices_position_records"],
        "sections": row["finished_geometry"]["native_lod0_material_sections"], "body_texture_estimate_MiB": row["estimated_body_texture_gpu_full_mips"]["MiB"],
        "native_model_MiB": row["native_uncooked"]["model_owned_total"]["MiB"], "import_warnings": len(row["import_warning_evidence"])} for row in report["models"]],
        "shared_texture_estimate_MiB": shared_gpu_bytes / MIB, "all_input_hashes_unchanged": not changed}, indent=2))


if __name__ == "__main__":
    main()
