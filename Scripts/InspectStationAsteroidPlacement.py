"""Read-only asteroid collision-fallback probes for the station's measured pose.

Run in the lead's serialized offscreen Unreal session after AuthorStationAsteroid.
No asset, map or actor is saved or changed. These are sampled geometry checks, not
continuous walkability, collision, rendered appearance or frame-time acceptance.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
ASSET = "/Game/SpaceSurvival/Licensed/StationReset/SM_StationAsteroid"
PATH = ROOT / "Content/SpaceSurvival/Licensed/StationReset/SM_StationAsteroid.uasset"
OUT = ROOT / "Artifacts/StationAsteroid/placement.json"


def main():
    before = hashlib.sha256(PATH.read_bytes()).hexdigest()
    record = {"utc": datetime.now(timezone.utc).isoformat(), "asset": ASSET, "asset_sha256": before,
              "status": "inspecting", "samples": [], "inside_samples": [], "camera_checks": [],
              "pose": {"location_cm": [7500, 0, 5300], "rotation_pitch_yaw_roll": [34.319873, -22.187753, -6.929723],
                       "uniform_scale": 145},
              "limits": ["Only sampled points/rays are checked, not whole boxes or continuous geometry.",
                         "Native collision uses this built fallback; actual world sweeps are tested separately.",
                         "Camera rays are advisory; they test rock occlusion, not other scene props or framing."]}
    try:
        mesh = u.load_asset(ASSET)
        assert mesh, "Reduced station asteroid is not installed"
        dynamic = u.DynamicMesh()
        lod = u.GeometryScriptMeshReadLOD(lod_type=u.GeometryScriptLODType.RENDER_DATA, lod_index=0)
        _, outcome = u.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(
            mesh, dynamic, u.GeometryScriptCopyMeshFromAssetOptions(apply_build_settings=False), lod)
        assert outcome == u.GeometryScriptOutcomePins.SUCCESS
        record["actual_source_triangles"] = mesh.get_static_mesh_description(0).get_triangle_count()
        record["actual_nanite_triangles"] = mesh.get_num_nanite_triangles()
        record["actual_fallback_triangles"] = dynamic.get_triangle_count()
        assert record["actual_fallback_triangles"] == mesh.get_num_triangles(0), "Inspection did not read built LOD0"
        record["inspected_geometry"] = "built_lod0_collision_fallback"
        spatial = u.GeometryScript_MeshSpatial
        _, bvh = spatial.build_bvh_for_mesh(dynamic)
        options = u.GeometryScriptSpatialQueryOptions(max_distance=500.)
        inverse = u.Quat(0, .30010876326423286, .16601761372063947, .9393470509596106)
        translation = u.Vector(7500, 0, 5300)
        queries = [("room", x, y, z) for x in range(-1900, 2101, 500)
                   for y in range(-1500, 1501, 500) for z in (-10, 250, 510)]
        queries += [("terrace", x, y, z) for x in (-2000, 0)
                    for y in (-6500, -4500, 4500, 6500) for z in (750, 1650, 2550)]
        down = inverse.rotate_vector(u.Vector(0, 0, -1))
        up = inverse.rotate_vector(u.Vector(0, 0, 1))
        for kind, x, y, z in queries:
            point = inverse.rotate_vector((u.Vector(x, y, z) - translation) / 145.)
            _, inside, _ = spatial.is_point_inside_mesh(dynamic, bvh, point, options)
            row = {"kind": kind, "world_cm": [x, y, z], "inside_rock": bool(inside)}
            if inside:
                record["inside_samples"].append(row)
            for label, direction in (("rock_below_cm", down), ("rock_above_cm", up)):
                _, hit, _ = spatial.find_nearest_ray_intersection_with_mesh(dynamic, bvh, point, direction, options)
                row[label] = float(hit.ray_parameter) * 145. if hit.hit else None
            record["samples"].append(row)
        cameras = [
            ("StationColonyOverview", (-17000, -6000, 9000), (-1600, 0, 2400)),
            ("StationPadMouth", (-2000, 2200, 1000), (-5200, -400, 300)),
        ]
        anchors = [
            ("pad", (-4450, 0, 300)),
            ("room_roof", (100, 0, 550)),
            ("terrace_negative_y", (-1000, -5500, 1600)),
            ("terrace_positive_y", (-1000, 5500, 1600)),
        ]
        for name, location, target in cameras:
            eye = u.Vector(*location)
            point = inverse.rotate_vector((eye - translation) / 145.)
            _, inside, _ = spatial.is_point_inside_mesh(dynamic, bvh, point, options)
            camera = {"name": name, "hub_local_cm": list(location), "target_cm": list(target),
                      "horizontal_fov_degrees": 70, "inside_rock": bool(inside), "rays": []}
            for label, destination in [("look_target", target)] + anchors:
                delta = u.Vector(*destination) - eye
                distance = (float(delta.x) ** 2 + float(delta.y) ** 2 + float(delta.z) ** 2) ** .5
                direction = inverse.rotate_vector(delta / distance)
                _, hit, _ = spatial.find_nearest_ray_intersection_with_mesh(
                    dynamic, bvh, point, direction, options)
                hit_distance = float(hit.ray_parameter) * 145. if hit.hit else None
                camera["rays"].append({"anchor": label, "hub_local_cm": list(destination),
                                       "target_distance_cm": distance, "first_rock_cm": hit_distance,
                                       "rock_before_target": hit_distance is not None and
                                       hit_distance < distance - 1.})
            record["camera_checks"].append(camera)
        assert not record["inside_samples"], "Reduced asteroid intersects sampled room/terrace points"
        record["status"] = "sampled-clearance-pass"
        print("STATION_ASTEROID_PLACEMENT " + json.dumps(
            {"status": record["status"], "fallback_triangles": record["actual_fallback_triangles"],
             "nanite_triangles": record["actual_nanite_triangles"], "source_triangles": record["actual_source_triangles"],
             "samples": len(record["samples"]), "inside": len(record["inside_samples"])}))
    except Exception as error:
        record["status"], record["error"] = "failed", str(error)
        raise
    finally:
        record["asset_preserved"] = hashlib.sha256(PATH.read_bytes()).hexdigest() == before
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        assert record["asset_preserved"], "Read-only inspection changed the asteroid package"


if __name__ == "__main__":
    main()
