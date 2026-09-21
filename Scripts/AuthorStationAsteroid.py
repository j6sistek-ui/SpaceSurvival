"""Author the private station asteroid from the owner's Photo 5 source.

Run through the installed Unreal editor with -NullRHI or -RenderOffscreen.
Inspection is the default; -SSApplyStationAsteroid (or --apply) authors the derivative.
Source assets are never saved. Existing output requires a matching ownership receipt.
The output is scenery: station-native floors/walls own playable collision.
"""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Artifacts/StationAsteroid"
RECEIPT = OUT / "author.json"
SOURCE = "/Game/Fab/High_Poly_Asteroid_Detailed_Free_3D_Model/SM_High_Poly_Asteroid_Detailed_Free_3D_Model"
BASE = "/Game/SpaceSurvival/Licensed/StationReset"
TARGET = BASE + "/SM_StationAsteroid"
APPLY = "-SSApplyStationAsteroid" in u.SystemLibrary.get_command_line() or "--apply" in sys.argv
REVISION = 1
TARGET_TRIANGLES = 500000
LIB = u.EditorAssetLibrary


def disk_path(package):
    assert package.startswith("/Game/")
    return ROOT / "Content" / (package[6:] + ".uasset")


def digest(package):
    path = disk_path(package)
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def xyz(vector):
    return [float(vector.x), float(vector.y), float(vector.z)]


def metadata(mesh):
    description = mesh.get_static_mesh_description(0)
    bounds = mesh.get_bounds()
    subsystem = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    return {"source_triangles": description.get_triangle_count(),
            "source_vertices": description.get_vertex_count(),
            "nanite_triangles": mesh.get_num_nanite_triangles(),
            "nanite_enabled": subsystem.get_nanite_settings(mesh).enabled,
            "bounds_origin_cm": xyz(bounds.origin), "bounds_extent_cm": xyz(bounds.box_extent),
            "lods": [{"index": i, "triangles": mesh.get_num_triangles(i),
                      "vertices": mesh.get_num_vertices(i)} for i in range(mesh.get_num_lods())],
            "materials": [slot.material_interface.get_path_name() if slot.material_interface else None
                          for slot in mesh.get_editor_property("static_materials")],
            "simple_collision_count": subsystem.get_simple_collision_count(mesh)}


def probes(mesh):
    """Compare the bowl and outer silhouette, without modifying an asset or actor."""
    spatial = u.GeometryScript_MeshSpatial
    _, bvh = spatial.build_bvh_for_mesh(mesh)
    options = u.GeometryScriptSpatialQueryOptions(max_distance=500.)
    # The measured opening axis points diagonally -X/+Z. This quaternion aligns it to -X.
    q_inverse = u.Quat(0, .30010876326423286, .16601761372063947, .9393470509596106)
    rays = []
    for y in (-40., -20., 0., 20., 40.):
        for z in (-40., -20., 0., 20., 40.):
            rays.append(("cavity", q_inverse.rotate_vector(u.Vector(-160, y, z)),
                         q_inverse.rotate_vector(u.Vector(1, 0, 0))))
    for axis in range(3):
        for sign in (-1., 1.):
            cross = [i for i in range(3) if i != axis]
            for a in (-80., -40., 0., 40., 80.):
                for b in (-80., -40., 0., 40., 80.):
                    origin, direction = [0., 0., 0.], [0., 0., 0.]
                    origin[axis], direction[axis] = 160. * sign, -sign
                    origin[cross[0]], origin[cross[1]] = a, b
                    rays.append(("silhouette", u.Vector(*origin), u.Vector(*direction)))
    result = []
    for kind, origin, direction in rays:
        _, hit, _ = spatial.find_nearest_ray_intersection_with_mesh(mesh, bvh, origin, direction, options)
        result.append({"kind": kind, "origin_cm": xyz(origin), "direction": xyz(direction),
                       "hit": bool(hit.hit), "distance_cm": float(hit.ray_parameter) if hit.hit else None})
    return result


def compare_probes(before, after):
    assert len(before) == len(after)
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a["hit"] != b["hit"]]
    differences = [abs(a["distance_cm"] - b["distance_cm"])
                   for a, b in zip(before, after) if a["hit"] and b["hit"]]
    maximum = max(differences, default=0.)
    result = {"rays": len(before), "changed_hit_indices": changed,
              "maximum_surface_distance_delta_cm_at_source_scale": maximum,
              "maximum_surface_distance_delta_cm_at_station_scale145": maximum * 145.,
              "source_scale_tolerance_cm": 1.0}
    assert not changed, "Simplification changed cavity/silhouette ray coverage: " + str(changed)
    assert math.isfinite(maximum) and maximum <= 1., "Simplification exceeds measured shape tolerance: " + str(maximum)
    return result


def main():
    source_hash = digest(SOURCE)
    assert source_hash, "Owned asteroid source is not installed"
    prior = json.loads(RECEIPT.read_text(encoding="utf-8")) if RECEIPT.is_file() else None
    current = digest(TARGET)
    if current:
        assert prior and prior.get("outputs", {}).get(TARGET) == current, "Refusing unrecognized/edited asteroid derivative"
        assert prior.get("source_sha256") == source_hash, "Source changed; review before replacing the derivative"
    record = {"utc": datetime.now(timezone.utc).isoformat(), "mode": "apply" if APPLY else "dry-run",
              "revision": REVISION, "status": "inspecting", "source": SOURCE, "source_sha256": source_hash,
              "target": TARGET, "target_triangles": TARGET_TRIANGLES, "outputs": {}, "source_preserved": False,
              "limits": ["Shape probes are sampled, not a complete Hausdorff/visual acceptance test.",
                         "No rendered appearance, packaged performance or owner acceptance is implied.",
                         "World scale changes dimensions only; this script reduces actual source geometry.",
                         "No collision is authored on the scenery mesh; the native district owns physical boundaries."]}
    try:
        source = u.load_asset(SOURCE)
        assert source, "Could not load the exact Photo 5 source"
        record["source_measurement"] = metadata(source)
        if not APPLY:
            record["status"] = "dry-run"
            print("STATION_ASTEROID_DRY_RUN " + json.dumps(record["source_measurement"]))
            return
        if current and prior.get("status") == "complete" and prior.get("revision") == REVISION:
            record.update({key: value for key, value in prior.items() if key not in ("utc", "mode", "outputs")})
            record["idempotent_existing"] = True
            return
        dynamic = u.DynamicMesh()
        options = u.GeometryScriptCopyMeshFromAssetOptions(apply_build_settings=False, request_tangents=True)
        lod = u.GeometryScriptMeshReadLOD(lod_type=u.GeometryScriptLODType.SOURCE_MODEL, lod_index=0)
        _, outcome = u.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(source, dynamic, options, lod)
        assert outcome == u.GeometryScriptOutcomePins.SUCCESS, "Source mesh copy failed"
        assert dynamic.get_triangle_count() == record["source_measurement"]["source_triangles"], "Copy did not use full source geometry"
        record["source_uv_channels"] = u.GeometryScript_MeshQueries.get_num_uv_sets(dynamic)
        before_bounds = u.GeometryScript_MeshQueries.get_mesh_bounding_box(dynamic)
        record["source_probes"] = probes(dynamic)
        print("STATION_ASTEROID_SIMPLIFY_BEGIN " + str(dynamic.get_triangle_count()), flush=True)
        u.GeometryScript_MeshSimplification.apply_editor_simplify_to_triangle_count(dynamic, TARGET_TRIANGLES)
        count = dynamic.get_triangle_count()
        assert TARGET_TRIANGLES // 2 <= count <= TARGET_TRIANGLES * 1.1, "Unexpected simplified triangle count: " + str(count)
        record["simplified_dynamic_triangles"] = count
        record["output_uv_channels"] = u.GeometryScript_MeshQueries.get_num_uv_sets(dynamic)
        assert record["output_uv_channels"] == record["source_uv_channels"], "Simplification removed UV channels"
        after_bounds = u.GeometryScript_MeshQueries.get_mesh_bounding_box(dynamic)
        bound_deltas = [abs(a - b) for a, b in zip(xyz(before_bounds.min) + xyz(before_bounds.max),
                                                   xyz(after_bounds.min) + xyz(after_bounds.max))]
        record["bounds_max_delta_cm"] = max(bound_deltas)
        assert max(bound_deltas) <= 1., "Simplification changed outer bounds by more than 1 source cm"
        record["output_probes"] = probes(dynamic)
        record["shape_comparison"] = compare_probes(record["source_probes"], record["output_probes"])
        # Create only after the transient geometry passes inspection. No source duplication/save is necessary.
        target = u.load_asset(TARGET) if current else u.AssetToolsHelpers.get_asset_tools().create_asset(
            "SM_StationAsteroid", BASE, u.StaticMesh, u.StaticMeshFactoryNew())
        assert target, "Could not create private asteroid mesh"
        target.set_editor_property("static_materials", source.get_editor_property("static_materials"))
        subsystem = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
        nanite = subsystem.get_nanite_settings(source)
        nanite.enabled = True
        nanite.keep_percent_triangles = 1.
        nanite.trim_relative_error = 0.
        nanite.fallback_target = u.NaniteFallbackTarget.PERCENT_TRIANGLES
        nanite.fallback_percent_triangles = min(1., 20000. / count)
        nanite.fallback_relative_error = 0.
        write = u.GeometryScriptCopyMeshToAssetOptions(apply_nanite_settings=True, new_nanite_settings=nanite,
                                                       enable_recompute_tangents=True, emit_transaction=False)
        _, outcome = u.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(
            dynamic, target, write, u.GeometryScriptMeshWriteLOD(lod_index=0))
        assert outcome == u.GeometryScriptOutcomePins.SUCCESS, "Private simplified mesh copy failed"
        subsystem.remove_collisions(target)
        LIB.set_metadata_tag(target, "SpaceSurvivalAuthor", "AuthorStationAsteroid.py")
        LIB.set_metadata_tag(target, "SpaceSurvivalSourceSHA256", source_hash)
        assert LIB.save_loaded_asset(target, only_if_is_dirty=False), "Private asteroid save failed"
        record["output_measurement"] = metadata(target)
        assert record["output_measurement"]["source_triangles"] <= TARGET_TRIANGLES * 1.1
        assert record["output_measurement"]["materials"] == record["source_measurement"]["materials"]
        assert record["output_measurement"]["simple_collision_count"] == 0
        record["status"] = "complete"
        print("STATION_ASTEROID_COMPLETE " + json.dumps(record["output_measurement"]), flush=True)
    except Exception as error:
        record["status"], record["error"] = "failed", str(error)
        raise
    finally:
        record["source_preserved"] = digest(SOURCE) == source_hash
        if digest(TARGET):
            record["outputs"][TARGET] = digest(TARGET)
        OUT.mkdir(parents=True, exist_ok=True)
        # Dry runs must not erase the ownership/verification record of a completed output.
        path = OUT / "dry-run.json" if not APPLY else RECEIPT
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        assert record["source_preserved"], "Original asteroid bytes changed during authoring"


if __name__ == "__main__":
    main()
