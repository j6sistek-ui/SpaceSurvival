"""Read-only Cryo assembly metrics; defaults to work/cryo-costs-final.json.

Uses the already installed Pillow for image inspection. No Unreal process,
asset imports, source changes, cook, GPU allocation or performance benchmark.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import argparse
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


def native_file(asset, content=CONTENT):
    package = asset.split(".")[0]
    assert package.startswith("/Game/")
    path = content / (package[len("/Game/"):] + ".uasset")
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


def import_warning_evidence(extra_logs=()):
    # Use each successful author run once, not duplicate console/backup copies.
    results = {model_id: [] for model_id in "ABCD"}
    for path in (WORK / "CryoAuthor2.log", WORK / "CryoConsoleUpgrade.log", *extra_logs):
        if not path.is_file():
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            match = re.search(r"FBXImport: Warning: (SM_([ABCD])_\S+) has some (.+)", line)
            if match:
                results[match[2]].append({"log": str(path), "line": number,
                                          "mesh": match[1], "message": match[3].strip()})
    return results


def author_meshes(author, manifest, manifest_path, author_path, content, native_current_hashes=None):
    """Resolve a full author inventory or the saved FitV4 delta without guessing assets."""
    receipts = [author_path]
    superseded = set()
    delta = "changes" in author and "meshes" not in author
    if delta and author.get("status") in ("TAIL_GLASS_FIT_SAVED_PENDING_REVIEW", "REAR_CONSOLE_SAVED_PENDING_VISUAL_REVIEW"):
        assert author.get("apply") is True and not author.get("errors")
        assert author["manifest_sha256"] == sha(manifest_path)
        assert author["map_materials_other_meshes_unchanged"] and author["protected_inputs_unchanged"]
        rear = author["status"] == "REAR_CONSOLE_SAVED_PENDING_VISUAL_REVIEW"
        expected_changes = ({("D", "Console_1_"+suffix) for suffix in ("Backing", "Glass", "HUD", "Frame")}
                            if rear else {("C", "Glass"), ("C", "Frost")})
        assert {(row["model_id"], row["name"]) for row in author["changes"]} == expected_changes
        base_path = WORK / ("CryoTailFitApply.json" if rear else "CryoFitV4Apply.json")
        base = json.loads(base_path.read_text(encoding="utf-8-sig"))
        base_manifest_path = Path(manifest["source_manifest"])
        base_manifest = json.loads(base_manifest_path.read_text(encoding="utf-8-sig"))
        saved, counts, base_receipts, superseded, _ = author_meshes(
            base, base_manifest, base_manifest_path, base_path, content, native_current_hashes or author["native_after_hashes"])
        receipts.extend([*base_receipts, base_manifest_path])
        for change in author["changes"]:
            key = (change["model_id"], change["name"])
            previous = saved[key]
            assert previous["asset"].split(".")[0] == change["asset"].split(".")[0]
            assert sha(previous["source"]) == change["previous_source_sha256"]
            assert sha(change["file"]) == change["source_sha256"]
            assert sha(native_file(change["asset"], content)) == (native_current_hashes or author["native_after_hashes"])[change["package"]]
            saved[key] = {**previous, "source": change["file"], "source_sha256": change["source_sha256"],
                          "sections_lod0": change["sections_lod0"],
                          "native_count_evidence": "Guarded corrective reimport preserves the same native asset and records one LOD0 section."}
    elif delta:
        assert author["status"].startswith("FIT_V4_SAVED_"), "Fit receipt is not saved successfully"
        assert author["manifest_sha256"] == sha(manifest_path), "Fit receipt belongs to another manifest"
        assert author["unchanged_original_bodies"] and author["unchanged_materials_lights_niagara_sequence"]
        assert not author.get("errors"), author.get("errors")
        baseline_path = WORK / "CryoFinalAuthor.json"
        baseline = json.loads(baseline_path.read_text(encoding="utf-8-sig"))
        assert baseline["status"].startswith("AUTHORED_SAVED_")
        receipts.append(baseline_path)
        saved = {(row["model_id"], row["component"]): dict(row) for row in baseline["meshes"]}
        changed = set()
        for change in author["changes"]:
            key = (change["model_id"], change["name"])
            assert key in saved and key not in changed, key
            changed.add(key)
            previous = saved[key]
            assert previous["asset"].split(".")[0] == change["previous_mesh"].split(".")[0], key
            assert sha(previous["source"]) == change["previous_source_sha256"], key
            assert sha(change["file"]) == change["source_sha256"], key
            superseded.add(native_file(change["previous_mesh"], content).resolve())
            asset_file = native_file(change["asset"], content)
            package_key = "Content\\" + change["asset"][len("/Game/"):].replace("/", "\\") + ".uasset"
            assert sha(asset_file) == (native_current_hashes or author["native_after_hashes"])[package_key], "Native FitV4 package changed"
            saved[key] = {**previous, "asset": change["asset"], "source": change["file"],
                          "source_sha256": change["source_sha256"], "lod_count": None,
                          "sections_lod0": 1,
                          "native_count_evidence": "Successful FitV4 import requires one LOD0 section; LOD count is not recorded in this delta receipt."}
        counts = baseline["counts"]
    else:
        assert author["status"].startswith(("AUTHORED_SAVED_", "FIT_V4_SAVED_"))
        saved = {(row["model_id"], row["component"]): dict(row) for row in author["meshes"]}
        assert len(saved) == len(author["meshes"]), "Duplicate native mesh inventory entries"
        counts = author["counts"]
    expected = {(model["id"], row["name"]) for model in manifest["models"] for row in model["components"]}
    assert set(saved) == expected, "Native inventory and manifest components differ"
    assert counts["active_mesh_actors"] == len(saved) == 76
    for model in manifest["models"]:
        for row in model["components"]:
            mesh = saved[(model["id"], row["name"])]
            assert mesh["role"] == row["role"], row["name"]
            source_hash = sha(mesh["source"])
            assert source_hash == sha(row["file"]), "Native mesh source differs from manifest: " + row["name"]
            if "source_sha256" in mesh:
                assert source_hash == mesh["source_sha256"]
    return saved, counts, receipts, superseded, delta


def current_stage_overrides(manifest_path, content, saved_meshes):
    """Apply recorded actor overrides only across an exact, current package chain."""
    statuses = {"CryoFitV4Apply.json": "FIT_V4_SAVED_PENDING_MULTIVIEW_REVIEW",
                "CryoFreezeFX.json": "FREEZE_MATERIAL_AND_JET_SAVED_PENDING_INTERACTION_RUNTIME",
                "CryoFit360Lighting.json": "REAR_FILL_SAVED_PENDING_360_REVIEW",
                "CryoInteractionApply.json": "INTERACTION_MAP_SAVED_PENDING_RUNTIME"}
    for name, status in {"CryoFreezeMasked.json": "MASKED_FREEZE_SAVED_PENDING_VISUAL_REVIEW",
                         "CryoTailFitApply.json": "TAIL_GLASS_FIT_SAVED_PENDING_REVIEW",
                         "CryoJetContainment.json": "INWARD_JET_SAVED_PENDING_VISUAL_REVIEW",
                         "CryoRearConsoleApply.json": "REAR_CONSOLE_SAVED_PENDING_VISUAL_REVIEW"}.items():
        if (WORK / name).is_file():
            statuses[name] = status
    paths = [WORK / name for name in statuses]
    receipts = {}
    for path in paths:
        row = json.loads(path.read_text(encoding="utf-8-sig"))
        assert row.get("apply") is True and row.get("status") == statuses[path.name], path.name
        assert not row.get("errors"), path.name
        for key in ("native_before_hashes", "native_after_hashes"):
            row[key] = {name.replace("\\", "/"): value for name, value in row[key].items()}
        receipts[path.name] = row
    fit = receipts["CryoFitV4Apply.json"]
    final_manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    base_manifest_path = manifest_path
    current_manifest = final_manifest
    while current_manifest["version"] != "v4_2_fitted_enclosures":
        receipt_name = {"v4_3_C_tail_clearance": "CryoTailFitApply.json",
                        "v4_4_D_rear_console": "CryoRearConsoleApply.json"}[current_manifest["version"]]
        assert receipts[receipt_name]["manifest_sha256"] == sha(base_manifest_path)
        base_manifest_path = Path(current_manifest["source_manifest"])
        current_manifest = json.loads(base_manifest_path.read_text(encoding="utf-8-sig"))
    assert fit["manifest_sha256"] == sha(base_manifest_path), "Native chain belongs to another base manifest"
    chain = ["CryoFitV4Apply.json"]
    remaining = set(receipts) - set(chain)
    while remaining:
        for name in sorted(remaining):
            row = receipts[name]
            if row["native_after_hashes"] == receipts[chain[0]]["native_before_hashes"]:
                chain.insert(0, name)
            elif row["native_before_hashes"] == receipts[chain[-1]]["native_after_hashes"]:
                chain.append(name)
            else:
                continue
            remaining.remove(name)
            break
        else:
            raise AssertionError("Disconnected native authoring receipts: " + str(sorted(remaining)))
    current = {"Content/" + path.relative_to(content).as_posix(): sha(path)
               for path in content.rglob("*")
               if path.is_file() and path.suffix.lower() in (".uasset", ".umap", ".uexp", ".ubulk")}
    assert current == receipts[chain[-1]]["native_after_hashes"], "Current native packages differ from saved authoring chain"
    freeze = receipts["CryoFreezeFX.json"]
    interaction = receipts["CryoInteractionApply.json"]
    assert freeze["ambient_effects_and_breathing_sequence_unchanged"]
    assert Path(interaction["manifest"]).resolve() == base_manifest_path.resolve()
    assert set(freeze["frost_actor_labels"]) == {bay + "_Frost" for bay in "ABCD"}
    material_package = freeze["frost"]["asset"].split(".")[0]
    material = material_package + "." + material_package.rsplit("/", 1)[1]
    native_file(material, content)
    for label in freeze["frost_actor_labels"]:
        bay, component = label.split("_", 1)
        mesh = saved_meshes[(bay, component)]
        assert mesh["role"] == "frost", label
        mesh["prior_material_reference"] = mesh["material"]
        mesh["material"] = material
        mesh["material_override_receipt"] = str(WORK / "CryoFreezeFX.json")
    actors = interaction["actors"]
    assert len(actors) == 4 and {row["model"] for row in actors} == set("ABCD")
    assert all(len(row["nozzle_local_cm"]) == 2 and row["frost_actor"] == row["model"] + "_Frost" for row in actors)
    containment = receipts.get("CryoJetContainment.json")
    if containment:
        assert containment["recipe"]["all_four_same_system"] and containment["recipe"]["nozzle_world_origins_unchanged"]
        native_file(containment["jet"]["system"], content)
    texture_keys = {key for key in current if "/Textures/" in key}
    initial = receipts[chain[0]]["native_before_hashes"]
    assert {key: current[key] for key in texture_keys} == {key: value for key, value in initial.items() if "/Textures/" in key}, "Native texture inventory changed"
    return {"status": "SAVED_AUTHORING_CHAIN_MATCHES_CURRENT_STAGE_RUNTIME_ACCEPTANCE_SEPARATE",
            "manifest_sha256": sha(manifest_path), "base_manifest_sha256": fit["manifest_sha256"],
            "authoring_receipts": [{"path": str(WORK / name), "sha256": sha(WORK / name)} for name in chain],
            "protected_native_hashes": current, "frost_material": material,
            "frost_actor_labels": freeze["frost_actor_labels"],
            "nozzle_niagara_components": sum(len(row["nozzle_local_cm"]) for row in actors),
            "native_interaction_actors": len(actors),
            "freeze_jet_system": (containment or freeze)["jet"]["system"],
            "reused_shared_texture_roles": ["frost", "mist"], "additional_authored_texture_maps": 0,
            "texture_evidence": "Freeze authoring creates two materials and one Niagara system; full native texture inventory is unchanged across the receipt chain."}, paths


def main(args=None):
    args = args or parse_args([])
    manifest_path, author_path, output = args.manifest.resolve(), args.author.resolve(), args.output.resolve()
    content = args.content.resolve()
    namespace = (content / args.namespace[len("/Game/"):] if args.namespace.startswith("/Game/")
                 else Path(args.namespace)).resolve()
    assert namespace.is_relative_to(content), "Namespace must be within Content"
    assert output.parent.resolve() == WORK.resolve(), "Metrics output must stay in work/"
    legacy = manifest_path == MANIFEST.resolve() and author_path == (WORK / "CryoFinalAuthor.json").resolve()
    assert legacy or output != OUTPUT.resolve(), "Use a new --output to preserve legacy final metrics"
    assert not args.refresh_output or output in {(WORK / name).resolve() for name in ("cryo-costs-v4.json", "cryo-costs-v4_3.json", "cryo-costs-v4_4.json")}, "Refresh is limited to the current v4 metrics snapshots"
    assert legacy or args.refresh_output or not output.exists(), "Refusing to overwrite an existing metrics snapshot; use --refresh-output for v4"
    assert output != (WORK / "cryo-costs.json").resolve(), "Preserve baseline metrics"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    baseline_path = WORK / "glb-baseline.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8-sig"))
    author = json.loads(author_path.read_text(encoding="utf-8-sig"))
    refinement_path = WORK / "CryoNativeRefinement.json"
    refinement = json.loads(refinement_path.read_text(encoding="utf-8-sig"))
    console_path = WORK / "CryoConsoleUpgrade.json"
    console = json.loads(console_path.read_text(encoding="utf-8-sig"))
    breathing_path = WORK / "CryoBreathingLights.json"
    breathing = json.loads(breathing_path.read_text(encoding="utf-8-sig"))
    assert refinement["status"].startswith("NATIVE_REFINEMENT_SAVED_")
    assert console["status"].startswith("CONSOLE_GLASS_HUD_SAVED_")
    assert breathing["status"].startswith("SAVED_NATIVE_LOOP_")
    by_hash = {row["sha256"]: row for row in baseline["assets"]}
    saved_meshes, counts, author_inputs, superseded, delta_author = author_meshes(
        author, manifest, manifest_path, author_path, content)
    current_evidence = None
    if not legacy:
        current_evidence, current_receipts = current_stage_overrides(manifest_path, content, saved_meshes)
        author_inputs = list(dict.fromkeys([*author_inputs, *current_receipts]))
    previous_author_path = WORK / "CryoFinalAuthor.json"
    previous_author = json.loads(previous_author_path.read_text(encoding="utf-8-sig"))
    if previous_author_path.resolve() not in {path.resolve() for path in author_inputs}:
        author_inputs.append(previous_author_path)
    warnings = import_warning_evidence(() if legacy else (WORK / "CryoFitV4Author.log",))
    prior_metrics = sorted(path for path in WORK.glob("cryo-costs*.json") if path.resolve() != output)
    input_hashes = {str(path): sha(path) for path in (manifest_path, baseline_path, *author_inputs, refinement_path,
        console_path, breathing_path, *prior_metrics)}
    assert str(output) not in input_hashes, "Output collides with an input"
    native_inputs = {path.resolve() for path in namespace.rglob("*")
                     if path.is_file() and path.suffix in (".uasset", ".umap")}
    native_inputs.update(path.resolve() for path in (content / "NiagaraExamples").rglob("*.uasset"))
    input_hashes.update({str(path): sha(path) for path in native_inputs})
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
            "active_recovery_accounting": "Active model meshes follow exact manifest components and saved native receipt references. Known superseded mesh packages and old opaque console resources are recovery. Other namespace packages are stored scene support; no current runtime dependency closure was probed."},
        "inputs": {"manifest": str(manifest_path), "baseline": str(baseline_path),
                   "native_author_receipt": str(author_path), "native_refinement_receipt": str(refinement_path),
                   "console_upgrade_receipt": str(console_path), "breathing_lights_receipt": str(breathing_path),
                   "preserved_prior_metrics": str(WORK / "cryo-costs.json"),
                   "preserved_metric_files": [str(path) for path in prior_metrics],
                   "native_author_receipts": [str(path) for path in author_inputs],
                   "native_author_is_delta": delta_author,
                   "refreshed_previous_v4_metrics_sha256": sha(output) if args.refresh_output and output.exists() else None,
                   "content": str(content), "namespace": str(namespace)},
        "current_native_evidence": current_evidence,
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
            assert saved["sections_lod0"] == 1 and saved["lod_count"] in (None, 1)
            row["native_lod0_material_sections"] = saved["sections_lod0"]
            row["native_lod_count"] = saved["lod_count"]
            row["native_mesh_uasset"] = size_info(native_file(saved["asset"], content))
            row["native_mesh_asset"] = saved["asset"]
            if "native_count_evidence" in saved:
                row["native_count_evidence"] = saved["native_count_evidence"]
            row["material_reference"] = saved["material"]
            for key in ("prior_material_reference", "material_override_receipt"):
                if key in saved:
                    row[key] = saved[key]
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
            row["native_texture_uasset"] = size_info(namespace / "Textures" / ("T_" + model_id + "_" + role + ".uasset"))
            texture_files.append(row["native_texture_uasset"]["path"])
            input_hashes[row["path"]] = row["sha256"]
            assert row["sha256"] in {image["sha256"] for image in original["images"]}, "Extracted body texture diverged from source"
        body_material = next(saved_meshes[(model_id, row["name"])]["material"]
                             for row in model["components"] if row["role"] == "body")
        material_file = native_file(body_material, content)
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
            "import_warning_evidence": [warning for warning in warnings[model_id]
                                        if warning["mesh"] in {Path(row["native_mesh_uasset"]["path"]).stem for row in components}],
            "warning_note": "No matching warning in this successful import log does not prove defect-free shading."})
    shared = {}
    for role, path in manifest["shared"].items():
        if role == "console":
            native = native_file(console["textures"][0]["asset"], content)
            assert Path(console["textures"][0]["source"]).resolve() == Path(path).resolve()
            build_evidence = "Successful ConsoleUpgrade import uses author_cryo_unreal.py Shared Console resize_during_build_x/y=2048/1024; source pixels unchanged."
        else:
            native = namespace / "Textures" / ("T_Cryo_" + role.title() + ".uasset")
            refinement_row = next(row for row in refinement["textures"] if row["asset"].split(".")[0].endswith(native.stem))
            assert refinement_row["build_size"] == BUILD_DIMS[role]
            build_evidence = "Native refinement receipt; original source pixels preserved."
        shared[role] = image_info(path, role, BUILD_DIMS[role])
        shared[role]["native_texture_uasset"] = size_info(native)
        shared[role]["build_dimensions_evidence"] = build_evidence
        input_hashes[shared[role]["path"]] = shared[role]["sha256"]
    assert shared["console"]["estimated_standard_bc_full_mips"]["format"] == "BC3"
    all_native_files = set(path.resolve() for path in namespace.rglob("*.uasset"))
    all_mesh_files = {path.resolve() for path in (namespace / "Meshes").rglob("*.uasset")}
    active_mesh_files = {Path(row["native_mesh_uasset"]["path"]).resolve()
                         for model in report["models"] for row in model["finished_geometry"]["components"]}
    assert active_mesh_files <= all_mesh_files
    previous_mesh_files = {native_file(row["asset"], content).resolve() for row in previous_author["meshes"]}
    previous_mesh_files.update((namespace / "Meshes" / model_id / ("SM_" + model_id + "_Console_" + index + ".uasset")).resolve()
                               for model_id in "ABCD" for index in ("1", "2"))
    recovery_meshes = previous_mesh_files - active_mesh_files
    assert recovery_meshes <= all_mesh_files
    assert superseded <= recovery_meshes
    recovery_files = recovery_meshes | {namespace / "Materials/M_Console.uasset", namespace / "Textures/T_Cryo_Console.uasset"}
    recovery_files = {path.resolve() for path in recovery_files}
    assert recovery_files <= all_native_files and not (recovery_files & model_owned_files)
    common_files = all_native_files - model_owned_files - recovery_files
    donor_files = list((content / "NiagaraExamples").rglob("*.uasset"))
    shared_gpu_bytes = sum(row["estimated_standard_bc_full_mips"]["bytes"] for row in shared.values())
    report["common"] = {"shared_images": shared,
        "estimated_shared_texture_gpu_full_mips": {"status": "ESTIMATE_NOT_MEASURED_GPU_ALLOCATION", "bytes": shared_gpu_bytes, "MiB": round(shared_gpu_bytes / MIB, 6)},
        ("namespace_active_shared_and_scene_support_uassets" if legacy else "namespace_stored_shared_and_scene_support_uassets"): aggregate_files(common_files),
        "shared_support_activity": "Stored support only; materials, freeze effects, jets and donor dependencies are not a current verified live dependency closure.",
        "niagara_donor_stored_uncooked_dependencies": aggregate_files(donor_files),
        "donor_reference_limit": "Original copied 16-package closure retained. Bounded Niagara now overrides the sprite material/cutout; exact final live subset of donor packages was not re-probed, so these bytes describe stored dependency support, not per-chamber or resident runtime cost.",
        "comparison_maps": aggregate_files(namespace.rglob("*.umap")),
        "native_effect_instances": {"niagara_system_actors": counts["niagara_actors"],
            "local_fog_volumes": counts["local_fog_volumes"], "global_exponential_volumetric_fog": 1,
            "evidence_scope": "Counts from listed author/breathing receipts; subsequent freeze/jet effects are not re-counted by this filesystem-only inventory.",
            "added_shadowless_point_lights": breathing["plan"]["new_point_lights"],
            "modified_existing_point_lights": breathing["plan"]["modified_point_lights"],
            "animated_intensity_tracks": len(breathing["tracks"]), "loop_period_seconds": breathing["period_seconds"],
            "all_eight_animated_lights_cast_shadows": any(row["cast_shadows"] for row in breathing["saved_resting_lights"]),
            "sequence_asset": breathing["sequence"], "light_effect_evidence": str(breathing_path),
            "runtime_cost": "UNMEASURED; identical per-chamber effect setup is not a GPU timing or FPS result."},
        "effect_instance_evidence": str(author_path),
        "niagara_gpu_texture_cost": "UNMEASURED; not included in standard BC estimate, and shared rather than charged four times."}
    if current_evidence:
        report["common"]["native_effect_instances"].update(
            ambient_niagara_system_actors=counts["niagara_actors"],
            nozzle_niagara_components=current_evidence["nozzle_niagara_components"],
            native_interaction_actors=current_evidence["native_interaction_actors"],
            niagara_component_instances_including_ambient=counts["niagara_actors"] + current_evidence["nozzle_niagara_components"],
            nozzle_activation="Eight saved nozzle components activate on interaction; this is not a simultaneous active-particle count.",
            effect_authoring_receipts=current_evidence["authoring_receipts"],
            evidence_scope="Saved package chain matches current stage: four ambient Niagara actors, eight nozzle Niagara components and four native interaction actors. Runtime/visual acceptance remains separate.",
            reused_shared_texture_roles=current_evidence["reused_shared_texture_roles"],
            additional_authored_texture_maps=0)
    report["stored_recovery"] = {"reason": "Known prior model mesh packages absent from the saved active component references, plus the original opaque console material and texture. Other unproven shared resources remain stored scene support.",
        "superseded_mesh_uassets": aggregate_files(recovery_meshes),
        "namespace_uncooked_uassets": aggregate_files(recovery_files),
        "excluded_from_active_texture_gpu_estimate": True, "no_deletion_performed": True}
    report["totals"] = {"triangles_all_four_static_assemblies": sum(row["finished_geometry"]["triangles"] for row in report["models"]),
        "static_material_sections_all_four": sum(row["finished_geometry"]["native_lod0_material_sections"] for row in report["models"]),
        "namespace_stored_uassets_including_recovery": aggregate_files(all_native_files),
        ("namespace_active_and_scene_support_uassets" if legacy else "namespace_active_model_and_stored_scene_support_uassets"): aggregate_files(all_native_files - recovery_files),
        "estimated_body_plus_shared_texture_gpu_full_mips_bytes": sum(row["estimated_body_texture_gpu_full_mips"]["bytes"] for row in report["models"]) + shared_gpu_bytes}
    report["totals"]["estimated_body_plus_shared_texture_gpu_full_mips_MiB"] = round(report["totals"]["estimated_body_plus_shared_texture_gpu_full_mips_bytes"] / MIB, 6)
    changed = [path for path, value in input_hashes.items() if sha(path) != value]
    assert not changed, changed
    assert {path.resolve() for path in namespace.rglob("*.uasset")} == all_native_files, "Native inventory changed during measurement"
    report["read_only_validation"] = {"input_hash_count": len(input_hashes), "all_inputs_unchanged": True, "prior_metrics_json_unchanged": True,
                                      "source_glb_hashes_match_baseline": True, "engine_launched": False,
                                      "native_input_hash_count": len(native_inputs), "native_component_sources_match_manifest": True}
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "models": [{"id": row["id"], "original_triangles": row["original"]["triangles"],
        "finished_triangles": row["finished_geometry"]["triangles"], "finished_obj_vertices": row["finished_geometry"]["vertices_position_records"],
        "sections": row["finished_geometry"]["native_lod0_material_sections"], "body_texture_estimate_MiB": row["estimated_body_texture_gpu_full_mips"]["MiB"],
        "native_model_MiB": row["native_uncooked"]["model_owned_total"]["MiB"], "import_warnings": len(row["import_warning_evidence"])} for row in report["models"]],
        "shared_texture_estimate_MiB": shared_gpu_bytes / MIB, "all_input_hashes_unchanged": not changed}, indent=2))


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--author", type=Path, default=WORK / "CryoFinalAuthor.json")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--refresh-output", action="store_true", help="Explicitly refresh only a named work/cryo-costs-v4*.json current snapshot")
    parser.add_argument("--content", type=Path, default=CONTENT)
    parser.add_argument("--namespace", default="/Game/SpaceSurvival/CryoComparison",
                        help="Unreal /Game package prefix or absolute directory within Content")
    return parser.parse_args(argv)


if __name__ == "__main__":
    main(parse_args())
